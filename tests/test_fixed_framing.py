"""Kiểm chứng cấu hình 25/10 ms xuyên suốt training, Cross Validation và test."""

import unittest
from unittest.mock import patch

import numpy as np

from speech_silence.algorithms import HistogramConfig
from speech_silence.config import FRAME_MS, HOP_MS
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
        """Đệm khung cuối vẫn dùng 400/1102 mẫu; không suy ngược frame từ thời gian tâm."""
        for fs, count in ((16000, 400), (44100, 1102)):
            length = round(fs * HOP_MS / 1000)
            feature = extract(np.ones(length), fs, FRAME_MS, HOP_MS, compute_f0=False)
            self.assertEqual(round(fs * FRAME_MS / 1000), count)
            self.assertAlmostEqual(feature.ste[0], length / count)
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

    def test_binary_and_gaussian_validate_one_configuration(self):
        """Mỗi phương pháp có bốn lượt kiểm chứng và một lượt fit cuối, không thử ba frame."""
        for method in ("binary", "statistical"):
            with patch("speech_silence.pipeline.fit", wraps=fit) as spy:
                models, _ = choose(self.records, only=method)
                self.assertEqual(spy.call_count, 5)
                self.assertEqual(models[method]["frame_ms"], 25)

    def test_histogram_search_does_not_include_frame_choices(self):
        """Histogram chỉ thử 162 cấu hình riêng, không nhân thêm ba độ dài khung."""
        metric = {"balanced_error": 0, "missed": 0, "extra": 0, "mae_ms": 0}
        with patch("speech_silence.pipeline.fit", return_value={"frame_ms": 25, "hop_ms": 10}) as spy:
            with patch("speech_silence.pipeline.predict", return_value=(None, None, 0, False)):
                with patch("speech_silence.pipeline.score", return_value=metric):
                    choose(self.records, only="histogram")
            self.assertEqual(spy.call_count, 162 * 4 + 1)

    def test_old_models_are_rejected(self):
        """Từ chối khung 20/30 ms, hop khác 10 ms hoặc mô hình thiếu cấu hình."""
        for model in ({"frame_ms": 20, "hop_ms": 10}, {"frame_ms": 30, "hop_ms": 10},
                      {"frame_ms": 25, "hop_ms": 5}, {}):
            with self.assertRaisesRegex(ValueError, "huấn luyện lại"):
                predict(self.records[0].samples, self.fs, model, "binary", compute_f0=False)
