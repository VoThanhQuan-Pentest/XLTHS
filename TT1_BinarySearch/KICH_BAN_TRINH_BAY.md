# Kịch bản Binary Search — Võ Thanh Quân

Slide: `output/slides/Slide_Chung_Nhom03.pptx`, trang 1–8.

Lời nói bằng tiếng Việt, khớp nội dung slide tiếng Anh. Phần slide có 170 giây
nội dung dự kiến và 10 giây dự phòng chuyển trang. Phần demo có 60 giây.
Các con số thời lượng là mục tiêu luyện tập; cần bấm giờ khi tập nói.

## Phân bổ thời gian slide

| Trang | Nội dung | Thời gian | Mốc kết thúc |
|---|---|---:|---:|
| 1 | Chào và giới thiệu | 10 giây | 0:10 |
| 2 | Thiết lập chung | 20 giây | 0:30 |
| 3 | Quy trình Binary Search | 40 giây | 1:10 |
| 4 | Đồ thị tìm ngưỡng | 35 giây | 1:45 |
| 5 | phone_F2 | 20 giây | 2:05 |
| 6 | phone_M2 | 10 giây | 2:15 |
| 7 | studio_F2 | 15 giây | 2:30 |
| 8 | studio_M2 và tổng kết | 20 giây | 2:50 |
| — | Chuyển trang, chỉ vào đồ thị | 10 giây dự phòng | 3:00 |

## Lời nói theo từng trang

### Trang 1 — 10 giây

**Nói:**

> Em chào thầy. Nhóm 03 thực hiện phân đoạn tiếng nói và khoảng lặng.
> Em là Võ Thanh Quân, phụ trách thuật toán Binary Search.

### Trang 2 — 20 giây

**Nói:**

> Nhóm dùng bốn file huấn luyện và bốn file kiểm thử riêng.
> Khung dài 25 mili giây, dịch 10 mili giây. STE được chuẩn hóa riêng từng file.
> Sau phân loại, chương trình lấp khoảng lặng ngắn hơn 200 mili giây.
> Đường đỏ là biên chuẩn, đường xanh là biên dự đoán.
> F0 minh họa thêm ở phía dưới.

**Thao tác:** Chỉ một lần vào dòng 25/10 ms và màu biên. Dành phần giải thích
đồ thị cụ thể cho các trang TEST.

### Trang 3 — 40 giây

**Nói:**

> Quy trình gồm huấn luyện và kiểm thử.
> Ở bước huấn luyện, em tính STE, chuẩn hóa, rồi lọc median để giảm dao động.
> Nhãn LAB chia frame thành Silence và Speech; cả v và uv đều thuộc Speech.
> Em gộp đặc trưng từ bốn file TRAIN, giữ vùng năng lượng chồng lấn và tìm ngưỡng bằng chia đôi.
> TRAIN chọn median bậc 15, với ngưỡng khoảng 0,0016.
> Sang TEST, em giữ bộ tham số này, phân loại theo ngưỡng rồi xử lý khoảng lặng ngắn.
> LAB của TEST phục vụ đối chiếu kết quả sau dự đoán.

**Thao tác:** Đi theo hàng TRAIN, chỉ giá trị median/T, rồi chuyển xuống hàng TEST.
Đọc ngưỡng làm tròn 0,0016; giá trị đầy đủ đã nằm trên slide.

### Trang 4 — 35 giây

**Nói:**

> Hình này minh họa cách quyết định tăng hoặc giảm ngưỡng.
> Đường xanh dương bên trái là mức năng lượng Silence vượt ngưỡng;
> đường cam là mức thiếu hụt của Speech so với ngưỡng.
> Nếu lỗi phía Silence lớn hơn, em tăng ngưỡng. Nếu lỗi phía Speech lớn hơn, em giảm ngưỡng.
> Ngưỡng được chọn khi hai mức gần cân bằng.
> Hình bên phải ghi lại 24 lần chia đôi thực tế, cho thấy khoảng tìm kiếm thu hẹp và hội tụ.

**Thao tác:** Chỉ hai đường bên trái và đường thẳng đứng đánh dấu T;
sau đó chỉ vùng khoảng tìm kiếm thu hẹp bên phải.
Hai đường biểu diễn mức lỗi năng lượng trung bình trong vùng chồng lấn.

### Trang 5 — 20 giây

**Nói:**

> Với phone_F2, biên bắt đầu trùng chuẩn, nhưng biên kết thúc muộn 60 mili giây;
> MAE là 30 mili giây.
> Nhìn đường STE sau median, năng lượng ở cuối vẫn trên ngưỡng nên chương trình
> kéo dài vùng Speech. Đây là file có sai số lớn nhất của Binary Search.

