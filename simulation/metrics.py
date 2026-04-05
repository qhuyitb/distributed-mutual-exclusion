"""
Bộ phân tích metrics cho Simulation + Testing Engine.

Module này chịu trách nhiệm:
- Đếm số lượng message đã gửi
- Đếm số lần vào critical section
- Tính thời gian chờ để vào critical section
- Kiểm tra vi phạm mutual exclusion
- Hỗ trợ đánh giá fairness cơ bản

Mọi phép đo đều dựa trên event log chuẩn trong simulation.contracts.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from simulation.contracts import Event, EventType


class MetricsAnalyzer:
    """
    Bộ phân tích metrics từ event log.

    Class này nhận danh sách Event và trả ra các chỉ số
    phục vụ so sánh hiệu năng giữa các thuật toán.
    """

    def __init__(self, events: List[Event]) -> None:
        """
        Khởi tạo bộ phân tích.

        Args:
            events: Danh sách event log thu được sau một lần mô phỏng
        """
        self.events = sorted(events, key=lambda event: event.timestamp)

    def analyze(self) -> Dict[str, Any]:
        """
        Phân tích toàn bộ event log và trả ra metrics tổng hợp.

        Returns:
            Dict[str, Any]: Các chỉ số đã phân tích
        """
        total_messages = self._count_total_messages()
        cs_entries = self._count_cs_entries()
        avg_wait_time_ms, max_wait_time_ms, wait_times_by_node = self._calculate_wait_times()
        mutual_exclusion_violations = self._detect_mutual_exclusion_violations()
        fairness_violations = self._detect_fairness_violations(wait_times_by_node)
        message_count_by_type = self._count_messages_by_type()
        cs_entries_by_node = self._count_cs_entries_by_node()

        return {
            "total_messages": total_messages,
            "message_count_by_type": message_count_by_type,
            "cs_entries": cs_entries,
            "cs_entries_by_node": cs_entries_by_node,
            "avg_wait_time_ms": avg_wait_time_ms,
            "max_wait_time_ms": max_wait_time_ms,
            "wait_times_by_node": wait_times_by_node,
            "mutual_exclusion_violations": mutual_exclusion_violations,
            "fairness_violations": fairness_violations,
            "total_events": len(self.events),
        }

    def _count_total_messages(self) -> int:
        """
        Đếm tổng số event gửi message.

        Returns:
            int: Tổng số message đã gửi
        """
        return sum(1 for event in self.events if event.event_type == EventType.MESSAGE_SENT)

    def _count_messages_by_type(self) -> Dict[str, int]:
        """
        Đếm số lượng message theo từng loại.

        Returns:
            Dict[str, int]: Số lượng message theo msg_type
        """
        counts: Dict[str, int] = defaultdict(int)

        for event in self.events:
            if event.event_type == EventType.MESSAGE_SENT and event.message is not None:
                counts[event.message.msg_type] += 1

        return dict(counts)

    def _count_cs_entries(self) -> int:
        """
        Đếm tổng số lần vào critical section.

        Returns:
            int: Số lần ENTER_CS
        """
        return sum(1 for event in self.events if event.event_type == EventType.ENTER_CS)

    def _count_cs_entries_by_node(self) -> Dict[int, int]:
        """
        Đếm số lần vào critical section theo từng node.

        Returns:
            Dict[int, int]: Số lần vào CS theo node_id
        """
        counts: Dict[int, int] = defaultdict(int)

        for event in self.events:
            if event.event_type == EventType.ENTER_CS:
                counts[event.node_id] += 1

        return dict(counts)

    def _calculate_wait_times(self) -> Tuple[float, float, Dict[int, List[float]]]:
        """
        Tính thời gian chờ từ lúc REQUEST_CS đến lúc ENTER_CS.

        Logic:
        - Khi gặp REQUEST_CS của một node, lưu thời điểm bắt đầu chờ
        - Khi gặp ENTER_CS của node đó, tính khoảng chênh lệch
        - Sau khi tính xong, xóa request pending tương ứng

        Returns:
            Tuple[float, float, Dict[int, List[float]]]:
                - average wait time (ms)
                - max wait time (ms)
                - wait times theo từng node
        """
        pending_requests: Dict[int, float] = {}
        wait_times: List[float] = []
        wait_times_by_node: Dict[int, List[float]] = defaultdict(list)

        for event in self.events:
            if event.event_type == EventType.REQUEST_CS:
                pending_requests[event.node_id] = event.timestamp

            elif event.event_type == EventType.ENTER_CS:
                request_time = pending_requests.get(event.node_id)

                if request_time is not None:
                    wait_time_ms = (event.timestamp - request_time) * 1000.0
                    wait_times.append(wait_time_ms)
                    wait_times_by_node[event.node_id].append(wait_time_ms)
                    del pending_requests[event.node_id]

        if not wait_times:
            return 0.0, 0.0, dict(wait_times_by_node)

        average_wait_time = sum(wait_times) / len(wait_times)
        max_wait_time = max(wait_times)

        return average_wait_time, max_wait_time, dict(wait_times_by_node)

    def _detect_mutual_exclusion_violations(self) -> int:
        """
        Phát hiện số lần vi phạm mutual exclusion.

        Logic:
        - Dùng một biến active_cs_node để theo dõi node đang ở critical section
        - Nếu gặp ENTER_CS khi đã có node khác đang ở critical section,
          thì đây là một violation
        - Khi gặp EXIT_CS của node hiện tại thì giải phóng trạng thái

        Returns:
            int: Số lần vi phạm mutual exclusion
        """
        violations = 0
        active_cs_node: Optional[int] = None

        for event in self.events:
            if event.event_type == EventType.ENTER_CS:
                if active_cs_node is not None and active_cs_node != event.node_id:
                    violations += 1
                else:
                    active_cs_node = event.node_id

            elif event.event_type == EventType.EXIT_CS:
                if active_cs_node == event.node_id:
                    active_cs_node = None

        return violations

    def _detect_fairness_violations(self, wait_times_by_node: Dict[int, List[float]]) -> int:
        """
        Kiểm tra fairness ở mức cơ bản.

        Logic đơn giản:
        - Nếu có node không bao giờ vào được CS trong khi node khác vào nhiều lần,
          xem như có dấu hiệu fairness issue
        - Đây không phải proof hình thức, chỉ là metric hỗ trợ phân tích

        Returns:
            int: Số lượng dấu hiệu fairness violation
        """
        cs_entries_by_node = self._count_cs_entries_by_node()

        if not cs_entries_by_node:
            return 0

        max_entries = max(cs_entries_by_node.values())
        min_entries = min(cs_entries_by_node.values())

        if max_entries - min_entries >= 2:
            return 1

        return 0


def analyze_events(events: List[Event]) -> Dict[str, Any]:
    """
    Hàm tiện ích để phân tích nhanh event log.

    Args:
        events: Danh sách event log

    Returns:
        Dict[str, Any]: Metrics tổng hợp
    """
    analyzer = MetricsAnalyzer(events)
    return analyzer.analyze()