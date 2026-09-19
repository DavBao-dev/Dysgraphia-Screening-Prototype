"""plot_per_video.py - Bieu do rieng cho tung video (Model A).

Doc ket qua tu data/for_testing/eval_cache.json (da duoc evaluate_real_data.py
tinh va luu), ve:

1. `model_a_per_video.png`  - Risk score cua tung video, to mau theo nhan
   (dysgraphia = do, control = xanh), kem duong nguong 0.5.
2. `roc_curves.png`         - ROC cua Model A / Model B / Fusion A+B.

Chay:  python plot_per_video.py
"""
import json
import os

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

CACHE = "data/for_testing/eval_cache.json"
THRESHOLD = 0.5


def load_cache():
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def plot_per_video(model_a: dict) -> str:
    """Bar chart: risk score cua tung video, mau theo nhan that."""
    names = sorted(model_a.keys())
    labels = [int(model_a[n][0]) for n in names]
    risks = [float(model_a[n][1]) for n in names]

    fig, ax = plt.subplots(figsize=(14, 6))
    colors = ["#C44E52" if lab == 1 else "#55A868" for lab in labels]
    bars = ax.bar(range(len(names)), risks, color=colors, edgecolor="black", linewidth=0.5)

    ax.axhline(THRESHOLD, color="black", linestyle="--", linewidth=1.2,
               label=f"threshold = {THRESHOLD}")

    for i, r in enumerate(risks):
        ax.text(i, r + 0.015, f"{r:.2f}", ha="center", fontsize=8)

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace(".mp4", "") for n in names], rotation=45, ha="right", fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Risk score (P(dysgraphia))")
    ax.set_title("Model A - Risk score tung video (do = dysgraphia that, xanh = control)")
    ax.legend(loc="upper left")

    # legend mau
    import matplotlib.patches as mpatches
    handles = [
        mpatches.Patch(color="#C44E52", label="dysgraphia (that)"),
        mpatches.Patch(color="#55A868", label="control (that)"),
    ]
    ax.legend(handles=handles + [ax.get_legend_handles_labels()[0][0]], loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    out = "model_a_per_video.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Da luu: {out}")
    return out


def plot_roc(model_a: dict, model_b: list) -> str:
    """ROC curves cho A / B / Fusion A+B (paired theo cach cua evaluate_real_data.py)."""
    a_names = sorted(model_a.keys())
    a_labels = np.array([int(model_a[n][0]) for n in a_names])
    a_scores = np.array([float(model_a[n][1]) for n in a_names])

    b_labels = np.array([int(r[1]) for r in model_b])
    b_scores = np.array([float(r[2]) for r in model_b])

    # Fusion: ghep moi anh voi 1 video cung lop (lap vong) -> diem = (risk+prob)/2
    a_by_label = {
        0: [float(model_a[n][1]) for n in a_names if int(model_a[n][0]) == 0],
        1: [float(model_a[n][1]) for n in a_names if int(model_a[n][0]) == 1],
    }
    counts = {0: 0, 1: 0}
    f_scores = []
    for _name, lab, prob in model_b:
        pool = a_by_label.get(int(lab), [])
        if not pool:
            continue
        risk = pool[counts[int(lab)] % len(pool)]
        counts[int(lab)] += 1
        f_scores.append((float(risk) + float(prob)) / 2.0)
    f_labels = np.array([int(r[1]) for r in model_b[: len(f_scores)]])
    f_scores = np.array(f_scores)

    fig, ax = plt.subplots(figsize=(7, 6))
    for name, lab, sco, color, ls in (
        ("Model A", a_labels, a_scores, "#4C72B0", "-"),
        ("Model B", b_labels, b_scores, "#DD8452", "-"),
        ("Fusion A+B", f_labels, f_scores, "#55A868", "-"),
    ):
        fpr, tpr, _ = roc_curve(lab, sco)
        auc = roc_auc_score(lab, sco)
        ax.plot(fpr, tpr, color=color, linestyle=ls, label=f"{name} (AUC={auc:.3f})")

    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC - Model A vs Model B vs Fusion A+B")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()

    out = "roc_curves.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"Da luu: {out}")
    return out


def main():
    cache = load_cache()
    model_a = cache.get("model_a")
    model_b = cache.get("model_b")
    if not isinstance(model_a, dict):
        raise SystemExit("Khong co 'model_a' trong cache (chay evaluate_real_data.py truoc).")
    if not isinstance(model_b, list):
        raise SystemExit("Khong co 'model_b' trong cache (chay evaluate_real_data.py truoc).")

    plot_per_video(model_a)
    plot_roc(model_a, model_b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
