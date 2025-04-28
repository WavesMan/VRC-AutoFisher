## VRC-AutoFisher DEV Branch 🛠️⚡

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/) [![OSC Protocol](https://img.shields.io/badge/OSC-1.1-brightgreen)](https://opensoundcontrol.stanford.edu/) [![Build Status](https://img.shields.io/badge/DEV-Branch-orange)]()


##### 基于[AutoFisher-VRC](https://github.com/arcxingye/AutoFisher-VRC)开发分支

### 🚀 开发分支特性

#### 新增功能

- **增强时间管理系统**
  - 本地/世界时间双模式
  - 自动时区偏移计算
  - 阿里云NTP时间同步

- **改进的OSC集成**
  - 精确到秒的UI时间显示
  - 10秒间隔的OSC通信
  - 144字符智能截断

- **开发者工具**
  - 线程安全检测
  - 详细的日志输出
  - 模块化架构设计

#### 🧩 项目结构

```
AutoFisher/
├── core/                               # 核心模块
│   ├── __init__.py                     # 模块导出文件
│   ├── fishing.py                      # 钓鱼逻辑
│   ├── osc.py                          # OSC通信
│   ├── time.py                         # 时间管理
│   ├── vrlog.py                        # 日志监听
│   └── technology.README.md            # 核心模块技术文档
├── ui/                                 # 用户界面模块
│   ├── __init__.py                     # 模块导出文件
│   ├── main_window.py                  # 主窗口界面
│   └── technology.README.md            # 用户界面模块技术文档
├── main.py                             # 主程序
└── technology.README.md                # 项目技术文档
```

### 🛠️ 开发说明

- 构建要求

    ```bash
    pip install -r requirements.txt
    ```

- 运行命令

    ```bash
    python main.py
    ```

### ⚠️ 问题

- 时间区块存在问题，未能复现主分支版本
- OSC通信未测试，可能存在异常