"""Kiểm chứng khung centered_hop_v1 và hiệu chỉnh TRAIN theo BT1."""

import unittest
from unittest.mock import patch

import numpy as np

from speech_silence.algorithms import HistogramConfig
from speech_silence.config import FRAME_MS, HOP_MS, FEATURE_LAYOUT
from speech_silence.data import Interval, Record
from speech_silence.features import extract
from speech_silence.pipeline import choose, fit, predict


class FixedFramingTests(unittest.TestCase):
    """Kiểm tra tham số phân khung thật sự được truyền vào các phép tính."""

    def setUp(self):
        """Tạo bốn bản ghi training có hai lớp; không dùng dữ liệu test của bài."""
        self.fs = 16000
        samples = np.full(8000, 0.001)
        t = np.arange(3200) / self.fs
        samples[2400:5600] = 0.2 + 0.05 * np.sin(2 * np.pi * 200 * t)
        labels = (Interval(0, 0.15, False), Interval(0.15, 0.35, True), Interval(0.35, 0.5, False))
        self.records = [Record(f"train_{i}", self.fs, samples.copy(), labels) for i in range(4)]

    def test_sample_counts_and_short_last_frame(self):
        """Khung danh định 400/1102 mẫu; khung mép chỉ lấy mẫu thật, không đệm zero."""
        for fs, count in ((16000, 400), (44100, 1102)):
            length = round(fs * HOP_MS / 1000)
            feature = extract(np.ones(length), fs, FRAME_MS, HOP_MS, compute_f0=False)
            self.assertEqual(round(fs * FRAME_MS / 1000), count)
            self.assertAlmostEqual(feature.ste[0], 1.0)
            self.assertAlmostEqual(feature.times[0], HOP_MS / 2000)
            self.assertAlmostEqual(feature.edges[-1], length / fs)
            self.assertTrue(np.isfinite(feature.log_ste).all())

    def test_training_and_prediction_use_fixed_parameters(self):
        """Cả ba phương pháp đều truyền 25/10 vào extract và ghi đúng cấu hình mô hình."""
        with patch("speech_silence.pipeline.extract", wraps=extract) as spy:
            features = []
            for method in ("binary", "histogram", "statistical"):
                model = fit(self.records, HistogramConfig(), method=method)
                self.assertEqual((model["frame_ms"], model["hop_ms"]), (25, 10))
                f, _, _, _ = predict(self.records[0].samples, self.fs, model, method, compute_f0=False)
                features.append(f)
            self.assertTrue(all(call.args[2:4] == (25, 10) for call in spy.call_args_list))
            for f in features[1:]:
                np.testing.assert_array_equal(f.times, features[0].times)
                np.testing.assert_array_equal(f.normalized_ste, features[0].normalized_ste)

    def test_training_calibration_fits_each_candidate_once(self):
        """Binary tìm sáu median, Histogram tám W, Gaussian một mô hình trên toàn TRAIN."""
        for method, expected in (("binary", 6), ("histogram", 8), ("statistical", 1)):
            with patch("speech_silence.pipeline.fit", wraps=fit) as spy:
                models, calibration = choose(self.records, only=method)
                self.assertEqual(spy.call_count, expected)
                self.assertTrue(all(call.args[0] is self.records for call in spy.call_args_list))
                self.assertEqual(models[method]["frame_ms"], 25)
                self.assertEqual(calibration[method]["protocol"], "train_calibration")

    def test_histogram_search_does_not_include_frame_choices(self):
        """Histogram chỉ đổi W, cố định 128 bins/3 smoothing/25 ms/10 ms."""
        metric = {"balanced_error": 0, "missed": 0, "extra": 0, "mae_ms": 0}
        with patch("speech_silence.pipeline.fit", return_value={"frame_ms": 25, "hop_ms": 10}) as spy:
            with patch("speech_silence.pipeline.predict", return_value=(None, None, 0, False)):
                with patch("speech_silence.pipeline.score", return_value=metric):
                    choose(self.records, only="histogram")
            self.assertEqual(spy.call_count, 8)
            self.assertTrue(all((c.args[1].bins, c.args[1].smooth) == (128, 3)
                                for c in spy.call_args_list))

    def test_old_models_are_rejected(self):
        """Từ chối cả mô hình 25/10 cũ thiếu dấu cửa sổ mới."""
        for model in ({"frame_ms": 20, "hop_ms": 10}, {"frame_ms": 30, "hop_ms": 10},
                      {"frame_ms": 25, "hop_ms": 5}, {"frame_ms": 25, "hop_ms": 10}, {}):
            with self.assertRaisesRegex(ValueError, "huấn luyện lại"):
                predict(self.records[0].samples, self.fs, model, "binary", compute_f0=False)

    def test_analysis_window_is_centered_and_end_is_clipped(self):
        """Cửa sổ đầu [-7.5,17.5] ms bị cắt, cửa sổ tiếp theo [2.5,27.5] ms."""
        signal = np.zeros(1600)
        signal[:280] = 1
        f = extract(signal, 16000, 25, 10, compute_f0=False)
        np.testing.assert_allclose(f.ste[:2], [1, .6])
        self.assertAlmostEqual(f.times[0], .005)
        self.assertAlmostEqual(f.edges[-1], .1)
        tail = extract(np.ones(1650), 16000, 25, 10)
        self.assertTrue(np.isfinite(tail.ste).all())
        self.assertAlmostEqual(tail.ste[-1], 1)
        self.assertAlmostEqual(tail.times[-1], (.1 + 1650 / 16000) / 2)
