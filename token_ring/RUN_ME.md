# ▶️ RUN_ME.md - Chạy Token Ring Ngay Bây Giờ!

## 🚀 3 Bước Để Chạy

### 1️⃣ Mở Terminal
```bash
# Trên Windows PowerShell hoặc Command Prompt
# Hoặc terminal bất kỳ
```

### 2️⃣ Chuyển Thư Mục
```bash
cd ..\token_ring\src
```

### 3️⃣ Chạy Demo
```bash
python demo.py 1
```

---

## ✨ Bạn Sẽ Thấy Gì?

```
================================================================================
DEMO 1: Khởi động vòng Token Ring cơ bản
================================================================================

2026-04-01 22:07:15,606 - INFO - Tạo vòng Token Ring với 4 node
2026-04-01 22:07:15,606 - INFO - Tạo Node 0 trên port 5000 -> Node 1 trên port 5001
...
2026-04-01 22:07:20,636 - INFO - Nhận được TOKEN (id=1)

Token đang di chuyển trong vòng...
Nhấn Ctrl+C để dừng hoặc chờ 15 giây

2026-04-01 22:07:21,138 - INFO - Chuyển TOKEN tới node kế tiếp
2026-04-01 22:07:21,138 - INFO - Nhận được TOKEN (id=1)

================================================================================
THỐNG KÊ VÒNG TOKEN RING
================================================================================
Node 0: Token=False, Gửi=2, Nhận=1, Token nhận=2, Buffer=0
Node 1: Token=False, Gửi=1, Nhận=1, Token nhận=1, Buffer=0
Node 2: Token=False, Gửi=1, Nhận=1, Token nhận=1, Buffer=0
Node 3: Token=False, Gửi=1, Nhận=1, Token nhận=1, Buffer=0
================================================================================
```

---

## 🎯 Giải Thích Output

**Token đang di chuyển:**
```
Node 0 nhận token → Xử lý → Chuyển tới Node 1
Node 1 nhận token → Xử lý → Chuyển tới Node 2
Node 2 nhận token → Xử lý → Chuyển tới Node 3
Node 3 nhận token → Xử lý → Chuyển tới Node 0 (vòng lặp)
```

**Thống kê:**
- **Gửi**: Số gói tin gửi đi
- **Nhận**: Số gói tin nhận được
- **Token nhận**: Số lần node nhận được token

---

## 📊 Các Demo Khác

```bash
# Demo 1: Vòng cơ bản
python demo.py 1

# Demo 2: Gửi tin nhắn
python demo.py 2

# Demo 3: Token di chuyển (6 node)
python demo.py 3

# Demo 4: Nhiều tin nhắn
python demo.py 4

# Chạy tất cả
python demo.py 5
```

---

## 💡 Ví Dụ Sử Dụng

### Ví Dụ 1: Cơ Bản
```bash
python example.py 1
```

### Ví Dụ 6: Client-Server
```bash
python example.py 6
```

---

## 🔧 Tùy Chỉnh

### Thay Đổi Số Node
Mở file `src/demo.py` hoặc `src/example.py`, tìm:
```python
TokenRingManager(num_nodes=4, base_port=5000)
```

Thay `4` thành số node bạn muốn (ví dụ: `8`)

### Thay Đổi Port
```python
TokenRingManager(num_nodes=4, base_port=6000)  # Dùng port 6000-6003
```

---

## ❌ Nếu Có Lỗi

### Lỗi: "Address already in use"
```
Nguyên nhân: Port đã được sử dụng
Cách sửa: Thay port
python demo.py  # Bạn có thể chọn port khác
```

### Lỗi: "Connection refused"
```
Nguyên nhân: Node chưa sẵn sàng
Cách sửa: Chờ dài hơn hoặc thử lại
```

### Lỗi: "No module named 'ring_manager'"
```
Nguyên nhân: Không ở trong thư mục src
Cách sửa: cd token_ring/src
```

---

