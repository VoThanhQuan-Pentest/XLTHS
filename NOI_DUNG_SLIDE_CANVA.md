# Nội dung slide và lời trình bày

Kịch bản dưới đây dành cho khoảng 7 phút trình bày và 1 phút demo. Không đưa công thức hoặc phần lý thuyết lên slide. Mỗi slide chỉ giữ một ý chính và một hình lớn.

## Quy cách thiết kế trên Canva

- Tỷ lệ 16:9, nền trắng hoặc xám rất nhạt.
- Dùng một font hỗ trợ tiếng Việt như Be Vietnam Pro, Inter hoặc Arial.
- Tiêu đề 30–34 pt, nội dung 20–24 pt, chú thích hình tối thiểu 17 pt.
- Giữ đúng quy ước trong kết quả: xanh dương là biên dự đoán, đỏ nét đứt là biên chuẩn, cam là F0.
- Không dùng ảnh minh họa trang trí. Sơ đồ khối và kết quả thực nghiệm là phần hình ảnh chính.
- Không chép lời nói dài lên slide. Phần “Nói” bên dưới dùng làm ghi chú người thuyết trình.

## Slide 1 — Phân đoạn Speech/Silence bằng ba phương pháp

**Trên slide**

- Phân đoạn tín hiệu thu âm thành Speech và Silence
- Binary Search, Histogram, Statistical Gaussian
- Họ tên, lớp, môn học

**Bố cục**

Tiêu đề lớn ở nửa trái. Nửa phải dùng một đoạn waveform mờ và hai đường biên xanh/đỏ làm điểm nhấn.

**Nói, khoảng 15 giây**

“Bài làm của em phân đoạn tín hiệu thu âm thành tiếng nói và khoảng lặng bằng ba phương pháp độc lập. Em tập trung trình bày quy trình xử lý, cách tìm ngưỡng và kết quả thực nghiệm trên toàn bộ bốn file kiểm thử.”

## Slide 2 — Quy trình huấn luyện và kiểm thử

**Trên slide**

```text
4 WAV training + LAB
        ↓
STE chuẩn hóa theo khung
        ↓
Tìm tham số hoặc ngưỡng
        ↓
Khóa tham số
        ↓
4 WAV test → dự đoán
        ↓
LAB test → chỉ đánh giá
```

Góc dưới ghi: khung 30 ms, bước dịch 10 ms, Silence tối thiểu 200 ms.

**Bố cục**

Sơ đồ khối ngang hoặc dọc chiếm gần toàn slide. Dùng màu khác nhau cho training và test. LAB test chỉ nối vào khối “Đánh giá”, không nối vào “Dự đoán”.

**Nói, khoảng 35 giây**

“Bốn file training cùng LAB được dùng để chia khung thành hai nhóm Speech và Silence, sau đó tìm tham số. Khi chuyển sang test, các tham số được khóa. Hàm dự đoán chỉ nhận WAV và mô hình đã học. LAB test chỉ dùng sau dự đoán để vẽ biên chuẩn và tính sai số. Điều này tránh dùng ground truth của test để chỉnh thuật toán.”

## Slide 3 — Phương pháp Binary Search

**Trên slide**

```text
STE training + LAB
        ↓
Hai nhóm Speech / Silence
        ↓
Chọn khoảng ngưỡng chồng lấn
        ↓
Thử ngưỡng giữa
        ↓
Cân bằng phần nhầm lẫn hai lớp
        ↓
Ngưỡng chung T = 0.00156
```

**Hình nên dùng**

Cắt phần histogram hai lớp từ `ket_qua/phan_bo_huan_luyen.png`, đặt cạnh sơ đồ.

**Nói, khoảng 35 giây**

“Binary Search dùng nhãn training để tạo hai nhóm STE. Thuật toán thử ngưỡng giữa miền đang xét, đo phần Silence nằm trên ngưỡng và phần Speech nằm dưới ngưỡng, rồi thu hẹp một nửa khoảng tìm kiếm. Ngưỡng cuối cùng là 0.00156 và được dùng chung cho mọi file test.”

