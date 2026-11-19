"""
image_features.py - Trich xuat 2 feature thu cong tu anh chu viet, dung
lam dau vao bo sung cho Model B (ghep voi embedding 2048-d cua ResNet50).

Dung OpenCV, khong can model rieng. 2 feature nay PHAI dung thu tu va cong
thuc GIONG HET luc ban train MLP head - neu khac cong thuc, ket qua se sai
ma khong bao loi gi ca (vi shape van dung 2050).
"""
import numpy as np
import cv2


def normalize_handwriting(image_bytes: bytes) -> bytes:
    """
    Dua moi anh chu viet ve cung mot dang truoc khi vao Model B: anh xam, nhi phan
    hoa (Otsu), muc DEN tren nen TRANG, tra ve PNG bytes.

    Ly do: bo du lieu huan luyen (Mendeley) la chu TRANG tren nen DEN, con anh chup
    vo that la chu TOI tren nen SANG. Muc luon chiem it dien tich hon nen, nen lop
    pixel chiem thieu so sau khi nhi phan hoa duoc coi la muc. Ca train_model_b.py va
    model_b_service deu goi ham nay, de luc train va luc chay app nhin thay anh giong nhau.
    """
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Khong doc duoc anh, kiem tra lai dinh dang file.")

    _, bright = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    ink_is_bright = np.count_nonzero(bright) < bright.size / 2
    ink_mask = bright > 0 if ink_is_bright else bright == 0
    canonical = np.where(ink_mask, 0, 255).astype(np.uint8)

    ok, buf = cv2.imencode(".png", canonical)
    if not ok:
        raise ValueError("Khong ma hoa duoc anh sau khi chuan hoa.")
    return buf.tobytes()


def extract_ink_and_baseline_features(image_bytes: bytes) -> dict:
    """
    Tra ve dict 2 feature:
      - ink_thickness_mean: do day net muc trung binh (uoc luong qua
        dien tich / chieu dai cua tung thanh phan lien thong)
      - baseline_deviation: do lech chuan vi tri Y cua cac thanh phan chinh
        so voi duong ke (proxy cho "chenh lech chu so voi duong ke tap")

    Gia dinh muc TOI tren nen SANG: hay truyen vao anh da qua normalize_handwriting().
    """
    file_bytes = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Khong doc duoc anh, kiem tra lai dinh dang file.")

    _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    component_stats = stats[1:]  # bo qua label 0 (background)
    component_centroids = centroids[1:]

    if len(component_stats) == 0:
        return {"ink_thickness_mean": 0.0, "baseline_deviation": 0.0}

    areas = component_stats[:, cv2.CC_STAT_AREA]
    widths = component_stats[:, cv2.CC_STAT_WIDTH]
    heights = component_stats[:, cv2.CC_STAT_HEIGHT]
    thickness_est = areas / np.maximum(widths, heights)
    ink_thickness_mean = float(np.mean(thickness_est))

    mean_area = np.mean(areas)
    main_components_y = component_centroids[areas >= 0.2 * mean_area][:, 1]
    baseline_deviation = float(np.std(main_components_y)) if len(main_components_y) > 1 else 0.0

    return {"ink_thickness_mean": ink_thickness_mean, "baseline_deviation": baseline_deviation}
