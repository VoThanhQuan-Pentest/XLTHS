from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import warnings

import numpy as np
from scipy.io import wavfile


@dataclass(frozen=True)
class Interval:
    start: float
    end: float
    speech: bool


@dataclass(frozen=True)
class Record:
    name: str
    fs: int
    samples: np.ndarray
    labels: tuple[Interval, ...]

    @property
    def duration(self) -> float:
        return len(self.samples) / self.fs


def discover(root: Path, split: str) -> list[Path]:
    folders = [p for p in root.rglob(split) if p.is_dir()]
    if len(folders) != 1:
        raise ValueError(f"Cần đúng một thư mục {split}, tìm thấy {len(folders)}")
    folder = folders[0]
    wavs = sorted(folder.glob("*.wav"))
    labs = {p.stem for p in folder.glob("*.lab")}
    if not wavs or {p.stem for p in wavs} != labs:
        raise ValueError(f"WAV/LAB không khớp trong {folder}")
    return wavs


def read_labels(path: Path, duration: float) -> tuple[Interval, ...]:
    rows: list[Interval] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.split()
        if not fields or fields[0] in {"F0mean", "F0std"}:
            continue
        if len(fields) != 3 or fields[2] not in {"sil", "v", "uv"}:
            raise ValueError(f"Nhãn không hợp lệ: {path}:{number}")
        try:
            start, end = float(fields[0]), float(fields[1])
        except ValueError as exc:
            raise ValueError(f"Thời gian không hợp lệ: {path}:{number}") from exc
        if start < 0 or end <= start or (rows and abs(start - rows[-1].end) > 1e-6):
            raise ValueError(f"Khoảng nhãn hở/chồng lấn: {path}:{number}")
        rows.append(Interval(start, end, fields[2] != "sil"))
    if not rows or abs(rows[0].start) > 1e-6 or rows[-1].end > duration + 0.011:
        raise ValueError(f"Phạm vi LAB không khớp WAV: {path}")
    return tuple(rows)


def read_record(path: Path) -> Record:
    # scipy cảnh báo về metadata WAV không liên quan đến mẫu âm thanh.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", wavfile.WavFileWarning)
        fs, raw = wavfile.read(path)
    if raw.ndim != 1 or raw.dtype != np.int16:
        raise ValueError(f"Chỉ hỗ trợ WAV mono PCM 16-bit: {path}")
    samples = raw.astype(np.float64) / 32768.0
    return Record(path.stem, fs, samples, read_labels(path.with_suffix(".lab"), len(samples) / fs))


def speech_at(times: np.ndarray, labels: tuple[Interval, ...]) -> tuple[np.ndarray, np.ndarray]:
    speech = np.zeros(len(times), dtype=bool)
    valid = np.zeros(len(times), dtype=bool)
    for row in labels:
        mask = (times >= row.start) & (times < row.end)
        valid |= mask
        speech[mask] = row.speech
    return speech, valid


def reference_boundaries(labels: tuple[Interval, ...]) -> list[tuple[float, bool]]:
    return [(row.start, row.speech) for prev, row in zip(labels, labels[1:]) if row.speech != prev.speech]

