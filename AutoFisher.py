import os
import time
import datetime
import pytz
import threading
from tkinter import *
from tkinter import ttk
from pythonosc import udp_client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VRChatLogHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.current_log = None
        self.last_check = 0
        self.lock = threading.Lock()
        self.update_log_file()

    def get_vrchat_log_dir(self):
        appdata = os.getenv('APPDATA', '')
        return os.path.normpath(os.path.join(
            appdata, r'..\LocalLow\VRChat\VRChat'
        ))

    def find_latest_log(self):
        log_dir = self.get_vrchat_log_dir()
        if not os.path.exists(log_dir):
            return None
            
        logs = [f for f in os.listdir(log_dir) 
               if f.startswith('output_log_') and f.endswith('.txt')]
        if not logs:
            return None
            
        latest = max(
            logs,
            key=lambda x: os.path.getmtime(os.path.join(log_dir, x))
        )
        return os.path.join(log_dir, latest)

    def update_log_file(self):
        new_log = self.find_latest_log()
        if new_log != self.current_log:
            print(f"检测到新日志文件: {new_log}")
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
                
            content = self.safe_read_file()
            if "SAVED DATA" in content:
                self.callback()

    def start_monitor(self):
        self.observer = Observer()
        self.observer.schedule(self, path=self.get_vrchat_log_dir(), recursive=False)
        self.observer.start()
        
        self.check_thread = threading.Thread(target=self.check_logs, daemon=True)
        self.check_thread.start()

