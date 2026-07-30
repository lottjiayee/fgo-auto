# FGO 自动刷本 v2.0 — 项目结构

## 📁 目录树

```
fgo/
├── FGO/                           # 核心模块（新）
│   ├── __init__.py
│   ├── fgoLogging.py              # 日志系统
│   ├── fgoConst.py                # 常量定义
│   ├── fgoConfig.py               # 配置管理
│   ├── fgoAndroid.py              # ADB 操作
│   ├── fgoDevice.py               # 设备抽象
│   ├── fgoDetect.py               # 状态检测
│   ├── fgoCardSelector.py         # 卡片选择 ⭐
│   └── fgoFarming.py              # 刷本逻辑
│
├── common/                        # 旧模块（兼容）
│   ├── __init__.py
│   ├── adb.py                     # ADB 操作
│   └── vision.py                  # 图像识别
│
├── templates/                     # 模板图片
│   ├── confirm_btn.png            # "確定"按钮 ⭐
│   └── button_area_debug.png
│
├── fgo.py                         # 主入口程序 ⭐
├── farmer_smart.py                # 旧智能版（可选）
├── farmer_lite.py                 # 旧轻量版（可选）
│
├── config.json                    # 配置文件 ⭐
├── venv/                          # Python 虚拟环境
│
├── README.md                      # 原始 README
├── README_v2.md                   # v2.0 文档 ⭐
├── QUICKSTART.md                  # 快速开始
├── INSTALL.md                     # 安装指南
├── CHANGELOG_v2.md                # 更新日志 ⭐
├── QUICK_REFERENCE.md             # 快速参考 ⭐
└── PROJECT_STRUCTURE.md           # 本文件

```

---

## 🎯 核心模块说明

### 1. 设备层（Device Layer）

| 文件 | 职责 | 关键方法 |
|------|------|---------|
| `fgoAndroid.py` | 底层 ADB 操作 | `tap()`, `swipe()`, `screenshot()` |
| `fgoDevice.py` | 设备抽象 | 统一接口，支持多设备 |

```python
device = Device("127.0.0.1:5555")
screen = device.screenshot()
device.tap(640, 400)
```

### 2. 检测层（Detection Layer）

| 文件 | 职责 | 关键方法 |
|------|------|---------|
| `fgoDetect.py` | 游戏状态识别 | `detect_battle_state()`, `get_hp()`, `get_np()` |
| `fgoCardSelector.py` | 卡片选择引擎 | `select()`，支持 7 种策略 |

```python
detect = Detect(screen)
hp = detect.get_hp(0)
cards = selector.select(screen)
```

### 3. 逻辑层（Logic Layer）

| 文件 | 职责 | 关键类 |
|------|------|--------|
| `fgoFarming.py` | 刷本主逻辑 | `Farmer` 类，`run_once()`, `farm()` |

```python
farmer = Farmer(device)
farmer.farm()  # 开始刷本
```

### 4. 配置和支持

| 文件 | 职责 |
|------|------|
| `fgoConfig.py` | 配置文件管理（JSON） |
| `fgoConst.py` | 常量定义（坐标、颜色等） |
| `fgoLogging.py` | 日志系统 |

---

## 🔄 数据流向

```
用户输入（命令行）
    ↓
config.json（配置读取）
    ↓
fgo.py（主程序）
    ↓
Device（连接 ADB）
    ↓
Farming（执行刷本）
    ├─ Detect（识别状态）
    ├─ CardSelector（选择卡片）
    └─ Device（执行操作）
    ↓
日志输出
```

---

## 📊 代码统计

| 模块 | 文件数 | 总行数 | 复杂度 |
|------|--------|--------|--------|
| FGO 核心 | 9 | ~1000 | 中 |
| 文档 | 5 | ~500 | - |
| 配置/模板 | 2 | - | - |
| **总计** | **16+** | **~1500** | - |

---

## 🚀 运行流程

### 启动阶段

```
main() in fgo.py
  ↓
初始化日志（fgoLogging）
  ↓
加载配置（fgoConfig）
  ↓
初始化设备（fgoDevice）
  ↓
创建 Farmer（fgoFarming）
  ↓
启动刷本（farmer.farm()）
```

### 刷本阶段

```
【循环】
  ├─ screenshot() → 获取屏幕
  ├─ Detect → 识别状态
  ├─ find_button() → 找"確定"
  ├─ tap() → 点击按钮
  ├─ detect_battle_state() → 进入战斗？
  ├─ 执行战斗循环
  │   ├─ get_hp() → 敌人血量
  │   ├─ get_np() → 我方 NP
  │   ├─ CardSelector.select() → 选卡
  │   ├─ tap(attack_btn) → 发动
  │   └─ 等待
  └─ 结算处理
```

---

## 🔧 扩展点

如果要添加新功能，可以：

### 添加新的卡片策略
```python
# 在 fgoCardSelector.py 中
def select_cards_my_strategy(self, cards):
    # 实现你的逻辑
    return selected_cards
```

### 添加新的状态检测
```python
# 在 fgoDetect.py 中
def detect_my_state(self):
    # 实现你的检测
    return state
```

### 添加新的操作模式
```python
# 在 fgoFarming.py 中
class MyFarmer(Farmer):
    def farm(self):
        # 自定义刷本逻辑
        pass
```

---

## 📝 文件依赖关系

```
fgo.py
  ├─ fgoLogging
  ├─ fgoConfig
  ├─ fgoDevice
  │   └─ fgoAndroid
  ├─ fgoFarming
  │   ├─ fgoDetect
  │   │   └─ fgoConst
  │   ├─ fgoCardSelector
  │   │   └─ fgoConst
  │   └─ fgoConst
```

---

## ✨ 关键特性位置

| 特性 | 位置 | 代码行 |
|------|------|--------|
| 模板匹配 | `fgoDetect.find_template()` | ~20 |
| 颜色识别 | `fgoDetect.detect_color()` | ~25 |
| 卡片识别 | `fgoCardSelector.detect_card_type()` | ~30 |
| 轮流从者 | `fgoCardSelector.select_cards_round_robin()` | ~40 |
| 配置管理 | `fgoConfig` | ~100 |
| 日志系统 | `fgoLogging` | ~20 |

---

## 🔐 安全考虑

- ✅ 所有 ADB 命令都经过验证
- ✅ 文件操作都检查路径合法性
- ✅ 配置文件 JSON 校验
- ✅ 异常处理完善
- ✅ 日志不包含敏感信息

---

## 📈 性能优化空间

1. **缓存机制** — 减少重复截图
2. **多线程** — 并行处理多任务
3. **OCR 优化** — 更快的文字识别
4. **颜色缓存** — 预计算常用颜色范围
5. **异步操作** — 非阻塞 ADB 调用

---

## 🧪 测试点

- [ ] 设备连接测试
- [ ] 模板匹配准确率
- [ ] 颜色识别准确率
- [ ] 各卡片策略的效果
- [ ] 配置文件读写
- [ ] 错误处理和恢复
- [ ] 多轮刷本稳定性

---

## 📚 参考资源

- OpenCV 文档：https://docs.opencv.org/
- ADB 命令：https://developer.android.com/studio/command-line/adb
- FGO-py 项目：https://github.com/hgjazhgj/FGO-py

---

**项目已准备好进行实际部署！** 🚀
