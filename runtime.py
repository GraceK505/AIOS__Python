

def ai_response(cmd: str) -> str:
    if cmd.lower() == "cpu":
        import psutil
        return f"CPU usage: {psutil.cpu_percent()}%"
    elif cmd.lower() == "mem":
        import psutil
        return f"Memory usage: {psutil.virtual_memory().percent}%"
    elif cmd.lower() == "exit":
        return "[Kernel] Shutting down..."
    else:
        return f"AIOS response to: {cmd}"