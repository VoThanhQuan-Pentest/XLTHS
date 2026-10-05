"""Kiểm tra hành vi quan trọng của thuật toán, metric và dữ liệu thật theo BT1."""

from pathlib import Path
import unittest
import numpy as np

from speech_silence.algorithms import binary_threshold, gaussian_threshold
from speech_silence.data import Interval, Record, discover, read_record
from speech_silence.features import median_filter, remove_virtual_silence
from speech_silence.evaluation import boundary_scores, summarize_scores, estimate_snr, score
from speech_silence.pipeline import choose, predict


class AlgorithmBehaviorTests(unittest.TestCase):
    """Test trường hợp biên riêng, không biến tín hiệu tổng hợp thành dữ liệu bài nộp."""

    def test_binary_uses_overlap_counts(self):
        """Giá trị ngoài overlap không được giữ trong mẫu số mean."""
        threshold = binary_threshold(np.array([0., .1, .2]), np.array([.15, .3, .4, .9]))
        self.assertAlmostEqual(threshold, .175, places=8)

    def test_binary_touching_and_separated_classes(self):
        """Miền chạm trả .2; miền tách trả trung điểm hai mép."""
        self.assertEqual(binary_threshold(np.array([0., .2]), np.array([.2, .9, 1.])), .2)
        self.assertAlmostEqual(binary_threshold(np.array([0., .1]), np.array([.3, .9])), .2)

    def test_median_edge_and_no_renormalization(self):
        """Median lặp mép; đỉnh mất sau lọc không được scale trở lại 1."""
        np.testing.assert_allclose(median_filter(np.array([1., 0., 0.]), 3), [1, 0, 0])
        filtered = median_filter(np.array([.2, .2, 1., .2, .2]), 3)
        self.assertAlmostEqual(filtered.max(), .2)
        with self.assertRaises(ValueError):
            median_filter(np.ones(3), 2)

    def test_gaussian_equal_variance_and_degenerate_fallback(self):
        """Hai std bằng nhau cho midpoint; dữ liệu hằng vẫn cho ngưỡng hữu hạn."""
        threshold, _ = gaussian_threshold(np.array([.1, .2, .3]), np.array([.6, .7, .8]))
        self.assertAlmostEqual(threshold, .45)
        threshold, _ = gaussian_threshold(np.full(5, .2), np.full(5, .2))
        self.assertAlmostEqual(threshold, .2)

    def test_silence_duration_and_short_speech(self):
        """Chỉ silence <200 ms bị lấp; không loại speech 20 ms."""
        for duration in (.19, .20, .21):
            mask = np.array([True, False, True])
            result = remove_virtual_silence(mask, np.array([0., .02, .02 + duration, .04 + duration]))
            self.assertEqual(bool(result[1]), duration < .2)
            self.assertTrue(result[0] and result[2])

    def test_invalid_snr_has_no_fabricated_finite_value(self):
        """Zero-audio, không nhiễu và speech yếu hơn nền đều không có SNR hợp lệ."""
        labels = (Interval(0, .1, False), Interval(.1, .2, True))
        for values in (np.zeros(200), np.r_[np.zeros(100), np.ones(100)],
                       np.r_[np.ones(100), np.zeros(100)]):
            self.assertIsNone(estimate_snr(Record("unit", 1000, values, labels)))


class MetricBehaviorTests(unittest.TestCase):
    """Kiểm tra ghép greedy một-một, không cutoff và hai kiểu tổng hợp sai số."""

    def test_greedy_differs_from_ordered_dp(self):
        """Chọn cặp gần nhất trước, kể cả kết quả khác ghép theo thứ tự thời gian."""
        metric = boundary_scores([(0., True), (10., True)], [(9., True), (11., True)])
        self.assertEqual([(d["reference_s"], d["predicted_s"]) for d in metric["boundary_details"]],
                         [(0., 11.), (10., 9.)])

    def test_same_direction_tie_and_large_error(self):
        """Hòa ưu tiên mốc sớm; biên lệch >200 ms vẫn đi vào MAE."""
        metric = boundary_scores([(1., True), (2., False)], [(0., True), (2., True), (3., False)])
        self.assertEqual(metric["boundary_details"][0]["predicted_s"], 0.)
        self.assertEqual(metric["mae_ms"], 1000.)
        self.assertEqual((metric["matched"], metric["extra"], metric["missed"]), (2, 1, 0))

    def test_no_pairs_returns_none(self):
        """Không ghép được không đồng nghĩa sai số bằng zero."""
        metric = boundary_scores([(1., True)], [(1., False)])
        self.assertIsNone(metric["mae_ms"])
        self.assertIsNone(metric["rmse_ms"])
        self.assertEqual((metric["matched"], metric["extra"], metric["missed"]), (0, 1, 1))

    def test_mean_file_and_pooled_rmse(self):
        """Căn bậc hai sau gộp khác trung bình các RMSE từng file."""
        rows = [boundary_scores([(0., True)], [(.01, True)]),
                boundary_scores([(0., True)], [(.03, True)])]
        summary = summarize_scores(rows)
        self.assertAlmostEqual(summary["mean_file_rmse_ms"], 20)
        self.assertAlmostEqual(summary["pooled_rmse_ms"], np.sqrt(500))
        self.assertAlmostEqual(summary["pooled_mae_ms"], 20)


