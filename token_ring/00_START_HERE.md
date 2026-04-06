# 👋 00_START_HERE.md - Bắt Đầu Từ ĐÂY!

## 🎯 Chào Mừng Đến Token Ring Implementation!

Đây là triển khai hoàn chỉnh của **Thuật Toán Token Ring** bằng Python.

### 🎁 Bạn Sẽ Học Được:
- ✅ Vòng logic (Logical Ring)
- ✅ Token-based protocol
- ✅ Network programming (Socket)
- ✅ Multi-threading
- ✅ Distributed systems

---

## ⚡ 3 Cách Bắt Đầu

### 1️⃣ **Chạy Ngay (30 giây)**
```bash
cd d:\Huy\Documents\HTPT\BTL\token_ring\src
python demo.py 1
```
→ Đọc: [RUN_ME.md](RUN_ME.md)

### 2️⃣ **Bắt Đầu Nhanh (5-10 phút)**
```bash
python demo.py        # Chọn demo
python example.py 1   # Chạy ví dụ
```
→ Đọc: [QUICK_START.md](QUICK_START.md)

### 3️⃣ **Học Chi Tiết (1-2 giờ)**
Đọc các tài liệu theo thứ tự:
1. [README_VI.md](README_VI.md) - Giới thiệu
2. [HUONG_DAN.md](HUONG_DAN.md) - Hướng dẫn
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Kiến trúc

---

## 📁 Cấu Trúc

```
token_ring/
├─ 👋 00_START_HERE.md         ← Bạn đang ở đây!
├─ ⚡ RUN_ME.md                ← Chạy ngay
├─ 🚀 QUICK_START.md           ← Bắt đầu nhanh
├─ 📖 README_VI.md             ← Giới thiệu
├─ 📚 HUONG_DAN.md             ← Hướng dẫn chi tiết
├─ 🏗️ ARCHITECTURE.md          ← Kiến trúc kỹ thuật
├─ 📋 INDEX.md                 ← Mục lục
├─ 📦 MANIFEST.md              ← Danh sách tệp
│
└─ src/
   ├─ message.py               ← Cấu trúc gói tin
   ├─ node.py                  ← Lớp Node
   ├─ ring_manager.py          ← Quản lý vòng
   ├─ demo.py                  ← 4 demo
   └─ example.py               ← 6 ví dụ
```

---

## 🎬 Các Demo

| Demo | Mô Tả |
|------|-------|
| `1` | ⭕ Vòng cơ bản - Token di chuyển |
| `2` | 💬 Gửi tin nhắn giữa các node |
| `3` | 🔄 Token di chuyển (6 node) |
| `4` | 📤 Nhiều tin nhắn liên tiếp |
| `5` | 🎬 Chạy tất cả |

```bash
cd src
python demo.py 1    # Chạy demo 1
python demo.py      # Chọn từ menu
```

---

## 💡 Ví Dụ (6 ví dụ)

```bash
python example.py 1  # Cài đặt cơ bản
python example.py 2  # Gửi unicast message
python example.py 3  # Gửi nhiều tin nhắn
python example.py 4  # Truy cập trực tiếp node
python example.py 5  # Vòng kích thước khác nhau
python example.py 6  # Mô hình Client-Server
```

---

## 🎓 Khái Niệm Chính (1 phút)

### Token Ring Là Gì?
```
Node 0 ──▶ Node 1 ──▶ Node 2 ──▶ Node 3
 ▲                                   │
 └───────────────────────────────────┘

Token di chuyển: 0→1→2→3→0→...
```

### Các Loại Gói Tin
- 🔴 **TOKEN**: Di chuyển xung quanh vòng
- 📨 **REQUEST**: Yêu cầu từ node
- 📬 **REPLY**: Phản hồi
- 📦 **DATA**: Dữ liệu
- ✅ **ACK**: Xác nhận

### Port Mặc Định
- Node 0: localhost:5000
- Node 1: localhost:5001
- Node 2: localhost:5002
- Node 3: localhost:5003

---

## 📖 Tài Liệu (Theo Mục Đích)

### Muốn Chạy Ngay?
→ Đọc **[RUN_ME.md](RUN_ME.md)** (< 5 phút)
```bash
python demo.py 1
```

### Muốn Bắt Đầu Nhanh?
→ Đọc **[QUICK_START.md](QUICK_START.md)** (5-10 phút)

### Muốn Hiểu Kỹ?
→ Đọc **[README_VI.md](README_VI.md)** (15-20 phút)

### Muốn Học Chi Tiết?
→ Đọc **[HUONG_DAN.md](HUONG_DAN.md)** (30-45 phút)

### Muốn Hiểu Kiến Trúc?
→ Đọc **[ARCHITECTURE.md](ARCHITECTURE.md)** (45-60 phút)

### Muốn Tìm Tài Liệu?
→ Đọc **[INDEX.md](INDEX.md)** (5 phút)

### Muốn Xem Tổng Quát?
→ Đọc **[SUMMARY.md](SUMMARY.md)** (20-30 phút)

### Muốn Biết Chi Tiết Tệp?
→ Đọc **[MANIFEST.md](MANIFEST.md)** (10 phút)

