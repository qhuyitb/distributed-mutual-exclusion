## 📺 TERMINAL DEMO GUIDE - Ricart-Agrawala

### ✅ Yêu Cầu
- Python 3.7+ đã cài
- 4 Command Prompt / PowerShell / Terminal windows

---

## 🔹 WINDOWS

### Bước 1: Mở 4 Command Prompt Windows

Nhấn `Windows Key + R`, gõ `cmd` rồi Enter. Lặp lại 4 lần để có 4 windows.

### Bước 2: Di Chuyển tới Folder

Trên tất cả 4 windows, gõ:
```
cd /d f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
```

### Bước 3: Chạy Coordinator (Window 1)

```
python coordinator.py
```

Chờ đến khi thấy:
```
[Coordinator] Started on localhost:5000
[Coordinator] Waiting for nodes to register...
```

### Bước 4: Chạy Node 0 (Window 2)

```
python node_process.py 0 3
```

Chờ đến khi thấy:
```
[Node 0] Connected to Coordinator
[Node 0] Ready for commands
[Node 0] >
```

### Bước 5: Chạy Node 1 (Window 3)

```
python node_process.py 1 3
```

Chờ:
```
[Node 1] >
```

### Bước 6: Chạy Node 2 (Window 4)

```
python node_process.py 2 3
```

Chờ:
```
[Node 2] >
```

---

## 🎮 TƯƠNG TÁC

Khi tất cả 4 windows đã ready, bạn sẽ thấy prompts như:

```
[Node 0] >
[Node 1] >
[Node 2] >
```

Bây giờ bạn có thể gõ commands:

### Test 1: Sequential Request

**Window 2 (Node 0):**
```
[Node 0] > request
```

Chờ 3 giây để Node 0 thoát CS. Sau đó:

**Window 3 (Node 1):**
```
[Node 1] > request
```

Chờ 3 giây:

**Window 4 (Node 2):**
```
[Node 2] > request
```

**Kỳ vọng:**
```
✅ Chỉ 1 node vào CS một lúc
✅ Thứ tự: Node 0 → Node 1 → Node 2
```

---

### Test 2: Concurrent Requests

Gõ nhanh tuần tự (không chờ):

**Window 2:**
```
[Node 0] > request
```

**Window 3:**
```
[Node 1] > request
```

**Window 4:**
```
[Node 2] > request
```

**Watch Coordinator Window:**
```
[Coordinator] Node 0 registered
[Coordinator] Node 1 registered
[Coordinator] Node 2 registered
```

**Kỳ vọng:**
```
✅ Node 0 enters CS first (ts=1)
✅ Node 1 waits (ts=2)
✅ Node 2 waits (ts=3)
✅ After Node 0 exits → Node 1 enters
✅ After Node 1 exits → Node 2 enters
```

---

### Test 3: Multiple Rounds

**Window 2:**
```
[Node 0] > request
[Node 0] > (chờ 3s)
[Node 0] > request
```

**Window 3 (same time):**
```
[Node 1] > request
```

**Kỳ vọng:**
```
✅ Mutual exclusion maintained
✅ FIFO fairness
```

---

## 📊 OUTPUT EXAMPLES

### Coordinator Window:
```
[Coordinator] Started on localhost:5000
[Coordinator] Waiting for nodes to register...

[Coordinator] Node 0 registered (listening: localhost:6000)
[Coordinator] Node 1 registered (listening: localhost:6001)
[Coordinator] Node 2 registered (listening: localhost:6002)
```

### Node 0 Window (Request):
```
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

### Node 1 Window (Receives Request):
```
[Node 1] > 
[Node 1] Received REQUEST from Node 0 (ts=1)
[Node 1] Sent REPLY immediately to Node 0
```

---

## ✋ THOÁT NODE

Trên bất kỳ Node window nào, gõ:
```
[Node X] > quit
[Node X] Shutting down...
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| **"Connection refused"** | Coordinator chưa start. Start Coordinator trước! |
| **"Address already in use"** | Ports đang dùng. Restart hoặc đợi 30s |
| **Nodes don't connect** | Chờ 2-3s sau khi start Coordinator |
| **No output** | Kiểm tra Python đã cài không: `python --version` |
| **"Module not found"** | Chạy từ folder `ricart_agrawala` |

---

## 🔹 LINUX / MAC

Mở 4 Terminal tabs:

```bash
# Terminal 1
cd ricart_agrawala
python3 coordinator.py

# Terminal 2
cd ricart_agrawala
python3 node_process.py 0 3

# Terminal 3
cd ricart_agrawala
python3 node_process.py 1 3

# Terminal 4
cd ricart_agrawala
python3 node_process.py 2 3
```

Rồi tương tác như Windows (gõ `request` hoặc `quit`).

---

## 📱 WINDOWS QUICK (Nếu muốn auto-start)

Gõ 1 lệnh thay vì 4:

```
start_demo.bat
```

Sẽ tự động mở 4 cmd windows.

---

## 🎯 COMMANDS

**Trên Node prompts:**

| Command | Ý nghĩa |
|---------|---------|
| `request` | Request vào Critical Section |
| `quit` | Thoát node |

---

## 📈 DEMO FLOW

```
1. Start Coordinator    → port 5000
                         ↓
2. Start Node 0, 1, 2    → register to Coordinator
                         ↓
3. User types "request"  → Node sends REQUEST to others
                         ↓
4. Others receive & reply → Depends on state
                         ↓
5. Node gets all RRPLYs  → Enters CS
                         ↓
6. Execute (2 giây)      → Thực thi công việc
                         ↓
7. Exit CS & send REPLY  → Cho pending requests
                         ↓
8. Ready for next request → Quay lại prompt
```

---

## ✨ KEY POINTS

✅ **Coordinator phải start trước** - nó là "registry server"  
✅ **Nodes register tự động** - khi kết nối  
✅ **Giao tiếp trực tiếp** - nodes talk P2P via TCP  
✅ **Interactive** - bạn kiểm soát khi nào request  
✅ **Clear logs** - thấy rõ REQUEST/REPLY/CS flow  

---

## 🎬 QUICK DEMO (Chỉ 1 phút)

```bash
# Terminal 1
python coordinator.py

# Terminal 2-4 (sau 2s)
python node_process.py 0 3
python node_process.py 1 3
python node_process.py 2 3

# Sau đó (trên Node 0): request
# Chờ 3s
# Sau đó (trên Node 1): request
# Chờ 3s
# (Node 2): request
```

**Kết quả:** Bạn sẽ thấy mutual exclusion hoạt động! ✅

---

**Ready? Mở 4 terminals và bắt đầu!** 🚀
