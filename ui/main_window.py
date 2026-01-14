# -*- coding: utf-8 -*-
"""
메인 윈도우 UI 및 컨텐츠 생성
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import threading

from constants import VERSION, DEFAULT_FONT, COLORS


class MainWindowMixin:
    """메인 윈도우 UI 믹스인"""

    def setup_ui(self):
        """UI 설정"""
        # === 메인 컨테이너 (사이드바 + 컨텐츠) ===
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # === 왼쪽 사이드바 ===
        self.sidebar = ctk.CTkFrame(main_container, width=140, fg_color="#1a1a2e", corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(5, 0), pady=5)
        self.sidebar.pack_propagate(False)

        # 사이드바 헤더
        ctk.CTkLabel(self.sidebar, text="Wonryeol",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"),
                     text_color="#00aaff").pack(pady=(15, 0))
        ctk.CTkLabel(self.sidebar, text="Helper",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                     text_color="#00aaff").pack()
        ctk.CTkLabel(self.sidebar, text=f"v{VERSION}",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=10),
                     text_color="#666666").pack(pady=(2, 15))

        # 구분선
        ctk.CTkFrame(self.sidebar, height=2, fg_color="#333344").pack(fill="x", padx=10, pady=5)

        # 메뉴 버튼들
        self.menu_buttons = {}
        menus = [
            ("🏠 Home", "home"),
            ("📖 사용법", "help"),
            ("🗑️ 버리기", "discard"),
            ("🍖 먹기", "consume"),
            ("💰 팔기", "sell"),
            ("✨ 꾸러기", "inventory"),
            ("👁️ 벨리알", "belial"),
            ("📋 패치", "patch"),
        ]

        for text, key in menus:
            btn = ctk.CTkButton(self.sidebar, text=text, anchor="w",
                               font=ctk.CTkFont(family=DEFAULT_FONT, size=13),
                               fg_color="transparent", hover_color="#2a2a4e",
                               text_color="#cccccc", height=40,
                               command=lambda k=key: self.show_content(k))
            btn.pack(fill="x", padx=8, pady=2)
            self.menu_buttons[key] = btn

        # 사이드바 하단 여백
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # 마우스 좌표 (하단)
        self.coord_label = ctk.CTkLabel(self.sidebar, text="마우스: (0, 0)",
                                        font=ctk.CTkFont(family=DEFAULT_FONT, size=9), text_color="#666666")
        self.coord_label.pack(pady=10)

        # === 오른쪽 컨텐츠 영역 ===
        self.content_area = ctk.CTkFrame(main_container, fg_color="#2b2b2b", corner_radius=10)
        self.content_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 컨텐츠 프레임들 저장
        self.content_frames = {}

        # === 각 컨텐츠 생성 ===
        # Home
        self.content_frames["home"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_home_content(self.content_frames["home"])

        # 사용법 (일반 프레임 - 텍스트박스가 자체 스크롤)
        self.content_frames["help"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.create_help_content(self.content_frames["help"])

        # 아이템 버리기
        self.content_frames["discard"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_discard_content(self.content_frames["discard"])

        # 아이템 먹기
        self.content_frames["consume"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_consume_content(self.content_frames["consume"])

        # 아이템 팔기
        self.content_frames["sell"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_sell_content(self.content_frames["sell"])

        # 신화장난꾸러기
        self.content_frames["inventory"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_inventory_content(self.content_frames["inventory"])

        # 벨리알
        self.content_frames["belial"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.main_frame = self.content_frames["belial"]  # 기존 호환성
        self.create_belial_content(self.content_frames["belial"])

        # 패치노트
        self.content_frames["patch"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_patch_content(self.content_frames["patch"])

        # 초기 화면: Home
        self.current_content = None
        self.show_content("home")

    def show_content(self, key):
        """컨텐츠 전환"""
        if self.current_content and self.current_content in self.content_frames:
            self.content_frames[self.current_content].pack_forget()

        if key in self.content_frames:
            self.content_frames[key].pack(fill="both", expand=True, padx=10, pady=10)
            self.current_content = key

        for k, btn in self.menu_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["primary"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#cccccc")

    def create_section_box(self, parent, title, icon=""):
        """섹션 박스 생성 헬퍼"""
        box = ctk.CTkFrame(parent, fg_color="#363636", corner_radius=10)
        box.pack(fill="x", pady=8, padx=5)

        header = ctk.CTkFrame(box, fg_color=COLORS["primary"], corner_radius=8, height=35)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=f"{icon} {title}",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                     text_color="white").pack(side="left", padx=15, pady=5)

        content = ctk.CTkFrame(box, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        return content

    # =========================================
    # Home 컨텐츠
    # =========================================
    def create_home_content(self, parent):
        """Home 컨텐츠 생성"""
        # 상단 행: 전체제어 + 기능상태 + 오버레이
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 기능 상태
        status_box = self.create_section_box(row1, "기능 상태", "⚡")
        status_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.home_switches = {}
        self.home_key_labels = {}
        self.home_status_labels = {}

        functions = [
            ("버리기", self.discard_trigger_key, self.discard_trigger_modifier, "discard_running", self.home_toggle_discard),
            ("먹기", self.consume_trigger_key, self.consume_trigger_modifier, "consume_running", self.home_toggle_consume),
            ("팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running", self.home_toggle_sell),
            ("꾸러기", self.inv_trigger_key, self.inv_trigger_modifier, "inv_running", self.home_toggle_inv),
            ("벨리알", self.trigger_key, self.trigger_modifier, "is_running", self.home_toggle_belial),
        ]

        for name, key_var, mod_var, running_attr, toggle_func in functions:
            row = ctk.CTkFrame(status_box, fg_color="transparent")
            row.pack(fill="x", pady=1)

            ctk.CTkLabel(row, text=name, width=50, anchor="w",
                         font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")

            key_label = ctk.CTkLabel(row, text="", width=60, anchor="center",
                                     text_color="#ff9900", font=ctk.CTkFont(family=DEFAULT_FONT, size=10, weight="bold"))
            key_label.pack(side="left")
            self.home_key_labels[running_attr] = (key_label, key_var, mod_var)

            status_label = ctk.CTkLabel(row, text="OFF", width=30,
                                        text_color="#666666", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
            status_label.pack(side="left")
            self.home_status_labels[running_attr] = status_label

            switch = ctk.CTkSwitch(row, text="", width=35, command=toggle_func)
            switch.pack(side="right")
            self.home_switches[running_attr] = switch

        # 오버레이
        overlay_box = self.create_section_box(row1, "오버레이", "🖥️")
        overlay_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.overlay_toggle_btn = ctk.CTkButton(overlay_box, text="켜기",
                                                 command=self.toggle_overlay, height=35,
                                                 fg_color="#28a745", hover_color="#218838")
        self.overlay_toggle_btn.pack(fill="x", pady=2)

        self.overlay_repos_btn = ctk.CTkButton(overlay_box, text="재배치",
                                                command=self.start_overlay_reposition, height=35,
                                                fg_color="#6c757d", hover_color="#5a6268")
        self.overlay_repos_btn.pack(fill="x", pady=2)

        alpha_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        alpha_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(alpha_frame, text="투명도", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.alpha_label = ctk.CTkLabel(alpha_frame, text="85%", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
        self.alpha_label.pack(side="right")
        ctk.CTkSlider(overlay_box, from_=0.3, to=1.0, variable=self.overlay_alpha,
                      command=self.update_overlay_alpha, height=15).pack(fill="x", pady=2)

        # 배경색
        bg_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        bg_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(bg_frame, text="배경색", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.bg_color_preview = ctk.CTkLabel(bg_frame, text="  ", width=25,
                                              fg_color=self.overlay_bg_color.get())
        self.bg_color_preview.pack(side="left", padx=5)
        ctk.CTkButton(bg_frame, text="변경", width=40, height=20,
                      command=self.change_overlay_bg_color).pack(side="left")

        # 하단 행: 설정관리 + 월드보스 + 알림
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        # 설정 관리
        save_box = self.create_section_box(row2, "설정 관리", "💾")
        save_box.master.pack(side="left", fill="both", expand=True, padx=2)

        ctk.CTkButton(save_box, text="저장", command=self.save_config,
                      fg_color="#007bff", hover_color="#0056b3", height=30).pack(fill="x", pady=1)
        ctk.CTkButton(save_box, text="불러오기", command=lambda: self.load_config(show_message=True),
                      fg_color="#17a2b8", hover_color="#138496", height=30).pack(fill="x", pady=1)
        ctk.CTkButton(save_box, text="📤 내보내기", command=self.export_config,
                      fg_color="#fd7e14", hover_color="#e96b00", height=30).pack(fill="x", pady=1)
        ctk.CTkButton(save_box, text="📥 가져오기", command=self.import_config,
                      fg_color="#20c997", hover_color="#17a689", height=30).pack(fill="x", pady=1)

        # 월드 보스
        boss_box = self.create_section_box(row2, "월드 보스", "🌍")
        boss_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.home_boss_name = ctk.CTkLabel(boss_box, text="로딩 중...",
                                           font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"),
                                           text_color="#ffaa00")
        self.home_boss_name.pack(pady=5)

        self.home_boss_time = ctk.CTkLabel(boss_box, text="",
                                           font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                                           text_color="#00ff00")
        self.home_boss_time.pack()

        ctk.CTkButton(boss_box, text="🔄 새로고침", height=25, width=100,
                      command=self.refresh_world_boss,
                      fg_color="#555555").pack(pady=5)

        # 알림 + 긴급 정지 (합쳐서 한 박스로)
        alert_emergency_box = self.create_section_box(row2, "알림 / 긴급정지", "🔔")
        alert_emergency_box.master.pack(side="left", fill="both", expand=True, padx=2)

        # 월드보스 알림
        boss_alert_row = ctk.CTkFrame(alert_emergency_box, fg_color="transparent")
        boss_alert_row.pack(fill="x", pady=3)
        ctk.CTkLabel(boss_alert_row, text="월드보스 알림", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkSwitch(boss_alert_row, text="", variable=self.boss_alert_enabled, width=40).pack(side="right")

        # 구분선
        ctk.CTkFrame(alert_emergency_box, height=1, fg_color="#444444").pack(fill="x", pady=5)

        # 긴급 정지 키
        key_row = ctk.CTkFrame(alert_emergency_box, fg_color="transparent")
        key_row.pack(fill="x", pady=3)
        ctk.CTkLabel(key_row, text="긴급정지:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        self.emergency_key_display = ctk.CTkLabel(key_row, text="F12",
                                                   font=ctk.CTkFont(family=DEFAULT_FONT, size=13, weight="bold"),
                                                   text_color="#ff4444")
        self.emergency_key_display.pack(side="left", padx=5)
        ctk.CTkButton(key_row, text="변경", width=45, height=22,
                      command=self.change_emergency_key).pack(side="right")

        # Home 탭 상태 업데이트 시작
        self.update_home_status()

    # =========================================
    # 벨리알 컨텐츠
    # =========================================
    def create_belial_content(self, parent):
        """벨리알 컨텐츠 생성"""
        self.main_frame = parent

        # 상단 행
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 타겟 색상
        color_box = self.create_section_box(row1, "타겟 색상", "🎨")
        color_box.master.pack(side="left", fill="both", expand=True, padx=2)
        self.color_section_parent = color_box
        self.create_color_section_content(color_box)

        # 제외 색상
        exclude_box = self.create_section_box(row1, "제외 색상", "🚫")
        exclude_box.master.pack(side="left", fill="both", expand=True, padx=2)
        self.create_exclude_section_content(exclude_box)

        # 하단 행
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        # 설정
        settings_box = self.create_section_box(row2, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)
        self.create_settings_section_content(settings_box)

        # 검색 영역
        area_box = self.create_section_box(row2, "검색 영역", "📐")
        area_box.master.pack(side="left", fill="both", expand=True, padx=2)
        self.create_area_section_content(area_box)

        # 컨트롤
        ctrl_box = self.create_section_box(row2, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)
        self.create_control_section_content(ctrl_box)

    def create_color_section_content(self, parent):
        """타겟 색상 섹션 내용"""
        # 색상 리스트
        self.color_listbox = tk.Listbox(parent, height=5, bg='#2b2b2b', fg='white',
                                        selectbackground='#1a5f2a', font=('맑은 고딕', 9))
        self.color_listbox.pack(fill="x", pady=5)

        # 버튼들
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="화면추출", width=70, height=28,
                      command=self.start_screen_picker, fg_color="#28a745").pack(side="left", padx=1)
        ctk.CTkButton(btn_frame, text="직접입력", width=70, height=28,
                      command=self.add_color_manual, fg_color="#17a2b8").pack(side="left", padx=1)
        ctk.CTkButton(btn_frame, text="삭제", width=50, height=28,
                      command=self.remove_color, fg_color="#dc3545").pack(side="left", padx=1)

        self.picker_status = ctk.CTkLabel(parent, text="", text_color="#00bfff", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
        self.picker_status.pack(pady=2)

    def create_exclude_section_content(self, parent):
        """제외 색상 섹션 내용"""
        self.exclude_listbox = tk.Listbox(parent, height=5, bg='#2b2b2b', fg='white',
                                          selectbackground='#dc3545', font=('맑은 고딕', 9))
        self.exclude_listbox.pack(fill="x", pady=5)

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="화면추출", width=70, height=28,
                      command=self.start_exclude_picker, fg_color="#fd7e14").pack(side="left", padx=1)
        ctk.CTkButton(btn_frame, text="직접입력", width=70, height=28,
                      command=self.add_exclude_manual, fg_color="#17a2b8").pack(side="left", padx=1)
        ctk.CTkButton(btn_frame, text="삭제", width=50, height=28,
                      command=self.remove_exclude_color, fg_color="#dc3545").pack(side="left", padx=1)

    def create_settings_section_content(self, parent):
        """설정 섹션 내용"""
        # 색상 허용 오차
        tol_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tol_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(tol_frame, text="색상 오차:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkEntry(tol_frame, textvariable=self.color_tolerance, width=50).pack(side="right")

        # 클릭 딜레이
        delay_frame = ctk.CTkFrame(parent, fg_color="transparent")
        delay_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(delay_frame, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkEntry(delay_frame, textvariable=self.click_delay, width=50).pack(side="right")

        # 핫키
        key_frame = ctk.CTkFrame(parent, fg_color="transparent")
        key_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(key_frame, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkButton(key_frame, text="변경", width=40, height=22,
                      command=self.change_trigger_key).pack(side="right", padx=2)
        self.key_display = ctk.CTkLabel(key_frame, text="",
                                         font=ctk.CTkFont(family=DEFAULT_FONT, size=11, weight="bold"),
                                         text_color="#00ff00")
        self.key_display.pack(side="right", padx=3)
        ctk.CTkLabel(key_frame, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="right")
        ctk.CTkComboBox(key_frame, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.trigger_modifier, width=60, height=22).pack(side="right", padx=2)

    def create_area_section_content(self, parent):
        """검색 영역 섹션 내용"""
        # 전체 화면 체크박스
        ctk.CTkCheckBox(parent, text="전체 화면", variable=self.use_full_screen,
                        command=self.toggle_area_mode).pack(anchor="w", pady=2)

        # 영역 버튼 프레임
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=2)

        # 영역 설정 버튼
        self.area_btn = ctk.CTkButton(btn_frame, text="영역 설정", height=28,
                                      command=self.start_area_selection,
                                      fg_color="#6c757d", width=80)
        self.area_btn.pack(side="left", padx=2)

        # 영역 보기/끄기 버튼
        self.area_show_btn = ctk.CTkButton(btn_frame, text="영역 보기", height=28,
                                           command=self.show_area_overlay,
                                           fg_color="#17a2b8", width=80)
        self.area_show_btn.pack(side="left", padx=2)

        # 현재 영역 표시
        self.area_label = ctk.CTkLabel(parent, text="영역: 전체 화면",
                                       font=ctk.CTkFont(family=DEFAULT_FONT, size=10), text_color="#888888")
        self.area_label.pack(pady=2)

    def toggle_area_mode(self):
        """전체 화면 모드 토글"""
        if self.use_full_screen.get():
            self.area_btn.configure(state="disabled")
            self.area_label.configure(text="영역: 전체 화면")
        else:
            self.area_btn.configure(state="normal")
            x1, y1 = self.search_x1.get(), self.search_y1.get()
            x2, y2 = self.search_x2.get(), self.search_y2.get()
            self.area_label.configure(text=f"영역: ({x1},{y1}) ~ ({x2},{y2})")

    def start_area_selection(self):
        """검색 영역 선택 시작"""
        self.select_area()

    def create_control_section_content(self, parent):
        """컨트롤 섹션 내용"""
        self.start_btn = ctk.CTkButton(parent, text="▶ 시작", height=40,
                                       command=self.toggle_running,
                                       fg_color="#28a745", hover_color="#218838",
                                       font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"))
        self.start_btn.pack(fill="x", pady=5)

        self.status_label = ctk.CTkLabel(parent, text="⏸️ 대기 중",
                                         font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.status_label.pack(pady=5)

    # =========================================
    # 신화장난꾸러기 컨텐츠
    # =========================================
    def create_inventory_content(self, parent):
        """신화장난꾸러기 컨텐츠 생성"""
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 보존 색상
        color_box = self.create_section_box(row1, "보존 색상", "🎨")
        color_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.inv_color_preview = ctk.CTkFrame(color_box, width=50, height=30, fg_color="#000000")
        self.inv_color_preview.pack(pady=5)

        color_row = ctk.CTkFrame(color_box, fg_color="transparent")
        color_row.pack(fill="x")
        ctk.CTkEntry(color_row, textvariable=self.inv_keep_color, width=80).pack(side="left", padx=2)
        ctk.CTkButton(color_row, text="추출", width=50, height=28,
                      command=self.inv_pick_color, fg_color="#28a745").pack(side="left", padx=2)

        tol_row = ctk.CTkFrame(color_box, fg_color="transparent")
        tol_row.pack(fill="x", pady=5)
        ctk.CTkLabel(tol_row, text="허용오차:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkEntry(tol_row, textvariable=self.inv_tolerance, width=50).pack(side="right")

        # 설정
        settings_box = self.create_section_box(row1, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=2)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=40, height=22,
                      command=self.change_inv_trigger_key).pack(side="right", padx=2)
        self.inv_key_display = ctk.CTkLabel(key_row, text="",
                                             font=ctk.CTkFont(family=DEFAULT_FONT, size=11, weight="bold"),
                                             text_color="#00ff00")
        self.inv_key_display.pack(side="right", padx=3)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.inv_trigger_modifier, width=60, height=22).pack(side="right", padx=2)

        delay_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        delay_row.pack(fill="x", pady=2)
        ctk.CTkLabel(delay_row, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkEntry(delay_row, textvariable=self.inv_delay, width=50).pack(side="right")

        # 컨트롤
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.inv_start_btn = ctk.CTkButton(ctrl_box, text="▶ 시작", height=40,
                                           command=self.toggle_inv_running,
                                           fg_color="#28a745",
                                           font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"))
        self.inv_start_btn.pack(fill="x", pady=5)

        self.inv_status_label = ctk.CTkLabel(ctrl_box, text="⏸️ 대기 중",
                                             font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.inv_status_label.pack(pady=5)

        self.inv_progress_label = ctk.CTkLabel(ctrl_box, text="",
                                                font=ctk.CTkFont(family=DEFAULT_FONT, size=11),
                                                text_color="#00aaff")
        self.inv_progress_label.pack(pady=2)

        # === 영역 설정 (두 번째 줄) ===
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        # 인벤토리 영역
        inv_area_box = self.create_section_box(row2, "인벤토리 영역", "📦")
        inv_area_box.master.pack(side="left", fill="both", expand=True, padx=2)

        inv_area_btn_frame = ctk.CTkFrame(inv_area_box, fg_color="transparent")
        inv_area_btn_frame.pack(fill="x", pady=2)

        ctk.CTkButton(inv_area_btn_frame, text="영역 설정", height=28, width=80,
                      command=self.select_inv_area, fg_color="#6c757d").pack(side="left", padx=2)
        ctk.CTkButton(inv_area_btn_frame, text="영역 보기", height=28, width=80,
                      command=self.show_inv_area_overlay, fg_color="#17a2b8").pack(side="left", padx=2)

        grid_frame = ctk.CTkFrame(inv_area_box, fg_color="transparent")
        grid_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(grid_frame, text="열:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        ctk.CTkEntry(grid_frame, textvariable=self.inv_cols, width=40).pack(side="left", padx=2)
        ctk.CTkLabel(grid_frame, text="행:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left", padx=5)
        ctk.CTkEntry(grid_frame, textvariable=self.inv_rows, width=40).pack(side="left", padx=2)

        # 설명 패널 영역
        desc_area_box = self.create_section_box(row2, "설명 패널 영역", "📋")
        desc_area_box.master.pack(side="left", fill="both", expand=True, padx=2)

        ctk.CTkButton(desc_area_box, text="영역 설정", height=28,
                      command=self.select_desc_area, fg_color="#6c757d").pack(fill="x", pady=2)

        ctk.CTkLabel(desc_area_box, text="💡 아이템 설명이 나오는 영역",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=10), text_color="#888888").pack(pady=5)

    # =========================================
    # 아이템 버리기 컨텐츠
    # =========================================
    def create_discard_content(self, parent):
        """아이템 버리기 컨텐츠 생성"""
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 설정
        settings_box = self.create_section_box(row1, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=5)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=45, height=25,
                      command=self.change_discard_trigger_key).pack(side="right", padx=2)
        self.discard_key_display = ctk.CTkLabel(key_row, text="",
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                                 text_color="#00ff00")
        self.discard_key_display.pack(side="right", padx=5)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.discard_trigger_modifier, width=65, height=25).pack(side="right", padx=2)

        delay_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        delay_row.pack(fill="x", pady=5)
        ctk.CTkLabel(delay_row, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkEntry(delay_row, textvariable=self.discard_delay, width=60).pack(side="right")

        # 컨트롤
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.discard_start_btn = ctk.CTkButton(ctrl_box, text="▶ 시작", height=50,
                                               command=self.toggle_discard_running,
                                               fg_color="#28a745",
                                               font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"))
        self.discard_start_btn.pack(fill="x", pady=10)

        self.discard_status_label = ctk.CTkLabel(ctrl_box, text="⏸️ 대기 중",
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=14))
        self.discard_status_label.pack(pady=10)

        ctk.CTkLabel(ctrl_box, text="💡 마우스를 아이템 위에 놓고\n핫키를 누르면 Ctrl+클릭 반복",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#888888").pack(pady=5)

    # =========================================
    # 아이템 먹기 컨텐츠
    # =========================================
    def create_consume_content(self, parent):
        """아이템 먹기 컨텐츠 생성"""
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 설정
        settings_box = self.create_section_box(row1, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=5)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=45, height=25,
                      command=self.change_consume_trigger_key).pack(side="right", padx=2)
        self.consume_key_display = ctk.CTkLabel(key_row, text="",
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                                 text_color="#00ff00")
        self.consume_key_display.pack(side="right", padx=5)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.consume_trigger_modifier, width=65, height=25).pack(side="right", padx=2)

        delay_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        delay_row.pack(fill="x", pady=5)
        ctk.CTkLabel(delay_row, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkEntry(delay_row, textvariable=self.consume_delay, width=60).pack(side="right")

        action_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        action_row.pack(fill="x", pady=5)
        ctk.CTkLabel(action_row, text="누를 키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(action_row, text="변경", width=45, height=25,
                      command=self.change_consume_action_key).pack(side="right", padx=2)
        self.consume_action_display = ctk.CTkLabel(action_row, text=self.consume_action_key.get().upper(),
                                                    font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                                    text_color="#ffaa00")
        self.consume_action_display.pack(side="right", padx=5)

        # 컨트롤
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.consume_start_btn = ctk.CTkButton(ctrl_box, text="▶ 시작", height=50,
                                               command=self.toggle_consume_running,
                                               fg_color="#28a745",
                                               font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"))
        self.consume_start_btn.pack(fill="x", pady=10)

        self.consume_status_label = ctk.CTkLabel(ctrl_box, text="⏸️ 대기 중",
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=14))
        self.consume_status_label.pack(pady=10)

        ctk.CTkLabel(ctrl_box, text="💡 선택한 키를 반복해서 누름",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#888888").pack(pady=5)

    # =========================================
    # 아이템 팔기 컨텐츠
    # =========================================
    def create_sell_content(self, parent):
        """아이템 팔기 컨텐츠 생성"""
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 설정
        settings_box = self.create_section_box(row1, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=5)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=45, height=25,
                      command=self.change_sell_trigger_key).pack(side="right", padx=2)
        self.sell_key_display = ctk.CTkLabel(key_row, text="",
                                              font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                              text_color="#00ff00")
        self.sell_key_display.pack(side="right", padx=5)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.sell_trigger_modifier, width=65, height=25).pack(side="right", padx=2)

        delay_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        delay_row.pack(fill="x", pady=5)
        ctk.CTkLabel(delay_row, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkEntry(delay_row, textvariable=self.sell_delay, width=60).pack(side="right")

        # 컨트롤
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.sell_start_btn = ctk.CTkButton(ctrl_box, text="▶ 시작", height=50,
                                            command=self.toggle_sell_running,
                                            fg_color="#28a745",
                                            font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"))
        self.sell_start_btn.pack(fill="x", pady=10)

        self.sell_status_label = ctk.CTkLabel(ctrl_box, text="⏸️ 대기 중",
                                              font=ctk.CTkFont(family=DEFAULT_FONT, size=14))
        self.sell_status_label.pack(pady=10)

        ctk.CTkLabel(ctrl_box, text="💡 상점에서 우클릭 반복",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#888888").pack(pady=5)

    # =========================================
    # 사용법 컨텐츠
    # =========================================
    def create_help_content(self, parent):
        """사용법 컨텐츠 생성"""
        # 스크롤 가능한 프레임
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 제목
        ctk.CTkLabel(scroll, text="📖 사용법 안내",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=20, weight="bold")).pack(pady=(10, 5))

        ctk.CTkLabel(scroll, text="💡 모든 기능은 핫키를 다시 누르면 멈춥니다!",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=13, weight="bold"),
                     text_color="#00ff00").pack(pady=(0, 15))

        # 사용법 섹션들
        help_sections = [
            ("👁️ 벨리알 (아이템 줍기)",
             "바닥에 떨어진 아이템을 자동으로 클릭해서 줍습니다.\n\n"
             "1. [화면추출] 버튼 클릭\n"
             "2. 게임 화면에서 아이템 이름 색상 클릭\n"
             "3. [시작] 버튼으로 기능 켜기\n"
             "4. 게임에서 핫키 누르면 자동 줍기 시작\n"
             "5. 다시 핫키 누르면 멈춤\n\n"
             "※ 제외 색상: 줍지 말아야 할 아이템 색상 등록"),
            ("✨ 신화장난꾸러기 (인벤 정리)",
             "인벤토리에서 신화 장난꾸러기만 즐겨찾기 등록합니다.\n\n"
             "1. [추출] 버튼으로 보존할 색상 등록\n"
             "2. [영역 설정]으로 인벤토리 영역 드래그\n"
             "3. [시작] 버튼으로 기능 켜기\n"
             "4. 게임에서 핫키 누르면 자동 즐겨찾기 시작\n"
             "5. 다시 핫키 누르면 멈춤\n\n"
             "※ 스페이스바로 즐겨찾기 등록됩니다"),
            ("🗑️ 아이템 버리기",
             "인벤토리의 아이템을 Ctrl+클릭으로 버립니다.\n\n"
             "1. [시작] 버튼으로 기능 켜기\n"
             "2. 게임에서 인벤토리 열기\n"
             "3. 버릴 아이템 위에 마우스 올리기\n"
             "4. 핫키 누르면 Ctrl+클릭 반복 시작\n"
             "5. 다시 핫키 누르면 멈춤"),
            ("💰 아이템 팔기",
             "상점에서 아이템을 우클릭으로 판매합니다.\n\n"
             "1. [시작] 버튼으로 기능 켜기\n"
             "2. 게임에서 상점 열기\n"
             "3. 팔 아이템 위에 마우스 올리기\n"
             "4. 핫키 누르면 우클릭 반복 시작\n"
             "5. 다시 핫키 누르면 멈춤"),
            ("🍖 아이템 먹기",
             "설정한 키를 빠르게 반복합니다.\n\n"
             "1. [누를 키]에서 사용할 키 설정 (예: 우클릭)\n"
             "2. [시작] 버튼으로 기능 켜기\n"
             "3. 사용할 아이템 위에 마우스 올리기\n"
             "4. 핫키 누르면 설정한 키 빠르게 반복\n"
             "5. 다시 핫키 누르면 멈춤"),
            ("🛑 긴급 정지",
             "실행 중인 클릭/매크로를 즉시 멈춥니다.\n\n"
             "• 기본 키: F12\n"
             "• Home 탭에서 키 변경 가능\n"
             "• 기능은 켜진 상태로 유지됩니다\n"
             "• 버그로 클릭이 안 멈출 때 사용!"),
        ]

        for title, content in help_sections:
            # 섹션 박스
            box = ctk.CTkFrame(scroll, fg_color="#363636", corner_radius=10)
            box.pack(fill="x", pady=6, padx=10)

            # 헤더
            header = ctk.CTkFrame(box, fg_color="#1a5f2a", corner_radius=8)
            header.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(header, text=title,
                         font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                         text_color="white").pack(padx=15, pady=8)

            # 내용
            ctk.CTkLabel(box, text=content,
                         font=ctk.CTkFont(family=DEFAULT_FONT, size=11),
                         text_color="#dddddd", justify="left", anchor="w").pack(fill="x", padx=15, pady=(0, 12))

    # =========================================
    # 패치노트 컨텐츠
    # =========================================
    def create_patch_content(self, parent):
        """패치노트 컨텐츠 생성"""
        ctk.CTkLabel(parent, text="📋 패치노트",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(parent, text=f"현재 버전: v{VERSION}",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14), text_color="#00aaff").pack(pady=5)

        self.patch_notes_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.patch_notes_container.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(self.patch_notes_container, text="로딩 중...").pack(pady=20)

        ctk.CTkButton(parent, text="🔄 새로고침", width=120,
                      command=self.fetch_patch_notes).pack(pady=10)

        threading.Thread(target=self.fetch_patch_notes, daemon=True).start()

    # =========================================
    # 마우스 좌표 업데이트
    # =========================================
    def update_mouse_pos(self):
        """마우스 좌표 업데이트"""
        try:
            import win32api
            x, y = win32api.GetCursorPos()
            self.coord_label.configure(text=f"마우스: ({x}, {y})")
        except:
            pass
        self.after(100, self.update_mouse_pos)
