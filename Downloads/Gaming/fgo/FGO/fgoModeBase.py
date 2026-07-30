"""模式基类 - Mode1/Mode2 共享的全部基础设施

子类只需实现 select_cards()：
  - Mode1: 智能选卡(card_selector 策略)
  - Mode2: 随机 3 张
"""
import time
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
        self.current_wave = 1
        self.run_count = 0
        self.config = config
        self.card_selector = CardSelector(strategy=card_strategy)
        self.attack_template = Detect.load_template("attack", template_dir="templates")
        self.result_template = Detect.load_template("result", template_dir="templates")
        self.last_wave_template = Detect.load_template("last_wave", template_dir="templates")
        self.wave1_template = Detect.load_template("wave_1", template_dir="templates")
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
        screen = self.device.screenshot()
        if screen is None:
            return False
        # 只取分子(第一个数字)区域，避开永远是N的分母
        region = screen[15:62, 1295:1360]
        return Detect.find_template(region, self.last_wave_template, threshold=0.80) is not None

    def is_wave_1(self):
        """检测是否第一波（BATTLE 1/N 的分子==1），用 wave_1.png 模板"""
        if self.wave1_template is None:
            return False
        screen = self.device.screenshot()
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
    def wait_for_state(self, target_state, timeout=60):
        """等待目标状态"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            screen = self.device.screenshot()
            if screen is None:
                time.sleep(1)
                continue

            detect = Detect(screen)
            state = detect.detect_battle_state()

            if state == target_state:
                logger.info(f"✅ 进入状态: {state}")
                return True

            time.sleep(1)

        logger.warning(f"⚠️  超时: 无法进入状态 {target_state}")
        return False

    def find_and_click_button(self, template_name, threshold=0.70, retries=3):
        """找到并点击按钮"""
        for attempt in range(retries):
            screen = self.device.screenshot()
            if screen is None:
                time.sleep(1)
                continue

            detect = Detect(screen)
            button_pos = detect.find_button(template_name, threshold)

            if button_pos:
                self.device.tap(button_pos[0], button_pos[1], delay=NORMAL_DELAY)
                return True

            if attempt < retries - 1:
                time.sleep(1)

        logger.error(f"❌ 无法找到按钮: {template_name}")
        return False

    def wait_for_attack(self, timeout=25, stable=1):
        """等待战斗下一步，用积极信号区分三种情况：
          ① 看到 Attack 按钮  → 返回坐标 (x, y)，战斗中
          ② 看到 RESULT 结算页 → 返回 "END"，战斗真结束
          ③ 都不是（动画/读条）→ 安静等，绝不乱按

        Returns:
            tuple (x, y) | "END"
        """
        start = time.time()
        hits = 0
        while time.time() - start < timeout:
            screen = self.device.screenshot()
            if screen is not None:
                # ① 攻击按钮
                if self.attack_template is not None:
                    pos = Detect.find_template(screen, self.attack_template, threshold=0.70)
                    if pos:
                        hits += 1
                        if hits >= stable:
                            return pos
                        time.sleep(0.5)
                        continue
                    hits = 0
                # ② 结算画面（积极确认结束）
                if self.result_template is not None:
                    if Detect.find_template(screen, self.result_template, threshold=0.75):
                        logger.info("检测到结算画面，战斗结束")
                        return "END"
            # ③ 动画/读条 → 安静等
            time.sleep(0.5)

        # 超时：可能卡在选卡界面（没凑满 3 张）→ 盲点固定卡位解卡，再观察一段时间
        logger.info("超时未见攻击/结算，尝试解卡（补点命令卡凑满 3 张）...")
        for x, y in COORDINATES["card_positions"][:3]:
            self.device.tap(x, y, delay=0.3)
        # 补点后等 15s 看反应（放卡动画较长），期间再判断回到攻击 / 进入结算
        recover_end = time.time() + 15
        while time.time() < recover_end:
            screen = self.device.screenshot()
            if screen is not None:
                if self.attack_template is not None:
                    pos = Detect.find_template(screen, self.attack_template, threshold=0.70)
                    if pos:
                        logger.info("解卡成功，回到攻击按钮")
                        return pos
                if self.result_template is not None:
                    if Detect.find_template(screen, self.result_template, threshold=0.75):
                        logger.info("解卡后检测到结算，战斗结束")
                        return "END"
            time.sleep(0.5)
        logger.info("解卡后仍无信号，按结束处理")
        return "END"

    def _already_in_battle(self):
        """是否已在战斗界面（再次出击复用助战，没有助战选择界面）"""
        screen = self.device.screenshot()
        return (screen is not None and self.attack_template is not None
                and Detect.find_template(screen, self.attack_template, threshold=0.70) is not None)

    def select_support(self):
        """选助战：先判断是否已在战斗（跳过），否则由 _pick_support 选"""
        if self._already_in_battle():
            logger.info("已在战斗界面，跳过选助战（再次出击复用助战）")
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
        support_template = Detect.load_template("support", template_dir="templates")
        if support_template is None:
            logger.warning("⚠️  未找到 templates/support.png，跳过助战选择")
            return False

        last_refresh = None  # 上次点更新按钮的时间（更新有 9 秒冷却）

        for refresh in range(max_refresh + 1):
            # 在当前列表中滚动查找（最多向下滑动 3 次）
            for scroll in range(4):
                screen = self.device.screenshot()
                if screen is not None:
                    pos = Detect.find_template(screen, support_template, threshold)
                    if pos:
                        logger.info(f"✅ 找到目标助战: {pos}")
                        self.device.tap(pos[0], pos[1], delay=NORMAL_DELAY)
                        return True
                # 没找到 → 向下滑动列表看更多助战
                self.device.swipe(960, 700, 960, 400, duration=400)
                time.sleep(0.8)

            # 整页都没找到 → 刷新助战列表
            if refresh < max_refresh:
                # 更新按钮有 9 秒冷却，确保距上次刷新 >= 9s
                if last_refresh is not None:
                    cd = 9 - (time.time() - last_refresh)
                    if cd > 0:
                        logger.info(f"等待更新冷却 {cd:.1f}s...")
                        time.sleep(cd)

                logger.info(f"未找到目标助战，刷新列表 ({refresh + 1}/{max_refresh})")
                self.device.tap(1395, 190, delay=0.2)   # リスト更新 刷新按钮
                last_refresh = time.time()
                time.sleep(0.3)                         # 等「はい」弹出
                self.device.tap(1245, 840, delay=0.2)   # 确认弹窗「はい」
                time.sleep(3.0)                         # 列表刷新冷却 ~3s
                self.device.swipe(960, 400, 960, 700, duration=400)  # 滑回顶部
                time.sleep(0.8)

        logger.warning("⚠️  超时未找到目标助战")
        return False

    def eat_apple(self):
        """AP不足时吃苹果（便宜优先：赤铜→青铜→白银→黄金，永不用圣晶石）

        逐个点苹果行：弹出「使用确认」=有货→点决定；没弹窗=0个→试下一个
        Returns: True=吃了苹果, False=都没货
        """
        apple_confirm = Detect.load_template("apple_confirm", template_dir="templates")

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

    def handle_result_screens(self):
        """战斗结束后处理结算流程
        EXP/羁绊/MasterEXP「点击继续」页 → 掉落页「次へ」→ 再次出击弹窗「連続出撃」
        連続出撃后会进入助战选择界面（由下一轮 select_support 接管）
        """
        # 1. 连点跳过「点击继续」页（EXP/羁绊/MasterEXP 等，页数可能不定）
        #    点底部中央「画面をタッチ」区：继续页会推进；掉落页点这里不会误触战利品
        for _ in range(10):
            self.device.tap(960, 1015, delay=0.6)

        # 2. 掉落页 → 次へ（点两次确保，第二次落空无害）
        self.device.tap(1696, 976, delay=1.5)
        self.device.tap(1696, 976, delay=1.5)

        # 3. 再次出击弹窗 → 連続出撃
        time.sleep(1.0)
        self.device.tap(1360, 875, delay=2.0)
        time.sleep(2.0)

        # 3b. AP 不足 → 弹出「AP回復」苹果界面 → 吃苹果（受上限控制）
        screen = self.device.screenshot()
        ap_tmpl = Detect.load_template("ap_recover", template_dir="templates")
        if screen is not None and ap_tmpl is not None:
            if Detect.find_template(screen, ap_tmpl, threshold=0.75):
                if self.apple_used >= self.apple_limit:
                    logger.info(f"已吃 {self.apple_used} 个苹果，达到上限 {self.apple_limit}，停止刷本")
                    self.device.press(4)  # 返回键关闭苹果界面
                    self.stop_farming = True
                    return
                logger.info(f"AP 不足，吃苹果回复（第 {self.apple_used + 1}/{self.apple_limit} 个）...")
                if self.eat_apple():
                    self.apple_used += 1
                time.sleep(3.0)
        # 之后落在助战选择界面，由下一轮 select_support 接管

    def execute_battle(self):
        """执行战斗逻辑直到战斗结束（共享流程）"""
        logger.info("开始战斗...")
        time.sleep(8)
        self.skills_released = False  # 每场重置

        wave = 1
        max_waves = 20

        while wave <= max_waves:
            # 等下一步：攻击按钮坐标 / "END"(结算)
            # Wave 1 要求连续2次检测稳定，避免读条/过渡期误判后放技能打偏
            attack_pos = self.wait_for_attack(timeout=30, stable=(2 if wave == 1 else 1))
            if attack_pos == "END":
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

            logger.info(f"Wave {wave} - 攻击...")

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
            # 选助战（模板识别目标助战）
            self.select_support()

            if self.find_and_click_button("confirm_btn", threshold=0.70):
                time.sleep(2)
                self.wait_for_state('attack', timeout=20)

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

                if not self.run_once():
                    logger.warning("本次刷本失败，重试...")
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
