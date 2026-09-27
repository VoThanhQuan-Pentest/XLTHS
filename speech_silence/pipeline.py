from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .algorithms import HistogramConfig, binary_threshold, gaussian_threshold, histogram_threshold
from .data import Record, discover, read_record, speech_at, reference_boundaries
from .evaluation import score, estimate_snr
from .features import Features, extract, remove_virtual_silence, predicted_boundaries, segments

METHODS = ("binary", "histogram", "statistical")
METHOD_LABELS = {"binary": "Tìm kiếm nhị phân", "histogram": "Histogram", "statistical": "Thống kê Gaussian"}


def training_arrays(records: list[Record], frame_ms: int) -> tuple[np.ndarray, np.ndarray]:
    sil, sp = [], []
    for record in records:
        features = extract(record.samples, record.fs, frame_ms)
        truth, valid = speech_at(features.times, record.labels)
        sil.extend(features.normalized_ste[valid & ~truth])
        sp.extend(features.normalized_ste[valid & truth])
    return np.asarray(sil), np.asarray(sp)


def fit(records: list[Record], frame_ms: int, histogram: HistogramConfig) -> dict:
    sil, sp = training_arrays(records, frame_ms)
    if not len(sil) or not len(sp):
        raise ValueError("Dữ liệu huấn luyện thiếu một lớp")
    statistical, stats = gaussian_threshold(sil, sp)
    # Ngưỡng dự phòng từ histogram gộp; percentile ở giữa hai lớp khi không có hai đỉnh.
    fallback = float(np.clip((np.median(sil) + np.median(sp)) / 2, 0, 1))
    pooled = np.concatenate([sil, sp])
    try:
        fallback, _ = histogram_threshold(pooled, histogram)
    except ValueError:
        pass
    return {"frame_ms": frame_ms, "hop_ms": 10, "minimum_silence_ms": 200,
            "binary_threshold": binary_threshold(sil, sp),
            "statistical_threshold": statistical, "statistics": stats,
            "histogram": asdict(histogram), "histogram_fallback": fallback}


def predict(samples: np.ndarray, fs: int, model: dict, method: str) -> tuple[Features, np.ndarray, float, bool]:
    if method not in METHODS:
        raise ValueError(f"Thuật toán không hợp lệ: {method}")
    features = extract(samples, fs, model["frame_ms"], model["hop_ms"])
    fallback_used = False
    if method == "binary":
        threshold = model["binary_threshold"]
    elif method == "statistical":
        threshold = model["statistical_threshold"]
    else:
        threshold, fallback_used = histogram_threshold(features.normalized_ste,
                                                       HistogramConfig(**model["histogram"]),
                                                       model["histogram_fallback"])
    mask = remove_virtual_silence(features.normalized_ste >= threshold, features.edges,
                                  model["minimum_silence_ms"] / 1000)
    return features, mask, float(threshold), fallback_used


def choose(records: list[Record]) -> tuple[dict, dict]:
    configs = {
        "binary": [(f, HistogramConfig()) for f in (20, 25, 30)],
        "statistical": [(f, HistogramConfig()) for f in (20, 25, 30)],
        "histogram": [(f, HistogramConfig(b, s, w)) for f in (20, 25, 30)
                      for b in (32, 64, 128) for s in (1, 3, 5) for w in (2, 5, 10)]}
    selected: dict[str, tuple[int, HistogramConfig]] = {}
    validation: dict[str, dict] = {}
    for method, candidates in configs.items():
        best_key = None
        for frame_ms, hist in candidates:
            scores = []
            for held in range(len(records)):
                train = [record for i, record in enumerate(records) if i != held]
                model = fit(train, frame_ms, hist)
                record = records[held]
                features, mask, _, _ = predict(record.samples, record.fs, model, method)
                scores.append(score(record, features, mask))
            key = (round(float(np.mean([s["balanced_error"] for s in scores])), 10),
                   sum(s["missed"] + s["extra"] for s in scores),
                   np.mean([s["mae_ms"] if s["mae_ms"] is not None else 200 for s in scores]),
                   frame_ms, hist.bins, hist.smooth, hist.weight)
            if best_key is None or key < best_key:
                best_key = key
                selected[method] = (frame_ms, hist)
                validation[method] = {"balanced_error": key[0], "boundary_misses": key[1],
                                      "mean_mae_ms": float(key[2])}
    models = {method: fit(records, *selected[method]) for method in METHODS}
    return models, validation


