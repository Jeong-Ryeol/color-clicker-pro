# -*- coding: utf-8 -*-
"""
색상 인식 자동 우클릭 프로그램 (Modern UI)
Windows 전용
"""

import customtkinter as ctk
from tkinter import messagebox, colorchooser, filedialog
import tkinter as tk
import threading
import json
import os
import sys
import winsound
import urllib.request
import re
from datetime import datetime, timezone

# === 버전 정보 ===
VERSION = "1.0.0"
GITHUB_REPO = "Jeong-Ryeol/color-clicker-pro"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Windows 전용 라이브러리
try:
    import pyautogui
    import keyboard
    from PIL import ImageGrab, Image
    import win32api
    import win32con
    import ctypes
    import mss
    import numpy as np
except ImportError as e:
    print(f"필요한 라이브러리가 설치되지 않았습니다: {e}")
    print("pip install pyautogui keyboard pillow pywin32 customtkinter mss numpy")
    sys.exit(1)

# DPI 인식 설정
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    pass

# 테마 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "color_clicker_config.json"


class ColorClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎯 Color Clicker Pro")
        self.geometry("550x1000")
        self.resizable(False, False)

        # 상태 변수
        self.colors = []
        self.exclude_colors = []
        self.tolerance = ctk.IntVar(value=10)
        self.exclude_range = ctk.IntVar(value=30)
        self.trigger_key = ctk.StringVar(value="f1")
        self.trigger_modifier = ctk.StringVar(value="없음")  # 없음, Ctrl, Shift, Alt
        self.click_type = ctk.StringVar(value="right")
        self.click_delay = ctk.DoubleVar(value=0.1)
        self.is_running = False
        self.detection_active = False
        self.picker_mode = False
        self.picker_target = "colors"

        # 검색 영역
        self.search_x1 = ctk.IntVar(value=0)
        self.search_y1 = ctk.IntVar(value=0)
        self.search_x2 = ctk.IntVar(value=1920)
        self.search_y2 = ctk.IntVar(value=1080)
        self.search_step = ctk.IntVar(value=5)

        # 쿨다운 시스템 (최근 클릭 위치)
        self.last_click_pos = None
        self.last_click_time = 0
        self.cooldown_distance = ctk.IntVar(value=50)  # 이 거리 내는 쿨다운
        self.cooldown_time = ctk.DoubleVar(value=0.1)  # 쿨다운 시간 (초)

        # === 신화장난꾸러기 탭 변수 ===
        self.inv_keep_color = ctk.StringVar(value="#FF6B00")  # 보존할 색상 (신화 장난꾸러기)
        self.inv_tolerance = ctk.IntVar(value=15)
        # 전체 인벤토리 영역 (균등 분할)
        self.inv_x1 = ctk.IntVar(value=1725)
        self.inv_y1 = ctk.IntVar(value=1009)
        self.inv_x2 = ctk.IntVar(value=2550)
        self.inv_y2 = ctk.IntVar(value=1340)
        # 설명 패널 영역 (첫 번째 슬롯 기준, X만 이동)
        self.inv_desc_x1 = ctk.IntVar(value=1144)
        self.inv_desc_y1 = ctk.IntVar(value=428)
        self.inv_desc_x2 = ctk.IntVar(value=1636)
        self.inv_desc_y2 = ctk.IntVar(value=1147)
        # 그리드 설정
        self.inv_cols = ctk.IntVar(value=11)
        self.inv_rows = ctk.IntVar(value=3)
        self.inv_running = False
        self.inv_cleanup_active = False  # 실제 정리 루프 실행 중 여부
        self.inv_trigger_key = ctk.StringVar(value="f2")
        self.inv_trigger_modifier = ctk.StringVar(value="없음")  # 없음, Ctrl, Shift, Alt
        self.inv_last_trigger_time = 0  # 디바운스용
        # 딜레이 설정
        self.inv_move_duration = ctk.DoubleVar(value=0.15)  # 슬롯 간 이동 시간
        self.inv_panel_delay = ctk.DoubleVar(value=0.05)  # 설명 패널 대기
        self.inv_space_delay = ctk.DoubleVar(value=0.05)  # 스페이스바 간격
        self.inv_click_delay = ctk.DoubleVar(value=0.01)  # 클릭 후 대기

        # === 아이템 버리기 탭 변수 ===
        self.discard_running = False
        self.discard_active = False
        self.discard_trigger_key = ctk.StringVar(value="f3")
        self.discard_trigger_modifier = ctk.StringVar(value="없음")
        self.discard_last_trigger_time = 0
        self.discard_delay = ctk.DoubleVar(value=0.01)  # 버리기 간격

        # === 아이템 팔기 탭 변수 ===
        self.sell_running = False
        self.sell_active = False
        self.sell_trigger_key = ctk.StringVar(value="f4")
        self.sell_trigger_modifier = ctk.StringVar(value="없음")
        self.sell_last_trigger_time = 0
        self.sell_delay = ctk.DoubleVar(value=0.01)  # 팔기 간격

        # === 아이템 먹기 탭 변수 ===
        self.consume_running = False
        self.consume_active = False
        self.consume_trigger_key = ctk.StringVar(value="f5")
        self.consume_trigger_modifier = ctk.StringVar(value="없음")
        self.consume_last_trigger_time = 0
        self.consume_delay = ctk.DoubleVar(value=0.01)  # 먹기 간격
        self.consume_input_type = ctk.StringVar(value="F키")  # F키, 우클릭, 왼클릭

        # === 오버레이 관련 변수 ===
        self.overlay_window = None
        self.overlay_visible = ctk.BooleanVar(value=False)
        self.overlay_reposition_mode = False
        self.overlay_x = ctk.IntVar(value=100)
        self.overlay_y = ctk.IntVar(value=100)
        self.overlay_alpha = ctk.DoubleVar(value=0.85)  # 투명도 (0.0~1.0)
        self.overlay_labels = {}  # 오버레이 라벨 참조 저장

        # === 소리 알림 ===
        self.sound_enabled = ctk.BooleanVar(value=True)

        # === 긴급 정지 핫키 ===
        self.emergency_stop_key = ctk.StringVar(value="esc")

        # === 자동 시작 설정 ===
        self.auto_start_belial = ctk.BooleanVar(value=False)
        self.auto_start_inv = ctk.BooleanVar(value=False)
        self.auto_start_discard = ctk.BooleanVar(value=False)
        self.auto_start_sell = ctk.BooleanVar(value=False)
        self.auto_start_consume = ctk.BooleanVar(value=False)

        # === 월드 보스 타이머 ===
        self.world_boss_name = ctk.StringVar(value="로딩 중...")
        self.world_boss_time = ctk.StringVar(value="")
        self.world_boss_zone = ctk.StringVar(value="")
        self.world_boss_timestamp = None  # datetime 객체
        self.world_boss_label = None  # 오버레이용 라벨 참조

        # === 오버레이 배경색 ===
        self.overlay_bg_color = ctk.StringVar(value="#1a1a2e")

        self.setup_ui()
        self.load_config()
        self.setup_hotkey()
        self.update_mouse_pos()
        # 자동 시작 적용 (약간의 딜레이 후)
        self.after(500, self.apply_auto_start)
        # 업데이트 확인 (백그라운드)
        self.after(1000, lambda: threading.Thread(target=self.check_for_updates, daemon=True).start())
        # 월드 보스 타이머 시작
        self.after(1500, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())
        self.after(2000, self.update_world_boss_timer)

    def setup_ui(self):
        # === 헤더 ===
        header = ctk.CTkLabel(self, text="🎯 Color Clicker Pro",
                              font=ctk.CTkFont(size=24, weight="bold"))
        header.pack(pady=(10, 5))

        # === 탭뷰 생성 ===
        self.tabview = ctk.CTkTabview(self, width=530, height=920)
        self.tabview.pack(pady=5, padx=10, fill="both", expand=True)

        # 탭 추가
        self.tabview.add("Home")
        self.tabview.add("사용법")
        self.tabview.add("벨리알")
        self.tabview.add("신화장난꾸러기")
        self.tabview.add("아이템 버리기")
        self.tabview.add("아이템 팔기")
        self.tabview.add("아이템 먹기")

        # === 벨리알 탭 ===
        self.main_frame = ctk.CTkScrollableFrame(self.tabview.tab("벨리알"), width=500, height=850)
        self.main_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 타겟 색상 ===
        self.create_color_section()

        # === 제외 색상 ===
        self.create_exclude_section()

        # === 설정 섹션 ===
        self.create_settings_section()

        # === 컨트롤 섹션 ===
        self.create_control_section()

        # === 인벤토리 정리 탭 ===
        self.create_inventory_tab()

        # === 아이템 버리기 탭 ===
        self.create_discard_tab()

        # === 아이템 팔기 탭 ===
        self.create_sell_tab()

        # === 아이템 먹기 탭 ===
        self.create_consume_tab()

        # === Home 탭 (대시보드) ===
        self.create_home_tab()

        # === 사용법 탭 ===
        self.create_help_tab()

    def create_color_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text="🎨 타겟 색상", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

        # 색상 리스트
        list_frame = ctk.CTkFrame(frame, fg_color="transparent")
        list_frame.pack(fill="x", padx=10)

        self.color_listbox = tk.Listbox(list_frame, height=5, font=("Consolas", 11),
                                         bg="#2b2b2b", fg="#ffffff", selectbackground="#1f6aa5",
                                         highlightthickness=0, bd=0)
        self.color_listbox.pack(fill="x", pady=5)

        # 버튼들
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="직접 입력", width=80, command=self.add_color_manual).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="색상 선택", width=80, command=self.add_color_picker).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🎯 화면 추출", width=100, command=self.start_screen_picker,
                      fg_color="#28a745", hover_color="#218838").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="삭제", width=60, command=self.remove_color,
                      fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=2)

        # 상태 라벨
        self.picker_status = ctk.CTkLabel(frame, text="", text_color="#00bfff")
        self.picker_status.pack(pady=2)

    def create_exclude_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text="🚫 제외 색상", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        ctk.CTkLabel(frame, text="이 색상이 근처에 있으면 클릭 안 함", text_color="gray").pack()

        # 제외 색상 리스트
        self.exclude_listbox = tk.Listbox(frame, height=4, font=("Consolas", 11),
                                           bg="#2b2b2b", fg="#ff6b6b", selectbackground="#1f6aa5",
                                           highlightthickness=0, bd=0)
        self.exclude_listbox.pack(fill="x", padx=10, pady=5)

        # 버튼들
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="직접 입력", width=80, command=self.add_exclude_manual).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="🎯 화면 추출", width=100, command=self.start_exclude_picker,
                      fg_color="#fd7e14", hover_color="#e96b00").pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="삭제", width=60, command=self.remove_exclude_color,
                      fg_color="#dc3545", hover_color="#c82333").pack(side="left", padx=2)

        # 검사 범위
        range_frame = ctk.CTkFrame(frame, fg_color="transparent")
        range_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(range_frame, text="검사 범위 (픽셀):").pack(side="left")
        ctk.CTkEntry(range_frame, textvariable=self.exclude_range, width=60).pack(side="left", padx=5)

    def create_settings_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text="⚙️ 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

        # 허용 범위
        tol_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tol_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(tol_frame, text="색상 허용 범위:").pack(side="left")
        self.tol_label = ctk.CTkLabel(tol_frame, text="10", width=30)
        self.tol_label.pack(side="right")
        tol_slider = ctk.CTkSlider(tol_frame, from_=0, to=50, variable=self.tolerance,
                                    command=lambda v: self.tol_label.configure(text=str(int(v))))
        tol_slider.pack(side="right", fill="x", expand=True, padx=10)

        # 검색 영역
        area_frame = ctk.CTkFrame(frame, fg_color="transparent")
        area_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(area_frame, text="검색 영역:").pack(side="left")
        ctk.CTkEntry(area_frame, textvariable=self.search_x1, width=50).pack(side="left", padx=2)
        ctk.CTkEntry(area_frame, textvariable=self.search_y1, width=50).pack(side="left", padx=2)
        ctk.CTkLabel(area_frame, text="~").pack(side="left")
        ctk.CTkEntry(area_frame, textvariable=self.search_x2, width=50).pack(side="left", padx=2)
        ctk.CTkEntry(area_frame, textvariable=self.search_y2, width=50).pack(side="left", padx=2)

        # 영역 버튼
        area_btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        area_btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(area_btn_frame, text="🖱️ 영역 선택", command=self.select_area,
                      fg_color="#6c757d", hover_color="#5a6268").pack(side="left", padx=2)
        ctk.CTkButton(area_btn_frame, text="👁️ 영역 보기", command=self.show_area_overlay,
                      fg_color="#17a2b8", hover_color="#138496").pack(side="left", padx=2)

        # 검색 간격
        step_frame = ctk.CTkFrame(frame, fg_color="transparent")
        step_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(step_frame, text="검색 간격:").pack(side="left")
        ctk.CTkEntry(step_frame, textvariable=self.search_step, width=50).pack(side="left", padx=5)
        ctk.CTkLabel(step_frame, text="(낮을수록 정밀)", text_color="gray").pack(side="left")

        # 트리거 키
        key_frame = ctk.CTkFrame(frame, fg_color="transparent")
        key_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(key_frame, text="트리거 키:").pack(side="left")
        ctk.CTkOptionMenu(key_frame, variable=self.trigger_modifier, values=["없음", "Ctrl", "Shift", "Alt"],
                          width=70).pack(side="left", padx=5)
        ctk.CTkLabel(key_frame, text="+").pack(side="left")
        self.key_display = ctk.CTkLabel(key_frame, text="F1", font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#00ff00")
        self.key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_frame, text="변경", width=60, command=self.change_trigger_key).pack(side="left")

        # 클릭 타입
        click_frame = ctk.CTkFrame(frame, fg_color="transparent")
        click_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(click_frame, text="클릭 타입:").pack(side="left")
        ctk.CTkRadioButton(click_frame, text="우클릭", variable=self.click_type, value="right").pack(side="left", padx=10)
        ctk.CTkRadioButton(click_frame, text="F키", variable=self.click_type, value="fkey").pack(side="left", padx=10)

        # 클릭 딜레이
        delay_frame = ctk.CTkFrame(frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(delay_frame, text="클릭 딜레이:").pack(side="left")
        self.delay_label = ctk.CTkLabel(delay_frame, text="0.10초", width=50)
        self.delay_label.pack(side="right")
        delay_slider = ctk.CTkSlider(delay_frame, from_=0.01, to=1.0, variable=self.click_delay,
                                      command=lambda v: self.delay_label.configure(text=f"{v:.2f}초"))
        delay_slider.pack(side="right", fill="x", expand=True, padx=10)

        # 쿨다운 설정
        cooldown_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cooldown_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cooldown_frame, text="같은위치 쿨다운:").pack(side="left")
        self.cooldown_label = ctk.CTkLabel(cooldown_frame, text="0.10초", width=50)
        self.cooldown_label.pack(side="right")
        cooldown_slider = ctk.CTkSlider(cooldown_frame, from_=0.01, to=0.5, variable=self.cooldown_time,
                                         command=lambda v: self.cooldown_label.configure(text=f"{v:.2f}초"))
        cooldown_slider.pack(side="right", fill="x", expand=True, padx=10)

        # 쿨다운 거리
        cd_dist_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cd_dist_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(cd_dist_frame, text="쿨다운 거리(px):").pack(side="left")
        ctk.CTkEntry(cd_dist_frame, textvariable=self.cooldown_distance, width=50).pack(side="left", padx=5)
        ctk.CTkLabel(cd_dist_frame, text="(이 거리 내 재클릭 방지)", text_color="gray").pack(side="left")

    def create_control_section(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(fill="x", pady=10)

        # 상태 표시
        self.status_frame = ctk.CTkFrame(frame, fg_color="#1a1a2e", corner_radius=10)
        self.status_frame.pack(fill="x", padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self.status_frame, text="⏸️ 대기 중",
                                          font=ctk.CTkFont(size=20, weight="bold"))
        self.status_label.pack(pady=10)

        self.coord_label = ctk.CTkLabel(self.status_frame, text="마우스: (0, 0)",
                                         font=ctk.CTkFont(family="Consolas", size=12))
        self.coord_label.pack(pady=5)

        # 버튼들
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text="▶️ 시작", font=ctk.CTkFont(size=16, weight="bold"),
                                        height=50, command=self.toggle_running,
                                        fg_color="#28a745", hover_color="#218838")
        self.start_btn.pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkButton(btn_frame, text="💾 저장", font=ctk.CTkFont(size=16), height=50,
                      command=self.save_config, fg_color="#007bff", hover_color="#0056b3").pack(side="left", expand=True, fill="x", padx=5)

    def create_inventory_tab(self):
        """신화장난꾸러기 탭 UI 생성"""
        inv_frame = ctk.CTkScrollableFrame(self.tabview.tab("신화장난꾸러기"), width=500, height=850)
        inv_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 설명 ===
        ctk.CTkLabel(inv_frame, text="🎭 신화장난꾸러기 필터",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(inv_frame, text="신화 장난꾸러기만 남기고 나머지 버리기",
                     text_color="gray").pack()

        # === 보존할 색상 ===
        color_frame = ctk.CTkFrame(inv_frame)
        color_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(color_frame, text="🎨 보존할 색상 (신화 장난꾸러기)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        color_input_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        color_input_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(color_input_frame, text="색상 코드:").pack(side="left")
        self.inv_color_entry = ctk.CTkEntry(color_input_frame, textvariable=self.inv_keep_color, width=100)
        self.inv_color_entry.pack(side="left", padx=5)

        self.inv_color_preview = ctk.CTkLabel(color_input_frame, text="  ■  ", width=40,
                                               fg_color=self.inv_keep_color.get())
        self.inv_color_preview.pack(side="left", padx=5)

        ctk.CTkButton(color_input_frame, text="🎯 화면 추출", width=100,
                      command=self.inv_pick_color, fg_color="#28a745").pack(side="left", padx=5)

        # 색상 미리보기 업데이트
        self.inv_color_entry.bind("<KeyRelease>", self.update_inv_color_preview)

        # 허용 범위
        tol_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        tol_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(tol_frame, text="허용 범위:").pack(side="left")
        self.inv_tol_label = ctk.CTkLabel(tol_frame, text="15", width=30)
        self.inv_tol_label.pack(side="right")
        ctk.CTkSlider(tol_frame, from_=0, to=50, variable=self.inv_tolerance,
                      command=lambda v: self.inv_tol_label.configure(text=str(int(v)))).pack(side="right", fill="x", expand=True, padx=10)

        # === 인벤토리 영역 설정 ===
        grid_frame = ctk.CTkFrame(inv_frame)
        grid_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(grid_frame, text="📐 인벤토리 영역 설정",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # 영역 좌표
        area_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        area_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(area_frame, text="영역:").pack(side="left")
        ctk.CTkEntry(area_frame, textvariable=self.inv_x1, width=55).pack(side="left", padx=2)
        ctk.CTkEntry(area_frame, textvariable=self.inv_y1, width=55).pack(side="left", padx=2)
        ctk.CTkLabel(area_frame, text="~").pack(side="left")
        ctk.CTkEntry(area_frame, textvariable=self.inv_x2, width=55).pack(side="left", padx=2)
        ctk.CTkEntry(area_frame, textvariable=self.inv_y2, width=55).pack(side="left", padx=2)

        # 영역 버튼
        area_btn_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        area_btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(area_btn_frame, text="🖱️ 영역 선택", command=self.select_inv_area,
                      fg_color="#6c757d", hover_color="#5a6268").pack(side="left", padx=2)
        ctk.CTkButton(area_btn_frame, text="👁️ 영역 보기", command=self.show_inv_area_overlay,
                      fg_color="#17a2b8", hover_color="#138496").pack(side="left", padx=2)

        # 그리드 크기
        size_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(size_frame, text="그리드:").pack(side="left")
        ctk.CTkLabel(size_frame, text="가로").pack(side="left", padx=(10, 2))
        ctk.CTkEntry(size_frame, textvariable=self.inv_cols, width=50).pack(side="left")
        ctk.CTkLabel(size_frame, text="세로").pack(side="left", padx=(10, 2))
        ctk.CTkEntry(size_frame, textvariable=self.inv_rows, width=50).pack(side="left")
        ctk.CTkLabel(size_frame, text="칸").pack(side="left", padx=5)

        # === 설명 패널 영역 ===
        desc_frame = ctk.CTkFrame(inv_frame)
        desc_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(desc_frame, text="📋 설명 패널 영역 (첫 번째 슬롯 기준)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        desc_area_frame = ctk.CTkFrame(desc_frame, fg_color="transparent")
        desc_area_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(desc_area_frame, text="영역:").pack(side="left")
        ctk.CTkEntry(desc_area_frame, textvariable=self.inv_desc_x1, width=55).pack(side="left", padx=2)
        ctk.CTkEntry(desc_area_frame, textvariable=self.inv_desc_y1, width=55).pack(side="left", padx=2)
        ctk.CTkLabel(desc_area_frame, text="~").pack(side="left")
        ctk.CTkEntry(desc_area_frame, textvariable=self.inv_desc_x2, width=55).pack(side="left", padx=2)
        ctk.CTkEntry(desc_area_frame, textvariable=self.inv_desc_y2, width=55).pack(side="left", padx=2)

        desc_btn_frame = ctk.CTkFrame(desc_frame, fg_color="transparent")
        desc_btn_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(desc_btn_frame, text="🖱️ 영역 선택", command=self.select_desc_area,
                      fg_color="#6c757d", hover_color="#5a6268").pack(side="left", padx=2)

        ctk.CTkLabel(desc_frame, text="※ Y축 고정, X축은 슬롯 이동에 따라 자동 계산",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=2)

        # === 속도 설정 ===
        speed_frame = ctk.CTkFrame(inv_frame)
        speed_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(speed_frame, text="⚡ 속도 설정",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # 마우스 이동 속도
        move_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        move_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(move_frame, text="이동 속도:").pack(side="left")
        self.inv_move_label = ctk.CTkLabel(move_frame, text="0.15초", width=60)
        self.inv_move_label.pack(side="right")
        ctk.CTkSlider(move_frame, from_=0.05, to=0.5, variable=self.inv_move_duration,
                      command=lambda v: self.inv_move_label.configure(text=f"{v:.2f}초")).pack(side="right", fill="x", expand=True, padx=10)

        # 패널 대기 딜레이
        panel_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        panel_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(panel_frame, text="패널 대기:").pack(side="left")
        self.inv_panel_label = ctk.CTkLabel(panel_frame, text="0.05초", width=60)
        self.inv_panel_label.pack(side="right")
        ctk.CTkSlider(panel_frame, from_=0.01, to=0.5, variable=self.inv_panel_delay,
                      command=lambda v: self.inv_panel_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        # 스페이스바 간격
        space_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        space_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(space_frame, text="스페이스 간격:").pack(side="left")
        self.inv_space_label = ctk.CTkLabel(space_frame, text="0.05초", width=60)
        self.inv_space_label.pack(side="right")
        ctk.CTkSlider(space_frame, from_=0.01, to=0.3, variable=self.inv_space_delay,
                      command=lambda v: self.inv_space_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        # 클릭 딜레이
        click_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        click_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(click_frame, text="클릭 대기:").pack(side="left")
        self.inv_click_label = ctk.CTkLabel(click_frame, text="0.01초", width=60)
        self.inv_click_label.pack(side="right")
        ctk.CTkSlider(click_frame, from_=0.005, to=0.1, variable=self.inv_click_delay,
                      command=lambda v: self.inv_click_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        # === 트리거 키 ===
        key_frame = ctk.CTkFrame(inv_frame)
        key_frame.pack(fill="x", pady=10, padx=10)

        key_inner = ctk.CTkFrame(key_frame, fg_color="transparent")
        key_inner.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(key_inner, text="트리거 키:").pack(side="left")
        ctk.CTkOptionMenu(key_inner, variable=self.inv_trigger_modifier, values=["없음", "Ctrl", "Shift", "Alt"],
                          width=70).pack(side="left", padx=5)
        ctk.CTkLabel(key_inner, text="+").pack(side="left")
        self.inv_key_display = ctk.CTkLabel(key_inner, text="F2", font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color="#00ff00")
        self.inv_key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_inner, text="변경", width=60, command=self.change_inv_trigger_key).pack(side="left")

        # === 상태 & 컨트롤 ===
        ctrl_frame = ctk.CTkFrame(inv_frame)
        ctrl_frame.pack(fill="x", pady=10, padx=10)

        self.inv_status_frame = ctk.CTkFrame(ctrl_frame, fg_color="#1a1a2e", corner_radius=10)
        self.inv_status_frame.pack(fill="x", padx=10, pady=10)

        self.inv_status_label = ctk.CTkLabel(self.inv_status_frame, text="⏸️ 대기 중",
                                              font=ctk.CTkFont(size=18, weight="bold"))
        self.inv_status_label.pack(pady=10)

        self.inv_progress_label = ctk.CTkLabel(self.inv_status_frame, text="",
                                                font=ctk.CTkFont(size=12))
        self.inv_progress_label.pack(pady=5)

        # 버튼
        btn_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.inv_start_btn = ctk.CTkButton(btn_frame, text="▶️ 시작", font=ctk.CTkFont(size=16, weight="bold"),
                                            height=50, command=self.toggle_inv_running,
                                            fg_color="#28a745", hover_color="#218838")
        self.inv_start_btn.pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkButton(btn_frame, text="🔍 그리드 테스트", font=ctk.CTkFont(size=14), height=50,
                      command=self.test_inv_grid, fg_color="#6c757d", hover_color="#5a6268").pack(side="left", expand=True, fill="x", padx=5)

    def create_discard_tab(self):
        """아이템 버리기 탭 UI 생성 - 초고속 전체 버리기"""
        discard_frame = ctk.CTkScrollableFrame(self.tabview.tab("아이템 버리기"), width=500, height=850)
        discard_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 설명 ===
        ctk.CTkLabel(discard_frame, text="🗑️ 아이템 전체 버리기",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(discard_frame, text="인벤토리 모든 아이템 초고속 버리기\n(신화장난꾸러기 탭과 같은 좌표 사용)",
                     text_color="gray").pack()

        # === 속도 설정 ===
        speed_frame = ctk.CTkFrame(discard_frame)
        speed_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(speed_frame, text="⚡ 버리기 간격",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        delay_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(delay_frame, text="딜레이:").pack(side="left")
        self.discard_delay_label = ctk.CTkLabel(delay_frame, text="0.01초", width=60)
        self.discard_delay_label.pack(side="right")
        ctk.CTkSlider(delay_frame, from_=0.001, to=0.1, variable=self.discard_delay,
                      command=lambda v: self.discard_delay_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        ctk.CTkLabel(speed_frame, text="※ 0.001초 = 초당 1000회 시도 (최고속)",
                     text_color="orange", font=ctk.CTkFont(size=11)).pack(pady=2)

        # === 트리거 키 ===
        key_frame = ctk.CTkFrame(discard_frame)
        key_frame.pack(fill="x", pady=10, padx=10)

        key_inner = ctk.CTkFrame(key_frame, fg_color="transparent")
        key_inner.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(key_inner, text="트리거 키:").pack(side="left")
        ctk.CTkOptionMenu(key_inner, variable=self.discard_trigger_modifier, values=["없음", "Ctrl", "Shift", "Alt"],
                          width=70).pack(side="left", padx=5)
        ctk.CTkLabel(key_inner, text="+").pack(side="left")
        self.discard_key_display = ctk.CTkLabel(key_inner, text="F3", font=ctk.CTkFont(size=14, weight="bold"),
                                                 text_color="#ff6600")
        self.discard_key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_inner, text="변경", width=60, command=self.change_discard_trigger_key).pack(side="left")

        # === 상태 & 컨트롤 ===
        ctrl_frame = ctk.CTkFrame(discard_frame)
        ctrl_frame.pack(fill="x", pady=10, padx=10)

        self.discard_status_frame = ctk.CTkFrame(ctrl_frame, fg_color="#1a1a2e", corner_radius=10)
        self.discard_status_frame.pack(fill="x", padx=10, pady=10)

        self.discard_status_label = ctk.CTkLabel(self.discard_status_frame, text="⏸️ 대기 중",
                                                  font=ctk.CTkFont(size=18, weight="bold"))
        self.discard_status_label.pack(pady=10)

        self.discard_progress_label = ctk.CTkLabel(self.discard_status_frame, text="",
                                                    font=ctk.CTkFont(size=12))
        self.discard_progress_label.pack(pady=5)

        # 버튼
        btn_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.discard_start_btn = ctk.CTkButton(btn_frame, text="▶️ 시작", font=ctk.CTkFont(size=16, weight="bold"),
                                                height=50, command=self.toggle_discard_running,
                                                fg_color="#dc3545", hover_color="#c82333")
        self.discard_start_btn.pack(side="left", expand=True, fill="x", padx=5)

        # 경고
        ctk.CTkLabel(discard_frame, text="⚠️ 주의: 모든 아이템이 버려집니다!\n즐겨찾기/잠금 아이템은 안전합니다.",
                     text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=10)

    def change_discard_trigger_key(self):
        """아이템 버리기 트리거 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...\n(마우스 4/5번 버튼도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.discard_trigger_key.set(event.name)
                self.discard_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def poll_mouse():
            import time
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.discard_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.discard_key_display.configure(text="MOUSE4"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.discard_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.discard_key_display.configure(text="MOUSE5"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def toggle_discard_running(self):
        """아이템 버리기 시작/중지"""
        self.discard_running = not self.discard_running
        if self.discard_running:
            self.discard_start_btn.configure(text="⏹️ 중지", fg_color="#6c757d", hover_color="#5a6268")
            self.discard_status_label.configure(text=f"🔴 [{self.discard_trigger_key.get().upper()}] 키로 시작")
            self.discard_status_frame.configure(fg_color="#3d1a1a")
        else:
            self.discard_active = False
            self.discard_start_btn.configure(text="▶️ 시작", fg_color="#dc3545", hover_color="#c82333")
            self.discard_status_label.configure(text="⏸️ 대기 중")
            self.discard_status_frame.configure(fg_color="#1a1a2e")
            self.discard_progress_label.configure(text="")

    def on_discard_trigger_key(self, event):
        """아이템 버리기 트리거 키 핸들러"""
        import time as time_module

        if not self.discard_running:
            return

        # 조합키 체크
        if not self.check_modifier(self.discard_trigger_modifier.get()):
            return

        # 디바운스
        current_time = time_module.time()
        if current_time - self.discard_last_trigger_time < 0.3:
            return
        self.discard_last_trigger_time = current_time

        if self.discard_active:
            self.discard_active = False
            self.after(0, lambda: self.discard_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.discard_status_frame.configure(fg_color="#3d3d1a"))
        else:
            self.discard_active = True
            self.run_fast_discard()

    def run_fast_discard(self):
        """초고속 아이템 버리기 - 픽셀 검사 없이 전체 버리기"""
        def discard_loop():
            import time
            positions = self.get_inventory_positions()
            total = len(positions)
            delay = self.discard_delay.get()

            self.after(0, lambda: self.discard_status_label.configure(text="🗑️ 버리는 중..."))
            self.after(0, lambda: self.discard_status_frame.configure(fg_color="#3d1a1a"))

            discarded = 0
            for i, (x, y, col) in enumerate(positions):
                if not self.discard_active:
                    break

                # 초고속: 텔레포트 + 즉시 Ctrl+클릭
                win32api.SetCursorPos((x, y))
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                discarded += 1

                if delay > 0.001:
                    time.sleep(delay)

                # 진행상황 (10개마다)
                if i % 10 == 0:
                    self.after(0, lambda idx=i, t=total: self.discard_progress_label.configure(
                        text=f"{idx+1}/{t}"))

            self.discard_active = False
            self.after(0, lambda: self.discard_status_label.configure(text="✅ 완료!"))
            self.after(0, lambda: self.discard_status_frame.configure(fg_color="#1a1a2e"))
            self.after(0, lambda d=discarded: self.discard_progress_label.configure(
                text=f"총 {d}개 버림"))

        threading.Thread(target=discard_loop, daemon=True).start()

    def create_sell_tab(self):
        """아이템 팔기 탭 UI 생성 - 초고속 전체 팔기 (우클릭)"""
        sell_frame = ctk.CTkScrollableFrame(self.tabview.tab("아이템 팔기"), width=500, height=850)
        sell_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 설명 ===
        ctk.CTkLabel(sell_frame, text="💰 아이템 전체 팔기",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(sell_frame, text="인벤토리 모든 아이템 초고속 판매 (우클릭)\n(신화장난꾸러기 탭과 같은 좌표 사용)",
                     text_color="gray").pack()

        # === 속도 설정 ===
        speed_frame = ctk.CTkFrame(sell_frame)
        speed_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(speed_frame, text="⚡ 팔기 간격",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        delay_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(delay_frame, text="딜레이:").pack(side="left")
        self.sell_delay_label = ctk.CTkLabel(delay_frame, text="0.01초", width=60)
        self.sell_delay_label.pack(side="right")
        ctk.CTkSlider(delay_frame, from_=0.001, to=0.1, variable=self.sell_delay,
                      command=lambda v: self.sell_delay_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        ctk.CTkLabel(speed_frame, text="※ 0.001초 = 초당 1000회 시도 (최고속)",
                     text_color="orange", font=ctk.CTkFont(size=11)).pack(pady=2)

        # === 트리거 키 ===
        key_frame = ctk.CTkFrame(sell_frame)
        key_frame.pack(fill="x", pady=10, padx=10)

        key_inner = ctk.CTkFrame(key_frame, fg_color="transparent")
        key_inner.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(key_inner, text="트리거 키:").pack(side="left")
        ctk.CTkOptionMenu(key_inner, variable=self.sell_trigger_modifier, values=["없음", "Ctrl", "Shift", "Alt"],
                          width=70).pack(side="left", padx=5)
        ctk.CTkLabel(key_inner, text="+").pack(side="left")
        self.sell_key_display = ctk.CTkLabel(key_inner, text="F4", font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color="#ff6600")
        self.sell_key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_inner, text="변경", width=60, command=self.change_sell_trigger_key).pack(side="left")

        # === 상태 & 컨트롤 ===
        ctrl_frame = ctk.CTkFrame(sell_frame)
        ctrl_frame.pack(fill="x", pady=10, padx=10)

        self.sell_status_frame = ctk.CTkFrame(ctrl_frame, fg_color="#1a1a2e", corner_radius=10)
        self.sell_status_frame.pack(fill="x", padx=10, pady=10)

        self.sell_status_label = ctk.CTkLabel(self.sell_status_frame, text="⏸️ 대기 중",
                                              font=ctk.CTkFont(size=18, weight="bold"))
        self.sell_status_label.pack(pady=10)

        self.sell_progress_label = ctk.CTkLabel(self.sell_status_frame, text="",
                                                font=ctk.CTkFont(size=12))
        self.sell_progress_label.pack(pady=5)

        # 버튼
        btn_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.sell_start_btn = ctk.CTkButton(btn_frame, text="▶️ 시작", font=ctk.CTkFont(size=16, weight="bold"),
                                            height=50, command=self.toggle_sell_running,
                                            fg_color="#28a745", hover_color="#218838")
        self.sell_start_btn.pack(side="left", expand=True, fill="x", padx=5)

        # 경고
        ctk.CTkLabel(sell_frame, text="⚠️ 주의: 상인 창을 열고 사용하세요!\n즐겨찾기/잠금 아이템은 안전합니다.",
                     text_color="#ffaa00", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=10)

    def change_sell_trigger_key(self):
        """아이템 팔기 트리거 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...\n(마우스 4/5번 버튼도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.sell_trigger_key.set(event.name)
                self.sell_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def poll_mouse():
            import time
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.sell_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.sell_key_display.configure(text="MOUSE4"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.sell_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.sell_key_display.configure(text="MOUSE5"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def toggle_sell_running(self):
        """아이템 팔기 시작/중지"""
        self.sell_running = not self.sell_running
        if self.sell_running:
            self.sell_start_btn.configure(text="⏹️ 중지", fg_color="#6c757d", hover_color="#5a6268")
            self.sell_status_label.configure(text=f"🔴 [{self.sell_trigger_key.get().upper()}] 키로 시작")
            self.sell_status_frame.configure(fg_color="#3d3d1a")
        else:
            self.sell_active = False
            self.sell_start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.sell_status_label.configure(text="⏸️ 대기 중")
            self.sell_status_frame.configure(fg_color="#1a1a2e")
            self.sell_progress_label.configure(text="")

    def on_sell_trigger_key(self, event):
        """아이템 팔기 트리거 키 핸들러"""
        import time as time_module

        if not self.sell_running:
            return

        # 조합키 체크
        if not self.check_modifier(self.sell_trigger_modifier.get()):
            return

        # 디바운스
        current_time = time_module.time()
        if current_time - self.sell_last_trigger_time < 0.3:
            return
        self.sell_last_trigger_time = current_time

        if self.sell_active:
            self.sell_active = False
            self.after(0, lambda: self.sell_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.sell_status_frame.configure(fg_color="#3d3d1a"))
        else:
            self.sell_active = True
            self.run_fast_sell()

    def run_fast_sell(self):
        """초고속 아이템 팔기 - 픽셀 검사 없이 전체 우클릭"""
        def sell_loop():
            import time
            positions = self.get_inventory_positions()
            total = len(positions)
            delay = self.sell_delay.get()

            self.after(0, lambda: self.sell_status_label.configure(text="💰 파는 중..."))
            self.after(0, lambda: self.sell_status_frame.configure(fg_color="#1a3d1a"))

            sold = 0
            for i, (x, y, col) in enumerate(positions):
                if not self.sell_active:
                    break

                # 초고속: 텔레포트 + 즉시 우클릭
                win32api.SetCursorPos((x, y))
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                sold += 1

                if delay > 0.001:
                    time.sleep(delay)

                # 진행상황 (10개마다)
                if i % 10 == 0:
                    self.after(0, lambda idx=i, t=total: self.sell_progress_label.configure(
                        text=f"{idx+1}/{t}"))

            self.sell_active = False
            self.after(0, lambda: self.sell_status_label.configure(text="✅ 완료!"))
            self.after(0, lambda: self.sell_status_frame.configure(fg_color="#1a1a2e"))
            self.after(0, lambda s=sold: self.sell_progress_label.configure(
                text=f"총 {s}개 판매"))

        threading.Thread(target=sell_loop, daemon=True).start()

    def create_consume_tab(self):
        """아이템 먹기 탭 UI 생성 - 마우스 위치에서 입력 반복"""
        consume_frame = ctk.CTkScrollableFrame(self.tabview.tab("아이템 먹기"), width=500, height=850)
        consume_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 설명 ===
        ctk.CTkLabel(consume_frame, text="🍖 아이템 먹기",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(consume_frame, text="현재 마우스 위치에서 선택한 입력 초고속 반복\n(마우스를 아이템에 가져다 놓고 사용)",
                     text_color="gray").pack()

        # === 입력 방식 선택 ===
        input_frame = ctk.CTkFrame(consume_frame)
        input_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(input_frame, text="🖱️ 입력 방식",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        input_inner = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_inner.pack(fill="x", padx=10, pady=5)

        ctk.CTkRadioButton(input_inner, text="F키", variable=self.consume_input_type,
                           value="F키").pack(side="left", padx=10)
        ctk.CTkRadioButton(input_inner, text="우클릭", variable=self.consume_input_type,
                           value="우클릭").pack(side="left", padx=10)
        ctk.CTkRadioButton(input_inner, text="왼클릭", variable=self.consume_input_type,
                           value="왼클릭").pack(side="left", padx=10)

        # === 속도 설정 ===
        speed_frame = ctk.CTkFrame(consume_frame)
        speed_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(speed_frame, text="⚡ 먹기 간격",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        delay_frame = ctk.CTkFrame(speed_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(delay_frame, text="딜레이:").pack(side="left")
        self.consume_delay_label = ctk.CTkLabel(delay_frame, text="0.01초", width=60)
        self.consume_delay_label.pack(side="right")
        ctk.CTkSlider(delay_frame, from_=0.001, to=0.1, variable=self.consume_delay,
                      command=lambda v: self.consume_delay_label.configure(text=f"{v:.3f}초")).pack(side="right", fill="x", expand=True, padx=10)

        ctk.CTkLabel(speed_frame, text="※ 0.001초 = 초당 1000회 시도 (최고속)",
                     text_color="orange", font=ctk.CTkFont(size=11)).pack(pady=2)

        # === 트리거 키 ===
        key_frame = ctk.CTkFrame(consume_frame)
        key_frame.pack(fill="x", pady=10, padx=10)

        key_inner = ctk.CTkFrame(key_frame, fg_color="transparent")
        key_inner.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(key_inner, text="트리거 키:").pack(side="left")
        ctk.CTkOptionMenu(key_inner, variable=self.consume_trigger_modifier, values=["없음", "Ctrl", "Shift", "Alt"],
                          width=70).pack(side="left", padx=5)
        ctk.CTkLabel(key_inner, text="+").pack(side="left")
        self.consume_key_display = ctk.CTkLabel(key_inner, text="F5", font=ctk.CTkFont(size=14, weight="bold"),
                                                text_color="#ff6600")
        self.consume_key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_inner, text="변경", width=60, command=self.change_consume_trigger_key).pack(side="left")

        # === 상태 & 컨트롤 ===
        ctrl_frame = ctk.CTkFrame(consume_frame)
        ctrl_frame.pack(fill="x", pady=10, padx=10)

        self.consume_status_frame = ctk.CTkFrame(ctrl_frame, fg_color="#1a1a2e", corner_radius=10)
        self.consume_status_frame.pack(fill="x", padx=10, pady=10)

        self.consume_status_label = ctk.CTkLabel(self.consume_status_frame, text="⏸️ 대기 중",
                                                 font=ctk.CTkFont(size=18, weight="bold"))
        self.consume_status_label.pack(pady=10)

        self.consume_progress_label = ctk.CTkLabel(self.consume_status_frame, text="",
                                                   font=ctk.CTkFont(size=12))
        self.consume_progress_label.pack(pady=5)

        # 버튼
        btn_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.consume_start_btn = ctk.CTkButton(btn_frame, text="▶️ 시작", font=ctk.CTkFont(size=16, weight="bold"),
                                               height=50, command=self.toggle_consume_running,
                                               fg_color="#17a2b8", hover_color="#138496")
        self.consume_start_btn.pack(side="left", expand=True, fill="x", padx=5)

        # 안내
        ctk.CTkLabel(consume_frame, text="💡 마우스를 아이템 위에 놓고 트리거 키를 누르세요",
                     text_color="#00aaff", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=10)

    def change_consume_trigger_key(self):
        """아이템 먹기 트리거 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...\n(마우스 4/5번 버튼도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.consume_trigger_key.set(event.name)
                self.consume_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def poll_mouse():
            import time
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.consume_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.consume_key_display.configure(text="MOUSE4"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.consume_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.consume_key_display.configure(text="MOUSE5"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def create_home_tab(self):
        """Home 탭 (대시보드) UI 생성"""
        home_frame = ctk.CTkScrollableFrame(self.tabview.tab("Home"), width=500, height=850)
        home_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 헤더 ===
        ctk.CTkLabel(home_frame, text="🏠 대시보드",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(home_frame, text="모든 기능을 한눈에 관리",
                     text_color="gray").pack()

        # === 전체 시작/중지 버튼 (큰 버튼) ===
        all_ctrl_frame = ctk.CTkFrame(home_frame)
        all_ctrl_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(all_ctrl_frame, text="🎮 전체 제어",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        all_btn_frame = ctk.CTkFrame(all_ctrl_frame, fg_color="transparent")
        all_btn_frame.pack(fill="x", padx=10, pady=10)

        self.all_start_btn = ctk.CTkButton(all_btn_frame, text="▶️ 전체 시작",
                                            font=ctk.CTkFont(size=16, weight="bold"),
                                            height=50, command=self.start_all_functions,
                                            fg_color="#28a745", hover_color="#218838")
        self.all_start_btn.pack(side="left", expand=True, fill="x", padx=5)

        self.all_stop_btn = ctk.CTkButton(all_btn_frame, text="⏹️ 전체 중지",
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           height=50, command=self.stop_all_functions,
                                           fg_color="#dc3545", hover_color="#c82333")
        self.all_stop_btn.pack(side="left", expand=True, fill="x", padx=5)

        # === 기능 목록 ===
        func_frame = ctk.CTkFrame(home_frame)
        func_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(func_frame, text="⚡ 기능 상태",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        # 각 기능 정보
        functions = [
            ("벨리알", self.trigger_key, self.trigger_modifier, "is_running", self.home_toggle_belial),
            ("신화장난꾸러기", self.inv_trigger_key, self.inv_trigger_modifier, "inv_running", self.home_toggle_inv),
            ("아이템 버리기", self.discard_trigger_key, self.discard_trigger_modifier, "discard_running", self.home_toggle_discard),
            ("아이템 팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running", self.home_toggle_sell),
            ("아이템 먹기", self.consume_trigger_key, self.consume_trigger_modifier, "consume_running", self.home_toggle_consume),
        ]

        # Home 탭 UI 참조 저장
        self.home_switches = {}
        self.home_key_labels = {}
        self.home_status_labels = {}

        for name, key_var, mod_var, running_attr, toggle_func in functions:
            row = ctk.CTkFrame(func_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=5)

            # 기능 이름
            ctk.CTkLabel(row, text=name, width=100, anchor="w",
                         font=ctk.CTkFont(size=13)).pack(side="left")

            # 핫키 표시
            key_label = ctk.CTkLabel(row, text="", width=100, anchor="center",
                                     text_color="#ff9900", font=ctk.CTkFont(size=12, weight="bold"))
            key_label.pack(side="left", padx=5)
            self.home_key_labels[running_attr] = (key_label, key_var, mod_var)

            # 상태 표시
            status_label = ctk.CTkLabel(row, text="OFF", width=40, anchor="center",
                                        text_color="#666666", font=ctk.CTkFont(size=12))
            status_label.pack(side="left", padx=5)
            self.home_status_labels[running_attr] = status_label

            # ON/OFF 스위치
            switch = ctk.CTkSwitch(row, text="", width=40, command=toggle_func)
            switch.pack(side="right", padx=10)
            self.home_switches[running_attr] = switch

        # === 소리 알림 설정 ===
        sound_frame = ctk.CTkFrame(home_frame)
        sound_frame.pack(fill="x", pady=10, padx=10)

        sound_inner = ctk.CTkFrame(sound_frame, fg_color="transparent")
        sound_inner.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(sound_inner, text="🔔 소리 알림",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(sound_inner, text="(기능 ON/OFF 시 효과음)",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=10)
        ctk.CTkSwitch(sound_inner, text="", variable=self.sound_enabled, width=40).pack(side="right", padx=10)

        # === 오버레이 컨트롤 ===
        overlay_frame = ctk.CTkFrame(home_frame)
        overlay_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(overlay_frame, text="🖥️ 오버레이",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        overlay_btn_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        overlay_btn_frame.pack(fill="x", padx=10, pady=10)

        self.overlay_toggle_btn = ctk.CTkButton(overlay_btn_frame, text="오버레이 켜기",
                                                 command=self.toggle_overlay,
                                                 fg_color="#28a745", hover_color="#218838")
        self.overlay_toggle_btn.pack(side="left", expand=True, fill="x", padx=5)

        self.overlay_repos_btn = ctk.CTkButton(overlay_btn_frame, text="위치 재배치",
                                                command=self.start_overlay_reposition,
                                                fg_color="#6c757d", hover_color="#5a6268")
        self.overlay_repos_btn.pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkLabel(overlay_frame, text="재배치 모드에서 드래그 후 Enter로 고정",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)

        # 투명도 조절
        alpha_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        alpha_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(alpha_frame, text="투명도:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.alpha_label = ctk.CTkLabel(alpha_frame, text="85%", width=50, font=ctk.CTkFont(size=12))
        self.alpha_label.pack(side="right")
        ctk.CTkSlider(alpha_frame, from_=0.3, to=1.0, variable=self.overlay_alpha,
                      command=self.update_overlay_alpha).pack(side="right", fill="x", expand=True, padx=10)

        # === 설정 저장/불러오기/내보내기/가져오기 ===
        save_frame = ctk.CTkFrame(home_frame)
        save_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(save_frame, text="💾 설정 관리",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        # 기본 저장/불러오기
        save_btn_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        save_btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(save_btn_frame, text="저장",
                      command=self.save_config, fg_color="#007bff", hover_color="#0056b3").pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(save_btn_frame, text="불러오기",
                      command=self.load_config, fg_color="#17a2b8", hover_color="#138496").pack(side="left", expand=True, fill="x", padx=5)

        # 클랜원 공유용 내보내기/가져오기
        share_btn_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        share_btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(share_btn_frame, text="📤 파일로 내보내기",
                      command=self.export_config,
                      fg_color="#fd7e14", hover_color="#e96b00").pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(share_btn_frame, text="📥 파일 가져오기",
                      command=self.import_config,
                      fg_color="#6f42c1", hover_color="#5a32a3").pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkLabel(save_frame, text="💡 내보내기로 설정파일 저장 → 클랜원에게 공유!",
                     text_color="#00aaff", font=ctk.CTkFont(size=11)).pack(pady=5)

        # === 긴급 정지 핫키 ===
        emergency_frame = ctk.CTkFrame(home_frame)
        emergency_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(emergency_frame, text="🛑 긴급 정지",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        emergency_inner = ctk.CTkFrame(emergency_frame, fg_color="transparent")
        emergency_inner.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(emergency_inner, text="긴급 정지 키:",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self.emergency_key_display = ctk.CTkLabel(emergency_inner, text="ESC",
                                                   font=ctk.CTkFont(size=14, weight="bold"),
                                                   text_color="#ff4444")
        self.emergency_key_display.pack(side="left", padx=10)
        ctk.CTkButton(emergency_inner, text="변경", width=60,
                      command=self.change_emergency_key).pack(side="left")

        ctk.CTkLabel(emergency_frame, text="이 키를 누르면 모든 기능이 즉시 중지됩니다",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)

        # === 자동 시작 설정 ===
        auto_frame = ctk.CTkFrame(home_frame)
        auto_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(auto_frame, text="🚀 자동 시작",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        ctk.CTkLabel(auto_frame, text="프로그램 실행 시 자동으로 켜질 기능 선택",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack()

        auto_checks_frame = ctk.CTkFrame(auto_frame, fg_color="transparent")
        auto_checks_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkCheckBox(auto_checks_frame, text="벨리알", variable=self.auto_start_belial,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkCheckBox(auto_checks_frame, text="꾸러기", variable=self.auto_start_inv,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkCheckBox(auto_checks_frame, text="버리기", variable=self.auto_start_discard,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=10)

        auto_checks_frame2 = ctk.CTkFrame(auto_frame, fg_color="transparent")
        auto_checks_frame2.pack(fill="x", padx=10, pady=5)

        ctk.CTkCheckBox(auto_checks_frame2, text="팔기", variable=self.auto_start_sell,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        ctk.CTkCheckBox(auto_checks_frame2, text="먹기", variable=self.auto_start_consume,
                        font=ctk.CTkFont(size=12)).pack(side="left", padx=10)

        ctk.CTkLabel(auto_frame, text="💡 저장 후 다음 실행부터 적용됩니다",
                     text_color="#00aaff", font=ctk.CTkFont(size=11)).pack(pady=5)

        # === 월드 보스 타이머 ===
        boss_frame = ctk.CTkFrame(home_frame)
        boss_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(boss_frame, text="🌍 다음 월드 보스",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        boss_info_frame = ctk.CTkFrame(boss_frame, fg_color="transparent")
        boss_info_frame.pack(fill="x", padx=10, pady=5)

        self.home_boss_name = ctk.CTkLabel(boss_info_frame, text="로딩 중...",
                                            font=ctk.CTkFont(size=16, weight="bold"),
                                            text_color="#ff9900")
        self.home_boss_name.pack()

        self.home_boss_zone = ctk.CTkLabel(boss_info_frame, text="",
                                            font=ctk.CTkFont(size=12),
                                            text_color="gray")
        self.home_boss_zone.pack()

        self.home_boss_time = ctk.CTkLabel(boss_info_frame, text="",
                                            font=ctk.CTkFont(size=14),
                                            text_color="#00ff00")
        self.home_boss_time.pack(pady=5)

        ctk.CTkButton(boss_frame, text="🔄 새로고침", width=100,
                      command=self.refresh_world_boss,
                      fg_color="#17a2b8", hover_color="#138496").pack(pady=5)

        # === 오버레이 배경색 ===
        bg_color_frame = ctk.CTkFrame(overlay_frame, fg_color="transparent")
        bg_color_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(bg_color_frame, text="배경색:", font=ctk.CTkFont(size=12)).pack(side="left")
        self.bg_color_preview = ctk.CTkLabel(bg_color_frame, text="  ", width=30,
                                              fg_color=self.overlay_bg_color.get())
        self.bg_color_preview.pack(side="left", padx=5)
        ctk.CTkButton(bg_color_frame, text="변경", width=60,
                      command=self.change_overlay_bg_color).pack(side="left")

        # Home 탭 상태 업데이트 시작
        self.update_home_status()

    # === Home 탭 토글 함수들 ===
    def home_toggle_belial(self):
        """Home에서 벨리알 토글"""
        self.toggle_running()

    def home_toggle_inv(self):
        """Home에서 신화장난꾸러기 토글"""
        self.toggle_inv_running()

    def home_toggle_discard(self):
        """Home에서 아이템 버리기 토글"""
        self.toggle_discard_running()

    def home_toggle_sell(self):
        """Home에서 아이템 팔기 토글"""
        self.toggle_sell_running()

    def home_toggle_consume(self):
        """Home에서 아이템 먹기 토글"""
        self.toggle_consume_running()

    def change_emergency_key(self):
        """긴급 정지 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("긴급 정지 키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 긴급 정지 키를 누르세요...",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.emergency_stop_key.set(event.name)
                self.emergency_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def on_emergency_stop(self, event=None):
        """긴급 정지 - 모든 기능 즉시 중지"""
        # 모든 running 상태 강제 중지
        if self.is_running:
            self.is_running = False
            self.detection_active = False
            self.start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.status_label.configure(text="⏸️ 대기 중")
            self.status_frame.configure(fg_color="#1a1a2e")

        if self.inv_running:
            self.inv_running = False
            self.inv_cleanup_active = False
            self.inv_start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.inv_status_label.configure(text="⏸️ 대기 중")
            self.inv_status_frame.configure(fg_color="#1a1a2e")

        if self.discard_running:
            self.discard_running = False
            self.discard_active = False
            self.discard_start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.discard_status_label.configure(text="⏸️ 대기 중")
            self.discard_status_frame.configure(fg_color="#1a1a2e")

        if self.sell_running:
            self.sell_running = False
            self.sell_active = False
            self.sell_start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.sell_status_label.configure(text="⏸️ 대기 중")
            self.sell_status_frame.configure(fg_color="#1a1a2e")

        if self.consume_running:
            self.consume_running = False
            self.consume_active = False
            self.consume_start_btn.configure(text="▶️ 시작", fg_color="#17a2b8", hover_color="#138496")
            self.consume_status_label.configure(text="⏸️ 대기 중")
            self.consume_status_frame.configure(fg_color="#1a1a2e")

        self.play_sound(False)

    def apply_auto_start(self):
        """자동 시작 설정 적용"""
        if self.auto_start_belial.get() and not self.is_running:
            self.toggle_running()
        if self.auto_start_inv.get() and not self.inv_running:
            self.toggle_inv_running()
        if self.auto_start_discard.get() and not self.discard_running:
            self.toggle_discard_running()
        if self.auto_start_sell.get() and not self.sell_running:
            self.toggle_sell_running()
        if self.auto_start_consume.get() and not self.consume_running:
            self.toggle_consume_running()

    def start_all_functions(self):
        """모든 기능 시작"""
        if not self.is_running:
            self.toggle_running()
        if not self.inv_running:
            self.toggle_inv_running()
        if not self.discard_running:
            self.toggle_discard_running()
        if not self.sell_running:
            self.toggle_sell_running()
        if not self.consume_running:
            self.toggle_consume_running()
        self.play_sound(True)

    def stop_all_functions(self):
        """모든 기능 중지"""
        if self.is_running:
            self.toggle_running()
        if self.inv_running:
            self.toggle_inv_running()
        if self.discard_running:
            self.toggle_discard_running()
        if self.sell_running:
            self.toggle_sell_running()
        if self.consume_running:
            self.toggle_consume_running()
        self.play_sound(False)

    def play_sound(self, is_on):
        """소리 알림 재생"""
        if not self.sound_enabled.get():
            return
        try:
            if is_on:
                # ON: 높은 음 (띵!)
                winsound.Beep(880, 150)  # A5, 150ms
            else:
                # OFF: 낮은 음 (뚝)
                winsound.Beep(440, 100)  # A4, 100ms
        except:
            pass  # 소리 재생 실패 시 무시

    def export_config(self):
        """설정을 파일로 내보내기 (클랜원 공유용)"""
        file_path = filedialog.asksaveasfilename(
            title="설정 내보내기",
            defaultextension=".json",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
            initialfile="ColorClicker_설정.json"
        )
        if not file_path:
            return

        config = self.get_config_dict()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("완료", f"설정이 저장되었습니다!\n\n📁 {file_path}\n\n이 파일을 클랜원에게 보내주세요!")
        except Exception as e:
            messagebox.showerror("오류", f"내보내기 실패: {e}")

    def import_config(self):
        """설정 파일 가져오기"""
        file_path = filedialog.askopenfilename(
            title="설정 가져오기",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.apply_config_dict(config)
            messagebox.showinfo("완료", "설정을 불러왔습니다!\n\n각 탭에서 확인해주세요.")
        except Exception as e:
            messagebox.showerror("오류", f"가져오기 실패: {e}")

    def get_config_dict(self):
        """현재 설정을 딕셔너리로 반환"""
        return {
            'colors': self.colors,
            'exclude_colors': self.exclude_colors,
            'tolerance': self.tolerance.get(),
            'exclude_range': self.exclude_range.get(),
            'trigger_key': self.trigger_key.get(),
            'trigger_modifier': self.trigger_modifier.get(),
            'click_type': self.click_type.get(),
            'click_delay': self.click_delay.get(),
            'search_area': {
                'x1': self.search_x1.get(),
                'y1': self.search_y1.get(),
                'x2': self.search_x2.get(),
                'y2': self.search_y2.get()
            },
            'search_step': self.search_step.get(),
            'inventory': {
                'keep_color': self.inv_keep_color.get(),
                'tolerance': self.inv_tolerance.get(),
                'area': {
                    'x1': self.inv_x1.get(),
                    'y1': self.inv_y1.get(),
                    'x2': self.inv_x2.get(),
                    'y2': self.inv_y2.get()
                },
                'desc_area': {
                    'x1': self.inv_desc_x1.get(),
                    'y1': self.inv_desc_y1.get(),
                    'x2': self.inv_desc_x2.get(),
                    'y2': self.inv_desc_y2.get()
                },
                'cols': self.inv_cols.get(),
                'rows': self.inv_rows.get(),
                'trigger_key': self.inv_trigger_key.get(),
                'trigger_modifier': self.inv_trigger_modifier.get(),
                'move_duration': self.inv_move_duration.get(),
                'panel_delay': self.inv_panel_delay.get(),
                'space_delay': self.inv_space_delay.get(),
                'click_delay': self.inv_click_delay.get()
            },
            'discard': {
                'trigger_key': self.discard_trigger_key.get(),
                'trigger_modifier': self.discard_trigger_modifier.get(),
                'delay': self.discard_delay.get()
            },
            'sell': {
                'trigger_key': self.sell_trigger_key.get(),
                'trigger_modifier': self.sell_trigger_modifier.get(),
                'delay': self.sell_delay.get()
            },
            'consume': {
                'trigger_key': self.consume_trigger_key.get(),
                'trigger_modifier': self.consume_trigger_modifier.get(),
                'delay': self.consume_delay.get(),
                'input_type': self.consume_input_type.get()
            },
            'overlay': {
                'x': self.overlay_x.get(),
                'y': self.overlay_y.get(),
                'alpha': self.overlay_alpha.get()
            },
            'sound_enabled': self.sound_enabled.get(),
            'emergency_stop_key': self.emergency_stop_key.get(),
            'auto_start': {
                'belial': self.auto_start_belial.get(),
                'inv': self.auto_start_inv.get(),
                'discard': self.auto_start_discard.get(),
                'sell': self.auto_start_sell.get(),
                'consume': self.auto_start_consume.get()
            }
        }

    def apply_config_dict(self, config):
        """딕셔너리에서 설정 적용"""
        self.colors = config.get('colors', [])
        self.exclude_colors = config.get('exclude_colors', [])
        self.tolerance.set(config.get('tolerance', 10))
        self.exclude_range.set(config.get('exclude_range', 30))
        self.trigger_key.set(config.get('trigger_key', 'f1'))
        self.trigger_modifier.set(config.get('trigger_modifier', '없음'))
        self.click_type.set(config.get('click_type', 'right'))
        self.click_delay.set(config.get('click_delay', 0.1))

        area = config.get('search_area', {})
        self.search_x1.set(area.get('x1', 0))
        self.search_y1.set(area.get('y1', 0))
        self.search_x2.set(area.get('x2', 1920))
        self.search_y2.set(area.get('y2', 1080))
        self.search_step.set(config.get('search_step', 5))

        inv = config.get('inventory', {})
        if inv:
            self.inv_keep_color.set(inv.get('keep_color', '#FF6B00'))
            self.inv_tolerance.set(inv.get('tolerance', 15))
            inv_area = inv.get('area', {})
            self.inv_x1.set(inv_area.get('x1', 1725))
            self.inv_y1.set(inv_area.get('y1', 1009))
            self.inv_x2.set(inv_area.get('x2', 2550))
            self.inv_y2.set(inv_area.get('y2', 1340))
            desc_area = inv.get('desc_area', {})
            self.inv_desc_x1.set(desc_area.get('x1', 1144))
            self.inv_desc_y1.set(desc_area.get('y1', 428))
            self.inv_desc_x2.set(desc_area.get('x2', 1636))
            self.inv_desc_y2.set(desc_area.get('y2', 1147))
            self.inv_cols.set(inv.get('cols', 11))
            self.inv_rows.set(inv.get('rows', 3))
            self.inv_trigger_key.set(inv.get('trigger_key', 'f2'))
            self.inv_trigger_modifier.set(inv.get('trigger_modifier', '없음'))
            self.inv_move_duration.set(inv.get('move_duration', 0.15))
            self.inv_panel_delay.set(inv.get('panel_delay', 0.05))
            self.inv_space_delay.set(inv.get('space_delay', 0.05))
            self.inv_click_delay.set(inv.get('click_delay', 0.01))
            self.inv_key_display.configure(text=self.inv_trigger_key.get().upper())
            self.update_inv_color_preview()

        discard = config.get('discard', {})
        if discard:
            self.discard_trigger_key.set(discard.get('trigger_key', 'f3'))
            self.discard_trigger_modifier.set(discard.get('trigger_modifier', '없음'))
            self.discard_delay.set(discard.get('delay', 0.01))
            self.discard_key_display.configure(text=self.discard_trigger_key.get().upper())

        sell = config.get('sell', {})
        if sell:
            self.sell_trigger_key.set(sell.get('trigger_key', 'f4'))
            self.sell_trigger_modifier.set(sell.get('trigger_modifier', '없음'))
            self.sell_delay.set(sell.get('delay', 0.01))
            self.sell_key_display.configure(text=self.sell_trigger_key.get().upper())

        consume = config.get('consume', {})
        if consume:
            self.consume_trigger_key.set(consume.get('trigger_key', 'f5'))
            self.consume_trigger_modifier.set(consume.get('trigger_modifier', '없음'))
            self.consume_delay.set(consume.get('delay', 0.01))
            self.consume_input_type.set(consume.get('input_type', 'F키'))
            self.consume_key_display.configure(text=self.consume_trigger_key.get().upper())

        overlay = config.get('overlay', {})
        if overlay:
            self.overlay_x.set(overlay.get('x', 100))
            self.overlay_y.set(overlay.get('y', 100))
            self.overlay_alpha.set(overlay.get('alpha', 0.85))
            self.alpha_label.configure(text=f"{int(self.overlay_alpha.get() * 100)}%")

        self.sound_enabled.set(config.get('sound_enabled', True))

        self.emergency_stop_key.set(config.get('emergency_stop_key', 'esc'))
        self.emergency_key_display.configure(text=self.emergency_stop_key.get().upper())

        auto_start = config.get('auto_start', {})
        if auto_start:
            self.auto_start_belial.set(auto_start.get('belial', False))
            self.auto_start_inv.set(auto_start.get('inv', False))
            self.auto_start_discard.set(auto_start.get('discard', False))
            self.auto_start_sell.set(auto_start.get('sell', False))
            self.auto_start_consume.set(auto_start.get('consume', False))

        self.key_display.configure(text=self.trigger_key.get().upper())
        self.update_color_list()
        self.update_exclude_list()
        self.setup_hotkey()

    def create_help_tab(self):
        """사용법 탭 UI 생성 (50대 눈높이)"""
        help_frame = ctk.CTkScrollableFrame(self.tabview.tab("사용법"), width=500, height=850)
        help_frame.pack(pady=5, padx=5, fill="both", expand=True)

        # === 헤더 ===
        ctk.CTkLabel(help_frame, text="📖 사용법 안내",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=15)
        ctk.CTkLabel(help_frame, text="각 기능별 간단한 설명입니다",
                     text_color="gray", font=ctk.CTkFont(size=14)).pack()

        # === 기본 사용법 ===
        basic_frame = ctk.CTkFrame(help_frame)
        basic_frame.pack(fill="x", pady=15, padx=10)

        ctk.CTkLabel(basic_frame, text="🎯 기본 사용법",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        basic_text = """
1. 각 탭에서 필요한 설정을 합니다
2. Home 탭에서 [전체 시작] 버튼을 누릅니다
3. 게임에서 핫키를 눌러 기능을 사용합니다
4. 끝나면 [전체 중지] 버튼을 누릅니다

💡 핫키를 누르면 기능이 켜지고,
   다시 누르면 꺼집니다!
"""
        ctk.CTkLabel(basic_frame, text=basic_text, justify="left",
                     font=ctk.CTkFont(size=14)).pack(padx=15, pady=10)

        # === 벨리알 탭 설명 ===
        belial_frame = ctk.CTkFrame(help_frame)
        belial_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(belial_frame, text="👁️ 벨리알 (아이템 줍기)",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#ffcc00").pack(pady=10)

        belial_text = """
✅ 화면에서 특정 색상을 찾아 자동 클릭

사용법:
1. [화면 추출] 버튼으로 원하는 아이템 색상 등록
2. 검색 영역 설정 (화면 전체 또는 일부)
3. [시작] 버튼 → 핫키로 ON/OFF

⚠️ 제외 색상: 클릭하면 안 되는 색상 등록
"""
        ctk.CTkLabel(belial_frame, text=belial_text, justify="left",
                     font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)

        # === 신화장난꾸러기 설명 ===
        inv_frame = ctk.CTkFrame(help_frame)
        inv_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(inv_frame, text="✨ 신화장난꾸러기 (인벤 정리)",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#ff6b00").pack(pady=10)

        inv_text = """
✅ 인벤토리에서 특정 색상만 즐겨찾기 등록

사용법:
1. 보존할 색상 설정 (신화 장난꾸러기 색상)
2. 인벤토리 영역 설정
3. [시작] 버튼 → 핫키로 실행

💡 스페이스바로 즐겨찾기 등록됩니다
"""
        ctk.CTkLabel(inv_frame, text=inv_text, justify="left",
                     font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)

        # === 버리기/팔기/먹기 설명 ===
        other_frame = ctk.CTkFrame(help_frame)
        other_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(other_frame, text="🔧 기타 기능",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#00aaff").pack(pady=10)

        other_text = """
🗑️ 아이템 버리기: Ctrl+클릭 반복 (인벤에서)
💰 아이템 팔기: 우클릭 반복 (상점에서)
🍖 아이템 먹기: 선택한 키 반복 (마우스 위치)

💡 마우스를 원하는 위치에 놓고 핫키 누르기!
   다시 핫키를 누르면 멈춤
"""
        ctk.CTkLabel(other_frame, text=other_text, justify="left",
                     font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)

        # === 설정 공유 설명 ===
        share_frame = ctk.CTkFrame(help_frame)
        share_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(share_frame, text="📤 클랜원에게 설정 공유하기",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#fd7e14").pack(pady=10)

        share_text = """
1. Home 탭에서 [파일로 내보내기] 클릭
2. 저장된 .json 파일을 카톡으로 전송
3. 받은 사람은 [파일 가져오기]로 적용

💡 한 번 설정하면 모두가 같은 설정 사용!
"""
        ctk.CTkLabel(share_frame, text=share_text, justify="left",
                     font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)

        # === 문제 해결 ===
        trouble_frame = ctk.CTkFrame(help_frame)
        trouble_frame.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(trouble_frame, text="❓ 문제 해결",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#dc3545").pack(pady=10)

        trouble_text = """
🔸 핫키가 안 먹어요
   → 프로그램을 관리자 권한으로 실행

🔸 색상 인식이 안 돼요
   → 허용 오차를 10~20으로 높여보세요

🔸 클릭이 너무 느려요/빨라요
   → 딜레이 값을 조절해보세요

🔸 게임 프레임이 떨어져요
   → 오버레이를 끄거나 검색 영역을 줄여보세요
"""
        ctk.CTkLabel(trouble_frame, text=trouble_text, justify="left",
                     font=ctk.CTkFont(size=13)).pack(padx=15, pady=10)

    def update_home_status(self):
        """Home 탭 상태 실시간 업데이트"""
        # 각 기능 상태 업데이트
        states = {
            "is_running": self.is_running,
            "inv_running": self.inv_running,
            "discard_running": self.discard_running,
            "sell_running": self.sell_running,
            "consume_running": self.consume_running
        }

        for attr, is_on in states.items():
            # 상태 라벨 업데이트
            if attr in self.home_status_labels:
                label = self.home_status_labels[attr]
                if is_on:
                    label.configure(text="ON", text_color="#00FF00")
                else:
                    label.configure(text="OFF", text_color="#666666")

            # 스위치 상태 업데이트 (UI만, 콜백 없이)
            if attr in self.home_switches:
                switch = self.home_switches[attr]
                if is_on and not switch.get():
                    switch.select()
                elif not is_on and switch.get():
                    switch.deselect()

            # 핫키 라벨 업데이트
            if attr in self.home_key_labels:
                key_label, key_var, mod_var = self.home_key_labels[attr]
                mod = mod_var.get()
                key = key_var.get().upper()
                if mod != "없음":
                    key_label.configure(text=f"{mod}+{key}")
                else:
                    key_label.configure(text=key)

        # 500ms 후 다시 업데이트
        self.after(500, self.update_home_status)

    # === 오버레이 관련 함수들 ===
    def toggle_overlay(self):
        """오버레이 켜기/끄기"""
        if self.overlay_window is None:
            self.create_overlay_window()
            self.overlay_toggle_btn.configure(text="오버레이 끄기", fg_color="#dc3545", hover_color="#c82333")
        else:
            self.destroy_overlay()
            self.overlay_toggle_btn.configure(text="오버레이 켜기", fg_color="#28a745", hover_color="#218838")

    def update_overlay_alpha(self, value):
        """오버레이 투명도 실시간 업데이트"""
        alpha = float(value)
        self.alpha_label.configure(text=f"{int(alpha * 100)}%")
        if self.overlay_window:
            try:
                self.overlay_window.attributes('-alpha', alpha)
            except:
                pass

    def create_overlay_window(self):
        """오버레이 창 생성"""
        bg_color = self.overlay_bg_color.get()

        self.overlay_window = tk.Toplevel(self)
        self.overlay_window.overrideredirect(True)  # 타이틀바 제거
        self.overlay_window.attributes('-topmost', True)  # 항상 위에
        self.overlay_window.attributes('-alpha', self.overlay_alpha.get())  # 투명도

        # 크기와 위치 (월드보스 섹션 추가로 높이 증가)
        width = 180
        height = 175
        x = self.overlay_x.get()
        y = self.overlay_y.get()
        self.overlay_window.geometry(f'{width}x{height}+{x}+{y}')

        # 배경 (커스텀 색상 적용)
        self.overlay_window.configure(bg=bg_color)

        # 메인 프레임
        main_frame = tk.Frame(self.overlay_window, bg=bg_color, padx=5, pady=5)
        main_frame.pack(fill='both', expand=True)

        # 타이틀
        title = tk.Label(main_frame, text="Color Clicker", bg=bg_color, fg='#00aaff',
                         font=('맑은 고딕', 9, 'bold'))
        title.pack(pady=(0, 5))

        # 각 기능 상태
        functions = [
            ("벨리알", self.trigger_key, self.trigger_modifier, "is_running"),
            ("꾸러기", self.inv_trigger_key, self.inv_trigger_modifier, "inv_running"),
            ("버리기", self.discard_trigger_key, self.discard_trigger_modifier, "discard_running"),
            ("팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running"),
            ("먹기", self.consume_trigger_key, self.consume_trigger_modifier, "consume_running"),
        ]

        self.overlay_labels = {}

        for name, key_var, mod_var, attr in functions:
            row = tk.Frame(main_frame, bg=bg_color)
            row.pack(fill='x', pady=1)

            # 기능명
            tk.Label(row, text=name, bg=bg_color, fg='#ffffff', width=5, anchor='w',
                     font=('맑은 고딕', 9)).pack(side='left')

            # 핫키
            mod = mod_var.get()
            key = key_var.get().upper()
            hotkey_text = f"{mod}+{key}" if mod != "없음" else key
            tk.Label(row, text=hotkey_text, bg=bg_color, fg='#ff9900', width=9, anchor='center',
                     font=('맑은 고딕', 8)).pack(side='left')

            # 상태 (●)
            status_label = tk.Label(row, text="● OFF", bg=bg_color, fg='#666666', width=6, anchor='e',
                                    font=('맑은 고딕', 9))
            status_label.pack(side='right')
            self.overlay_labels[attr] = status_label

        # === 월드 보스 섹션 ===
        separator = tk.Frame(main_frame, bg='#444444', height=1)
        separator.pack(fill='x', pady=3)

        boss_row = tk.Frame(main_frame, bg=bg_color)
        boss_row.pack(fill='x', pady=1)

        tk.Label(boss_row, text="🌍", bg=bg_color, fg='#ffffff',
                 font=('맑은 고딕', 9)).pack(side='left')

        self.world_boss_label = tk.Label(boss_row, text="로딩...", bg=bg_color, fg='#ff9900',
                                          font=('맑은 고딕', 9))
        self.world_boss_label.pack(side='left', padx=3)

        # 오버레이 상태 업데이트 시작
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

        for attr, is_on in states.items():
            if attr in self.overlay_labels:
                label = self.overlay_labels[attr]
                if is_on:
                    label.configure(text="● ON", fg='#00FF00')
                else:
                    label.configure(text="● OFF", fg='#666666')

        # 200ms 후 다시 업데이트
        if self.overlay_window:
            self.overlay_window.after(200, self.update_overlay)

    def start_overlay_reposition(self):
        """오버레이 재배치 모드 시작"""
        if self.overlay_window is None:
            messagebox.showinfo("알림", "먼저 오버레이를 켜주세요!")
            return

        self.overlay_reposition_mode = True
        self.overlay_repos_btn.configure(text="Enter로 고정", fg_color="#ffc107", hover_color="#e0a800")

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
        self.overlay_repos_btn.configure(text="위치 재배치", fg_color="#6c757d", hover_color="#5a6268")

        # 이벤트 바인딩 해제
        if self.overlay_window:
            self.overlay_window.unbind('<Button-1>')
            self.overlay_window.unbind('<B1-Motion>')
            self.overlay_window.unbind('<Return>')
            self.overlay_window.unbind('<Escape>')

            # 현재 위치 저장
            self.overlay_x.set(self.overlay_window.winfo_x())
            self.overlay_y.set(self.overlay_window.winfo_y())

    def toggle_consume_running(self):
        """아이템 먹기 시작/중지"""
        self.consume_running = not self.consume_running
        if self.consume_running:
            self.consume_start_btn.configure(text="⏹️ 중지", fg_color="#6c757d", hover_color="#5a6268")
            self.consume_status_label.configure(text=f"🔴 [{self.consume_trigger_key.get().upper()}] 키로 시작")
            self.consume_status_frame.configure(fg_color="#3d3d1a")
        else:
            self.consume_active = False
            self.consume_start_btn.configure(text="▶️ 시작", fg_color="#17a2b8", hover_color="#138496")
            self.consume_status_label.configure(text="⏸️ 대기 중")
            self.consume_status_frame.configure(fg_color="#1a1a2e")
            self.consume_progress_label.configure(text="")

    def on_consume_trigger_key(self, event):
        """아이템 먹기 트리거 키 핸들러"""
        import time as time_module

        if not self.consume_running:
            return

        # 조합키 체크
        if not self.check_modifier(self.consume_trigger_modifier.get()):
            return

        # 디바운스
        current_time = time_module.time()
        if current_time - self.consume_last_trigger_time < 0.3:
            return
        self.consume_last_trigger_time = current_time

        if self.consume_active:
            self.consume_active = False
            self.after(0, lambda: self.consume_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.consume_status_frame.configure(fg_color="#3d3d1a"))
        else:
            self.consume_active = True
            self.run_fast_consume()

    def run_fast_consume(self):
        """초고속 아이템 먹기 - 현재 마우스 위치에서 선택한 입력 반복"""
        def consume_loop():
            import time
            delay = self.consume_delay.get()
            input_type = self.consume_input_type.get()

            self.after(0, lambda: self.consume_status_label.configure(text=f"🍖 먹는 중... ({input_type})"))
            self.after(0, lambda: self.consume_status_frame.configure(fg_color="#1a3d3d"))

            consumed = 0
            while self.consume_active:
                if input_type == "F키":
                    # F 키 입력 (0x46 = F)
                    win32api.keybd_event(0x46, 0, 0, 0)
                    win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)
                elif input_type == "우클릭":
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                elif input_type == "왼클릭":
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

                consumed += 1

                if delay > 0.001:
                    time.sleep(delay)

                # 진행상황 (100개마다)
                if consumed % 100 == 0:
                    self.after(0, lambda c=consumed: self.consume_progress_label.configure(
                        text=f"{c}회"))

            self.after(0, lambda: self.consume_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.consume_status_frame.configure(fg_color="#1a1a2e"))
            self.after(0, lambda c=consumed: self.consume_progress_label.configure(
                text=f"총 {c}회 입력"))

        threading.Thread(target=consume_loop, daemon=True).start()

    def update_inv_color_preview(self, event=None):
        """인벤토리 탭 색상 미리보기 업데이트"""
        try:
            color = self.inv_keep_color.get()
            if self.validate_hex(color):
                self.inv_color_preview.configure(fg_color=color)
        except:
            pass

    def inv_pick_color(self):
        """화면에서 보존할 색상 추출"""
        self.picker_mode = True
        self.picker_target = "inv_keep"
        self.picker_status.configure(text="보존할 색상을 클릭하세요 (ESC 취소)")

        def on_click():
            if self.picker_mode and self.picker_target == "inv_keep":
                x, y = pyautogui.position()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color).upper()
                    self.inv_keep_color.set(hex_color)
                    self.update_inv_color_preview()
                    self.picker_status.configure(text=f"✅ 보존 색상: {hex_color}")
                except Exception as e:
                    self.picker_status.configure(text=f"오류: {e}")
                self.picker_mode = False

        def wait_click():
            import time
            while self.picker_mode:
                if keyboard.is_pressed('esc'):
                    self.picker_mode = False
                    self.after(0, lambda: self.picker_status.configure(text="취소됨"))
                    break
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    time.sleep(0.1)
                    self.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_click, daemon=True).start()

    def change_inv_trigger_key(self):
        """인벤토리 정리 트리거 키 변경"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...\n(마우스 4/5번 버튼도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.inv_trigger_key.set(event.name)
                self.inv_key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def poll_mouse():
            import time
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.inv_trigger_key.set("mouse4"))
                    self.after(0, lambda: self.inv_key_display.configure(text="MOUSE4"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:
                    dialog_active[0] = False
                    self.after(0, lambda: self.inv_trigger_key.set("mouse5"))
                    self.after(0, lambda: self.inv_key_display.configure(text="MOUSE5"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def toggle_inv_running(self):
        """인벤토리 정리 시작/중지"""
        self.inv_running = not self.inv_running
        if self.inv_running:
            self.inv_start_btn.configure(text="⏹️ 중지", fg_color="#dc3545", hover_color="#c82333")
            self.inv_status_label.configure(text=f"🔴 [{self.inv_trigger_key.get().upper()}] 키로 시작")
            self.inv_status_frame.configure(fg_color="#3d1a1a")
        else:
            self.inv_start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.inv_status_label.configure(text="⏸️ 대기 중")
            self.inv_status_frame.configure(fg_color="#1a1a2e")
            self.inv_progress_label.configure(text="")

    def select_inv_area(self):
        """인벤토리 영역 드래그 선택"""
        self.inv_status_label.configure(text="🖱️ 드래그로 영역 선택...")

        overlay = tk.Toplevel(self)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline='red', width=3, fill='blue', stipple='gray50')

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                canvas.coords(rect_id, x1, y1, event.x, event.y)

        def on_release(event):
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.inv_x1.set(x1)
                self.inv_y1.set(y1)
                self.inv_x2.set(x2)
                self.inv_y2.set(y2)

                self.inv_status_label.configure(text=f"✅ 영역 설정 완료")
                overlay.destroy()
                self.show_inv_area_overlay()

        def on_escape(event):
            self.inv_status_label.configure(text="⏸️ 대기 중")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def show_inv_area_overlay(self):
        """인벤토리 영역 오버레이 토글"""
        if hasattr(self, 'inv_area_overlay') and self.inv_area_overlay:
            try:
                self.inv_area_overlay.destroy()
            except:
                pass
            self.inv_area_overlay = None
            return

        x1, y1 = self.inv_x1.get(), self.inv_y1.get()
        x2, y2 = self.inv_x2.get(), self.inv_y2.get()
        width, height = x2 - x1, y2 - y1

        if width <= 0 or height <= 0:
            return

        self.inv_area_overlay = tk.Toplevel(self)
        self.inv_area_overlay.overrideredirect(True)
        self.inv_area_overlay.attributes('-topmost', True)
        self.inv_area_overlay.attributes('-transparentcolor', 'white')
        self.inv_area_overlay.geometry(f'{width}x{height}+{x1}+{y1}')

        canvas = tk.Canvas(self.inv_area_overlay, width=width, height=height, bg='white', highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(2, 2, width-2, height-2, outline='#ff6600', width=3)
        canvas.bind('<Button-1>', lambda e: self.show_inv_area_overlay())

    def select_desc_area(self):
        """설명 패널 영역 드래그 선택"""
        self.inv_status_label.configure(text="🖱️ 설명 패널 영역 드래그...")

        overlay = tk.Toplevel(self)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline='green', width=3, fill='green', stipple='gray50')

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                canvas.coords(rect_id, x1, y1, event.x, event.y)

        def on_release(event):
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.inv_desc_x1.set(x1)
                self.inv_desc_y1.set(y1)
                self.inv_desc_x2.set(x2)
                self.inv_desc_y2.set(y2)

                self.inv_status_label.configure(text=f"✅ 설명 패널 영역 설정 완료")
                overlay.destroy()

        def on_escape(event):
            self.inv_status_label.configure(text="⏸️ 대기 중")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def test_inv_grid(self):
        """그리드 좌표 테스트 - 각 셀 위치로 마우스 이동 + 설명 패널 영역 표시"""
        def move_test():
            import time
            positions = self.get_inventory_positions()

            # 인벤토리 슬롯 간격 계산
            inv_x1 = self.inv_x1.get()
            cols = self.inv_cols.get()
            inv_width = self.inv_x2.get() - inv_x1
            cell_w = inv_width / cols

            # 설명 패널 기본 좌표
            desc_x1 = self.inv_desc_x1.get()
            desc_y1 = self.inv_desc_y1.get()
            desc_x2 = self.inv_desc_x2.get()
            desc_y2 = self.inv_desc_y2.get()
            desc_width = desc_x2 - desc_x1
            desc_height = desc_y2 - desc_y1

            for i, (x, y, col) in enumerate(positions):
                if self.inv_running:
                    break

                # 해당 슬롯의 설명 패널 X 오프셋 계산
                x_offset = int(col * cell_w)
                current_desc_x1 = desc_x1 + x_offset

                # 설명 패널 오버레이 표시
                self.after(0, lambda dx1=current_desc_x1, dy1=desc_y1, dw=desc_width, dh=desc_height:
                           self.show_desc_overlay(dx1, dy1, dw, dh))

                pyautogui.moveTo(x, y, duration=0.1)
                self.after(0, lambda idx=i, dx1=current_desc_x1: self.inv_progress_label.configure(
                    text=f"테스트: {idx+1}/{len(positions)} | 설명패널 X: {dx1}"))
                time.sleep(0.5)

                # 오버레이 제거
                self.after(0, self.hide_desc_overlay)

            self.after(0, lambda: self.inv_progress_label.configure(text="테스트 완료!"))

        threading.Thread(target=move_test, daemon=True).start()

    def show_desc_overlay(self, x, y, width, height):
        """설명 패널 오버레이 표시"""
        self.hide_desc_overlay()  # 기존 오버레이 제거

        self.desc_overlay = tk.Toplevel(self)
        self.desc_overlay.overrideredirect(True)
        self.desc_overlay.attributes('-topmost', True)
        self.desc_overlay.attributes('-transparentcolor', 'white')
        self.desc_overlay.geometry(f'{width}x{height}+{x}+{y}')

        canvas = tk.Canvas(self.desc_overlay, width=width, height=height, bg='white', highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(2, 2, width-2, height-2, outline='#00ff00', width=3)

    def hide_desc_overlay(self):
        """설명 패널 오버레이 숨기기"""
        if hasattr(self, 'desc_overlay') and self.desc_overlay:
            try:
                self.desc_overlay.destroy()
            except:
                pass
            self.desc_overlay = None

    def get_inventory_positions(self):
        """인벤토리 셀 좌표 목록 반환 (뱀패턴: 123,654,789) - (x, y, col) 튜플"""
        positions = []
        x1, y1 = self.inv_x1.get(), self.inv_y1.get()
        x2, y2 = self.inv_x2.get(), self.inv_y2.get()
        cols = self.inv_cols.get()
        rows = self.inv_rows.get()

        width = x2 - x1
        height = y2 - y1
        cell_w = width / cols
        cell_h = height / rows

        for row in range(rows):
            if row % 2 == 0:
                # 짝수 줄: 왼쪽 → 오른쪽
                col_range = range(cols)
            else:
                # 홀수 줄: 오른쪽 → 왼쪽
                col_range = range(cols - 1, -1, -1)

            for col in col_range:
                x = int(x1 + col * cell_w + cell_w / 2)
                y = int(y1 + row * cell_h + cell_h / 2)
                positions.append((x, y, col))

        return positions

    def smooth_move_to(self, target_x, target_y, duration=0.15):
        """초부드러운 마우스 이동 - 144fps급"""
        import time

        start_x, start_y = win32api.GetCursorPos()

        # 144fps급 부드러움
        steps = max(20, int(duration * 144))

        for i in range(1, steps + 1):
            t = i / steps
            # ease-in-out 커브 (시작/끝 부드럽게)
            t = t * t * (3 - 2 * t)

            x = int(start_x + (target_x - start_x) * t)
            y = int(start_y + (target_y - start_y) * t)
            win32api.SetCursorPos((x, y))
            time.sleep(duration / steps)

    def run_inventory_cleanup(self):
        """인벤토리 정리 - 1단계: 스캔+즐겨찾기, 2단계: 나머지 버리기"""
        def cleanup_loop():
            import time
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

            # 인벤토리 영역 및 설명 패널 정보
            inv_x1 = self.inv_x1.get()
            inv_width = self.inv_x2.get() - inv_x1
            cell_w = inv_width / cols

            # 설명 패널 기본 좌표 (첫 번째 슬롯 기준)
            desc_x1 = self.inv_desc_x1.get()
            desc_y1 = self.inv_desc_y1.get()
            desc_x2 = self.inv_desc_x2.get()
            desc_y2 = self.inv_desc_y2.get()
            desc_width = desc_x2 - desc_x1
            desc_height = desc_y2 - desc_y1

            # 딜레이 값 가져오기
            move_duration = self.inv_move_duration.get()
            panel_delay = self.inv_panel_delay.get()
            space_delay = self.inv_space_delay.get()
            click_delay = self.inv_click_delay.get()

            # 즐겨찾기된 슬롯 인덱스 저장
            favorite_slots = set()

            # ========== 1단계: 스캔 + 즐겨찾기 ==========
            self.after(0, lambda: self.inv_status_label.configure(text="🔍 1단계: 스캔 중..."))
            self.after(0, lambda: self.inv_status_frame.configure(fg_color="#1a3d1a"))

            # 첫 번째 슬롯에서 0.3초 호버링 (게임 초기 인식)
            if positions:
                first_x, first_y, first_col = positions[0]
                self.smooth_move_to(first_x, first_y, duration=move_duration)
                time.sleep(0.3)

            with mss.mss() as sct:
                for i, (x, y, col) in enumerate(positions):
                    if not self.inv_cleanup_active:
                        break

                    # 부드럽게 슬롯으로 이동 (끊김 없이)
                    self.smooth_move_to(x, y, duration=move_duration)
                    time.sleep(panel_delay)  # 설명 패널 대기

                    # 해당 슬롯의 설명 패널 X 오프셋 계산
                    x_offset = int(col * cell_w)
                    current_desc_x1 = desc_x1 + x_offset

                    try:
                        # 설명 패널 영역 캡처
                        monitor = {
                            "top": desc_y1,
                            "left": current_desc_x1,
                            "width": desc_width,
                            "height": desc_height
                        }
                        screenshot = sct.grab(monitor)
                        pixels = screenshot.raw

                        # 신화장난꾸러기 색상 찾기 (numpy 초고속 벡터 스캔)
                        img_array = np.frombuffer(screenshot.raw, dtype=np.uint8)
                        img_array = img_array.reshape((desc_height, desc_width, 4))

                        # BGR 채널 분리 (BGRA에서)
                        b_diff = np.abs(img_array[:, :, 0].astype(np.int16) - target_b)
                        g_diff = np.abs(img_array[:, :, 1].astype(np.int16) - target_g)
                        r_diff = np.abs(img_array[:, :, 2].astype(np.int16) - target_r)

                        # 색상 매칭 (한번에 전체 비교)
                        found_keep_color = np.any((r_diff <= tol) & (g_diff <= tol) & (b_diff <= tol))

                        # 신화장난꾸러기 발견! 스페이스바 2번 (즐겨찾기)
                        if found_keep_color:
                            favorite_slots.add(i)
                            keyboard.press_and_release('space')
                            time.sleep(space_delay)
                            keyboard.press_and_release('space')
                            time.sleep(space_delay)
                            self.after(0, lambda idx=i: self.inv_progress_label.configure(
                                text=f"⭐ 즐겨찾기: 슬롯 {idx+1}"))

                    except Exception as e:
                        print(f"Scan error: {e}")

                    # 진행 상황 업데이트
                    if i % 3 == 0:
                        self.after(0, lambda idx=i, t=total, f=len(favorite_slots): self.inv_progress_label.configure(
                            text=f"스캔: {idx+1}/{t} (즐겨찾기: {f})"))

            if not self.inv_cleanup_active:
                self.after(0, lambda: self.inv_status_label.configure(text="⏹️ 중지됨"))
                self.inv_cleanup_active = False
                return

            # ========== 2단계: 즐겨찾기 안된 것들 빠르게 버리기 ==========
            self.after(0, lambda f=len(favorite_slots): self.inv_status_label.configure(
                text=f"🗑️ 2단계: 버리기... (보존: {f}개)"))

            discarded = 0
            for i, (x, y, col) in enumerate(positions):
                if not self.inv_cleanup_active:
                    break

                # 즐겨찾기된 슬롯은 스킵
                if i in favorite_slots:
                    continue

                # 빠르게 이동 (텔레포트)
                win32api.SetCursorPos((x, y))
                time.sleep(0.02)

                # Ctrl + 클릭으로 버리기
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
                discarded += 1
                time.sleep(click_delay)

                if i % 5 == 0:
                    self.after(0, lambda d=discarded: self.inv_progress_label.configure(
                        text=f"버리는 중... ({d}개)"))

            self.inv_cleanup_active = False
            self.after(0, lambda: self.inv_status_label.configure(text="✅ 완료!"))
            self.after(0, lambda: self.inv_status_frame.configure(fg_color="#1a1a2e"))
            self.after(0, lambda f=len(favorite_slots), d=discarded: self.inv_progress_label.configure(
                text=f"⭐ 보존: {f}개 | 🗑️ 버림: {d}개"))

        threading.Thread(target=cleanup_loop, daemon=True).start()

    def update_mouse_pos(self):
        try:
            x, y = pyautogui.position()
            self.coord_label.configure(text=f"마우스: ({x}, {y})")

            if self.picker_mode:
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
                    self.picker_status.configure(text=f"현재 색상: {hex_color} - 클릭하여 추가")
                except:
                    pass
        except:
            pass
        self.after(50, self.update_mouse_pos)

    def add_color_manual(self):
        dialog = ctk.CTkInputDialog(text="HEX 색상 코드 입력 (예: #FF0000):", title="색상 추가")
        hex_color = dialog.get_input()
        if hex_color and self.validate_hex(hex_color):
            self.colors.append((hex_color.upper(), hex_color.upper()))
            self.update_color_list()

    def add_color_picker(self):
        color = colorchooser.askcolor(title="색상 선택")
        if color[1]:
            hex_color = color[1].upper()
            self.colors.append((hex_color, hex_color))
            self.update_color_list()

    def start_screen_picker(self):
        self.picker_mode = True
        self.picker_target = "colors"
        self.picker_status.configure(text="화면에서 원하는 색상을 클릭하세요 (ESC 취소)")

        def on_click():
            if self.picker_mode and self.picker_target == "colors":
                x, y = pyautogui.position()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color).upper()
                    self.colors.append((hex_color, f"{hex_color} @({x},{y})"))
                    self.update_color_list()
                    self.picker_status.configure(text=f"✅ 추가됨: {hex_color}")
                except Exception as e:
                    self.picker_status.configure(text=f"오류: {e}")
                self.picker_mode = False

        def wait_click():
            import time
            while self.picker_mode:
                if keyboard.is_pressed('esc'):
                    self.picker_mode = False
                    self.after(0, lambda: self.picker_status.configure(text="취소됨"))
                    break
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    time.sleep(0.1)
                    self.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_click, daemon=True).start()

    def remove_color(self):
        selection = self.color_listbox.curselection()
        if selection:
            del self.colors[selection[0]]
            self.update_color_list()

    def update_color_list(self):
        self.color_listbox.delete(0, tk.END)
        for hex_color, name in self.colors:
            self.color_listbox.insert(tk.END, f"  {hex_color} - {name}")

    def add_exclude_manual(self):
        dialog = ctk.CTkInputDialog(text="HEX 색상 코드 입력 (예: #FF0000):", title="제외 색상 추가")
        hex_color = dialog.get_input()
        if hex_color and self.validate_hex(hex_color):
            self.exclude_colors.append((hex_color.upper(), hex_color.upper()))
            self.update_exclude_list()

    def start_exclude_picker(self):
        self.picker_mode = True
        self.picker_target = "exclude"
        self.picker_status.configure(text="제외할 색상을 클릭하세요 (ESC 취소)")

        def on_click():
            if self.picker_mode and self.picker_target == "exclude":
                x, y = pyautogui.position()
                try:
                    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))
                    color = img.getpixel((0, 0))
                    hex_color = '#{:02x}{:02x}{:02x}'.format(*color).upper()
                    self.exclude_colors.append((hex_color, f"{hex_color} @({x},{y})"))
                    self.update_exclude_list()
                    self.picker_status.configure(text=f"✅ 제외 색상 추가됨: {hex_color}")
                except Exception as e:
                    self.picker_status.configure(text=f"오류: {e}")
                self.picker_mode = False

        def wait_click():
            import time
            while self.picker_mode:
                if keyboard.is_pressed('esc'):
                    self.picker_mode = False
                    self.after(0, lambda: self.picker_status.configure(text="취소됨"))
                    break
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
                    time.sleep(0.1)
                    self.after(0, on_click)
                    break
                time.sleep(0.01)

        threading.Thread(target=wait_click, daemon=True).start()

    def remove_exclude_color(self):
        selection = self.exclude_listbox.curselection()
        if selection:
            del self.exclude_colors[selection[0]]
            self.update_exclude_list()

    def update_exclude_list(self):
        self.exclude_listbox.delete(0, tk.END)
        for hex_color, name in self.exclude_colors:
            self.exclude_listbox.insert(tk.END, f"  {hex_color} - {name}")

    def validate_hex(self, hex_color):
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
        self.status_label.configure(text="🖱️ 드래그로 영역 선택...")

        overlay = tk.Toplevel(self)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.attributes('-alpha', 0.3)
        overlay.configure(bg='gray')
        overlay.config(cursor='cross')

        canvas = tk.Canvas(overlay, highlightthickness=0, bg='gray')
        canvas.pack(fill=tk.BOTH, expand=True)

        start_x, start_y = None, None
        rect_id = None

        def on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x_root, event.y_root
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                               outline='red', width=3, fill='blue', stipple='gray50')

        def on_drag(event):
            nonlocal rect_id
            if start_x is not None and rect_id:
                x1 = start_x - overlay.winfo_rootx()
                y1 = start_y - overlay.winfo_rooty()
                canvas.coords(rect_id, x1, y1, event.x, event.y)

        def on_release(event):
            if start_x is not None:
                end_x, end_y = event.x_root, event.y_root
                x1, x2 = min(start_x, end_x), max(start_x, end_x)
                y1, y2 = min(start_y, end_y), max(start_y, end_y)

                self.search_x1.set(x1)
                self.search_y1.set(y1)
                self.search_x2.set(x2)
                self.search_y2.set(y2)

                self.status_label.configure(text=f"✅ 영역 설정 완료")
                overlay.destroy()
                self.show_area_overlay()

        def on_escape(event):
            self.status_label.configure(text="⏸️ 대기 중")
            overlay.destroy()

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)
        overlay.bind('<Escape>', on_escape)
        overlay.focus_set()

    def show_area_overlay(self):
        if hasattr(self, 'area_overlay') and self.area_overlay:
            try:
                self.area_overlay.destroy()
            except:
                pass
            self.area_overlay = None
            return

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()
        width, height = x2 - x1, y2 - y1

        if width <= 0 or height <= 0:
            return

        self.area_overlay = tk.Toplevel(self)
        self.area_overlay.overrideredirect(True)
        self.area_overlay.attributes('-topmost', True)
        self.area_overlay.attributes('-transparentcolor', 'white')
        self.area_overlay.geometry(f'{width}x{height}+{x1}+{y1}')

        canvas = tk.Canvas(self.area_overlay, width=width, height=height, bg='white', highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(2, 2, width-2, height-2, outline='#00ff00', width=3)
        canvas.bind('<Button-1>', lambda e: self.show_area_overlay())

    def change_trigger_key(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("키 설정")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...\n(마우스 4/5번 버튼도 가능)",
                     font=ctk.CTkFont(size=14)).pack(pady=20)

        dialog_active = [True]

        def on_key(event):
            if dialog_active[0]:
                dialog_active[0] = False
                self.trigger_key.set(event.name)
                self.key_display.configure(text=event.name.upper())
                self.setup_hotkey()
                dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        # 마우스 버튼 감지
        def poll_mouse():
            import time
            while dialog_active[0]:
                if win32api.GetAsyncKeyState(0x05) & 0x8000:  # Mouse4
                    dialog_active[0] = False
                    self.after(0, lambda: self.trigger_key.set("mouse4"))
                    self.after(0, lambda: self.key_display.configure(text="MOUSE4"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                if win32api.GetAsyncKeyState(0x06) & 0x8000:  # Mouse5
                    dialog_active[0] = False
                    self.after(0, lambda: self.trigger_key.set("mouse5"))
                    self.after(0, lambda: self.key_display.configure(text="MOUSE5"))
                    self.after(0, self.setup_hotkey)
                    self.after(0, dialog.destroy)
                    break
                time.sleep(0.01)

        threading.Thread(target=poll_mouse, daemon=True).start()

        def on_close():
            dialog_active[0] = False
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def check_modifier(self, required_modifier):
        """조합키가 눌렸는지 확인"""
        if required_modifier == "없음":
            return True
        elif required_modifier == "Ctrl":
            return win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000
        elif required_modifier == "Shift":
            return win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000
        elif required_modifier == "Alt":
            return win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000
        return True

    def is_mouse_key(self, key):
        """마우스 버튼인지 확인"""
        return key in ["mouse4", "mouse5"]

    def start_mouse_polling(self):
        """마우스 버튼 폴링 스레드 시작"""
        self.mouse_polling_active = True

        def poll_mouse():
            import time
            mouse4_pressed = False
            mouse5_pressed = False

            while self.mouse_polling_active:
                # 마우스 4번 (XBUTTON1 = 0x05)
                m4_state = win32api.GetAsyncKeyState(0x05) & 0x8000
                if m4_state and not mouse4_pressed:
                    mouse4_pressed = True
                    self.on_mouse_button("mouse4")
                elif not m4_state:
                    mouse4_pressed = False

                # 마우스 5번 (XBUTTON2 = 0x06)
                m5_state = win32api.GetAsyncKeyState(0x06) & 0x8000
                if m5_state and not mouse5_pressed:
                    mouse5_pressed = True
                    self.on_mouse_button("mouse5")
                elif not m5_state:
                    mouse5_pressed = False

                time.sleep(0.01)  # 100Hz 폴링

        threading.Thread(target=poll_mouse, daemon=True).start()

    def on_mouse_button(self, button):
        """마우스 버튼 핸들러"""
        # 각 탭의 트리거 키와 비교
        if self.trigger_key.get() == button:
            self.on_trigger_key(None)
        if self.inv_trigger_key.get() == button:
            self.on_inv_trigger_key(None)
        if self.discard_trigger_key.get() == button:
            self.on_discard_trigger_key(None)
        if self.sell_trigger_key.get() == button:
            self.on_sell_trigger_key(None)
        if self.consume_trigger_key.get() == button:
            self.on_consume_trigger_key(None)

    def setup_hotkey(self):
        keyboard.unhook_all()
        # 키보드 핫키 등록 (마우스 버튼 제외)
        if not self.is_mouse_key(self.trigger_key.get()):
            keyboard.on_press_key(self.trigger_key.get(), self.on_trigger_key, suppress=False)
        if not self.is_mouse_key(self.inv_trigger_key.get()):
            keyboard.on_press_key(self.inv_trigger_key.get(), self.on_inv_trigger_key, suppress=False)
        if not self.is_mouse_key(self.discard_trigger_key.get()):
            keyboard.on_press_key(self.discard_trigger_key.get(), self.on_discard_trigger_key, suppress=False)
        if not self.is_mouse_key(self.sell_trigger_key.get()):
            keyboard.on_press_key(self.sell_trigger_key.get(), self.on_sell_trigger_key, suppress=False)
        if not self.is_mouse_key(self.consume_trigger_key.get()):
            keyboard.on_press_key(self.consume_trigger_key.get(), self.on_consume_trigger_key, suppress=False)

        # 긴급 정지 키 등록
        if not self.is_mouse_key(self.emergency_stop_key.get()):
            keyboard.on_press_key(self.emergency_stop_key.get(), self.on_emergency_stop, suppress=False)

        # 마우스 폴링 시작 (한 번만)
        if not hasattr(self, 'mouse_polling_active') or not self.mouse_polling_active:
            self.start_mouse_polling()

    def on_inv_trigger_key(self, event):
        """인벤토리 정리 트리거 키 핸들러 - 토글 방식"""
        import time as time_module

        if not self.inv_running:
            return

        # 조합키 체크
        if not self.check_modifier(self.inv_trigger_modifier.get()):
            return

        # 디바운스: 0.3초 내 중복 입력 무시
        current_time = time_module.time()
        if current_time - self.inv_last_trigger_time < 0.3:
            return
        self.inv_last_trigger_time = current_time

        if self.inv_cleanup_active:
            # 실행 중이면 중지
            self.inv_cleanup_active = False
            self.after(0, lambda: self.inv_status_label.configure(text="⏹️ 중지됨"))
            self.after(0, lambda: self.inv_status_frame.configure(fg_color="#3d3d1a"))
        else:
            # 실행 중 아니면 시작
            self.inv_cleanup_active = True
            self.run_inventory_cleanup()

    def on_trigger_key(self, event):
        if not self.is_running:
            return
        # 조합키 체크
        if not self.check_modifier(self.trigger_modifier.get()):
            return
        self.detection_active = not self.detection_active
        if self.detection_active:
            self.after(0, lambda: self.status_label.configure(text="🟢 검색 활성화"))
            self.after(0, lambda: self.status_frame.configure(fg_color="#1a3d1a"))
        else:
            self.after(0, lambda: self.status_label.configure(text="🔴 검색 비활성화"))
            self.after(0, lambda: self.status_frame.configure(fg_color="#3d1a1a"))

    def toggle_running(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.start_btn.configure(text="⏹️ 중지", fg_color="#dc3545", hover_color="#c82333")
            self.status_label.configure(text=f"🔴 [{self.trigger_key.get().upper()}] 키로 시작")
            self.status_frame.configure(fg_color="#3d1a1a")
            self.detection_active = False
            self.setup_hotkey()
            self.run_detection()
        else:
            self.start_btn.configure(text="▶️ 시작", fg_color="#28a745", hover_color="#218838")
            self.status_label.configure(text="⏸️ 대기 중")
            self.status_frame.configure(fg_color="#1a1a2e")
            self.detection_active = False

    def run_detection(self):
        def detection_loop():
            while self.is_running:
                try:
                    if self.detection_active:
                        found = self.search_and_click()
                        if found:
                            self.after(0, lambda: self.status_label.configure(text="🟢 클릭!"))
                            import time
                            time.sleep(self.click_delay.get())
                except Exception as e:
                    print(f"Error: {e}")
                import time
                time.sleep(0.01)

        threading.Thread(target=detection_loop, daemon=True).start()

    def search_and_click(self):
        if not self.colors:
            return False

        x1, y1 = self.search_x1.get(), self.search_y1.get()
        x2, y2 = self.search_x2.get(), self.search_y2.get()
        step = max(1, self.search_step.get())
        tol = self.tolerance.get()
        exclude_range = self.exclude_range.get()

        try:
            import time as time_module

            # mss로 빠른 화면 캡처
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

                                # 텍스트 중앙 찾기
                                center_x, center_y = self.find_text_center(
                                    pixels, x, y, width, height, hex_color, tol
                                )

                                # 중복 체크
                                center_key = (center_x // 20, center_y // 20)
                                if center_key in visited_centers:
                                    continue
                                visited_centers.add(center_key)

                                screen_x = x1 + center_x
                                screen_y = y1 + center_y

                                # 쿨다운 체크
                                if self.last_click_pos:
                                    dist_to_last = ((screen_x - self.last_click_pos[0])**2 +
                                                    (screen_y - self.last_click_pos[1])**2)**0.5
                                    time_passed = time_module.time() - self.last_click_time
                                    if dist_to_last < self.cooldown_distance.get() and time_passed < self.cooldown_time.get():
                                        continue

                                # 주변에 B 있는지 체크
                                if self.exclude_colors:
                                    if self.has_exclude_color_nearby(pixels, center_x, center_y, width, height, exclude_range, tol):
                                        continue

                                # 부드럽게 이동 (144fps급, 신화장난꾸러기와 동일)
                                self.smooth_move_to(screen_x, screen_y, duration=0.15)

                                # 클릭
                                if self.click_type.get() == "right":
                                    pyautogui.rightClick()
                                elif self.click_type.get() == "fkey":
                                    keyboard.press_and_release('f')

                                self.last_click_pos = (screen_x, screen_y)
                                self.last_click_time = time_module.time()
                                return True

                        except:
                            continue

        except Exception as e:
            print(f"Search error: {e}")

        return False

    def has_exclude_color_nearby(self, pixels, cx, cy, width, height, check_range, tol):
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

    def color_matches(self, pixel, hex_color, tol):
        """픽셀이 특정 색상과 일치하는지 확인"""
        r, g, b = pixel[0], pixel[1], pixel[2]
        target_r = int(hex_color[1:3], 16)
        target_g = int(hex_color[3:5], 16)
        target_b = int(hex_color[5:7], 16)
        return (abs(r - target_r) <= tol and
                abs(g - target_g) <= tol and
                abs(b - target_b) <= tol)

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

    def save_config(self):
        config = {
            'colors': self.colors,
            'exclude_colors': self.exclude_colors,
            'tolerance': self.tolerance.get(),
            'exclude_range': self.exclude_range.get(),
            'trigger_key': self.trigger_key.get(),
            'trigger_modifier': self.trigger_modifier.get(),
            'click_type': self.click_type.get(),
            'click_delay': self.click_delay.get(),
            'search_area': {
                'x1': self.search_x1.get(),
                'y1': self.search_y1.get(),
                'x2': self.search_x2.get(),
                'y2': self.search_y2.get()
            },
            'search_step': self.search_step.get(),
            # 신화장난꾸러기 탭 설정
            'inventory': {
                'keep_color': self.inv_keep_color.get(),
                'tolerance': self.inv_tolerance.get(),
                'area': {
                    'x1': self.inv_x1.get(),
                    'y1': self.inv_y1.get(),
                    'x2': self.inv_x2.get(),
                    'y2': self.inv_y2.get()
                },
                'desc_area': {
                    'x1': self.inv_desc_x1.get(),
                    'y1': self.inv_desc_y1.get(),
                    'x2': self.inv_desc_x2.get(),
                    'y2': self.inv_desc_y2.get()
                },
                'cols': self.inv_cols.get(),
                'rows': self.inv_rows.get(),
                'trigger_key': self.inv_trigger_key.get(),
                'trigger_modifier': self.inv_trigger_modifier.get(),
                'move_duration': self.inv_move_duration.get(),
                'panel_delay': self.inv_panel_delay.get(),
                'space_delay': self.inv_space_delay.get(),
                'click_delay': self.inv_click_delay.get()
            },
            # 아이템 버리기 탭 설정
            'discard': {
                'trigger_key': self.discard_trigger_key.get(),
                'trigger_modifier': self.discard_trigger_modifier.get(),
                'delay': self.discard_delay.get()
            },
            # 아이템 팔기 탭 설정
            'sell': {
                'trigger_key': self.sell_trigger_key.get(),
                'trigger_modifier': self.sell_trigger_modifier.get(),
                'delay': self.sell_delay.get()
            },
            # 아이템 먹기 탭 설정
            'consume': {
                'trigger_key': self.consume_trigger_key.get(),
                'trigger_modifier': self.consume_trigger_modifier.get(),
                'delay': self.consume_delay.get(),
                'input_type': self.consume_input_type.get()
            },
            # 오버레이 설정
            'overlay': {
                'x': self.overlay_x.get(),
                'y': self.overlay_y.get(),
                'alpha': self.overlay_alpha.get(),
                'bg_color': self.overlay_bg_color.get()
            },
            # 소리 알림 설정
            'sound_enabled': self.sound_enabled.get(),
            # 긴급 정지 키
            'emergency_stop_key': self.emergency_stop_key.get(),
            # 자동 시작 설정
            'auto_start': {
                'belial': self.auto_start_belial.get(),
                'inv': self.auto_start_inv.get(),
                'discard': self.auto_start_discard.get(),
                'sell': self.auto_start_sell.get(),
                'consume': self.auto_start_consume.get()
            }
        }

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("저장", "설정이 저장되었습니다!")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    def load_config(self):
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
            self.trigger_modifier.set(config.get('trigger_modifier', '없음'))
            self.click_type.set(config.get('click_type', 'right'))
            self.click_delay.set(config.get('click_delay', 0.1))

            area = config.get('search_area', {})
            self.search_x1.set(area.get('x1', 0))
            self.search_y1.set(area.get('y1', 0))
            self.search_x2.set(area.get('x2', 1920))
            self.search_y2.set(area.get('y2', 1080))

            self.search_step.set(config.get('search_step', 5))

            # 신화장난꾸러기 탭 설정 불러오기
            inv = config.get('inventory', {})
            if inv:
                self.inv_keep_color.set(inv.get('keep_color', '#FF6B00'))
                self.inv_tolerance.set(inv.get('tolerance', 15))

                inv_area = inv.get('area', {})
                self.inv_x1.set(inv_area.get('x1', 1725))
                self.inv_y1.set(inv_area.get('y1', 1009))
                self.inv_x2.set(inv_area.get('x2', 2550))
                self.inv_y2.set(inv_area.get('y2', 1340))

                desc_area = inv.get('desc_area', {})
                self.inv_desc_x1.set(desc_area.get('x1', 1144))
                self.inv_desc_y1.set(desc_area.get('y1', 428))
                self.inv_desc_x2.set(desc_area.get('x2', 1636))
                self.inv_desc_y2.set(desc_area.get('y2', 1147))

                self.inv_cols.set(inv.get('cols', 11))
                self.inv_rows.set(inv.get('rows', 3))
                self.inv_trigger_key.set(inv.get('trigger_key', 'f2'))
                self.inv_trigger_modifier.set(inv.get('trigger_modifier', '없음'))
                self.inv_move_duration.set(inv.get('move_duration', 0.15))
                self.inv_panel_delay.set(inv.get('panel_delay', 0.05))
                self.inv_space_delay.set(inv.get('space_delay', 0.05))
                self.inv_click_delay.set(inv.get('click_delay', 0.01))

                # UI 업데이트
                self.inv_key_display.configure(text=self.inv_trigger_key.get().upper())
                self.update_inv_color_preview()
                self.inv_move_label.configure(text=f"{self.inv_move_duration.get():.2f}초")
                self.inv_panel_label.configure(text=f"{self.inv_panel_delay.get():.3f}초")
                self.inv_space_label.configure(text=f"{self.inv_space_delay.get():.3f}초")
                self.inv_click_label.configure(text=f"{self.inv_click_delay.get():.3f}초")

            # 아이템 버리기 탭 설정 불러오기
            discard = config.get('discard', {})
            if discard:
                self.discard_trigger_key.set(discard.get('trigger_key', 'f3'))
                self.discard_trigger_modifier.set(discard.get('trigger_modifier', '없음'))
                self.discard_delay.set(discard.get('delay', 0.01))
                self.discard_key_display.configure(text=self.discard_trigger_key.get().upper())
                self.discard_delay_label.configure(text=f"{self.discard_delay.get():.3f}초")

            # 아이템 팔기 탭 설정 불러오기
            sell = config.get('sell', {})
            if sell:
                self.sell_trigger_key.set(sell.get('trigger_key', 'f4'))
                self.sell_trigger_modifier.set(sell.get('trigger_modifier', '없음'))
                self.sell_delay.set(sell.get('delay', 0.01))
                self.sell_key_display.configure(text=self.sell_trigger_key.get().upper())
                self.sell_delay_label.configure(text=f"{self.sell_delay.get():.3f}초")

            # 아이템 먹기 탭 설정 불러오기
            consume = config.get('consume', {})
            if consume:
                self.consume_trigger_key.set(consume.get('trigger_key', 'f5'))
                self.consume_trigger_modifier.set(consume.get('trigger_modifier', '없음'))
                self.consume_delay.set(consume.get('delay', 0.01))
                self.consume_input_type.set(consume.get('input_type', 'F키'))
                self.consume_key_display.configure(text=self.consume_trigger_key.get().upper())
                self.consume_delay_label.configure(text=f"{self.consume_delay.get():.3f}초")

            # 오버레이 설정 불러오기
            overlay = config.get('overlay', {})
            if overlay:
                self.overlay_x.set(overlay.get('x', 100))
                self.overlay_y.set(overlay.get('y', 100))
                self.overlay_alpha.set(overlay.get('alpha', 0.85))
                self.overlay_bg_color.set(overlay.get('bg_color', '#1a1a2e'))
                self.alpha_label.configure(text=f"{int(self.overlay_alpha.get() * 100)}%")
                # 배경색 미리보기 업데이트
                if hasattr(self, 'bg_color_preview'):
                    self.bg_color_preview.configure(fg_color=self.overlay_bg_color.get())

            # 소리 알림 설정 불러오기
            self.sound_enabled.set(config.get('sound_enabled', True))

            # 긴급 정지 키 불러오기
            self.emergency_stop_key.set(config.get('emergency_stop_key', 'esc'))
            self.emergency_key_display.configure(text=self.emergency_stop_key.get().upper())

            # 자동 시작 설정 불러오기
            auto_start = config.get('auto_start', {})
            if auto_start:
                self.auto_start_belial.set(auto_start.get('belial', False))
                self.auto_start_inv.set(auto_start.get('inv', False))
                self.auto_start_discard.set(auto_start.get('discard', False))
                self.auto_start_sell.set(auto_start.get('sell', False))
                self.auto_start_consume.set(auto_start.get('consume', False))

            self.key_display.configure(text=self.trigger_key.get().upper())
            self.update_color_list()
            self.update_exclude_list()
            self.setup_hotkey()  # 핫키 재설정
        except Exception as e:
            print(f"Config load error: {e}")

    # ============================================================
    # === 자동 업데이트 시스템 ===
    # ============================================================

    def check_for_updates(self):
        """시작 시 업데이트 확인 (백그라운드 스레드에서 실행)"""
        try:
            req = urllib.request.Request(GITHUB_API)
            req.add_header('User-Agent', 'ColorClickerPro')

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                latest_version = data['tag_name'].lstrip('v')

                if self.is_newer_version(latest_version, VERSION):
                    # 새 버전 발견 - 메인 스레드에서 다이얼로그 표시
                    self.after(0, lambda: self.prompt_update(data))
        except Exception as e:
            print(f"업데이트 확인 실패 (무시됨): {e}")

    def is_newer_version(self, latest, current):
        """버전 비교 (예: 1.1.0 > 1.0.0)"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # 길이 맞추기
            while len(latest_parts) < 3:
                latest_parts.append(0)
            while len(current_parts) < 3:
                current_parts.append(0)

            return latest_parts > current_parts
        except:
            return False

    def prompt_update(self, release_data):
        """업데이트 확인 다이얼로그"""
        latest_version = release_data['tag_name'].lstrip('v')
        release_notes = release_data.get('body', '변경 사항 없음')[:200]

        result = messagebox.askyesno(
            "업데이트 확인",
            f"새 버전이 있습니다!\n\n"
            f"현재 버전: v{VERSION}\n"
            f"최신 버전: v{latest_version}\n\n"
            f"변경 사항:\n{release_notes}...\n\n"
            f"지금 업데이트하시겠습니까?"
        )

        if result:
            # EXE 다운로드 URL 찾기
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    threading.Thread(target=self.download_and_update, args=(download_url,), daemon=True).start()
                    return

            messagebox.showerror("오류", "다운로드할 EXE 파일을 찾을 수 없습니다.")

    def download_and_update(self, download_url):
        """업데이트 다운로드 및 적용"""
        try:
            # 현재 실행 파일 경로
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                new_exe = current_exe + '.new'
                backup_exe = current_exe + '.backup'
            else:
                messagebox.showinfo("알림", "소스 코드 실행 중에는 자동 업데이트가 지원되지 않습니다.\nGitHub에서 최신 버전을 다운로드하세요.")
                return

            # 진행 다이얼로그 표시
            self.after(0, lambda: self.show_update_progress())

            # 다운로드
            urllib.request.urlretrieve(download_url, new_exe)

            # 배치 스크립트로 교체 (앱 종료 후 실행)
            batch_content = f'''@echo off
timeout /t 2 /nobreak > nul
if exist "{backup_exe}" del "{backup_exe}"
move "{current_exe}" "{backup_exe}"
move "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
'''
            batch_path = os.path.join(os.path.dirname(current_exe), 'update.bat')
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            # 배치 실행 및 앱 종료
            import subprocess
            subprocess.Popen(['cmd', '/c', batch_path], creationflags=subprocess.CREATE_NO_WINDOW)
            self.after(0, self.quit)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("업데이트 실패", f"업데이트 중 오류가 발생했습니다:\n{e}"))

    def show_update_progress(self):
        """업데이트 진행 중 표시"""
        self.update_dialog = ctk.CTkToplevel(self)
        self.update_dialog.title("업데이트 중")
        self.update_dialog.geometry("300x100")
        self.update_dialog.transient(self)
        self.update_dialog.grab_set()

        ctk.CTkLabel(self.update_dialog, text="업데이트 다운로드 중...",
                     font=ctk.CTkFont(size=14)).pack(pady=20)
        ctk.CTkLabel(self.update_dialog, text="잠시만 기다려주세요",
                     text_color="gray").pack()

    # ============================================================
    # === 월드 보스 타이머 ===
    # ============================================================

    def fetch_world_boss_info(self):
        """helltides.com에서 월드 보스 정보 가져오기"""
        try:
            url = "https://helltides.com/worldboss"
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')

            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')

                # 여러 패턴으로 시도
                # 패턴 1: world_boss 타입의 이벤트 찾기
                event_pattern = r'"type"\s*:\s*"world_boss"[^}]*"boss"\s*:\s*"([^"]+)"[^}]*"startTime"\s*:\s*"([^"]+)"[^}]*"zone"\s*:\s*"([^"]+)"'
                event_match = re.search(event_pattern, html, re.DOTALL)

                # 패턴 2: 순서가 다를 수 있음
                if not event_match:
                    boss_match = re.search(r'"boss"\s*:\s*"(Ashava|Avarice|Wandering Death|Azmodan)"', html)
                    time_match = re.search(r'"startTime"\s*:\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?)"', html)
                    zone_match = re.search(r'"zone"\s*:\s*"([^"]+)"', html)

                    if boss_match and time_match:
                        boss_name = boss_match.group(1)
                        start_time_str = time_match.group(1)
                        zone_raw = zone_match.group(1) if zone_match else "unknown"
                    else:
                        # 패턴 3: timestamp로 시도
                        timestamp_match = re.search(r'"timestamp"\s*:\s*(\d{10,13})[^}]*"boss"\s*:\s*"([^"]+)"', html)
                        if timestamp_match:
                            timestamp = int(timestamp_match.group(1))
                            if timestamp > 9999999999:  # 밀리초
                                timestamp = timestamp // 1000
                            self.world_boss_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                            boss_name = timestamp_match.group(2)
                            zone_raw = "unknown"
                            zone_display = self._format_zone_name(zone_raw)
                            self.after(0, lambda b=boss_name, z=zone_display: self._update_boss_ui(b, z))
                            self.after(300000, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())
                            return
                        else:
                            self.after(0, lambda: self._update_boss_ui("정보 없음", ""))
                            self.after(300000, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())
                            return
                else:
                    boss_name = event_match.group(1)
                    start_time_str = event_match.group(2)
                    zone_raw = event_match.group(3)

                # 시간 파싱
                if not start_time_str.endswith('Z'):
                    start_time_str += 'Z'
                start_time_str = start_time_str.replace('Z', '+00:00')
                self.world_boss_timestamp = datetime.fromisoformat(start_time_str)

                # 지역명 포맷팅
                zone_display = self._format_zone_name(zone_raw)

                # UI 업데이트 (메인 스레드)
                self.after(0, lambda b=boss_name, z=zone_display: self._update_boss_ui(b, z))

        except Exception as e:
            print(f"월드 보스 정보 가져오기 실패: {e}")
            self.after(0, lambda: self._update_boss_ui("연결 실패", ""))

        # 5분 후 다시 가져오기
        self.after(300000, lambda: threading.Thread(target=self.fetch_world_boss_info, daemon=True).start())

    def _format_zone_name(self, zone_raw):
        """지역명 포맷팅 (fractured_peaks -> Fractured Peaks)"""
        zone_names = {
            "fractured_peaks": "Fractured Peaks",
            "scosglen": "Scosglen",
            "dry_steppes": "Dry Steppes",
            "kehjistan": "Kehjistan",
            "nahantu": "Nahantu"
        }
        return zone_names.get(zone_raw, zone_raw.replace('_', ' ').title())

    def _update_boss_ui(self, boss_name, zone):
        """월드 보스 UI 업데이트 (메인 스레드)"""
        self.world_boss_name.set(boss_name)
        self.world_boss_zone.set(zone)

        # Home 탭 업데이트
        if hasattr(self, 'home_boss_name'):
            self.home_boss_name.configure(text=boss_name)
        if hasattr(self, 'home_boss_zone'):
            self.home_boss_zone.configure(text=zone)

    def update_world_boss_timer(self):
        """월드 보스 남은 시간 업데이트 (1분 간격)"""
        if self.world_boss_timestamp:
            now = datetime.now(timezone.utc)
            diff = self.world_boss_timestamp - now

            if diff.total_seconds() > 0:
                hours, remainder = divmod(int(diff.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)

                if hours > 0:
                    time_str = f"{hours}시간 {minutes}분 후"
                else:
                    time_str = f"{minutes}분 후"

                # 5분 이하면 빨간색
                if diff.total_seconds() <= 300:
                    time_color = "#ff4444"
                else:
                    time_color = "#00ff00"

                self.world_boss_time.set(time_str)

                # Home 탭 업데이트
                if hasattr(self, 'home_boss_time'):
                    self.home_boss_time.configure(text=f"⏰ {time_str}", text_color=time_color)

                # 오버레이 업데이트
                if self.world_boss_label:
                    boss_name = self.world_boss_name.get()
                    short_name = boss_name[:6] if len(boss_name) > 6 else boss_name
                    if hours > 0:
                        overlay_text = f"{short_name} {hours}:{minutes:02d}"
                    else:
                        overlay_text = f"{short_name} {minutes}분"
                    self.world_boss_label.configure(text=overlay_text, fg=time_color)
            else:
                # 시간 지남 - 새로 가져오기
                self.world_boss_time.set("지나감")
                if hasattr(self, 'home_boss_time'):
                    self.home_boss_time.configure(text="⏰ 새로고침 필요", text_color="#ff9900")
                threading.Thread(target=self.fetch_world_boss_info, daemon=True).start()

        # 1분 후 다시 업데이트
        self.after(60000, self.update_world_boss_timer)

    def refresh_world_boss(self):
        """월드 보스 정보 새로고침"""
        self.world_boss_name.set("로딩 중...")
        self.world_boss_time.set("")
        if hasattr(self, 'home_boss_name'):
            self.home_boss_name.configure(text="로딩 중...")
        if hasattr(self, 'home_boss_time'):
            self.home_boss_time.configure(text="")
        threading.Thread(target=self.fetch_world_boss_info, daemon=True).start()

    # ============================================================
    # === 오버레이 배경색 커스터마이징 ===
    # ============================================================

    def change_overlay_bg_color(self):
        """오버레이 배경색 선택"""
        color = colorchooser.askcolor(
            initialcolor=self.overlay_bg_color.get(),
            title="오버레이 배경색 선택"
        )
        if color[1]:  # 색상 선택됨
            self.overlay_bg_color.set(color[1])
            # 미리보기 업데이트
            if hasattr(self, 'bg_color_preview'):
                self.bg_color_preview.configure(fg_color=color[1])
            # 오버레이에 적용
            self.apply_overlay_bg_color()

    def apply_overlay_bg_color(self):
        """오버레이에 배경색 적용"""
        if self.overlay_window:
            color = self.overlay_bg_color.get()
            try:
                self.overlay_window.configure(bg=color)
                # 모든 자식 위젯의 배경색도 변경
                for widget in self.overlay_window.winfo_children():
                    try:
                        widget.configure(bg=color)
                        for child in widget.winfo_children():
                            try:
                                # separator 프레임은 제외
                                if child.cget('bg') != '#444444':
                                    child.configure(bg=color)
                            except:
                                pass
                    except:
                        pass
            except Exception as e:
                print(f"배경색 적용 실패: {e}")


if __name__ == "__main__":
    app = ColorClickerApp()
    app.mainloop()
