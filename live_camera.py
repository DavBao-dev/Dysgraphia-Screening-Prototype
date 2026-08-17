"""
live_camera.py - Live webcam hand tracking cho Model A (hien thi trong Streamlit).

Streamlit chay trong trinh duyet nen khong dung duoc cv2.imshow()/waitKey() nhu
model_a_dysgraphia.py (cua so goc). File nay thay phan hien thi bang cach tra
anh da ve landmark (BGR ndarray) cho Streamlit dung st.image(). Camera doc tu
may local bang cv2.VideoCapture(0) - phu hop prototype chay ngay tren may nguoi
dung (khong phai server headless).

Logic MediaPipe + trich feature van dung lai 100% tu model_a_dysgraphia.py.
"""
from __future__ import annotations

import cv2
import numpy as np

from model_a_dysgraphia import (
    EnhancedKinematicFeatureExtractor,
    HandLandmarkRecorder,
    KinematicFeatureExtractor,
)


def open_camera(index: int = 0, width: int = 640, height: int = 480) -> cv2.VideoCapture:
    """Mo webcam. Tra ve doi tuong VideoCapture, hoac raise neu khong mo duoc.

    Dat do phan giai thap (mac dinh 640x480) + buffer=1 de giam do tre va tang
    FPS. Landmark cua MediaPipe la toa do chuan hoa (0..1) nen viec giam do
    phan giai khong lam mat do chinh xac cua feature.
    """
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Khong mo duoc webcam (index {index}). Kiem tra quyen truy cap camera."
        )
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # doc frame moi nhat, giam latency
    return cap


def get_camera_fps(cap: cv2.VideoCapture, fallback: float = 30.0) -> float:
    """Doc FPS tu camera; tra ve ``fallback`` neu gia tri khong hop le."""
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = fallback
    return float(fps)


def make_hands():
    """Tao MediaPipe Hands instance (import lazy vi MediaPipe import cham)."""
    from mediapipe.python.solutions import hands as mp_hands

    return mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )


def process_frame(frame: np.ndarray, hands) -> tuple[np.ndarray, np.ndarray | None]:
    """Chay MediaPipe Hands tren 1 frame BGR.

    Tra ve ``(annotated_bgr, landmarks)``: anh da ve skeleton tay + mang
    landmark (21, 3) cua ban tay dau tien, hoac ``None`` neu khong thay tay.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = hands.process(rgb)

    annotated = frame.copy()
    landmarks = None
    if results.multi_hand_landmarks:
        HandLandmarkRecorder._draw_landmarks(annotated, results.multi_hand_landmarks)
        chosen = results.multi_hand_landmarks[0]
        landmarks = np.array(
            [[lm.x, lm.y, lm.z] for lm in chosen.landmark], dtype=np.float64
        )
    return annotated, landmarks


def resize_for_display(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    """Thu nho khung hinh truoc khi gui len Streamlit (giam du lieu, tang FPS)."""
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / float(w)
        frame = cv2.resize(frame, (max_width, int(h * scale)), interpolation=cv2.INTER_AREA)
    return frame


def extract_features_from_trajectory(
    trajectory, fps: float, use_enhanced: bool = True
) -> dict:
    """Ghep chuoi landmark (list cac mang (21, 3)) thanh (T, 21, 3) roi tinh feature."""
    arr = np.stack(trajectory, axis=0)
    if use_enhanced:
        extractor = EnhancedKinematicFeatureExtractor(fps=fps)
        return extractor.extract_features(arr)
    extractor = KinematicFeatureExtractor(fps=fps)
    return extractor.extract(arr)
