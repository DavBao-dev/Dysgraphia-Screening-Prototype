"""
train_model_b.py - Danh gia va huan luyen lai Model B (anh chu viet) bang DUNG pipeline cua app.

Du lieu: bo Mendeley "Potential Dysgraphia Handwriting Dataset of School-Age Children",
giai nen thanh 2 thu muc con trong --data-dir:
    Potential Dysgraphia/       PD (1).jpg ...   -> nhan 1
    Low Potential Dysgraphia/   LPD (1).jpg ...  -> nhan 0
Moi hoc sinh chep 3 cau co dinh, file duoc danh so lien tiep, nen
hoc sinh = (so thu tu - 1) // 3 trong tung lop.

Pipeline (giong het backend/services/model_b_service.py):
    anh -> image_features.normalize_handwriting (muc den, nen trang)
        -> [ink_thickness_mean, baseline_deviation] -> StandardScaler
        -> + embedding ResNet50 (weights/resnet50_backbone.onnx)
        -> MLP 2050 -> 128 -> 32 -> 1 -> sigmoid

Danh gia: kiem dinh cheo 5 phan THEO HOC SINH (StratifiedGroupKFold), scaler va head
huan luyen lai trong tung phan, dung som dua tren mot nhom hoc sinh tach ra tu phan
huan luyen (khong nhin phan kiem thu). Lap lai voi nhieu seed.

Chay:
    python train_model_b.py --data-dir data/for_testing/model_b --cv-only   # chi danh gia
    python train_model_b.py --data-dir data/for_testing/model_b             # danh gia + ghi weights/
"""
import argparse
import collections
import json
import os
import re

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

from backend.ml import image_features
from backend.services import model_b_service

CLASSES = (("Potential Dysgraphia", 1), ("Low Potential Dysgraphia", 0))
EPOCHS, LR, BATCH, PATIENCE, MIN_DELTA = 30, 1e-3, 16, 8, 1e-4


# ---------------------------------------------------------------------------- data
def load_dataset(data_dir):
    items = []
    for cls_dir, label in CLASSES:
        d = os.path.join(data_dir, cls_dir)
        for fname in sorted(os.listdir(d)):
            m = re.search(r"\((\d+)\)", fname)
            if not m or not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            idx = int(m.group(1))
            prefix = "PD" if label else "LPD"
            items.append({"path": os.path.join(d, fname), "name": fname, "label": label,
                          "child": f"{prefix}{(idx - 1) // 3 + 1:02d}", "sentence": (idx - 1) % 3 + 1})
    return items


def compute_features(items):
    emb, hc = [], []
    for it in items:
        with open(it["path"], "rb") as f:
            norm = image_features.normalize_handwriting(f.read())
        feats = image_features.extract_ink_and_baseline_features(norm)
        hc.append([feats["ink_thickness_mean"], feats["baseline_deviation"]])
        emb.append(model_b_service.extract_embedding(norm)[0])
    return np.asarray(emb, np.float32), np.asarray(hc, np.float32)


