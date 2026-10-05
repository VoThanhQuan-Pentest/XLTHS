"""Điểm khởi chạy chính thức của chương trình phân đoạn tiếng nói và khoảng lặng (Speech/Silence).

Cách thức demo trước Giảng viên:
- SV hoặc GV bấm nút 'Run' chạy chương trình (hoặc gõ: python3 main.py) đúng 01 lần duy nhất.
- Chương trình tự động đọc toàn bộ 4 tệp tín hiệu trong thư mục 'TinHieuKiemThu'.
- Xuất ra kết quả trên 4 Figure riêng biệt (mỗi Figure cho 1 tệp tín hiệu).
- Mỗi Figure chứa đầy đủ kết quả trung gian (STE, logSTE/logMA) và kết quả cuối cùng
  (biên chuẩn Ground Truth màu đỏ, biên dự đoán màu xanh, và đường F0 màu cam).
- Mỗi sinh viên chọn một thuật toán; bốn figure chỉ chứa thuật toán đã chọn.
- Bốn PNG và bình luận lưu riêng theo thuật toán trong 'ket_qua/demo/'.
- Chương trình tự động sắp xếp 4 cửa sổ Figure vào đúng 4 góc của màn hình
  (Top-Left, Top-Right, Bottom-Left, Bottom-Right) để GV quan sát thuận tiện.
- Mỗi plot con (subplot) đều có tiêu đề (title) và nhãn trục (axis label) phân biệt rõ ràng.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

# Qt trên Wayland không cho chương trình tự đặt vị trí cửa sổ.
# Khi có DISPLAY, ưu tiên X11/XWayland trong tiến trình demo để xếp bốn góc.
# Giữ cấu hình QT_QPA_PLATFORM nếu người dùng đã đặt rõ từ bên ngoài.
if os.name == "posix" and os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from speech_silence.pipeline import METHODS, METHOD_LABELS, run
from speech_silence.config import FRAME_MS, HOP_MS


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
        "--output", type=Path, default=None,
        help="Thư mục đầu ra (mặc định: ket_qua/demo/<thuật toán>)"
    )

    # Khối 3: Thiết lập các tùy chọn thuật toán và chế độ demo
    parser.add_argument(
        "--algorithm", choices=("all",) + METHODS, default=None,
        help="Chọn thuật toán của sinh viên; bỏ trống để chọn 1/2/3 khi Run. 'all' chỉ dùng so sánh nhóm."
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


def select_algorithm(argument: str | None) -> str:
    """Nhận tên thuật toán từ CLI hoặc None; trả lựa chọn để chạy riêng phần của sinh viên."""
    # Khối 1: Khi chạy lệnh có --algorithm, không yêu cầu nhập thêm trong demo.
    if argument is not None:
        return argument
    print("Chọn thuật toán phụ trách:")
    for index, method in enumerate(METHODS, 1):
        print(f"  {index}. {METHOD_LABELS[method]}")

    # Khối 2: Chỉ chấp nhận một lựa chọn; hướng dẫn CLI khi môi trường không có stdin.
    while True:
        try:
            choice = input("Nhập 1, 2 hoặc 3: ").strip()
        except EOFError as error:
            raise SystemExit("Hãy chạy với --algorithm binary, histogram hoặc statistical.") from error
        if choice in {"1", "2", "3"}:
            return METHODS[int(choice) - 1]
        print("Lựa chọn chưa hợp lệ. Vui lòng nhập 1, 2 hoặc 3.")


def main() -> None:
    """Khởi chạy demo từ đối số dòng lệnh, xuất bốn figure; không trả giá trị."""
    # Khối 1: Phân tích các tùy chọn dòng lệnh
    args = parse_args()
    algorithm = select_algorithm(args.algorithm)
    selected_method = None if algorithm == "all" else algorithm
    output = args.output or args.root / "ket_qua" / "demo" / algorithm

    # Khối 2: In biểu ngữ thông tin chương trình
    print("=" * 70)
    print(" BÀI TẬP LỚN: PHÂN ĐOẠN TÍN HIỆU THÀNH TIẾNG NÓI VÀ KHOẢNG LẶNG (SPEECH/SILENCE)")
    print(f" Thuật toán: {METHOD_LABELS.get(algorithm, 'Cả ba (so sánh nhóm)')}")
    print(f" Phân khung cố định: {FRAME_MS} ms; bước dịch: {HOP_MS} ms")
    print(" Huấn luyện: TinHieuHuanLuyen | Kiểm thử: TinHieuKiemThu (4 tệp)")
    print("=" * 70)

    # Khối 3: Thực thi quy trình phân đoạn, xuất hình và sắp xếp 4 Figure lên 4 góc màn hình
    run(
        root=args.root,
        output=output,
        only=selected_method,
        noise=not args.no_noise,
        show_gui=not args.no_show
    )


if __name__ == "__main__":
    main()
