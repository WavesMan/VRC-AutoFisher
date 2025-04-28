## 项目技术实现

### 主程序模块 (`main`)
- **`main.py`**:
  - 初始化所有核心模块
  - 配置模块间依赖关系
  - 启动主事件循环

### 项目结构

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
