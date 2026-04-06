from dataclasses import dataclass
from enum import Enum
import json
import time
from typing import Optional
from typing import Any

"""Định nghĩa thông điệp cho thuật toán loại trừ tương hỗ tập trung.

Ba loại thông điệp cốt lõi:
- REQUEST: tiến trình xin vào vùng tới hạn.
- GRANT: bộ điều phối cấp quyền vào vùng tới hạn.
- RELEASE: tiến trình trả quyền sau khi rời vùng tới hạn.
    - data: payload tuy chon (vd: dia chi callback trong che do TCP process).
"""


class MessageType(str, Enum):
    REQUEST = "REQUEST"
    GRANT = "GRANT"
    RELEASE = "RELEASE"


@dataclass(frozen=True)
class Message:
    """Thông điệp trao đổi giữa Participant và Coordinator.

    Thuộc tính:
    - msg_type: loại thông điệp thuộc MessageType.
    - sender_id: định danh nút gửi.
    - receiver_id: định danh nút nhận.
    - timestamp: thời điểm tạo thông điệp.
    - request_id: mã yêu cầu tùy chọn để theo dõi luồng xử lý.
    """

    msg_type: MessageType
    sender_id: int
    receiver_id: int
    timestamp: float
    request_id: Optional[int] = None
    data: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "msg_type": self.msg_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "data": self.data,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    def to_bytes(self, newline: bool = True) -> bytes:
        payload = self.to_json()
        if newline:
            payload += "\n"
        return payload.encode("utf-8")

    @classmethod
    def from_dict(cls, payload: dict) -> "Message":
        return cls(
            msg_type=MessageType(payload["msg_type"]),
            sender_id=int(payload["sender_id"]),
            receiver_id=int(payload["receiver_id"]),
            timestamp=float(payload.get("timestamp", time.time())),
            request_id=payload.get("request_id"),
            data=payload.get("data"),
        )

    @classmethod
    def from_json(cls, raw: str) -> "Message":
        return cls.from_dict(json.loads(raw))

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Message":
        return cls.from_json(raw.decode("utf-8").rstrip("\r\n"))
