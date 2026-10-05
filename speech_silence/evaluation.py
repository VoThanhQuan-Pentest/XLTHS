"""Đánh giá định lượng độ chính xác phân đoạn Speech/Silence và ước lượng SNR.

Các tiêu chí đánh giá bao gồm:
- MAE (Mean Absolute Error, tính bằng mili-giây): Sai số tuyệt đối trung bình giữa các biên.
- RMSE (Root Mean Squared Error, tính bằng mili-giây): Căn bậc hai sai số toàn phương trung bình.
- Biên đúng (matched), biên thừa (extra), biên thiếu (missed), Precision, Recall, F1-score.
- Balanced Error: Tỷ lệ lỗi phân lớp cân bằng giữa khung Speech và Silence.
- SNR: Ước lượng tỷ số tín hiệu trên nhiễu nền dựa trên các vùng Silence có nhãn.
"""

from __future__ import annotations

import numpy as np

from .data import Record, reference_boundaries, speech_at
from .features import Features, predicted_boundaries


def boundary_scores(reference: list[tuple[float, bool]],
                    predicted: list[tuple[float, bool]]) -> dict:
    """Ghép greedy các cặp biên cùng hướng, gần nhất trước, để tính MAE/RMSE theo BT1.

    Mỗi biên chỉ được dùng một lần. Khi khoảng cách hòa, ưu tiên biên chuẩn rồi
    biên dự đoán xuất hiện sớm hơn. Không áp dụng cutoff 100/200 ms khi ghép.

    Args:
        reference: Danh sách các biên chuẩn Ground Truth dạng (thời_điểm_s, bắt_đầu_speech_bool).
        predicted: Danh sách các biên dự đoán dạng (thời_điểm_s, bắt_đầu_speech_bool).

    Returns:
        Từ điển chứa các chỉ số đánh giá:
            - matched: Số lượng biên ghép đúng cặp.
            - missed: Số lượng biên chuẩn bị bỏ sót.
            - extra: Số lượng biên thuật toán dự đoán thừa.
            - mae_ms: Sai số tuyệt đối trung bình giữa các biên ghép cặp (ms).
            - rmse_ms: Căn bậc hai sai số bình phương trung bình (ms).
            - precision, recall, f1: Độ chuẩn xác, độ phủ và F1-score.
            - boundary_details: Danh sách chi tiết từng cặp biên được ghép kèm độ lệch ms.
    """
    # Khối 1: Liệt kê các cặp hợp lệ và sắp theo khoảng cách, thời gian và chỉ số.
    candidates = sorted(
        (abs(p[0] - r[0]), r[0], p[0], i, j)
        for i, r in enumerate(reference) for j, p in enumerate(predicted)
        if r[1] == p[1]
    )
    used_reference, used_predicted, pairs = set(), set(), []
    for _, _, _, i, j in candidates:
        if i not in used_reference and j not in used_predicted:
            used_reference.add(i)
            used_predicted.add(j)
            pairs.append((i, j))

    # Khối 2: Đưa cặp đã ghép về thứ tự biên chuẩn để trình bày và tính sai lệch.
    pairs.sort(key=lambda pair: (reference[pair[0]][0], predicted[pair[1]][0]))
    count = len(pairs)
    errors = np.array([(predicted[j][0] - reference[i][0]) * 1000 for i, j in pairs])
    details = [
        {
            "reference_s": reference[i][0],
            "predicted_s": predicted[j][0],
            "starts_speech": reference[i][1],
            "error_ms": float((predicted[j][0] - reference[i][0]) * 1000)
        }
        for i, j in pairs
    ]

    # Khối 3: Đóng gói và tính toán các chỉ số thống kê
    return {
        "matched": count,
        "missed": len(reference) - count,
        "extra": len(predicted) - count,
        "mae_ms": float(np.mean(abs(errors))) if count else None,
        "rmse_ms": float(np.sqrt(np.mean(errors ** 2))) if count else None,
        "precision": count / len(predicted) if predicted else (1.0 if not reference else 0.0),
        "recall": count / len(reference) if reference else 1.0,
        "f1": 2 * count / (len(reference) + len(predicted)) if reference or predicted else 1.0,
        "boundary_details": details
    }


