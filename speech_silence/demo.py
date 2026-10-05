"""Vẽ một figure cho mỗi WAV và viết bình luận riêng từ kết quả thực nghiệm."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .data import Record, reference_boundaries, speech_at
from .features import Features, predicted_boundaries, segments
from .config import FRAME_MS, HOP_MS


def format_metric(value: float | None) -> str:
    """Nhận sai số value theo ms; trả chuỗi một số lẻ hoặc 'KXĐ' nếu thiếu cặp biên."""
    return "KXĐ" if value is None else f"{value:.1f}"


def plot_demo(record: Record, results: dict, labels: dict, path: Path, number: int) -> plt.Figure:
    """Vẽ toàn bộ phương pháp cho một WAV trên một figure.

    Args:
        record: WAV kiểm thử và nhãn chuẩn để vẽ biên đỏ.
        results: Mỗi phương pháp chứa features, mask, threshold, metrics và fallback.
        labels: Tên tiếng Việt của các phương pháp.
        path: Đường dẫn PNG đầu ra.
        number: Số cửa sổ figure, từ 1 đến 4.
    Returns:
        Figure có waveform, kết quả từng phương pháp, logSTE/logMA và F0.
    """
    # Khối 1: Chia bố cục thành waveform, ba phương pháp và hai đặc trưng chung.
    fig = plt.figure(num=number, figsize=(10, 5.5), layout="constrained")
    grid = fig.add_gridspec(3, 6, height_ratios=(0.8, 1, 0.9))
    waveform = fig.add_subplot(grid[0, :])
    logaxis = fig.add_subplot(grid[2, :3])
    f0axis = fig.add_subplot(grid[2, 3:])
    first = next(iter(results.values()))["features"]

    # Khối 2: Giữ màu biên và các đơn vị nhất quán giữa bốn cửa sổ.
    waveform.plot(np.arange(len(record.samples)) / record.fs, record.samples, color="0.3", lw=0.45)
    waveform.set(title=f"{record.name}.wav — Dạng sóng và biên chuẩn", ylabel="Biên độ")
    for index, (time, _) in enumerate(reference_boundaries(record.labels)):
        waveform.axvline(time, color="red", ls="--", lw=1,
                         label="Biên chuẩn" if index == 0 else None)
    for method_index, (method, result) in enumerate(results.items()):
        for index, (time, _) in enumerate(predicted_boundaries(result["mask"], result["features"].edges)):
            waveform.axvline(time, color="blue", ls=("-", "-.", ":")[method_index], lw=1,
                            label=f"Biên dự đoán ({labels[method]})" if index == 0 else None)
    waveform.legend(fontsize=7, loc="upper right")

    # Khối 3: Mỗi phương pháp có STE, ngưỡng và hai loại biên trên một trục riêng.
    width = 6 // len(results)
    for index, (method, result) in enumerate(results.items()):
        axis = fig.add_subplot(grid[1, index * width:(index + 1) * width])
        feature, mask = result["features"], result["mask"]
        metric = result["metrics"]
        axis.plot(feature.times, feature.normalized_ste, color="0.65", lw=0.7, label="STE trước lọc")
        decision = feature.decision_ste if feature.decision_ste is not None else feature.normalized_ste
        axis.plot(feature.times, decision, color="#185a8d", lw=0.9,
                  label="Median so ngưỡng" if method == "binary" else "STE so ngưỡng")
        axis.legend(fontsize=6, loc="upper left")
        axis.axhline(result["threshold"], color="#e69f00", ls=":", lw=1)

        # Khối 4: Tô Speech và vẽ biên xanh/đỏ mà không trộn ba thuật toán với nhau.
        for left, right, speech in segments(mask, feature.edges):
            if speech:
                axis.axvspan(left, right, color="#b7dfc0", alpha=0.3)
        for time, _ in predicted_boundaries(mask, feature.edges):
            axis.axvline(time, color="blue", lw=1)
        for time, _ in reference_boundaries(record.labels):
            axis.axvline(time, color="red", ls="--", lw=1)

        # Khối 5: Đặt sai số cùng số biên ghép/thừa/thiếu ngay trên đồ thị tương ứng.
        axis.set_title(f'{labels[method]}\nMAE {format_metric(metric["mae_ms"])} ms; '
                       f'ghép/thừa/thiếu {metric["matched"]}/{metric["extra"]}/{metric["missed"]}', fontsize=8)
        axis.set_ylabel("STE chuẩn hóa", fontsize=8)
        axis.text(0.98, 0.95, f'T={result["threshold"]:.5f}', transform=axis.transAxes,
                  ha="right", va="top", fontsize=7)

    # Khối 6: Cả ba phương pháp cùng khung danh định; tránh suy ngược từ khung cuối ngắn.
    frame_ms = FRAME_MS
    logaxis.plot(first.times, first.log_ste, color="#6f42a2", lw=0.8, label="logSTE")
    logaxis.plot(first.times, first.log_ma, color="#009e73", lw=0.8, label="logMA")
    logaxis.set(title=f"Đặc trưng log ({frame_ms:.0f} ms)", ylabel="Mức (dB)")
    logaxis.legend(fontsize=7, loc="upper right")
    f0axis.plot(first.times, first.f0, color="#d55e00", lw=0.8, marker=".", ms=1.5, label="F0 ước lượng")

    # Khối 7: F0mean LAB là thống kê tham chiếu, không phải đường F0 chuẩn từng khung.
    if record.reference_f0_mean is not None:
        f0axis.axhline(record.reference_f0_mean, color="0.4", ls="--", lw=0.8, label="F0mean LAB")
    f0axis.set(title=f"F0 tự tương quan ({frame_ms:.0f} ms)", ylabel="F0 (Hz)", ylim=(50, 420))
    f0axis.legend(fontsize=7, loc="upper right")
    fig.suptitle("Xanh: biên dự đoán · Đỏ nét đứt: biên chuẩn · Nền xanh nhạt: Speech", fontsize=8)

    # Khối 8: Mọi plot có trục thời gian và tiêu đề, lưu đúng một ảnh cho WAV này.
    for axis in fig.axes:
        axis.set_xlim(0, record.duration)
        axis.set_xlabel("Thời gian (giây)", fontsize=8)
        axis.tick_params(labelsize=7)
        axis.grid(alpha=0.15)
    fig.savefig(path, dpi=160)
    return fig


def figure_comments(record: Record, results: dict, labels: dict) -> list[str]:
    """Nhận bản ghi/kết quả/tên phương pháp; trả các dòng Markdown bình luận một figure."""
    # Khối 1: Gắn bình luận với đúng WAV và PNG, mô tả các panel chung.
    lines = [f"## {record.name}.png", "",
             f"Phân khung cố định {FRAME_MS} ms, bước dịch {HOP_MS} ms.",
             "Cửa sổ căn giữa ô quyết định 10 ms; mép WAV chỉ dùng mẫu thật.",
             "Hình gồm waveform, STE trước/sau median nếu có, ngưỡng/biên, logSTE/logMA và F0.",
             "Đường xanh là biên dự đoán, đường đỏ nét đứt là biên chuẩn. Các chỉ số tính bằng ms.", ""]
    for method, result in results.items():
        metric = result["metrics"]
        lines.extend([f"### {labels[method]}", "",
                      f'Ngưỡng {result["threshold"]:.6f}; MAE/RMSE '
                      f'{format_metric(metric["mae_ms"])}/{format_metric(metric["rmse_ms"])} ms. '
                      f'Biên ghép/thừa/thiếu: {metric["matched"]}/{metric["extra"]}/{metric["missed"]}.'])

        # Khối 2: Bình luận hướng và vị trí sai lệch từ các cặp biên thực tế.
        details = metric["boundary_details"]
        for item in details:
            kind = "Bắt đầu Speech" if item["starts_speech"] else "Kết thúc Speech"
            lines.append(f'- {kind}: chuẩn {item["reference_s"]:.2f} s, '
                         f'dự đoán {item["predicted_s"]:.2f} s; lệch {item["error_ms"]:+.0f} ms.')
        maximum = max((round(abs(item["error_ms"]), 6) for item in details), default=None)
        assessment = ("Không có biên ghép nên chưa thể tính MAE/RMSE" if maximum is None else
                      "Sai lệch nhỏ (tối đa 30 ms)" if maximum <= 30 else
                      "Sai lệch thấy rõ (trên 30 đến 100 ms)" if maximum <= 100 else
                      "Sai lệch lớn (trên 100 ms)")
        lines.append(f"- {assessment}. Các mức này chỉ phục vụ bình luận, không dùng làm dung sai ghép biên.")

        # Khối 3: Phân biệt cắt Speech giả với phát hiện Speech giả trong vùng nền.
        paired = {round(item["predicted_s"], 8) for item in details}
        for time, kind in predicted_boundaries(result["mask"], result["features"].edges):
            if time > record.labels[-1].end or round(time, 8) in paired:
                continue
            truth, _ = speech_at(np.array([time]), record.labels)
            where = "trong Speech chuẩn" if truth[0] else "trong Silence chuẩn"
            cause = ("vùng Speech năng lượng thấp rơi dưới ngưỡng, tạo khoảng lặng giả hoặc biên trở lại Speech"
                     if truth[0] else "năng lượng nền vượt ngưỡng, tạo Speech giả hoặc biên kết thúc đoạn giả")
            lines.append(f'- Biên thừa {time:.2f} s ({"sang Speech" if kind else "sang Silence"}, {where}): '
                         f"phù hợp với {cause}.")

        # Khối 4: Nêu nguyên nhân khả dĩ và các biên thiếu mà không khẳng định quá mức.
        if maximum and maximum > 0:
            lines.append("- Biên lệch phù hợp với năng lượng tăng/giảm quanh ngưỡng và khung chồng lấn. "
                         "Đây là diễn giải từ đồ thị STE, chưa chứng minh được một nguyên nhân duy nhất.")
        if metric["missed"]:
            lines.append(f'- Thiếu {metric["missed"]} biên: không có chuyển tiếp dự đoán cùng loại để ghép đủ.')
        if result["fallback"]:
            lines.append("- Histogram thiếu hai đỉnh nên dùng mean normalized STE của chính WAV này.")
        lines.append("")

    # Khối 5: F0 hữu thanh được ước lượng độc lập với LAB, không có F0 chuẩn theo thời gian.
    feature = next(iter(results.values()))["features"]
    voiced = feature.f0[np.isfinite(feature.f0)]
    if len(voiced):
        lines.append(f"F0 ước lượng: trung vị {np.median(voiced):.1f} Hz. "
                     f"F0mean LAB tham chiếu: {record.reference_f0_mean} Hz.")
    lines.extend(["Khoảng trống F0 biểu thị khung không đạt điều kiện năng lượng/tương quan. "
                  "Không thể khẳng định tất cả đều là vô thanh; đỉnh nhọn có thể do nhầm họa âm.", ""])
    return lines
