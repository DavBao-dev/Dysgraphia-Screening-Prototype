"""
evaluate_real_data.py - Danh gia tren DU LIEU THAT (data/for_testing).

- Model A: video -> MediaPipe kinematics -> RandomForest.
  Test set: data/for_testing/model_a/  (dysgraphia_V* = 1, V* = 0).
- Model B: anh -> ResNet50 embedding + 2 features -> MLP head.
  Test set: data/for_testing/model_b/  (Potential Dysgraphia = 1, Low Potential = 0).
- Fusion (A+B): can bo mau GHEP (video + anh CUNG 1 mau) de tinh majority vote;
  bo test hien tai tach rieng nen fusion per-sample khong tinh duoc.

Chay: python evaluate_real_data.py
"""
import json
import os
import numpy as np
import cv2

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from backend.ml.dysgraphia_predictor import DysgraphiaPredictor
from backend.ml import inference
from backend.ml import image_features

MODEL_A_DIR = "data/for_testing/model_a"
MODEL_B_DIR = "data/for_testing/model_b"
MAX_FRAMES_PER_VIDEO = 150
CACHE = "data/for_testing/eval_cache.json"


def extract_landmarks_capped(video_path, max_frames=MAX_FRAMES_PER_VIDEO):
    """Doc video, lay toi da ~max_frames khung co tay (de giam thoi gian chay)."""
    from mediapipe.python.solutions import hands as mp_hands

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, total // max_frames) if total > max_frames else 1

    frames = []
    idx = 0
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.4,
        min_tracking_confidence=0.4,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = hands.process(rgb)
                if res.multi_hand_landmarks:
                    lm = res.multi_hand_landmarks[0]
                    frames.append(np.array(
                        [[p.x, p.y, p.z] for p in lm.landmark], dtype=np.float64
                    ))
            idx += 1
    cap.release()

    if frames:
        return np.stack(frames), float(fps / step)
    return np.empty((0, 21, 3)), float(fps)


def iter_model_a(predictor, prior=None):
    """Chay Model A tren cac video that; skip video da co trong prior cache.

    prior: {fname: [label, risk]}. Tra ve generator (fname, label, risk).
    """
    prior = prior or {}
    for fname in sorted(os.listdir(MODEL_A_DIR)):
        if not fname.lower().endswith((".mp4", ".mov", ".avi")):
            continue
        label = 1 if fname.lower().startswith("dysgraphia") else 0
        if fname in prior:
            risk = float(prior[fname][1])
            print(f"  [cache] {fname}: risk={risk:.3f}", flush=True)
            yield fname, int(prior[fname][0]), risk
            continue
        path = os.path.join(MODEL_A_DIR, fname)
        try:
            traj, fps = extract_landmarks_capped(path)
            if traj.shape[0] < 5:
                print(f"  {fname}: khong du frame co tay ({traj.shape[0]})", flush=True)
                continue
            risk = predictor.predict_kinematics(traj, fps=fps)["risk_score"]
            print(f"  [{'DYS' if label else 'CTRL'}] {fname}: risk={risk:.3f} (frames={traj.shape[0]})", flush=True)
            yield fname, label, float(risk)
        except Exception as e:
            print(f"  {fname}: LOI {e}", flush=True)


def evaluate_model_b(backbone, head):
    """Chay Model B tren cac anh that. Tra ve [(name, label, prob)]."""
    out = []
    for cls_dir, label in (("Potential Dysgraphia", 1), ("Low Potential Dysgraphia", 0)):
        d = os.path.join(MODEL_B_DIR, cls_dir)
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            path = os.path.join(d, fname)
            with open(path, "rb") as f:
                img_bytes = f.read()
            feat = image_features.extract_ink_and_baseline_features(img_bytes)
            extra = [feat["ink_thickness_mean"], feat["baseline_deviation"]]
            _, prob = inference.run_model_b(backbone, head, img_bytes, extra_features=extra)
            out.append((fname, label, float(prob)))
    return out


