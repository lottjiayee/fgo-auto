# FGO v2.0 — 快速参考

## 🚀 5 秒开始

```bash
cd /Users/kellylott/Downloads/fgo
source venv/bin/activate
python fgo.py --debug
```

---

## 📋 常用命令

| 需求 | 命令 |
|------|------|
| 基础刷本 | `python fgo.py --debug` |
| 轮流从者（推荐） | `python fgo.py --card-strategy round_robin --debug` |
| 高伤害输出 | `python fgo.py --card-strategy chain_buster --debug` |
| 智能策略 | `python fgo.py --card-strategy smart --debug` |
| 指定次数 | `python fgo.py --count 10 --debug` |
| 指定设备 | `python fgo.py --device 192.168.1.100:5555 --debug` |

---

## 🎴 卡片策略速查

| 策略 | 命令 | 适用 |
|------|------|------|
| 轮流从者 ⭐ | `round_robin` | **推荐所有** |
| 连续 Buster | `chain_buster` | 高伤害队 |
| 智能选择 | `smart` | 自适应 |
| 优先 Arts | `arts_first` | 充能队 |
| 优先 Quick | `chain_quick` | 暴击队 |
| 优先 Buster | `buster_first` | 单卡队 |
| 前三张 | `first_three` | 快速测试 |

---

## 🔧 配置修改

编辑 `config.json`：

```json
{
  "run_count": 10,                    // 刷本 10 次
  "farming": {
    "attack_card_strategy": "round_robin"  // 卡片策略
  }
}
```

---

## 📱 设备连接

```bash
# 检查连接
adb devices

# 连接 BlueStacks
adb connect 127.0.0.1:5555

# 连接真机
adb connect 192.168.1.100:5555
```

---

## 🐛 调试技巧

| 问题 | 解决 |
|------|------|
| 无法连接设备 | 检查 `adb devices` 输出 |
| 按钮识别失败 | 重新截图 `templates/confirm_btn.png` |
| 血条识别不准 | 检查分辨率是否 1280×720 |
| 卡片选择错误 | 用 `--debug` 查看日志 |

---

## 📊 日志文件位置

```
fgo_YYYYMMDD_HHMMSS.log
```

查看最新日志：
```bash
tail -f fgo_*.log
```

---

## 🎯 工作流程（概览）

```
启动脚本
   ↓
连接设备（ADB）
   ↓
加载配置
   ↓
【循环】
├─ 等待进入战斗（找"確定"按钮）
├─ 自动执行攻击（选卡 → Attack）
├─ 处理结算
└─ 等待 30s 后重复
   ↓
完成或中断
```

---

## 💡 最佳实践

1. **首次运行用 debug 模式**
   ```bash
   python fgo.py --debug
   ```

2. **根据队伍选择策略**
   - 3 主从队 → `round_robin`
   - 1 主 + 2 辅 → `chain_buster`
   - 快速刷本 → `first_three`

3. **定期检查日志**
   ```bash
   tail -20 fgo_*.log
   ```

4. **遇到问题先截图**
   ```bash
   adb -s 127.0.0.1:5555 shell screencap /sdcard/debug.png
   adb pull /sdcard/debug.png ./debug.png
   ```

---

## 📚 更多信息

- 完整文档：`README_v2.md`
- 更新日志：`CHANGELOG_v2.md`
- 配置说明：`config.json`
- 源代码：`FGO/` 目录

---

**现在就试试吧！** 🎮

```bash
python fgo.py --card-strategy round_robin --debug
```
