from simulation.adapters import CentralizedAdapter, RicartAgrawalaAdapter
from simulation.benchmark import (
    export_results_to_csv,
    export_results_to_json,
    print_results_table,
    run_benchmark,
    summarize_results,
)


def main() -> None:
    scenario_names = ["low_contention", "high_contention", "round_robin"]

    print("\n=== CENTRALIZED ===")
    centralized_results = run_benchmark(
        adapter_factory=CentralizedAdapter,
        scenario_names=scenario_names,
        post_run_wait_seconds=1.0,
    )
    print_results_table(centralized_results)

    print("\n=== RICART-AGRAWALA ===")
    ra_results = run_benchmark(
        adapter_factory=RicartAgrawalaAdapter,
        scenario_names=scenario_names,
        post_run_wait_seconds=1.0,
    )
    print_results_table(ra_results)

    all_results = centralized_results + ra_results

    export_results_to_json(all_results, "compare_benchmark.json")
    export_results_to_csv(all_results, "compare_benchmark.csv")

    print("\n=== RAW SUMMARY ===")
    for item in summarize_results(all_results):
        print(item)

    print("\nSaved:")
    print("- compare_benchmark.json")
    print("- compare_benchmark.csv")


if __name__ == "__main__":
    main()