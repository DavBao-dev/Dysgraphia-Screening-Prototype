# Dysgraphia Screening — FastAPI + Next.js

Ứng dụng sàng lọc khó viết (dysgraphia): ghi lại **chuyển động tay** (video tải lên hoặc
camera trực tiếp) và **ảnh chữ viết tay**, chạy 2 mô hình độc lập rồi tổng hợp thành một
kết quả sàng lọc. Kết quả **chỉ mang tính tham khảo, không phải chẩn đoán y tế**.

Giao diện Streamlit cũ (`app.py`, `live_camera.py`, `live_cam_component/`) **đã được xoá** —
UI hiện tại là Next.js + Tailwind trong `frontend/`.

## Kiến trúc

```
frontend/  Next.js 16 + Tailwind, giao diện tiếng Việt
   │  fetch("/api/*")  →  next.config.ts rewrites  →  http://127.0.0.1:8000
   ▼
backend/   FastAPI
   ├─ routes/     screening.py, history.py            (6 endpoint)
   ├─ services/   model_a_service, model_b_service, ensemble_service
   ├─ ml/         model_a_adapter, model_a_dysgraphia, dysgraphia_predictor,
   │              image_features, inference, inference_openvino
   ├─ config.py   đường dẫn weights, MIN_MODEL_A_FRAMES, giới hạn upload
   └─ db.py       lưu CSV trong data/  (thay MySQL/SQLite)
weights/   model + scaler
data/      CSV sinh lúc chạy: sessions, model_a_features, model_b_features, predictions
```

## Cài đặt & chạy

### 1. Backend

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

