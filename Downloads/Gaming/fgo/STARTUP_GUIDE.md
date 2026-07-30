# FGO 自动刷本 — 启动指南

## 🚀 快速启动

### 最简单的方式（推荐）

```bash
cd /Users/kellylott/Downloads/fgo
python run.py
```

这会：
1. 检查虚拟环境
2. 自动激活环境
3. 进入交互式模式选择菜单
4. 运行脚本

---

## 📋 三种启动方式

### 方式 1️⃣ ：Python 启动脚本（推荐）

```bash
python run.py [选项]
```

**优点：** 跨平台，自动管理虚拟环境

**例子：**
```bash
# 交互式选择模式
python run.py

# 指定 Mode 1 + 调试
python run.py --script-mode 1 --debug

# 指定次数和策略
python run.py --count 10 --strategy round_robin --debug

# 完整选项
python run.py --script-mode 1 --device 127.0.0.1:5555 --count 10 --strategy round_robin --debug
```

### 方式 2️⃣ ：Bash 启动脚本

```bash
./start.sh [选项]
```

**优点：** Shell 脚本，轻量级

**例子：**
```bash
# 交互式
./start.sh

# 指定参数
./start.sh --script-mode 1 --debug
./start.sh --mode 1 --count 10 --strategy round_robin --debug
```

### 方式 3️⃣ ：原始 Python

```bash
source venv/bin/activate
python fgo.py [选项]
```

**优点：** 完全控制，查看详细输出

**例子：**
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行
python fgo.py --script-mode 1 --debug
python fgo.py --count 10 --card-strategy round_robin --debug
```

---

## 🎯 命令行选项

| 选项 | 值 | 说明 |
|------|-----|------|
| `--script-mode` | 1, 2, 3 | 脚本模式（默认交互选择） |
| `--device` | ADDR | ADB 设备地址（默认 127.0.0.1:5555） |
| `--count` | N | 刷本次数（0=无限，默认 0） |
| `--card-strategy` | 见下 | 卡片策略（默认 round_robin） |
| `--debug` | - | 启用调试模式 |

### 卡片策略

| 策略 | 说明 |
|------|------|
| `round_robin` | 轮流从者（推荐） |
| `chain_buster` | 连续 Buster（链击） |
| `buster_first` | 优先 Buster |
| `arts_first` | 优先 Arts（充能） |
| `chain_quick` | 连续 Quick（暴击） |
| `smart` | 智能选择 |
| `first_three` | 选前三张 |

---

## 📝 常见用法

### 基础刷本（交互选择）
```bash
python run.py
```

### Mode 1 + 调试输出
```bash
python run.py --script-mode 1 --debug
```

### 刷 10 次
```bash
python run.py --count 10 --debug
```

### 自定义策略 + 指定设备
```bash
python run.py --strategy chain_buster --device 192.168.1.100:5555 --debug
```

### 无限刷本
```bash
python run.py --count 0 --debug
```

---

## 🔧 虚拟环境管理

### 首次运行（自动）
启动脚本会自动创建虚拟环境：
```bash
python run.py  # 自动创建 venv 并安装依赖
```

### 手动激活
```bash
source venv/bin/activate
```

### 手动停用
```bash
deactivate
```

### 重建虚拟环境
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -q opencv-python numpy Pillow
```

---

## ✅ 检查清单

运行前检查：

- [ ] ADB 连接正常：`adb devices`
- [ ] FGO 已启动并进入选择关卡界面
- [ ] 虚拟环境存在：`ls venv/`
- [ ] 配置文件存在：`ls config.json`
- [ ] 模板存在：`ls templates/`

---

## 🐛 故障排除

### 虚拟环境问题
```bash
# 重建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install opencv-python numpy Pillow
```

### ADB 连接问题
```bash
# 检查连接
adb devices

# 重新连接
adb kill-server
adb start-server
adb connect 127.0.0.1:5555
```

### 权限问题
```bash
# 给启动脚本执行权限
chmod +x start.sh run.py
```

---

## 📖 更多信息

- 快速参考：[QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- 项目结构：[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- 更新日志：[CHANGELOG_v2.md](CHANGELOG_v2.md)

---

**现在就开始吧！** 🎮

```bash
python run.py --debug
```
