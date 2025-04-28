# ui/main_window.py

# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import ttk, messagebox
import pytz
import datetime

class MainWindow:
    def __init__(self, root, app_core):
        self.root = root
        self.core = app_core
        self.setup_ui()
        self.setup_time_ui()
        self.update_local_time()  # 初始化本地时间显示

    def toggle_time_display(self):
        """切换时间显示状态"""
        if hasattr(self.core, 'time_display_enabled'):
            self.core.time_display_enabled = not self.core.time_display_enabled
            btn_text = "显示时间" if not self.core.time_display_enabled else "隐藏时间"
            self.time_toggle_btn.config(text=btn_text)
            
            # 立即应用更改
            if self.core.time_display_enabled:
                if hasattr(self, 'update_ui_time'):
                    self.update_ui_time()
            else:
                # 只发送自定义文本
                self.send_chat_text()

    def setup_ui(self):
        self.root.title("自动钓鱼v1.4.2")
        
        # 参数设置框架
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

        # 控制按钮框架
        control_frame = Frame(self.root)
        control_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.start_btn = Button(control_frame, text="开始", command=self.safe_toggle, width=8)
        self.start_btn.pack(side=LEFT, padx=(0, 10))
        
        self.status_label = Label(control_frame, text="[开发者WaveYo]", width=15, anchor=W)
        self.status_label.pack(side=LEFT)

        # 聊天框功能
        chat_frame = Frame(self.root)
        chat_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        Label(chat_frame, text="聊天文本:").pack(side=LEFT, padx=(0,5))
        self.chat_entry = Entry(chat_frame, width=30)
        self.chat_entry.pack(side=LEFT, padx=5)
        
        Button(chat_frame, text="发送", command=self.send_chat_text).pack(side=LEFT, padx=(5,0))
        Button(chat_frame, text="清空", command=self.clear_chat_text).pack(side=LEFT, padx=5)

    def setup_time_ui(self):
        # 时间控制框架
        time_frame = Frame(self.root)
        time_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=W)
        
        # 时间显示开关
        self.time_toggle_btn = Button(time_frame, text="隐藏时间", command=self.toggle_time_display)
        self.time_toggle_btn.pack(side=LEFT, padx=(0,10))
        
        # 时间源选择
        self.time_source_var = StringVar(value="local")
        Radiobutton(time_frame, text="本地时间", variable=self.time_source_var, 
                   value="local", command=self.on_time_source_change).pack(side=LEFT, padx=5)
        Radiobutton(time_frame, text="世界时间", variable=self.time_source_var,
                   value="world", command=self.on_time_source_change).pack(side=LEFT, padx=5)
        
        # 时区选择框架
        self.tz_frame = Frame(time_frame)
        self.tz_frame.pack(side=LEFT, padx=5)
        
        # 洲选择
        Label(self.tz_frame, text="洲:").grid(row=0, column=0, padx=5, sticky=W)
        self.continent_var = StringVar()
        self.continent_cb = ttk.Combobox(self.tz_frame, textvariable=self.continent_var, 
                                       width=15, state="readonly")
        self.continent_cb["values"] = sorted(set(tz.split('/')[0] for tz in pytz.all_timezones if '/' in tz))
        self.continent_cb.grid(row=0, column=1, padx=5, sticky=W)
        self.continent_cb.bind("<<ComboboxSelected>>", self.update_regions)
        
        # 地区选择
        Label(self.tz_frame, text="地区:").grid(row=0, column=2, padx=5, sticky=W)
        self.region_var = StringVar()
        self.region_cb = ttk.Combobox(self.tz_frame, textvariable=self.region_var, 
                                    width=20, state="readonly")
        self.region_cb.grid(row=0, column=3, padx=5, sticky=W)
        self.region_cb.bind("<<ComboboxSelected>>", self.on_region_change)
        
        # GMT偏移显示
        self.gmt_label = Label(time_frame, text="", fg="blue")
        self.gmt_label.pack(side=LEFT, padx=(10,0))
        
        # 控制按钮框架
        self.time_control_frame = Frame(time_frame)
        self.time_control_frame.pack(side=LEFT, padx=5)
        
        self.apply_btn = Button(self.time_control_frame, text="应用更改", 
                              command=self.apply_time_changes, state=DISABLED)
        self.apply_btn.pack(side=LEFT, padx=5)
        
        self.cancel_btn = Button(self.time_control_frame, text="取消更改", 
                               command=self.cancel_time_changes, state=DISABLED)
        self.cancel_btn.pack(side=LEFT, padx=5)
        
        # 默认隐藏时区和控制按钮
        self.tz_frame.grid_remove()
        self.time_control_frame.pack_forget()
        
        # 时间显示标签
        self.time_label = Label(time_frame, text="", font=('Arial', 10))
        self.time_label.pack(side=LEFT, padx=(10,0))

        # 启动UI时间更新
        self.update_ui_time()

    def update_ui_time(self):
        """实时更新UI时间显示（每秒）"""
        if self.time_source_var.get() == "local":
            now = datetime.datetime.now()
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            # 计算本地时区偏移
            utc_now = datetime.datetime.utcnow()
            delta = now - utc_now
            hours = delta.seconds // 3600
            gmt_offset = f"UTC{hours:+d}" if hours != 0 else "UTC"
            self.gmt_label.config(text=gmt_offset)
        else:
            if hasattr(self, 'current_timezone'):
                tz = pytz.timezone(self.current_timezone)
                now = datetime.datetime.now(tz)
                time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        self.update_time_display(time_str)  # 使用新方法更新时间
        self.root.after(1000, self.update_ui_time)  # 每秒更新一次

    def update_regions(self, event=None):
        """更新地区选择框数据"""
        continent = self.continent_var.get()
        if continent:
            regions = []
            for tz in pytz.all_timezones:
                if tz.startswith(continent + '/'):
                    region_parts = tz.split('/')[1:]
                    if region_parts:
                        regions.append(region_parts[0])
            
            regions = sorted(list(set(regions)))
            self.region_cb["values"] = regions
            
            if regions:
                self.region_var.set(regions[0])
                self.on_region_change()

    def on_time_source_change(self):
        """时间源改变处理"""
        if self.time_source_var.get() == "world":
            self.tz_frame.grid()
            self.update_regions()
        else:
            self.tz_frame.grid_remove()
        
        # 显示控制按钮
        self.time_control_frame.pack()
        self.apply_btn.config(state=NORMAL)
        self.cancel_btn.config(state=NORMAL)

    def on_region_change(self, event=None):
        """地区改变处理"""
        continent = self.continent_var.get()
        region = self.region_var.get()
        if continent and region:
            self.current_timezone = f"{continent}/{region}"
            tz = pytz.timezone(self.current_timezone)
            now = datetime.datetime.now(tz)
            offset = now.utcoffset().total_seconds() / 3600
            gmt_offset = f"UTC{int(offset):+d}" if offset.is_integer() else f"UTC{offset:+.1f}"
            self.gmt_label.config(text=gmt_offset)
            
            # 显示控制按钮
            self.time_control_frame.pack()
            self.apply_btn.config(state=NORMAL)
            self.cancel_btn.config(state=NORMAL)

    def apply_time_changes(self):
        """应用时间设置更改"""
        if self.time_source_var.get() == "world":
            continent = self.continent_var.get()
            region = self.region_var.get()
            if continent and region:
                self.core.timezone = f"{continent}/{region}"
        
        # 立即与OSC同步
        if hasattr(self.core, 'update_osc_time'):
            self.core.update_osc_time()
        
        # 隐藏控制按钮
        self.time_control_frame.pack_forget()
        self.apply_btn.config(state=DISABLED)
        self.cancel_btn.config(state=DISABLED)

    def cancel_time_changes(self):
        """取消时间设置更改"""
        # 恢复原设置显示
        if hasattr(self.core, 'time_source'):
            self.time_source_var.set(self.core.time_source)
            if self.core.time_source == "world":
                self.tz_frame.grid()
                self.continent_var.set(self.core.timezone.split('/')[0])
                self.update_regions()
                self.region_var.set('/'.join(self.core.timezone.split('/')[1:]))
                tz = pytz.timezone(self.core.timezone)
                now = datetime.datetime.now(tz)
                offset = now.utcoffset().total_seconds() / 3600
                gmt_offset = f"UTC{int(offset):+d}" if offset.is_integer() else f"UTC{offset:+.1f}"
                self.gmt_label.config(text=gmt_offset)
            else:
                self.tz_frame.grid_remove()
        
        # 隐藏控制按钮
        self.time_control_frame.pack_forget()
        self.apply_btn.config(state=DISABLED)
        self.cancel_btn.config(state=DISABLED)

    def update_time_display(self, time_str=None):
        """更新时间显示"""
        if not hasattr(self, 'time_label'):
            return
            
        # 如果未传入时间字符串，则获取当前时间
        if time_str is None:
            if hasattr(self, 'time_source_var'):
                if self.time_source_var.get() == "local":
                    now = datetime.datetime.now()
                    time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if hasattr(self, 'current_timezone'):
                        tz = pytz.timezone(self.current_timezone)
                        now = datetime.datetime.now(tz)
                        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新UI显示
        self.time_label.config(text=time_str)
        
        # 同时更新OSC显示
        if hasattr(self.core, 'osc_client'):
            chat_text = self.chat_entry.get()
            display_text = f"{time_str}\n{chat_text}" if chat_text else time_str
            if len(display_text) > 144:
                display_text = display_text[:144]
            self.core.osc_client.send_message("/chatbox/input", [display_text, True, False])


    def safe_toggle(self):
        """安全调用核心模块的toggle方法"""
        if hasattr(self.core, 'toggle'):
            self.core.toggle()
            btn_text = "停止" if getattr(self.core, 'running', False) else "开始"
            self.start_btn.config(text=btn_text)

    def send_chat_text(self):
        """发送聊天文本"""
        if hasattr(self.core, 'osc_client'):
            chat_text = self.chat_entry.get()
            if chat_text:
                if len(chat_text) > 144:
                    chat_text = chat_text[:144]
                    messagebox.showwarning("提示", "聊天文本超过144字符限制，已截断")
                self.core.osc_client.send_message("/chatbox/input", [chat_text, True, False])

    def clear_chat_text(self):
        """清空聊天文本"""
        self.chat_entry.delete(0, END)
        if hasattr(self.core, 'osc_client'):
            self.core.osc_client.send_message("/chatbox/input", ["", True, False])

    def update_local_time(self):
        """初始化本地时区信息"""
        now = datetime.datetime.now()
        utc_now = datetime.datetime.utcnow()
        delta = now - utc_now
        hours = delta.seconds // 3600
        gmt_offset = f"UTC{hours:+d}" if hours != 0 else "UTC"
        self.gmt_label.config(text=gmt_offset)
