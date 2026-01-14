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

    def has_exclude_color_nearby(self, pixels, cx, cy, width, height, check_range, tol):
        """주변에 제외 색상이 있는지 확인"""
        for ex_hex, _ in self.exclude_colors:
            ex_r = int(ex_hex[1:3], 16)
            ex_g = int(ex_hex[3:5], 16)
            ex_b = int(ex_hex[5:7], 16)

            for dy in range(-check_range, check_range + 1):
                for dx in range(-check_range, check_range + 1):
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
        """텍스트 중앙 찾기"""
        target_r = int(hex_color[1:3], 16)
        target_g = int(hex_color[3:5], 16)
        target_b = int(hex_color[5:7], 16)

        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y

        # 좌우 확장
        for x in range(start_x, min(start_x + 150, width)):
            try:
                pixel = pixels[x, start_y]
                if (abs(pixel[0] - target_r) <= tol and
                    abs(pixel[1] - target_g) <= tol and
                    abs(pixel[2] - target_b) <= tol):
                    max_x = x
                else:
                    break
            except:
                break

        for x in range(start_x, max(start_x - 150, 0), -1):
            try:
                pixel = pixels[x, start_y]
                if (abs(pixel[0] - target_r) <= tol and
                    abs(pixel[1] - target_g) <= tol and
                    abs(pixel[2] - target_b) <= tol):
                    min_x = x
                else:
                    break
            except:
                break

        # 상하 확장
        center_x = (min_x + max_x) // 2
        for y in range(start_y, min(start_y + 30, height)):
            try:
                pixel = pixels[center_x, y]
                if (abs(pixel[0] - target_r) <= tol and
                    abs(pixel[1] - target_g) <= tol and
                    abs(pixel[2] - target_b) <= tol):
                    max_y = y
                else:
                    break
            except:
                break

        for y in range(start_y, max(start_y - 30, 0), -1):
            try:
                pixel = pixels[center_x, y]
                if (abs(pixel[0] - target_r) <= tol and
                    abs(pixel[1] - target_g) <= tol and
                    abs(pixel[2] - target_b) <= tol):
                    min_y = y
                else:
                    break
            except:
                break

        return (min_x + max_x) // 2, (min_y + max_y) // 2

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
        """확대경 색상 추출"""
        self.picker_mode = True
        self.picker_target = target
        if hasattr(self, 'picker_status'):
            self.picker_status.configure(text="화면 클릭으로 색상 추출 (ESC 취소)")

        def on_click():
            if self.picker_mode:
                x, y = win32api.GetCursorPos()
                import mss
                with mss.mss() as sct:
                    monitor = {"top": y, "left": x, "width": 1, "height": 1}
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    r, g, b = img.getpixel((0, 0))
                    hex_color = f"#{r:02X}{g:02X}{b:02X}"

                    if self.picker_target == "colors":
                        self.colors.append([hex_color, hex_color])
                        self.update_color_list()
                    else:
                        self.exclude_colors.append([hex_color, hex_color])
                        self.update_exclude_list()

                    if hasattr(self, 'picker_status'):
                        self.picker_status.configure(text=f"추출 완료: {hex_color}")
                    self.picker_mode = False

        def wait_for_click():
            import time as time_module
            import win32con
            while self.picker_mode:
                if win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000:
                    self.picker_mode = False
                    self.after(0, lambda: self.picker_status.configure(text="취소됨"))
                    break
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    self.after(0, on_click)
                    break
                time_module.sleep(0.01)

        threading.Thread(target=wait_for_click, daemon=True).start()

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
                self.trigger_key.set(event.name)
                if hasattr(self, 'key_display'):
                    self.key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)
