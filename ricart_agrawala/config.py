import random

# Định nghĩa node và cổng của chúng
NODES = {
    1: ("127.0.0.1", 5001),
    2: ("127.0.0.1", 5002),
    3: ("127.0.0.1", 5003),
}

# Độ trễ mạng giả lập khi gửi tin nhắn (giây)
NETWORK_DELAY = (0.1, 0.5)

# Thời gian giữ trong critical section
CS_DURATION = 5


def random_network_delay():
    return random.uniform(NETWORK_DELAY[0], NETWORK_DELAY[1])
