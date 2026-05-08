# 🔐 Ricart-Agrawala – Giải thuật Loại trừ Tương hỗ Phân tán

Mô phỏng giải thuật **Ricart-Agrawala** cho bài toán **Mutual Exclusion** (loại trừ tương hỗ) trong hệ thống phân tán, sử dụng **Lamport Clock** để sắp thứ tự các sự kiện.

---

## 📋 Mục lục

- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu trúc project](#-cấu-trúc-project)
- [Cách chạy](#-cách-chạy)
- [Giải thích thuật toán](#-giải-thích-thuật-toán)
- [Xử lý lỗi thường gặp](#-xử-lý-lỗi-thường-gặp)

---

## ⚙️ Yêu cầu hệ thống

| Yêu cầu       | Phiên bản tối thiểu |
|---------------|---------------------|
| Python        | 3.8 trở lên         |
| Hệ điều hành  | Windows / Linux / macOS |

> **Không cần cài thêm thư viện nào!** Project chỉ dùng thư viện chuẩn của Python (`socket`, `threading`, `json`, ...).

---

## 📥 Cài đặt

### 1. Clone repository (nếu chưa có)

```bash
git clone <url-repository>
cd ricart_agrawala
```

### 2. Kiểm tra Python

```bash
python --version
```

Đảm bảo phiên bản >= 3.8.

---

## 📁 Cấu trúc project

```
ricart_agrawala/
│
├── test/
│   └── run_node.py    ← ⭐ File chạy chính của project
│
├── node.py        # Cài đặt node cho main.py (không dùng trực tiếp)
├── main.py        # Entry point thay thế (không dùng)
├── network.py     # Tầng mạng TCP
├── message.py     # Cấu trúc tin nhắn JSON
├── lamport.py     # Đồng hồ Lamport
├── logger.py      # Module in log
├── config.py      # Cấu hình node
└── shared.txt     # File tài nguyên chia sẻ
```

---

## 🚀 Cách chạy

Project mô phỏng **N node** chạy đồng thời trên máy tính cục bộ. Mỗi node cần **một cửa sổ terminal riêng**.

### Cú pháp lệnh

```bash
python test/run_node.py <node_id> <total_nodes>
```

| Tham số        | Ý nghĩa                                    |
|----------------|--------------------------------------------|
| `node_id`      | ID của node này, bắt đầu từ `0`            |
| `total_nodes`  | Tổng số node trong hệ thống (mặc định: 3) |

---

### Ví dụ: Chạy 3 node

Mở **3 cửa sổ terminal** riêng biệt, tất cả đều `cd` vào thư mục gốc của project:

```bash
cd đường-dẫn-tới-thư-mục\ricart_agrawala
```

**Terminal 1 – Node 0:**
```bash
python test/run_node.py 0 3
```

**Terminal 2 – Node 1:**
```bash
python test/run_node.py 1 3
```

**Terminal 3 – Node 2:**
```bash
python test/run_node.py 2 3
```

> **⚠️ Lưu ý:** Khởi động cả 3 node trước khi gõ lệnh `r`, vì các node cần kết nối được với nhau.

Sau khi khởi động thành công, mỗi terminal hiển thị banner như sau:

```
  ══════════════════════════════════════════════════════
  Ricart-Agrawala Mutual Exclusion  (TCP Sockets)
  Node ID : 0   |   Tổng số nodes : 3
  Port    : localhost:5000
  ──────────────────────────────────────────────────────
  r + Enter  →  Request Critical Section
  q + Enter  →  Quit
  ══════════════════════════════════════════════════════
```

---

### Thao tác điều khiển

Sau khi tất cả node đã chạy, gõ lệnh vào từng terminal:

| Lệnh | Chức năng |
|------|-----------|
| `r` + Enter | Yêu cầu vào Critical Section (CS) |
| `q` + Enter | Thoát node |

> **Thử nghiệm:** Gõ `r` ở nhiều node **gần như cùng lúc** để quan sát cơ chế loại trừ tương hỗ — chỉ **một node duy nhất** được vào CS tại một thời điểm.

---

### Chạy với số node khác (tuỳ chọn)

Bạn có thể mô phỏng với **nhiều hơn 3 node**, ví dụ 5 node:

```bash
python test/run_node.py 0 5
python test/run_node.py 1 5
python test/run_node.py 2 5
python test/run_node.py 3 5
python test/run_node.py 4 5
```

Các node sẽ lắng nghe trên các cổng tăng dần từ `5000`:

| Node ID | Port     |
|---------|----------|
| 0       | 5000     |
| 1       | 5001     |
| 2       | 5002     |
| ...     | ...      |
| N       | 5000 + N |

---

## 🧠 Giải thích thuật toán

**Ricart-Agrawala** là thuật toán loại trừ tương hỗ phân tán:

1. **Node muốn vào CS** → chuyển sang trạng thái `WANTED`, gửi `REQUEST(timestamp, id)` đến tất cả node khác.
2. **Node nhận REQUEST** → quyết định trả lời ngay hay hoãn lại:
   - Đang `HELD` (trong CS) → **hoãn REPLY**
   - Đang `WANTED` và có ưu tiên cao hơn (timestamp nhỏ hơn) → **hoãn REPLY**
   - Ngược lại → **REPLY ngay**
3. **Node yêu cầu** nhận đủ `(N-1)` REPLY → chuyển sang `HELD`, vào CS.
4. **Sau khi ra CS** → chuyển về `RELEASED`, gửi REPLY cho tất cả node bị hoãn (deferred queue).

### Sơ đồ trạng thái

```
         r (gửi REQUEST)
RELEASED ──────────────► WANTED
    ▲                      │
    │                      │ nhận đủ (N-1) REPLY
    │                      ▼
    └──────────────── HELD (trong CS)
       thoát CS
       (gửi deferred REPLY)
```

### Sơ đồ giao tiếp (3 node)

```
Node-0         Node-1         Node-2
  │──REQUEST──►  │               │
  │──REQUEST─────────────────►   │
  │               │◄──REQUEST──  │   ← Node-2 cũng muốn vào CS
  │◄──REPLY───   │               │
  │               │           (DEFER)  ← Node-2 hoãn vì Node-0 có ts nhỏ hơn
  │          [ENTER CS]            │
  │          [EXIT CS]             │
  │──deferred REPLY──────────►   │
  │                          [ENTER CS]
```

---

## 🐛 Xử lý lỗi thường gặp

### ❌ `✗ Không thể bind cổng 5000: ...`

Port đang bị chiếm bởi tiến trình cũ. Giải pháp:

**Windows (PowerShell):**
```powershell
# Tìm PID đang dùng port 5000
netstat -ano | findstr :5000
# Kết thúc tiến trình (thay <PID> bằng số thực)
taskkill /PID <PID> /F
```

**Linux / macOS:**
```bash
lsof -ti:5000 | xargs kill -9
```

### ❌ Node không nhận được REPLY

- Đảm bảo **tất cả N node đã khởi động** trước khi gõ `r`.
- Kiểm tra `total_nodes` truyền vào phải **giống nhau** trên tất cả terminal.
- Kiểm tra firewall không chặn các port từ `5000` đến `5000 + N - 1`.

### ❌ `node_id phải trong khoảng [0, N-1]`

`node_id` phải bắt đầu từ **0**, không phải 1. Ví dụ với 3 node thì ID hợp lệ là `0`, `1`, `2`.

---

## 👥 Tác giả

Đây là project mô phỏng thuật toán **Ricart-Agrawala** phục vụ mục đích học tập môn **Hệ thống phân tán**.
