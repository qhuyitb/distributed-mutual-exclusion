"""
common/network.py
-----------------
Lớp network dùng chung cho cả 3 thuật toán.

Vấn đề với raw TCP socket:
  TCP là giao thức stream, không có ranh giới message tự nhiên.
  Nếu gửi 2 message liên tiếp, recv() có thể trả về cả 2 gộp lại
  (TCP nagling) hoặc trả về 1 nửa (buffer đầy).

Giải pháp: Length-prefix framing
  Mỗi message được đóng gói như sau:
  ┌──────────────┬─────────────────────┐
  │  4 bytes     │  N bytes            │
  │  độ dài (N)  │  JSON payload       │
  └──────────────┴─────────────────────┘
  Người nhận đọc 4 bytes đầu → biết cần đọc thêm bao nhiêu bytes.
"""

import socket
import struct
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Header = 4 bytes unsigned int big-endian, lưu độ dài payload
HEADER_FORMAT = ">I"          # big-endian unsigned 32-bit int
HEADER_SIZE   = struct.calcsize(HEADER_FORMAT)   # = 4 bytes
MAX_MSG_SIZE  = 64 * 1024     # 64 KB — đủ dùng cho bài toán này


# ─────────────────────────────────────────────
# Gửi và nhận (blocking)
# ─────────────────────────────────────────────

def send_msg(sock: socket.socket, payload: bytes) -> None:
    """
    Gửi 1 message qua socket với length-prefix framing.

    Args:
        sock   : socket đã connect
        payload: bytes cần gửi (output của message.make_msg)

    Raises:
        ValueError       : nếu payload vượt MAX_MSG_SIZE
        ConnectionError  : nếu socket đã đóng giữa chừng
    """
    if len(payload) > MAX_MSG_SIZE:
        raise ValueError(
            f"Message quá lớn: {len(payload)} bytes (max {MAX_MSG_SIZE})"
        )

    header = struct.pack(HEADER_FORMAT, len(payload))
    try:
        sock.sendall(header + payload)
        logger.debug("Đã gửi %d bytes (payload %d bytes)", HEADER_SIZE + len(payload), len(payload))
    except OSError as e:
        raise ConnectionError(f"Lỗi khi gửi dữ liệu: {e}") from e


def recv_msg(sock: socket.socket) -> bytes:
    """
    Nhận đúng 1 message từ socket (blocking).

    Returns:
        bytes: payload nguyên vẹn (chưa parse)

    Raises:
        ConnectionError: nếu socket đóng trước khi nhận đủ dữ liệu
    """
    # Bước 1: Đọc đúng 4 bytes header
    header = _recv_exact(sock, HEADER_SIZE)
    msg_len = struct.unpack(HEADER_FORMAT, header)[0]

    if msg_len == 0:
        raise ConnectionError("Nhận được message rỗng (length = 0)")
    if msg_len > MAX_MSG_SIZE:
        raise ConnectionError(
            f"Message header báo độ dài bất thường: {msg_len} bytes"
        )

    # Bước 2: Đọc đúng msg_len bytes payload
    payload = _recv_exact(sock, msg_len)
    logger.debug("Đã nhận %d bytes payload", msg_len)
    return payload


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """
    Đọc đúng n bytes từ socket, gọi recv() nhiều lần nếu cần.

    Raises:
        ConnectionError: nếu socket đóng trước khi đủ n bytes
    """
    buf = bytearray()
    while len(buf) < n:
        remaining = n - len(buf)
        try:
            chunk = sock.recv(remaining)
        except OSError as e:
            raise ConnectionError(f"Socket lỗi khi đọc: {e}") from e

        if not chunk:
            raise ConnectionError(
                f"Socket đóng giữa chừng: cần {n} bytes, "
                f"mới đọc được {len(buf)} bytes"
            )
        buf.extend(chunk)
    return bytes(buf)


# ─────────────────────────────────────────────
# Gửi không đồng bộ (mở socket mới mỗi lần)
# ─────────────────────────────────────────────

