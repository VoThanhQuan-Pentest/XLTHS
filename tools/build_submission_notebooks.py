"""Tạo và thực thi ba notebook tự chứa cho bộ nộp nhóm 03, không sao chép dữ liệu."""

from __future__ import annotations

import argparse
import ast
import base64
import csv
import hashlib
import json
import os
from pathlib import Path
import sys

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "03-Phân đoạn tín hiệu thành tiếng nói và khoảng lặng"
BUILD = ROOT / ".notebook-build"
STUDENTS = (
    ("binary", "Võ Thanh Quân", "TT1_BinarySearch", "VoThanhQuan_BinarySearch.ipynb", "Binary Search"),
    ("histogram", "Vương Quốc Trung", "TT2_Histogram", "VuongQuocTrung_Histogram.ipynb", "Histogram"),
    ("statistical", "Đinh Huỳnh Nguyên Khang", "TT3_Statistics", "DinhHuynhNguyenKhang_Statistics.ipynb", "Statistical Gaussian"),
)


def source_of(relative_path: str, names: list[str]) -> str:
    """Nhận tệp nguồn và tên định nghĩa; trả mã đầy đủ gồm decorator, docstring và comments."""
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    lines = text.splitlines()
    nodes = {node.name: node for node in ast.parse(text).body
             if isinstance(node, (ast.ClassDef, ast.FunctionDef))}
    parts = []
    for name in names:
        node = nodes[name]
        first = min([node.lineno] + [d.lineno for d in node.decorator_list])
        parts.append("\n".join(lines[first - 1:node.end_lineno]))
    return "\n\n\n".join(parts)


