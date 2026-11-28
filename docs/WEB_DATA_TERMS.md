# Điều khoản và nút xác nhận trên web

- `/terms`: danh sách điều khoản, không phải hợp đồng; có nút in/lưu.
- `/screening`: chỉ mở các thành phần nhập dữ liệu/camera sau khi xác nhận được API ghi nhận.
- `GET /api/consent/policy`: nội dung, phiên bản, SHA-256 và trạng thái sẵn sàng.
- `POST /api/consent`: kiểm tra từng lựa chọn; giáo viên phải cung cấp mã hồ sơ đồng ý riêng. Lưu thời điểm UTC của máy chủ và bản sao chính xác điều khoản vào Supabase trước khi cấp bằng chứng có chữ ký HMAC, hiệu lực 4 giờ.
- Cả ba API phân tích yêu cầu `X-Consent-Token`. Thiếu, sửa chữ ký, hết hạn hoặc điều khoản thay đổi đều bị từ chối trước khi gọi mô hình. Không lưu token trong localStorage hoặc URL.

## Cấu hình bản riêng

1. Điền các biến server trong `deploy/consent.env.example`, tạo khóa ký ngẫu nhiên ít nhất 32 ký tự và dùng cùng khóa trên các worker. Không commit khóa.
2. Tạo dự án Supabase thực sự tại Singapore; chạy `deploy/supabase/consent.sql`. RLS bật và không cấp quyền anon/authenticated; chỉ backend giữ service role key. Cấu hình xóa bằng chứng quá 24 tháng và xử lý yêu cầu xóa sớm.
3. Bảo vệ toàn bộ website và backend bằng hệ thống đăng nhập/phân quyền của bản riêng, bao gồm `/api/history`, tệp CSV và cổng backend. Xác nhận trên web KHÔNG thay thế xác thực và KHÔNG tự chứng minh tư cách đại diện. Chỉ đặt `CONSENT_PRIVATE_ACCESS_VERIFIED=true` sau khi kiểm tra truy cập chưa đăng nhập và truy cập chéo. Giá trị này là xác nhận vận hành, không phải chức năng đăng nhập mới.
4. `CONSENT_APP_LOCATION` phải ghi đúng nhà cung cấp/quốc gia của máy phân tích, khác với Supabase. Khi thiếu cấu hình, API trả 503 và nút xác nhận bị khóa. Lỗi ghi Supabase không được cho tiếp tục.
5. Repo demo có chức năng giả lập kết quả: bản thu thật phải build `DEMO_MODE=0` (tương ứng `NEXT_PUBLIC_DEMO_MODE=0`). Không thu dữ liệu thật trên Hugging Face demo công khai hiện tại.
6. Xác định người có năng lực và căn cứ đại diện phù hợp cho bên tổ chức trước khi thu thật. Ba tên thành viên không tự tạo tư cách pháp nhân hoặc quyền đại diện.

## Phạm vi lưu dữ liệu

Thay đổi này lưu bằng chứng đồng ý ở Supabase; kết quả sàng lọc vẫn là CSV trên máy ứng dụng. Không tuyên bố toàn bộ dữ liệu đã chuyển sang Supabase. Video/ảnh tạm vẫn bị xóa sau phân tích; chưa bổ sung kho giữ video 90 ngày. Không thu đồng ý nghiên cứu khi chưa có luồng nghiên cứu riêng. Chỉ đặt `CONSENT_SUPABASE_STORAGE_VERIFIED=true` sau khi luồng lưu kết quả đã chuyển hoàn toàn sang Supabase và kiểm tra hạn xóa 30 ngày cùng việc xóa sớm. Cờ này mặc định false vì bản vá này chỉ tích hợp kho bằng chứng đồng ý; nó không chuyển các bảng kết quả CSV hiện có. Thiết lập tác vụ xóa định kỳ cho kết quả và bằng chứng đồng ý trong môi trường triển khai. Bản sao lưu cần được bên vận hành quản lý theo cùng hạn.

Liên hệ được người dùng cung cấp: phanxuankhoa2010@gmail.com. Bản ghi là xác nhận tự khai; phụ huynh và giáo viên cần được xác minh ngoài bước click theo quy trình riêng. Đã đối chiếu Điều 3, 4, 9, 10, 14, 24 Luật 91/2025/QH15. Không sao chép quy tắc dữ liệu trẻ em từ văn bản đã hết hiệu lực để diễn giải luật mới.