def compute_metrics(labels, scores, thr=0.5):
    labels = np.asarray(labels)
    scores = np.asarray(scores)
    pred = (scores >= thr).astype(int)
    auc = roc_auc_score(labels, scores) if len(set(labels)) > 1 else float("nan")
    return {
        "accuracy": accuracy_score(labels, pred),
        "precision": precision_score(labels, pred, zero_division=0),
        "recall": recall_score(labels, pred, zero_division=0),
        "f1": f1_score(labels, pred, zero_division=0),
        "roc_auc": auc,
        "confusion": confusion_matrix(labels, pred).tolist(),
        "n": int(len(labels)),
        "pos": int(np.sum(labels)),
        "scores": scores,
        "labels": labels,
    }


def optimal_threshold(labels, scores):
    """Nguong toi uu theo Youden index (TPR - FPR) tu ROC."""
    if roc_auc_score(labels, scores) < 0.55:
        return 0.5
    fpr, tpr, thrs = roc_curve(labels, scores)
    youden = tpr - fpr
    valid = np.isfinite(thrs)
    return float(thrs[valid][int(np.argmax(youden[valid]))])


def load_or_compute(key, compute_fn, cache):
    """Doc tu cache neu co, nguoc lai tinh + luu cache."""
    if cache.get(key) is not None:
        return cache[key]
    val = compute_fn()
    cache[key] = val
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    return val


def build_paired_fusion(res_a, res_b):
    """Ghep moi anh (res_b) voi 1 video CUNG LOP (res_a) bang cach lap (cycle).

    Theo yeu cau: Low Potential Dysgraphia -> video khong co 'dysgraphia' (control),
    Potential Dysgraphia -> video co 'dysgraphia' trong ten (dysgraphic).
    """
    a_by_label = {
        0: [r for r in res_a if int(r[1]) == 0],
        1: [r for r in res_a if int(r[1]) == 1],
    }
    counts = {0: 0, 1: 0}
    pairs = []
    for _img, label, prob in res_b:
        lab = int(label)
        pool = a_by_label.get(lab, [])
        if not pool:
            continue
        _vid, _, risk = pool[counts[lab] % len(pool)]
        counts[lab] += 1
        pairs.append({"risk": float(risk), "prob": float(prob), "label": lab})
    return pairs


def fusion_label(risk, prob, thr=0.5):
    """Majority vote; tie -> trung binh xac suat (nhu app.py)."""
    a = 1 if risk >= thr else 0
    b = 1 if prob >= thr else 0
    if a == b:
        return a
    return 1 if (risk + prob) / 2 >= thr else 0


def evaluate_fusion(pairs, thr=0.5):
    labels = [p["label"] for p in pairs]
    scores = [(p["risk"] + p["prob"]) / 2 for p in pairs]
    preds = [fusion_label(p["risk"], p["prob"], thr) for p in pairs]
    return compute_metrics(labels, scores, preds)