def specialized_training(method: str) -> str:
    """Nhận tên thuật toán; trả mã fit/predict/CV riêng, tương đương phép tính trong repo."""
    # Mỗi notebook có một phương pháp duy nhất, không mang mã hai phương pháp còn lại.
    fit_parts = {
        "binary": 'model["binary_threshold"] = binary_threshold(sil, sp)',
        "statistical": 'model["statistical_threshold"], model["statistics"] = gaussian_threshold(sil, sp)',
        "histogram": '''fallback = float(np.clip((np.median(sil) + np.median(sp)) / 2.0, 0.0, 1.0))
    try:
        fallback, _ = histogram_threshold(np.concatenate([sil, sp]), config)
    except ValueError:
        pass
    model.update(histogram=asdict(config), histogram_fallback=fallback)''',
    }
    prediction_parts = {
        "binary": 'threshold = model["binary_threshold"]',
        "statistical": 'threshold = model["statistical_threshold"]',
        "histogram": '''threshold, fallback_used = histogram_threshold(
        features.normalized_ste, HistogramConfig(**model["histogram"]), model["histogram_fallback"]
    )''',
    }
    candidates = ('[HistogramConfig(b, s, w, distance, depth)\n'
                  '                  for b in (32, 64, 128) for s in (1, 3, 5)\n'
                  '                  for w in (2, 5, 10) for distance in (3, 6, 12)\n'
                  '                  for depth in (0.2, 0.4)]' if method == "histogram" else "[None]")
    tie = ("(config.bins, config.smooth, config.weight, config.min_peak_distance, config.min_valley_depth)"
           if method == "histogram" else "()")
    return f'''def fit_model(records: list[Record], config=None) -> dict:
    """Nhận training và cấu hình nếu có; trả mô hình chỉ học từ các khung training có nhãn."""
    # Khối 1: Gom STE và kiểm tra hai lớp trước khi học ngưỡng.
    sil, sp = training_arrays(records)
    if not len(sil) or not len(sp):
        raise ValueError("Training phải có cả Speech và Silence")
    model = {{"frame_ms": FRAME_MS, "hop_ms": HOP_MS, "minimum_silence_ms": MIN_SILENCE_MS}}

    # Khối 2: Tính ngưỡng bằng thuật toán riêng của notebook này.
    {fit_parts[method]}
    return model


def predict_signal(samples: np.ndarray, fs: int, model: dict,
                   compute_f0: bool = True) -> tuple[Features, np.ndarray, float, bool]:
    """Nhận WAV/mô hình, không nhận LAB; trả đặc trưng, nhãn dự đoán, ngưỡng và cờ fallback."""
    # Khối 1: Mô hình và đặc trưng phải cùng cấu hình 25/10 ms.
    if model.get("frame_ms") != FRAME_MS or model.get("hop_ms") != HOP_MS:
        raise ValueError("Cần huấn luyện lại mô hình ở 25/10 ms")
    features = extract(samples, fs, FRAME_MS, HOP_MS, compute_f0=compute_f0)
    fallback_used = False

    # Khối 2: Áp dụng ngưỡng, sau đó gộp Silence ảo ngắn hơn 200 ms.
    {prediction_parts[method]}
    raw_mask = features.normalized_ste >= threshold
    mask = remove_virtual_silence(raw_mask, features.edges, MIN_SILENCE_MS / 1000)
    return features, mask, float(threshold), fallback_used


def train_model(records: list[Record]) -> tuple[dict, dict]:
    """Nhận bốn WAV training; trả mô hình cuối và chỉ số kiểm chứng chéo, không dùng test."""
    # Khối 1: Không khảo sát frame; chỉ Histogram có tập cấu hình riêng để chọn.
    candidates = {candidates}
    best_key, best_config, validation = None, None, None
    for config in candidates:
        scores = []
        for held in range(len(records)):
            training = [r for i, r in enumerate(records) if i != held]
            model = fit_model(training, config)

            # Khối 2: Kiểm chứng bằng WAV giữ lại trong training, không phải WAV test.
            record = records[held]
            f, mask, _, _ = predict_signal(record.samples, record.fs, model, compute_f0=False)
            scores.append(score(record, f, mask))
        tie = {tie}
        key = (round(float(np.mean([s["balanced_error"] for s in scores])), 10),
               sum(s["missed"] + s["extra"] for s in scores),
               np.mean([s["mae_ms"] if s["mae_ms"] is not None else 200 for s in scores])) + tie

        # Khối 3: Chọn theo training rồi học lại bằng tất cả bốn bản ghi training.
        if best_key is None or key < best_key:
            best_key, best_config = key, config
            validation = {{"balanced_error": key[0], "boundary_misses": key[1], "mean_mae_ms": float(key[2])}}
    return fit_model(records, best_config), validation
'''


