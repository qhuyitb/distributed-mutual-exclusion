import threading
from queue import Queue

"""
Coordinator module - triển khai bộ điều phối trong thuật toán Centralized.

Module này chịu trách nhiệm:
- Quản lý quyền truy cập vào Critical Section
- Xử lý các thông điệp REQUEST và RELEASE
- Duy trì trạng thái tài nguyên và hàng đợi FIFO

Đảm bảo tại mỗi thời điểm chỉ có một node được phép truy cập tài nguyên dùng chung.
"""


class Coordinator:
    def __init__(self):
        # Trạng thái vùng tới hạn
        self.is_locked = False

        # Hàng đợi FIFO các request
        self.queue = Queue()

        # Lock để tránh race condition
        self.lock = threading.Lock()

    def handle_request(self, node):
        with self.lock:
            print(f"[Coordinator] REQUEST từ Node {node.id}")

            if not self.is_locked:
                self.is_locked = True
                print(f"[Coordinator] → GRANT cho Node {node.id}")
                node.receive_grant()
            else:
                print(f"[Coordinator] → Queue Node {node.id}")
                self.queue.put(node)

    def handle_release(self, node):
        with self.lock:
            print(f"[Coordinator] RELEASE từ Node {node.id}")

            if not self.queue.empty():
                next_node = self.queue.get()
                print(f"[Coordinator] → GRANT cho Node {next_node.id}")
                next_node.receive_grant()
            else:
                self.is_locked = False
                print(f"[Coordinator] → Resource FREE")