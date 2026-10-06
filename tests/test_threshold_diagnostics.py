"""Kiểm chứng hình tìm ngưỡng dùng đúng bộ giải/đỉnh/phân phối, không thay đáp án phân đoạn."""

import unittest
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from speech_silence.algorithms import (
    binary_threshold, binary_search_details, HistogramConfig, histogram_threshold, gaussian_threshold,
)
from speech_silence.diagnostics import plot_binary_learning, plot_histogram_learning, plot_gaussian_learning


class ThresholdDiagnosticsTests(unittest.TestCase):
    """Các ví dụ nhỏ kiểm tra tính trung thực của telemetry và hình, không xuất làm dữ liệu bài nộp."""

    def tearDown(self):
        """Đóng hình unit test để không ảnh hưởng các cửa sổ của chương trình demo."""
        plt.close("all")

    def test_binary_history_is_the_solver_history(self):
        """T và residual cuối phải khớp, mỗi cận mới là một cận cũ hoặc midpoint cũ."""
        sil = np.array([0., .1, .2])
        sp = np.array([.15, .3, .4, .9])
        info = binary_search_details(sil, sp)
        self.assertEqual(info["threshold"], binary_threshold(sil, sp))
        self.assertAlmostEqual(info["threshold"], .175, places=8)
        for before, after in zip(info["history"], info["history"][1:]):
            if before["delta"] > 0:
                self.assertEqual(after["lower"], before["threshold"])
                self.assertEqual(after["upper"], before["upper"])
            else:
                self.assertEqual(after["upper"], before["threshold"])
                self.assertEqual(after["lower"], before["lower"])
        last = info["history"][-1]
        self.assertTrue(abs(last["delta"]) <= 1e-10 or last["upper"] - last["lower"] <= 1e-10)
        fig, metadata = plot_binary_learning(sil, sp, {"binary_threshold": info["threshold"], "median_order": 1})
        self.assertEqual(metadata["history"], info["history"])
        self.assertEqual(len(fig.axes), 2)

    def test_binary_touching_has_no_fabricated_iterations(self):
        """Nhánh miền chạm không được tạo lịch sử chia đôi giả."""
        info = binary_search_details(np.array([0., .2]), np.array([.2, 1.]))
        self.assertEqual(info["threshold"], .2)
        self.assertEqual(info["history"], [])
        self.assertEqual(info["stop_reason"], "touching_classes")

    def test_histogram_metadata_matches_chosen_centers(self):
        """Hình dùng tâm bin và T của đúng hàm Histogram; không nhận LAB."""
        values = np.r_[np.zeros(20), np.full(10, 3.5 / 32), np.full(60, 16.5 / 32)]
        config = HistogramConfig(bins=32, smooth=1, weight=5)
        threshold, _ = histogram_threshold(values, config)
        fig, info = plot_histogram_learning(values, config, threshold, "unit")
        self.assertEqual(info["peak_indices"], [0, 3])
        self.assertAlmostEqual(info["threshold"], (5 * info["peak_centers"][0] + info["peak_centers"][1]) / 6)
        self.assertEqual(info["source"], "TEST waveform without LAB")
        self.assertEqual(len(fig.axes), 2)
        with self.assertRaises(ValueError):
            plot_histogram_learning(values, config, threshold + .1, "unit")

    def test_gaussian_crossing_and_observed_data_are_separate(self):
        """Mật độ ở T bằng nhau; hình gồm phân bố quan sát và hai PDF fitted."""
        silence = np.array([.01, .02, .03])
        speech = np.array([.3, .4, .5])
        threshold, stats = gaussian_threshold(silence, speech)
        fig, info = plot_gaussian_learning(silence, speech,
            {"statistical_threshold": threshold, "statistics": stats})
        self.assertTrue(info["is_density_crossing"])
        self.assertAlmostEqual(info["density_at_threshold"][0], info["density_at_threshold"][1], places=8)
        self.assertEqual(fig.axes[0].get_yscale(), "log")
        self.assertEqual(fig.axes[1].get_yscale(), "linear")
        with self.assertRaises(ValueError):
            plot_gaussian_learning(silence + .1, speech,
                {"statistical_threshold": threshold, "statistics": stats})


if __name__ == "__main__":
    unittest.main()
