#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System monitoring for AIOS
"""

import threading
import queue
import time
import psutil
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
import config

class SystemMetrics:
    """Collects system metrics"""
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            
            try:
                load = os.getloadavg()
            except:
                load = (0, 0, 0)
            
            return {
                "percent": cpu,
                "load_1min": load[0],
                "load_5min": load[1] if len(load) > 1 else 0,
                "load_15min": load[2] if len(load) > 2 else 0,
                "cores": psutil.cpu_count(),
            }
        except:
            return {"percent": 0, "load_1min": 0, "cores": 0}
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "percent": mem.percent,
                "used_mb": mem.used // (1024 ** 2),
                "total_mb": mem.total // (1024 ** 2),
                "swap_percent": swap.percent,
                "swap_used_mb": swap.used // (1024 ** 2),
            }
        except:
            return {"percent": 0, "used_mb": 0, "total_mb": 0}
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk information"""
        try:
            disk = psutil.disk_usage('/')
            return {
                "percent": disk.percent,
                "used_gb": disk.used // (1024 ** 3),
                "total_gb": disk.total // (1024 ** 3),
            }
        except:
            return {"percent": 0, "used_gb": 0, "total_gb": 0}
    
    @staticmethod
    def get_processes(limit: int = 8) -> List[Tuple[int, str, float, float]]:
        """Get top processes"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append((
                        info['pid'],
                        info.get('name', 'unknown')[:20],
                        info.get('cpu_percent', 0.0),
                        info.get('memory_percent', 0.0)
                    ))
                except:
                    continue
            
            processes.sort(key=lambda x: x[3], reverse=True)
            return processes[:limit]
        except:
            return []
    
    @staticmethod
    def check_alerts() -> List[str]:
        """Check for system alerts"""
        alerts = []
        
        try:
            cpu = psutil.cpu_percent()
            if cpu > config.SYSTEM_CONFIG["cpu_warning"]:
                alerts.append(f"High CPU usage: {cpu:.1f}%")
            
            mem = psutil.virtual_memory()
            if mem.percent > config.SYSTEM_CONFIG["memory_warning"]:
                alerts.append(f"High memory usage: {mem.percent:.1f}%")
            
            disk = psutil.disk_usage('/')
            if disk.percent > config.SYSTEM_CONFIG["disk_warning"]:
                alerts.append(f"High disk usage: {disk.percent:.1f}%")
        except:
            pass
        
        return alerts


class KernelMonitor(threading.Thread):
    """System monitor thread"""
    
    def __init__(self, update_queue: queue.Queue):
        super().__init__(daemon=True)
        self.queue = update_queue
        self.running = True
        self.metrics = SystemMetrics()
    
    def stop(self):
        """Stop the monitor"""
        self.running = False
    
    def run(self):
        """Main monitoring loop"""
        while self.running:
            try:
                cpu_info = self.metrics.get_cpu_info()
                mem_info = self.metrics.get_memory_info()
                disk_info = self.metrics.get_disk_info()
                processes = self.metrics.get_processes(config.SYSTEM_CONFIG["max_processes"])
                alerts = self.metrics.check_alerts()
                
                data = {
                    "cpu": cpu_info,
                    "memory": mem_info,
                    "disk": disk_info,
                    "processes": processes,
                    "alerts": alerts,
                    "timestamp": time.time()
                }
                
                self.queue.put(("update", data))
                time.sleep(config.SYSTEM_CONFIG["update_interval"])
            except Exception as e:
                self.queue.put(("error", f"Monitor error: {str(e)}"))
                time.sleep(config.SYSTEM_CONFIG["update_interval"] * 2)