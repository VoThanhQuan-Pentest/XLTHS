"""Thuật toán của thành viên 1: học ngưỡng bằng tìm kiếm nhị phân từ STE có nhãn."""

from __future__ import annotations

import numpy as np


def binary_energy_errors(silence: np.ndarray, speech: np.ndarray, threshold: float) -> tuple[float, float]:
    """Nhận hai mảng overlap và T; trả mean năng lượng Sil vượt T và Sp thiếu so với T."""
    silence_error = float(np.maximum(silence - threshold, 0).mean())
    speech_error = float(np.maximum(threshold - speech, 0).mean())
    return silence_error, speech_error


def binary_search_details(silence: np.ndarray, speech: np.ndarray) -> dict:
    """Nhận STE hai lớp đã median; trả T, overlap và lịch sử thật của cùng bộ giải Binary."""
    # Khối 1: Kiểm tra dữ liệu đầu vào có đủ 2 lớp hay không
    if not len(silence) or not len(speech):
        raise ValueError("Thiếu khung huấn luyện cho một lớp")

    # Khối 2: Tìm khoảng chồng lấn giữa giá trị lớn nhất của Sil và nhỏ nhất của Sp
    smax, pmin = float(np.max(silence)), float(np.min(speech))
    result = {"initial_lower": pmin, "initial_upper": smax, "history": [],
              "silence_overlap": silence[(silence >= pmin) & (silence <= smax)],
              "speech_overlap": speech[(speech >= pmin) & (speech <= smax)]}
    if smax <= pmin:
        result.update(threshold=(smax + pmin) / 2,
                      stop_reason="touching_classes" if smax == pmin else "separated_classes")
        return result

    # Khối 3: Khởi tạo cận tìm kiếm nhị phân
    lo, hi = pmin, smax
    overlap_silence, overlap_speech = result["silence_overlap"], result["speech_overlap"]

    # Khối 4: Vòng lặp chia đôi khoảng tìm kiếm để cân bằng diện tích lỗi hai phía
    for iteration in range(1, 201):
        mid = (lo + hi) / 2
        # Mẫu số là số quan sát overlap của mỗi lớp, không phải số khung toàn lớp.
        silence_error, speech_error = binary_energy_errors(overlap_silence, overlap_speech, mid)
        delta = silence_error - speech_error
        result["history"].append({"iteration": iteration, "lower": lo, "upper": hi,
                                  "threshold": mid, "silence_error": silence_error,
                                  "speech_error": speech_error, "delta": delta})
        if abs(delta) <= 1e-10 or hi - lo <= 1e-10:
            result.update(threshold=float(mid), stop_reason="energy_balance" if abs(delta) <= 1e-10 else "interval_width")
            return result
        if delta > 0:
            lo = mid
        else:
            hi = mid

    # Khối 5: Chuẩn hóa ngưỡng trong khoảng an toàn [0, 1]
    result.update(threshold=float(np.clip((lo + hi) / 2, 0, 1)), stop_reason="iteration_limit")
    return result


def binary_threshold(silence: np.ndarray, speech: np.ndarray) -> float:
    """Nhận STE hai lớp từ TRAIN; trả ngưỡng overlap-only của bộ giải có ghi lại lịch sử."""
    return binary_search_details(silence, speech)["threshold"]
