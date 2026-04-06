# 📑 Mục Lục - Token Ring Implementation

## 🎯 Bạn Nên Bắt ĐẦU Từ ĐÂU?

### ⚡ **Bắt Đầu Nhanh (2 phút)**
→ Đọc **[QUICK_START.md](QUICK_START.md)**
```bash
cd token_ring/src
python demo.py 1
```

### 📖 **Hiểu Dự Án**
→ Đọc **[README_VI.md](README_VI.md)** (Tiếng Việt)  
→ hoặc **[README.md](README.md)** (English)

### 📚 **Hướng Dẫn Chi Tiết**
→ Đọc **[HUONG_DAN.md](HUONG_DAN.md)**
- Giải thích từng thành phần
- Ví dụ sử dụng cụ thể
- Cấu trúc gói tin

### 🏗️ **Kiến Trúc Kỹ Thuật**
→ Đọc **[ARCHITECTURE.md](ARCHITECTURE.md)**
- Thiết kế hệ thống
- Luồng hoạt động chi tiết
- Thread & Socket

### 📋 **Tóm Tắt Dự Án**
→ Đọc **[SUMMARY.md](SUMMARY.md)**
- Tất cả chức năng
- Các module chính
- Kỹ năng học được

---

## 📁 Cấu Trúc Tệp

```
token_ring/
│
├─ README.md                  📖 Giới thiệu chính
├─ README_VI.md              📖 Giới thiệu Tiếng Việt
├─ QUICK_START.md            ⚡ Bắt đầu nhanh
├─ HUONG_DAN.md              📚 Hướng dẫn chi tiết
├─ ARCHITECTURE.md           🏗️ Kiến trúc kỹ thuật
├─ SUMMARY.md                📋 Tóm tắt
├─ INDEX.md                  📑 File này
├─ requirements.txt          📦 Dependencies
│
└─ src/
   ├─ message.py             💬 Cấu trúc gói tin
   ├─ node.py                🔌 Lớp Node
   ├─ ring_manager.py        🎛️ Quản lý vòng
   ├─ demo.py                🎬 Các demo
   ├─ example.py             💡 Các ví dụ
   └─ __init__.py            📦 Package init
```

---

## 🎬 Chạy Demo & Ví Dụ

### Demo (Built-in)
```bash
cd token_ring/src

python demo.py          # Chọn từ menu
python demo.py 1        # Demo 1: Vòng cơ bản
python demo.py 2        # Demo 2: Gửi tin nhắn
python demo.py 3        # Demo 3: Token di chuyển (6 node)
python demo.py 4        # Demo 4: Nhiều tin nhắn
python demo.py 5        # Chạy tất cả
```

### Ví Dụ (6 ví dụ sử dụng)
```bash
python example.py       # Chọn từ menu
python example.py 1     # Cài đặt cơ bản
python example.py 2     # Gửi unicast message
python example.py 3     # Gửi nhiều tin nhắn
python example.py 4     # Truy cập trực tiếp node
python example.py 5     # Vòng kích thước khác nhau
python example.py 6     # Mô hình Client-Server
```

---

## 📚 Tài Liệu Chi Tiết

### Mục Lục Tài Liệu

| Tệp | Chủ Đề | Thích Hợp Cho |
|-----|--------|--------------|
| [README_VI.md](README_VI.md) | Giới thiệu chung | Người mới bắt đầu |
| [QUICK_START.md](QUICK_START.md) | Bắt đầu nhanh | Người vội |
| [HUONG_DAN.md](HUONG_DAN.md) | Hướng dẫn chi tiết | Người muốn hiểu kỹ |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc kỹ thuật | Developer |
| [SUMMARY.md](SUMMARY.md) | Tóm tắt đầy đủ | Người ôn tập |

---

## 🎯 Các Khái Niệm Chính

### Token Ring Là Gì?
- Vòng logic: Các node được sắp xếp thành vòng kín
- Token di chuyển: Một gói tin đặc biệt di chuyển qua các node
- Công bằng: Mỗi node có cơ hội gửi dữ liệu công bằng
- Không xung đột: Chỉ một node gửi tại một thời điểm

### Các Loại Gói Tin

| Loại | Chức Năng | Ví Dụ |
|------|----------|-------|
| **TOKEN** | Di chuyển qua vòng | `Node 0 → 1 → 2 → 3 → 0` |
| **REQUEST** | Yêu cầu từ node | `Node 0 hỏi Node 2` |
| **REPLY** | Phản hồi từ node | `Node 2 trả lời Node 0` |
| **DATA** | Dữ liệu thông thường | `Node 1 gửi cho Node 3` |
| **ACK** | Xác nhận nhận được | `Node 2 xác nhận Node 0` |

### Cấu Trúc Gói Tin

```python
{
    "msg_type": "REQUEST",           # Loại gói tin
    "sender_id": 0,                  # Node gửi
    "receiver_id": 2,                # Node nhận
    "sequence_num": 1001,            # Số thứ tự
    "timestamp": 1234567890.123,     # Thời gian
    "data": {"action": "query"},     # Dữ liệu
    "token_holder": null,            # Node giữ token
    "visited_nodes": null            # Nodes đã đi qua
}
```

---

## 🔧 Các Module Chính

