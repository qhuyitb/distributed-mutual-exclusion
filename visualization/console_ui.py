from __future__ import annotations

import argparse
import os
import sys
import time
import webbrowser
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from simulation.adapters import CentralizedAdapter, RicartAgrawalaAdapter, TokenRingAdapter
from simulation.benchmark import run_benchmark, summarize_results
from simulation.contracts import EventType, SimulationResult

import plot_performance

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    HAS_RICH = True
except Exception:
    HAS_RICH = False


OUTPUT_DIR = Path(__file__).resolve().parent / "output"

ALGORITHM_CONFIGS: List[Tuple[str, Callable]] = [
    ("centralized", CentralizedAdapter),
    ("ricart_agrawala", RicartAgrawalaAdapter),
    ("token_ring", TokenRingAdapter),
]

SCENARIOS = ["low_contention", "high_contention", "round_robin"]


def _console() -> Console | None:
    if HAS_RICH:
        return Console()
    return None


def _print_header(title: str) -> None:
    console = _console()
    if console:
        console.print(Panel.fit(title, border_style="cyan"))
    else:
        print("=" * 80)
        print(title)
        print("=" * 80)


def _run_all_benchmarks() -> List[SimulationResult]:
    all_results: List[SimulationResult] = []
    console = _console()

    for algo_name, adapter_cls in ALGORITHM_CONFIGS:
        text = f"Running benchmark for {algo_name}"
        if console:
            console.print(f"[bold blue]>>[/bold blue] {text}")
        else:
            print(f">> {text}")

        results = run_benchmark(
            adapter_factory=adapter_cls,
            scenario_names=SCENARIOS,
            post_run_wait_seconds=1.0,
        )
        all_results.extend(results)

    return all_results


def _show_summary_table(results: List[SimulationResult]) -> None:
    summary = summarize_results(results)
    console = _console()

    if console:
        table = Table(title="Benchmark Summary")
        table.add_column("Algorithm", style="bold")
        table.add_column("Scenario")
        table.add_column("Duration(s)", justify="right")
        table.add_column("Messages", justify="right")
        table.add_column("Avg Wait(s)", justify="right")
        table.add_column("Max Wait(s)", justify="right")
        table.add_column("Success", justify="center")

        for item in summary:
            table.add_row(
                str(item["algorithm"]),
                str(item["scenario_name"]),
                f"{float(item['duration_seconds']):.3f}",
                str(item["total_messages"]),
                f"{float(item['avg_waiting_time']):.4f}",
                f"{float(item['max_waiting_time']):.4f}",
                "OK" if item["success"] else "FAIL",
            )

        console.print(table)
        return

    print("\nBenchmark Summary")
    print(
        "algorithm | scenario | duration(s) | messages | avg_wait(s) | max_wait(s) | success"
    )
    for item in summary:
        print(
            f"{item['algorithm']} | {item['scenario_name']} | {float(item['duration_seconds']):.3f}"
            f" | {item['total_messages']} | {float(item['avg_waiting_time']):.4f}"
            f" | {float(item['max_waiting_time']):.4f} | {'OK' if item['success'] else 'FAIL'}"
        )


def _select_replay_result(results: List[SimulationResult], scenario: str) -> SimulationResult | None:
    for algorithm in ["centralized", "ricart_agrawala", "token_ring"]:
        for result in results:
            if result.algorithm.value == algorithm and result.scenario_name == scenario:
                return result
    return results[0] if results else None


def _format_event_line(base_ts: float, idx: int, result: SimulationResult, inside_cs: set[int], waiting_nodes: set[int]) -> str:
    event = result.events[idx]
    t_rel = event.timestamp - base_ts
    node = "-" if event.node_id is None else str(event.node_id)
    peer = "-" if event.peer_id is None else str(event.peer_id)
    msg = "-" if event.message_type is None else event.message_type.value

    if event.event_type == EventType.REQUEST_CS and event.node_id is not None:
        waiting_nodes.add(event.node_id)
    elif event.event_type == EventType.ENTER_CS and event.node_id is not None:
        waiting_nodes.discard(event.node_id)
        inside_cs.add(event.node_id)
    elif event.event_type == EventType.EXIT_CS and event.node_id is not None:
        inside_cs.discard(event.node_id)

    state = (
        f"inside_cs={sorted(list(inside_cs))}; waiting={sorted(list(waiting_nodes))}"
    )
    return (
        f"[{t_rel:7.3f}s] {event.event_type.value:16} node={node:>2} "
        f"peer={peer:>2} msg={msg:>7} | {state}"
    )