SUMMARY_AND_MAIN = '''def display_summary(rows: list[dict]) -> dict:
    """Nhận số liệu bốn WAV; hiển thị bảng và trả MAE/RMSE gộp cùng số biên ghép/thừa/thiếu."""
    # Khối 1: Bảng kết quả từng WAV, tất cả sai số theo mili-giây.
    lines = ["### Bảng kết quả trên toàn bộ tập test", "",
             "| WAV | Ngưỡng | MAE (ms) | RMSE (ms) | Ghép/thừa/thiếu | BER |",
             "|---|---:|---:|---:|---|---:|"]
    for row in rows:
        lines.append(f'| {row["wav"]} | {row["threshold"]:.8f} | {format_metric(row["mae_ms"])} | '
                     f'{format_metric(row["rmse_ms"])} | {row["matched"]}/{row["extra"]}/{row["missed"]} | '
                     f'{row["balanced_error"]:.4f} |')

    # Khối 2: Gộp theo số cặp ghép; không lấy trung bình RMSE của từng WAV.
    count = sum(row["matched"] for row in rows)
    mae = sum(row["mae_ms"] * row["matched"] for row in rows if row["mae_ms"] is not None) / count if count else None
    rmse = np.sqrt(sum(row["rmse_ms"] ** 2 * row["matched"] for row in rows
                       if row["rmse_ms"] is not None) / count) if count else None
    pooled = {"mae_ms": mae, "rmse_ms": float(rmse) if rmse is not None else None,
              "matched": count, "extra": sum(r["extra"] for r in rows), "missed": sum(r["missed"] for r in rows)}
    lines.append(f'| **Gộp biên** | | **{format_metric(mae)}** | **{format_metric(rmse)}** | '
                 f'{pooled["matched"]}/{pooled["extra"]}/{pooled["missed"]} | |')
    display(Markdown("\\n".join(lines)))
    return pooled


def main() -> dict:
    """Chạy riêng một thuật toán; trả mô hình/số liệu và giữ test trong bộ nhớ cho phân tích nhiễu."""
    # Khối 1: Training được đọc từ dữ liệu ngoài notebook; không đóng gói WAV/LAB.
    training = [read_record(p) for p in discover(DATA_ROOT, "TinHieuHuanLuyen")]
    if len(training) != 4:
        raise ValueError("Bài thực nghiệm yêu cầu đúng bốn WAV training")
    print("Thành viên:", STUDENT, "— Thuật toán:", METHOD_LABELS[METHOD])
    print("Phân khung cố định:", FRAME_MS, "ms; bước dịch:", HOP_MS, "ms")
    print("Training:", ", ".join(r.name + ".wav" for r in training))

    # Khối 2: Học và khóa tham số trước khi dùng test; in rõ mô hình đã học.
    model, validation = train_model(training)
    display(Markdown("### Tham số học từ training và kết quả kiểm chứng chéo"))
    print(json.dumps({"model": model, "validation": validation}, ensure_ascii=False, indent=2))
    test = [read_record(p) for p in discover(DATA_ROOT, "TinHieuKiemThu")]
    if len(test) != 4:
        raise ValueError("Bài thực nghiệm yêu cầu đúng bốn WAV test")
    rows = []

    # Khối 3: Mỗi WAV test sinh một figure với đặc trưng, F0, biên xanh/đỏ và bình luận.
    for number, record in enumerate(test, 1):
        features, mask, threshold, fallback = predict_signal(record.samples, record.fs, model)
        metrics = score(record, features, mask)
        rows.append({"wav": record.name, "method": METHOD, "threshold": threshold,
                     "histogram_fallback": fallback, "snr_estimate_db": estimate_snr(record), **metrics})
        fig = plot_result(record, METHOD, features, mask, threshold, metrics, fig_num=number)
        display(fig)
        plt.close(fig)

        # Khối 4: LAB test chỉ dùng để đánh giá và giải thích sau dự đoán.
        result = {METHOD: {"features": features, "mask": mask, "threshold": threshold,
                           "metrics": metrics, "fallback": fallback}}
        display(Markdown("\\n".join(figure_comments(record, result, METHOD_LABELS))))
    pooled = display_summary(rows)
    return {"model": model, "validation": validation, "rows": rows, "pooled": pooled, "test_records": test}
'''


NOISE_CODE = '''def analyze_noise(records: list[Record], model: dict) -> list[dict]:
    """Nhận WAV test/mô hình đã khóa; trả BER trung bình khi cộng nhiễu, không huấn luyện lại."""
    # Khối 1: SNR nền dùng LAB để phân tích sau dự đoán, không điều chỉnh mô hình.
    lines = ["### SNR nền ước lượng từ các vùng có nhãn", "", "| WAV | SNR (dB) |", "|---|---:|"]
    for record in records:
        value = estimate_snr(record)
        lines.append(f"| {record.name} | {value:.1f} |" if value is not None else f"| {record.name} | KXĐ |")
    display(Markdown("\\n".join(lines)))

    # Khối 2: Nhiễu trắng đặt theo công suất toàn WAV, dùng ba seed như chương trình gốc.
    summary = []
    for db in (30, 20, 10, 0):
        errors = []
        for record in records:
            power = float(np.mean(record.samples ** 2))
            for seed in (2026, 2027, 2028):
                rng = np.random.default_rng(seed)
                added = rng.normal(0, np.sqrt(power / (10 ** (db / 10))), len(record.samples))

                # Khối 3: Ngưỡng/hyperparameter không học lại từ kết quả khảo sát.
                f, mask, _, _ = predict_signal(record.samples + added, record.fs, model, compute_f0=False)
                errors.append(score(record, f, mask)["balanced_error"])
        summary.append({"signal_to_added_noise_db": db, "balanced_error": float(np.mean(errors))})
    table = ["### Khảo sát nhiễu bổ sung", "", "| Q (dB) | BER trung bình |", "|---:|---:|"]
    table.extend(f'| {r["signal_to_added_noise_db"]} | {r["balanced_error"]:.3f} |' for r in summary)
    display(Markdown("\\n".join(table)))
    return summary


NOISE_SUMMARY = analyze_noise(RESULT["test_records"], RESULT["model"])
'''


