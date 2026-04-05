"""
Runner điều phối toàn bộ quá trình mô phỏng.

Module này chịu trách nhiệm:
- Khởi tạo adapter của thuật toán
- Chạy scenario theo timeline
- Phát các action đến từng node
- Thu event log
- Phân tích metrics
- Trả về kết quả mô phỏng chuẩn

Runner là lõi trung tâm của phần TV4.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from simulation.contracts import (
    ActionType,
    AlgorithmAdapter,
    ScenarioDefinition,
    SimulationResult,
)
from simulation.metrics import MetricsAnalyzer


class SimulationRunner:
    """
    Bộ điều phối mô phỏng chung cho các thuật toán.

    Class này không phụ thuộc trực tiếp vào Centralized,
    Ricart-Agrawala hay Token Ring. Nó chỉ làm việc thông qua
    interface AlgorithmAdapter.
    """

    def __init__(self, adapter: AlgorithmAdapter, post_run_wait_ms: int = 500) -> None:
        """
        Khởi tạo runner.

        Args:
            adapter: Adapter của thuật toán cần mô phỏng
            post_run_wait_ms: Thời gian chờ thêm sau action cuối cùng
                để hệ thống xử lý nốt message và log event
        """
        self.adapter = adapter
        self.post_run_wait_ms = post_run_wait_ms

    def run(self, scenario: ScenarioDefinition) -> SimulationResult:
        """
        Chạy một scenario mô phỏng hoàn chỉnh.

        Quy trình:
        1. Setup adapter
        2. Start adapter
        3. Thực thi từng action theo timeline
        4. Chờ xử lý nốt các event còn lại
        5. Stop adapter
        6. Thu event log + raw stats
        7. Phân tích metrics
        8. Trả về SimulationResult

        Args:
            scenario: Scenario cần chạy

        Returns:
            SimulationResult: Kết quả mô phỏng hoàn chỉnh
        """
        self.adapter.setup(
            num_nodes=scenario.num_nodes,
            network_delay_ms=scenario.network_delay_ms,
        )

        self.adapter.start()
        start_time = time.time()

        try:
            self._execute_actions(scenario.actions, start_time)
            self._wait_ms(self.post_run_wait_ms)
        finally:
            self.adapter.stop()

        events = self.adapter.get_event_log()
        raw_stats = self.adapter.collect_stats()
        metrics = MetricsAnalyzer(events).analyze()

        return SimulationResult(
            scenario_name=scenario.name,
            events=events,
            raw_stats=raw_stats,
            metrics=metrics,
        )

    def run_many(self, scenarios: List[ScenarioDefinition]) -> List[SimulationResult]:
        """
        Chạy nhiều scenario liên tiếp.

        Args:
            scenarios: Danh sách scenario cần chạy

        Returns:
            List[SimulationResult]: Danh sách kết quả tương ứng
        """
        results: List[SimulationResult] = []

        for scenario in scenarios:
            result = self.run(scenario)
            results.append(result)

        return results

    def _execute_actions(self, actions: List[Any], start_time: float) -> None:
        """
        Thực thi danh sách action theo timeline.

        Args:
            actions: Danh sách NodeAction
            start_time: Mốc thời gian bắt đầu chạy scenario
        """
        sorted_actions = sorted(actions, key=lambda action: action.at_ms)

        for action in sorted_actions:
            self._wait_until(start_time, action.at_ms)
            self._execute_action(action)

    def _execute_action(self, action: Any) -> None:
        """
        Thực thi một action cụ thể.

        Args:
            action: NodeAction cần thực thi

        Raises:
            ValueError: Nếu action_type không hợp lệ
        """
        if action.action_type == ActionType.REQUEST_CS:
            self.adapter.request_critical_section(action.node_id)

        elif action.action_type == ActionType.RELEASE_CS:
            self.adapter.release_critical_section(action.node_id)

        elif action.action_type == ActionType.CRASH_NODE:
            self.adapter.crash_node(action.node_id)

        elif action.action_type == ActionType.RECOVER_NODE:
            self.adapter.recover_node(action.node_id)

        else:
            raise ValueError(f"Unsupported action_type: {action.action_type}")

    def _wait_until(self, start_time: float, target_offset_ms: int) -> None:
        """
        Chờ đến đúng thời điểm cần thực thi action.

        Args:
            start_time: Mốc bắt đầu mô phỏng
            target_offset_ms: Offset mục tiêu tính theo millisecond
        """
        target_time = start_time + (target_offset_ms / 1000.0)
        now = time.time()

        if target_time > now:
            time.sleep(target_time - now)

    @staticmethod
    def _wait_ms(duration_ms: int) -> None:
        """
        Chờ trong một khoảng thời gian tính theo millisecond.

        Args:
            duration_ms: Thời gian chờ
        """
        if duration_ms > 0:
            time.sleep(duration_ms / 1000.0)


def summarize_result(result: SimulationResult) -> Dict[str, Any]:
    """
    Tạo bản tóm tắt ngắn gọn từ SimulationResult.

    Args:
        result: Kết quả mô phỏng

    Returns:
        Dict[str, Any]: Thông tin tóm tắt phục vụ in ra màn hình
    """
    return {
        "scenario_name": result.scenario_name,
        "total_events": len(result.events),
        "total_messages": result.metrics.get("total_messages", 0),
        "cs_entries": result.metrics.get("cs_entries", 0),
        "avg_wait_time_ms": result.metrics.get("avg_wait_time_ms", 0.0),
        "max_wait_time_ms": result.metrics.get("max_wait_time_ms", 0.0),
        "mutual_exclusion_violations": result.metrics.get("mutual_exclusion_violations", 0),
        "fairness_violations": result.metrics.get("fairness_violations", 0),
    }