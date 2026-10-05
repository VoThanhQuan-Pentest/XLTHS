# Notebook nộp giữa kỳ của nhóm 03

Thư mục chuẩn bị nộp: **03-Phân đoạn tín hiệu thành tiếng nói và khoảng lặng**.

| Thành viên | Thuật toán | File riêng |
|---|---|---|
| Võ Thanh Quân | Binary Search | VoThanhQuan_BinarySearch.ipynb |
| Vương Quốc Trung | Histogram | VuongQuocTrung_Histogram.ipynb |
| Đinh Huỳnh Nguyên Khang | Statistical Gaussian | DinhHuynhNguyenKhang_Statistics.ipynb |

Mỗi notebook tự chứa đủ mã xử lý và thuật toán riêng, không gọi main.py hoặc import thư viện của repo. Có 11 cell mã chạy theo thứ tự từ kernel mới; output lưu sẵn gồm tham số training, số liệu kiểm chứng chéo, bốn hình test kèm F0/biên xanh đỏ, bình luận mỗi hình, bảng MAE/RMSE và khảo sát nhiễu. Cấu hình cố định 25 ms, bước dịch 10 ms, Silence tối thiểu 200 ms.

Notebook được mở xem trực tiếp mà không cần WAV. Chỉ khi muốn chạy lại mới cần NumPy, Matplotlib, IPython và dữ liệu WAV/LAB bên ngoài; chỉnh DATA_ROOT trong cell cấu hình đến nơi chứa hai thư mục TinHieuHuanLuyen và TinHieuKiemThu. Không nộp dữ liệu cùng notebook.

Thư mục nộp hiện chỉ có ba file .ipynb, không có WAV/LAB, CSV, .py, cache, dữ liệu âm thanh nhúng hay attachments. **PDF slide chung chưa được làm theo phạm vi bạn đã chốt. Bộ nộp chưa hoàn chỉnh cho tới khi bổ sung Slide_Chung_Nhom03.pdf.**

## Kết quả đã đối chiếu

| WAV test | Binary MAE | Histogram MAE | Gaussian MAE |
|---|---:|---:|---:|
| phone_F2 | 50 ms | 35 ms | 20 ms |
| phone_M2 | 10 ms | 10 ms | 10 ms |
| studio_F2 | 15 ms | 35 ms | 15 ms |
| studio_M2 | 5 ms | 30 ms | 10 ms |
| Gộp biên | 20,00 ms | 27,50 ms | 13,75 ms |

Biên thừa tương ứng 3/2/0, không thiếu biên. MAE chỉ tính các cặp ghép nên luôn đọc kèm số biên thừa/thiếu. Ngưỡng và bảng khảo sát nhiễu cũng khớp baseline của chương trình ở 25/10 ms.

## Tạo lại tại máy phát triển

Các công cụ tạo notebook và môi trường thực thi nằm ngoài thư mục nộp:

```bash
python3 -m venv --system-site-packages .venv-notebooks
.venv-notebooks/bin/python -m pip install -r requirements-notebooks.txt
.venv-notebooks/bin/python -m ipykernel install --prefix .venv-notebooks --name xlths-notebooks --display-name "Python (XLTHS notebooks)"
.venv-notebooks/bin/python tools/build_submission_notebooks.py
```

Có thể tạo lại một notebook với --only binary, --only histogram hoặc --only statistical. Công cụ học và dự đoán lại từ tín hiệu thật, kiểm tra khớp baseline, lưu output và kiểm tra không có file ngoài danh sách cho phép. Không thay thế tính toán bằng CSV/PNG có sẵn. Các ảnh phục vụ kiểm tra và snapshot số liệu nằm trong .notebook-build, không thuộc bộ nộp.

Theo thông báo giảng viên, hạn nộp nhóm là 21:00 thứ Tư ngày 07/10/2026. Khi có PDF, chỉ upload thư mục nộp đã kiểm tra; không upload toàn bộ repo vì repo làm việc có WAV/LAB.
