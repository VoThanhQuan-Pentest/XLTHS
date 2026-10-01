"""Thuật toán của thành viên 1: học ngưỡng bằng tìm kiếm nhị phân từ STE có nhãn."""

from __future__ import annotations

import numpy as np


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
