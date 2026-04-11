"""
common/base_process.py
----------------------
Lớp cơ sở (BaseProcess) dùng chung cho cả 3 thuật toán.

Mỗi thuật toán kế thừa BaseProcess và override:
  - _handle_message(msg, conn) : xử lý message nhận được
  - request_cs()               : logic xin vào CS
  - release_cs()               : logic ra khỏi CS

Sơ đồ kế thừa:
  BaseProcess
  ├── centralized/CoordinatorProcess
  ├── centralized/ClientProcess
  ├── distributed/RAProcess         (Ricart-Agrawala)
  └── token_ring/RingProcess
"""

import socket
import threading
import logging
import time
import queue
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from common.network import make_server_socket, recv_msg, send_to, send_to_async
from common.message import parse_msg, make_msg, fmt_msg, MsgType

# Cấu hình logging: mỗi process in ra pid + level + nội dung
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-12s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S"
)


# ─────────────────────────────────────────────
# Kiểu dữ liệu biểu diễn 1 peer process
# ─────────────────────────────────────────────

class PeerInfo:
    """Thông tin về một process khác trong mạng."""
    def __init__(self, pid: int, host: str, port: int):
        self.pid  = pid
        self.host = host
        self.port = port

    def __repr__(self):
        return f"P{self.pid}@{self.host}:{self.port}"


# ─────────────────────────────────────────────
# Các trạng thái của process với CS
# ─────────────────────────────────────────────

class State:
    RELEASED = "RELEASED"   # Không muốn vào CS
    WANTED   = "WANTED"     # Đang xin vào CS (chờ đủ REPLY/GRANT)
    HELD     = "HELD"       # Đang trong CS


# ─────────────────────────────────────────────
# Lớp cơ sở
# ─────────────────────────────────────────────

