"""Giao diện tương thích cho phần dùng chung; mã thuật toán nằm ở thư mục từng thành viên.

TT1_BinarySearch/algorithm.py: Binary Search.
TT2_Histogram/algorithm.py: Histogram.
TT3_Statistics/algorithm.py: Statistical Gaussian.
"""

from TT1_BinarySearch.algorithm import binary_threshold
from TT2_Histogram.algorithm import (
    HistogramConfig, smooth_1d, histogram_local_maxima,
    histogram_peak_pair, histogram_threshold, as_model,
)
from TT3_Statistics.algorithm import normal_cdf, gaussian_threshold

__all__ = [
    "binary_threshold", "HistogramConfig", "smooth_1d",
    "histogram_local_maxima", "histogram_peak_pair",
    "histogram_threshold", "as_model", "normal_cdf", "gaussian_threshold",
]