def replay_flow(result: SimulationResult, speed: float = 12.0) -> None:
    _print_header(
        f"Flow Replay | algo={result.algorithm.value} | scenario={result.scenario_name}"
    )

    if not result.events:
        print("No events to replay")
        return

    base_ts = min(event.timestamp for event in result.events)
    inside_cs: set[int] = set()
    waiting_nodes: set[int] = set()

    previous_t_rel = 0.0
    for idx in range(len(result.events)):
        event = result.events[idx]
        current_t_rel = event.timestamp - base_ts
        wait = max(0.0, (current_t_rel - previous_t_rel) / speed)
        if wait > 0:
            time.sleep(wait)

        line = _format_event_line(base_ts, idx, result, inside_cs, waiting_nodes)
        print(line)
        previous_t_rel = current_t_rel

    print("Replay completed")


def generate_charts() -> None:
    _print_header("Generating visualization charts")
    plot_performance.main()


def open_charts() -> None:
    _print_header("Opening generated charts")

    targets = [
        OUTPUT_DIR / "performance_by_scenario.png",
        OUTPUT_DIR / "performance_overall_mean.png",
    ]

    missing = [path for path in targets if not path.exists()]
    if missing:
        print("Missing chart files. Generating charts first...")
        generate_charts()

    for chart in targets:
        if chart.exists():
            try:
                if os.name == "nt":
                    os.startfile(str(chart))  # type: ignore[attr-defined]
                else:
                    webbrowser.open(chart.as_uri())
                print(f"Opened: {chart}")
            except Exception as exc:
                print(f"Can not open {chart}: {exc}")


def run_dashboard(scenario_for_replay: str = "high_contention", replay_speed: float = 12.0) -> None:
    _print_header("Distributed Mutual Exclusion - Console Dashboard")
    results = _run_all_benchmarks()
    _show_summary_table(results)

    selected = _select_replay_result(results, scenario_for_replay)
    if selected is not None:
        replay_flow(selected, speed=replay_speed)


def interactive_menu() -> None:
    while True:
        print("\n=== Console UI Menu ===")
        print("1) Run dashboard (benchmark + summary + replay)")
        print("2) Generate charts")
        print("3) Open charts")
        print("4) Exit")
        choice = input("Select: ").strip()

        if choice == "1":
            run_dashboard()
        elif choice == "2":
            generate_charts()
        elif choice == "3":
            open_charts()
        elif choice == "4":
            print("Bye")
            return
        else:
            print("Invalid choice")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Console UI for monitoring simulation flow and visualization charts"
    )
    parser.add_argument(
        "--mode",
        choices=["menu", "dashboard", "charts", "open-charts", "all"],
        default="menu",
        help="Execution mode",
    )
    parser.add_argument(
        "--scenario",
        default="high_contention",
        choices=SCENARIOS,
        help="Scenario used for flow replay in dashboard",
    )
    parser.add_argument(
        "--replay-speed",
        type=float,
        default=12.0,
        help="Replay speed factor (higher means faster)",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.mode == "menu":
        interactive_menu()
        return 0

    if args.mode == "dashboard":
        run_dashboard(scenario_for_replay=args.scenario, replay_speed=args.replay_speed)
        return 0

    if args.mode == "charts":
        generate_charts()
        return 0

    if args.mode == "open-charts":
        open_charts()
        return 0

    if args.mode == "all":
        run_dashboard(scenario_for_replay=args.scenario, replay_speed=args.replay_speed)
        generate_charts()
        open_charts()
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
