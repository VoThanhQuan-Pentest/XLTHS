# Kết quả sau khi cố định phân khung 25 ms / 10 ms

## Cấu hình và quy trình

Tất cả thuật toán luôn dùng khung danh định 25 ms, bước dịch 10 ms. Cấu hình duy nhất nằm trong `speech_silence/config.py`. Tại 16 kHz, mỗi khung có 400 mẫu; tại 44,1 kHz có 1102 mẫu theo `round`, tương đương khoảng 24,989 ms. Bước dịch lần lượt là 160 và 441 mẫu.

Cross Validation không chọn độ dài khung. Binary/Gaussian chỉ đánh giá kiểm chứng ở 25/10 ms; Histogram tối ưu số bin, độ trơn, trọng số, khoảng cách đỉnh và độ sâu valley trên training. Mô hình chứa khung/bước dịch khác bị từ chối trước khi dự đoán.

Tham số được học lại trên bốn WAV training, khóa trước khi đánh giá bốn WAV test. LAB test không tham gia chọn tham số. Quy tắc Silence dưới 200 ms và cách ghép biên không đổi.

## Tham số mới

| Thuật toán | Tham số học từ training |
|---|---|
| Binary Search | Ngưỡng chung 0,001301266565 |
| Gaussian | Ngưỡng chung 0,002868194105 |
| Histogram | 128 bin, độ trơn 1, trọng số 10, khoảng cách tối thiểu 12 bin, valley sâu tối thiểu 0,2; fallback 0,020951704545 |

Gaussian: meanSil = 0,000384032520; stdSil = 0,000707281144; meanSp = 0,202648898168; stdSp = 0,235626132774. Cả hai thuật toán có nhãn dùng 501 khung Silence và 794 khung Speech.

Histogram tiếp tục tính ngưỡng riêng từ từng WAV: phone_F2 = 0,014559659091; phone_M2 = 0,022372159091; studio_F2 = 0,037286931818; studio_M2 = 0,029474431818. Không dùng LAB test để tính các ngưỡng này.

## Kết quả trên đủ bốn WAV test

| WAV | Binary MAE | Histogram MAE | Gaussian MAE |
|---|---:|---:|---:|
| phone_F2 | 50 ms | 35 ms | 20 ms |
| phone_M2 | 10 ms | 10 ms | 10 ms |
| studio_F2 | 15 ms | 35 ms | 15 ms |
| studio_M2 | 5 ms | 30 ms | 10 ms |
| Gộp biên | 20,00 ms | 27,50 ms | 13,75 ms |

| Thuật toán | RMSE gộp | Biên ghép/thừa/thiếu |
|---|---:|---|
| Binary Search | 33,54 ms | 8 / 3 / 0 |
| Histogram | 32,79 ms | 8 / 2 / 0 |
| Gaussian | 15,41 ms | 8 / 0 / 0 |

Các biên thừa hiện ở phone_F2. “Biên ghép” là cặp dùng để tính sai lệch, không đồng nghĩa biên đúng tuyệt đối. MAE/RMSE chỉ dùng các cặp ghép; phải đọc kèm biên thừa/thiếu.

## So với cấu hình trước thay đổi

| Thuật toán | Frame cũ | MAE cũ → mới | RMSE cũ → mới | Biên thừa cũ → mới |
|---|---|---|---|---|
| Binary Search | 30 ms | 20,0 → 20,0 ms | 30,8 → 33,5 ms | 1 → 3 |
| Histogram | 20 ms | 22,5 → 27,5 ms | 25,5 → 32,8 ms | 2 → 2 |
| Gaussian | 30 ms | 12,5 → 13,75 ms | 16,6 → 15,4 ms | 0 → 0 |

Mục tiêu của thay đổi là cùng điều kiện phân khung cho ba phương pháp. Không khẳng định mọi chỉ số đều cải thiện. Các giá trị cũ thuộc phiên bản trước khi cố định frame, được giữ làm lịch sử.

## Khảo sát nhiễu

Lỗi phân lớp cân bằng trung bình trên bốn WAV và ba seed. Q là tỷ số công suất toàn WAV/nhiễu thêm vào, không phải SNR đo với tiếng nói sạch.

| Q | Binary | Histogram | Gaussian |
|---|---:|---:|---:|
| 30 dB | 0,028 | 0,023 | 0,005 |
| 20 dB | 0,292 | 0,023 | 0,006 |
| 10 dB | 0,500 | 0,023 | 0,500 |
| 0 dB | 0,500 | 0,064 | 0,500 |

## Vị trí kết quả

Ba thư mục thành viên có kết quả hiện hành trong `ket_qua/` của riêng mình. Điểm chạy chung xuất vào `ket_qua/demo/{binary,histogram,statistical,all}/`. Các JSON/PNG/CSV đặt trực tiếp tại `ket_qua/` và `ket_qua/demo/` là lịch sử; xem `README_LICH_SU.md` trong đó.

Mỗi chế độ riêng vẫn tạo bốn figure cho bốn WAV test, có đặc trưng, F0 và biên xanh/đỏ. Mỗi thư mục có file `binh_luan_tung_hinh.md` với vị trí sai và nguyên nhân khả dĩ.
