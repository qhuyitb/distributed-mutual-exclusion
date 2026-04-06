from simulation.contracts import ScenarioDefinition, NodeAction, ActionType
from simulation.runner import SimulationRunner, summarize_result
from simulation.centralized_adapter import CentralizedAdapter
from centralized.coordinator import Coordinator
from centralized.node import Node


def main():
    adapter = CentralizedAdapter(Coordinator, Node)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=8000)

    scenario = ScenarioDefinition(
        name="centralized_low_contention",
        description="3 nodes request CS at different times",
        num_nodes=3,
        network_delay_ms=0,
        actions=[
            NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
            NodeAction(at_ms=500, action_type=ActionType.REQUEST_CS, node_id=2),
            NodeAction(at_ms=1000, action_type=ActionType.REQUEST_CS, node_id=3),
        ],
    )

    result = runner.run(scenario)

    print("\n=== SUMMARY ===")
    print(summarize_result(result))

    print("\n=== RAW STATS ===")
    print(result.raw_stats)

    print("\n=== TOTAL EVENTS ===")
    print(len(result.events))


if __name__ == "__main__":
    main()