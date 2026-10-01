# Thành viên 3: Statistical Gaussian

Bấm Run ở `main.py` trong thư mục này, hoặc chạy từ thư mục gốc:

```bash
python3 TT3_Statistics/main.py
```

Chương trình chạy thẳng Statistical Gaussian, không có menu và không chạy hai thuật toán khác. Một lần chạy huấn luyện bằng bốn WAV training, xử lý đủ bốn WAV test và mở bốn figure ở bốn góc.

- `algorithm.py`: hàm CDF tự viết và cách chọn ngưỡng từ hai phân bố Gaussian.
- `main.py`: điểm khởi chạy của riêng thành viên này.
- `ket_qua/`: bốn PNG, meanSp/stdSp/meanSil/stdSil và ngưỡng trong JSON, CSV cùng `binh_luan_tung_hinh.md`.

Ngưỡng Gaussian học chung từ các khung Speech/Silence có nhãn trong training và giữ cố định trên test. LAB test chỉ phục vụ đánh giá.

Các hàm đọc dữ liệu, STE/F0, đánh giá và vẽ hình dùng chung từ speech_silence ở gốc. Khi chuyển sang máy khác, giữ cấu trúc toàn dự án với các thư mục thuật toán, speech_silence và dữ liệu. Dùng `--root đường_dẫn` nếu dữ liệu nằm nơi khác; `--no-show` để chỉ lưu ảnh; `--noise` để khảo sát nhiễu.
