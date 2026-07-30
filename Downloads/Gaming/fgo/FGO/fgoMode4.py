"""Mode 4 - extra2：每一波都放 3 宝具"""
from FGO.fgoLogging import get_logger
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode4")


class Mode4(ModeBase):
    """Mode 4 - extra2（每波 3 宝具）"""

    def do_cards(self, wave):
        logger.info("每波 → 3 宝具 + 保底补满命令卡")
        self.fire_nps(3)
        # 保底：若有宝具没充能，凑不满 3 张会卡在选卡界面 → 补点命令卡填满推进
        # （3 张宝具都放出时已自动结算，这几下补点落在动画上无害）
        self.tap_cards(self.select_buster_cards(3))
