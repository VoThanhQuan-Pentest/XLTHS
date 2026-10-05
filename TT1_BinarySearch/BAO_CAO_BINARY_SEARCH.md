# BÁO CÁO THUẬT TOÁN BINARY SEARCH
## Phân đoạn tín hiệu thu âm thành Speech và Silence

Báo cáo mô tả thuật toán trong TT1_BinarySearch với phân khung cố định 25 ms / 10 ms, cùng số liệu đã chạy lại ở cấu hình này. Phần công thức phục vụ việc hiểu mã và viết báo cáo. Khi trình bày slide 3 phút, chỉ chọn sơ đồ các bước, hình kết quả và nhận xét theo yêu cầu của giảng viên.

Quy ước: các số thập phân trong công thức và mã dùng dấu chấm như Python. Thời gian LAB tính bằng giây; sai số biên tính bằng mili-giây.

## 1. Mục tiêu và ý tưởng

Chương trình nhận tín hiệu WAV và xác định các khoảng thời gian có tiếng nói hoặc khoảng lặng. Speech gồm cả âm hữu thanh và vô thanh; Silence có thể chứa nhiễu nền, không nhất thiết có biên độ bằng không.

Thuật toán dùng mức năng lượng ngắn hạn làm đặc trưng phân biệt. Nó học một ngưỡng T từ các khung training đã có nhãn, rồi giữ ngưỡng đó khi xử lý test:

$$
\widehat y_k=
\begin{cases}
1 \;(\mathrm{Speech}),& e_k\geq T,\\
0 \;(\mathrm{Silence}),& e_k<T.
\end{cases}
$$

Trong đó $e_k$ là STE chuẩn hóa của khung $k$ và $\widehat y_k$ là nhãn dự đoán ban đầu. Sau bước này, chương trình loại các khoảng Silence dự đoán ngắn hơn 200 ms.

Binary Search ở đây là phép chia đôi một khoảng ngưỡng để giải phương trình cân bằng mức nhầm lẫn. Nó tìm giá trị ngưỡng năng lượng, không trực tiếp tìm vị trí biên thời gian trên WAV.

## 2. Dữ liệu và nguyên tắc huấn luyện/kiểm thử

Các tệp WAV và LAB được ghép tự động theo cùng tên gốc.

| Tập | Các WAV | Vai trò |
|---|---|---|
| Training | phone_F1, phone_M1, studio_F1, studio_M1 | Học ngưỡng và kiểm chứng ở khung cố định |
| Test | phone_F2, phone_M2, studio_F2, studio_M2 | Đánh giá sau khi khóa tham số |

Tất cả WAV hiện có đều mono PCM 16-bit. Các bản ghi phone có tần số lấy mẫu 16.000 Hz; studio có tần số lấy mẫu 44.100 Hz.

Định dạng mỗi dòng phân đoạn LAB:

~~~text
thời_gian_bắt_đầu    thời_gian_kết_thúc    nhãn
~~~

| Nhãn LAB | Ý nghĩa | Nhãn nhị phân trong chương trình |
|---|---|---|
| sil | Silence | False, tức 0 |
| v | Voiced, âm hữu thanh | True, tức 1 |
| uv | Unvoiced, âm vô thanh | True, tức 1 |

Hai dòng F0mean/F0std cuối LAB là thống kê cao độ, không phải khoảng phân đoạn và không được dùng để tìm ngưỡng Speech/Silence.

Chương trình gom đặc trưng của cả bốn WAV training để học một ngưỡng chung. WAV vẫn được phân khung và chuẩn hóa riêng; chương trình không nối bốn bản ghi thành một tín hiệu dài. LAB test chỉ dùng trong bước đánh giá và vẽ biên đỏ.

## 3. Quy trình tổng thể

~~~mermaid
flowchart TD
    A[WAV training] --> B[Đọc PCM và chia khung]
    B --> C[Tính STE và chuẩn hóa riêng từng WAV]
    L[LAB training] --> D[Gán nhãn theo tâm khung]
    C --> D
    D --> E[Gom nhóm Silence và Speech]
    E --> F[Binary Search học ngưỡng chung]
    F --> G[Khóa tham số]
    T[WAV test] --> H[Tính normalized STE]
    G --> I[Phân loại từng khung]
    H --> I
    I --> J[Loại Silence dưới 200 ms]
    J --> K[Trích biên và vẽ kết quả]
    R[LAB test] --> M[Đánh giá MAE và RMSE]
    K --> M
~~~

## 4. Bước 1: Đọc và đổi biên độ PCM

Gọi $q[n]$ là mẫu PCM 16-bit có dấu, nhận giá trị từ -32768 đến 32767. Mẫu số thực được tính:

$$
x[n]=\frac{q[n]}{32768}.
$$

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| $q[n]$ | Giá trị nguyên của mẫu WAV | raw_samples |
| $x[n]$ | Biên độ sau khi đổi sang float | samples |
| $f_s$ | Tần số lấy mẫu, đơn vị Hz | fs |

Mã trong hàm read_record ở ../speech_silence/data.py:

~~~python
raw_samples = np.frombuffer(raw_bytes, dtype=np.int16)
samples = raw_samples.astype(np.float64) / 32768.0
~~~

Ví dụ, q[n] = 528 tương ứng x[n] = 528/32768 = 0.01611328125.

