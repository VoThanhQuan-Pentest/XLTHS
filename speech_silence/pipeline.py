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

from dataclasses import asdict, replace
from pathlib import Path
import csv
import json

import matplotlib.pyplot as plt
import numpy as np

from .algorithms import HistogramConfig, binary_threshold, gaussian_threshold, histogram_threshold
from .data import Record, discover, read_record, speech_at, reference_boundaries
from .evaluation import score, estimate_snr, summarize_scores
from .features import Features, extract, median_filter, remove_virtual_silence, predicted_boundaries, segments
from .demo import plot_demo, figure_comments
from .config import FRAME_MS, HOP_MS, FEATURE_LAYOUT, TRAINING_PROTOCOL, MEDIAN_ORDERS, HISTOGRAM_WEIGHTS

METHODS = ("binary", "histogram", "statistical")
METHOD_LABELS = {
    "binary": "Tìm kiếm nhị phân",
    "histogram": "Histogram",
    "statistical": "Thống kê Gaussian"
}


def training_arrays(records: list[Record], median_order: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Nhận TRAIN/bậc median; trả STE hai lớp, chỉ lấy ô có nhãn tại tâm quyết định."""
    # Khối 1: Mỗi WAV chuẩn hóa riêng, sau đó mới median; không chuẩn hóa lại đường lọc.
    silence_values, speech_values = [], []
    for record in records:
        features = extract(record.samples, record.fs, FRAME_MS, HOP_MS, compute_f0=False)
        decision = median_filter(features.normalized_ste, median_order)
        truth, valid = speech_at(features.times, record.labels)

        # Khối 2: Gộp đặc trưng có nhãn, không nối bốn WAV thành một tín hiệu mới.
        silence_values.extend(decision[valid & ~truth])
        speech_values.extend(decision[valid & truth])
    return np.asarray(silence_values), np.asarray(speech_values)


def fit(records: list[Record], histogram: HistogramConfig | None = None,
        method: str | None = None, median_order: int = 1) -> dict:
    """Nhận TRAIN/cấu hình/phương pháp; trả mô hình BT1 chỉ dùng các khung training có nhãn."""
    # Khối 1: Ghi cả bố trí cửa sổ để mô hình 25/10 ms cũ không được dùng nhầm.
    if method is not None and method not in METHODS:
        raise ValueError(f"Thuật toán không hợp lệ: {method}")
    model = {"frame_ms": FRAME_MS, "hop_ms": HOP_MS, "minimum_silence_ms": 200,
             "feature_layout": FEATURE_LAYOUT, "training_protocol": TRAINING_PROTOCOL}

    # Khối 2: Binary dùng median riêng; Statistics dùng STE chuẩn hóa chưa median.
    if method is None or method == "binary":
        sil, sp = training_arrays(records, median_order)
        model.update(binary_threshold=binary_threshold(sil, sp), median_order=median_order)
    if method is None or method == "statistical":
        sil, sp = training_arrays(records)
        model["statistical_threshold"], model["statistics"] = gaussian_threshold(sil, sp)

    # Khối 3: Histogram khóa cấu hình; ngưỡng và fallback mean được tính trên từng WAV.
    if method is None or method == "histogram":
        model["histogram"] = asdict(histogram or HistogramConfig())
    return model


def predict(samples: np.ndarray, fs: int, model: dict, method: str,
            compute_f0: bool = True) -> tuple[Features, np.ndarray, float, bool]:
    """Nhận waveform/fs/mô hình, không nhận LAB; trả đặc trưng, mask, T và cờ fallback."""
    # Khối 1: Mô hình phải cùng 25/10 ms và cửa sổ centered_hop_v1.
    if method not in METHODS:
        raise ValueError(f"Thuật toán không hợp lệ: {method}")
    if (model.get("frame_ms") != FRAME_MS or model.get("hop_ms") != HOP_MS
            or model.get("feature_layout") != FEATURE_LAYOUT):
        raise ValueError("Mô hình không dùng 25/10 ms và centered_hop_v1. Hãy huấn luyện lại.")
    features = extract(samples, fs, FRAME_MS, HOP_MS, compute_f0=compute_f0)
    fallback_used = False

    # Khối 2: Chỉ Binary median; Histogram vẫn adaptive từ chính WAV đang xử lý.
    if method == "binary":
        decision = median_filter(features.normalized_ste, model["median_order"])
        threshold = model["binary_threshold"]
    elif method == "statistical":
        decision = features.normalized_ste
        threshold = model["statistical_threshold"]
    else:
        decision = features.normalized_ste
        threshold, fallback_used = histogram_threshold(decision, HistogramConfig(**model["histogram"]))
    features = replace(features, decision_ste=decision)

    # Khối 3: Zero-audio giữ Silence; không để >=0 hoặc lấp silence ngắn sinh speech giả.
    raw_mask = decision >= threshold
    if not np.any(samples):
        mask = np.zeros(len(raw_mask), dtype=bool)
    else:
        mask = remove_virtual_silence(raw_mask, features.edges, model["minimum_silence_ms"] / 1000)
    return features, mask, float(threshold), fallback_used


def choose(records: list[Record], only: str | None = None) -> tuple[dict, dict]:
    """Nhận TRAIN/phương pháp; trả mô hình và điểm hiệu chỉnh TRAIN, không phải LOO/TEST."""
    # Khối 1: Không tìm frame/hop; Binary tìm median, Histogram chỉ tìm W.
    if not records or (only is not None and only not in METHODS):
        raise ValueError("Cần TRAIN không rỗng và thuật toán hợp lệ")
    candidates = {"binary": MEDIAN_ORDERS, "histogram": HISTOGRAM_WEIGHTS, "statistical": (1,)}
    models, calibration = {}, {}
    methods = (only,) if only else METHODS
    for method in methods:
        best_key = None
        for candidate in candidates[method]:
            histogram = HistogramConfig(weight=candidate) if method == "histogram" else None
            median_order = candidate if method == "binary" else 1
            model = fit(records, histogram, method=method, median_order=median_order)

            # Khối 2: Chấm lại toàn TRAIN theo BT1; không gọi đây là hiệu suất độc lập.
            scores = []
            for record in records:
                f, mask, _, _ = predict(record.samples, record.fs, model, method, compute_f0=False)
                scores.append(score(record, f, mask))
            mean_mae = float(np.mean([s["mae_ms"] if s["mae_ms"] is not None else float("inf")
                                     for s in scores]))

            # Khối 3: Ưu tiên biên lỗi, MAE rồi tham số nhỏ hơn; BER chỉ dùng báo cáo.
            key = (sum(s["missed"] + s["extra"] for s in scores), round(mean_mae, 10), candidate)
            if best_key is None or key < best_key:
                best_key = key
                models[method] = model
                calibration[method] = {
                    "protocol": TRAINING_PROTOCOL, "boundary_misses": key[0],
                    "mean_mae_ms": mean_mae if np.isfinite(mean_mae) else None,
                    "balanced_error": float(np.mean([s["balanced_error"] for s in scores])),
                    "candidate_count": len(candidates[method]), "training_files": len(records),
                }
    return models, calibration


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
    fx.plot(features.times, features.normalized_ste, color="0.65", lw=0.8, label="STE chuẩn hóa trước lọc")
    decision = features.decision_ste if features.decision_ste is not None else features.normalized_ste
    fx.plot(features.times, decision, color="#185a8d", lw=1.2,
            label="STE sau median (so ngưỡng)" if method == "binary" else "STE so ngưỡng")
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
        axis.plot(feat.times, feat.normalized_ste, color="0.65", lw=0.7)
        decision = feat.decision_ste if feat.decision_ste is not None else feat.normalized_ste
        axis.plot(feat.times, decision, color="#185a8d", lw=0.9)
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
    sil, sp = training_arrays(records)
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
    # Khối 1: Nạp TRAIN, hiệu chỉnh và khóa mô hình trước khi đọc TEST.
    train = [read_record(p) for p in discover(root, "TinHieuHuanLuyen")]
    if len(train) != 4:
        raise ValueError(f"Yêu cầu đúng 4 WAV training, hiện tìm thấy {len(train)}")
    models, calibration = choose(train, only=only)
    test = [read_record(p) for p in discover(root, "TinHieuKiemThu")]
    if len(test) != 4:
        raise ValueError(f"Demo yêu cầu đúng 4 WAV kiểm thử, hiện tìm thấy {len(test)}")
    output.mkdir(parents=True, exist_ok=True)

    # Khối 2: Huấn luyện và xác định ngưỡng tối ưu
    model_path = output / "tham_so_huan_luyen.json"
    # Chỉ huấn luyện thuật toán đang demo, không mượn mô hình của thành viên khác.
    model_path.write_text(
        json.dumps({"models": models, "calibration": calibration}, indent=2, ensure_ascii=False),
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
        snr = estimate_snr(record)
        snr_text = f"{snr:.1f} dB" if snr is not None else "KXĐ"
        print(f"\nTín hiệu: {record.name} | SNR nền ước lượng: {snr_text}")
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
    summaries = [{"method": method, **summarize_scores([r for r in rows if r["method"] == method])}
                 for method in methods]
    write_csv(output / "tong_hop.csv", summaries)
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
