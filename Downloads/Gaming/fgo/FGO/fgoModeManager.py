"""模式管理器 - 选择和运行不同的模式"""
from FGO.fgoLogging import get_logger
from FGO.fgoMode1 import Mode1
from FGO.fgoMode2 import Mode2
from FGO.fgoMode3 import Mode3
from FGO.fgoMode4 import Mode4
from FGO.fgoMode5 import Mode5
from FGO.fgoMode6 import Mode6

logger = get_logger("ModeManager")

class ModeManager:
    """模式管理器"""

    MODES = {
        1: Mode1,
        2: Mode2,
        3: Mode3,
        4: Mode4,
        5: Mode5,
        6: Mode6,
    }

    @staticmethod
    def get_mode(mode_id, device, card_strategy="chain_buster"):
        """获取指定模式的实例

        Args:
            mode_id: 模式 ID (1, 2, 3)
            device: 设备对象
            card_strategy: 卡片策略

        Returns:
            Mode 实例
        """
        if mode_id not in ModeManager.MODES:
            logger.error(f"❌ 未知模式: {mode_id}")
            return None

        mode_class = ModeManager.MODES[mode_id]
        logger.info(f"📋 初始化 Mode {mode_id}: {mode_class.__doc__.strip()}")
        return mode_class(device, card_strategy=card_strategy)

    @staticmethod
    def run(mode_id, device, card_strategy="chain_buster", run_count=0):
        """运行指定模式

        Args:
            mode_id: 模式 ID
            device: 设备对象
            card_strategy: 卡片策略
            run_count: 刷本次数 (0=无限)

        Returns:
            bool: 是否成功
        """
        mode = ModeManager.get_mode(mode_id, device, card_strategy)
        if mode is None:
            return False

        try:
            return mode.farm(run_count=run_count)
        except Exception as e:
            logger.exception(f"❌ Mode {mode_id} 执行异常: {e}")
            return False
