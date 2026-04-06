import socket
import threading
from typing import Dict, Protocol, Tuple

try:
    from .message import Message
except ImportError:
    from message import Message


class Endpoint(Protocol):
    """Giao diện tối thiểu cho một endpoint nhận thông điệp."""

    def on_message(self, message: Message) -> None:
        ...


class CommunicationLayer:
    """Lớp giao tiếp trung gian theo mô hình Stub/Skeleton dùng TCP.

    Mỗi endpoint được gán một host/port và có listener riêng.
    Việc gửi thông điệp dùng TCP sockets để mô phỏng kênh tin cậy.
    """

    def __init__(self):
        self._endpoints: Dict[int, Endpoint] = {}
        self._addresses: Dict[int, Tuple[str, int]] = {}
        self._servers: Dict[int, socket.socket] = {}
        self._listener_threads: Dict[int, threading.Thread] = {}
        self._lock = threading.Lock()
        self._running = False
        self.total_messages = 0

    def register(self, endpoint_id: int, endpoint: Endpoint, host: str = "127.0.0.1", port: int = 0) -> None:
        """Đăng ký endpoint cùng địa chỉ TCP dùng để nhận thông điệp."""

        with self._lock:
            if self._running:
                raise RuntimeError("Cannot register endpoint while communication layer is running")
            self._endpoints[endpoint_id] = endpoint
            self._addresses[endpoint_id] = (host, int(port))

    def start(self) -> None:
        """Khởi động listener TCP cho toàn bộ endpoint đã đăng ký."""

        with self._lock:
            if self._running:
                return
            self._running = True
            endpoint_ids = list(self._endpoints.keys())

        for endpoint_id in endpoint_ids:
            listener = threading.Thread(target=self._serve_endpoint, args=(endpoint_id,))
            listener.start()
            with self._lock:
                self._listener_threads[endpoint_id] = listener

    def stop(self) -> None:
        """Dừng toàn bộ listener và giải phóng cổng mạng."""

        with self._lock:
            self._running = False
            servers = list(self._servers.values())
            listeners = list(self._listener_threads.values())
            self._servers.clear()
            self._listener_threads.clear()

        for srv in servers:
            try:
                srv.close()
            except Exception:
                pass

        for listener in listeners:
            listener.join(timeout=1.0)

    def _serve_endpoint(self, endpoint_id: int) -> None:
        with self._lock:
            endpoint = self._endpoints.get(endpoint_id)
            address = self._addresses.get(endpoint_id)

        if endpoint is None or address is None:
            return

        host, port = address
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(16)
        server.settimeout(0.5)

        with self._lock:
            self._servers[endpoint_id] = server

        while True:
            with self._lock:
                running = self._running
            if not running:
                break

            try:
                client, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self._handle_client(endpoint, client)

        try:
            server.close()
        except Exception:
            pass

    @staticmethod
    def _handle_client(endpoint: Endpoint, client_sock: socket.socket) -> None:
        try:
            data = client_sock.recv(4096)
            if not data:
                return
            message = Message.from_bytes(data)
            endpoint.on_message(message)
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def send(self, message: Message) -> None:
        """Gửi thông điệp tới endpoint nhận tương ứng.

        Nếu không tìm thấy endpoint đích, hàm ném lỗi để phát hiện cấu hình sai.
        """

        with self._lock:
            target_addr = self._addresses.get(message.receiver_id)
            self.total_messages += 1

        if target_addr is None:
            raise RuntimeError(f"Unknown endpoint id: {message.receiver_id}")

        host, port = target_addr
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            sock.connect((host, port))
            sock.sendall(message.to_bytes())
        finally:
            sock.close()
