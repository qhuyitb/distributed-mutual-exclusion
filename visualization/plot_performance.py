from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

ALGO_LABELS = {
    "centralized": "Centralized",
    "ricart_agrawala": "Ricart-Agrawala",
    "token_ring": "Token Ring",
}

SCENARIO_ORDER = ["low_contention", "high_contention", "round_robin"]

METRICS = [
    ("duration_seconds", "Duration (s)"),
    ("total_messages", "Total Messages"),
    ("avg_waiting_time", "Avg Waiting Time (s)"),
    ("max_waiting_time", "Max Waiting Time (s)"),
]


def _load_records() -> list[dict[str, Any]]:
    json_file = ROOT / "compare_benchmark_all.json"
    csv_file = ROOT / "compare_benchmark_all.csv"

    if json_file.exists():
        with json_file.open("r", encoding="utf-8") as f:
            records = json.load(f)
        return records

    if csv_file.exists():
        with csv_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        for record in records:
            for key in [
                "duration_seconds",
                "total_messages",
                "avg_waiting_time",
                "max_waiting_time",
            ]:
                record[key] = float(record[key])
        return records

    raise FileNotFoundError(
        "Can not find compare_benchmark_all.json or compare_benchmark_all.csv in project root"
    )


def _normalize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for rec in records:
        if not rec.get("success", True):
            continue

        algo = str(rec["algorithm"]).strip().lower()
        scenario = str(rec["scenario_name"]).strip().lower()

        normalized.append(
            {
                "algorithm": algo,
                "scenario_name": scenario,
                "duration_seconds": float(rec["duration_seconds"]),
                "total_messages": float(rec["total_messages"]),
                "avg_waiting_time": float(rec["avg_waiting_time"]),
                "max_waiting_time": float(rec["max_waiting_time"]),
            }
        )
    return normalized


def _build_scenario_matrix(
    records: list[dict[str, Any]],
) -> tuple[list[str], dict[str, dict[str, dict[str, float]]]]:
    scenarios = [s for s in SCENARIO_ORDER if any(r["scenario_name"] == s for r in records)]
    matrix: dict[str, dict[str, dict[str, float]]] = {}

    for rec in records:
        algo = rec["algorithm"]
        scenario = rec["scenario_name"]
        matrix.setdefault(algo, {})[scenario] = {
            metric_key: rec[metric_key] for metric_key, _ in METRICS
        }

    return scenarios, matrix


def _plot_by_scenario(
    scenarios: list[str], matrix: dict[str, dict[str, dict[str, float]]]
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    algo_keys = [k for k in ALGO_LABELS if k in matrix]
    x_positions = list(range(len(scenarios)))
    bar_width = 0.22

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    axes_flat = axes.flatten()

    for ax, (metric_key, metric_label) in zip(axes_flat, METRICS):
        for idx, algo_key in enumerate(algo_keys):
            values = [matrix[algo_key][scenario][metric_key] for scenario in scenarios]
            shifts = [x + (idx - (len(algo_keys) - 1) / 2.0) * bar_width for x in x_positions]
            ax.bar(shifts, values, width=bar_width, label=ALGO_LABELS[algo_key])

        ax.set_title(metric_label)
        ax.set_xticks(x_positions)
        ax.set_xticklabels([s.replace("_", " ").title() for s in scenarios], rotation=10)
        ax.grid(axis="y", linestyle="--", alpha=0.35)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.suptitle("Performance Comparison by Scenario", y=0.99, fontsize=14)
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.955),
        ncol=len(algo_keys),
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.87])

    output_path = OUTPUT_DIR / "performance_by_scenario.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def _plot_overall_summary(matrix: dict[str, dict[str, dict[str, float]]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    algo_keys = [k for k in ALGO_LABELS if k in matrix]

    summary_values: dict[str, dict[str, float]] = {metric_key: {} for metric_key, _ in METRICS}

    for metric_key, _ in METRICS:
        for algo_key in algo_keys:
            values = [metric_map[metric_key] for metric_map in matrix[algo_key].values()]
            summary_values[metric_key][algo_key] = mean(values)

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes_flat = axes.flatten()

    for ax, (metric_key, metric_label) in zip(axes_flat, METRICS):
        values = [summary_values[metric_key][algo] for algo in algo_keys]
        labels = [ALGO_LABELS[algo] for algo in algo_keys]
        ax.bar(labels, values)
        ax.set_title(f"Mean {metric_label}")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.tick_params(axis="x", rotation=12)

    fig.suptitle("Overall Performance Summary (Mean Across Scenarios)", y=0.98, fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    output_path = OUTPUT_DIR / "performance_overall_mean.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def _export_summary_csv(matrix: dict[str, dict[str, dict[str, float]]]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "performance_summary.csv"

    rows: list[dict[str, Any]] = []
    for algo_key, scenarios_map in matrix.items():
        for scenario, metrics_map in scenarios_map.items():
            rows.append(
                {
                    "algorithm": ALGO_LABELS.get(algo_key, algo_key),
                    "scenario": scenario,
                    **metrics_map,
                }
            )

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "algorithm",
                "scenario",
                "duration_seconds",
                "total_messages",
                "avg_waiting_time",
                "max_waiting_time",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main() -> None:
    records = _normalize(_load_records())
    scenarios, matrix = _build_scenario_matrix(records)

    fig1 = _plot_by_scenario(scenarios, matrix)
    fig2 = _plot_overall_summary(matrix)
    csv_out = _export_summary_csv(matrix)

    print("Generated files:")
    print(f"- {fig1}")
    print(f"- {fig2}")
    print(f"- {csv_out}")


if __name__ == "__main__":
    main()
