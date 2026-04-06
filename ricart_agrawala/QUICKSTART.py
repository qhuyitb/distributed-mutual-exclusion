"""
Quick Start Guide for Multi-Process Demo
Hướng dẫn nhanh để chạy demo
"""

print("""
╔══════════════════════════════════════════════════════════════════╗
║     RICART-AGRAWALA DISTRIBUTED MUTUAL EXCLUSION DEMO            ║
║              Multi-Process with Network Communication             ║
╚══════════════════════════════════════════════════════════════════╝

📖 HƯỚNG DẪN CHẠY DEMO
═════════════════════════════════════════════════════════════════


🔹 BƯỚC 1: CHO CHẮC PYTHON ĐÃ CÀI
──────────────────────────────────

Windows:     python --version
Linux/Mac:   python3 --version

Nếu chưa cài, tải từ: https://www.python.org/downloads/


🔹 BƯỚC 2: CHẠY DEMO
──────────────────

▮ Windows (Cách dễ nhất):
  1. Mở Windows PowerShell hoặc Command Prompt
  2. Chạy:
     
     start_demo.bat
  
  3. Sẽ mở 4 cửa sổ Terminal tự động


▮ Linux/Mac:
  1. Mở Terminal
  2. Chạy:
     
     chmod +x start_demo.sh
     ./start_demo.sh
  
  3. Hoặc mở 4 terminal riêng:
     - Terminal 1: python coordinator.py
     - Terminal 2: python node_process.py 0 3
     - Terminal 3: python node_process.py 1 3
     - Terminal 4: python node_process.py 2 3


🔹 BƯỚC 3: TƯƠNG TÁC VỚI NODES
───────────────────────────────

Mỗi Node terminal sẽ hiển thị prompt:

    [Node 0] > _

Gõ:
  - request    :  Node request vào Critical Section
  - quit       :  Thoát node


📊 EXPECTED OUTPUT
═════════════════════════════════════════════════════════════════

▮ Coordinator Terminal:
┌─────────────────────────────────────────┐
│ [Coordinator] Started on localhost:5000 │
│ [Coordinator] Waiting for nodes...      │
│ [Coordinator] Node 0 registered         │
│ [Coordinator] Node 1 registered         │
│ [Coordinator] Node 2 registered         │
└─────────────────────────────────────────┘

▮ Node 0 Terminal:
┌──────────────────────────────────┐
│ [Node 0] Starting...             │
│ [Node 0] Listening on port 6000  │
│ [Node 0] Connected to Coordinator│
│ [Node 0] Other nodes: {...}      │
│ [Node 0] Ready for commands      │
│                                  │
│ [Node 0] > request               │ ← User types
│ [Node 0] >>> REQUESTING (ts=1)   │
│ [Node 0] Received REPLY from ... │
│ [Node 0] ✓ ENTER CS (ts=1)       │
│ ... (chạy 2 giây) ...            │
│ [Node 0] ✗ EXIT CS               │
│ [Node 0] Sent REPLY to ...       │
│                                  │
│ [Node 0] > quit                  │ ← User types
│ [Node 0] Shutting down...        │
└──────────────────────────────────┘

▮ Node 1 Terminal (khi Node 0 request):
┌──────────────────────────────────┐
│ [Node 1] >                       │
│ [Node 1] Received REQUEST from 0 │
│ [Node 1] Sent REPLY immediately  │
└──────────────────────────────────┘


🧪 TEST SCENARIOS
═════════════════════════════════════════════════════════════════

▶ Scenario 1: Sequential Access (Tuần tự)
  Node 0: request → (finishes) → OK
  Node 1: request → (finishes) → OK  
  Node 2: request → (finishes) → OK


▶ Scenario 2: Concurrent Access (Cạnh tranh)
  Node 0: request  (at time 0)    ts=1
  Node 1: request  (immediately)  ts=2  (xếp hàng)
  Node 2: request  (immediately)  ts=3  (xếp hàng)
  
  Result: Node 0 → Node 1 → Node 2 (thứ tự FIFO)


▶ Scenario 3: Multiple Rounds (Nhiều lượt)
  Node 0: request  (Round 1)
  Node 0: request  (Round 2)
  Node 1: request  (in between)
  
  Result: FIFO fairness - không starvation


⚠️  TROUBLESHOOTING
═════════════════════════════════════════════════════════════════

X Problem: "Module not found" or "Import error"
  ✓ Solution: Đảm bảo chạy từ thư mục chứa .py files

X Problem: "Address already in use"
  ✓ Solution: Port đang dùng bởi process cũ
             Kill process hoặc đợi 30 giây rồi thử lại

X Problem: Nodes can't connect to Coordinator
  ✓ Solution: Chắc chắn chạy Coordinator trước
             Chờ 2-3 giây trước start nodes
             Check firewall (Windows)

X Problem: "Connection refused"
  ✓ Solution: Coordinator có thể bị crash
             Restart Coordinator
             Check python có chạy đúng không


🔌 PORTS USED
═════════════════════════════════════════════════════════════════

Coordinator:  localhost:5000
Node 0:       localhost:6000
Node 1:       localhost:6001
Node 2:       localhost:6002

(Để add thêm nodes, dùng port 6000+node_id)


📁 FILES
═════════════════════════════════════════════════════════════════

coordinator.py       - Server quản lý nodes
node_process.py      - Node client (independent process)
message.py           - Message structures
start_demo.bat       - Windows start script
start_demo.sh        - Linux/Mac start script
MULTI_PROCESS_DEMO.md - Chi tiết documentation


💡 TIPS
═════════════════════════════════════════════════════════════════

1. Open each Node terminal side-by-side để dễ theo dõi
2. Try multiple concurrent requests để thấy mutual exclusion
3. Try rapid requests để test fairness (FIFO ordering)
4. Kiểm tra timestamp - lower timestamp → enter CS trước


═════════════════════════════════════════════════════════════════
📖 Chi tiết: Xem MULTI_PROCESS_DEMO.md
═════════════════════════════════════════════════════════════════
""")