Đây là đổi thang biên độ PCM; chuẩn hóa STE ở bước sau là một thao tác khác.

## 5. Bước 2: Chia khung chồng lấn

Với độ dài khung W_ms và bước dịch H_ms:

$$
N=\operatorname{round}\left(\frac{f_sW_{ms}}{1000}\right),
\qquad
H=\operatorname{round}\left(\frac{f_sH_{ms}}{1000}\right).
$$

Khung k bắt đầu tại chỉ số a_k = kH:

$$
x_k[n]=x[a_k+n],\qquad n=0,\ldots,N-1.
$$

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| k | Chỉ số khung, bắt đầu từ 0 | Chỉ số hàng trong frames |
| N | Số mẫu trong một khung | frame_len |
| H | Số mẫu dịch giữa hai khung | hop_len |
| a_k | Chỉ số mẫu bắt đầu khung k | starts[k] |
| x_k[n] | Mẫu n thuộc khung k | frames[k, n] |
| W_ms | Độ dài khung theo ms | frame_ms |
| H_ms | Bước dịch theo ms | hop_ms |

Mã trong hàm extract ở ../speech_silence/features.py:

~~~python
frame_len = max(1, round(fs * frame_ms / 1000))
hop_len = max(1, round(fs * hop_ms / 1000))
starts = np.arange(0, len(samples), hop_len)
padded = np.pad(samples, (0, frame_len))
frames = np.lib.stride_tricks.sliding_window_view(padded, frame_len)[starts]
~~~

Cấu hình chung được cố định trong ../speech_silence/config.py: khung 25 ms, bước dịch 10 ms:

| Tần số lấy mẫu | Số mẫu/khung N | Bước dịch H |
|---:|---:|---:|
| 16.000 Hz | 400 | 160 |
| 44.100 Hz | 1102 | 441 |

Các khung chồng lấn khoảng 15 ms. Ở 44,1 kHz, round(1102.5) = 1102 nên khung thực dài khoảng 24,989 ms; đây là làm tròn về số mẫu nguyên, cả ba phương pháp dùng cùng quy tắc. Khung cuối được đệm zero; STE vẫn chia cho N, kể cả khi số mẫu có thật ở cuối WAV ít hơn N.

## 6. Bước 3: Tính STE, MA và chuẩn hóa STE

### 6.1. Năng lượng trung bình theo khung

Chương trình dùng phiên bản STE trung bình bình phương:

$$
E_k=\frac{1}{N}\sum_{n=0}^{N-1}x_k[n]^2.
$$

E_k là giá trị STE thô của khung k. Một số tài liệu gọi STE là tổng bình phương; mã hiện tại chia thêm cho N. Báo cáo này luôn theo cách tính trong mã.

~~~python
ste = np.mean(frames * frames, axis=1)
~~~

frames * frames bình phương từng mẫu; axis=1 lấy trung bình theo chiều mẫu trong mỗi khung.

### 6.2. Độ lớn biên độ trung bình

$$
MA_k=\frac{1}{N}\sum_{n=0}^{N-1}|x_k[n]|.
$$

~~~python
ma = np.mean(np.abs(frames), axis=1)
~~~

MA phục vụ hình minh họa. Ngưỡng Binary Search trong bài làm này được học từ normalized STE.

### 6.3. Chuẩn hóa STE

Với một bản ghi có K khung:

$$
E_{\max}=\max_{0\leq j<K}E_j,
\qquad
e_k=
\begin{cases}
E_k/E_{\max},&E_{\max}>0,\\
0,&E_{\max}=0.
\end{cases}
$$

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| E_k | STE thô của khung k | ste[k] |
| E_max | STE lớn nhất trong chính WAV đang xử lý | max_ste |
| e_k | STE chuẩn hóa trong khoảng [0,1] | normalized_ste[k] |
| K | Số khung của WAV | len(ste) |

~~~python
max_ste = float(np.max(ste))
normalized_ste = ste / max_ste if max_ste > 0 else np.zeros_like(ste)
~~~

Mỗi WAV có E_max riêng. Vì vậy ngưỡng chung được áp dụng lên cùng thang normalized STE, không áp trực tiếp lên biên độ hoặc STE thô của các bản ghi khác nhau. Chuẩn hóa giảm ảnh hưởng của chênh lệch mức âm lượng nhưng không loại hết ảnh hưởng của nhiễu nền hoặc một xung có năng lượng quá lớn.

### 6.4. Đặc trưng logarithmic trên hình

$$
L^{STE}_k=10\log_{10}\big(\max(E_k,10^{-12})\big),
\qquad
L^{MA}_k=20\log_{10}\big(\max(MA_k,10^{-12})\big).
$$

~~~python
log_ste = 10 * np.log10(np.maximum(ste, 1e-12))
log_ma = 20 * np.log10(np.maximum(ma, 1e-12))
~~~

Sàn 10^-12 giúp tránh log(0). logSTE/logMA giúp quan sát các vùng năng lượng nhỏ; Binary Search hiện tại dùng e_k, không dùng hai giá trị log này.

## 7. Bước 4: Chọn LAB và gán nhãn từng khung training

Chương trình lấy LAB có cùng tên gốc với WAV. Ví dụ phone_F1.wav đi cùng phone_F1.lab. Không chọn LAB của một tệp khác.

Với khung đầy đủ, thời điểm giữa khung:

$$
t_k=\frac{a_k+N/2}{f_s}.
$$

Ở khung cuối, mã dùng số mẫu thực còn lại:

$$
t_k=\frac{a_k+\min(N,L-a_k)/2}{f_s},
$$

trong đó L là tổng số mẫu của WAV.

Nếu một dòng LAB có khoảng [u_j,v_j) và nhãn c_j, chương trình tìm dòng thỏa:

$$
u_j\leq t_k<v_j.
$$

Nhãn của khung:

$$
y_k=
\begin{cases}
0,&c_j=\mathrm{sil},\\
1,&c_j\in\{\mathrm{v},\mathrm{uv}\}.
\end{cases}
$$

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| t_k | Thời điểm giữa khung theo giây | times[k] |
| u_j, v_j | Thời điểm bắt đầu/kết thúc dòng LAB | segment.start, segment.end |
| c_j | Nhãn văn bản sil/v/uv | fields[2] khi đọc LAB |
| y_k | Nhãn training của khung | truth[k], hoặc is_speech[k] |
| valid[k] | Tâm khung thuộc vùng LAB có nhãn | is_valid[k] |

Mã gộp v/uv thành Speech:

~~~python
intervals.append(Interval(start_time, end_time, fields[2] != "sil"))
~~~

Mã chiếu khoảng thời gian LAB vào các tâm khung:

~~~python
for segment in labels:
    in_segment = (times >= segment.start) & (times < segment.end)
    is_valid |= in_segment
    is_speech[in_segment] = segment.speech
~~~

Khung có tâm nằm ngoài phần được LAB gán nhãn không được đưa vào thống kê có nhãn. Phần đuôi WAV chưa có nhãn cũng bị loại khỏi đánh giá.

Một khung có thể chứa cả Silence và Speech vì nó đi qua biên. Mã vẫn gán một nhãn theo tâm khung; không dùng tỷ lệ giao nhau để gán nhãn. Điều này có thể làm hai nhóm năng lượng chồng lấn gần ranh giới.

## 8. Bước 5: Gom đặc trưng từ bốn WAV training

Sau khi chuẩn hóa riêng từng WAV và gán nhãn, chương trình gom:

$$
\mathcal S=\{s_1,\ldots,s_{N_{Sil}}\}
=\{e_k:y_k=0\},
$$

$$
\mathcal P=\{p_1,\ldots,p_{N_{Sp}}\}
=\{e_k:y_k=1\}.
$$

Các tập ở đây gom khung thuộc tất cả bản ghi training hợp lệ:

| WAV training | Khung Silence | Khung Speech |
|---|---:|---:|
| phone_F1 | 100 | 222 |
| phone_M1 | 108 | 306 |
| studio_F1 | 139 | 147 |
| studio_M1 | 154 | 119 |
| Tổng cộng | 501 | 794 |

Mã trong hàm training_arrays ở ../speech_silence/pipeline.py:

~~~python
truth, valid = speech_at(features.times, record.labels)
silence_values.extend(features.normalized_ste[valid & ~truth])
speech_values.extend(features.normalized_ste[valid & truth])
~~~

Các phần tử của hai mảng không cần sắp xếp. Binary Search phía sau chia đôi miền giá trị T, không tìm một phần tử trong mảng đã sắp xếp.

## 9. Bước 6: Học ngưỡng bằng Binary Search

### 9.1. Miền tìm kiếm

Đặt:

$$
s_{\max}=\max_i s_i,\qquad p_{\min}=\min_j p_j.
$$

Nếu s_max < p_min, hai lớp không chồng lấn. Chương trình chọn ngưỡng giữa khoảng trống:

$$
T=\frac{s_{\max}+p_{\min}}{2}.
$$

Nếu hai lớp chồng lấn, đặt cận:

$$
lo=p_{\min},\qquad hi=s_{\max}.
$$

Với dữ liệu thực tế:

$$
lo=0.00005423969907103939,\qquad
hi=0.011368689197374226.
$$

Các số này là cận tìm kiếm, không phải hai ngưỡng cuối cùng. Chương trình chỉ học một T.

Trong trường hợp hai cận trùng nhau, nhánh dự phòng của mã lấy trung điểm hai trung bình lớp rồi giới hạn về [0,1]. Trường hợp này không xảy ra trong thí nghiệm hiện tại.

### 9.2. Hai mức nhầm lẫn

Với ngưỡng thử T:

$$
A(T)=\frac{1}{N_{Sil}}\sum_{i=1}^{N_{Sil}}\max(s_i-T,0),
$$

$$
B(T)=\frac{1}{N_{Sp}}\sum_{j=1}^{N_{Sp}}\max(T-p_j,0).
$$

A(T) là mức Silence vượt ngưỡng trung bình; B(T) là mức Speech hụt dưới ngưỡng trung bình.

Ví dụ với một giá trị s_i = 0.002 và T = 0.0015, phần đóng góp vào A là 0.0005. Nếu s_i = 0.001, phần đóng góp bằng 0. Với p_j = 0.0012, phần đóng góp vào B là 0.0003.

Các mức A/B tính độ lớn của phần nhầm lẫn, không chỉ đếm số khung sai. Đây không phải tỷ lệ False Alarm hay tỷ lệ bỏ sót Speech.

Ngưỡng được chọn sao cho:

$$
D(T)=A(T)-B(T)\approx 0.
$$

