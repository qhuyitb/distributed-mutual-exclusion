from simulation.contracts import ScenarioDefinition, NodeAction, ActionType
from simulation.runner import SimulationRunner, summarize_result
from simulation.token_ring_adapter import TokenRingAdapter


def main():
    adapter = TokenRingAdapter(base_port=8500)
    runner = SimulationRunner(adapter=adapter, post_run_wait_ms=8000)

    scenario = ScenarioDefinition(
        name="token_ring_low_contention",
        description="3 nodes request CS in Token Ring",
        num_nodes=3,
        network_delay_ms=0,
        actions=[
            NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=0),
            NodeAction(at_ms=500, action_type=ActionType.REQUEST_CS, node_id=1),
            NodeAction(at_ms=1000, action_type=ActionType.REQUEST_CS, node_id=2),
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