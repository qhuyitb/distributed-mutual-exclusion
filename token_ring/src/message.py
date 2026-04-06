import json
import time
from enum import Enum
from typing import Any, Dict, Optional


class MessageType(str, Enum):
    TOKEN = "TOKEN"
    DATA = "DATA"
    REQUEST = "REQUEST"
    REPLY = "REPLY"
    HEARTBEAT = "HEARTBEAT"


class Message:
    """Represents a message passed between nodes in the token ring.

    Fields
    - msg_type: one of MessageType
    - sender_id: int
    - receiver_id: int or None (None means broadcast/next-hop)
    - sequence_num: optional int for ordering
    - timestamp: wall-clock epoch seconds (float)
    - data: optional payload (JSON-serializable)
    - lamport: optional Lamport timestamp (int)
    """

    def __init__(
        self,
        msg_type: str,
        sender_id: int,
        receiver_id: Optional[int] = None,
        sequence_num: Optional[int] = None,
        timestamp: Optional[float] = None,
        data: Any = None,
        lamport: Optional[int] = None,
    ):
        self.msg_type = str(msg_type)
        self.sender_id = int(sender_id)
        self.receiver_id = None if receiver_id is None else int(receiver_id)
        self.sequence_num = sequence_num
        self.timestamp = float(timestamp) if timestamp is not None else time.time()
        self.data = data
        self.lamport = lamport

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_type": self.msg_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp,
            "data": self.data,
            "lamport": self.lamport,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        return cls(
            d.get("msg_type"),
            d.get("sender_id"),
            d.get("receiver_id"),
            d.get("sequence_num"),
            d.get("timestamp"),
            d.get("data"),
            d.get("lamport"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        d = json.loads(json_str)
        return cls.from_dict(d)

    def to_bytes(self, newline: bool = True) -> bytes:
        s = self.to_json()
        if newline:
            s += "\n"
        return s.encode("utf-8")

    @classmethod
    def from_bytes(cls, b: bytes) -> "Message":
        s = b.decode("utf-8")
        s = s.rstrip("\r\n")
        return cls.from_json(s)

    # convenience factories
    @classmethod
    def token(cls, sender_id: int, token_id: Optional[int] = None, lamport: Optional[int] = None) -> "Message":
        return cls(MessageType.TOKEN.value, sender_id, None, token_id, time.time(), data=None, lamport=lamport)

    @classmethod
    def data_msg(cls, sender_id: int, receiver_id: int, body: Any, sequence_num: Optional[int] = None, lamport: Optional[int] = None) -> "Message":
        return cls(MessageType.DATA.value, sender_id, receiver_id, sequence_num, time.time(), data=body, lamport=lamport)

    @classmethod
    def request(cls, sender_id: int, receiver_id: Optional[int] = None, body: Any = None, lamport: Optional[int] = None) -> "Message":
        return cls(MessageType.REQUEST.value, sender_id, receiver_id, None, time.time(), data=body, lamport=lamport)

    @classmethod
    def reply(cls, sender_id: int, receiver_id: int, body: Any = None, lamport: Optional[int] = None) -> "Message":
        return cls(MessageType.REPLY.value, sender_id, receiver_id, None, time.time(), data=body, lamport=lamport)

    def __repr__(self) -> str:
        return f"Message({self.msg_type}, from={self.sender_id}, to={self.receiver_id}, seq={self.sequence_num}, lamport={self.lamport})"