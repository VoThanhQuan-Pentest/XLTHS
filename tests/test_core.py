import numpy as np

from speech_silence.algorithms import HistogramConfig, binary_threshold, gaussian_threshold, histogram_threshold
from speech_silence.data import Interval, speech_at
from speech_silence.evaluation import boundary_scores
from speech_silence.features import extract, remove_virtual_silence, predicted_boundaries
from speech_silence.pipeline import predict


def test_virtual_silence_exact_limit_and_edges():
    edges = np.arange(0, 1.01, 0.01)
    mask = np.ones(100, bool)
    mask[:19] = False
    mask[30:50] = False
    mask[80:] = False
    cleaned = remove_virtual_silence(mask, edges)
    assert cleaned[:19].all()
    assert not cleaned[30:50].any()
    assert not cleaned[80:].any()
    for duration, survives in ((0.199, False), (0.200, True), (0.201, True)):
        exact_edges = np.array([0.0, duration, 1.0])
        exact_mask = np.array([False, True])
        assert (not remove_virtual_silence(exact_mask, exact_edges)[0]) == survives


def test_features_and_labels_two_sample_rates():
    for fs in (16000, 44100):
        signal = np.zeros(round(0.51 * fs))
        feature = extract(signal, fs, 30)
        assert len(feature.times) == len(feature.normalized_ste)
        assert np.all(feature.normalized_ste == 0)
        assert np.isfinite(feature.log_ste).all()
        assert len(feature.f0) == len(feature.times)
        labels = (Interval(0, 0.2, False), Interval(0.2, 0.5, True))
        speech, valid = speech_at(feature.times, labels)
        assert speech.any() and (~speech & valid).any()
        assert not valid[-1]


def test_f0_autocorrelation_on_known_tone():
    fs = 16000
    time = np.arange(fs) / fs
    feature = extract(0.5 * np.sin(2 * np.pi * 200 * time), fs, 30)
    voiced = feature.f0[np.isfinite(feature.f0)]
    assert len(voiced) > 80
    assert abs(np.median(voiced) - 200) < 3


def test_thresholds_and_fallback():
    sil = np.array([0.01, 0.02, 0.03])
    sp = np.array([0.7, 0.8, 0.9])
    assert binary_threshold(sil, sp) == 0.365
    threshold, stats = gaussian_threshold(sil, sp)
    assert 0 < threshold < 1
    assert stats["nSil"] == 3 and stats["nSp"] == 3
    value, used = histogram_threshold(np.zeros(100), HistogramConfig(), 0.15)
    assert used and value == 0.15


def test_boundary_matching_counts_extra():
    reference = [(0.5, True), (2.5, False)]
    predicted = [(0.51, True), (1.2, False), (1.5, True), (2.49, False)]
    result = boundary_scores(reference, predicted)
    assert result["matched"] == 2
    assert result["extra"] == 2
    assert result["missed"] == 0
    assert abs(result["mae_ms"] - 10) < 1e-8
    # Sai lệch lớn hơn 200 ms vẫn phải được tính, không được biến thành biên thiếu/thừa.
    far = boundary_scores([(0.5, True)], [(0.9, True)])
    assert far["matched"] == 1 and abs(far["mae_ms"] - 400) < 1e-8


def test_prediction_does_not_accept_labels():
    model = {"frame_ms": 20, "hop_ms": 10, "minimum_silence_ms": 200,
             "binary_threshold": 0.1, "statistical_threshold": 0.2,
             "histogram_fallback": 0.3, "histogram": {"bins": 32, "smooth": 3, "weight": 5}}
    samples = np.r_[np.zeros(16000), np.ones(16000) * 0.3]
    feature, mask, _, _ = predict(samples, 16000, model, "binary")
    boundaries = predicted_boundaries(mask, feature.edges)
    assert len(boundaries) == 1
