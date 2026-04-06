## 🚀 Multi-Process Demo - Ricart-Agrawala with Network Communication

Đây là cách chạy Ricart-Agrawala với **mỗi node là 1 process riêng biệt** giao tiếp qua **TCP network**.

### 📋 Cách Chạy

#### **Windows (Cách dễ nhất)**

```bash
start_demo.bat
```

Lệnh này sẽ tự động mở **4 terminal cửa sổ**:
- 1 Coordinator (quản lý nodes)
- 3 Node clients (Node 0, 1, 2)

#### **Linux/Mac**

```bash
chmod +x start_demo.sh
./start_demo.sh
```

Hoặc mở 4 terminal riêng và chạy từng cái:

```bash
# Terminal 1: Coordinator
python coordinator.py

# Terminal 2: Node 0
python node_process.py 0 3

# Terminal 3: Node 1
python node_process.py 1 3

# Terminal 4: Node 2
python node_process.py 2 3
```

### 🎮 Sử Dụng

Mỗi Node terminal sẽ hiển thị:
```
[Node 0] > request
```

Bạn có thể gõ:
- `request` → Node request vào Critical Section
- `quit` → Thoát node

### 💬 Output Ví Dụ

**Terminal Coordinator:**
```
[Coordinator] Started on localhost:5000
[Coordinator] Waiting for nodes to connect...

[Coordinator] Node 0 registered (listening: localhost:6000)
[Coordinator] Node 1 registered (listening: localhost:6001)
[Coordinator] Node 2 registered (listening: localhost:6002)
```

**Terminal Node 0:**
```
[Node 0] Starting...
[Node 0] Listening on port 6000
[Node 0] Connected to Coordinator
[Node 0] Other nodes: {1: ('localhost', 6001), 2: ('localhost', 6002)}
[Node 0] Ready for commands
[Node 0] Type 'request' or 'quit'

[Node 0] > request

[Node 0] >>> REQUESTING (ts=1)
[Node 0] Received REPLY from Node 1 (1/2)
[Node 0] Received REPLY from Node 2 (2/2)
[Node 0] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts=1)
... (thực thi 2 giây) ...
[Node 0] ✗ EXITING CS
[Node 0] Sent REPLY to Node 1
[Node 0] Sent REPLY to Node 2

[Node 0] >
```

**Terminal Node 1 (khi Node 0 request, Node 1 reply):**
```
[Node 1] > 
[Node 1] Received REQUEST from Node 0 (ts=1)
[Node 1] Sent REPLY immediately to Node 0
```

### 🔄 Workflow

1. **Node sends REQUEST** → Tất cả nodes khác nhận REQUEST
2. **Other nodes decide** → REPLY ngay hoặc delay (nếu trong CS hoặc có older request)
3. **When all REPLYs received** → Node enters CS
4. **In CS** → Thực thi 2 giây
5. **Gửi REPLY** → Cho pending requests trong queue
6. **Repeat** → Hoặc `quit`

### 🔑 Khái Niệm

**Coordinator Server:**
- Lắng nghe port 5000
- Xác nhận nodes register
- Forward messages giữa nodes (optional, các nodes có thể giao tiếp trực tiếp)

**Node Process:**
- Lắng nghe port 6000+node_id
- Duy trì logical clock
- Gửi REQUEST khi user type "request"
- Gửi REPLY dựa trên Ricart-Agrawala rules
- Interactive CLI chấp nhận commands

### ⚙️ Port Allocation

```
Coordinator: localhost:5000
Node 0:      localhost:6000
Node 1:      localhost:6001
Node 2:      localhost:6002
```

Để chạy > 3 nodes, chỉ cần:
```bash
python node_process.py 0 5  # Node 0 của 5 nodes
python node_process.py 1 5  # Node 1 của 5 nodes
...
python node_process.py 4 5  # Node 4 của 5 nodes
```

### 🧪 Ví Dụ Test Scenario

**Scenario 1: Sequential Access**
```
Terminal Node 0: request     # → Enter CS, Exit
Terminal Node 1: request     # → Wait → Enter CS, Exit
Terminal Node 2: request     # → Wait → Enter CS, Exit
```

**Scenario 2: Concurrent Requests (Contention)**
```
Terminal Node 0: request     # ts=1
Terminal Node 1: request     # ts=2 (request tới Node 0)
Terminal Node 2: request     # ts=3 (request tới Node 0, 1)
                            # → Node 0 enters (ts=1)
                            # → Node 0 exits → sends REPLY
                            # → Node 1 enters (ts=2)
                            # → Node 1 exits → sends REPLY
                            # → Node 2 enters (ts=3)
```

**Scenario 3: Multiple Requests**
```
Terminal Node 0: request     # Round 1
wait 3 seconds...
Terminal Node 0: request     # Round 2
Terminal Node 1: request     # Concurrent
```

### 🐛 Debugging

Nếu nodes không kết nối:
1. Đảm bảo **Coordinator start trước**
2. Chờ 2 giây trước bắt đầu nodes
3. Kiểm tra firewall (Windows)
4. Đảm bảo Python có `socket` module (built-in)

### 📊 So Sánh với Cách Demo Cũ

| Khía Cạnh | Demo Cũ (Simulation) | Demo Mới (Network) |
|-----------|---------------------|-------------------|
| **Process** | 1 process (threads) | 4 processes (3 nodes + 1 coordinator) |
| **Communication** | Direct function calls | TCP sockets over network |
| **Realism** | Simulation | Distributed system thực |
| **Scalability** | Hạn chế (all in 1 process) | Không hạn chế |
| **Demo Style** | Menu/auto | Interactive CLI |
| **Network Delay** | Không | Mô phỏng (2-3ms) |

### ✨ Lợi Ích Cách Mới

✅ **Thực tế hơn** - Giống distributed system thật  
✅ **Tách biệt rõ** - Mỗi node độc lập  
✅ **Interactive** - Kiểm soát timing theo ý muốn  
✅ **Dễ debug** - Mỗi terminal riêng, easy to follow  
✅ **Scalable** - Easy add thêm nodes  

---

**Thử ngay:** `start_demo.bat` (Windows) hoặc `./start_demo.sh` (Linux/Mac)! 🎉
