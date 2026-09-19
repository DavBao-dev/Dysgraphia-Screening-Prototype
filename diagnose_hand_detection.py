"""diagnose_hand_detection.py - Diagnostic: why does MediaPipe find 0 hands?

Runs the exact same MediaPipe config as model_a_adapter.extract_landmarks_from_video
on every video in data/for_testing/model_a/ and reports how many frames contain
a detectable hand. Also samples a few frames and saves them as JPGs so you can
visually check the video content/orientation.
"""
import glob
import os
import sys

import cv2
import numpy as np
from mediapipe.python.solutions import hands as mp_hands

SAMPLES_PER_VIDEO = 5  # save every Nth frame thumbnail
MAX_FRAMES_SCAN = 4000


def diagnose(video_path: str) -> None:
    print("=" * 78)
    print(f"Video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("  !! KHONG MO DUOC VIDEO")
        return

    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    # Read rotation metadata (phone recordings are often rotated)
    rot = cap.get(cv2.CAP_PROP_ORIENTATION_META)
    print(f"  frames={n_frames}  fps={fps:.2f}  size={w}x{h}  rotation_meta={rot}")

    out_dir = os.path.join(
        "debug_frames",
        os.path.splitext(os.path.basename(video_path))[0],
    )
    os.makedirs(out_dir, exist_ok=True)

    hand_frames = 0
    scanned = 0
    saved = 0
    fps_eff = fps if np.isfinite(fps) and fps > 0 else 30.0

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.4,
        min_tracking_confidence=0.4,
    ) as hands:
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            if idx > MAX_FRAMES_SCAN:
                print("  (stopped early after MAX_FRAMES_SCAN frames)")
                break
            scanned += 1

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            if results.multi_hand_landmarks:
                hand_frames += 1

            if saved < SAMPLES_PER_VIDEO and idx % max(1, n_frames // SAMPLES_PER_VIDEO) == 0:
                thumb_path = os.path.join(out_dir, f"frame_{idx:05d}.jpg")
                cv2.imwrite(thumb_path, frame)
                saved += 1

    cap.release()
    print(f"  scanned={scanned}  frames_with_hand={hand_frames}  ratio={hand_frames / max(1, scanned):.1%}")
    print(f"  thumbnails saved to {out_dir}/")


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "data/for_testing/model_a/*.mp4"
    for p in sorted(glob.glob(pattern)):
        try:
            diagnose(p)
        except Exception as e:  # noqa: BLE001
            print(f"  !! ERROR: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
