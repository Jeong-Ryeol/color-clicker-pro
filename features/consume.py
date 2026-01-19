# -*- coding: utf-8 -*-
"""
아이템 먹기 기능
"""

import time
import pyautogui
import keyboard
import win32api

from constants import COLORS


class ConsumeMixin:
    """아이템 먹기 믹스인"""

    def init_consume_vars(self):
        """먹기 관련 변수 초기화"""
        import customtkinter as ctk

        self.consume_running = False
        self.consume_active = False
        self.consume_paused = False  # Enter로 일시정지
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
            self.consume_paused = False
            self.consume_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.consume_status_label.configure(text="⏸️ 대기 중")
            self.consume_progress_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def run_consume_loop(self):
        """먹기 루프 실행 - 선택한 입력 반복"""
        import win32api
        import win32con

        delay = self.consume_delay.get()
        action_key = self.consume_action_key.get()

        self.after(0, lambda: self.consume_status_label.configure(text=f"🍖 먹는 중... ({action_key})"))

        consumed = 0
        while self.consume_active and self.consume_running:
            # Enter로 일시정지된 상태
            if self.consume_paused:
                time.sleep(0.01)
                continue

            # 마우스 클릭
            if action_key == "좌클릭" or action_key == "왼클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif action_key == "우클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif action_key.lower() == "mouse4":
                win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON1, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON1, 0)
            elif action_key.lower() == "mouse5":
                win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON2, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON2, 0)
            else:
                # 키보드 키
                try:
                    keyboard.press_and_release(action_key.lower())
                except:
                    pass

            consumed += 1

            if delay > 0.001:
                time.sleep(delay)

            # 진행상황 (100개마다)
            if consumed % 100 == 0:
                self.after(0, lambda c=consumed: self.consume_progress_label.configure(text=f"{c}회"))

        self.consume_active = False
        self.after(0, lambda: self.consume_status_label.configure(text="⏹️ 중지됨"))
        self.after(0, lambda c=consumed: self.consume_progress_label.configure(text=f"총 {c}회 입력"))

    def on_consume_trigger_key(self, event):
        """먹기 트리거 키 핸들러"""
        import threading

        if not self.consume_running:
            return

        if self.is_chatting():
            return

        if not self.check_modifier(self.consume_trigger_modifier.get()):
            return

        current_time = time.time()
        if current_time - self.consume_last_trigger_time < 0.3:
            return
        self.consume_last_trigger_time = current_time

        if self.consume_active:
            self.consume_active = False
            self.consume_paused = False
            self.after(0, lambda: self.consume_status_label.configure(text="⏹️ 중지됨"))
        else:
            self.consume_active = True
            self.consume_paused = False
            threading.Thread(target=self.run_consume_loop, daemon=True).start()

    def on_consume_enter_pause(self, event):
        """Enter 키로 먹기 pause/resume 토글"""
        if not self.consume_running or not self.consume_active:
            return

        self.consume_paused = not self.consume_paused
        if self.consume_paused:
            self.after(0, lambda: self.consume_status_label.configure(text="⏸️ PAUSED (Enter로 재개)"))
        else:
            action_key = self.consume_action_key.get()
            self.after(0, lambda: self.consume_status_label.configure(text=f"🍖 먹는 중... ({action_key})"))

    def change_consume_trigger_key(self):
        """먹기 핫키 변경"""
        import customtkinter as ctk
        import threading
        import win32api

        dialog = ctk.CTkToplevel(self)
        dialog.title("핫키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 핫키를 누르세요...\n(마우스 4/5번도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                # 충돌 체크 - 충돌 시 설정 안 함
                conflict_msg = self.check_hotkey_conflict(event.name)
                if conflict_msg:
                    from tkinter import messagebox
                    self.after(100, lambda: messagebox.showwarning("핫키 충돌", conflict_msg))
                    dialog.destroy()
                    return
                self.consume_trigger_key.set(event.name)
                if hasattr(self, 'consume_key_display'):
                    self.consume_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        # 딜레이 후 키 감지 시작 (버튼 클릭 잔여 입력 방지)
        def start_key_detection():
            time.sleep(0.3)
            if dialog_active[0]:
                keyboard.on_press(on_key, suppress=False)

        threading.Thread(target=start_key_detection, daemon=True).start()

        # 마우스 버튼 폴링
        def poll_mouse():
            time.sleep(0.3)  # 딜레이
            # 모든 버튼 떼어질 때까지 대기
            while dialog_active[0]:
                if not (win32api.GetAsyncKeyState(0x05) & 0x8000) and not (win32api.GetAsyncKeyState(0x06) & 0x8000):
                    break
                time.sleep(0.01)
            time.sleep(0.1)  # 추가 안정화 딜레이
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.consume_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.consume_key_display.configure(text="MOUSE4") if hasattr(self, 'consume_key_display') else None)
                    # 버튼 떼어질 때까지 대기
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.consume_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.consume_key_display.configure(text="MOUSE5") if hasattr(self, 'consume_key_display') else None)
                    # 버튼 떼어질 때까지 대기
                    while win32api.GetAsyncKeyState(0x06) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            self.setup_hotkey()  # Lock 안에서 unhook_all + 재등록
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def change_consume_action_key(self):
        """아이템 먹기 - 누를 키 변경 (마우스 클릭 포함)"""
        import customtkinter as ctk
        import threading

        dialog = ctk.CTkToplevel(self)
        dialog.title("누를 키 설정")
        dialog.geometry("320x180")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="누를 키를 입력하세요\n(키보드 또는 마우스 버튼)",
                     font=ctk.CTkFont(size=14)).pack(pady=15)

        ctk.CTkLabel(dialog, text="마우스: 좌클릭, 우클릭, Mouse4, Mouse5",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack()

        dialog_active = [True]

        def update_action_key(key_name):
            """누를 키 업데이트"""
            self.consume_action_key.set(key_name)
            display_text = key_name.upper()
            if hasattr(self, 'consume_action_display'):
                self.consume_action_display.configure(text=display_text)

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                key_name = event.name.upper()
                self.after(0, lambda: update_action_key(key_name))
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def poll_mouse():
            # 버튼 클릭이 해제될 때까지 대기 (0.3초)
            time.sleep(0.3)
            # 기존 마우스 상태 클리어
            win32api.GetAsyncKeyState(0x01)
            win32api.GetAsyncKeyState(0x02)
            win32api.GetAsyncKeyState(0x05)
            win32api.GetAsyncKeyState(0x06)

            while dialog_active[0]:
                # 좌클릭
                if win32api.GetAsyncKeyState(0x01) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_action_key("좌클릭"))
                    self.after(0, dialog.destroy)
                    break
                # 우클릭
                if win32api.GetAsyncKeyState(0x02) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_action_key("우클릭"))
                    self.after(0, dialog.destroy)
                    break
                # Mouse4
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_action_key("mouse4"))
                    self.after(0, dialog.destroy)
                    break
                # Mouse5
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_action_key("mouse5"))
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
