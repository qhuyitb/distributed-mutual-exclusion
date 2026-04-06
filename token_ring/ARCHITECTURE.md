# 🏗️ Kiến Trúc Token Ring Implementation

## Tổng Quan

Token Ring là một mô hình mạng máy tính nơi các node được sắp xếp thành một vòng logic. Một "token" (bộ dữ liệu đặc biệt) di chuyển xung quanh vòng, và chỉ node nào giữ token mới có thể truyền dữ liệu.

## 🎯 Lợi Ích

- **Công bằng**: Mỗi node có cơ hội công bằng để gửi dữ liệu
- **Không xung đột**: Không có collision vì chỉ một node gửi tại một thời điểm
- **Tiên đoán được**: Độ trễ tối đa có thể được xác định trước
- **Hiệu quả**: Không cần CD (Collision Detection) như Ethernet

## 📐 Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────┐
│         Layer: Ứng Dụng (Application)               │
│  (Demo, Example, User Code)                         │
└──────────────────────────────────────────────────────┘
                        △
                        │
┌──────────────────────────────────────────────────────┐
│     Layer: Quản Lý Vòng (Ring Manager)              │
│  - Tạo vòng                                          │
│  - Khởi động/dừng                                   │
│  - Điều phối giao tiếp                              │
└──────────────────────────────────────────────────────┘
                        △
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐     ┌────────┐     ┌────────┐
    │ Node 0 │────▶│ Node 1 │────▶│ Node 2 │
    │ Port   │     │ Port   │     │ Port   │
    │ 5000   │     │ 5001   │     │ 5002   │
    └────────┘     └────────┘     └────────┘
        ▲                               │
        │                               ▼
        └───────────────────────────────┘
        
        Vòng Kín (Logical Ring)
```

## 🔌 Layer: Message (Gói Tin)

### Cấu Trúc Message

```python
Message = {
    msg_type: str                      # Loại: TOKEN, REQUEST, REPLY, DATA, ACK
    sender_id: int                     # Node gửi
    receiver_id: Optional[int]         # Node nhận (None cho TOKEN)
    sequence_num: int                  # Số thứ tự
    timestamp: float                   # Thời gian gửi (Unix timestamp)
    data: Any                          # Payload
    token_holder: Optional[int]        # ID node giữ token (cho TOKEN)
    visited_nodes: Optional[List[int]] # Danh sách node đã đi qua
}
```

### Serialization

- **Format**: JSON
- **Encoding**: UTF-8
- **Method**: `Message.to_json()` / `Message.from_json()`

### Message Types

```
┌──────────┐
│  TOKEN   │  Di chuyển xung quanh vòng, cho phép node gửi dữ liệu
├──────────┤
│ REQUEST  │  Yêu cầu từ node này sang node khác
├──────────┤
│  REPLY   │  Phản hồi từ node nhận
├──────────┤
│  DATA    │  Dữ liệu thông thường
├──────────┤
│   ACK    │  Xác nhận nhận được dữ liệu
└──────────┘
```

## 🔌 Layer: Node (Nút Mạng)

### Cấu Trúc Node

```python
class Node:
    # Thông tin cơ bản
    node_id: int                    # ID duy nhất
    port: int                       # Port lắng nghe
    next_node_host: str             # Host node kế tiếp
    next_node_port: int             # Port node kế tiếp
    
    # Trạng thái Token
    has_token: bool                 # Có token hay không
    token_id: Optional[int]         # ID token hiện tại
    token_received_time: float      # Thời gian nhận token
    
    # Giao tiếp
    server_socket: socket           # Lắng nghe kết nối
    client_socket: socket           # Kết nối tới node kế tiếp
    
    # Xử lý dữ liệu
    message_queue: Queue            # Hàng đợi xử lý
    send_queue: Queue               # Hàng đợi gửi
    buffer: Dict[int, Message]      # Lưu trữ tin nhắn
    acknowledgments: Dict[int, bool]# Xác nhận
    
    # Thống kê
    messages_sent: int              # Số gói tin gửi
    messages_received: int          # Số gói tin nhận
    tokens_received: int            # Số lần nhận token
