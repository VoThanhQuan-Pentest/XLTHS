"""Đánh giá định lượng độ chính xác phân đoạn Speech/Silence và ước lượng SNR.

Các tiêu chí đánh giá bao gồm:
- MAE (Mean Absolute Error, tính bằng mili-giây): Sai số tuyệt đối trung bình giữa các biên.
- RMSE (Root Mean Squared Error, tính bằng mili-giây): Căn bậc hai sai số toàn phương trung bình.
- Biên đúng (matched), biên thừa (extra), biên thiếu (missed), Precision, Recall, F1-score.
- Balanced Error: Tỷ lệ lỗi phân lớp cân bằng giữa khung Speech và Silence.
- SNR: Ước lượng tỷ số tín hiệu trên nhiễu nền dựa trên các vùng Silence có nhãn.
"""

from __future__ import annotations

from functools import lru_cache
import numpy as np

from .data import Record, reference_boundaries, speech_at
from .features import Features, predicted_boundaries


def boundary_scores(reference: list[tuple[float, bool]],
                    predicted: list[tuple[float, bool]]) -> dict:
    """Ghép cặp tối ưu giữa các biên chuẩn và biên dự đoán để tính sai số MAE/RMSE.

    Sử dụng quy hoạch động để ghép các biên cùng loại (cùng bắt đầu Speech hoặc cùng bắt đầu Silence)
    theo thứ tự thời gian. Không áp dụng ngưỡng dung sai nhân tạo (như 200 ms) trong việc tính toán sai số,
    đảm bảo phản ánh trung thực độ lệch thời gian giữa thuật toán và nhãn chuẩn.

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
    # Khối 1: Quy hoạch động tìm cách ghép cặp nhiều nhất với tổng sai số nhỏ nhất
    @lru_cache(None)
    def solve(i: int, j: int) -> tuple[int, float, tuple[tuple[int, int], ...]]:
        """Ghép từ biên i/j; trả số cặp, tổng độ lệch và chỉ số các cặp tối ưu."""
        if i == len(reference) or j == len(predicted):
            return 0, 0.0, ()

        # Nhánh bỏ qua một biên ở reference hoặc predicted
        options = [solve(i + 1, j), solve(i, j + 1)]

        # Nếu cùng loại biên (cùng chiều chuyển tiếp Sp/Sil), xem xét ghép cặp
        if reference[i][1] == predicted[j][1]:
            matched_count, sum_err, sub_pairs = solve(i + 1, j + 1)
            pair_err = abs(reference[i][0] - predicted[j][0])
            options.append((matched_count + 1, sum_err + pair_err, ((i, j),) + sub_pairs))

        # Ưu tiên ghép được nhiều biên nhất, sau đó đến tổng sai số nhỏ nhất
        return max(options, key=lambda row: (row[0], -row[1]))

    # Khối 2: Thực thi hàm giải thuật và tính toán độ lệch từng cặp
    count, _, pairs = solve(0, 0)
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
        Giá trị SNR ước lượng tính bằng dB (float), hoặc None nếu thiếu nhãn một trong hai lớp.
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

    # SNR = 10 * log10(max(P_signal, eps) / P_noise)
    estimated_signal_power = max(signal_plus_noise_power - noise_power, 1e-12)
    snr_db = float(10 * np.log10(estimated_signal_power / max(noise_power, 1e-12)))

    return snr_db
