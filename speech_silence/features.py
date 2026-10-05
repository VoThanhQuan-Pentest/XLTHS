"""Trích xuất các đặc trưng âm thanh ngắn hạn phục vụ phân đoạn Speech/Silence.

Bao gồm các hàm:
- extract: Phân khung tín hiệu, tính năng lượng ngắn hạn (STE), độ lớn biên độ ngắn hạn (MA),
  logSTE (dB), logMA (dB), chuẩn hóa STE và ước lượng tần số cơ bản F0.
- estimate_f0: Ước lượng F0 trên từng khung hữu thanh bằng phương pháp tự tương quan (Autocorrelation).
- remove_virtual_silence: Áp dụng điều kiện khoảng lặng tối thiểu 200 ms để loại bỏ các khoảng lặng ảo.
- segments, predicted_boundaries: Chuyển đổi mặt nạ nhị phân khung thành các đoạn và mốc thời gian biên.

Mã nguồn được viết hoàn toàn bằng Numpy, tuân thủ quy chuẩn không dùng thư viện ngoài.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from .config import HOP_MS


@dataclass(frozen=True)
class Features:
    """Tập hợp các đặc trưng ngắn hạn trích xuất từ tín hiệu âm thanh.

    Attributes:
        times: Mốc thời gian trung tâm của từng khung (giây).
        ste: Năng lượng ngắn hạn (Short-Time Energy) thô.
        ma: Độ lớn biên độ ngắn hạn (Short-Time Magnitude).
        normalized_ste: STE đã được chuẩn hóa về dải [0, 1] theo giá trị cực đại.
        log_ste: Mức năng lượng tính theo thang logarithmic (dB).
        log_ma: Mức biên độ tính theo thang logarithmic (dB).
        f0: Tần số cơ bản F0 ước lượng theo Hz (khung vô thanh/silence nhận NaN).
        edges: Các mốc biên thời gian bắt đầu và kết thúc của các khung (giây).
    """
    times: np.ndarray
    ste: np.ndarray
    ma: np.ndarray
    normalized_ste: np.ndarray
    log_ste: np.ndarray
    log_ma: np.ndarray
    f0: np.ndarray
    edges: np.ndarray


def extract(samples: np.ndarray, fs: int, frame_ms: int, hop_ms: int = HOP_MS,
            compute_f0: bool = True) -> Features:
    """Trích xuất toàn bộ các đặc trưng ngắn hạn từ mảng mẫu âm thanh WAV.

    Chia tín hiệu thành các khung chồng lấn, tính toán STE, MA, logSTE, logMA,
    chuẩn hóa STE cực đại và tính đường F0 nếu được yêu cầu.

    Args:
        samples: Mảng 1D float chứa biên độ các mẫu tín hiệu âm thanh đã chuẩn hóa về [-1, 1].
        fs: Tần số lấy mẫu của tín hiệu (Hz), ví dụ 16000 hoặc 44100 Hz.
        frame_ms: Độ dài khung của tiện ích tổng quát; ba thuật toán luôn truyền FRAME_MS=25.
        hop_ms: Bước dịch chuyển giữa hai khung kế tiếp tính bằng mili-giây (mặc định: 10 ms).
        compute_f0: Cờ boolean cho biết có thực hiện tính F0 hay không (mặc định: True).

    Returns:
        Đối tượng Features chứa tất cả các mảng đặc trưng đã tính toán.
    """
    # Khối 1: Quy đổi độ dài khung và bước dịch từ mili-giây sang số lượng mẫu
    frame_len = max(1, round(fs * frame_ms / 1000))
    hop_len = max(1, round(fs * hop_ms / 1000))
    if len(samples) == 0:
        raise ValueError("Tín hiệu WAV rỗng, không thể trích xuất đặc trưng")

    # Khối 2: Đệm zero cho phần đuôi và chia khung bằng sliding window
    starts = np.arange(0, len(samples), hop_len)
    padded = np.pad(samples, (0, frame_len))
    frames = np.lib.stride_tricks.sliding_window_view(padded, frame_len)[starts]

    # Khối 3: Tính toán Short-Time Energy (STE) và Short-Time Magnitude (MA)
    # STE = (1/N) * sum(x[n]^2); MA = (1/N) * sum(|x[n]|)
    ste = np.mean(frames * frames, axis=1)
    ma = np.mean(np.abs(frames), axis=1)

    # Khối 4: Chuẩn hóa STE về khoảng [0, 1] theo giá trị cực đại của bản ghi
    max_ste = float(np.max(ste))
    normalized_ste = ste / max_ste if max_ste > 0 else np.zeros_like(ste)

    # Khối 5: Ước lượng tần số cơ bản F0 và các đặc trưng logarit (dB)
    f0 = estimate_f0(frames, fs, normalized_ste) if compute_f0 else np.full(len(frames), np.nan)
    log_ste = 10 * np.log10(np.maximum(ste, 1e-12))
    log_ma = 20 * np.log10(np.maximum(ma, 1e-12))

    # Khối 6: Xác định mốc thời gian trung tâm và các mốc biên khung
    edges = np.r_[starts / fs, len(samples) / fs]
    times = (starts + np.minimum(frame_len, len(samples) - starts) / 2) / fs

    return Features(times, ste, ma, normalized_ste, log_ste, log_ma, f0, edges)


def estimate_f0(frames: np.ndarray, fs: int, normalized_ste: np.ndarray,
                minimum_hz: float = 60.0, maximum_hz: float = 400.0) -> np.ndarray:
    """Ước lượng đường tần số cơ bản F0 qua hàm tự tương quan ngắn hạn (Autocorrelation).

    Chỉ tính toán F0 cho các khung có năng lượng đủ lớn (nghi ngờ hữu thanh);
    các khung khoảng lặng hoặc âm vô thanh sẽ nhận giá trị NaN.

    Args:
        frames: Mảng 2D kích thước (số khung, độ dài khung) chứa các mẫu tín hiệu từng khung.
        fs: Tần số lấy mẫu (Hz).
        normalized_ste: Mảng 1D normalized STE tương ứng của từng khung.
        minimum_hz: Giới hạn tần số cơ bản dưới (Hz, mặc định 60 Hz).
        maximum_hz: Giới hạn tần số cơ bản trên (Hz, mặc định 400 Hz).

    Returns:
        Mảng 1D float cùng chiều dài với số khung, chứa F0 ước lượng (Hz) hoặc NaN.
    """
    # Khối 1: Xác định khoảng trễ (lag) tìm kiếm tương ứng dải tần số F0
    min_lag = max(1, int(fs / maximum_hz))
    max_lag = min(frames.shape[1] - 1, int(fs / minimum_hz))
    result = np.full(len(frames), np.nan)
    window = np.hamming(frames.shape[1])

    # Khối 2: Duyệt qua từng khung tín hiệu để tính hàm tự tương quan
    for index, frame in enumerate(frames):
        # Bỏ qua các khung có năng lượng quá thấp (tiếng ồn nền hoặc khoảng lặng)
        if normalized_ste[index] < 0.01:
            continue

        # Cân bằng mức DC và nhân cửa sổ Hamming để giảm hiện tượng rò rỉ phổ
        centered = (frame - np.mean(frame)) * window

        # Khối 3: Tính nhanh hàm tự tương quan ngắn hạn thông qua FFT và IFFT
        fft_size = 1 << (2 * len(centered) - 1).bit_length()
        spectrum = np.fft.rfft(centered, n=fft_size)
        correlation = np.fft.irfft(spectrum * np.conj(spectrum), n=fft_size)[:len(centered)]

        # Khối 4: Tìm đỉnh tương quan cực đại trong dải trễ [min_lag, max_lag]
        if correlation[0] <= 1e-12:
            continue
        search_region = correlation[min_lag:max_lag + 1]
        best_lag = min_lag + int(np.argmax(search_region))

        # Khối 5: Kiểm tra tỷ số tương quan chuẩn hóa (nếu >= 0.30 mới xác nhận là hữu thanh)
        if correlation[best_lag] / correlation[0] >= 0.30:
            result[index] = fs / best_lag

    return result


def remove_virtual_silence(mask: np.ndarray, edges: np.ndarray, minimum_s: float = 0.2) -> np.ndarray:
    """Loại bỏ các khoảng lặng ảo có độ dài ngắn hơn ngưỡng quy định (200 ms).

    Theo yêu cầu đề bài: độ dài tối thiểu của một khoảng lặng thực sự là 200 ms.
    Nếu một đoạn Silence có thời lượng < 200 ms (ví dụ: các khoảng đóng thanh môn ngắn),
    thuật toán sẽ tự động gộp đoạn đó vào phân đoạn tiếng nói (Speech).

    Args:
        mask: Mảng boolean phân lớp ban đầu của từng khung (True: Speech, False: Silence).
        edges: Mảng mốc thời gian biên của các khung (giây).
        minimum_s: Thời lượng khoảng lặng tối thiểu tính bằng giây (mặc định: 0.2 s = 200 ms).

    Returns:
        Mảng boolean mask mới sau khi đã loại bỏ toàn bộ khoảng lặng ảo ngắn hạn.
    """
    # Khối 1: Khởi tạo mảng kết quả và tìm vị trí các điểm chuyển đổi trạng thái Silence
    cleaned_mask = mask.copy()
    is_silence = ~cleaned_mask
    change_indices = np.flatnonzero(np.diff(np.r_[False, is_silence, False]))

    # Khối 2: Duyệt từng đoạn Silence liên tục và đo độ dài thời gian thực tế
    for start_idx, end_idx in change_indices.reshape(-1, 2):
        duration = edges[end_idx] - edges[start_idx]
        # Nếu khoảng lặng ngắn hơn 200 ms, chuyển thành Speech (True)
        if duration < minimum_s - 1e-12:
            cleaned_mask[start_idx:end_idx] = True

    return cleaned_mask


def segments(mask: np.ndarray, edges: np.ndarray) -> list[tuple[float, float, bool]]:
    """Phân rã mảng mask phân lớp thành danh sách các đoạn thời gian liên tục.

    Args:
        mask: Mảng boolean phân lớp của từng khung (True: Speech, False: Silence).
        edges: Mảng mốc thời gian biên của các khung (giây).

    Returns:
        Danh sách các bộ (thời_điểm_bắt_đầu, thời_điểm_kết_thúc, là_speech).
    """
    # Khối 1: Tìm các vị trí thay đổi nhãn phân lớp giữa các khung kế tiếp
    change_points = np.r_[0, np.flatnonzero(np.diff(mask)) + 1, len(mask)]

    # Khối 2: Tạo các khoảng thời gian bắt đầu - kết thúc tương ứng
    segment_list = [
        (float(edges[start]), float(edges[end]), bool(mask[start]))
        for start, end in zip(change_points, change_points[1:])
    ]
    return segment_list


def predicted_boundaries(mask: np.ndarray, edges: np.ndarray) -> list[tuple[float, bool]]:
    """Trích xuất các mốc biên thời gian chuyển đổi giữa Speech và Silence từ kết quả dự đoán.

    Args:
        mask: Mảng boolean phân lớp của từng khung.
        edges: Mảng mốc thời gian biên của các khung (giây).

    Returns:
        Danh sách các bộ (thời_điểm_biên_s, bắt_đầu_speech_bool).
    """
    # Khối 1: Tìm các điểm nhảy nhãn (chuyển tiếp giữa 0 -> 1 hoặc 1 -> 0)
    boundary_indices = np.flatnonzero(np.diff(mask)) + 1

    # Khối 2: Lấy mốc thời gian chính xác tại biên và trạng thái chuyển tiếp
    boundary_list = [(float(edges[idx]), bool(mask[idx])) for idx in boundary_indices]
    return boundary_list
