"""
Turns the biomechanical features produced by :mod:`model_a_dysgraphia` into a
single *dysgraphia probability* (a ``float`` in ``[0, 1]``) using a tabular
classifier (Random Forest by default; any scikit-learn / XGBoost style
estimator with ``predict_proba`` can be substituted).

The number is ``P(dysgraphia)``: ``0.0`` = clearly not dysgraphic,
``1.0`` = clearly dysgraphic. A ``threshold`` (default ``0.5``) maps it to a
hard label.

NOTE
----
A probability is only as good as the labelled data the model was trained on.
This module provides the complete, production-ready scaffolding (train /
predict / persist). Before clinical use you must train it on a real, labelled
dataset of handwriting kinematics from diagnosed and non-diagnosed subjects.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional, Sequence, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from model_a_dysgraphia import (
    EnhancedKinematicFeatureExtractor,
    HandLandmarkRecorder,
    KinematicFeatureExtractor,
    adaptive_smooth_keypoints,
    is_stationary_motion,
)

__all__ = [
    "BASIC_FEATURE_COLUMNS",
    "ADVANCED_FEATURE_COLUMNS",
    "FEATURE_COLUMNS",
    "DysgraphiaPredictor",
    "extract_basic_features",
    "extract_all_features",
    "main",
]

# The 18 "basic" clinical features produced by KinematicFeatureExtractor. This is
# the schema used by the synthetic-data generator and the Kaggle training script.
BASIC_FEATURE_COLUMNS: List[str] = [
    "num_frames",
    "fps",
    "speed_mean",
    "speed_max",
    "speed_std",
    "acceleration_mean",
    "acceleration_max",
    "acceleration_std",
    "jerk_mean",
    "jerk_max",
    "jerk_std",
    "wrist_flexion_angle_mean",
    "wrist_flexion_angle_std",
    "in_air_pause_ratio",
    "tremor_peak_frequency_hz",
    "tremor_peak_amplitude",
    "pinch_distance_std",
    "pinch_distance_mean",
]

# Extra "advanced" biomechanical features from EnhancedKinematicFeatureExtractor.
ADVANCED_FEATURE_COLUMNS: List[str] = [
    "mean_speed",
    "std_speed",
    "mean_jerk",
    "max_jerk",
    "normalized_jerk",
    "nvc_per_second",
    "spectral_entropy",
    "tremor_power_ratio",
    "pincer_correlation",
    "wrist_drift_rate",
]

# Full merged schema (28 features) for models trained on both extractors.
FEATURE_COLUMNS: List[str] = BASIC_FEATURE_COLUMNS + ADVANCED_FEATURE_COLUMNS


def extract_basic_features(
    landmarks: np.ndarray,
    fps: float = 30.0,
    pause_threshold: float = 0.005,
    tremor_band: tuple = (3.0, 8.0),
) -> Dict[str, float]:
    """Run the basic extractor and return the 18 clinical features (in order).

    This matches the schema used by the synthetic-data CSV and by models trained
    on ``KinematicFeatureExtractor`` output alone.
    """
    features = KinematicFeatureExtractor(
        fps=fps, pause_threshold=pause_threshold, tremor_band=tremor_band
    ).extract(landmarks)
    return {col: features[col] for col in BASIC_FEATURE_COLUMNS}


def extract_all_features(
    landmarks: np.ndarray,
    fps: float = 30.0,
    pause_threshold: float = 0.005,
    tremor_band: tuple = (3.0, 8.0),
) -> Dict[str, float]:
    """Run both extractors on ``(T, 21, 3)`` landmarks and merge into one vector.

    The returned dict has exactly the :data:`FEATURE_COLUMNS` keys, in order,
    ready to feed :class:`DysgraphiaPredictor`.
    """
    basic = KinematicFeatureExtractor(
        fps=fps, pause_threshold=pause_threshold, tremor_band=tremor_band
    ).extract(landmarks)

    advanced = EnhancedKinematicFeatureExtractor(fps=fps).extract_features(landmarks)

    merged: Dict[str, float] = dict(basic)
    merged.update(advanced)
    # Keep the configurable-threshold pause ratio from the basic extractor.
    merged["in_air_pause_ratio"] = basic["in_air_pause_ratio"]

    return {col: merged[col] for col in FEATURE_COLUMNS}


class DysgraphiaPredictor:
    """Predict a dysgraphia probability in ``[0, 1]`` from extracted features.

    Parameters
    ----------
    model:
        A classifier with ``fit``/``predict_proba`` (e.g. ``RandomForestClassifier``,
        ``XGBClassifier``). Defaults to a balanced Random Forest.
    feature_columns:
        Ordered feature names the model expects. Inferred automatically when
        ``fit`` receives a ``DataFrame``; required otherwise.
    threshold:
        Probability above which a sample is labelled dysgraphic (1).
    random_state:
        Seed for reproducibility when the default model is built.

    Examples
    --------
    >>> predictor = DysgraphiaPredictor().fit(X_train, y_train)
    >>> score = predictor.predict(features_dict)       # float in [0, 1]
    >>> label = predictor.predict_label(features_dict)  # 0 or 1
    """

    def __init__(
        self,
        model: Any = None,
        feature_columns: Optional[Sequence[str]] = None,
        threshold: float = 0.5,
        random_state: int = 42,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {threshold!r}.")
        self.threshold = float(threshold)
        self.random_state = random_state
        self.feature_columns = list(feature_columns) if feature_columns is not None else None
        self.model = model if model is not None else RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        )

    # ------------------------------------------------------------------ training
    def fit(self, features: Union[pd.DataFrame, np.ndarray], labels) -> "DysgraphiaPredictor":
        """Train the model on ``features`` and binary ``labels`` (0/1)."""
        if isinstance(features, pd.DataFrame):
            self.feature_columns = list(features.columns)
            X = features.to_numpy(dtype=np.float64)
        else:
            X = np.asarray(features, dtype=np.float64)
            if self.feature_columns is None:
                raise ValueError(
                    "feature_columns must be provided when features is not a DataFrame."
                )
            if X.ndim == 2 and X.shape[1] != len(self.feature_columns):
                raise ValueError(
                    f"Expected {len(self.feature_columns)} feature columns, got {X.shape[1]}."
                )

        y = np.asarray(labels).ravel()
        if X.shape[0] != y.shape[0]:
            raise ValueError(f"Mismatched samples: {X.shape[0]} features vs {y.shape[0]} labels.")
        if not set(np.unique(y)).issubset({0, 1}):
            raise ValueError(f"labels must be binary (0/1), got {sorted(set(np.unique(y)))}.")
        if X.shape[0] == 0:
            raise ValueError("No training samples provided.")

        self.model.fit(X, y)
        return self


    # ----------------------------------------------------------------- inference
    def predict_proba(self, features: Union[pd.DataFrame, Dict, np.ndarray]) -> np.ndarray:
        """Return ``P(dysgraphia)`` for each sample as a ``(n,)`` array in ``[0, 1]``."""
        X = self._as_matrix(features)
        # Attach feature names when the model was fitted on a DataFrame so that
        # scikit-learn validates column order by name (not just position).
        if hasattr(self.model, "feature_names_in_"):
            X = pd.DataFrame(X, columns=self.feature_columns)
        proba = self.model.predict_proba(X)
        if proba.ndim == 2 and proba.shape[1] == 2:
            return proba[:, 1]
        return np.full(X.shape[0], 0.0)  # degenerate single-class model

    def predict(self, features: Union[pd.DataFrame, Dict, np.ndarray]) -> float:
        """Return the dysgraphia probability as a single ``float`` in ``[0, 1]``.

        Expects exactly one sample; use :meth:`predict_proba` for batches.
        """
        probs = self.predict_proba(features)
        if probs.shape[0] != 1:
            raise ValueError(
                f"predict() expects a single sample, got {probs.shape[0]}. "
                "Use predict_proba() for batches."
            )
        return float(probs[0])

    def predict_label(self, features: Union[pd.DataFrame, Dict, np.ndarray]) -> int:
        """Return the hard label (0/1) for a single sample using ``threshold``."""
        return int(self.predict(features) >= self.threshold)

    def predict_batch(self, features: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Return hard labels (0/1) for multiple samples."""
        return (self.predict_proba(features) >= self.threshold).astype(int)

    def predict_from_landmarks(self, landmarks: np.ndarray, fps: float = 30.0) -> float:
        """Extract features from raw ``(T, 21, 3)`` landmarks and return ``P(dysgraphia)``.

        Only the features the model actually needs are computed: the 18 basic
        features for a basic-schema model, the full merged vector otherwise.
        """
        if self.feature_columns is not None and set(self.feature_columns).issubset(
            BASIC_FEATURE_COLUMNS
        ):
            features = extract_basic_features(landmarks, fps=fps)
        else:
            features = extract_all_features(landmarks, fps=fps)
        return self.predict(features)

    def predict_kinematics(
        self,
        landmarks: np.ndarray,
        fps: float = 30.0,
    ) -> Dict[str, Any]:
        """Smooth keypoints -> movement gate -> extract features -> predict.

        Returns a dict::

            {
                "risk_score": float,   # in [0, 1]
                "status": str,         # "OK" or "Hand Stationary / Contracted Pose"
                "features": dict,      # zeroed when stationary
            }

        The movement gate rejects stationary *and* contracted/static poses
        (low max speed + short path length), so MediaPipe jitter is never
        scored as dysgraphia.
        """
        landmarks = np.asarray(landmarks, dtype=np.float64)

        # Movement activity gate (adaptive smoothing first, so a contracted
        # hand's stronger jitter is flattened before checking speed/path).
        smoothed = adaptive_smooth_keypoints(landmarks)
        if is_stationary_motion(smoothed):
            cols = self.feature_columns if self.feature_columns is not None else FEATURE_COLUMNS
            return {
                "risk_score": 0.0,
                "status": "Hand Stationary / Contracted Pose",
                "features": {col: 0.0 for col in cols},
            }

        # Normal path: extract features (extractors smooth internally) + predict.
        if self.feature_columns is not None and set(self.feature_columns).issubset(
            BASIC_FEATURE_COLUMNS
        ):
            features = extract_basic_features(landmarks, fps=fps)
        else:
            features = extract_all_features(landmarks, fps=fps)

        return {
            "risk_score": float(self.predict(features)),
            "status": "OK",
            "features": features,
        }

    # ----------------------------------------------------------------- persistence
    def save(self, path: str) -> None:
        """Persist model, feature schema and threshold to ``path`` (joblib)."""
        joblib.dump(
            {
                "model": self.model,
                "feature_columns": self.feature_columns,
                "threshold": self.threshold,
            },
            path,
        )

    @classmethod
    def from_sklearn(
        cls,
        model_path: str,
        feature_columns: Optional[Sequence[str]] = None,
        threshold: float = 0.5,
    ) -> "DysgraphiaPredictor":
        """Load a raw scikit-learn model saved with ``joblib.dump``.

        ``feature_columns`` defaults to :data:`BASIC_FEATURE_COLUMNS` (the 18
        clinical features used by the synthetic-data training pipeline).
        """
        model = joblib.load(model_path)
        columns = feature_columns if feature_columns is not None else BASIC_FEATURE_COLUMNS
        return cls(model=model, feature_columns=columns, threshold=threshold)

    @classmethod
    def load(cls, path: str) -> "DysgraphiaPredictor":
        """Load a predictor saved with :meth:`save`, or a raw scikit-learn model.

        Files written by :meth:`save` contain a dict (model + schema + threshold).
        A bare ``joblib.dump`` of an estimator (e.g. a ``RandomForestClassifier``
        from the Kaggle training script) is also accepted and assumed to use the
        18-feature basic schema.
        """
        payload = joblib.load(path)
        if isinstance(payload, dict) and "model" in payload:
            return cls(
                model=payload["model"],
                feature_columns=payload["feature_columns"],
                threshold=payload["threshold"],
            )
        return cls(model=payload, feature_columns=BASIC_FEATURE_COLUMNS)

    # ------------------------------------------------------------------ internals
    def _as_matrix(self, features: Union[pd.DataFrame, Dict, np.ndarray]) -> np.ndarray:
        if self.feature_columns is None:
            raise RuntimeError("Model is not fitted; call fit() first (or pass feature_columns).")

        if isinstance(features, pd.DataFrame):
            missing = sorted(set(self.feature_columns) - set(features.columns))
            if missing:
                raise ValueError(f"Missing feature columns: {missing}")
            return features[self.feature_columns].to_numpy(dtype=np.float64)

        if isinstance(features, dict):
            missing = sorted(set(self.feature_columns) - set(features))
            if missing:
                raise ValueError(f"Missing feature keys: {missing}")
            return np.array([[features[c] for c in self.feature_columns]], dtype=np.float64)

        arr = np.asarray(features, dtype=np.float64)
        if arr.ndim == 1:
            if arr.shape[0] != len(self.feature_columns):
                raise ValueError(
                    f"Expected {len(self.feature_columns)} features, got {arr.shape[0]}."
                )
            arr = arr.reshape(1, -1)
        elif arr.ndim == 2 and arr.shape[1] != len(self.feature_columns):
            raise ValueError(
                f"Expected {len(self.feature_columns)} feature columns, got {arr.shape[1]}."
            )
        return arr


