"""Model A -- Dysgraphia Screening System: Hand Kinematics Feature Extraction.

Implements the vision pipeline for "Model A" of a dysgraphia screening system:

1. **Hand tracking** -- captures a live webcam feed (or a video file), detects
   the 21 3D hand landmarks per frame with Google MediaPipe Hands, renders the
   skeleton overlay, and buffers the trajectories into a NumPy array of shape
   ``(T, 21, 3)``.

2. **Kinematic feature extraction** -- turns the buffered trajectory into a
   flat feature vector ready for a tabular ML model (Random Forest / XGBoost).

Dependencies
------------
    opencv-python, mediapipe, numpy, scipy, pandas

Usage
-----
    python model_a_dysgraphia.py                      # webcam (index 0)
    python model_a_dysgraphia.py --source video.mp4   # video file
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
from enum import IntEnum
from typing import Any

import cv2
import numpy as np
import pandas as pd
from scipy.signal import detrend, find_peaks
from scipy.stats import entropy

__all__ = [
    "Landmark",
    "KinematicFeatureExtractor",
    "EnhancedKinematicFeatureExtractor",
    "HandLandmarkRecorder",
    "main",
]


class Landmark(IntEnum):
    """MediaPipe Hand landmark indices (0..20), usable directly for NumPy indexing."""

    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


class EnhancedKinematicFeatureExtractor:
    """
    Advanced Kinematic & Biomechanical Feature Extractor for Dysgraphia Screening.
    Input: Keypoint trajectory matrix of shape (T, 21, 3) at a given FPS.
    """
    def __init__(self, fps: float = 60.0) -> None:
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError(f"fps must be a positive finite number, got {fps!r}.")
        self.fps = float(fps)
        self.dt = 1.0 / self.fps

    def extract_features(self, keypoints_3d: np.ndarray) -> dict[str, float]:
        T = keypoints_3d.shape[0]
        if T < 15:
            raise ValueError(f"Sequence length T={T} is too short for reliable feature extraction.")

        # Keypoint Mapping (MediaPipe standard)
        wrist = keypoints_3d[:, 0, :]
        thumb_tip = keypoints_3d[:, 4, :]
        index_tip = keypoints_3d[:, 8, :]

        # -------------------------------------------------------------
        # 1. Basic Kinematics (Index Fingertip)
        # -------------------------------------------------------------
        v_vector: np.ndarray = np.gradient(index_tip, self.dt, axis=0)
        speed = np.linalg.norm(v_vector, axis=-1)
        
        a_vector: np.ndarray = np.gradient(v_vector, self.dt, axis=0)

        j_vector: np.ndarray = np.gradient(a_vector, self.dt, axis=0)
        jerk = np.linalg.norm(j_vector, axis=-1)

        total_duration = T * self.dt
        path_length = float(np.sum(speed * self.dt))
        path_length = max(path_length, 1e-6)

        # -------------------------------------------------------------
        # 2. Advanced Feature: Normalized Jerk (NJ)
        # -------------------------------------------------------------
        jerk_squared_integral = np.trapezoid(jerk**2, dx=self.dt)
        normalized_jerk = np.sqrt(0.5 * jerk_squared_integral * (total_duration**5) / (path_length**2))

        # -------------------------------------------------------------
        # 3. Advanced Feature: Number of Velocity Changes (NVC)
        # -------------------------------------------------------------
        peaks, _ = find_peaks(speed, distance=int(self.fps * 0.05)) # 50ms min separation
        nvc_rate = len(peaks) / total_duration  # Peaks per second

        # -------------------------------------------------------------
        # 4. Advanced Feature: Frequency Domain (Spectral Entropy & Tremor Power Ratio)
        # -------------------------------------------------------------
        speed_detrended = speed - np.mean(speed)
        yf = np.abs(np.fft.fft(speed_detrended))[: T // 2]
        xf = np.fft.fftfreq(T, self.dt)[: T // 2]

        psd = yf**2
        psd_norm = psd / (np.sum(psd) + 1e-8)
        
        # Spectral Entropy
        spectral_entropy = float(entropy(psd_norm + 1e-12, base=2))

        # Relative Tremor Power Ratio (3.0 - 8.0 Hz vs Total Power)
        tremor_mask = (xf >= 3.0) & (xf <= 8.0)
        total_mask = (xf >= 0.5) & (xf <= 15.0)
        
        tremor_power = np.sum(psd[tremor_mask])
        total_power = np.sum(psd[total_mask]) + 1e-8
        tremor_power_ratio = float(tremor_power / total_power)

        # -------------------------------------------------------------
        # 5. Advanced Feature: Thumb-Index Pinch Synergy
        # -------------------------------------------------------------
        thumb_v_vector: np.ndarray = np.gradient(thumb_tip, self.dt, axis=0)
        thumb_speed = np.linalg.norm(thumb_v_vector, axis=-1)

        # Pearson correlation between index and thumb speeds
        if np.std(speed) > 1e-6 and np.std(thumb_speed) > 1e-6:
            pincer_correlation = float(np.corrcoef(speed, thumb_speed)[0, 1])
        else:
            pincer_correlation = 0.0

        # -------------------------------------------------------------
        # 6. Advanced Feature: Wrist Postural Drift
        # -------------------------------------------------------------
        wrist_drift_dist = np.linalg.norm(wrist[-1] - wrist[0])
        wrist_drift_rate = float(wrist_drift_dist / total_duration)

        # In-Air Pause Ratio
        pause_ratio = float(np.sum(speed < 0.005) / T)

        return {
            # Standard Metrics
            "mean_speed": float(np.mean(speed)),
            "std_speed": float(np.std(speed)),
            "mean_jerk": float(np.mean(jerk)),
            "max_jerk": float(np.max(jerk)),
            "in_air_pause_ratio": pause_ratio,
            
            # New Advanced Biomechanical Features
            "normalized_jerk": float(normalized_jerk),
            "nvc_per_second": float(nvc_rate),
            "spectral_entropy": spectral_entropy,
            "tremor_power_ratio": tremor_power_ratio,
            "pincer_correlation": pincer_correlation,
            "wrist_drift_rate": wrist_drift_rate,
        }

    def extract_dataframe(self, landmarks: np.ndarray) -> pd.DataFrame:
        """Shortcut: extract features and return them as a 1-row DataFrame."""
        return self.to_dataframe(self.extract_features(landmarks))

    @staticmethod
    def to_dataframe(features: dict[str, float]) -> pd.DataFrame:
        """Convert a feature dict into a 1-row DataFrame for tabular models."""
        return pd.DataFrame([features])

class KinematicFeatureExtractor:
    """Compute biomechanical kinematic features from a ``(T, 21, 3)`` landmark sequence.

    Parameters
    ----------
    fps:
        Sampling rate (frames per second). Converts frame indices to seconds
        for numerical differentiation and FFT.
    minimum_frames:
        Minimum sequence length ``T`` required for a valid extraction.
    pause_threshold:
        Speed threshold (normalized-coordinate units / second) below which the
        index fingertip is considered at rest (in-air pause).
    tremor_band:
        ``(low_hz, high_hz)`` bounds of the involuntary motor-tremor band.
    """

    def __init__(
        self,
        fps: float = 30.0,
        minimum_frames: int = 10,
        pause_threshold: float = 0.005,
        tremor_band: tuple[float, float] = (3.0, 8.0),
    ) -> None:
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError(f"fps must be a positive finite number, got {fps!r}.")
        if minimum_frames < 3:
            raise ValueError("minimum_frames must be at least 3 for 3rd-order derivatives.")
        if not (0 < tremor_band[0] < tremor_band[1]):
            raise ValueError("tremor_band must be (low_hz, high_hz) with 0 < low < high.")
        self.fps = float(fps)
        self.dt = 1.0 / self.fps
        self.minimum_frames = int(minimum_frames)
        self.pause_threshold = float(pause_threshold)
        self.tremor_band = (float(tremor_band[0]), float(tremor_band[1]))

    def extract(self, landmarks: np.ndarray) -> dict[str, float]:
        """Extract all kinematic features from a landmark sequence.

        Returns a flat ``{feature_name: value}`` dictionary.
        """
        landmarks = np.asarray(landmarks, dtype=np.float64)
        self._validate(landmarks)

        dt = self.dt
        tip = landmarks[:, Landmark.INDEX_TIP, :]  # (T, 3)

        velocity: np.ndarray = np.gradient(tip, dt, axis=0, edge_order=2)  # (T, 3)
        speed = np.linalg.norm(velocity, axis=1)  # (T,)
        acceleration: np.ndarray = np.gradient(velocity, dt, axis=0, edge_order=2)  # (T, 3)
        accel_mag = np.linalg.norm(acceleration, axis=1)  # (T,)
        jerk: np.ndarray = np.gradient(acceleration, dt, axis=0, edge_order=2)  # (T, 3)
        jerk_mag = np.linalg.norm(jerk, axis=1)  # (T,)

        features: dict[str, float] = {
            "num_frames": float(landmarks.shape[0]),
            "fps": self.fps,
            "speed_mean": float(np.mean(speed)),
            "speed_max": float(np.max(speed)),
            "speed_std": float(np.std(speed)),
            "acceleration_mean": float(np.mean(accel_mag)),
            "acceleration_max": float(np.max(accel_mag)),
            "acceleration_std": float(np.std(accel_mag)),
            "jerk_mean": float(np.mean(jerk_mag)),
            "jerk_max": float(np.max(jerk_mag)),
            "jerk_std": float(np.std(jerk_mag)),
        }
        features.update(self._flexion_angle(landmarks))
        features["in_air_pause_ratio"] = self._pause_ratio(speed)
        features.update(self._tremor_fft(speed))
        features.update(self._pinch_distance(landmarks))
        return features

    def extract_dataframe(self, landmarks: np.ndarray) -> pd.DataFrame:
        """Shortcut: extract features and return them as a 1-row DataFrame."""
        return self.to_dataframe(self.extract(landmarks))

    @staticmethod
    def to_dataframe(features: dict[str, float]) -> pd.DataFrame:
        """Convert a feature dict into a 1-row DataFrame for tabular models."""
        return pd.DataFrame([features])

    # ----------------------------------------------------------------- helpers
    def _validate(self, landmarks: np.ndarray) -> None:
        if landmarks.ndim != 3 or landmarks.shape[1:] != (21, 3):
            raise ValueError(f"Expected landmarks of shape (T, 21, 3), got {landmarks.shape}.")
        if landmarks.shape[0] < self.minimum_frames:
            raise ValueError(
                f"Sequence too short: got {landmarks.shape[0]} frames, need at least {self.minimum_frames}."
            )
        if not np.all(np.isfinite(landmarks)):
            raise ValueError("Landmark sequence contains NaN or Inf values.")

    def _flexion_angle(self, landmarks: np.ndarray) -> dict[str, float]:
        """Flexion angle at the index MCP joint (WRIST -> INDEX_MCP -> INDEX_TIP).

        The angle is measured at keypoint 5 between the proximal segment
        (MCP -> wrist) and the distal segment (MCP -> fingertip), using the 3D
        vector dot product.
        """
        p_wrist = landmarks[:, Landmark.WRIST, :]
        p_mcp = landmarks[:, Landmark.INDEX_MCP, :]
        p_tip = landmarks[:, Landmark.INDEX_TIP, :]

        v_prox = p_wrist - p_mcp  # MCP -> wrist
        v_dist = p_tip - p_mcp  # MCP -> fingertip

        denom = np.linalg.norm(v_prox, axis=1) * np.linalg.norm(v_dist, axis=1)
        denom = np.where(denom == 0.0, 1e-12, denom)
        cos_theta = np.einsum("ij,ij->i", v_prox, v_dist) / denom
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        angle_deg = np.degrees(np.arccos(cos_theta))

        return {
            "wrist_flexion_angle_mean": float(np.mean(angle_deg)),
            "wrist_flexion_angle_std": float(np.std(angle_deg)),
        }

    def _pause_ratio(self, speed: np.ndarray) -> float:
        """Fraction of frames where the fingertip speed is below the rest threshold."""
        paused = int(np.count_nonzero(speed < self.pause_threshold))
        return float(paused) / float(speed.size)

    def _tremor_fft(self, speed: np.ndarray) -> dict[str, float]:
        """Micro-tremor analysis: FFT of the detrended speed signal in a band.

        Returns the peak frequency (Hz) and peak one-sided amplitude within the
        involuntary motor-tremor band (default 3.0--8.0 Hz).
        """
        n = speed.size
        signal: np.ndarray = detrend(speed, type="linear")
        spectrum: np.ndarray = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, d=self.dt)
        amplitude = (2.0 / n) * np.abs(spectrum)  # one-sided amplitude spectrum
        amplitude[0] = 0.0  # drop the DC bin

        low, high = self.tremor_band
        band = (freqs >= low) & (freqs <= high)
        if np.any(band):
            idx = int(np.argmax(amplitude[band]))
            peak_freq = float(freqs[band][idx])
            peak_amp = float(amplitude[band][idx])
        else:
            peak_freq, peak_amp = float("nan"), float("nan")

        return {
            "tremor_peak_frequency_hz": peak_freq,
            "tremor_peak_amplitude": peak_amp,
        }

    def _pinch_distance(self, landmarks: np.ndarray) -> dict[str, float]:
        """Euclidean distance between index tip (8) and thumb tip (4)."""
        index_tip = landmarks[:, Landmark.INDEX_TIP, :]
        thumb_tip = landmarks[:, Landmark.THUMB_TIP, :]
        distance = np.linalg.norm(index_tip - thumb_tip, axis=1)
        return {
            "pinch_distance_std": float(np.std(distance)),
            "pinch_distance_mean": float(np.mean(distance)),
        }


class HandLandmarkRecorder:
    """Capture and buffer 21 3D hand landmarks from a webcam or video file.

    MediaPipe is imported lazily inside :meth:`run` because it is a heavy,
    slow-importing dependency; keeping it out of the module import path lets the
    feature-extraction part of this module be used in environments without a
    camera or MediaPipe installed.

    Parameters
    ----------
    source:
        Webcam index (``int``) or path to a video file (``str``).
    max_frames:
        Stop recording after this many frames with a detected hand (``None`` =
        unlimited).
    max_num_hands:
        Maximum number of hands MediaPipe tracks simultaneously.
    preferred_hand:
        ``"Left"``, ``"Right"`` or ``None``. When multiple hands are visible,
        prefer this hand for the recorded trajectory.
    static_image_mode, model_complexity, min_detection_confidence,
    min_tracking_confidence:
        Passed through to ``mp.solutions.hands.Hands``.
    window_name:
        Title of the OpenCV preview window.
    """

    def __init__(
        self,
        source: int | str = 0,
        max_frames: int | None = None,
        max_num_hands: int = 1,
        preferred_hand: str | None = None,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        window_name: str = "Model A - Hand Tracking (press 'q' to stop)",
    ) -> None:
        if preferred_hand is not None and preferred_hand not in {"Left", "Right"}:
            raise ValueError("preferred_hand must be 'Left', 'Right', or None.")
        if max_frames is not None and max_frames <= 0:
            raise ValueError("max_frames must be positive or None.")
        self.source = source
        self.max_frames = max_frames
        self.max_num_hands = max_num_hands
        self.preferred_hand = preferred_hand
        self.static_image_mode = static_image_mode
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.window_name = window_name

    def run(self) -> tuple[np.ndarray, float]:
        """Run the tracking loop and return ``(landmarks, fps)``.

        ``landmarks`` has shape ``(T, 21, 3)`` where ``T`` is the number of
        frames in which a hand was detected. Recording stops on 'q', on a
        failed frame read, or once ``max_frames`` is reached.
        """
        from mediapipe.python.solutions import hands as mp_hands  # deferred heavy import

        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source!r}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not np.isfinite(fps) or fps <= 0:
            fps = 30.0

        frames: list[np.ndarray] = []
        with mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_num_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        ) as hands:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results: Any = hands.process(rgb)
                rgb.flags.writeable = True

                if results.multi_hand_landmarks:
                    hand = self._select_hand(results)
                    landmarks = np.array(
                        [[lm.x, lm.y, lm.z] for lm in hand.landmark],
                        dtype=np.float64,
                    )
                    frames.append(landmarks)

                annotated = frame.copy()
                if results.multi_hand_landmarks:
                    self._draw_landmarks(annotated, results.multi_hand_landmarks)

                cv2.imshow(self.window_name, annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                if self.max_frames is not None and len(frames) >= self.max_frames:
                    break

        cap.release()
        cv2.destroyAllWindows()

        if frames:
            trajectory = np.stack(frames, axis=0)  # (T, 21, 3)
        else:
            trajectory = np.empty((0, 21, 3), dtype=np.float64)
        return trajectory, float(fps)

    def _select_hand(self, results: Any) -> Any:
        """Choose the hand to record (first, or the one matching ``preferred_hand``)."""
        hands = results.multi_hand_landmarks
        if len(hands) == 1:
            return hands[0]
        if self.preferred_hand and results.multi_handedness:
            for hand, handedness in zip(hands, results.multi_handedness):
                if handedness.classification[0].label == self.preferred_hand:
                    return hand
        return hands[0]

    @staticmethod
    def _draw_landmarks(image: np.ndarray, hand_landmarks: Sequence[Any]) -> None:
        """Render the hand skeleton overlay onto ``image`` in place."""
        from mediapipe.python.solutions import drawing_utils as mp_drawing
        from mediapipe.python.solutions import drawing_styles as mp_drawing_styles
        from mediapipe.python.solutions.hands_connections import HAND_CONNECTIONS

        connections = list(HAND_CONNECTIONS)
        try:
            for hand in hand_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    hand,
                    connections,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )
        except AttributeError:  # older MediaPipe without drawing_styles
            for hand in hand_landmarks:
                mp_drawing.draw_landmarks(image, hand, connections)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: record, extract features, print them and save a CSV."""
    parser = argparse.ArgumentParser(
        description="Model A dysgraphia screening: hand kinematics feature extraction."
    )
    parser.add_argument("--source", default="0",
                        help="Webcam index (default: 0) or path to a video file.")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Stop after this many frames with a detected hand.")
    parser.add_argument("--fps", type=float, default=None,
                        help="Override the recording FPS (default: from the source).")
    parser.add_argument("--pause-threshold", type=float, default=0.005,
                        help="In-air pause speed threshold (default: 0.005).")
    parser.add_argument("--tremor-low", type=float, default=3.0,
                        help="Lower tremor-band frequency in Hz (default: 3.0).")
    parser.add_argument("--tremor-high", type=float, default=8.0,
                        help="Upper tremor-band frequency in Hz (default: 8.0).")
    parser.add_argument("--output", default=None,
                        help="CSV path to save the features (default: dysgraphia_features_<timestamp>.csv).")
    args = parser.parse_args(argv)

    # Allow the source to be a webcam index or a file path.
    source: int | str = (
        int(args.source) if str(args.source).strip().isdigit() else args.source
    )

    recorder = HandLandmarkRecorder(source=source, max_frames=args.max_frames)
    print("Recording -- press 'q' in the video window to stop and extract features.")
    trajectory, fps = recorder.run()

    if trajectory.shape[0] == 0:
        print("No hand was detected in any frame; nothing to extract.")
        return 1

    effective_fps = args.fps if args.fps is not None else fps
    extractor = KinematicFeatureExtractor(
        fps=effective_fps,
        pause_threshold=args.pause_threshold,
        tremor_band=(args.tremor_low, args.tremor_high),
    )

    features = extractor.extract(trajectory)
    dataframe = KinematicFeatureExtractor.to_dataframe(features)

    print("\nExtracted features:")
    print(dataframe.T.to_string(header=False))

    output_path = args.output or f"dysgraphia_features_{datetime.now():%Y%m%d_%H%M%S}.csv"
    dataframe.to_csv(output_path, index=False)
    print(f"\nFeatures saved to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())



