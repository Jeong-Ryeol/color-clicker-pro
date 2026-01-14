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