Mỗi tổng được chia cho số khung của chính lớp đó, nên hai lớp có trọng số ngang nhau ở cấp lớp. Trong mỗi lớp, các khung có trọng số bằng nhau; bản ghi dài hơn có thể đóng góp nhiều khung hơn.

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| s_i | normalized STE của khung Silence thứ i | silence[i-1] |
| p_j | normalized STE của khung Speech thứ j | speech[j-1] |
| N_Sil | Số khung Silence training | len(silence) |
| N_Sp | Số khung Speech training | len(speech) |
| T đang thử | Giá trị giữa hai cận | mid |
| A(T) | Mức Silence vượt T trung bình | np.maximum(silence-mid, 0).mean() |
| B(T) | Mức Speech hụt dưới T trung bình | np.maximum(mid-speech, 0).mean() |
| D(T) | Hiệu hai mức nhầm lẫn | delta |
| lo, hi | Cận tìm kiếm dưới/trên | lo, hi |

Cách học T này cân bằng mức nhầm lẫn năng lượng. Nó không bảo đảm tối đa hóa số khung đúng hoặc trực tiếp tối thiểu hóa MAE biên.

### 9.3. Vì sao có thể chia đôi?

Khi tăng T, A(T) không tăng vì Silence phải vượt một ngưỡng cao hơn. Đồng thời B(T) không giảm vì nhiều giá trị Speech nằm thấp hơn T. Do đó D(T) là hàm không tăng theo T.

- D(T) > 0: mức Silence vượt ngưỡng đang lớn hơn. Cần tăng T, nên giữ nửa khoảng phía trên bằng lo = mid.
- D(T) < 0: mức Speech hụt dưới ngưỡng đang lớn hơn. Cần giảm T, nên giữ nửa khoảng phía dưới bằng hi = mid.
- D(T) = 0: đã cân bằng; mã hiện tại vẫn thu hẹp cận hi và tiếp tục đến khi đạt điều kiện dừng.

### 9.4. Mã lõi thực tế

~~~python
smax, pmin = float(np.max(silence)), float(np.min(speech))
if smax < pmin:
    return (smax + pmin) / 2

lo, hi = pmin, smax
if lo >= hi:
    return float(np.clip((np.mean(silence) + np.mean(speech)) / 2, 0, 1))

for _ in range(100):
    mid = (lo + hi) / 2
    delta = (
        np.maximum(silence - mid, 0).mean()
        - np.maximum(mid - speech, 0).mean()
    )
    if delta > 0:
        lo = mid
    else:
        hi = mid
    if hi - lo < 1e-8:
        break

return float(np.clip((lo + hi) / 2, 0, 1))
~~~

Mã đầy đủ nằm trong [algorithm.py](algorithm.py), hàm binary_threshold.

### 9.5. Điều kiện dừng và hội tụ

Chương trình dừng khi:

$$
hi-lo<\varepsilon,\qquad \varepsilon=10^{-8},
$$

hoặc đã thực hiện 100 vòng. Epsilon là dung sai trên độ rộng miền ngưỡng; không phải dung sai thời gian biên.

Sau m lần chia đôi, độ rộng khoảng tìm kiếm bằng:

$$
\frac{hi_0-lo_0}{2^m}.
$$

Các bước đầu trên bốn WAV training:

| Vòng | mid | A(mid) | B(mid) | Điều chỉnh |
|---:|---:|---:|---:|---|
| 1 | 0.005711464 | 0.000011292 | 0.000568169 | hi = mid |
| 2 | 0.002882852 | 0.000021351 | 0.000188785 | hi = mid |
| 3 | 0.001468546 | 0.000040727 | 0.000058683 | hi = mid |
| 4 | 0.000761393 | 0.000098192 | 0.000014041 | lo = mid |
| 5 | 0.001114969 | 0.000055792 | 0.000033158 | lo = mid |
| 6 | 0.001291758 | 0.000046498 | 0.000045422 | lo = mid |
| 7 | 0.001380152 | 0.000043303 | 0.000051913 | hi = mid |
| 8 | 0.001335955 | 0.000044803 | 0.000048640 | hi = mid |
| 9 | 0.001313856 | 0.000045603 | 0.000047025 | hi = mid |
| 10 | 0.001302807 | 0.000046045 | 0.000046218 | hi = mid |

Sau 21 vòng, khoảng còn rộng khoảng 5.39515 × 10^-9. Ngưỡng cuối:

$$
\boxed{T=0.0013012665647267243}.
$$

Mỗi vòng cần tính trên hai mảng training. Chi phí học ngưỡng trực tiếp xấp xỉ O(m(N_Sil+N_Sp)); bộ nhớ đặc trưng xấp xỉ O(N_Sil+N_Sp).

## 10. Kiểm chứng ở khung cố định và học ngưỡng cuối

Cả ba thuật toán luôn dùng khung 25 ms, bước dịch 10 ms. Binary Search không chọn frame bằng Cross Validation nữa. Chương trình vẫn chạy Leave-One-Out trên bốn WAV training để báo cáo khả năng tổng quát:

1. Giữ lại một WAV training để kiểm chứng.
2. Học ngưỡng từ ba WAV training còn lại, ở 25/10 ms.
3. Dự đoán WAV giữ lại và tính lỗi.
4. Lặp cho cả bốn WAV. Tất cả các lượt đều dùng cùng cấu hình phân khung.
5. Học lại ngưỡng cuối trên toàn bộ bốn WAV training và khóa trước khi đánh giá test.

