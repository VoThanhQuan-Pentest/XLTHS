# Sửa quy tắc chọn đỉnh Histogram

## Thay đổi

- Xét đỉnh ở bin 0 và bin cuối; mỗi plateau dương chỉ tạo một đỉnh.
- Chọn đỉnh nền trong vùng chứa 20% giá trị normalized STE thấp nhất của WAV, thay vì chọn hai đỉnh cao tùy ý.
- Yêu cầu valley đủ sâu giữa hai đỉnh và khoảng cách đỉnh đủ lớn. Cửa sổ làm trơn phải lẻ để giữ đúng số bin.
- Chọn lại toàn bộ cấu hình bằng kiểm chứng chéo trên bốn WAV training. Không dùng LAB test để học ngưỡng hoặc chọn cấu hình.
- Hàm tính ngưỡng vẫn chỉ nhận normalized STE, cấu hình và fallback. LAB test chỉ dùng sau dự đoán để đánh giá.

## Cấu hình mới

Khung 20 ms, bước dịch 10 ms, 128 bin, cửa sổ trơn 1, trọng số 10, khoảng cách đỉnh tối thiểu 6 bin, độ sâu valley tối thiểu 0,2. Fallback học từ training là 0,009588. Cửa sổ trơn 1 nghĩa là training chọn không làm trơn; các kiểm tra vị trí/valley/khoảng cách vẫn áp dụng.

Khoảng cách được khảo sát tại 3/6/12 bin, độ sâu valley tại 0,2/0,4; số bin, khung, mức trơn và trọng số được khảo sát như trước. Cấu hình khóa trước khi đo kết quả test.

## Kết quả thực nghiệm

Baseline là bản trước sửa ở commit fadcdbe. So sánh này bao gồm cả sửa thuật toán và chọn lại cấu hình training, không chỉ riêng thay đổi bin 0.

| WAV test | MAE trước sửa | MAE sau sửa | Biên thừa trước/sau |
|---|---:|---:|---:|
| phone_F2 | 55 ms | 35 ms | 4 / 2 |
| phone_M2 | 15 ms | 10 ms | 0 / 0 |
| studio_F2 | 35 ms | 20 ms | 0 / 0 |
| studio_M2 | 95 ms | 25 ms | 0 / 0 |
| Tổng hợp | 50,0 ms | 22,5 ms | 4 / 2 |

RMSE gộp giảm từ 67,5 xuống 25,5 ms. Cả trước và sau đều ghép được 8 biên, không thiếu biên. MAE giảm 55% trên bộ test nhỏ này; không suy rộng thành tỷ lệ cải thiện cho mọi môi trường thu âm.

Sau sửa, bốn WAV đều chọn bin 0 làm đỉnh nền. Các bin đỉnh cao lần lượt là 13, 22, 9 và 32. Đối chiếu LAB sau suy luận cho thấy bin đỉnh cao chứa Speech; bin 0 chứa phần lớn Silence nhưng vẫn có Speech năng lượng thấp. Vì vậy đây là các đỉnh đại diện, không phải hai lớp tách hoàn toàn.

phone_F2 còn hai biên thừa trong Speech. Bình luận vị trí cụ thể, ngưỡng và sai số nằm trong ket_qua/demo/histogram/binh_luan_tung_hinh.md. Không tuyên bố Histogram sau sửa tốt hơn Gaussian: Gaussian hiện có MAE 12,5 ms trên cùng bốn WAV.

## Kiểm chứng

Năm kiểm thử dùng unittest và NumPy kiểm tra bin 0, plateau/bin cuối, valley nông, khoảng cách đỉnh và tín hiệu một đỉnh. Lệnh chạy: `python3 -m unittest discover -s tests -v`.

Các file kết quả Histogram hiện tại đã được tạo lại từ đầu bằng `python3 main.py --algorithm histogram --no-show`. Các thuật toán tính ngưỡng Binary Search và Gaussian giữ nguyên.
