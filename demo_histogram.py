from pathlib import Path
from speech_silence.pipeline import run
run(Path(__file__).resolve().parent, Path(__file__).resolve().parent / "ket_qua" / "demo_histogram", "histogram", False)