def main():
    cache = {}
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    print("=== [1/2] DANH GIA MODEL A (video that) ===")
    predictor = DysgraphiaPredictor.load("weights/writesense_model_a.joblib")
    prior_a = cache.get("model_a")
    if isinstance(prior_a, list):  # migrate dinh dang cu: [[name, label, risk], ...]
        prior_a = {r[0]: [int(r[1]), float(r[2])] for r in prior_a}
    prior_a = prior_a if isinstance(prior_a, dict) else {}
    res_a = []
    for _fname, _label, _risk in iter_model_a(predictor, prior_a):
        res_a.append((_fname, _label, _risk))
        prior_a[_fname] = [int(_label), float(_risk)]
        cache["model_a"] = prior_a
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    m_a = compute_metrics([r[1] for r in res_a], [r[2] for r in res_a])
    print(f"  Mau: {m_a['n']} (dysgraphic={m_a['pos']}, control={m_a['n'] - m_a['pos']})")
    for r in res_a:
        tag = "DYS" if r[1] == 1 else "CTRL"
        print(f"  [{tag}] {r[0]}: risk={r[2]:.3f}")

    print("\n=== [2/2] DANH GIA MODEL B (anh that) ===")
    backbone = inference.load_resnet50_backbone()
    head = inference.load_model_b_head("weights/model_b.pt")
    res_b = load_or_compute("model_b", lambda: evaluate_model_b(backbone, head), cache)
    m_b = compute_metrics([r[1] for r in res_b], [r[2] for r in res_b])
    print(f"  Mau: {m_b['n']} (dysgraphic={m_b['pos']}, control={m_b['n'] - m_b['pos']})")

    print("\n================= KET QUA (nguong mac dinh 0.5) =================")
    for name, m in (("Model A only", m_a), ("Model B only", m_b)):
        print(f"--- {name} (n={m['n']}) ---")
        print(f"  Accuracy : {m['accuracy']:.3f}")
        print(f"  Precision: {m['precision']:.3f}")
        print(f"  Recall   : {m['recall']:.3f}")
        print(f"  F1       : {m['f1']:.3f}")
        print(f"  ROC-AUC  : {m['roc_auc']:.3f}")
        print(f"  Confusion [TN FP; FN TP]: {m['confusion']}")

    print("\n=== FUSION (A+B) - ghep anh voi video CUNG LOP ===")
    print("Low Potential Dysgraphia -> video KHONG co 'dysgraphia' (control)")
    print("Potential Dysgraphia     -> video CO 'dysgraphia' trong ten (dysgraphic)")
    pairs = build_paired_fusion(res_a, res_b)
    m_f = evaluate_fusion(pairs)
    print(f"  Mau ghep: {m_f['n']} (dysgraphic={m_f['pos']}, control={m_f['n'] - m_f['pos']})")
    print(f"  [nguong 0.5] Accuracy={m_f['accuracy']:.3f} Precision={m_f['precision']:.3f} "
          f"Recall={m_f['recall']:.3f} F1={m_f['f1']:.3f} AUC={m_f['roc_auc']:.3f}")
    print(f"  Confusion [TN FP; FN TP]: {m_f['confusion']}")

    # TAI NGUONG TOI UU (so sanh cong bang hon)
    m_a_opt = compute_metrics(m_a["labels"], m_a["scores"],
                              optimal_threshold(m_a["labels"], m_a["scores"]))
    m_b_opt = compute_metrics(m_b["labels"], m_b["scores"],
                              optimal_threshold(m_b["labels"], m_b["scores"]))
    m_f_opt = compute_metrics(m_f["labels"], m_f["scores"],
                              optimal_threshold(m_f["labels"], m_f["scores"]))
    thr_f = optimal_threshold(m_f["labels"], m_f["scores"])

    print("\n=== TAI NGUONG TOI UU (Youden) ===")
    print(f"  Nguong: A={optimal_threshold(m_a['labels'], m_a['scores']):.3f}, "
          f"B={optimal_threshold(m_b['labels'], m_b['scores']):.3f}, Fusion={thr_f:.3f}")
    header = f"{'Chi so':<12}{'Model A':>16}{'Model B':>16}{'Fusion':>16}"
    print(header)
    print("-" * len(header))
    for k, lab in (("accuracy", "Accuracy"), ("precision", "Precision"),
                   ("recall", "Recall"), ("f1", "F1"), ("roc_auc", "ROC-AUC")):
        row = [f"{mm[k]:.3f}" for mm in (m_a_opt, m_b_opt, m_f_opt)]
        print(f"{lab:<12}{row[0]:>16}{row[1]:>16}{row[2]:>16}")

    try:
        import matplotlib.pyplot as plt
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        plt.style.use("ggplot")

    keys = ("accuracy", "precision", "recall", "f1", "roc_auc")
    labels_plot = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    x = np.arange(len(keys))
    w = 0.26
    fig, ax = plt.subplots(figsize=(10, 5.5))
    b1 = ax.bar(x - w, [m_a_opt[k] for k in keys], w,
                label="Model A only", color="#4C72B0", edgecolor="black")
    b2 = ax.bar(x, [m_b_opt[k] for k in keys], w,
                label="Model B only", color="#DD8452", edgecolor="black")
    b3 = ax.bar(x + w, [m_f_opt[k] for k in keys], w,
                label="Fusion A+B", color="#55A868", edgecolor="black")
    for bars, m in ((b1, m_a_opt), (b2, m_b_opt), (b3, m_f_opt)):
        for b, k in zip(bars, keys):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02,
                    f"{m[k]:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels_plot)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Gia tri")
    ax.set_title("Danh gia tren DU LIEU THAT: Model A vs Model B vs Fusion A+B")
    ax.legend()
    fig.tight_layout()
    fig.savefig("evaluation_real_data.png", dpi=150)
    print("\nDa luu bieu do: evaluation_real_data.png")


if __name__ == "__main__":
    main()

