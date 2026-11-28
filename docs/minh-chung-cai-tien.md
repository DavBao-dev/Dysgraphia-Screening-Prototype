# Minh chứng cải tiến – DysScan

Trang này liệt kê các cải tiến của dự án sau vòng trước, kèm bằng chứng kiểm chứng được: mỗi cải tiến dẫn tới commit hoặc pull request trên GitHub (có ngày giờ và người thực hiện), tệp kết quả đánh giá và các test tự động.

- Phiên bản trước: commit [`8985dfd`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/8985dfd) (19/09/2026).
- Toàn bộ thay đổi từ phiên bản đó đến nay: [so sánh `8985dfd...main`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/compare/8985dfd...main).
- Danh sách pull request đã gộp: [Pull requests](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pulls?q=is%3Apr+is%3Amerged).

## 1. Theo góp ý của ban giám khảo

| Góp ý | Cải tiến | Minh chứng |
|---|---|---|
| Báo cáo chưa đề cập số lượng mẫu test | Báo cáo bổ sung bảng số người và số mẫu cho từng loại dữ liệu. Model B được đánh giá bằng kiểm định chéo 5 phần **theo học sinh** trên 249 ảnh của 83 học sinh, kèm khoảng tin cậy 95%. | [PR #1](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/1), [`train_model_b.py`](../train_model_b.py), [`model_b_cv_report.json`](../model_b_cv_report.json) |
| Cần thử nghiệm trên dữ liệu thực tế | Kiểm tra các đặc trưng động học của Model A trên tín hiệu bút thật của 273 trẻ 8–12 tuổi (bộ dữ liệu công khai DiaGraMo), đo AUC từng đặc trưng kèm khoảng tin cậy. | [PR #5](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/5), [`evaluation/diagramo_feature_check/`](../evaluation/diagramo_feature_check/) |
| Cần ý kiến chuyên gia y khoa | Phiếu kết quả không đưa ra kết luận về trẻ mà luôn hướng tới chuyên gia; quy trình thử nghiệm thực tế có chuyên gia gán nhãn độc lập được mô tả trong báo cáo (mục 7d). Đội chưa tìm được chuyên gia để rà soát. | [PR #6](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/6), [PR #7](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/7) |

## 2. Mô hình AI

| Vấn đề phát hiện | Cải tiến | Kết quả và minh chứng |
|---|---|---|
| Trọng số Model B cũ được huấn luyện trong notebook với cách trích đặc trưng khác ứng dụng; chạy qua ứng dụng chỉ phát hiện 38,9% ảnh nguy cơ cao, kể cả trên chính dữ liệu đã học. | Chuẩn hoá ảnh (mực tối trên nền sáng) giống nhau khi huấn luyện và khi chạy; huấn luyện lại bằng đúng mã nguồn của ứng dụng. | Độ nhạy 83,2% (73,5–91,2%), độ đặc hiệu 82,2% (72,6–90,4%), ROC-AUC 0,900 (0,840–0,951); theo học sinh đúng 33/38 và 38/45. [`d38d8c8`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/d38d8c8) |
| Model A cũ phụ thuộc nhiều nhất vào tốc độ khung hình (fps, khoảng 38% độ quan trọng), tức điểm nguy cơ thay đổi theo cách quay video. | Bỏ `fps` và số khung hình, còn 16 đặc trưng; thêm script huấn luyện và đánh giá theo bản ghi. | Điểm nguy cơ không còn phụ thuộc vào tốc độ khung hình của video. [`b1e499e`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/b1e499e), [`model_a_cv_report.json`](../model_a_cv_report.json) |
| Chưa có bằng chứng các đặc trưng động học liên quan đến khó viết ở trẻ. | Tính lại đặc trưng theo cách của Model A trên dữ liệu DiaGraMo. | Độ giật chuẩn hoá AUC 0,70 (0,63–0,76); thời gian hoàn thành AUC 0,76 (0,70–0,82). [`e8b5592`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/e8b5592) |

## 3. Cách trình bày kết quả và đạo đức

| Cải tiến | Minh chứng |
|---|---|
| Phiếu kết quả có **mức độ chắc chắn** 3 mức (tín hiệu khá rõ / chưa chắc chắn / chưa đủ căn cứ) và lý do; khi video không dùng được, phiếu không đưa ra kết luận mà chỉ hướng dẫn quay lại. | [`39138ae`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/39138ae), [PR #6](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/6) |
| Khuyến nghị thay vì dán nhãn: quan sát thêm 2–4 tuần và gặp chuyên gia (chuyên viên tâm lý học đường, hoạt động trị liệu, bác sĩ nhi khoa phát triển). | [`39138ae`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/39138ae) |
| Lưu điểm và chất lượng video của Model A, để phiên mở lại vẫn hiển thị đúng mức độ chắc chắn. | [`202a556`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/202a556), [PR #7](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/7) |
| Giao diện dành cho giáo viên và phụ huynh, theo hướng dẫn ngôn ngữ dễ hiểu về sức khoẻ; nhận diện "vở ô li, mực tím". | [PR #4](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/4) ([`5868c06`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/5868c06), [`79c3e02`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/79c3e02)) |
| Chụp ảnh trang viết trực tiếp bằng camera, có xoay ảnh. | [`0cfb4e6`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/0cfb4e6) |

## 4. Bảo vệ dữ liệu trẻ em

| Cải tiến | Minh chứng |
|---|---|
| Điều khoản xử lý dữ liệu và bước xác nhận đồng ý bắt buộc trước khi sàng lọc (người đại diện xác nhận, trẻ đồng ý tham gia, giáo viên cần mã hồ sơ đồng ý riêng). Không có xác nhận hợp lệ thì API không chạy mô hình. | [`394a04f`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/394a04f), [`docs/DATA_PROCESSING_TERMS.vi.md`](DATA_PROCESSING_TERMS.vi.md) |
| Kết quả sàng lọc có thể lưu trong cơ sở dữ liệu PostgreSQL (đặt `DATABASE_URL`) thay vì tệp CSV, với Row Level Security để API công khai của nhà cung cấp không đọc được. | [`440b98e`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/440b98e) |
| Không lưu video hay ảnh của trẻ: video bị xoá ngay sau khi phân tích, ảnh chỉ được đọc trong bộ nhớ. | [`backend/services/model_a_service.py`](../backend/services/model_a_service.py) |

## 5. Triển khai và kiểm thử

| Cải tiến | Minh chứng |
|---|---|
| Đóng gói Docker để chạy thử qua Internet bằng HTTPS: một bản cho Hugging Face Spaces, một bản cho máy chủ ảo với Caddy tự cấp chứng chỉ. Bản chạy thử trên máy chủ tại Việt Nam yêu cầu đăng nhập trước mọi trang. | [PR #2](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/2), [PR #3](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/3) |
| Test tự động cho dịch vụ mô hình, API, đặc trưng động học, bước đồng ý và lưu trữ dữ liệu. | [`backend/tests/`](../backend/tests/) |