- Kiểm tra: `GET http://127.0.0.1:8000/api/health` → `{"status":"ok", ...}`
- Tài liệu tự động: `http://127.0.0.1:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

Bản production: `npm run build && npm run start`

`frontend/next.config.ts` proxy `/api/*` sang backend `127.0.0.1:8000`, nên chỉ cần mở cổng 3000.

### 3. Chạy nhanh cả hai bằng 1 lệnh

```powershell
.\run-dev.ps1           # start backend + frontend (chạy nền, log trong logs\); tự thêm Node vào PATH nếu thiếu
.\run-dev.ps1 -Attach   # start rồi xem log trực tiếp; Ctrl+C để dừng cả hai
.\run-dev.ps1 -Status   # xem trạng thái 2 server
.\run-dev.ps1 -Stop     # dừng cả hai (port 8000/3000 được giải phóng)
```

**Yêu cầu:** Python 3.11+ (đã kiểm thử với 3.12), Node.js LTS (đã kiểm thử 24.x). Cần internet
cho lần đầu tải weight ResNet50 (nhánh PyTorch) và cho CDN MediaPipe JS (`@mediapipe/hands@0.4`)
ở chế độ camera trực tiếp.

## API

| Method | Path | Mô tả |
| --- | --- | --- |
| POST | `/api/screening` | Sàng lọc đầy đủ, **có lưu** CSV. multipart: `patient_id`, `model_a_source` (`video` \| `live`), `video` (file) hoặc `landmarks_json`, `image` (tuỳ chọn) → trả `session_id` + kết quả Model A/B/ensemble |
| POST | `/api/screening/model-a` | Chỉ Model A, **không lưu** |
| POST | `/api/screening/model-b` | Chỉ Model B (ảnh), **không lưu** |
| GET | `/api/health` | Trạng thái dịch vụ |
| GET | `/api/history?limit=50` | Danh sách phiên gần nhất |
| GET | `/api/history/{session_id}` | Chi tiết một phiên (Model A + Model B + ensemble) |

Lỗi: `400` dữ liệu không hợp lệ (video không có bàn tay, thiếu frame, landmark sai shape),
`413` video vượt giới hạn dung lượng (mặc định **4096 MB** — `MAX_VIDEO_SIZE_MB` trong
`backend/config.py`), `404` không tìm thấy phiên.

## Pipeline ML

**Model A — chuyển động tay (bắt buộc).**
video / landmark từ browser → MediaPipe Hands (21 điểm mỗi bàn tay) → `KinematicFeatureExtractor`
(18 feature: tốc độ, gia tốc, jerk, pause ratio, tremor 3–8 Hz, pinch…) → **Random Forest**
(`weights/writesense_model_a.joblib`, schema 18 feature) → `risk_score` + `prediction`.

- Cần tối thiểu `MIN_MODEL_A_FRAMES = 5` frame có bàn tay (`backend/config.py`); frontend giữ
  cùng giá trị ở `frontend/lib/constants.ts` (`MIN_LIVE_FRAMES`).
- Có "movement gate": bàn tay đứng yên hoặc co cứng → `risk_score = 0.0`,
  `status = "Hand Stationary / Contracted Pose"`, các feature trả về 0.
- `EnhancedKinematicFeatureExtractor.extract_features()` vẫn yêu cầu `T >= 15` — chỉ ảnh hưởng
  nếu bạn load model theo schema 28 feature; model hiện tại là 18 feature nên không đi nhánh này.

**Model B — ảnh chữ viết tay (tuỳ chọn).**
ảnh → ResNet50 embedding (2048-d, bỏ `fc`) + 2 feature thủ công từ `backend/ml/image_features.py`
(`ink_thickness_mean`, `baseline_deviation`) → MLP head
`Linear(2050→128) → ReLU → Dropout → Linear(128→32) → ReLU → Linear(32→1) → Sigmoid`.

- Runtime ưu tiên **ONNX Runtime** (`resnet50_backbone.onnx` + `model_b.onnx`); fallback PyTorch
  (`model_b.pt`).
- Scaler 2 giá trị (`model_b_scaler_mean.npy` / `model_b_scaler_scale.npy`, mean ≈ `[9.35, 48.02]`,
  scale ≈ `[4.09, 35.19]`) được áp dụng cho 2 feature thủ công trước khi vào head. **Đây là giả
  định suy ra từ chính các file `.npy`** (repo không có training script để xác nhận) — nếu có
  script gốc, hãy đối chiếu lại. Nếu lúc train bạn dùng thứ tự feature khác, kết quả sẽ SAI mà
  không báo lỗi (shape vẫn đúng 2050).

**Ensemble.** majority vote giữa Model A và Model B; hoà → trung bình xác suất với ngưỡng 0.5;
không có ảnh → Model A quyết định. `ensemble_method` được lưu vào CSV.

**MediaPipe.** `requirements.txt` ghim `mediapipe==0.10.14`: các bản 0.10.15+ đã bỏ
`mediapipe.python.solutions.hands` mà `backend/ml/model_a_dysgraphia.py` đang dùng — nâng cấp sẽ
lỗi `ModuleNotFoundError: No module named 'mediapipe.python'`.

## Weights (`weights/`)

| File | Vai trò |
| --- | --- |
| `writesense_model_a.joblib` | Random Forest cho Model A (bắt buộc) |
| `resnet50_backbone.onnx` | ResNet50 backbone cho Model B (ONNX, ưu tiên) |
| `model_b.onnx` | MLP head cho Model B (ONNX) |
| `model_b.pt` | MLP head cho Model B (dự phòng PyTorch) |
| `model_b_scaler_mean.npy`, `model_b_scaler_scale.npy` | Scaler cho 2 feature thủ công |
| `resnet50_openvino.{xml,bin}`, `resnet50_backbone_openvino.{xml,bin}`, `model_b_openvino*.{xml,bin}` | **Legacy, runtime không dùng — KHÔNG xoá** |

## Kiểm thử

```bash
python -m pytest backend/tests -v        # 32 test: services, API, kinematics
cd frontend && npm run lint && npm run build
```

Chạy thử end-to-end:

```bash
uvicorn backend.main:app --port 8000     # cửa sổ 1
cd frontend && npm run dev               # cửa sổ 2 → http://localhost:3000/screening
```

## Đã kiểm thử trong lần migrate này

- `python -m pytest backend/tests -q` → **32 passed**.
- `npm run lint` → sạch; `npm run build` → thành công (Next.js 16.3.5, TypeScript pass).
- E2E qua proxy của Next.js (`http://localhost:3000` → FastAPI):
  - `GET /api/health` → `ok`.
  - `POST /api/screening` (`model_a_source=live`, 5 frame + ảnh) → có `session_id`, Model A `OK`,
    Model B khả dụng, ensemble majority vote.
  - `POST /api/screening` (`model_a_source=video`, video thật ~5 MB) → 198 frame bàn tay, fps 30,
    `data/predictions.csv` có dòng mới và phiên xuất hiện đầu `GET /api/history`.
  - Gửi 4 frame (dưới ngưỡng) → `400` "cần >= 5 frame có bàn tay".
  - `POST /api/screening` (`model_a_source=video`, video 4K **289 MB / 48 giây**) qua proxy → `200`,
    1423 frame bàn tay, `score=0.315` (khoảng 100 giây xử lý MediaPipe). Trước khi nâng giới hạn và
    `proxyTimeout`, cùng video này bị `500` (`socket hang up`) sau đúng 30 giây do proxy dev.
  - Các trang `/`, `/screening`, `/history`, `/about`, `/results/{id}` → `200`.
- **Chưa kiểm thử tự động:** thao tác click trong browser (chọn file qua UI, ghi camera trực tiếp) —
  cần chạy tay trên máy có webcam.

## Ghi chú

- Phiên lưu ở `data/*.csv` (đã `.gitignore`), thay cho MySQL/SQLite trước đây; `parkinson_data.db`
  không còn dùng.
- Upload tối đa **4096 MB** (`MAX_VIDEO_SIZE_MB` trong `backend/config.py`; UI dùng
  `MAX_VIDEO_MB` trong `frontend/lib/constants.ts`). `frontend/next.config.ts` cũng chặn body của
  proxy `/api/*` qua `experimental.proxyClientMaxBodySize` — giá trị này phải là **số byte**
  (chuỗi kiểu `"250mb"` không được parse nên giới hạn sẽ vô hiệu) và nên đặt **cao hơn** giới hạn
  của backend, nếu không proxy sẽ cắt body trước khi backend kịp trả `413`.
- `frontend/next.config.ts` cũng có `experimental.proxyTimeout`: mặc định của Next dev là **30 giây**
  (`proxyTimeout || 30000`), nên video 4K hoặc video dài sẽ bị proxy cắt giữa chừng (`socket hang up`)
  dù backend vẫn đang xử lý. Repo này đặt 30 phút.
- Kế hoạch/đặc tả của lần migrate nằm trong `docs/superpowers/plans/` và `docs/superpowers/specs/`.
- Đã biết (chưa xử lý): `/results/{id}` đọc lại phiên qua `GET /api/history/{id}`, mà
  `db.save_model_a()` chỉ lưu `features_json` + `model_a_output`, nên **xác suất (`score`), `status`
  và `quality` (fps/frames/duration) của Model A hiện không hiển thị lại được sau khi tải lại trang**.

