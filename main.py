"""Điểm khởi chạy chính thức của chương trình phân đoạn tiếng nói và khoảng lặng (Speech/Silence).

Cách thức demo trước Giảng viên:
- SV hoặc GV bấm nút 'Run' chạy chương trình (hoặc gõ: python3 main.py) đúng 01 lần duy nhất.
- Chương trình tự động đọc toàn bộ 4 tệp tín hiệu trong thư mục 'TinHieuKiemThu'.
- Xuất ra kết quả trên 4 Figure riêng biệt (mỗi Figure cho 1 tệp tín hiệu).
- Mỗi Figure chứa đầy đủ kết quả trung gian (STE, logSTE/logMA) và kết quả cuối cùng
  (biên chuẩn Ground Truth màu đỏ, biên dự đoán màu xanh, và đường F0 màu cam).
- Chương trình tự động sắp xếp 4 cửa sổ Figure vào đúng 4 góc của màn hình
  (Top-Left, Top-Right, Bottom-Left, Bottom-Right) để GV quan sát thuận tiện.
- Mỗi plot con (subplot) đều có tiêu đề (title) và nhãn trục (axis label) phân biệt rõ ràng.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from speech_silence.pipeline import METHODS, run


def parse_args() -> argparse.Namespace:
    """Xử lý và phân tích các tham số dòng lệnh đầu vào khi khởi chạy chương trình.

    Returns:
        argparse.Namespace: Đối tượng chứa các tham số cấu hình:
            - root: Đường dẫn thư mục gốc dự án.
            - output: Thư mục lưu trữ kết quả đầu ra.
            - algorithm: Thuật toán lựa chọn ('all', 'binary', 'histogram', 'statistical').
            - no_noise: Cờ boolean bỏ qua khảo sát nhiễu để tăng tốc demo.
            - no_show: Cờ boolean tắt hiển thị cửa sổ GUI (chỉ lưu ảnh ra đĩa).
    """
    # Khối 1: Khởi tạo bộ phân tích tham số dòng lệnh
    parser = argparse.ArgumentParser(
        description="Huấn luyện và đánh giá phân đoạn Speech/Silence trên toàn bộ tập kiểm thử"
    )

    # Khối 2: Thiết lập các đối số đường dẫn thư mục dữ liệu
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent,
        help="Thư mục dự án chứa TinHieuHuanLuyen và TinHieuKiemThu (mặc định: thư mục hiện tại)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parent / "ket_qua",
        help="Thư mục lưu kết quả đồ thị và bảng số liệu CSV (mặc định: ./ket_qua)"
    )

    # Khối 3: Thiết lập các tùy chọn thuật toán và chế độ demo
    parser.add_argument(
        "--algorithm", choices=("all",) + METHODS, default="all",
        help="Lựa chọn thuật toán: 'all' (cả 3 phương pháp), 'binary', 'histogram', 'statistical'"
    )
    parser.add_argument(
        "--no-noise", action="store_true",
        help="Bỏ qua phần khảo sát cộng nhiễu trắng để tối ưu thời gian demo nhanh"
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="Chỉ xuất hình ảnh và bảng số liệu ra đĩa, không bật 4 cửa sổ GUI trên màn hình"
    )

    return parser.parse_args()


def main() -> None:
    """Hàm điều khiển chính: Nạp tham số, in thông báo và khởi chạy quy trình phân đoạn."""
    # Khối 1: Phân tích các tùy chọn dòng lệnh
    args = parse_args()
    selected_method = None if args.algorithm == "all" else args.algorithm

    # Khối 2: In biểu ngữ thông tin chương trình
    print("=" * 70)
    print(" BÀI TẬP LỚN: PHÂN ĐOẠN TÍN HIỆU THÀNH TIẾNG NÓI VÀ KHOẢNG LẶNG (SPEECH/SILENCE)")
    print(" 3 Phương pháp: Tìm kiếm nhị phân, Histogram, Thống kê Gaussian")
    print(" Huấn luyện: TinHieuHuanLuyen | Kiểm thử: TinHieuKiemThu (4 tệp)")
    print("=" * 70)

    # Khối 3: Thực thi quy trình phân đoạn, xuất hình và sắp xếp 4 Figure lên 4 góc màn hình
    run(
        root=args.root,
        output=args.output,
        only=selected_method,
        noise=not args.no_noise,
        show_gui=not args.no_show
    )


if __name__ == "__main__":
    main()
