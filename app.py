# -*- coding: utf-8 -*-
"""
Wonryeol Helper - 메인 애플리케이션
모든 믹스인을 조합하여 완전한 앱 구성
"""

import customtkinter as ctk
from tkinter import messagebox
import threading

# 상수
from constants import VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_FONT, COLORS

# 기능 믹스인
from features.belial import BelialMixin
from features.inventory import InventoryMixin
from features.discard import DiscardMixin
from features.sell import SellMixin
from features.consume import ConsumeMixin

# UI 믹스인
from ui.overlay import OverlayMixin

# 유틸리티 믹스인
from utils.updater import UpdaterMixin


class ColorClickerApp(
    ctk.CTk,
    BelialMixin,
    InventoryMixin,
    DiscardMixin,
    SellMixin,
    ConsumeMixin,
    OverlayMixin,
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
        self.init_overlay_vars()
        self.init_common_vars()

        # UI 설정
        self.setup_ui()

        # 설정 불러오기
        self.load_config()

        # 핫키 설정
        self.setup_hotkey()

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

    def setup_ui(self):
        """UI 설정 - 기존 color_clicker_modern.py의 setup_ui 메서드 참조"""
        # 이 메서드는 기존 코드에서 가져와야 합니다
        # 현재는 플레이스홀더입니다
        pass

    def setup_hotkey(self):
        """핫키 설정"""
        # 기존 코드에서 가져와야 합니다
        pass

    def load_config(self, show_message=False):
        """설정 불러오기"""
        # 기존 코드에서 가져와야 합니다
        pass

    def save_config(self):
        """설정 저장"""
        # 기존 코드에서 가져와야 합니다
        pass

    def update_mouse_pos(self):
        """마우스 좌표 업데이트"""
        # 기존 코드에서 가져와야 합니다
        pass

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

    def update_home_status_now(self):
        """Home 탭 상태 즉시 업데이트"""
        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running
        }

        active_map = {
            "is_running": self.detection_active,
            "inv_running": self.inv_cleanup_active,
            "discard_running": self.discard_active,
            "sell_running": self.sell_active,
            "consume_running": self.consume_active
        }

        for attr, is_on in states.items():
            # Home 탭 상태 라벨 업데이트
            if attr in self.home_status_labels:
                label = self.home_status_labels[attr]
                if is_on:
                    label.configure(text="ON", text_color=COLORS["on_color"])
                else:
                    label.configure(text="OFF", text_color=COLORS["off_color"])

            # Home 탭 스위치 상태 업데이트
            if attr in self.home_switches:
                switch = self.home_switches[attr]
                if is_on and not switch.get():
                    switch.select()
                elif not is_on and switch.get():
                    switch.deselect()

            # 오버레이 상태 업데이트
            if hasattr(self, 'overlay_labels') and attr in self.overlay_labels:
                label = self.overlay_labels[attr]
                if is_on:
                    label.configure(text="● ON", fg=COLORS["on_color"])
                else:
                    label.configure(text="● OFF", fg=COLORS["off_color"])

            # 오버레이 기능명 색상 업데이트
            if hasattr(self, 'overlay_name_labels') and attr in self.overlay_name_labels:
                name_label = self.overlay_name_labels[attr]
                is_active = active_map.get(attr, False)
                if is_active:
                    name_label.configure(fg=COLORS["active_color"])
                else:
                    name_label.configure(fg='#ffffff')

        self.update_idletasks()

    def on_emergency_stop(self, event=None):
        """긴급 정지 - 실행 중인 클릭/매크로 동작만 즉시 중지"""
        self.detection_active = False
        self.inv_cleanup_active = False
        self.discard_active = False
        self.sell_active = False
        self.consume_active = False

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

    def validate_hex(self, hex_color):
        """HEX 색상 검증"""
        if not hex_color or len(hex_color) != 7 or hex_color[0] != '#':
            return False
        try:
            int(hex_color[1:], 16)
            return True
        except ValueError:
            return False

    def fetch_world_boss_info(self):
        """월드 보스 정보 가져오기"""
        # 기존 코드에서 가져와야 합니다
        pass

    def update_world_boss_timer(self):
        """월드 보스 타이머 업데이트"""
        # 기존 코드에서 가져와야 합니다
        pass
