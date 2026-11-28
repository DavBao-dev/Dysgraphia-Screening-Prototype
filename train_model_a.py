"""
train_model_a.py - Danh gia va huan luyen lai Model A (chuyen dong tay) tren video THAT, bang DUNG
pipeline cua app.

Du lieu: cac video .mp4 trong --data-dir. Nhan suy ra tu ten file:
    *_dys.mp4 hoac dysgraphia_*.mp4  -> nhan 1 (co dau hieu)
    con lai                          -> nhan 0 (doi chung)

Pipeline (giong het backend/services/model_a_service.py):
    video -> model_a_adapter.extract_landmarks_from_video (MediaPipe, chi giu frame co ban tay)
          -> movement gate (adaptive_smooth_keypoints + is_stationary_motion)
          -> extract_basic_features (18 dac trung) -> bo "fps" va "num_frames"
          -> RandomForest

Bo fps va num_frames vi model cu phu thuoc vao fps (dac trung quan trong nhat, ~38%): diem nguy co chay
theo cach quay video thay vi theo chuyen dong tay. DysgraphiaPredictor van tinh du 18 dac trung roi chi
lay cac cot model can, nen app nap model moi khong can sua code.

Danh gia: kiem dinh cheo bo-mot-nhom (LeaveOneGroupOut). Cac clip cat tu cung mot video goc nam chung
mot nhom (V003_1..5; 6 clip *_dys cat tu 2 video lon, xem DYS_SOURCES), de model khong duoc kiem tra
tren chinh doan video no da hoc. Lap lai voi nhieu seed.

Chay:
    python train_model_a.py --cv-only   # chi danh gia
    python train_model_a.py             # danh gia + ghi weights/writesense_model_a.joblib
"""
import argparse
import glob
import json
import os
import re

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut

from backend.config import MIN_MODEL_A_FRAMES, MODEL_A_WEIGHTS
from backend.ml import model_a_adapter
from backend.ml.dysgraphia_predictor import BASIC_FEATURE_COLUMNS, DysgraphiaPredictor, extract_basic_features
from backend.ml.model_a_dysgraphia import adaptive_smooth_keypoints, is_stationary_motion

DROPPED = ["num_frames", "fps"]
FEATURES = [c for c in BASIC_FEATURE_COLUMNS if c not in DROPPED]

# 6 clip dysgraphia cat tu 2 video 4K lon (dysgraphia_V001.mp4 53.8s, dysgraphia_V003.mp4 34.8s), da
# doi chieu bang so khop khung hinh. Chi la 2 ban ghi, nen moi ban ghi la mot nhom.
DYS_SOURCES = {
    "V001_dys": "dys_V001", "V002_dys": "dys_V001", "V003_dys": "dys_V001",
    "V004_dys": "dys_V003", "V005_dys": "dys_V003", "V006_dys": "dys_V003",
}


def label_of(stem):
    return 1 if stem.endswith("_dys") or stem.startswith("dysgraphia_") else 0


def group_of(stem):
    if stem in DYS_SOURCES:
        return DYS_SOURCES[stem]
    return re.sub(r"_\d+$", "", stem)  # V003_1..V003_5 -> V003


def extract(data_dir, cache):
    if cache and os.path.exists(cache):
        print(f"Dung lai dac trung da luu: {cache}")
        return pd.read_csv(cache)
    rows = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.mp4"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        landmarks, fps = model_a_adapter.extract_landmarks_from_video(path)
        row = {"clip": stem, "label": label_of(stem), "group": group_of(stem), "hand_frames": len(landmarks)}
        if len(landmarks) < MIN_MODEL_A_FRAMES:
            row["status"] = "too_few_frames"
        elif is_stationary_motion(adaptive_smooth_keypoints(np.asarray(landmarks, dtype=np.float64))):
            row["status"] = "stationary"
        else:
            row["status"] = "OK"
            row.update(extract_basic_features(landmarks, fps=fps))
        print(f"  {stem:16s} nhan={row['label']} nhom={row['group']:9s} frames={row['hand_frames']:5d} {row['status']}")
        rows.append(row)
    df = pd.DataFrame(rows)
    if cache:
        df.to_csv(cache, index=False)
    return df


