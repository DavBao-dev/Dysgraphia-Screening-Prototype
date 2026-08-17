"""
db.py - Quan ly MySQL. Model A xuat ra rat nhieu feature (xem
model_a_dysgraphia.py) nen luu duoi dang JSON cho linh hoat.
"""
import mysql.connector
import json
import uuid
from datetime import datetime

# Cấu hình kết nối MySQL (Bạn hãy thay đổi thông tin này cho phù hợp)
DB_CONFIG = {
    "host": "localhost",       # Ví dụ: 127.0.0.1
    "user": "root",            # Tên đăng nhập MySQL
    "password": "bao666579",# Mật khẩu MySQL
    "database": "parkinson_data", # Tên database (cần tạo trước trong MySQL)
    "port": 3306
}

def get_connection():
    """Tạo và trả về đối tượng kết nối MySQL."""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def init_db():
    """Khởi tạo các bảng nếu chưa tồn tại."""
    conn = get_connection()
    cur = conn.cursor()

    # Bảng sessions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(36) PRIMARY KEY,
        patient_id VARCHAR(100),
        created_at VARCHAR(50)
    )
    """)

    # Bảng model_a_features
    cur.execute("""
    CREATE TABLE IF NOT EXISTS model_a_features (
        feature_id VARCHAR(36) PRIMARY KEY,
        session_id VARCHAR(36),
        features_json LONGTEXT,      -- Toàn bộ dict feature
        model_a_output INT NULL,     -- NULL nếu chưa có bộ phân loại cho Model A
        model_a_note TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """)

    # Bảng model_b_features
    cur.execute("""
    CREATE TABLE IF NOT EXISTS model_b_features (
        feature_id VARCHAR(36) PRIMARY KEY,
        session_id VARCHAR(36),
        ink_thickness_mean FLOAT,
        baseline_deviation FLOAT,
        model_b_output INT NULL,
        model_b_probability FLOAT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """)

    # Bảng predictions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id VARCHAR(36) PRIMARY KEY,
        session_id VARCHAR(36),
        model_a_output INT NULL,
        model_b_output INT NULL,
        final_output INT,
        ensemble_method VARCHAR(50),
        predicted_at VARCHAR(50),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def new_session(patient_id: str) -> str:
    """Tạo phiên làm việc mới cho bệnh nhân."""
    conn = get_connection()
    cur = conn.cursor()
    session_id = str(uuid.uuid4())
    
    cur.execute(
        "INSERT INTO sessions (session_id, patient_id, created_at) VALUES (%s, %s, %s)",
        (session_id, patient_id, datetime.now().isoformat()),
    )
    conn.commit()
    cur.close()
    conn.close()
    return session_id


def save_model_a(session_id: str, features: dict, output=None, note: str = ""):
    """Lưu trữ các features và kết quả của Model A."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO model_a_features (feature_id, session_id, features_json, model_a_output, model_a_note)
           VALUES (%s, %s, %s, %s, %s)""",
        (str(uuid.uuid4()), session_id, json.dumps(features), output, note),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_model_b(session_id: str, ink_thickness_mean: float, baseline_deviation: float, output: int, probability: float):
    """Lưu trữ các features và kết quả của Model B."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO model_b_features
           (feature_id, session_id, ink_thickness_mean, baseline_deviation, model_b_output, model_b_probability)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (str(uuid.uuid4()), session_id, float(ink_thickness_mean), float(baseline_deviation), output, float(probability)),
    )
    conn.commit()
    cur.close()
    conn.close()


def save_prediction(session_id: str, out_a, out_b, final_out: int, method: str):
    """Lưu trữ kết quả dự đoán cuối cùng (Ensemble)."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """INSERT INTO predictions
           (prediction_id, session_id, model_a_output, model_b_output, final_output, ensemble_method, predicted_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (str(uuid.uuid4()), session_id, out_a, out_b, final_out, method, datetime.now().isoformat()),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_history(limit: int = 50):
    """Lấy lịch sử dự đoán mới nhất."""
    conn = get_connection()
    # Dùng dictionary=True để kết quả fetch ra là danh sách các dict
    cur = conn.cursor(dictionary=True)
    
    cur.execute(
        """
        SELECT p.predicted_at, p.session_id, s.patient_id,
               p.model_a_output, p.model_b_output, p.final_output, p.ensemble_method
        FROM predictions p
        JOIN sessions s ON p.session_id = s.session_id
        ORDER BY p.predicted_at DESC
        LIMIT %s
        """,
        (int(limit),),
    )
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    return rows