# ---------------------------------------------------------------------------- model
class Head(nn.Module):
    """Cung key voi backend.ml.inference.MLPHead (net.0 / net.3 / net.5); tra ve logit."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(2050, 128), nn.ReLU(), nn.Dropout(0.3),
                                 nn.Linear(128, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        return self.net(x)


class OnnxHead(nn.Module):
    """Dau vao/ra giong weights/model_b.onnx cu: (embedding, handcrafted) -> score (sigmoid)."""

    def __init__(self, head):
        super().__init__()
        self.head = head

    def forward(self, embedding, handcrafted):
        return torch.sigmoid(self.head(torch.cat([embedding, handcrafted], dim=1)))


def fit_head(EMB, HC, y, groups, train_idx, seed):
    """Huan luyen scaler + head tren train_idx. Tra ve (head, scaler)."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=seed)
    fit_i, es_i = next(gss.split(train_idx, y[train_idx], groups[train_idx]))
    fit, es = train_idx[fit_i], train_idx[es_i]

    scaler = StandardScaler().fit(HC[fit])

    def X(idx):
        return torch.tensor(np.hstack([EMB[idx], scaler.transform(HC[idx])]), dtype=torch.float32)

    Xf, yf = X(fit), torch.tensor(y[fit], dtype=torch.float32).unsqueeze(1)
    Xe, ye = X(es), torch.tensor(y[es], dtype=torch.float32).unsqueeze(1)
    head = Head()
    opt = torch.optim.Adam(head.parameters(), lr=LR)
    crit = nn.BCEWithLogitsLoss()
    best, best_state, bad = float("inf"), None, 0
    for _ in range(EPOCHS):
        head.train()
        perm = torch.randperm(len(fit))
        for i in range(0, len(fit), BATCH):
            b = perm[i:i + BATCH]
            xb = Xf[b].clone()
            xb[:, :2048] += 0.01 * torch.randn_like(xb[:, :2048])  # nhieu nhe tren embedding
            xb[:, 2048:] += 0.05 * torch.randn_like(xb[:, 2048:])  # va tren 2 feature thu cong
            loss = crit(head(xb), yf[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
        head.eval()
        with torch.no_grad():
            val = crit(head(Xe), ye).item()
        if val < best - MIN_DELTA:
            best, best_state, bad = val, {k: v.clone() for k, v in head.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    head.load_state_dict(best_state)
    head.eval()
    return head, scaler


def predict(head, scaler, EMB, HC, idx):
    x = torch.tensor(np.hstack([EMB[idx], scaler.transform(HC[idx])]), dtype=torch.float32)
    with torch.no_grad():
        return torch.sigmoid(head(x)).numpy().reshape(-1)


# ---------------------------------------------------------------------------- metrics
def metrics(y, prob, thr=0.5):
    p = (prob >= thr).astype(int)
    tp, tn = int(((p == 1) & (y == 1)).sum()), int(((p == 0) & (y == 0)).sum())
    fp, fn = int(((p == 1) & (y == 0)).sum()), int(((p == 0) & (y == 1)).sum())
    sens, spec = tp / max(tp + fn, 1), tn / max(tn + fp, 1)
    prec = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * prec * sens / (prec + sens) if prec + sens else 0.0
    return {"accuracy": (tp + tn) / len(y), "sensitivity": sens, "specificity": spec, "precision": prec,
            "f1": f1, "roc_auc": float(roc_auc_score(y, prob)), "tp": tp, "fn": fn, "tn": tn, "fp": fp}


def bootstrap_ci(y, prob, groups, n=2000, seed=0):
    """Khoang tin cay 95%, lay mau lai THEO HOC SINH (giu ty le 2 lop)."""
    rng = np.random.default_rng(seed)
    by_child = collections.defaultdict(list)
    for i, g in enumerate(groups):
        by_child[g].append(i)
    pos = [g for g in by_child if y[by_child[g][0]] == 1]
    neg = [g for g in by_child if y[by_child[g][0]] == 0]
    out = collections.defaultdict(list)
    for _ in range(n):
        idx = np.concatenate([by_child[g] for g in rng.choice(pos, len(pos))] +
                             [by_child[g] for g in rng.choice(neg, len(neg))])
        m = metrics(y[idx], prob[idx])
        for k in ("accuracy", "sensitivity", "specificity", "precision", "f1", "roc_auc"):
            out[k].append(m[k])
    return {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in out.items()}


def cross_validate(EMB, HC, y, groups, seed):
    prob = np.zeros(len(y))
    for k, (tr, te) in enumerate(StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(EMB, y, groups)):
        assert not set(groups[tr]) & set(groups[te]), "hoc sinh bi lot sang ca 2 phan"
        head, scaler = fit_head(EMB, HC, y, groups, tr, seed * 10 + k)
        prob[te] = predict(head, scaler, EMB, HC, te)
    return prob


# ---------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/for_testing/model_b")
    ap.add_argument("--out-dir", default="weights")
    ap.add_argument("--report", default="model_b_cv_report.json")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123, 2024, 99])
    ap.add_argument("--cv-only", action="store_true", help="chi danh gia, khong ghi weights")
    args = ap.parse_args()

    items = load_dataset(args.data_dir)
    y = np.array([it["label"] for it in items])
    groups = np.array([it["child"] for it in items])
    print(f"Anh: {len(y)} (PD {y.sum()}, LPD {(1 - y).sum()}) | hoc sinh: PD {len(set(groups[y == 1]))}, "
          f"LPD {len(set(groups[y == 0]))}")
    EMB, HC = compute_features(items)

    probs = [cross_validate(EMB, HC, y, groups, s) for s in args.seeds]
    per_seed = [metrics(y, p) for p in probs]
    keys = ("accuracy", "sensitivity", "specificity", "precision", "f1", "roc_auc")
    main_prob = probs[0]
    report = {
        "n_images": int(len(y)), "n_children": {"PD": len(set(groups[y == 1])), "LPD": len(set(groups[y == 0]))},
        "seeds": args.seeds,
        "primary_seed": args.seeds[0],
        "primary": metrics(y, main_prob),
        "primary_ci95": bootstrap_ci(y, main_prob, groups),
        "mean_over_seeds": {k: float(np.mean([m[k] for m in per_seed])) for k in keys},
        "sd_over_seeds": {k: float(np.std([m[k] for m in per_seed])) for k in keys},
        "per_seed": per_seed,
    }
    kids = sorted(set(groups))
    child_prob = np.array([main_prob[groups == g].mean() for g in kids])
    child_y = np.array([y[groups == g][0] for g in kids])
    report["child_level"] = metrics(child_y, child_prob)
    pred = (main_prob >= 0.5).astype(int)
    report["errors"] = [{"file": items[i]["name"], "child": items[i]["child"], "sentence": items[i]["sentence"],
                         "label": int(y[i]), "prob": round(float(main_prob[i]), 3)}
                        for i in range(len(y)) if pred[i] != y[i]]
    report["accuracy_by_sentence"] = {s: float((pred == y)[[it["sentence"] == s for it in items]].mean())
                                      for s in (1, 2, 3)}
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    fmt = lambda m: " ".join(f"{k}={m[k]:.3f}" for k in keys)
    print("Kiem dinh cheo theo hoc sinh, seed", args.seeds[0], ":", fmt(report["primary"]))
    print("  CI95:", {k: [round(a, 3), round(b, 3)] for k, (a, b) in report["primary_ci95"].items()})
    print("Trung binh", len(args.seeds), "seed:", fmt(report["mean_over_seeds"]))
    print("Theo hoc sinh:", fmt(report["child_level"]))
    print("Bao cao:", args.report)

    if args.cv_only:
        return

    # Mo hinh cuoi: cung quy trinh, tren TOAN BO hoc sinh.
    head, scaler = fit_head(EMB, HC, y, groups, np.arange(len(y)), args.seeds[0])
    os.makedirs(args.out_dir, exist_ok=True)
    np.save(os.path.join(args.out_dir, "model_b_scaler_mean.npy"), scaler.mean_)
    np.save(os.path.join(args.out_dir, "model_b_scaler_scale.npy"), scaler.scale_)
    torch.save(head.state_dict(), os.path.join(args.out_dir, "model_b.pt"))
    torch.onnx.export(OnnxHead(head), (torch.zeros(1, 2048), torch.zeros(1, 2)),
                      os.path.join(args.out_dir, "model_b.onnx"),
                      input_names=["embedding", "handcrafted"], output_names=["score"],
                      dynamic_axes={"embedding": {0: "batch_size"}, "handcrafted": {0: "batch_size"},
                                    "score": {0: "batch_size"}},
                      opset_version=17, dynamo=False)
    print("Da ghi:", ", ".join(f"{args.out_dir}/{n}" for n in
                               ("model_b.onnx", "model_b.pt", "model_b_scaler_mean.npy", "model_b_scaler_scale.npy")))


if __name__ == "__main__":
    main()
