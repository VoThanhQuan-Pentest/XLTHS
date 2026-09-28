# Kịch bản slide 3 phút

Tổng cộng đúng 6 slide. Mỗi thuật toán chỉ dùng một slide vì hai slide cho mỗi thuật toán sẽ vượt thời gian. Thời lượng mục tiêu: 10 + 35 + 35 + 35 + 60 + 5 = 180 giây.

## Slide 1 — Chào và giới thiệu đề tài — 10 giây

### Nội dung trên slide

**PHÂN ĐOẠN TÍN HIỆU THÀNH SPEECH VÀ SILENCE**

So sánh Binary Search, Histogram và Statistical Gaussian

Họ tên — Lớp — Môn Xử lý tín hiệu số

### Bố cục Canva

Giữ slide tối giản. Tiêu đề ở giữa hoặc bên trái. Dùng một đoạn waveform mờ làm nền, không thêm phần mục lục.

### Lời nói

“Em xin chào thầy. Bài làm của em phân đoạn tín hiệu thu âm thành Speech và Silence bằng ba phương pháp. Em sẽ trình bày ngắn gọn cách tiến hành và kết quả trên toàn bộ bốn file kiểm thử.”

## Slide 2 — Binary Search — 35 giây

### Nội dung trên slide

```text
STE training + LAB
        ↓
Tách nhóm Speech / Silence
        ↓
Thử ngưỡng giữa miền chồng lấn
        ↓
Cân bằng phần nhầm lẫn hai lớp
        ↓
Khóa ngưỡng T = 0.00156
```

Góc dưới:

- Ngưỡng chung cho cả 4 WAV test
- MAE tổng hợp: **20.0 ms**
- Biên đúng/thừa/thiếu: **8 / 1 / 0**

### Hình dùng trên slide

Dùng `ket_qua/phone_M2_binary.png`. Trong Canva, crop để giữ waveform, normalized STE và panel F0. Đặt hình ở nửa phải, sơ đồ ở nửa trái.

### Lời nói

“Binary Search dùng LAB training để chia normalized STE thành hai nhóm Speech và Silence. Thuật toán liên tục thử ngưỡng giữa và thu hẹp khoảng tìm kiếm đến khi phần nhầm lẫn của hai lớp cân bằng. Ngưỡng 0.00156 được khóa và dùng chung cho toàn bộ test. Phương pháp đạt MAE 20 mili giây, nhưng có một biên thừa trên phone_F2 do nhiễu cuối bản ghi vượt ngưỡng.”

## Slide 3 — Histogram — 35 giây

### Nội dung trên slide

```text
Normalized STE của từng WAV
        ↓
Histogram và làm trơn
        ↓
Tìm hai đỉnh chính
        ↓
Tính ngưỡng có trọng số
        ↓
Phân loại và loại Silence < 200 ms
```

Góc dưới:

- Ngưỡng adaptive, tính riêng cho từng WAV
- MAE tổng hợp: **50.0 ms**
- Biên đúng/thừa/thiếu: **8 / 4 / 0**

### Hình dùng trên slide

Dùng `ket_qua/phone_F2_histogram.png`. Hình này thể hiện rõ các biên thừa tại khoảng 2.50–2.80 s và 3.44–3.64 s.

### Lời nói

“Histogram tự tính ngưỡng từ phân bố STE của từng WAV test. Training chỉ chọn số bin, mức làm trơn, trọng số và ngưỡng dự phòng. Ưu điểm là ngưỡng thích nghi theo mức năng lượng của bản ghi. Tuy nhiên, trên phone_F2, ngưỡng cao làm các vùng tiếng nói năng lượng thấp bị xem là Silence và tạo bốn biên thừa. Vì vậy MAE tổng hợp là 50 mili giây.”

## Slide 4 — Statistical Gaussian — 35 giây

### Nội dung trên slide

```text
STE training + LAB
        ↓
mean/std của Speech và Silence
        ↓
Chọn ngưỡng tách hai phân bố
        ↓
Khóa ngưỡng T = 0.00358
```

