# -*- coding: utf-8 -*-
"""
벨리알 기능 (색상 감지 + 자동 클릭)
"""

import threading
import time
from PIL import Image
import mss
import pyautogui
import keyboard
import win32api

from constants import COLORS


class BelialMixin:
    """벨리알 기능 믹스인"""

    def init_belial_vars(self):
        """벨리알 관련 변수 초기화"""
        import customtkinter as ctk

        self.colors = [
            ["#DFB387", "#DFB387"],
            ["#DDB186", "#DDB186"],
            ["#D9AE83", "#D9AE83"],
            ["#D8AD82", "#D8AD82"],
            ["#D8AD81", "#D8AD81"],
        ]
        self.exclude_colors = [
            ["#37EAD5", "#37EAD5"],
        ]
        self.tolerance = ctk.IntVar(value=0)
        self.color_tolerance = ctk.IntVar(value=0)
        self.exclude_range = ctk.IntVar(value=3)
        self.trigger_key = ctk.StringVar(value="f4")
        self.trigger_modifier = ctk.StringVar(value="없음")
        self.click_type = ctk.StringVar(value="fkey")
        self.click_delay = ctk.DoubleVar(value=0.01)
        self.use_full_screen = ctk.BooleanVar(value=False)
        self.is_running = False
        self.detection_active = False
        self.picker_mode = False
        self.picker_target = "colors"

        # 검색 영역
        self.search_x1 = ctk.IntVar(value=6)
        self.search_y1 = ctk.IntVar(value=7)
        self.search_x2 = ctk.IntVar(value=2137)
        self.search_y2 = ctk.IntVar(value=1168)
        self.search_step = ctk.IntVar(value=5)

        # 쿨다운 시스템
        self.last_click_pos = None
        self.last_click_time = 0
        self.cooldown_distance = ctk.IntVar(value=50)
        self.cooldown_time = ctk.DoubleVar(value=0.1)

    def toggle_running(self):
        """벨리알 시작/중지"""
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.configure(text="⏹️ 중지", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.status_label.configure(text=f"🔴 [{self.trigger_key.get().upper()}] 키로 시작")
            self.update_idletasks()
            self.detection_active = False
            self.setup_hotkey()
            self.run_detection()
        else:
            self.start_btn.configure(text="▶️ 시작", fg_color=COLORS["success"], hover_color=COLORS["success_hover"])
            self.status_label.configure(text="⏸️ 대기 중")
            self.update_idletasks()
            self.detection_active = False
        self.update_home_status_now()

    def run_detection(self):
        """감지 루프 실행"""
        def detection_loop():
            while self.is_running:
                try:
                    if self.detection_active:
                        found = self.search_and_click()
                        if found:
                            self.after(0, lambda: self.status_label.configure(text="🟢 클릭!"))
                            time.sleep(self.click_delay.get())
                except Exception as e:
                    print(f"Error: {e}")
                time.sleep(0.01)

        threading.Thread(target=detection_loop, daemon=True).start()

    def search_and_click(self):
        """색상 검색 및 클릭"""
        if not self.colors:
            return False

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()
        step = max(1, self.search_step.get())
        tol = self.tolerance.get()
        exclude_range = self.exclude_range.get()

        try:
            with mss.mss() as sct:
                monitor = {"top": y1, "left": x1, "width": x2 - x1, "height": y2 - y1}
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                pixels = img.load()
                width, height = img.size

            visited_centers = set()

            for hex_color, _ in self.colors:
                target_r = int(hex_color[1:3], 16)
                target_g = int(hex_color[3:5], 16)
                target_b = int(hex_color[5:7], 16)

                for y in range(0, height, step):
                    for x in range(0, width, step):
                        try:
                            pixel = pixels[x, y]
                            r, g, b = pixel[0], pixel[1], pixel[2]

                            if (abs(r - target_r) <= tol and
                                abs(g - target_g) <= tol and
                                abs(b - target_b) <= tol):

                                center_x, center_y = self.find_text_center(
                                    pixels, x, y, width, height, hex_color, tol
                                )

                                center_key = (center_x // 20, center_y // 20)
                                if center_key in visited_centers:
                                    continue
                                visited_centers.add(center_key)

                                screen_x = x1 + center_x
                                screen_y = y1 + center_y

                                if self.last_click_pos:
                                    dist_to_last = ((screen_x - self.last_click_pos[0])**2 +
                                                    (screen_y - self.last_click_pos[1])**2)**0.5
                                    time_passed = time.time() - self.last_click_time
                                    if dist_to_last < self.cooldown_distance.get() and time_passed < self.cooldown_time.get():
                                        continue

                                if self.exclude_colors:
                                    if self.has_exclude_color_nearby(pixels, center_x, center_y, width, height, exclude_range, tol):
                                        continue

                                self.smooth_move_to(screen_x, screen_y, duration=0.15)

                                if self.click_type.get() == "right":
                                    pyautogui.rightClick()
                                elif self.click_type.get() == "fkey":
                                    keyboard.press_and_release('f')

                                self.last_click_pos = (screen_x, screen_y)
                                self.last_click_time = time.time()
                                return True

                        except:
                            continue
        except Exception as e:
            print(f"Search error: {e}")

        return False

    def color_matches(self, pixel, hex_color, tol):
        """픽셀이 특정 색상과 일치하는지 확인"""
        r, g, b = pixel[0], pixel[1], pixel[2]
        target_r = int(hex_color[1:3], 16)
        target_g = int(hex_color[3:5], 16)
        target_b = int(hex_color[5:7], 16)
        return (abs(r - target_r) <= tol and
                abs(g - target_g) <= tol and
                abs(b - target_b) <= tol)

    def has_exclude_color_nearby(self, pixels, cx, cy, width, height, check_range, tol):
        """주변에 제외 색상이 있는지 확인"""
        for ex_hex, _ in self.exclude_colors:
            ex_r = int(ex_hex[1:3], 16)
            ex_g = int(ex_hex[3:5], 16)
            ex_b = int(ex_hex[5:7], 16)

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

    def find_text_center(self, pixels, start_x, start_y, width, height, hex_color, tol):
        """시작 픽셀에서 연결된 텍스트 영역의 중앙 좌표 반환"""
        # 수평 스캔 - 왼쪽 끝 찾기
        left_x = start_x
        while left_x > 0:
            try:
                pixel = pixels[left_x - 1, start_y]
                if not self.color_matches(pixel, hex_color, tol):
                    break
                left_x -= 1
            except:
                break

        # 수평 스캔 - 오른쪽 끝 찾기
        right_x = start_x
        while right_x < width - 1:
            try:
                pixel = pixels[right_x + 1, start_y]
                if not self.color_matches(pixel, hex_color, tol):
                    break
                right_x += 1
            except:
                break

        center_x = (left_x + right_x) // 2

        # 수직 스캔 - 위쪽 끝 찾기
        top_y = start_y
        while top_y > 0:
            try:
                pixel = pixels[center_x, top_y - 1]
                if not self.color_matches(pixel, hex_color, tol):
                    break
                top_y -= 1
            except:
                break

        # 수직 스캔 - 아래쪽 끝 찾기
        bottom_y = start_y
        while bottom_y < height - 1:
            try:
                pixel = pixels[center_x, bottom_y + 1]
                if not self.color_matches(pixel, hex_color, tol):
                    break
                bottom_y += 1
            except:
                break

        center_y = (top_y + bottom_y) // 2

        return center_x, center_y

    def find_all_exclude_positions(self, pixels, width, height, step, tol):
        """모든 제외 색상(B) 픽셀 위치 수집"""
        exclude_positions = []
        for ex_hex, _ in self.exclude_colors:
            ex_r = int(ex_hex[1:3], 16)
            ex_g = int(ex_hex[3:5], 16)
            ex_b = int(ex_hex[5:7], 16)

            for y in range(0, height, step):
                for x in range(0, width, step):
                    try:
                        pixel = pixels[x, y]
                        r, g, b = pixel[0], pixel[1], pixel[2]
                        if (abs(r - ex_r) <= tol and
                            abs(g - ex_g) <= tol and
                            abs(b - ex_b) <= tol):
                            exclude_positions.append((x, y))
                    except:
                        continue
        return exclude_positions

    def calculate_min_distance_to_exclude(self, center_x, center_y, exclude_positions):
        """A 중앙에서 가장 가까운 B까지의 거리 계산"""
        if not exclude_positions:
            return float('inf')  # B가 없으면 무한대 거리 (가장 안전)

        min_dist = float('inf')
        for ex_x, ex_y in exclude_positions:
            dist = ((center_x - ex_x) ** 2 + (center_y - ex_y) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def check_nearby_exclude(self, screen_x, screen_y, check_range, tol):
        """이동 후 주변에 제외 색상이 있는지 확인"""
        from PIL import ImageGrab
        try:
            x1 = max(0, screen_x - check_range)
            y1 = max(0, screen_y - check_range)
            x2 = screen_x + check_range
            y2 = screen_y + check_range

            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            pixels = img.load()
            img_width, img_height = img.size

            for ex_hex, _ in self.exclude_colors:
                ex_r = int(ex_hex[1:3], 16)
                ex_g = int(ex_hex[3:5], 16)
                ex_b = int(ex_hex[5:7], 16)

                # 주변 영역 스캔 (3픽셀 간격)
                for y in range(0, img_height, 3):
                    for x in range(0, img_width, 3):
                        try:
                            pixel = pixels[x, y]
                            r, g, b = pixel[0], pixel[1], pixel[2]
                            if (abs(r - ex_r) <= tol and
                                abs(g - ex_g) <= tol and
                                abs(b - ex_b) <= tol):
                                return True  # 제외 색상 발견
                        except:
                            continue
            return False
        except:
            return False

    def verify_before_click(self, screen_x, screen_y, tol):
        """클릭 직전에 현재 위치 색상 확인 - 제외 색상이면 False 반환"""
        from PIL import ImageGrab
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

    def smooth_move_to(self, target_x, target_y, duration=0.15):
        """초부드러운 마우스 이동 - 144fps급"""
        start_x, start_y = win32api.GetCursorPos()
        steps = max(20, int(duration * 144))

        for i in range(1, steps + 1):
            t = i / steps
            t = t * t * (3 - 2 * t)  # ease-in-out

            x = int(start_x + (target_x - start_x) * t)
            y = int(start_y + (target_y - start_y) * t)
            win32api.SetCursorPos((x, y))
            time.sleep(duration / steps)

    def on_trigger_key(self, event):
        """트리거 키 핸들러"""
        if not self.is_running:
            return
        if self.is_chatting():
            return
        if not self.check_modifier(self.trigger_modifier.get()):
            return
        self.detection_active = not self.detection_active
        if self.detection_active:
            self.after(0, lambda: self.status_label.configure(text="🟢 검색 활성화"))
        else:
            self.after(0, lambda: self.status_label.configure(text="🔴 검색 비활성화"))

    def update_color_list(self):
        """색상 리스트 업데이트"""
        if hasattr(self, 'color_listbox'):
            self.color_listbox.delete(0, 'end')
            for color, _ in self.colors:
                self.color_listbox.insert('end', color)

    def update_exclude_list(self):
        """제외 색상 리스트 업데이트"""
        if hasattr(self, 'exclude_listbox'):
            self.exclude_listbox.delete(0, 'end')
            for color, _ in self.exclude_colors:
                self.exclude_listbox.insert('end', color)

    def add_color_manual(self):
        """색상 직접 입력"""
        import customtkinter as ctk
        from tkinter import simpledialog

        color = simpledialog.askstring("색상 입력", "HEX 색상 코드 입력 (예: #FF5500)")
        if color and self.validate_hex(color):
            self.colors.append([color, color])
            self.update_color_list()

    def start_screen_picker(self):
        """화면에서 색상 추출 시작"""
        self.start_magnifier_picker(target="colors")

    def start_exclude_picker(self):
        """제외 색상 추출 시작"""
        self.start_magnifier_picker(target="exclude")

    def start_magnifier_picker(self, target="colors"):
        """돋보기 색상 추출 창"""
        import tkinter as tk
        from PIL import ImageGrab, ImageTk
        import pyautogui

        self.picker_mode = True
        self.picker_target = target

        # 돋보기 창 생성
        mag_window = tk.Toplevel(self)
        mag_window.title("색상 추출기 - 화면 클릭으로 선택 (ESC 취소)")
        mag_window.attributes('-topmost', True)
        mag_window.overrideredirect(False)
        mag_window.geometry("280x280")
        mag_window.resizable(False, False)

        # 확대 영역 크기
        capture_size = 15  # 캡처할 영역 (15x15 픽셀)
        magnify = 12       # 확대 배율
        display_size = capture_size * magnify  # 180x180

        # 캔버스 (확대 이미지)
        canvas = tk.Canvas(mag_window, width=display_size, height=display_size,
                          bg='black', highlightthickness=2, highlightbackground='#00aaff')
        canvas.pack(pady=10)

        # 색상 정보 레이블
        color_frame = tk.Frame(mag_window, bg='#2b2b2b')
        color_frame.pack(fill='x', padx=10)

        color_preview = tk.Label(color_frame, width=4, height=2, bg='#000000',
                                relief='solid', borderwidth=2)
        color_preview.pack(side='left', padx=5)

        color_label = tk.Label(color_frame, text="#000000", font=('Consolas', 16, 'bold'),
                              fg='#00ff00', bg='#2b2b2b')
        color_label.pack(side='left', padx=10)

        # 안내 레이블
        info_label = tk.Label(mag_window, text="🖱️ 화면 아무 곳이나 클릭하여 색상 선택",
                             font=('맑은 고딕', 10), fg='#00ff00', bg='#2b2b2b')
        info_label.pack(pady=5)

        esc_label = tk.Label(mag_window, text="ESC 키로 취소",
                            font=('맑은 고딕', 9), fg='#888888', bg='#2b2b2b')
        esc_label.pack(pady=2)

        mag_window.configure(bg='#2b2b2b')

        current_color = [None]  # 현재 색상 저장
        mouse_was_down = [False]  # 마우스 상태 추적

        def select_color():
            """색상 선택 및 저장"""
            if current_color[0]:
                hex_color = current_color[0]
                if self.picker_target == "colors":
                    self.colors.append([hex_color, hex_color])
                    self.update_color_list()
                    self.picker_status.configure(text=f"✅ 추가됨: {hex_color}")
                elif self.picker_target == "exclude":
                    self.exclude_colors.append([hex_color, hex_color])
                    self.update_exclude_list()
                    self.picker_status.configure(text=f"✅ 제외 색상 추가됨: {hex_color}")
                elif self.picker_target == "inv_keep":
                    self.inv_keep_color.set(hex_color)
                    self.update_inv_color_preview()
                    self.picker_status.configure(text=f"✅ 보존 색상: {hex_color}")
                self.picker_mode = False
                mag_window.destroy()

        def update_magnifier():
            if not self.picker_mode:
                try:
                    mag_window.destroy()
                except:
                    pass
                return

            try:
                x, y = pyautogui.position()
                half = capture_size // 2

                # 전역 마우스 클릭 감지 (win32api)
                # 0x01 = VK_LBUTTON (왼쪽 마우스 버튼)
                mouse_down = win32api.GetAsyncKeyState(0x01) & 0x8000

                if mouse_down:
                    if not mouse_was_down[0]:
                        # 클릭 시작 - 현재 위치의 색상 저장
                        mouse_was_down[0] = True
                else:
                    if mouse_was_down[0]:
                        # 클릭 해제 - 색상 선택 완료
                        mouse_was_down[0] = False
                        select_color()
                        return

                # 화면 캡처
                img = ImageGrab.grab(bbox=(x - half, y - half, x + half + 1, y + half + 1))

                # 중앙 픽셀 색상
                center_color = img.getpixel((half, half))
                hex_color = '#{:02x}{:02x}{:02x}'.format(*center_color).upper()
                current_color[0] = hex_color

                # 이미지 확대
                img_resized = img.resize((display_size, display_size), Image.NEAREST)
                photo = ImageTk.PhotoImage(img_resized)

                canvas.delete('all')
                canvas.create_image(0, 0, anchor='nw', image=photo)
                canvas.image = photo  # 참조 유지

                # 중앙 십자선 및 선택 영역 표시
                center = display_size // 2
                # 선택될 픽셀 영역 표시 (빨간 테두리)
                canvas.create_rectangle(center - magnify//2, center - magnify//2,
                                        center + magnify//2, center + magnify//2,
                                        outline='#ff0000', width=2)
                # 십자선
                canvas.create_line(center, 0, center, display_size, fill='#ffffff', width=1, dash=(4, 4))
                canvas.create_line(0, center, display_size, center, fill='#ffffff', width=1, dash=(4, 4))

                # 색상 정보 업데이트
                color_preview.configure(bg=hex_color)
                color_label.configure(text=hex_color)

                # 창 위치 업데이트 (마우스 옆에)
                screen_w = mag_window.winfo_screenwidth()
                screen_h = mag_window.winfo_screenheight()
                win_w, win_h = 280, 280

                # 마우스 오른쪽에 표시, 화면 밖으로 나가면 왼쪽에
                new_x = x + 30
                new_y = y - win_h // 2
                if new_x + win_w > screen_w:
                    new_x = x - win_w - 30
                if new_y < 0:
                    new_y = 0
                if new_y + win_h > screen_h:
                    new_y = screen_h - win_h

                mag_window.geometry(f"{win_w}x{win_h}+{new_x}+{new_y}")

            except Exception as e:
                pass

            mag_window.after(30, update_magnifier)

        def on_escape(event=None):
            self.picker_mode = False
            if hasattr(self, 'picker_status'):
                self.picker_status.configure(text="취소됨")
            try:
                mag_window.destroy()
            except:
                pass

        # ESC 키로 취소
        mag_window.bind('<Escape>', on_escape)

        # 창 닫기 버튼
        mag_window.protocol("WM_DELETE_WINDOW", on_escape)

        update_magnifier()

    def remove_color(self):
        """선택된 색상 삭제"""
        if hasattr(self, 'color_listbox'):
            selection = self.color_listbox.curselection()
            if selection:
                idx = selection[0]
                del self.colors[idx]
                self.update_color_list()

    def add_exclude_manual(self):
        """제외 색상 직접 입력"""
        from tkinter import simpledialog

        color = simpledialog.askstring("색상 입력", "HEX 색상 코드 입력 (예: #FF5500)")
        if color and self.validate_hex(color):
            self.exclude_colors.append([color, color])
            self.update_exclude_list()

    def remove_exclude_color(self):
        """선택된 제외 색상 삭제"""
        if hasattr(self, 'exclude_listbox'):
            selection = self.exclude_listbox.curselection()
            if selection:
                idx = selection[0]
                del self.exclude_colors[idx]
                self.update_exclude_list()

    def select_area(self):
        """검색 영역 선택"""
        import tkinter as tk
        from tkinter import messagebox

        messagebox.showinfo("영역 선택", "드래그로 영역을 선택하세요.\n좌상단에서 우하단으로 드래그")

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
            self.search_x1.set(x1)
            self.search_y1.set(y1)
            self.search_x2.set(x2)
            self.search_y2.set(y2)
            if hasattr(self, 'area_label'):
                self.area_label.configure(text=f"영역: ({x1},{y1}) ~ ({x2},{y2})")
            overlay.destroy()

        canvas.bind('<Button-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        canvas.bind('<Escape>', lambda e: overlay.destroy())

    def show_area_overlay(self):
        """영역 미리보기"""
        import tkinter as tk

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()

        overlay = tk.Toplevel()
        overlay.geometry(f"{x2-x1}x{y2-y1}+{x1}+{y1}")
        overlay.overrideredirect(True)
        overlay.attributes('-alpha', 0.3)
        overlay.attributes('-topmost', True)
        overlay.configure(bg='green')

        tk.Label(overlay, text="검색 영역", bg='green', fg='white').pack(expand=True)

        overlay.after(2000, overlay.destroy)

    def change_trigger_key(self):
        """트리거 키 변경"""
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
                self.trigger_key.set(event.name)
                if hasattr(self, 'key_display'):
                    self.key_display.configure(text=event.name.upper())
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
                    self.after(0, lambda: self.trigger_key.set("mouse4"))
                    self.after(0, lambda: self.key_display.configure(text="MOUSE4") if hasattr(self, 'key_display') else None)
                    # 버튼 떼어질 때까지 대기
                    while win32api.GetAsyncKeyState(0x05) & 0x8000:
                        time.sleep(0.01)
                    time.sleep(0.1)
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.trigger_key.set("mouse5"))
                    self.after(0, lambda: self.key_display.configure(text="MOUSE5") if hasattr(self, 'key_display') else None)
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
            self.setup_hotkey()  # Lock 안에서 unhook_all + 재등록
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
