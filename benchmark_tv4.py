import csv
from pathlib import Path

from simulation.contracts import ScenarioDefinition, NodeAction, ActionType
from simulation.runner import SimulationRunner, summarize_result

from simulation.centralized_adapter import CentralizedAdapter
from simulation.ricart_adapter import RicartAgrawalaAdapter

from centralized.coordinator import Coordinator
from centralized.node import Node


OUTPUT_CSV = "tv4_benchmark_results.csv"


def build_low_contention(num_nodes: int):
    actions = []
    for i in range(1, num_nodes + 1):
        actions.append(
            NodeAction(
                at_ms=(i - 1) * 500,
                action_type=ActionType.REQUEST_CS,
                node_id=i,
            )
        )
    return ScenarioDefinition(
        name="low_contention",
        description=f"{num_nodes} nodes request CS with spacing",
        num_nodes=num_nodes,
        network_delay_ms=0,
        actions=actions,
    )


def build_high_contention(num_nodes: int):
    actions = []
    for i in range(1, num_nodes + 1):
        actions.append(
            NodeAction(
                at_ms=0,
                action_type=ActionType.REQUEST_CS,
                node_id=i,
            )
        )
    return ScenarioDefinition(
        name="high_contention",
        description=f"{num_nodes} nodes request CS at same time",
        num_nodes=num_nodes,
        network_delay_ms=0,
        actions=actions,
    )


def build_round_robin(num_nodes: int, rounds: int = 2):
    actions = []
    current_ms = 0
    for _ in range(rounds):
        for i in range(1, num_nodes + 1):
            actions.append(
                NodeAction(
                    at_ms=current_ms,
                    action_type=ActionType.REQUEST_CS,
                    node_id=i,
                )
            )
            current_ms += 500
    return ScenarioDefinition(
        name="round_robin",
        description=f"{num_nodes} nodes request CS in turn for {rounds} rounds",
        num_nodes=num_nodes,
        network_delay_ms=0,
        actions=actions,
    )


def get_scenarios():
    scenarios = []
    for n in [3, 5]:
        scenarios.append(build_low_contention(n))
        scenarios.append(build_high_contention(n))
        scenarios.append(build_round_robin(n, rounds=2))
    return scenarios


def run_centralized(scenario: ScenarioDefinition):
    adapter = CentralizedAdapter(Coordinator, Node)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=15000)
    return runner.run(scenario)


def run_ricart(scenario: ScenarioDefinition):
    base_port = 7000 + scenario.num_nodes * 100
    if scenario.name == "high_contention":
        base_port += 20
    elif scenario.name == "round_robin":
        base_port += 40

    runner_wait = 30000
    if scenario.num_nodes == 5:
        runner_wait = 50000

    adapter = RicartAgrawalaAdapter(base_port=base_port)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=runner_wait)
    return runner.run(scenario)


def to_row(algorithm: str, scenario: ScenarioDefinition, result):
    summary = summarize_result(result)
    return {
        "algorithm": algorithm,
        "scenario": scenario.name,
        "num_nodes": scenario.num_nodes,
        "total_events": len(result.events),
        "total_messages": summary["total_messages"],
        "cs_entries": summary["cs_entries"],
        "avg_wait_time_ms": round(summary["avg_wait_time_ms"], 2),
        "max_wait_time_ms": round(summary["max_wait_time_ms"], 2),
        "mutual_exclusion_violations": summary["mutual_exclusion_violations"],
        "fairness_violations": summary["fairness_violations"],
    }


def print_row(row: dict):
    print(
        f"[{row['algorithm']}] "
        f"scenario={row['scenario']}, "
        f"nodes={row['num_nodes']}, "
        f"messages={row['total_messages']}, "
        f"cs_entries={row['cs_entries']}, "
        f"avg_wait={row['avg_wait_time_ms']} ms, "
        f"max_wait={row['max_wait_time_ms']} ms, "
        f"ME={row['mutual_exclusion_violations']}, "
        f"fair={row['fairness_violations']}"
    )


def save_csv(rows, path: str):
    fieldnames = [
        "algorithm",
        "scenario",
        "num_nodes",
        "total_events",
        "total_messages",
        "cs_entries",
        "avg_wait_time_ms",
        "max_wait_time_ms",
        "mutual_exclusion_violations",
        "fairness_violations",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = []
    scenarios = get_scenarios()

    for scenario in scenarios:
        print(f"\n=== RUN CENTRALIZED | {scenario.name} | {scenario.num_nodes} nodes ===")
        c_result = run_centralized(scenario)
        c_row = to_row("Centralized", scenario, c_result)
        rows.append(c_row)
        print_row(c_row)

        print(f"\n=== RUN RICART-AGRAWALA | {scenario.name} | {scenario.num_nodes} nodes ===")
        r_result = run_ricart(scenario)
        r_row = to_row("Ricart-Agrawala", scenario, r_result)
        rows.append(r_row)
        print_row(r_row)

    save_csv(rows, OUTPUT_CSV)
    print(f"\nSaved benchmark results to: {Path(OUTPUT_CSV).resolve()}")


if __name__ == "__main__":
    main()