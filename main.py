# -*- coding: utf-8 -*-
"""
Wonryeol Helper - 진입점
디아블로4용 자동화 도우미 프로그램 (Windows 전용)
"""

import sys
import ctypes

# DPI 인식 설정
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass

# 테마 설정
import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def main():
    """메인 함수"""
    # Windows 전용 라이브러리 확인
    try:
        import pyautogui
        import keyboard
        from PIL import ImageGrab, Image, ImageTk
        import win32api
        import win32con
        import mss
        import numpy as np
    except ImportError as e:
        print(f"필요한 라이브러리가 설치되지 않았습니다: {e}")
        print("pip install pyautogui keyboard pillow pywin32 customtkinter mss numpy")
        sys.exit(1)

    # 앱 실행
    from app import ColorClickerApp
    app = ColorClickerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
