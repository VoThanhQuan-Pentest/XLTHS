from pathlib import Path
import argparse
from speech_silence.pipeline import run

parser = argparse.ArgumentParser(description="Huấn luyện và đánh giá ba cách phân đoạn Speech/Silence")
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "ket_qua")
parser.add_argument("--no-noise", action="store_true", help="Bỏ thí nghiệm thêm nhiễu")
args = parser.parse_args()
run(args.root, args.output, noise=not args.no_noise)
