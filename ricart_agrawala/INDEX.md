## 📁 Ricart-Agrawala Distributed Mutual Exclusion - Complete Implementation

### 🎯 Tổng Quan

Đây là **triển khai hoàn chỉnh Ricart-Agrawala Algorithm** - một thuật toán phân tán để điều phối truy cập vào Critical Section **mà không cần coordinator tập trung**.

Có **2 cách demo**:
1. **Simulation Mode** (tất cả trong 1 process)
2. **Network Mode** (mỗi node là 1 process, giao tiếp qua TCP) ⭐ **RECOMMENDED**

---

## 📂 File Structure

```
ricart_agrawala/
├── NETWORK COMMUNICATION (New - Multi-Process)
│   ├── coordinator.py              ← Server quản lý node registration
│   ├── node_process.py             ← Node client độc lập (chạy 4 lần)
│   ├── start_demo.bat              ← Auto start script (Windows)
│   ├── start_demo.sh               ← Auto start script (Linux/Mac)
│   ├── WINDOWS_HOWTO.md            ← Hướng dẫn chi tiết (Windows)
│   └── MULTI_PROCESS_DEMO.md       ← Tài liệu đầy đủ (Multi-Process)
│
├── SIMULATION MODE (Old - In-Process)
│   ├── node.py                     ← Node class & NodeManager
│   ├── message.py                  ← Message structures
│   ├── main.py                     ← Interactive menu
│   ├── example.py                  ← 5 scenarios
│   ├── demo.py                     ← Quick demo
│   └── README.md                   ← Documentation (Simulation)
│
├── UTILITIES
│   ├── __init__.py
│   ├── QUICKSTART.py               ← Quick start visual guide
│   └── run_demo.bat/ps1            ← Old scripts
```

---

## 🚀 QUICK START

### ⭐ **Cách Demo Mới (Network Mode - Recommended)**

**Windows - 1 lệnh:**
```bash
cd f:\BTL_HTPT-Git\distributed-mutual-exclusion\ricart_agrawala
start_demo.bat
```

**Linux/Mac:**
```bash
cd ricart_agrawala
chmod +x start_demo.sh
./start_demo.sh
```

**Manual (4 terminals):**
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

**Tương tác:**
- Trên mỗi Node terminal, gõ: `request` hoặc `quit`

---

### 🔹 **Cách Demo Cũ (Simulation Mode)**

```bash
# Quick demo
python demo.py

# Interactive menu
python main.py

# Examples
python example.py
```

---

## 📖 Documentation

| Mode | File | Chi tiết |
|------|------|---------|
| **Network** | `WINDOWS_HOWTO.md` | 👈 **Start here (Windows)** |
| **Network** | `MULTI_PROCESS_DEMO.md` | Chi tiết đầy đủ (dành cho tất cả OS) |
| **Simulation** | `README.md` | Cách simulation mode chạy |
| **Quick Ref** | `QUICKSTART.py` | Visual guide |

---

## 🎯 Chọn Cách Demo Nào?

### 🟢 **Use Network Mode (coordinator.py + node_process.py)** Nếu:
- ✅ Muốn thấy **distributed system thực tế**
- ✅ Muốn **kiểm soát timing** (gõ request khi muốn)
- ✅ Muốn **debug** bằng cách xem 4 terminals
- ✅ Muốn scale tới > 3 nodes dễ dàng
- ✅ Đang trên **Windows** (dễ chạy `start_demo.bat`)

### 🔵 **Use Simulation Mode (main.py / example.py)** Nếu:
- ✅ Muốn **ngay lập tức** xem demo
- ✅ Muốn **auto pre-configured scenarios**
- ✅ Không cần **interactive control**
- ✅ Chỉ để **reference** algorithm logic

---

## 🔑 Algorithm Concepts

### Ricart-Agrawala Protocol:

1. **When node needs CS:**
   - Send REQUEST to all other nodes (with timestamp)
   
