import socket
import threading
import time
from .message import Message
from .config import random_network_delay


class Network:
    def __init__(self, node_id, host, port, on_message_received):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.on_message_received = on_message_received
        self._stop_event = threading.Event()
        self.server_thread = threading.Thread(target=self._start_server, daemon=True)
        self.owner_node = None

    def start(self):
        if self.server_thread.is_alive():
            return
        self._stop_event.clear()
        self.server_thread = threading.Thread(target=self._start_server, daemon=True)
        self.server_thread.start()

    def stop(self):
        self._stop_event.set()

    def _start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self.port))
            server.listen(5)

            while not self._stop_event.is_set():
                try:
                    server.settimeout(1.0)
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break

                threading.Thread(
                    target=self._handle_connection,
                    args=(conn,),
                    daemon=True
                ).start()
        finally:
            server.close()

    def _handle_connection(self, conn):
        if self.owner_node is not None and not self.owner_node.active:
            conn.close()
            return

        with conn:
            data = b""
            while True:
                try:
                    chunk = conn.recv(4096)
                except ConnectionResetError:
                    break
                except OSError:
                    break

                if not chunk:
                    break
                data += chunk

            if not data:
                return

            text = data.decode("utf-8").strip()
            for line in text.split("\n"):
                if not line:
                    continue

                if self.owner_node is not None and not self.owner_node.active:
                    return

                try:
                    msg = Message.from_json(line)
                    self.on_message_received(msg)
                except Exception:
                    continue

    def send_message(self, target_host, target_port, msg):
        if self.owner_node is not None and not self.owner_node.active:
            return

        delay = random_network_delay()
        time.sleep(delay)

        if self.owner_node is not None and not self.owner_node.active:
            return

        try:
            with socket.create_connection((target_host, target_port), timeout=5) as sock:
                payload = msg.to_json() + "\n"
                sock.sendall(payload.encode("utf-8"))
        except Exception:
            pass