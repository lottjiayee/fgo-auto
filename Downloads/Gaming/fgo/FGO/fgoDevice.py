"""设备抽象层"""
from FGO.fgoAndroid import Android
from FGO.fgoLogging import get_logger
from FGO.fgoConst import TAP_DELAY

logger = get_logger("Device")

class Device:
    """设备类 — 包装 Android 操作"""

    def __init__(self, device_name="127.0.0.1:5555"):
        self.android = Android(device_name)
        self.name = device_name
        self.available = self.android.available

    def screenshot(self):
        """截图"""
        return self.android.screenshot()

    def tap(self, x, y, delay=None):
        """点击"""
        if delay is None:
            delay = TAP_DELAY
        self.android.tap(x, y, delay)

    def swipe(self, x1, y1, x2, y2, duration=300):
        """滑动"""
        self.android.swipe(x1, y1, x2, y2, duration)

    def press(self, keycode):
        """按键"""
        self.android.press(keycode)

    def __repr__(self):
        return f"<Device: {self.name}, available={self.available}>"

# 全局设备实例
device = None

def initialize_device(device_name="127.0.0.1:5555"):
    """初始化全局设备"""
    global device
    device = Device(device_name)
    if device.available:
        logger.info(f"✅ 设备初始化成功: {device_name}")
    else:
        logger.error(f"❌ 设备初始化失败: {device_name}")
    return device
