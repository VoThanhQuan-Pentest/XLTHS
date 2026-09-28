from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Features:
    times: np.ndarray
    ste: np.ndarray
    ma: np.ndarray
    normalized_ste: np.ndarray
    log_ste: np.ndarray
    log_ma: np.ndarray
    f0: np.ndarray
    edges: np.ndarray


def extract(samples: np.ndarray, fs: int, frame_ms: int, hop_ms: int = 10,
            compute_f0: bool = True) -> Features:
    frame = max(1, round(fs * frame_ms / 1000))
    hop = max(1, round(fs * hop_ms / 1000))
    if len(samples) == 0:
        raise ValueError("WAV rỗng")
    starts = np.arange(0, len(samples), hop)
    padded = np.pad(samples, (0, frame))
    frames = np.lib.stride_tricks.sliding_window_view(padded, frame)[starts]
    # Khung cuối được đệm zero; mẫu thiếu không làm thay đổi mẫu số.
    ste = np.mean(frames * frames, axis=1)
    ma = np.mean(np.abs(frames), axis=1)
    maximum = float(np.max(ste))
    normalized = ste / maximum if maximum > 0 else np.zeros_like(ste)
    f0 = estimate_f0(frames, fs, normalized) if compute_f0 else np.full(len(frames), np.nan)
    edges = np.r_[starts / fs, len(samples) / fs]
    times = (starts + np.minimum(frame, len(samples) - starts) / 2) / fs
    return Features(times, ste, ma, normalized, 10 * np.log10(np.maximum(ste, 1e-12)),
                    20 * np.log10(np.maximum(ma, 1e-12)), f0, edges)


def estimate_f0(frames: np.ndarray, fs: int, normalized_ste: np.ndarray,
                minimum_hz: float = 60.0, maximum_hz: float = 400.0) -> np.ndarray:
    """Ước lượng F0 bằng tự tương quan; khung vô thanh/khoảng lặng nhận NaN."""
    minimum_lag = max(1, int(fs / maximum_hz))
    maximum_lag = min(frames.shape[1] - 1, int(fs / minimum_hz))
    result = np.full(len(frames), np.nan)
    window = np.hamming(frames.shape[1])
    for index, frame in enumerate(frames):
        if normalized_ste[index] < 0.01:
            continue
        centered = (frame - np.mean(frame)) * window
        fft_size = 1 << (2 * len(centered) - 1).bit_length()
        spectrum = np.fft.rfft(centered, n=fft_size)
        correlation = np.fft.irfft(spectrum * np.conj(spectrum), n=fft_size)[:len(centered)]
        if correlation[0] <= 1e-12:
            continue
        search = correlation[minimum_lag:maximum_lag + 1]
        lag = minimum_lag + int(np.argmax(search))
        # Tương quan yếu thường là âm vô thanh hoặc nhiễu, không phải F0.
        if correlation[lag] / correlation[0] >= 0.30:
            result[index] = fs / lag
    return result


def remove_virtual_silence(mask: np.ndarray, edges: np.ndarray, minimum_s: float = 0.2) -> np.ndarray:
    result = mask.copy()
    silence = ~result
    changes = np.flatnonzero(np.diff(np.r_[False, silence, False]))
    for start, end in changes.reshape(-1, 2):
        if edges[end] - edges[start] < minimum_s - 1e-12:
            result[start:end] = True
    return result


def segments(mask: np.ndarray, edges: np.ndarray) -> list[tuple[float, float, bool]]:
    changes = np.r_[0, np.flatnonzero(np.diff(mask)) + 1, len(mask)]
    return [(float(edges[a]), float(edges[b]), bool(mask[a])) for a, b in zip(changes, changes[1:])]


def predicted_boundaries(mask: np.ndarray, edges: np.ndarray) -> list[tuple[float, bool]]:
    changes = np.flatnonzero(np.diff(mask)) + 1
    return [(float(edges[i]), bool(mask[i])) for i in changes]
