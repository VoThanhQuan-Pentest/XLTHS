# Phân đoạn tín hiệu thành tiếng nói và khoảng lặng

Chương trình cài đặt ba cách tìm ngưỡng riêng biệt: tìm kiếm nhị phân từ dữ liệu huấn luyện có nhãn, histogram từ đặc trưng của WAV đầu vào, và mô hình thống kê Gaussian từ STE chuẩn hóa của hai lớp. Cả ba dùng chung bước trích đặc trưng và loại khoảng lặng ngắn hơn 200 ms.

Kịch bản mở mã nguồn, chạy chương trình và trình bày từng hình nằm trong [`HUONG_DAN_DEMO.md`](HUONG_DAN_DEMO.md).

## Chạy

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Đây là entry point chính thức để demo. Một lần chạy sẽ tự động xử lý đúng 4 WAV trong `TinHieuKiemThu`, bằng cả ba thuật toán. Kết quả được lưu trong `ket_qua/`: tham số huấn luyện, CSV đánh giá/biên dự đoán/khảo sát nhiễu, 12 hình từng thuật toán, 4 hình so sánh, hình phân bố huấn luyện, tóm tắt và bình luận cho từng hình. Mỗi hình có waveform, STE chuẩn hóa, logSTE/logMA, F0, biên dự đoán xanh và biên chuẩn đỏ.

Khi cần demo nhanh mà không chạy thí nghiệm nhiễu:

```bash
python3 main.py --no-noise
```

Có thể chọn riêng một phương pháp với `--algorithm binary`, `--algorithm histogram` hoặc `--algorithm statistical`. `run_all.py` được giữ làm tên lệnh tương thích.

Để demo riêng từng thuật toán, chạy `python3 demo_binary.py`, `python3 demo_histogram.py` hoặc `python3 demo_statistical.py`. Mỗi script xử lý cả 4 WAV kiểm thử trong một lần chạy và lưu kết quả trong thư mục riêng. Nếu đã chạy `run_all.py`, chúng sử dụng cùng tham số huấn luyện đã lưu.

## Quy ước đánh giá

`v` và `uv` đều là Speech, `sil` là Silence. Hai dòng F0mean/F0std trong LAB không tham gia quyết định Speech/Silence; đường F0 trên hình được ước lượng trực tiếp từ WAV bằng tự tương quan. Phần đuôi WAV nằm ngoài LAB không được dùng để chấm điểm. Biên chuẩn là chuyển tiếp Speech/Silence; không tính chuyển tiếp `v`/`uv`. Biên dự đoán được vẽ **xanh dương**, biên chuẩn **đỏ**. MAE và RMSE tính bằng ms trên các biên cùng loại ghép một-một theo thứ tự. Không dùng dung sai 200 ms khi tính metric; 200 ms chỉ dùng để loại khoảng lặng ảo. Số biên thiếu/thừa được báo riêng.

Tham số được chọn bằng kiểm chứng chéo trên bốn bản ghi huấn luyện. Nhãn kiểm thử không đi vào hàm dự đoán. Histogram chọn ngưỡng theo hai đỉnh của STE chuẩn hóa, dùng ngưỡng dự phòng học trên huấn luyện khi histogram một đỉnh. Đây là biến thể một đặc trưng của cách histogram; tài liệu tham khảo của Giannakopoulos còn sử dụng spectral centroid. SNR nền trong báo cáo là ước lượng từ vùng Silence được gán nhãn, không phải SNR đo từ tín hiệu sạch. Thí nghiệm cộng nhiễu dùng tỷ số công suất toàn bản ghi/nhiễu đặt trước.

## Kiểm tra

```bash
python3 -m pytest -q
```

Các bản ghi hiện có chỉ chứa một đoạn Speech sau khi gộp `v`/`uv`; kiểm thử tự tạo kiểm tra thêm trường hợp nhiều đoạn và khoảng lặng nội bộ.
