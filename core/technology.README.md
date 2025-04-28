## 核心模块 (`core`)

核心模块包含了自动钓鱼应用的核心逻辑和功能实现，分为以下几个子模块：

#### 1. **`fishing.py`**
   - **功能**: 负责钓鱼逻辑的实现，包括抛竿、收杆、等待鱼上钩等操作。
   - **关键类**: `FishingCore`
     - `toggle()`: 启动或停止钓鱼。
     - `perform_cast()`: 执行抛竿操作。
     - `check_fish_pickup()`: 检测鱼上钩状态。
     - `update_status()`: 更新UI状态。
     - 线程安全的超时处理和异常捕获机制。

#### 2. **`osc.py`**
   - **功能**: 负责与VRChat的OSC通信，符合VRChat OSC API规范。
   - **关键类**: `OSCManager`
     - `send_click(press)`: 发送鼠标点击事件。
     - `send_chat_message(text, typing)`: 发送聊天消息到VRChat。
     - 支持127.0.0.1:9000默认地址配置。

#### 3. **`time.py`**
   - **功能**: 高级时间管理，支持：
     - 本地时间（自动计算时区偏移）
     - 世界时间（通过阿里云NTP服务器同步）
     - 每30分钟自动同步网络时间
     - 每10秒更新OSC时间显示
   - **关键类**: `TimeManager`
     - `start_update_loop(callback)`: 启动时间更新线程。
     - 支持时区选择和GMT偏移显示。

#### 4. **`vrlog.py`**
   - **功能**: 监听VRChat日志文件，检测鱼上钩事件。
   - **关键类**: `VRChatLogHandler`
     - 自动检测日志文件变化
     - 实时监控日志内容
     - 线程安全的文件读取机制