## Slide 4 — Phương pháp Histogram

**Trên slide**

```text
Normalized STE của WAV cần xử lý
        ↓
Histogram và làm trơn
        ↓
Tìm hai đỉnh chính
        ↓
Ngưỡng có trọng số giữa hai đỉnh
        ↓
Phân loại từng khung
```

Dòng nhấn mạnh: “Ngưỡng adaptive, được tính riêng cho từng WAV test.”

**Nói, khoảng 35 giây**

“Histogram khác hai phương pháp còn lại ở chỗ ngưỡng chính được tính lại trên từng WAV. Training chỉ chọn số bin, mức làm trơn, trọng số và ngưỡng dự phòng. Cách này thích nghi tốt hơn khi mức năng lượng thay đổi, nhưng có thể đặt ngưỡng quá cao nếu phân bố không tách thành hai đỉnh rõ.”

## Slide 5 — Phương pháp Statistical Gaussian

**Trên slide**

- `meanSil = 0.000412`, `stdSil = 0.000920`
- `meanSp = 0.209630`, `stdSp = 0.240703`
- Ngưỡng chung `T = 0.00358`

```text
STE training + LAB
        ↓
Ước lượng hai phân bố
        ↓
Chọn ngưỡng có sai số kỳ vọng nhỏ nhất
        ↓
Khóa ngưỡng và áp dụng cho test
```

**Hình nên dùng**

`ket_qua/phan_bo_huan_luyen.png` đặt lớn ở nửa phải.

**Nói, khoảng 40 giây**

“Phương pháp thống kê cũng dùng nhãn training, nhưng tóm tắt hai nhóm bằng mean và standard deviation. Từ hai phân bố này, chương trình chọn một ngưỡng chung có sai số phân loại kỳ vọng nhỏ nhất. Trên dữ liệu hiện tại, ngưỡng là 0.00358.”

## Slide 6 — Kết quả `phone_F2`

**Hình chính**

`ket_qua/phone_F2_so_sanh.png`

**Trên slide**

- Gaussian: hai biên trùng chuẩn, MAE 0 ms.
- Binary: biên kết thúc muộn 80 ms, thêm Speech giả tại 4.76 s.
- Histogram: MAE 55 ms, có bốn biên thừa trong vùng Speech.
- F0 trung vị 142.9 Hz, gần F0mean LAB 145 Hz.

**Nói, khoảng 40 giây**

“Đây là trường hợp khó nhất vì bản ghi phone có nhiễu nền cao hơn. Gaussian trùng cả hai biên chuẩn. Binary phát hiện một đoạn Speech giả gần cuối do nhiễu nền vượt ngưỡng. Histogram chia nhỏ vùng Speech tại khoảng 2.50 đến 2.80 giây và 3.44 đến 3.64 giây vì STE xuống dưới ngưỡng adaptive đủ lâu.”

## Slide 7 — Kết quả `phone_M2`

**Hình chính**

`ket_qua/phone_M2_so_sanh.png`

**Trên slide**

- Binary: MAE 10 ms.
- Histogram: MAE 15 ms.
- Gaussian: MAE 15 ms.
- Không thuật toán nào tạo biên thừa hoặc bỏ sót biên.
- F0 trung vị 135.0 Hz, F0mean LAB 129 Hz.

**Nói, khoảng 30 giây**

“Cả ba phương pháp làm tốt trên phone_M2. Hai đường biên xanh nằm rất gần đường đỏ và không có đoạn giả. Sai số chỉ từ 10 đến 15 ms, tương đương khoảng một đến hai bước dịch khung.”

## Slide 8 — Kết quả `studio_F2`

**Hình chính**

`ket_qua/studio_F2_so_sanh.png`

**Trên slide**

- Binary: MAE 20 ms.
- Gaussian: MAE 25 ms.
- Histogram: MAE 35 ms.
- Không có biên thừa hoặc thiếu.
- F0 trung vị 185.3 Hz, F0mean LAB 200 Hz.

**Nói, khoảng 30 giây**