class AutoFishingApp:
    def __init__(self, root):
        # 基础功能
        self.root = root
        self.running = False
        self.current_action = "等待"
        self.protected = False
        self.last_cycle_end = 0
        self.timeout_timer = None
        
        # OSC客户端
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
        
        # 文本功能
        self.chatbox_visible = True
        self.chatbox_text = ""
        self.time_display_enabled = True  # 时间显示默认开启
        
        # 时间功能
        self.time_format = "%Y年%m月%d日 - %H:%M"
        self.time_source = "local"
        self.timezone = "Asia/Shanghai"
        self.gmt_offset = "+8"
        self.last_sync_time = 0
        self.last_osc_update = 0
        
        # 临时设置
        self.temp_time_source = "local"
        self.temp_timezone = "Asia/Shanghai"
        
        # 先初始化UI
        self.setup_ui()
        
        # 启动时间同步线程
        self.time_running = True
        self.time_thread = threading.Thread(target=self.time_update_loop, daemon=True)
        self.time_thread.start()
        
        self.log_handler = VRChatLogHandler(self.fish_on_hook)
        self.log_handler.start_monitor()
        self.send_click(False)
        self.first_cast = True

    def time_update_loop(self):
        """时间更新主循环"""
        while self.time_running:
            try:
                current_time = time.time()
                
                # 每分钟与OSC同步一次时间
                if current_time - self.last_osc_update >= 10:
                    self.update_osc_time()
                    self.last_osc_update = current_time
                
                time.sleep(1)  # 每秒检查一次
            except Exception as e:
                print(f"时间更新错误: {e}")

    def update_osc_time(self):
        """更新OSC时间显示"""
        if not self.time_display_enabled:
            return
            
        # 获取时间字符串
        if self.time_source == "local":
            time_str, gmt = self.get_local_time()
        else:
            time_str, gmt = self.get_world_time(self.timezone)
        
        # 获取自定义文本
        custom_text = self.chat_entry.get()
        
        # 组合显示文本(换行显示)
        if custom_text:
            display_text = f"{time_str}\n{custom_text}"
        else:
            display_text = time_str
            
        # 确保不超过144字符限制
        if len(display_text) > 144:
            display_text = display_text[:144]
        
        # 发送OSC消息
        self.osc_client.send_message("/chatbox/input", [display_text, True, False])
        self.osc_client.send_message("/chatbox/typing", self.chatbox_visible)

    def get_local_time(self):
        """获取本地时间"""
        now = datetime.datetime.now()
        gmt_offset = "+8"  # 中国标准时间固定为GMT+8
        return now.strftime(self.time_format) + f" (GMT{gmt_offset})", gmt_offset

    def get_world_time(self, timezone):
        """获取指定时区的时间"""
        try:
            tz = pytz.timezone(timezone)
            now = datetime.datetime.now(tz)
            
            # 计算GMT偏移
            offset = now.utcoffset().total_seconds() / 3600
            gmt_offset = f"{int(offset):+d}" if offset.is_integer() else f"{offset:+.1f}"
            
            return now.strftime(self.time_format) + f" (GMT{gmt_offset})", gmt_offset
        except pytz.UnknownTimeZoneError:
            return self.get_local_time()

    def toggle_time_display(self):
        """切换时间显示状态"""
        self.time_display_enabled = not self.time_display_enabled
        self.time_toggle_btn.config(text="显示时间" if not self.time_display_enabled else "隐藏时间")
        
        # 立即应用更改
        if self.time_display_enabled:
            self.update_osc_time()
        else:
            # 只发送自定义文本
            text = self.chat_entry.get()
            if len(text) > 144:
                text = text[:144]
            self.osc_client.send_message("/chatbox/input", [text, True, False])
            self.osc_client.send_message("/chatbox/typing", self.chatbox_visible)

    def toggle(self):
        self.running = not self.running
        self.start_btn.config(text="停止" if self.running else "开始")
        if self.running:
            self.first_cast = True
            self.current_action = "开始抛竿"
            self.update_status()
            threading.Thread(target=self.perform_cast).start()
        else:
            self.emergency_release()

    def toggle_chatbox(self):
        self.chatbox_visible = not self.chatbox_visible
        self.chat_toggle_btn.config(text="显示聊天框" if not self.chatbox_visible else "隐藏聊天框")
        self.update_chat_text()

    def update_chat_text(self):
        text = self.chat_entry.get()
        if len(text) > 144:
            text = text[:144]
            print("警告: 聊天文本超过144字符限制，已截断")
        self.osc_client.send_message("/chatbox/input", [text, True, False])
        self.osc_client.send_message("/chatbox/typing", self.chatbox_visible)

    def emergency_release(self):
        self.send_click(False)
        self.current_action = "已停止"
        self.update_status()

    def setup_ui(self):
        self.root.title("自动钓鱼v1.4.2")
        
        params_frame = Frame(self.root)
        params_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=2)
        
        row_counter = 0
        Label(params_frame, text="蓄力时间 (秒):").grid(row=row_counter, padx=5, pady=2, sticky=W)
        self.cast_time = Entry(params_frame)
        self.cast_time.insert(0, "2")
        self.cast_time.grid(row=row_counter, column=1, padx=5, pady=2)
        row_counter += 1

        Label(params_frame, text="休息时间 (秒):").grid(row=row_counter, padx=5, pady=2, sticky=W)
        self.rest_time = Entry(params_frame)
        self.rest_time.insert(0, "3")
        self.rest_time.grid(row=row_counter, column=1, padx=5, pady=2)
        row_counter += 1

        Label(params_frame, text="超时重钓 (分):").grid(row=row_counter, padx=5, pady=2, sticky=W)
        self.timeout_limit = Entry(params_frame)
        self.timeout_limit.insert(0, "5")
        self.timeout_limit.grid(row=row_counter, column=1, padx=5, pady=2)

        # ChatBox功能
        chat_frame = Frame(self.root)
        chat_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        Label(chat_frame, text="聊天框文本:").grid(row=0, column=0, padx=5, pady=2, sticky=W)
        self.chat_entry = Entry(chat_frame, width=30)
        self.chat_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.chat_toggle_btn = Button(chat_frame, text="隐藏聊天框", command=self.toggle_chatbox)
        self.chat_toggle_btn.grid(row=0, column=2, padx=5, pady=2)
        
        Button(chat_frame, text="更新文本", command=self.update_chat_text).grid(row=1, column=1, pady=2)

        # 时间功能
        time_frame = Frame(self.root)
        time_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=W)
        
        # 时间显示开关
        self.time_toggle_btn = Button(time_frame, text="隐藏时间", command=self.toggle_time_display)
        self.time_toggle_btn.grid(row=0, column=0, padx=5, pady=2, sticky=W)
        
        Label(time_frame, text="时间源:").grid(row=0, column=1, padx=5, pady=2, sticky=W)
        self.time_source_var = StringVar(value="local")
        Radiobutton(time_frame, text="本地时间", variable=self.time_source_var, 
                   value="local", command=self.on_time_source_change).grid(row=0, column=2, sticky=W)
        Radiobutton(time_frame, text="世界时间", variable=self.time_source_var, 
                   value="world", command=self.on_time_source_change).grid(row=0, column=3, sticky=W)
        
        # 时区选择框架
        self.timezone_frame = Frame(time_frame)
        self.timezone_frame.grid(row=1, column=0, columnspan=5, pady=5, sticky=W)
        
        # 洲选择
        Label(self.timezone_frame, text="洲:").grid(row=0, column=0, padx=5, sticky=W)
        self.continent_var = StringVar()
        self.continent_cb = ttk.Combobox(self.timezone_frame, textvariable=self.continent_var, 
                                       width=15, state="readonly")
        self.continent_cb["values"] = sorted(set(tz.split('/')[0] for tz in pytz.all_timezones if '/' in tz))
        self.continent_cb.grid(row=0, column=1, padx=5, sticky=W)
        self.continent_cb.bind("<<ComboboxSelected>>", self.update_regions)
        
        # 地区选择
        Label(self.timezone_frame, text="地区:").grid(row=0, column=2, padx=5, sticky=W)
        self.region_var = StringVar()
        self.region_cb = ttk.Combobox(self.timezone_frame, textvariable=self.region_var, 
                                    width=20, state="readonly")
        self.region_cb.grid(row=0, column=3, padx=5, sticky=W)
        
        # GMT显示
        self.gmt_label = Label(time_frame, text="GMT+8", fg="gray")
        self.gmt_label.grid(row=0, column=4, padx=5, sticky=E)
        
        # 控制按钮框架
        self.time_control_frame = Frame(time_frame)
        self.time_control_frame.grid(row=2, column=0, columnspan=5, pady=5)
        
        self.apply_btn = Button(self.time_control_frame, text="应用更改", 
                              command=self.apply_time_changes, state=DISABLED)
        self.apply_btn.pack(side=LEFT, padx=5)
        
        self.cancel_btn = Button(self.time_control_frame, text="取消更改", 
                               command=self.cancel_time_changes, state=DISABLED)
        self.cancel_btn.pack(side=LEFT, padx=5)
        
        # 默认隐藏时区和控制按钮
        self.timezone_frame.grid_remove()
        self.time_control_frame.grid_remove()

        control_frame = Frame(self.root)
        control_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.start_btn = Button(control_frame, text="开始", command=self.toggle, width=8)
        self.start_btn.pack(side=LEFT, padx=(0, 10))
        
        self.status_label = Label(control_frame, text="[开发者WaveYo]", width=15, anchor=W)
        self.status_label.pack(side=LEFT)

    def update_regions(self, event=None):
        """更新地区选择框数据"""
        continent = self.continent_var.get()
        if continent:
            # 获取该洲下的所有地区
            regions = []
            for tz in pytz.all_timezones:
                if tz.startswith(continent + '/'):
                    region_parts = tz.split('/')[1:]
                    # 只取第一级地区
                    if region_parts:
                        regions.append(region_parts[0])
            
            # 去重并排序
            regions = sorted(list(set(regions)))
            self.region_cb["values"] = regions
            
            # 自动选择第一个地区
            if regions:
                self.region_var.set(regions[0])
                self.on_region_change()

    def on_time_source_change(self):
        """时间源改变处理"""
        self.temp_time_source = self.time_source_var.get()
        if self.temp_time_source == "world":
            self.timezone_frame.grid()
            self.update_regions()
        else:
            self.timezone_frame.grid_remove()
            self.gmt_label.config(text="GMT+8 (待应用)")
        
        # 显示控制按钮
        self.time_control_frame.grid()
        self.apply_btn.config(state=NORMAL)
        self.cancel_btn.config(state=NORMAL)

    def on_region_change(self, event=None):
        """地区改变处理"""
        continent = self.continent_var.get()
        region = self.region_var.get()
        if continent and region:
            # 构建完整时区字符串
            self.temp_timezone = f"{continent}/{region}"
            
            # 更新GMT显示
            _, gmt_offset = self.get_world_time(self.temp_timezone)
            self.gmt_label.config(text=f"GMT{gmt_offset} (待应用)")
            
            # 显示控制按钮（新增）
            if self.time_source_var.get() == "world":
                self.time_control_frame.grid()
                self.apply_btn.config(state=NORMAL)
                self.cancel_btn.config(state=NORMAL)

    def apply_time_changes(self):
        """应用时间设置更改"""
        self.time_source = self.temp_time_source
        if self.time_source == "world":
            self.timezone = self.temp_timezone
            _, self.gmt_offset = self.get_world_time(self.timezone)
            self.gmt_label.config(text=f"GMT{self.gmt_offset}")
        else:
            self.gmt_offset = "+8"
            self.gmt_label.config(text="GMT+8")
        
        # 隐藏控制按钮
        self.time_control_frame.grid_remove()
        self.apply_btn.config(state=DISABLED)
        self.cancel_btn.config(state=DISABLED)
        
        # 立即更新OSC显示
        self.update_osc_time()

    def cancel_time_changes(self):
        """取消时间设置更改"""
        # 恢复原设置显示
        self.time_source_var.set(self.time_source)
        if self.time_source == "world":
            self.timezone_frame.grid()
            self.update_regions()
            _, self.gmt_offset = self.get_world_time(self.timezone)
            self.gmt_label.config(text=f"GMT{self.gmt_offset}")
        else:
            self.timezone_frame.grid_remove()
            self.gmt_label.config(text="GMT+8")
        
        # 隐藏控制按钮
        self.time_control_frame.grid_remove()
        self.apply_btn.config(state=DISABLED)
        self.cancel_btn.config(state=DISABLED)

    def update_status(self):
        self.status_label.config(text=f"[{self.current_action}]")
        self.root.update()

    def send_click(self, press):
        self.osc_client.send_message("/input/UseRight", 1 if press else 0)

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
        if self.running and self.current_action == "等待上钩":
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

    def fish_on_hook(self):
        if not self.running or self.protected or time.time() - self.last_cycle_end < 2:
            return

        try:
            self.protected = True
            self.last_cycle_end = time.time()
            self.perform_reel()
            self.perform_cast()
        finally:
            self.protected = False
            self.last_cycle_end = time.time()

    def on_close(self):
        # 停止时间线程
        self.time_running = False
        if self.time_thread and self.time_thread.is_alive():
            self.time_thread.join(timeout=1)
        
        # 关闭时隐藏聊天框
        self.osc_client.send_message("/chatbox/typing", False)
        
        self.emergency_release()
        try:
            if hasattr(self, 'timeout_timer') and self.timeout_timer:
                self.timeout_timer.cancel()
            
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=1)
            
            if hasattr(self.log_handler, 'check_thread'):
                self.log_handler.check_thread.join(timeout=0.5)
                
        except Exception as e:
            print(f"关闭时发生错误: {e}")
        finally:
            self.root.destroy()
            self.root.quit()

if __name__ == "__main__":
    root = Tk()
    app = AutoFishingApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
