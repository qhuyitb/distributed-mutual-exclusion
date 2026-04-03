"""
Message định nghĩa cấu trúc gói tin cho Token Ring
Bao gồm: Request, Reply, Token
"""
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Any, Optional
import json
import time


class MessageType(Enum):
    """Loại gói tin trong Token Ring"""
    TOKEN = "TOKEN"           # Gói token di chuyển trong vòng
    REQUEST = "REQUEST"       # Yêu cầu từ node gửi tới node khác
    REPLY = "REPLY"           # Phản hồi từ node nhận tới node gửi
    DATA = "DATA"             # Dữ liệu thông thường
    ACK = "ACK"               # Xác nhận nhận được dữ liệu


@dataclass
class Message:
    """
    Cấu trúc gói tin chung
    
    Attributes:
        msg_type: Loại gói tin (TOKEN, REQUEST, REPLY, DATA, ACK)
        sender_id: ID của node gửi
        receiver_id: ID của node nhận (None nếu là TOKEN)
        sequence_num: Số thứ tự gói tin
        timestamp: Thời gian gửi
        data: Dữ liệu payload
        token_holder: ID của node đang giữ token (chỉ dùng cho TOKEN)
        visited_nodes: Danh sách các node đã đi qua (chỉ dùng cho TOKEN)
    """
    msg_type: str
    sender_id: int
    receiver_id: Optional[int]
    sequence_num: int
    timestamp: float
    data: Any = None
    token_holder: Optional[int] = None  # Chỉ dùng cho TOKEN
    visited_nodes: Optional[list] = None  # Chỉ dùng cho TOKEN

    def to_json(self) -> str:
        """Chuyển gói tin thành JSON"""
        data_dict = asdict(self)
        data_dict['timestamp'] = self.timestamp
        return json.dumps(data_dict, default=str)

    @staticmethod
    def from_json(json_str: str) -> 'Message':
        """Tạo gói tin từ JSON"""
        data = json.loads(json_str)
        return Message(**data)

    def __str__(self) -> str:
        return f"Message(type={self.msg_type}, from={self.sender_id}, to={self.receiver_id}, seq={self.sequence_num})"


class Token:
    """
    Lớp Token đặc biệt cho Token Ring
    Token di chuyển xung quanh vòng để cho phép các node gửi dữ liệu
    """
    def __init__(self, token_id: int, initial_holder: int):
        """
        Tạo token mới
        
        Args:
            token_id: ID của token
            initial_holder: ID node đầu tiên giữ token
        """
        self.token_id = token_id
        self.current_holder = initial_holder
        self.creation_time = time.time()
        self.visited_nodes = [initial_holder]
        self.free = True  # True nếu token rỗi (không mang dữ liệu)

    def to_message(self) -> Message:
        """Chuyển token thành gói tin MESSAGE để gửi"""
        msg = Message(
            msg_type=MessageType.TOKEN.value,
            sender_id=self.current_holder,
            receiver_id=None,
            sequence_num=0,
            timestamp=time.time(),
            data={
                'token_id': self.token_id,
                'free': self.free,
                'creation_time': self.creation_time
            },
            token_holder=self.current_holder,
            visited_nodes=self.visited_nodes
        )
        return msg

    def __str__(self) -> str:
        return f"Token(id={self.token_id}, holder={self.current_holder}, free={self.free})"


# Các hàm tiện ích để tạo gói tin

def create_token_message(sender_id: int, token_id: int, free: bool, 
                         visited_nodes: list) -> Message:
    """Tạo gói tin TOKEN"""
    return Message(
        msg_type=MessageType.TOKEN.value,
        sender_id=sender_id,
        receiver_id=None,
        sequence_num=0,
        timestamp=time.time(),
        data={'token_id': token_id, 'free': free},
        token_holder=sender_id,
        visited_nodes=visited_nodes
    )


def create_request_message(sender_id: int, receiver_id: int, seq_num: int, 
                          data: Any) -> Message:
    """Tạo gói tin REQUEST"""
    return Message(
        msg_type=MessageType.REQUEST.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        sequence_num=seq_num,
        timestamp=time.time(),
        data=data
    )


def create_reply_message(sender_id: int, receiver_id: int, seq_num: int, 
                        data: Any) -> Message:
    """Tạo gói tin REPLY"""
    return Message(
        msg_type=MessageType.REPLY.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        sequence_num=seq_num,
        timestamp=time.time(),
        data=data
    )


def create_data_message(sender_id: int, receiver_id: int, seq_num: int, 
                       data: Any) -> Message:
    """Tạo gói tin DATA"""
    return Message(
        msg_type=MessageType.DATA.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        sequence_num=seq_num,
        timestamp=time.time(),
        data=data
    )


def create_ack_message(sender_id: int, receiver_id: int, seq_num: int) -> Message:
    """Tạo gói tin ACK"""
    return Message(
        msg_type=MessageType.ACK.value,
        sender_id=sender_id,
        receiver_id=receiver_id,
        sequence_num=seq_num,
        timestamp=time.time()
    )
