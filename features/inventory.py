# -*- coding: utf-8 -*-
"""
신화장난꾸러기 기능 (인벤토리 정리)
"""

import threading
import time
from PIL import Image
import mss
import numpy as np
import pyautogui
import keyboard
import win32api

from constants import COLORS


class InventoryMixin:
    """신화장난꾸러기 기능 믹스인"""

    def init_inventory_vars(self):
        """인벤토리 관련 변수 초기화"""
        import customtkinter as ctk

        self.inv_keep_color = ctk.StringVar(value="#DFA8F0")
        self.inv_tolerance = ctk.IntVar(value=15)
        self.inv_x1 = ctk.IntVar(value=1690)
        self.inv_y1 = ctk.IntVar(value=961)
        self.inv_x2 = ctk.IntVar(value=2501)
        self.inv_y2 = ctk.IntVar(value=1287)
        self.inv_desc_x1 = ctk.IntVar(value=1144)
        self.inv_desc_y1 = ctk.IntVar(value=428)
        self.inv_desc_x2 = ctk.IntVar(value=1636)
        self.inv_desc_y2 = ctk.IntVar(value=1147)
        self.inv_cols = ctk.IntVar(value=11)
        self.inv_rows = ctk.IntVar(value=3)
        self.inv_running = False
        self.inv_cleanup_active = False
        self.inv_trigger_key = ctk.StringVar(value="f3")
        self.inv_trigger_modifier = ctk.StringVar(value="없음")
        self.inv_last_trigger_time = 0
        self.inv_delay = ctk.DoubleVar(value=0.01)
        self.inv_move_duration = ctk.DoubleVar(value=0.15)
        self.inv_panel_delay = ctk.DoubleVar(value=0.08)
        self.inv_space_delay = ctk.DoubleVar(value=0.05)
        self.inv_click_delay = ctk.DoubleVar(value=0.01)
        self.inv_area_overlay = None

    def toggle_inv_running(self):
        """인벤토리 정리 시작/중지"""
        self.inv_running = not self.inv_running
        if self.inv_running:
            self.inv_start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.inv_status_label.configure(text=f"🔴 [{self.inv_trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
        else:
            self.inv_start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.inv_status_label.configure(text="⏸️ 대기 중")
            self.inv_progress_label.configure(text="")
            self.update_idletasks()
        self.update_home_status_now()

    def get_inventory_positions(self):
        """인벤토리 셀 좌표 목록 반환 (뱀패턴: 123,654,789) - (x, y, col) 튜플"""
        positions = []
        x1, y1 = self.inv_x1.get(), self.inv_y1.get()
        x2, y2 = self.inv_x2.get(), self.inv_y2.get()
        cols = self.inv_cols.get()
        rows = self.inv_rows.get()

        width = x2 - x1
        height = y2 - y1
        cell_w = width / cols
        cell_h = height / rows

        for row in range(rows):
            if row % 2 == 0:
                # 짝수 줄: 왼쪽 → 오른쪽
                col_range = range(cols)
            else:
                # 홀수 줄: 오른쪽 → 왼쪽
                col_range = range(cols - 1, -1, -1)

            for col in col_range:
                x = int(x1 + col * cell_w + cell_w / 2)
                y = int(y1 + row * cell_h + cell_h / 2)
                positions.append((x, y, col))

        return positions

    def run_inventory_cleanup(self):
        """인벤토리 정리 - 1단계: 스캔+즐겨찾기, 2단계: 나머지 버리기"""
        import win32con

        def cleanup_loop():
            positions = self.get_inventory_positions()
            keep_color = self.inv_keep_color.get()
            tol = self.inv_tolerance.get()

            if not self.validate_hex(keep_color):
                self.after(0, lambda: self.inv_status_label.configure(text="❌ 유효하지 않은 색상"))
                return

            target_r = int(keep_color[1:3], 16)
            target_g = int(keep_color[3:5], 16)
            target_b = int(keep_color[5:7], 16)

            total = len(positions)
            cols = self.inv_cols.get()
            inv_x1 = self.inv_x1.get()
            inv_width = self.inv_x2.get() - inv_x1
            cell_w = inv_width / cols

            desc_x1 = self.inv_desc_x1.get()
            desc_y1 = self.inv_desc_y1.get()
            desc_x2 = self.inv_desc_x2.get()
            desc_y2 = self.inv_desc_y2.get()
            desc_width = desc_x2 - desc_x1
            desc_height = desc_y2 - desc_y1

            # 딜레이 값
            move_duration = self.inv_move_duration.get()
            panel_delay = self.inv_panel_delay.get()
            space_delay = self.inv_space_delay.get()
            click_delay = self.inv_click_delay.get()

            # 즐겨찾기된 슬롯 저장
            favorite_slots = set()

            # ========== 1단계: 스캔 + 즐겨찾기 ==========
            self.after(0, lambda: self.inv_status_label.configure(text="🔍 1단계: 스캔 중..."))

            # 첫 번째 슬롯에서 0.3초 호버링 (게임 초기 인식)
            if positions:
                first_x, first_y, first_col = positions[0]
                self.smooth_move_to(first_x, first_y, duration=move_duration)
                time.sleep(0.3)

            with mss.mss() as sct:
                for i, (x, y, col) in enumerate(positions):
                    if not self.inv_cleanup_active:
                        break

                    # 부드럽게 슬롯으로 이동
                    self.smooth_move_to(x, y, duration=move_duration)
                    time.sleep(panel_delay)

                    # 해당 슬롯의 설명 패널 X 오프셋 계산
                    x_offset = int(col * cell_w)
                    current_desc_x1 = desc_x1 + x_offset

                    try:
                        # 설명 패널 영역 캡처
                        monitor = {
                            "top": desc_y1,
                            "left": current_desc_x1,
                            "width": desc_width,
                            "height": desc_height
                        }
                        screenshot = sct.grab(monitor)

                        # numpy 초고속 벡터 스캔
                        img_array = np.frombuffer(screenshot.raw, dtype=np.uint8)
                        img_array = img_array.reshape((desc_height, desc_width, 4))

                        b_diff = np.abs(img_array[:, :, 0].astype(np.int16) - target_b)
                        g_diff = np.abs(img_array[:, :, 1].astype(np.int16) - target_g)
                        r_diff = np.abs(img_array[:, :, 2].astype(np.int16) - target_r)

                        found_keep_color = np.any((r_diff <= tol) & (g_diff <= tol) & (b_diff <= tol))

                        # 신화장난꾸러기 발견! 스페이스바 2번 (즐겨찾기)
                        if found_keep_color:
                            favorite_slots.add(i)
                            keyboard.press_and_release('space')
                            time.sleep(space_delay)
                            keyboard.press_and_release('space')
                            time.sleep(space_delay)
                            self.after(0, lambda idx=i: self.inv_progress_label.configure(
                                text=f"⭐ 즐겨찾기: 슬롯 {idx+1}"))

                    except Exception as e:
                        print(f"Scan error: {e}")

                    # 진행 상황 (3개마다)
                    if i % 3 == 0:
                        self.after(0, lambda idx=i, t=total, f=len(favorite_slots): self.inv_progress_label.configure(
                            text=f"스캔: {idx+1}/{t} (즐겨찾기: {f})"))

            if not self.inv_cleanup_active:
                self.after(0, lambda: self.inv_status_label.configure(text="⏹️ 중지됨"))
                self.inv_cleanup_active = False
                return

            # ========== 2단계: 즐겨찾기 안된 것들 빠르게 버리기 ==========
            self.after(0, lambda f=len(favorite_slots): self.inv_status_label.configure(
                text=f"🗑️ 2단계: 버리기... (보존: {f}개)"))

            discarded = 0
            for i, (x, y, col) in enumerate(positions):
                if not self.inv_cleanup_active:
                    break

                # 즐겨찾기된 슬롯은 스킵
                if i in favorite_slots:
                    continue

                # 빠르게 이동 (텔레포트)
                win32api.SetCursorPos((x, y))
                time.sleep(0.02)

                # Ctrl + 클릭으로 버리기
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                discarded += 1
                time.sleep(click_delay)

                if i % 5 == 0:
                    self.after(0, lambda d=discarded: self.inv_progress_label.configure(
                        text=f"버리는 중... ({d}개)"))

            self.inv_cleanup_active = False
            self.after(0, lambda: self.inv_status_label.configure(text="✅ 완료!"))
            self.after(0, lambda f=len(favorite_slots), d=discarded: self.inv_progress_label.configure(
                text=f"⭐ 보존: {f}개 | 🗑️ 버림: {d}개"))

        threading.Thread(target=cleanup_loop, daemon=True).start()

    def on_inv_trigger_key(self, event):
        """인벤토리 정리 트리거 키 핸들러 - 토글 방식"""
        if not self.inv_running:
            return

        if self.is_chatting():
            return

        if not self.check_modifier(self.inv_trigger_modifier.get()):
            return

        # 디바운스
        current_time = time.time()
        if current_time - self.inv_last_trigger_time < 0.3:
            return
        self.inv_last_trigger_time = current_time

        if self.inv_cleanup_active:
            self.inv_cleanup_active = False
            self.after(0, lambda: self.inv_status_label.configure(text="⏹️ 중지됨"))
        else:
            self.inv_cleanup_active = True
            self.run_inventory_cleanup()

    def change_inv_trigger_key(self):
        """인벤토리 핫키 변경"""
        import customtkinter as ctk
        import threading
        import time
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
                self.inv_trigger_key.set(event.name)
                if hasattr(self, 'inv_key_display'):
                    self.inv_key_display.configure(text=event.name.upper())
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
                    self.after(0, lambda: self.inv_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.inv_key_display.configure(text="MOUSE4") if hasattr(self, 'inv_key_display') else None)
                    # 버튼 떼어질 때까지 대기
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.inv_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.inv_key_display.configure(text="MOUSE5") if hasattr(self, 'inv_key_display') else None)
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

    def select_inv_area(self):
        """인벤토리 영역 드래그 선택"""
        import tkinter as tk

        self.inv_status_label.configure(text="🖱️ 드래그로 영역 선택...")

        overlay = tk.Toplevel(self)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline='red', width=3, fill='blue', stipple='gray50')

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                canvas.coords(rect_id, x1, y1, event.x, event.y)

        def on_release(event):
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.inv_x1.set(x1)
                self.inv_y1.set(y1)
                self.inv_x2.set(x2)
                self.inv_y2.set(y2)

                self.inv_status_label.configure(text=f"✅ 영역 설정 완료")
                overlay.destroy()
                self.show_inv_area_overlay()

        def on_escape(event):
            self.inv_status_label.configure(text="⏸️ 대기 중")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def show_inv_area_overlay(self):
        """인벤토리 영역 오버레이 토글"""
        import tkinter as tk

        if hasattr(self, 'inv_area_overlay') and self.inv_area_overlay:
            try:
                self.inv_area_overlay.destroy()
            except:
                pass
            self.inv_area_overlay = None
            return

        x1, y1 = self.inv_x1.get(), self.inv_y1.get()
        x2, y2 = self.inv_x2.get(), self.inv_y2.get()
        width, height = x2 - x1, y2 - y1

        if width <= 0 or height <= 0:
            return

        self.inv_area_overlay = tk.Toplevel(self)
        self.inv_area_overlay.overrideredirect(True)
        self.inv_area_overlay.attributes('-topmost', True)
        self.inv_area_overlay.attributes('-transparentcolor', 'white')
        self.inv_area_overlay.geometry(f'{width}x{height}+{x1}+{y1}')

        canvas = tk.Canvas(self.inv_area_overlay, width=width, height=height, bg='white', highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(2, 2, width-2, height-2, outline='#ff6600', width=3)
        canvas.bind('<Button-1>', lambda e: self.show_inv_area_overlay())

    def select_desc_area(self):
        """설명 패널 영역 드래그 선택"""
        import tkinter as tk

        self.inv_status_label.configure(text="🖱️ 설명 패널 영역 드래그...")

        overlay = tk.Toplevel(self)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline='green', width=3, fill='green', stipple='gray50')

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                canvas.coords(rect_id, x1, y1, event.x, event.y)

        def on_release(event):
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.inv_desc_x1.set(x1)
                self.inv_desc_y1.set(y1)
                self.inv_desc_x2.set(x2)
                self.inv_desc_y2.set(y2)

                self.inv_status_label.configure(text=f"✅ 설명 패널 영역 설정 완료")
                overlay.destroy()

        def on_escape(event):
            self.inv_status_label.configure(text="⏸️ 대기 중")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def update_inv_color_preview(self, event=None):
        """인벤토리 탭 색상 미리보기 업데이트"""
        try:
            color = self.inv_keep_color.get()
            if self.validate_hex(color):
                self.inv_color_preview.configure(fg_color=color)
        except:
            pass

    def inv_pick_color(self):
        """돋보기 보존 색상 추출기 시작"""
        self.picker_mode = True
        self.picker_target = "inv_keep"
        self.start_magnifier_picker("inv_keep")
