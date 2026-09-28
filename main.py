"""Điểm khởi chạy chính dùng khi demo trước giảng viên."""

from __future__ import annotations

import argparse
from pathlib import Path

from speech_silence.pipeline import METHODS, run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Huấn luyện và đánh giá phân đoạn Speech/Silence trên toàn bộ tập kiểm thử")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent,
                        help="Thư mục dự án chứa TinHieuHuanLuyen và TinHieuKiemThu")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "ket_qua",
                        help="Thư mục lưu hình, CSV và nhận xét")
    parser.add_argument("--algorithm", choices=("all",) + METHODS, default="all",
                        help="Chạy cả ba phương pháp hoặc chọn một phương pháp")
    parser.add_argument("--no-noise", action="store_true",
                        help="Bỏ khảo sát cộng nhiễu để demo nhanh")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = None if args.algorithm == "all" else args.algorithm
    print("PHÂN ĐOẠN SPEECH/SILENCE")
    print("Huấn luyện chỉ dùng TinHieuHuanLuyen; đánh giá chỉ dùng TinHieuKiemThu.")
    run(args.root, args.output, only=selected, noise=not args.no_noise)


if __name__ == "__main__":
    main()
