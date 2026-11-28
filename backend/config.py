import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEIGHTS_DIR = REPO_ROOT / "weights"
DATA_DIR = REPO_ROOT / "data"

MODEL_A_WEIGHTS = WEIGHTS_DIR / "writesense_model_a.joblib"
MODEL_B_BACKBONE_ONNX = WEIGHTS_DIR / "resnet50_backbone.onnx"
MODEL_B_HEAD_ONNX = WEIGHTS_DIR / "model_b.onnx"
MODEL_B_HEAD_TORCH = WEIGHTS_DIR / "model_b.pt"
MODEL_B_SCALER_MEAN = WEIGHTS_DIR / "model_b_scaler_mean.npy"
MODEL_B_SCALER_SCALE = WEIGHTS_DIR / "model_b_scaler_scale.npy"

USE_MODEL_B_SCALER = True
# Ban deploy (deploy/huggingface/Dockerfile) dat bien moi truong nay thap hon de may chu nho khong bi qua tai.
MAX_VIDEO_SIZE_MB = int(os.environ.get("MAX_VIDEO_SIZE_MB", "4096"))
MAX_VIDEO_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
# Chuoi ket noi Postgres (vd. Supabase, dung "Session pooler" de co IPv4). De trong -> luu CSV trong data/.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
MIN_MODEL_A_FRAMES = 5
MODEL_A_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mpeg4", ".mkv"}
MODEL_B_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
DISCLAIMER = "Kết quả sàng lọc, không phải chẩn đoán y tế."
