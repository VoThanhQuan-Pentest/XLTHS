# Demo bốn figure

Chạy hoặc bấm Run tại `main.py` một lần:

```bash
python3 main.py --no-noise
```

Mặc định chương trình dùng đủ bốn WAV trong `TinHieuKiemThu`, xử lý cả ba thuật toán và mở đúng bốn cửa sổ. Mỗi cửa sổ ứng với một WAV, chứa waveform, STE/ngưỡng/biên của cả ba thuật toán, logSTE/logMA và F0. Các plot có tiêu đề và nhãn trục. Chương trình tự đặt cửa sổ ở bốn góc trên backend Qt hoặc Tk.

Kết quả mới lưu trong `ket_qua/demo/`: bốn PNG có tên WAV, các bảng CSV, tham số đã học và `binh_luan_tung_hinh.md`. Những PNG trong thư mục `ket_qua/` trước đây là kết quả cũ; chúng không được mở khi demo mới.

`python3 main.py` chạy thêm khảo sát nhiễu nhưng vẫn chỉ tạo bốn figure. Chọn riêng một phương pháp bằng `--algorithm binary`, `--algorithm histogram` hoặc `--algorithm statistical` vẫn tạo bốn figure. Dùng `--no-show` khi chỉ muốn lưu hình.

Bình luận từng hình gồm vị trí biên chuẩn/dự đoán, độ lệch ms, số biên ghép/thừa/thiếu, nhận xét lỗi và nguyên nhân khả dĩ từ STE. “Biên ghép” không đồng nghĩa biên chính xác: MAE/RMSE biểu thị sai lệch thực tế, không áp dụng dung sai 200 ms. Quy tắc 200 ms chỉ loại Silence ảo. F0mean trong LAB là thống kê tham chiếu, không phải đường F0 chuẩn theo thời gian.