def _make_demo_dataset(n_per_class: int = 250, seed: int = 42):
    """Build a SYNTHETIC labelled feature table (demonstration only).

    The data is invented purely to exercise the train -> predict -> [0, 1]
    flow and has **no clinical validity**. Real training requires labelled
    recordings from diagnosed and non-diagnosed subjects.
    """
    rng = np.random.default_rng(seed)

    def r(n, mu, sd, lo, hi):
        return np.clip(rng.normal(mu, sd, n), lo, hi)

    def build(is_case):
        d = 1.0 if is_case else 0.0  # inject a consistent "dysgraphic" signal
        n = n_per_class
        return pd.DataFrame(
            {
                "num_frames": np.full(n, 150.0),
                "fps": np.full(n, 60.0),
                "speed_mean": r(n, 0.30 - 0.10 * d, 0.08, 0.0, 1.0),
                "speed_max": r(n, 0.60 - 0.15 * d, 0.15, 0.0, 2.0),
                "speed_std": r(n, 0.10 - 0.03 * d, 0.03, 0.0, 1.0),
                "acceleration_mean": r(n, 2.0 + 1.5 * d, 0.6, 0.0, 20.0),
                "acceleration_max": r(n, 5.0 + 3.0 * d, 1.5, 0.0, 40.0),
                "acceleration_std": r(n, 1.2 + 0.8 * d, 0.4, 0.0, 15.0),
                "jerk_mean": r(n, 20.0 + 25.0 * d, 8.0, 0.0, 300.0),
                "jerk_max": r(n, 50.0 + 60.0 * d, 20.0, 0.0, 800.0),
                "jerk_std": r(n, 15.0 + 18.0 * d, 6.0, 0.0, 250.0),
                "wrist_flexion_angle_mean": r(n, 150.0 - 20.0 * d, 15.0, 0.0, 180.0),
                "wrist_flexion_angle_std": r(n, 8.0 + 6.0 * d, 3.0, 0.0, 60.0),
                "in_air_pause_ratio": r(n, 0.10 + 0.25 * d, 0.08, 0.0, 1.0),
                "tremor_peak_frequency_hz": r(n, 4.5 + 1.0 * d, 1.2, 3.0, 8.0),
                "tremor_peak_amplitude": r(n, 0.02 + 0.04 * d, 0.015, 0.0, 0.3),
                "pinch_distance_std": r(n, 0.05 + 0.04 * d, 0.02, 0.0, 0.5),
                "pinch_distance_mean": r(n, 0.12, 0.04, 0.0, 0.6),
                "mean_speed": r(n, 0.30 - 0.10 * d, 0.08, 0.0, 1.0),
                "std_speed": r(n, 0.10 - 0.03 * d, 0.03, 0.0, 1.0),
                "mean_jerk": r(n, 20.0 + 25.0 * d, 8.0, 0.0, 300.0),
                "max_jerk": r(n, 50.0 + 60.0 * d, 20.0, 0.0, 800.0),
                "normalized_jerk": r(n, 40.0 + 80.0 * d, 20.0, 0.0, 1000.0),
                "nvc_per_second": r(n, 8.0 + 6.0 * d, 3.0, 0.0, 40.0),
                "spectral_entropy": r(n, 6.0 + 1.0 * d, 0.8, 0.0, 12.0),
                "tremor_power_ratio": r(n, 0.15 + 0.25 * d, 0.10, 0.0, 1.0),
                "pincer_correlation": r(n, 0.6 - 0.3 * d, 0.2, -1.0, 1.0),
                "wrist_drift_rate": r(n, 0.02 + 0.03 * d, 0.015, 0.0, 0.3),
            }
        )[FEATURE_COLUMNS]

    controls = build(False)
    cases = build(True)
    X = pd.concat([controls, cases], ignore_index=True)
    y = np.array([0] * n_per_class + [1] * n_per_class, dtype=int)
    return X, y


