"""常量定义（坐标基于 1920x1080）"""

# 延迟时间（秒）
TAP_DELAY = 0.5
NORMAL_DELAY = 2.0
VERY_LONG_DELAY = 5.0

COORDINATES = {
    # 5 张指令卡位置
    "card_positions": [
        (192, 720),
        (592, 720),
        (965, 720),
        (1333, 720),
        (1741, 720),
    ],
}

# 模板匹配阈值
TEMPLATE_THRESHOLD = 0.70
