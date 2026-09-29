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

Chạy trực tiếp tại thư mục dự án (hoặc bấm nút **Run** trên file `main.py` trong IDE):

```bash
python3 main.py --no-noise
```

**Hành vi khi chạy CT (đúng chuẩn yêu cầu đề bài):**
- Chỉ cần bấm Run chạy **đúng 1 lần duy nhất**.
- CT tự động nạp 4 file test trong `TinHieuKiemThu`, xuất kết quả trên **4 cửa sổ Figure** tương ứng.
- Chương trình **tự động sắp xếp 4 Figure vào 4 góc màn hình** (Top-Left, Top-Right, Bottom-Left, Bottom-Right) để GV quan sát cùng lúc.
- Mỗi plot con (subplot) trên từng Figure đều có **Title** và **Axis Label (xlabel, ylabel)** phân biệt rõ ràng:
  - *Plot 1*: Dạng sóng Waveform & Biên phân đoạn (Đỏ: Chuẩn, Xanh: Dự đoán).
  - *Plot 2*: STE chuẩn hóa & Đường ngưỡng nằm ngang T & Vùng tiếng nói Speech phát hiện.
  - *Plot 3*: Mức năng lượng logSTE (dB) và logMA (dB).
  - *Plot 4*: Đường tần số cơ bản F0 ước lượng và đường F0mean chuẩn LAB.
- Toàn bộ hình ảnh và số liệu đánh giá cũng được tự động lưu vào thư mục `ket_qua/`.

*(Lưu ý: Nếu muốn chạy không bật giao diện GUI để kiểm tra nhanh trong terminal, có thể thêm cờ `--no-show`: `python3 main.py --no-noise --no-show`)*

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
