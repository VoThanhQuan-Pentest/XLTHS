"""Hình tìm ngưỡng từ dữ liệu thật, dùng chung cho chương trình Python và notebook tự chứa."""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from .algorithms import (
    binary_search_details, binary_energy_errors,
    HistogramConfig, histogram_peak_pair, histogram_threshold, smooth_1d,
)


def plot_binary_learning(silence: np.ndarray, speech: np.ndarray,
                         model: dict, path: Path | None = None) -> tuple[plt.Figure, dict]:
    """Nhận hai lớp TRAIN sau median/mô hình/path; trả hình cân bằng lỗi, lịch sử thật và metadata."""
    # Khối 1: Dùng chính bộ giải học T; không mô phỏng một thuật toán khác để vẽ minh họa.
    details = binary_search_details(silence, speech)
    threshold = details["threshold"]
    if abs(threshold - model["binary_threshold"]) > 1e-12:
        raise ValueError("Đặc trưng minh họa Binary khác đặc trưng đã học mô hình")
    sil, sp = details["silence_overlap"], details["speech_overlap"]
    history = details["history"]
    lower, upper = sorted((details["initial_lower"], details["initial_upper"]))

    # Khối 2: Các đường lỗi được tính từ cùng mẫu overlap, trên một lưới chỉ phục vụ vẽ.
    grid = np.unique(np.r_[np.linspace(lower, upper, 400), threshold]) if lower < upper else np.array([threshold])
    errors = [binary_energy_errors(sil if len(sil) else silence,
                                  sp if len(sp) else speech, t) for t in grid]
    with plt.rc_context({"font.size": 22, "axes.labelsize": 22, "axes.titlesize": 24,
                         "xtick.labelsize": 22, "ytick.labelsize": 22, "legend.fontsize": 22}):
        fig, axes = plt.subplots(1, 2, figsize=(15, 6.8), layout="constrained")
        axes[0].plot(grid, [e[0] for e in errors], color="#527B9B", lw=3, label="Silence above T")
        axes[0].plot(grid, [e[1] for e in errors], color="#CA7836", lw=3, label="Speech below T")

        # Khối 3: Giao hai đại lượng nhầm tương ứng ngưỡng của bộ giải.
        axes[0].axvline(threshold, color="#087F78", ls="--", lw=2.5, label=f"T = {threshold:.7f}")
        axes[0].set(title="Energy errors in TRAIN overlap", xlabel="Threshold candidate", ylabel="Mean energy error")
        view_end = min(upper, max(threshold * 2.5, lower + (upper - lower) * .2))
        if lower < view_end:
            visible = [(t, e) for t, e in zip(grid, errors) if t <= view_end]
            axes[0].set(xlim=(lower, view_end), ylim=(0, max(max(e) for _, e in visible) * 1.1),
                        title="Energy balance near the solution")
        axes[0].legend(loc="upper right")
        if history:
            iterations = [step["iteration"] for step in history]
            axes[1].fill_between(iterations, [s["lower"] for s in history], [s["upper"] for s in history],
                                 color="#A9DECF", alpha=.55, label="Search interval")
            axes[1].plot(iterations, [s["threshold"] for s in history], "o-", color="#15363D", lw=2.2,
                         markersize=5, label="Actual midpoint")

        # Khối 4: Chỉ các điểm thật trong vòng lặp được dùng vẽ đường hội tụ.
        axes[1].axhline(threshold, color="#087F78", ls="--", lw=2.5)
        axes[1].set(title=f"{len(history)} actual bisection iterations", xlabel="Iteration", ylabel="Threshold")
        axes[1].legend(loc="upper right")
        for ax in axes:
            ax.grid(alpha=.2)
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        fig.suptitle(f"Binary Search on TRAIN: median {model['median_order']}, overlap {len(sil)}/{len(sp)}",
                     fontsize=24, fontweight="bold")
        if path is not None:
            fig.savefig(path, dpi=180)

    # Khối 5: Chỉ lưu số liệu đặc trưng/thuật toán, không nhúng mảng mẫu WAV vào báo cáo.
    metadata = {"method": "binary", "source": "TRAIN", "threshold": threshold,
                "median_order": model["median_order"], "silence_frames": len(silence), "speech_frames": len(speech),
                "silence_overlap": len(sil), "speech_overlap": len(sp), "iterations": len(history),
                "stop_reason": details["stop_reason"], "history": history}
    return fig, metadata


