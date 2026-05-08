import json

class Message:
    """Message(
    msg_type,       # loại tin (REQUEST, REPLY, TOKEN...)
    sender_id,      # bên gửi
    receiver_id,    # bên nhận
    sequence_num,   # số thứ tự
    timestamp,      # thời gian
    data,           # payload
    )"""

    def __init__(self, msg_type, sender_id, receiver_id, sequence_num, timestamp, data=None):
        self.msg_type = msg_type
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sequence_num = sequence_num
        self.timestamp = timestamp
        self.data = data

    def to_dict(self):
        return {
            "msg_type": self.msg_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "sequence_num": self.sequence_num,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    @staticmethod
    def from_dict(d):
        return Message(
            d.get("msg_type"),
            d.get("sender_id"),
            d.get("receiver_id"),
            d.get("sequence_num"),
            d.get("timestamp"),
            d.get("data"),
        )

    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_str):
        d = json.loads(json_str)
        return Message.from_dict(d)
