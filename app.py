"""
app.py - Giao dien Streamlit.
Model A: video -> model_a_dysgraphia.py (MediaPipe cua Google) -> feature (chua co bo phan loai)
Model B: anh -> ResNet50 embedding + 2 feature thu cong -> MLP head (weight that cua ban) -> 0/1

Chay: streamlit run app.py
"""
import tempfile
import os

import streamlit as st
import pandas as pd

import db
import inference
import image_features
import model_a_adapter

st.set_page_config(page_title="Dysgraphia/Parkinson Screening Prototype", layout="centered")
db.init_db()

st.title("Dysgraphia Screening Prototype")
st.caption(
    "Model A: video cu dong tay -> MediaPipe (Google) -> feature (chua co bo phan loai)  |  "
    "Model B: anh chu viet -> ResNet50 + MLP head -> 0/1  |  Ket qua luu vao SQLite."
)

st.sidebar.header("Duong dan file weight")
path_model_b_head = st.sidebar.text_input("Model B - MLP head weight (.pt)", value="weights/model_b_resnet50.pt")
st.sidebar.caption(
    "Model A hien khong co file weight (chua co bo phan loai da train) - "
    "chi chay trich xuat feature. Xem model_a_adapter.py."
)


@st.cache_resource(show_spinner="Dang load ResNet50 backbone (ImageNet pretrained)...")
def get_backbone():
    return inference.load_resnet50_backbone()


@st.cache_resource(show_spinner="Dang load Model B head...")
def get_head(path):
    return inference.load_model_b_head(path)


patient_id = st.text_input("Ma benh nhan (patient_id)", value="patient_001")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Model A - Video cu dong tay")
    video_file = st.file_uploader("Upload video (mp4/mov)", type=["mp4", "mov", "avi"], key="video")
    st.caption("Can video co canh tay dang viet (khong dung anh tinh - can chuoi thoi gian de tinh jerk/tremor).")

with col2:
    st.subheader("Model B - Anh chu viet tay")
    image_file = st.file_uploader("Upload anh chu viet", type=["png", "jpg", "jpeg"], key="img")

run = st.button("Chay chan doan", type="primary", use_container_width=True)

if run:
    if not video_file or not image_file:
        st.error("Vui long upload ca video (Model A) va anh (Model B).")
    else:
        try:
            with st.spinner("Dang chay Model A (MediaPipe)..."):
                # luu video tam de OpenCV doc bang duong dan file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_file.read())
                    tmp_path = tmp.name
                try:
                    feat_a = model_a_adapter.run_model_a_pipeline(tmp_path)
                    out_a = None  # CHUA co bo phan loai cho Model A
                finally:
                    os.unlink(tmp_path)

            with st.spinner("Dang chay Model B (ResNet50 + MLP head)..."):
                backbone = get_backbone()
                head = get_head(path_model_b_head)

                image_bytes = image_file.read()
                feat_b = image_features.extract_ink_and_baseline_features(image_bytes)
                extra = [feat_b["ink_thickness_mean"], feat_b["baseline_deviation"]]
                out_b, prob_b = inference.run_model_b(backbone, head, image_bytes, extra_features=extra)

            # ---- ENSEMBLE ----
            # Model A chua co output 0/1 (chua co bo phan loai da train), nen
            # ket qua cuoi cung hien tam thoi = out_b. Khi co bo phan loai
            # Model A, sua doan nay de ket hop ca 2 (vd majority vote / meta model).
            final_out = out_b
            method = "model_b_only (model_a chua co bo phan loai)"

            # ---- LUU SQL ----
            session_id = db.new_session(patient_id)
            db.save_model_a(session_id, feat_a, out_a, note="Model A: chi co feature, chua co classifier")
            db.save_model_b(session_id, feat_b["ink_thickness_mean"], feat_b["baseline_deviation"], out_b, prob_b)
            db.save_prediction(session_id, out_a, out_b, final_out, method)

            # ---- HIEN THI ----
            st.divider()
            label = "Co dau hieu nghi ngo" if final_out == 1 else "Khong co dau hieu ro ret"
            if final_out == 1:
                st.warning(f"Ket qua tong hop: **{label}**")
            else:
                st.success(f"Ket qua tong hop: **{label}**")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Model A - feature (MediaPipe)**")
                st.caption("Chua co output 0/1 - can train bo phan loai (vd Random Forest) tren cac feature nay.")
                st.json(feat_a)
            with c2:
                st.markdown("**Model B**")
                st.markdown(f"Output: `{out_b}` | Xac suat: `{prob_b:.2%}`")
                st.json(feat_b)

            st.caption(f"Session ID: {session_id} | Ensemble method: {method}")
            st.caption("Da luu ket qua vao parkinson_data.db (SQLite).")

        except FileNotFoundError as e:
            st.error(f"Khong tim thay file weight: {e}. Kiem tra duong dan trong sidebar.")
        except RuntimeError as e:
            st.error(str(e))
        except ValueError as e:
            st.error(f"Loi du lieu: {e}")
        except Exception as e:
            st.error(f"Loi khi xu ly: {e}")

st.divider()
if st.checkbox("Xem lich su cac lan chan doan (doc tu SQLite)"):
    history = db.get_history()
    if history:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
    else:
        st.info("Chua co du lieu nao trong SQLite.")
