# XLTHS — Nhóm 03

Đề tài: **Phân đoạn tín hiệu thành tiếng nói và khoảng lặng**.

| Thành viên | Thuật toán | Mã Python | Notebook riêng |
|---|---|---|---|
| Võ Thanh Quân | Binary Search | TT1_BinarySearch | VoThanhQuan_BinarySearch.ipynb |
| Vương Quốc Trung | Histogram | TT2_Histogram | VuongQuocTrung_Histogram.ipynb |
| Đinh Huỳnh Nguyên Khang | Statistical Gaussian | TT3_Statistics | DinhHuynhNguyenKhang_Statistics.ipynb |

## Cấu trúc

```text
XLTHS/
├── 03-Phân đoạn tín hiệu thành tiếng nói và khoảng lặng/
│   └── 3 notebook .ipynb đã chạy và lưu kết quả
├── TT1_BinarySearch/
│   ├── main.py, algorithm.py, __init__.py
│   ├── BAO_CAO_BINARY_SEARCH.md
│   └── ket_qua/
├── TT2_Histogram/
│   ├── main.py, algorithm.py, __init__.py
│   └── ket_qua/
├── TT3_Statistics/
│   ├── main.py, algorithm.py, __init__.py
│   └── ket_qua/
├── speech_silence/           # Đọc dữ liệu, đặc trưng, đánh giá, vẽ hình
├── TinHieuHuanLuyen/         # 4 WAV và LAB tương ứng; README.txt mô tả LAB
├── TinHieuKiemThu/           # 4 WAV và LAB tương ứng
├── tests/                   # Khung, thuật toán, metric và bảng mục tiêu BT1
├── tools/build_submission_notebooks.py
├── main.py                  # Chạy chọn thuật toán hoặc so sánh nhóm
├── requirements.txt
├── requirements-notebooks.txt
└── README.md
```

Trong `ket_qua/` của mỗi thành viên có bốn hình PNG, bảng MAE/RMSE, `tong_hop.csv`
phân biệt trung bình theo file/gộp biên, danh sách biên,
tham số huấn luyện, bình luận từng hình và bảng khảo sát nhiễu. Mã Python dùng chung
`speech_silence/` và dữ liệu tại gốc repo; cần giữ cấu trúc này để chạy lại.

## Chạy chương trình

Cài NumPy và Matplotlib bằng `python3 -m pip install -r requirements.txt`.
Chạy từ thư mục gốc, mỗi lệnh xử lý riêng một thuật toán trên cả bốn WAV test:

```bash
python3 TT1_BinarySearch/main.py
python3 TT2_Histogram/main.py
python3 TT3_Statistics/main.py
```

Thêm `--no-show` để chỉ lưu kết quả, `--noise` để chạy khảo sát nhiễu.
So sánh cả nhóm: `python3 main.py --algorithm all --no-noise --no-show`.
Kết quả chạy từ `main.py` gốc được tạo trong `ket_qua/demo/` và không đưa vào Git.

## Cách xử lý theo BT1

Cả ba thuật toán dùng cửa sổ danh định 25 ms căn giữa ô quyết định 10 ms, tâm đầu
5 ms. Mép WAV chỉ lấy mẫu thật; STE/MA chia cho số mẫu thực có, không đệm zero.
STE chuẩn hóa theo max riêng từng WAV. Khoảng Silence dưới 200 ms được lấp, kể cả
ở đầu/cuối; riêng zero-audio luôn giữ Silence. Không loại Speech ngắn dưới 100 ms.

- Binary chọn median trong `[1,5,9,11,15,21]`, lọc sau chuẩn hóa và không chuẩn hóa
  lại. Chỉ giữ quan sát overlap khi cân bằng diện tích nhầm lẫn. Hiện học được
  median 15 và T xấp xỉ 0,001605424181.
