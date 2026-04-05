"""
Chương trình demo cho Simulation + Testing Engine.

Module này dùng FakeAdapter để:
- Chạy thử các scenario mặc định
- Kiểm tra runner hoạt động đúng
- Kiểm tra metrics hoạt động đúng
- In kết quả tóm tắt ra màn hình

Đây là điểm khởi đầu để TV4 chứng minh engine đã chạy được.
"""

from __future__ import annotations

from simulation.fake_adapter import FakeAdapter
from simulation.runner import SimulationRunner, summarize_result
from simulation.scenarios import get_default_scenarios


def print_result(result_summary: dict) -> None:
    """
    In kết quả mô phỏng ra màn hình theo dạng dễ đọc.

    Args:
        result_summary: Dữ liệu tóm tắt kết quả mô phỏng
    """
    print("=" * 70)
    print(f"Scenario: {result_summary['scenario_name']}")
    print(f"Total events: {result_summary['total_events']}")
    print(f"Total messages: {result_summary['total_messages']}")
    print(f"CS entries: {result_summary['cs_entries']}")
    print(f"Average wait time (ms): {result_summary['avg_wait_time_ms']:.2f}")
    print(f"Max wait time (ms): {result_summary['max_wait_time_ms']:.2f}")
    print(
        "Mutual exclusion violations: "
        f"{result_summary['mutual_exclusion_violations']}"
    )
    print(f"Fairness violations: {result_summary['fairness_violations']}")
    print("=" * 70)


def main() -> None:
    """
    Hàm main chạy demo Simulation Engine.
    """
    adapter = FakeAdapter()
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=300)

    scenarios = get_default_scenarios()

    for scenario_name, scenario in scenarios.items():
        print(f"\nRunning scenario: {scenario_name}")
        result = runner.run(scenario)
        summary = summarize_result(result)
        print_result(summary)


if __name__ == "__main__":
    main()