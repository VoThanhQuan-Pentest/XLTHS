# Bình luận bốn figure kiểm thử

Mỗi figure ứng với một WAV và chứa toàn bộ các phương pháp đã chọn.
Biên ghép là cặp cùng hướng để đo sai lệch, không có dung sai chấp nhận 200 ms.

## phone_F2.png

Hình gồm waveform, normalized STE/ngưỡng/biên của từng phương pháp, logSTE/logMA và F0.
Đường xanh là biên dự đoán, đường đỏ nét đứt là biên chuẩn. Các chỉ số tính bằng ms.

### Thống kê Gaussian

Ngưỡng 0.003580; MAE/RMSE 0.0/0.0 ms. Biên ghép/thừa/thiếu: 2/0/0.
- Bắt đầu Speech: chuẩn 1.02 s, dự đoán 1.02 s; lệch +0 ms.
- Kết thúc Speech: chuẩn 4.04 s, dự đoán 4.04 s; lệch +0 ms.
- Sai lệch nhỏ (tối đa 30 ms). Các mức này chỉ phục vụ bình luận, không dùng làm dung sai ghép biên.

F0 ước lượng: trung vị 142.9 Hz. F0mean LAB tham chiếu: 145.0 Hz.
Khoảng trống F0 biểu thị khung không đạt điều kiện năng lượng/tương quan. Không thể khẳng định tất cả đều là vô thanh; đỉnh nhọn có thể do nhầm họa âm.

## phone_M2.png

Hình gồm waveform, normalized STE/ngưỡng/biên của từng phương pháp, logSTE/logMA và F0.
Đường xanh là biên dự đoán, đường đỏ nét đứt là biên chuẩn. Các chỉ số tính bằng ms.

### Thống kê Gaussian

Ngưỡng 0.003580; MAE/RMSE 15.0/15.8 ms. Biên ghép/thừa/thiếu: 2/0/0.
- Bắt đầu Speech: chuẩn 0.53 s, dự đoán 0.52 s; lệch -10 ms.
- Kết thúc Speech: chuẩn 2.52 s, dự đoán 2.50 s; lệch -20 ms.
- Sai lệch nhỏ (tối đa 30 ms). Các mức này chỉ phục vụ bình luận, không dùng làm dung sai ghép biên.
- Biên lệch phù hợp với năng lượng tăng/giảm quanh ngưỡng và khung chồng lấn. Đây là diễn giải từ đồ thị STE, chưa chứng minh được một nguyên nhân duy nhất.

F0 ước lượng: trung vị 135.0 Hz. F0mean LAB tham chiếu: 129.0 Hz.
Khoảng trống F0 biểu thị khung không đạt điều kiện năng lượng/tương quan. Không thể khẳng định tất cả đều là vô thanh; đỉnh nhọn có thể do nhầm họa âm.

## studio_F2.png

Hình gồm waveform, normalized STE/ngưỡng/biên của từng phương pháp, logSTE/logMA và F0.
Đường xanh là biên dự đoán, đường đỏ nét đứt là biên chuẩn. Các chỉ số tính bằng ms.

### Thống kê Gaussian

Ngưỡng 0.003580; MAE/RMSE 25.0/25.5 ms. Biên ghép/thừa/thiếu: 2/0/0.
- Bắt đầu Speech: chuẩn 0.77 s, dự đoán 0.75 s; lệch -20 ms.
- Kết thúc Speech: chuẩn 2.37 s, dự đoán 2.34 s; lệch -30 ms.
- Sai lệch nhỏ (tối đa 30 ms). Các mức này chỉ phục vụ bình luận, không dùng làm dung sai ghép biên.
- Biên lệch phù hợp với năng lượng tăng/giảm quanh ngưỡng và khung chồng lấn. Đây là diễn giải từ đồ thị STE, chưa chứng minh được một nguyên nhân duy nhất.

F0 ước lượng: trung vị 185.3 Hz. F0mean LAB tham chiếu: 200.0 Hz.
Khoảng trống F0 biểu thị khung không đạt điều kiện năng lượng/tương quan. Không thể khẳng định tất cả đều là vô thanh; đỉnh nhọn có thể do nhầm họa âm.

## studio_M2.png

Hình gồm waveform, normalized STE/ngưỡng/biên của từng phương pháp, logSTE/logMA và F0.
Đường xanh là biên dự đoán, đường đỏ nét đứt là biên chuẩn. Các chỉ số tính bằng ms.

### Thống kê Gaussian

Ngưỡng 0.003580; MAE/RMSE 10.0/14.1 ms. Biên ghép/thừa/thiếu: 2/0/0.
- Bắt đầu Speech: chuẩn 0.45 s, dự đoán 0.45 s; lệch +0 ms.
- Kết thúc Speech: chuẩn 1.93 s, dự đoán 1.91 s; lệch -20 ms.
- Sai lệch nhỏ (tối đa 30 ms). Các mức này chỉ phục vụ bình luận, không dùng làm dung sai ghép biên.
- Biên lệch phù hợp với năng lượng tăng/giảm quanh ngưỡng và khung chồng lấn. Đây là diễn giải từ đồ thị STE, chưa chứng minh được một nguyên nhân duy nhất.

F0 ước lượng: trung vị 139.1 Hz. F0mean LAB tham chiếu: 155.0 Hz.
Khoảng trống F0 biểu thị khung không đạt điều kiện năng lượng/tương quan. Không thể khẳng định tất cả đều là vô thanh; đỉnh nhọn có thể do nhầm họa âm.
