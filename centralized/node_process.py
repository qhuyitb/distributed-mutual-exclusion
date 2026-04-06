"""Tien trinh Participant cho thuat toan loai tru tuong ho tap trung qua TCP.

File nay phuc vu demo da tien trinh:
- Moi node la mot process rieng.
- Node gui REQUEST/RELEASE den Coordinator.
- Node mo listener de nhan GRANT tu Coordinator.
"""

import argparse
import socket
import threading
import time

try:
    from .message import Message, MessageType
except ImportError:
    from message import Message, MessageType


class NodeProcess:
    """Tien trinh Participant cho giao thuc cap quyen tap trung."""

    def __init__(
        self,
        node_id: int,
        coordinator_host: str = "127.0.0.1",
        coordinator_port: int = 7500,
        listen_host: str = "127.0.0.1",
        listen_port: int | None = None,
    ):
        self.node_id = int(node_id)
        self.coordinator_host = coordinator_host
        self.coordinator_port = int(coordinator_port)
        self.listen_host = listen_host
        self.listen_port = int(listen_port) if listen_port is not None else (7600 + self.node_id)

        self._granted = threading.Event()
        self._running = False
        self._server: socket.socket | None = None

    def start(self, auto_request: bool = False, hold_seconds: float = 2.0) -> None:
        self._running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        time.sleep(0.2)

        print(f"[Node {self.node_id}] listening on {self.listen_host}:{self.listen_port}")
        print(f"[Node {self.node_id}] coordinator: {self.coordinator_host}:{self.coordinator_port}")

        if auto_request:
            self.enter_cs(hold_seconds=hold_seconds)
            self.stop()
            return

        self._run_cli()

    def stop(self) -> None:
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass

    def _listen_loop(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.listen_host, self.listen_port))
        self._server.listen(16)
        self._server.settimeout(1.0)

        while self._running:
            try:
                client, _ = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                data = client.recv(4096)
                if not data:
                    continue
                msg = Message.from_bytes(data)
                if msg.msg_type == MessageType.GRANT:
                    print(f"[Node {self.node_id}] received GRANT")
                    self._granted.set()
            finally:
                try:
                    client.close()
                except Exception:
                    pass

    def enter_cs(self, hold_seconds: float = 2.0, wait_timeout: float = 15.0) -> None:
        self._granted.clear()
        print(f"[Node {self.node_id}] send REQUEST")
        sent_ok = self._send_to_coordinator(MessageType.REQUEST)
        if not sent_ok:
            print(f"[Node {self.node_id}] REQUEST failed, skip waiting")
            return

        granted = self._granted.wait(timeout=wait_timeout)
        if not granted:
            print(f"[Node {self.node_id}] timeout waiting GRANT")
            return

        print(f"[Node {self.node_id}] >>> ENTER CS")
        time.sleep(hold_seconds)
        self.exit_cs()

    def exit_cs(self) -> None:
        print(f"[Node {self.node_id}] <<< EXIT CS")
        self._send_to_coordinator(MessageType.RELEASE)

    def _send_to_coordinator(self, msg_type: MessageType) -> bool:
        msg = Message(
            msg_type=msg_type,
            sender_id=self.node_id,
            receiver_id=-1,
            timestamp=time.time(),
            data={"listen_host": self.listen_host, "listen_port": self.listen_port},
        )

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect((self.coordinator_host, self.coordinator_port))
            sock.sendall(msg.to_bytes())
            return True
        except Exception as exc:
            print(f"[Node {self.node_id}] send error: {exc}")
            return False
        finally:
            sock.close()

    def _run_cli(self) -> None:
        print(f"[Node {self.node_id}] commands: request [hold_seconds], quit")
        while self._running:
            try:
                raw = input(f"[Node {self.node_id}] > ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                raw = "quit"

            if not raw:
                continue
            if raw == "quit":
                break
            if raw.startswith("request"):
                parts = raw.split()
                hold = 2.0
                if len(parts) == 2:
                    try:
                        hold = float(parts[1])
                    except ValueError:
                        print(f"[Node {self.node_id}] invalid hold_seconds")
                        continue
                threading.Thread(
                    target=self.enter_cs,
                    kwargs={"hold_seconds": hold, "wait_timeout": self.wait_timeout},
                    daemon=True,
                ).start()
            else:
                print(f"[Node {self.node_id}] unknown command")

        self.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Tien trinh participant cua thuat toan tap trung")
    parser.add_argument("--node-id", type=int, required=True)
    parser.add_argument("--coordinator-host", default="127.0.0.1")
    parser.add_argument("--coordinator-port", type=int, default=7500)
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int)
    parser.add_argument("--auto-request", action="store_true")
    parser.add_argument("--hold-seconds", type=float, default=2.0)
    parser.add_argument("--wait-timeout", type=float, default=6.0)
    args = parser.parse_args()

    node = NodeProcess(
        node_id=args.node_id,
        coordinator_host=args.coordinator_host,
        coordinator_port=args.coordinator_port,
        listen_host=args.listen_host,
        listen_port=args.listen_port,
    )
    node.wait_timeout = args.wait_timeout

    try:
        if args.auto_request:
            node._running = True
            threading.Thread(target=node._listen_loop, daemon=True).start()
            time.sleep(0.2)
            print(f"[Node {node.node_id}] listening on {node.listen_host}:{node.listen_port}")
            print(f"[Node {node.node_id}] coordinator: {node.coordinator_host}:{node.coordinator_port}")
            node.enter_cs(hold_seconds=args.hold_seconds, wait_timeout=args.wait_timeout)
            node.stop()
        else:
            node.start(auto_request=False, hold_seconds=args.hold_seconds)
    except KeyboardInterrupt:
        print(f"\n[Node {args.node_id}] shutting down")
    finally:
        node.stop()


if __name__ == "__main__":
    main()
