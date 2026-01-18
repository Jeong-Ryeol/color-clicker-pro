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
        self.overlay_scale = ctk.DoubleVar(value=1.0)
        self.overlay_scale_w = ctk.DoubleVar(value=1.0)
        self.overlay_scale_h = ctk.DoubleVar(value=1.0)
        self.overlay_labels = {}
        self.overlay_name_labels = {}
        self.overlay_hotkey_labels = {}
        self.overlay_hotkey_vars = {}
        self.overlay_bg_color = ctk.StringVar(value="#1a1a2e")

    def update_overlay_alpha(self, value):
        """오버레이 투명도 실시간 업데이트"""
        alpha = float(value)
        self.alpha_label.configure(text=f"{int(alpha * 100)}%")
        if self.overlay_window:
            try:
                self.overlay_window.attributes('-alpha', alpha)
            except:
                pass

    def update_overlay_scale(self, value):
        """오버레이 크기 실시간 업데이트"""
        scale = float(value)
        self.scale_label.configure(text=f"{int(scale * 100)}%")
        if self.overlay_window:
            # 크기 변경은 오버레이 재생성 필요
            self.destroy_overlay()
            self.create_overlay_window()
            self.overlay_toggle_btn.configure(text="오버레이 끄기", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])

    def update_overlay_scale_w(self, value):
        """오버레이 가로 크기 실시간 업데이트"""
        scale = float(value)
        self.scale_w_label.configure(text=f"{int(scale * 100)}%")
        if self.overlay_window:
            self.destroy_overlay()
            self.create_overlay_window()
            self.overlay_toggle_btn.configure(text="오버레이 끄기", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])

    def update_overlay_scale_h(self, value):
        """오버레이 세로 크기 실시간 업데이트"""
        scale = float(value)
        self.scale_h_label.configure(text=f"{int(scale * 100)}%")
        if self.overlay_window:
            self.destroy_overlay()
            self.create_overlay_window()
            self.overlay_toggle_btn.configure(text="오버레이 끄기", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])

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

        scale = self.overlay_scale.get()
        scale_w = self.overlay_scale_w.get()
        scale_h = self.overlay_scale_h.get()
        width = int(250 * scale * scale_w)
        height = int(255 * scale * scale_h)
        x = self.overlay_x.get()
        y = self.overlay_y.get()
        self.overlay_window.geometry(f'{width}x{height}+{x}+{y}')

        # 폰트 크기 계산
        self.overlay_font_size = max(7, int(9 * scale))
        self.overlay_font_size_small = max(6, int(8 * scale))

        self.overlay_window.after(100, self.set_overlay_click_through, True)
        self.overlay_window.configure(bg=bg_color)

        main_frame = tk.Frame(self.overlay_window, bg=bg_color, padx=int(5*scale), pady=int(5*scale))
        main_frame.pack(fill='both', expand=True)

        title = tk.Label(main_frame, text="Wonryeol Helper", bg=bg_color, fg='#00aaff',
                         font=('맑은 고딕', self.overlay_font_size, 'bold'))
        title.pack(pady=(0, int(5*scale)))

        # 기본 기능 목록 (스킬 제외)
        functions = [
            ("버리기", self.discard_trigger_key, self.discard_trigger_modifier, "discard_running"),
            ("먹기", self.consume_trigger_key, self.consume_trigger_modifier, "consume_running"),
            ("사기", self.consume2_trigger_key, self.consume2_trigger_modifier, "consume2_running"),
            ("팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running"),
            ("꾸러기", self.inv_trigger_key, self.inv_trigger_modifier, "inv_running"),
            ("벨리알", self.trigger_key, self.trigger_modifier, "is_running"),
        ]

        # running=True인 스킬 프리셋만 동적으로 추가
        for i, preset in enumerate(self.skill_presets):
            if preset['running']:
                functions.append((
                    f"스킬{i+1}",
                    preset['trigger_key'],
                    preset['trigger_modifier'],
                    f"skill_preset_{i}_running"
                ))

        self.overlay_labels = {}
        self.overlay_name_labels = {}
        self.overlay_hotkey_labels = {}
        self.overlay_hotkey_vars = {}

        for name, key_var, mod_var, attr in functions:
            row = tk.Frame(main_frame, bg=bg_color)
            row.pack(fill='x', pady=1)

            name_label = tk.Label(row, text=name, bg=bg_color, fg='#ffffff', width=5, anchor='w',
                                  font=('맑은 고딕', self.overlay_font_size))
            name_label.pack(side='left')
            self.overlay_name_labels[attr] = name_label

            mod = mod_var.get()
            key = key_var.get().upper()
            hotkey_text = f"{mod}+{key}" if mod != "없음" else key
            hotkey_label = tk.Label(row, text=hotkey_text, bg=bg_color, fg='#ff9900', width=9, anchor='center',
                     font=('맑은 고딕', self.overlay_font_size_small))
            hotkey_label.pack(side='left')
            self.overlay_hotkey_labels[attr] = hotkey_label
            self.overlay_hotkey_vars[attr] = (key_var, mod_var)

            status_label = tk.Label(row, text="● OFF", bg=bg_color, fg='#666666', width=10, anchor='e',
                                    font=('맑은 고딕', self.overlay_font_size_small))
            status_label.pack(side='right')
            self.overlay_labels[attr] = status_label

        separator = tk.Frame(main_frame, bg='#444444', height=1)
        separator.pack(fill='x', pady=3)

        # 긴급정지 키
        keys_row = tk.Frame(main_frame, bg=bg_color)
        keys_row.pack(fill='x', pady=1)

        tk.Label(keys_row, text="긴급정지", bg=bg_color, fg='#aaaaaa', anchor='w',
                 font=('맑은 고딕', self.overlay_font_size_small)).pack(side='left')

        self.overlay_emergency_label = tk.Label(keys_row, text=self.emergency_stop_key.get().upper(),
                                                 bg=bg_color, fg='#ff4444', anchor='center',
                                                 font=('맑은 고딕', self.overlay_font_size_small))
        self.overlay_emergency_label.pack(side='left', padx=5)

        boss_row = tk.Frame(main_frame, bg=bg_color)
        boss_row.pack(fill='x', pady=(5, 1))

        tk.Label(boss_row, text="🌍", bg=bg_color, fg='#ffffff',
                 font=('맑은 고딕', self.overlay_font_size)).pack(side='left')

        self.world_boss_label = tk.Label(boss_row, text="로딩...", bg=bg_color, fg='#ff9900',
                                          font=('맑은 고딕', self.overlay_font_size))
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
            self.overlay_hotkey_labels = {}
            self.overlay_hotkey_vars = {}

    def update_overlay(self):
        """오버레이 상태 업데이트 (200ms 간격) - 5개 스킬 프리셋 지원"""
        if self.overlay_window is None:
            return

        # 기본 기능 상태
        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running,
            "consume2_running": self.consume2_running,
        }

        active_states = {
            "is_running": self.detection_active,
            "inv_running": self.inv_cleanup_active,
            "discard_running": self.discard_active,
            "sell_running": self.sell_active,
            "consume_running": self.consume_active,
            "consume2_running": self.consume2_active,
        }

        paused_states = {
            "consume_running": getattr(self, 'consume_paused', False),
            "consume2_running": getattr(self, 'consume2_paused', False),
        }

        # 스킬 프리셋별 상태 추가
        for i, preset in enumerate(self.skill_presets):
            attr = f"skill_preset_{i}_running"
            states[attr] = preset['running']
            active_states[attr] = preset['active']
            paused_states[attr] = preset['paused']

        for attr, is_on in states.items():
            is_active = active_states.get(attr, False)
            is_paused = paused_states.get(attr, False)

            if attr in self.overlay_labels:
                label = self.overlay_labels[attr]
                if is_active and is_paused:
                    label.configure(text="● Pause", fg="#ff9900")
                elif is_active:
                    label.configure(text="● Working", fg="#ff4444")
                elif is_on:
                    label.configure(text="● ON", fg=COLORS["on_color"])
                else:
                    label.configure(text="● OFF", fg=COLORS["off_color"])

            if attr in self.overlay_name_labels:
                name_label = self.overlay_name_labels[attr]
                if is_active:
                    name_label.configure(fg=COLORS["active_color"])
                else:
                    name_label.configure(fg='#ffffff')

            # 핫키 텍스트 업데이트
            if attr in self.overlay_hotkey_labels and attr in self.overlay_hotkey_vars:
                hotkey_label = self.overlay_hotkey_labels[attr]
                key_var, mod_var = self.overlay_hotkey_vars[attr]
                mod = mod_var.get()
                key = key_var.get().upper()
                hotkey_text = f"{mod}+{key}" if mod != "없음" else key
                hotkey_label.configure(text=hotkey_text)

        # 긴급정지 키 업데이트
        if hasattr(self, 'overlay_emergency_label') and self.overlay_emergency_label:
            try:
                self.overlay_emergency_label.configure(text=self.emergency_stop_key.get().upper())
            except:
                pass

        # 월드보스는 app.py의 update_world_boss_timer에서 직접 업데이트함

        if self.overlay_window:
            self.overlay_window.after(200, self.update_overlay)

    def refresh_overlay_for_skill_presets(self):
        """스킬 프리셋 ON/OFF 시 오버레이 재생성"""
        if self.overlay_window is not None:
            self.destroy_overlay()
            self.create_overlay_window()
            if hasattr(self, 'overlay_toggle_btn'):
                self.overlay_toggle_btn.configure(
                    text="오버레이 끄기",
                    fg_color=COLORS["danger"],
                    hover_color=COLORS["danger_hover"]
                )

    def set_overlay_click_through(self, enable=True):
        """오버레이 클릭 통과 설정 (Windows only)"""
        if self.overlay_window is None:
            return
        try:
            # 윈도우 핸들 가져오기
            hwnd = int(self.overlay_window.winfo_id())
            # 부모 윈도우 핸들 (실제 Toplevel 윈도우)
            hwnd = win32gui.GetParent(hwnd)

            # 현재 확장 스타일 가져오기
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            if enable:
                # 클릭 통과 활성화: WS_EX_LAYERED | WS_EX_TRANSPARENT
                ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            else:
                # 클릭 통과 비활성화
                ex_style &= ~win32con.WS_EX_TRANSPARENT

            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        except Exception as e:
            print(f"클릭 통과 설정 실패: {e}")

    def start_overlay_reposition(self):
        """오버레이 재배치 모드 시작"""
        from tkinter import messagebox

        if self.overlay_window is None:
            messagebox.showinfo("알림", "먼저 오버레이를 켜주세요!")
            return

        self.overlay_reposition_mode = True
        self.overlay_repos_btn.configure(text="Enter로 고정", fg_color="#ffc107", hover_color="#e0a800")

        # 클릭 통과 해제 (드래그 가능하게)
        self.set_overlay_click_through(False)

        # 드래그 이벤트 바인딩
        self.overlay_window.bind('<Button-1>', self.overlay_start_drag)
        self.overlay_window.bind('<B1-Motion>', self.overlay_do_drag)
        self.overlay_window.bind('<Return>', self.finish_overlay_reposition)
        self.overlay_window.bind('<Escape>', self.finish_overlay_reposition)

        # 포커스 설정
        self.overlay_window.focus_set()

    def overlay_start_drag(self, event):
        """드래그 시작"""
        if self.overlay_reposition_mode:
            self._drag_x = event.x
            self._drag_y = event.y

    def overlay_do_drag(self, event):
        """드래그 중"""
        if self.overlay_reposition_mode and self.overlay_window:
            x = self.overlay_window.winfo_x() + event.x - self._drag_x
            y = self.overlay_window.winfo_y() + event.y - self._drag_y
            self.overlay_window.geometry(f'+{x}+{y}')

    def finish_overlay_reposition(self, event=None):
        """오버레이 재배치 완료"""
        self.overlay_reposition_mode = False
        self.overlay_repos_btn.configure(text="재배치", fg_color="#6c757d", hover_color="#5a6268")

        # 이벤트 바인딩 해제
        if self.overlay_window:
            self.overlay_window.unbind('<Button-1>')
            self.overlay_window.unbind('<B1-Motion>')
            self.overlay_window.unbind('<Return>')
            self.overlay_window.unbind('<Escape>')

            # 현재 위치 저장
            self.overlay_x.set(self.overlay_window.winfo_x())
            self.overlay_y.set(self.overlay_window.winfo_y())

            # 클릭 통과 다시 활성화
            self.set_overlay_click_through(True)
