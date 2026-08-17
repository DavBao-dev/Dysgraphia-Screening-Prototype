"""Unit tests for stationary-hand handling and camera-noise smoothing.

Covers the acceptance criteria:
1. A static (identical-keypoint) hand -> 0% risk + "Hand Stationary".
2. Active writing -> normal features + risk in [0, 1].
3. Stationary / normal / high-jerk synthetic trajectories.
"""
import os

import numpy as np
import pytest

from model_a_dysgraphia import (
    EnhancedKinematicFeatureExtractor,
    KinematicFeatureExtractor,
    index_tip_path_length,
    mean_joint_spread,
    smooth_keypoints,
)
from dysgraphia_predictor import BASIC_FEATURE_COLUMNS, DysgraphiaPredictor


def _stationary_trajectory(T: int = 30) -> np.ndarray:
    """A hand that does not move: every keypoint identical across frames."""
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    kp[:, 0, :] = [0.5, 0.5, 0.0]  # wrist
    kp[:, 4, :] = [0.55, 0.55, 0.0]  # thumb tip
    kp[:, 8, :] = [0.6, 0.5, 0.0]  # index tip
    for j in range(21):
        if j not in (0, 4, 8):
            kp[:, j, :] = [0.5 + 0.01 * j, 0.5, 0.0]
    return kp


def _writing_trajectory(T: int = 60) -> np.ndarray:
    """A hand whose index tip traces a Lissajous 'writing' figure."""
    t = np.linspace(0.0, 1.0, T)
    tip_x = 0.5 + 0.15 * np.sin(2 * np.pi * t)
    tip_y = 0.5 + 0.10 * np.sin(4 * np.pi * t)
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    kp[:, 0, :] = [0.5, 0.5, 0.0]
    kp[:, 4, :] = [0.55, 0.55, 0.0]
    kp[:, 8, 0] = tip_x
    kp[:, 8, 1] = tip_y
    kp[:, 8, 2] = 0.0
    for j in range(21):
        if j not in (0, 4, 8):
            kp[:, j, :] = [0.5 + 0.01 * j, 0.5, 0.0]
    return kp


def _contracted_trajectory(T: int = 60) -> np.ndarray:
    """A clenched hand: all 21 joints clustered tightly near the palm."""
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    for j in range(21):
        kp[:, j, :] = [0.5 + 0.02 * (j % 5), 0.5 + 0.01 * (j // 5), 0.0]
    return kp


# ---------------------------------------------------------------------------
# 1. Movement activity gate
# ---------------------------------------------------------------------------
def test_stationary_hand_returns_zero_risk():
    predictor = DysgraphiaPredictor(feature_columns=BASIC_FEATURE_COLUMNS)
    result = predictor.predict_kinematics(_stationary_trajectory())
    assert result["risk_score"] == 0.0
    assert result["status"] == "Hand Stationary / Contracted Pose"
    assert all(v == 0.0 for v in result["features"].values())


def test_index_tip_path_length_stationary_vs_writing():
    assert index_tip_path_length(_stationary_trajectory()) == 0.0
    assert index_tip_path_length(_writing_trajectory()) > 0.05


# ---------------------------------------------------------------------------
# 2. in_air_pause_ratio guard (stationary hand != 100% freeze)
# ---------------------------------------------------------------------------
def test_basic_in_air_pause_ratio_zero_for_stationary():
    feats = KinematicFeatureExtractor(fps=30.0).extract(_stationary_trajectory())
    assert feats["in_air_pause_ratio"] == 0.0


def test_enhanced_in_air_pause_ratio_zero_for_stationary():
    feats = EnhancedKinematicFeatureExtractor(fps=30.0).extract_features(_stationary_trajectory())
    assert feats["in_air_pause_ratio"] == 0.0


# ---------------------------------------------------------------------------
# 3. Temporal smoothing
# ---------------------------------------------------------------------------
def test_smoothing_reduces_variance():
    rng = np.random.default_rng(0)
    noisy = _stationary_trajectory(60) + rng.normal(0.0, 0.001, size=(60, 21, 3))
    smoothed = smooth_keypoints(noisy)
    assert np.var(smoothed) <= np.var(noisy)


def test_smoothing_preserves_shape():
    arr = _writing_trajectory(30)
    assert smooth_keypoints(arr).shape == arr.shape


# ---------------------------------------------------------------------------
# 4. Normal movement + high jerk
# ---------------------------------------------------------------------------
def test_normal_movement_returns_ok_and_risk_in_range():
    if not os.path.exists("weights/writesense_model_a.joblib"):
        pytest.skip("writesense_model_a.joblib not present")
    predictor = DysgraphiaPredictor.load("weights/writesense_model_a.joblib")
    result = predictor.predict_kinematics(_writing_trajectory())
    assert result["status"] == "OK"
    assert 0.0 <= result["risk_score"] <= 1.0


def test_high_jerk_detected():
    T = 60
    kp = np.zeros((T, 21, 3), dtype=np.float64)
    kp[:, 0, :] = [0.5, 0.5, 0.0]
    # index tip: square-wave motion with abrupt reversals -> large jerk
    for t in range(T):
        kp[t, 8, 0] = 0.5 + 0.2 * (1.0 if (t // 5) % 2 == 0 else -1.0)
        kp[t, 8, 1] = 0.5
    feats = KinematicFeatureExtractor(fps=30.0).extract(kp)
    assert feats["jerk_max"] > 0.0


# ---------------------------------------------------------------------------
# 5. Contracted / clenched hand (acceptance criterion 1)
# ---------------------------------------------------------------------------
def test_contracted_hand_with_jitter_returns_zero_risk():
    rng = np.random.default_rng(1)
    base = _contracted_trajectory(60)
    jitter = rng.normal(0.0, 0.0015, size=base.shape)  # ~1px MediaPipe jitter
    noisy = base + jitter
    predictor = DysgraphiaPredictor(feature_columns=BASIC_FEATURE_COLUMNS)
    result = predictor.predict_kinematics(noisy)
    assert result["risk_score"] == 0.0
    assert result["status"] == "Hand Stationary / Contracted Pose"


def test_contracted_hand_has_smaller_spread_than_open():
    # Open hand: joints spread on a circle of radius 0.25.
    open_hand = np.tile(np.zeros((1, 21, 3)), (30, 1, 1))
    for j in range(21):
        a = 2 * np.pi * j / 21
        open_hand[:, j, 0] = 0.5 + 0.25 * np.cos(a)
        open_hand[:, j, 1] = 0.5 + 0.25 * np.sin(a)
    assert mean_joint_spread(_contracted_trajectory(30)) < 0.15
    assert mean_joint_spread(open_hand) > 0.15


def test_posture_features_zeroed_when_inactive():
    feats = KinematicFeatureExtractor(fps=30.0).extract(_contracted_trajectory(30))
    assert feats["wrist_flexion_angle_mean"] == 0.0
    assert feats["pinch_distance_mean"] == 0.0
