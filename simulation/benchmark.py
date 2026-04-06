from __future__ import annotations

import json
from typing import Callable, Iterable, List, Optional

from simulation.contracts import AlgorithmAdapter, SimulationResult
from simulation.runner import SimulationRunner, summarize_result
from simulation.scenarios import get_default_scenarios


def run_benchmark(
    adapter_factory: Callable[[], AlgorithmAdapter],
    scenario_names: Optional[Iterable[str]] = None,
    post_run_wait_seconds: float = 1.0,
) -> List[SimulationResult]:
    scenarios = get_default_scenarios()

    if scenario_names is None:
        # Mặc định chỉ chạy các scenario benchmark cơ bản.
        # node_crash_recover để riêng vì nhiều adapter chưa hỗ trợ fault injection.
        selected_names = ["low_contention", "high_contention", "round_robin"]
    else:
        selected_names = list(scenario_names)

    results: List[SimulationResult] = []

    for scenario_name in selected_names:
        if scenario_name not in scenarios:
            raise ValueError(
                f"Unknown scenario '{scenario_name}'. Available: {list(scenarios.keys())}"
            )

        adapter = adapter_factory()
        runner = SimulationRunner(
            adapter=adapter,
            post_run_wait_seconds=post_run_wait_seconds,
        )

        result = runner.run(scenarios[scenario_name])
        results.append(result)

    return results


def summarize_results(results: List[SimulationResult]) -> List[dict]:
    return [summarize_result(result) for result in results]


def print_results_table(results: List[SimulationResult]) -> None:
    summaries = summarize_results(results)

    headers = [
        "scenario",
        "success",
        "messages",
        "requests",
        "entries",
        "avg_wait",
        "max_wait",
        "mutex_vio",
        "fair_vio",
        "duration",
    ]

    rows = []
    for item in summaries:
        rows.append(
            [
                item["scenario_name"],
                str(item["success"]),
                str(item["total_messages"]),
                str(item["request_count"]),
                str(item["cs_entries"]),
                f'{item["avg_waiting_time"]:.4f}' if isinstance(item["avg_waiting_time"], (int, float)) else str(item["avg_waiting_time"]),
                f'{item["max_waiting_time"]:.4f}' if isinstance(item["max_waiting_time"], (int, float)) else str(item["max_waiting_time"]),
                str(item["mutual_exclusion_violations"]),
                str(item["fairness_violations"]),
                f'{item["duration_seconds"]:.3f}' if isinstance(item["duration_seconds"], (int, float)) else str(item["duration_seconds"]),
            ]
        )

    widths = [len(h) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(value))

    def fmt_row(values: List[str]) -> str:
        return " | ".join(value.ljust(widths[i]) for i, value in enumerate(values))

    divider = "-+-".join("-" * width for width in widths)

    print(fmt_row(headers))
    print(divider)
    for row in rows:
        print(fmt_row(row))


def export_results_to_json(results: List[SimulationResult], output_path: str) -> None:
    summaries = summarize_results(results)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)


def export_results_to_csv(results: List[SimulationResult], output_path: str) -> None:
    summaries = summarize_results(results)

    headers = [
        "algorithm",
        "scenario_name",
        "success",
        "duration_seconds",
        "total_events",
        "total_messages",
        "request_count",
        "cs_entries",
        "avg_waiting_time",
        "max_waiting_time",
        "mutual_exclusion_violations",
        "fairness_violations",
        "messages_by_type",
        "entries_by_node",
        "errors",
    ]

    def escape_csv(value) -> str:
        text = str(value)
        text = text.replace('"', '""')
        return f'"{text}"'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(",".join(headers) + "\n")
        for item in summaries:
            row = [
                item.get("algorithm"),
                item.get("scenario_name"),
                item.get("success"),
                item.get("duration_seconds"),
                item.get("total_events"),
                item.get("total_messages"),
                item.get("request_count"),
                item.get("cs_entries"),
                item.get("avg_waiting_time"),
                item.get("max_waiting_time"),
                item.get("mutual_exclusion_violations"),
                item.get("fairness_violations"),
                item.get("messages_by_type"),
                item.get("entries_by_node"),
                item.get("errors"),
            ]
            f.write(",".join(escape_csv(value) for value in row) + "\n")