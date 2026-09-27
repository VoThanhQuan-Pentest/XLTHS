# Tóm tắt kết quả

Các số liệu sau được đo trên tập kiểm thử; tham số chỉ chọn bằng tập huấn luyện.

- **Tìm kiếm nhị phân**: MAE trung bình theo tệp 20.0 ms; MAE/RMSE gộp biên 20.0/30.8 ms; biên đúng/thừa/thiếu 8/1/0.
- **Histogram**: MAE trung bình theo tệp 50.0 ms; MAE/RMSE gộp biên 50.0/67.5 ms; biên đúng/thừa/thiếu 8/4/0.
- **Thống kê Gaussian**: MAE trung bình theo tệp 12.5 ms; MAE/RMSE gộp biên 12.5/16.6 ms; biên đúng/thừa/thiếu 8/0/0.

SNR nền là ước lượng từ vùng Silence có nhãn, không phải SNR đo với tín hiệu sạch.
Histogram có thể tự tính ngưỡng từ WAV kiểm thử; nhãn kiểm thử chỉ dùng để đánh giá.

Khi thêm nhiễu trắng, lỗi phân lớp cân bằng trung bình trên 4 tệp × 3 seed:
- Tìm kiếm nhị phân: 30 dB: 0.013; 20 dB: 0.183; 10 dB: 0.500; 0 dB: 0.500.
- Histogram: 30 dB: 0.054; 20 dB: 0.083; 10 dB: 0.118; 0 dB: 0.164.
- Thống kê Gaussian: 30 dB: 0.006; 20 dB: 0.005; 10 dB: 0.500; 0 dB: 0.500.
Mức 0 dB là tỷ số công suất toàn WAV/nhiễu thêm vào; không tương đương SNR tiếng nói sạch.
