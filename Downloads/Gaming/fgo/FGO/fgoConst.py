"""常量定义"""

# 版本信息
VERSION = "2.0.0"

# 屏幕分辨率
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
# 原始分辨率 (用于坐标缩放参考)
ORIGINAL_WIDTH = 1440
ORIGINAL_HEIGHT = 900

# ADB 默认设备
DEFAULT_DEVICE = "127.0.0.1:5555"

# 延迟时间（秒）
TAP_DELAY = 0.5
NORMAL_DELAY = 2.0
VERY_LONG_DELAY = 5.0

# 坐标常量（1920x1080 分辨率，从 1440x900 缩放）
COORDINATES = {
    # 卡片位置（CardSelector 检测卡片类型用）
    "card_positions": [
        (192, 720),   # 144, 600
        (592, 720),   # 444, 600
        (965, 720),   # 724, 600
        (1333, 720),  # 1000, 600
        (1741, 720),  # 1306, 600
    ],
}

# 模板匹配阈值
TEMPLATE_THRESHOLD = 0.70

# 卡片类型和颜色识别
CARD_TYPES = {
    "arts": {"color": "蓝色", "hsv": {"h": (100, 130), "s": (100, 255), "v": (100, 255)}},
    "buster": {"color": "红色", "hsv": {"h": (0, 30), "s": (100, 255), "v": (100, 255)}},
    "quick": {"color": "绿色", "hsv": {"h": (40, 80), "s": (100, 255), "v": (100, 255)}},
}
