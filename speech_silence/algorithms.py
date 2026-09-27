from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.stats import norm


@dataclass(frozen=True)
class HistogramConfig:
    bins: int = 64
    smooth: int = 3
    weight: int = 5


def binary_threshold(silence: np.ndarray, speech: np.ndarray) -> float:
    if not len(silence) or not len(speech):
        raise ValueError("Thiếu khung huấn luyện cho một lớp")
    smax, pmin = float(np.max(silence)), float(np.min(speech))
    if smax < pmin:
        return (smax + pmin) / 2
    lo, hi = pmin, smax
    if lo >= hi:
        return float(np.clip((np.mean(silence) + np.mean(speech)) / 2, 0, 1))
    # Diện tích nhầm lẫn hai phía; hàm hiệu đơn điệu nên có thể chia đôi.
    for _ in range(100):
        mid = (lo + hi) / 2
        delta = np.maximum(silence - mid, 0).mean() - np.maximum(mid - speech, 0).mean()
        if delta > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-8:
            break
    return float(np.clip((lo + hi) / 2, 0, 1))


def histogram_threshold(values: np.ndarray, config: HistogramConfig, fallback: float | None = None) -> tuple[float, bool]:
    hist, edges = np.histogram(values, bins=config.bins, range=(0, 1))
    smooth = uniform_filter1d(hist.astype(float), size=config.smooth, mode="nearest")
    peaks = [i for i in range(1, len(smooth) - 1)
             if smooth[i] >= smooth[i - 1] and smooth[i] > smooth[i + 1]]
    # Cần hai đỉnh tách biệt ít nhất hai bin để tránh nhiễu lượng tử hóa.
    pairs = [(a, b) for a in peaks for b in peaks if b >= a + 2]
    if not pairs:
        if fallback is None:
            raise ValueError("Histogram không có hai đỉnh; cần ngưỡng dự phòng")
        return float(fallback), True
    a, b = max(pairs, key=lambda pair: (min(smooth[pair[0]], smooth[pair[1]]),
                                      smooth[pair[0]] + smooth[pair[1]], pair[1] - pair[0]))
    centers = (edges[:-1] + edges[1:]) / 2
    return float((config.weight * centers[a] + centers[b]) / (config.weight + 1)), False


def gaussian_threshold(silence: np.ndarray, speech: np.ndarray) -> tuple[float, dict[str, float]]:
    if not len(silence) or not len(speech):
        raise ValueError("Thiếu khung huấn luyện cho một lớp")
    ms, mp = float(np.mean(silence)), float(np.mean(speech))
    ss, sp = float(np.std(silence)), float(np.std(speech))
    sd_s, sd_p = max(ss, 1e-6), max(sp, 1e-6)
    # Giao hai mật độ Gaussian giải bằng phương trình bậc hai.
    a = 1 / sd_p**2 - 1 / sd_s**2
    b = -2 * mp / sd_p**2 + 2 * ms / sd_s**2
    c = mp**2 / sd_p**2 - ms**2 / sd_s**2 - 2 * np.log(sd_s / sd_p)
    candidates = [0.0, 1.0]
    roots = np.roots([a, b, c]) if abs(a) > 1e-12 else ([-c / b] if abs(b) > 1e-12 else [])
    candidates.extend(float(np.real(x)) for x in roots if abs(np.imag(x)) < 1e-9 and 0 <= np.real(x) <= 1)
    def error(threshold: float) -> float:
        return (1 - norm.cdf(threshold, ms, sd_s) + norm.cdf(threshold, mp, sd_p)) / 2
    threshold = min(candidates, key=error)
    return float(threshold), {"meanSil": ms, "stdSil": ss, "meanSp": mp, "stdSp": sp,
                              "nSil": len(silence), "nSp": len(speech)}


def as_model(config: HistogramConfig) -> dict:
    return asdict(config)