“Với studio_F2, mức nhiễu nền thấp và cả ba phương pháp đều xác định đúng một vùng Speech. Binary có sai số thấp nhất là 20 ms. Histogram kết thúc Speech sớm 50 ms nên MAE cao hơn.”

## Slide 9 — Kết quả `studio_M2`

**Hình chính**

`ket_qua/studio_M2_so_sanh.png`

**Trên slide**

- Binary: MAE 5 ms.
- Gaussian: MAE 10 ms.
- Histogram: MAE 95 ms.
- Histogram kết thúc Speech tại 1.77 s, sớm 160 ms so với chuẩn 1.93 s.
- F0 trung vị 139.1 Hz, F0mean LAB 155 Hz.

**Nói, khoảng 35 giây**

“Binary và Gaussian bám rất sát biên chuẩn. Histogram dùng ngưỡng 0.2759, cao hơn nhiều so với hai ngưỡng cố định, nên phần đuôi có năng lượng giảm dần bị cắt sớm 160 ms. Đây là sai lệch lớn nhất trong bốn file kiểm thử.”

## Slide 10 — So sánh định lượng

**Bảng trên slide**

| Phương pháp | MAE gộp | RMSE gộp | Biên đúng/thừa/thiếu |
|---|---:|---:|---:|
| Binary Search | 20.0 ms | 30.8 ms | 8 / 1 / 0 |
| Histogram | 50.0 ms | 67.5 ms | 8 / 4 / 0 |
| Statistical Gaussian | 12.5 ms | 16.6 ms | 8 / 0 / 0 |

**Bố cục**

Đặt bảng bên trái. Bên phải dùng biểu đồ cột MAE, cùng màu cho từng thuật toán trên toàn bộ deck. Tô đậm hàng Gaussian.

**Nói, khoảng 40 giây**

“Gaussian cho kết quả tốt nhất trên tập test hiện tại với MAE 12.5 ms và không có biên thừa hoặc thiếu. Binary đứng thứ hai với MAE 20 ms. Histogram có MAE 50 ms và bốn biên thừa, chủ yếu đến từ phone_F2.”

## Slide 11 — Ảnh hưởng của nhiễu

**Biểu đồ trên slide**

Vẽ line chart từ bảng lỗi phân lớp cân bằng:

| Mức nhiễu thêm | Binary | Histogram | Gaussian |
|---:|---:|---:|---:|
| 30 dB | 0.013 | 0.054 | 0.006 |
| 20 dB | 0.183 | 0.083 | 0.005 |
| 10 dB | 0.500 | 0.118 | 0.500 |
| 0 dB | 0.500 | 0.164 | 0.500 |

**Trên slide**

“Ngưỡng cố định chính xác hơn khi nhiễu thấp. Histogram adaptive suy giảm chậm hơn khi nhiễu tăng.”

**Nói, khoảng 45 giây**

“Ở 30 và 20 dB, Gaussian vẫn có lỗi thấp nhất. Khi nhiễu tăng đến 10 dB, hai phương pháp dùng ngưỡng cố định gần như phân loại toàn bộ tín hiệu về một lớp nên lỗi đạt 0.5. Histogram tự tính lại ngưỡng theo từng WAV nên suy giảm chậm hơn, dù kết quả trên tín hiệu gốc chưa tốt bằng Gaussian.”

## Slide 12 — Kết luận và demo

**Trên slide**

- Gaussian tốt nhất trên tập kiểm thử hiện tại.
- Binary ổn định và dễ giải thích.
- Histogram thích nghi với mức năng lượng nhưng nhạy với hình dạng histogram.

Lệnh demo đặt lớn ở cuối slide:

```bash
python3 main.py --no-noise
```

**Nói, khoảng 20 giây trước khi demo**

“Kết quả tốt nhất thuộc về Gaussian, nhưng khảo sát nhiễu cho thấy ngưỡng adaptive có ưu điểm riêng. Sau đây em chạy chương trình một lần. Chương trình tự duyệt đủ bốn file test, in chỉ số của ba thuật toán và tạo toàn bộ hình mà em vừa trình bày.”

