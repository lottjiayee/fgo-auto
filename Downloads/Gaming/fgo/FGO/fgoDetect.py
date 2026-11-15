"""检测层 — 模板匹配"""
import os
import cv2
import numpy as np
from FGO.fgoLogging import get_logger
from FGO.fgoConst import TEMPLATE_THRESHOLD

logger = get_logger("Detect")


class Detect:
    """模板加载与匹配（全部为静态方法）"""

    @staticmethod
    def load_template(template_name, template_dir="templates"):
        """加载模板"""
        try:
            path = os.path.join(template_dir, f"{template_name}.png")
            if os.path.exists(path):
                return cv2.imread(path)
            return None
        except Exception as e:
            logger.error(f"❌ 模板加载失败: {template_name}, {e}")
            return None

    @staticmethod
    def find_template(image, template, threshold=TEMPLATE_THRESHOLD):
        """在图像中找模板，返回中心坐标 (x, y) 或 None"""
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

    @staticmethod
    def find_all_templates(image, template, threshold=TEMPLATE_THRESHOLD):
        """找出所有匹配位置（中心坐标列表，按匹配度从高到低，相近的只留一个）"""
        if image is None or template is None:
            return []
        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        h, w = template_gray.shape
        ys, xs = np.where(result >= threshold)
        hits = sorted(zip(result[ys, xs], xs, ys), reverse=True)
        found = []
        for _, x, y in hits:
            c = (int(x) + w // 2, int(y) + h // 2)
            if all(abs(c[0] - f[0]) > w // 2 or abs(c[1] - f[1]) > h for f in found):
                found.append(c)
        return found