### 1. message.py - Cấu Trúc Gói Tin
**Định nghĩa:**
- `MessageType`: Enum các loại gói tin
- `Message`: Dataclass cấu trúc gói tin
- `Token`: Lớp Token đặc biệt

**Chức năng:**
- Tạo gói tin
- Serialize/deserialize JSON
- Tạo token

### 2. node.py - Nút Mạng
**Định nghĩa:**
- `Node`: Lớp đại diện cho một node

**Chức năng:**
- Lắng nghe kết nối
- Xử lý gói tin
- Quản lý token
- Gửi/nhận dữ liệu

**3 Luồng chạy:**
1. Listener: Lắng nghe port
2. Processor: Xử lý queue
3. Connector: Kết nối node kế tiếp

### 3. ring_manager.py - Quản Lý Vòng
**Định nghĩa:**
- `TokenRingManager`: Quản lý toàn vòng

**Chức năng:**
- Tạo vòng logic
- Khởi động/dừng các node
- Khởi tạo token
- Gửi dữ liệu giữa các node
- Thống kê và giám sát

---

## 💻 Ví Dụ Sử Dụng

### Ví Dụ 1: Tạo và Chạy Vòng
```python
from ring_manager import TokenRingManager
import time

# Tạo vòng với 4 node
manager = TokenRingManager(num_nodes=4, base_port=5000)

# Tạo vòng logic
manager.create_ring()

# Khởi động vòng
manager.start_ring()

# Chạy 5 giây
time.sleep(5)

# In thống kê
manager.print_stats()

# Dừng vòng
manager.stop_ring()
```

### Ví Dụ 2: Gửi Tin Nhắn
```python
from ring_manager import TokenRingManager
from message import MessageType
import time

manager = TokenRingManager(num_nodes=4, base_port=5000)
manager.create_ring()
manager.start_ring()

time.sleep(3)

# Node 0 gửi REQUEST tới Node 2
manager.unicast_message(0, 2, MessageType.REQUEST.value,
                       {'cmd': 'query', 'data': 'hello'})

time.sleep(2)

# Node 2 gửi REPLY tới Node 0
manager.unicast_message(2, 0, MessageType.REPLY.value,
                       {'result': 'ok', 'data': 'world'})

time.sleep(2)

manager.print_stats()
manager.stop_ring()
```

---

## 🎓 Kỹ Năng Học Được

Khi hoàn thành dự án này, bạn sẽ hiểu:

✅ **Network Programming**
- Socket TCP/IP
- Client-Server architecture
- Connection handling

✅ **Multi-Threading**
- Thread creation
- Thread-safe communication
- Queue-based message passing

✅ **Distributed Systems**
- Ring topology
- Token-based protocol
- Message passing

✅ **Python Programming**
- Dataclasses
- Enums
- JSON serialization
- Logging

---

## 🚀 Các Bước Tiếp Theo

### Cơ Bản
1. ✅ Đọc QUICK_START.md
2. ✅ Chạy `python demo.py 1`
3. ✅ Hiểu token di chuyển

### Trung Bình
1. ✅ Đọc HUONG_DAN.md
2. ✅ Chạy các ví dụ
3. ✅ Tạo code riêng

### Nâng Cao
1. ✅ Đọc ARCHITECTURE.md
2. ✅ Hiểu chi tiết từng module
3. ✅ Thêm tính năng mới

---

## ❓ Câu Hỏi Thường Gặp

**Q: Tôi nên bắt đầu từ đâu?**
A: Bắt đầu với [QUICK_START.md](QUICK_START.md) rồi chạy `python demo.py 1`

**Q: Làm thế nào để thêm node mới?**
A: `TokenRingManager(num_nodes=10)` thay vì 4

**Q: Port bị chiếm thì sao?**
A: `TokenRingManager(num_nodes=4, base_port=6000)` dùng port khác

**Q: Tôi muốn hiểu code chi tiết?**
A: Đọc [ARCHITECTURE.md](ARCHITECTURE.md)

**Q: Làm thế nào để debug?**
A: Kiểm tra log được in ra khi chạy demo

**Q: Có thể chạy trên máy thực không?**
A: Có, chỉ cần đổi `localhost` thành IP của máy khác

---

## 📞 Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề:

1. **Đọc tài liệu phù hợp** → Xem mục lục ở trên
2. **Chạy demo** → `python demo.py 1`
3. **Kiểm tra log** → Xem thông báo được in ra
4. **Đọc ARCHITECTURE.md** → Hiểu sâu hơn

---

## 📄 Phiên Bản & Cập Nhật

| Phiên Bản | Ngày | Thay Đổi |
|-----------|------|----------|
| 1.0 | 2026-04-01 | Phiên bản đầu tiên |

---

## 🎉 Bạn Đã Sẵn Sàng!

### Bắt Đầu Ngay:
```bash
cd token_ring/src
python demo.py 1
```

### Hoặc Đọc Tài Liệu:
- **Vội?** → [QUICK_START.md](QUICK_START.md)
- **Muốn hiểu?** → [README_VI.md](README_VI.md)
- **Muốn chi tiết?** → [HUONG_DAN.md](HUONG_DAN.md)
- **Muốn kỹ thuật?** → [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Happy Learning! 🚀**
