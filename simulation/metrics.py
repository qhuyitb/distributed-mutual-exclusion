from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict, List, Set

from simulation.contracts import EventRecord, EventType, MessageType, SimulationMetrics


class MetricsAnalyzer:
    """
    Phân tích event log để tạo SimulationMetrics chuẩn cho báo cáo.

    Quy ước:
    - total_messages: chỉ tính message phục vụ request
    - background_messages: message nền không trực tiếp phục vụ request
    - với Token Ring:
        * TOKEN + traffic_scope=request_related  -> tính vào total_messages
        * TOKEN + traffic_scope=idle             -> tính vào background_messages
    - waiting time: tính từ REQUEST_CS -> ENTER_CS theo từng node
    """

    def analyze(self, events: List[EventRecord]) -> SimulationMetrics:
        metrics = SimulationMetrics()

        request_times_by_node: Dict[int, Deque[float]] = defaultdict(deque)
        inside_cs_nodes: Set[int] = set()

        for event in sorted(events, key=lambda e: e.timestamp):
            if event.event_type == EventType.REQUEST_CS:
                metrics.request_count += 1
                if event.node_id is not None:
                    request_times_by_node[event.node_id].append(event.timestamp)

            elif event.event_type == EventType.ENTER_CS:
                metrics.cs_entries += 1

                if event.node_id is not None:
                    metrics.entries_by_node[event.node_id] = (
                        metrics.entries_by_node.get(event.node_id, 0) + 1
                    )

                    if request_times_by_node[event.node_id]:
                        request_ts = request_times_by_node[event.node_id].popleft()
                        waiting_time = max(0.0, event.timestamp - request_ts)

                        if event.node_id not in metrics.waiting_time_by_node:
                            metrics.waiting_time_by_node[event.node_id] = []
                        metrics.waiting_time_by_node[event.node_id].append(waiting_time)

                    if inside_cs_nodes:
                        if event.node_id not in inside_cs_nodes or len(inside_cs_nodes) > 1:
                            metrics.mutual_exclusion_violations += 1

                    inside_cs_nodes.add(event.node_id)

            elif event.event_type == EventType.EXIT_CS:
                if event.node_id is not None:
                    inside_cs_nodes.discard(event.node_id)

            elif event.event_type == EventType.MESSAGE_SENT:
                msg_type = event.message_type
                traffic_scope = event.details.get("traffic_scope", "request_related")

                # Token Ring: tách message phục vụ request và message nền
                if msg_type == MessageType.TOKEN and traffic_scope == "idle":
                    metrics.background_messages += 1
                    metrics.idle_token_messages += 1
                else:
                    metrics.total_messages += 1

                    if msg_type == MessageType.TOKEN:
                        metrics.request_related_token_messages += 1

                    if msg_type is not None:
                        msg_key = msg_type.value
                        metrics.messages_by_type[msg_key] = (
                            metrics.messages_by_type.get(msg_key, 0) + 1
                        )

        all_waiting_times: List[float] = []
        for node_waits in metrics.waiting_time_by_node.values():
            all_waiting_times.extend(node_waits)

        if all_waiting_times:
            metrics.avg_waiting_time = sum(all_waiting_times) / len(all_waiting_times)
            metrics.max_waiting_time = max(all_waiting_times)

        if metrics.entries_by_node:
            counts = list(metrics.entries_by_node.values())
            if max(counts) - min(counts) >= 2:
                metrics.fairness_violations = 1

        return metrics


def analyze_events(events: List[EventRecord]) -> SimulationMetrics:
    analyzer = MetricsAnalyzer()
    return analyzer.analyze(events)