```

### Luồng Hoạt Động Node

```
Node:
├─ start()
│  ├─ Tạo server_socket lắng nghe
│  ├─ Bắt đầu _listen_for_messages()     [Thread 1]
│  ├─ Bắt đầu _process_messages()        [Thread 2]
│  └─ Bắt đầu _connect_to_next_node()    [Thread 3]
│
├─ Thread 1: _listen_for_messages()
│  ├─ Lắng nghe trên port
│  ├─ Khi có kết nối:
│  │  ├─ Nhận dữ liệu
│  │  ├─ Parse thành Message
│  │  ├─ Đặt vào message_queue
│  │  └─ Gửi ACK nếu cần
│  └─ Lặp lại
│
├─ Thread 2: _process_messages()
│  ├─ Lấy Message từ queue
│  ├─ Xác định loại:
│  │  ├─ TOKEN → _handle_token() → Chuyển tiếp
│  │  ├─ REQUEST → _handle_request() → Lưu buffer
│  │  ├─ REPLY → _handle_reply() → Lưu buffer
│  │  ├─ DATA → _handle_data() → Lưu buffer
│  │  └─ ACK → _handle_ack() → Cập nhật
│  └─ Lặp lại
│
└─ Thread 3: _connect_to_next_node()
   ├─ Tạo client_socket
   ├─ Kết nối tới node kế tiếp
   ├─ Sẵn sàng gửi dữ liệu
   ├─ Nếu mất kết nối → Thử lại
   └─ Lặp lại
```

## 🎚️ Layer: Ring Manager (Quản Lý Vòng)

### Cấu Trúc Manager

```python
class TokenRingManager:
    num_nodes: int                  # Số lượng node
    base_port: int                  # Port bắt đầu
    nodes: List[Node]               # Danh sách các node
    is_running: bool                # Trạng thái chạy
```

### Quy Trình Khởi Tạo

```
create_ring():
├─ Tạo num_nodes Node
│  ├─ Node 0: port=base_port+0, next=Node 1
│  ├─ Node 1: port=base_port+1, next=Node 2
│  ├─ Node 2: port=base_port+2, next=Node 3
│  └─ Node n: port=base_port+n, next=Node 0 (vòng)
└─ Nối các node thành vòng

start_ring():
├─ Bắt đầu tất cả node.start()
├─ Chờ tất cả node sẵn sàng (3 giây)
├─ Tạo token đầu tiên
├─ Gửi token tới node đầu tiên
└─ Bắt đầu _monitor_ring() [Thread]

_monitor_ring():
├─ Định kỳ (mỗi 5 giây):
│  └─ print_stats()
└─ Lặp lại
```

## 🔄 Quá Trình Token Di Chuyển

```
Thời gian: t₀
┌─────────────┐
│   Node 0    │
│  HAS TOKEN  │
│   id=1      │
└─────────────┘

Thời gian: t₀ + 0.5s
┌─────────────┐
│   Node 0    │  ┌─────────────┐
│ Xử lý token │→→→│  Truyền tới  │
│    Gửi data │  │   Node 1     │
└─────────────┘  └─────────────┘

Thời gian: t₀ + 1s
                 ┌─────────────┐
                 │   Node 1    │
                 │  HAS TOKEN  │
                 │   id=1      │
                 └─────────────┘

Thời gian: t₀ + 1.5s
                 ┌─────────────┐
                 │   Node 1    │  ┌─────────────┐
                 │ Xử lý token │→→→│  Truyền tới  │
                 │    Gửi data │  │   Node 2     │
                 └─────────────┘  └─────────────┘

...và cứ tiếp tục
```

## 📨 Quá Trình Gửi/Nhận Dữ Liệu

### Kịch Bản 1: Gửi Unicast

```
Node A muốn gửi dữ liệu tới Node B

1. Node A giữ token
   ├─ Kiểm tra send_queue
   └─ Có dữ liệu cần gửi

2. Node A tạo MESSAGE
   ├─ msg_type = REQUEST/DATA/REPLY
   ├─ sender_id = A
   ├─ receiver_id = B
   └─ data = payload

3. Node A gửi MESSAGE trực tiếp tới Node B
   ├─ Tạo kết nối TCP
   ├─ Gửi JSON Message
   └─ Đóng kết nối

4. Node B nhận MESSAGE
   ├─ Server socket nhận kết nối
   ├─ Parse JSON
   ├─ Đặt vào message_queue
   └─ Gửi ACK

5. Node A nhận ACK
   ├─ acknowledgments[seq_num] = True
   └─ Xác nhận gửi thành công

6. Node A chuyển TOKEN tới Node C
   ├─ Chuyển tới client_socket (kết nối Node C)
   └─ Token di chuyển tiếp
```

### Kịch Bản 2: Broadcast

```
Node A muốn gửi dữ liệu tới tất cả

