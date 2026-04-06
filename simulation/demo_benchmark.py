from simulation.adapters import CentralizedAdapter
from simulation.benchmark import (
    export_results_to_csv,
    export_results_to_json,
    print_results_table,
    run_benchmark,
)


def main() -> None:
    results = run_benchmark(
        adapter_factory=CentralizedAdapter,
        scenario_names=["low_contention", "high_contention", "round_robin"],
        post_run_wait_seconds=1.0,
    )

    print("\n=== BENCHMARK RESULTS: CENTRALIZED ===")
    print_results_table(results)

    export_results_to_json(results, "centralized_benchmark.json")
    export_results_to_csv(results, "centralized_benchmark.csv")

    print("\nSaved:")
    print("- centralized_benchmark.json")
    print("- centralized_benchmark.csv")


if __name__ == "__main__":
    main()