class RealDatasetAcceptanceTests(unittest.TestCase):
    """Tái học từ TRAIN và kiểm chứng các mục tiêu BT1 trên đúng bốn TEST của đề."""

    @classmethod
    def setUpClass(cls):
        """Đọc dữ liệu đề và học cấu hình từ TRAIN một lần, không đọc baseline JSON."""
        root = Path(__file__).resolve().parents[1]
        cls.training = [read_record(p) for p in discover(root, "TinHieuHuanLuyen")]
        cls.models, cls.calibration = choose(cls.training)
        cls.test = [read_record(p) for p in discover(root, "TinHieuKiemThu")]

    def test_learned_parameters_and_statistics(self):
        """Median 15/W30 phải là kết quả chọn, không giá trị gán cứng."""
        self.assertEqual(self.models["binary"]["median_order"], 15)
        self.assertEqual(self.models["histogram"]["histogram"], {"bins": 128, "smooth": 3, "weight": 30})
        stats = self.models["statistical"]["statistics"]
        self.assertEqual((stats["nSil"], stats["nSp"]), (503, 794))
        for key, expected in (("meanSil", .000368811045), ("stdSil", .000681376238),
                              ("meanSp", .196690200744), ("stdSp", .228553953604)):
            self.assertAlmostEqual(stats[key], expected, places=11)
        self.assertAlmostEqual(self.models["statistical"]["statistical_threshold"], .002763416581, places=11)
        self.assertAlmostEqual(self.models["binary"]["binary_threshold"], .0016054239935545923, places=8)

    def test_twelve_test_results_match_bt1(self):
        """Kiểm tra từng file và số biên lỗi, không chỉ MAE trung bình."""
        expected = {"phone_F2": (30, 10, 5), "phone_M2": (0, 5, 5),
                    "studio_F2": (10, 15, 15), "studio_M2": (5, 15, 10)}
        for record in self.test:
            for method, target in zip(("binary", "histogram", "statistical"), expected[record.name]):
                with self.subTest(wav=record.name, method=method):
                    f, mask, _, _ = predict(record.samples, record.fs, self.models[method], method, compute_f0=False)
                    metric = score(record, f, mask)
                    self.assertAlmostEqual(metric["mae_ms"], target, places=7)
                    self.assertEqual((metric["matched"], metric["extra"], metric["missed"]), (2, 0, 0))

    def test_test_labels_do_not_change_predictions(self):
        """Thay toàn bộ LAB test chỉ đổi đánh giá, không thay tham số/biên suy luận."""
        record = self.test[0]
        altered = Record(record.name, record.fs, record.samples,
                         (Interval(0, record.duration, False),))
        for method, model in self.models.items():
            original = predict(record.samples, record.fs, model, method, compute_f0=False)
            changed = predict(altered.samples, altered.fs, model, method, compute_f0=False)
            np.testing.assert_array_equal(original[1], changed[1])
            self.assertEqual(original[2], changed[2])

    def test_zero_audio_short_and_long_is_silence(self):
        """Zero-audio không thành Speech dù ngưỡng mean fallback bằng zero."""
        for length in (1600, 16000):
            for method, model in self.models.items():
                f, mask, _, _ = predict(np.zeros(length), 16000, model, method)
                self.assertFalse(mask.any())
                self.assertTrue(np.isnan(f.f0).all())


if __name__ == "__main__":
    unittest.main()