Các số liệu nhỏ bên cạnh:

- `meanSil = 0.000412`, `stdSil = 0.000920`
- `meanSp = 0.209630`, `stdSp = 0.240703`
- MAE tổng hợp: **12.5 ms**
- Biên đúng/thừa/thiếu: **8 / 0 / 0**

### Hình dùng trên slide

Dùng `ket_qua/phone_F2_statistical.png` làm hình chính. Có thể đặt `ket_qua/phan_bo_huan_luyen.png` thành inset nhỏ ở góc trên.

### Lời nói

“Phương pháp thống kê dùng toàn bộ khung training có nhãn để tính mean và standard deviation cho hai lớp. Chương trình chọn ngưỡng 0.00358 để tách hai phân bố rồi giữ cố định trên test. Đây là phương pháp tốt nhất trong thí nghiệm: MAE 12.5 mili giây, không có biên thừa hoặc thiếu. Trên phone_F2, cả hai biên dự đoán trùng biên chuẩn.”

## Slide 5 — So sánh kết quả trên toàn bộ tập test — 60 giây

### Bảng chính trên slide

| Tín hiệu | Binary MAE | Histogram MAE | Gaussian MAE |
|---|---:|---:|---:|
| phone_F2 | 45 ms | 55 ms | **0 ms** |
| phone_M2 | **10 ms** | 15 ms | 15 ms |
| studio_F2 | **20 ms** | 35 ms | 25 ms |
| studio_M2 | **5 ms** | 95 ms | 10 ms |
| **Tổng hợp** | **20.0 ms** | **50.0 ms** | **12.5 ms** |

Phía dưới bảng:

- Gaussian tốt nhất tổng thể: **12.5 ms**, không có biên thừa/thiếu.
- Histogram sai lớn nhất tại `studio_M2`: kết thúc Speech sớm **160 ms**.
- `phone_F2` nhiều nhiễu nhất: Binary có một biên thừa, Histogram có bốn biên thừa.
- Tất cả figure đều hiển thị waveform, STE, logSTE/logMA, F0, biên dự đoán xanh và biên chuẩn đỏ.

### Bố cục Canva

Bảng chiếm khoảng 70% slide. Bên phải đặt biểu đồ cột nhỏ cho ba giá trị MAE tổng hợp: 20.0, 50.0 và 12.5 ms. Dùng cùng màu cho mỗi phương pháp như ba slide trước. Không đặt bốn figure thu nhỏ vì người xem sẽ không đọc được.

### Lời nói

“Bảng này tổng hợp đủ bốn file trong TinHieuKiemThu. Gaussian cho kết quả tốt nhất toàn bộ với MAE 12.5 mili giây và không có biên thừa hoặc thiếu. Binary đứng thứ hai với 20 mili giây. Histogram có sai số cao nhất, đặc biệt kết thúc Speech sớm 160 mili giây trên studio_M2 và tạo bốn biên thừa trên phone_F2. Kết quả cũng cho thấy bản ghi phone_F2 có nhiễu nền cao nên khó phân đoạn hơn. Tất cả hình kết quả đều có đường F0 và hai loại biên để kiểm tra trực quan.”

## Slide 6 — Cảm ơn — 5 giây

### Nội dung trên slide

**EM XIN CẢM ƠN THẦY ĐÃ LẮNG NGHE**

Demo: `python3 main.py --no-noise`

### Lời nói

“Phần trình bày của em xin kết thúc. Em xin cảm ơn thầy và sẵn sàng demo chương trình.”

# Prompt Canva Pro cho bản 3 phút

