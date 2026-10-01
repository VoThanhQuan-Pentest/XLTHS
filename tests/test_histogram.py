"""Kiểm tra lỗi đỉnh biên, plateau, valley và khoảng cách của Histogram."""

import unittest
import numpy as np

from speech_silence.algorithms import HistogramConfig, histogram_local_maxima, histogram_peak_pair, histogram_threshold


class HistogramRegressionTests(unittest.TestCase):
    """Các tín hiệu tổng hợp kiểm tra quy tắc chọn đỉnh, không dùng nhãn kiểm thử."""

    def test_bin_zero_is_kept(self):
        """Đỉnh bin 0 phải được chọn làm đỉnh thấp khi dữ liệu có hai vùng rõ."""
        values = np.r_[np.zeros(100), np.full(50, 0.4), np.full(30, 0.7)]
        pair = histogram_peak_pair(values, HistogramConfig(bins=32, smooth=1))
        self.assertIsNotNone(pair)
        self.assertEqual(pair[0], 0)
        self.assertGreater(pair[1], 0)

    def test_plateau_and_right_boundary(self):
        """Một plateau chỉ có một đỉnh; hai biên không bị bỏ qua."""
        self.assertEqual(histogram_local_maxima(np.array([8, 8, 4, 6, 6, 1])), [0, 3])
        self.assertEqual(histogram_local_maxima(np.array([2, 1, 4])), [0, 2])

    def test_shallow_valley_is_rejected(self):
        """Hai dao động trên nền histogram cao không được coi là hai lớp tách biệt."""
        counts = np.full(32, 76)
        counts[0], counts[16] = 100, 80
        values = np.repeat((np.arange(32) + 0.5) / 32, counts)
        threshold, used = histogram_threshold(values, HistogramConfig(bins=32, smooth=1), 0.02)
        self.assertTrue(used)
        self.assertEqual(threshold, 0.02)

    def test_peak_distance_is_respected(self):
        """Khoảng cách được cấu hình phải loại cặp đỉnh quá gần nhau."""
        values = np.r_[np.zeros(100), np.full(80, 3.5 / 32)]
        config = HistogramConfig(bins=32, smooth=1, min_peak_distance=6)
        threshold, used = histogram_threshold(values, config, 0.02)
        self.assertTrue(used)
        self.assertEqual(threshold, 0.02)

    def test_constant_signal_uses_fallback(self):
        """Histogram một đỉnh dùng ngưỡng dự phòng, không bịa ra đỉnh thứ hai."""
        threshold, used = histogram_threshold(np.zeros(100), HistogramConfig(), 0.02)
        self.assertTrue(used)
        self.assertEqual(threshold, 0.02)
