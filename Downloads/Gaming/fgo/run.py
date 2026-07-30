#!/usr/bin/env python3
"""FGO 自动刷本启动器"""
import os
import sys
import subprocess
import argparse

def run():
    """启动 FGO 脚本"""
    # 项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # 激活虚拟环境
    venv_bin = os.path.join(project_dir, "venv", "bin", "activate")

    parser = argparse.ArgumentParser(
        description="FGO 自动刷本脚本启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py                                    # 交互式选择模式
  python run.py --script-mode 1 --debug           # Mode 1 + 调试
  python run.py --count 10 --strategy round_robin # 指定次数和策略
        """
    )

    parser.add_argument('--script-mode', type=int, choices=[1, 2, 3],
                        help='脚本模式 (1=通用, 2=简化, 3=高级)')
    parser.add_argument('--device', default='127.0.0.1:5555',
                        help='ADB 设备地址 (默认: 127.0.0.1:5555)')
    parser.add_argument('--count', type=int, default=0,
                        help='刷本次数 (0=无限, 默认: 0)')
    parser.add_argument('--strategy', '--card-strategy',
                        default='round_robin',
                        choices=['first_three', 'buster_first', 'chain_buster', 'arts_first', 'chain_quick', 'smart', 'round_robin'],
                        help='卡片策略 (默认: round_robin)')
    parser.add_argument('--debug', action='store_true',
                        help='启用调试模式')

    args = parser.parse_args()

    # 构建命令
    cmd = [sys.executable, os.path.join(project_dir, 'fgo.py')]

    if args.script_mode:
        cmd.extend(['--script-mode', str(args.script_mode)])

    cmd.extend(['--device', args.device])
    cmd.extend(['--count', str(args.count)])
    cmd.extend(['--card-strategy', args.strategy])

    if args.debug:
        cmd.append('--debug')

    print("="*60)
    print("FGO 自动刷本脚本 v2.0")
    print("="*60)
    print(f"\n🚀 启动命令: {' '.join(cmd)}\n")

    # 执行
    try:
        result = subprocess.run(cmd, cwd=project_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run()
