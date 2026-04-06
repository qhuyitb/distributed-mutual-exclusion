# 🚀 GETTING STARTED - Ricart-Agrawala Demo

## ⏱️ 3 Phút để Chạy Demo

### Bước 1: Mở Terminal
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
```

### Bước 2: Chạy Demo (Chọn 1)

#### **🟢 EASY (Khuyến Khích)**
Nếu bạn muốn **4 cửa sổ terminal tự động mở**:

**Windows:**
```bash
start_demo.bat
```

**Linux/Mac:**
```bash
chmod +x start_demo.sh
./start_demo.sh
```

---

#### **🔵 MANUAL (Kiểm soát hơn)**

Mở **4 Command Prompt/Terminal Windows** riêng:

**Window 1 - Coordinator:**
```bash
python coordinator.py
```

**Window 2 - Node 0:**
```bash
python node_process.py 0 3
```

**Window 3 - Node 1:**
```bash
python node_process.py 1 3
```

**Window 4 - Node 2:**
```bash
python node_process.py 2 3
```

---

### Bước 3: Tương Tác

Khi tất cả 4 windows ready, bạn sẽ thấy:

```
[Node 0] > _
[Node 1] > _
[Node 2] > _
[Coordinator] Started...
```

**Gõ vào Node windows:**
- `request` → Request vào Critical Section
- `quit` → Thoát node

---

## 📊 Ví Dụ: Chạy Demo

**Coordinator Window:**
```
[Coordinator] Started on localhost:5000
[Coordinator] Node 0 registered (listening: localhost:6000)
[Coordinator] Node 1 registered (listening: localhost:6001)
[Coordinator] Node 2 registered (listening: localhost:6002)
```

**Node 0 Window:**
```
[Node 0] > request
[Node 0] >>> REQUESTING (ts=1)
[Node 0] Sent REQUEST to Node 1
[Node 0] Sent REQUEST to Node 2
[Node 0] Received REPLY from Node 1 (1/2)
[Node 0] Received REPLY from Node 2 (2/2)
[Node 0] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts=1)
... (thực thi 2 giây) ...
[Node 0] ✗ EXITING CS
[Node 0] Sent REPLY to Node 1
[Node 0] Sent REPLY to Node 2
[Node 0] > _
```

**Node 1 Window:**
```
[Node 1] > 
[Node 1] Received REQUEST from Node 0 (ts=1)
[Node 1] Sent REPLY immediately to Node 0
[Node 1] >
```

---

## 🧪 Test Cases

### Test 1: Sequential
```
[Node 0] > request
[Node 0] > (waits 3 seconds)
[Node 0] > _
[Node 1] > request
[Node 1] > (waits 3 seconds)
[Node 1] > _
```

✅ **Mutual Exclusion verified** - chỉ 1 node vào CS một lúc

---

### Test 2: Concurrent
```
[Node 0] > request  (ts=1)
[Node 1] > request  (ts=2) 
[Node 2] > request  (ts=3)
```

✅ **FIFO Ordering** - Node 0 (ts=1) enters first, then 1, then 2

---

### Test 3: Multiple Rounds
```
[Node 0] > request
[Node 0] > (waiting 3s)
[Node 1] > request  (concurrent)
[Node 0] > (finishes, sends REPLY to Node 1)
[Node 1] > (enters CS)
```

✅ **Fairness maintained** - lower timestamp gets priority

---

## 📁 File Guide

| File | Purpose |
|------|---------|
| `coordinator.py` | Central registration server |
| `node_process.py` | Independent node client |
| `start_demo.bat` | Auto-start all 4 processes (Windows) |
| `WINDOWS_HOWTO.md` | Detailed Windows guide |
| `MULTI_PROCESS_DEMO.md` | Complete technical docs |
| `INDEX.md` | Overview of all files |

---

## ❓ FAQ

**Q: Tại sao có 4 windows?**  
A: 1 Coordinator (quản lý) + 3 Node clients (tham gia). Mỗi là separate process.

**Q: Tôi có thể add thêm nodes không?**  
A: Có! `python node_process.py 3 4` thêm Node 3 vào 4-node system.

**Q: "Address already in use" - làm gì?**  
A: Ports đang dùng. Restart Windows hoặc đợi 30 giây rồi thử lại.

**Q: Có cách demo khác không?**  
A: Có! Chạy `python main.py` để demo simulation mode (all in 1 process).

---

## 🎯 What You'll Learn

✅ Distributed mutual exclusion algorithm  
✅ Network communication with sockets  
✅ Logical clocks (Lamport timestamps)  
✅ FIFO ordering for fairness  
✅ No single point of failure  
✅ Race conditions và synchronization  

---

## 📚 Next Steps

1. **Chạy demo** → `start_demo.bat` (Windows)
2. **Thử test cases** → Sequential, Concurrent, Multiple rounds
3. **Đọc code** → `node_process.py`, `coordinator.py`
4. **Modify & Experiment** → Try different scenarios
5. **Read docs** → `MULTI_PROCESS_DEMO.md` for details

---

**Ready?** 👇

```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
start_demo.bat
```

Or for detailed instructions: Read `WINDOWS_HOWTO.md`

---

**Have fun! 🎉**
