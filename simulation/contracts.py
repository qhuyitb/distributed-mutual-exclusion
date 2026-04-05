"""
Contracts chung cho Simulation + Testing Engine.

Module này định nghĩa các kiểu dữ liệu và interface chung để:
- Chuẩn hóa message giữa các thuật toán
- Chuẩn hóa event log cho việc mô phỏng và đo đạc
- Tạo adapter chung để ghép Centralized, Ricart-Agrawala, Token Ring

Toàn bộ phần Simulation của TV4 phải bám theo chuẩn Message:
    Message(
        msg_type,
        sender_id,
        receiver_id,
        sequence_num,
        timestamp,
        data,
    )
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """
    Cấu trúc gói tin chung cho toàn bộ hệ thống.

    Attributes:
        msg_type: Loại gói tin (REQUEST, REPLY, TOKEN, RELEASE, ...)
        sender_id: ID của node gửi
        receiver_id: ID của node nhận, có thể là None nếu broadcast hoặc token
        sequence_num: Số thứ tự gói tin
        timestamp: Mốc thời gian gắn với gói tin
        data: Dữ liệu payload mở rộng
    """
    msg_type: str
    sender_id: int
    receiver_id: Optional[int]
    sequence_num: int
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển Message thành dictionary.

        Returns:
            Dict[str, Any]: Dữ liệu dạng dict để log hoặc serialize
        """
        return {
            "msg_type": self.msg_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Message":
        """
        Tạo Message từ dictionary.

        Args:
            data: Dictionary chứa dữ liệu message

        Returns:
            Message: Đối tượng Message được khởi tạo từ dict
        """
        return Message(
            msg_type=data.get("msg_type", ""),
            sender_id=data.get("sender_id", -1),
            receiver_id=data.get("receiver_id"),
            sequence_num=data.get("sequence_num", 0),
            timestamp=data.get("timestamp", 0.0),
            data=data.get("data", {}),
        )


@dataclass
class Event:
    """
    Event mô phỏng dùng để ghi nhận hành vi của node và hệ thống.

    Attributes:
        event_type: Loại sự kiện (REQUEST_CS, ENTER_CS, EXIT_CS, MESSAGE_SENT, ...)
        node_id: ID node liên quan đến sự kiện
        timestamp: Mốc thời gian của sự kiện
        message: Message đính kèm nếu sự kiện liên quan đến gửi/nhận message
        data: Metadata bổ sung cho việc phân tích
    """
    event_type: str
    node_id: int
    timestamp: float
    message: Optional[Message] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Chuyển Event thành dictionary.

        Returns:
            Dict[str, Any]: Dữ liệu dạng dict của event
        """
        return {
            "event_type": self.event_type,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "message": self.message.to_dict() if self.message else None,
            "data": self.data,
        }


@dataclass
class NodeAction:
    """
    Hành động được lên lịch trong một scenario mô phỏng.

    Attributes:
        at_ms: Thời điểm thực thi hành động, tính theo millisecond kể từ lúc bắt đầu
        action_type: Loại hành động (request_cs, release_cs, crash_node, recover_node)
        node_id: Node thực hiện hành động
        data: Dữ liệu bổ sung cho hành động
    """
    at_ms: int
    action_type: str
    node_id: int
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioDefinition:
    """
    Định nghĩa một kịch bản mô phỏng hoàn chỉnh.

    Attributes:
        name: Tên scenario
        description: Mô tả ngắn gọn scenario
        num_nodes: Số node tham gia mô phỏng
        network_delay_ms: Độ trễ mạng giả lập
        actions: Danh sách hành động được chạy theo thời gian
    """
    name: str
    description: str
    num_nodes: int
    network_delay_ms: int
    actions: List[NodeAction] = field(default_factory=list)


@dataclass
class SimulationResult:
    """
    Kết quả của một lần chạy mô phỏng.

    Attributes:
        scenario_name: Tên scenario đã chạy
        events: Danh sách event log thu được
        raw_stats: Thống kê thô lấy từ adapter hoặc thuật toán
        metrics: Chỉ số phân tích sau khi xử lý event log
    """
    scenario_name: str
    events: List[Event] = field(default_factory=list)
    raw_stats: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)


class EventType:
    """
    Tập hằng số cho các loại event log dùng chung trong simulation.
    """
    REQUEST_CS = "REQUEST_CS"
    ENTER_CS = "ENTER_CS"
    EXIT_CS = "EXIT_CS"
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    NODE_CRASH = "NODE_CRASH"
    NODE_RECOVER = "NODE_RECOVER"


class MessageType:
    """
    Tập hằng số cho các loại message dùng chung trong simulation.
    """
    REQUEST = "REQUEST"
    REPLY = "REPLY"
    RELEASE = "RELEASE"
    TOKEN = "TOKEN"
    GRANT = "GRANT"
    ACK = "ACK"
    DATA = "DATA"


class ActionType:
    """
    Tập hằng số cho các hành động có thể xuất hiện trong scenario.
    """
    REQUEST_CS = "request_cs"
    RELEASE_CS = "release_cs"
    CRASH_NODE = "crash_node"
    RECOVER_NODE = "recover_node"


class AlgorithmAdapter(ABC):
    """
    Interface chung để ghép từng thuật toán vào Simulation Engine.

    Mỗi thuật toán như Centralized, Ricart-Agrawala, Token Ring
    cần có một adapter triển khai interface này để TV4 có thể:
    - chạy mô phỏng
    - thu event log
    - đo metrics
    - so sánh công bằng giữa các thuật toán
    """

    @abstractmethod
    def setup(self, num_nodes: int, network_delay_ms: int = 0) -> None:
        """
        Khởi tạo môi trường cho thuật toán.

        Args:
            num_nodes: Số node trong hệ mô phỏng
            network_delay_ms: Độ trễ mạng giả lập
        """
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """
        Khởi động thuật toán hoặc các node tương ứng.
        """
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """
        Dừng thuật toán hoặc các node tương ứng.
        """
        raise NotImplementedError

    @abstractmethod
    def request_critical_section(self, node_id: int) -> None:
        """
        Yêu cầu một node xin vào critical section.

        Args:
            node_id: ID node muốn vào critical section
        """
        raise NotImplementedError

    @abstractmethod
    def release_critical_section(self, node_id: int) -> None:
        """
        Yêu cầu một node rời khỏi critical section.

        Args:
            node_id: ID node rời critical section
        """
        raise NotImplementedError

    @abstractmethod
    def crash_node(self, node_id: int) -> None:
        """
        Giả lập node bị lỗi.

        Args:
            node_id: ID node bị crash
        """
        raise NotImplementedError

    @abstractmethod
    def recover_node(self, node_id: int) -> None:
        """
        Giả lập node phục hồi sau lỗi.

        Args:
            node_id: ID node được recover
        """
        raise NotImplementedError

    @abstractmethod
    def send_message(self, message: Message) -> None:
        """
        Gửi một Message theo chuẩn chung.

        Args:
            message: Gói tin chuẩn dùng trong hệ mô phỏng
        """
        raise NotImplementedError

    @abstractmethod
    def get_event_log(self) -> List[Event]:
        """
        Lấy toàn bộ event log của lần chạy.

        Returns:
            List[Event]: Danh sách event đã ghi nhận
        """
        raise NotImplementedError

    @abstractmethod
    def collect_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê thô do thuật toán hoặc adapter cung cấp.

        Returns:
            Dict[str, Any]: Raw statistics
        """
        raise NotImplementedError