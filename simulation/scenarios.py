"""
Các kịch bản mô phỏng chuẩn cho Simulation + Testing Engine.

Module này định nghĩa các scenario dùng chung để:
- Kiểm thử trường hợp ít tranh chấp
- Kiểm thử trường hợp tranh chấp cao
- Kiểm thử tình huống node bị lỗi và phục hồi

Tất cả scenario đều bám theo contract trong simulation.contracts.
"""

from __future__ import annotations

from typing import Dict, List

from simulation.contracts import ActionType, NodeAction, ScenarioDefinition


def build_low_contention_scenario() -> ScenarioDefinition:
    """
    Tạo scenario ít tranh chấp tài nguyên.

    Ý tưởng:
    - Các node xin vào critical section cách nhau theo thời gian
    - Giúp kiểm tra luồng chạy cơ bản
    - Giúp kiểm tra tính đúng đắn của ENTER_CS và EXIT_CS

    Returns:
        ScenarioDefinition: Kịch bản low contention
    """
    actions: List[NodeAction] = [
        NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
        NodeAction(at_ms=800, action_type=ActionType.RELEASE_CS, node_id=1),
        NodeAction(at_ms=1200, action_type=ActionType.REQUEST_CS, node_id=2),
        NodeAction(at_ms=2000, action_type=ActionType.RELEASE_CS, node_id=2),
        NodeAction(at_ms=2400, action_type=ActionType.REQUEST_CS, node_id=3),
        NodeAction(at_ms=3200, action_type=ActionType.RELEASE_CS, node_id=3),
    ]

    return ScenarioDefinition(
        name="low_contention",
        description="Các node xin critical section cách nhau, gần như không tranh chấp.",
        num_nodes=3,
        network_delay_ms=50,
        actions=actions,
    )


def build_high_contention_scenario() -> ScenarioDefinition:
    """
    Tạo scenario tranh chấp cao.

    Ý tưởng:
    - Nhiều node xin vào critical section gần như cùng lúc
    - Dùng để đo thời gian chờ, số lượng message và fairness

    Returns:
        ScenarioDefinition: Kịch bản high contention
    """
    actions: List[NodeAction] = [
        NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
        NodeAction(at_ms=50, action_type=ActionType.REQUEST_CS, node_id=2),
        NodeAction(at_ms=100, action_type=ActionType.REQUEST_CS, node_id=3),
        NodeAction(at_ms=150, action_type=ActionType.REQUEST_CS, node_id=4),
        NodeAction(at_ms=1200, action_type=ActionType.RELEASE_CS, node_id=1),
        NodeAction(at_ms=1500, action_type=ActionType.RELEASE_CS, node_id=2),
        NodeAction(at_ms=1800, action_type=ActionType.RELEASE_CS, node_id=3),
        NodeAction(at_ms=2100, action_type=ActionType.RELEASE_CS, node_id=4),
    ]

    return ScenarioDefinition(
        name="high_contention",
        description="Nhiều node cùng xin critical section trong thời gian rất gần nhau.",
        num_nodes=4,
        network_delay_ms=80,
        actions=actions,
    )


def build_node_crash_scenario() -> ScenarioDefinition:
    """
    Tạo scenario có node bị lỗi và phục hồi.

    Ý tưởng:
    - Một node đang hoạt động thì bị crash
    - Sau đó node được recover
    - Dùng để quan sát độ ổn định của thuật toán khi có lỗi

    Returns:
        ScenarioDefinition: Kịch bản node crash và recover
    """
    actions: List[NodeAction] = [
        NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
        NodeAction(at_ms=100, action_type=ActionType.REQUEST_CS, node_id=2),
        NodeAction(at_ms=600, action_type=ActionType.CRASH_NODE, node_id=2),
        NodeAction(at_ms=1200, action_type=ActionType.RELEASE_CS, node_id=1),
        NodeAction(at_ms=1800, action_type=ActionType.RECOVER_NODE, node_id=2),
        NodeAction(at_ms=2200, action_type=ActionType.REQUEST_CS, node_id=3),
        NodeAction(at_ms=3000, action_type=ActionType.RELEASE_CS, node_id=3),
    ]

    return ScenarioDefinition(
        name="node_crash",
        description="Một node bị crash giữa lúc hệ thống đang hoạt động rồi được recover.",
        num_nodes=3,
        network_delay_ms=60,
        actions=actions,
    )


def build_round_robin_requests_scenario() -> ScenarioDefinition:
    """
    Tạo scenario các node lần lượt xin critical section nhiều vòng.

    Ý tưởng:
    - Mỗi node xin critical section nhiều lần
    - Dùng để kiểm tra fairness và starvation

    Returns:
        ScenarioDefinition: Kịch bản round robin requests
    """
    actions: List[NodeAction] = [
        NodeAction(at_ms=0, action_type=ActionType.REQUEST_CS, node_id=1),
        NodeAction(at_ms=500, action_type=ActionType.RELEASE_CS, node_id=1),
        NodeAction(at_ms=600, action_type=ActionType.REQUEST_CS, node_id=2),
        NodeAction(at_ms=1100, action_type=ActionType.RELEASE_CS, node_id=2),
        NodeAction(at_ms=1200, action_type=ActionType.REQUEST_CS, node_id=3),
        NodeAction(at_ms=1700, action_type=ActionType.RELEASE_CS, node_id=3),
        NodeAction(at_ms=1800, action_type=ActionType.REQUEST_CS, node_id=1),
        NodeAction(at_ms=2300, action_type=ActionType.RELEASE_CS, node_id=1),
        NodeAction(at_ms=2400, action_type=ActionType.REQUEST_CS, node_id=2),
        NodeAction(at_ms=2900, action_type=ActionType.RELEASE_CS, node_id=2),
        NodeAction(at_ms=3000, action_type=ActionType.REQUEST_CS, node_id=3),
        NodeAction(at_ms=3500, action_type=ActionType.RELEASE_CS, node_id=3),
    ]

    return ScenarioDefinition(
        name="round_robin_requests",
        description="Các node lần lượt xin critical section qua nhiều vòng để kiểm tra fairness.",
        num_nodes=3,
        network_delay_ms=40,
        actions=actions,
    )


def get_default_scenarios() -> Dict[str, ScenarioDefinition]:
    """
    Lấy danh sách scenario mặc định của hệ thống.

    Returns:
        Dict[str, ScenarioDefinition]: Từ điển các scenario theo tên
    """
    scenarios = {
        "low_contention": build_low_contention_scenario(),
        "high_contention": build_high_contention_scenario(),
        "node_crash": build_node_crash_scenario(),
        "round_robin_requests": build_round_robin_requests_scenario(),
    }
    return scenarios


def get_scenario_by_name(name: str) -> ScenarioDefinition:
    """
    Lấy một scenario theo tên.

    Args:
        name: Tên scenario cần lấy

    Returns:
        ScenarioDefinition: Scenario tương ứng

    Raises:
        ValueError: Nếu tên scenario không tồn tại
    """
    scenarios = get_default_scenarios()

    if name not in scenarios:
        available = ", ".join(scenarios.keys())
        raise ValueError(f"Scenario '{name}' không tồn tại. Các scenario hợp lệ: {available}")

    return scenarios[name]