- Histogram cố định 128 bins/trơn 3 bins, chọn hai cực đại đầu theo trục STE.
  W được chọn trong `[1,2,5,10,15,20,30,50]`, hiện W=30. Ngưỡng adaptive theo từng
  WAV; thiếu hai đỉnh dùng mean normalized STE của chính WAV đó.
- Statistics học mean/std population từ toàn bộ khung TRAIN có nhãn, sigma floor
  1e-8; ưu tiên giao mật độ Gaussian giữa hai mean. Hiện T xấp xỉ 0,002763416581.

Chọn median/W trên toàn bộ bốn TRAIN theo thứ tự **biên thừa/thiếu → MAE → tham số
nhỏ hơn**. Đây là hiệu chỉnh trên TRAIN, không còn LOO và không phải hiệu suất độc
lập. `tham_so_huan_luyen.json` ghi `calibration`, `feature_layout=centered_hop_v1`
và `training_protocol=train_calibration`; mô hình 25/10 ms cũ vẫn phải học lại.
LAB TEST chỉ đánh giá/vẽ chuẩn sau khi khóa mô hình. F0 không tham gia phân đoạn.

Biên cùng hướng được ghép greedy gần nhất trước, một-một, không cutoff 100/200 ms.
MAE/RMSE tính trên cặp ghép; đọc cùng số biên thừa/thiếu. `tong_hop.csv` và notebook
ghi rõ mean-file và pooled, không lấy trung bình RMSE từng file để gọi là RMSE gộp.

| WAV TEST | Binary MAE (ms) | Histogram MAE (ms) | Statistics MAE (ms) |
|---|---:|---:|---:|
| phone_F2 | 30 | 10 | 5 |
| phone_M2 | 0 | 5 | 5 |
| studio_F2 | 10 | 15 | 15 |
| studio_M2 | 5 | 15 | 10 |
| **Trung bình theo file** | **11,25** | **11,25** | **8,75** |

Cả ba có tám cặp biên ghép, không thừa/thiếu trên bốn TEST. Kết quả khớp báo cáo
BT1 trên bộ đề này; chưa chứng minh hiệu quả tương tự với mọi tín hiệu khác.
Không có mã BT1 gốc: bộ tám W, median lặp mép và quy tắc phụ chọn nghiệm là các
mặc định đã chốt dựa trên báo cáo và thử nghiệm tái tạo, không phải bản sao mã BT1.

## Bộ nộp

Chỉ nộp thư mục **03-Phân đoạn tín hiệu thành tiếng nói và khoảng lặng**.
Ba notebook tự chứa mã của từng sinh viên, có sẵn số liệu, bốn đồ thị và bình luận;
xem kết quả không cần WAV. Chạy lại cần dữ liệu ngoài bộ nộp và chỉnh `DATA_ROOT`.

**Chưa có PDF slide chung; sẽ bổ sung khi làm slide. Không nộp toàn bộ repo hoặc
chép WAV/LAB vào thư mục nộp.** Nhóm ba người cần bảng so sánh thuật toán trong slide.

Tạo lại notebook từ mã Python:

```bash
python3 -m venv --system-site-packages .venv-notebooks
.venv-notebooks/bin/python -m pip install -r requirements-notebooks.txt
.venv-notebooks/bin/python -m ipykernel install --prefix .venv-notebooks --name xlths-notebooks --display-name "Python (XLTHS notebooks)"
.venv-notebooks/bin/python tools/build_submission_notebooks.py
```

Công cụ thực thi notebook bằng kernel mới, đối chiếu mô hình, calibration,
metric từng WAV, mean-file/pooled và khảo sát nhiễu với kết quả của từng thành viên
và kiểm tra bộ nộp không chứa dữ liệu âm thanh. Có thể thêm `--only binary`,
`--only histogram` hoặc `--only statistical` để tạo lại riêng một notebook.

Kiểm tra mã: `python3 -m unittest discover -s tests -v` (26 test, gồm mục tiêu BT1).
