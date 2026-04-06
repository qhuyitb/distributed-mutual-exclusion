import os
import threading
from datetime import datetime

class SharedResource:
    """Quản lý truy cập file tài nguyên dùng chung"""
    
    def __init__(self):
        # Sử dụng path tuyệt đối để đảm bảo ghi vào đúng vị trí
        self.SHARED_FILE = os.path.join(os.path.dirname(__file__), "shared.txt")
        # Lock để đảm bảo atomicity khi đọc/ghi file
        self.file_lock = threading.RLock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Tạo file nếu chưa tồn tại, khởi tạo giá trị int"""
        if not os.path.exists(self.SHARED_FILE):
            with open(self.SHARED_FILE, 'w') as f:
                f.write("0")
    
    def _read_int(self):
        """Đọc giá trị số nguyên từ file shared.txt"""
        with self.file_lock:
            try:
                with open(self.SHARED_FILE, 'r') as f:
                    text = f.read().strip()
                    return int(text) if text else 0
            except (FileNotFoundError, ValueError):
                return 0
    
    def _write_int(self, value):
        """Ghi giá trị số nguyên vào file shared.txt"""
        with self.file_lock:
            try:
                with open(self.SHARED_FILE, 'w') as f:
                    f.write(str(value))
                    f.flush()
                    os.fsync(f.fileno())
            except IOError as e:
                print(f"Error writing to shared file: {e}")
    
    def read(self):
        """Đọc giá trị hiện tại của bộ đếm"""
        return self._read_int()
    
    def increment(self):
        """Tăng bộ đếm lên 1 khi node vào CS"""
        with self.file_lock:
            current = self._read_int()
            new_value = current + 1
            try:
                with open(self.SHARED_FILE, 'w') as f:
                    f.write(str(new_value))
                    f.flush()
                    os.fsync(f.fileno())
            except IOError as e:
                print(f"Error writing to shared file: {e}")
                return current
            return new_value
    
    def get_access_count(self):
        """Lấy bộ đếm hiện tại"""
        return self._read_int()
    
    def write_data(self, node_id, data):
        """Không hỗ trợ ghi dữ liệu tự do cho file số nguyên"""
        raise NotImplementedError("shared.txt only stores an integer counter")
