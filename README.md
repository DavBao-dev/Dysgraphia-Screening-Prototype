# Dysgraphia Screening Prototype (Streamlit + MySQL)

## Cai dat & chay

```bash
pip install -r requirements.txt
streamlit run app.py
```

**LUU Y VE MEDIAPIPE**: `requirements.txt` ghim cung `mediapipe==0.10.14`.
Ban KHONG duoc nang cap mediapipe len ban moi hon (0.10.15+), vi ban moi da
bo API `mediapipe.python.solutions.hands` ma file `model_a_dysgraphia.py`
cua ban dang dung - neu nang cap se bi loi
`ModuleNotFoundError: No module named 'mediapipe.python'`.

## Cau truc file

```
parkinson_prototype/
  app.py                   # Giao dien Streamlit
  model_a_dysgraphia.py    # File GOC cua ban (khong sua) - MediaPipe + tinh feature
  model_a_adapter.py       # Adapter: chay model_a_dysgraphia.py o che do headless
                            # (doc video da upload, khong dung cv2.imshow vi server
                            # khong co man hinh)
  image_features.py        # Trich 2 feature thu cong cho Model B (do day muc, lech dong)
  inference.py             # Load + chay Model B: ResNet50 backbone + MLP head (weight that)
  db.py                    # SQLite: luu feature + ket qua
  weights/model_b_resnet50.pt   # Weight MLP head cua ban (dat san trong nay)
  requirements.txt
```

## Kien truc Model B (suy ra TU CHINH file weight ban dua, khong doan)

State dict co cac key: `net.0` (Linear 2050->128), `net.3` (Linear 128->32),
`net.5` (Linear 32->1). Suy ra:

```
Input 2050-d = ResNet50 embedding (2048-d, ImageNet pretrained, bo fc) + 2 feature thu cong
  -> Linear(2050, 128) -> ReLU -> Dropout -> Linear(128, 32) -> ReLU -> Linear(32, 1) -> Sigmoid
```

`inference.py` da load thu va **khop 100%** voi file weight ban upload (test
thanh cong, khong loi size mismatch).

**QUAN TRONG - thu tu 2 feature thu cong**: code hien dang ghep
`[ink_thickness_mean, baseline_deviation]` theo dung thu tu ban mo ta ban dau
("do day muc" roi "chenh lech duong ke"). Neu luc train ban dung thu tu khac,
hoac cong thuc tinh feature khac voi `image_features.py`, ket qua se SAI ma
KHONG bao loi gi (vi shape van dung 2050) - day la diem duy nhat ban can tu
kiem tra lai, khong co cach nao code tu phat hien duoc.

## Model A - hien CHUA co bo phan loai

File `model_a_dysgraphia.py` ban dua chi co phan **trich xuat feature**
(dung MediaPipe Hands cua Google de lay 21 diem tren tay, tinh jerk, tremor,
spectral entropy,...) - CHUA co model phan loai da train (Random Forest/XGBoost
nhu ban de cap trong thiet ke ban dau).

- `app.py` hien dang chi chay Model B de ra ket qua cuoi cung
  (`ensemble_method = "model_b_only"`), feature cua Model A van duoc tinh va
  luu vao SQLite (cot `features_json` trong bang `model_a_features`) de sau
  nay dung train model.
- Khi ban co bo phan loai cho Model A (file `.pkl` cua sklearn/joblib hoac
  `.pt` cua PyTorch), sua ham trong `app.py`:
  ```python
  feat_a = model_a_adapter.run_model_a_pipeline(tmp_path)
  out_a = None  # <-- THAY DOAN NAY bang: out_a = your_model_a.predict(feat_a)
  ```
  roi sua lai `final_out`/`method` de ket hop ca 2 model (vd majority vote
  hoac meta classifier nhu ban de cap ban dau).

## Input Model A la VIDEO, khong phai anh tinh

`model_a_dysgraphia.py` can chuoi thoi gian (nhieu frame) de tinh jerk,
tremor (dao ham bac 2, 3 theo thoi gian, FFT) - **1 anh tinh khong du du
lieu** de tinh cac feature nay. App yeu cau upload video (mp4/mov/avi) quay
lai qua trinh viet, khong phai anh chup ket qua chu viet.

## Test da chay (khong chi la code ly thuyet)

- Load weight that `model_b_resnet50.pt` vao dung kien truc: **thanh cong,
  khong loi**.
- Chay full pipeline Model B (anh gia -> embedding -> concat -> MLP head ->
  sigmoid): **thanh cong**.
- Chay `model_a_adapter.py` voi video that qua MediaPipe (mo hinh Google):
  **thanh cong**, detect dung, bao loi ro rang khi video khong co tay.
- Tinh feature tu chuoi keypoint qua `EnhancedKinematicFeatureExtractor`:
  **thanh cong**, ra du 11 feature.

## Khi deploy that (khong con la prototype)

- Lan dau chay se tu tai weight ResNet50 ImageNet tu internet (can mang, vai
  chuc MB). Neu server khong co internet, tai truoc va luu vao
  `~/.cache/torch/hub/checkpoints/`.
- Video upload qua Streamlit gioi han dung luong mac dinh (200MB) - co the
  chinh trong `.streamlit/config.toml` (`maxUploadSize`).
