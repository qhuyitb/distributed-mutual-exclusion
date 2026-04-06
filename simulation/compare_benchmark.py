from simulation.adapters import CentralizedAdapter, RicartAgrawalaAdapter, TokenRingAdapter
from simulation.benchmark import (
    export_results_to_csv,
    export_results_to_json,
    print_results_table,
    run_benchmark,
    summarize_results,
)


def main() -> None:
    scenario_names = ["low_contention", "high_contention", "round_robin"]

    configs = [
        ("CENTRALIZED", CentralizedAdapter),
        ("RICART-AGRAWALA", RicartAgrawalaAdapter),
        ("TOKEN RING", TokenRingAdapter),
    ]

    all_results = []

    for title, adapter_cls in configs:
        print(f"\n=== {title} ===")
        results = run_benchmark(
            adapter_factory=adapter_cls,
            scenario_names=scenario_names,
            post_run_wait_seconds=1.0,
        )
        print_results_table(results)
        all_results.extend(results)

    export_results_to_json(all_results, "compare_benchmark_all.json")
    export_results_to_csv(all_results, "compare_benchmark_all.csv")

    print("\nSaved:")
    print("- compare_benchmark_all.json")
    print("- compare_benchmark_all.csv")

    print("\n=== RAW SUMMARY ===")
    for item in summarize_results(all_results):
        print(item)


if __name__ == "__main__":
    main()