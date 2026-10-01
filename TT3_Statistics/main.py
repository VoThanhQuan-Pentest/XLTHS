"""Bấm Run file này để demo riêng Statistical Gaussian trên đủ bốn WAV test."""

from pathlib import Path
import sys

# Khối 1: Xác định thư mục thực của file để chạy được từ IDE hoặc thư mục bất kỳ.
STUDENT_DIRECTORY = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDENT_DIRECTORY.parent))
from speech_silence.student_demo import run_student


def main() -> None:
    """Không nhận tham số hàm; chạy Statistical Gaussian và xuất bốn figure, trả None."""
    run_student("statistical", STUDENT_DIRECTORY)


if __name__ == "__main__":
    main()
