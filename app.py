# -*- coding: utf-8 -*-
"""
Wonryeol Helper - 메인 애플리케이션
모든 믹스인을 조합하여 완전한 앱 구성
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, colorchooser
import threading
import json
import os
import sys
import re
import urllib.request
from datetime import datetime, timezone

try:
    import keyboard
    import winsound
except ImportError:
    pass

# 상수
from constants import VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_FONT, COLORS, CONFIG_FILE, GITHUB_API

# 기능 믹스인
from features.belial import BelialMixin
from features.inventory import InventoryMixin
from features.discard import DiscardMixin
from features.sell import SellMixin
from features.consume import ConsumeMixin
from features.consume2 import Consume2Mixin
from features.skill_auto import SkillAutoMixin
from features.quick_button import QuickButtonMixin

# UI 믹스인
from ui.overlay import OverlayMixin
from ui.main_window import MainWindowMixin

# 유틸리티 믹스인
from utils.updater import UpdaterMixin


class ColorClickerApp(
    ctk.CTk,
    BelialMixin,
    InventoryMixin,
    DiscardMixin,
    SellMixin,
    ConsumeMixin,
    Consume2Mixin,
    SkillAutoMixin,
    QuickButtonMixin,
    OverlayMixin,
    MainWindowMixin,
    UpdaterMixin
):
    """메인 애플리케이션 클래스"""

    def __init__(self):
        super().__init__()

        self.title("🎯 Wonryeol Helper")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)

        # 각 믹스인의 변수 초기화
        self.init_belial_vars()
        self.init_inventory_vars()
        self.init_discard_vars()
        self.init_sell_vars()
        self.init_consume_vars()
        self.init_consume2_vars()
        self.init_skill_auto_vars()
        self.init_quick_button_vars()
        self.init_overlay_vars()
        self.init_common_vars()

        # UI 설정
        self.setup_ui()

        # 설정 불러오기
        self.load_config()

        # 핫키 설정
        self.setup_hotkey()
        self.setup_quick_button_hotkeys()

        # 마우스 좌표 업데이트
        self.update_mouse_pos()

        # 자동 시작 적용
        self.after(500, self.apply_auto_start)

        # 업데이트 확인
        self.after(1000, lambda: threading.Thread(target=self.check_for_updates, daemon=True).start())

        # 월드 보스 타이머
        self.after(1500, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())
        self.after(2000, self.update_world_boss_timer)

    def init_common_vars(self):
        """공통 변수 초기화"""
        # 월드보스 알림
        self.boss_alert_enabled = ctk.BooleanVar(value=True)
        self.boss_alerted_id = None

        # 긴급 정지 핫키
        self.emergency_stop_key = ctk.StringVar(value="f12")

        # 자동 시작 설정
        self.auto_start_belial = ctk.BooleanVar(value=False)
        self.auto_start_inv = ctk.BooleanVar(value=False)
        self.auto_start_discard = ctk.BooleanVar(value=False)
        self.auto_start_sell = ctk.BooleanVar(value=False)
        self.auto_start_consume = ctk.BooleanVar(value=False)
        self.auto_start_consume2 = ctk.BooleanVar(value=False)
        self.auto_start_skill_auto = ctk.BooleanVar(value=False)

        # 월드 보스 타이머
        self.world_boss_name = ctk.StringVar(value="로딩 중...")
        self.world_boss_time = ctk.StringVar(value="")
        self.world_boss_zone = ctk.StringVar(value="")
        self.world_boss_timestamp = None
        self.world_boss_label = None

        # Home 탭 UI 참조
        self.home_switches = {}
        self.home_key_labels = {}
        self.home_status_labels = {}

        # 핫키 설정 Lock (동시 호출 방지)
        self._hotkey_lock = threading.Lock()

    # =========================================
    # 핫키 관련
    # =========================================
    def setup_hotkey(self):
        """핫키 설정 - 5개 스킬 프리셋 지원"""
        with self._hotkey_lock:
            keyboard.unhook_all()
            # 키보드 핫키 등록 (마우스 버튼 제외)
            if not self.is_mouse_key(self.trigger_key.get()):
                keyboard.on_press_key(self.trigger_key.get(), self.on_trigger_key, suppress=False)
            if not self.is_mouse_key(self.inv_trigger_key.get()):
                keyboard.on_press_key(self.inv_trigger_key.get(), self.on_inv_trigger_key, suppress=False)
            if not self.is_mouse_key(self.discard_trigger_key.get()):
                keyboard.on_press_key(self.discard_trigger_key.get(), self.on_discard_trigger_key, suppress=False)
            if not self.is_mouse_key(self.sell_trigger_key.get()):
                keyboard.on_press_key(self.sell_trigger_key.get(), self.on_sell_trigger_key, suppress=False)
            if not self.is_mouse_key(self.consume_trigger_key.get()):
                keyboard.on_press_key(self.consume_trigger_key.get(), self.on_consume_trigger_key, suppress=False)
            if not self.is_mouse_key(self.consume2_trigger_key.get()):
                keyboard.on_press_key(self.consume2_trigger_key.get(), self.on_consume2_trigger_key, suppress=False)

            # 5개 스킬 프리셋 각각의 핫키 등록
            for i, preset in enumerate(self.skill_presets):
                key = preset['trigger_key'].get()
                if not self.is_mouse_key(key):
                    # 클로저로 인덱스 캡처
                    keyboard.on_press_key(
                        key,
                        lambda e, idx=i: self.on_skill_preset_trigger_key(idx, e),
                        suppress=False
                    )

            # Enter로 pause/resume (스킬 자동 + 사기)
            keyboard.on_press_key('enter', self.on_combined_enter_pause, suppress=False)

            # 긴급 정지 키 등록
            if not self.is_mouse_key(self.emergency_stop_key.get()):
                keyboard.on_press_key(self.emergency_stop_key.get(), self.on_emergency_stop, suppress=False)

            # 마우스 폴링 시작 (한 번만)
            if not hasattr(self, 'mouse_polling_active') or not self.mouse_polling_active:
                self.start_mouse_polling()

    def is_mouse_key(self, key):
        """마우스 키 여부 확인"""
        return key.lower() in ['mouse4', 'mouse5', 'xbutton1', 'xbutton2']

    def check_modifier(self, required_modifier):
        """조합키 체크"""
        if required_modifier == "없음":
            return True
        elif required_modifier == "Ctrl":
            return keyboard.is_pressed('ctrl')
        elif required_modifier == "Alt":
            return keyboard.is_pressed('alt')
        elif required_modifier == "Shift":
            return keyboard.is_pressed('shift')
        return True

    def check_hotkey_conflict(self, new_key):
        """핫키 충돌 체크 - 긴급정지 키와 충돌 시 차단"""
        new_key_lower = new_key.lower()
        emergency_key = self.emergency_stop_key.get().lower()

        if new_key_lower == emergency_key:
            return f"⚠️ 경고: {new_key.upper()} 키가 긴급정지 키와 충돌합니다!\n다른 키를 선택해주세요."
        return None

    def on_combined_enter_pause(self, event):
        """Enter 키 - 먹기 + 사기 + 스킬 자동 동시 pause/resume"""
        self.on_consume_enter_pause(event)
        self.on_consume2_enter_pause(event)
        self.on_skill_auto_enter_pause(event)

    def start_mouse_polling(self):
        """마우스 버튼 폴링 시작"""
        self.mouse_polling_active = True

        def poll_mouse():
            import win32api
            import win32con
            import time

            last_x1_state = False
            last_x2_state = False

            while self.mouse_polling_active:
                try:
                    x1_state = win32api.GetAsyncKeyState(win32con.VK_XBUTTON1) & 0x8000 != 0
                    x2_state = win32api.GetAsyncKeyState(win32con.VK_XBUTTON2) & 0x8000 != 0

                    # Mouse4 (XButton1) 처리
                    if x1_state and not last_x1_state:
                        self.on_mouse_button('mouse4')
                    last_x1_state = x1_state

                    # Mouse5 (XButton2) 처리
                    if x2_state and not last_x2_state:
                        self.on_mouse_button('mouse5')
                    last_x2_state = x2_state

                except:
                    pass
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

    def on_mouse_button(self, button):
        """마우스 버튼 핸들러 - 5개 스킬 프리셋 지원"""
        if self.trigger_key.get().lower() == button:
            self.on_trigger_key(None)
        if self.inv_trigger_key.get().lower() == button:
            self.on_inv_trigger_key(None)
        if self.discard_trigger_key.get().lower() == button:
            self.on_discard_trigger_key(None)
        if self.sell_trigger_key.get().lower() == button:
            self.on_sell_trigger_key(None)
        if self.consume_trigger_key.get().lower() == button:
            self.on_consume_trigger_key(None)
        if self.consume2_trigger_key.get().lower() == button:
            self.on_consume2_trigger_key(None)
        # 5개 스킬 프리셋 마우스 핫키 체크
        for i, preset in enumerate(self.skill_presets):
            if preset['trigger_key'].get().lower() == button:
                self.on_skill_preset_trigger_key(i, None)

    # =========================================
    # Home 탭 토글 함수들
    # =========================================
    def home_toggle_belial(self):
        """Home에서 벨리알 토글"""
        self.toggle_running()

    def home_toggle_inv(self):
        """Home에서 신화장난꾸러기 토글"""
        self.toggle_inv_running()

    def home_toggle_discard(self):
        """Home에서 아이템 버리기 토글"""
        self.toggle_discard_running()

    def home_toggle_sell(self):
        """Home에서 아이템 팔기 토글"""
        self.toggle_sell_running()

    def home_toggle_consume(self):
        """Home에서 아이템 먹기 토글"""
        self.toggle_consume_running()

    def home_toggle_consume2(self):
        """Home에서 아이템 사기 토글"""
        self.toggle_consume2_running()

    def home_toggle_skill_auto(self):
        """Home에서 스킬 자동 토글"""
        self.toggle_skill_auto_running()

    def change_emergency_key(self):
        """긴급 정지 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("긴급 정지 키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 긴급 정지 키를 누르세요...",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.emergency_stop_key.set(event.name)
                self.emergency_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            self.setup_hotkey()  # Lock 안에서 unhook_all + 재등록
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def on_emergency_stop(self, event=None):
        """긴급 정지 - 실행 중인 클릭/매크로 동작만 즉시 중지 (5개 스킬 프리셋 지원)"""
        self.detection_active = False
        self.inv_cleanup_active = False
        self.discard_active = False
        self.sell_active = False
        self.consume_active = False
        self.consume_paused = False
        self.consume2_active = False
        self.consume2_paused = False

        # 5개 스킬 프리셋 모두 중지
        for i, preset in enumerate(self.skill_presets):
            preset['active'] = False
            preset['paused'] = False
            if preset['running'] and preset['_status_label']:
                preset['_status_label'].configure(
                    text=f"🔴 [{preset['trigger_key'].get().upper()}] 키로 시작"
                )
            if preset['_pause_label']:
                preset['_pause_label'].configure(text="")
            # 오버레이 상태 업데이트
            self._update_overlay_preset_status(i, "stopped")

        if self.is_running:
            self.status_label.configure(text=f"🔴 [{self.trigger_key.get().upper()}] 키로 시작")
        if self.inv_running:
            self.inv_status_label.configure(text=f"🔴 [{self.inv_trigger_key.get().upper()}] 키로 시작")
        if self.discard_running:
            self.discard_status_label.configure(text=f"🔴 [{self.discard_trigger_key.get().upper()}] 키로 시작")
        if self.sell_running:
            self.sell_status_label.configure(text=f"🔴 [{self.sell_trigger_key.get().upper()}] 키로 시작")
        if self.consume_running:
            self.consume_status_label.configure(text=f"🔴 [{self.consume_trigger_key.get().upper()}] 키로 시작")
        if self.consume2_running:
            self.consume2_status_label.configure(text=f"🔴 [{self.consume2_trigger_key.get().upper()}] 키로 시작")

    def is_chatting(self):
        """채팅 중인지 확인 (pause 상태면 채팅 중으로 간주) - 5개 스킬 프리셋 지원"""
        if getattr(self, 'consume_paused', False) or getattr(self, 'consume2_paused', False):
            return True
        # 5개 프리셋 중 하나라도 paused면 채팅 중
        for preset in self.skill_presets:
            if preset['paused']:
                return True
        return False

    def apply_auto_start(self):
        """자동 시작 적용"""
        if self.auto_start_belial.get() and not self.is_running:
            self.toggle_running()
        if self.auto_start_inv.get() and not self.inv_running:
            self.toggle_inv_running()
        if self.auto_start_discard.get() and not self.discard_running:
            self.toggle_discard_running()
        if self.auto_start_sell.get() and not self.sell_running:
            self.toggle_sell_running()
        if self.auto_start_consume.get() and not self.consume_running:
            self.toggle_consume_running()
        if self.auto_start_consume2.get() and not self.consume2_running:
            self.toggle_consume2_running()
        if self.auto_start_skill_auto.get() and not self.skill_auto_running:
            self.toggle_skill_auto_running()

    # =========================================
    # Home 탭 상태 업데이트
    # =========================================
    def update_home_status(self):
        """Home 탭 상태 실시간 업데이트"""
        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running,
            "consume2_running": self.consume2_running,
            "skill_p0_running": self.skill_presets[0]['running'],
            "skill_p1_running": self.skill_presets[1]['running'],
            "skill_p2_running": self.skill_presets[2]['running'],
            "skill_p3_running": self.skill_presets[3]['running'],
            "skill_p4_running": self.skill_presets[4]['running'],
        }

        for attr, is_on in states.items():
            if attr in self.home_status_labels:
                label = self.home_status_labels[attr]
                if is_on:
                    label.configure(text="ON", text_color="#00FF00")
                else:
                    label.configure(text="OFF", text_color="#666666")

            if attr in self.home_switches:
                switch = self.home_switches[attr]
                if is_on and not switch.get():
                    switch.select()
                elif not is_on and switch.get():
                    switch.deselect()

            if attr in self.home_key_labels:
                key_label, key_var, mod_var = self.home_key_labels[attr]
                mod = mod_var.get()
                key = key_var.get().upper()
                if mod != "없음":
                    key_label.configure(text=f"{mod}+{key}")
                else:
                    key_label.configure(text=key)

        self.update_idletasks()
        self.after(500, self.update_home_status)

    def update_home_status_now(self):
        """Home 탭 + 오버레이 상태 즉시 업데이트"""
        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running,
            "consume2_running": self.consume2_running,
            "skill_p0_running": self.skill_presets[0]['running'],
            "skill_p1_running": self.skill_presets[1]['running'],
            "skill_p2_running": self.skill_presets[2]['running'],
            "skill_p3_running": self.skill_presets[3]['running'],
            "skill_p4_running": self.skill_presets[4]['running'],
        }

        active_map = {
            "is_running": self.detection_active,
            "inv_running": self.inv_cleanup_active,
            "discard_running": self.discard_active,
            "sell_running": self.sell_active,
            "consume_running": self.consume_active,
            "consume2_running": self.consume2_active,
            "skill_p0_running": self.skill_presets[0]['active'],
            "skill_p1_running": self.skill_presets[1]['active'],
            "skill_p2_running": self.skill_presets[2]['active'],
            "skill_p3_running": self.skill_presets[3]['active'],
            "skill_p4_running": self.skill_presets[4]['active'],
        }

        for attr, is_on in states.items():
            if attr in self.home_status_labels:
                label = self.home_status_labels[attr]
                if is_on:
                    label.configure(text="ON", text_color=COLORS["on_color"])
                else:
                    label.configure(text="OFF", text_color=COLORS["off_color"])

            if attr in self.home_switches:
                switch = self.home_switches[attr]
                if is_on and not switch.get():
                    switch.select()
                elif not is_on and switch.get():
                    switch.deselect()

            if hasattr(self, 'overlay_labels') and attr in self.overlay_labels:
                label = self.overlay_labels[attr]
                if is_on:
                    label.configure(text="● ON", fg=COLORS["on_color"])
                else:
                    label.configure(text="● OFF", fg=COLORS["off_color"])

            if hasattr(self, 'overlay_name_labels') and attr in self.overlay_name_labels:
                name_label = self.overlay_name_labels[attr]
                is_active = active_map.get(attr, False)
                if is_active:
                    name_label.configure(fg=COLORS["active_color"])
                else:
                    name_label.configure(fg='#ffffff')

        self.update_idletasks()

    # =========================================
    # 설정 저장/불러오기
    # =========================================
    def save_config(self):
        """설정 저장"""
        config = {
            'colors': self.colors,
            'exclude_colors': self.exclude_colors,
            'tolerance': self.tolerance.get(),
            'color_tolerance': self.color_tolerance.get(),
            'exclude_range': self.exclude_range.get(),
            'trigger_key': self.trigger_key.get(),
            'trigger_modifier': self.trigger_modifier.get(),
            'click_type': self.click_type.get(),
            'click_delay': self.click_delay.get(),
            'use_full_screen': self.use_full_screen.get(),
            'cooldown_distance': self.cooldown_distance.get(),
            'cooldown_time': self.cooldown_time.get(),
            'search_area': {
                'x1': self.search_x1.get(),
                'y1': self.search_y1.get(),
                'x2': self.search_x2.get(),
                'y2': self.search_y2.get()
            },
            'search_step': self.search_step.get(),
            'inventory': {
                'keep_color': self.inv_keep_color.get(),
                'tolerance': self.inv_tolerance.get(),
                'area': {
                    'x1': self.inv_x1.get(),
                    'y1': self.inv_y1.get(),
                    'x2': self.inv_x2.get(),
                    'y2': self.inv_y2.get()
                },
                'desc_area': {
                    'x1': self.inv_desc_x1.get(),
                    'y1': self.inv_desc_y1.get(),
                    'x2': self.inv_desc_x2.get(),
                    'y2': self.inv_desc_y2.get()
                },
                'cols': self.inv_cols.get(),
                'rows': self.inv_rows.get(),
                'trigger_key': self.inv_trigger_key.get(),
                'trigger_modifier': self.inv_trigger_modifier.get(),
                'delay': self.inv_delay.get(),
                'move_duration': self.inv_move_duration.get(),
                'panel_delay': self.inv_panel_delay.get(),
                'space_delay': self.inv_space_delay.get(),
                'click_delay': self.inv_click_delay.get()
            },
            'discard': {
                'trigger_key': self.discard_trigger_key.get(),
                'trigger_modifier': self.discard_trigger_modifier.get(),
                'delay': self.discard_delay.get()
            },
            'sell': {
                'trigger_key': self.sell_trigger_key.get(),
                'trigger_modifier': self.sell_trigger_modifier.get(),
                'delay': self.sell_delay.get()
            },
            'consume': {
                'trigger_key': self.consume_trigger_key.get(),
                'trigger_modifier': self.consume_trigger_modifier.get(),
                'delay': self.consume_delay.get(),
                'input_type': self.consume_input_type.get(),
                'action_key': self.consume_action_key.get()
            },
            'consume2': {
                'trigger_key': self.consume2_trigger_key.get(),
                'trigger_modifier': self.consume2_trigger_modifier.get(),
                'delay': self.consume2_delay.get(),
                'input_type': self.consume2_input_type.get(),
                'action_key': self.consume2_action_key.get()
            },
            'skill_auto': {
                'presets': [
                    {
                        'name': preset['name'].get(),
                        'trigger_key': preset['trigger_key'].get(),
                        'trigger_modifier': preset['trigger_modifier'].get(),
                        'honryeongsa_mode': preset['honryeongsa_mode'].get(),
                        'slots': [
                            {
                                'enabled': slot['enabled'].get(),
                                'key': slot['key'].get(),
                                'cooldown': slot['cooldown'].get()
                            }
                            for slot in preset['slots']
                        ]
                    }
                    for preset in self.skill_presets
                ]
            },
            'overlay': {
                'x': self.overlay_x.get(),
                'y': self.overlay_y.get(),
                'alpha': self.overlay_alpha.get(),
                'scale': self.overlay_scale.get(),
                'scale_w': self.overlay_scale_w.get(),
                'scale_h': self.overlay_scale_h.get(),
                'bg_color': self.overlay_bg_color.get()
            },
            'boss_alert_enabled': self.boss_alert_enabled.get(),
            'emergency_stop_key': self.emergency_stop_key.get(),
            'auto_start': {
                'belial': self.auto_start_belial.get(),
                'inv': self.auto_start_inv.get(),
                'discard': self.auto_start_discard.get(),
                'sell': self.auto_start_sell.get(),
                'consume': self.auto_start_consume.get(),
                'consume2': self.auto_start_consume2.get(),
                'skill_auto': self.auto_start_skill_auto.get()
            },
            'quick_btn_enabled': self.quick_btn_enabled.get(),
            'quick_btn': {
                'discard_x': self.quick_btn_x.get(),
                'discard_y': self.quick_btn_y.get(),
                'sell_x': self.quick_sell_x.get(),
                'sell_y': self.quick_sell_y.get(),
                'bundle_x': self.quick_bundle_x.get(),
                'bundle_y': self.quick_bundle_y.get(),
                'detect_pos1_x': self.detect_pos1_x.get(),
                'detect_pos1_y': self.detect_pos1_y.get(),
                'detect_color1': self.detect_color1.get(),
                'detect_pos2_x': self.detect_pos2_x.get(),
                'detect_pos2_y': self.detect_pos2_y.get(),
                'detect_color2': self.detect_color2.get()
            }
        }

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("저장", "설정이 저장되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def load_config(self, show_message=False):
        """설정 불러오기"""
        config_path = CONFIG_FILE
        if not os.path.exists(config_path):
            old_path = "color_clicker_config.json"
            if os.path.exists(old_path):
                config_path = old_path
            else:
                if show_message:
                    messagebox.showwarning("알림", "저장된 설정 파일이 없습니다.")
                return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.colors = config.get('colors', self.colors)
            self.exclude_colors = config.get('exclude_colors', self.exclude_colors)
            self.tolerance.set(config.get('tolerance', 0))
            self.color_tolerance.set(config.get('color_tolerance', 0))
            self.exclude_range.set(config.get('exclude_range', 3))
            self.trigger_key.set(config.get('trigger_key', 'f4'))
            self.trigger_modifier.set(config.get('trigger_modifier', '없음'))
            self.click_type.set(config.get('click_type', 'fkey'))
            self.click_delay.set(config.get('click_delay', 0.01))
            self.use_full_screen.set(config.get('use_full_screen', False))
            self.cooldown_distance.set(config.get('cooldown_distance', 50))
            self.cooldown_time.set(config.get('cooldown_time', 0.1))

            area = config.get('search_area', {})
            self.search_x1.set(area.get('x1', 6))
            self.search_y1.set(area.get('y1', 7))
            self.search_x2.set(area.get('x2', 2137))
            self.search_y2.set(area.get('y2', 1168))

            self.search_step.set(config.get('search_step', 5))

            # 신화장난꾸러기 설정
            inv = config.get('inventory', {})
            if inv:
                self.inv_keep_color.set(inv.get('keep_color', '#DFA8F0'))
                self.inv_tolerance.set(inv.get('tolerance', 15))

                inv_area = inv.get('area', {})
                self.inv_x1.set(inv_area.get('x1', 1690))
                self.inv_y1.set(inv_area.get('y1', 961))
                self.inv_x2.set(inv_area.get('x2', 2501))
                self.inv_y2.set(inv_area.get('y2', 1287))

                desc_area = inv.get('desc_area', {})
                self.inv_desc_x1.set(desc_area.get('x1', 1144))
                self.inv_desc_y1.set(desc_area.get('y1', 428))
                self.inv_desc_x2.set(desc_area.get('x2', 1636))
                self.inv_desc_y2.set(desc_area.get('y2', 1147))

                self.inv_cols.set(inv.get('cols', 11))
                self.inv_rows.set(inv.get('rows', 3))
                self.inv_trigger_key.set(inv.get('trigger_key', 'f3'))
                self.inv_trigger_modifier.set(inv.get('trigger_modifier', '없음'))
                self.inv_delay.set(inv.get('delay', 0.01))
                self.inv_move_duration.set(inv.get('move_duration', 0.15))
                self.inv_panel_delay.set(inv.get('panel_delay', 0.08))
                self.inv_space_delay.set(inv.get('space_delay', 0.05))
                self.inv_click_delay.set(inv.get('click_delay', 0.01))

                if hasattr(self, 'inv_key_display'):
                    self.inv_key_display.configure(text=self.inv_trigger_key.get().upper())

            # 버리기 설정
            discard = config.get('discard', {})
            if discard:
                self.discard_trigger_key.set(discard.get('trigger_key', 'f1'))
                self.discard_trigger_modifier.set(discard.get('trigger_modifier', '없음'))
                self.discard_delay.set(discard.get('delay', 0.01))
                if hasattr(self, 'discard_key_display'):
                    self.discard_key_display.configure(text=self.discard_trigger_key.get().upper())

            # 팔기 설정
            sell = config.get('sell', {})
            if sell:
                self.sell_trigger_key.set(sell.get('trigger_key', 'f2'))
                self.sell_trigger_modifier.set(sell.get('trigger_modifier', '없음'))
                self.sell_delay.set(sell.get('delay', 0.01))
                if hasattr(self, 'sell_key_display'):
                    self.sell_key_display.configure(text=self.sell_trigger_key.get().upper())

            # 먹기 설정
            consume = config.get('consume', {})
            if consume:
                self.consume_trigger_key.set(consume.get('trigger_key', 'mouse5'))
                self.consume_trigger_modifier.set(consume.get('trigger_modifier', '없음'))
                self.consume_delay.set(consume.get('delay', 0.01))
                input_type = consume.get('input_type', '우클릭')
                self.consume_input_type.set(input_type)
                action_key = consume.get('action_key', input_type)
                self.consume_action_key.set(action_key)
                if hasattr(self, 'consume_key_display'):
                    self.consume_key_display.configure(text=self.consume_trigger_key.get().upper())
                if hasattr(self, 'consume_action_display'):
                    self.consume_action_display.configure(text=action_key.upper())

            # 사기 설정 (먹기 V2)
            consume2 = config.get('consume2', {})
            if consume2:
                self.consume2_trigger_key.set(consume2.get('trigger_key', 'mouse4'))
                self.consume2_trigger_modifier.set(consume2.get('trigger_modifier', '없음'))
                self.consume2_delay.set(consume2.get('delay', 0.01))
                input_type2 = consume2.get('input_type', '우클릭')
                self.consume2_input_type.set(input_type2)
                action_key2 = consume2.get('action_key', input_type2)
                self.consume2_action_key.set(action_key2)
                if hasattr(self, 'consume2_key_display'):
                    self.consume2_key_display.configure(text=self.consume2_trigger_key.get().upper())
                if hasattr(self, 'consume2_action_display'):
                    self.consume2_action_display.configure(text=action_key2.upper())

            # 스킬 자동 설정 (5개 프리셋 지원 + 마이그레이션)
            skill_auto = config.get('skill_auto', {})
            if skill_auto:
                presets_data = skill_auto.get('presets', [])

                # 기존 단일 프리셋 설정 마이그레이션
                if not presets_data and 'trigger_key' in skill_auto:
                    presets_data = [{
                        'name': '프리셋 1',
                        'trigger_key': skill_auto.get('trigger_key', 'f6'),
                        'trigger_modifier': skill_auto.get('trigger_modifier', '없음'),
                        'honryeongsa_mode': skill_auto.get('honryeongsa_mode', False),
                        'slots': skill_auto.get('slots', [])
                    }]

                # 프리셋 데이터 로드
                for i, preset_data in enumerate(presets_data):
                    if i >= len(self.skill_presets):
                        break

                    preset = self.skill_presets[i]
                    preset['name'].set(preset_data.get('name', f'프리셋 {i + 1}'))
                    preset['trigger_key'].set(preset_data.get('trigger_key', f'f{6 + i}'))
                    preset['trigger_modifier'].set(preset_data.get('trigger_modifier', '없음'))
                    preset['honryeongsa_mode'].set(preset_data.get('honryeongsa_mode', False))

                    slots_data = preset_data.get('slots', [])
                    for j, slot_data in enumerate(slots_data):
                        if j >= len(preset['slots']):
                            break
                        preset['slots'][j]['enabled'].set(slot_data.get('enabled', False))
                        preset['slots'][j]['key'].set(slot_data.get('key', str(j + 1)))
                        preset['slots'][j]['cooldown'].set(slot_data.get('cooldown', 0.0))

                # 프리셋 요약 라벨 업데이트
                if hasattr(self, '_update_skill_preset_summary'):
                    self._update_skill_preset_summary()

            # 오버레이 설정
            overlay = config.get('overlay', {})
            if overlay:
                self.overlay_x.set(overlay.get('x', 100))
                self.overlay_y.set(overlay.get('y', 100))
                self.overlay_alpha.set(overlay.get('alpha', 0.85))
                self.overlay_scale.set(overlay.get('scale', 1.0))
                self.overlay_scale_w.set(overlay.get('scale_w', 1.0))
                self.overlay_scale_h.set(overlay.get('scale_h', 1.0))
                self.overlay_bg_color.set(overlay.get('bg_color', '#1a1a2e'))
                if hasattr(self, 'alpha_label'):
                    self.alpha_label.configure(text=f"{int(self.overlay_alpha.get() * 100)}%")
                if hasattr(self, 'scale_label'):
                    self.scale_label.configure(text=f"{int(self.overlay_scale.get() * 100)}%")
                if hasattr(self, 'scale_w_label'):
                    self.scale_w_label.configure(text=f"{int(self.overlay_scale_w.get() * 100)}%")
                if hasattr(self, 'scale_h_label'):
                    self.scale_h_label.configure(text=f"{int(self.overlay_scale_h.get() * 100)}%")
                if hasattr(self, 'bg_color_preview'):
                    self.bg_color_preview.configure(fg_color=self.overlay_bg_color.get())

            # 월드보스 알림
            self.boss_alert_enabled.set(config.get('boss_alert_enabled', True))

            # 긴급 정지 키
            self.emergency_stop_key.set(config.get('emergency_stop_key', 'f12'))
            if hasattr(self, 'emergency_key_display'):
                self.emergency_key_display.configure(text=self.emergency_stop_key.get().upper())

            # 자동 시작 설정
            auto_start = config.get('auto_start', {})
            if auto_start:
                self.auto_start_belial.set(auto_start.get('belial', False))
                self.auto_start_inv.set(auto_start.get('inv', False))
                self.auto_start_discard.set(auto_start.get('discard', False))
                self.auto_start_sell.set(auto_start.get('sell', False))
                self.auto_start_consume.set(auto_start.get('consume', False))
                self.auto_start_consume2.set(auto_start.get('consume2', False))
                self.auto_start_skill_auto.set(auto_start.get('skill_auto', False))

            # 빠른 버튼 설정
            self.quick_btn_enabled.set(config.get('quick_btn_enabled', True))

            quick_btn = config.get('quick_btn', {})
            if quick_btn:
                self.quick_btn_x.set(quick_btn.get('discard_x', 1812))
                self.quick_btn_y.set(quick_btn.get('discard_y', 898))
                self.quick_sell_x.set(quick_btn.get('sell_x', 1865))
                self.quick_sell_y.set(quick_btn.get('sell_y', 899))
                self.quick_bundle_x.set(quick_btn.get('bundle_x', 1759))
                self.quick_bundle_y.set(quick_btn.get('bundle_y', 898))
                self.detect_pos1_x.set(quick_btn.get('detect_pos1_x', 1738))
                self.detect_pos1_y.set(quick_btn.get('detect_pos1_y', 267))
                self.detect_pos2_x.set(quick_btn.get('detect_pos2_x', 1859))
                self.detect_pos2_y.set(quick_btn.get('detect_pos2_y', 280))
                # 각 위치별 색상 (이전 버전 호환성 유지)
                old_color = quick_btn.get('detect_color', '#E4DBCA')
                self.detect_color1.set(quick_btn.get('detect_color1', old_color))
                self.detect_color2.set(quick_btn.get('detect_color2', old_color))

            if hasattr(self, 'key_display'):
                self.key_display.configure(text=self.trigger_key.get().upper())
            self.update_color_list()
            self.update_exclude_list()
            self.setup_hotkey()

            if show_message:
                messagebox.showinfo("불러오기", "설정을 불러왔습니다!")
        except Exception as e:
            if show_message:
                messagebox.showerror("오류", f"설정 불러오기 실패: {e}")
            print(f"Config load error: {e}")

    def export_config(self):
        """설정 내보내기"""
        file_path = filedialog.asksaveasfilename(
            title="설정 내보내기",
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
            initialfile="ColorClicker_설정.json"
        )
        if not file_path:
            return

        config = self.get_config_dict()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("완료", f"설정이 저장되었습니다!\n\n📁 {file_path}")
        except Exception as e:
            messagebox.showerror("오류", f"내보내기 실패: {e}")

    def import_config(self):
        """설정 가져오기"""
        file_path = filedialog.askopenfilename(
            title="설정 가져오기",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.apply_config_dict(config)
            messagebox.showinfo("완료", "설정을 불러왔습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"가져오기 실패: {e}")

    def get_config_dict(self):
        """현재 설정을 딕셔너리로 반환"""
        return {
            'colors': self.colors,
            'exclude_colors': self.exclude_colors,
            'tolerance': self.tolerance.get(),
            'trigger_key': self.trigger_key.get(),
            'trigger_modifier': self.trigger_modifier.get(),
            'click_delay': self.click_delay.get(),
            'search_area': {
                'x1': self.search_x1.get(),
                'y1': self.search_y1.get(),
                'x2': self.search_x2.get(),
                'y2': self.search_y2.get()
            },
            'inventory': {
                'keep_color': self.inv_keep_color.get(),
                'tolerance': self.inv_tolerance.get(),
                'trigger_key': self.inv_trigger_key.get(),
                'trigger_modifier': self.inv_trigger_modifier.get()
            }
        }

    def apply_config_dict(self, config):
        """설정 딕셔너리 적용"""
        self.colors = config.get('colors', self.colors)
        self.exclude_colors = config.get('exclude_colors', self.exclude_colors)
        self.tolerance.set(config.get('tolerance', 0))
        self.trigger_key.set(config.get('trigger_key', 'f4'))
        self.trigger_modifier.set(config.get('trigger_modifier', '없음'))
        self.click_delay.set(config.get('click_delay', 0.01))

        area = config.get('search_area', {})
        self.search_x1.set(area.get('x1', 6))
        self.search_y1.set(area.get('y1', 7))
        self.search_x2.set(area.get('x2', 2137))
        self.search_y2.set(area.get('y2', 1168))

        inv = config.get('inventory', {})
        if inv:
            self.inv_keep_color.set(inv.get('keep_color', '#DFA8F0'))
            self.inv_tolerance.set(inv.get('tolerance', 15))
            self.inv_trigger_key.set(inv.get('trigger_key', 'f3'))
            self.inv_trigger_modifier.set(inv.get('trigger_modifier', '없음'))

        self.update_color_list()
        self.update_exclude_list()
        self.setup_hotkey()

    # =========================================
    # 월드 보스
    # =========================================
    def fetch_world_boss_info(self):
        """월드 보스 정보 가져오기"""
        try:
            url = "https://helltides.com/worldboss"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')

                nuxt_match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>([^<]+)</script>', html)

                if nuxt_match:
                    data_str = nuxt_match.group(1)
                    now = datetime.now(timezone.utc)

                    boss_events = []
                    boss_names = ["Ashava", "Avarice", "Wandering Death", "Azmodan"]

                    all_times = re.findall(r'"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)"', data_str)

                    for time_str in all_times:
                        try:
                            boss_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            if boss_time > now:
                                time_pos = data_str.find(time_str)
                                search_range = data_str[max(0, time_pos-200):time_pos+200]
                                for boss in boss_names:
                                    if boss in search_range:
                                        boss_events.append((boss_time, boss))
                                        break
                        except:
                            continue

                    if boss_events:
                        boss_events.sort(key=lambda x: x[0])
                        next_time, next_boss = boss_events[0]
                        self.world_boss_timestamp = next_time
                        boss_name_ko = self._get_korean_boss_name(next_boss)
                        self.after(0, lambda b=boss_name_ko: self._update_boss_ui(b, ""))
                    else:
                        self.after(0, lambda: self._update_boss_ui("정보 없음", ""))
                else:
                    self.after(0, lambda: self._update_boss_ui("정보 없음", ""))

        except Exception as e:
            print(f"월드 보스 정보 가져오기 실패: {e}")
            self.after(0, lambda: self._update_boss_ui("연결 실패", ""))

        self.after(300000, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())

    def _get_korean_boss_name(self, boss_name_en):
        """보스 이름 한글화"""
        boss_names_ko = {
            "Ashava": "아샤바",
            "Avarice": "아바리스",
            "Wandering Death": "떠도는 죽음",
            "Azmodan": "아즈모단"
        }
        return boss_names_ko.get(boss_name_en, boss_name_en)

    def _update_boss_ui(self, boss_name, zone):
        """월드 보스 UI 업데이트"""
        self.world_boss_name.set(boss_name)
        self.world_boss_zone.set(zone)

        if hasattr(self, 'home_boss_name'):
            self.home_boss_name.configure(text=boss_name)

    def update_world_boss_timer(self):
        """월드 보스 남은 시간 업데이트"""
        if self.world_boss_timestamp:
            now = datetime.now(timezone.utc)
            diff = self.world_boss_timestamp - now

            if diff.total_seconds() > 0:
                total_seconds = int(diff.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                if hours > 0:
                    time_str = f"{hours}시간 {minutes}분 {seconds}초 후"
                    overlay_time = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    time_str = f"{minutes}분 {seconds}초 후"
                    overlay_time = f"{minutes}:{seconds:02d}"

                if total_seconds <= 300:
                    time_color = "#ff4444"
                    if self.boss_alert_enabled.get():
                        if self.boss_alerted_id != self.world_boss_timestamp:
                            self.boss_alerted_id = self.world_boss_timestamp
                            self.play_boss_alert()
                elif total_seconds <= 600:
                    time_color = "#ffaa00"
                else:
                    time_color = "#00ff00"

                self.world_boss_time.set(time_str)

                if hasattr(self, 'home_boss_time'):
                    self.home_boss_time.configure(text=f"⏰ {time_str}", text_color=time_color)

                # 오버레이 월드보스 업데이트
                if self.overlay_window and hasattr(self, 'world_boss_label') and self.world_boss_label:
                    try:
                        self.world_boss_label.configure(text=f"{self.world_boss_name.get()} {overlay_time}", fg=time_color)
                        self.overlay_window.update_idletasks()
                    except:
                        pass
            else:
                self.world_boss_time.set("스폰됨!")
                if hasattr(self, 'home_boss_time'):
                    self.home_boss_time.configure(text="⏰ 스폰됨! 새로고침 중...", text_color="#ff9900")
                threading.Thread(target=self.fetch_world_boss_info, daemon=True).start()

        self.after(1000, self.update_world_boss_timer)

    def refresh_world_boss(self):
        """월드 보스 정보 새로고침"""
        self.world_boss_name.set("로딩 중...")
        self.world_boss_time.set("")
        if hasattr(self, 'home_boss_name'):
            self.home_boss_name.configure(text="로딩 중...")
        if hasattr(self, 'home_boss_time'):
            self.home_boss_time.configure(text="")
        threading.Thread(target=self.fetch_world_boss_info, daemon=True).start()

    def play_boss_alert(self):
        """월드보스 5분 전 알림 소리"""
        def alert_sound():
            try:
                import time
                for _ in range(2):
                    winsound.Beep(800, 100)
                    time.sleep(0.05)
                    winsound.Beep(1000, 100)
                    time.sleep(0.1)
                    winsound.Beep(800, 100)
                    time.sleep(0.05)
                    winsound.Beep(1000, 100)
                    time.sleep(0.3)
            except:
                pass
        threading.Thread(target=alert_sound, daemon=True).start()

    # =========================================
    # 오버레이 배경색
    # =========================================
    def change_overlay_bg_color(self):
        """오버레이 배경색 선택"""
        color = colorchooser.askcolor(
            initialcolor=self.overlay_bg_color.get(),
            title="오버레이 배경색 선택"
        )
        if color[1]:
            self.overlay_bg_color.set(color[1])
            if hasattr(self, 'bg_color_preview'):
                self.bg_color_preview.configure(fg_color=color[1])
            self.apply_overlay_bg_color()

    def apply_overlay_bg_color(self):
        """오버레이에 배경색 적용"""
        if self.overlay_window:
            color = self.overlay_bg_color.get()

            def apply_to_children(widget):
                for child in widget.winfo_children():
                    try:
                        child.configure(bg=color)
                    except:
                        pass
                    apply_to_children(child)

            try:
                self.overlay_window.configure(bg=color)
                apply_to_children(self.overlay_window)
            except:
                pass

    # =========================================
    # 패치노트
    # =========================================
    def fetch_patch_notes(self):
        """GitHub에서 모든 릴리즈 정보 가져오기"""
        try:
            from constants import GITHUB_REPO
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'WonryeolHelper')

            with urllib.request.urlopen(req, timeout=15) as response:
                releases = json.loads(response.read().decode())

            self.after(0, lambda: self.display_patch_notes(releases))

        except Exception as e:
            self.after(0, lambda: self.display_patch_notes_error(str(e)))

    def display_patch_notes(self, releases):
        """패치노트 표시"""
        for widget in self.patch_notes_container.winfo_children():
            widget.destroy()

        if not releases:
            ctk.CTkLabel(self.patch_notes_container,
                        text="릴리즈 정보가 없습니다.",
                        font=ctk.CTkFont(family=DEFAULT_FONT, size=14)).pack(pady=20)
            return

        for release in releases:
            version = release.get('tag_name', 'Unknown')
            title = release.get('name', '') or version
            body = release.get('body', '') or '변경 사항 없음'
            published = release.get('published_at', '')[:10]

            release_frame = ctk.CTkFrame(self.patch_notes_container, fg_color="#2b2b2b", corner_radius=8)
            release_frame.pack(fill="x", pady=8)

            header_frame = ctk.CTkFrame(release_frame, fg_color="#1a5f2a", corner_radius=5)
            header_frame.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(header_frame, text=f"  {version}  ",
                        font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"),
                        text_color="white").pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(header_frame, text=published,
                        font=ctk.CTkFont(family=DEFAULT_FONT, size=12),
                        text_color="#aaaaaa").pack(side="right", padx=10, pady=8)

            if title and title != version:
                ctk.CTkLabel(release_frame, text=title,
                            font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                            text_color="#ffaa00").pack(anchor="w", padx=15, pady=(10, 5))

            ctk.CTkLabel(release_frame, text=body,
                        font=ctk.CTkFont(family=DEFAULT_FONT, size=13),
                        justify="left", wraplength=450).pack(anchor="w", padx=15, pady=(5, 15))

    def display_patch_notes_error(self, error):
        """패치노트 로드 실패 표시"""
        for widget in self.patch_notes_container.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.patch_notes_container,
                    text=f"패치노트를 불러올 수 없습니다.\n\n{error}",
                    font=ctk.CTkFont(family=DEFAULT_FONT, size=14),
                    text_color="#ff6666").pack(pady=20)

    # =========================================
    # 유틸리티
    # =========================================
    def validate_hex(self, hex_color):
        """HEX 색상 검증"""
        if not hex_color or len(hex_color) != 7 or hex_color[0] != '#':
            return False
        try:
            int(hex_color[1:], 16)
            return True
        except ValueError:
            return False
