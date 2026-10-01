"""Điểm chạy dùng chung cho ba thư mục sinh viên, không có menu chọn thuật toán."""

import argparse
import os
from pathlib import Path

# Khối 1: Ưu tiên X11/XWayland cho Qt để có thể đặt cửa sổ vào bốn góc.
# Chỉ đặt trong tiến trình này, giữ cấu hình backend do người dùng chọn từ ngoài.
if os.name == "posix" and os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from .pipeline import METHOD_LABELS, run


def run_student(method: str, directory: Path) -> None:
    """Khởi chạy một bài demo theo thuật toán cố định của thành viên.

    Args:
        method: Tên thuật toán cố định bởi main.py của thư mục thành viên.
        directory: Đường dẫn tuyệt đối đến thư mục main.py đang chạy.
    Returns:
        None. Huấn luyện, xuất bốn figure và lưu kết quả vào directory/ket_qua.
    """
    # Khối 1: Kiểm tra thuật toán và khai báo tùy chọn đường dẫn, GUI của demo.
    if method not in METHOD_LABELS:
        raise ValueError(f"Thuật toán không hợp lệ: {method}")
    parser = argparse.ArgumentParser(description=f"Demo riêng: {METHOD_LABELS[method]}")
    parser.add_argument("--root", type=Path, default=directory.parent,
                        help="Thư mục chứa hai tập dữ liệu (mặc định: thư mục gốc dự án)")
    parser.add_argument("--output", type=Path, default=directory / "ket_qua",
                        help="Thư mục kết quả của riêng thành viên này")

    # Khối 2: Mặc định demo nhanh; khảo sát nhiễu có thể bật rõ bằng --noise.
    parser.add_argument("--no-show", action="store_true", help="Chỉ lưu hình, không mở GUI")
    noise_options = parser.add_mutually_exclusive_group()
    noise_options.add_argument("--noise", dest="noise", action="store_true", help="Bật khảo sát nhiễu")
    noise_options.add_argument("--no-noise", dest="noise", action="store_false", help="Demo nhanh (mặc định)")
    parser.set_defaults(noise=False)
    args = parser.parse_args()

    # Khối 3: Chỉ huấn luyện và chạy phương pháp của sinh viên, không hiện menu.
    print(f"DEMO RIÊNG: {METHOD_LABELS[method]}")
    print("Một lần chạy: bốn WAV test, bốn figure, một thuật toán.")
    print(f"Mã thuật toán: {directory / 'algorithm.py'}")
    run(root=args.root.resolve(), output=args.output.resolve(), only=method,
        noise=args.noise, show_gui=not args.no_show)
