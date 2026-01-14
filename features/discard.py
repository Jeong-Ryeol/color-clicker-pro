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

    def on_discard_trigger_key(self, event):
        """버리기 트리거 키 핸들러"""
        import threading

        if not self.discard_running:
            return

        if not self.check_modifier(self.discard_trigger_modifier.get()):
            return

        current_time = time.time()
        if current_time - self.discard_last_trigger_time < 0.3:
            return
        self.discard_last_trigger_time = current_time

        if self.discard_active:
            self.discard_active = False
            self.after(0, lambda: self.discard_status_label.configure(text="⏹️ 중지됨"))
        else:
            self.discard_active = True
            threading.Thread(target=self.run_discard_loop, daemon=True).start()

    def change_discard_trigger_key(self):
        """버리기 핫키 변경"""
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
                self.discard_trigger_key.set(event.name)
                if hasattr(self, 'discard_key_display'):
                    self.discard_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
