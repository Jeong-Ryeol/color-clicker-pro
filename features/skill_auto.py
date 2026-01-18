# -*- coding: utf-8 -*-
"""
스킬 자동 사용 기능 (시간 기반)
"""

import time
import threading
import keyboard
import win32api

from constants import COLORS


class SkillAutoMixin:
    """스킬 자동 사용 믹스인"""

    def init_skill_auto_vars(self):
        """스킬 자동 관련 변수 초기화"""
        import customtkinter as ctk

        self.skill_auto_running = False
        self.skill_auto_active = False
        self.skill_auto_paused = False  # Enter로 일시정지
        self.skill_auto_trigger_key = ctk.StringVar(value="f6")
        self.skill_auto_trigger_modifier = ctk.StringVar(value="없음")
        self.skill_auto_last_trigger_time = 0

        # 스킬 슬롯 설정 (9개 슬롯)
        self.skill_slots = []
        for i in range(9):
            slot = {
                'enabled': ctk.BooleanVar(value=False),
                'key': ctk.StringVar(value=str(i + 1) if i < 9 else str(i + 1)),  # 기본: 1~9
                'cooldown': ctk.DoubleVar(value=0.0)  # 쿨타임 (초)
            }
            self.skill_slots.append(slot)

        # 각 스킬별 마지막 사용 시간
        self.skill_last_used = [0.0] * 9

        # 혼령사 물총 모드 (스페이스바 누르는 동안 매크로 스페이스바 스킵)
        self.honryeongsa_mode = ctk.BooleanVar(value=False)

    def toggle_skill_auto_running(self):
        """스킬 자동 시작/중지"""
        self.skill_auto_running = not self.skill_auto_running
        if self.skill_auto_running:
            self.skill_auto_start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.skill_auto_status_label.configure(text=f"🔴 [{self.skill_auto_trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
        else:
            self.skill_auto_active = False
            self.skill_auto_paused = False
            self.skill_auto_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.skill_auto_status_label.configure(text="⏸️ 대기 중")
            self.skill_auto_pause_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def run_skill_auto_loop(self):
        """스킬 자동 루프 - 각 스킬별 쿨타임 체크 후 입력"""
        import win32con

        self.after(0, lambda: self.skill_auto_status_label.configure(text="⚡ 스킬 실행 중..."))

        # 마지막 사용 시간 초기화 (즉시 사용 시작)
        self.skill_last_used = [0.0] * 9

        while self.skill_auto_active and self.skill_auto_running:
            # Enter로 일시정지된 상태
            if self.skill_auto_paused:
                time.sleep(0.01)
                continue

            current_time = time.time()

            for i, slot in enumerate(self.skill_slots):
                if not slot['enabled'].get():
                    continue

                cooldown = slot['cooldown'].get()
                if cooldown <= 0:
                    continue  # 쿨타임이 0이하면 스킵

                # 쿨타임 체크
                if current_time - self.skill_last_used[i] >= cooldown:
                    key = slot['key'].get()

                    # 혼령사 모드: 스페이스바를 직접 누르고 있으면 스킵
                    if self.honryeongsa_mode.get() and key.lower() == "space":
                        if win32api.GetAsyncKeyState(0x20) & 0x8000:  # VK_SPACE
                            continue

                    try:
                        # 마우스 클릭 처리
                        if key == "좌클릭" or key == "왼클릭":
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        elif key == "우클릭":
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                        elif key.lower() == "mouse4":
                            win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON1, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON1, 0)
                        elif key.lower() == "mouse5":
                            win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON2, 0)
                            win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON2, 0)
                        else:
                            # 키보드 키
                            keyboard.press_and_release(key.lower())
                    except:
                        pass
                    self.skill_last_used[i] = current_time

            time.sleep(0.01)  # CPU 절약 (10ms)

        self.skill_auto_active = False
        self.after(0, lambda: self.skill_auto_status_label.configure(text="⏹️ 중지됨"))
        self.after(0, lambda: self.skill_auto_pause_label.configure(text=""))

    def on_skill_auto_trigger_key(self, event):
        """스킬 자동 트리거 키 핸들러 (시작/중지)"""
        if not self.skill_auto_running:
            return

        if self.is_chatting():
            return

        if not self.check_modifier(self.skill_auto_trigger_modifier.get()):
            return

        current_time = time.time()
        if current_time - self.skill_auto_last_trigger_time < 0.3:
            return
        self.skill_auto_last_trigger_time = current_time

        if self.skill_auto_active:
            self.skill_auto_active = False
            self.skill_auto_paused = False
            self.after(0, lambda: self.skill_auto_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.skill_auto_pause_label.configure(text=""))
        else:
            self.skill_auto_active = True
            self.skill_auto_paused = False
            threading.Thread(target=self.run_skill_auto_loop, daemon=True).start()

    def on_skill_auto_enter_pause(self, event):
        """Enter 키로 pause/resume 토글 (채팅용)"""
        if not self.skill_auto_running or not self.skill_auto_active:
            return  # 실행 중이 아니면 무시

        self.skill_auto_paused = not self.skill_auto_paused
        if self.skill_auto_paused:
            self.after(0, lambda: self.skill_auto_pause_label.configure(text="⏸️ PAUSED (Enter로 재개)", text_color="#ff6600"))
        else:
            self.after(0, lambda: self.skill_auto_pause_label.configure(text=""))

    def change_skill_auto_trigger_key(self):
        """스킬 자동 핫키 변경"""
        import customtkinter as ctk
        import threading

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
                self.skill_auto_trigger_key.set(event.name)
                if hasattr(self, 'skill_auto_key_display'):
                    self.skill_auto_key_display.configure(text=event.name.upper())
                # 오버레이 핫키 라벨 즉시 업데이트
                if hasattr(self, 'overlay_hotkey_labels') and 'skill_auto_running' in self.overlay_hotkey_labels:
                    mod = self.skill_auto_trigger_modifier.get()
                    key = event.name.upper()
                    hotkey_text = f"{mod}+{key}" if mod != "없음" else key
                    self.overlay_hotkey_labels['skill_auto_running'].configure(text=hotkey_text)
                self.setup_hotkey()
                dialog.destroy()

        def start_key_detection():
            time.sleep(0.3)
            if dialog_active[0]:
                keyboard.on_press(on_key, suppress=False)

        threading.Thread(target=start_key_detection, daemon=True).start()

        def poll_mouse():
            time.sleep(0.3)
            while dialog_active[0]:
                if not (win32api.GetAsyncKeyState(0x05) & 0x8000) and not (win32api.GetAsyncKeyState(0x06) & 0x8000):
                    break
                time.sleep(0.01)
            time.sleep(0.1)
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.skill_auto_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.skill_auto_key_display.configure(text="MOUSE4") if hasattr(self, 'skill_auto_key_display') else None)
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.skill_auto_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.skill_auto_key_display.configure(text="MOUSE5") if hasattr(self, 'skill_auto_key_display') else None)
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

    def change_skill_slot_key(self, slot_idx):
        """스킬 슬롯의 키 변경 (키보드 + 마우스 버튼)"""
        import customtkinter as ctk
        import threading

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"슬롯 {slot_idx + 1} 키 설정")
        dialog.geometry("320x180")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="누를 키를 입력하세요\n(키보드 또는 마우스 버튼)",
                     font=ctk.CTkFont(size=14)).pack(pady=15)
        ctk.CTkLabel(dialog, text="마우스: 좌클릭, 우클릭, Mouse4, Mouse5",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack()

        dialog_active = [True]

        def update_slot_key(key_name):
            self.skill_slots[slot_idx]['key'].set(key_name)
            if hasattr(self, 'skill_slot_widgets') and slot_idx < len(self.skill_slot_widgets):
                self.skill_slot_widgets[slot_idx]['key_label'].configure(text=key_name.upper())

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.after(0, lambda: update_slot_key(event.name))
                dialog.destroy()

        def start_key_detection():
            time.sleep(0.3)
            if dialog_active[0]:
                keyboard.on_press(on_key, suppress=False)

        threading.Thread(target=start_key_detection, daemon=True).start()

        def poll_mouse():
            time.sleep(0.3)
            win32api.GetAsyncKeyState(0x01)
            win32api.GetAsyncKeyState(0x02)
            win32api.GetAsyncKeyState(0x05)
            win32api.GetAsyncKeyState(0x06)

            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x01) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_slot_key("좌클릭"))
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x02) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_slot_key("우클릭"))
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_slot_key("mouse4"))
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: update_slot_key("mouse5"))
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
