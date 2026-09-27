# Phân đoạn tín hiệu thành tiếng nói và khoảng lặng

Chương trình cài đặt ba cách tìm ngưỡng riêng biệt: tìm kiếm nhị phân từ dữ liệu huấn luyện có nhãn, histogram từ đặc trưng của WAV đầu vào, và mô hình thống kê Gaussian từ STE chuẩn hóa của hai lớp. Cả ba dùng chung bước trích đặc trưng và loại khoảng lặng ngắn hơn 200 ms.

## Chạy

```bash
python3 -m pip install -r requirements.txt
python3 run_all.py
```

Lệnh duy nhất xử lý tự động tất cả WAV kiểm thử. Kết quả được lưu trong `ket_qua/`: tham số huấn luyện, CSV đánh giá/biên dự đoán/khảo sát nhiễu, 12 hình từng thuật toán, 4 hình so sánh, hình phân bố huấn luyện và ghi chú ngắn để làm slide. Có thể dùng `--no-noise` để bỏ thí nghiệm thêm nhiễu; `--root` và `--output` để đổi thư mục đầu vào/đầu ra.

Để demo riêng từng thuật toán, chạy `python3 demo_binary.py`, `python3 demo_histogram.py` hoặc `python3 demo_statistical.py`. Mỗi script xử lý cả 4 WAV kiểm thử trong một lần chạy và lưu kết quả trong thư mục riêng. Nếu đã chạy `run_all.py`, chúng sử dụng cùng tham số huấn luyện đã lưu.

## Quy ước đánh giá

`v` và `uv` đều là Speech, `sil` là Silence. Hai dòng F0 trong LAB không tham gia phân đoạn. Phần đuôi WAV nằm ngoài LAB không được dùng để chấm điểm. Biên chuẩn là chuyển tiếp Speech/Silence; không tính chuyển tiếp `v`/`uv`. Biên dự đoán được vẽ **xanh dương**, biên chuẩn **đỏ**. MAE và RMSE tính bằng ms trên các biên ghép một-một đúng hướng trong phạm vi 200 ms; số biên thiếu/thừa được báo riêng. Nếu không có biên ghép, MAE/RMSE không xác định.

Tham số được chọn bằng kiểm chứng chéo trên bốn bản ghi huấn luyện. Nhãn kiểm thử không đi vào hàm dự đoán. Histogram chọn ngưỡng theo hai đỉnh của STE chuẩn hóa, dùng ngưỡng dự phòng học trên huấn luyện khi histogram một đỉnh. Đây là biến thể một đặc trưng của cách histogram; tài liệu tham khảo của Giannakopoulos còn sử dụng spectral centroid. SNR nền trong báo cáo là ước lượng từ vùng Silence được gán nhãn, không phải SNR đo từ tín hiệu sạch. Thí nghiệm cộng nhiễu dùng tỷ số công suất toàn bản ghi/nhiễu đặt trước.

## Kiểm tra

```bash
python3 -m pytest -q
```

Các bản ghi hiện có chỉ chứa một đoạn Speech sau khi gộp `v`/`uv`; kiểm thử tự tạo kiểm tra thêm trường hợp nhiều đoạn và khoảng lặng nội bộ.