Lỗi phân lớp cân bằng:

$$
BER=\frac{1}{2}
\left(
\frac{FP}{N_{Sil}}+\frac{FN}{N_{Sp}}
\right).
$$

FP là số khung Silence bị dự đoán thành Speech; FN là số khung Speech bị dự đoán thành Silence. Trong phép đánh giá này, N_Sil/N_Sp là số khung có nhãn của WAV đang kiểm chứng, không nhất thiết bằng 501/794 của toàn training.

Kết quả kiểm chứng ở cấu hình cố định: BER trung bình 0.0908657481, hai biên lỗi cộng dồn và MAE trung bình theo lượt 20 ms. Các chỉ số này chỉ báo cáo tại 25 ms, không được dùng để chuyển về khung 20/30 ms. Không có dung sai ±200 ms khi ghép biên.

Mô hình cũ học ở khung khác bị predict từ chối trước khi tính đặc trưng; cần chạy main.py để huấn luyện lại ở 25/10 ms.

## 11. Ví dụ tính toán thực tế từ phone_F1

### 11.1. Khung đang xét

Tần số lấy mẫu f_s = 16000 Hz, N = 400, H = 160. Với khung k = 52:

$$
a_{52}=52\times160=8320.
$$

Khung lấy mẫu từ chỉ số 8320 đến 8719, tương ứng khoảng [0.520,0.545) giây. Tâm khung:

$$
t_{52}=\frac{8320+400/2}{16000}=0.5325\ \mathrm{s}.
$$

### 11.2. STE và normalized STE

Từ 400 mẫu thực tế:

$$
\sum_{n=0}^{399}x_{52}[n]^2=0.03776868898421526.
$$

$$
E_{52}=\frac{0.03776868898421526}{400}
=0.00009442172246053815.
$$

STE lớn nhất của phone_F1.wav:

$$
E_{\max}=0.12892314322991297.
$$

Vì vậy:

$$
e_{52}=
\frac{0.00009442172246053815}{0.12892314322991297}
=0.0007323876853681168.
$$

### 11.3. LAB và quyết định ban đầu

Các dòng đầu của phone_F1.lab:

~~~text
0.00    0.53    sil
0.53    1.14    v
~~~

Tâm 0.5325 s nằm trong [0.53,1.14), nên nhãn training của khung là Speech. Tuy nhiên:

$$
e_{52}=0.0007323877<T=0.0013012666.
$$

Do đó quyết định ngưỡng ban đầu xem khung này là Silence. Đây là một khung Speech năng lượng thấp bị nhầm; ngưỡng chung không bảo đảm mọi khung đều đúng.

Khung kế tiếp có tâm 0.5425 s, normalized STE khoảng 0.006526, cao hơn T nên được xem là Speech. Hậu xử lý có thể gộp các Silence ngắn bên trong Speech, nhưng vùng Silence đầu bản ghi vốn dài hơn 200 ms vẫn được giữ.

## 12. Bước 7: Dự đoán test, hậu xử lý và trích biên

### 12.1. Phân loại khung

Mỗi WAV test được phân khung, tính STE và chuẩn hóa bằng E_max của chính nó. Sau đó:

~~~python
threshold = model["binary_threshold"]
raw_mask = features.normalized_ste >= threshold
~~~

raw_mask là mảng boolean: True là Speech, False là Silence. Nhãn test không đi vào phép tính này.

### 12.2. Loại Silence ảo dưới 200 ms

Gọi b_k là biên bắt đầu khung k; với khung đầy đủ:

$$
b_k=\frac{kH}{f_s}.
$$

Một đoạn Silence liên tục chứa khung từ a đến b-1 có thời lượng:

$$
d=b_b-b_a.
$$

Nếu d < 0.2 giây, chuyển toàn bộ đoạn đó thành Speech:

$$
d<0.2\ \mathrm{s}\quad\Longrightarrow\quad
\widehat y_a=\cdots=\widehat y_{b-1}=1.
$$

Với bước dịch 10 ms, đoạn 19 bước tương ứng 190 ms bị loại; đoạn 20 bước tương ứng 200 ms được giữ. Mã dùng epsilon số học rất nhỏ để không loại nhầm đoạn đúng 200 ms vì sai số float.

Quy tắc hiện tại áp dụng cả ở đầu và cuối WAV. Nó gộp Silence ngắn nhưng không loại Speech ngắn. Vì vậy một đột biến nhiễu thành Speech vẫn có thể tồn tại.

### 12.3. Trích biên cuối

Biên được tạo khi hai khung liên tiếp có nhãn khác nhau:

$$
\widehat y_k\neq\widehat y_{k-1}
\quad\Longrightarrow\quad
\widehat t=\frac{kH}{f_s}.
$$

Mã:

~~~python
changes = np.flatnonzero(np.diff(mask)) + 1
boundaries = [(float(edges[i]), bool(mask[i])) for i in changes]
~~~

Trong mã thực tế, tên biến nội bộ có thể là change_indices/change_points; chức năng nằm trong predicted_boundaries của ../speech_silence/features.py.

