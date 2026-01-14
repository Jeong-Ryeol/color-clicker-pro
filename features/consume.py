# -*- coding: utf-8 -*-
"""
아이템 먹기 기능
"""

import time
import pyautogui
import keyboard

from constants import COLORS


class ConsumeMixin:
    """아이템 먹기 믹스인"""

    def init_consume_vars(self):
        """먹기 관련 변수 초기화"""
        import customtkinter as ctk

        self.consume_running = False
        self.consume_active = False
        self.consume_trigger_key = ctk.StringVar(value="mouse5")
        self.consume_trigger_modifier = ctk.StringVar(value="없음")
        self.consume_last_trigger_time = 0
        self.consume_delay = ctk.DoubleVar(value=0.01)
        self.consume_input_type = ctk.StringVar(value="우클릭")
        self.consume_action_key = ctk.StringVar(value="우클릭")

    def toggle_consume_running(self):
        """아이템 먹기 시작/중지"""
        self.consume_running = not self.consume_running
        if self.consume_running:
            self.consume_start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.consume_status_label.configure(text=f"🔴 [{self.consume_trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
        else:
            self.consume_active = False
            self.consume_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.consume_status_label.configure(text="⏸️ 대기 중")
            self.consume_progress_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def run_consume_loop(self):
        """먹기 루프 실행"""
        count = 0
        action = self.consume_action_key.get()

        while self.consume_active and self.consume_running:
            if action == "우클릭":
                pyautogui.rightClick()
            elif action == "왼클릭":
                pyautogui.click()
            else:
                keyboard.press_and_release(action.lower())

            count += 1
            self.after(0, lambda c=count: self.consume_progress_label.configure(text=f"먹음: {c}"))
            time.sleep(self.consume_delay.get())

        self.consume_active = False
        self.after(0, lambda: self.consume_status_label.configure(text=f"🔴 [{self.consume_trigger_key.get().upper()}] 키로 시작"))

    def on_consume_trigger_key(self, event):
        """먹기 트리거 키 핸들러"""
        import threading

        if not self.consume_running:
            return

        if not self.check_modifier(self.consume_trigger_modifier.get()):
            return

        current_time = time.time()
        if current_time - self.consume_last_trigger_time < 0.3:
            return
        self.consume_last_trigger_time = current_time

        if self.consume_active:
            self.consume_active = False
            self.after(0, lambda: self.consume_status_label.configure(text="⏹️ 중지됨"))
        else:
            self.consume_active = True
            threading.Thread(target=self.run_consume_loop, daemon=True).start()

    def change_consume_trigger_key(self):
        """먹기 핫키 변경"""
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
                self.consume_trigger_key.set(event.name)
                if hasattr(self, 'consume_key_display'):
                    self.consume_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def change_consume_action_key(self):
        """먹기 액션 키 변경"""
        import customtkinter as ctk
        from tkinter import simpledialog

        result = simpledialog.askstring("키 설정", "사용할 키 입력\n(우클릭, 왼클릭, 또는 키보드 키)")
        if result:
            self.consume_action_key.set(result)
            if hasattr(self, 'consume_action_display'):
                self.consume_action_display.configure(text=result.upper())
