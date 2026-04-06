from __future__ import annotations

from typing import Dict, List

from simulation.contracts import ActionType, NodeAction, ScenarioDefinition


def build_low_contention_scenario() -> ScenarioDefinition:
    actions: List[NodeAction] = [
        NodeAction(
            at_seconds=0.0,
            action_type=ActionType.REQUEST_CS,
            node_id=1,
            details={"cs_duration_seconds": 0.8},
        ),
        NodeAction(
            at_seconds=1.5,
            action_type=ActionType.REQUEST_CS,
            node_id=2,
            details={"cs_duration_seconds": 0.8},
        ),
        NodeAction(
            at_seconds=3.0,
            action_type=ActionType.REQUEST_CS,
            node_id=3,
            details={"cs_duration_seconds": 0.8},
        ),
    ]

    return ScenarioDefinition(
        name="low_contention",
        description="Các node xin vào critical section cách nhau, gần như không tranh chấp.",
        num_nodes=3,
        actions=actions,
        network_delay_ms=20,
        timeout_seconds=10.0,
        metadata={"contention_level": "low"},
    )


def build_high_contention_scenario() -> ScenarioDefinition:
    actions: List[NodeAction] = [
        NodeAction(
            at_seconds=0.0,
            action_type=ActionType.REQUEST_CS,
            node_id=1,
            details={"cs_duration_seconds": 1.0},
        ),
        NodeAction(
            at_seconds=0.05,
            action_type=ActionType.REQUEST_CS,
            node_id=2,
            details={"cs_duration_seconds": 1.0},
        ),
        NodeAction(
            at_seconds=0.10,
            action_type=ActionType.REQUEST_CS,
            node_id=3,
            details={"cs_duration_seconds": 1.0},
        ),
        NodeAction(
            at_seconds=0.15,
            action_type=ActionType.REQUEST_CS,
            node_id=4,
            details={"cs_duration_seconds": 1.0},
        ),
    ]

    return ScenarioDefinition(
        name="high_contention",
        description="Nhiều node cùng xin vào critical section gần như đồng thời.",
        num_nodes=4,
        actions=actions,
        network_delay_ms=50,
        timeout_seconds=15.0,
        metadata={"contention_level": "high"},
    )


def build_round_robin_scenario() -> ScenarioDefinition:
    actions: List[NodeAction] = [
        NodeAction(
            at_seconds=0.0,
            action_type=ActionType.REQUEST_CS,
            node_id=1,
            details={"cs_duration_seconds": 0.4},
        ),
        NodeAction(
            at_seconds=0.6,
            action_type=ActionType.REQUEST_CS,
            node_id=2,
            details={"cs_duration_seconds": 0.4},
        ),
        NodeAction(
            at_seconds=1.2,
            action_type=ActionType.REQUEST_CS,
            node_id=3,
            details={"cs_duration_seconds": 0.4},
        ),
        NodeAction(
            at_seconds=1.8,
            action_type=ActionType.REQUEST_CS,
            node_id=1,
            details={"cs_duration_seconds": 0.4},
        ),
        NodeAction(
            at_seconds=2.4,
            action_type=ActionType.REQUEST_CS,
            node_id=2,
            details={"cs_duration_seconds": 0.4},
        ),
        NodeAction(
            at_seconds=3.0,
            action_type=ActionType.REQUEST_CS,
            node_id=3,
            details={"cs_duration_seconds": 0.4},
        ),
    ]

    return ScenarioDefinition(
        name="round_robin",
        description="Các node thay phiên xin vào CS nhiều vòng để kiểm tra fairness.",
        num_nodes=3,
        actions=actions,
        network_delay_ms=20,
        timeout_seconds=12.0,
        metadata={"focus": "fairness"},
    )


def build_node_crash_recover_scenario() -> ScenarioDefinition:
    actions: List[NodeAction] = [
        NodeAction(
            at_seconds=0.0,
            action_type=ActionType.REQUEST_CS,
            node_id=1,
            details={"cs_duration_seconds": 1.0},
        ),
        NodeAction(
            at_seconds=0.1,
            action_type=ActionType.REQUEST_CS,
            node_id=2,
            details={"cs_duration_seconds": 1.0},
        ),
        NodeAction(
            at_seconds=0.8,
            action_type=ActionType.CRASH_NODE,
            node_id=2,
        ),
        NodeAction(
            at_seconds=2.5,
            action_type=ActionType.RECOVER_NODE,
            node_id=2,
        ),
        NodeAction(
            at_seconds=3.0,
            action_type=ActionType.REQUEST_CS,
            node_id=3,
            details={"cs_duration_seconds": 0.8},
        ),
    ]

    return ScenarioDefinition(
        name="node_crash_recover",
        description="Một node bị crash rồi recover trong khi hệ thống đang xử lý request.",
        num_nodes=3,
        actions=actions,
        network_delay_ms=30,
        timeout_seconds=15.0,
        metadata={"focus": "fault_tolerance"},
    )


def get_default_scenarios() -> Dict[str, ScenarioDefinition]:
    scenarios = {
        "low_contention": build_low_contention_scenario(),
        "high_contention": build_high_contention_scenario(),
        "round_robin": build_round_robin_scenario(),
        "node_crash_recover": build_node_crash_recover_scenario(),
    }
    return scenarios


def get_scenario_by_name(name: str) -> ScenarioDefinition:
    scenarios = get_default_scenarios()
    if name not in scenarios:
        available = ", ".join(scenarios.keys())
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")
    return scenarios[name]