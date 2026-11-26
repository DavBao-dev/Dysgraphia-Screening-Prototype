# Kiểm tra đặc trưng của Model A trên DiaGraMo

Kiểm tra xem các đặc trưng động học mà Model A dùng (độ giật, biến thiên tốc độ, tỉ lệ dừng bút, năng lượng rung 4–12 Hz) có tách được trẻ có khó khăn về viết với trẻ bình thường trên dữ liệu thật hay không.

Đây là tín hiệu bút trên máy tính bảng, không phải điểm mốc bàn tay từ video, nên kết quả chỉ kiểm tra cách chọn đặc trưng, không phải độ chính xác của Model A.

## Dữ liệu

DiaGraMo: Zvončáková và cộng sự, *Multimodal Czech online handwriting and cognitive data from children with and without handwriting disabilities*. Zenodo, doi:10.5281/zenodo.18299326 (bản 2: record 21236910), giấy phép CC BY 4.0.

Bộ dữ liệu (1,36 GB) không được đưa vào kho mã nguồn. Tải `DiaGraMo-project.zip` về `<thư mục>/diagramo/`.

Nhãn lấy từ biến `group` trong `cognitiveTestCSV2data_cleaned.csv` (1 = có khó khăn về viết, 0 = phát triển bình thường).

## Chạy

```
python run_dg.py <thư mục chứa feat.py và diagramo/>
```

- `feat.py`: tính đặc trưng từ file SVC (x, y, thời gian, trạng thái bút), ở tần số gốc và sau khi hạ xuống 30 Hz.
- `run_dg.py`: tính đặc trưng cho bài chép câu (TSK15/16) và bài vẽ vòng (TSK9), rồi tính AUC kèm khoảng tin cậy 95% bằng bootstrap.
- `dg_features.csv`: đặc trưng theo từng trẻ.
- `dg_auc.csv`: AUC theo từng đặc trưng.

## Kết quả chính (bài chép câu, 30 Hz, 154 khó viết / 119 bình thường)

| Đặc trưng | AUC (KTC 95%) |
|---|---|
| Độ giật chuẩn hoá | 0,70 (0,63–0,76) |
| Biến thiên tốc độ | 0,64 (0,58–0,71) |
| Tỉ lệ dừng bút khi chạm giấy | 0,58 (0,51–0,65) |
| Thời gian hoàn thành | 0,76 (0,70–0,82) |
| Năng lượng rung 4–12 Hz | 0,51 (0,44–0,57) |

Random Forest trên các đặc trưng quỹ đạo, kiểm định chéo 5 phần theo trẻ và lặp 5 lần, đạt ROC-AUC 0,76 (0,65 nếu bỏ thời gian hoàn thành).
