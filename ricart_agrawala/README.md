## 🔄 Ricart-Agrawala Algorithm - Distributed Mutual Exclusion

Triển khai thuật toán **Ricart-Agrawala** - một thuật toán phân tán để điều phối truy cập vào **Critical Section** mà không cần coordinator tập trung.

### 📁 Cấu trúc Module

```
ricart_agrawala/
├── __init__.py           # Package initialization
├── message.py            # Cấu trúc gói tin REQUEST/REPLY
├── node.py              # Triển khai Node và NodeManager
├── main.py              # Menu tương tác (chạy demos)
├── example.py           # 5 scenarios ví dụ
├── demo.py              # Quick demo đơn giản
└── README.md            # Tài liệu này
```

### 🎯 Cách sử dụng

#### 1️⃣ **Quick Demo** (Chạy nhanh)
```bash
python demo.py
```
Chạy 1 scenario đơn giản với 4 nodes.

#### 2️⃣ **Interactive Menu** (Menu tương tác)
```bash
python main.py
```
Menu cho phép chọn:
- Demo cơ bản (3 nodes)
- Demo trung bình (5 nodes) 
- Demo lớn (10 nodes)
- Demo tự định nghĩa (tuỳ chọn số nodes và scenario)

#### 3️⃣ **Examples** (Các ví dụ chi tiết)
```bash
python example.py
```
5 ví dụ minh họa khác nhau:
1. **Sequential Requests** - 3 nodes yêu cầu tuần tự
2. **Concurrent Requests** - 4 nodes yêu cầu cùng lúc (contention)
3. **Multiple Requests** - 5 nodes, mỗi node request 2 lần
4. **High Load** - 8 nodes, 16 requests (stress test)
5. **Starvation Prevention** - Kiểm tra không có node nào bị từ chối dài hạn

### 🔑 Khái niệm Chính

#### Ricart-Agrawala Algorithm:

**Mục tiêu:** Đơn giản hóa vấn đề mutual exclusion trong hệ thống phân tán mà không cần 1 coordinator tập trung.

**Cơ chế:**

1. **Logical Clock:** Mỗi node duy trì 1 đồng hồ logic (Lamport clock) 
   - Tăng khi gửi/nhận message
   - Dùng để so sánh thứ tự các request

2. **REQUEST:** Khi cần vào CS, node gửi REQUEST tới **tất cả** node khác với timestamp hiện tại

3. **REPLY:** Node nhận REQUEST sẽ:
   - **REPLY ngay** nếu:
     - Nó không cần vào CS, **hoặc**
     - Request mới có timestamp cũ hơn request của chính nó
   - **Delay** nếu nó đang vào CS hoặc có request cũ hơn chờ xử lý

4. **CS Entry:** Node chỉ vào CS khi nhận **REPLY từ tất cả** node khác

5. **CS Exit & Release:**
   - Thoát CS
   - Gửi REPLY cho tất cả pending requests trong queue
   - Request tiếp theo được xử lý

### 📊 So sánh Thuật toán

| Tiêu chí | Ricart-Agrawala | Centralized |
|---------|-----------------|------------|
| **Architecture** | Phân tán, P2P | Tập trung (Coordinator) |
| **Messages/Request** | O(2n-2): n-1 REQUESTs + n-1 REPLYs | O(3): REQUEST + GRANT + RELEASE |
| **Availability** | Cao (không single point of failure) | Thấp (phụ thuộc Coordinator) |
| **Complexity** | Cao (logical clocks, queues) | Thấp |
| **Starvation** | Không (FIFO timestamp ordering) | Có thể xảy ra |

### 💡 Output Demo Là Gì?

Khi chạy, bạn sẽ thấy:

```
============================================================
Ricart-Agrawala Demo: 4 nodes
============================================================

[Node 0] Gửi REQUEST (ts=1)
[Node 1] Gửi REQUEST (ts=2)
[Node 2] Gửi REQUEST (ts=3)
[Node 3] Gửi REQUEST (ts=4)
[Node 0] Gửi REPLY ngay tới Node 1
[Node 0] Gửi REPLY ngay tới Node 2
[Node 0] Gửi REPLY ngay tới Node 3
[Node 1] Gửi REPLY ngay tới Node 2
[Node 1] Gửi REPLY ngay tới Node 3
[Node 2] Gửi REPLY ngay tới Node 3

[Node 0] >>> ĐÃ NHẬN ĐỦ REPLY - ENTER CS (ts=1)
[Node 0] <<< EXIT CS
[Node 0] Gửi REPLY tới Node 1

[Node 1] >>> ĐÃ NHẬN ĐỦ REPLY - ENTER CS (ts=2)
[Node 1] <<< EXIT CS
[Node 1] Gửi REPLY tới Node 2
...
```

**Giải thích:**
- Mỗi node in ra khi gửi/nhận message
- `>>>` = Enter CS (Critical Section)
- `<<<` = Exit CS
- Timestamps được so sánh để quyết định REPLY

### 🔒 Đảm Bảo Mutual Exclusion

✅ **Chỉ 1 node vào CS một lúc:**
- Một node vào CS chỉ khi nhận REPLY từ **tất cả** node khác
- Trong khi một node trong CS, các node khác chờ REPLY

✅ **Không deadlock:**
- Logical clock ordering đảm bảo có thứ tự

✅ **Không starvation:**
- FIFO queue của timestamp đảm bảo tất cả request được xử lý

### 🧪 Test Cases

Mỗi example test một khía cạnh khác:

1. **Sequential** → Kiểm tra thứ tự đơn giản
2. **Contention** → Nhiều nodes cạnh tranh resource
3. **Multiple Rounds** → Repeated access
4. **Stress** → Load cao, độ tin cậy
5. **Fairness** → Không có unfairness hay starvation

### 📝 Chi tiết Implementation

#### Node Class:
```python
class Node:
    def __init__(self, node_id, all_nodes):
        self.logical_clock      # Đồng hồ logic (Lamport)
        self.request_queue      # Queue của (node_id, timestamp) chờ xử lý
        self.waiting_for_replies # Set của node IDs chờ REPLY
        self.in_cs             # Boolean: đang trong CS?
        
    def enter_cs()          # Gửi REQUEST, chờ REPLY từ tất cả
    def exit_cs()           # Thoát CS, gửi REPLY cho queue
    def receive_request()   # Nhận REQUEST, quyết định REPLY
    def receive_reply()     # Nhận REPLY, check xem có thể vào CS chưa
```

#### NodeManager Class:
```python
class NodeManager:
    def __init__(num_nodes)         # Tạo n nodes
    def run_scenario(request_seq)   # Chạy với chuỗi request tuỳ chỉnh
    def run_random_scenario(n_req)  # Chạy với n request ngẫu nhiên
```

### ⚠️ Lưu ý

- **Logical Clock:** Tăng mỗi khi gửi/nhận message (Lamport timestamp)
- **Thread Safety:** Dùng `threading.Lock` và `Condition` để đồng bộ hóa
- **CS Work Time:** Mặc định 2 giây (có thể thay đổi ở `node.py`)
- **Ordering:** Timestamp nhỏ hơn được xử lý trước (FIFO fairness)

### 🚀 Tối ưu hóa Có thể Làm

1. **Chang-Roberts optimization:** Giảm số message từ O(2n-2) → O(n-1)
2. **Token passing:** Thêm token để tránh broadcaster pattern
3. **Adaptive retry:** Backoff exponential nếu contention cao
4. **Rate limiting:** Giới hạn request rate để tránh thundering herd

### ✨ Đặc điểm Chính

✅ **Hoàn toàn phân tán** - Không cần máy chủ tập trung  
✅ **Symmetric** - Tất cả nodes có vai trò như nhau  
✅ **Fairness** - FIFO ordering theo timestamp  
✅ **Liveness** - Không deadlock, không starvation  
✅ **Safety** - Mutual exclusion được đảm bảo  

---

**Happy Distributed Computing!** 🎉
