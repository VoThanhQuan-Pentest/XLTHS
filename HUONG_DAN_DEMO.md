# Kịch bản trình bày và demo

## 1. Trình bày mã nguồn

Mở các tệp theo thứ tự sau để người chấm thấy rõ luồng dữ liệu và việc tách training/test:

1. `main.py`: điểm chạy chính thức; mặc định chạy cả ba thuật toán trên toàn bộ tập kiểm thử.
2. `speech_silence/data.py`: tự tìm các cặp WAV/LAB; gộp `v`, `uv` thành Speech và giữ `sil` là Silence.
3. `speech_silence/features.py`: chia khung, tính STE/MA, logSTE/logMA, normalized STE và F0 bằng tự tương quan.
4. `speech_silence/algorithms.py`: ba cách tìm ngưỡng nằm trong ba hàm riêng: Binary Search, Histogram và Gaussian.
5. `speech_silence/pipeline.py`: chọn tham số bằng training, khóa tham số, dự đoán test, vẽ hình và xuất báo cáo.
6. `speech_silence/evaluation.py`: LAB test chỉ xuất hiện ở bước đánh giá; MAE/RMSE không dùng dung sai 200 ms.

Điểm cần nói rõ: điều kiện 200 ms chỉ biến các khoảng Silence dự đoán ngắn hơn 200 ms thành Speech. Nó không phải dung sai khi ghép biên.

## 2. Demo chương trình

Chạy tại thư mục dự án:

```bash
python3 main.py --no-noise
```

Lệnh này huấn luyện và xử lý đủ bốn file `phone_F2`, `phone_M2`, `studio_F2`, `studio_M2` trong một lần chạy. Dùng `python3 main.py` khi muốn chạy thêm khảo sát nhiễu.

Sau khi chương trình kết thúc, mở theo thứ tự:

1. `ket_qua/phan_bo_huan_luyen.png`: hai phân bố normalized STE và ngưỡng thống kê.
2. Bốn hình `*_so_sanh.png`: so sánh nhanh ba thuật toán trên từng tín hiệu.
3. Các hình `*_binary.png`, `*_histogram.png`, `*_statistical.png`: waveform, STE, logSTE/logMA, F0, biên dự đoán xanh và biên chuẩn đỏ.
4. `ket_qua/binh_luan_tung_hinh.md`: vị trí và nguyên nhân sai cụ thể cho từng hình.
5. `ket_qua/ghi_chu_slide.md`: bảng số liệu tổng hợp và kết quả khảo sát nhiễu.

## 3. Nội dung nói khi chỉ vào hình

- Đường xanh trùng hoặc gần đường đỏ: thuật toán xác định đúng biên; đọc độ lệch cụ thể trong phần bình luận.
- Đường xanh xuất hiện thêm trong vùng Speech: STE đã xuống dưới ngưỡng ít nhất 200 ms, tạo Silence giả.
- Đường xanh xuất hiện thêm trong vùng Silence: năng lượng nhiễu nền vượt ngưỡng, tạo Speech giả.
- Đường F0 chỉ tồn tại ở khung hữu thanh. Khoảng trống F0 thuộc silence hoặc âm vô thanh; đỉnh F0 nhọn có thể do chọn nhầm họa âm.
- Histogram dùng ngưỡng adaptive riêng cho từng WAV test. Training chỉ chọn số bin, độ làm trơn, trọng số và ngưỡng dự phòng.

## 4. Kết luận thực nghiệm ngắn

- Gaussian tốt nhất trên tập test hiện tại: MAE gộp 12,5 ms, RMSE 16,6 ms, không có biên thừa/thiếu.
- Binary Search đứng thứ hai: MAE 20,0 ms, có một biên thừa trên `phone_F2` do nhiễu cuối bản ghi.
- Histogram có MAE 50,0 ms và bốn biên thừa trên `phone_F2`; ngưỡng adaptive cao làm các vùng tiếng nói năng lượng thấp bị chia nhỏ.
- Khi tăng nhiễu trắng, Binary/Gaussian dùng ngưỡng cố định suy giảm mạnh ở 10 dB; Histogram adaptive ổn định hơn nhưng kém chính xác trên dữ liệu sạch hiện tại.
