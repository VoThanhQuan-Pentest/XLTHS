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
    edges: np.ndarray


def extract(samples: np.ndarray, fs: int, frame_ms: int, hop_ms: int = 10) -> Features:
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
    edges = np.r_[starts / fs, len(samples) / fs]
    times = (starts + np.minimum(frame, len(samples) - starts) / 2) / fs
    return Features(times, ste, ma, normalized, 10 * np.log10(np.maximum(ste, 1e-12)),
                    20 * np.log10(np.maximum(ma, 1e-12)), edges)


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
