def log_message(message):
    print(f"[LOG] {message}")

def format_message(sender, message):
    return f"From {sender}: {message}"

def parse_message(message):
    parts = message.split(": ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, message

def validate_node_id(node_id, total_nodes):
    if 0 <= node_id < total_nodes:
        return True
    return False