def plot_histogram_learning(values: np.ndarray, config: HistogramConfig, threshold: float,
                            name: str, path: Path | None = None) -> tuple[plt.Figure, dict]:
    """Nhận STE/config/T/tên WAV/path, không nhận LAB; trả histogram thật, hai đỉnh, T và metadata."""
    # Khối 1: Kiểm chứng đúng hai đỉnh và ngưỡng được chọn bởi cùng hàm suy luận.
    expected, fallback = histogram_threshold(values, config)
    if abs(expected - threshold) > 1e-12:
        raise ValueError("Ngưỡng minh họa Histogram khác ngưỡng dùng phân đoạn")
    pair = histogram_peak_pair(values, config)
    counts, edges = np.histogram(values, bins=config.bins, range=(0, 1))
    smoothed = smooth_1d(counts, config.smooth)
    centers = (edges[:-1] + edges[1:]) / 2
    indices = [] if pair is None else [pair[0], pair[1]]
    zoom_end = max(.04, (centers[indices[-1]] + 4 / config.bins) if indices else threshold * 2)

    # Khối 2: Toàn miền và vùng hai đỉnh dùng cùng histogram, không dựng lại dữ liệu khác.
    with plt.rc_context({"font.size": 22, "axes.labelsize": 22, "axes.titlesize": 24,
                         "xtick.labelsize": 22, "ytick.labelsize": 22, "legend.fontsize": 22}):
        fig, axes = plt.subplots(1, 2, figsize=(15, 6.8), layout="constrained")
        for ax in axes:
            ax.bar(centers, counts, width=1 / config.bins, color="#D0D8DA", label="Raw counts")
            ax.plot(centers, smoothed, color="#527B9B", lw=2.5, label="Smoothed counts")
            ax.axvline(threshold, color="#087F78", ls="--", lw=2.5, label=f"T = {threshold:.7f}")

            # Khối 3: M1/M2 là hai cực đại đầu, không tự gán thành hai lớp thuần.
            for number, index in enumerate(indices, 1):
                ax.scatter(centers[index], smoothed[index], s=100, color="#CA7836", zorder=5)
                ax.annotate(f"M{number}", (centers[index], smoothed[index]), xytext=(12, 12),
                            textcoords="offset points", fontsize=22, color="#9A541F")
            ax.set(xlabel="Normalized STE", ylabel="Frame count")
            ax.grid(alpha=.2)
        axes[0].set(title="All STE bins", xlim=(0, 1))
        axes[1].set(title="Selected peaks and threshold", xlim=(0, min(1, zoom_end)))
        axes[1].set(yscale="log", ylim=(.5, max(float(np.max(counts)), float(np.max(smoothed))) * 1.2),
                    ylabel="Frame count (log scale)")
        axes[0].legend(loc="upper right")
        fig.suptitle(f"{name}: {config.bins} bins, smoothing {config.smooth}, W = {config.weight}",
                     fontsize=24, fontweight="bold")
        if fallback:
            axes[1].text(.5, .8, "One peak: mean-STE fallback", transform=axes[1].transAxes,
                         ha="center", fontsize=20)
        if path is not None:
            fig.savefig(path, dpi=180)

    # Khối 4: Lưu vị trí được chọn, để notebook/hình/slide có thể đối chiếu với ngưỡng thực.
    metadata = {"method": "histogram", "source": "TEST waveform without LAB", "wav": name,
                "bins": config.bins, "smooth": config.smooth, "weight": config.weight,
                "threshold": threshold, "fallback_used": fallback, "frames": len(values),
                "peak_indices": indices, "peak_centers": [float(centers[i]) for i in indices],
                "peak_heights": [float(smoothed[i]) for i in indices]}
    return fig, metadata


