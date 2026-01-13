# -*- coding: utf-8 -*-
"""
색상 인식 자동 우클릭 프로그램 (Modern UI)
Windows 전용
"""

import customtkinter as ctk
from tkinter import messagebox, colorchooser
import tkinter as tk
import threading
import json
import os
import sys

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
        self.inv_last_trigger_time = 0  # 디바운스용
        # 딜레이 설정
        self.inv_move_duration = ctk.DoubleVar(value=0.15)  # 슬롯 간 이동 시간
        self.inv_panel_delay = ctk.DoubleVar(value=0.05)  # 설명 패널 대기
        self.inv_space_delay = ctk.DoubleVar(value=0.05)  # 스페이스바 간격
        self.inv_click_delay = ctk.DoubleVar(value=0.01)  # 클릭 후 대기

        self.setup_ui()
        self.load_config()
        self.setup_hotkey()
        self.update_mouse_pos()

    def setup_ui(self):
        # === 헤더 ===
        header = ctk.CTkLabel(self, text="🎯 Color Clicker Pro",
                              font=ctk.CTkFont(size=24, weight="bold"))
        header.pack(pady=(10, 5))

        # === 탭뷰 생성 ===
        self.tabview = ctk.CTkTabview(self, width=530, height=920)
        self.tabview.pack(pady=5, padx=10, fill="both", expand=True)

        # 탭 추가
        self.tabview.add("아이템 줍기")
        self.tabview.add("신화장난꾸러기")

        # === 아이템 줍기 탭 ===
        self.main_frame = ctk.CTkScrollableFrame(self.tabview.tab("아이템 줍기"), width=500, height=850)
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
        self.key_display = ctk.CTkLabel(key_frame, text="F1", font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#00ff00")
        self.key_display.pack(side="left", padx=10)
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
        self.inv_key_display = ctk.CTkLabel(key_inner, text="F2", font=ctk.CTkFont(size=14, weight="bold"),
                                             text_color="#00ff00")
        self.inv_key_display.pack(side="left", padx=10)
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
        dialog.geometry("300x120")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...",
                     font=ctk.CTkFont(size=14)).pack(pady=30)

        def on_key(event):
            self.inv_trigger_key.set(event.name)
            self.inv_key_display.configure(text=event.name.upper())
            self.setup_hotkey()
            dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
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
        dialog.geometry("300x120")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="새 트리거 키를 누르세요...",
                     font=ctk.CTkFont(size=14)).pack(pady=30)

        def on_key(event):
            self.trigger_key.set(event.name)
            self.key_display.configure(text=event.name.upper())
            self.setup_hotkey()
            dialog.destroy()

        keyboard.on_press(on_key, suppress=False)

        def on_close():
            keyboard.unhook_all()
            self.setup_hotkey()
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

    def setup_hotkey(self):
        keyboard.unhook_all()
        keyboard.on_press_key(self.trigger_key.get(), self.on_trigger_key, suppress=False)
        keyboard.on_press_key(self.inv_trigger_key.get(), self.on_inv_trigger_key, suppress=False)

    def on_inv_trigger_key(self, event):
        """인벤토리 정리 트리거 키 핸들러 - 토글 방식"""
        import time as time_module

        if not self.inv_running:
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
                'move_duration': self.inv_move_duration.get(),
                'panel_delay': self.inv_panel_delay.get(),
                'space_delay': self.inv_space_delay.get(),
                'click_delay': self.inv_click_delay.get()
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

            self.key_display.configure(text=self.trigger_key.get().upper())
            self.update_color_list()
            self.update_exclude_list()
        except Exception as e:
            print(f"Config load error: {e}")


if __name__ == "__main__":
    app = ColorClickerApp()
    app.mainloop()
