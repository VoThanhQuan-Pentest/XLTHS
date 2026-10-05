"""Thuật toán của thành viên 2: Histogram STE, hai cực đại đầu theo mô tả BT1."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class HistogramConfig:
    """Tham số Histogram: bins là số ô, smooth là bậc trơn lẻ, weight là trọng số đỉnh đầu."""
    bins: int = 128
    smooth: int = 3
    weight: int = 30


def smooth_1d(x: np.ndarray, size: int) -> np.ndarray:
    """Nhận histogram và bậc lẻ dương; trả trung bình trượt, lặp giá trị mép, không gọi convolve."""
    # Khối 1: Bậc 1 giữ nguyên histogram; bậc chẵn không tạo cửa sổ đối xứng.
    if size < 1 or size % 2 == 0 or not len(x):
        raise ValueError("Làm trơn cần bậc lẻ dương và histogram không rỗng")
    if size == 1:
        return x.astype(float)
    padded = np.pad(x.astype(float), size // 2, mode="edge")

    # Khối 2: Tự duyệt các cửa sổ, chỉ dùng mean để tính trung bình.
    smoothed = np.empty(len(x), dtype=float)
    for index in range(len(x)):
        smoothed[index] = np.mean(padded[index:index + size])
    return smoothed


def histogram_local_maxima(histogram: np.ndarray) -> list[int]:
    """Nhận histogram đã trơn; trả các đỉnh tăng dần, gồm bin 0/cuối và plateau dương."""
    # Khối 1: Gom các phần tử bằng nhau thành một plateau, tránh đếm đỉnh lặp.
    peaks, start = [], 0
    while start < len(histogram):
        end = start
        while end + 1 < len(histogram) and histogram[end + 1] == histogram[start]:
            end += 1

        # Khối 2: So sánh hai phía; plateau ở biên 0 đại diện bằng chính bin 0.
        left = histogram[start - 1] if start > 0 else -np.inf
        right = histogram[end + 1] if end + 1 < len(histogram) else -np.inf
        if histogram[start] > 0 and histogram[start] > left and histogram[start] > right:
            peaks.append(0 if start == 0 else (start + end) // 2)
        start = end + 1
    return peaks


def histogram_peak_pair(values: np.ndarray, config: HistogramConfig) -> tuple | None:
    """Nhận normalized STE/cấu hình; trả (đỉnh đầu, đỉnh thứ hai, hist, edges), hoặc None."""
    # Khối 1: Histogram của STE nằm trên cùng miền [0,1] cho mọi WAV.
    if config.bins < 3 or config.smooth < 1 or config.smooth % 2 == 0 or config.weight <= 0:
        raise ValueError("Cần ít nhất 3 bin, bậc trơn lẻ dương và W dương")
    if not len(values) or not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError("Normalized STE phải hữu hạn, không rỗng và nằm trong [0,1]")
    hist, edges = np.histogram(values, bins=config.bins, range=(0, 1))

    # Khối 2: Lấy hai cực đại đầu theo trục STE, không xếp theo chiều cao/valley.
    peaks = histogram_local_maxima(smooth_1d(hist, config.smooth))
    if len(peaks) < 2:
        return None
    return peaks[0], peaks[1], hist, edges


def histogram_threshold(values: np.ndarray, config: HistogramConfig) -> tuple[float, bool]:
    """Nhận STE của WAV/cấu hình; trả T và cờ fallback mean của chính WAV khi thiếu hai đỉnh."""
    # Khối 1: Không dùng ngưỡng dự phòng học chung hoặc nhãn LAB trong suy luận.
    pair = histogram_peak_pair(values, config)
    if pair is None:
        return float(np.mean(values)), True
    a, b, _, edges = pair
    centers = (edges[:-1] + edges[1:]) / 2

    # Khối 2: Ngưỡng có trọng số của hai tâm bin; W được khóa bằng TRAIN.
    threshold = (config.weight * centers[a] + centers[b]) / (config.weight + 1)
    return float(threshold), False


def as_model(config: HistogramConfig) -> dict:
    """Nhận cấu hình Histogram; trả từ điển để ghi JSON mô hình."""
    return asdict(config)
