# core/fishing.py

import time
import threading

class FishingCore:
    def __init__(self, osc_manager, log_handler):
        self.osc = osc_manager
        self.log_handler = log_handler
        self.running = False
        self.protected = False
        self.first_cast = True
        self.timeout_timer = None
        self.current_action = "等待"
        self.last_cycle_end = 0

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.first_cast = True
            self.current_action = "开始抛竿"
            threading.Thread(target=self.perform_cast).start()
        else:
            self.emergency_release()

    def perform_cast(self):
        if not self.first_cast:
            self.current_action = "休息中"
            self.update_status()
            try:
                rest_duration = float(self.rest_time.get())
            except:
                rest_duration = 3.0
            time.sleep(max(0.1, rest_duration))
        else:
            self.first_cast = False

        self.current_action = "鱼竿蓄力中"
        self.update_status()
        cast_duration = self.get_param(self.cast_time, 2)
        self.send_click(True)
        time.sleep(cast_duration)
        self.send_click(False)

        self.current_action = "等待鱼上钩"
        self.update_status()
        self.start_timeout_timer()
        time.sleep(3)

    def update_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"[{self.current_action}]")
            if hasattr(self, 'root'):
                self.root.update()

    def send_click(self, press):
        self.osc.send_click(press)

    def get_param(self, entry, default):
        try:
            value = float(entry.get())
            return max(0.5, value)
        except:
            return max(0.5, default)

    def start_timeout_timer(self):
        if self.timeout_timer and self.timeout_timer.is_alive():
            self.timeout_timer.cancel()
        
        timeout = self.get_param(self.timeout_limit, 5) * 60
        self.timeout_timer = threading.Timer(timeout, self.handle_timeout)
        self.timeout_timer.start()

    def handle_timeout(self):
        if self.running and self.current_action == "等待鱼上钩":
            self.current_action = "超时收杆"
            self.update_status()
            self.force_reel()

    def force_reel(self):
        if self.protected:
            return

        try:
            self.protected = True
            self.perform_reel()
            self.perform_cast()
        finally:
            self.protected = False

    def perform_reel(self):
        self.current_action = "收杆中"
        self.update_status()
        self.send_click(True)
        
        success = self.check_fish_pickup()
        
        if success and self.detected_time:
            elapsed = time.time() - self.detected_time
            remaining_time = max(0, 2 - elapsed)
            if remaining_time > 0:
                time.sleep(remaining_time)
        
        self.send_click(False)
        self.detected_time = None

    def check_fish_pickup(self):
        start_time = time.time()
        self.detected_time = None
        
        while time.time() - start_time < 30:
            content = self.log_handler.safe_read_file()
            
            if "Fish Pickup attached to rod Toggles(True)" in content:
                if not self.detected_time:
                    self.detected_time = time.time()
                    
            if self.detected_time and (time.time() - self.detected_time >= 2):
                return True
                
            time.sleep(0.5)
            
        return False

    def emergency_release(self):
        self.send_click(False)
        self.current_action = "已停止"
        self.update_status()
