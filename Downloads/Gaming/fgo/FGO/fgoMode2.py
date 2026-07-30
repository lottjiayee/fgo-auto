"""Mode 2 - 刷钱（QP）：技能 wave1、每波宝具、随机选卡"""
import random
from FGO.fgoModeBase import ModeBase


class Mode2(ModeBase):
    """Mode 2 - 刷钱（QP）简化版"""

    def __init__(self, device, card_strategy="chain_buster"):
        super().__init__(device, card_strategy=card_strategy)
        self.skill_wave = 1   # wave 1 放技能

    def select_cards(self):
        """随机选 3 张卡"""
        cards = [(192, 720), (592, 720), (965, 720), (1333, 720), (1741, 720)]
        return random.sample(cards, 3)

    def _pick_support(self):
        """刷钱：模板识别 Castoria 助战"""
        return self._pick_castoria()

    # use_np 默认每波都用宝具（刷钱），沿用基类