def _run_demo(seed: int = 42) -> int:
    X, y = _make_demo_dataset(seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=seed
    )
    predictor = DysgraphiaPredictor(random_state=seed).fit(X_train, y_train)

    probs = predictor.predict_proba(X_test)
    labels = (probs >= predictor.threshold).astype(int)
    print("Synthetic demo (NOT clinically valid):")
    print(f"  train samples: {len(X_train)}, test samples: {len(X_test)}")
    print(f"  test accuracy: {accuracy_score(y_test, labels):.3f}")
    print(f"  ROC AUC:       {roc_auc_score(y_test, probs):.3f}")

    sample = X_test.iloc[[0]]
    score = predictor.predict(sample)
    print(f"\n  example sample -> P(dysgraphia) = {score:.4f} "
          f"(true={int(y_test[0])}, predicted={predictor.predict_label(sample)})")
    return 0


def _predict_live(model_path: str, source: Union[int, str], fps_override: Optional[float]) -> int:
    predictor = DysgraphiaPredictor.load(model_path)
    recorder = HandLandmarkRecorder(source=source)
    print("Recording -- press 'q' in the video window to stop and predict.")
    trajectory, fps = recorder.run()

    if trajectory.shape[0] < 15:
        print("Not enough frames with a detected hand (need >= 15).")
        return 1

    effective_fps = fps_override if fps_override else fps
    score = predictor.predict_from_landmarks(trajectory, fps=effective_fps)
    verdict = "DYSGRAPHIC" if score >= predictor.threshold else "CONTROL"
    print(f"\nDysgraphia probability: {score:.4f}  ->  {verdict} "
          f"(threshold={predictor.threshold})")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI: run the demo, train from a CSV, or predict live from the camera."""
    parser = argparse.ArgumentParser(
        description="Dysgraphia probability prediction (0..1) from hand kinematics."
    )
    parser.add_argument("--demo", action="store_true",
                        help="Run the synthetic train/predict demo (default when no other mode).")
    parser.add_argument("--fit-csv", default=None,
                        help="Train on a CSV of feature rows plus a binary label column.")
    parser.add_argument("--label-col", default="label",
                        help="Name of the binary (0/1) label column in --fit-csv.")
    parser.add_argument("--output", default=None,
                        help="Path to save a trained model (default: dysgraphia_model.joblib).")
    parser.add_argument("--model", default=None,
                        help="Path to a trained .joblib model to load for live prediction.")
    parser.add_argument("--source", default="0",
                        help="Webcam index or video path for live prediction.")
    parser.add_argument("--fps", type=float, default=None,
                        help="Override the recording FPS for live prediction.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args(argv)

    if args.fit_csv:
        data = pd.read_csv(args.fit_csv)
        if args.label_col not in data.columns:
            raise SystemExit(f"Label column {args.label_col!r} not found in {args.fit_csv}.")
        y = data.pop(args.label_col).to_numpy()
        predictor = DysgraphiaPredictor(random_state=args.seed).fit(data, y)
        out = args.output or "dysgraphia_model.joblib"
        predictor.save(out)
        print(f"Trained on {len(data)} samples; model saved to {out}.")
        return 0

    if args.model:
        source: Union[int, str] = (
            int(args.source) if str(args.source).strip().isdigit() else args.source
        )
        return _predict_live(args.model, source, args.fps)

    # No explicit mode -> run the demo so `python dysgraphia_predictor.py` does something.
    return _run_demo(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())




