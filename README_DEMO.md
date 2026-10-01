# Demo bốn figure

Mỗi thành viên chạy hoặc bấm Run tại `main.py` một lần, rồi chọn thuật toán phụ trách:

```bash
python3 main.py --no-noise
```

Chương trình hỏi `1` (Binary Search), `2` (Histogram), hoặc `3` (Statistical Gaussian). Chỉ thuật toán đã chọn được huấn luyện và chạy trên đủ bốn WAV test. Có đúng bốn cửa sổ, mỗi cửa sổ ứng với một WAV và chứa kết quả của riêng thành viên đó, cùng waveform, STE/ngưỡng/biên, logSTE/logMA và F0.

Có thể chọn ngay bằng dòng lệnh, tránh nhập menu khi trình bày:

```bash
python3 main.py --algorithm binary --no-noise
python3 main.py --algorithm histogram --no-noise
python3 main.py --algorithm statistical --no-noise
```

Mỗi lệnh là một lần demo riêng của một thành viên. Kết quả lưu lần lượt trong `ket_qua/demo/binary/`, `ket_qua/demo/histogram/`, `ket_qua/demo/statistical/`. Mỗi thư mục có bốn PNG, CSV, mô hình riêng và `binh_luan_tung_hinh.md`; kết quả không ghi đè lên nhau. Chương trình tự đặt cửa sổ ở bốn góc trên backend Qt hoặc Tk.

`python3 main.py` chạy thêm khảo sát nhiễu cho thuật toán đã chọn nhưng vẫn chỉ tạo bốn figure. Dùng `--no-show` khi chỉ muốn lưu hình. Khi nhóm cần so sánh chung, chạy rõ `--algorithm all`; đây không phải chế độ mặc định khi Run.

Binary Search và Gaussian gom STE có nhãn của bốn WAV training để học ngưỡng chung riêng cho từng phương pháp. STE được chuẩn hóa riêng trong từng WAV. Histogram học cấu hình trên training, rồi tính ngưỡng adaptive từ mỗi WAV test. Không dùng LAB test để học lại ngưỡng. Đây cũng là cách phân biệt ba phương pháp trong ảnh yêu cầu đã cung cấp.

Histogram xét cả đỉnh bin 0, gom plateau thành một đỉnh và giới hạn đỉnh nền trong vùng chứa 20% giá trị năng lượng thấp nhất. Đỉnh cao phải đủ xa đỉnh nền và có valley đủ sâu. Khoảng cách tối thiểu và độ sâu valley được chọn bằng kiểm chứng chéo training cùng số bin, mức trơn và trọng số. Các quy tắc này dựa trên giả định nền có năng lượng thấp; không đảm bảo hai đỉnh là hai lớp thuần nhất khi nhiễu/Speech chồng lấn.

Bình luận từng hình gồm vị trí biên chuẩn/dự đoán, độ lệch ms, số biên ghép/thừa/thiếu, nhận xét lỗi và nguyên nhân khả dĩ từ STE. “Biên ghép” không đồng nghĩa biên chính xác: MAE/RMSE biểu thị sai lệch thực tế, không áp dụng dung sai 200 ms. Quy tắc 200 ms chỉ loại Silence ảo. F0mean trong LAB là thống kê tham chiếu, không phải đường F0 chuẩn theo thời gian.
