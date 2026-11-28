"""Versioned click consent; this is evidence of a declaration, not authentication."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Literal
from urllib.request import Request, urlopen

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, StrictBool

router = APIRouter(prefix="/api/consent", tags=["consent"])
VERSION = "2026-11-28.1"
TEAM = "Phan Xuân Khoa, Nguyễn Trần Gia Bảo, Cao Tùng Lâm"
CONTACT = "phanxuankhoa2010@gmail.com"


def policy():
    app_location = os.getenv("CONSENT_APP_LOCATION", "Máy chủ ứng dụng do nhóm vận hành")
    sections = [
        {"title": "1. Bên thu thập và đầu mối liên hệ", "text": f"Nhóm thực hiện: {TEAM}. Email tiếp nhận yêu cầu về dữ liệu: {CONTACT}. Bên vận hành phải xác định người chịu trách nhiệm và căn cứ đại diện phù hợp trước khi thu dữ liệu của trẻ."},
        {"title": "2. Dữ liệu được xử lý", "text": "Mã học sinh, video bàn tay khi viết hoặc chuỗi điểm mốc bàn tay, ảnh chữ viết nếu cung cấp, thông số trích xuất và kết quả sàng lọc. Không nhập họ tên trong mã học sinh; không ghi khuôn mặt, âm thanh, thẻ tên hoặc thông tin ngoài phạm vi. Kết quả phản ánh sức khỏe cần được bảo vệ như dữ liệu nhạy cảm."},
        {"title": "3. Mục đích và giới hạn", "text": "Chỉ phân tích để hỗ trợ sàng lọc khó khăn khi viết và cung cấp kết quả cho người có quyền nhận. Kết quả có thể sai và không thay thế chẩn đoán chuyên môn; không dùng để chấm điểm, kỷ luật hoặc phân biệt đối xử. Xác nhận này không cho phép nghiên cứu, huấn luyện mô hình, bán hoặc công khai dữ liệu."},
        {"title": "4. Nơi xử lý và lưu trữ", "text": f"Dữ liệu gửi qua mạng đến máy chạy ứng dụng: {app_location}. Video tải lên được gửi nguyên tệp; camera trực tiếp gửi điểm mốc bàn tay và tốc độ khung hình; ảnh được gửi khi cung cấp. Dữ liệu lưu trữ, gồm kết quả sàng lọc và bằng chứng đồng ý, được lưu trên Supabase, máy chủ tại Singapore. Video được truyền đến máy ứng dụng để phân tích; đây có thể là hoạt động chuyển dữ liệu ra nước ngoài."},
        {"title": "5. Thời hạn lưu và xóa", "text": "Video và ảnh chỉ được dùng tạm để phân tích rồi xóa. Kết quả được giữ tối đa 30 ngày từ khi tạo phiên. Bằng chứng đồng ý được giữ tối đa 24 tháng và rà soát xóa sớm. Thời hạn này là chính sách dự án. Việc giữ video lâu hơn hoặc dùng cho nghiên cứu phải được thông báo và chấp thuận riêng trước khi thực hiện."},
        {"title": "6. Người được tiếp cận và bảo vệ", "text": "Chỉ giáo viên được phân công, người đánh giá được giao nhiệm vụ và người quản trị cần thiết được tiếp cận. Bên vận hành phải bảo vệ toàn bộ ứng dụng bằng đăng nhập và phân quyền, bảo vệ đường truyền, nơi lưu và bản sao lưu. Không chia sẻ mã học sinh, ảnh, video hoặc kết quả trong nhóm công khai. Không sử dụng bản trình diễn có lịch sử công khai để thu dữ liệu thật của trẻ."},
        {"title": "7. Quyền và cách gửi yêu cầu", "text": f"Người đại diện và học sinh có quyền được biết, yêu cầu xem, sửa, cung cấp, xóa, rút lại sự đồng ý, hạn chế hoặc phản đối xử lý theo pháp luật. Gửi yêu cầu đến {CONTACT}, nêu mã học sinh hoặc mã xác nhận và nội dung đề nghị; không gửi video hoặc giấy tờ cá nhân qua mục công khai. Yêu cầu được xác minh và giải quyết theo thời hạn pháp luật; không mặc định mọi yêu cầu đều được thực hiện tức thì."},
        {"title": "8. Tự nguyện và ý kiến của trẻ", "text": "Người xác nhận phải là cha/mẹ, người đại diện hợp pháp hoặc giáo viên có sự đồng ý hợp lệ của người đại diện được lưu riêng và có thể kiểm chứng. Giáo viên không tự thay phụ huynh đồng ý. Phải giải thích bằng lời dễ hiểu và chỉ tiếp tục khi trẻ muốn tham gia; trẻ có thể dừng bất cứ lúc nào. Từ chối không ảnh hưởng kết quả học tập hoặc quyền được hỗ trợ."},
        {"title": "9. Ý nghĩa của nút xác nhận", "text": "Khi tự chọn các ô và bấm xác nhận, người dùng cho phép xử lý cho mục đích sàng lọc nêu trên. Hệ thống ghi mã xác nhận, thời điểm máy chủ, tư cách tự khai, mã hồ sơ đồng ý riêng nếu là giáo viên, phiên bản và bản sao điều khoản. Thao tác này không tự chứng minh danh tính hoặc quyền đại diện. Không đánh dấu sẵn; im lặng không phải đồng ý."},
        {"title": "10. Thay đổi điều khoản", "text": "Khi thay đổi đáng kể mục đích, loại dữ liệu, bên tiếp nhận hoặc nơi xử lý, bên vận hành phải thông báo và xin lại sự đồng ý khi cần. Điều khoản này là danh sách thông tin và lựa chọn xác nhận trên web, không phải hợp đồng ký giữa các bên; không hạn chế quyền theo pháp luật Việt Nam."},
    ]
    document = {"version": VERSION, "title": "Điều khoản xử lý dữ liệu cá nhân", "sections": sections}
    digest = hashlib.sha256(json.dumps(document, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    ready = all([os.getenv("CONSENT_PRIVATE_ACCESS_VERIFIED") == "true", os.getenv("CONSENT_SUPABASE_STORAGE_VERIFIED") == "true", os.getenv("CONSENT_APP_LOCATION"),
                 len(os.getenv("CONSENT_SIGNING_KEY", "")) >= 32, os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY")])
    return {**document, "policy_hash": digest, "ready": ready,
            "notice": "Chỉ thu dữ liệu thật trên bản riêng có kiểm soát truy cập. Bản triển khai chưa cấu hình đủ sẽ không nhận dữ liệu."}


def _audit(record):
    """Private Supabase table: no frontend access or service key exposure."""
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/data_consents"
    if not url.startswith("https://"):
        raise HTTPException(503, "Kho bằng chứng đồng ý phải sử dụng HTTPS.")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    request = Request(url, json.dumps(record, ensure_ascii=False).encode(), method="POST", headers={
        "apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=minimal"})
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 204):
                raise OSError("Consent store rejected record")
    except Exception as exc:
        raise HTTPException(503, "Chưa lưu được bằng chứng đồng ý. Chưa thể tiếp tục.") from exc


class Acceptance(BaseModel):
    version: str
    policy_hash: str
    role: Literal["parent", "representative", "teacher"]
    accepted: StrictBool
    child_assent: StrictBool
    authority_confirmed: StrictBool
    guardian_reference: str = ""


@router.get("/policy")
def get_policy():
    return policy()


@router.post("")
def accept(body: Acceptance):
    current = policy()
    if not current["ready"]:
        raise HTTPException(503, "Bản thu dữ liệu thật chưa được cấu hình đầy đủ.")
    if body.version != VERSION or body.policy_hash != current["policy_hash"]:
        raise HTTPException(409, "Điều khoản đã thay đổi. Vui lòng tải lại và đọc trước khi xác nhận.")
    if not all([body.accepted, body.child_assent, body.authority_confirmed]):
        raise HTTPException(403, "Cần sự đồng ý hợp lệ và ý kiến muốn tham gia của trẻ.")
    reference = body.guardian_reference.strip()
    if len(reference) > 120 or (body.role == "teacher" and not reference):
        raise HTTPException(400, "Giáo viên cần mã hồ sơ đồng ý của người đại diện; không ghi họ tên.")
    now = int(time.time())
    record = {"id": secrets.token_hex(16), "accepted_at": datetime.now(timezone.utc).isoformat(),
              "expires_at": now + 4 * 3600, "role": body.role, "guardian_reference": reference,
              "version": VERSION, "policy_hash": current["policy_hash"], "purpose": "screening",
              "accepted": True, "child_assent": True, "authority_confirmed": True,
              "document": {k: current[k] for k in ("title", "version", "sections")}}
    _audit(record)
    payload = base64.urlsafe_b64encode(json.dumps({"id": record["id"], "exp": record["expires_at"],
        "hash": current["policy_hash"]}, separators=(",", ":")).encode()).decode()
    signature = hmac.new(os.environ["CONSENT_SIGNING_KEY"].encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {"token": payload + "." + signature, "receipt_id": record["id"], "accepted_at": record["accepted_at"]}


def require_consent(x_consent_token: str = Header(default="")):
    current = policy()
    if not current["ready"]:
        raise HTTPException(503, "Chưa mở thu dữ liệu thật trên bản triển khai này.")
    try:
        payload, signature = x_consent_token.split(".")
        expected = hmac.new(os.environ["CONSENT_SIGNING_KEY"].encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Signature")
        data = json.loads(base64.urlsafe_b64decode(payload))
        if data["exp"] <= time.time() or data["hash"] != current["policy_hash"]:
            raise ValueError("Expired or changed policy")
        return data["id"]
    except Exception as exc:
        raise HTTPException(403, "Vui lòng đọc và xác nhận điều khoản trước khi phân tích.") from exc


def link_session(receipt_id, session_id):
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/screening_consent_links"
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    request = Request(url, json.dumps({"receipt_id": receipt_id, "session_id": session_id}).encode(), method="POST", headers={
        "apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json", "Prefer": "return=minimal"})
    try:
        with urlopen(request, timeout=15) as response:
            if response.status not in (200, 201, 204):
                raise OSError("Consent link rejected")
    except Exception as exc:
        raise HTTPException(503, "Chưa ghi nhận được liên kết phiên với xác nhận dữ liệu.") from exc
