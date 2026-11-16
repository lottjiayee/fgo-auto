"""Android ADB 操作（底层）"""
import subprocess
import time
import io
from PIL import Image
import cv2
import numpy as np
from FGO.fgoLogging import get_logger

logger = get_logger("Android")

class Android:
    """Android 设备操作类"""

    def __init__(self, device="127.0.0.1:5555"):
        self.device = device
        self.available = self.check_connection()

    def check_connection(self, retries=3):
        """检查设备连接（带重试，避免 ADB 瞬时抽风直接退出）"""
        for attempt in range(1, retries + 1):
            try:
                result = subprocess.run(
                    f"adb -s {self.device} shell echo ok",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"✅ 设备连接成功: {self.device}")
                    return True
                logger.warning(f"⚠️  连接失败 ({attempt}/{retries})，重试...")
            except Exception as e:
                logger.warning(f"⚠️  连接检查异常 ({attempt}/{retries}): {e}")

            if attempt < retries:
                # 重试前尝试重新连接
                subprocess.run(f"adb connect {self.device}",
                               shell=True, capture_output=True, timeout=5)
                time.sleep(1)

        logger.error(f"❌ 设备连接失败: {self.device}（已重试 {retries} 次）")
        return False

    use_raw_screencap = True  # 原始像素比 PNG 快一倍（实测 0.3–0.5s vs 0.7–1.0s，省了模拟器里压 PNG）

    def _screenshot_raw(self):
        """screencap 不加 -p：头部 12/16 字节（宽、高、格式）+ RGBA 像素"""
        out = subprocess.run(f"adb -s {self.device} exec-out screencap",
                             shell=True, capture_output=True, timeout=10).stdout
        if len(out) < 12:
            return None
        w, h, fmt = (int.from_bytes(out[i:i + 4], "little") for i in (0, 4, 8))
        size = w * h * 4
        if fmt != 1 or not (0 < w <= 8192 and 0 < h <= 8192) or len(out) < size + 12:
            return None  # 不是 RGBA_8888 → 交给 PNG
        pixels = np.frombuffer(out[len(out) - size:], dtype=np.uint8).reshape(h, w, 4)
        return cv2.cvtColor(pixels, cv2.COLOR_RGBA2BGR)

    def screenshot(self):
        """截取屏幕（BGR）。先取原始像素，不行再用 PNG"""
        try:
            if self.use_raw_screencap:
                img = self._screenshot_raw()
                if img is not None:
                    return img
                self.use_raw_screencap = False
                logger.info("原始截图格式不支持，改用 PNG 截图")
            result = subprocess.run(
                f"adb -s {self.device} exec-out screencap -p",
                shell=True, capture_output=True, timeout=10
            )
            if result.stdout:
                img = Image.open(io.BytesIO(result.stdout))
                return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            return None
        except Exception as e:
            logger.error(f"❌ 截图失败: {e}")
            return None

    def tap(self, x, y, delay=0.5):
        """点击屏幕"""
        try:
            subprocess.run(
                f"adb -s {self.device} shell input tap {int(x)} {int(y)}",
                shell=True, capture_output=True, timeout=5
            )
            time.sleep(delay)
            logger.debug(f"点击: ({x}, {y})")
        except Exception as e:
            logger.error(f"❌ 点击失败: {e}")

    def swipe(self, x1, y1, x2, y2, duration=300):
        """滑动屏幕"""
        try:
            subprocess.run(
                f"adb -s {self.device} shell input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {duration}",
                shell=True, capture_output=True, timeout=5
            )
            time.sleep(0.5)
            logger.debug(f"滑动: ({x1}, {y1}) → ({x2}, {y2})")
        except Exception as e:
            logger.error(f"❌ 滑动失败: {e}")

    def press(self, keycode):
        """按键"""
        try:
            subprocess.run(
                f"adb -s {self.device} shell input keyevent {keycode}",
                shell=True, capture_output=True, timeout=5
            )
            time.sleep(0.3)
            logger.debug(f"按键: {keycode}")
        except Exception as e:
            logger.error(f"❌ 按键失败: {e}")