def plot_result(record: Record, method: str, features: Features, mask: np.ndarray,
                threshold: float, metrics: dict, path: Path) -> None:
    fig, (ax, fx, logax) = plt.subplots(3, 1, figsize=(13, 8), sharex=True, layout="constrained")
    t = np.arange(len(record.samples)) / record.fs
    ax.plot(t, record.samples, color="0.25", linewidth=0.5)
    ax.set_ylabel("Biên độ")
    fx.plot(features.times, features.normalized_ste, color="#185a8d", lw=1.2, label="STE chuẩn hóa")
    fx.axhline(threshold, color="#e69f00", ls="--", label=f"Ngưỡng {threshold:.4f}")
    fx.set_ylabel("STE chuẩn hóa")
    fx.set_xlabel("Thời gian (giây)")
    logax.plot(features.times, features.log_ste, color="#6f42a2", lw=1, label="logSTE (dB)")
    logax.plot(features.times, features.log_ma, color="#009e73", lw=1, alpha=0.75, label="logMA (dB)")
    logax.set_ylabel("Mức (dB)")
    logax.set_xlabel("Thời gian (giây)")
    for left, right, is_speech in segments(mask, features.edges):
        if is_speech:
            fx.axvspan(left, right, color="#b7dfc0", alpha=0.22)
    for i, (boundary, _) in enumerate(predicted_boundaries(mask, features.edges)):
        for axis in (ax, fx, logax):
            axis.axvline(boundary, color="blue", lw=1.4, label="Biên dự đoán" if i == 0 and axis is ax else None)
    for i, (boundary, _) in enumerate(reference_boundaries(record.labels)):
        for axis in (ax, fx, logax):
            axis.axvline(boundary, color="red", ls="--", lw=1.4,
                         label="Biên chuẩn" if i == 0 and axis is ax else None)
    ax.legend(loc="upper right", fontsize=9)
    fx.legend(loc="upper right", fontsize=9)
    logax.legend(loc="upper right", fontsize=9)
    mae = "KXĐ" if metrics["mae_ms"] is None else f'{metrics["mae_ms"]:.1f}'
    fig.suptitle(f'{record.name} — {METHOD_LABELS[method]} | MAE: {mae} ms | '
                 f'đúng/thừa/thiếu: {metrics["matched"]}/{metrics["extra"]}/{metrics["missed"]}')
    ax.set_xlim(0, record.duration)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_comparison(record: Record, predictions: dict[str, tuple[Features, np.ndarray]], path: Path) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(13, 8), sharex=True, layout="constrained")
    axes[0].plot(np.arange(len(record.samples)) / record.fs, record.samples, color="0.25", lw=0.5)
    axes[0].set_ylabel("WAV")
    for axis, method in zip(axes[1:], METHODS):
        features, mask = predictions[method]
        axis.plot(features.times, features.normalized_ste, color="0.35", lw=0.8)
        for left, right, speech in segments(mask, features.edges):
            if speech:
                axis.axvspan(left, right, color="#b7dfc0", alpha=0.5)
        for boundary, _ in predicted_boundaries(mask, features.edges):
            axis.axvline(boundary, color="blue", lw=1.3)
        axis.set_ylabel(METHOD_LABELS[method], fontsize=9)
    for axis in axes:
        for boundary, _ in reference_boundaries(record.labels):
            axis.axvline(boundary, color="red", ls="--", lw=1.3)
    axes[-1].set_xlabel("Thời gian (giây)")
    axes[0].set_xlim(0, record.duration)
    fig.suptitle(f"So sánh ba thuật toán — {record.name} | xanh: dự đoán, đỏ: chuẩn")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_distributions(records: list[Record], models: dict, path: Path) -> None:
    frame_ms = models["statistical"]["frame_ms"]
    sil, sp = training_arrays(records, frame_ms)
    fig, axis = plt.subplots(figsize=(10, 5), layout="constrained")
    bins = np.linspace(0, 1, 101)
    axis.hist(sil, bins=bins, density=True, alpha=0.55, label=f"Silence (n={len(sil)})")
    axis.hist(sp, bins=bins, density=True, alpha=0.55, label=f"Speech (n={len(sp)})")
    axis.axvline(models["statistical"]["statistical_threshold"], color="black", ls="--", label="Ngưỡng Gaussian")
    axis.set(xlabel="STE chuẩn hóa", ylabel="Mật độ", title="Phân bố khung trên tập huấn luyện")
    axis.set_xlim(0, min(0.3, max(float(np.quantile(sp, 0.9)), 0.03)))
    axis.legend()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(root: Path, output: Path, only: str | None = None, noise: bool = True) -> None:
    train = [read_record(path) for path in discover(root, "TinHieuHuanLuyen")]
    test = [read_record(path) for path in discover(root, "TinHieuKiemThu")]
    output.mkdir(parents=True, exist_ok=True)
    model_path = output / "tham_so_huan_luyen.json"
    shared_model_path = output.parent / "tham_so_huan_luyen.json" if only else model_path
    if only and shared_model_path.exists():
        package = json.loads(shared_model_path.read_text(encoding="utf-8"))
        models, validation = package["models"], package["validation"]
    else:
        models, validation = choose(train)
        model_path.write_text(json.dumps({"models": models, "validation": validation}, indent=2,
                                         ensure_ascii=False), encoding="utf-8")
    methods = (only,) if only else METHODS
    plot_distributions(train, models, output / "phan_bo_huan_luyen.png")
    rows, boundaries, noise_rows = [], [], []
    for record in test:
        print(f"\nTín hiệu: {record.name} | SNR nền ước lượng: {estimate_snr(record):.1f} dB")
        all_predictions = {}
        for method in methods:
            model = models[method]
            features, mask, threshold, fallback = predict(record.samples, record.fs, model, method)
            metrics = score(record, features, mask)
            all_predictions[method] = (features, mask)
            row = {"wav": record.name, "method": method, "threshold": threshold,
                   "histogram_fallback": fallback, "snr_estimate_db": estimate_snr(record), **metrics}
            rows.append(row)
            for time, starts_speech in predicted_boundaries(mask, features.edges):
                boundaries.append({"wav": record.name, "method": method, "time_s": time,
                                   "starts_speech": starts_speech})
            plot_result(record, method, features, mask, threshold, metrics, output / f"{record.name}_{method}.png")
            mae = "KXĐ" if metrics["mae_ms"] is None else f'{metrics["mae_ms"]:.1f}'
            print(f'  {METHOD_LABELS[method]}: MAE={mae} ms, biên đúng/thừa/thiếu='
                  f'{metrics["matched"]}/{metrics["extra"]}/{metrics["missed"]}')
            if noise:
                rng_seed = 2026
                for db in (30, 20, 10, 0):
                    for repeat in range(3):
                        rng = np.random.default_rng(rng_seed + repeat)
                        signal_power = float(np.mean(record.samples ** 2))
                        added = rng.normal(0, np.sqrt(signal_power / (10 ** (db / 10))), len(record.samples))
                        nf, nm, _, _ = predict(record.samples + added, record.fs, model, method)
                        noise_rows.append({"wav": record.name, "method": method, "signal_to_added_noise_db": db,
                                           "seed": rng_seed + repeat, **score(record, nf, nm)})
        if not only:
            plot_comparison(record, all_predictions, output / f"{record.name}_so_sanh.png")
    write_csv(output / "ket_qua.csv", rows)
    write_csv(output / "bien_du_doan.csv", boundaries)
    if noise:
        write_csv(output / "khao_sat_nhieu.csv", noise_rows)
    lines = ["# Tóm tắt kết quả", "", "Các số liệu sau được đo trên tập kiểm thử; tham số chỉ chọn bằng tập huấn luyện.", ""]
    for method in methods:
        subset = [r for r in rows if r["method"] == method]
        matched = sum(r["matched"] for r in subset)
        extra = sum(r["extra"] for r in subset)
        missed = sum(r["missed"] for r in subset)
        defined = [r["mae_ms"] for r in subset if r["mae_ms"] is not None]
        mean_mae = f"{np.mean(defined):.1f}" if defined else "KXĐ"
        pooled_mae = (sum(r["mae_ms"] * r["matched"] for r in subset if r["mae_ms"] is not None) / matched
                      if matched else None)
        pooled_rmse = (np.sqrt(sum(r["rmse_ms"]**2 * r["matched"] for r in subset
                                   if r["rmse_ms"] is not None) / matched) if matched else None)
        pooled_text = f"{pooled_mae:.1f}/{pooled_rmse:.1f}" if matched else "KXĐ/KXĐ"
        lines.append(f"- **{METHOD_LABELS[method]}**: MAE trung bình theo tệp {mean_mae} ms; "
                     f"MAE/RMSE gộp biên {pooled_text} ms; "
                     f"biên đúng/thừa/thiếu {matched}/{extra}/{missed}.")
    lines.extend(["", "SNR nền là ước lượng từ vùng Silence có nhãn, không phải SNR đo với tín hiệu sạch.",
                  "Histogram có thể tự tính ngưỡng từ WAV kiểm thử; nhãn kiểm thử chỉ dùng để đánh giá."])
    if noise:
        lines.extend(["", "Khi thêm nhiễu trắng, lỗi phân lớp cân bằng trung bình trên 4 tệp × 3 seed:"])
        for method in methods:
            values = []
            for db in (30, 20, 10, 0):
                sample = [r["balanced_error"] for r in noise_rows
                          if r["method"] == method and r["signal_to_added_noise_db"] == db]
                values.append(f"{db} dB: {np.mean(sample):.3f}")
            lines.append(f"- {METHOD_LABELS[method]}: " + "; ".join(values) + ".")
        lines.append("Mức 0 dB là tỷ số công suất toàn WAV/nhiễu thêm vào; không tương đương SNR tiếng nói sạch.")
    (output / "ghi_chu_slide.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nThống kê huấn luyện (normalized STE):")
    for method in methods:
        model = models[method]
        print(f'  {METHOD_LABELS[method]}: khung={model["frame_ms"]} ms, '
              f'ngưỡng nhị phân={model["binary_threshold"]:.5f}, '
              f'ngưỡng Gaussian={model["statistical_threshold"]:.5f}')
    print(json.dumps(models["statistical"]["statistics"], ensure_ascii=False, indent=2))
    print(f"Đã lưu kết quả tại: {output}")