Nhãn training được gán tại tâm khung, trong khi biên dự đoán đặt tại đầu khung chuyển trạng thái. Đây là quy ước thời gian của chương trình hiện tại. Sự chồng lấn khung và quy ước này có thể làm biên sớm hoặc muộn, ngoài ảnh hưởng của ngưỡng và nhiễu. Bước dịch 10 ms quyết định độ phân giải của vị trí biên.

## 13. Đường F0 trên figure

F0 phục vụ minh họa các vùng có tính tuần hoàn; nó không tham gia quyết định ngưỡng Binary Search.

Chương trình trừ trung bình và nhân cửa sổ Hamming:

$$
z_k[n]=(x_k[n]-\overline{x}_k)w[n].
$$

Với N > 1, cửa sổ Hamming trong np.hamming(N) có dạng:

$$
w[n]=0.54-0.46\cos\left(\frac{2\pi n}{N-1}\right).
$$

Tự tương quan không chia theo số mẫu còn lại ở mỗi lag:

$$
R_k[\ell]=\sum_{n=0}^{N-1-\ell}z_k[n]z_k[n+\ell].
$$

Chương trình tính nhanh R bằng FFT/IFFT với đệm zero, sau đó tìm lag cực đại trong dải ứng với khoảng 60–400 Hz:

$$
\ell_{\min}=\max(1,\lfloor f_s/400\rfloor),
\qquad
\ell_{\max}=\min(N-1,\lfloor f_s/60\rfloor).
$$

Với lag tốt nhất $\ell_*$:

$$
F0_k=\frac{f_s}{\ell_*},
\qquad
\rho_k=\frac{R_k[\ell_*]}{R_k[0]}.
$$

| Ký hiệu | Ý nghĩa | Biến trong mã |
|---|---|---|
| $w[n]$ | Cửa sổ Hamming dùng riêng cho F0 | window |
| $\overline{x}_k$ | Trung bình mẫu âm thanh trong khung | np.mean(frame) |
| $z_k[n]$ | Khung đã trừ DC và nhân cửa sổ | centered |
| $R_k[\ell]$ | Tự tương quan tại độ trễ $\ell$ | correlation[lag] |
| $\ell_*$ | Lag có tự tương quan lớn nhất trong dải | best_lag |
| $\rho_k$ | Mức tương quan so với lag 0 | correlation[best_lag]/correlation[0] |
| $F0_k$ | Cao độ ước lượng theo Hz | result[index] |

Chỉ khung có normalized STE từ 0.01 trở lên và $\rho_k$ từ 0.30 trở lên mới có F0; các khung còn lại nhận NaN. Khoảng trống F0 không chứng minh chắc chắn khung là Silence/vô thanh, vì điều kiện năng lượng cũng có thể bỏ qua Speech yếu. Đỉnh F0 cao bất thường có thể do nhầm họa âm.

Đường ngang F0mean từ LAB chỉ là thống kê tham chiếu, không phải F0 chuẩn theo từng khung. STE dùng cửa sổ chữ nhật; cửa sổ Hamming ở đây chỉ áp dụng khi ước lượng F0.

## 14. Đánh giá MAE/RMSE và kết quả thực nghiệm

### 14.1. Cách ghép biên

Biên chuẩn chỉ gồm các chuyển tiếp Speech/Silence sau khi gộp v/uv, không gồm mọi chuyển tiếp hữu thanh/vô thanh.

Mã ghép một-một các biên cùng hướng theo thứ tự: ưu tiên số cặp lớn nhất, rồi tổng sai lệch nhỏ nhất. Không có cửa sổ chấp nhận ±200 ms. Biên ghép không đồng nghĩa biên đã chính xác; MAE/RMSE biểu thị độ lệch thực tế.

Với $M$ cặp ghép, $t_i$ là biên chuẩn theo giây, $\widehat t_i$ là biên dự đoán:

$$
d_i=1000(\widehat t_i-t_i),
$$

$$
MAE=\frac{1}{M}\sum_{i=1}^{M}|d_i|,
\qquad
RMSE=\sqrt{\frac{1}{M}\sum_{i=1}^{M}d_i^2}.
$$

d_i, MAE và RMSE đều tính bằng ms. Nếu M = 0 thì hai chỉ số không xác định, không gán bằng 0. Mã nằm trong boundary_scores ở ../speech_silence/evaluation.py.

Các biên dự đoán thừa và biên chuẩn thiếu được báo riêng vì chúng không đi vào MAE/RMSE của các cặp đã ghép.

### 14.2. Bảng kết quả đủ bốn WAV test

| WAV | Ngưỡng T | MAE | RMSE | Ghép/thừa/thiếu |
|---|---:|---:|---:|---|
| phone_F2 | 0.00130127 | 50.0 ms | 64.0 ms | 2 / 3 / 0 |
| phone_M2 | 0.00130127 | 10.0 ms | 10.0 ms | 2 / 0 / 0 |
| studio_F2 | 0.00130127 | 15.0 ms | 15.8 ms | 2 / 0 / 0 |
| studio_M2 | 0.00130127 | 5.0 ms | 7.1 ms | 2 / 0 / 0 |
| Gộp 8 cặp biên | — | 20.0 ms | 33.5 ms | 8 / 3 / 0 |

Cả bốn bản ghi hiện tại có một vùng Speech sau khi gộp v/uv. Vì mỗi tệp đều ghép được hai biên, MAE trung bình theo tệp bằng MAE gộp. RMSE gộp phải tính từ các sai số bình phương hoặc trọng số số cặp, không lấy trung bình bốn RMSE.