class BaseProcess(ABC):
    """
    Lớp cơ sở cho tất cả các process trong hệ thống phân tán.

    Cung cấp sẵn:
      - Server socket: lắng nghe kết nối đến (thread riêng)
      - Lamport clock: tick() / tick_recv()
      - Gửi message: send_one() / broadcast()
      - Log đẹp:     log()
      - Thống kê:    msg_sent, msg_recv (dùng cho benchmark)
    """

    def __init__(self,
                 pid    : int,
                 host   : str,
                 port   : int,
                 peers  : List[PeerInfo]):
        """
        Args:
            pid  : ID duy nhất của process này (0-based)
            host : địa chỉ lắng nghe (thường "127.0.0.1")
            port : cổng lắng nghe
            peers: danh sách tất cả process KHÁC trong mạng
        """
        self.pid    = pid
        self.host   = host
        self.port   = port
        self.peers  = peers          # List[PeerInfo]

        # Lamport logical clock
        self._clock      = 0
        self._clock_lock = threading.Lock()

        # Trạng thái với CS
        self.state       = State.RELEASED
        self.state_lock  = threading.Lock()

        # Event báo hiệu được vào CS (set bởi _handle_message)
        self.cs_event    = threading.Event()

        # Thống kê (dùng cho benchmark so sánh thuật toán)
        self.msg_sent = 0
        self.msg_recv = 0
        self._stat_lock = threading.Lock()

        # Log riêng cho mỗi process
        self.logger = logging.getLogger(f"P{pid}")

        # Server socket + flag dừng
        self._server_sock : Optional[socket.socket] = None
        self._running      = False

    # ─── Lamport Clock ───────────────────────

    @property
    def clock(self) -> int:
        with self._clock_lock:
            return self._clock

    def tick(self) -> int:
        """Tăng clock khi gửi event nội bộ. Trả về giá trị mới."""
        with self._clock_lock:
            self._clock += 1
            return self._clock

    def tick_recv(self, received_ts: int) -> int:
        """
        Cập nhật clock khi nhận message.
        Quy tắc Lamport: clock = max(local, received) + 1
        """
        with self._clock_lock:
            self._clock = max(self._clock, received_ts) + 1
            return self._clock

    # ─── Gửi message ─────────────────────────

    def send_one(self, peer: PeerInfo, payload: bytes,
             async_send: bool = True,
             timeout: float = 5.0) -> None:
        """
        Gửi 1 message đến 1 peer.

        Args:
            async_send: True = gửi trong thread riêng (không block)
                        False = gửi đồng bộ (block đến khi xong)
            timeout   : giây chờ kết nối — hết timeout = coi peer bị crash
        """
        if async_send:
            send_to_async(peer.host, peer.port, payload,
                        timeout=timeout,
                        on_fail=self._on_peer_failure(peer))
        else:
            try:
                send_to(peer.host, peer.port, payload, timeout=timeout)
            except ConnectionError:
                self._on_peer_failure(peer)()

        with self._stat_lock:
            self.msg_sent += 1

    def _on_peer_failure(self, peer: PeerInfo):
        """
        Trả về callback được gọi khi không liên lạc được peer.
        Tách thành hàm riêng để subclass có thể override nếu muốn
        xử lý crash theo cách riêng của từng thuật toán.
        """
        def _callback():
            self.log(
                f"CẢNH BÁO: Không liên lạc được P{peer.pid} "
                f"({peer.host}:{peer.port}) — peer có thể đã crash.\n"
                f"  Trong R-A gốc: không có cơ chế xử lý → "
                f"các process đang WANTED sẽ chờ mãi (blocked).\n"
                f"  Mở rộng thực tế: cần failure detector (Zookeeper/etcd) "
                f"để loại peer này khỏi tập N.",
                level="warning"
            )
            # Đánh dấu peer này là suspected crash
            # để RAProcess có thể tự xử lý nếu muốn
            self._mark_suspected(peer.pid)

        return _callback

    def _mark_suspected(self, pid: int) -> None:
        """
        Ghi nhận pid bị nghi là crash.
        Mặc định chỉ log — RAProcess override để xử lý thêm.
        """
        if not hasattr(self, '_suspected'):
            self._suspected = set()
        self._suspected.add(pid)
        self.log(f"P{pid} được đánh dấu suspected-crash", level="warning")
                

    def broadcast(self, payload: bytes,
                  exclude_pid: Optional[int] = None) -> None:
        """
        Gửi cùng 1 message đến TẤT CẢ peer (song song).

        Args:
            exclude_pid: bỏ qua peer có pid này (nếu có)
        """
        targets = [p for p in self.peers
                   if p.pid != exclude_pid] if exclude_pid is not None \
                   else self.peers

        for peer in targets:
            self.send_one(peer, payload, async_send=True)

    def send_to_pid(self, target_pid: int, payload: bytes,
                    async_send: bool = True) -> None:
        """Gửi message đến peer theo pid."""
        peer = self._get_peer(target_pid)
        if peer is None:
            self.logger.warning("Không tìm thấy peer pid=%d", target_pid)
            return
        self.send_one(peer, payload, async_send)

    def _get_peer(self, pid: int) -> Optional[PeerInfo]:
        for p in self.peers:
            if p.pid == pid:
                return p
        return None

    # ─── Server: lắng nghe kết nối đến ──────

    def start(self) -> None:
        """Khởi động server socket và bắt đầu lắng nghe."""
        self._running     = True
        self._server_sock = make_server_socket(self.host, self.port)
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        self.log(f"Đã khởi động tại {self.host}:{self.port}")
        self.on_start()   # hook để subclass làm thêm việc khi start

    def stop(self) -> None:
        """Dừng server socket."""
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
        self.log("Đã dừng.")

    def _accept_loop(self) -> None:
        """Thread chính chấp nhận kết nối mới."""
        while self._running:
            try:
                conn, addr = self._server_sock.accept()
            except OSError:
                break   # socket đã đóng
            # Mỗi kết nối được xử lý trong thread riêng
            t = threading.Thread(
                target=self._recv_and_handle,
                args=(conn,),
                daemon=True
            )
            t.start()

    def _recv_and_handle(self, conn: socket.socket) -> None:
        """Nhận 1 message rồi gọi _handle_message."""
        try:
            with conn:
                data = recv_msg(conn)
                msg  = parse_msg(data)
                self.tick_recv(msg["timestamp"])
                with self._stat_lock:
                    self.msg_recv += 1
                self.logger.debug("Nhận: %s", fmt_msg(msg))
                self._handle_message(msg, conn)
        except (ConnectionError, ValueError) as e:
            self.logger.warning("Lỗi xử lý kết nối: %s", e)

    # ─── Hooks để subclass override ──────────

    @abstractmethod
    def _handle_message(self, msg: dict, conn: socket.socket) -> None:
        """
        Xử lý 1 message đã nhận được.
        Subclass PHẢI override hàm này.

        Args:
            msg : dict đã parse từ JSON
            conn: socket kết nối (đã đóng sau khi hàm return)
        """

    @abstractmethod
    def request_cs(self) -> None:
        """
        Yêu cầu vào Critical Section.
        Hàm này BLOCK cho đến khi process được vào CS.
        Subclass PHẢI override.
        """

    @abstractmethod
    def release_cs(self) -> None:
        """
        Ra khỏi Critical Section và thông báo cho các process khác.
        Subclass PHẢI override.
        """

    def on_start(self) -> None:
        """
        Hook gọi sau khi start(). Subclass override nếu cần
        làm thêm việc khi khởi động (ví dụ: gửi token ban đầu).
        Mặc định: không làm gì.
        """

    # ─── Mô phỏng làm việc trong CS ─────────

    def do_critical_section(self, duration: float = 0.5) -> None:
        """
        Mô phỏng công việc bên trong Critical Section.
        Thực tế có thể thay bằng đọc/ghi file, cập nhật DB, v.v.
        """
        self.log(f">>> Đang trong CS (sleep {duration}s)")
        time.sleep(duration)
        self.log(f"<<< Hoàn thành CS")

    # ─── Thống kê (dùng cho benchmark) ───────

    def get_stats(self) -> dict:
        """Trả về thống kê của process để so sánh thuật toán."""
        with self._stat_lock:
            return {
                "pid"     : self.pid,
                "msg_sent": self.msg_sent,
                "msg_recv": self.msg_recv,
                "msg_total": self.msg_sent + self.msg_recv,
            }

    # ─── Logging ─────────────────────────────

    def log(self, msg: str, level: str = "info") -> None:
        """In log kèm pid và Lamport clock hiện tại."""
        full = f"[ts={self.clock:3d}] {msg}"
        getattr(self.logger, level)(full)

    # ─── Biểu diễn ───────────────────────────

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"pid={self.pid} state={self.state} "
                f"clock={self.clock}>")


