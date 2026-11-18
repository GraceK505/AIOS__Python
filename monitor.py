import psutil
import asyncio

async def cpu_monitor():
    """Continuously monitor CPU usage."""
    while True:
        # interval=0 gives instant usage, but interval=1 is fine for smoother values
        usage = psutil.cpu_percent(interval=0.5)
        print(f"[CPU Monitor] Usage: {usage}%")
        await asyncio.sleep(2)

async def memory_monitor():
    """Continuously monitor memory usage."""
    while True:
        mem = psutil.virtual_memory()
        used_mb = mem.used / (1024 * 1024)
        total_mb = mem.total / (1024 * 1024)
        print(f"[Memory Monitor] Usage: {used_mb:.2f} MB / {total_mb:.2f} MB")
        await asyncio.sleep(3)

async def disk_monitor():
    """Continuously monitor disk usage."""
    while True:
        disk = psutil.disk_usage('/')
        used_gb = disk.used / (1024 * 1024 * 1024)
        total_gb = disk.total / (1024 * 1024 * 1024)
        print(f"[Disk Monitor] Usage: {disk.percent}% ({used_gb:.2f} GB / {total_gb:.2f} GB)")
        await asyncio.sleep(5)

async def network_monitor():
    """Continuously monitor network I/O."""
    while True:
        net = psutil.net_io_counters()
        sent_mb = net.bytes_sent / (1024 * 1024)
        recv_mb = net.bytes_recv / (1024 * 1024)
        print(f"[Network Monitor] Sent: {sent_mb:.2f} MB | Received: {recv_mb:.2f} MB")
        await asyncio.sleep(4)

async def process_memory_monitor():
    """List top processes by memory usage."""
    while True:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                mem = proc.info['memory_info'].rss / (1024 * 1024)  # MB
                processes.append((proc.info['pid'], proc.info['name'], mem))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by memory usage (descending) and show top 5
        top = sorted(processes, key=lambda x: x[2], reverse=True)[:5]
        print("\n[Process Monitor] Top 5 processes by memory usage:")
        for pid, name, mem in top:
            print(f"  PID {pid:<6} {name:<25} {mem:.2f} MB")

        await asyncio.sleep(5)