import threading
import time

"""
Node module - mô phỏng các tiến trình tham gia hệ thống phân tán.

Mỗi Node có nhiệm vụ:
- Gửi yêu cầu truy cập (REQUEST) đến Coordinator
- Chờ cấp quyền (GRANT)
- Thực thi trong Critical Section
- Giải phóng tài nguyên bằng thông điệp RELEASE

Module này thể hiện hành vi của các participant trong thuật toán Centralized.
"""

class Node:
    def __init__(self, node_id, coordinator):
        self.id = node_id
        self.coordinator = coordinator
        self.granted_event = threading.Event()

    # Nhận GRANT
    def receive_grant(self):
        print(f"[Node {self.id}] Nhận GRANT")
        self.granted_event.set()

    # Yêu cầu vào CS
    def enter_CS(self):
        print(f"[Node {self.id}] Gửi REQUEST")
        self.coordinator.handle_request(self)

        # Chờ GRANT
        self.granted_event.wait()

        print(f"[Node {self.id}] >>> ENTER CS")
        time.sleep(2)  

        self.exit_CS()

    # Thoát CS
    def exit_CS(self):
        print(f"[Node {self.id}] <<< EXIT CS")
        self.granted_event.clear()
        self.coordinator.handle_release(self)