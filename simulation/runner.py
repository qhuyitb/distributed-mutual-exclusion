from __future__ import annotations

import time
from typing import List
from simulation.metrics import analyze_events

from simulation.contracts import (
    ActionType,
    AlgorithmAdapter,
    AlgorithmType,
    EventRecord,
    EventType,
    ScenarioDefinition,
    SimulationMetrics,
    SimulationResult,
)


class SimulationRunner:
    """
    Runner điều phối mô phỏng theo timeline.
    Ở bước này runner chỉ orchestration:
    - setup
    - start
    - phát action đúng thời điểm
    - chờ hậu xử lý
    - stop
    - thu event
    - trả SimulationResult với metrics tạm thời
    """

    def __init__(self, adapter: AlgorithmAdapter, post_run_wait_seconds: float = 1.0) -> None:
        self.adapter = adapter
        self.post_run_wait_seconds = post_run_wait_seconds

    def run(self, scenario: ScenarioDefinition) -> SimulationResult:
        started_at = time.time()
        errors: List[str] = []
        success = True

        bootstrap_events: List[EventRecord] = [
            EventRecord(
                timestamp=started_at,
                event_type=EventType.SIMULATION_START,
                details={
                    "scenario_name": scenario.name,
                    "algorithm": self.adapter.algorithm_type.value,
                    "num_nodes": scenario.num_nodes,
                    "network_delay_ms": scenario.network_delay_ms,
                },
            )
        ]

        try:
            self.adapter.setup(scenario)
            self.adapter.start()

            action_start_time = time.time()
            self._execute_actions(scenario, action_start_time)

            if self.post_run_wait_seconds > 0:
                time.sleep(self.post_run_wait_seconds)

        except Exception as exc:
            success = False
            errors.append(str(exc))
        finally:
            try:
                self.adapter.stop()
            except Exception as stop_exc:
                success = False
                errors.append(f"stop_failed: {stop_exc}")

        finished_at = time.time()

        adapter_events: List[EventRecord] = []
        try:
            adapter_events = self.adapter.collect_events()
        except Exception as collect_exc:
            success = False
            errors.append(f"collect_events_failed: {collect_exc}")

        closing_event = EventRecord(
            timestamp=finished_at,
            event_type=EventType.SIMULATION_END,
            details={
                "scenario_name": scenario.name,
                "algorithm": self.adapter.algorithm_type.value,
                "success": success,
            },
        )

        all_events = bootstrap_events + adapter_events + [closing_event]
        metrics = analyze_events(all_events)

        return SimulationResult(
            algorithm=self.adapter.algorithm_type,
            scenario_name=scenario.name,
            success=success,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=finished_at - started_at,
            metrics=metrics,
            events=all_events,
            errors=errors,
        )

    def run_many(self, scenarios: List[ScenarioDefinition]) -> List[SimulationResult]:
        return [self.run(scenario) for scenario in scenarios]

    def _execute_actions(self, scenario: ScenarioDefinition, start_time: float) -> None:
        actions = sorted(scenario.actions, key=lambda action: action.at_seconds)

        for action in actions:
            self._wait_until(start_time, action.at_seconds)
            self._execute_action(action)

    def _execute_action(self, action) -> None:
        if action.action_type == ActionType.REQUEST_CS:
            if action.node_id is None:
                raise ValueError("REQUEST_CS requires node_id")

            cs_duration = action.details.get("cs_duration_seconds")
            if cs_duration is not None and hasattr(self.adapter, "set_next_cs_duration"):
                self.adapter.set_next_cs_duration(action.node_id, float(cs_duration))

            self.adapter.request_cs(action.node_id)

        elif action.action_type == ActionType.CRASH_NODE:
            if action.node_id is None:
                raise ValueError("CRASH_NODE requires node_id")
            self.adapter.crash_node(action.node_id)

        elif action.action_type == ActionType.RECOVER_NODE:
            if action.node_id is None:
                raise ValueError("RECOVER_NODE requires node_id")
            self.adapter.recover_node(action.node_id)

        elif action.action_type == ActionType.SLEEP:
            duration = action.duration_seconds or action.details.get("duration_seconds", 0.0)
            if duration > 0:
                time.sleep(duration)

        else:
            raise ValueError(f"Unsupported action type: {action.action_type}")

    @staticmethod
    def _wait_until(start_time: float, offset_seconds: float) -> None:
        target_time = start_time + offset_seconds
        now = time.time()
        if target_time > now:
            time.sleep(target_time - now)


def summarize_result(result: SimulationResult) -> dict:
    return {
        "algorithm": result.algorithm.value,
        "scenario_name": result.scenario_name,
        "success": result.success,
        "duration_seconds": round(result.duration_seconds, 3),
        "total_events": len(result.events),
        "total_messages": result.metrics.total_messages,
        "messages_by_type": result.metrics.messages_by_type,
        "request_count": result.metrics.request_count,
        "cs_entries": result.metrics.cs_entries,
        "avg_waiting_time": round(result.metrics.avg_waiting_time, 4),
        "max_waiting_time": round(result.metrics.max_waiting_time, 4),
        "entries_by_node": result.metrics.entries_by_node,
        "mutual_exclusion_violations": result.metrics.mutual_exclusion_violations,
        "fairness_violations": result.metrics.fairness_violations,
        "errors": result.errors,
    }