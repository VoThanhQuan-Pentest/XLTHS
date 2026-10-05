"""Kiểm tra hai cực đại đầu, plateau, làm trơn và fallback của Histogram BT1."""

import unittest
import numpy as np

from speech_silence.algorithms import (
    HistogramConfig, smooth_1d, histogram_local_maxima, histogram_peak_pair, histogram_threshold,
)


class HistogramRegressionTests(unittest.TestCase):
    """Tín hiệu tổng hợp chỉ phục vụ unit test, không đưa vào kết quả thực nghiệm."""

    def test_first_two_peaks_include_bin_zero(self):
        """Đỉnh cao nhất thứ ba không được thay thế một trong hai đỉnh đầu."""
        values = np.r_[np.zeros(30), np.full(20, 3.5 / 32), np.full(200, 16.5 / 32)]
        a, b, _, _ = histogram_peak_pair(values, HistogramConfig(bins=32, smooth=1))
        self.assertEqual((a, b), (0, 3))

    def test_plateau_and_right_boundary(self):
        """Một plateau chỉ có một đỉnh; giữ cả hai mép của histogram."""
        self.assertEqual(histogram_local_maxima(np.array([8, 8, 4, 6, 6, 1])), [0, 3])
        self.assertEqual(histogram_local_maxima(np.array([2, 1, 4])), [0, 2])

    def test_smoothing_repeats_edge_values(self):
        """Trung bình tại mép lặp mẫu biên, không chia theo cửa sổ bị cắt."""
        actual = smooth_1d(np.array([9., 0., 3.]), 3)
        np.testing.assert_allclose(actual, [6, 4, 2])

    def test_weighted_bin_centers(self):
        """T lấy từ tâm hai bin, không lấy chỉ số hoặc độ cao của đỉnh."""
        values = np.r_[np.zeros(30), np.full(20, 3.5 / 32)]
        threshold, fallback = histogram_threshold(values, HistogramConfig(bins=32, smooth=1, weight=5))
        self.assertFalse(fallback)
        self.assertAlmostEqual(threshold, (5 * .5 / 32 + 3.5 / 32) / 6)

    def test_fallback_is_mean_of_current_wav(self):
        """Histogram một đỉnh dùng mean của chính WAV, gồm zero-audio."""
        for level in (0., .4):
            threshold, used = histogram_threshold(np.full(100, level), HistogramConfig())
            self.assertTrue(used)
            self.assertAlmostEqual(threshold, level)

    def test_invalid_values_and_smoothing(self):
        """Không dựng histogram cho chuỗi rỗng, ngoài miền hoặc bậc trơn chẵn."""
        for values, config in ((np.array([]), HistogramConfig()),
                               (np.array([1.1]), HistogramConfig()),
                               (np.array([0.]), HistogramConfig(smooth=2))):
            with self.assertRaises(ValueError):
                histogram_threshold(values, config)


if __name__ == "__main__":
    unittest.main()
