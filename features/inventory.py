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
        """인벤토리 슬롯 중앙 좌표 계산"""
        x1 = self.inv_x1.get()
        y1 = self.inv_y1.get()
        x2 = self.inv_x2.get()
        y2 = self.inv_y2.get()
        cols = self.inv_cols.get()
        rows = self.inv_rows.get()

        positions = []
        cell_w = (x2 - x1) / cols
        cell_h = (y2 - y1) / rows

        for row in range(rows):
            for col in range(cols):
                cx = int(x1 + cell_w * (col + 0.5))
                cy = int(y1 + cell_h * (row + 0.5))
                positions.append((cx, cy, col))

        return positions

    def run_inventory_cleanup(self):
        """인벤토리 정리 실행"""
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

            for idx, (sx, sy, col_idx) in enumerate(positions):
                if not self.inv_cleanup_active:
                    self.after(0, lambda: self.inv_status_label.configure(text="⏸️ 중지됨"))
                    return

                self.after(0, lambda i=idx: self.inv_progress_label.configure(text=f"스캔 중: {i+1}/{total}"))

                self.smooth_move_to(sx, sy, duration=self.inv_move_duration.get())
                time.sleep(self.inv_panel_delay.get())

                x_offset = int(col_idx * cell_w)
                scan_x1 = desc_x1 + x_offset
                scan_x2 = desc_x2 + x_offset

                try:
                    with mss.mss() as sct:
                        monitor = {"top": desc_y1, "left": scan_x1, "width": scan_x2 - scan_x1, "height": desc_y2 - desc_y1}
                        screenshot = np.array(sct.grab(monitor))

                    r_diff = np.abs(screenshot[:, :, 2].astype(np.int16) - target_r)
                    g_diff = np.abs(screenshot[:, :, 1].astype(np.int16) - target_g)
                    b_diff = np.abs(screenshot[:, :, 0].astype(np.int16) - target_b)
                    matches = (r_diff <= tol) & (g_diff <= tol) & (b_diff <= tol)

                    if np.any(matches):
                        keyboard.press_and_release('space')
                        time.sleep(self.inv_space_delay.get())

                except Exception as e:
                    print(f"Scan error: {e}")

                time.sleep(self.inv_click_delay.get())

            self.after(0, lambda: self.inv_status_label.configure(text="✅ 완료!"))
            self.after(0, lambda: self.inv_progress_label.configure(text=""))
            self.inv_cleanup_active = False

        threading.Thread(target=cleanup_loop, daemon=True).start()

    def on_inv_trigger_key(self, event):
        """인벤토리 정리 트리거 키 핸들러 - 토글 방식"""
        if not self.inv_running:
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
                self.inv_trigger_key.set(event.name)
                if hasattr(self, 'inv_key_display'):
                    self.inv_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def select_inv_area(self):
        """인벤토리 영역 선택"""
        import tkinter as tk
        from tkinter import messagebox

        messagebox.showinfo("영역 선택", "인벤토리 영역을 드래그하세요")

        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-alpha', 0.3)
        overlay.attributes('-topmost', True)
        overlay.configure(bg='gray')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill='both', expand=True)

        start_pos = [0, 0]
        rect = [None]

        def on_press(event):
            start_pos[0] = event.x
            start_pos[1] = event.y

        def on_drag(event):
            if rect[0]:
                canvas.delete(rect[0])
            rect[0] = canvas.create_rectangle(start_pos[0], start_pos[1], event.x, event.y,
                                               outline='red', width=3)

        def on_release(event):
            x1, y1 = min(start_pos[0], event.x), min(start_pos[1], event.y)
            x2, y2 = max(start_pos[0], event.x), max(start_pos[1], event.y)
            self.inv_x1.set(x1)
            self.inv_y1.set(y1)
            self.inv_x2.set(x2)
            self.inv_y2.set(y2)
            overlay.destroy()

        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<Escape>', lambda e: overlay.destroy())

    def show_inv_area_overlay(self):
        """인벤토리 영역 미리보기"""
        import tkinter as tk

        x1, y1 = self.inv_x1.get(), self.inv_y1.get()
        x2, y2 = self.inv_x2.get(), self.inv_y2.get()

        overlay = tk.Toplevel()
        overlay.geometry(f"{x2-x1}x{y2-y1}+{x1}+{y1}")
        overlay.overrideredirect(True)
        overlay.attributes('-alpha', 0.3)
        overlay.attributes('-topmost', True)
        overlay.configure(bg='blue')

        tk.Label(overlay, text="인벤토리 영역", bg='blue', fg='white').pack(expand=True)

        overlay.after(2000, overlay.destroy)

    def select_desc_area(self):
        """설명 패널 영역 선택"""
        import tkinter as tk
        from tkinter import messagebox

        messagebox.showinfo("영역 선택", "설명 패널 영역을 드래그하세요")

        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-alpha', 0.3)
        overlay.attributes('-topmost', True)
        overlay.configure(bg='gray')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill='both', expand=True)

        start_pos = [0, 0]
        rect = [None]

        def on_press(event):
            start_pos[0] = event.x
            start_pos[1] = event.y

        def on_drag(event):
            if rect[0]:
                canvas.delete(rect[0])
            rect[0] = canvas.create_rectangle(start_pos[0], start_pos[1], event.x, event.y,
                                               outline='yellow', width=3)

        def on_release(event):
            x1, y1 = min(start_pos[0], event.x), min(start_pos[1], event.y)
            x2, y2 = max(start_pos[0], event.x), max(start_pos[1], event.y)
            self.inv_desc_x1.set(x1)
            self.inv_desc_y1.set(y1)
            self.inv_desc_x2.set(x2)
            self.inv_desc_y2.set(y2)
            overlay.destroy()

        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<Escape>', lambda e: overlay.destroy())

    def inv_pick_color(self):
        """인벤토리 보존 색상 추출"""
        if hasattr(self, 'picker_status'):
            self.picker_status.configure(text="클릭으로 색상 추출")

        def on_click():
            x, y = win32api.GetCursorPos()
            import mss
            from PIL import Image
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": 1, "height": 1}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                r, g, b = img.getpixel((0, 0))
                hex_color = f"#{r:02X}{g:02X}{b:02X}"
                self.inv_keep_color.set(hex_color)
                if hasattr(self, 'inv_color_preview'):
                    self.inv_color_preview.configure(fg_color=hex_color)

        def wait_for_click():
            import win32con
            while True:
                if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000:
                    break
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    self.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_for_click, daemon=True).start()
