"""Thuật toán của thành viên 2: ngưỡng Histogram adaptive với kiểm tra đỉnh/valley."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class HistogramConfig:
    """Cấu hình tham số cho thuật toán Histogram.

    Attributes:
        bins: Số lượng bin chia khoảng giá trị normalized STE trong [0, 1].
        smooth: Kích thước cửa sổ lọc trung bình trượt để làm mịn histogram.
        weight: Trọng số ưu tiên đỉnh Silence (giúp ngưỡng nghiêng về phía an toàn).
        min_peak_distance: Khoảng cách nhỏ nhất giữa hai đỉnh, tính bằng số bin.
        min_valley_depth: Độ sâu valley tối thiểu tương đối với đỉnh thấp hơn (0 đến 1).
    """
    bins: int = 64
    smooth: int = 3
    weight: int = 5
    min_peak_distance: int = 4
    min_valley_depth: float = 0.2


def smooth_1d(x: np.ndarray, size: int) -> np.ndarray:
    """Làm trơn mảng 1D bằng bộ lọc trung bình trượt (Moving Average) thuần Numpy.

    Thay thế hoàn toàn uniform_filter1d của scipy để tuân thủ quy định tự cài đặt.
    Sử dụng chế độ đệm biên tương đương mode='nearest'.

    Args:
        x: Mảng dữ liệu 1D (ví dụ: mảng đếm tần suất histogram).
        size: Kích thước cửa sổ lọc (số phần tử).

    Returns:
        Mảng 1D sau khi làm trơn có cùng kích thước với mảng x ban đầu.
    """
    # Khối 1: Kiểm tra kích thước cửa sổ lọc
    if size <= 1:
        return x.astype(float)

    # Khối 2: Đệm biên hai phía bằng giá trị biên gần nhất (edge mode)
    pad_len = size // 2
    padded = np.pad(x.astype(float), pad_len, mode="edge")

    # Khối 3: Tạo nhân lọc trung bình (kernel) và thực hiện tích chập 1D
    kernel = np.ones(size, dtype=float) / size
    smoothed = np.convolve(padded, kernel, mode="valid")

    return smoothed


def histogram_local_maxima(histogram: np.ndarray) -> list[int]:
    """Nhận histogram đã làm trơn; trả chỉ số đỉnh, gồm biên 0/cuối và plateau dương."""
    # Khối 1: Duyệt từng plateau thay vì đếm nhiều điểm bằng nhau thành nhiều đỉnh.
    peaks = []
    start = 0
    while start < len(histogram):
        end = start
        while end + 1 < len(histogram) and histogram[end + 1] == histogram[start]:
            end += 1

        # Khối 2: Đỉnh phải cao hơn hai phía; ở biên chỉ có một phía để so sánh.
        left = histogram[start - 1] if start > 0 else -np.inf
        right = histogram[end + 1] if end + 1 < len(histogram) else -np.inf
        if histogram[start] > 0 and histogram[start] > left and histogram[start] > right:
            peaks.append(0 if start == 0 else (start + end) // 2)
        start = end + 1
    return peaks


def histogram_peak_pair(values: np.ndarray, config: HistogramConfig) -> tuple | None:
    """Tìm cặp đỉnh từ STE không có nhãn; trả (a, b, hist, edges, valley_depth) hoặc None.

    a bị giới hạn trong vùng chứa 20% giá trị năng lượng thấp nhất, nhằm tránh
    chọn hai đỉnh ở vùng Speech. Đây là giả định năng lượng nền thấp, không phải
    kiểm chứng lớp bằng LAB. b phải có valley đủ sâu và đủ xa a.
    """
    # Khối 1: Kiểm tra cấu hình và dữ liệu trước khi dựng histogram trên miền [0, 1].
    if config.bins < 3 or config.smooth < 1 or config.smooth % 2 == 0:
        raise ValueError("Histogram cần ít nhất 3 bin và cửa sổ trơn lẻ, dương")
    if config.weight <= 0 or config.min_peak_distance < 2 or not 0 <= config.min_valley_depth <= 1:
        raise ValueError("Trọng số, khoảng cách đỉnh hoặc độ sâu valley không hợp lệ")
    if not len(values) or not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError("Normalized STE phải hữu hạn, không rỗng và nằm trong [0, 1]")

    # Khối 2: Phát hiện đỉnh kể cả bin 0; xác định vùng nền từ giá trị STE của WAV.
    hist, edges = np.histogram(values, bins=config.bins, range=(0, 1))
    smooth = smooth_1d(hist, size=config.smooth)
    peaks = histogram_local_maxima(smooth)
    low_limit = min(config.bins - 1, int(np.quantile(values, 0.2) * config.bins))
    low_peaks = [index for index in peaks if index <= low_limit]
    if not low_peaks:
        return None

    # Khối 3: Đỉnh nền là đỉnh cao nhất trong vùng thấp, không phải đỉnh cao tùy ý.
    a = max(low_peaks, key=lambda index: (smooth[index], -index))
    candidates = []
    for b in peaks:
        if b - a < config.min_peak_distance:
            continue
        valley = float(np.min(smooth[a + 1:b]))
        depth = 1 - valley / min(smooth[a], smooth[b])

        # Khối 4: Chỉ giữ cặp có valley, ưu tiên đỉnh Speech nổi rõ so với valley.
        if depth >= config.min_valley_depth:
            candidates.append((b, depth, smooth[b] - valley))
    if not candidates:
        return None
    b, depth, _ = max(candidates, key=lambda item: (item[2], smooth[item[0]], item[0] - a))
    return a, b, hist, edges, float(depth)


def histogram_threshold(values: np.ndarray, config: HistogramConfig,
                        fallback: float | None = None) -> tuple[float, bool]:
    """Tìm ngưỡng phân đoạn thích nghi từ Histogram mức năng lượng của tín hiệu.

    Thuật toán xây dựng lược đồ tần suất năng lượng, làm trơn bằng moving average,
    chọn đỉnh nền ở vùng năng lượng thấp và đỉnh cao có valley rõ ràng,
    sau đó tính ngưỡng có trọng số. Không có cặp phù hợp thì dùng fallback.

    Args:
        values: Mảng normalized STE của toàn bộ các khung trong tín hiệu kiểm thử.
        config: Đối tượng cấu hình HistogramConfig (số bin, độ trơn, trọng số).
        fallback: Ngưỡng dự phòng khi histogram không phát hiện đủ 2 đỉnh rõ rệt.

    Returns:
        tuple gồm:
            - threshold: Giá trị ngưỡng tìm được (float).
            - fallback_used: True nếu phải sử dụng ngưỡng dự phòng, ngược lại False.
    """
    # Khối 1: Dùng cùng quy tắc vị trí, khoảng cách và valley trong training/test.
    pair = histogram_peak_pair(values, config)
    if pair is None:
        if fallback is None:
            raise ValueError("Histogram không có cặp đỉnh nền/Speech phù hợp; cần ngưỡng dự phòng")
        return float(fallback), True

    # Khối 2: Tính ngưỡng nghiêng về đỉnh nền từ hai tâm bin đã kiểm tra.
    a, b, _, edges, _ = pair
    centers = (edges[:-1] + edges[1:]) / 2
    threshold = float((config.weight * centers[a] + centers[b]) / (config.weight + 1))
    return threshold, False


def as_model(config: HistogramConfig) -> dict:
    """Chuyển đổi đối tượng HistogramConfig thành từ điển thông thường để serialize JSON.

    Args:
        config: Đối tượng cấu hình HistogramConfig.

    Returns:
        Từ điển chứa các trường tham số của cấu hình.
    """
    return asdict(config)