def build_notebook(method: str, student: str, folder: str, label: str):
    """Nhận thông tin thành viên; trả notebook chỉ chứa thuật toán đó và toàn bộ hàm hỗ trợ."""
    cells = []
    def markdown(text):
        """Thêm văn bản giải thích vào danh sách cell, không tạo output giả."""
        cells.append(nbformat.v4.new_markdown_cell(text))
    def code(text):
        """Thêm mã nguồn hiển thị đầy đủ và kiểm tra cú pháp trước khi thực thi."""
        ast.parse(text)
        cells.append(nbformat.v4.new_code_cell(text))

    markdown(f"# Nhóm 03 — Phân đoạn tín hiệu thành tiếng nói và khoảng lặng\n\n"
             f"**Sinh viên: {student}**  \n**Thuật toán riêng: {label}**\n\n"
             "Notebook chứa mã và kết quả thực thi sẵn. Mở để đọc kết quả không cần WAV. "
             "Để chạy lại, cung cấp dữ liệu ngoài notebook và chỉnh DATA_ROOT. Không nộp WAV/LAB cùng file này.\n\n"
             "Khung 25 ms, bước dịch 10 ms, Silence tối thiểu 200 ms. "
             "LAB training dùng để học/kiểm chứng; LAB test chỉ đánh giá và vẽ biên chuẩn.")
    markdown("## 1. Thư viện và cấu hình\n\nChỉ dùng NumPy và thư viện chuẩn để xử lý tín hiệu. "
             "Matplotlib/IPython phục vụ vẽ và lưu kết quả hiển thị trong notebook.")
    code(f'''from __future__ import annotations

from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
import json
import math
import wave

import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
from matplotlib_inline.backend_inline import set_matplotlib_formats

# Hiển thị PNG trực tiếp và lưu trong output của notebook, không mở cửa sổ GUI.
get_ipython().run_line_magic("matplotlib", "inline")
set_matplotlib_formats("png")
FRAME_MS, HOP_MS, MIN_SILENCE_MS = 25, 10, 200
METHOD, STUDENT = {method!r}, {student!r}
METHOD_LABELS = {{METHOD: {label!r}}}

# Khi thực thi bộ nộp tại máy, kernel làm việc ở thư mục chứa các tập dữ liệu.
# Nếu chạy lại trên máy khác, đặt DATA_ROOT đến nơi có hai tập WAV/LAB gốc.
DATA_ROOT = Path.cwd()
''')
    markdown("## 2. Đọc WAV/LAB và gán nhãn\n\nGhép WAV/LAB theo tên gốc. "
             "sil là Silence, v/uv là Speech. Nhãn khung lấy theo tâm khung; bỏ phần chưa có nhãn.")
    code(source_of("speech_silence/data.py", ["Interval", "Record", "discover", "read_labels", "read_record", "speech_at", "reference_boundaries"]))
    markdown("## 3. Đặc trưng ngắn hạn, F0 và hậu xử lý\n\nTính STE/MA trực tiếp từ mẫu; "
             "STE chuẩn hóa theo cực đại của mỗi WAV. F0 minh họa bằng tự tương quan; "
             "không dùng F0 để tìm ngưỡng. Silence dự đoán dưới 200 ms chuyển thành Speech.")
    code(source_of("speech_silence/features.py", ["Features", "extract", "estimate_f0", "remove_virtual_silence", "segments", "predicted_boundaries"]))
    explanations = {
        "binary": "Hai nhóm STE có nhãn từ cả bốn WAV training được gom để học một ngưỡng chung. "
                  "Chia đôi miền ngưỡng đến khi độ rộng nhỏ hơn 10⁻⁸. Tiêu chí cân bằng độ lệch năng lượng, không chỉ đếm khung sai.",
        "histogram": "Training chỉ chọn cấu hình/fallback; ngưỡng chính tính adaptive trên mỗi WAV. "
                     "Xét đỉnh bin 0, vị trí vùng nền, valley và khoảng cách giữa đỉnh. Giả định năng lượng nền thấp có giới hạn khi hai lớp chồng lấn.",
        "statistical": "Ước lượng mean/std của hai nhóm normalized STE training, giả thiết Gaussian. "
                       "Chọn một ngưỡng chung có lỗi kỳ vọng cân bằng nhỏ nhất. Các thống kê và ngưỡng được in ở phần kết quả.",
    }
    markdown(f"## 4. Thuật toán {label}\n\n{explanations[method]}")
    names = {"binary": ["binary_threshold"],
             "histogram": ["HistogramConfig", "smooth_1d", "histogram_local_maxima", "histogram_peak_pair", "histogram_threshold"],
             "statistical": ["normal_cdf", "gaussian_threshold"]}[method]
    code(source_of(f"{folder}/algorithm.py", names))
    markdown("## 5. Đánh giá biên và lỗi phân lớp\n\nGhép biên cùng hướng, một-một theo thứ tự; "
             "không áp dụng dung sai 200 ms khi ghép. MAE/RMSE tính bằng ms trên các cặp ghép. "
             "Luôn báo thêm biên thừa/thiếu vì chúng không đi vào MAE của cặp đã ghép.")
    code(source_of("speech_silence/evaluation.py", ["boundary_scores", "score", "estimate_snr"]))
    markdown("## 6. Huấn luyện và khóa tham số\n\nKhung luôn cố định 25/10 ms. "
             "Kiểm chứng chéo chỉ dùng bốn WAV training. Sau kiểm chứng, học lại từ toàn training trước khi đọc test.")
    code(source_of("speech_silence/pipeline.py", ["training_arrays"]) + "\n\n\n" + specialized_training(method))
    markdown("## 7. Hàm vẽ hình và tạo bình luận\n\nMỗi WAV có một hình với waveform, "
             "normalized STE/ngưỡng, logSTE/logMA, F0. Biên dự đoán xanh, biên chuẩn đỏ. "
             "F0mean LAB chỉ là thống kê tham chiếu, không phải đường F0 chuẩn từng khung.")
    plotting = source_of("speech_silence/pipeline.py", ["plot_result"])
    plotting = plotting.replace("Biên đúng/thừa/thiếu", "Biên ghép/thừa/thiếu")
    plotting = plotting.replace("F0mean chuẩn LAB:", "F0mean LAB:")
    comments = source_of("speech_silence/demo.py", ["format_metric", "figure_comments"])
    comments = comments.replace('f"## {record.name}.png"', 'f"### Nhận xét {record.name}.wav"')
    code(plotting + "\n\n\n" + comments)
    markdown("## 8. Điểm chạy main()\n\nHàm main tự xử lý đủ bốn WAV test, không chọn file thủ công. "
             "Không đọc mô hình/CSV/PNG có sẵn để thay thế việc tính toán.")
    code(SUMMARY_AND_MAIN)
    markdown("## 9. Kết quả đã thực thi\n\nCell dưới đây học ngưỡng/cấu hình từ đầu, "
             "sau đó tính và xuất bốn hình test cùng nhận xét. Các output được giữ nguyên khi lưu file.")
    code("# Một lần gọi main xử lý đủ bốn WAV; kết quả nằm trong output của notebook.\nRESULT = main()")
    markdown("## 10. Nhận xét nhiễu/SNR\n\nSNR nền là ước lượng sau dự đoán. "
             "Q trong khảo sát là tỷ số công suất toàn WAV/nhiễu trắng thêm vào, không phải SNR tiếng nói sạch. "
             "Chỉ biến đổi bốn WAV test hiện có; không dùng kết quả này để chỉnh tham số.")
    code(NOISE_CODE)
    markdown("## 11. Kết luận và giới hạn\n\nĐọc MAE/RMSE cùng số biên thừa/thiếu. "
             "Các nguyên nhân sai trong bình luận là diễn giải từ STE và hậu xử lý, không phải chứng minh nhân quả duy nhất. "
             "Dữ liệu chỉ có bốn WAV test và mỗi WAV hiện có một vùng Speech nhị phân; "
             "kết quả chưa đại diện cho mọi cuộc hội thoại hay môi trường thu âm.")
    code('''# Tóm tắt từ đúng các kết quả vừa tính, không chép số liệu cố định.
p = RESULT["pooled"]
display(Markdown(f'**{METHOD_LABELS[METHOD]}**: MAE gộp **{format_metric(p["mae_ms"])} ms**, '
                 f'RMSE **{format_metric(p["rmse_ms"])} ms**; '
                 f'biên ghép/thừa/thiếu **{p["matched"]}/{p["extra"]}/{p["missed"]}**.'))''')
    nb = nbformat.v4.new_notebook(cells=cells)
    nb.metadata.kernelspec = {"name": "python3", "display_name": "Python 3", "language": "python"}
    return nb


