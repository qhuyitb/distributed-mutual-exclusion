"""
Node Process - Node client độc lập
Mỗi node chạy trong 1 process riêng, kết nối tới Coordinator
Có interactive CLI để request hoặc quit
"""
import socket
import threading
import json
import time
import sys
from collections import deque
from typing import Dict, Tuple


class NodeProcess:
    """Node process độc lập - Ricart-Agrawala client"""

    def __init__(self, node_id: int, num_nodes: int,
                 coordinator_host: str = "localhost",
                 coordinator_port: int = 5000,
                 listen_port: int = None):
        self.id = node_id
        self.num_nodes = num_nodes
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.listen_port = listen_port or (6000 + node_id)

        # Logical clock & state
        self.logical_clock = 0
        self.request_queue = deque()           # (node_id, timestamp)
        self.waiting_for_replies: set = set()
        self.in_cs = False
        self.replies_received = 0
        self.seq_num = 0
        self.my_request_timestamp = float('inf')

        # Synchronization
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.running = True

        # Network
        self.coordinator_socket = None
        self.other_nodes: Dict[int, Tuple[str, int]] = {}
        self.server_socket = None

    # ------------------------------------------------------------------ start
    def start(self):
        print(f"\n[Node {self.id}] Starting...")
        print(f"[Node {self.id}] Listening on port {self.listen_port}")

        threading.Thread(target=self._start_server, daemon=True).start()
        time.sleep(0.5)

        self._connect_to_coordinator()
        self._run_cli()

    # ------------------------------------------------------------------ server (receive)
    def _start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("localhost", self.listen_port))
        self.server_socket.listen(10)

        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_incoming_message,
                    args=(client_socket,),
                    daemon=True,
                ).start()
            except Exception:
                break

    def _handle_incoming_message(self, client_socket: socket.socket):
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                msg_dict = json.loads(data)
                msg_type = msg_dict.get('msg_type')
                if msg_type == 'REQUEST':
                    self._handle_request(msg_dict)
                elif msg_type == 'REPLY':
                    self._handle_reply(msg_dict)
        except Exception as e:
            print(f"[Node {self.id}] Error handling message: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ coordinator
    def _connect_to_coordinator(self):
        try:
            self.coordinator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.coordinator_socket.connect((self.coordinator_host, self.coordinator_port))

            register_msg = {
                'type': 'REGISTER',
                'node_id': self.id,
                'num_nodes': self.num_nodes,
                'listen_port': self.listen_port,
            }
            self.coordinator_socket.send(json.dumps(register_msg).encode('utf-8'))

            data = self.coordinator_socket.recv(4096).decode('utf-8')
            nodes_info = json.loads(data)

            with self.lock:
                for node_id, info in nodes_info['nodes'].items():
                    self.other_nodes[int(node_id)] = (info['host'], info['port'])

            print(f"[Node {self.id}] Connected to Coordinator")
            print(f"[Node {self.id}] Other nodes: {self.other_nodes}")

            threading.Thread(target=self._listen_coordinator_updates, daemon=True).start()

        except Exception as e:
            print(f"[Node {self.id}] Error connecting to Coordinator: {e}")
            sys.exit(1)

    def _listen_coordinator_updates(self):
        while self.running:
            try:
                data = self.coordinator_socket.recv(4096).decode('utf-8')
                if data:
                    msg_dict = json.loads(data)
                    if msg_dict.get('type') == 'NODES_UPDATE':
                        with self.lock:
                            self.other_nodes = {
                                int(nid): (info['host'], info['port'])
                                for nid, info in msg_dict['nodes'].items()
                            }
                        print(f"[Node {self.id}] Updated nodes list: {self.other_nodes}")
            except Exception:
                break

    # ------------------------------------------------------------------ clock
    def _increment_clock(self) -> int:
        """Tăng logical clock trong lock, trả về giá trị mới."""
        with self.lock:
            self.logical_clock += 1
            return self.logical_clock

    def _update_clock(self, timestamp: int):
        with self.lock:
            self.logical_clock = max(self.logical_clock, timestamp) + 1

    # ------------------------------------------------------------------ CS
    def send_request(self):
        """Gửi REQUEST tới tất cả nodes khác và chờ đủ REPLY."""
        # --- Chuẩn bị state trong lock, lấy snapshot trước khi gửi ---
        with self.lock:
            self.logical_clock += 1
            request_ts = self.logical_clock
            self.request_queue.append((self.id, request_ts))
            self.waiting_for_replies = set(
                i for i in range(self.num_nodes) if i != self.id
            )
            self.replies_received = 0
            self.seq_num += 1
            self.my_request_timestamp = request_ts
            nodes_to_send = list(self.waiting_for_replies)   # snapshot - FIX chính
            num_expected = len(self.waiting_for_replies)

        print(f"\n[Node {self.id}] >>> REQUESTING (ts={request_ts})")

        # --- Gửi REQUEST dùng snapshot, không đụng self.waiting_for_replies ---
        for node_id in nodes_to_send:
            with self.lock:
                addr = self.other_nodes.get(node_id)
            if addr:
                host, port = addr
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((host, port))
                    sock.send(json.dumps({
                        'msg_type': 'REQUEST',
                        'sender_id': self.id,
                        'receiver_id': node_id,
                        'timestamp': request_ts,
                        'sequence_num': self.seq_num,
                    }).encode('utf-8'))
                    sock.close()
                    print(f"[Node {self.id}] Sent REQUEST to Node {node_id}")
                except Exception as e:
                    print(f"[Node {self.id}] Error sending REQUEST to Node {node_id}: {e}")

        # --- Chờ đủ REPLY ---
        with self.lock:
            while self.replies_received < num_expected:
                self.condition.wait(timeout=5)

        print(f"[Node {self.id}] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts={request_ts})")
        self.in_cs = True

        time.sleep(2)  # Giả lập công việc trong CS

        self.release_cs()

    def release_cs(self):
        """Thoát CS và gửi REPLY cho pending requests."""
        with self.lock:
            print(f"[Node {self.id}] ✗ EXITING CS")
            self.in_cs = False
            self.my_request_timestamp = float('inf')
            self.request_queue = deque(
                (nid, ts) for nid, ts in self.request_queue if nid != self.id
            )
            pending = list(self.request_queue)
            self.logical_clock += 1
            reply_ts = self.logical_clock

        for requester_id, _ in pending:
            with self.lock:
                addr = self.other_nodes.get(requester_id)
            if addr:
                host, port = addr
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((host, port))
                    sock.send(json.dumps({
                        'msg_type': 'REPLY',
                        'sender_id': self.id,
                        'receiver_id': requester_id,
                        'timestamp': reply_ts,
                        'sequence_num': self.seq_num,
                    }).encode('utf-8'))
                    sock.close()
                    print(f"[Node {self.id}] Sent REPLY to Node {requester_id}")
                except Exception as e:
                    print(f"[Node {self.id}] Error sending REPLY to {requester_id}: {e}")
            else:
                print(f"[Node {self.id}] Node {requester_id} not known, skipping REPLY")

    # ------------------------------------------------------------------ handlers
    def _handle_request(self, msg_dict: dict):
        sender_id = msg_dict['sender_id']
        timestamp = msg_dict['timestamp']

        self._update_clock(timestamp)

        with self.lock:
            self.request_queue.append((sender_id, timestamp))
            incoming_priority = (timestamp, sender_id)
            my_priority = (self.my_request_timestamp, self.id)
            should_reply = (
                not self.in_cs
                and (not self.waiting_for_replies or incoming_priority < my_priority)
            )
            reply_ts = self.logical_clock
            addr = self.other_nodes.get(sender_id)

        if should_reply and addr:
            host, port = addr
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, port))
                sock.send(json.dumps({
                    'msg_type': 'REPLY',
                    'sender_id': self.id,
                    'receiver_id': sender_id,
                    'timestamp': reply_ts,
                    'sequence_num': msg_dict.get('sequence_num', 0),
                }).encode('utf-8'))
                sock.close()
                print(f"[Node {self.id}] Sent REPLY immediately to Node {sender_id}")
            except Exception as e:
                print(f"[Node {self.id}] Error sending REPLY: {e}")

    def _handle_reply(self, msg_dict: dict):
        sender_id = msg_dict['sender_id']
        timestamp = msg_dict['timestamp']

        self._update_clock(timestamp)

        with self.lock:
            if sender_id in self.waiting_for_replies:
                self.waiting_for_replies.discard(sender_id)
                self.replies_received += 1
                expected = self.num_nodes - 1
                print(f"[Node {self.id}] Received REPLY from Node {sender_id} "
                      f"({self.replies_received}/{expected})")
                if self.replies_received >= expected:
                    self.condition.notify_all()

    # ------------------------------------------------------------------ CLI
    def _run_cli(self):
        print(f"\n[Node {self.id}] Ready for commands")
        print(f"[Node {self.id}] Type 'request' or 'quit'\n")

        while self.running:
            try:
                cmd = input(f"[Node {self.id}] > ").strip().lower()
                if cmd == 'request':
                    threading.Thread(target=self.send_request, daemon=True).start()
                elif cmd == 'quit':
                    print(f"\n[Node {self.id}] Shutting down...")
                    self.running = False
                    break
                else:
                    print(f"[Node {self.id}] Unknown command: {cmd}")
            except (KeyboardInterrupt, EOFError):
                print(f"\n[Node {self.id}] Shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"[Node {self.id}] Error: {e}")

        self._cleanup()

    def _cleanup(self):
        self.running = False
        for sock in [self.coordinator_socket, self.server_socket]:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python node_process.py <node_id> [num_nodes]")
        print("Example: python node_process.py 0 3")
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
        num_nodes = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    except ValueError:
        print("Error: Arguments must be integers")
        sys.exit(1)

    node = NodeProcess(node_id=node_id, num_nodes=num_nodes)
    node.start()


if __name__ == "__main__":
    main()