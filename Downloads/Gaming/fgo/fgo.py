#!/usr/bin/env python3
"""FGO 自动刷本 — 主入口"""

import sys
import argparse
from FGO.fgoLogging import get_logger
from FGO.fgoDevice import initialize_device
from FGO.fgoConfig import config
from FGO.fgoModeManager import ModeManager

logger = get_logger("Main")

def select_script_mode():
    """交互式脚本模式选择"""
    print("\n" + "="*60)
    print("FGO 自动刷本脚本 v2.0 — 模式选择")
    print("="*60)
    print("\n📋 选择脚本模式:")
    print("  1. Mode 1 - 刷素材（智能选卡，最后一波放技能+宝具）")
    print("  2. Mode 2 - 刷钱 QP（随机选卡，wave1 放技能，每波宝具）⭐")
    print("  3. Mode 3 - extra1（wave1卡片 / wave2 从者1,2宝具 / wave3 从者2,3宝具+换人技能）")
    print("  4. Mode 4 - extra2（每波 3 宝具）")
    print("  5. Mode 5 - extra3（前两波卡片 / 3/3 用1单体宝具+2Arts）")

    while True:
        choice = input("\n请选择 [1-5] (默认 2): ").strip()
        if not choice:
            return 2
        if choice in ['1', '2', '3', '4', '5']:
            return int(choice)
        print("❌ 输入错误，请选择 1-5")

def main():
    parser = argparse.ArgumentParser(
        description="FGO 自动刷本脚本 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python fgo.py                    # 使用默认配置启动
  python fgo.py --device 127.0.0.1:5555 --count 10  # 指定设备和次数
  python fgo.py --config custom.json              # 使用自定义配置
        """
    )

    parser.add_argument('--device', default='127.0.0.1:5555',
                        help='ADB 设备地址 (默认: 127.0.0.1:5555)')
    parser.add_argument('--count', type=int, default=0,
                        help='刷本次数 (0=无限, 默认: 0)')
    parser.add_argument('--config', default='config.json',
                        help='配置文件路径 (默认: config.json)')
    parser.add_argument('--script-mode', type=int, choices=[1, 2, 3, 4, 5],
                        default=None,
                        help='脚本模式 (1=通用, 2=简化, 3=高级；默认交互式选择)')
    parser.add_argument('--card-strategy', default='round_robin',
                        choices=['first_three', 'buster_first', 'chain_buster', 'arts_first', 'chain_quick', 'smart', 'round_robin'],
                        help='卡片选择策略 (默认: round_robin - 轮流从者)')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')

    args = parser.parse_args()

    # 如果没有指定脚本模式，进入交互式选择
    if args.script_mode is None:
        args.script_mode = select_script_mode()

    # 设置日志
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔧 调试模式已启用")

    logger.info("="*60)
    logger.info("FGO 自动刷本脚本 v2.0")
    logger.info("="*60)
    logger.info(f"📋 脚本模式: Mode {args.script_mode}")

    # 初始化配置
    logger.info(f"📋 加载配置: {args.config}")
    if args.count > 0:
        config.set("run_count", args.count)

    # 初始化设备
    logger.info(f"📱 初始化设备: {args.device}")
    device = initialize_device(args.device)

    if not device.available:
        logger.error("❌ 设备不可用，请检查 ADB 连接")
        return 1

    # 开始刷本
    logger.info(f"🎴 卡片策略: {args.card_strategy}")

    try:
        success = ModeManager.run(
            mode_id=args.script_mode,
            device=device,
            card_strategy=args.card_strategy,
            run_count=args.count
        )

        if success:
            logger.info("✅ 执行完成")
            return 0
        else:
            logger.error("❌ 执行失败")
            return 1

    except KeyboardInterrupt:
        logger.info("⏹️  用户中断")
        return 0
    except Exception as e:
        logger.exception(f"❌ 执行异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
