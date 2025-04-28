# core/vrlog.py

import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VRChatLogHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.current_log = None
        self.file_position = 0
        self.update_log_file()

    def get_vrchat_log_dir(self):
        appdata = os.getenv('APPDATA', '')
        return os.path.normpath(os.path.join(appdata, r'..\LocalLow\VRChat\VRChat'))

    def find_latest_log(self):
        log_dir = self.get_vrchat_log_dir()
        if not os.path.exists(log_dir):
            return None
            
        logs = [f for f in os.listdir(log_dir) 
               if f.startswith('output_log_') and f.endswith('.txt')]
        return max(logs, key=lambda x: os.path.getmtime(os.path.join(log_dir, x))) if logs else None

    def update_log_file(self):
        new_log = self.find_latest_log()
        if new_log != self.current_log:
            self.current_log = new_log
            self.file_position = 0
            return True
        return False

    def safe_read_file(self):
        if not self.current_log or not os.path.exists(self.current_log):
            return ''
            
        try:
            with open(self.current_log, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                file_size = f.tell()
                if self.file_position > file_size:
                    self.file_position = 0
                f.seek(self.file_position)
                content = f.read()
                self.file_position = f.tell()
                return content
        except Exception as e:
            print(f"读取日志失败: {str(e)}")
            return ''

    def check_logs(self):
        while True:
            time.sleep(1)
            if self.update_log_file():
                continue
            if "SAVED DATA" in self.safe_read_file():
                self.callback()

    def start_monitor(self):
        self.observer = Observer()
        self.observer.schedule(self, path=self.get_vrchat_log_dir(), recursive=False)
        self.observer.start()
        self.check_thread = threading.Thread(target=self.check_logs, daemon=True)
        self.check_thread.start()
