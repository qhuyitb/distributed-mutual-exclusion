"""
Message định nghĩa cấu trúc gói tin cho Ricart-Agrawala
Bao gồm: REQUEST, REPLY
"""
from enum import Enum
from dataclasses import dataclass, asdict
import json


class MessageType(Enum):
    """Loại gói tin trong Ricart-Agrawala"""
    REQUEST = "REQUEST"
    REPLY = "REPLY"


@dataclass
class Message:
    """
    Cấu trúc gói tin cho Ricart-Agrawala

    Attributes:
        msg_type: Loại gói tin (REQUEST hoặc REPLY)
        sender_id: ID của node gửi
        receiver_id: ID của node nhận
        timestamp: Logical clock timestamp
        sequence_num: Số thứ tự gói tin
    """
    msg_type: str
    sender_id: int
    receiver_id: int
    timestamp: int
    sequence_num: int

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(json_str: str) -> 'Message':
        return Message(**json.loads(json_str))

    def __str__(self) -> str:
        return (f"Message(type={self.msg_type}, from={self.sender_id}, "
                f"to={self.receiver_id}, ts={self.timestamp})")


def create_request_message(sender_id: int, receiver_id: int,
                           timestamp: int, seq_num: int) -> Message:
    """Tạo gói tin REQUEST"""
    return Message(
        msg_type=MessageType.REQUEST.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        timestamp=timestamp,
        sequence_num=seq_num,
    )


def create_reply_message(sender_id: int, receiver_id: int,
                         timestamp: int, seq_num: int) -> Message:
    """Tạo gói tin REPLY"""
    return Message(
        msg_type=MessageType.REPLY.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        timestamp=timestamp,
        sequence_num=seq_num,
    )