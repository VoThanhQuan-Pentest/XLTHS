# Demo bốn figure

> Yêu cầu nộp mới dùng notebook đã chạy sẵn. Xem `NOTEBOOK_NHOM03.md` và thư mục `03-Phân đoạn tín hiệu thành tiếng nói và khoảng lặng/`. Các điểm chạy .py dưới đây phục vụ phát triển/đối chiếu, không phải bộ mã nguồn nộp cho giảng viên. PDF slide chung sẽ bổ sung sau.

## Phân khung cố định

Cả ba thuật toán luôn dùng khung danh định **25 ms**, bước dịch **10 ms**, trong training, Cross Validation và test. Cấu hình nằm duy nhất trong `speech_silence/config.py`. Binary/Gaussian chỉ kiểm chứng chéo để báo cáo; Histogram chỉ tối ưu tham số riêng, không thử lại khung 20/25/30 ms. Mô hình lưu từ cấu hình khung khác phải được huấn luyện lại trước khi dự đoán.

Quy đổi bằng `round` như trước: 400 mẫu ở 16 kHz, 1102 mẫu ở 44,1 kHz. Bước dịch tương ứng 160/441 mẫu. Khung 44,1 kHz có độ dài thực khoảng 24,989 ms do không thể dùng nửa mẫu; cả ba thuật toán sử dụng cùng quy tắc này.

## Thư mục riêng cho từng thành viên

| Thành viên | Thư mục | File bấm Run | Mã thuật toán |
|---|---|---|---|
| Binary Search | TT1_BinarySearch | TT1_BinarySearch/main.py | TT1_BinarySearch/algorithm.py |
| Histogram | TT2_Histogram | TT2_Histogram/main.py | TT2_Histogram/algorithm.py |
| Statistical Gaussian | TT3_Statistics | TT3_Statistics/main.py | TT3_Statistics/algorithm.py |

Mỗi file main.py chạy thẳng một thuật toán, không có menu và không cần --algorithm. Kết quả lưu trong thư mục ket_qua của chính thành viên: bốn hình, tham số, CSV và bình luận riêng. Mặc định bỏ khảo sát nhiễu để demo nhanh, bật lại bằng --noise.

Dữ liệu WAV/LAB và các hàm tiện ích trong speech_silence dùng chung ở gốc dự án. Mã tính ngưỡng thực tế đã được chuyển vào algorithm.py của từng thành viên; speech_silence/algorithms.py chỉ xuất lại tên hàm để chương trình nhóm và kiểm thử cũ tiếp tục hoạt động. Cần giữ cấu trúc đầy đủ của dự án khi chạy trên máy khác.

## Điểm chạy chung của nhóm

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

Các đầu ra trực tiếp tại `ket_qua/` và `ket_qua/demo/` (không nằm trong thư mục tên thuật toán) là lịch sử trước khi cố định khung. Dùng kết quả hiện hành trong ba thư mục thành viên hoặc `ket_qua/demo/{binary,histogram,statistical,all}/`.
