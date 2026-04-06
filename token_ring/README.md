# Token Ring Implementation - Vòng Logic Token

## Giới thiệu
Đây là một triển khai hoàn chỉnh của **Thuật toán Token Ring** bằng Python sử dụng localhost như các node.

### Tính năng chính:
1. **Thiết kế Vòng Logic**: Các node được sắp xếp thành một vòng tròn, token di chuyển tuần tự từ node này sang node khác
2. **Truyền/Nhận Token**: Token được truyền từ node hiện tại tới node tiếp theo trong vòng
3. **Giao tiếp Node**: Các node có thể gửi/nhận dữ liệu khi sở hữu token
4. **Cấu trúc Gói Tin Chung**: Định nghĩa các loại gói tin (Request, Reply, Token, Data, ACK)

## Cấu trúc Dự Án

```
token_ring/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── message.py               # Định nghĩa cấu trúc gói tin
│   ├── node.py                  # Lớp Node trong vòng
│   ├── ring_manager.py          # Quản lý vòng Token Ring
│   └── demo.py                  # Ứng dụng demo
└── README.md                    # Tài liệu này
```

## Các Thành Phần Chính

### 1. Message (message.py)
Định nghĩa cấu trúc gói tin chung cho tất cả các node:

```python
class MessageType(Enum):
    TOKEN = "TOKEN"         # Gói token
    REQUEST = "REQUEST"     # Yêu cầu
    REPLY = "REPLY"        # Phản hồi
    DATA = "DATA"          # Dữ liệu
    ACK = "ACK"            # Xác nhận
```

**Cấu trúc Message:**
- `msg_type`: Loại gói tin
- `sender_id`: ID node gửi
- `receiver_id`: ID node nhận
- `sequence_num`: Số thứ tự
- `timestamp`: Thời gian gửi
- `data`: Dữ liệu payload
- `token_holder`: Node giữ token (cho TOKEN)
- `visited_nodes`: Danh sách node đã đi qua

### 2. Node (node.py)
Lớp đại diện cho một node trong vòng:

**Chức năng:**
- Lắng nghe gói tin đến
- Xử lý token (tiếp nhận, xử lý, truyền tiếp)
- Gửi/nhận tin nhắn
- Quản lý bộ đệm và xác nhận

**Port mặc định:**
- Node 0: 5000
- Node 1: 5001
- Node 2: 5002
- ...

### 3. TokenRingManager (ring_manager.py)
Quản lý toàn bộ vòng:

**Chức năng:**
- Tạo vòng logic (cấu hình liên kết các node)
- Khởi động/dừng vòng
- Khởi tạo và gửi token
- Điều phối giao tiếp
- Thống kê và giám sát

### 4. Demo (demo.py)
Các kịch bản demo:

1. **Demo 1**: Khởi động vòng cơ bản - quan sát token di chuyển
2. **Demo 2**: Gửi tin nhắn giữa các node
3. **Demo 3**: Token di chuyển xung quanh vòng (6 node)
4. **Demo 4**: Gửi nhiều tin nhắn liên tiếp

## Cách Chạy

### Yêu cầu
```bash
python >= 3.6
```

### Chạy Demo
```bash
# Chuyển tới thư mục src
cd token_ring/src

# Chạy demo
python demo.py

# Chạy demo cụ thể
python demo.py 1    # Demo cơ bản
python demo.py 2    # Demo gửi tin nhắn
python demo.py 3    # Demo token di chuyển
python demo.py 4    # Demo nhiều tin nhắn
python demo.py 5    # Chạy tất cả
```

## Luồng Hoạt Động

### 1. Khởi Tạo Vòng
```
TokenRingManager.create_ring()
  ↓
Tạo 4 node: 0→1→2→3→0 (vòng kín)
Mỗi node biết node kế tiếp của nó
```

### 2. Khởi Động Vòng
```
TokenRingManager.start_ring()
  ↓
Mỗi node khởi động luồng lắng nghe và xử lý
  ↓
Token được tạo và gửi tới Node 0
```

### 3. Token Di Chuyển
```
Node 0 nhận token
  ↓
Xử lý (nếu có dữ liệu cần gửi)
  ↓
Chuyển token tới Node 1
  ↓
Node 1 nhận token
  ↓
... (lặp lại)
```

### 4. Gửi/Nhận Dữ Liệu
```
Node A (có token) muốn gửi dữ liệu tới Node B
  ↓
Tạo gói tin MESSAGE
  ↓
Gửi tới Node B
  ↓
Node B nhận và gửi ACK
  ↓
Node A chuyển token tới node kế tiếp
```

## Ví Dụ Sử Dụng

### Tạo và Chạy Vòng
```python
from ring_manager import TokenRingManager
from message import MessageType

# Tạo vòng với 4 node
manager = TokenRingManager(num_nodes=4, base_port=5000)

# Tạo vòng
manager.create_ring()

# Khởi động
manager.start_ring()

# Chờ một lúc
import time
time.sleep(5)

# In thống kê
manager.print_stats()

# Dừng vòng
manager.stop_ring()
```

### Gửi Tin Nhắn
```python
# Gửi unicast từ Node 0 tới Node 2
manager.unicast_message(
    sender_id=0,
    receiver_id=2,
    message_type=MessageType.REQUEST.value,
    data={'action': 'query', 'params': 'hello'}
)
```

## Output Ví Dụ

```
2026-04-01 10:30:45,123 - RingManager - INFO - Tạo vòng Token Ring với 4 node
2026-04-01 10:30:45,125 - RingManager - INFO - Tạo Node 0 trên port 5000 -> Node 1 trên port 5001
2026-04-01 10:30:45,126 - RingManager - INFO - Tạo Node 1 trên port 5001 -> Node 2 trên port 5002
2026-04-01 10:30:45,127 - RingManager - INFO - Tạo Node 2 trên port 5002 -> Node 3 trên port 5003
2026-04-01 10:30:45,128 - RingManager - INFO - Tạo Node 3 trên port 5003 -> Node 0 trên port 5000
2026-04-01 10:30:45,128 - RingManager - INFO - Vòng Token Ring đã được tạo thành công
2026-04-01 10:30:45,130 - RingManager - INFO - Khởi động vòng Token Ring...
2026-04-01 10:30:45,131 - Node 0 - INFO - Node 0 khởi động trên port 5000
2026-04-01 10:30:48,135 - Node 0 - INFO - Nhận được TOKEN (id=1)
2026-04-01 10:30:48,640 - Node 0 - INFO - Chuyển TOKEN tới node kế tiếp
2026-04-01 10:30:49,145 - Node 1 - INFO - Nhận được TOKEN (id=1)
2026-04-01 10:30:49,650 - Node 1 - INFO - Chuyển TOKEN tới node kế tiếp
```

## Ghi Chú

- Token được tạo và khởi tạo bởi TokenRingManager
- Các node sử dụng socket TCP để giao tiếp
- Vòng là lý thuyết (logic), không yêu cầu kết nối vật lý vòng
- Có thể dễ dàng mở rộng để thêm số lượng node hơn
- Logging chi tiết để dễ debug

## Phát Triển Tiếp Theo

1. **Phát Hiện Node Chết**: Thêm heartbeat để phát hiện node offline
2. **Phục Hồi Token**: Tái sinh token nếu bị mất
3. **Ưu Tiên Tin Nhắn**: Thêm hàng đợi ưu tiên
4. **Mã Hóa**: Mã hóa dữ liệu giữa các node
5. **Persistent Storage**: Lưu trữ tin nhắn ra đĩa
6. **Web Interface**: Thêm giao diện web để giám sát
