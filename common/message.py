"""
common/message.py
-----------------
Định nghĩa cấu trúc message dùng chung cho cả 3 thuật toán:
  - Centralized Mutual Exclusion
  - Distributed (Ricart-Agrawala)
  - Token Ring

Message được serialize thành JSON bytes để truyền qua socket.
"""

import json
import time


# ─────────────────────────────────────────────
# Các loại message (type) hợp lệ
# ─────────────────────────────────────────────

class MsgType:
    # Dùng trong Centralized
    REQUEST = "REQUEST"     # Client → Coordinator: xin vào CS
    GRANT   = "GRANT"       # Coordinator → Client: cho phép vào CS
    RELEASE = "RELEASE"     # Client → Coordinator: báo ra CS

    # Dùng trong Distributed (Ricart-Agrawala)
    # REQUEST và RELEASE dùng lại ở trên
    REPLY   = "REPLY"       # Process → Process: đồng ý cho vào CS

    # Dùng trong Token Ring
    TOKEN   = "TOKEN"       # Process → Process: chuyển token

    # Dùng chung (debug / điều phối)
    ACK     = "ACK"         # Xác nhận nhận message
    DONE    = "DONE"        # Báo kết thúc (dùng khi chạy benchmark)

    ALL = {REQUEST, GRANT, RELEASE, REPLY, TOKEN, ACK, DONE}


# ─────────────────────────────────────────────
# Tạo message
# ─────────────────────────────────────────────

def make_msg(msg_type: str, sender_id: int, timestamp: int = 0, **kwargs) -> bytes:
    """
    Tạo một message dạng bytes (JSON-encoded).

    Args:
        msg_type  : Loại message (dùng hằng số MsgType)
        sender_id : ID của tiến trình gửi
        timestamp : Lamport clock tại thời điểm gửi
        **kwargs  : Các trường bổ sung tùy thuật toán

    Returns:
        bytes: JSON-encoded message

    Ví dụ:
        msg = make_msg(MsgType.REQUEST, sender_id=1, timestamp=5)
        msg = make_msg(MsgType.TOKEN,   sender_id=2, timestamp=0, has_cs_request=True)
    """
    if msg_type not in MsgType.ALL:
        raise ValueError(f"Loại message không hợp lệ: '{msg_type}'. "
                         f"Chọn trong: {MsgType.ALL}")

    payload = {
        "type"      : msg_type,
        "sender"    : sender_id,
        "timestamp" : timestamp,
        "sent_at"   : time.time(),   # wall-clock để đo latency trong benchmark
        **kwargs
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


# ─────────────────────────────────────────────
# Phân tích message
# ─────────────────────────────────────────────

def parse_msg(data: bytes) -> dict:
    """
    Giải mã bytes nhận được từ socket thành dict.

    Args:
        data: bytes nhận từ socket

    Returns:
        dict với ít nhất các key: type, sender, timestamp, sent_at

    Raises:
        ValueError: nếu data không phải JSON hợp lệ hoặc thiếu field bắt buộc
    """
    try:
        msg = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Không thể parse message: {e}\nRaw data: {data!r}")

    # Kiểm tra các field bắt buộc
    required = {"type", "sender", "timestamp"}
    missing = required - msg.keys()
    if missing:
        raise ValueError(f"Message thiếu các field: {missing}\nNhận được: {msg}")

    return msg


# ─────────────────────────────────────────────
# Các hàm helper tạo message nhanh
# ─────────────────────────────────────────────

def msg_request(sender_id: int, timestamp: int) -> bytes:
    """REQUEST: xin vào Critical Section."""
    return make_msg(MsgType.REQUEST, sender_id, timestamp)

def msg_reply(sender_id: int, timestamp: int) -> bytes:
    """REPLY: đồng ý cho process khác vào CS (Ricart-Agrawala)."""
    return make_msg(MsgType.REPLY, sender_id, timestamp)

def msg_grant(sender_id: int, timestamp: int, to_pid: int) -> bytes:
    """GRANT: Coordinator cấp phép vào CS (Centralized)."""
    return make_msg(MsgType.GRANT, sender_id, timestamp, granted_to=to_pid)

def msg_release(sender_id: int, timestamp: int) -> bytes:
    """RELEASE: thông báo ra khỏi CS."""
    return make_msg(MsgType.RELEASE, sender_id, timestamp)

def msg_token(sender_id: int, timestamp: int, want_cs: bool = False) -> bytes:
    """TOKEN: chuyển token trong Token Ring."""
    return make_msg(MsgType.TOKEN, sender_id, timestamp, want_cs=want_cs)

def msg_done(sender_id: int) -> bytes:
    """DONE: báo hiệu process kết thúc (dùng cho benchmark)."""
    return make_msg(MsgType.DONE, sender_id, timestamp=0)


# ─────────────────────────────────────────────
# In log message (dùng khi debug)
# ─────────────────────────────────────────────

def fmt_msg(msg: dict) -> str:
    """Trả về chuỗi mô tả ngắn gọn của message để in log."""
    mtype   = msg.get("type", "?")
    sender  = msg.get("sender", "?")
    ts      = msg.get("timestamp", "?")
    extras  = {k: v for k, v in msg.items()
               if k not in {"type", "sender", "timestamp", "sent_at"}}
    extra_str = f" | {extras}" if extras else ""
    return f"[{mtype}] from P{sender} @ ts={ts}{extra_str}"


# ─────────────────────────────────────────────
# Test nhanh khi chạy trực tiếp
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Test message.py ===\n")

    # Tạo và parse các loại message
    cases = [
        msg_request(sender_id=1, timestamp=3),
        msg_reply(sender_id=2, timestamp=5),
        msg_grant(sender_id=0, timestamp=1, to_pid=2),
        msg_release(sender_id=1, timestamp=8),
        msg_token(sender_id=3, timestamp=0, want_cs=True),
        msg_done(sender_id=4),
    ]

    for raw in cases:
        parsed = parse_msg(raw)
        print(f"  encode → decode OK: {fmt_msg(parsed)}")

    # Kiểm tra lỗi type không hợp lệ
    try:
        make_msg("INVALID_TYPE", sender_id=1, timestamp=0)
    except ValueError as e:
        print(f"\n  Bắt lỗi đúng: {e}")

    print("\nTất cả test passed ✓")