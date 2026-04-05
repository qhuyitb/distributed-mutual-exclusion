"""
Fake adapter dùng để kiểm thử Simulation + Testing Engine.

Module này không triển khai thuật toán mutual exclusion thật.
Nó chỉ mô phỏng hành vi cơ bản để:
- Tạo event log chuẩn
- Tạo message log chuẩn
- Cho phép test runner, scenarios và metrics độc lập

Mục tiêu là giúp TV4 kiểm tra engine trước khi ghép adapter thật.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set

from simulation.contracts import (
    AlgorithmAdapter,
    Event,
    EventType,
    Message,
    MessageType,
)


class FakeAdapter(AlgorithmAdapter):
    """
    Adapter giả dùng để test Simulation Engine.

    FakeAdapter mô phỏng một hệ thống đơn giản:
    - Node có thể request critical section
    - Nếu không có node nào đang ở critical section thì được vào ngay
    - Nếu đang bận thì request sẽ được giữ trong hàng đợi
    - Khi node hiện tại release, node tiếp theo trong queue sẽ được vào
    - Có hỗ trợ crash và recover ở mức đơn giản
    """

    def __init__(self) -> None:
        """
        Khởi tạo FakeAdapter.
        """
        self.num_nodes: int = 0
        self.network_delay_ms: int = 0
        self.running: bool = False

        self.sequence_num: int = 0
        self.event_log: List[Event] = []

        self.active_cs_node: Optional[int] = None
        self.waiting_queue: List[int] = []
        self.crashed_nodes: Set[int] = set()

        self.message_count: int = 0

    def setup(self, num_nodes: int, network_delay_ms: int = 0) -> None:
        """
        Khởi tạo trạng thái hệ thống.

        Args:
            num_nodes: Số node trong mô phỏng
            network_delay_ms: Độ trễ mạng giả lập
        """
        self.num_nodes = num_nodes
        self.network_delay_ms = network_delay_ms
        self.running = False

        self.sequence_num = 0
        self.event_log = []

        self.active_cs_node = None
        self.waiting_queue = []
        self.crashed_nodes = set()

        self.message_count = 0

    def start(self) -> None:
        """
        Khởi động adapter.
        """
        self.running = True

    def stop(self) -> None:
        """
        Dừng adapter.
        """
        self.running = False

    def request_critical_section(self, node_id: int) -> None:
        """
        Yêu cầu node xin vào critical section.

        Args:
            node_id: ID node xin critical section
        """
        if not self.running or node_id in self.crashed_nodes:
            return

        now = time.time()

        self.event_log.append(
            Event(
                event_type=EventType.REQUEST_CS,
                node_id=node_id,
                timestamp=now,
            )
        )

        for receiver_id in range(1, self.num_nodes + 1):
            if receiver_id == node_id:
                continue

            message = self._build_message(
                msg_type=MessageType.REQUEST,
                sender_id=node_id,
                receiver_id=receiver_id,
                data={"resource": "critical_section"},
            )
            self.send_message(message)

        if self.active_cs_node is None:
            self._grant_critical_section(node_id)
        else:
            if node_id not in self.waiting_queue:
                self.waiting_queue.append(node_id)

    def release_critical_section(self, node_id: int) -> None:
        """
        Yêu cầu node rời khỏi critical section.

        Args:
            node_id: ID node rời critical section
        """
        if not self.running or node_id in self.crashed_nodes:
            return

        if self.active_cs_node != node_id:
            return

        now = time.time()

        self.event_log.append(
            Event(
                event_type=EventType.EXIT_CS,
                node_id=node_id,
                timestamp=now,
            )
        )

        for receiver_id in range(1, self.num_nodes + 1):
            if receiver_id == node_id:
                continue

            message = self._build_message(
                msg_type=MessageType.RELEASE,
                sender_id=node_id,
                receiver_id=receiver_id,
                data={"resource": "critical_section"},
            )
            self.send_message(message)

        self.active_cs_node = None
        self._grant_next_waiting_node()

    def crash_node(self, node_id: int) -> None:
        """
        Giả lập node bị crash.

        Args:
            node_id: ID node bị crash
        """
        if node_id in self.crashed_nodes:
            return

        self.crashed_nodes.add(node_id)

        self.event_log.append(
            Event(
                event_type=EventType.NODE_CRASH,
                node_id=node_id,
                timestamp=time.time(),
            )
        )

        if self.active_cs_node == node_id:
            self.active_cs_node = None
            self._grant_next_waiting_node()

        self.waiting_queue = [waiting_node for waiting_node in self.waiting_queue if waiting_node != node_id]

    def recover_node(self, node_id: int) -> None:
        """
        Giả lập node phục hồi sau crash.

        Args:
            node_id: ID node được recover
        """
        if node_id not in self.crashed_nodes:
            return

        self.crashed_nodes.remove(node_id)

        self.event_log.append(
            Event(
                event_type=EventType.NODE_RECOVER,
                node_id=node_id,
                timestamp=time.time(),
            )
        )

    def send_message(self, message: Message) -> None:
        """
        Gửi message theo chuẩn chung.

        Args:
            message: Message cần gửi
        """
        if not self.running:
            return

        self.message_count += 1

        self.event_log.append(
            Event(
                event_type=EventType.MESSAGE_SENT,
                node_id=message.sender_id,
                timestamp=time.time(),
                message=message,
            )
        )

    def get_event_log(self) -> List[Event]:
        """
        Lấy event log hiện tại.

        Returns:
            List[Event]: Danh sách event đã ghi nhận
        """
        return list(self.event_log)

    def collect_stats(self) -> Dict[str, Any]:
        """
        Thu thống kê thô từ adapter.

        Returns:
            Dict[str, Any]: Thống kê cơ bản của fake adapter
        """
        return {
            "num_nodes": self.num_nodes,
            "network_delay_ms": self.network_delay_ms,
            "message_count": self.message_count,
            "waiting_queue_length": len(self.waiting_queue),
            "crashed_nodes": sorted(self.crashed_nodes),
            "active_cs_node": self.active_cs_node,
        }

    def _build_message(
        self,
        msg_type: str,
        sender_id: int,
        receiver_id: Optional[int],
        data: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Tạo một Message theo chuẩn chung.

        Args:
            msg_type: Loại message
            sender_id: ID node gửi
            receiver_id: ID node nhận
            data: Payload mở rộng

        Returns:
            Message: Đối tượng message đã tạo
        """
        self.sequence_num += 1

        return Message(
            msg_type=msg_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sequence_num=self.sequence_num,
            timestamp=time.time(),
            data=data or {},
        )

    def _grant_critical_section(self, node_id: int) -> None:
        """
        Cho một node vào critical section.

        Args:
            node_id: ID node được cấp quyền
        """
        if node_id in self.crashed_nodes:
            return

        self.active_cs_node = node_id

        for receiver_id in range(1, self.num_nodes + 1):
            if receiver_id == node_id:
                continue

            reply_message = self._build_message(
                msg_type=MessageType.REPLY,
                sender_id=receiver_id,
                receiver_id=node_id,
                data={"grant": True},
            )
            self.send_message(reply_message)

        self.event_log.append(
            Event(
                event_type=EventType.ENTER_CS,
                node_id=node_id,
                timestamp=time.time(),
            )
        )

    def _grant_next_waiting_node(self) -> None:
        """
        Cấp quyền critical section cho node tiếp theo trong queue.
        """
        while self.waiting_queue:
            next_node = self.waiting_queue.pop(0)

            if next_node not in self.crashed_nodes:
                self._grant_critical_section(next_node)
                return