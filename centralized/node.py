import threading
import time

try:
    from .communication import CommunicationLayer
    from .message import Message, MessageType
except ImportError:
    from communication import CommunicationLayer
    from message import Message, MessageType

"""Triển khai Participant trong thuật toán tập trung.

Mỗi Node cung cấp hai thao tác mức ứng dụng:
- enter_CS(): gửi REQUEST và chờ GRANT (blocking).
- exit_CS(): gửi RELEASE sau khi rời vùng tới hạn.

Tầng ứng dụng chỉ gọi enter_CS/exit_CS mà không cần biết chi tiết truyền thông.
"""

class Node:
    """Tiến trình tham gia giao thức cấp quyền bởi Coordinator."""

    def __init__(self, node_id: int, coordinator_id: int, comm: CommunicationLayer):
        self.id = node_id
        self.coordinator_id = coordinator_id
        self.comm = comm
        self.granted_event = threading.Event()
        self.last_request_ts = None
        self.last_grant_latency = None

    def on_message(self, message: Message):
        """Nhận thông điệp từ tầng giao tiếp và xử lý các loại liên quan."""

        if message.msg_type == MessageType.GRANT:
            self.receive_grant()

    def receive_grant(self):
        """Đánh dấu đã được cấp quyền để enter_CS tiếp tục thực thi."""

        grant_ts = time.time()
        if self.last_request_ts is not None:
            self.last_grant_latency = grant_ts - self.last_request_ts
        print(f"[Node {self.id}] Nhan GRANT")
        self.granted_event.set()

    def enter_CS(self, wait_timeout: float = 10.0):
        print(f"[Node {self.id}] Gui REQUEST")
        self.last_request_ts = time.time()
        request = Message(
            msg_type=MessageType.REQUEST,
            sender_id=self.id,
            receiver_id=self.coordinator_id,
            timestamp=self.last_request_ts,
        )
        self.comm.send(request)

        # Cho GRANT
        granted = self.granted_event.wait(timeout=wait_timeout)
        if not granted:
            raise TimeoutError(
                f"Node {self.id} timeout waiting GRANT - possible coordinator failure"
            )

        print(f"[Node {self.id}] >>> ENTER CS")
        time.sleep(2)
        self.exit_CS()

    def exit_CS(self):
        """Rời vùng tới hạn và gửi RELEASE cho Coordinator."""

        print(f"[Node {self.id}] <<< EXIT CS")
        self.granted_event.clear()
        release = Message(
            msg_type=MessageType.RELEASE,
            sender_id=self.id,
            receiver_id=self.coordinator_id,
            timestamp=time.time(),
        )
        self.comm.send(release)