"""检测层 — 游戏状态识别"""
import cv2
import numpy as np
from FGO.fgoLogging import get_logger
from FGO.fgoConst import TEMPLATE_THRESHOLD

logger = get_logger("Detect")

class Detect:
    """游戏状态检测类"""

    def __init__(self, screenshot):
        self.screenshot = screenshot
        self.cache = screenshot

    @staticmethod
    def load_template(template_name, template_dir="templates"):
        """加载模板"""
        try:
            import os
            path = os.path.join(template_dir, f"{template_name}.png")
            if os.path.exists(path):
                return cv2.imread(path)
            return None
        except Exception as e:
            logger.error(f"❌ 模板加载失败: {template_name}, {e}")
            return None

    @staticmethod
    def find_template(image, template, threshold=TEMPLATE_THRESHOLD):
        """在图像中找模板"""
        if image is None or template is None:
            return None

        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template_gray.shape
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return (cx, cy)
        return None

    def detect_battle_state(self):
        """检测当前战斗状态

        Returns:
            str: 'attack' | 'result' | 'loading' | 'menu' | 'unknown'
        """
        if self.screenshot is None:
            return 'loading'

        # 检查红色血条（战斗中）
        hsv = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        red_mask = ((h < 10) | (h > 170)) & (s > 100) & (v > 100)
        red_pixels = np.sum(red_mask)

        if red_pixels > 1000:
            return 'attack'

        # 检查下方按钮
        lower_region = self.screenshot[500:, :]
        if np.mean(lower_region) > 100:
            return 'attack'

        return 'loading'

    def find_button(self, template_name, threshold=TEMPLATE_THRESHOLD):
        """找到指定的按钮

        Args:
            template_name: 模板名称
            threshold: 匹配阈值

        Returns:
            tuple: (x, y) 按钮坐标，或 None
        """
        template = self.load_template(template_name)
        if template is None:
            return None

        return self.find_template(self.screenshot, template, threshold)

    def __repr__(self):
        return f"<Detect: screenshot_shape={self.screenshot.shape if self.screenshot is not None else None}>"
