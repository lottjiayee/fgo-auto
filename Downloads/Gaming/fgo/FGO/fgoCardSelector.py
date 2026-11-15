"""卡片选择策略模块"""
import cv2
import numpy as np
from FGO.fgoLogging import get_logger
from FGO.fgoConst import COORDINATES

logger = get_logger("CardSelector")

class CardSelector:
    """卡片选择器 — 支持多种策略"""

    def __init__(self, strategy="chain_buster"):
        self.strategy = strategy
        self.card_positions = COORDINATES["card_positions"]
        logger.info(f"🎴 初始化卡片选择器: 策略 = {strategy}")

    # 卡面 Arts/Buster/Quick 大标志所在区域（卡位 x±90，y 760–900），避开上方人物立绘
    CARD_REGION_Y = (760, 900)
    CARD_REGION_HALF_W = 90

    def detect_card_type(self, screen, card_pos):
        """识别卡片类型：在标志区域里数 红/绿/蓝 高饱和像素，票多者胜
        （红只算真红 0–12/170+，避免把金色铠甲等算成 Buster）

        Returns:
            str: 'arts' | 'buster' | 'quick' | 'unknown'
        """
        x, _ = card_pos
        y1, y2 = self.CARD_REGION_Y
        x1, x2 = x - self.CARD_REGION_HALF_W, x + self.CARD_REGION_HALF_W
        if screen is None or x1 < 0 or x2 > screen.shape[1] or y2 > screen.shape[0]:
            return "unknown"
        hsv = cv2.cvtColor(screen[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        ok = (s > 150) & (v > 120)
        votes = {
            "buster": int(np.sum(ok & ((h <= 12) | (h >= 170)))),
            "quick": int(np.sum(ok & (h >= 40) & (h <= 85))),
            "arts": int(np.sum(ok & (h >= 95) & (h <= 130))),
        }
        best = max(votes, key=votes.get)
        return best if votes[best] > 500 else "unknown"

    def detect_all_cards(self, screen):
        """检测所有卡片及其类型

        Args:
            screen: BGR 图像

        Returns:
            list: [(pos, type), ...] 卡片列表
        """
        cards = []
        for pos in self.card_positions:
            card_type = self.detect_card_type(screen, pos)
            cards.append((pos, card_type))
            logger.debug(f"🎴 卡片 at {pos}: {card_type}")

        return cards

    def select_cards_first_three(self, cards):
        """策略：选前三张"""
        return [cards[i][0] for i in range(min(3, len(cards)))]

    def select_cards_buster_first(self, cards):
        """策略：优先 Buster"""
        buster_cards = [pos for pos, card_type in cards if card_type == "buster"]
        other_cards = [pos for pos, card_type in cards if card_type != "buster"]

        # 优先 Buster，不足则补充其他
        result = buster_cards[:3]
        if len(result) < 3:
            result.extend(other_cards[:3 - len(result)])

        return result[:3]

    def select_cards_chain_buster(self, cards):
        """策略：连续 Buster（链击翻倍）"""
        buster_cards = [pos for pos, card_type in cards if card_type == "buster"]

        # 优先连续选择 Buster，最多 3 张
        if len(buster_cards) >= 3:
            return buster_cards[:3]
        else:
            # Buster 不足 3 张，补充其他卡片
            other_cards = [pos for pos, card_type in cards if card_type != "buster"]
            result = buster_cards + other_cards[:3 - len(buster_cards)]
            return result[:3]

    def select_cards_arts_first(self, cards):
        """策略：优先 Arts（充能）"""
        arts_cards = [pos for pos, card_type in cards if card_type == "arts"]
        other_cards = [pos for pos, card_type in cards if card_type != "arts"]

        result = arts_cards[:3]
        if len(result) < 3:
            result.extend(other_cards[:3 - len(result)])

        return result[:3]

    def select_cards_chain_quick(self, cards):
        """策略：连续 Quick（暴击链）"""
        quick_cards = [pos for pos, card_type in cards if card_type == "quick"]
        other_cards = [pos for pos, card_type in cards if card_type != "quick"]

        result = quick_cards[:3]
        if len(result) < 3:
            result.extend(other_cards[:3 - len(result)])

        return result[:3]

    def select_cards_round_robin(self, cards):
        """策略：轮流从者（避免同一从者连续输出）

        将卡片按从者分组（Servant1、2、3），然后轮流选择，确保每个从者都参与。
        例如：[S1-card, S2-card, S1-card] 或 [S1-card, S2-card, S3-card]

        Args:
            cards: 卡片列表 [(pos, type), ...]
                  位置对应：0-2=Servant1, 3-5=Servant2, 6-8=Servant3

        Returns:
            list: 轮流选中的卡片位置列表
        """
        # 将卡片按从者分组
        servant_cards = [[], [], []]
        for i, (pos, card_type) in enumerate(cards):
            servant_idx = i // 3  # 确定从者编号
            servant_cards[servant_idx].append((pos, card_type))

        logger.debug(f"🎴 按从者分组: S1={len(servant_cards[0])} S2={len(servant_cards[1])} S3={len(servant_cards[2])}")

        # 轮流选择
        selected = []
        servant_idx = 0
        for _ in range(3):  # 需要选 3 张卡
            # 尝试从当前从者选卡
            if servant_cards[servant_idx]:
                pos, card_type = servant_cards[servant_idx].pop(0)
                selected.append(pos)
                logger.debug(f"🎴 轮流选择 Servant{servant_idx + 1}: {card_type} at {pos}")
            else:
                # 当前从者没有卡了，找下一个有卡的从者
                for offset in range(1, 3):
                    next_idx = (servant_idx + offset) % 3
                    if servant_cards[next_idx]:
                        pos, card_type = servant_cards[next_idx].pop(0)
                        selected.append(pos)
                        servant_idx = next_idx
                        logger.debug(f"🎴 轮流选择 Servant{next_idx + 1}: {card_type} at {pos}")
                        break

            # 轮到下一个从者
            servant_idx = (servant_idx + 1) % 3

        return selected[:3]

    # 策略名 → 选卡方法（smart 等同 chain_buster）
    STRATEGIES = {
        "first_three": select_cards_first_three,
        "buster_first": select_cards_buster_first,
        "chain_buster": select_cards_chain_buster,
        "arts_first": select_cards_arts_first,
        "chain_quick": select_cards_chain_quick,
        "smart": select_cards_chain_buster,
        "round_robin": select_cards_round_robin,
    }

    def select(self, screen):
        """根据策略选择卡片（简化版 — 不需要敌人血量）

        Args:
            screen: BGR 图像

        Returns:
            list: 选中的卡片位置列表 [(x, y), ...]
        """
        cards = self.detect_all_cards(screen)

        strategy_fn = self.STRATEGIES.get(self.strategy)
        if strategy_fn is None:
            logger.warning(f"⚠️  未知策略: {self.strategy}，使用默认")
            strategy_fn = CardSelector.select_cards_first_three
        selected = strategy_fn(self, cards)

        logger.info(f"🎴 策略 {self.strategy}: 选择 {len(selected)} 张卡片")
        return selected