def compare_snapshot(snapshot: dict, folder: str) -> None:
    """Nhận kết quả kernel và thư mục baseline; báo lỗi nếu số liệu khác chương trình hiện hành."""
    package = json.loads((ROOT / folder / "ket_qua/tham_so_huan_luyen.json").read_text())
    expected_model = next(iter(package["models"].values()))
    if snapshot["model"] != expected_model or snapshot["validation"] != next(iter(package["validation"].values())):
        raise ValueError(f"Mô hình hoặc kiểm chứng chéo khác baseline: {folder}")
    with (ROOT / folder / "ket_qua/ket_qua.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for expected, actual in zip(rows, snapshot["rows"], strict=True):
        if expected["wav"] != actual["wav"]:
            raise ValueError("Thứ tự/tên WAV khác baseline")
        for key in ("threshold", "mae_ms", "rmse_ms", "matched", "missed", "extra", "balanced_error"):
            if abs(float(expected[key]) - actual[key]) > 1e-10:
                raise ValueError(f"Sai số liệu {folder}/{actual['wav']}/{key}")
    # Đối chiếu cả bảng khảo sát nhiễu; đây là đánh giá sau chạy, không chọn lại tham số.
    with (ROOT / folder / "ket_qua/khao_sat_nhieu.csv").open(encoding="utf-8-sig") as stream:
        baseline_noise = list(csv.DictReader(stream))
    method = snapshot["rows"][0]["method"]
    for actual in snapshot["noise"]:
        values = [float(row["balanced_error"]) for row in baseline_noise
                  if row["method"] == method and int(row["signal_to_added_noise_db"]) == actual["signal_to_added_noise_db"]]
        if not values or abs(sum(values) / len(values) - actual["balanced_error"]) > 1e-10:
            raise ValueError(f"Bảng nhiễu khác baseline: {method}")


def validate_notebook(nb, filename: str, expected_count: int = 4) -> dict:
    """Nhận notebook đã chạy; kiểm tra output, imports và không có âm thanh/dữ liệu nhúng."""
    nbformat.validate(nb)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    if [c.execution_count for c in code_cells] != list(range(1, len(code_cells) + 1)):
        raise ValueError("Cell chưa được chạy tuần tự từ kernel mới")
    allowed = {"__future__", "dataclasses", "functools", "pathlib", "json", "math", "wave", "numpy", "matplotlib", "matplotlib_inline", "IPython"}
    images = []
    for cell in code_cells:
        for node in ast.walk(ast.parse(cell.source)):
            imported = ([a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else
                        [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) else [])
            if any(name not in allowed for name in imported):
                raise ValueError(f"Notebook phụ thuộc module bên ngoài không cho phép: {imported}")
        for output in cell.outputs:
            if output.output_type == "error":
                raise ValueError("Notebook còn output lỗi")
            data = output.get("data", {})
            if set(data) - {"text/plain", "text/markdown", "image/png"}:
                raise ValueError(f"Output có MIME ngoài nội dung nộp: {set(data)}")
            if any(mime.startswith("audio/") or mime.startswith("video/") for mime in data):
                raise ValueError("Notebook nhúng âm thanh/video")
            if "image/png" in data:
                images.append(base64.b64decode(data["image/png"]))
    if len(images) != expected_count or any(cell.get("attachments") for cell in nb.cells):
        raise ValueError("Số hình test không đúng hoặc có attachment ngoài yêu cầu")
    for index, png in enumerate(images, 1):
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Output ảnh không phải PNG hợp lệ")
        (BUILD / f"{Path(filename).stem}_{index}.png").write_bytes(png)
    return {"code_cells": len(code_cells), "test_figures": len(images), "errors": 0}


def main() -> None:
    """Tạo, thực thi và kiểm tra bộ notebook; tùy chọn --only xây lại riêng một thành viên."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=("binary", "histogram", "statistical"))
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    SUBMISSION.mkdir(exist_ok=True)
    permitted = {r[3] for r in STUDENTS} | {"Slide_Chung_Nhom03.pdf"}
    if any(p.is_dir() or p.name not in permitted for p in SUBMISSION.iterdir()):
        raise ValueError("Thư mục nộp có file ngoài ba notebook/PDF slide chung; không tự xóa dữ liệu người dùng")

    # Kernel chỉ cài trong môi trường cục bộ; metadata file nộp vẫn dùng Python 3 chung.
    os.environ["JUPYTER_PATH"] = str(ROOT / ".venv-notebooks/share/jupyter")
    records = []
    for method, student, folder, filename, label in STUDENTS:
        if args.only and args.only != method:
            continue
        print(f"Đang tạo và chạy: {student} — {label}", flush=True)
        nb = build_notebook(method, student, folder, label)
        audit = nbformat.v4.new_code_cell('print(json.dumps({"model": RESULT["model"], '
                                        '"validation": RESULT["validation"], "rows": RESULT["rows"], '
                                        '"noise": NOISE_SUMMARY}, ensure_ascii=False))')
        nb.cells.append(audit)
        client = NotebookClient(nb, timeout=600, kernel_name="xlths-notebooks",
                                resources={"metadata": {"path": str(ROOT)}}, allow_errors=False)
        client.execute()
        snapshot = json.loads("".join(o.get("text", "") for o in nb.cells[-1].outputs))
        nb.cells.pop()  # Cell đối chiếu nội bộ không thuộc bài nộp; mã tính toán đã chạy giữ nguyên.
        compare_snapshot(snapshot, folder)
        report = validate_notebook(nb, filename)
        path = SUBMISSION / filename
        nbformat.write(nb, path)
        saved = nbformat.read(path, as_version=4)
        nbformat.validate(saved)
        report.update(filename=filename, method=method, student=student, bytes=path.stat().st_size,
                      sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        records.append(report)
        (BUILD / f"{method}_snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Đạt: {filename}; {report['code_cells']} cell đã chạy, 4 hình, khớp baseline.", flush=True)
    (BUILD / "validation.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Thư mục nộp notebook: {SUBMISSION}", flush=True)


if __name__ == "__main__":
    main()
