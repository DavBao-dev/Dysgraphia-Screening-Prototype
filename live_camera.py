"""
live_camera.py - Live webcam hand tracking (MediaPipe chay trong trinh duyet).

Component nay chay MediaPipe Hands bang JavaScript trong browser (60 FPS) va chi
gui chuoi landmark (T,21,3) ve Python 1 lan khi nguoi dung nhan Stop, qua co che
custom component cua Streamlit (declare_component + Streamlit.setComponentValue).

Can internet vi MediaPipe JS + model duoc tai tu CDN (jsdelivr).
"""
import os

import streamlit.components.v1 as components

COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_cam_component")

_live_cam = components.declare_component("live_cam", path=COMPONENT_DIR)


def render_live_cam(key=None):
    """Render component va tra ve gia tri gui tu browser (dict hoac None)."""
    return _live_cam(default=None, key=key)