def summarize_scores(rows: list[dict]) -> dict:
    """Nhận metric từng WAV; trả mean-file và pooled MAE/RMSE riêng, cùng số biên lỗi."""
    # Khối 1: Mean-file không coi file chưa có cặp ghép là sai số zero.
    valid = [row for row in rows if row["mae_ms"] is not None and row["rmse_ms"] is not None]
    complete = bool(rows) and len(valid) == len(rows)
    count = sum(row["matched"] for row in rows)
    result = {"files": len(rows), "files_with_matched_boundaries": len(valid),
              "matched": count, "extra": sum(r["extra"] for r in rows),
              "missed": sum(r["missed"] for r in rows),
              "mean_file_mae_ms": float(np.mean([r["mae_ms"] for r in valid])) if complete else None,
              "mean_file_rmse_ms": float(np.mean([r["rmse_ms"] for r in valid])) if complete else None}

    # Khối 2: Pooled dùng số cặp làm trọng số và căn sau khi gộp bình phương lỗi.
    result["pooled_mae_ms"] = sum(r["mae_ms"] * r["matched"] for r in valid) / count if count else None
    result["pooled_rmse_ms"] = float(np.sqrt(sum(r["rmse_ms"] ** 2 * r["matched"] for r in valid) / count)) if count else None
    return result


def score(record: Record, features: Features, mask: np.ndarray) -> dict:
    """Đánh giá toàn diện kết quả phân đoạn của một bản ghi âm thanh.

    Tính toán đồng thời cả sai số vị trí biên (MAE/RMSE) và tỷ lệ lỗi phân loại khung (Frame-level Balanced Error).

    Args:
        record: Đối tượng Record chứa dữ liệu âm thanh và nhãn chuẩn.
        features: Đối tượng Features chứa các đặc trưng ngắn hạn đã tính.
        mask: Mảng boolean phân lớp dự đoán của các khung (True: Speech, False: Silence).

    Returns:
        Từ điển chứa tất cả các chỉ số sai số biên cùng balanced_error.
    """
    # Khối 1: Lấy danh sách biên chuẩn và biên dự đoán trong phạm vi có nhãn
    ref_boundaries = reference_boundaries(record.labels)
    valid_end_time = record.labels[-1].end
    pred_boundaries = [
        (time, kind) for time, kind in predicted_boundaries(mask, features.edges)
        if time <= valid_end_time
    ]

    # Khối 2: Tính toán các chỉ số sai lệch vị trí biên
    eval_result = boundary_scores(ref_boundaries, pred_boundaries)

    # Khối 3: Đánh giá tỷ lệ lỗi phân loại ở cấp độ khung (Frame-level)
    truth_speech, in_range = speech_at(features.times, record.labels)
    in_range &= features.times < valid_end_time

    # Tỷ lệ nhầm Silence thành Speech (False Alarm) và Speech thành Silence (Miss)
    false_speech_rate = np.mean(mask[in_range & ~truth_speech]) if np.any(in_range & ~truth_speech) else 0.0
    false_silence_rate = np.mean(~mask[in_range & truth_speech]) if np.any(in_range & truth_speech) else 0.0

    eval_result["balanced_error"] = float((false_speech_rate + false_silence_rate) / 2.0)
    return eval_result


def estimate_snr(record: Record) -> float | None:
    """Ước lượng tỷ số tín hiệu trên nhiễu (SNR) của môi trường thu âm tính theo dB.

    Tính công suất trung bình trong vùng tiếng nói và công suất nhiễu trong vùng khoảng lặng có nhãn.

    Args:
        record: Đối tượng Record chứa mẫu tín hiệu và các đoạn nhãn chuẩn.

    Returns:
        SNR theo dB, hoặc None nếu thiếu lớp/công suất không tạo được tỷ số hợp lệ.
    """
    # Khối 1: Tách và tích lũy năng lượng của từng vùng Speech và Silence
    class_energies = [[], []]
    for interval in record.labels:
        segment_samples = record.samples[round(interval.start * record.fs):round(interval.end * record.fs)]
        class_energies[int(interval.speech)].append(float(np.sum(segment_samples * segment_samples)))

    # Khối 2: Tính tổng thời lượng của từng lớp
    total_durations = [
        sum(interval.end - interval.start for interval in record.labels if int(interval.speech) == class_id)
        for class_id in (0, 1)
    ]
    if not all(total_durations):
        return None

    # Khối 3: Tính công suất trung bình (Power = Năng lượng / Số mẫu)
    noise_power = sum(class_energies[0]) / (total_durations[0] * record.fs)
    signal_plus_noise_power = sum(class_energies[1]) / (total_durations[1] * record.fs)

    # Khối 3b: Không dùng floor để tạo SNR hữu hạn cho zero-audio hoặc P_signal <= 0.
    if noise_power <= 0 or signal_plus_noise_power <= noise_power:
        return None
    estimated_signal_power = signal_plus_noise_power - noise_power
    snr_db = float(10 * np.log10(estimated_signal_power / noise_power))

    return snr_db
