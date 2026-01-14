# -*- coding: utf-8 -*-
"""
아이템 버리기 기능
"""

import time
import pyautogui
import keyboard

from constants import COLORS


class DiscardMixin:
    """아이템 버리기 믹스인"""

    def init_discard_vars(self):
        """버리기 관련 변수 초기화"""
        import customtkinter as ctk

        self.discard_running = False
        self.discard_active = False
        self.discard_trigger_key = ctk.StringVar(value="f1")
        self.discard_trigger_modifier = ctk.StringVar(value="없음")
        self.discard_last_trigger_time = 0
        self.discard_delay = ctk.DoubleVar(value=0.01)

    def toggle_discard_running(self):
        """아이템 버리기 시작/중지"""
        self.discard_running = not self.discard_running
        if self.discard_running:
            self.discard_start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.discard_status_label.configure(text=f"🔴 [{self.discard_trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
        else:
            self.discard_active = False
            self.discard_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.discard_status_label.configure(text="⏸️ 대기 중")
            self.discard_progress_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def run_discard_loop(self):
        """버리기 루프 실행"""
        count = 0
        while self.discard_active and self.discard_running:
            keyboard.press('ctrl')
            time.sleep(0.01)
            pyautogui.click()
            time.sleep(0.01)
            keyboard.release('ctrl')

            count += 1
            self.after(0, lambda c=count: self.discard_progress_label.configure(text=f"버림: {c}"))
            time.sleep(self.discard_delay.get())

        self.discard_active = False
        self.after(0, lambda: self.discard_status_label.configure(text=f"🔴 [{self.discard_trigger_key.get().upper()}] 키로 시작"))
