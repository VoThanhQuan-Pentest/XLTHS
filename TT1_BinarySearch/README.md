# Thành viên 1: Binary Search

Phân khung cố định 25 ms, bước dịch 10 ms cho cả training và test. Ngưỡng được học lại từ training với cấu hình này; không còn chọn độ dài khung bằng Cross Validation.

[Báo cáo đầy đủ](BAO_CAO_BINARY_SEARCH.md) có công thức, ký hiệu tương ứng với mã, ví dụ tính STE/LAB/Binary Search, hình và kết quả của cả bốn WAV test.

Bấm Run ở `main.py` trong thư mục này, hoặc chạy từ thư mục gốc:

```bash
python3 TT1_BinarySearch/main.py
```

Chương trình chạy thẳng Binary Search, không có menu và không chạy hai thuật toán khác. Một lần chạy huấn luyện bằng TinHieuHuanLuyen, xử lý đủ bốn WAV trong TinHieuKiemThu và mở bốn figure ở bốn góc.

- `algorithm.py`: toàn bộ mã tìm ngưỡng Binary Search để giải thích với giảng viên.
- `main.py`: điểm khởi chạy của riêng thành viên này.
- `ket_qua/`: bốn PNG, tham số training, CSV và `binh_luan_tung_hinh.md`.

Các hàm đọc WAV/LAB, tính STE/F0, đánh giá, vẽ hình nằm trong thư mục dùng chung `speech_silence/` ở gốc. Dữ liệu cũng nằm ở gốc, không nhân bản. Khi chuyển dự án sang máy khác, giữ cả ba thư mục thuật toán, speech_silence và dữ liệu cùng cấu trúc. Nếu dữ liệu đặt ở nơi khác, dùng `--root đường_dẫn`.

Dùng `--no-show` để chỉ lưu ảnh; `--noise` để khảo sát nhiễu. Mặc định demo nhanh. Ngưỡng Binary Search học chung từ bốn WAV training và giữ cố định khi đánh giá test.