### 14.3. phone_F2: sai lệch rõ và ba biên thừa

![Binary Search trên phone_F2](ket_qua/phone_F2.png)

- Biên bắt đầu chuẩn 1.02 s, dự đoán 1.01 s: sớm 10 ms.
- Biên kết thúc chuẩn 4.04 s, dự đoán 4.13 s: muộn 90 ms.
- Ba biên thừa tại 0.61 s, 0.63 s và 4.57 s.
- MAE = (10 + 90)/2 = 50 ms.
- RMSE = sqrt((10² + 90²)/2) ≈ 64.0 ms.

Ở vùng Silence đầu bản ghi, một đoạn nhiễu 0.61–0.63 s bị nhận thành Speech, tạo hai biên thừa. Tại 0.61 s, e ≈ 0.00159180 vượt T ≈ 0.00130127. Quy tắc 200 ms chỉ gộp Silence ngắn; không loại Speech ngắn 20 ms này.

Đối chiếu trước/sau hậu xử lý ở cuối tệp:

| Khoảng | Phân loại theo ngưỡng | Sau quy tắc 200 ms |
|---|---|---|
| 4.13–4.57 s | Silence | Silence |
| 4.57–4.58 s | Speech | Speech |
| 4.58–4.76 s | Silence, 180 ms | Chuyển thành Speech |
| 4.76–4.78 s | Speech | Speech |
| 4.78–4.80 s | Silence, 20 ms | Chuyển thành Speech |

Khung bắt đầu tại 4.57 s có e ≈ 0.00131194, chỉ cao hơn T một chút. Các khung nhiễu vượt ngưỡng kết hợp việc gộp Silence ngắn tạo Speech giả kéo từ 4.57 s đến cuối WAV. Như vậy lỗi liên quan cả nhiễu nền lẫn chính sách hậu xử lý.

Các Silence ngắn bên trong Speech ở 2.62–2.69 s và 3.56–3.61 s được gộp đúng mục đích, tránh chia tiếng nói thành nhiều đoạn.

F0 trung vị ước lượng 150.9 Hz, F0mean LAB 145 Hz. Những đỉnh nhọn và khoảng trống vẫn cần được xem như hạn chế của bộ ước lượng đơn giản.

### 14.4. phone_M2: hai biên gần chuẩn

![Binary Search trên phone_M2](ket_qua/phone_M2.png)

Biên bắt đầu 0.52 s so với chuẩn 0.53 s, biên kết thúc 2.51 s so với chuẩn 2.52 s. Cả hai đều sớm 10 ms. MAE và RMSE cùng bằng 10 ms; không có biên thừa/thiếu. Độ lệch tương đương một bước dịch khung.

F0 trung vị 139.1 Hz, F0mean LAB 129 Hz. F0 là tín hiệu minh họa, không được dùng để đưa hai biên về gần LAB.

### 14.5. studio_F2: biên sớm 10 và 20 ms

![Binary Search trên studio_F2](ket_qua/studio_F2.png)

Biên bắt đầu dự đoán 0.76 s so với chuẩn 0.77 s: sớm 10 ms; biên kết thúc 2.35 s so với chuẩn 2.37 s: sớm 20 ms. MAE = 15 ms, RMSE ≈ 15.8 ms; không có biên thừa/thiếu.

Khung chồng lấn chứa cả hai trạng thái gần ranh giới và quy ước gán biên tại đầu khung là nguyên nhân khả dĩ của độ lệch. Không thể tách riêng ảnh hưởng từng nguyên nhân chỉ từ hai vị trí biên.

F0 trung vị 184.5 Hz, F0mean LAB 200 Hz.

### 14.6. studio_M2: kết quả chính xác nhất của Binary Search

![Binary Search trên studio_M2](ket_qua/studio_M2.png)

Biên bắt đầu trùng chuẩn tại 0.45 s; biên kết thúc 1.92 s, sớm 10 ms so với chuẩn 1.93 s. MAE = 5 ms, RMSE ≈ 7.1 ms; không có biên thừa/thiếu.

F0 trung vị 141.6 Hz, F0mean LAB 155 Hz. Khác biệt giữa trung vị ước lượng và trung bình LAB không phải sai số F0 theo từng khung; hai thống kê và tập khung có thể khác nhau.

## 15. Ảnh hưởng của nhiễu và giới hạn

### 15.1. Quan sát trên dữ liệu gốc

SNR nền ước lượng từ các vùng có nhãn:

$$
SNR_{\text{ước lượng}}
=10\log_{10}
\frac{\max(P_{Sp}-P_{Sil},10^{-12})}
{\max(P_{Sil},10^{-12})}.
$$

P_Sp là công suất trung bình ở vùng Speech quan sát được, gồm cả nhiễu; P_Sil là công suất vùng Silence. Phép tính giả định nhiễu trong Speech có mức gần với Silence. LAB test chỉ được dùng sau suy luận để phân tích này.

| WAV | SNR nền ước lượng |
|---|---:|
| phone_F2 | 24.8 dB |
| phone_M2 | 27.0 dB |
| studio_F2 | 49.3 dB |
| studio_M2 | 37.7 dB |