def make_rf(seed):
    # Rat it du lieu: cay nong + la toi thieu 2 mau de bot hoc thuoc.
    return RandomForestClassifier(n_estimators=300, max_depth=4, min_samples_leaf=2,
                                  class_weight="balanced", random_state=seed, n_jobs=-1)


def metrics(y, p, thr=0.5):
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "auc": round(float(roc_auc_score(y, p)), 3) if len(set(y)) == 2 else None,
        "accuracy": round(float((tp + tn) / len(y)), 3),
        "sensitivity": round(float(tp / (tp + fn)), 3) if tp + fn else None,
        "specificity": round(float(tn / (tn + fp)), 3) if tn + fp else None,
        "confusion_tn_fp_fn_tp": [int(tn), int(fp), int(fn), int(tp)],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data/for_testing/model_a")
    ap.add_argument("--cache", default="data/for_testing/model_a_features.csv")
    ap.add_argument("--out", default=str(MODEL_A_WEIGHTS))
    ap.add_argument("--report", default="model_a_cv_report.json")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 7, 123, 2024, 99])
    ap.add_argument("--cv-only", action="store_true")
    args = ap.parse_args()

    df = extract(args.data_dir, args.cache)
    skipped = df[df["status"] != "OK"]
    df = df[df["status"] == "OK"].reset_index(drop=True)
    X, y, groups = df[FEATURES].to_numpy(dtype=np.float64), df["label"].to_numpy(), df["group"].to_numpy()
    print(f"\n{len(df)} clip dung duoc ({int(y.sum())} dys / {int((y == 0).sum())} doi chung), "
          f"{df['group'].nunique()} nhom; bo qua {len(skipped)}: {list(skipped['clip'])}")

    # Kiem dinh cheo bo-mot-nhom, trung binh xac suat qua cac seed.
    oof = np.zeros((len(args.seeds), len(df)))
    for s, seed in enumerate(args.seeds):
        for tr, te in LeaveOneGroupOut().split(X, y, groups):
            if len(set(y[tr])) < 2:
                oof[s, te] = 0.5
                continue
            oof[s, te] = make_rf(seed).fit(pd.DataFrame(X[tr], columns=FEATURES), y[tr]).predict_proba(
                pd.DataFrame(X[te], columns=FEATURES))[:, 1]
    df["p_new_cv"] = oof.mean(axis=0)

    # Model hien tai (18 dac trung, co fps) tren cung cac clip, de so sanh.
    old = DysgraphiaPredictor.load(str(MODEL_A_WEIGHTS))
    df["p_old"] = old.predict_proba(df[BASIC_FEATURE_COLUMNS])

    report = {
        "features": FEATURES,
        "dropped": DROPPED,
        "n_clips": int(len(df)), "n_dys": int(y.sum()), "n_groups": int(df["group"].nunique()),
        "skipped": skipped[["clip", "status"]].to_dict("records"),
        "new_model_group_cv": metrics(y, df["p_new_cv"].to_numpy()),
        "old_model_same_clips": metrics(y, df["p_old"].to_numpy()),
        "per_clip": df[["clip", "label", "group", "hand_frames", "p_new_cv", "p_old"]].round(3).to_dict("records"),
    }

    if not args.cv_only:
        final = DysgraphiaPredictor(model=make_rf(42)).fit(df[FEATURES], y)
        imp = sorted(zip(final.model.feature_importances_, FEATURES), reverse=True)
        report["feature_importance"] = {n: round(float(v), 3) for v, n in imp}
        final.save(args.out)
        print(f"Da ghi model moi: {args.out}")

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nclip              nhan  nhom       P(moi, CV)  P(cu)")
    for r in report["per_clip"]:
        print(f"  {r['clip']:16s} {r['label']}    {r['group']:9s}  {r['p_new_cv']:.3f}       {r['p_old']:.3f}")
    print("\nModel moi (CV theo nhom):", report["new_model_group_cv"])
    print("Model cu (cung clip):    ", report["old_model_same_clips"])
    if "feature_importance" in report:
        print("Dac trung quan trong nhat:", list(report["feature_importance"].items())[:5])
    print(f"Bao cao: {args.report}")


if __name__ == "__main__":
    main()
