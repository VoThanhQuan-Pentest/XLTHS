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
├── tests/                   # Kiểm tra Histogram và cấu hình phân khung
├── tools/build_submission_notebooks.py
├── main.py                  # Chạy chọn thuật toán hoặc so sánh nhóm
├── requirements.txt
├── requirements-notebooks.txt
└── README.md
```

Trong `ket_qua/` của mỗi thành viên có bốn hình PNG, bảng MAE/RMSE, danh sách biên,
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

Cả ba thuật toán dùng khung 25 ms, bước dịch 10 ms và gộp khoảng lặng dưới 200 ms.
Binary Search/Gaussian học một ngưỡng chung trên bốn WAV training sau khi chuẩn hóa
STE riêng từng WAV. Histogram học cấu hình trên training rồi tính ngưỡng từ từng
WAV test. LAB test chỉ dùng đánh giá và vẽ biên chuẩn.

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

Công cụ thực thi notebook bằng kernel mới, đối chiếu với kết quả của từng thành viên
và kiểm tra bộ nộp không chứa dữ liệu âm thanh. Có thể thêm `--only binary`,
`--only histogram` hoặc `--only statistical` để tạo lại riêng một notebook.

Kiểm tra mã: `python3 -m unittest discover -s tests -v`.