phone_F2 có SNR ước lượng thấp nhất và có lỗi rõ nhất trong bốn tệp. Tuy nhiên người nói, nội dung và mức năng lượng cũng khác nhau, nên không thể quy mọi sai lệch chỉ cho SNR.

### 15.2. Khảo sát cộng nhiễu trên chính bốn WAV test

Kết quả phụ lấy từ chế độ khảo sát nhiễu đã chạy của nhóm. Ba seed 2026/2027/2028 tạo nhiễu trắng với tỷ số:

$$
Q=10\log_{10}\frac{P_{\mathrm{WAV}}}{P_{\text{nhiễu thêm}}},
\qquad
\sigma_{\text{nhiễu}}=\sqrt{\frac{P_{\mathrm{WAV}}}{10^{Q/10}}}.
$$

P_WAV là công suất toàn bản ghi, gồm cả Speech và Silence. Q không phải SNR đo từ tín hiệu tiếng nói sạch.

| Q | BER trung bình Binary Search trên 4 tệp × 3 seed |
|---:|---:|
| 30 dB | 0.028 |
| 20 dB | 0.292 |
| 10 dB | 0.500 |
| 0 dB | 0.500 |

Ngưỡng cố định suy giảm mạnh khi nền nhiễu tăng so với training. BER = 0.5 trong trường hợp này phù hợp với việc dự đoán gần như toàn bộ thành một lớp, không có nghĩa mọi biên đều lệch 50%.

### 15.3. Các giới hạn cần nêu khi bảo vệ

- Chỉ dùng năng lượng để phân biệt nên nhiễu lớn và Speech yếu có thể chồng lấn.
- Ngưỡng chung có thể không thích hợp với một môi trường rất khác training.
- Chuẩn hóa theo cực đại từng WAV có thể chịu ảnh hưởng của một xung năng lượng lớn.
- Quy tắc 200 ms có thể nối một Speech giả tới đuôi WAV như phone_F2; mã hiện tại không loại Speech ngắn.
- MAE/RMSE chỉ phản ánh các cặp ghép; phải đọc kèm biên thừa/thiếu.
- Bộ dữ liệu nhỏ và mỗi WAV chỉ có một vùng Speech nhị phân; chưa đủ để khẳng định hiệu quả trên hội thoại nhiều khoảng nghỉ.
- F0 tự tương quan chỉ là phần minh họa bổ trợ và có thể nhầm họa âm.

## 16. Tổ chức mã và cách demo

| Tệp/hàm | Vai trò |
|---|---|
| main.py | Điểm chạy của thành viên Binary Search |
| algorithm.py: binary_threshold | Học T bằng chia đôi miền ngưỡng |
| ../speech_silence/data.py | Đọc WAV/LAB, gán nhãn tại tâm khung |
| ../speech_silence/config.py | Cấu hình chung FRAME_MS=25, HOP_MS=10 |
| ../speech_silence/features.py | STE/MA, chuẩn hóa, F0, hậu xử lý và biên |
| ../speech_silence/pipeline.py | Kiểm chứng ở khung cố định, học ngưỡng và dự đoán test |
| ../speech_silence/evaluation.py | Ghép biên, MAE/RMSE và BER |
| ../speech_silence/demo.py | Bốn figure và bình luận Markdown |

Chạy từ thư mục gốc dự án:

~~~bash
python3 TT1_BinarySearch/main.py
~~~

Không có menu và không chạy Histogram/Gaussian. Mặc định demo nhanh, xử lý đủ bốn WAV test, mở bốn figure ở bốn góc trên backend Qt/Tk hỗ trợ. Mỗi figure có waveform, normalized STE/ngưỡng/biên, logSTE/logMA và F0. Biên dự đoán màu xanh; biên chuẩn màu đỏ nét đứt. Mọi plot đều có title và axis label.

Kết quả lưu tại TT1_BinarySearch/ket_qua. Các file minh chứng:

- [Tham số đã học](ket_qua/tham_so_huan_luyen.json).
- [Kết quả bốn WAV test](ket_qua/ket_qua.csv).
- [Danh sách biên dự đoán](ket_qua/bien_du_doan.csv).
- [Bình luận từng figure](ket_qua/binh_luan_tung_hinh.md).
- [Khảo sát nhiễu của nhóm](../ket_qua/demo/all/khao_sat_nhieu.csv).

Chỉ lưu hình: thêm --no-show. Khảo sát nhiễu cho riêng Binary: thêm --noise. Mỗi lần chạy vẫn chỉ hiển thị bốn figure.

## 17. Kết luận

Binary Search học ngưỡng bằng cân bằng độ lệch năng lượng của hai lớp đã gán nhãn trên training. Với khung cố định 25 ms và bước dịch 10 ms, ngưỡng chung là 0.0013012666. Trên toàn bộ bốn WAV kiểm thử, chương trình đạt MAE 20.0 ms, RMSE 33.5 ms, ghép được tám biên, có ba biên thừa và không thiếu biên.

Kết quả tốt trên các bản ghi hiện có, nhưng còn nhạy với nhiễu nền và Speech năng lượng thấp. Trường hợp phone_F2 minh họa Speech giả ở đầu và cuối bản ghi do nhiễu vượt ngưỡng cùng hậu xử lý Silence ngắn. Vì vậy khi trình bày cần nêu cả chỉ số sai lệch lẫn số biên thừa/thiếu và giới hạn dữ liệu.
