# Simulation + Testing Engine

## 1. Mục tiêu

Phần việc của thành viên 4 là xây dựng **Simulation + Testing Engine** để kiểm thử và so sánh các thuật toán loại trừ tương hỗ trong hệ phân tán.

Hệ thống này có nhiệm vụ:

- Chuẩn hóa cách mô phỏng cho các thuật toán
- Chuẩn hóa cách ghi nhận message và event log
- Xây dựng các kịch bản kiểm thử dùng chung
- Thu thập dữ liệu thực nghiệm
- Tính toán các chỉ số để phục vụ so sánh hiệu năng

Phần này không cài đặt lại thuật toán Centralized, Ricart-Agrawala hay Token Ring, mà đóng vai trò là **môi trường chạy và bộ đo chung** cho các thuật toán đó.

---

## 2. Chuẩn message dùng chung

Toàn bộ hệ thống mô phỏng bám theo cấu trúc message thống nhất:

```python
Message(
    msg_type,
    sender_id,
    receiver_id,
    sequence_num,
    timestamp,
    data,
)