```text
Hãy tạo một bài thuyết trình học thuật bằng tiếng Việt, tỷ lệ 16:9, gồm đúng 6 slide về đề tài “Phân đoạn tín hiệu thành Speech và Silence bằng ba phương pháp”. Thời lượng nói tối đa 3 phút. Người nghe là giảng viên môn Xử lý tín hiệu số.

Yêu cầu chung:
- Không trình bày lý thuyết nền hoặc công thức toán.
- Tập trung vào sơ đồ các bước thuật toán, hình kết quả, số liệu và nhận xét.
- Phong cách sạch, kỹ thuật, nền trắng hoặc xám rất nhạt.
- Dùng font Be Vietnam Pro hoặc Inter, tiêu đề xanh navy, điểm nhấn teal và cam.
- Giữ quy ước: biên dự đoán xanh dương, biên chuẩn đỏ nét đứt, F0 màu cam.
- Sơ đồ khối, bảng và biểu đồ phải chỉnh sửa được trong Canva.
- Dùng ít chữ, kích thước chữ lớn, không thêm agenda, tài liệu tham khảo hoặc slide ngoài sáu slide được yêu cầu.
- Dùng placeholder ảnh đúng tên file để tôi thay bằng PNG thật.

Slide 1, “Phân đoạn tín hiệu thành Speech và Silence”: phụ đề “So sánh Binary Search, Histogram và Statistical Gaussian”. Chừa chỗ cho họ tên, lớp và môn học. Thiết kế tối giản với waveform mờ.

Slide 2, “Binary Search”: bên trái vẽ sơ đồ STE training + LAB, tách Speech/Silence, thử ngưỡng giữa, cân bằng phần nhầm lẫn, khóa T = 0.00156. Bên phải tạo placeholder `ket_qua/phone_M2_binary.png`. Ghi MAE 20.0 ms và biên đúng/thừa/thiếu 8/1/0.

Slide 3, “Histogram”: bên trái vẽ sơ đồ normalized STE từng WAV, histogram và làm trơn, tìm hai đỉnh, ngưỡng có trọng số, phân loại, loại Silence ngắn hơn 200 ms. Bên phải tạo placeholder `ket_qua/phone_F2_histogram.png`. Nhấn mạnh “ngưỡng adaptive theo từng WAV”. Ghi MAE 50.0 ms và biên đúng/thừa/thiếu 8/4/0.

Slide 4, “Statistical Gaussian”: vẽ sơ đồ STE training + LAB, tính mean/std hai lớp, chọn ngưỡng tách phân bố, khóa T = 0.00358. Hiển thị meanSil 0.000412, stdSil 0.000920, meanSp 0.209630, stdSp 0.240703. Tạo placeholder lớn `ket_qua/phone_F2_statistical.png` và inset nhỏ `ket_qua/phan_bo_huan_luyen.png`. Ghi MAE 12.5 ms và biên đúng/thừa/thiếu 8/0/0.

Slide 5, “So sánh kết quả trên toàn bộ tập test”: tạo bảng gồm các dòng phone_F2, phone_M2, studio_F2, studio_M2 và Tổng hợp. Ba cột MAE là Binary, Histogram, Gaussian. Dữ liệu lần lượt: phone_F2 45, 55, 0 ms; phone_M2 10, 15, 15 ms; studio_F2 20, 35, 25 ms; studio_M2 5, 95, 10 ms; Tổng hợp 20.0, 50.0, 12.5 ms. Tạo biểu đồ cột nhỏ cho ba MAE tổng hợp. Ghi ba nhận xét: Gaussian tốt nhất và không có biên thừa/thiếu; Histogram kết thúc Speech sớm 160 ms trên studio_M2; phone_F2 tạo một biên thừa với Binary và bốn biên thừa với Histogram. Ghi nhỏ rằng tất cả figure có waveform, STE, logSTE/logMA, F0, biên xanh và biên đỏ.

Slide 6, “Em xin cảm ơn thầy đã lắng nghe”: thiết kế tối giản. Hiển thị nhỏ lệnh demo `python3 main.py --no-noise`.

Không tự tạo hoặc thay đổi số liệu. Không thêm slide thứ bảy. Không thu nhỏ chữ để nhét thêm nội dung.
```

## Nếu Canva tạo quá nhiều chữ

Giữ lại sơ đồ và ba con số ở mỗi slide thuật toán. Xóa mọi đoạn văn mà Canva tự thêm. Phần giải thích chi tiết nằm trong lời nói, không nằm trên slide.
