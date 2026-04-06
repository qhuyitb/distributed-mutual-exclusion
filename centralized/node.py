import threading
import time


class Node:
    def __init__(self, node_id, coordinator, adapter=None):
        self.id = node_id
        self.coordinator = coordinator
        self.granted_event = threading.Event()
        self.adapter = adapter
        self.active = True
        self.in_cs = False

    def receive_grant(self):
        if not self.active:
            return

        print(f"[Node {self.id}] Nhận GRANT")

        if self.adapter:
            self.adapter.log_message_received("GRANT", 0, self.id)

        self.granted_event.set()

    def enter_CS(self):
        if not self.active:
            return

        print(f"[Node {self.id}] Gửi REQUEST")

        if self.adapter:
            self.adapter.log_request_cs(self.id)
            self.adapter.log_message_sent("REQUEST", self.id, 0)

        self.coordinator.handle_request(self)
        self.granted_event.wait()

        if not self.active:
            return

        self.in_cs = True
        if self.adapter:
            self.adapter.log_enter_cs(self.id)

        print(f"[Node {self.id}] >>> ENTER CS")
        time.sleep(2)

        self.exit_CS()

    def exit_CS(self):
        if not self.active or not self.in_cs:
            return

        print(f"[Node {self.id}] <<< EXIT CS")

        if self.adapter:
            self.adapter.log_exit_cs(self.id)
            self.adapter.log_message_sent("RELEASE", self.id, 0)

        self.in_cs = False
        self.granted_event.clear()
        self.coordinator.handle_release(self)

    def force_release(self):
        if self.in_cs:
            self.exit_CS()