"""日志系统"""
import logging
import sys
import os
import glob
from datetime import datetime

def cleanup_old_logs(keep=30, pattern="fgo_*.log"):
    """日志文件超过 keep 个时删除最旧的，始终保持最多 keep 个"""
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    # 留出 1 个名额给即将创建的新日志
    excess = len(files) - (keep - 1)
    for f in files[:excess] if excess > 0 else []:
        try:
            os.remove(f)
        except OSError:
            pass

def setup_logging(level=logging.INFO):
    """初始化日志"""
    cleanup_old_logs(keep=30)
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'fgo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )

def get_logger(name):
    """获取指定名称的 logger"""
    return logging.getLogger(name)

# 初始化默认日志
setup_logging()