1. Node A giữ token

2. Node A gửi MESSAGE tới từng node
   ├─ Gửi tới Node B
   ├─ Gửi tới Node C
   └─ Gửi tới Node D

3. Mỗi node nhận và lưu vào buffer

4. Node A chuyển token
```

## 🧵 Mô Hình Thread

```
Node:
├─ Main Thread
│  └─ node.start()
│
├─ Listener Thread (daemon)
│  ├─ server_socket.accept() [blocking]
│  ├─ Nhận kết nối từ node trước
│  ├─ Đọc dữ liệu
│  └─ Gọi _handle_incoming_message()
│
├─ Process Thread (daemon)
│  ├─ message_queue.get() [blocking]
│  ├─ Xử lý message
│  └─ Gọi _handle_*()
│
└─ Connect Thread (daemon)
   ├─ socket.connect() [blocking]
   ├─ Duy trì kết nối tới node kế tiếp
   └─ Sẵn sàng gửi dữ liệu

Manager:
├─ Main Thread
│  └─ manager.start_ring()
│
└─ Monitor Thread (daemon)
   ├─ Định kỳ mỗi 5 giây
   ├─ print_stats()
   └─ Ghi log
```

## 🔒 Thread Safety

### Cơ Chế Bảo Vệ

1. **Message Queue**
   ```python
   message_queue = queue.Queue()  # Thread-safe FIFO
   ```

2. **Send Queue**
   ```python
   send_queue = queue.Queue()     # Thread-safe FIFO
   ```

3. **Lock trên Buffer** (tùy chọn)
   ```python
   buffer_lock = threading.Lock()
   with buffer_lock:
       buffer[seq_num] = message
   ```

## ⚡ Các Lỗi Có Thể Xảy Ra & Cách Xử Lý

### 1. Node Chết (Node Failure)

```
Vấn đề: Node B bị crash
├─ Node A đang chờ kết nối tới Node B
└─ Timeout → ConnectionRefusedError

Xử Lý:
├─ Tự động thử kết nối lại
├─ Delay 2 giây rồi thử lại
└─ Lặp lại cho đến khi kết nối được
```

### 2. Token Mất (Token Loss)

```
Vấn đề: Token bị mất trong quá trình truyền
├─ Không node nào nhận token
└─ Vòng đóng băng

Xử Lý (hiện tại): Không có
Cần thêm:
├─ Timeout: Nếu token quá lâu không có node giữ
├─ Regenerate: Tạo token mới
└─ Heartbeat: Định kỳ kiểm tra
```

### 3. Duplicate Message

```
Vấn đề: Message gửi 2 lần
├─ Network delay
└─ Retry gửi lại

Xử Lý:
├─ sequence_num độc nhất
├─ Kiểm tra trùng trước xử lý
└─ Bỏ qua nếu đã xử lý
```

## 📊 Thông Số Hiệu Năng

### Độ Trễ Token (Token Latency)

```
Thời gian token di chuyển từ node này sang node khác:
├─ Tạo message: ~0.1ms
├─ Gửi qua socket: ~0.1ms
├─ Nhận và xử lý: ~0.2ms
└─ Tổng cộng: ~0.4ms

Vòng hoàn chỉnh (N node):
├─ Thời gian = N × latency
├─ VD: 4 node → ~1.6ms
└─ VD: 10 node → ~4ms
```

### Bandwidth

```
Message payload: ~500 bytes (trung bình)
Token per node: ~0.1 sec
Bandwidth: 500 bytes / 0.1s = 5 KB/s
```

## 🎯 Cải Tiến Có Thể

1. **Phát Hiện Token Mất**
   - Thêm timeout và regeneration
   
2. **Priority Queue**
   - Ưu tiên tin nhắn quan trọng
   
3. **Compression**
   - Nén payload để tiết kiệm bandwidth
   
4. **Encryption**
   - Mã hóa dữ liệu
   
5. **Persistence**
   - Lưu tin nhắn vào database
   
6. **Monitoring Dashboard**
   - Web interface để theo dõi
   
7. **Load Balancing**
   - Phân bổ token thời gian
   
8. **Error Recovery**
   - Tự động phục hồi khi node chết

## 📚 Tài Liệu Tham Khảo

- **IEEE 802.5**: Token Ring Standard
- **Computer Networks** - Kurose & Ross
- **Distributed Systems** - Tanenbaum & Van Steen

---

**Version**: 1.0  
**Last Updated**: 2026-04-01  
**Author**: Token Ring Team