def gaussian_pdf_values(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    """Nhận lưới x/mean/std; trả mật độ Gaussian tự tính với sigma floor giống bộ học ngưỡng."""
    effective_std = max(std, 1e-8)
    return np.exp(-.5 * ((x - mean) / effective_std) ** 2) / (effective_std * np.sqrt(2 * np.pi))


def plot_gaussian_learning(silence: np.ndarray, speech: np.ndarray,
                           model: dict, path: Path | None = None) -> tuple[plt.Figure, dict]:
    """Nhận hai lớp TRAIN/mô hình/path; trả phân bố quan sát, Gaussian fitted, zoom giao điểm và metadata."""
    # Khối 1: Dùng mean/std/T của đúng mô hình đã học, không fit một mô hình mới để minh họa.
    stats, threshold = model["statistics"], model["statistical_threshold"]
    if (len(silence), len(speech)) != (stats["nSil"], stats["nSp"]):
        raise ValueError("Số khung minh họa Gaussian khác mô hình")
    for values, mean_key, std_key in ((silence, "meanSil", "stdSil"), (speech, "meanSp", "stdSp")):
        if abs(float(np.mean(values)) - stats[mean_key]) > 1e-12 or abs(float(np.std(values)) - stats[std_key]) > 1e-12:
            raise ValueError("Dữ liệu minh họa Gaussian khác mean/std đã học")
    density = [float(gaussian_pdf_values(np.array([threshold]), stats[m], stats[s])[0])
               for m, s in (("meanSil", "stdSil"), ("meanSp", "stdSp"))]
    identical = (stats["meanSil"] == stats["meanSp"] and max(stats["stdSil"], 1e-8) == max(stats["stdSp"], 1e-8))
    crossing = not identical and abs(density[0] - density[1]) <= max(density) * 1e-7 + 1e-12
    grid = np.unique(np.r_[np.linspace(0, 1, 2000), np.linspace(0, max(threshold * 2, .006), 1200), threshold])
    colors = ("#527B9B", "#CA7836")

    # Khối 2: Histogram quan sát và PDF Gaussian giữ nguyên mật độ, không scale từng đường theo max.
    with plt.rc_context({"font.size": 22, "axes.labelsize": 22, "axes.titlesize": 24,
                         "xtick.labelsize": 22, "ytick.labelsize": 22, "legend.fontsize": 22}):
        fig, axes = plt.subplots(1, 2, figsize=(15, 6.8), layout="constrained")
        for values, mean_key, std_key, color, name in (
                (silence, "meanSil", "stdSil", colors[0], "Silence"),
                (speech, "meanSp", "stdSp", colors[1], "Speech")):
            maximum = max(float(np.max(values)) * 1.05, .001)
            axes[0].hist(values, bins=np.linspace(0, maximum, 65), density=True,
                         histtype="step", color=color, lw=1.5, alpha=.5, label=f"Observed {name}")

            # Khối 3: Log chỉ đổi trục nhìn, không đổi các PDF hay vị trí giao điểm.
            pdf = gaussian_pdf_values(grid, stats[mean_key], stats[std_key])
            axes[0].plot(grid, np.where(pdf > 1e-12, pdf, np.nan), color=color, lw=3,
                         label=f"Fitted {name}")
            half_width = max(stats["stdSil"] * .45, threshold * .08, 1e-7)
            local = np.linspace(max(0, threshold - half_width), min(1, threshold + half_width), 800)
            axes[1].plot(local, gaussian_pdf_values(local, stats[mean_key], stats[std_key]), color=color,
                         lw=3, label=f"Fitted {name}")

        # Khối 4: Giao điểm thật được đánh dấu; nhánh fallback được ghi rõ nếu không có giao.
        for ax in axes:
            ax.axvline(threshold, color="#087F78", ls="--", lw=2.5)
            ax.grid(alpha=.2)
        axes[0].set(title="Observed TRAIN and fitted models", xlabel="Normalized STE",
                    ylabel="Density (log scale)", xlim=(0, 1), yscale="log", ylim=(1e-3, None))
        axes[0].set_xscale("symlog", linthresh=.003, linscale=1.2)
        axes[0].set_xticks([0, .003, .03, .3, 1])
        axes[0].set_xticklabels(["0", "0.003", "0.03", "0.3", "1"])
        axes[0].set_xlabel("STE (expanded near zero)")
        axes[1].set(title="Chosen crossing" if crossing else "Fallback threshold",
                    xlabel="Normalized STE", ylabel="Density")
        axes[1].scatter([threshold], [np.mean(density)], s=110, color="#087F78", zorder=5)
        axes[0].legend(loc="upper right")
        axes[1].legend(loc="upper right")
        fig.suptitle(f"Gaussian TRAIN: {len(silence)} silence, {len(speech)} speech, T = {threshold:.7f}",
                     fontsize=24, fontweight="bold")
        if path is not None:
            fig.savefig(path, dpi=180)

    # Khối 5: Gaussian là giả thiết fitted; không gọi nó là phân bố thật của dữ liệu.
    metadata = {"method": "statistical", "source": "TRAIN", "threshold": threshold,
                "statistics": stats, "density_at_threshold": density, "is_density_crossing": crossing}
    return fig, metadata


def learning_figure_comments(info: dict) -> list[str]:
    """Nhận metadata hình tìm ngưỡng; trả bình luận vị trí, ý nghĩa và giới hạn bằng tiếng Việt."""
    # Khối 1: Nêu rõ nguồn TRAIN hay waveform TEST không nhãn.
    lines = [f"### Minh họa tìm ngưỡng: {info['method']}", "",
             f"Nguồn: {info['source']}. Ngưỡng đang dùng T={info['threshold']:.10f}."]
    if info["method"] == "binary":
        last = info["history"][-1] if info["history"] else None
        lines += [f"- Median {info['median_order']}; overlap có {info['silence_overlap']} Silence và {info['speech_overlap']} Speech.",
                  f"- Đường trái dùng đúng các mẫu overlap; đường phải là {info['iterations']} vòng chia đôi thật.",
                  f"- Điều kiện dừng: {info['stop_reason']}. " +
                  (f"Residual cuối {last['delta']:.3e}; hai mean năng lượng nhầm gần bằng nhau." if last else "Hai lớp không có vùng chồng lấn rộng.")]
    elif info["method"] == "histogram":
        lines += [f"- {info['wav']}: {info['bins']} bins, trơn {info['smooth']} bins, W={info['weight']} đã khóa từ TRAIN.",
                  f"- Chọn hai cực đại đầu: indices={info['peak_indices']}, tâm bin={info['peak_centers']}.",
                  "- T nghiêng về M1 theo W. Hai đỉnh không bảo đảm là hai lớp thuần Silence/Speech."]
        if info["fallback_used"]:
            lines.append("- Không có hai đỉnh: dùng mean normalized STE của chính WAV này.")
    else:
        lines += ["- Histogram là dữ liệu TRAIN quan sát; hai đường trơn là Gaussian ước lượng bằng mean/std.",
                  f"- Mật độ tại T: Silence={info['density_at_threshold'][0]:.8f}, Speech={info['density_at_threshold'][1]:.8f}.",
                  "- Hình phải phóng vùng chọn ngưỡng. Hình trái dùng log mật độ và mở rộng trục STE gần zero; không đổi PDF hay T.",
                  "- Dữ liệu có thể không khớp hoàn toàn giả thiết Gaussian; không kết luận phân bố thực là chuẩn."]
    return lines + [""]