def send_to(host: str, port: int, payload: bytes,
            timeout: float = 5.0) -> None:
    """
    Mở kết nối TCP mới, gửi 1 message rồi đóng.
    Phù hợp cho kiểu giao tiếp "fire and forget" trong các thuật toán
    phân tán (mỗi lần gửi REQUEST/REPLY là 1 kết nối ngắn).

    Args:
        host   : địa chỉ đích
        port   : cổng đích
        payload: bytes cần gửi
        timeout: timeout kết nối (giây)

    Raises:
        ConnectionError: nếu không kết nối được hoặc lỗi khi gửi
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            send_msg(s, payload)
    except (OSError, TimeoutError) as e:
        raise ConnectionError(
            f"Không thể gửi đến {host}:{port} — {e}"
        ) from e


def send_to_async(host: str, port: int, payload: bytes,
                  timeout: float = 5.0,
                  on_fail=None) -> None:
    """
    Gửi message trong thread riêng.
    on_fail: callable, gọi khi không kết nối được.
    """
    def _run():
        try:
            send_to(host, port, payload, timeout)
        except ConnectionError as e:
            logger.warning("Gửi đến %s:%d thất bại: %s", host, port, e)
            if on_fail:
                on_fail()   # ← gọi callback báo lỗi

    threading.Thread(target=_run, daemon=True).start()


def _send_safe(host: str, port: int, payload: bytes, timeout: float) -> None:
    """Wrapper bắt lỗi khi gửi trong thread."""
    try:
        send_to(host, port, payload, timeout)
    except ConnectionError as e:
        logger.warning("Gửi đến %s:%d thất bại: %s", host, port, e)


# ─────────────────────────────────────────────
# Server socket helper
# ─────────────────────────────────────────────

def make_server_socket(host: str, port: int,
                       backlog: int = 10) -> socket.socket:
    """
    Tạo và bind server socket. Dùng SO_REUSEADDR để tránh lỗi
    "Address already in use" khi restart process nhanh.

    Returns:
        socket đã bind và listen, sẵn sàng để accept()
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(backlog)
    logger.info("Server socket lắng nghe tại %s:%d", host, port)
    return s


# ─────────────────────────────────────────────
# Test khi chạy trực tiếp
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import time
    from message import make_msg, parse_msg, fmt_msg, MsgType

    TEST_HOST = "127.0.0.1"
    TEST_PORT = 19000
    received  = []

    def server():
        srv = make_server_socket(TEST_HOST, TEST_PORT)
        conn, addr = srv.accept()
        with conn:
            for _ in range(3):
                data = recv_msg(conn)
                msg  = parse_msg(data)
                received.append(msg)
                print(f"  Server nhận: {fmt_msg(msg)}")
        srv.close()

    print("=== Test network.py ===\n")

    t = threading.Thread(target=server, daemon=True)
    t.start()
    time.sleep(0.2)

    # Gửi 3 message liên tiếp qua cùng 1 socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TEST_HOST, TEST_PORT))
        for pid, ts, mtype in [(1, 3, MsgType.REQUEST),
                               (2, 5, MsgType.REPLY),
                               (0, 1, MsgType.GRANT)]:
            payload = make_msg(mtype, pid, ts)
            send_msg(s, payload)
            print(f"  Client gửi : [{mtype}] from P{pid} @ ts={ts}")

    t.join(timeout=3)

    assert len(received) == 3, f"Nhận {len(received)}/3 message"
    print(f"\n  Đã gửi 3, nhận đủ 3 message ✓")

    # Test send_to (mở kết nối mới mỗi lần)
    def single_server():
        srv = make_server_socket(TEST_HOST, TEST_PORT + 1)
        conn, _ = srv.accept()
        with conn:
            data = recv_msg(conn)
            print(f"  send_to nhận: {fmt_msg(parse_msg(data))}")
        srv.close()

    t2 = threading.Thread(target=single_server, daemon=True)
    t2.start()
    time.sleep(0.1)
    send_to(TEST_HOST, TEST_PORT + 1,
            make_msg(MsgType.TOKEN, sender_id=3, timestamp=7))
    t2.join(timeout=3)

    print("\nTất cả test passed ✓")