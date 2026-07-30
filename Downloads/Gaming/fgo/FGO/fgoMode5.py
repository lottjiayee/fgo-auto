"""Mode 5 - extra3：前两波卡片，3/3 波放 1 单体宝具 + 2 Arts"""
from FGO.fgoLogging import get_logger
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode5")


class Mode5(ModeBase):
    """Mode 5 - extra3（前两波卡片 / 3/3 用1单体宝具+2Arts）"""

    def do_cards(self, wave):
        if self.is_last_wave():
            logger.info("最后一波(3/3) → 1单体宝具 + 3卡（多1张保险凑组合）")
            self.fire_nps(1)              # 放 servant1 宝具
            self.device.tap(1440, 582, delay=0.3)  # 单体宝具 → 点敌人选目标
            self.tap_cards(self.select_arts_cards(3))
        else:
            logger.info("非最后波 → 选卡片")
            self.tap_cards(self.select_cards())
