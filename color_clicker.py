# -*- coding: utf-8 -*-
"""
색상 인식 자동 우클릭 프로그램
Windows 전용
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import threading
import json
import os
import sys

# Windows 전용 라이브러리
try:
    import pyautogui
    import keyboard
    from PIL import ImageGrab
    import win32api
    import win32con
    import ctypes
except ImportError as e:
    print(f"필요한 라이브러리가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요:")
    print("pip install pyautogui keyboard pillow pywin32")
    sys.exit(1)

# DPI 인식 설정 (고해상도 모니터 지원)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass

CONFIG_FILE = "color_clicker_config.json"


class ColorClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("색상 인식 자동 클릭기")
        self.root.geometry("500x1020")
        self.root.resizable(False, False)

        # 상태 변수
        self.colors = []  # [(hex_color, name), ...] - 클릭할 색상
        self.exclude_colors = []  # [(hex_color, name), ...] - 제외할 색상
        self.tolerance = tk.IntVar(value=10)
        self.exclude_range = tk.IntVar(value=30)  # 제외 색상 검사 범위 (픽셀)
        self.trigger_key = tk.StringVar(value="f1")
        self.click_type = tk.StringVar(value="right")  # 클릭 타입
        self.is_running = False
        self.detection_active = False  # 트리거 키로 토글되는 활성 상태
        self.picker_mode = False
        self.picker_target = "colors"  # "colors" 또는 "exclude"

        # 검색 영역
        self.search_x1 = tk.IntVar(value=0)
        self.search_y1 = tk.IntVar(value=0)
        self.search_x2 = tk.IntVar(value=1920)
        self.search_y2 = tk.IntVar(value=1080)

        # 검색 간격 (픽셀)
        self.search_step = tk.IntVar(value=5)
        self.click_delay = tk.DoubleVar(value=0.1)  # 클릭 후 딜레이 (초)

        self.setup_ui()
        self.load_config()
        self.setup_hotkey()

    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === 색상 목록 섹션 ===
        color_frame = ttk.LabelFrame(main_frame, text="색상 목록", padding="5")
        color_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 색상 리스트박스
        list_frame = ttk.Frame(color_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.color_listbox = tk.Listbox(list_frame, height=8, font=("Consolas", 10))
        self.color_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.color_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.color_listbox.config(yscrollcommand=scrollbar.set)

        # 색상 미리보기
        self.preview_frame = tk.Frame(color_frame, width=50, height=30, bg="white", relief=tk.SUNKEN, bd=2)
        self.preview_frame.pack(pady=5)
        self.color_listbox.bind('<<ListboxSelect>>', self.on_color_select)

        # 버튼 프레임
        btn_frame = ttk.Frame(color_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="직접 입력", command=self.add_color_manual).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="색상 선택기", command=self.add_color_picker).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🎯 화면에서 추출", command=self.start_screen_picker).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="삭제", command=self.remove_color).pack(side=tk.LEFT, padx=2)

        # 스포이드 상태 라벨
        self.picker_status = ttk.Label(color_frame, text="", foreground="blue")
        self.picker_status.pack()

        # === 제외 색상 목록 섹션 ===
        exclude_frame = ttk.LabelFrame(main_frame, text="제외 색상 (이 색이 근처에 있으면 클릭 안함)", padding="5")
        exclude_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 제외 색상 리스트박스
        exclude_list_frame = ttk.Frame(exclude_frame)
        exclude_list_frame.pack(fill=tk.BOTH, expand=True)

        self.exclude_listbox = tk.Listbox(exclude_list_frame, height=4, font=("Consolas", 10))
        self.exclude_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        exclude_scrollbar = ttk.Scrollbar(exclude_list_frame, orient=tk.VERTICAL, command=self.exclude_listbox.yview)
        exclude_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.exclude_listbox.config(yscrollcommand=exclude_scrollbar.set)

        # 제외 색상 버튼
        exclude_btn_frame = ttk.Frame(exclude_frame)
        exclude_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(exclude_btn_frame, text="직접 입력", command=self.add_exclude_manual).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclude_btn_frame, text="🎯 화면에서 추출", command=self.start_exclude_picker).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclude_btn_frame, text="삭제", command=self.remove_exclude_color).pack(side=tk.LEFT, padx=2)

        # 제외 범위 설정
        exclude_range_frame = ttk.Frame(exclude_frame)
        exclude_range_frame.pack(fill=tk.X)
        ttk.Label(exclude_range_frame, text="검사 범위 (픽셀):").pack(side=tk.LEFT)
        ttk.Entry(exclude_range_frame, textvariable=self.exclude_range, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(exclude_range_frame, text="(타겟 주변 이 범위 내 검사)").pack(side=tk.LEFT)

        # === 허용 범위 설정 ===
        tolerance_frame = ttk.LabelFrame(main_frame, text="색상 허용 범위 (0-255)", padding="5")
        tolerance_frame.pack(fill=tk.X, pady=5)

        ttk.Scale(tolerance_frame, from_=0, to=50, variable=self.tolerance, orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(tolerance_frame, textvariable=self.tolerance, width=5).pack(side=tk.RIGHT)

        # === 검색 영역 설정 ===
        area_frame = ttk.LabelFrame(main_frame, text="검색 영역 (픽셀)", padding="5")
        area_frame.pack(fill=tk.X, pady=5)

        area_grid = ttk.Frame(area_frame)
        area_grid.pack(fill=tk.X)

        ttk.Label(area_grid, text="X1:").grid(row=0, column=0, padx=2)
        ttk.Entry(area_grid, textvariable=self.search_x1, width=6).grid(row=0, column=1, padx=2)
        ttk.Label(area_grid, text="Y1:").grid(row=0, column=2, padx=2)
        ttk.Entry(area_grid, textvariable=self.search_y1, width=6).grid(row=0, column=3, padx=2)
        ttk.Label(area_grid, text="X2:").grid(row=0, column=4, padx=2)
        ttk.Entry(area_grid, textvariable=self.search_x2, width=6).grid(row=0, column=5, padx=2)
        ttk.Label(area_grid, text="Y2:").grid(row=0, column=6, padx=2)
        ttk.Entry(area_grid, textvariable=self.search_y2, width=6).grid(row=0, column=7, padx=2)

        area_btn_frame = ttk.Frame(area_frame)
        area_btn_frame.pack(pady=5)
        ttk.Button(area_btn_frame, text="🖱️ 영역 선택", command=self.select_area).pack(side=tk.LEFT, padx=2)
        ttk.Button(area_btn_frame, text="👁️ 영역 보기", command=self.show_area_overlay).pack(side=tk.LEFT, padx=2)

        # 검색 간격
        step_frame = ttk.Frame(area_frame)
        step_frame.pack(fill=tk.X, pady=2)
        ttk.Label(step_frame, text="검색 간격 (픽셀):").pack(side=tk.LEFT)
        ttk.Entry(step_frame, textvariable=self.search_step, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(step_frame, text="(낮을수록 정밀, 높을수록 빠름)").pack(side=tk.LEFT)

        # === 트리거 키 설정 ===
        key_frame = ttk.LabelFrame(main_frame, text="트리거 키 설정", padding="5")
        key_frame.pack(fill=tk.X, pady=5)

        key_inner = ttk.Frame(key_frame)
        key_inner.pack(fill=tk.X)

        ttk.Label(key_inner, text="현재 키:").pack(side=tk.LEFT)
        self.key_label = ttk.Label(key_inner, textvariable=self.trigger_key, font=("Arial", 12, "bold"))
        self.key_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(key_inner, text="키 변경", command=self.change_trigger_key).pack(side=tk.LEFT)

        ttk.Label(key_frame, text="(한 번 누르면 시작, 다시 누르면 중지)", foreground="gray").pack()

        # === 클릭 타입 설정 ===
        click_frame = ttk.LabelFrame(main_frame, text="클릭 타입", padding="5")
        click_frame.pack(fill=tk.X, pady=5)

        click_inner = ttk.Frame(click_frame)
        click_inner.pack(fill=tk.X)

        ttk.Radiobutton(click_inner, text="우클릭", variable=self.click_type, value="right").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(click_inner, text="F키", variable=self.click_type, value="fkey").pack(side=tk.LEFT, padx=5)

        # === 클릭 딜레이 설정 ===
        delay_frame = ttk.LabelFrame(main_frame, text="클릭 딜레이 (초)", padding="5")
        delay_frame.pack(fill=tk.X, pady=5)

        self.delay_label = ttk.Label(delay_frame, text="0.10")

        def update_delay_label(val):
            self.delay_label.config(text=f"{float(val):.2f}")

        delay_scale = ttk.Scale(delay_frame, from_=0.01, to=1.0, variable=self.click_delay,
                                orient=tk.HORIZONTAL, command=update_delay_label)
        delay_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.delay_label.pack(side=tk.RIGHT, padx=5)

        ttk.Label(delay_frame, text="(낮을수록 빠름, 높을수록 느림)").pack()

        # === 상태 표시 ===
        status_frame = ttk.LabelFrame(main_frame, text="상태", padding="5")
        status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(status_frame, text="대기 중", font=("Arial", 14))
        self.status_label.pack()

        self.coord_label = ttk.Label(status_frame, text="마우스: (0, 0)", font=("Consolas", 10))
        self.coord_label.pack()

        # === 컨트롤 버튼 ===
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(ctrl_frame, text="▶ 시작", command=self.toggle_running)
        self.start_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        ttk.Button(ctrl_frame, text="설정 저장", command=self.save_config).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # 마우스 좌표 업데이트
        self.update_mouse_pos()

    def update_mouse_pos(self):
        """마우스 좌표 실시간 업데이트"""
        try:
            x, y = pyautogui.position()
            self.coord_label.config(text=f"마우스: ({x}, {y})")

            # 스포이드 모드일 때 색상도 표시
            if self.picker_mode:
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                    self.picker_status.config(text=f"현재 색상: {hex_color} - 클릭하여 추가 (ESC 취소)")
                except:
                    pass
        except:
            pass
        self.root.after(50, self.update_mouse_pos)

    def on_color_select(self, event):
        """색상 선택 시 미리보기 업데이트"""
        selection = self.color_listbox.curselection()
        if selection:
            idx = selection[0]
            if idx < len(self.colors):
                hex_color = self.colors[idx][0]
                self.preview_frame.config(bg=hex_color)

    def add_color_manual(self):
        """직접 색상 코드 입력"""
        dialog = tk.Toplevel(self.root)
        dialog.title("색상 입력")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="HEX 색상 코드 (예: #FF0000):").pack(pady=10)
        hex_entry = ttk.Entry(dialog, width=20)
        hex_entry.pack()
        hex_entry.insert(0, "#")

        ttk.Label(dialog, text="이름 (선택):").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=20)
        name_entry.pack()

        def add():
            hex_color = hex_entry.get().strip()
            name = name_entry.get().strip() or hex_color
            if self.validate_hex(hex_color):
                self.colors.append((hex_color.upper(), name))
                self.update_color_list()
                dialog.destroy()
            else:
                messagebox.showerror("오류", "올바른 HEX 색상 코드를 입력하세요 (예: #FF0000)")

        ttk.Button(dialog, text="추가", command=add).pack(pady=10)

    def add_color_picker(self):
        """색상 선택기 다이얼로그"""
        color = colorchooser.askcolor(title="색상 선택")
        if color[1]:
            hex_color = color[1].upper()
            self.colors.append((hex_color, hex_color))
            self.update_color_list()

    def start_screen_picker(self):
        """화면에서 색상 추출 모드 시작"""
        self.picker_mode = True
        self.picker_status.config(text="화면에서 원하는 색상 위치를 클릭하세요 (ESC 취소)")

        # 전역 마우스 클릭 감지
        def on_click():
            if self.picker_mode:
                x, y = pyautogui.position()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color).upper()
                    self.colors.append((hex_color, f"{hex_color} @({x},{y})"))
                    self.update_color_list()
                    self.picker_status.config(text=f"추가됨: {hex_color}")
                except Exception as e:
                    self.picker_status.config(text=f"오류: {e}")
                self.picker_mode = False

        def on_escape():
            self.picker_mode = False
            self.picker_status.config(text="취소됨")

        # 키보드 훅 설정
        keyboard.on_press_key('esc', lambda _: on_escape(), suppress=False)

        # 마우스 클릭 대기 (별도 스레드)
        def wait_click():
            import time
            while self.picker_mode:
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    time.sleep(0.1)  # 디바운스
                    self.root.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_click, daemon=True).start()

    def remove_color(self):
        """선택된 색상 삭제"""
        selection = self.color_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.colors[idx]
            self.update_color_list()

    def add_exclude_manual(self):
        """제외 색상 직접 입력"""
        dialog = tk.Toplevel(self.root)
        dialog.title("제외 색상 입력")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="HEX 색상 코드 (예: #FF0000):").pack(pady=10)
        hex_entry = ttk.Entry(dialog, width=20)
        hex_entry.pack()
        hex_entry.insert(0, "#")

        ttk.Label(dialog, text="이름 (선택):").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=20)
        name_entry.pack()

        def add():
            hex_color = hex_entry.get().strip()
            name = name_entry.get().strip() or hex_color
            if self.validate_hex(hex_color):
                self.exclude_colors.append((hex_color.upper(), name))
                self.update_exclude_list()
                dialog.destroy()
            else:
                messagebox.showerror("오류", "올바른 HEX 색상 코드를 입력하세요 (예: #FF0000)")

        ttk.Button(dialog, text="추가", command=add).pack(pady=10)

    def start_exclude_picker(self):
        """제외 색상 추출 모드 시작"""
        self.picker_mode = True
        self.picker_target = "exclude"
        self.picker_status.config(text="제외할 색상 위치를 클릭하세요 (ESC 취소)")

        def on_click():
            if self.picker_mode and self.picker_target == "exclude":
                x, y = pyautogui.position()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color).upper()
                    self.exclude_colors.append((hex_color, f"{hex_color} @({x},{y})"))
                    self.update_exclude_list()
                    self.picker_status.config(text=f"제외 색상 추가됨: {hex_color}")
                except Exception as e:
                    self.picker_status.config(text=f"오류: {e}")
                self.picker_mode = False

        def on_escape():
            self.picker_mode = False
            self.picker_status.config(text="취소됨")

        keyboard.on_press_key('esc', lambda _: on_escape(), suppress=False)

        def wait_click():
            import time
            while self.picker_mode:
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    time.sleep(0.1)
                    self.root.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_click, daemon=True).start()

    def remove_exclude_color(self):
        """선택된 제외 색상 삭제"""
        selection = self.exclude_listbox.curselection()
        if selection:
            idx = selection[0]
            del self.exclude_colors[idx]
            self.update_exclude_list()

    def update_exclude_list(self):
        """제외 색상 리스트박스 업데이트"""
        self.exclude_listbox.delete(0, tk.END)
        for hex_color, name in self.exclude_colors:
            self.exclude_listbox.insert(tk.END, f"{hex_color} - {name}")

    def update_color_list(self):
        """색상 리스트박스 업데이트"""
        self.color_listbox.delete(0, tk.END)
        for hex_color, name in self.colors:
            self.color_listbox.insert(tk.END, f"{hex_color} - {name}")

    def validate_hex(self, hex_color):
        """HEX 색상 코드 유효성 검사"""
        if not hex_color.startswith('#'):
            return False
        hex_color = hex_color[1:]
        if len(hex_color) != 6:
            return False
        try:
            int(hex_color, 16)
            return True
        except ValueError:
            return False

    def select_area(self):
        """드래그로 검색 영역 선택 (오버레이)"""
        self.status_label.config(text="드래그로 영역을 선택하세요...")

        # 오버레이 창 생성
        overlay = tk.Toplevel(self.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        # 캔버스 생성
        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        # 선택 변수
        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline='red', width=3, fill='blue', stipple='gray50'
            )

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                # 캔버스 좌표로 변환
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                x2 = event.x
                y2 = event.y
                canvas.coords(rect_id, x1, y1, x2, y2)

        def on_release(event):
            nonlocal start_x, start_y
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                # 좌표 정렬 (좌상단, 우하단)
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.search_x1.set(x1)
                self.search_y1.set(y1)
                self.search_x2.set(x2)
                self.search_y2.set(y2)

                self.status_label.config(text=f"영역 설정 완료: ({x1},{y1}) ~ ({x2},{y2})")
                overlay.destroy()
                self.show_area_overlay()

        def on_escape(event):
            self.status_label.config(text="영역 선택 취소")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def show_area_overlay(self):
        """선택된 영역을 오버레이로 표시 (토글)"""
        # 이미 보이면 숨기기
        if hasattr(self, 'area_overlay') and self.area_overlay:
            try:
                self.area_overlay.destroy()
            except:
                pass
            self.area_overlay = None
            return

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()
        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            return

        # 테두리만 보이는 오버레이
        self.area_overlay = tk.Toplevel(self.root)
        self.area_overlay.overrideredirect(True)
        self.area_overlay.attributes('-topmost', True)
        self.area_overlay.attributes('-transparentcolor', 'white')
        self.area_overlay.geometry(f'{width}x{height}+{x1}+{y1}')

        canvas = tk.Canvas(self.area_overlay, width=width, height=height,
                          bg='white', highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(2, 2, width-2, height-2, outline='red', width=3)

        # 클릭하면 닫기
        canvas.bind('<Button-1>', lambda e: self.hide_area_overlay())

    def hide_area_overlay(self):
        """오버레이 숨기기"""
        if hasattr(self, 'area_overlay') and self.area_overlay:
            try:
                self.area_overlay.destroy()
            except:
                pass
            self.area_overlay = None

    def change_trigger_key(self):
        """트리거 키 변경"""
        dialog = tk.Toplevel(self.root)
        dialog.title("키 설정")
        dialog.geometry("250x100")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="새 트리거 키를 누르세요...").pack(pady=20)

        def on_key(event):
            key_name = event.name
            self.trigger_key.set(key_name)
            self.setup_hotkey()
            dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def setup_hotkey(self):
        """핫키 설정"""
        keyboard.unhook_all()
        # 트리거 키 핫키 등록
        keyboard.on_press_key(self.trigger_key.get(), self.on_trigger_key, suppress=False)

    def on_trigger_key(self, event):
        """트리거 키 눌렸을 때 토글"""
        if not self.is_running:
            return
        self.detection_active = not self.detection_active
        if self.detection_active:
            self.root.after(0, lambda: self.status_label.config(text="● 검색 활성화", foreground="green"))
        else:
            self.root.after(0, lambda: self.status_label.config(text="○ 검색 비활성화", foreground="red"))

    def toggle_running(self):
        """시작/중지 토글"""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.config(text="⏹ 중지")
            self.status_label.config(text=f"○ 검색 비활성화 - [{self.trigger_key.get()}] 키로 시작", foreground="red")
            self.detection_active = False
            self.setup_hotkey()
            self.run_detection()
        else:
            self.start_btn.config(text="▶ 시작")
            self.status_label.config(text="대기 중", foreground="black")
            self.detection_active = False

    def run_detection(self):
        """색상 감지 스레드"""
        def detection_loop():
            while self.is_running:
                try:
                    # 토글로 활성화된 상태인지 확인
                    if self.detection_active:
                        found = self.search_and_click()
                        if found:
                            self.root.after(0, lambda: self.status_label.config(text="● 클릭!", foreground="green"))
                            import time
                            time.sleep(self.click_delay.get())  # 클릭 후 딜레이
                except Exception as e:
                    print(f"Error: {e}")
                import time
                time.sleep(0.01)

        threading.Thread(target=detection_loop, daemon=True).start()

    def search_and_click(self):
        """색상을 검색하고 클릭"""
        if not self.colors:
            return False

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()
        step = max(1, self.search_step.get())
        tol = self.tolerance.get()
        exclude_range = self.exclude_range.get()

        try:
            # 검색 영역 캡처
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            pixels = img.load()
            width, height = img.size

            # 각 색상에 대해 검색
            for hex_color, _ in self.colors:
                target_r = int(hex_color[1:3], 16)
                target_g = int(hex_color[3:5], 16)
                target_b = int(hex_color[5:7], 16)

                for y in range(0, height, step):
                    for x in range(0, width, step):
                        try:
                            pixel = pixels[x, y]
                            r, g, b = pixel[0], pixel[1], pixel[2]

                            # 허용 범위 내 색상 체크
                            if (abs(r - target_r) <= tol and
                                abs(g - target_g) <= tol and
                                abs(b - target_b) <= tol):

                                # 제외 색상 체크 (주변 범위 내)
                                if self.exclude_colors and self.has_exclude_color_nearby(pixels, x, y, width, height, exclude_range, tol):
                                    continue  # 제외 색상 있으면 패스

                                # 실제 화면 좌표로 변환
                                screen_x = x1 + x
                                screen_y = y1 + y

                                # 마우스 이동 및 클릭
                                pyautogui.moveTo(screen_x, screen_y, duration=0)

                                # 클릭 직전 더블 체크: 현재 위치가 제외 색상이 아닌지 확인
                                if not self.verify_before_click(screen_x, screen_y, tol):
                                    continue  # 제외 색상이면 클릭 안 함

                                click_type = self.click_type.get()
                                if click_type == "right":
                                    pyautogui.rightClick()
                                elif click_type == "fkey":
                                    keyboard.press_and_release('f')
                                return True
                        except:
                            continue
        except Exception as e:
            print(f"Search error: {e}")

        return False

    def has_exclude_color_nearby(self, pixels, cx, cy, width, height, check_range, tol):
        """주변에 제외 색상이 있는지 확인"""
        for ex_hex, _ in self.exclude_colors:
            ex_r = int(ex_hex[1:3], 16)
            ex_g = int(ex_hex[3:5], 16)
            ex_b = int(ex_hex[5:7], 16)

            # 주변 범위 검사
            for dy in range(-check_range, check_range + 1, 3):
                for dx in range(-check_range, check_range + 1, 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        try:
                            pixel = pixels[nx, ny]
                            r, g, b = pixel[0], pixel[1], pixel[2]
                            if (abs(r - ex_r) <= tol and
                                abs(g - ex_g) <= tol and
                                abs(b - ex_b) <= tol):
                                return True
                        except:
                            continue
        return False

    def verify_before_click(self, screen_x, screen_y, tol):
        """클릭 직전에 현재 위치 색상 확인 - 제외 색상이면 False 반환"""
        try:
            # 현재 마우스 위치의 색상 캡처
            img = ImageGrab.grab(bbox=(screen_x-2, screen_y-2, screen_x+3, screen_y+3))
            pixels = img.load()

            # 중앙 픽셀 확인
            center_pixel = pixels[2, 2]
            r, g, b = center_pixel[0], center_pixel[1], center_pixel[2]

            # 제외 색상인지 확인
            for ex_hex, _ in self.exclude_colors:
                ex_r = int(ex_hex[1:3], 16)
                ex_g = int(ex_hex[3:5], 16)
                ex_b = int(ex_hex[5:7], 16)

                if (abs(r - ex_r) <= tol and
                    abs(g - ex_g) <= tol and
                    abs(b - ex_b) <= tol):
                    return False  # 제외 색상이면 클릭하지 않음

            return True  # 안전하면 클릭
        except:
            return True  # 오류 시 일단 클릭

    def save_config(self):
        """설정 저장"""
        config = {
            'colors': self.colors,
            'exclude_colors': self.exclude_colors,
            'tolerance': self.tolerance.get(),
            'exclude_range': self.exclude_range.get(),
            'trigger_key': self.trigger_key.get(),
            'click_type': self.click_type.get(),
            'click_delay': self.click_delay.get(),
            'search_area': {
                'x1': self.search_x1.get(),
                'y1': self.search_y1.get(),
                'x2': self.search_x2.get(),
                'y2': self.search_y2.get()
            },
            'search_step': self.search_step.get()
        }

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("저장", "설정이 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def load_config(self):
        """설정 불러오기"""
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.colors = config.get('colors', [])
            self.exclude_colors = config.get('exclude_colors', [])
            self.tolerance.set(config.get('tolerance', 10))
            self.exclude_range.set(config.get('exclude_range', 30))
            self.trigger_key.set(config.get('trigger_key', 'f1'))
            self.click_type.set(config.get('click_type', 'right'))
            self.click_delay.set(config.get('click_delay', 0.1))

            area = config.get('search_area', {})
            self.search_x1.set(area.get('x1', 0))
            self.search_y1.set(area.get('y1', 0))
            self.search_x2.set(area.get('x2', 1920))
            self.search_y2.set(area.get('y2', 1080))

            self.search_step.set(config.get('search_step', 5))

            self.update_color_list()
            self.update_exclude_list()
        except Exception as e:
            print(f"Config load error: {e}")


def main():
    root = tk.Tk()
    app = ColorClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
