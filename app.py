"""
app.py - Giao dien Streamlit.
Model A: video HOAC live camera -> MediaPipe -> Random Forest (writesense) -> 0/1
Model B: anh -> ResNet50 embedding + 2 feature thu cong -> MLP head -> 0/1 (null neu khong co anh)
Ensemble: majority vote giua 2 output.

Chay: streamlit run app.py
"""
import tempfile
import os
import json

import streamlit as st
import pandas as pd

import db
import inference
import inference_openvino
import image_features
import model_a_adapter
import live_camera
import dysgraphia_predictor
import numpy as np

st.set_page_config(page_title="Dysgraphia/Parkinson Screening Prototype", layout="centered")
db.init_db()

st.title("Dysgraphia Screening Prototype")
st.caption(
    "Model A: video / live camera -> MediaPipe + Random Forest -> 0/1  |  "
    "Model B: anh chu viet -> ResNet50 + MLP head -> 0/1 (null neu khong co anh)  |  "
    "Ket qua: majority vote."
)

st.sidebar.header("Duong dan file weight")
path_model_a = st.sidebar.text_input("Model A - classifier (.joblib)", value="weights/writesense_model_a.joblib")
path_model_b_head = st.sidebar.text_input("Model B - MLP head weight (.pt)", value="weights/model_b_classifier.pt")
st.sidebar.caption(
    "Model A: Random Forest (.joblib) tren 18 feature co ban. Model B: MLP head (.pt)."
)


@st.cache_resource(show_spinner="Dang load ResNet50 backbone (ImageNet pretrained)...")
def get_backbone():
    return inference.load_resnet50_backbone()


@st.cache_resource(show_spinner="Dang chuan bi OpenVINO ResNet50 (lan dau se convert model)...")
def get_backbone_openvino():
    return inference_openvino.load_resnet50_openvino()


@st.cache_resource(show_spinner="Dang load Model B head...")
def get_head(path):
    return inference.load_model_b_head(path)


@st.cache_resource(show_spinner="Dang load Model A classifier...")
def get_model_a(path):
    return dysgraphia_predictor.DysgraphiaPredictor.load(path)


patient_id = st.text_input("Ma benh nhan (patient_id)", value="patient_001")


# Khoi tao cac key ket qua live camera (luon co san de tranh KeyError o phan chay)
if "cam_features" not in st.session_state:
    st.session_state.cam_features = None
if "cam_prob_a" not in st.session_state:
    st.session_state.cam_prob_a = None
if "cam_out_a" not in st.session_state:
    st.session_state.cam_out_a = None
if "cam_status" not in st.session_state:
    st.session_state.cam_status = "OK"
if "_last_cam_value" not in st.session_state:
    st.session_state._last_cam_value = None


# =====================================================================
# MODEL A - nguon du lieu: upload video HOAC live camera
# =====================================================================
st.subheader("Model A - Hand kinematics (MediaPipe + Random Forest)")
model_a_mode = st.radio("Nguon du lieu Model A", ["Upload video", "Live camera"], horizontal=True)

video_file = None

if model_a_mode == "Upload video":
    video_file = st.file_uploader("Upload video (mp4/mov/avi)", type=["mp4", "mov", "avi"], key="video")
    st.caption("Can video co canh tay dang viet (khong dung anh tinh - can chuoi thoi gian de tinh jerk/tremor).")

else:  # Live camera - MediaPipe chay trong trinh duyet (60fps)
    st.caption(
        "MediaPipe chay ngay trong trinh duyet (JavaScript) de dat 60 FPS thoi gian thuc. "
        "Nhan **Start** de mo camera, **Stop** de gui chuoi landmark ve Python va tinh Model A."
    )
    component_value = live_camera.render_live_cam(key="live_cam")

    if component_value is not None and component_value != st.session_state._last_cam_value:
        st.session_state._last_cam_value = component_value
        try:
            if isinstance(component_value, str):
                data = json.loads(component_value)
            else:
                data = component_value
            landmarks = np.array(data["landmarks"], dtype=np.float64)
            fps = float(data.get("fps", 30.0))
            if landmarks.ndim != 3 or landmarks.shape[1:] != (21, 3):
                raise ValueError(f"Landmarks shape khong hop le: {landmarks.shape}")
            if landmarks.shape[0] < 15:
                raise ValueError(f"Khong du frame co ban tay: can >= 15, moi duoc {landmarks.shape[0]} frame.")
            predictor_a = get_model_a(path_model_a)
            result_a = predictor_a.predict_kinematics(landmarks, fps=fps)
            st.session_state.cam_features = result_a["features"]
            st.session_state.cam_prob_a = result_a["risk_score"]
            st.session_state.cam_out_a = 1 if result_a["risk_score"] >= predictor_a.threshold else 0
            st.session_state.cam_status = result_a["status"]
        except Exception as e:
            st.session_state.cam_features = None
            st.session_state.cam_prob_a = None
            st.session_state.cam_out_a = None
            st.session_state.cam_status = "OK"
            st.error(f"Loi khi xu ly landmarks tu live camera: {e}")

    if st.session_state.cam_out_a is not None:
        if st.session_state.get("cam_status", "OK") != "OK":
            st.info(st.session_state.cam_status)
        st.markdown(
            f"**Model A (live camera):** Output `{st.session_state.cam_out_a}` | "
            f"Xac suat `{st.session_state.cam_prob_a:.2%}`"
        )
        with st.expander("Xem feature chi tiet"):
            st.json(st.session_state.cam_features)


# =====================================================================
# MODEL B - anh chu viet (tuy chon)
# =====================================================================
st.subheader("Model B - Anh chu viet tay (tuy chon)")
image_file = st.file_uploader(
    "Upload anh chu viet (tuy chon - neu khong co anh, Model B tra ve null)",
    type=["png", "jpg", "jpeg"],
    key="img",
)


