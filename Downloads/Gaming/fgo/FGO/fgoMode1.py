"""Mode 1 - 刷素材：智能选卡、最后一波(检测3/3)才放技能+宝具、随便选助战"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode1")


class Mode1(ModeBase):
    """Mode 1 - 刷素材（智能选卡）"""

    # 前面用脸卡省 NP，检测到最后一波(BATTLE x/N 的 x==N)才放技能+宝具
    def should_release_skills(self, wave):
        return self.is_last_wave()

    def use_np(self, wave):
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

    # select_cards(智能选卡) 和 _pick_support(点第一个助战) 均沿用基类默认
