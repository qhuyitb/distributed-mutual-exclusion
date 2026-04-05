# Hướng dẫn Cài đặt Thuật toán Token Ring

## Giới thiệu
Dự án này triển khai thuật toán **Token Ring** - một giải pháp cho bài toán **Mutual Exclusion** trong hệ thống phân tán. Token Ring đảm bảo chỉ có một node có thể truy cập tài nguyên chung tại một thời điểm.

## Yêu cầu Hệ thống
- Python 3.8 trở lên
- pip (Python package manager)
- Hệ điều hành: Windows, macOS, hoặc Linux

## Cấu trúc Dự án
```
token_ring/
├── src/
│   ├── message.py          # Định nghĩa cấu trúc gói tin
│   ├── node.py             # Lớp Node triển khai thuật toán Token Ring
│   ├── network.py          # Mô phỏng mạng và giao tiếp giữa các node
│   └── main.py             # Điểm khởi đầu của chương trình
├── tests/                  # Unit tests
├── docs/                   # Tài liệu chi tiết
└── INSTALLATION.md         # File này
```

## Các Bước Cài đặt

### 1. Clone hoặc Download Dự án
```bash
cd d:\Huy\Documents\HTPT\BTL\distributed-mutual-exclusion\token_ring
```

### 2. Tạo Virtual Environment (Tùy chọn nhưng khuyến nghị)
```bash
python -m venv venv
```

Kích hoạt Virtual Environment:
- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Cài đặt Dependencies
```bash
pip install -r requirements.txt
```

Nếu chưa có `requirements.txt`, cài đặt các package cần thiết:
```bash
pip install dataclasses-json
```

### 4. Chạy Chương trình
```bash
python src/main.py
```

### 5. Chạy Unit Tests
```bash
python -m pytest tests/
```

## Mô tả Quá trình Triển khai Token Ring

### Nguyên tắc Hoạt động
1. **Khởi tạo Token**: Một node được chọn làm node khởi đầu và giữ token
2. **Truyền Token**: Node hiện tại truyền token cho node tiếp theo trong vòng
3. **Kiểm soát Truy cập**: Chỉ node có token mới được phép truy cập tài nguyên chung
4. **Chu kỳ Lặp**: Token liên tục di chuyển trong vòng cho đến khi hệ thống dừng

### Các Thành phần Chính

#### 1. **Message (src/message.py)**
Định nghĩa các loại gói tin:
- `TOKEN`: Gói tin token di chuyển trong vòng
- `REQUEST`: Yêu cầu truy cập tài nguyên
- `REPLY`: Phản hồi từ node khác
- `DATA`: Dữ liệu thông thường
- `ACK`: Xác nhận

#### 2. **Node (src/node.py)**
Mỗi node:
- Có ID duy nhất trong hệ thống
- Giữ danh sách các node hàng xóm
- Xử lý nhận và gửi gói tin
- Quản lý trạng thái (có token hay không)
- Thực thi critical section khi có token

#### 3. **Network (src/network.py)**
Mô phỏng mạng:
- Quản lý kết nối giữa các node
- Gửi gói tin từ node này đến node khác
- Xử lý trễ mạng (nếu cần)

### Luồng Hoạt động

```
1. KHỞI TẠO
   └─ Tạo N node trong vòng (0 → 1 → 2 → ... → N-1 → 0)
   └─ Node 0 nhận token ban đầu

2. VÒNG LẶP CHÍNH
   ├─ Node có token thực thi critical section
   ├─ Node kiểm tra queue yêu cầu từ các node khác
   ├─ Node gửi token cho node tiếp theo
   └─ Lặp lại cho đến khi dừng

3. TRUYỀN TOKEN
   ├─ Node hiện tại (N) gửi token cho node tiếp theo (N+1)
   ├─ Node N+1 nhận token
   ├─ Node N+1 cập nhật trạng thái
   └─ Lặp lại

4. DỪNG HỆ THỐNG
   └─ Khi điều kiện kết thúc được đáp ứng
```

## Cấu hình Tham số

Trong `src/main.py` hoặc file cấu hình, bạn có thể điều chỉnh:
- Số lượng node: `num_nodes`
- Thời gian mỗi node giữ token: `hold_time`
- Trễ mạng mô phỏng: `network_delay`
- Số lần thử cập nhật token: `iterations`

## Ví dụ Sử dụng

```python
from src.network import Network

# Tạo mạng với 5 node
network = Network(num_nodes=5)

# Khởi chạy mô phỏng
network.run(iterations=10)

# In kết quả
network.print_stats()
```

## Xử lý Sự cố

### Lỗi: "ModuleNotFoundError"
**Giải pháp**: Đảm bảo rằng bạn đang chạy từ thư mục gốc của dự án và tất cả file Python nằm trong `src/`.

### Lỗi: "Port already in use"
**Giải pháp**: Nếu sử dụng socket, đóng tất cả các tiến trình trước đó hoặc đổi port.

### Mô phỏng chạy quá chậm
**Giải pháp**: Giảm số lượng node hoặc số iterations.

## Tài liệu Tham khảo
- Token Ring Mutual Exclusion: [Lamport's Logical Clocks]
- Distributed Systems: Principles and Paradigms (Andrew S. Tanenbaum)

## Tác giả
Dự án được thực hiện cho môn học Hệ Thống Phân Tán.

---
**Phiên bản**: 1.0  
**Ngày cập nhật**: 2024