## Phần demo trực tiếp, khoảng 1 phút

1. Chạy `python3 main.py --no-noise`.
2. Chỉ vào console để xác nhận đủ bốn tên file test và ba phương pháp.
3. Mở `ket_qua/phone_F2_statistical.png` để chỉ bốn panel: waveform, STE, logSTE/logMA, F0.
4. Mở `ket_qua/phone_F2_histogram.png` để chỉ các biên thừa và giải thích nguyên nhân.
5. Không mở mã nguồn dài trong lúc demo. Nếu giảng viên hỏi, mở đúng hàm tương ứng theo thứ tự trong `HUONG_DAN_DEMO.md`.

# Prompt dùng cho Canva Pro

Sao chép toàn bộ prompt dưới đây vào Canva. Sau khi Canva tạo deck, thay các placeholder bằng hình PNG thật trong thư mục `ket_qua/`.

```text
Hãy tạo một bài thuyết trình học thuật bằng tiếng Việt, tỷ lệ 16:9, gồm đúng 12 slide về đề tài “Phân đoạn tín hiệu thành Speech và Silence bằng ba phương pháp”. Người nghe là giảng viên môn Xử lý tín hiệu số. Thời lượng trình bày khoảng 7 phút và 1 phút demo.

Mục tiêu thiết kế:
- Tập trung vào sơ đồ khối, các bước thuật toán, đồ thị thực nghiệm, số liệu và bình luận.
- Không trình bày lý thuyết nền, định nghĩa dài hoặc công thức toán.
- Phong cách sạch, kỹ thuật và dễ đọc khi chiếu trong lớp.
- Nền trắng hoặc xám rất nhạt, tiêu đề xanh navy, điểm nhấn xanh teal và cam.
- Dùng font Be Vietnam Pro hoặc Inter.
- Giữ quy ước màu: biên dự đoán xanh dương, biên chuẩn đỏ nét đứt, F0 màu cam.
- Mỗi slide có một ý chính, ít chữ, không dùng ảnh trang trí hoặc icon không cần thiết.
- Các sơ đồ khối phải là đối tượng editable. Dùng đường nối thẳng, tránh đường chéo.
- Tạo placeholder ảnh lớn và ghi đúng tên file để tôi thay bằng hình thực nghiệm thật.

Slide 1: Tiêu đề “Phân đoạn Speech/Silence bằng ba phương pháp”. Phụ đề “Binary Search, Histogram, Statistical Gaussian”. Chừa chỗ cho họ tên, lớp và môn học.

Slide 2: Tiêu đề “Quy trình huấn luyện và kiểm thử”. Vẽ sơ đồ: 4 WAV training + LAB, STE chuẩn hóa theo khung, tìm tham số/ngưỡng, khóa tham số, 4 WAV test, dự đoán, LAB test chỉ dùng để đánh giá. Ghi nhỏ: khung 30 ms, bước dịch 10 ms, Silence tối thiểu 200 ms. Thể hiện rõ LAB test không đi vào khối dự đoán.

Slide 3: Tiêu đề “Phương pháp Binary Search”. Sơ đồ: STE training + LAB, hai nhóm Speech/Silence, miền chồng lấn, thử ngưỡng giữa, cân bằng phần nhầm lẫn, ngưỡng chung T = 0.00156. Thêm placeholder `ket_qua/phan_bo_huan_luyen.png`.

Slide 4: Tiêu đề “Phương pháp Histogram”. Sơ đồ: normalized STE của WAV, histogram và làm trơn, tìm hai đỉnh, ngưỡng có trọng số, phân loại khung. Nhấn mạnh “Ngưỡng adaptive, tính riêng cho từng WAV test”. Ghi nhỏ: training chọn số bin, mức làm trơn, trọng số và fallback.

Slide 5: Tiêu đề “Phương pháp Statistical Gaussian”. Hiển thị meanSil = 0.000412, stdSil = 0.000920, meanSp = 0.209630, stdSp = 0.240703, T = 0.00358. Vẽ sơ đồ training STE + LAB, ước lượng hai phân bố, chọn ngưỡng có sai số kỳ vọng nhỏ nhất, khóa ngưỡng. Thêm placeholder `ket_qua/phan_bo_huan_luyen.png`.

Slide 6: Tiêu đề “Kết quả phone_F2”. Placeholder lớn `ket_qua/phone_F2_so_sanh.png`. Bình luận ngắn: Gaussian MAE 0 ms; Binary kết thúc muộn 80 ms và thêm Speech giả tại 4.76 s; Histogram MAE 55 ms và có bốn biên thừa; F0 trung vị 142.9 Hz, F0mean LAB 145 Hz.

Slide 7: Tiêu đề “Kết quả phone_M2”. Placeholder lớn `ket_qua/phone_M2_so_sanh.png`. Bình luận: Binary MAE 10 ms; Histogram và Gaussian MAE 15 ms; không có biên thừa hoặc thiếu; F0 trung vị 135 Hz, F0mean LAB 129 Hz.

Slide 8: Tiêu đề “Kết quả studio_F2”. Placeholder lớn `ket_qua/studio_F2_so_sanh.png`. Bình luận: Binary MAE 20 ms; Gaussian 25 ms; Histogram 35 ms; không có biên thừa hoặc thiếu; F0 trung vị 185.3 Hz, F0mean LAB 200 Hz.

Slide 9: Tiêu đề “Kết quả studio_M2”. Placeholder lớn `ket_qua/studio_M2_so_sanh.png`. Bình luận: Binary MAE 5 ms; Gaussian 10 ms; Histogram 95 ms; Histogram kết thúc Speech tại 1.77 s, sớm 160 ms so với chuẩn 1.93 s; F0 trung vị 139.1 Hz, F0mean LAB 155 Hz.

Slide 10: Tiêu đề “So sánh định lượng”. Tạo bảng và biểu đồ cột MAE. Binary Search: MAE 20.0 ms, RMSE 30.8 ms, biên đúng/thừa/thiếu 8/1/0. Histogram: 50.0 ms, 67.5 ms, 8/4/0. Statistical Gaussian: 12.5 ms, 16.6 ms, 8/0/0. Tô đậm Gaussian là kết quả tốt nhất trên tập test hiện tại.

Slide 11: Tiêu đề “Ảnh hưởng của nhiễu”. Tạo line chart editable với trục ngang lần lượt 30, 20, 10, 0 dB. Binary: 0.013, 0.183, 0.500, 0.500. Histogram: 0.054, 0.083, 0.118, 0.164. Gaussian: 0.006, 0.005, 0.500, 0.500. Trục dọc là lỗi phân lớp cân bằng. Kết luận ngắn: ngưỡng cố định chính xác hơn khi nhiễu thấp; Histogram adaptive suy giảm chậm hơn khi nhiễu tăng.

Slide 12: Tiêu đề “Kết luận và demo”. Ba kết luận ngắn: Gaussian tốt nhất trên tập test; Binary ổn định và dễ giải thích; Histogram thích nghi mức năng lượng nhưng nhạy với hình dạng histogram. Hiển thị lớn lệnh `python3 main.py --no-noise` và dòng “Một lần chạy xử lý đủ 4 WAV test × 3 thuật toán”.

Không thêm slide tài liệu tham khảo, agenda, cảm ơn hoặc lý thuyết. Không tự tạo số liệu khác. Giữ tất cả bảng, biểu đồ và sơ đồ có thể chỉnh sửa trong Canva.
```

## Cách so sánh bản Canva với cấu trúc đề xuất

Sau khi Canva tạo xong, kiểm tra bốn điểm:

1. Canva có giữ đủ bốn slide kết quả cho bốn WAV hay đã gộp khiến hình quá nhỏ.
2. Canva có đặt LAB test chỉ ở bước đánh giá hay nối nhầm vào dự đoán.
3. Canva có giữ đúng màu biên xanh/đỏ và không đổi màu các figure.
4. Canva có tự thêm lý thuyết, công thức, agenda hoặc slide cảm ơn hay không. Xóa các phần này để dành thời gian cho kết quả và demo.
