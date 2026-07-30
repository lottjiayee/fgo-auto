# FGO 自动刷本 v2.0 — 完整更新日志

日期：2026-06-07  
版本：2.0.0（FGO-py 风格架构重构）

---

## 🎯 核心更新

### ✅ 架构升级（三层设计）

从**单文件脚本** → **模块化三层架构**

```
设备层 (Device)    ← ADB 操作
    ↓
检测层 (Detect)    ← 状态识别
    ↓
逻辑层 (Farming)   ← 战斗决策
```

---

## 📁 新增文件

### 核心模块（FGO/）

| 文件 | 功能 | 行数 |
|------|------|------|
| `__init__.py` | 包初始化 | 3 |
| `fgoLogging.py` | 日志系统 | 20 |
| `fgoConst.py` | 常量定义 | 80 |
| `fgoConfig.py` | 配置管理（JSON） | 100 |
| `fgoAndroid.py` | ADB 底层操作 | 80 |
| `fgoDevice.py` | 设备抽象层 | 80 |
| `fgoDetect.py` | 状态检测 | 150 |
| `fgoCardSelector.py` | 卡片选择引擎 ⭐ | 200 |
| `fgoFarming.py` | 刷本核心逻辑 | 200 |

### 主入口

| 文件 | 功能 |
|------|------|
| `fgo.py` | 命令行主程序 |
| `config.json` | 用户配置文件 |
| `README_v2.md` | 完整文档 |
| `CHANGELOG_v2.md` | 本文件 |

---

## 🎴 卡片选择系统（新增）⭐

### 支持 7 种策略

| 策略 | 说明 | 使用场景 |
|------|------|---------|
| `first_three` | 选前三张 | 快速测试 |
| `buster_first` | 优先 Buster | 高伤害队 |
| `chain_buster` | 连续 Buster | 链击伤害翻倍 |
| `arts_first` | 优先 Arts | 充能宝具 |
| `chain_quick` | 连续 Quick | 暴击链 |
| `smart` | 智能选择 | 根据敌人血量 |
| `round_robin` | **轮流从者** ⭐ | **1-2-1 式，推荐** |

### 自动卡片识别

✅ 自动识别卡片类型（蓝色/红色/绿色）  
✅ 自动分组按从者  
✅ 支持轮流选择避免重复

---

## 🚀 使用指南

### 基础运行

```bash
cd /Users/kellylott/Downloads/fgo
source venv/bin/activate

# 使用推荐的轮流从者策略
python fgo.py --debug

# 或指定其他卡片策略
python fgo.py --card-strategy chain_buster --debug
python fgo.py --card-strategy smart --debug
```

### 高级用法

```bash
# 指定设备和次数
python fgo.py --device 127.0.0.1:5555 --count 10 --card-strategy round_robin

# 邮箱模式（开发中）
python fgo.py --mode mail

# 抽卡模式（开发中）
python fgo.py --mode gacha
```

### 命令行参数

```
--device ADDR          ADB 设备地址 (默认: 127.0.0.1:5555)
--count N             刷本次数 (0=无限, 默认: 0)
--config FILE         配置文件路径 (默认: config.json)
--mode {farming|mail|gacha|synthesis}  运行模式
--card-strategy STR   卡片策略 (默认: round_robin)
--debug              启用调试模式
```

---

## 📊 配置文件（config.json）

```json
{
  "device": "127.0.0.1:5555",
  "run_count": 0,
  "farming": {
    "enabled": true,
    "np_strategy": "on_full",
    "attack_card_strategy": "round_robin",
    "support_skill_timing": "wave1"
  },
  "advanced": {
    "debug": false,
    "log_level": "INFO"
  }
}
```

---

## 🔧 核心类 API

### Device（设备层）

```python
from FGO.fgoDevice import Device

device = Device("127.0.0.1:5555")
screen = device.screenshot()        # 截图
device.tap(640, 400, delay=0.5)    # 点击
device.swipe(x1, y1, x2, y2)       # 滑动
```

### Detect（检测层）