# =====================================================================
# CHAY CHAN DOAN
# =====================================================================
run = st.button("Chay chan doan", type="primary", width="stretch")

if run:
    # Kiem tra dieu kien dau vao truoc khi chay
    if model_a_mode == "Upload video" and video_file is None:
        st.error("Vui long upload video cho Model A.")
        st.stop()
    if model_a_mode == "Live camera" and st.session_state.cam_out_a is None:
        st.error("Hay Start + Stop live camera truoc khi chay chan doan.")
        st.stop()

    try:
        # ---------- Model A ----------
        if model_a_mode == "Upload video":
            with st.spinner("Dang chay Model A (MediaPipe + Random Forest)..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    tmp.write(video_file.read())
                    tmp_path = tmp.name
                try:
                    trajectory, fps = model_a_adapter.extract_landmarks_from_video(tmp_path)
                    if trajectory.shape[0] < 15:
                        raise ValueError(
                            f"Khong du du lieu: can >= 15 frame co ban tay, moi duoc {trajectory.shape[0]} frame."
                        )
                    predictor_a = get_model_a(path_model_a)
                    result_a = predictor_a.predict_kinematics(trajectory, fps=fps)
                    feat_a = result_a["features"]
                    prob_a = result_a["risk_score"]
                    out_a = 1 if prob_a >= predictor_a.threshold else 0
                    model_a_status = result_a["status"]
                finally:
                    os.unlink(tmp_path)
        else:  # Live camera
            out_a = st.session_state.cam_out_a
            prob_a = st.session_state.cam_prob_a
            feat_a = st.session_state.cam_features
            model_a_status = st.session_state.get("cam_status", "OK")

        # ---------- Model B (null neu khong co anh) ----------
        if image_file is None:
            out_b, prob_b, feat_b = None, None, None
        else:
            with st.spinner("Dang chay Model B (OpenVINO ResNet50 + MLP head)..."):
                head = get_head(path_model_b_head)
                image_bytes = image_file.read()
                feat_b = image_features.extract_ink_and_baseline_features(image_bytes)
                extra = [feat_b["ink_thickness_mean"], feat_b["baseline_deviation"]]
                try:
                    backbone = get_backbone_openvino()
                    out_b, prob_b = inference_openvino.run_model_b(backbone, head, image_bytes, extra_features=extra)
                except Exception as e:
                    st.warning(f"OpenVINO khong kha dung, dung PyTorch ResNet50: {e}")
                    backbone = get_backbone()
                    out_b, prob_b = inference.run_model_b(backbone, head, image_bytes, extra_features=extra)

        # ---------- ENSEMBLE: majority vote ----------
        outputs = [(o, p) for o, p in ((out_a, prob_a), (out_b, prob_b)) if o is not None]
        ones = sum(1 for o, _ in outputs if o == 1)
        zeros = sum(1 for o, _ in outputs if o == 0)
        if ones > zeros:
            final_out, vote_kind = 1, "majority"
        elif zeros > ones:
            final_out, vote_kind = 0, "majority"
        else:
            probs = [p for _, p in outputs if p is not None]
            avg = sum(probs) / len(probs) if probs else 0.5
            final_out, vote_kind = (1 if avg >= 0.5 else 0), "tie -> avg prob"
        method = f"majority_vote ({vote_kind})"

        # ---------- LUU CSV ----------
        session_id = db.new_session(patient_id)
        db.save_model_a(session_id, feat_a, out_a, note="Model A: Random Forest (writesense)")
        if feat_b is not None:
            db.save_model_b(session_id, feat_b["ink_thickness_mean"], feat_b["baseline_deviation"], out_b, prob_b)
        db.save_prediction(session_id, out_a, out_b, final_out, method)

        # ---------- HIEN THI ----------
        st.divider()
        st.subheader("Ket qua chan doan")
        label = "Co dau hieu nghi ngo" if final_out == 1 else "Khong co dau hieu ro ret"
        if final_out == 1:
            st.warning(f"**Ket luan cuoi cung (majority vote):** {label}")
        else:
            st.success(f"**Ket luan cuoi cung (majority vote):** {label}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Model A - Random Forest**")
            if model_a_status != "OK":
                st.info(model_a_status)
            st.markdown(f"Output: `{out_a}` | Xac suat: `{prob_a:.2%}`")
            with st.expander("Xem feature Model A"):
                st.json(feat_a)
        with c2:
            st.markdown("**Model B - ResNet50 + MLP head**")
            if out_b is None:
                st.markdown("Output: `null` (khong co anh)")
            else:
                st.markdown(f"Output: `{out_b}` | Xac suat: `{prob_b:.2%}`")
                with st.expander("Xem feature Model B"):
                    st.json(feat_b)

        st.markdown(f"Vote: Model A=`{out_a}`, Model B=`{out_b}` -> Final=`{final_out}` ({vote_kind})")
        st.caption(f"Session ID: {session_id} | Ensemble method: {method}")
        st.caption("Da luu ket qua vao cac file CSV (thu muc data/).")

    except FileNotFoundError as e:
        st.error(f"Khong tim thay file weight: {e}. Kiem tra duong dan trong sidebar.")
    except RuntimeError as e:
        st.error(str(e))
    except ValueError as e:
        st.error(f"Loi du lieu: {e}")
    except Exception as e:
        st.error(f"Loi khi xu ly: {e}")


st.divider()
if st.checkbox("Xem lich su cac lan chan doan (doc tu CSV)"):
    history = db.get_history()
    if history:
        st.dataframe(pd.DataFrame(history), width="stretch")
    else:
        st.info("Chua co du lieu nao trong CSV.")