2. **When node receives REQUEST:**
   - If node NOT in CS and (doesn't need CS OR incoming request has higher priority):
     - Send REPLY immediately
   - Else:
     - Add to queue, defer REPLY

3. **When node has all REPLYs:**
   - Enter CS
   
4. **When node exits CS:**
   - Send REPLY to all deferred requests

### Guarantees:
✅ **Mutual Exclusion** - Only 1 node in CS  
✅ **No Starvation** - FIFO ordering by timestamp  
✅ **Deadlock-free** - Logical clock ordering  
✅ **Decentralized** - No single point of failure  

---

## 💬 Output Examples

### Network Mode (coordinator.py):
```
[Coordinator] Started on localhost:5000
[Coordinator] Node 0 registered (listening: localhost:6000)
[Coordinator] Node 1 registered (listening: localhost:6001)
[Coordinator] Node 2 registered (listening: localhost:6002)
```

### Network Mode (node_process.py):
```
[Node 0] >>> REQUESTING (ts=1)
[Node 0] Sent REQUEST to Node 1
[Node 0] Sent REQUEST to Node 2
[Node 0] Received REPLY from Node 1 (1/2)
[Node 0] Received REPLY from Node 2 (2/2)
[Node 0] ✓ RECEIVED ALL REPLIES - ENTERING CS (ts=1)
[Node 0] ✗ EXITING CS
[Node 0] Sent REPLY to Node 1
[Node 0] Sent REPLY to Node 2
```

### Simulation Mode (main.py):
```
[Node 0] Gửi REQUEST (ts=1)
[Node 1] Gửi REQUEST (ts=2)
[Node 0] >>> ĐÃ NHẬN ĐỦ REPLY - ENTER CS (ts=1)
[Node 0] <<< EXIT CS
[Node 1] >>> ĐÃ NHẬN ĐỦ REPLY - ENTER CS (ts=2)
```

---

## 🧪 Test Scenarios

### Scenario 1: Sequential
```
Node 0: request  → (finishes)
Node 1: request  → (finishes)
Node 2: request  → (finishes)
```
✅ **Result:** Mutual Exclusion verified

### Scenario 2: Concurrent (Contention)
```
Node 0: request (ts=1)
Node 1: request (ts=2)  
Node 2: request (ts=3)
```
✅ **Result:** FIFO ordering: 0→1→2

### Scenario 3: Multiple Rounds
```
Node 0: request › exit › request
Node 1: request (concurrent)
```
✅ **Result:** Fairness maintained

---

## ⚙️ Architecture Comparison

| Aspect | Network Mode | Simulation Mode |
|--------|-------------|-----------------|
| **Process Count** | 4 (Coordinator + 3 nodes) | 1 (all in main) |
| **Communication** | TCP sockets | Function calls |
| **Realism** | High (actual distributed) | Low (simulation) |
| **Interaction** | Interactive CLI | Menu/auto |
| **Scalability** | Unlimited | Limited (threads) |
| **Latency** | ~2-5ms | 0ms |
| **Debuggability** | 4 separate consoles | 1 console |

---

## 🔌 Ports Used (Network Mode)

```
Coordinator:  localhost:5000
Node 0:       localhost:6000
Node 1:       localhost:6001
Node 2:       localhost:6002
```

To add more nodes, use `python node_process.py N total_nodes` with next available port.

---

## 📋 Implementation Statistics

- **Total Lines:** ~600 (excluding docs)
- **Main Classes:**
  - `Coordinator` - Registration server
  - `NodeProcess` - Network-based node
  - `Node` / `NodeManager` - In-process simulation
- **Message Types:** REQUEST, REPLY (JSON over TCP)
- **Synchronization:** threading.Lock, Condition
- **Logical Clock:** Lamport timestamps

---

## ✨ Key Features

✅ **Fully distributed** - P2P architecture  
✅ **Symmetric** - All nodes are peers  
✅ **Fair** - FIFO ordering, no starvation  
✅ **Safe** - Mutual exclusion guaranteed  
✅ **Live** - No deadlocks  
✅ **Scalable** - Add nodes easily  
✅ **Debuggable** - Clear logging  
✅ **Well-documented** - This guide + code comments  

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Address already in use"** | Ports taken. Restart / wait 30s |
| **"Connection refused"** | Start Coordinator first, wait 2s |
| **"Module not found"** | Run from ricart_agrawala folder |
| **No output** | Check terminal console (scroll up) |
| **Nodes don't register** | Verify Coordinator is running on port 5000 |

---

## 🎓 For Learning

Recommended reading order:

1. `WINDOWS_HOWTO.md` → Quick run
2. Run the demo → See it work  
3. `node_process.py` → Study network communication
4. `coordinator.py` → Study node management
5. Watch timestamp ordering → Understand Ricart-Agrawala
6. `MULTI_PROCESS_DEMO.md` → Advanced topics

---

## 📊 Comparison with Other Algorithms

| Algorithm | Centralized | Ricart-Agrawala | Token Ring |
|-----------|------------|-----------------|-----------|
| **Messages/req** | 3 | 2(n-1) | n |
| **Synchronizer** | Coordinator | Clocks | Token |
| **Fault tolerance** | No | Yes | Weak |
| **Complexity** | Simple | Moderate | Moderate |

---

**Happy Distributed Computing!** 🎉

For detailed instructions: 
- **Windows:** Read `WINDOWS_HOWTO.md`
- **All OS:** Read `MULTI_PROCESS_DEMO.md`
