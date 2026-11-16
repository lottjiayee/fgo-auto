"""Mode 6 - 单刷活动周回（hardcode 版）
旧版 Mode 5 打法（2026-11-14 实录：9 个技能给 1 号位，不换人；现在的 Mode 5 已改成换人打法），差别：
  - 9 个技能、5 次选目标全部按坐标 + 固定等待点，不先确认「対象を選択」弹窗
  - 出卡固定：1 号位宝具 + 第 1/2/3 张卡（不认卡的颜色；宝具放出时第 3 张会被忽略）
保留的判断（最基本的画面）：攻击按钮、结算画面、BATTLE 字样、好友申请/AP 回复弹窗
助战：照样认图找带指定礼装的 Uーオルガマリー（沿用 Mode 5）
"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoConst import COORDINATES
from FGO.fgoMode5 import Mode5, SKILL, TARGET_SERVANT1, NP_SERVANT1, SKIP_TAP

# 旧版 Mode 5 打法（2026-11-14 实录）：(从者, 技能, 是否要选目标)
TURN1_SKILLS = [
    (2, 1, True),
    (1, 3, False), (1, 2, False), (1, 1, False),
    (2, 2, True), (2, 3, True),
    (3, 1, False), (3, 2, True), (3, 3, True),
]

logger = get_logger("Mode6")

TARGET_DELAY = 0.8      # 点技能后等选目标弹窗出来
SKILL_ANIM_WAIT = 1.0   # 点两下跳过后停 1 秒就放下一个（不再等 Attack）


class Mode6(Mode5):
    """Mode 6 - 单刷活动周回 hardcode 版（技能/目标/出卡全按坐标）"""

    # Mode 5 现在是 3 波本（按 BATTLE x/3 分波放技能），这里还是单波本的旧规则：
    # 不跟 Mode 5 的加速：hardcode 版靠固定等待，保留原来的时间
    LOADING_PRE_WAIT = 2
    LOADING_POLL = 1.0
    BATTLE_START_SLEEP = 8
    CARD_TAP_DELAY = 0.7
    SKIP_TAPS = 2

    def should_release_skills(self, wave):
        return wave == 1  # 只在第 1 回合放技能

    def is_last_wave(self):
        """单刷本只有 1 波（BATTLE 1/1），last_wave.png 只认「3」→ 每回合都当最后一波"""
        return True

    def release_skills(self):
        logger.info("第 1 回合 → 按坐标放 9 个技能（目标都给 1 号位，不检查弹窗）")
        self.wait_attack_ready(stable_s=1.5, timeout=30)   # 敌方开场 buff 演出结束再开始
        for servant, skill, need_target in TURN1_SKILLS:
            x, y = SKILL[(servant, skill)]
            self.device.tap(x, y, delay=TARGET_DELAY if need_target else 0.3)
            if need_target:
                self.device.tap(*TARGET_SERVANT1, delay=0.3)
            for _ in range(2):
                self.device.tap(*SKIP_TAP, delay=0.08)  # 快速连点两下
            time.sleep(SKILL_ANIM_WAIT)
        time.sleep(1.0)

    def do_cards(self, wave):
        logger.info("出卡 → 1 号位宝具 + 第 1/2/3 张卡（固定）")
        self.device.tap(*NP_SERVANT1, delay=0.3)
        self.tap_cards(COORDINATES["card_positions"][:3])
