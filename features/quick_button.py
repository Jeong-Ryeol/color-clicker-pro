# -*- coding: utf-8 -*-
"""
빠른 버튼 기능 - 인벤토리 열면 버튼 표시
"""

import tkinter as tk
import threading
import time
import os
import json
import mss
from PIL import Image
import numpy as np


class QuickButtonMixin:
    """빠른 버튼 기능 믹스인"""

    def init_quick_button_vars(self):
        """빠른 버튼 관련 변수 초기화"""
        import customtkinter as ctk

        # 설정 파일 경로
        self.quick_btn_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "quick_btn_config.json"
        )

        # sell.png 템플릿 경로
        self.sell_template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "sell.png"
        )
        self.sell_template = None
        self._load_sell_template()

        # 버리기 빠른 버튼
        self.quick_btn_window = None
        self.quick_btn_enabled = ctk.BooleanVar(value=True)
        self.quick_btn_x = ctk.IntVar(value=1812)
        self.quick_btn_y = ctk.IntVar(value=898)

        # 팔기 빠른 버튼
        self.quick_sell_window = None
        self.quick_sell_x = ctk.IntVar(value=1865)
        self.quick_sell_y = ctk.IntVar(value=899)

        # 꾸러미 빠른 버튼
        self.quick_bundle_window = None
        self.quick_bundle_x = ctk.IntVar(value=1759)
        self.quick_bundle_y = ctk.IntVar(value=898)

        # 인식 좌표/색깔 설정 (사용자 설정 가능)
        self.detect_pos1_x = ctk.IntVar(value=1738)
        self.detect_pos1_y = ctk.IntVar(value=267)
        self.detect_color1 = ctk.StringVar(value="#E4DBCA")
        self.detect_pos2_x = ctk.IntVar(value=1859)
        self.detect_pos2_y = ctk.IntVar(value=280)
        self.detect_color2 = ctk.StringVar(value="#E4DBCA")

        self.quick_btn_monitoring = False
        self.inventory_open = False
        self.sell_ui_open = False
        self.bundle_ui_open = False

        # 저장된 위치 불러오기
        self._load_quick_btn_config()

    def _load_quick_btn_config(self):
        """저장된 버튼 위치 및 인식 설정 불러오기"""
        try:
            if os.path.exists(self.quick_btn_config_path):
                with open(self.quick_btn_config_path, 'r') as f:
                    config = json.load(f)
                    # 버튼 위치
                    if 'discard_x' in config:
                        self.quick_btn_x.set(config['discard_x'])
                    if 'discard_y' in config:
                        self.quick_btn_y.set(config['discard_y'])
                    if 'sell_x' in config:
                        self.quick_sell_x.set(config['sell_x'])
                    if 'sell_y' in config:
                        self.quick_sell_y.set(config['sell_y'])
                    if 'bundle_x' in config:
                        self.quick_bundle_x.set(config['bundle_x'])
                    if 'bundle_y' in config:
                        self.quick_bundle_y.set(config['bundle_y'])
                    # 인식 설정
                    if 'detect_pos1_x' in config:
                        self.detect_pos1_x.set(config['detect_pos1_x'])
                    if 'detect_pos1_y' in config:
                        self.detect_pos1_y.set(config['detect_pos1_y'])
                    if 'detect_color1' in config:
                        self.detect_color1.set(config['detect_color1'])
                    elif 'detect_color' in config:  # 이전 버전 호환
                        self.detect_color1.set(config['detect_color'])
                    if 'detect_pos2_x' in config:
                        self.detect_pos2_x.set(config['detect_pos2_x'])
                    if 'detect_pos2_y' in config:
                        self.detect_pos2_y.set(config['detect_pos2_y'])
                    if 'detect_color2' in config:
                        self.detect_color2.set(config['detect_color2'])
                    elif 'detect_color' in config:  # 이전 버전 호환
                        self.detect_color2.set(config['detect_color'])
                    print(f"[QuickBtn] 설정 불러옴")
        except Exception as e:
            print(f"[QuickBtn] 설정 로드 실패: {e}")

    def _save_quick_btn_config(self):
        """버튼 위치 및 인식 설정 저장"""
        try:
            config = {
                # 버튼 위치
                'discard_x': self.quick_btn_x.get(),
                'discard_y': self.quick_btn_y.get(),
                'sell_x': self.quick_sell_x.get(),
                'sell_y': self.quick_sell_y.get(),
                'bundle_x': self.quick_bundle_x.get(),
                'bundle_y': self.quick_bundle_y.get(),
                # 인식 설정
                'detect_pos1_x': self.detect_pos1_x.get(),
                'detect_pos1_y': self.detect_pos1_y.get(),
                'detect_color1': self.detect_color1.get(),
                'detect_pos2_x': self.detect_pos2_x.get(),
                'detect_pos2_y': self.detect_pos2_y.get(),
                'detect_color2': self.detect_color2.get()
            }
            with open(self.quick_btn_config_path, 'w') as f:
                json.dump(config, f)
            print(f"[QuickBtn] 설정 저장됨")
        except Exception as e:
            print(f"[QuickBtn] 설정 저장 실패: {e}")

    def _load_door_template(self):
        """door.png 템플릿 이미지 로드"""
        try:
            img = Image.open(self.door_image_path).convert('RGB')
            self.door_template = np.array(img)
        except:
            self.door_template = None

    def _load_sell_template(self):
        """sell.png 템플릿 이미지 로드"""
        try:
            if os.path.exists(self.sell_template_path):
                img = Image.open(self.sell_template_path).convert('RGB')
                self.sell_template = np.array(img)
                print(f"[QuickBtn] sell.png 로드 완료: {self.sell_template.shape}")
            else:
                print(f"[QuickBtn] sell.png 없음: {self.sell_template_path}")
                self.sell_template = None
        except Exception as e:
            print(f"[QuickBtn] sell.png 로드 실패: {e}")
            self.sell_template = None

    def match_template(self, screenshot_np, template_np, threshold=0.8):
        """간단한 템플릿 매칭 (numpy only)"""
        if template_np is None:
            return False, None

        sh, sw = screenshot_np.shape[:2]
        th, tw = template_np.shape[:2]

        if sh < th or sw < tw:
            return False, None

        # 슬라이딩 윈도우로 검색 (빠른 검색을 위해 stride 사용)
        stride = 4
        best_match = 0
        best_pos = None

        for y in range(0, sh - th, stride):
            for x in range(0, sw - tw, stride):
                region = screenshot_np[y:y+th, x:x+tw]
                # 간단한 유사도 계산 (평균 절대 차이)
                diff = np.abs(region.astype(np.float32) - template_np.astype(np.float32))
                similarity = 1 - (np.mean(diff) / 255)

                if similarity > best_match:
                    best_match = similarity
                    best_pos = (x, y)

        if best_match > 0.5:  # 디버그: 50% 이상일 때만 출력
            print(f"[QuickBtn] 템플릿 유사도: {best_match:.2%}")
        return best_match >= threshold, best_pos

    def setup_quick_button_hotkeys(self):
        """인벤토리 이미지 감지 모니터링 시작"""
        if not self.quick_btn_monitoring:
            self.quick_btn_monitoring = True
            threading.Thread(target=self.monitor_inventory_image, daemon=True).start()

    def monitor_inventory_image(self):
        """인벤토리/팔기 감지 루프 (mss 사용)"""
        tolerance = 0  # 정확히 일치할 때만 감지

        print(f"[QuickBtn] 인식 설정: 위치1({self.detect_pos1_x.get()}, {self.detect_pos1_y.get()}) 색깔1={self.detect_color1.get()}, 위치2({self.detect_pos2_x.get()}, {self.detect_pos2_y.get()}) 색깔2={self.detect_color2.get()}")

        with mss.mss() as sct:
            while self.quick_btn_monitoring:
                try:
                    if not self.quick_btn_enabled.get():
                        if self.inventory_open:
                            self.after(0, self.hide_quick_button)
                        if self.sell_ui_open:
                            self.after(0, self.hide_quick_sell)
                        if self.bundle_ui_open:
                            self.after(0, self.hide_quick_bundle)
                        time.sleep(0.1)
                        continue

                    # === 인벤토리 감지 (버리기/팔기/꾸러미 ON일 때) ===
                    found_discard = False
                    bundle_on = getattr(self, 'inv_running', False)  # 신화장난꾸러미
                    if self.discard_running or self.sell_running or bundle_on:
                        # 위치 1 설정값
                        pos1_x = self.detect_pos1_x.get()
                        pos1_y = self.detect_pos1_y.get()
                        hex_color1 = self.detect_color1.get().lstrip('#')
                        target1_r = int(hex_color1[0:2], 16)
                        target1_g = int(hex_color1[2:4], 16)
                        target1_b = int(hex_color1[4:6], 16)

                        # 위치 2 설정값
                        pos2_x = self.detect_pos2_x.get()
                        pos2_y = self.detect_pos2_y.get()
                        hex_color2 = self.detect_color2.get().lstrip('#')
                        target2_r = int(hex_color2[0:2], 16)
                        target2_g = int(hex_color2[2:4], 16)
                        target2_b = int(hex_color2[4:6], 16)

                        # 위치 1 확인
                        monitor1 = {"top": pos1_y, "left": pos1_x, "width": 1, "height": 1}
                        screenshot1 = sct.grab(monitor1)
                        img1 = Image.frombytes("RGB", screenshot1.size, screenshot1.bgra, "raw", "BGRX")
                        color1 = img1.getpixel((0, 0))
                        found1 = (abs(color1[0] - target1_r) <= tolerance and
                                 abs(color1[1] - target1_g) <= tolerance and
                                 abs(color1[2] - target1_b) <= tolerance)

                        # 위치 2 확인
                        monitor2 = {"top": pos2_y, "left": pos2_x, "width": 1, "height": 1}
                        screenshot2 = sct.grab(monitor2)
                        img2 = Image.frombytes("RGB", screenshot2.size, screenshot2.bgra, "raw", "BGRX")
                        color2 = img2.getpixel((0, 0))
                        found2 = (abs(color2[0] - target2_r) <= tolerance and
                                 abs(color2[1] - target2_g) <= tolerance and
                                 abs(color2[2] - target2_b) <= tolerance)

                        found_discard = found1 or found2

                    # === 버리기 버튼 표시 ===
                    if self.discard_running:
                        if found_discard and not self.inventory_open:
                            self.inventory_open = True
                            self.after(0, self.show_quick_button)
                        elif not found_discard and self.inventory_open:
                            self.after(0, self.hide_quick_button)
                    else:
                        if self.inventory_open:
                            self.after(0, self.hide_quick_button)

                    # === 팔기 버튼 표시 ===
                    if self.sell_running:
                        if found_discard and not self.sell_ui_open:
                            self.sell_ui_open = True
                            self.after(0, self.show_quick_sell)
                        elif not found_discard and self.sell_ui_open:
                            self.after(0, self.hide_quick_sell)
                    else:
                        if self.sell_ui_open:
                            self.after(0, self.hide_quick_sell)

                    # === 꾸러미 버튼 표시 ===
                    if bundle_on:
                        if found_discard and not self.bundle_ui_open:
                            self.bundle_ui_open = True
                            self.after(0, self.show_quick_bundle)
                        elif not found_discard and self.bundle_ui_open:
                            self.after(0, self.hide_quick_bundle)
                    else:
                        if self.bundle_ui_open:
                            self.after(0, self.hide_quick_bundle)

                except Exception as e:
                    pass

                time.sleep(0.03)  # 0.03초 간격 (~33fps)

    def color_changed(self, color1, color2, threshold):
        """두 색상이 임계값 이상 다른지 확인"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2
        return (abs(r1 - r2) > threshold or
                abs(g1 - g2) > threshold or
                abs(b1 - b2) > threshold)

    def show_quick_button(self):
        """빠른 버튼 표시 - 둥근 게임 스타일"""
        if self.quick_btn_window:
            return

        x = self.quick_btn_x.get()
        y = self.quick_btn_y.get()
        size = 50  # 버튼 크기

        self.quick_btn_window = tk.Toplevel(self)
        self.quick_btn_window.overrideredirect(True)
        self.quick_btn_window.attributes('-topmost', True)
        self.quick_btn_window.attributes('-transparentcolor', 'magenta')
        self.quick_btn_window.geometry(f'{size}x{size}+{x}+{y}')

        # Canvas로 둥근 버튼 만들기
        canvas = tk.Canvas(
            self.quick_btn_window,
            width=size,
            height=size,
            bg='magenta',
            highlightthickness=0
        )
        canvas.pack()

        # 바깥 테두리 (어두운 갈색)
        canvas.create_oval(2, 2, size-2, size-2, fill='#2a2015', outline='#1a1510', width=2)
        # 안쪽 원 (붉은 갈색 그라데이션 효과)
        canvas.create_oval(6, 6, size-6, size-6, fill='#4a2a1a', outline='#3a1a0a', width=1)
        # 중앙 아이콘 영역
        canvas.create_oval(10, 10, size-10, size-10, fill='#5a3020', outline='#6a4030', width=1)

        # 버리기 아이콘 (X 표시)
        center = size // 2
        canvas.create_line(center-8, center-8, center+8, center+8, fill='#c4a060', width=3)
        canvas.create_line(center-8, center+8, center+8, center-8, fill='#c4a060', width=3)

        # 클릭 이벤트
        canvas.bind('<Button-1>', lambda e: self.on_quick_discard_click())
        canvas.bind('<Enter>', lambda e: canvas.config(cursor='hand2'))

        # 드래그로 위치 조정 가능
        canvas.bind('<Button-3>', self.start_quick_btn_drag)
        canvas.bind('<B3-Motion>', self.do_quick_btn_drag)

    def hide_quick_button(self):
        """버리기 버튼 숨기기"""
        self.inventory_open = False

        if self.quick_btn_window:
            try:
                self.quick_btn_window.destroy()
            except:
                pass
            self.quick_btn_window = None

    def show_quick_sell(self):
        """팔기 버튼 표시 - 둥근 게임 스타일"""
        if self.quick_sell_window:
            return

        x = self.quick_sell_x.get()
        y = self.quick_sell_y.get()
        size = 50  # 버리기와 같은 크기

        self.quick_sell_window = tk.Toplevel(self)
        self.quick_sell_window.overrideredirect(True)
        self.quick_sell_window.attributes('-topmost', True)
        self.quick_sell_window.attributes('-transparentcolor', 'magenta')
        self.quick_sell_window.geometry(f'{size}x{size}+{x}+{y}')

        canvas = tk.Canvas(
            self.quick_sell_window,
            width=size,
            height=size,
            bg='magenta',
            highlightthickness=0
        )
        canvas.pack()

        # 바깥 테두리 (어두운 갈색)
        canvas.create_oval(2, 2, size-2, size-2, fill='#2a2015', outline='#1a1510', width=2)
        # 안쪽 원 (금색 계열)
        canvas.create_oval(6, 6, size-6, size-6, fill='#3a3520', outline='#2a2510', width=1)
        # 중앙 아이콘 영역
        canvas.create_oval(10, 10, size-10, size-10, fill='#4a4530', outline='#5a5540', width=1)

        # 팔기 아이콘 ($ 표시)
        center = size // 2
        canvas.create_text(center, center, text="$", fill='#ffd700', font=('Arial', 14, 'bold'))

        # 클릭 이벤트
        canvas.bind('<Button-1>', lambda e: self.on_quick_sell_click())
        canvas.bind('<Enter>', lambda e: canvas.config(cursor='hand2'))

        # 드래그로 위치 조정 가능
        canvas.bind('<Button-3>', self.start_quick_sell_drag)
        canvas.bind('<B3-Motion>', self.do_quick_sell_drag)

    def hide_quick_sell(self):
        """팔기 버튼 숨기기"""
        self.sell_ui_open = False

        if self.quick_sell_window:
            try:
                self.quick_sell_window.destroy()
            except:
                pass
            self.quick_sell_window = None

    def on_quick_sell_click(self):
        """팔기 버튼 클릭 - 핫키와 동일한 토글 방식"""
        self.hide_quick_sell()

        if self.sell_active:
            # 실행 중이면 중지
            self.sell_active = False
            self.after(0, lambda: self.sell_status_label.configure(text="⏹️ 중지됨"))
        else:
            # 실행 중 아니면 시작
            self.sell_active = True
            threading.Thread(target=self.run_sell_loop, daemon=True).start()

    def start_quick_sell_drag(self, event):
        """팔기 버튼 우클릭 드래그 시작"""
        self._quick_sell_drag_x = event.x
        self._quick_sell_drag_y = event.y

    def do_quick_sell_drag(self, event):
        """팔기 버튼 우클릭 드래그 중"""
        if self.quick_sell_window:
            x = self.quick_sell_window.winfo_x() + event.x - self._quick_sell_drag_x
            y = self.quick_sell_window.winfo_y() + event.y - self._quick_sell_drag_y
            self.quick_sell_window.geometry(f'+{x}+{y}')
            self.quick_sell_x.set(x)
            self.quick_sell_y.set(y)
            self._save_quick_btn_config()  # 위치 저장

    def show_quick_bundle(self):
        """꾸러미 버튼 표시 - 둥근 게임 스타일"""
        if self.quick_bundle_window:
            return

        x = self.quick_bundle_x.get()
        y = self.quick_bundle_y.get()
        size = 50  # 버리기와 같은 크기

        self.quick_bundle_window = tk.Toplevel(self)
        self.quick_bundle_window.overrideredirect(True)
        self.quick_bundle_window.attributes('-topmost', True)
        self.quick_bundle_window.attributes('-transparentcolor', 'magenta')
        self.quick_bundle_window.geometry(f'{size}x{size}+{x}+{y}')

        canvas = tk.Canvas(
            self.quick_bundle_window,
            width=size,
            height=size,
            bg='magenta',
            highlightthickness=0
        )
        canvas.pack()

        # 바깥 테두리 (어두운 갈색)
        canvas.create_oval(2, 2, size-2, size-2, fill='#2a2015', outline='#1a1510', width=2)
        # 안쪽 원 (보라색 계열)
        canvas.create_oval(6, 6, size-6, size-6, fill='#352040', outline='#251030', width=1)
        # 중앙 아이콘 영역
        canvas.create_oval(10, 10, size-10, size-10, fill='#453050', outline='#554060', width=1)

        # 꾸러미 아이콘 (K 표시)
        center = size // 2
        canvas.create_text(center, center, text="K", fill='#ffd700', font=('Arial', 16, 'bold'))

        # 클릭 이벤트
        canvas.bind('<Button-1>', lambda e: self.on_quick_bundle_click())
        canvas.bind('<Enter>', lambda e: canvas.config(cursor='hand2'))

        # 드래그로 위치 조정 가능
        canvas.bind('<Button-3>', self.start_quick_bundle_drag)
        canvas.bind('<B3-Motion>', self.do_quick_bundle_drag)

    def hide_quick_bundle(self):
        """꾸러미 버튼 숨기기"""
        self.bundle_ui_open = False

        if self.quick_bundle_window:
            try:
                self.quick_bundle_window.destroy()
            except:
                pass
            self.quick_bundle_window = None

    def on_quick_bundle_click(self):
        """꾸러미 버튼 클릭 - 핫키와 동일한 토글 방식"""
        self.hide_quick_bundle()

        if self.inv_cleanup_active:
            # 실행 중이면 중지
            self.inv_cleanup_active = False
            self.after(0, lambda: self.inv_status_label.configure(text="⏹️ 중지됨"))
        else:
            # 실행 중 아니면 시작
            self.inv_cleanup_active = True
            self.run_inventory_cleanup()

    def start_quick_bundle_drag(self, event):
        """꾸러미 버튼 우클릭 드래그 시작"""
        self._quick_bundle_drag_x = event.x
        self._quick_bundle_drag_y = event.y

    def do_quick_bundle_drag(self, event):
        """꾸러미 버튼 우클릭 드래그 중"""
        if self.quick_bundle_window:
            x = self.quick_bundle_window.winfo_x() + event.x - self._quick_bundle_drag_x
            y = self.quick_bundle_window.winfo_y() + event.y - self._quick_bundle_drag_y
            self.quick_bundle_window.geometry(f'+{x}+{y}')
            self.quick_bundle_x.set(x)
            self.quick_bundle_y.set(y)
            self._save_quick_btn_config()  # 위치 저장

    def on_quick_discard_click(self):
        """버리기 버튼 클릭 - 핫키와 동일한 토글 방식"""
        self.hide_quick_button()

        if self.discard_active:
            # 실행 중이면 중지
            self.discard_active = False
            self.after(0, lambda: self.discard_status_label.configure(text="⏹️ 중지됨"))
        else:
            # 실행 중 아니면 시작
            self.discard_active = True
            threading.Thread(target=self.run_discard_loop, daemon=True).start()

    def start_quick_btn_drag(self, event):
        """우클릭 드래그 시작"""
        self._quick_drag_x = event.x
        self._quick_drag_y = event.y

    def do_quick_btn_drag(self, event):
        """우클릭 드래그 중"""
        if self.quick_btn_window:
            x = self.quick_btn_window.winfo_x() + event.x - self._quick_drag_x
            y = self.quick_btn_window.winfo_y() + event.y - self._quick_drag_y
            self.quick_btn_window.geometry(f'+{x}+{y}')
            self.quick_btn_x.set(x)
            self.quick_btn_y.set(y)
            self._save_quick_btn_config()  # 위치 저장

    def open_detect_settings(self):
        """인식 설정 창 열기"""
        import customtkinter as ctk

        # 이미 열려있으면 포커스
        if hasattr(self, '_detect_settings_window') and self._detect_settings_window:
            try:
                self._detect_settings_window.focus()
                return
            except:
                pass

        win = ctk.CTkToplevel(self)
        win.title("빠른버튼 인식 설정")
        win.geometry("350x350")
        win.attributes('-topmost', True)
        win.resizable(False, False)
        self._detect_settings_window = win

        # 타이틀
        ctk.CTkLabel(win, text="인벤토리 인식 설정",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        ctk.CTkLabel(win, text="인벤토리를 열었을 때 감지할 좌표와 색깔을 설정합니다.\n돋보기로 인벤토리 UI의 고정된 부분을 선택하세요.",
                    font=ctk.CTkFont(size=11), text_color="gray").pack(pady=5)

        # 위치 1
        pos1_frame = ctk.CTkFrame(win)
        pos1_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(pos1_frame, text="위치 1:", width=50).pack(side="left")
        self._detect_color1_preview = ctk.CTkLabel(pos1_frame, text="  ", width=20,
                                                   fg_color=self.detect_color1.get())
        self._detect_color1_preview.pack(side="left", padx=2)
        self._detect_pos1_label = ctk.CTkLabel(pos1_frame,
            text=f"({self.detect_pos1_x.get()}, {self.detect_pos1_y.get()}) {self.detect_color1.get()}",
            font=ctk.CTkFont(family="Consolas", size=11))
        self._detect_pos1_label.pack(side="left", padx=5)
        ctk.CTkButton(pos1_frame, text="🔍 설정", width=70,
                     command=lambda: self.start_detect_picker(1)).pack(side="right")

        # 위치 2
        pos2_frame = ctk.CTkFrame(win)
        pos2_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(pos2_frame, text="위치 2:", width=50).pack(side="left")
        self._detect_color2_preview = ctk.CTkLabel(pos2_frame, text="  ", width=20,
                                                   fg_color=self.detect_color2.get())
        self._detect_color2_preview.pack(side="left", padx=2)
        self._detect_pos2_label = ctk.CTkLabel(pos2_frame,
            text=f"({self.detect_pos2_x.get()}, {self.detect_pos2_y.get()}) {self.detect_color2.get()}",
            font=ctk.CTkFont(family="Consolas", size=11))
        self._detect_pos2_label.pack(side="left", padx=5)
        ctk.CTkButton(pos2_frame, text="🔍 설정", width=70,
                     command=lambda: self.start_detect_picker(2)).pack(side="right")

        # 상태
        self._detect_status = ctk.CTkLabel(win, text="", font=ctk.CTkFont(size=11))
        self._detect_status.pack(pady=10)

        # 설명
        ctk.CTkLabel(win, text="두 위치 중 하나라도 색깔이 일치하면 인벤토리가\n열린 것으로 감지합니다.",
                    font=ctk.CTkFont(size=10), text_color="gray").pack(pady=5)

        # 저장 버튼
        ctk.CTkButton(win, text="저장", width=100, fg_color="#28a745",
                     command=lambda: self._save_detect_and_close(win)).pack(pady=10)

        def on_close():
            self._detect_settings_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)

    def _save_detect_and_close(self, win):
        """인식 설정 저장 후 창 닫기"""
        self._save_quick_btn_config()
        self._detect_settings_window = None
        win.destroy()

    def start_detect_picker(self, position_num):
        """인식 위치 픽커 시작 (돋보기)"""
        import pyautogui
        from PIL import ImageGrab, ImageTk
        import win32api

        self._detect_picker_mode = True
        self._detect_picker_pos = position_num

        # 돋보기 창 생성
        mag_window = tk.Toplevel(self)
        mag_window.title(f"위치 {position_num} 선택 - 화면 클릭 (ESC 취소)")
        mag_window.attributes('-topmost', True)
        mag_window.geometry("280x280")
        mag_window.resizable(False, False)

        # 확대 영역
        capture_size = 15
        magnify = 12
        display_size = capture_size * magnify

        canvas = tk.Canvas(mag_window, width=display_size, height=display_size,
                          bg='black', highlightthickness=2, highlightbackground='#00aaff')
        canvas.pack(pady=10)

        # 색상/좌표 정보
        info_frame = tk.Frame(mag_window, bg='#2b2b2b')
        info_frame.pack(fill='x', padx=10)

        color_preview = tk.Label(info_frame, width=4, height=2, bg='#000000',
                                relief='solid', borderwidth=2)
        color_preview.pack(side='left', padx=5)

        info_label = tk.Label(info_frame, text="(0, 0) #000000",
                             font=('Consolas', 12, 'bold'), fg='#00ff00', bg='#2b2b2b')
        info_label.pack(side='left', padx=10)

        help_label = tk.Label(mag_window, text="화면 클릭으로 위치와 색깔 선택",
                             font=('맑은 고딕', 10), fg='#00ff00', bg='#2b2b2b')
        help_label.pack(pady=5)

        mag_window.configure(bg='#2b2b2b')

        current_data = [None, None, None]  # x, y, color
        mouse_was_down = [False]

        def select_position():
            if current_data[0] is not None:
                x, y, hex_color = current_data
                if position_num == 1:
                    self.detect_pos1_x.set(x)
                    self.detect_pos1_y.set(y)
                    self.detect_color1.set(hex_color)
                    if hasattr(self, '_detect_pos1_label'):
                        self._detect_pos1_label.configure(text=f"({x}, {y}) {hex_color}")
                    if hasattr(self, '_detect_color1_preview'):
                        self._detect_color1_preview.configure(fg_color=hex_color)
                else:
                    self.detect_pos2_x.set(x)
                    self.detect_pos2_y.set(y)
                    self.detect_color2.set(hex_color)
                    if hasattr(self, '_detect_pos2_label'):
                        self._detect_pos2_label.configure(text=f"({x}, {y}) {hex_color}")
                    if hasattr(self, '_detect_color2_preview'):
                        self._detect_color2_preview.configure(fg_color=hex_color)

                if hasattr(self, '_detect_status'):
                    self._detect_status.configure(text=f"위치 {position_num} 설정됨: ({x}, {y}) {hex_color}")

                self._detect_picker_mode = False
                mag_window.destroy()

        def update_magnifier():
            if not self._detect_picker_mode:
                try:
                    mag_window.destroy()
                except:
                    pass
                return

            try:
                x, y = pyautogui.position()
                half = capture_size // 2

                mouse_down = win32api.GetAsyncKeyState(0x01) & 0x8000
                if mouse_down:
                    if not mouse_was_down[0]:
                        mouse_was_down[0] = True
                else:
                    if mouse_was_down[0]:
                        mouse_was_down[0] = False
                        select_position()
                        return

                img = ImageGrab.grab(bbox=(x - half, y - half, x + half + 1, y + half + 1))
                center_color = img.getpixel((half, half))
                hex_color = '#{:02x}{:02x}{:02x}'.format(*center_color).upper()

                current_data[0] = x
                current_data[1] = y
                current_data[2] = hex_color

                img_resized = img.resize((display_size, display_size), Image.NEAREST)
                photo = ImageTk.PhotoImage(img_resized)

                canvas.delete('all')
                canvas.create_image(0, 0, anchor='nw', image=photo)
                canvas.image = photo

                center = display_size // 2
                canvas.create_rectangle(center - magnify//2, center - magnify//2,
                                        center + magnify//2, center + magnify//2,
                                        outline='#ff0000', width=2)
                canvas.create_line(center, 0, center, display_size, fill='#ffffff', width=1, dash=(4, 4))
                canvas.create_line(0, center, display_size, center, fill='#ffffff', width=1, dash=(4, 4))

                color_preview.configure(bg=hex_color)
                info_label.configure(text=f"({x}, {y}) {hex_color}")

                # 창 위치
                screen_w = mag_window.winfo_screenwidth()
                screen_h = mag_window.winfo_screenheight()
                win_w, win_h = 280, 280
                new_x = x + 30
                new_y = y - win_h // 2
                if new_x + win_w > screen_w:
                    new_x = x - win_w - 30
                if new_y < 0:
                    new_y = 0
                if new_y + win_h > screen_h:
                    new_y = screen_h - win_h
                mag_window.geometry(f"{win_w}x{win_h}+{new_x}+{new_y}")

            except:
                pass

            mag_window.after(30, update_magnifier)

        def on_escape(event=None):
            self._detect_picker_mode = False
            if hasattr(self, '_detect_status'):
                self._detect_status.configure(text="취소됨")
            try:
                mag_window.destroy()
            except:
                pass

        mag_window.bind('<Escape>', on_escape)
        mag_window.protocol("WM_DELETE_WINDOW", on_escape)
        update_magnifier()