```python
from FGO.fgoDetect import Detect

detect = Detect(screen)
state = detect.detect_battle_state()      # 获取状态
hp = detect.get_hp(0)                     # 敌人血量
np = detect.get_np(0)                     # 从者NP
button = detect.find_button("confirm_btn") # 找按钮
```

### CardSelector（卡片选择）

```python
from FGO.fgoCardSelector import CardSelector

selector = CardSelector(strategy="round_robin")
cards = selector.select(screen, enemy_hp_ratio=0.8)  # 选卡
```

### Farmer（刷本核心）

```python
from FGO.fgoFarming import Farmer

farmer = Farmer(device, card_strategy="round_robin")
farmer.farm()        # 开始刷本
```

---

## 🎯 工作流程

### 单次刷本流程

```
1️⃣  等待进入战斗
   ↓
2️⃣  点击"確定"按钮（模板匹配）
   ↓
3️⃣  进入战斗
   ↓
4️⃣  【循环】
    ├─ 检测战斗状态
    ├─ 识别敌人血量和 NP
    ├─ 执行技能（待实现）
    ├─ 点击 Attack 按钮
    ├─ 自动选择卡片（7种策略）
    └─ 等待战斗继续
   ↓
5️⃣  战斗结束，处理结算
   ↓
6️⃣  返回队伍选择页面
```

---

## ✨ 关键特性

### 已实现 ✅

- ✅ 三层模块化架构
- ✅ 配置文件管理（JSON）
- ✅ 完整日志系统
- ✅ 模板匹配（找按钮）
- ✅ 颜色分析（识别血条/NP）
- ✅ 7 种卡片选择策略
- ✅ **轮流从者策略**（避免重复输出）
- ✅ 命令行参数配置
- ✅ 调试模式
- ✅ 多设备支持

### 待实现 ⬜

- ⬜ 技能自动释放
- ⬜ 邮箱自动领取
- ⬜ 抽卡自动化
- ⬜ 强化自动化
- ⬜ 多线程后台运行
- ⬜ 缓存机制（减少截图）
- ⬜ GUI 可视化界面
- ⬜ 从者配置文件

---

## 📈 性能对比

| 指标 | v1.x | v2.0 |
|------|------|------|
| **代码行数** | 400 | 1200+ |
| **模块数** | 1 | 9 |
| **策略数** | 1 | 7 |
| **可扩展性** | 低 | 高 ⭐ |
| **配置方式** | 代码 | JSON ⭐ |
| **日志系统** | 简单 | 完整 ⭐ |
| **错误处理** | 基础 | 完善 ⭐ |

---

## 🐛 已知问题与解决方案

### 问题 1：按钮识别不稳定
**解决**：降低 threshold 值（如 0.60）或提供更清晰的模板

### 问题 2：颜色识别失败
**解决**：调整 HSV 颜色范围（在 fgoConst.py 中修改）

### 问题 3：战斗结束检测不准
**解决**：检查屏幕亮度阈值或添加额外验证

---

## 🚀 后续改进方向

### 短期（1-2 周）
1. 实现技能自动释放
2. 从者配置文件支持
3. 更多卡片策略

### 中期（1-2 个月）
1. 邮箱和抽卡功能
2. 多线程并行执行
3. 缓存和优化

### 长期（2-3 个月）
1. GUI 可视化界面
2. 支持更多游戏版本
3. 社区模板库

---

## 📝 文件变更总结

### 新增文件（11 个）
- FGO/ 目录及 9 个模块文件
- fgo.py（主入口）
- config.json（配置）
- README_v2.md（文档）
- CHANGELOG_v2.md（本文）

### 修改文件（3 个）
- farmer_smart.py（添加 TEMPLATES_DIR）
- fgoConst.py（多次更新）
- fgo.py（多次更新）

### 保留文件（兼容）
- common/ 目录（仍可用）
- farmer_lite.py（旧版本）
- farmer_smart.py（可选）

---

## 🙏 致谢

参考了 [FGO-py](https://github.com/hgjazhgj/FGO-py) 的架构设计思想，感谢开源社区！

---

## 📄 许可证

MIT License

---

**更新完成！现在可以使用新的 FGO 自动刷本脚本 v2.0 了！** 🎉

试试这个命令：
```bash
python fgo.py --card-strategy round_robin --debug
```
