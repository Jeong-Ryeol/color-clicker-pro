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

    def on_sell_trigger_key(self, event):
        """팔기 트리거 키 핸들러"""
        import threading

        if not self.sell_running:
            return

        if not self.check_modifier(self.sell_trigger_modifier.get()):
            return

        current_time = time.time()
        if current_time - self.sell_last_trigger_time < 0.3:
            return
        self.sell_last_trigger_time = current_time

        if self.sell_active:
            self.sell_active = False
            self.after(0, lambda: self.sell_status_label.configure(text="⏹️ 중지됨"))
        else:
            self.sell_active = True
            threading.Thread(target=self.run_sell_loop, daemon=True).start()

    def change_sell_trigger_key(self):
        """팔기 핫키 변경"""
        import customtkinter as ctk

        dialog = ctk.CTkToplevel(self)
        dialog.title("핫키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 핫키를 누르세요...",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.sell_trigger_key.set(event.name)
                if hasattr(self, 'sell_key_display'):
                    self.sell_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
