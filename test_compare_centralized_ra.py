from simulation.contracts import ScenarioDefinition, NodeAction, ActionType
from simulation.runner import SimulationRunner, summarize_result

from simulation.centralized_adapter import CentralizedAdapter
from simulation.ricart_adapter import RicartAgrawalaAdapter

from centralized.coordinator import Coordinator
from centralized.node import Node


def build_scenario():
    return ScenarioDefinition(
        name="compare_low_contention",
        description="Compare Centralized vs Ricart-Agrawala with 3 nodes",
        num_nodes=3,
        network_delay_ms=0,
        actions=[
            NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
            NodeAction(at_ms=500, action_type=ActionType.REQUEST_CS, node_id=2),
            NodeAction(at_ms=1000, action_type=ActionType.REQUEST_CS, node_id=3),
        ],
    )


def run_centralized():
    adapter = CentralizedAdapter(Coordinator, Node)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=8000)
    scenario = build_scenario()
    result = runner.run(scenario)
    return result


def run_ricart():
    adapter = RicartAgrawalaAdapter(base_port=6200)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=20000)
    scenario = build_scenario()
    result = runner.run(scenario)
    return result


def print_result_block(title, result):
    summary = summarize_result(result)

    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")
    print("Summary:")
    print(summary)
    print("\nRaw stats:")
    print(result.raw_stats)
    print("\nTotal events:")
    print(len(result.events))


def print_comparison(centralized_result, ricart_result):
    c = summarize_result(centralized_result)
    r = summarize_result(ricart_result)

    print(f"\n{'=' * 60}")
    print("COMPARISON TABLE")
    print(f"{'=' * 60}")
    print(f"{'Metric':35} {'Centralized':15} {'Ricart-Agrawala':15}")
    print(f"{'-' * 60}")
    print(f"{'Total events':35} {len(centralized_result.events):15} {len(ricart_result.events):15}")
    print(f"{'Total messages':35} {c['total_messages']:15} {r['total_messages']:15}")
    print(f"{'CS entries':35} {c['cs_entries']:15} {r['cs_entries']:15}")
    print(f"{'Avg wait time (ms)':35} {c['avg_wait_time_ms']:.2f}{'':7} {r['avg_wait_time_ms']:.2f}")
    print(f"{'Max wait time (ms)':35} {c['max_wait_time_ms']:.2f}{'':7} {r['max_wait_time_ms']:.2f}")
    print(f"{'Mutual exclusion violations':35} {c['mutual_exclusion_violations']:15} {r['mutual_exclusion_violations']:15}")
    print(f"{'Fairness violations':35} {c['fairness_violations']:15} {r['fairness_violations']:15}")


def main():
    centralized_result = run_centralized()
    ricart_result = run_ricart()

    print_result_block("CENTRALIZED", centralized_result)
    print_result_block("RICART-AGRAWALA", ricart_result)
    print_comparison(centralized_result, ricart_result)


if __name__ == "__main__":
    main()