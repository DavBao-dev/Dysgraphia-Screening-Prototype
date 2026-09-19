# backend/services/ensemble_service.py
def combine(model_a, model_b):
    if model_a is None and model_b is None:
        raise ValueError(
            "Kh\u00f4ng c\u00f3 m\u00f4 h\u00ecnh n\u00e0o c\u00f3 k\u1ebft qu\u1ea3 \u0111\u1ec3 t\u1ed5ng h\u1ee3p."
        )
    out_a = model_a["prediction"] if model_a else None
    prob_a = model_a["score"] if model_a else None
    out_b = model_b["prediction"] if model_b else None
    prob_b = model_b["score"] if model_b else None

    outputs = [(o, p) for o, p in ((out_a, prob_a), (out_b, prob_b)) if o is not None]
    ones = sum(1 for o, _ in outputs if o == 1)
    zeros = sum(1 for o, _ in outputs if o == 0)
    if ones > zeros:
        final_out, vote_kind = 1, "majority"
    elif zeros > ones:
        final_out, vote_kind = 0, "majority"
    else:
        probs = [p for _, p in outputs if p is not None]
        avg = sum(probs) / len(probs) if probs else 0.5
        final_out, vote_kind = (1 if avg >= 0.5 else 0), "tie -> avg prob"
    return {"prediction": final_out, "method": f"majority_vote ({vote_kind})"}