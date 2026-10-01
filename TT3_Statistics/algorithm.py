"""Thuật toán của thành viên 3: ngưỡng thống kê từ hai phân bố Gaussian training."""

from __future__ import annotations

import math
import numpy as np


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
