## 🎯 Windows - Hướng Dẫn Chạy Multi-Process Demo

### Yêu cầu

1. **Python 3.7+** đã cài và trong PATH
   - Kiểm tra: Mở CMD/PowerShell gõ `python --version`
   - Nếu chưa cài: Download từ https://www.python.org/downloads/ (chọn "Add to PATH")

### ⚡ Cách Chạy Nhanh Nhất (Windows)

#### **Option 1: AutoRun (1 dòng lệnh)**

Mở Windows PowerShell hoặc Command Prompt, gõ:

```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
start_demo.bat
```

**✅ Kết quả:** 4 cửa sổ terminal sẽ tự động mở:
- Coordinator Server  
- Node 0, Node 1, Node 2

---

#### **Option 2: Manual (Nếu auto không chạy)**

Mở **4 Command Prompt windows** riêng biệt:

**Window 1 - Coordinator Server:**
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
python coordinator.py
```
Chờ đến khi thấy: `[Coordinator] Waiting for nodes...`

**Window 2 - Node 0:**
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
python node_process.py 0 3
```

**Window 3 - Node 1:**
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
python node_process.py 1 3
```

**Window 4 - Node 2:**
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
python node_process.py 2 3
```

---

### 🎮 Tương Tác với Nodes

Sau khi tất cả 4 window đã ready, bạn sẽ thấy trên mỗi Node window:

```
[Node 0] > _
```

Bạn có thể gõ:

#### **`request`** - Request vào Critical Section
```
[Node 0] > request
[Node 0] >>> REQUESTING (ts=1)
[Node 0] Received REPLY from Node 1 (1/2)
[Node 0] Received REPLY from Node 2 (2/2)
[Node 0] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts=1)
... thực thi trong CS (2 giây) ...
[Node 0] ✗ EXITING CS
[Node 0] > _
```

#### **`quit`** - Thoát node
```
[Node 0] > quit
[Node 0] Shutting down...
```

---

### 📊 Test Scenarios

#### **Test 1: Sequential Access**

Gõ lần lượt (chờ mỗi node finish trước):

```
Window Node 0: request  → (wait 3s) → exit
Window Node 1: request  → (wait 3s) → exit
Window Node 2: request  → (wait 3s) → exit
```

**Kỳ vọng:** Chỉ 1 node vào CS một lúc ✅

---

#### **Test 2: Concurrent Requests (Contention)**

Gõ nhanh tuần tự:

```
Window Node 0: request
Window Node 1: request
Window Node 2: request
```

**Kỳ vọng:** Trong Coordinator window, bạn sẽ thấy:
```
[Coordinator] Node 0 registered
[Coordinator] Node 1 registered  
[Coordinator] Node 2 registered
```

Và nodes sẽ handle requests theo FIFO timestamp:
- Node 0 enters CS (ts=1)
- Node 0 exits → sends REPLY
- Node 1 enters CS (ts=2)
- Node 1 exits → sends REPLY
- Node 2 enters CS (ts=3)

✅ **Mutual Exclusion đảm bảo!**

---

#### **Test 3: Multiple Rounds**

```
Window Node 0: request  → exit
wait 1-2 seconds
Window Node 0: request  → exit
```

Interleaved:
```
Window Node 0: request
Window Node 1: request  
```

**Kỳ vọng:** Fairness - lower timestamp được serve trước ✅

---

### 📋 Kiểm Tra Output

#### Coordinator Window:
```
[Coordinator] Started on localhost:5000
[Coordinator] Waiting for nodes to register...

[Coordinator] Node 0 registered (listening: localhost:6000)
[Coordinator] Node 1 registered (listening: localhost:6001)
[Coordinator] Node 2 registered (listening: localhost:6002)
```

#### Node 0 Window (khi request):
```
[Node 0] Starting...
[Node 0] Listening on port 6000
[Node 0] Connected to Coordinator
[Node 0] Other nodes: {1: ('localhost', 6001), 2: ('localhost', 6002)}
[Node 0] Ready for commands
[Node 0] Type 'request' or 'quit'

[Node 0] > request
[Node 0] >>> REQUESTING (ts=1)
[Node 0] Sent REQUEST to Node 1
[Node 0] Sent REQUEST to Node 2
[Node 0] Received REPLY from Node 1 (1/2)
[Node 0] Received REPLY from Node 2 (2/2)
[Node 0] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts=1)
[Node 0] ✗ EXITING CS
[Node 0] Sent REPLY to Node 1
[Node 0] Sent REPLY to Node 2

[Node 0] >
```

#### Node 1 Window (khi nhận request từ Node 0):
```
[Node 1] > 
[Node 1] Received REQUEST from Node 0 (ts=1)
[Node 1] Sent REPLY immediately to Node 0
```

---

### ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **"python is not recognized"** | Cài Python từ python.org, tích "Add Python to PATH" |
| **"Address already in use"** | Ports còn dùng. Restart Windows hoặc đợi 30s rồi thử lại |
| **Nodes can't connect** | Coordinator phải start trước. Chờ 2s trước start nodes |
| **No output** | Kiểm tra cmd window - scroll up xem có error không |
| **"Connection refused"** | Coordinator crashed. Kiểm tra Coordinator window |

---

### 🔌 Network Diagram

```
┌────────────────────────────────────────────────┐
│                  localhost                     │
├────────────────────────────────────────────────┤
│                                                │
│  Coordinator (port 5000)                       │
│       ↓ registers ↓                             │
│  ┌────────┬────────┬────────┐                 │
│  │        │        │        │                 │
│  ↓        ↓        ↓        ↓                 │
│  Node 0   Node 1   Node 2                     │
│  (6000)   (6001)   (6002)                     │
│    ↕        ↕        ↕                         │
│    └────────┴────────┘ (direct TCP)           │
│      REQUEST & REPLY messages                  │
│                                                │
└────────────────────────────────────────────────┘
```

---

### 📚 Files

```
coordinator.py      → Server coordinator
node_process.py     → Node client (chạy 4 lần, mỗi lần 1 node)
start_demo.bat      → Auto-start script (Windows)
MULTI_PROCESS_DEMO.md → Chi tiết documentation
```

---

### 💡 Tips

1. **Mở Node windows side-by-side** để dễ thấy actions
2. **Watch Coordinator window** để thấy khi nào nodes connect
3. **Nhìn timestamps** - lower ts enters CS trước
4. **Thử rapid fire requests** để test mutual exclusion

---

### 🎉 Demo Success

Khi bạn thấy:
- Tất cả 3 nodes request
- Chỉ 1 node vào CS một lúc
- Các node sau xếp hàng (FIFO)
- Release đúng thứ tự

**→ Ricart-Agrawala algorithm hoạt động đúng!** ✅

---

**Vấn đề gì? Xem MULTI_PROCESS_DEMO.md hoặc check Coordinator/Node windows.**