---

## ❓ Bạn Muốn...

| Bạn Muốn | Làm |
|---------|-----|
| **Chạy ngay** | `cd src; python demo.py 1` |
| **Hiểu vòng logic** | Đọc QUICK_START.md |
| **Biết APIs** | Đọc HUONG_DAN.md |
| **Hiểu code chi tiết** | Đọc ARCHITECTURE.md |
| **Tìm demo cụ thể** | Đọc INDEX.md |
| **Biết cấu trúc** | Đọc MANIFEST.md |
| **Tạo code riêng** | Xem example.py |
| **Debug lỗi** | Chạy demo 1 trước |

---

## ✅ Checklist Bắt Đầu

- [ ] Python 3.6+ cài đặt
  ```bash
  python --version  # Kiểm tra
  ```

- [ ] Vào thư mục src
  ```bash
  cd d:\Huy\Documents\HTPT\BTL\token_ring\src
  ```

- [ ] Chạy demo 1
  ```bash
  python demo.py 1
  ```

- [ ] Thấy output token di chuyển ✓

- [ ] Đọc tài liệu phù hợp

---

## 🚀 Bắt Đầu (Copy & Paste)

### Windows PowerShell / Command Prompt
```bash
cd d:\Huy\Documents\HTPT\BTL\token_ring\src
python demo.py 1
```

### Linux / macOS
```bash
cd ~/Documents/HTPT/BTL/token_ring/src  # Điều chỉnh đường dẫn
python3 demo.py 1
```

---

## 📊 Output Ví Dụ

Bạn sẽ thấy:
```
================================================================================
DEMO 1: Khởi động vòng Token Ring cơ bản
================================================================================

Node 0 khởi động trên port 5000
Node 1 khởi động trên port 5001
Node 2 khởi động trên port 5002
Node 3 khởi động trên port 5003

Token đang di chuyển trong vòng...

2026-04-01 22:07:21,138 - INFO - Nhận được TOKEN (id=1)
2026-04-01 22:07:21,138 - INFO - Chuyển TOKEN tới node kế tiếp
2026-04-01 22:07:21,640 - INFO - Nhận được TOKEN (id=1)

================================================================================
THỐNG KÊ VÒNG TOKEN RING
================================================================================
Node 0: Token=False, Gửi=2, Nhận=1, Token nhận=2
Node 1: Token=False, Gửi=1, Nhận=1, Token nhận=1
Node 2: Token=False, Gửi=1, Nhận=1, Token nhận=1
Node 3: Token=False, Gửi=1, Nhận=1, Token nhận=1
================================================================================
```

---

## 🔧 Nếu Có Lỗi

### Lỗi 1: "Address already in use"
```
→ Đổi port: TokenRingManager(base_port=6000)
```

### Lỗi 2: "Connection refused"
```
→ Chờ lâu hơn: time.sleep(5)
```

### Lỗi 3: "No module named 'ring_manager'"
```
→ Vào đúng thư mục: cd token_ring/src
```

### Lỗi 4: Token không di chuyển
```
→ Kiểm tra log và thử demo 1
```

---

## 💭 Câu Hỏi Nhanh

**Q: Tôi phải làm gì trước?**  
A: Chạy `python demo.py 1`

**Q: Làm sao để hiểu Token Ring?**  
A: 1. Chạy demo 2. Đọc README_VI.md 3. Đọc HUONG_DAN.md

**Q: Có thể thêm node không?**  
A: Có! `TokenRingManager(num_nodes=10)`

**Q: Port 5000 bị chiếm thì sao?**  
A: `TokenRingManager(base_port=6000)`

**Q: Tôi muốn sửa code?**  
A: Xem example.py hoặc ARCHITECTURE.md

---

## 📞 Cần Giúp?

1. **Lần đầu tiên?** → Đọc RUN_ME.md
2. **Muốn chạy?** → Chạy `python demo.py 1`
3. **Có lỗi?** → Kiểm tra phần "Nếu Có Lỗi"
4. **Muốn hiểu hơn?** → Đọc QUICK_START.md
5. **Muốn chi tiết?** → Đọc HUONG_DAN.md

---

## 🎉 Bạn Đã Sẵn Sàng!

Dự án này:
- ✅ Đã hoàn thành 100%
- ✅ Đã được test
- ✅ Có tài liệu đầy đủ
- ✅ Sẵn sàng chạy
- ✅ Dễ tùy chỉnh

### Tiếp Theo:
1. **Chạy**: `python demo.py 1`
2. **Học**: Đọc tài liệu phù hợp
3. **Thực Hành**: Chạy các ví dụ
4. **Sửa Đổi**: Tạo code riêng

---

## 🚀 Let's Go!

```bash
cd d:\Huy\Documents\HTPT\BTL\token_ring\src
python demo.py 1
```

**Chúc mừng! Bạn vừa chạy Token Ring! 🎊**

---

**Trạng Thái**: ✅ Sẵn sàng  
**Phiên Bản**: 1.0  
**Ngày**: 2026-04-01

👉 **Bắt đầu nào!** → [RUN_ME.md](RUN_ME.md)
