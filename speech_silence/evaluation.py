from __future__ import annotations

from functools import lru_cache
import numpy as np

from .data import Record, reference_boundaries, speech_at
from .features import Features, predicted_boundaries


def boundary_scores(reference: list[tuple[float, bool]], predicted: list[tuple[float, bool]]) -> dict:
    """Ghép biên cùng loại theo thứ tự, không áp dụng dung sai chấp nhận."""
    # 200 ms chỉ dùng để loại silence ảo, không được dùng để làm đẹp metric.
    @lru_cache(None)
    def solve(i: int, j: int) -> tuple[int, float, tuple[tuple[int, int], ...]]:
        if i == len(reference) or j == len(predicted):
            return 0, 0.0, ()
        options = [solve(i + 1, j), solve(i, j + 1)]
        if reference[i][1] == predicted[j][1]:
            n, error, pairs = solve(i + 1, j + 1)
            options.append((n + 1, error + abs(reference[i][0] - predicted[j][0]), ((i, j),) + pairs))
        return max(options, key=lambda row: (row[0], -row[1]))
    count, _, pairs = solve(0, 0)
    errors = np.array([(predicted[j][0] - reference[i][0]) * 1000 for i, j in pairs])
    details = [{"reference_s": reference[i][0], "predicted_s": predicted[j][0],
                "starts_speech": reference[i][1], "error_ms": float((predicted[j][0] - reference[i][0]) * 1000)}
               for i, j in pairs]
    return {"matched": count, "missed": len(reference) - count, "extra": len(predicted) - count,
            "mae_ms": float(np.mean(abs(errors))) if count else None,
            "rmse_ms": float(np.sqrt(np.mean(errors ** 2))) if count else None,
            "precision": count / len(predicted) if predicted else (1.0 if not reference else 0.0),
            "recall": count / len(reference) if reference else 1.0,
            "f1": 2 * count / (len(reference) + len(predicted)) if reference or predicted else 1.0,
            "boundary_details": details}


def score(record: Record, features: Features, mask: np.ndarray) -> dict:
    ref = reference_boundaries(record.labels)
    # Không chấm phần đuôi WAV chưa được LAB gán nhãn.
    pred = [(time, kind) for time, kind in predicted_boundaries(mask, features.edges)
            if time <= record.labels[-1].end]
    result = boundary_scores(ref, pred)
    truth, valid = speech_at(features.times, record.labels)
    valid &= features.times < record.labels[-1].end
    false_sp = np.mean(mask[valid & ~truth]) if np.any(valid & ~truth) else 0.0
    false_sil = np.mean(~mask[valid & truth]) if np.any(valid & truth) else 0.0
    result["balanced_error"] = float((false_sp + false_sil) / 2)
    return result


def estimate_snr(record: Record) -> float | None:
    powers = [[], []]
    for row in record.labels:
        data = record.samples[round(row.start * record.fs):round(row.end * record.fs)]
        powers[int(row.speech)].append(float(np.sum(data * data)))
    durations = [sum(row.end - row.start for row in record.labels if int(row.speech) == i) for i in (0, 1)]
    if not all(durations):
        return None
    sil, sp = [sum(powers[i]) / (durations[i] * record.fs) for i in (0, 1)]
    return float(10 * np.log10(max(sp - sil, 1e-12) / max(sil, 1e-12)))
