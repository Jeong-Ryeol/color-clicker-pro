# -*- coding: utf-8 -*-
"""
오버레이 창 기능
"""

import tkinter as tk
import win32gui
import win32con

from constants import COLORS


class OverlayMixin:
    """오버레이 기능 믹스인"""

    def init_overlay_vars(self):
        """오버레이 관련 변수 초기화"""
        import customtkinter as ctk

        self.overlay_window = None
        self.overlay_visible = ctk.BooleanVar(value=False)
        self.overlay_reposition_mode = False
        self.overlay_x = ctk.IntVar(value=100)
        self.overlay_y = ctk.IntVar(value=100)
        self.overlay_alpha = ctk.DoubleVar(value=0.85)
        self.overlay_labels = {}
        self.overlay_name_labels = {}
        self.overlay_bg_color = ctk.StringVar(value="#1a1a2e")

    def toggle_overlay(self):
        """오버레이 켜기/끄기"""
        if self.overlay_window is None:
            self.create_overlay_window()
            self.overlay_toggle_btn.configure(text="오버레이 끄기", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        else:
            self.destroy_overlay()
            self.overlay_toggle_btn.configure(text="오버레이 켜기", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])

    def create_overlay_window(self):
        """오버레이 창 생성"""
        bg_color = self.overlay_bg_color.get()

        self.overlay_window = tk.Toplevel(self)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', self.overlay_alpha.get())

        width = 180
        height = 175
        x = self.overlay_x.get()
        y = self.overlay_y.get()
        self.overlay_window.geometry(f'{width}x{height}+{x}+{y}')

        self.overlay_window.after(100, self.set_overlay_click_through, True)
        self.overlay_window.configure(bg=bg_color)

        main_frame = tk.Frame(self.overlay_window, bg=bg_color, padx=5, pady=5)
        main_frame.pack(fill='both', expand=True)

        title = tk.Label(main_frame, text="Wonryeol Helper", bg=bg_color, fg='#00aaff',
                         font=('맑은 고딕', 9, 'bold'))
        title.pack(pady=(0, 5))

        functions = [
            ("버리기", self.discard_trigger_key, self.discard_trigger_modifier, "discard_running"),
            ("먹기", self.consume_trigger_key, self.consume_trigger_modifier, "consume_running"),
            ("팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running"),
            ("꾸러기", self.inv_trigger_key, self.inv_trigger_modifier, "inv_running"),
            ("벨리알", self.trigger_key, self.trigger_modifier, "is_running"),
        ]

        self.overlay_labels = {}
        self.overlay_name_labels = {}

        for name, key_var, mod_var, attr in functions:
            row = tk.Frame(main_frame, bg=bg_color)
            row.pack(fill='x', pady=1)

            name_label = tk.Label(row, text=name, bg=bg_color, fg='#ffffff', width=5, anchor='w',
                                  font=('맑은 고딕', 9))
            name_label.pack(side='left')
            self.overlay_name_labels[attr] = name_label

            mod = mod_var.get()
            key = key_var.get().upper()
            hotkey_text = f"{mod}+{key}" if mod != "없음" else key
            tk.Label(row, text=hotkey_text, bg=bg_color, fg='#ff9900', width=9, anchor='center',
                     font=('맑은 고딕', 8)).pack(side='left')

            status_label = tk.Label(row, text="● OFF", bg=bg_color, fg='#666666', width=6, anchor='e',
                                    font=('맑은 고딕', 9))
            status_label.pack(side='right')
            self.overlay_labels[attr] = status_label

        separator = tk.Frame(main_frame, bg='#444444', height=1)
        separator.pack(fill='x', pady=3)

        boss_row = tk.Frame(main_frame, bg=bg_color)
        boss_row.pack(fill='x', pady=1)

        tk.Label(boss_row, text="🌍", bg=bg_color, fg='#ffffff',
                 font=('맑은 고딕', 9)).pack(side='left')

        self.world_boss_label = tk.Label(boss_row, text="로딩...", bg=bg_color, fg='#ff9900',
                                          font=('맑은 고딕', 9))
        self.world_boss_label.pack(side='left', padx=3)

        self.update_overlay()

    def destroy_overlay(self):
        """오버레이 창 제거"""
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
            self.overlay_window = None
            self.overlay_labels = {}
            self.overlay_name_labels = {}

    def update_overlay(self):
        """오버레이 상태 업데이트 (200ms 간격)"""
        if self.overlay_window is None:
            return

        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running
        }

        active_states = {
            "is_running": self.detection_active,
            "inv_running": self.inv_cleanup_active,
            "discard_running": self.discard_active,
            "sell_running": self.sell_active,
            "consume_running": self.consume_active
        }

        for attr, is_on in states.items():
            if attr in self.overlay_labels:
                label = self.overlay_labels[attr]
                if is_on:
                    label.configure(text="● ON", fg=COLORS["on_color"])
                else:
                    label.configure(text="● OFF", fg=COLORS["off_color"])

            if attr in self.overlay_name_labels:
                name_label = self.overlay_name_labels[attr]
                is_active = active_states.get(attr, False)
                if is_active:
                    name_label.configure(fg=COLORS["active_color"])
                else:
                    name_label.configure(fg='#ffffff')

        if self.overlay_window:
            self.overlay_window.after(200, self.update_overlay)

    def set_overlay_click_through(self, enable):
        """오버레이 클릭 통과 설정"""
        if self.overlay_window is None:
            return

        try:
            hwnd = self.overlay_window.winfo_id()
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            if enable:
                ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            else:
                ex_style &= ~win32con.WS_EX_TRANSPARENT

            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        except Exception as e:
            print(f"클릭 통과 설정 실패: {e}")
