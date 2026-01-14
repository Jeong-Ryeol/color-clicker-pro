# -*- coding: utf-8 -*-
"""
아이템 팔기 기능
"""

import time
import pyautogui
import keyboard

from constants import COLORS


class SellMixin:
    """아이템 팔기 믹스인"""

    def init_sell_vars(self):
        """팔기 관련 변수 초기화"""
        import customtkinter as ctk

        self.sell_running = False
        self.sell_active = False
        self.sell_trigger_key = ctk.StringVar(value="f2")
        self.sell_trigger_modifier = ctk.StringVar(value="없음")
        self.sell_last_trigger_time = 0
        self.sell_delay = ctk.DoubleVar(value=0.01)

    def toggle_sell_running(self):
        """아이템 팔기 시작/중지"""
        self.sell_running = not self.sell_running
        if self.sell_running:
            self.sell_start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.sell_status_label.configure(text=f"🔴 [{self.sell_trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
        else:
            self.sell_active = False
            self.sell_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.sell_status_label.configure(text="⏸️ 대기 중")
            self.sell_progress_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def run_sell_loop(self):
        """팔기 루프 실행"""
        count = 0
        while self.sell_active and self.sell_running:
            keyboard.press('ctrl')
            time.sleep(0.01)
            pyautogui.click()
            time.sleep(0.01)
            keyboard.release('ctrl')

            count += 1
            self.after(0, lambda c=count: self.sell_progress_label.configure(text=f"판매: {c}"))
            time.sleep(self.sell_delay.get())

        self.sell_active = False
        self.after(0, lambda: self.sell_status_label.configure(text=f"🔴 [{self.sell_trigger_key.get().upper()}] 키로 시작"))
