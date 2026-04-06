import threading
from queue import Queue
import time

try:
    from .communication import CommunicationLayer
    from .message import Message, MessageType
except ImportError:
    from communication import CommunicationLayer
    from message import Message, MessageType

"""Triển khai Coordinator cho thuật toán loại trừ tương hỗ tập trung.

Coordinator duy trì hai trạng thái cốt lõi đúng theo đặc tả:
- is_locked: cho biết vùng tới hạn đang được cấp cho một tiến trình hay chưa.
- queue FIFO: lưu các yêu cầu REQUEST đến khi tài nguyên đang bận.

Quy tắc xử lý:
- Nhận REQUEST khi rảnh: gửi GRANT ngay và đặt is_locked = True.
- Nhận REQUEST khi bận: đưa nút vào hàng đợi FIFO.
- Nhận RELEASE: nếu có hàng đợi thì cấp GRANT cho nút đầu hàng,
  nếu không thì đặt is_locked = False.
"""


class Coordinator:
    """Bộ điều phối trung tâm cấp quyền vào vùng tới hạn."""

    def __init__(self, coordinator_id: int, comm: CommunicationLayer):
        self.id = coordinator_id
        self.comm = comm

        # Trạng thái vùng tới hạn
        self.is_locked = False

        # Hàng đợi FIFO các request
        self.queue = Queue()

        # Lock để tránh race condition
        self.lock = threading.Lock()

        self._next_request_id = 1

    def _new_request_id(self) -> int:
        """Sinh mã yêu cầu nội bộ để hỗ trợ theo dõi và log."""

        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id

    def on_message(self, message: Message):
        """Điểm vào xử lý thông điệp từ tầng giao tiếp."""

        if message.msg_type == MessageType.REQUEST:
            self.handle_request(message)
        elif message.msg_type == MessageType.RELEASE:
            self.handle_release(message)

    def _grant(self, node_id: int) -> None:
        """Tạo và gửi thông điệp GRANT cho một participant."""

        grant = Message(
            msg_type=MessageType.GRANT,
            sender_id=self.id,
            receiver_id=node_id,
            timestamp=time.time(),
            request_id=self._new_request_id(),
        )
        print(f"[Coordinator] -> GRANT cho Node {node_id}")
        self.comm.send(grant)

    def handle_request(self, message: Message):
        """Xử lý REQUEST theo đúng chính sách cấp quyền tập trung."""

        with self.lock:
            requester_id = message.sender_id
            print(f"[Coordinator] REQUEST tu Node {requester_id}")

            if not self.is_locked:
                self.is_locked = True
                self._grant(requester_id)
            else:
                print(f"[Coordinator] -> Queue Node {requester_id}")
                self.queue.put(requester_id)

    def handle_release(self, message: Message):
        """Xử lý RELEASE và cấp quyền tiếp theo theo thứ tự FIFO."""

        with self.lock:
            print(f"[Coordinator] RELEASE tu Node {message.sender_id}")

            if not self.queue.empty():
                next_node = self.queue.get()
                self._grant(next_node)
            else:
                self.is_locked = False
                print(f"[Coordinator] -> Resource FREE")