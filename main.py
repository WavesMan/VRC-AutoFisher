from tkinter import Tk
from core.fishing import FishingCore
from core.osc import OSCManager
from core.vrlog import VRChatLogHandler
from core.time import TimeManager
from ui.main_window import MainWindow

def main():
    root = Tk()
    
    # 初始化核心模块
    osc = OSCManager()
    log_handler = VRChatLogHandler(lambda: None)
    fishing_core = FishingCore(osc, log_handler)
    time_manager = TimeManager()
    
    # 创建UI并注入依赖
    app = MainWindow(root, fishing_core)
    
    # 配置时间管理器
    fishing_core.time_manager = time_manager
    time_manager.start_update_loop(app.update_time_display)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()
