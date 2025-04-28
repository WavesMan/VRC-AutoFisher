# core/time.py

import time
import datetime
import pytz
import threading
import requests

class TimeManager:
    def __init__(self):
        self.time_format = "%Y年%m月%d日 - %H:%M:%S"
        self.time_source = "local"
        self.timezone = "Asia/Shanghai"
        self.gmt_offset = "+8"
        self.last_sync_time = 0
        self.last_osc_update = 0
        self.time_running = True
        self.time_display_enabled = True
        self.ntp_server = "ntp.aliyun.com"

    def get_local_time(self):
        """获取本地系统时间"""
        now = datetime.datetime.now()
        return now.strftime(self.time_format) + f" (GMT{self.gmt_offset})", self.gmt_offset

    def get_network_time(self):
        """从阿里云获取网络时间"""
        try:
            response = requests.get(f"http://{self.ntp_server}/", timeout=3)
            if response.status_code == 200:
                server_time = datetime.datetime.strptime(
                    response.headers['Date'], '%a, %d %b %Y %H:%M:%S GMT'
                )
                server_time += datetime.timedelta(hours=8)  # 转换为北京时间
                return server_time.strftime(self.time_format) + " (GMT+8)", "+8"
        except Exception as e:
            print(f"网络时间同步失败: {e}")
        return self.get_local_time()  # 失败时回退到本地时间

    def get_world_time(self, timezone):
        """获取指定时区的时间"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.datetime.now(tz)
            offset = now.utcoffset().total_seconds() / 3600
            gmt_offset = f"{int(offset):+d}" if offset.is_integer() else f"{offset:+.1f}"
            return now.strftime(self.time_format) + f" (GMT{gmt_offset})", gmt_offset
        except pytz.UnknownTimeZoneError:
            return self.get_local_time()

    def sync_time(self):
        """同步时间（每30分钟）"""
        while self.time_running:
            if time.time() - self.last_sync_time > 1800:  # 30分钟
                if self.time_source == "world":
                    self.last_sync_time = time.time()
                    print("正在同步网络时间...")
                    time_str, _ = self.get_network_time()
                    print(f"同步完成: {time_str}")
            time.sleep(60)

    def start_update_loop(self, callback):
        """启动时间更新线程"""
        self.update_callback = callback
        # 启动时间同步线程
        threading.Thread(target=self.sync_time, daemon=True).start()
        # 启动OSC更新线程
        threading.Thread(target=self.osc_update_loop, daemon=True).start()

    def osc_update_loop(self):
        """OSC时间更新循环（每10秒）"""
        while self.time_running:
            if self.time_display_enabled and time.time() - self.last_osc_update >= 10:
                time_str = self.get_current_time()[0]
                self.update_callback(time_str)
                self.last_osc_update = time.time()
            time.sleep(1)

    def get_current_time(self):
        """获取当前时间（根据时间源）"""
        if self.time_source == "local":
            return self.get_local_time()
        else:
            return self.get_world_time(self.timezone)