# ─────────────────────────────────────────────
# Ví dụ Process đơn giản để test
# ─────────────────────────────────────────────

class EchoProcess(BaseProcess):
    """
    Process đơn giản chỉ echo lại mọi message nhận được.
    Dùng để kiểm tra BaseProcess hoạt động đúng.
    """

    def _handle_message(self, msg: dict, conn: socket.socket) -> None:
        self.log(f"Echo: {fmt_msg(msg)}")

    def request_cs(self) -> None:
        self.log("EchoProcess không dùng CS")

    def release_cs(self) -> None:
        self.log("EchoProcess không dùng CS")


# ─────────────────────────────────────────────
# Test khi chạy trực tiếp
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import time
    from message import msg_request

    print("=== Test base_process.py ===\n")

    # Tạo 2 EchoProcess và để chúng gửi message cho nhau
    peer_b = PeerInfo(pid=1, host="127.0.0.1", port=20001)
    peer_a = PeerInfo(pid=0, host="127.0.0.1", port=20000)

    proc_a = EchoProcess(pid=0, host="127.0.0.1", port=20000, peers=[peer_b])
    proc_b = EchoProcess(pid=1, host="127.0.0.1", port=20001, peers=[peer_a])

    proc_a.start()
    proc_b.start()
    time.sleep(0.3)   # đợi server socket sẵn sàng

    # A gửi REQUEST đến B
    ts = proc_a.tick()
    proc_a.send_one(peer_b, msg_request(sender_id=0, timestamp=ts))
    print(f"  P0 gửi REQUEST đến P1 @ ts={ts}")

    # B gửi REQUEST đến A
    ts = proc_b.tick()
    proc_b.send_one(peer_a, msg_request(sender_id=1, timestamp=ts))
    print(f"  P1 gửi REQUEST đến P0 @ ts={ts}")

    time.sleep(0.5)

    stats_a = proc_a.get_stats()
    stats_b = proc_b.get_stats()
    print(f"\n  P0 stats: {stats_a}")
    print(f"  P1 stats: {stats_b}")

    assert stats_a["msg_sent"] == 1 and stats_a["msg_recv"] == 1
    assert stats_b["msg_sent"] == 1 and stats_b["msg_recv"] == 1

    proc_a.stop()
    proc_b.stop()
    print("\nTất cả test passed ✓")