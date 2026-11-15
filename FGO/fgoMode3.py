"""Mode 3 - extra1（仅适用 3 波本）：
  wave1 → 智能选卡
  wave2 → 从者1,2宝具 + 3卡(优先Buster)
  wave3 → 从者2,3宝具 + 3卡(优先Buster)
  最后一波(3/3) 开打前额外：御主换人 → S2三技能+S3两技能 → 第1御主技能
"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode3")


class Mode3(ModeBase):
    """Mode 3 - extra1（wave1卡片 / wave2 从者1,2宝具 / wave3 从者2,3宝具 / 3波换人+技能）"""

    def should_release_skills(self, wave):
        # 只在最后一波(3/3)做：御主换人 + 从者技能 + 御主技能
        return self.is_last_wave()

    def release_skills(self):
        """第3波开打前：点(440,108) → 御主换人 → S2三技能+S3两技能 → 第1御主技能"""
        logger.info("第3波 → 换人 + S2/S3技能 + 御主技能")
        # 开场先点一下 (330,90 → 440,108)，等 3s 再开御主技能
        self.device.tap(440, 108, delay=3.0)
        # 换人
        self.device.tap(1805, 455, delay=1.0)   # マスタースキル 御主技能
        self.device.tap(1612, 491, delay=1.0)   # 第3个御主技能（换人）
        self.device.tap(513, 528, delay=0.3)    # 选从者1
        self.device.tap(1107, 528, delay=0.5)   # 选从者2
        self.device.tap(960, 900, delay=1.0)    # 确定换人
        # 快速点两下确认坐标，跳过换人动画
        self.device.tap(969, 313, delay=0.5)
        self.device.tap(969, 313, delay=0.5)
        time.sleep(1.0)  # 间隔1s，等换人动画结束再放技能

        def cast(sx, sy):
            self.device.tap(sx, sy, delay=0.2)
            for _ in range(2):
                self.device.tap(969, 313, delay=0.2)
            time.sleep(0.8)

        # S2 三技能（坐标对齐基类：技能1,2 y=864，技能3 y=840）
        for sx, sy in ((593, 864), (720, 864), (853, 840)):
            cast(sx, sy)
        time.sleep(0.5)  # S2 点完隔 0.5s 再点 S3
        # S3 两技能（y=864）
        for sx, sy in ((1067, 864), (1187, 864)):
            cast(sx, sy)
        time.sleep(1.0)

        # 全部技能后：再开御主技能 → 放第1个御主技能 → 确认×2 → 确定
        self.device.tap(1805, 455, delay=1.0)   # マスタースキル
        self.device.tap(1353, 462, delay=0.3)   # 第1个御主技能 (1015,385)
        for _ in range(2):
            self.device.tap(969, 313, delay=0.2)  # 确认×2
        self.device.tap(960, 900, delay=1.0)    # 确定 (720,750)
        time.sleep(1.0)

    def do_cards(self, wave):
        time.sleep(1.2)  # 等选卡界面+BATTLE计数器稳定再判波数，避免过渡帧误判
        if self.is_wave_1():
            logger.info("第1波 → 选卡片")
            self.tap_cards(self.select_cards())
        elif self.is_last_wave():
            logger.info("第3/3波 → 从者2,3宝具 + 3卡（优先Buster，多1张保险凑组合）")
            self.fire_nps([1, 2])   # 从者2、3 的宝具
            self.tap_cards(self.select_buster_cards(3))
            time.sleep(4)           # 2宝具动画长，多等避免卡顿
        else:
            logger.info("第2/3波 → 从者1,2宝具 + 3卡（优先Buster，多1张保险凑组合）")
            self.fire_nps([0, 1])   # 从者1、2 的宝具
            self.tap_cards(self.select_buster_cards(3))
            time.sleep(4)           # 2宝具动画长，多等避免卡顿

    # select_cards(智能选卡) 和 _pick_support(点第一个助战) 均沿用基类默认
