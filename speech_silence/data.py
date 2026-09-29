"""Quản lý, đọc và chuẩn hóa dữ liệu tín hiệu âm thanh WAV và nhãn kiểm thử LAB.

Module đảm nhiệm:
- discover: Tự động quét và tìm các thư mục chứa cặp tệp WAV và LAB.
- read_labels: Đọc nhãn phân đoạn từ tệp LAB chuẩn (ground truth).
- read_record: Đọc tệp âm thanh WAV (sử dụng thư viện wave chuẩn của Python) và nạp nhãn kèm thống kê F0.
- speech_at, reference_boundaries: Đồng bộ nhãn thời gian thực với các khung mẫu để phục vụ đánh giá.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import wave

import numpy as np


@dataclass(frozen=True)
class Interval:
    """Khoảng thời gian được gán nhãn trong tệp LAB.

    Attributes:
        start: Thời điểm bắt đầu của phân đoạn (giây).
        end: Thời điểm kết thúc của phân đoạn (giây).
        speech: True nếu là tiếng nói (v hoặc uv), False nếu là khoảng lặng (sil).
    """
    start: float
    end: float
    speech: bool


@dataclass(frozen=True)
class Record:
    """Bản ghi dữ liệu hoàn chỉnh của một mẫu âm thanh.

    Attributes:
        name: Tên của mẫu âm thanh (ví dụ: 'phone_F2', 'studio_M1').
        fs: Tần số lấy mẫu của tệp WAV (Hz).
        samples: Mảng 1D float chứa các mẫu âm thanh đã chuẩn hóa về [-1, 1].
        labels: Tuple các phân đoạn nhãn chuẩn từ tệp LAB.
        reference_f0_mean: Giá trị F0mean chuẩn đọc từ tệp LAB (nếu có).
        reference_f0_std: Giá trị F0std chuẩn đọc từ tệp LAB (nếu có).
    """
    name: str
    fs: int
    samples: np.ndarray
    labels: tuple[Interval, ...]
    reference_f0_mean: float | None = None
    reference_f0_std: float | None = None

    @property
    def duration(self) -> float:
        """Tổng thời lượng của tệp âm thanh tính bằng giây."""
        return len(self.samples) / self.fs


def discover(root: Path, split: str) -> list[Path]:
    """Tìm kiếm đệ quy thư mục chứa tập dữ liệu WAV và LAB theo tên split.

    Args:
        root: Thư mục gốc để bắt đầu tìm kiếm.
        split: Tên thư mục con cần tìm (ví dụ: 'TinHieuHuanLuyen' hoặc 'TinHieuKiemThu').

    Returns:
        Danh sách đường dẫn (Path) đến các tệp .wav được sắp xếp theo thứ tự bảng chữ cái.
    """
    # Khối 1: Tìm kiếm thư mục tương ứng trong cấu trúc cây thư mục
    folders = [p for p in root.rglob(split) if p.is_dir()]
    if len(folders) != 1:
        raise ValueError(f"Cần tìm đúng một thư mục {split}, phát hiện {len(folders)}")

    # Khối 2: Lấy danh sách các tệp WAV và kiểm tra tính toàn vẹn với tệp LAB
    target_folder = folders[0]
    wav_files = sorted(target_folder.glob("*.wav"))
    lab_names = {p.stem for p in target_folder.glob("*.lab")}

    # Khối 3: Đảm bảo mọi tệp WAV đều có tệp LAB đi kèm tương ứng
    if not wav_files or {p.stem for p in wav_files} != lab_names:
        raise ValueError(f"Các cặp WAV và LAB không khớp nhau trong {target_folder}")

    return wav_files


def read_labels(path: Path, duration: float) -> tuple[Interval, ...]:
    """Đọc và kiểm tra tính hợp lệ của tệp nhãn phân đoạn .lab.

    Tệp LAB chứa các dòng: <thời_điểm_bắt_đầu> <thời_điểm_kết_thúc> <nhãn>
    Trong đó: nhãn 'sil' là khoảng lặng, 'v' (voiced) và 'uv' (unvoiced) đều là tiếng nói.

    Args:
        path: Đường dẫn đến tệp .lab cần đọc.
        duration: Tổng thời lượng tín hiệu WAV tương ứng (giây) để kiểm tra biên ngoài.

    Returns:
        Tuple các đối tượng Interval đã được kiểm tra tính liên tục và hợp lệ.
    """
    # Khối 1: Đọc nội dung văn bản và lọc các dòng dữ liệu hợp lệ
    intervals: list[Interval] = []
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_num, line in enumerate(lines, 1):
        fields = line.split()
        # Bỏ qua các dòng trống hoặc dòng chứa thông tin thống kê F0
        if not fields or fields[0] in {"F0mean", "F0std"}:
            continue

        if len(fields) != 3 or fields[2] not in {"sil", "v", "uv"}:
            raise ValueError(f"Cấu trúc nhãn không hợp lệ tại {path}:{line_num}")

        # Khối 2: Chuyển đổi và kiểm tra khoảng thời gian bắt đầu và kết thúc
        try:
            start_time, end_time = float(fields[0]), float(fields[1])
        except ValueError as exc:
            raise ValueError(f"Giá trị thời gian sai định dạng tại {path}:{line_num}") from exc

        if start_time < 0 or end_time <= start_time or (intervals and abs(start_time - intervals[-1].end) > 1e-6):
            raise ValueError(f"Khoảng nhãn bị ngắt quãng hoặc chồng lấn tại {path}:{line_num}")

        # Gộp 'v' và 'uv' thành Speech (True), 'sil' thành Silence (False)
        intervals.append(Interval(start_time, end_time, fields[2] != "sil"))

    # Khối 3: Kiểm tra biên bao phủ của tệp LAB so với thời lượng file WAV
    if not intervals or abs(intervals[0].start) > 1e-6 or intervals[-1].end > duration + 0.011:
        raise ValueError(f"Phạm vi thời gian của LAB không khớp với thời lượng WAV: {path}")

    return tuple(intervals)


def read_record(path: Path) -> Record:
    """Đọc tệp âm thanh WAV và nạp đầy đủ nhãn kiểm thử cùng thông số F0.

    Sử dụng mô-đun chuẩn wave của Python để đọc mẫu âm thanh 16-bit PCM mono,
    chuyển đổi sang float trong dải [-1.0, 1.0].

    Args:
        path: Đường dẫn đến tệp âm thanh .wav.

    Returns:
        Đối tượng Record chứa dữ liệu sóng âm, nhãn chuẩn và tham số F0.
    """
    # Khối 1: Đọc tệp WAV bằng mô-đun wave chuẩn (Standard Library)
    with wave.open(str(path), "rb") as wave_file:
        fs = wave_file.getframerate()
        n_channels = wave_file.getnchannels()
        samp_width = wave_file.getsampwidth()
        n_frames = wave_file.getnframes()
        raw_bytes = wave_file.readframes(n_frames)

    # Khối 2: Kiểm tra định dạng PCM 16-bit và đơn kênh (mono)
    if samp_width != 2:
        raise ValueError(f"Chỉ hỗ trợ âm thanh định dạng PCM 16-bit: {path}")

    raw_samples = np.frombuffer(raw_bytes, dtype=np.int16)
    if n_channels == 2:
        # Nếu là stereo, lấy kênh thứ nhất để thành mono
        raw_samples = raw_samples[::2]
    elif n_channels > 2:
        raise ValueError(f"Không hỗ trợ tệp âm thanh nhiều hơn 2 kênh: {path}")

    # Chuẩn hóa giá trị mẫu về dải [-1.0, 1.0]
    samples = raw_samples.astype(np.float64) / 32768.0

    # Khối 3: Nạp tệp nhãn .lab và trích xuất F0mean, F0std nếu có
    lab_path = path.with_suffix(".lab")
    f0_stats: dict[str, float] = {}
    if lab_path.exists():
        for line in lab_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] in {"F0mean", "F0std"}:
                f0_stats[parts[0]] = float(parts[1])

    labels = read_labels(lab_path, len(samples) / fs)

    return Record(
        name=path.stem,
        fs=fs,
        samples=samples,
        labels=labels,
        reference_f0_mean=f0_stats.get("F0mean"),
        reference_f0_std=f0_stats.get("F0std")
    )


def speech_at(times: np.ndarray, labels: tuple[Interval, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Xác định nhãn tiếng nói (Speech) tại từng mốc thời gian của khung mẫu.

    Args:
        times: Mảng 1D float chứa các mốc thời gian trung tâm của các khung.
        labels: Tuple các phân đoạn nhãn chuẩn từ tệp LAB.

    Returns:
        tuple gồm:
            - is_speech: Mảng boolean (True: Speech, False: Silence).
            - is_valid: Mảng boolean cho biết khung có nằm trong phạm vi gán nhãn hay không.
    """
    # Khối 1: Khởi tạo mảng kết quả boolean
    is_speech = np.zeros(len(times), dtype=bool)
    is_valid = np.zeros(len(times), dtype=bool)

    # Khối 2: Chiếu từng khoảng nhãn lên mảng mốc thời gian
    for segment in labels:
        in_segment = (times >= segment.start) & (times < segment.end)
        is_valid |= in_segment
        is_speech[in_segment] = segment.speech

    return is_speech, is_valid


def reference_boundaries(labels: tuple[Interval, ...]) -> list[tuple[float, bool]]:
    """Trích xuất các mốc biên thời gian chuyển đổi chuẩn (Ground Truth) từ các khoảng nhãn.

    Args:
        labels: Tuple các phân đoạn nhãn chuẩn.

    Returns:
        Danh sách các bộ (thời_điểm_biên_s, chuyển_sang_speech_bool).
    """
    # Khối 1: So sánh từng cặp khoảng nhãn liên tiếp để xác định điểm thay đổi phân lớp
    ground_truth_boundaries = [
        (current.start, current.speech)
        for prev, current in zip(labels, labels[1:])
        if current.speech != prev.speech
    ]
    return ground_truth_boundaries
