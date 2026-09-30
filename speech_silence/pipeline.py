"""Quy trình huấn luyện, dự đoán, đánh giá và trực quan hóa phân đoạn Speech/Silence.

Quy trình hoạt động:
1. Huấn luyện (Training): Chỉ sử dụng dữ liệu từ thư mục 'TinHieuHuanLuyen' để khảo sát
   phân bố năng lượng, tìm ngưỡng tối ưu cho 3 phương pháp (Binary, Histogram, Gaussian).
2. Kiểm thử (Testing): Khóa cố định bộ tham số, chạy dự đoán trên 4 tệp trong 'TinHieuKiemThu'.
3. Trực quan hóa (Demo): Xuất 4 Figure cho 4 tệp kiểm thử, tự động sắp xếp trên 4 góc màn hình,
   đảm bảo mỗi plot có title và axis label riêng biệt.
4. Đánh giá (Evaluation): Tính toán MAE, RMSE, biên đúng/thừa/thiếu và khảo sát khả năng kháng nhiễu.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json

import matplotlib.pyplot as plt
import numpy as np

from .algorithms import HistogramConfig, binary_threshold, gaussian_threshold, histogram_threshold
from .data import Record, discover, read_record, speech_at, reference_boundaries
from .evaluation import score, estimate_snr
from .features import Features, extract, remove_virtual_silence, predicted_boundaries, segments
from .demo import plot_demo, figure_comments

METHODS = ("binary", "histogram", "statistical")
METHOD_LABELS = {
    "binary": "Tìm kiếm nhị phân",
    "histogram": "Histogram",
    "statistical": "Thống kê Gaussian"
}


def training_arrays(records: list[Record], frame_ms: int) -> tuple[np.ndarray, np.ndarray]:
    """Trích xuất và gộp mảng normalized STE của hai lớp Silence và Speech từ tập huấn luyện.

    Args:
        records: Danh sách các đối tượng Record của tập huấn luyện.
        frame_ms: Độ dài khung tính theo mili-giây (ví dụ: 20 ms, 30 ms).

    Returns:
        tuple gồm (silence_ste, speech_ste) dưới dạng mảng 1D numpy float.
    """
    # Khối 1: Khởi tạo danh sách chứa các giá trị năng lượng của từng lớp
    silence_values: list[float] = []
    speech_values: list[float] = []

    # Khối 2: Duyệt qua từng bản ghi huấn luyện và trích xuất đặc trưng
    for record in records:
        features = extract(record.samples, record.fs, frame_ms, compute_f0=False)
        truth, valid = speech_at(features.times, record.labels)
        # Phân tách khung Silence (valid & ~truth) và Speech (valid & truth)
        silence_values.extend(features.normalized_ste[valid & ~truth])
        speech_values.extend(features.normalized_ste[valid & truth])

    return np.asarray(silence_values), np.asarray(speech_values)


def fit(records: list[Record], frame_ms: int, histogram: HistogramConfig,
        method: str | None = None) -> dict:
    """Xác định bộ tham số và các ngưỡng phân đoạn tối ưu từ dữ liệu huấn luyện.

    Args:
        records: Danh sách Record thuộc tập huấn luyện.
        frame_ms: Độ dài khung (ms).
        histogram: Cấu hình tham số HistogramConfig.
        method: Thuật toán cần huấn luyện; None huấn luyện cả ba.

    Returns:
        Từ điển chứa bộ mô hình huấn luyện (ngưỡng nhị phân, ngưỡng Gaussian, ngưỡng dự phòng).
    """
    # Khối 1: Trích xuất mảng năng lượng hai lớp từ tập huấn luyện
    sil, sp = training_arrays(records, frame_ms)
    if not len(sil) or not len(sp):
        raise ValueError("Dữ liệu huấn luyện thiếu một trong hai lớp Speech hoặc Silence")

    # Khối 2: Đóng gói cấu hình chung, chỉ tính thuật toán đang được chọn để demo.
    model = {
        "frame_ms": frame_ms,
        "hop_ms": 10,
        "minimum_silence_ms": 200,
    }
    if method is None or method == "binary":
        model["binary_threshold"] = binary_threshold(sil, sp)
    if method is None or method == "statistical":
        model["statistical_threshold"], model["statistics"] = gaussian_threshold(sil, sp)

    # Khối 3: Chỉ Histogram cần cấu hình và ngưỡng dự phòng từ tập huấn luyện.
    if method is None or method == "histogram":
        fallback_th = float(np.clip((np.median(sil) + np.median(sp)) / 2.0, 0.0, 1.0))
        try:
            fallback_th, _ = histogram_threshold(np.concatenate([sil, sp]), histogram)
        except ValueError:
            pass
        model.update(histogram=asdict(histogram), histogram_fallback=fallback_th)
    return model


def predict(samples: np.ndarray, fs: int, model: dict, method: str,
            compute_f0: bool = True) -> tuple[Features, np.ndarray, float, bool]:
    """Thực hiện phân đoạn Speech/Silence trên một tín hiệu âm thanh kiểm thử.

    Hàm áp dụng ngưỡng tương ứng của thuật toán được chọn, sau đó lọc bỏ
    khoảng lặng ảo có độ dài < 200 ms theo quy định đề tài.

    Args:
        samples: Mảng mẫu âm thanh của tệp WAV kiểm thử.
        fs: Tần số lấy mẫu (Hz).
        model: Từ điển tham số mô hình đã được huấn luyện.
        method: Tên thuật toán cần dùng ('binary', 'histogram', hoặc 'statistical').
        compute_f0: Cho biết có tính đường F0 hay không (mặc định True).

    Returns:
        tuple gồm (features, mask, threshold, fallback_used).
    """
    # Khối 1: Kiểm tra tính hợp lệ của phương pháp và trích xuất đặc trưng
    if method not in METHODS:
        raise ValueError(f"Thuật toán không hợp lệ: {method}")

    features = extract(samples, fs, model["frame_ms"], model["hop_ms"], compute_f0=compute_f0)
    fallback_used = False

    # Khối 2: Lấy giá trị ngưỡng tương ứng với từng thuật toán
    if method == "binary":
        threshold = model["binary_threshold"]
    elif method == "statistical":
        threshold = model["statistical_threshold"]
    else:
        # Histogram tính ngưỡng thích nghi trực tiếp trên tín hiệu kiểm thử
        threshold, fallback_used = histogram_threshold(
            features.normalized_ste,
            HistogramConfig(**model["histogram"]),
            model["histogram_fallback"]
        )

    # Khối 3: Phân đoạn ban đầu và loại bỏ khoảng lặng ảo dưới 200 ms
    raw_mask = features.normalized_ste >= threshold
    mask = remove_virtual_silence(raw_mask, features.edges, model["minimum_silence_ms"] / 1000.0)

    return features, mask, float(threshold), fallback_used


def choose(records: list[Record], only: str | None = None) -> tuple[dict, dict]:
    """Tìm kiếm siêu tham số tối ưu (frame_ms, cấu hình histogram) bằng phương pháp Cross-Validation.

    Args:
        records: Danh sách các Record trong tập huấn luyện.
        only: Thuật toán của sinh viên, hoặc None để so sánh cả ba.

    Returns:
        tuple gồm (models, validation_metrics) chỉ cho thuật toán được chọn, hoặc cả ba khi only=None.
    """
    # Khối 1: Định nghĩa không gian tìm kiếm siêu tham số
    configs = {
        "binary": [(f, HistogramConfig()) for f in (20, 25, 30)],
        "statistical": [(f, HistogramConfig()) for f in (20, 25, 30)],
        "histogram": [(f, HistogramConfig(b, s, w))
                      for f in (20, 25, 30)
                      for b in (32, 64, 128)
                      for s in (1, 3, 5)
                      for w in (2, 5, 10)]
    }

    # Lưu ứng viên tốt nhất riêng cho từng thuật toán, không dùng dữ liệu kiểm thử.
    selected: dict[str, tuple[int, HistogramConfig]] = {}
    validation: dict[str, dict] = {}

    # Khối 2: Đánh giá Leave-One-Out trên từng ứng viên tham số
    methods = (only,) if only else METHODS
    for method in methods:
        candidates = configs[method]
        best_score = None
        for frame_ms, hist in candidates:
            scores = []
            for held_idx in range(len(records)):
                train_subset = [r for i, r in enumerate(records) if i != held_idx]
                val_record = records[held_idx]
                fitted_model = fit(train_subset, frame_ms, hist, method=method)
                feat, msk, _, _ = predict(val_record.samples, val_record.fs, fitted_model, method, compute_f0=False)
                scores.append(score(val_record, feat, msk))

            # Khóa tối ưu: ưu tiên balanced_error, số biên lỗi, và MAE trung bình
            key = (
                round(float(np.mean([s["balanced_error"] for s in scores])), 10),
                sum(s["missed"] + s["extra"] for s in scores),
                np.mean([s["mae_ms"] if s["mae_ms"] is not None else 200 for s in scores]),
                frame_ms, hist.bins, hist.smooth, hist.weight
            )

            if best_score is None or key < best_score:
                best_score = key
                selected[method] = (frame_ms, hist)
                validation[method] = {
                    "balanced_error": key[0],
                    "boundary_misses": key[1],
                    "mean_mae_ms": float(key[2])
                }

    # Khối 3: Huấn luyện lại trên toàn bộ tập dữ liệu huấn luyện với tham số tốt nhất
    models = {method: fit(records, *selected[method], method=method) for method in methods}
    return models, validation


def plot_result(record: Record, method: str, features: Features, mask: np.ndarray,
                threshold: float, metrics: dict, path: Path | None = None,
                fig_num: int | None = None) -> plt.Figure:
    """Tạo Figure hiển thị kết quả trung gian và kết quả cuối cùng cho 1 tệp tín hiệu.

    Figure gồm 4 subplot được định dạng đầy đủ tiêu đề (title) và nhãn trục (axis labels):
    1. Tín hiệu dạng sóng (WAV) & Các đường kẻ dọc biên chuẩn (đỏ) và biên dự đoán (xanh).
    2. Năng lượng ngắn hạn (Normalized STE), đường ngưỡng nằm ngang và vùng Speech phát hiện.
    3. Mức năng lượng logSTE (dB) và logMA (dB).
    4. Đường tần số cơ bản F0 ước lượng và F0mean chuẩn đọc từ tệp LAB.

    Args:
        record: Đối tượng Record của tệp âm thanh kiểm thử.
        method: Tên thuật toán sử dụng.
        features: Đối tượng Features chứa các đặc trưng ngắn hạn.
        mask: Mảng boolean phân đoạn kết quả.
        threshold: Ngưỡng năng lượng phân đoạn được áp dụng.
        metrics: Từ điển các chỉ số đánh giá (MAE, RMSE, biên đúng/thừa/thiếu).
        path: Đường dẫn để lưu tệp ảnh PNG (nếu None sẽ không lưu).
        fig_num: Số thứ tự Figure (1, 2, 3, 4) để quản lý cửa sổ GUI.

    Returns:
        Đối tượng matplotlib Figure đã vẽ hoàn chỉnh.
    """
    # Khối 1: Khởi tạo Figure và 4 Subplot chia sẻ trục thời gian chung
    fig, (ax, fx, logax, f0ax) = plt.subplots(
        4, 1, figsize=(11, 8.5), sharex=True, layout="constrained", num=fig_num
    )
    t = np.arange(len(record.samples)) / record.fs

    # Khối 2: Subplot 1 — Dạng sóng tín hiệu (WAV) và các biên phân đoạn
    ax.plot(t, record.samples, color="0.25", linewidth=0.6, label="Tín hiệu WAV")
    ax.set_title(f"1. Dạng sóng tín hiệu (Waveform) & Biên phân đoạn — {record.name}.wav",
                 fontsize=10, fontweight="bold")
    ax.set_ylabel("Biên độ", fontsize=9)
    ax.set_xlabel("Thời gian (giây)", fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)

    # Khối 3: Subplot 2 — Năng lượng ngắn hạn (STE chuẩn hóa) và Ngưỡng phân đoạn
    fx.plot(features.times, features.normalized_ste, color="#185a8d", lw=1.2, label="STE chuẩn hóa")
    fx.axhline(threshold, color="#e69f00", ls="--", lw=1.3, label=f"Ngưỡng T = {threshold:.4f}")
    fx.set_title(f"2. Năng lượng ngắn hạn chuẩn hóa (STE) & Ngưỡng — {METHOD_LABELS[method]}",
                 fontsize=10, fontweight="bold")
    fx.set_ylabel("STE chuẩn hóa", fontsize=9)
    fx.set_xlabel("Thời gian (giây)", fontsize=9)
    fx.grid(True, linestyle=":", alpha=0.5)

    # Tô màu nền các vùng được nhận diện là tiếng nói (Speech)
    for left, right, is_speech in segments(mask, features.edges):
        if is_speech:
            fx.axvspan(left, right, color="#b7dfc0", alpha=0.35, label="Vùng Speech" if left == 0 else None)

    # Khối 4: Subplot 3 — Mức năng lượng logSTE (dB) và logMA (dB)
    logax.plot(features.times, features.log_ste, color="#6f42a2", lw=1.0, label="logSTE (dB)")
    logax.plot(features.times, features.log_ma, color="#009e73", lw=1.0, alpha=0.8, label="logMA (dB)")
    logax.set_title("3. Mức năng lượng logSTE (dB) và logMA (dB)", fontsize=10, fontweight="bold")
    logax.set_ylabel("Mức (dB)", fontsize=9)
    logax.set_xlabel("Thời gian (giây)", fontsize=9)
    logax.grid(True, linestyle=":", alpha=0.5)

    # Khối 5: Subplot 4 — Tần số cơ bản F0 ước lượng và đường F0 chuẩn LAB
    f0ax.plot(features.times, features.f0, color="#d55e00", lw=1.2, marker=".", ms=2,
              label="F0 ước lượng (Tự tương quan)")
    f0_lab_text = ""
    if record.reference_f0_mean is not None:
        f0ax.axhline(record.reference_f0_mean, color="#0072b2", ls="--", lw=1.2,
                     label=f"F0mean chuẩn LAB: {record.reference_f0_mean:.1f} Hz")
        f0_lab_text = f" [F0mean LAB: {record.reference_f0_mean:.1f} Hz]"
    f0ax.set_title(f"4. Tần số cơ bản F0 theo thời gian (Hz){f0_lab_text}",
                   fontsize=10, fontweight="bold")
    f0ax.set_ylabel("F0 (Hz)", fontsize=9)
    f0ax.set_xlabel("Thời gian (giây)", fontsize=9)
    f0ax.set_ylim(50, 420)
    f0ax.grid(True, linestyle=":", alpha=0.5)

    # Khối 6: Vẽ các đường kẻ dọc biểu diễn biên dự đoán (xanh) và biên chuẩn (đỏ) trên cả 4 trục
    for i, (b_time, _) in enumerate(predicted_boundaries(mask, features.edges)):
        for axis in (ax, fx, logax, f0ax):
            axis.axvline(b_time, color="blue", lw=1.4,
                         label="Biên dự đoán (Thuật toán)" if i == 0 and axis is ax else None)

    for i, (b_time, _) in enumerate(reference_boundaries(record.labels)):
        for axis in (ax, fx, logax, f0ax):
            axis.axvline(b_time, color="red", ls="--", lw=1.4,
                         label="Biên chuẩn (Ground Truth)" if i == 0 and axis is ax else None)

    # Khối 7: Cài đặt hiển thị chú thích (Legend), giới hạn thời gian và tiêu đề tổng
    for axis in (ax, fx, logax, f0ax):
        axis.legend(loc="upper right", fontsize=8)
        axis.set_xlim(0, record.duration)

    mae_str = "KXĐ" if metrics["mae_ms"] is None else f"{metrics['mae_ms']:.1f}"
    fig.suptitle(
        f"KẾT QUẢ PHÂN ĐOẠN SPEECH/SILENCE — {record.name}.wav\n"
        f"Thuật toán: {METHOD_LABELS[method]} | MAE: {mae_str} ms | "
        f"Biên đúng/thừa/thiếu: {metrics['matched']}/{metrics['extra']}/{metrics['missed']}",
        fontsize=11, fontweight="bold"
    )

    # Khối 8: Lưu tệp ảnh nếu có yêu cầu
    if path is not None:
        fig.savefig(path, dpi=160)

    return fig


def arrange_4_figures(figures: list[plt.Figure]) -> None:
    """Tự động định vị và sắp xếp 4 cửa sổ Figure vào 4 góc màn hình để GV quan sát.

    Thứ tự sắp xếp:
    - Figure 1: Góc trên - trái (Top-Left)
    - Figure 2: Góc trên - phải (Top-Right)
    - Figure 3: Góc dưới - trái (Bottom-Left)
    - Figure 4: Góc dưới - phải (Bottom-Right)

    Hỗ trợ cả môi trường giao diện Qt (PyQt/PySide) và Tkinter (TkAgg).

    Args:
        figures: Danh sách chứa đúng 4 đối tượng Figure tương ứng 4 tệp kiểm thử.
    Returns:
        None. Thay đổi vị trí cửa sổ GUI, in hướng dẫn nếu backend không hỗ trợ.
    """
    # Khối 1: Hiện cửa sổ trước khi đặt vị trí để backend hoàn tất khung cửa sổ.
    for fig in figures:
        fig.canvas.manager.show()
        fig.canvas.flush_events()

    # Khối 2: Xác định kích thước vùng hiển thị khả dụng của màn hình.
    screen_x, screen_y = 0, 0
    screen_w, screen_h = 1920, 1080

    for fig in figures:
        try:
            manager = fig.canvas.manager
            win = getattr(manager, "window", None)
            if win is not None and hasattr(win, "screen"):
                geom = win.screen().availableGeometry()
                screen_x, screen_y = geom.x(), geom.y()
                screen_w, screen_h = geom.width(), geom.height()
                break
            if win is not None and hasattr(win, "winfo_screenwidth"):
                screen_w, screen_h = win.winfo_screenwidth(), win.winfo_screenheight()
                break
        except Exception:
            pass

    # Khối 3: Tính toán kích thước mỗi cửa sổ xấp xỉ 1/4 màn hình.
    win_w = screen_w // 2
    win_h = screen_h // 2

    # Tọa độ 4 góc: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    quadrants = [
        (screen_x, screen_y),
        (screen_x + win_w, screen_y),
        (screen_x, screen_y + win_h),
        (screen_x + win_w, screen_y + win_h)
    ]

    # Khối 4: Gán vị trí hình học cho từng cửa sổ Figure.
    for i, fig in enumerate(figures[:4]):
        qx, qy = quadrants[i]
        try:
            manager = fig.canvas.manager
            win = getattr(manager, "window", None)
            if win is not None:
                if hasattr(win, "setGeometry"):  # Qt backend
                    win.setGeometry(qx + 8, qy + 28, win_w - 16, win_h - 48)
                elif hasattr(win, "wm_geometry"):  # Tkinter backend
                    win.wm_geometry(f"{win_w - 16}x{win_h - 48}+{qx + 8}+{qy + 28}")
                else:
                    print("Backend chưa hỗ trợ tự xếp cửa sổ; hãy đặt figure vào bốn góc thủ công.")
            else:
                print("Backend không có cửa sổ GUI. PNG đã lưu để quan sát kết quả.")
        except Exception as error:
            print(f"Không tự xếp được Figure {i + 1}: {error}")


def plot_comparison(record: Record, predictions: dict[str, tuple[Features, np.ndarray]], path: Path) -> None:
    """Tạo hình vẽ so sánh trực quan kết quả của cả 3 thuật toán trên cùng 1 tín hiệu.

    Args:
        record: Đối tượng Record của tệp âm thanh.
        predictions: Từ điển chứa kết quả dự đoán của từng thuật toán.
        path: Đường dẫn tệp PNG để lưu ảnh so sánh.
    Returns:
        None. Lưu hình so sánh trong path (hàm hỗ trợ, không gọi trong demo bốn figure).
    """
    # Khối 1: Khởi tạo đồ thị 5 dải so sánh
    fig, axes = plt.subplots(5, 1, figsize=(13, 10), sharex=True, layout="constrained")
    t = np.arange(len(record.samples)) / record.fs

    # Subplot 1: Sóng âm thanh WAV
    axes[0].plot(t, record.samples, color="0.25", lw=0.5)
    axes[0].set_title(f"So sánh ba thuật toán trên {record.name}.wav (Xanh: Dự đoán, Đỏ: Chuẩn)",
                      fontsize=11, fontweight="bold")
    axes[0].set_ylabel("WAV", fontsize=9)
    axes[0].set_xlabel("Thời gian (giây)", fontsize=9)
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # Khối 2: Subplot 2-4: Từng thuật toán phân đoạn
    for axis, method in zip(axes[1:4], METHODS):
        feat, msk = predictions[method]
        axis.plot(feat.times, feat.normalized_ste, color="0.35", lw=0.8)
        for left, right, speech in segments(msk, feat.edges):
            if speech:
                axis.axvspan(left, right, color="#b7dfc0", alpha=0.5)
        for b_time, _ in predicted_boundaries(msk, feat.edges):
            axis.axvline(b_time, color="blue", lw=1.3)
        axis.set_title(f"Thuật toán {METHOD_LABELS[method]}", fontsize=9, fontweight="bold")
        axis.set_ylabel(METHOD_LABELS[method], fontsize=9)
        axis.set_xlabel("Thời gian (giây)", fontsize=9)
        axis.grid(True, linestyle=":", alpha=0.5)

    # Khối 3: Subplot 5: Đường tần số cơ bản F0
    rep_feat = predictions[METHODS[0]][0]
    axes[4].plot(rep_feat.times, rep_feat.f0, color="#d55e00", lw=1, marker=".", ms=2)
    if record.reference_f0_mean is not None:
        axes[4].axhline(record.reference_f0_mean, color="#0072b2", ls="--", lw=1,
                        label=f"F0mean LAB: {record.reference_f0_mean:.1f} Hz")
        axes[4].legend(loc="upper right", fontsize=8)
    axes[4].set_title("Tần số cơ bản F0 ước lượng (Hz)", fontsize=9, fontweight="bold")
    axes[4].set_ylabel("F0 (Hz)", fontsize=9)
    axes[4].set_xlabel("Thời gian (giây)", fontsize=9)
    axes[4].set_ylim(50, 420)
    axes[4].grid(True, linestyle=":", alpha=0.5)

    # Khối 4: Thêm biên chuẩn đỏ lên tất cả các trục và lưu ảnh
    for axis in axes[:4]:
        for b_time, _ in reference_boundaries(record.labels):
            axis.axvline(b_time, color="red", ls="--", lw=1.3)
        axis.set_xlim(0, record.duration)

    fig.savefig(path, dpi=160)
    plt.close(fig)




def plot_distributions(records: list[Record], models: dict, path: Path) -> None:
    """Vẽ biểu đồ phân bố mật độ xác suất normalized STE của tập huấn luyện.

    Args:
        records: Danh sách bản ghi huấn luyện.
        models: Từ điển chứa mô hình và ngưỡng thống kê.
        path: Đường dẫn lưu ảnh.
    Returns:
        None. Lưu phân bố training trong path (hàm hỗ trợ, không gọi trong demo).
    """
    # Khối 1: Lấy mẫu năng lượng và khởi tạo đồ thị
    frame_ms = models["statistical"]["frame_ms"]
    sil, sp = training_arrays(records, frame_ms)
    fig, axis = plt.subplots(figsize=(10, 5), layout="constrained")
    bins = np.linspace(0, 1, 101)

    # Khối 2: Vẽ histogram mật độ cho hai lớp Silence và Speech
    axis.hist(sil, bins=bins, density=True, alpha=0.55, label=f"Silence (n={len(sil)})", color="#56b4e9")
    axis.hist(sp, bins=bins, density=True, alpha=0.55, label=f"Speech (n={len(sp)})", color="#d55e00")
    axis.axvline(models["statistical"]["statistical_threshold"], color="black", ls="--",
                 lw=1.5, label=f"Ngưỡng Gaussian = {models['statistical']['statistical_threshold']:.5f}")

    # Khối 3: Đặt tiêu đề, nhãn trục và lưu ảnh
    axis.set_xlabel("Năng lượng ngắn hạn chuẩn hóa (STE)", fontsize=10)
    axis.set_ylabel("Mật độ xác suất", fontsize=10)
    axis.set_title("Phân bố năng lượng ngắn hạn (Normalized STE) trên tập huấn luyện", fontsize=11, fontweight="bold")
    axis.set_xlim(0, min(0.3, max(float(np.quantile(sp, 0.9)), 0.03)))
    axis.grid(True, linestyle=":", alpha=0.5)
    axis.legend(fontsize=9)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict]) -> None:
    """Ghi danh sách từ điển ra tệp định dạng CSV có hỗ trợ UTF-8 BOM.

    Args:
        path: Đường dẫn tệp CSV đầu ra.
        rows: Danh sách các dòng dữ liệu dạng dict.
    Returns:
        None. Ghi bảng số liệu ra tệp path nếu có dữ liệu.
    """
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(root: Path, output: Path, only: str | None = None, noise: bool = True,
        show_gui: bool = True) -> None:
    """Thực thi toàn bộ quy trình: Huấn luyện -> Kiểm thử -> Lưu kết quả -> Demo 4 Figure 4 góc.

    Args:
        root: Thư mục gốc chứa dự án.
        output: Thư mục xuất kết quả (hình ảnh, CSV, markdown).
        only: Chọn 1 thuật toán cụ thể ('binary', 'histogram', 'statistical') hoặc None cho cả 3.
        noise: Khảo sát ảnh hưởng khi thêm nhiễu trắng (SNR = 30, 20, 10, 0 dB).
        show_gui: Nếu True, mở 4 Figure trên màn hình và tự sắp xếp 4 góc cho GV quan sát.
    Returns:
        None. Lưu bốn PNG, CSV và bình luận Markdown trong thư mục output.
    """
    # Khối 1: Nạp dữ liệu huấn luyện và kiểm thử
    train = [read_record(p) for p in discover(root, "TinHieuHuanLuyen")]
    test = [read_record(p) for p in discover(root, "TinHieuKiemThu")]
    if len(test) != 4:
        raise ValueError(f"Demo yêu cầu đúng 4 WAV kiểm thử, hiện tìm thấy {len(test)}")
    output.mkdir(parents=True, exist_ok=True)

    # Khối 2: Huấn luyện và xác định ngưỡng tối ưu
    model_path = output / "tham_so_huan_luyen.json"
    # Chỉ huấn luyện thuật toán đang demo, không mượn mô hình của thành viên khác.
    models, validation = choose(train, only=only)
    model_path.write_text(
        json.dumps({"models": models, "validation": validation}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    methods = (only,) if only else METHODS
    rows, boundaries, noise_rows = [], [], []
    demo_figures: list[plt.Figure] = []
    comments = ["# Bình luận bốn figure kiểm thử", "",
                "Mỗi figure ứng với một WAV và chứa toàn bộ các phương pháp đã chọn.",
                "Biên ghép là cặp cùng hướng để đo sai lệch, không có dung sai chấp nhận 200 ms.", ""]

    # Khối 3: Dự đoán trên 4 tệp kiểm thử và tạo các figure
    for file_idx, record in enumerate(test, 1):
        print(f"\nTín hiệu: {record.name} | SNR nền ước lượng: {estimate_snr(record):.1f} dB")
        all_predictions = {}

        for method in methods:
            model = models[method]
            features, mask, threshold, fallback = predict(record.samples, record.fs, model, method)
            metrics = score(record, features, mask)
            all_predictions[method] = {"features": features, "mask": mask, "threshold": threshold,
                                       "metrics": metrics, "fallback": fallback}

            # Lưu số liệu đánh giá
            row = {
                "wav": record.name, "method": method, "threshold": threshold,
                "histogram_fallback": fallback, "snr_estimate_db": estimate_snr(record), **metrics
            }
            rows.append(row)

            # Khối 3c: Xuất danh sách biên theo giây, giữ thông tin hướng chuyển tiếp.
            for b_time, starts_sp in predicted_boundaries(mask, features.edges):
                boundaries.append({
                    "wav": record.name, "method": method, "time_s": b_time, "starts_speech": starts_sp
                })

            # Khối 3a: In số liệu của từng phương pháp; chỉ vẽ sau khi đủ kết quả WAV này.
            mae_str = "KXĐ" if metrics["mae_ms"] is None else f"{metrics['mae_ms']:.1f}"
            print(f'  {METHOD_LABELS[method]}: MAE={mae_str} ms, '
                  f'biên ghép/thừa/thiếu={metrics["matched"]}/{metrics["extra"]}/{metrics["missed"]}')

            # Khảo sát khả năng kháng nhiễu nếu được bật
            if noise:
                rng_seed = 2026
                for db in (30, 20, 10, 0):
                    for repeat in range(3):
                        rng = np.random.default_rng(rng_seed + repeat)
                        signal_power = float(np.mean(record.samples ** 2))
                        added = rng.normal(0, np.sqrt(signal_power / (10 ** (db / 10))), len(record.samples))
                        nf, nm, _, _ = predict(record.samples + added, record.fs, model, method, compute_f0=False)
                        noise_rows.append({
                            "wav": record.name, "method": method, "signal_to_added_noise_db": db,
                            "seed": rng_seed + repeat, **score(record, nf, nm)
                        })

        # Khối 3b: Tạo đúng một Figure cho WAV, chứa cả ba phương pháp ở chế độ all.
        fig = plot_demo(record, all_predictions, METHOD_LABELS, output / f"{record.name}.png", file_idx)
        fig.canvas.manager.set_window_title(f"Figure {file_idx}: {record.name}.wav")
        demo_figures.append(fig)
        comments.extend(figure_comments(record, all_predictions, METHOD_LABELS))

    # Khối 4: Xuất các tệp báo cáo tổng hợp
    write_csv(output / "ket_qua.csv", rows)
    write_csv(output / "bien_du_doan.csv", boundaries)
    if noise:
        write_csv(output / "khao_sat_nhieu.csv", noise_rows)
    (output / "binh_luan_tung_hinh.md").write_text("\n".join(comments), encoding="utf-8")

    # Khối 5: Sắp xếp 4 Figure lên 4 góc màn hình và hiển thị cho GV quan sát
    if show_gui and demo_figures:
        print("\n--> Đang sắp xếp 4 Figure lên 4 góc màn hình (Top-Left, Top-Right, Bottom-Left, Bottom-Right)...")
        arrange_4_figures(demo_figures)
        print("--> Nhấn nút đóng cửa sổ hoặc Ctrl+C để kết thúc demo.")
        plt.show()
    else:
        for fig in demo_figures:
            plt.close(fig)

    print(f"\nĐã hoàn thành! Toàn bộ kết quả đã được lưu tại: {output}")
