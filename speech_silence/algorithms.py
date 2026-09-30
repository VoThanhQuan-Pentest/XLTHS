"""Các thuật toán xác định ngưỡng phân đoạn tiếng nói và khoảng lặng (Speech/Silence).

Bao gồm 3 phương pháp độc lập theo yêu cầu đề tài:
1. Binary Search: Tìm kiếm nhị phân cân bằng diện tích nhầm lẫn giữa hai lớp.
2. Histogram: Phân tích phân bố mức năng lượng để tìm hai đỉnh cục bộ.
3. Statistical Gaussian: Mô hình hóa thống kê Gaussian từ tập dữ liệu huấn luyện.

Mã nguồn được cài đặt hoàn toàn bằng Numpy và thư viện chuẩn Python (math),
không sử dụng các hàm xử lý tín hiệu từ toolbox hay thư viện ngoài (scipy).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import numpy as np


@dataclass(frozen=True)
class HistogramConfig:
    """Cấu hình tham số cho thuật toán Histogram.

    Attributes:
        bins: Số lượng bin chia khoảng giá trị normalized STE trong [0, 1].
        smooth: Kích thước cửa sổ lọc trung bình trượt để làm mịn histogram.
        weight: Trọng số ưu tiên đỉnh Silence (giúp ngưỡng nghiêng về phía an toàn).
    """
    bins: int = 64
    smooth: int = 3
    weight: int = 5


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


def normal_cdf(x: float, mean: float, std: float) -> float:
    """Tính hàm phân bố tích lũy chuẩn tắc (Gaussian Cumulative Distribution Function).

    Sử dụng hàm sai số giải tích math.erf có sẵn trong thư viện chuẩn Python,
    không dùng thư viện ngoài scipy.stats.norm.

    Args:
        x: Giá trị ngưỡng STE cần tính xác suất tích lũy.
        mean: Kỳ vọng (mean) của phân bố Gaussian.
        std: Độ lệch chuẩn (standard deviation) của phân bố Gaussian.

    Returns:
        Xác suất tích lũy P(X <= x) trong khoảng [0, 1].
    """
    # Khối 1: Xử lý trường hợp suy biến khi độ lệch chuẩn xấp xỉ 0
    if std <= 1e-12:
        return 1.0 if x >= mean else 0.0

    # Khối 2: Tính toán tích phân Gauss qua hàm math.erf
    z = (x - mean) / (std * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def binary_threshold(silence: np.ndarray, speech: np.ndarray) -> float:
    """Tìm ngưỡng phân đoạn tối ưu bằng thuật toán Tìm kiếm nhị phân (Binary Search).

    Thuật toán duyệt tìm ngưỡng trong miền chồng lấn giữa hai lớp [min(Sp), max(Sil)]
    sao cho cân bằng diện tích nhầm lẫn (phần Silence vượt ngưỡng và Speech dưới ngưỡng).

    Args:
        silence: Mảng normalized STE của các khung khoảng lặng từ tập huấn luyện.
        speech: Mảng normalized STE của các khung tiếng nói từ tập huấn luyện.

    Returns:
        Giá trị ngưỡng năng lượng tối ưu T nằm trong khoảng [0, 1].
    """
    # Khối 1: Kiểm tra dữ liệu đầu vào có đủ 2 lớp hay không
    if not len(silence) or not len(speech):
        raise ValueError("Thiếu khung huấn luyện cho một lớp")

    # Khối 2: Tìm khoảng chồng lấn giữa giá trị lớn nhất của Sil và nhỏ nhất của Sp
    smax, pmin = float(np.max(silence)), float(np.min(speech))
    if smax < pmin:
        return (smax + pmin) / 2

    # Khối 3: Khởi tạo cận tìm kiếm nhị phân
    lo, hi = pmin, smax
    if lo >= hi:
        return float(np.clip((np.mean(silence) + np.mean(speech)) / 2, 0, 1))

    # Khối 4: Vòng lặp chia đôi khoảng tìm kiếm để cân bằng diện tích lỗi hai phía
    for _ in range(100):
        mid = (lo + hi) / 2
        # Tính diện tích sai số: (Silence > mid) - (Speech < mid)
        delta = np.maximum(silence - mid, 0).mean() - np.maximum(mid - speech, 0).mean()
        if delta > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-8:
            break

    # Khối 5: Chuẩn hóa ngưỡng trong khoảng an toàn [0, 1]
    return float(np.clip((lo + hi) / 2, 0, 1))


def histogram_threshold(values: np.ndarray, config: HistogramConfig,
                        fallback: float | None = None) -> tuple[float, bool]:
    """Tìm ngưỡng phân đoạn thích nghi từ Histogram mức năng lượng của tín hiệu.

    Thuật toán xây dựng lược đồ tần suất năng lượng, làm trơn bằng moving average,
    tìm 2 đỉnh cục bộ tương ứng với Silence (đỉnh thấp) và Speech (đỉnh cao),
    sau đó tính ngưỡng theo trọng số giữa 2 tâm bin này.

    Args:
        values: Mảng normalized STE của toàn bộ các khung trong tín hiệu kiểm thử.
        config: Đối tượng cấu hình HistogramConfig (số bin, độ trơn, trọng số).
        fallback: Ngưỡng dự phòng khi histogram không phát hiện đủ 2 đỉnh rõ rệt.

    Returns:
        tuple gồm:
            - threshold: Giá trị ngưỡng tìm được (float).
            - fallback_used: True nếu phải sử dụng ngưỡng dự phòng, ngược lại False.
    """
    # Khối 1: Tính histogram và làm trơn phân bố bằng Moving Average tự viết
    hist, edges = np.histogram(values, bins=config.bins, range=(0, 1))
    smooth = smooth_1d(hist, size=config.smooth)

    # Khối 2: Phát hiện tất cả các đỉnh cục bộ (local maxima) trong phân bố
    peaks = [i for i in range(1, len(smooth) - 1)
             if smooth[i] >= smooth[i - 1] and smooth[i] > smooth[i + 1]]

    # Khối 3: Lọc các cặp đỉnh tách biệt ít nhất 2 bin để tránh nhiễu cục bộ
    pairs = [(a, b) for a in peaks for b in peaks if b >= a + 2]
    if not pairs:
        if fallback is None:
            raise ValueError("Histogram không có hai đỉnh; cần ngưỡng dự phòng")
        return float(fallback), True

    # Khối 4: Chọn cặp đỉnh tối ưu (ưu tiên độ cao đỉnh và khoảng cách giữa hai đỉnh)
    a, b = max(pairs, key=lambda pair: (min(smooth[pair[0]], smooth[pair[1]]),
                                        smooth[pair[0]] + smooth[pair[1]],
                                        pair[1] - pair[0]))

    # Khối 5: Tính tọa độ tâm bin và suy ra ngưỡng phân tách có trọng số
    centers = (edges[:-1] + edges[1:]) / 2
    threshold = float((config.weight * centers[a] + centers[b]) / (config.weight + 1))
    return threshold, False


def gaussian_threshold(silence: np.ndarray, speech: np.ndarray) -> tuple[float, dict[str, float]]:
    """Tìm ngưỡng phân đoạn tối ưu bằng mô hình Thống kê Gaussian (Statistical Approach).

    Mô hình hóa phân bố normalized STE của Silence và Speech dưới dạng 2 phân bố chuẩn
    N(meanSil, stdSil) và N(meanSp, stdSp). Giải nghiệm giao điểm của 2 hàm mật độ xác suất
    và chọn nghiệm làm cực tiểu hóa tổng lỗi phân lớp Bayes.

    Args:
        silence: Mảng normalized STE của các khung khoảng lặng từ tập huấn luyện.
        speech: Mảng normalized STE của các khung tiếng nói từ tập huấn luyện.

    Returns:
        tuple gồm:
            - threshold: Giá trị ngưỡng năng lượng tối ưu (float).
            - statistics: Từ điển chứa các đại lượng thống kê (meanSil, stdSil, meanSp, stdSp, nSil, nSp).
    """
    # Khối 1: Kiểm tra tính hợp lệ của dữ liệu huấn luyện
    if not len(silence) or not len(speech):
        raise ValueError("Thiếu khung huấn luyện cho một lớp")

    # Khối 2: Ước lượng kỳ vọng và độ lệch chuẩn của từng phân bố
    ms, mp = float(np.mean(silence)), float(np.mean(speech))
    ss, sp = float(np.std(silence)), float(np.std(speech))
    sd_s, sd_p = max(ss, 1e-6), max(sp, 1e-6)

    # Khối 3: Thiết lập phương trình bậc hai xác định giao điểm 2 hàm mật độ Gaussian
    # f_sil(x) = f_sp(x) <=> a*x^2 + b*x + c = 0
    a = 1 / sd_p**2 - 1 / sd_s**2
    b = -2 * mp / sd_p**2 + 2 * ms / sd_s**2
    c = mp**2 / sd_p**2 - ms**2 / sd_s**2 - 2 * np.log(sd_s / sd_p)

    # Khối 4: Tìm các nghiệm thực của phương trình nằm trong miền hợp lệ [0, 1]
    candidates = [0.0, 1.0]
    roots = np.roots([a, b, c]) if abs(a) > 1e-12 else ([-c / b] if abs(b) > 1e-12 else [])
    candidates.extend(float(np.real(x)) for x in roots
                      if abs(np.imag(x)) < 1e-9 and 0 <= np.real(x) <= 1)

    # Khối 5: Chọn nghiệm có tổng sai số phân lớp nhỏ nhất dựa trên normal_cdf tự viết
    def total_error(th: float) -> float:
        """Tính lỗi kỳ vọng hai lớp cho ngưỡng th; trả về xác suất lỗi cân bằng."""
        # P(lỗi) = [P(Sil > th) + P(Sp < th)] / 2
        return ((1.0 - normal_cdf(th, ms, sd_s)) + normal_cdf(th, mp, sd_p)) / 2.0

    best_threshold = min(candidates, key=total_error)

    # Khối 6: Đóng gói tham số thống kê trả về
    stats = {
        "meanSil": ms, "stdSil": ss,
        "meanSp": mp, "stdSp": sp,
        "nSil": len(silence), "nSp": len(speech)
    }
    return float(best_threshold), stats


def as_model(config: HistogramConfig) -> dict:
    """Chuyển đổi đối tượng HistogramConfig thành từ điển thông thường để serialize JSON.

    Args:
        config: Đối tượng cấu hình HistogramConfig.

    Returns:
        Từ điển chứa các trường tham số của cấu hình.
    """
    return asdict(config)
