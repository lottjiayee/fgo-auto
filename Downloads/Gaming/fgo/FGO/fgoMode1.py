"""Mode 1 - 刷素材：智能选卡、最后一波(检测3/3)放技能 + 3 个宝具全点 + 3 张卡、随便选助战"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoModeBase import ModeBase
from FGO.fgoConst import NORMAL_DELAY, COORDINATES

logger = get_logger("Mode1")


class Mode1(ModeBase):
    """Mode 1 - 刷素材（智能选卡）"""

    # 最后一波 3 个宝具动画长：出卡到结算实测 20–62 秒，等 67 秒才判超时
    LAST_WAVE_TIMEOUT = 67

    # 前面用脸卡省 NP，检测到最后一波(BATTLE x/N 的 x==N)才放技能+宝具
    def should_release_skills(self, wave):
        return self.is_last_wave()

    def release_skills(self):
        """刷素材：最后一波只放 servant 3 的技能1、技能2（servant 1/2 不放，避免误触详情面板）"""
        logger.info("放 servant 3 技能...")
        # 技能1：点 → 确认×2 → [0.7s]
        self.device.tap(1067, 864, delay=0.2)
        for _ in range(2):
            self.device.tap(969, 313, delay=0.2)
        time.sleep(0.7)
        # 技能2：点 → [0.3s] → 确认×2（无敌人）
        self.device.tap(1187, 864, delay=0.2)
        time.sleep(0.3)
        for _ in range(2):
            self.device.tap(969, 313, delay=0.2)
        time.sleep(1.2)

    def _pick_support(self):
        """刷素材：随便点一个助战（725, 650）"""
        time.sleep(1.5)  # 等助战界面稳定
        logger.info("随便选一个助战 (725, 650)")
        self.device.tap(725, 650, delay=NORMAL_DELAY)
        return True

    def do_cards(self, wave):
        """前面的波：智能选 3 张卡（不放宝具）
        最后一波(3/3)兜底：3 个宝具全点（没充能的点了无效）+ 智能选 3 张卡，不够用固定卡位补满"""
        if not self.is_last_wave():
            self.tap_cards(self.select_cards())
            return
        logger.info("最后一波 → 3 个宝具全点 + 3 张指令卡")
        self.fire_nps(3)
        time.sleep(0.4)  # 等指令卡界面稳定再截图认卡
        cards = list(self.select_cards())[:3]
        for p in COORDINATES["card_positions"]:
            if len(cards) >= 3:
                break
            if p not in cards:
                cards.append(p)
        self.tap_cards(cards)
