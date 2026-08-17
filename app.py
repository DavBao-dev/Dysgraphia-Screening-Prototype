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
import live_camera

st.set_page_config(page_title="Dysgraphia/Parkinson Screening Prototype", layout="centered")
db.init_db()

st.title("Dysgraphia Screening Prototype")
st.caption(
    "Model A: video cu dong tay -> MediaPipe (Google) -> feature (chua co bo phan loai)  |  "
    "Model B: anh chu viet -> ResNet50 + MLP head -> 0/1  |  Ket qua luu vao CSV (thu muc data/)."
)

st.sidebar.header("Duong dan file weight")
path_model_b_head = st.sidebar.text_input("Model B - MLP head weight (.pt)", value="weights/model_b_classifier.pt")
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

run = st.button("Chay chan doan", type="primary", width="stretch")

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
            st.caption("Da luu ket qua vao cac file CSV (thu muc data/).")

        except FileNotFoundError as e:
            st.error(f"Khong tim thay file weight: {e}. Kiem tra duong dan trong sidebar.")
        except RuntimeError as e:
            st.error(str(e))
        except ValueError as e:
            st.error(f"Loi du lieu: {e}")
        except Exception as e:
            st.error(f"Loi khi xu ly: {e}")

# =====================================================================
# Model A - LIVE CAMERA (track tay truc tiep tu webcam ngay trong Streamlit)
# =====================================================================
st.divider()
st.subheader("Model A - Live Camera (track tay truc tiep)")
st.caption(
    "Nhan **Start** de mo webcam va MediaPipe theo doi ban tay truc tiep ngay "
    "trong Streamlit (khong can upload video). Nhan **Stop** de dung va tinh "
    "feature (jerk / tremor / entropy...) tu chuoi keypoint vua thu duoc."
)

if "cam_running" not in st.session_state:
    st.session_state.cam_running = False
if "cam_cap" not in st.session_state:
    st.session_state.cam_cap = None
if "cam_trajectory" not in st.session_state:
    st.session_state.cam_trajectory = []
if "cam_fps" not in st.session_state:
    st.session_state.cam_fps = 30.0
if "cam_features" not in st.session_state:
    st.session_state.cam_features = None


@st.cache_resource(show_spinner="Dang khoi tao MediaPipe Hands...")
def _get_hands():
    return live_camera.make_hands()


def _release_camera():
    cap = st.session_state.get("cam_cap")
    if cap is not None:
        cap.release()
    st.session_state.cam_cap = None


col_start, col_stop = st.columns(2)
with col_start:
    if st.button(
        "Start",
        type="primary",
        width="stretch",
        disabled=st.session_state.cam_running,
    ):
        st.session_state.cam_running = True
        st.session_state.cam_trajectory = []
        st.session_state.cam_features = None
        try:
            st.session_state.cam_cap = live_camera.open_camera(0)
            st.session_state.cam_fps = live_camera.get_camera_fps(st.session_state.cam_cap)
        except Exception as e:
            st.session_state.cam_running = False
            st.error(f"Khong mo duoc camera: {e}")

with col_stop:
    if st.button(
        "Stop",
        type="secondary",
        width="stretch",
        disabled=not st.session_state.cam_running,
    ):
        st.session_state.cam_running = False
        _release_camera()
        traj = st.session_state.cam_trajectory
        if len(traj) >= 15:
            try:
                st.session_state.cam_features = live_camera.extract_features_from_trajectory(
                    traj, st.session_state.cam_fps
                )
            except Exception as e:
                st.session_state.cam_features = None
                st.error(f"Loi khi tinh feature: {e}")
        else:
            st.session_state.cam_features = None


def _render_live_camera():
    """Doc 1 frame tu webcam, ve landmark va hien thi len Streamlit.

    Duoc auto-rerun dinh ky (Streamlit >= 1.37) de tao hieu ung video truc tiep.
    """
    if not st.session_state.cam_running:
        return
    cap = st.session_state.get("cam_cap")
    if cap is None or not cap.isOpened():
        return
    ok, frame = cap.read()
    if not ok:
        st.session_state.cam_running = False
        _release_camera()
        return
    annotated, landmarks = live_camera.process_frame(frame, _get_hands())
    if landmarks is not None:
        st.session_state.cam_trajectory.append(landmarks)
    st.image(live_camera.resize_for_display(annotated), channels="BGR", width="stretch")
    st.caption(f"Da thu duoc {len(st.session_state.cam_trajectory)} frame co ban tay.")


# Wrap thanh fragment tu dong lam moi. CAM_REFRESH_SECONDS cang nho => FPS cang
# cao. 1/30 ~ 30 FPS. Neu thay giat/lag thi tang len (vd 0.05 ~ 20 FPS).
# Luu y: moi vong phai round-trip qua websocket + gui lai khung hinh, nen FPS
# thuc te bi gioi han boi do tre mang/trinh duyet (thuong toi da 20-30 FPS).
CAM_REFRESH_SECONDS = 1.0 / 30.0
_frag = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None)
if _frag is not None:
    try:
        _render_live_camera = _frag(run_every=CAM_REFRESH_SECONDS)(_render_live_camera)
    except TypeError:
        _render_live_camera = _frag()(_render_live_camera)

_render_live_camera()

if not st.session_state.cam_running:
    if st.session_state.cam_features is not None:
        st.markdown("**Feature vua trich xuat (Model A):**")
        st.json(st.session_state.cam_features)
    elif st.session_state.cam_trajectory:
        st.info(
            f"Da dung. Thu duoc {len(st.session_state.cam_trajectory)} frame co tay "
            "(< 15 frame - chua du de tinh feature)."
        )

st.divider()
if st.checkbox("Xem lich su cac lan chan doan (doc tu CSV)"):
    history = db.get_history()
    if history:
        st.dataframe(pd.DataFrame(history), width="stretch")
    else:
        st.info("Chua co du lieu nao trong CSV.")
