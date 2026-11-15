# FGO 自动刷本

通过 ADB 控制模拟器（1920×1080），用模板识别 + 固定坐标自动刷本。

## 开始前
1. 游戏里点进要刷的关卡，停在**助战选择界面（サポート選択）**，列表在最顶上。
2. Mode 1 点第二行助战（第一行是 NPC）；Mode 2 自动找 Castoria（`templates/support.png`）。

## 启动

```bash
cd fgo-auto/Downloads/Gaming/fgo
venv/bin/python fgo.py --script-mode 1   # 刷素材
venv/bin/python fgo.py --script-mode 2   # 刷钱 QP
venv/bin/python fgo.py                   # 不带参数 → 菜单选 1-6
```

常用参数：`--count N` 只刷 N 场（不会写进 config.json）、`--card-strategy`、`--device`、`--debug`。

`bash start.sh` 会自动建 venv、装依赖再启动。

## 停止
- 按 **Ctrl + C**（会打印总结）。
- **不要按 Ctrl + Z**，那只是挂起，进程还在。挂起了就 `fg` 再 Ctrl + C，或 `pkill -f fgo.py`。
- 同一时间只跑一个脚本；运行中不要点模拟器。

## 自动停止
- 跑满 `--count` 场数
- AP 不足且已吃满 `apple_limit` 个苹果
- 连续失败 3 次（比如不在助战界面）
- 设备断开

## 模式
- Mode 1：刷素材（智能选卡，最后一波放技能 + 3 个宝具全点 + 3 张卡，点第二行助战）
- Mode 2：刷钱 QP（随机选卡，wave1 放技能，每波宝具，找 Castoria）
- Mode 3：extra1（wave1 卡片 / wave2 从者1,2宝具 / wave3 从者2,3宝具 + 换人技能）
- Mode 4：特别活动周回（每波 3 宝具）
- Mode 6：单刷活动周回 hardcode 版（同 Mode 5 打法；9 个技能、选目标、出卡全按坐标和固定等待，不认弹窗和卡色；只认攻击按钮/结算/BATTLE 等基本画面；助战照样认图找 Uーオルガマリー；出卡固定为 1 号位宝具 + 第 1/2/3 张卡）
- Mode 5：单刷活动周回（按 records/mode5_turn1.md 实录：第 1 回合 9 个技能、目标都给 1 号位，1 号位宝具 + Buster；进本先等读条；助战找带指定礼装的 Uーオルガマリー：名字+礼装必须对上（有无闪光都行），头像加分，找不到就一直刷新到找到为止）

## 配置（config.json）

```json
{
  "run_count": 0,
  "apple_limit": 0
}
```

- `run_count`：默认刷几场，0 = 无限
- `apple_limit`：最多吃几个苹果，0 = 不吃

## 文件
- `fgo.py`：入口
- `FGO/fgoModeBase.py`：共享流程（选助战 / 战斗 / 结算 / 吃苹果 / 连场）
- `FGO/fgoMode1.py` ~ `fgoMode5.py`：各模式差异
- `FGO/fgoCardSelector.py`：选卡策略
- `FGO/fgoDetect.py`：模板匹配；`fgoAndroid.py` / `fgoDevice.py`：ADB 操作
- `templates/`：识别用的截图模板
