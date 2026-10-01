# Thành viên 2: Histogram

Bấm Run ở `main.py` trong thư mục này, hoặc chạy từ thư mục gốc:

```bash
python3 TT2_Histogram/main.py
```

Chương trình chạy thẳng Histogram, không có menu và không chạy hai thuật toán khác. Một lần chạy chọn cấu hình trên training, xử lý đủ bốn WAV test và mở bốn figure ở bốn góc.

- `algorithm.py`: cấu hình, làm trơn, tìm đỉnh/valley và tính ngưỡng Histogram.
- `main.py`: điểm khởi chạy của riêng thành viên này.
- `ket_qua/`: bốn PNG, tham số training, CSV và `binh_luan_tung_hinh.md`.

Thuật toán đã xét bin 0, kiểm tra vị trí đỉnh nền và valley, học khoảng cách đỉnh trên training. Ngưỡng chính tính adaptive trên từng WAV test, không dùng LAB test để học lại. Fallback và cấu hình được học từ training.

Các hàm đọc dữ liệu, trích đặc trưng, đánh giá và vẽ hình dùng chung từ speech_silence ở gốc. Khi chuyển sang máy khác, giữ cấu trúc toàn dự án với các thư mục thuật toán, speech_silence và dữ liệu. Dùng `--root đường_dẫn` nếu dữ liệu nằm nơi khác; `--no-show` để chỉ lưu ảnh; `--noise` để khảo sát nhiễu.
