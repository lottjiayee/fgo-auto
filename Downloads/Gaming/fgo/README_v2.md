# FGO 自动刷本 v2.0 — FGO-py 风格架构

## 📋 项目结构（新架构）

```
fgo/
  ├── FGO/                      # 核心模块
  │   ├── __init__.py
  │   ├── fgoLogging.py         ✅ 日志系统
  │   ├── fgoConst.py           ✅ 常量定义
  │   ├── fgoConfig.py          ✅ 配置管理
  │   ├── fgoAndroid.py         ✅ ADB 底层操作
  │   ├── fgoDevice.py          ✅ 设备抽象层
  │   ├── fgoDetect.py          ✅ 状态检测层
  │   ├── fgoFarming.py         ✅ 刷本核心逻辑
  │   ├── fgoMail.py            ⬜ 邮箱功能（待实现）
  │   ├── fgoGacha.py           ⬜ 抽卡功能（待实现）
  │   └── fgoSynthesis.py       ⬜ 强化功能（待实现）
  ├── fgo.py                    ✅ 主入口
  ├── config.json               ✅ 配置文件
  ├── templates/                # 模板图片
  └── common/                   # 旧模块（兼容）
```

---

## 🏗️ 三层架构设计

### 1️⃣ **设备层**（fgoDevice.py + fgoAndroid.py）
```
负责: ADB 操作（截图、点击、滑动、按键）
特点: 低级操作，不依赖游戏逻辑
```

### 2️⃣ **检测层**（fgoDetect.py）
```
负责: 游戏状态识别（模板匹配、颜色分析、OCR）
特点: 中级接口，提供状态查询和按钮寻找
```

### 3️⃣ **逻辑层**（fgoFarming.py、fgoMail.py 等）
```
负责: 业务逻辑（战斗策略、邮箱处理等）
特点: 高级决策，基于检测层的结果制定行动
```

---

## 🚀 快速开始

### Step 1：安装依赖
```bash
cd /Users/kellylott/Downloads/fgo
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2：配置（可选）
编辑 `config.json`：
```json
{
  "device": "127.0.0.1:5555",
  "run_count": 10,
  "farming": {
    "np_strategy": "on_full",
    "attack_card_strategy": "first_three"
  }
}
```

### Step 3：运行
```bash
# 基础运行
python fgo.py

# 指定设备和次数
python fgo.py --device 127.0.0.1:5555 --count 10

# 调试模式
python fgo.py --debug

# 其他模式（开发中）
python fgo.py --mode mail
python fgo.py --mode gacha
```

---

## 📖 核心类说明

### fgoDevice.Device
```python
device = Device("127.0.0.1:5555")
device.screenshot()              # 截图
device.tap(x, y, delay=0.5)     # 点击
device.swipe(x1, y1, x2, y2)    # 滑动
device.press(keycode)            # 按键
```

### fgoDetect.Detect
```python
screen = device.screenshot()
detect = Detect(screen)

# 状态检测
state = detect.detect_battle_state()  # 'attack' | 'loading' | ...

# 颜色识别
hp = detect.get_hp(enemy_idx=0)       # 获取敌人血量
np = detect.get_np(servant_idx=0)     # 获取从者 NP

# 模板匹配
button_pos = detect.find_button("confirm_btn", threshold=0.70)
```

### fgoFarming.Farmer
```python
farmer = Farmer()
farmer.run_once()   # 运行一次刷本
farmer.farm()       # 持续刷本
```

---

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `device` | ADB 设备地址 | `127.0.0.1:5555` |
| `run_count` | 刷本次数（0=无限） | `0` |
| `farming.np_strategy` | NP 释放策略 | `on_full` |
| `farming.attack_card_strategy` | 攻击卡选择 | `first_three` |
| `advanced.debug` | 调试模式 | `false` |

---

## 📊 当前功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 刷本（Farming） | ✅ 完成 | 自动战斗和结算 |
| 邮箱（Mail） | ⬜ 待实现 | 预计下个版本 |
| 抽卡（Gacha） | ⬜ 待实现 | 预计下个版本 |
| 强化（Synthesis） | ⬜ 待实现 | 预计下个版本 |
| 多线程 | ⬜ 待实现 | 后台并行执行 |
| 缓存机制 | ⬜ 待实现 | 减少截图次数 |

---

## 🐛 故障排除

### 问题：设备不可用
```
❌ 设备不可用，请检查 ADB 连接
```
**解决**：
```bash
adb kill-server
adb start-server
adb connect 127.0.0.1:5555
adb devices
```

### 问题：无法找到按钮
```
❌ 无法找到按钮: confirm_btn
```
**解决**：
1. 检查 `templates/confirm_btn.png` 是否存在
2. 降低 `threshold` 值（如 0.60）
3. 检查分辨率是否是 1280×720

### 问题：战斗超时
```
❌ 战斗超时
```
**解决**：
1. 检查 FGO 是否正常运行
2. 检查网络连接
3. 检查队伍配置是否合理

---

## 🚀 后续改进方向

1. **邮箱功能** — 自动领取邮件奖励
2. **抽卡功能** — 自动进行友情点抽卡
3. **强化功能** — 自动强化宝具和技能
4. **多线程** — 后台执行多个任务
5. **缓存机制** — 减少不必要的截图
6. **GUI 界面** — 可视化控制面板

---

## 📝 许可证

MIT License

## 🙏 致谢

参考了 [FGO-py](https://github.com/hgjazhgj/FGO-py) 的架构设计思想。
