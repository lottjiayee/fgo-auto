"""Mode 5 - 90++周回（活动 3 波本，按 records/mode5_turn1.md 实录，2026-11-16 版）
队伍：1 号位 Uーオルガマリー（助战）／2 号位 諸葛孔明／3 号位 光のコヤンスカヤ，礼装 アトラス院制服，不换人
第 1 波：オルガマリー 技能2→3→1 → コヤンスカヤ 1 → 孔明 3→2→1(→1号位) → コヤンスカヤ 3(→1号位)、2
        → 御主技能 3 → Attack → Buster→Quick→Arts（凑 QAB，不放宝具）
第 2 波：1 号位宝具 → Buster → Buster
第 3 波：オルガマリー 技能2→3→1 → Attack → Buster 优先、不够补 Arts
波数看右上角 BATTLE x/3：1 = 第 1 波，3 = 最后一波，其余当第 2 波；同一波没打完时下回合照这一波的出卡
助战：找 Uーオルガマリー —— 名字(support_olga.png) + 礼装(support_olga_ce.png) + 满破闪光(support_ce_mlb.png) + 头像(support_olga_face.png)
  礼装必须对上（REQUIRE_CE），而且必须满破：礼装右边有黄绿色闪光（REQUIRE_MLB，满破的活动加成显示 +200%）；
  同一屏里 名字+礼装+闪光+头像 > 名字+礼装+闪光；
  找不到就一直滑动+刷新，直到找到为止（没有名字模板时才退回点第二行）"""
import time
from FGO.fgoLogging import get_logger
from FGO.fgoDetect import Detect
from FGO.fgoConst import NORMAL_DELAY, COORDINATES
from FGO.fgoModeBase import ModeBase

logger = get_logger("Mode5")

# 头像 / 礼装中心相对名字中心的位置（由截图量得，1920x1080）
FACE_DX, FACE_DY = -434, -66
CE_DX, CE_DY = -417, 72
MLB_DX, MLB_DY = -326, 97     # 满破闪光（礼装图右下）中心，2026-11-16 实测：满破 1.00、没满破 0.10–0.39


# ---- 实录坐标（1920x1080）----
# 技能按钮：(从者, 技能) → 坐标
SKILL = {
    (1, 1): (124, 865), (1, 2): (251, 860), (1, 3): (375, 847),
    (2, 1): (571, 852), (2, 2): (732, 850), (2, 3): (855, 870),
    (3, 1): (1063, 870), (3, 2): (1196, 874), (3, 3): (1319, 864),
}
TARGET_SERVANT1 = (490, 580)   # 「対象を選択してください」弹窗里的 1 号位立绘中心
SKIP_TAP = (1000, 420)         # 战场中间：弹窗没出来要重点时，先在这里点两下跳过动画（点到不会开详情）
SKILL_ANIM_WAIT = 0.3          # 点完两下跳过后稍停；下一个技能点之前还会等 Attack 按钮回来
NP_SERVANT1 = (606, 365)       # 选卡界面上方 1 号位宝具

# 御主技能：右侧「マスタースキル」按钮 → 展开 3 个图标
MASTER_BTN = (1776, 471)
MASTER_SKILL = {1: (1360, 471), 2: (1473, 471), 3: (1641, 471)}

# 各波放技能的步骤：
#   ("skill", 从者, 技能, 选目标)  选目标: True=等弹窗选 1 号位 / False=不用 / None=录像里看不清，放完等一下，有弹窗才选 1 号位
#   ("master", 技能, 选目标)
STAGE_STEPS = {
    1: [
        ("skill", 1, 2, False), ("skill", 1, 3, False), ("skill", 1, 1, False),  # オルガマリー 驚天動地 → 天衣無縫 → 空前絶後
        ("skill", 3, 1, None),                               # コヤンスカヤ イノベイター・バニー
        ("skill", 2, 3, False), ("skill", 2, 2, False),      # 孔明 軍師の指揮、軍師の忠言
        ("skill", 2, 1, True),                               # 孔明 時計塔の奇宝 → 1 号位
        ("skill", 3, 3, True),                               # コヤンスカヤ NFFスペシャル → 1 号位
        ("skill", 3, 2, None),                               # コヤンスカヤ 殺戮技巧（人）
        ("master", 3, None),                                 # アトラス院制服 メジェドの眼
    ],
    3: [
        ("skill", 1, 2, False), ("skill", 1, 3, False), ("skill", 1, 1, False),  # オルガマリー 2→3→1（冷却已转好）
    ],
}

