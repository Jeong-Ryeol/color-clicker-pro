# -*- coding: utf-8 -*-
"""
상수 및 버전 정보
"""

import os
import sys

# === 버전 정보 ===
VERSION = "1.9.0"
GITHUB_REPO = "Jeong-Ryeol/color-clicker-pro"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# === 경로 설정 ===
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 EXE
    APP_DIR = os.path.dirname(sys.executable)
else:
    # 소스 코드 실행
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(APP_DIR, "color_clicker_config.json")

# === UI 설정 ===
DEFAULT_FONT = "맑은 고딕"
WINDOW_WIDTH = 950
WINDOW_HEIGHT = 650

# === 기본값 ===
DEFAULT_COLORS = [
    ["#DFB387", "#DFB387"],
    ["#DDB186", "#DDB186"],
    ["#D9AE83", "#D9AE83"],
    ["#D8AD82", "#D8AD82"],
    ["#D8AD81", "#D8AD81"],
]

DEFAULT_EXCLUDE_COLORS = [
    ["#37EAD5", "#37EAD5"],
]

# === 색상 테마 ===
COLORS = {
    "primary": "#1a5f2a",
    "primary_hover": "#2a7f3a",
    "danger": "#dc3545",
    "danger_hover": "#c82333",
    "success": "#28a745",
    "success_hover": "#218838",
    "warning": "#ffc107",
    "warning_hover": "#e0a800",
    "info": "#17a2b8",
    "info_hover": "#138496",
    "secondary": "#6c757d",
    "secondary_hover": "#5a6268",
    "background": "#2b2b2b",
    "sidebar": "#1a1a2e",
    "text": "#ffffff",
    "text_muted": "#666666",
    "accent": "#00aaff",
    "on_color": "#00FF00",
    "off_color": "#666666",
    "active_color": "#ff4444",
}
