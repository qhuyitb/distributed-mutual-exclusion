"""Tien trinh Coordinator cho thuat toan loai tru tuong ho tap trung qua TCP.

Coordinator nhan REQUEST/RELEASE tu cac node participant,
quan ly trang thai khoa va hang doi FIFO,
roi gui GRANT cho node phu hop.
"""

import argparse
import socket
import threading
import time
from queue import Queue
from typing import Dict, Tuple

try:
    from .message import Message, MessageType
except ImportError:
    from message import Message, MessageType


class CoordinatorServer:
    """Tien trinh Coordinator cap quyen vao vung toi han."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7500):
        self.host = host
        self.port = int(port)
        self.coordinator_id = -1

        self.is_locked = False
        self.queue: Queue[int] = Queue()
        self.node_addresses: Dict[int, Tuple[str, int]] = {}

        self._lock = threading.Lock()
        self._running = False
        self._server: socket.socket | None = None

    def start(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(32)
        self._server.settimeout(1.0)
        self._running = True

        print(f"[Coordinator] listening on {self.host}:{self.port}")

        while self._running:
            try:
                client, addr = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()

    def stop(self) -> None:
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass

    def _handle_client(self, client: socket.socket, addr: Tuple[str, int]) -> None:
        try:
            data = client.recv(4096)
            if not data:
                return
            message = Message.from_bytes(data)

            if isinstance(message.data, dict):
                listen_host = message.data.get("listen_host", addr[0])
                listen_port = message.data.get("listen_port")
                if listen_port is not None:
                    with self._lock:
                        self.node_addresses[message.sender_id] = (str(listen_host), int(listen_port))

            if message.msg_type == MessageType.REQUEST:
                self._handle_request(message.sender_id)
            elif message.msg_type == MessageType.RELEASE:
                self._handle_release(message.sender_id)
        except Exception as exc:
            print(f"[Coordinator] error handling client: {exc}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _handle_request(self, node_id: int) -> None:
        with self._lock:
            print(f"[Coordinator] REQUEST from Node {node_id}")
            if not self.is_locked:
                self.is_locked = True
                self._grant(node_id)
            else:
                self.queue.put(node_id)
                print(f"[Coordinator] queued Node {node_id}")

    def _handle_release(self, node_id: int) -> None:
        with self._lock:
            print(f"[Coordinator] RELEASE from Node {node_id}")
            if not self.queue.empty():
                next_node = self.queue.get()
                self._grant(next_node)
            else:
                self.is_locked = False
                print("[Coordinator] resource free")

    def _grant(self, node_id: int) -> None:
        target = self.node_addresses.get(node_id)
        if target is None:
            print(f"[Coordinator] cannot GRANT Node {node_id}: unknown address")
            self.is_locked = False
            return

        host, port = target
        msg = Message(
            msg_type=MessageType.GRANT,
            sender_id=self.coordinator_id,
            receiver_id=node_id,
            timestamp=time.time(),
        )

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            s.sendall(msg.to_bytes())
            s.close()
            print(f"[Coordinator] GRANT -> Node {node_id} ({host}:{port})")
        except Exception as exc:
            print(f"[Coordinator] failed GRANT to Node {node_id}: {exc}")
            self.is_locked = False


def main() -> None:
    parser = argparse.ArgumentParser(description="Tien trinh coordinator cua thuat toan tap trung")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7500)
    args = parser.parse_args()

    server = CoordinatorServer(host=args.host, port=args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Coordinator] shutting down")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
