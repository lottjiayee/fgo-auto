"""Mode 5 - 单刷活动周回（按 records/mode5_turn1.md 实录，2026-11-15 第 2 次演示版）
队伍：1 号位 Uーオルガマリー（助战）／2 号位 ファントム／3 号位 マーリン，替补第 1 位 諸葛孔明
第 1 回合：ファントム 技能3、2、1 → 换人（ファントム↔孔明）→ 孔明 1(→1号位)、2、3
  → マーリン 1、2、3(→1号位) → 御主技能 2(→1号位) → オルガマリー 3、2、1 → Attack → 2 张 Buster + 1 号位宝具（第 3 张）
之后的回合（没打完时）：同样出卡
助战：找 Uーオルガマリー —— 名字(support_olga.png) + 礼装(support_olga_ce.png) + 头像(support_olga_face.png)
  礼装必须对上（REQUIRE_CE）；同一屏里 名字+礼装+头像 > 名字+礼装；
  找不到就一直滑动+刷新，直到找到为止（没有名字模板时才退回点第二行）"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoDetect import Detect
from FGO.fgoConst import NORMAL_DELAY
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode5")

# 头像 / 礼装中心相对名字中心的位置（由截图量得，1920x1080）
FACE_DX, FACE_DY = -434, -66
CE_DX, CE_DY = -417, 72


# ---- 实录坐标（1920x1080，2026-11-15 实录）----
# 技能按钮：(从者, 技能) → 坐标
SKILL = {
    (1, 1): (124, 865), (1, 2): (251, 860), (1, 3): (375, 847),
    (2, 1): (571, 852), (2, 2): (732, 850), (2, 3): (855, 870),
    (3, 1): (1063, 870), (3, 2): (1196, 874), (3, 3): (1319, 864),
}
TARGET_SERVANT1 = (490, 580)   # 「対象を選択してください」弹窗里的 1 号位立绘中心
SKIP_TAP = (1000, 420)         # 战场中间地面：点两下跳过技能动画（在下方头像之上，点到不会开详情）
SKILL_ANIM_WAIT = 1.0          # 点完跳过后停 1 秒就放下一个（不再等 Attack）
NP_SERVANT1 = (606, 365)       # 选卡界面上方 1 号位宝具

# 御主技能：右侧「マスタースキル」按钮 → 展开 3 个图标
MASTER_BTN = (1776, 471)
MASTER_SKILL = {1: (1360, 471), 2: (1473, 471), 3: (1641, 471)}
# 换人（御主技能 3「オーダーチェンジ」）弹窗
ORDER_START2 = (500, 500)      # Starting Member 第 2 位（ファントム）
ORDER_SUB1 = (1100, 500)       # Sub Member 第 1 位（諸葛孔明）
ORDER_EXEC = (960, 935)        # 「入れ替え実行」

# 第 1 回合步骤：
#   ("skill", 从者, 技能, 选目标)  选目标: True=要选 1 号位 / False=不用 / None=没录到，放完看一眼有弹窗就选 1 号位
#   ("master", 技能, 选目标)
#   ("order_change",)
# 队伍：1 号位 Uーオルガマリー（助战）/ 2 号位 ファントム / 3 号位 マーリン，替补第 1 位 諸葛孔明
TURN1_STEPS = [
    ("skill", 2, 3, False), ("skill", 2, 2, False), ("skill", 2, 1, False),  # ファントム 技能3→2→1
    ("order_change",),                                   # ファントム ↔ 諸葛孔明
    ("skill", 2, 1, True),                               # 孔明 技能1 → 1 号位
    ("skill", 2, 2, False), ("skill", 2, 3, False),      # 孔明 技能2、3
    ("skill", 3, 1, False), ("skill", 3, 2, False),      # マーリン 技能1、2
    ("skill", 3, 3, True),                               # マーリン 技能3 → 1 号位
    ("master", 2, True),                                 # 御主技能 2「魔力強化」→ 1 号位（要在オルガマリー 技能之前）
    ("skill", 1, 3, False), ("skill", 1, 2, False), ("skill", 1, 1, False),  # オルガマリー 技能3→2→1
]


class Mode5(ModeBase):
    """Mode 5 - 单刷活动周回（换人孔明、技能和御主技能都给 1 号位 / 2 张 Buster + 1 号位宝具）"""

    REQUIRE_CE = True  # True=必须带这张礼装；False=礼装只是加分项
    wait_loading_after_start = True  # 第 1 回合就放技能，先等读条结束，免得被开场动画吃掉点击
    LAST_WAVE_TIMEOUT = 60  # 一回合清场：宝具动画 + BATTLE FINISH 实测约 50s

    def __init__(self, device, card_strategy="chain_buster"):
        super().__init__(device, card_strategy=card_strategy)
        self.olga_name = Detect.load_template("support_olga", template_dir="templates")
        self.olga_face = Detect.load_template("support_olga_face", template_dir="templates")
        self.olga_ce = Detect.load_template("support_olga_ce", template_dir="templates")
        self.target_select = Detect.load_template("target_select", template_dir="templates")
        self.order_change = Detect.load_template("order_change", template_dir="templates")  # 换人弹窗「入れ替え実行」

    @staticmethod
    def _part_matches(screen, name_pos, template, dx, dy, threshold=0.80):
        """名字所在那一行，相对名字 (dx, dy) 处是否对得上 template（头像/礼装）"""
        if template is None:
            return False
        cx, cy = name_pos[0] + dx, name_pos[1] + dy
        h, w = template.shape[:2]
        y1, y2 = max(0, cy - h // 2 - 30), min(screen.shape[0], cy + h // 2 + 30)
        x1, x2 = max(0, cx - w // 2 - 30), min(screen.shape[1], cx + w // 2 + 30)
        region = screen[y1:y2, x1:x2]
        if region.shape[0] < h or region.shape[1] < w:
            return False  # 那一行在屏幕边缘，礼装/头像没露全 → 滑动后再看
        return Detect.find_template(region, template, threshold=threshold) is not None

    def _locate_olga(self, screen):
        names = Detect.find_all_templates(screen, self.olga_name, threshold=0.80)
        if not names:
            return None
        need_ce = self.REQUIRE_CE and self.olga_ce is not None  # 没礼装模板就不强制
        best, best_score = None, -1
        for pos in names:
            ce = self._part_matches(screen, pos, self.olga_ce, CE_DX, CE_DY)
            face = self._part_matches(screen, pos, self.olga_face, FACE_DX, FACE_DY)
            if need_ce and not ce:
                continue
            score = ce * 2 + face
            if score > best_score:
                best, best_score, best_desc = pos, score, ("礼装✓" if ce else "礼装✗") + (" 头像✓" if face else " 头像✗")
        if best is None:
            logger.info(f"看到 {len(names)} 个 Uーオルガマリー，但礼装不对，继续找")
            return None
        logger.info(f"选中 Uーオルガマリー {best}：{best_desc}")
        return best

    def _pick_support(self):
        """找带指定礼装的 Uーオルガマリー，一直刷新到找到为止；没有名字模板才退回点第二行 (725, 650)"""
        if self.olga_name is not None:
            return self._pick_by_locator(self._locate_olga, max_refresh=None)  # False = 不在助战界面
        logger.warning("没有 templates/support_olga.png，改点第二行助战 (725, 650)")
        self.device.swipe(960, 400, 960, 700, duration=400)  # 滑回列表顶部
        self.device.tap(725, 650, delay=NORMAL_DELAY)
        return True

    def is_last_wave(self):
        """单刷本只有 1 波（BATTLE 1/1），last_wave.png 只认「3」→ 这里每回合都当最后一波，
        出卡后按最后一波给 35 秒等结算"""
        return True

    def _wait_template(self, template, timeout):
        """等 template 出现；没模板就按旧方式停 0.6 秒当作出现了"""
        if template is None:
            time.sleep(0.6)
            return True
        end = time.time() + timeout
        while time.time() < end:
            if Detect.find_template(self.device.screenshot(), template, threshold=0.80):
                return True
            time.sleep(0.3)
        return False

    def _wait_target_dialog(self, timeout=2.5):
        """等「対象を選択してください」弹窗出现"""
        return self._wait_template(self.target_select, timeout)

    def _skip_anim(self):
        for _ in range(2):
            self.device.tap(*SKIP_TAP, delay=0.08)  # 快速连点两下
        time.sleep(SKILL_ANIM_WAIT)

    def _tap_master(self, skill):
        """等上一个技能动画播完（Attack 按钮回来）→ 展开御主技能 → 点第 skill 个
        动画中点「マスタースキル」会被当成跳过动画吃掉，菜单打不开"""
        self.wait_attack_ready(stable_s=0.5, timeout=8)
        self.device.tap(*MASTER_BTN, delay=0.8)
        self.device.tap(*MASTER_SKILL[skill], delay=0.3)

    def _use(self, name, tap, need_target):
        """tap() 点出技能；need_target: True=等弹窗选 1 号位 / False=不选 / None=看一眼，有弹窗才选"""
        tap()
        if need_target is None:
            time.sleep(0.5)
            if self.target_select is not None and Detect.find_template(
                    self.device.screenshot(), self.target_select, threshold=0.80):
                logger.info(f"{name} 弹出选目标 → 1 号位")
                self.device.tap(*TARGET_SERVANT1, delay=0.3)
        elif need_target:
            ok = self._wait_target_dialog()
            if not ok:
                # 上一个技能动画还没播完、这一下被吃掉 → 跳过动画、停 1 秒，再点一次
                logger.info(f"{name} 弹窗没出来，跳过动画后再点一次")
                self._skip_anim()
                tap()
                ok = self._wait_target_dialog()
            if not ok:
                # 两次都没出现，不点目标，免得点到头像打开详情面板
                logger.warning(f"{name} 没出现选目标弹窗，跳过")
                return
            self.device.tap(*TARGET_SERVANT1, delay=0.3)
        self._skip_anim()

    def _order_change(self):
        """御主技能 3 换人：Starting 第 2 位 ↔ Sub 第 1 位 → 入れ替え実行"""
        logger.info("换人：ファントム ↔ 諸葛孔明")
        self._tap_master(3)
        if not self._wait_template(self.order_change, 3):
            logger.info("换人弹窗没出来，跳过动画后再点一次")
            self._skip_anim()
            self._tap_master(3)
            if not self._wait_template(self.order_change, 3):
                logger.warning("没出现换人弹窗，跳过换人（后面孔明的技能会点空）")
                self._skip_anim()
                return
        self.device.tap(*ORDER_START2, delay=0.4)
        self.device.tap(*ORDER_SUB1, delay=0.4)
        self.device.tap(*ORDER_EXEC, delay=0.3)
        time.sleep(2.5)                                   # 换人动画
        self.wait_attack_ready(stable_s=1.0, timeout=15)

    # 第 1 回合放技能（基类默认 should_release_skills: wave == skill_wave == 1）
    def release_skills(self):
        logger.info("第 1 回合 → 按实录放技能 + 换人 + 御主技能")
        self.wait_attack_ready(stable_s=1.5, timeout=30)   # 敌方开场 buff 演出结束再开始
        for step in TURN1_STEPS:
            if step[0] == "skill":
                _, servant, skill, need_target = step
                x, y = SKILL[(servant, skill)]
                self._use(f"{servant} 号位技能{skill}",
                          lambda x=x, y=y: self.device.tap(x, y, delay=0.3), need_target)
            elif step[0] == "master":
                _, skill, need_target = step
                self._use(f"御主技能{skill}", lambda skill=skill: self._tap_master(skill), need_target)
            elif step[0] == "order_change":
                self._order_change()
        time.sleep(1.0)

    def do_cards(self, wave):
        """2 张 Buster → 1 号位宝具（第 3 张，跟实录一样）；宝具没出来就补第 3 张卡"""
        logger.info("出卡 → 2 张 Buster + 1 号位宝具")
        cards = self.select_buster_cards(3)
        self.tap_cards(cards[:2])
        self.device.tap(*NP_SERVANT1, delay=1.2)
        if self._on_card_select(self.device.screenshot()):
            logger.info("宝具没出（没充能？）→ 补第 3 张卡")
            self.tap_cards(cards[2:3])
