"""Khởi chạy demo nhanh phương pháp Thống kê Gaussian trên 4 tệp kiểm thử."""

from pathlib import Path
from speech_silence.pipeline import run


def main() -> None:
    """Chạy phân đoạn bằng Thống kê Gaussian và hiển thị 4 Figure tại 4 góc màn hình."""
    root = Path(__file__).resolve().parent
    output = root / "ket_qua" / "demo_statistical"
    run(root=root, output=output, only="statistical", noise=False, show_gui=True)


if __name__ == "__main__":
    main()
