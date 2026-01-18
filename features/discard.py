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
        """버리기 루프 실행 - 인벤토리 전체 한 번 버리기"""
        import win32api
        import win32con

        positions = self.get_inventory_positions()
        total = len(positions)
        delay = self.discard_delay.get()

        self.after(0, lambda: self.discard_status_label.configure(text="🗑️ 버리는 중..."))

        discarded = 0
        for i, (x, y, col) in enumerate(positions):
            if not self.discard_active:
                break

            # 초고속: 텔레포트 + 즉시 Ctrl+클릭
            win32api.SetCursorPos((x, y))
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            discarded += 1

            if delay > 0.001:
                time.sleep(delay)

            # 진행상황 (10개마다)
            if i % 10 == 0:
                self.after(0, lambda idx=i, t=total: self.discard_progress_label.configure(text=f"{idx+1}/{t}"))

        self.discard_active = False
        self.after(0, lambda: self.discard_status_label.configure(text="✅ 완료!"))
        self.after(0, lambda d=discarded: self.discard_progress_label.configure(text=f"총 {d}개 버림"))

    def run_discard_simultaneous(self):
        """테스트: 동시 버리기 - 모든 위치에 동시에 Ctrl+클릭"""
        import win32api
        import win32con
        import threading

        positions = self.get_inventory_positions()
        total = len(positions)

        self.after(0, lambda: self.discard_status_label.configure(text="⚡ 동시 버리기 중..."))

        def click_at(x, y):
            win32api.SetCursorPos((x, y))
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        threads = []
        for x, y, col in positions:
            t = threading.Thread(target=click_at, args=(x, y))
            threads.append(t)

        # 모든 스레드 동시 시작
        for t in threads:
            t.start()

        # 완료 대기
        for t in threads:
            t.join()

        self.discard_active = False
        self.after(0, lambda: self.discard_status_label.configure(text="✅ 동시 버리기 완료!"))
        self.after(0, lambda t=total: self.discard_progress_label.configure(text=f"총 {t}개 시도"))

    def on_discard_trigger_key(self, event):
        """버리기 트리거 키 핸들러"""
        import threading

        if not self.discard_running:
            return

        if self.is_chatting():
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
                self.discard_trigger_key.set(event.name)
                if hasattr(self, 'discard_key_display'):
                    self.discard_key_display.configure(text=event.name.upper())
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
                    self.after(0, lambda: self.discard_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.discard_key_display.configure(text="MOUSE4") if hasattr(self, 'discard_key_display') else None)
                    # 버튼 떼어질 때까지 대기
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.discard_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.discard_key_display.configure(text="MOUSE5") if hasattr(self, 'discard_key_display') else None)
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
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
