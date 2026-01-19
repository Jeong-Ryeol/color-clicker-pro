# -*- coding: utf-8 -*-
"""
스킬 자동 사용 기능 (시간 기반) - 5개 프리셋 지원
"""

import time
import threading
import keyboard
import win32api

from constants import COLORS


class SkillAutoMixin:
    """스킬 자동 사용 믹스인 - 5개 프리셋 지원"""

    SKILL_PRESET_COUNT = 5

    def init_skill_auto_vars(self):
        """스킬 자동 관련 변수 초기화 - 5개 프리셋"""
        import customtkinter as ctk

        # 5개 프리셋 배열
        self.skill_presets = []
        for i in range(self.SKILL_PRESET_COUNT):
            preset = {
                'name': ctk.StringVar(value=f"프리셋 {i + 1}"),
                'running': False,          # 시작 버튼으로 ON/OFF
                'active': False,           # 핫키로 실행 중
                'paused': False,           # Enter로 일시정지
                'trigger_key': ctk.StringVar(value=f"f{6 + i}"),  # F6~F10
                'trigger_modifier': ctk.StringVar(value="없음"),
                'last_trigger_time': 0,
                'slots': [],               # 9개 슬롯
                'last_used': [0.0] * 9,    # 각 스킬별 마지막 사용 시간
                'honryeongsa_mode': ctk.BooleanVar(value=False),
                # UI 위젯 참조 (동적 생성)
                '_start_btn': None,
                '_status_label': None,
                '_pause_label': None,
                '_slot_widgets': []
            }
            # 9개 슬롯 초기화
            for j in range(9):
                slot = {
                    'enabled': ctk.BooleanVar(value=False),
                    'key': ctk.StringVar(value=str(j + 1)),
                    'cooldown': ctk.DoubleVar(value=0.0),
                    'hold': ctk.BooleanVar(value=False)  # hold 모드: 꾹 누르기
                }
                preset['slots'].append(slot)
            self.skill_presets.append(preset)

        # 현재 UI에서 선택된 프리셋 인덱스
        self.skill_current_preset_idx = ctk.IntVar(value=0)

        # 하위 호환성을 위한 래퍼 (기존 코드에서 사용 시)
        self.skill_auto_running = False
        self.skill_auto_active = False
        self.skill_auto_paused = False
        self.skill_auto_trigger_key = self.skill_presets[0]['trigger_key']
        self.skill_auto_trigger_modifier = self.skill_presets[0]['trigger_modifier']
        self.skill_slots = self.skill_presets[0]['slots']
        self.honryeongsa_mode = self.skill_presets[0]['honryeongsa_mode']

    def _execute_skill_key(self, key):
        """스킬 키 입력 실행 (공통 함수)"""
        import win32con
        try:
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
                keyboard.press_and_release(key.lower())
        except:
            pass

    def _press_skill_key(self, key):
        """스킬 키 누르기 (hold 모드용 - 누르고 유지)"""
        import win32con
        try:
            if key == "좌클릭" or key == "왼클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            elif key == "우클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            elif key.lower() == "mouse4":
                win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON1, 0)
            elif key.lower() == "mouse5":
                win32api.mouse_event(win32con.MOUSEEVENTF_XDOWN, 0, 0, win32con.XBUTTON2, 0)
            else:
                keyboard.press(key.lower())
        except:
            pass

    def _release_skill_key(self, key):
        """스킬 키 떼기 (hold 모드용)"""
        import win32con
        try:
            if key == "좌클릭" or key == "왼클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif key == "우클릭":
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif key.lower() == "mouse4":
                win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON1, 0)
            elif key.lower() == "mouse5":
                win32api.mouse_event(win32con.MOUSEEVENTF_XUP, 0, 0, win32con.XBUTTON2, 0)
            else:
                keyboard.release(key.lower())
        except:
            pass

    def _release_all_hold_keys(self, preset):
        """프리셋의 모든 hold 키 떼기"""
        for i, slot in enumerate(preset['slots']):
            if slot['enabled'].get() and slot['hold'].get():
                key = slot['key'].get()
                self._release_skill_key(key)

    def toggle_skill_preset_running(self, preset_idx):
        """특정 프리셋 시작/중지"""
        preset = self.skill_presets[preset_idx]
        preset['running'] = not preset['running']

        if preset['running']:
            # 시작
            if preset['_start_btn']:
                preset['_start_btn'].configure(
                    text="⏹️ 중지",
                    fg_color=COLORS["danger"],
                    hover_color=COLORS["danger_hover"]
                )
            if preset['_status_label']:
                preset['_status_label'].configure(
                    text=f"🔴 [{preset['trigger_key'].get().upper()}] 키로 시작"
                )
        else:
            # 중지
            preset['active'] = False
            preset['paused'] = False
            if preset['_start_btn']:
                preset['_start_btn'].configure(
                    text="▶️ 시작",
                    fg_color=COLORS["success"],
                    hover_color=COLORS["success_hover"]
                )
            if preset['_status_label']:
                preset['_status_label'].configure(text="⏸️ 대기 중")
            if preset['_pause_label']:
                preset['_pause_label'].configure(text="")

        # 오버레이 업데이트
        if hasattr(self, 'refresh_overlay_for_skill_presets'):
            self.refresh_overlay_for_skill_presets()

        self.update_home_status_now()
        self._update_skill_preset_summary()

    def run_skill_auto_loop(self, preset_idx):
        """스킬 자동 루프 - 특정 프리셋에 대해 실행"""
        preset = self.skill_presets[preset_idx]

        # 상태 라벨 업데이트
        if preset['_status_label']:
            self.after(0, lambda: preset['_status_label'].configure(text="⚡ 스킬 실행 중..."))

        # 오버레이 상태 업데이트
        self.after(0, lambda: self._update_overlay_preset_status(preset_idx, "active"))

        # 마지막 사용 시간 초기화
        preset['last_used'] = [0.0] * 9

        # hold 모드 키 상태 추적 (눌려있는지 여부)
        hold_key_pressed = [False] * 9

        while preset['active'] and preset['running']:
            if preset['paused']:
                # 일시정지 시 hold 키 모두 떼기
                for i, slot in enumerate(preset['slots']):
                    if hold_key_pressed[i] and slot['hold'].get():
                        self._release_skill_key(slot['key'].get())
                        hold_key_pressed[i] = False
                time.sleep(0.01)
                continue

            current_time = time.time()

            for i, slot in enumerate(preset['slots']):
                if not slot['enabled'].get():
                    # 비활성화된 슬롯의 hold 키 떼기
                    if hold_key_pressed[i]:
                        self._release_skill_key(slot['key'].get())
                        hold_key_pressed[i] = False
                    continue

                cooldown = slot['cooldown'].get()
                if cooldown <= 0:
                    continue

                key = slot['key'].get()
                is_hold = slot['hold'].get()

                if current_time - preset['last_used'][i] >= cooldown:
                    # 혼령사 모드
                    if preset['honryeongsa_mode'].get() and key.lower() == "space":
                        if win32api.GetAsyncKeyState(0x20) & 0x8000:
                            continue

                    if is_hold:
                        # hold 모드: 아직 안 눌렸으면 누르기
                        if not hold_key_pressed[i]:
                            self._press_skill_key(key)
                            hold_key_pressed[i] = True
                    else:
                        # 일반 모드: 누르고 떼기
                        self._execute_skill_key(key)

                    preset['last_used'][i] = current_time

            time.sleep(0.01)

        # 루프 종료 시 모든 hold 키 떼기
        for i, slot in enumerate(preset['slots']):
            if hold_key_pressed[i]:
                self._release_skill_key(slot['key'].get())
                hold_key_pressed[i] = False

        preset['active'] = False
        if preset['_status_label']:
            self.after(0, lambda: preset['_status_label'].configure(text="⏹️ 중지됨"))
        if preset['_pause_label']:
            self.after(0, lambda: preset['_pause_label'].configure(text=""))

        # 오버레이 상태 업데이트
        self.after(0, lambda: self._update_overlay_preset_status(preset_idx, "stopped"))

    def on_skill_preset_trigger_key(self, preset_idx, event=None):
        """프리셋별 핫키 핸들러"""
        preset = self.skill_presets[preset_idx]

        if not preset['running']:
            return

        if self.is_chatting():
            return

        if not self.check_modifier(preset['trigger_modifier'].get()):
            return

        current_time = time.time()
        if current_time - preset['last_trigger_time'] < 0.3:
            return
        preset['last_trigger_time'] = current_time

        if preset['active']:
            # 중지
            preset['active'] = False
            preset['paused'] = False
            if preset['_status_label']:
                self.after(0, lambda: preset['_status_label'].configure(text="⏹️ 중지됨"))
            if preset['_pause_label']:
                self.after(0, lambda: preset['_pause_label'].configure(text=""))
            self.after(0, lambda: self._update_overlay_preset_status(preset_idx, "stopped"))
        else:
            # 시작
            preset['active'] = True
            preset['paused'] = False
            threading.Thread(target=self.run_skill_auto_loop, args=(preset_idx,), daemon=True).start()

    def on_skill_auto_enter_pause(self, event):
        """Enter 키로 모든 활성 프리셋 pause/resume 토글"""
        for i, preset in enumerate(self.skill_presets):
            if not preset['running'] or not preset['active']:
                continue

            preset['paused'] = not preset['paused']
            if preset['paused']:
                if preset['_pause_label']:
                    self.after(0, lambda p=preset: p['_pause_label'].configure(
                        text="⏸️ PAUSED (Enter로 재개)",
                        text_color="#ff6600"
                    ))
                self.after(0, lambda idx=i: self._update_overlay_preset_status(idx, "paused"))
            else:
                if preset['_pause_label']:
                    self.after(0, lambda p=preset: p['_pause_label'].configure(text=""))
                self.after(0, lambda idx=i: self._update_overlay_preset_status(idx, "active"))

    def _update_overlay_preset_status(self, preset_idx, status):
        """오버레이에서 프리셋 상태 업데이트"""
        attr_name = f"skill_preset_{preset_idx}_running"
        if hasattr(self, 'overlay_labels') and attr_name in self.overlay_labels:
            label = self.overlay_labels[attr_name]
            if status == "active":
                label.configure(text="⚡ 실행중", fg="#00ff00")
            elif status == "paused":
                label.configure(text="⏸ 일시정지", fg="#ff6600")
            else:  # stopped
                label.configure(text="● OFF", fg="#666666")

        # 오버레이 이름 라벨 색상도 업데이트
        if hasattr(self, 'overlay_name_labels') and attr_name in self.overlay_name_labels:
            name_label = self.overlay_name_labels[attr_name]
            preset = self.skill_presets[preset_idx]
            if preset['active']:
                name_label.configure(fg="#00ff00")
            else:
                name_label.configure(fg="#ffffff")

    def _update_skill_preset_summary(self):
        """하단 프리셋 상태 요약 업데이트"""
        if not hasattr(self, 'skill_preset_summary_labels'):
            return

        for i, preset in enumerate(self.skill_presets):
            if i < len(self.skill_preset_summary_labels):
                labels = self.skill_preset_summary_labels[i]
                if preset['running']:
                    if preset['active']:
                        labels['status'].configure(text="RUN", text_color="#00ff00")
                    else:
                        labels['status'].configure(text="ON", text_color="#ffaa00")
                else:
                    labels['status'].configure(text="OFF", text_color="#666666")
                labels['key'].configure(text=preset['trigger_key'].get().upper())

    def change_skill_preset_trigger_key(self, preset_idx):
        """특정 프리셋의 핫키 변경"""
        import customtkinter as ctk

        preset = self.skill_presets[preset_idx]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"프리셋 {preset_idx + 1} 핫키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 핫키를 누르세요...\n(마우스 4/5번도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                # 충돌 체크
                conflict_msg = self.check_skill_preset_hotkey_conflict(preset_idx, event.name)
                if conflict_msg:
                    from tkinter import messagebox
                    self.after(100, lambda: messagebox.showwarning("핫키 충돌", conflict_msg))
                    dialog.destroy()
                    return
                preset['trigger_key'].set(event.name)
                if hasattr(self, 'skill_preset_key_display') and self.skill_current_preset_idx.get() == preset_idx:
                    self.skill_preset_key_display.configure(text=event.name.upper())
                self._update_skill_preset_summary()
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
                    self.after(0, lambda: preset['trigger_key'].set("mouse4"))
                    if hasattr(self, 'skill_preset_key_display') and self.skill_current_preset_idx.get() == preset_idx:
                        self.after(0, lambda: self.skill_preset_key_display.configure(text="MOUSE4"))
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self._update_skill_preset_summary)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: preset['trigger_key'].set("mouse5"))
                    if hasattr(self, 'skill_preset_key_display') and self.skill_current_preset_idx.get() == preset_idx:
                        self.after(0, lambda: self.skill_preset_key_display.configure(text="MOUSE5"))
                    while win32api.GetAsyncKeyState(0x06) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self._update_skill_preset_summary)
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

    def check_skill_preset_hotkey_conflict(self, preset_idx, new_key):
        """프리셋 핫키 충돌 체크"""
        new_key_lower = new_key.lower()

        # 다른 프리셋과 충돌 체크
        for i, preset in enumerate(self.skill_presets):
            if i == preset_idx:
                continue
            if preset['trigger_key'].get().lower() == new_key_lower:
                return f"프리셋 {i + 1}에서 이미 사용 중인 핫키입니다."

        # 다른 기능과 충돌 체크
        return self.check_hotkey_conflict(new_key)

    def change_skill_preset_slot_key(self, preset_idx, slot_idx):
        """특정 프리셋의 슬롯 키 변경"""
        import customtkinter as ctk

        preset = self.skill_presets[preset_idx]

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"프리셋 {preset_idx + 1} - 슬롯 {slot_idx + 1} 키 설정")
        dialog.geometry("320x180")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="누를 키를 입력하세요\n(키보드 또는 마우스 버튼)",
                     font=ctk.CTkFont(size=14)).pack(pady=15)
        ctk.CTkLabel(dialog, text="마우스: 좌클릭, 우클릭, Mouse4, Mouse5",
                     font=ctk.CTkFont(size=11), text_color="#888888").pack()

        dialog_active = [True]

        def update_slot_key(key_name):
            preset['slots'][slot_idx]['key'].set(key_name)
            if preset['_slot_widgets'] and slot_idx < len(preset['_slot_widgets']):
                preset['_slot_widgets'][slot_idx]['key_label'].configure(text=key_name.upper())

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

    # ===============================
    # 하위 호환성을 위한 래퍼 메서드들
    # ===============================

    def toggle_skill_auto_running(self):
        """하위 호환성 - 첫 번째 프리셋 토글"""
        self.toggle_skill_preset_running(0)

    def on_skill_auto_trigger_key(self, event):
        """하위 호환성 - 첫 번째 프리셋 트리거"""
        self.on_skill_preset_trigger_key(0, event)

    def change_skill_auto_trigger_key(self):
        """하위 호환성 - 첫 번째 프리셋 핫키 변경"""
        self.change_skill_preset_trigger_key(0)

    def change_skill_slot_key(self, slot_idx):
        """하위 호환성 - 첫 번째 프리셋 슬롯 키 변경"""
        self.change_skill_preset_slot_key(0, slot_idx)
