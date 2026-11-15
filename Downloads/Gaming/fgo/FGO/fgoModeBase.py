"""模式基类 - 各 Mode 共享的流程（选助战/战斗/结算/吃苹果/连场）

子类按需覆盖钩子：select_cards / use_np / should_release_skills /
release_skills / do_cards / _pick_support
"""
import time
import cv2
import numpy as np
from FGO.fgoLogging import get_logger
from FGO.fgoDetect import Detect
from FGO.fgoConfig import config
from FGO.fgoConst import COORDINATES, NORMAL_DELAY, VERY_LONG_DELAY
from FGO.fgoCardSelector import CardSelector

logger = get_logger("Mode")


class ModeBase:
    """模式基类 - 共享流程（选助战/战斗/结算/吃苹果/连场）"""

    def __init__(self, device, card_strategy="chain_buster"):
        self.device = device
        self.run_count = 0
        self.config = config
        self.card_selector = CardSelector(strategy=card_strategy)
        self.attack_template = Detect.load_template("attack", template_dir="templates")
        self.result_template = Detect.load_template("result", template_dir="templates")
        self.last_wave_template = Detect.load_template("last_wave", template_dir="templates")
        self.wave1_template = Detect.load_template("wave_1", template_dir="templates")
        self.battle_hud_template = Detect.load_template("battle_hud", template_dir="templates")
        self.confirm_btn_template = Detect.load_template("confirm_btn", template_dir="templates")
        self.ap_recover_template = Detect.load_template("ap_recover", template_dir="templates")
        self.apple_confirm_template = Detect.load_template("apple_confirm", template_dir="templates")
        self.castoria_template = Detect.load_template("support", template_dir="templates")
        self.friend_request_template = Detect.load_template("friend_request", template_dir="templates")
        self.support_screen_template = Detect.load_template("support_screen", template_dir="templates")
        self.continue_popup_template = Detect.load_template("continue_popup", template_dir="templates")
        self.next_btn_template = Detect.load_template("next_btn", template_dir="templates")
        self.card_select_template = Detect.load_template("card_select", template_dir="templates")  # 选卡界面右下「戻る」
        # 本回合「看到攻击按钮」那一帧，判断波数直接用它，不再另外截图
        self._turn_screen = None
        self.skills_released = False  # 本场是否已放过技能（只放一次）
        # 吃苹果上限（本次会话），到上限就停止刷本
        self.apple_used = 0
        self.apple_limit = self.config.get("apple_limit", 5)
        self.stop_farming = False
        # 战斗策略（子类覆盖）
        self.skill_wave = 1   # 在第几波释放技能（Mode2刷钱=1, Mode1刷素材=3）

    # 宝具位置（从者1/2/3），Arts 卡靠识别
    NP_POSITIONS = [(607, 346), (993, 346), (1340, 346)]

    def fire_nps(self, count_or_indices):
        """放宝具。传 int=放前 N 个；传 list=放指定从者下标(0=从者1,1=从者2,2=从者3)
        有宝具就放，没充能点了无害"""
        if isinstance(count_or_indices, int):
            indices = range(min(count_or_indices, len(self.NP_POSITIONS)))
        else:
            indices = count_or_indices
        for i in indices:
            if 0 <= i < len(self.NP_POSITIONS):
                x, y = self.NP_POSITIONS[i]
                self.device.tap(x, y, delay=0.3)

    def select_typed_cards(self, pref_type, count):
        """选 count 张指令卡，优先 pref_type（arts/buster/quick）；
        不够/检测失败用固定卡位补满，保证一定凑齐 count 张"""
        if count <= 0:
            return []
        time.sleep(0.4)  # 放完宝具后等指令卡界面稳定再截图
        fixed = list(COORDINATES["card_positions"])  # 5 个固定卡位
        chosen = []
        screen = self.device.screenshot()
        if screen is not None:
            cards = self.card_selector.detect_all_cards(screen)  # [(pos, type), ...]
            chosen = [pos for pos, t in cards if t == pref_type]  # 先要指定类型
        # 不足 count → 用固定卡位补满（避免漏点导致凑不齐组合）
        for p in fixed:
            if len(chosen) >= count:
                break
            if p not in chosen:
                chosen.append(p)
        chosen = chosen[:count]
        logger.info(f"选指令卡(优先{pref_type}) {len(chosen)} 张: {chosen}")
        return chosen

    def select_arts_cards(self, count):
        """优先 Arts"""
        return self.select_typed_cards("arts", count)

    def select_buster_cards(self, count):
        """优先 Buster"""
        return self.select_typed_cards("buster", count)

    def tap_cards(self, positions):
        """依次点选卡片"""
        for x, y in positions:
            self.device.tap(x, y, delay=0.7)

    def do_cards(self, wave):
        """放宝具 + 选卡。默认：use_np 决定放 1 个宝具(servant3) + select_cards 选卡。
        extra 模式覆盖此方法实现按波数的宝具/卡片组合。
        """
        if self.use_np(wave):
            self.device.tap(1340, 346, delay=0.3)  # 宝具: 1005,288
        self.tap_cards(self.select_cards())

    # ---- 子类钩子 ----
    def select_cards(self):
        """选卡 → 返回卡片坐标列表。默认智能选卡(card_selector)；Mode2 覆盖为随机"""
        return self.card_selector.select(self.device.screenshot())

    def use_np(self, wave):
        """该波是否用宝具。默认每波都用（刷钱）；刷素材子类只在 boss 波用"""
        return True

    def should_release_skills(self, wave):
        """该波是否释放技能。默认在 skill_wave（刷钱=1）；刷素材子类按最后一波"""
        return wave == self.skill_wave

    def is_last_wave(self):
        """检测是否最后一波（BATTLE x/N 的 x==N），用 last_wave.png 模板
        只在分子(第一个数字)位置(1295-1360,15-62)局部匹配，避免匹配到分母 N
        """
        if self.last_wave_template is None:
            return True  # 没模板 → 保险起见当最后一波（照常放技能/宝具）
        screen = self._turn_screen if self._turn_screen is not None else self.device.screenshot()
        if screen is None:
            return False
        # 只取分子(第一个数字)区域，避开永远是N的分母
        region = screen[15:62, 1295:1360]
        return Detect.find_template(region, self.last_wave_template, threshold=0.80) is not None

    def is_wave_1(self):
        """检测是否第一波（BATTLE 1/N 的分子==1），用 wave_1.png 模板"""
        if self.wave1_template is None:
            return False
        screen = self._turn_screen if self._turn_screen is not None else self.device.screenshot()
        if screen is None:
            return False
        region = screen[15:62, 1295:1360]
        return Detect.find_template(region, self.wave1_template, threshold=0.80) is not None

    def release_skills(self):
        """释放技能（点技能按钮 + 确认 + 目标）。两模式技能按钮位置相同，默认共用"""
        servants = [
            {"skills": [(117, 864), (240, 864), (373, 840)]},  # S1
            {"skills": [(593, 864), (720, 864), (853, 840)]},  # S2
            {"skills": [(1067, 864), (1187, 864)]},            # S3（2技能，无敌人）
        ]
        for s_idx, servant in enumerate(servants):
            for skill_idx, skill_pos in enumerate(servant["skills"]):
                self.device.tap(skill_pos[0], skill_pos[1], delay=0.2)

                if skill_idx == 0:
                    # 技能1：点 → 确认×2 → [0.7s]
                    for _ in range(2):
                        self.device.tap(969, 313, delay=0.2)
                    time.sleep(0.7)
                elif s_idx == 2 and skill_idx == 1:
                    # Servant3 技能2：点 → [0.3s] → 确认×2（无敌人）
                    time.sleep(0.3)
                    for _ in range(2):
                        self.device.tap(969, 313, delay=0.2)
                else:
                    # S1、S2 技能2和3：点 → [0.3s] → 敌人 → [0.3s] → 确认×3
                    time.sleep(0.3)
                    self.device.tap(1440, 582, delay=0.2)
                    time.sleep(0.3)
                    for _ in range(3):
                        self.device.tap(969, 313, delay=0.2)

                # Servant1、2 技能2 后加 0.3s 延迟再进行技能3
                if s_idx < 2 and skill_idx == 1:
                    time.sleep(0.3)

            if s_idx < len(servants) - 1:
                time.sleep(0.7)

        time.sleep(1.2)

    # ---- 共享基础设施 ----
    def _in_battle_hud(self, screen):
        """右上角有「BATTLE x/y」→ 仍在战斗画面"""
        if screen is None or self.battle_hud_template is None:
            return False
        return Detect.find_template(screen[0:90, 1100:1400], self.battle_hud_template, threshold=0.75) is not None

    def _watch_battle(self, timeout, stable=1):
        """在 timeout 内观察画面。
        Returns: (结果, 期间是否见过 BATTLE 字样)；结果 = (x, y) 攻击按钮 / "END" 结算 / None 没信号"""
        start = time.time()
        hits = 0
        saw_hud = False
        while time.time() - start < timeout:
            screen = self.device.screenshot()
            if screen is not None:
                # ① 攻击按钮
                if self.attack_template is not None:
                    pos = Detect.find_template(screen, self.attack_template, threshold=0.70)
                    if pos:
                        hits += 1
                        if hits >= stable:
                            self._turn_screen = screen  # 记下这一帧，本回合判断波数用
                            return pos, True
                        time.sleep(0.5)
                        continue
                    hits = 0
                # ② 结算画面（积极确认结束）
                if self.result_template is not None:
                    if Detect.find_template(screen, self.result_template, threshold=0.75):
                        return "END", saw_hud
                if self._in_battle_hud(screen):
                    saw_hud = True
            # ③ 动画/读条 → 安静等
            time.sleep(0.5)
        return None, saw_hud

    def _on_card_select(self, screen):
        """是否停在选卡界面：右下角「戻る」按钮。没模板时当作是（沿用旧的盲点）"""
        if self.card_select_template is None:
            return True
        if screen is None:
            return False
        return Detect.find_template(screen[960:1080, 1620:1920], self.card_select_template, 0.80) is not None

    def _unstick_if_card_select(self):
        """确认在选卡界面才补点 3 张卡；否则（动画/结算/读条）不点"""
        if self._on_card_select(self.device.screenshot()):
            logger.info("停在选卡界面 → 补点 3 张命令卡解卡")
            for x, y in COORDINATES["card_positions"][:3]:
                self.device.tap(x, y, delay=0.3)
            return True
        logger.info("不在选卡界面（动画/结算中）→ 不点，继续等")
        return False

    def wait_for_attack(self, timeout=25, stable=1, max_extra=3):
        """等待战斗下一步：
          ① 看到 Attack 按钮  → 返回坐标 (x, y)，战斗中
          ② 看到 RESULT 结算页 → 返回 "END"，战斗真结束
          ③ 都不是（动画/读条）→ 安静等，绝不乱按
        超时后确认停在选卡界面（右下「戻る」）才补点 3 张卡；之后仍没信号时：
          - 画面还有「BATTLE x/y」→ 仍在战斗（敌方回合/动画长），继续等，最多再等 max_extra 轮
          - 没有 → 当作结算画面没认出来，按结束处理（沿用原兜底）

        Returns:
            tuple (x, y) | "END"
        """
        res, _ = self._watch_battle(timeout, stable)
        if res == "END":
            logger.info("检测到结算画面，战斗结束")
            return "END"
        if res:
            return res

        # 超时：只有确认停在选卡界面（没凑满 3 张）才补点解卡；动画/结算中一律不点
        logger.info("超时未见攻击/结算，检查是否卡在选卡界面...")
        self._unstick_if_card_select()

        for extra in range(max_extra + 1):
            # 第一轮等 15s（放卡动画较长），之后每轮再等 timeout
            res, saw_hud = self._watch_battle(15 if extra == 0 else timeout)
            if res == "END":
                logger.info("解卡后检测到结算，战斗结束")
                return "END"
            if res:
                logger.info("解卡成功，回到攻击按钮")
                return res
            if not saw_hud:
                logger.info("解卡后仍无信号，也不在战斗画面，按结束处理")
                return "END"
            if extra < max_extra:
                logger.info(f"仍在战斗中（看到 BATTLE），继续等 ({extra + 1}/{max_extra})")
                self._unstick_if_card_select()
        logger.warning("⚠️  长时间仍在战斗却等不到攻击按钮，按结束处理")
        return "END"

    # 最后一波出卡后等攻击/结算的秒数（宝具+结算动画长；Mode5 单刷本更长）
    LAST_WAVE_TIMEOUT = 35

    # 进本后是否先等读条结束（Mode2 打开）
    wait_loading_after_start = False

    def _wait_loading_done(self, timeout=90):
        """等读条结束：看到战斗画面右上角「BATTLE x/y」（或攻击按钮）才算进入战斗。
        不再用「画面变亮」判断——关卡标题画面很亮，会被误判成读条结束"""
        end = time.time() + timeout
        while time.time() < end:
            screen = self.device.screenshot()
            if screen is not None and (
                    self._in_battle_hud(screen)
                    or (self.attack_template is not None
                        and Detect.find_template(screen, self.attack_template, threshold=0.70))):
                logger.info("✅ 读条结束，进入战斗")
                return True
            time.sleep(1)
        logger.warning("⚠️  等读条超时，继续")
        return False

    def wait_attack_ready(self, stable_s=1.5, timeout=30):
        """等 Attack 按钮连续稳定出现 stable_s 秒（敌方开场 buff/演出结束、可以操作了）"""
        if self.attack_template is None:
            time.sleep(stable_s)
            return True
        end = time.time() + timeout
        since = None
        while time.time() < end:
            if self._seen(self.device.screenshot(), self.attack_template, 0.70):
                since = since or time.time()
                if time.time() - since >= stable_s:
                    return True
            else:
                since = None
            time.sleep(0.3)
        logger.warning("⚠️  等 Attack 稳定出现超时，继续")
        return False

    def _already_in_battle(self):
        """是否已在战斗界面（再次出击复用助战，没有助战选择界面）"""
        screen = self.device.screenshot()
        return (screen is not None and self.attack_template is not None
                and Detect.find_template(screen, self.attack_template, threshold=0.70) is not None)

    def select_support(self):
        """选助战：已在战斗就跳过；否则由 _pick_support 按坐标/模板选"""
        if self._already_in_battle():
            logger.info("已在战斗界面，跳过选助战（再次出击复用助战）")
            return True
        if self._seen(self.device.screenshot(), self.confirm_btn_template, 0.70):
            logger.info("已在编队确认界面，跳过选助战")
            return True
        return self._pick_support()

    def _pick_support(self):
        """默认：随便点第一个助战。Mode2(刷钱)覆盖为模板识别 Castoria"""
        time.sleep(1.5)  # 等助战界面稳定
        logger.info("随便选第一个助战")
        self.device.tap(725, 445, delay=NORMAL_DELAY)  # 第一个助战行
        return True

    def _pick_castoria(self, threshold=0.80, max_refresh=5):
        """模板识别目标助战 Castoria（templates/support.png），找不到则滚动/刷新"""
        return self._pick_by_template(self.castoria_template, "support.png", threshold, max_refresh)

    def _pick_by_template(self, support_template, name, threshold=0.80, max_refresh=5):
        """按模板在助战列表里找目标助战，找不到则向下滑/刷新列表。找到并点了返回 True"""
        if support_template is None:
            logger.warning(f"⚠️  未找到 templates/{name}，跳过助战选择")
            return False
        return self._pick_by_locator(lambda screen: Detect.find_template(screen, support_template, threshold),
                                     max_refresh)

    MAX_SCROLLS = 30  # 每页最多下拉次数（正常会先到底）

    @staticmethod
    def _list_unchanged(a, b):
        """两张截图的助战列表区域几乎一样 → 列表没动（已到底）"""
        ga = cv2.cvtColor(a[260:1060, 60:1800], cv2.COLOR_BGR2GRAY)
        gb = cv2.cvtColor(b[260:1060, 60:1800], cv2.COLOR_BGR2GRAY)
        if float(gb.std()) < 20:  # 黑屏/过场（几乎同色）不算「到底」
            return False
        return float(np.mean(cv2.absdiff(ga, gb))) < 3.0

    def _wait_support_screen(self, timeout=20):
        """等右上角「サポート選択」出现（認图找人前确认在助战界面）；没模板就当在"""
        if self.support_screen_template is None:
            time.sleep(2.0)
            return True
        end = time.time() + timeout
        while time.time() < end:
            if self._seen(self.device.screenshot(), self.support_screen_template):
                time.sleep(0.8)  # 列表刚出来，等它稳定
                return True
            time.sleep(1.0)
        return False

    def _pick_by_locator(self, locate, max_refresh=5):
        """在助战列表里用 locate(screen)->(x,y)|None 找目标，找不到则向下滑/刷新列表。找到并点了返回 True
        max_refresh=None → 一直刷新直到找到（Ctrl+C 可停）"""

        last_refresh = None  # 上次点更新按钮的时间（更新有 9 秒冷却）
        if not self._wait_support_screen():
            logger.error("❌ 不在助战选择界面，不拖动/不刷新（可能回到了地图）")
            return False

        refresh = 0
        while True:
            # 在当前列表中一直往下拉，拉到列表不再移动（到底）为止，最多 MAX_SCROLLS 次
            prev = None
            for scroll in range(self.MAX_SCROLLS + 1):
                screen = self.device.screenshot()
                if screen is not None:
                    pos = locate(screen)
                    if pos:
                        logger.info(f"✅ 找到目标助战: {pos}（第 {scroll} 次下拉）")
                        self.device.tap(pos[0], pos[1], delay=NORMAL_DELAY)
                        return True
                    if prev is not None and self._list_unchanged(prev, screen):
                        logger.info(f"助战列表已拉到底（下拉 {scroll} 次）")
                        break
                    prev = screen
                # 没找到 → 向下拉 500px（约 1.7 行；屏幕可见约 2.7 行，前后两屏重叠约 1 行，不会漏）
                self.device.swipe(960, 850, 960, 350, duration=600)
                time.sleep(0.8)

            # 整页都没找到 → 刷新助战列表
            if max_refresh is not None and refresh >= max_refresh:
                break
            # 更新按钮有 9 秒冷却，确保距上次刷新 >= 9s
            if last_refresh is not None:
                cd = 9 - (time.time() - last_refresh)
                if cd > 0:
                    logger.info(f"等待更新冷却 {cd:.1f}s...")
                    time.sleep(cd)

            logger.info(f"未找到目标助战，刷新列表 ({refresh + 1}/{max_refresh if max_refresh is not None else '∞'})")
            self.device.tap(1395, 190, delay=0.2)   # リスト更新 刷新按钮
            last_refresh = time.time()
            time.sleep(0.3)                         # 等「はい」弹出
            self.device.tap(1245, 840, delay=0.2)   # 确认弹窗「はい」
            time.sleep(3.0)                         # 列表刷新冷却 ~3s
            self.device.swipe(960, 400, 960, 700, duration=400)  # 滑回顶部
            time.sleep(0.8)
            refresh += 1
            if not self._wait_support_screen(timeout=10):
                logger.error("❌ 刷新后不在助战选择界面，停止找人")
                return False

        logger.warning("⚠️  超时未找到目标助战")
        return False

    def eat_apple(self):
        """AP不足时吃苹果（便宜优先：赤铜→青铜→白银→黄金，永不用圣晶石）

        逐个点苹果行：弹出「使用确认」=有货→点决定；没弹窗=0个→试下一个
        Returns: True=吃了苹果, False=都没货
        """
        apple_confirm = self.apple_confirm_template

        def try_row(y):
            self.device.tap(960, y, delay=1.0)
            screen = self.device.screenshot()
            if screen is not None and apple_confirm is not None:
                if Detect.find_template(screen, apple_confirm, threshold=0.75):
                    logger.info("有货 → 吃这个苹果（点決定）")
                    self.device.tap(1259, 844, delay=VERY_LONG_DELAY)  # 決定
                    return True
            return False

        # 滚到底（便宜的赤铜/青铜在最下面）
        self.device.swipe(960, 600, 960, 300, duration=400)
        time.sleep(1.0)
        # 便宜优先：赤铜(752) → 青铜(528) → 白银(304)
        for y in (752, 528, 304):
            if try_row(y):
                return True
        # 都没货 → 滚回顶部吃黄金（顶部：圣晶石320/黄金528/白银752，永不点圣晶石）
        self.device.swipe(960, 300, 960, 600, duration=400)
        time.sleep(1.0)
        if try_row(528):  # 黄金
            return True
        logger.warning("⚠️  没有可用苹果，无法继续刷本")
        return False

    # 好友申请弹窗：按钮相对标题「フレンド申請を送り」中心的位置
    FRIEND_APPLY_OFFSET = (584, 583)   # フレンド申請する
    FRIEND_CLOSE_OFFSET = (-342, 583)  # 終了する

    def _find_friend_dialog(self):
        return Detect.find_template(self.device.screenshot(), self.friend_request_template, threshold=0.80)

    def handle_friend_request(self, wait=2.5):
        """非好友助战打完后会弹「フレンド申請を送りますか？」：
        先点「フレンド申請する」；没反应（如对方好友已满、按钮灰掉）就点「終了する」。
        wait 秒内没出现弹窗 → 返回 False"""
        if self.friend_request_template is None:
            return False
        end = time.time() + wait
        pos = None
        while time.time() < end:
            pos = self._find_friend_dialog()
            if pos:
                break
            time.sleep(0.5)
        if not pos:
            return False
        logger.info("出现好友申请弹窗 → 点「フレンド申請する」")
        ax, ay = self.FRIEND_APPLY_OFFSET
        self.device.tap(pos[0] + ax, pos[1] + ay, delay=1.5)
        if self._find_friend_dialog():
            logger.info("申请没反应（对方好友可能已满）→ 点「終了する」")
            cx, cy = self.FRIEND_CLOSE_OFFSET
            self.device.tap(pos[0] + cx, pos[1] + cy, delay=1.5)
            if self._find_friend_dialog():
                logger.warning("⚠️  好友申请弹窗还在，后面的盲点可能点不准")
        return True

    def _seen(self, screen, template, threshold=0.80):
        return template is not None and Detect.find_template(screen, template, threshold) is not None

    def _handle_ap_recover(self):
        """AP 不足 →「AP回復」苹果界面 → 吃苹果（受上限控制）"""
        if self.apple_used >= self.apple_limit:
            logger.info(f"已吃 {self.apple_used} 个苹果，达到上限 {self.apple_limit}，停止刷本")
            self.device.press(4)  # 返回键关闭苹果界面
            self.stop_farming = True
            return
        logger.info(f"AP 不足，吃苹果回复（第 {self.apple_used + 1}/{self.apple_limit} 个）...")
        if self.eat_apple():
            self.apple_used += 1
        time.sleep(3.0)

    def handle_result_screens(self, timeout=40):
        """战斗结束后处理结算流程（看到什么画面就做什么）：
          EXP/羁绊页（顶上有 RESULT）→ 点画面下方推进
          掉落页「次へ」→ 点次へ
          好友申请框 → 先申请，没反应就「終了する」
          連続出撃框 → 点「連続出撃」→ 若弹 AP 回復就按上限吃苹果
          已回到助战界面 → 结束
        不再盲点：底部中央 (960,1015) 在助战界面正好是一行助战，画面一换就会点错助战，
        所以只在认出 RESULT 页时才点。
        """
        end = time.time() + timeout
        while time.time() < end:
            screen = self.device.screenshot()
            if screen is None:
                time.sleep(0.5)
                continue
            if self._seen(screen, self.friend_request_template):
                self.handle_friend_request(wait=0.5)
                continue
            if self._seen(screen, self.continue_popup_template):
                logger.info("連続出撃 → 点「連続出撃」")
                self.device.tap(1360, 875, delay=2.0)
                time.sleep(2.0)
                if self._seen(self.device.screenshot(), self.ap_recover_template, 0.75):
                    self._handle_ap_recover()
                return
            if self._seen(screen, self.ap_recover_template, 0.75):
                self._handle_ap_recover()
                return
            if self._seen(screen, self.support_screen_template):
                return  # 已在助战界面
            if self._seen(screen, self.next_btn_template):
                self.device.tap(1696, 976, delay=1.2)  # 掉落页「次へ」
                continue
            if self._seen(screen, self.result_template, 0.75):
                self.device.tap(960, 1015, delay=0.6)  # EXP/羁绊页「画面をタッチしてください」
                continue
            time.sleep(0.6)  # 过场/读条 → 等
        logger.warning("⚠️  结算后没看到 連続出撃 / 助战界面")

    def execute_battle(self):
        """执行战斗逻辑直到战斗结束（共享流程）"""
        logger.info("开始战斗...")
        time.sleep(8)
        self.skills_released = False  # 每场重置
        self._turn_screen = None

        wave = 1
        max_waves = 20
        on_last_wave = False  # 上一回合是否在最后一波（宝具+结算动画长，多等一会）

        while wave <= max_waves:
            # 等下一步：攻击按钮坐标 / "END"(结算)
            # Wave 1 要求连续2次检测稳定，避免读条/过渡期误判后放技能打偏
            # 最后一波打完到结算画面常要 ~31s，给 35s；其他波 33s
            # 第 1 回合给 60s：读条 + 敌人登场动画（可能带技能演出）
            timeout = 60 if wave == 1 else (self.LAST_WAVE_TIMEOUT if on_last_wave else 33)
            attack_pos = self.wait_for_attack(timeout=timeout, stable=(2 if wave == 1 else 1))
            if attack_pos == "END":
                self._turn_screen = None
                logger.info("战斗结束，处理结算...")
                self.handle_result_screens()
                break

            # 释放技能（满足条件且本场没放过）
            if not self.skills_released and self.should_release_skills(wave):
                logger.info("释放技能...")
                self.release_skills()
                self.skills_released = True
                # 技能放完后重新确认攻击按钮位置
                pos = self.wait_for_attack(timeout=10)
                if pos != "END":
                    attack_pos = pos

            on_last_wave = self.is_last_wave()
            logger.info(f"Wave {wave} - 攻击...{'（最后一波）' if on_last_wave else ''}")

            # 点 attack 打开选卡界面
            self.device.tap(attack_pos[0], attack_pos[1], delay=0.2)
            time.sleep(0.5)

            # 宝具 + 选卡（默认逻辑见 do_cards，extra 模式覆盖）
            self.do_cards(wave)

            # 等卡片执行动画开始（避免误判旧帧的攻击按钮）
            time.sleep(2)

            logger.info(f"Wave {wave} 完成")
            wave += 1

        logger.info("战斗结束")
        return True

    def run_once(self):
        """运行一次刷本"""
        logger.info(f"开始第 {self.run_count + 1} 次刷本")

        try:
            # 选助战
            if not self.select_support():
                return False

            # 首场有编队确认界面 → 点クエスト開始；連続出撃会直接进本，没有这个按钮属正常
            for _ in range(2):
                pos = Detect.find_template(self.device.screenshot(), self.confirm_btn_template, 0.70)
                if pos:
                    self.device.tap(pos[0], pos[1], delay=NORMAL_DELAY)
                    break
                time.sleep(1)
            else:
                logger.info("没有クエスト開始按钮（連続出撃直接进本）")

            # 等读条结束再开打（Mode2 wave1 就放技能，太早会被开场动画吃掉点击）
            if self.wait_loading_after_start:
                time.sleep(2)
                self._wait_loading_done(timeout=90)  # 活动本读条可能 >40s，看到 BATTLE 就继续

            if not self.execute_battle():
                logger.error("战斗执行失败")
                return False

            logger.info("本次刷本完成")
            self.run_count += 1
            return True

        except Exception as e:
            logger.error(f"刷本异常: {e}")
            return False

    def farm(self, run_count=0):
        """持续刷本"""
        if run_count == 0:
            run_count = self.config.get("run_count", 0)
        logger.info(f"开始刷本 (次数: {'无限' if run_count == 0 else run_count})")

        start_time = time.time()
        fails = 0           # 连续失败次数
        max_fails = 3       # 连续失败到这个数就停，避免卡在某个界面无限重试
        try:
            while True:
                if self.stop_farming:
                    logger.info(f"达到苹果上限（已吃 {self.apple_used} 个），停止刷本")
                    break

                if run_count > 0 and self.run_count >= run_count:
                    logger.info(f"已完成 {self.run_count} 次刷本")
                    break

                if not self.device.available:
                    logger.error("设备不可用")
                    break

                if self.run_once():
                    fails = 0
                else:
                    fails += 1
                    if fails >= max_fails:
                        logger.error(f"❌ 连续失败 {fails} 次，停止刷本（请检查游戏画面）")
                        break
                    logger.warning(f"本次刷本失败，重试 ({fails}/{max_fails})...")
                    time.sleep(5)
                # 注：结算→次へ→連続出撃 已由 execute_battle 内的 handle_result_screens 处理
        except KeyboardInterrupt:
            logger.info("手动中断 (Ctrl+C)")

        elapsed = time.time() - start_time
        avg = elapsed / self.run_count if self.run_count > 0 else 0
        logger.info("=" * 40)
        logger.info(f"刷本结束 — 总结:")
        logger.info(f"  完成场次: {self.run_count} 场")
        logger.info(f"  吃了苹果: {self.apple_used} 个")
        logger.info(f"  总耗时:   {int(elapsed // 60)} 分 {int(elapsed % 60)} 秒")
        if self.run_count > 0:
            logger.info(f"  平均每场: {avg/60:.1f} 分钟 ({avg:.0f} 秒)")
        logger.info("=" * 40)
        return True
