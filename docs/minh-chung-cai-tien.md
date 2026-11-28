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
| Cần ý kiến chuyên gia y khoa | Đội chưa tìm được chuyên gia để rà soát, nên đã làm 4 việc thay thế (chi tiết ở mục 1a): đối chiếu các đặc trưng với nghiên cứu đã công bố, kiểm tra đặc trưng trên dữ liệu thật của 273 trẻ, để hệ thống nói rõ khi nó chưa chắc chắn và luôn chuyển trẻ tới chuyên gia, và chuẩn bị sẵn quy trình để chuyên gia gán nhãn độc lập khi có điều kiện. | [PR #5](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/5), [PR #6](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/6), [PR #7](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/7) |

### 1a. Khi chưa có chuyên gia, đội dựa vào đâu

**Câu hỏi:** "Nếu không có chuyên gia, làm sao chắc được mô hình cho ra kết quả đáng tin cậy?"

1. **Đặc trưng dựa trên nghiên cứu đã công bố.** Các đặc trưng của Model A (tốc độ, gia tốc, độ giật, độ run, dừng và nhấc bút) là những đặc trưng mà các nghiên cứu về khó viết đã dùng. Các số liệu dưới đây là kết quả của các nghiên cứu đó, đo trên bảng số, không phải độ chính xác của DysScan:
   - Asselborn và cộng sự, 2018 (*npj Digital Medicine*): 298 trẻ viết trên bảng số, Random Forest trên 53 đặc trưng; độ rộng dải tần số run, tốc độ và tỉ lệ nhấc bút phân biệt được trẻ khó viết.
   - Rosenblum, 2018 (*PLOS ONE*): 64 trẻ 10–12 tuổi; kết hợp số đo quá trình viết trên bảng số với chức năng điều hành phân loại đúng 98,4%.
   - Fallah và cộng sự, 2025 (*PLOS ONE*): tổng quan các phương pháp AI chẩn đoán khó viết từ dữ liệu viết trực tuyến và ngoại tuyến.
   - Schwellnus và cộng sự, 2012: 120 học sinh lớp 4; kiểu cầm bút không ảnh hưởng tốc độ hay độ dễ đọc của chữ, nên DysScan không chấm cách cầm bút.
2. **Kiểm tra trên dữ liệu thật của trẻ.** Nhãn của bộ DiaGraMo lấy từ chẩn đoán rối loạn học tập có sẵn trong bộ dữ liệu, tức đã có chuyên môn đứng sau. Trên 273 trẻ Séc 8–12 tuổi (154 khó viết, 119 bình thường): độ giật chuẩn hoá AUC 0,70, biến thiên tốc độ AUC 0,64, thời gian hoàn thành bài chép AUC 0,76; Random Forest trên các đặc trưng quỹ đạo, kiểm định chéo theo trẻ, ROC-AUC 0,76. Đây là kiểm tra cách chọn đặc trưng, không phải độ chính xác của Model A trên video. [PR #5](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/5)
3. **Hệ thống nói rõ khi nó chưa chắc chắn.** Phiếu kết quả có 3 mức chắc chắn; khi chưa chắc hoặc chưa đủ căn cứ thì nói rõ và không đưa ra kết luận. Phiếu luôn khuyên gặp chuyên gia (chuyên viên tâm lý học đường, hoạt động trị liệu, bác sĩ nhi khoa phát triển) thay vì dán nhãn trẻ. [PR #6](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/6), [PR #7](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/pull/7)
4. **Quy trình sẵn sàng cho chuyên gia.** Khi có điều kiện thử với trẻ thật: chỉ thu khi có văn bản đồng ý của phụ huynh và nhà trường, trẻ chỉ ghi bằng mã, chuyên gia gán nhãn độc lập theo thang đo do chuyên gia đề xuất trước khi xem kết quả của hệ thống, sau đó nhận xét về nhãn, mức hữu ích và cách diễn đạt trên phiếu. Bước đồng ý và điều khoản xử lý dữ liệu đã có trong ứng dụng. [`394a04f`](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype/commit/394a04f)

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
