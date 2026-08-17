"""
model_a_adapter.py - Chay model_a_dysgraphia.py o che do headless (khong GUI).

File goc model_a_dysgraphia.py cua ban dung cv2.imshow()/waitKey() de hien thi
webcam truc tiep - cach nay KHONG chay duoc tren server (Streamlit chay tren
server khong co man hinh, cv2.imshow se bao loi hoac treo).

File nay dung lai dung logic MediaPipe (mo hinh 21 diem tay cua Google) va
dung lai nguyen KinematicFeatureExtractor / EnhancedKinematicFeatureExtractor
tu file goc de trich feature - CHI thay phan doc frame: doc tu file video da
upload thay vi webcam, va bo hoan toan phan hien thi cua so.
"""
import numpy as np
import cv2

from model_a_dysgraphia import KinematicFeatureExtractor, EnhancedKinematicFeatureExtractor


def extract_landmarks_from_video(video_path: str, max_num_hands: int = 1, preferred_hand: str | None = None):
    """
    Doc toan bo video, chay MediaPipe Hands tren tung frame (khong hien thi
    cua so), tra ve (landmarks, fps) voi landmarks shape (T, 21, 3).
    """
    from mediapipe.python.solutions import hands as mp_hands

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Khong mo duoc video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        fps = 30.0

    frames = []
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=max_num_hands,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)

            if results.multi_hand_landmarks:
                hand_list = results.multi_hand_landmarks
                chosen = hand_list[0]
                if len(hand_list) > 1 and preferred_hand and results.multi_handedness:
                    for hand, handedness in zip(hand_list, results.multi_handedness):
                        if handedness.classification[0].label == preferred_hand:
                            chosen = hand
                            break
                landmarks = np.array([[lm.x, lm.y, lm.z] for lm in chosen.landmark], dtype=np.float64)
                frames.append(landmarks)

    cap.release()

    if frames:
        trajectory = np.stack(frames, axis=0)  # (T, 21, 3)
    else:
        trajectory = np.empty((0, 21, 3), dtype=np.float64)
    return trajectory, float(fps)


def run_model_a_pipeline(video_path: str, use_enhanced: bool = True) -> dict:
    """
    Chay toan bo pipeline Model A: video -> 21 keypoint/frame (MediaPipe cua
    Google) -> feature dict (jerk, tremor, entropy,...).

    LUU Y: model_a_dysgraphia.py CHUA co bo phan loai (chua train Random
    Forest/XGBoost tren cac feature nay) - ham nay chi tra ve FEATURE, khong
    co output 0/1. Khi ban co model phan loai da train cho Model A (vd
    random_forest.pkl), them buoc load + predict(feature_vector) o cuoi ham
    nay va tra ve them (feature, output, confidence).
    """
    trajectory, fps = extract_landmarks_from_video(video_path)

    if trajectory.shape[0] == 0:
        raise ValueError("Khong phat hien duoc ban tay nao trong video.")

    if use_enhanced:
        extractor = EnhancedKinematicFeatureExtractor(fps=fps)
    else:
        extractor = KinematicFeatureExtractor(fps=fps)

    features = extractor.extract_features(trajectory) if use_enhanced else extractor.extract(trajectory)
    return features