**Thao tác:** Chỉ cặp biên đỏ/xanh phía cuối và phần median STE nằm trên T.
Đây là diễn giải từ đồ thị, không khẳng định median là nguyên nhân duy nhất.

### Trang 6 — 10 giây

**Nói:**

> Với phone_M2, cả hai biên trùng chuẩn, MAE bằng 0.
> Đây là file cho kết quả tốt nhất trong bốn file TEST.

**Thao tác:** Chỉ hai vị trí biên trùng nhau, rồi chuyển trang.

### Trang 7 — 15 giây

**Nói:**

> Với studio_F2, hai biên đều sớm 10 mili giây; MAE là 10 mili giây.
> Đường năng lượng vượt và giảm dưới ngưỡng trước các mốc LAB,
> nên vùng Speech dự đoán bị dịch sớm một chút.

**Thao tác:** Chỉ cặp biên đầu và cuối trên waveform.

### Trang 8 — 20 giây

**Nói:**

> Với studio_M2, biên đầu muộn 10 mili giây, biên cuối trùng chuẩn;
> MAE là 5 mili giây. Sai lệch đầu có thể liên quan đến năng lượng yếu gần biên.
> Tổng hợp bốn file, MAE trung bình là 11,25 mili giây, với không có biên thừa hoặc thiếu.

**Thao tác:** Chỉ biên đầu rồi chuyển sang notebook để demo.

## Demo code — 60 giây

Dùng notebook `Nhóm_03-Phân_đoạn_tín hiệu_thành_tiếng_nói_và_khoảng_lặng/VoThanhQuan_BinarySearch.ipynb`
đã lưu kết quả thực thi, phù hợp thông báo nộp bài mới của thầy.

### Chuẩn bị trước khi trình bày

- Mở slide và notebook trước khi đến lượt.
- Trong notebook, chuẩn bị vị trí **mục 4 — Binary Search algorithm**, code cell có số thực thi `[4]`.
  Đặt màn hình ở đoạn `delta`, điều kiện dừng và cập nhật `lo`/`hi`.
- Chuẩn bị vị trí **mục 9 — Executed results**, code cell `[9]`, nơi gọi `RESULT = main()`.
  Output có mô hình học được, hình tìm ngưỡng, bốn hình TEST và bảng kết quả.
- Thu gọn các cell định nghĩa dài để chuyển giữa hai vị trí nhanh.

### 0–10 giây — Mở đúng bài của mình

**Nói:**

> Đây là notebook Binary Search riêng của em.
> Một lần gọi main xử lý đủ bốn file TEST.

**Thao tác:** Chỉ tên thuật toán, rồi chỉ `RESULT = main()` ở cell `[9]`.

### 10–35 giây — Chỉ phần quyết định ngưỡng

**Nói:**

> Hàm này đo hai mức lỗi năng lượng trên TRAIN.
> Hiệu dương thì cập nhật cận dưới để tăng ngưỡng.
> Hiệu âm thì cập nhật cận trên để giảm ngưỡng.
> Chương trình dừng khi hai mức gần bằng nhau hoặc khoảng tìm kiếm đủ nhỏ.

**Thao tác:** Ở cell `[4]`, lần lượt chỉ:

```python
silence_error, speech_error = binary_energy_errors(...)
delta = silence_error - speech_error
if abs(delta) <= 1e-10 or hi - lo <= 1e-10:
    ...
if delta > 0:
    lo = mid
else:
    hi = mid
```

Đoạn trên là phần trích để định vị khi demo; dấu `...` rút gọn những dòng đã có
trong notebook. Điều kiện chạy thật và lịch sử 24 vòng đã được lưu trong chương trình.

### 35–55 giây — Cho xem kết quả đã lưu

**Nói:**

> Đây là kết quả của cả bốn file kiểm thử.
> Bảng cho MAE lần lượt 30, 0, 10 và 5 mili giây.
> Trung bình là 11,25 mili giây. Bốn hình kèm theo chứa tín hiệu,
> STE, các biên chuẩn và dự đoán, cùng kết quả F0.

**Thao tác:** Trở lại output của cell `[9]`, chỉ bảng đủ bốn tên file và MAE.
Các hình TEST đã được diễn giải trên slide; dùng bảng để tổng hợp trong khoảng thời gian này.

### 55–60 giây — Bàn giao

**Nói:**

> Phần Binary Search của em kết thúc. Mời bạn Trung trình bày Histogram.

## Khi tập nói

Ưu tiên trang 3–5: quy trình, cách tăng/giảm ngưỡng và file có sai số lớn nhất.
Tới mốc 1:45 cần chuyển sang trang 5. Tới mốc 3:00 cần chuyển sang notebook.
Nếu chậm, rút ngắn nhận xét ở trang 6–8 và giữ đủ kết quả của cả bốn file.
