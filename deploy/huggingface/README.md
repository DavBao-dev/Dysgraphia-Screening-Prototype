---
title: Dysgraphia Screening
emoji: ✍️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
short_description: Sàng lọc dấu hiệu khó viết qua chuyển động tay và chữ viết
---

# Dysgraphia Screening (demo)

Bản chạy thử của dự án [Dysgraphia Screening Prototype](https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype).
Ứng dụng chỉ hỗ trợ sàng lọc, **không phải công cụ chẩn đoán y tế**.

- Đây là máy chủ demo công khai: lịch sử phiên sàng lọc ai cũng xem được và bị xoá khi Space khởi động lại.
  Không tải lên dữ liệu thật của trẻ.
- Giới hạn video tải lên: 200 MB.

## Cách cập nhật Space

Space này chỉ chứa `Dockerfile` và `README.md` (sao chép từ thư mục `deploy/huggingface/` của repo GitHub).
Khi build, Dockerfile tự clone repo GitHub ở nhánh `main`. Muốn cập nhật bản mới: đẩy code lên `main`,
rồi vào **Settings → Factory rebuild** của Space.
