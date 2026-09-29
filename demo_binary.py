"""Khởi chạy demo nhanh phương pháp Tìm kiếm nhị phân (Binary Search) trên 4 tệp kiểm thử."""

from pathlib import Path
from speech_silence.pipeline import run


def main() -> None:
    """Chạy phân đoạn bằng Binary Search và hiển thị 4 Figure tại 4 góc màn hình."""
    root = Path(__file__).resolve().parent
    output = root / "ket_qua" / "demo_binary"
    run(root=root, output=output, only="binary", noise=False, show_gui=True)


if __name__ == "__main__":
    main()