# 各波出卡：(先点宝具?, 按顺序要的卡色, 要几张普通卡)；要的颜色没有就用别的卡补满
STAGE_CARDS = {
    1: (False, ["buster", "quick", "arts"], 3),               # B→Q→A 凑 QAB
    2: (True, ["buster", "buster"], 2),                       # 宝具 → B → B
    3: (False, ["buster"] * 3 + ["arts"] * 3, 3),            # B 优先，不够补 A
}


class Mode5(ModeBase):
    """Mode 5 - 90++周回（第 1、3 波放技能 / 第 2 波宝具）"""

    REQUIRE_CE = True   # True=必须带这张礼装；False=礼装只是加分项
    REQUIRE_MLB = True  # True=礼装必须满破（右边有闪光），没有就继续找 / 刷新
    wait_loading_after_start = True  # 第 1 回合就放技能，先等读条结束，免得被开场动画吃掉点击
    LAST_WAVE_TIMEOUT = 60
    # 加速（2026-11-16）：读条一结束就开始，不再固定等 8 秒；release_skills 开头还会等 Attack 稳定 1.5 秒
    LOADING_PRE_WAIT = 0.5
    LOADING_POLL = 0.3
    BATTLE_START_SLEEP = 0
    CARD_TAP_DELAY = 0.35
    ONLY_SLOT1 = False     # True = 只放 1 号位技能和御主技能，跳过孔明、コヤンスカヤ（试验用，看能不能打过、快多少）
    SKIP_TAPS = 2          # 放完技能在技能上快速点几下跳过动画（试过 3 下：第 1 波反而慢 8 秒）

    def __init__(self, device, card_strategy="chain_buster"):
        super().__init__(device, card_strategy=card_strategy)
        self.olga_name = Detect.load_template("support_olga", template_dir="templates")
        self.olga_face = Detect.load_template("support_olga_face", template_dir="templates")
        self.olga_ce = Detect.load_template("support_olga_ce", template_dir="templates")
        self.olga_mlb = Detect.load_template("support_ce_mlb", template_dir="templates")
        self.target_select = Detect.load_template("target_select", template_dir="templates")
        self._stages_done = set()

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
        need_mlb = self.REQUIRE_MLB and self.olga_mlb is not None
        best, best_score = None, -1
        skipped = []
        for pos in names:
            ce = self._part_matches(screen, pos, self.olga_ce, CE_DX, CE_DY)
            mlb = self._part_matches(screen, pos, self.olga_mlb, MLB_DX, MLB_DY)
            face = self._part_matches(screen, pos, self.olga_face, FACE_DX, FACE_DY)
            if need_ce and not ce:
                skipped.append("礼装不对")
                continue
            if need_mlb and not mlb:
                skipped.append("礼装没满破（没闪光）")
                continue
            score = ce * 4 + mlb * 2 + face
            if score > best_score:
                best, best_score = pos, score
                best_desc = ("礼装✓" if ce else "礼装✗") + (" 满破✓" if mlb else " 满破✗") + (" 头像✓" if face else " 头像✗")
        if best is None:
            logger.info(f"看到 {len(names)} 个 Uーオルガマリー，但{'、'.join(dict.fromkeys(skipped))}，继续找")
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

    # ---- 波数 ----
    # 基类每场只放一次技能（skills_released），这里第 1、3 波都要放 → 改成按波记录。
    # execute_battle 开场会设 skills_released = False，借这个清空记录。
    @property
    def skills_released(self):
        return False

    @skills_released.setter
    def skills_released(self, value):
        if not value:
            self._stages_done = set()

    def _stage(self):
        """BATTLE x/3：1 → 1，3 → 3，其余 → 2（看本回合等到 Attack 时那一帧）"""
        if self.is_wave_1():
            return 1
        if self.is_last_wave():
            return 3
        return 2

    def should_release_skills(self, wave):
        stage = self._stage()
        return stage in STAGE_STEPS and stage not in self._stages_done

    # ---- 放技能 ----
    def _wait_template(self, template, timeout):
        """等 template 出现；没模板就停 0.6 秒当作出现了"""
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

    def _skip_anim(self, pos=SKIP_TAP):
        """在 pos 快速点两下跳过技能动画。放完技能后 pos = 刚点的技能按钮：
        动画中点 = 跳过；动画已结束 = 技能在冷却，点了没反应；第一下被吃掉时这两下还能补放出来"""
        for _ in range(self.SKIP_TAPS):
            self.device.tap(*pos, delay=0.12)
        time.sleep(SKILL_ANIM_WAIT)

    def _wait_ready(self, timeout=8):
        """等到能点下一个技能：一看到 Attack 按钮（≥0.80）就走，不再要求连续 0.5 秒
        （实测空闲 0.87–1.00，按钮淡出中 0.72–0.73）。
        中途看到选目标弹窗（本来不用选目标却弹了）→ 选 1 号位，免得卡住"""
        end = time.time() + timeout
        while time.time() < end:
            screen = self.device.screenshot()
            if screen is None:
                continue
            if self.target_select is not None and Detect.find_template(screen, self.target_select, 0.80):
                logger.info("有选目标弹窗 → 1 号位")
                self.device.tap(*TARGET_SERVANT1, delay=0.3)
                continue
            if self.attack_template is not None and Detect.find_template(screen, self.attack_template, 0.80):
                return True
            time.sleep(0.1)
        logger.info("等 Attack 按钮超时，照样点下一个")
        return False

    def _tap_master(self, skill):
        """展开御主技能 → 点第 skill 个"""
        self.device.tap(*MASTER_BTN, delay=0.8)
        self.device.tap(*MASTER_SKILL[skill], delay=0.3)

    def _use(self, name, tap, need_target, pos=SKIP_TAP):
        """tap() 点出技能；need_target: True=等弹窗选 1 号位 / False=不选 / None=等一下，有弹窗才选
        每次点之前先等上一个技能动画播完（看到 Attack 按钮，_wait_ready）：动画中点技能会被当成跳过动画吃掉
        （实测：空前絶後 动画长，紧接着点 3 号位技能1 被吃掉，技能没放出来）"""
        raw_tap = tap

        def tap():
            self._wait_ready()
            raw_tap()

        tap()
        if need_target is None:
            # 先确认有没有弹窗再跳动画：跳动画点在战场中间，弹窗开着时会点到 2 号位
            if self.target_select is not None and self._wait_target_dialog(timeout=1.2):
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
        self._skip_anim(pos)  # 在刚点的技能附近点两下跳过动画

    def release_skills(self):
        stage = self._stage()
        logger.info(f"第 {stage} 波 → 按实录放技能")
        self._stages_done.add(stage)
        self.wait_attack_ready(stable_s=1.5, timeout=30)   # 敌方登场演出结束再开始
        steps = STAGE_STEPS[stage]
        if self.ONLY_SLOT1:
            steps = [st for st in steps if st[0] != "skill" or st[1] == 1]
        for step in steps:
            if step[0] == "skill":
                _, servant, skill, need_target = step
                x, y = SKILL[(servant, skill)]
                self._use(f"{servant} 号位技能{skill}",
                          lambda x=x, y=y: self.device.tap(x, y, delay=0.3), need_target, pos=(x, y))
            elif step[0] == "master":
                _, skill, need_target = step
                self._use(f"御主技能{skill}", lambda skill=skill: self._tap_master(skill), need_target,
                          pos=MASTER_SKILL[skill])
        time.sleep(1.0)

    # ---- 出卡 ----
    def _choose_cards(self, wanted, count):
        """按 wanted 的颜色顺序挑 count 张；某个颜色没有就跳过，最后用剩下的卡位补满"""
        time.sleep(0.4)  # 等指令卡界面稳定再截图
        screen = self.device.screenshot()
        left = list(self.card_selector.detect_all_cards(screen)) if screen is not None else []
        chosen = []
        for color in wanted:
            if len(chosen) >= count:
                break
            for card in left:
                if card[1] == color:
                    chosen.append(card[0])
                    left.remove(card)
                    break
        for p in [c[0] for c in left] + list(COORDINATES["card_positions"]):
            if len(chosen) >= count:
                break
            if p not in chosen:
                chosen.append(p)
        return chosen

    def do_cards(self, wave):
        stage = self._stage()
        use_np, wanted, count = STAGE_CARDS[stage]
        if use_np:
            logger.info(f"第 {stage} 波出卡 → 1 号位宝具 + {wanted}")
            self.device.tap(*NP_SERVANT1, delay=0.5)
            cards = self._choose_cards(wanted, count + 1)  # 多挑一张备用：宝具没出时补第 3 张
            self.tap_cards(cards[:count])
            time.sleep(0.5)
            if self._on_card_select(self.device.screenshot()):
                logger.info("宝具没出（没充能？）→ 补第 3 张卡")
                self.tap_cards(cards[count:count + 1])
        else:
            cards = self._choose_cards(wanted, count)
            logger.info(f"第 {stage} 波出卡（按 {'→'.join(dict.fromkeys(wanted))} 优先）：{cards}")
            self.tap_cards(cards)
