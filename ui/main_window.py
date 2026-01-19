# -*- coding: utf-8 -*-
"""
메인 윈도우 UI 및 컨텐츠 생성
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
import threading

from constants import VERSION, DEFAULT_FONT, COLORS


def create_numeric_entry(parent, variable, width=50, is_float=True):
    """숫자 입력용 안전한 Entry 생성 (빈 값 허용, 변수 연동)"""
    entry = ctk.CTkEntry(parent, width=width)
    entry.insert(0, str(variable.get()))

    def on_focus_out(event):
        try:
            val = entry.get().strip()
            if val == "":
                val = "0"
            if is_float:
                variable.set(float(val))
            else:
                variable.set(int(val))
        except ValueError:
            entry.delete(0, "end")
            entry.insert(0, str(variable.get()))

    def on_variable_change(*args):
        """변수 변경 시 Entry 업데이트"""
        current = entry.get()
        new_val = str(variable.get())
        if current != new_val:
            entry.delete(0, "end")
            entry.insert(0, new_val)

    entry.bind("<FocusOut>", on_focus_out)
    variable.trace_add("write", on_variable_change)
    return entry


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
            ("🛒 사기", "consume2"),
            ("💰 팔기", "sell"),
            ("⚡ 스킬", "skill_auto"),
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

        # 아이템 사기 (먹기 V2)
        self.content_frames["consume2"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_consume2_content(self.content_frames["consume2"])

        # 아이템 팔기
        self.content_frames["sell"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_sell_content(self.content_frames["sell"])

        # 스킬 자동 사용
        self.content_frames["skill_auto"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_skill_auto_content(self.content_frames["skill_auto"])

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
            ("사기", self.consume2_trigger_key, self.consume2_trigger_modifier, "consume2_running", self.home_toggle_consume2),
            ("팔기", self.sell_trigger_key, self.sell_trigger_modifier, "sell_running", self.home_toggle_sell),
            ("스킬P1", self.skill_presets[0]['trigger_key'], self.skill_presets[0]['trigger_modifier'], "skill_p0_running", lambda: self.toggle_skill_preset_running(0)),
            ("스킬P2", self.skill_presets[1]['trigger_key'], self.skill_presets[1]['trigger_modifier'], "skill_p1_running", lambda: self.toggle_skill_preset_running(1)),
            ("스킬P3", self.skill_presets[2]['trigger_key'], self.skill_presets[2]['trigger_modifier'], "skill_p2_running", lambda: self.toggle_skill_preset_running(2)),
            ("스킬P4", self.skill_presets[3]['trigger_key'], self.skill_presets[3]['trigger_modifier'], "skill_p3_running", lambda: self.toggle_skill_preset_running(3)),
            ("스킬P5", self.skill_presets[4]['trigger_key'], self.skill_presets[4]['trigger_modifier'], "skill_p4_running", lambda: self.toggle_skill_preset_running(4)),
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

        # 크기
        scale_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        scale_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(scale_frame, text="크기", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.scale_label = ctk.CTkLabel(scale_frame, text="100%", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
        self.scale_label.pack(side="right")
        ctk.CTkSlider(overlay_box, from_=0.7, to=1.5, variable=self.overlay_scale,
                      command=self.update_overlay_scale, height=15).pack(fill="x", pady=2)

        # 가로 크기
        scale_w_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        scale_w_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(scale_w_frame, text="가로", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.scale_w_label = ctk.CTkLabel(scale_w_frame, text="100%", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
        self.scale_w_label.pack(side="right")
        ctk.CTkSlider(overlay_box, from_=0.7, to=1.5, variable=self.overlay_scale_w,
                      command=self.update_overlay_scale_w, height=15).pack(fill="x", pady=2)

        # 세로 크기
        scale_h_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        scale_h_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(scale_h_frame, text="세로", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.scale_h_label = ctk.CTkLabel(scale_h_frame, text="100%", font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
        self.scale_h_label.pack(side="right")
        ctk.CTkSlider(overlay_box, from_=0.7, to=1.5, variable=self.overlay_scale_h,
                      command=self.update_overlay_scale_h, height=15).pack(fill="x", pady=2)

        # 배경색
        bg_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        bg_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(bg_frame, text="배경색", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        self.bg_color_preview = ctk.CTkLabel(bg_frame, text="  ", width=25,
                                              fg_color=self.overlay_bg_color.get())
        self.bg_color_preview.pack(side="left", padx=5)
        ctk.CTkButton(bg_frame, text="변경", width=40, height=20,
                      command=self.change_overlay_bg_color).pack(side="left")

        # 빠른 버튼 UI
        quick_btn_frame = ctk.CTkFrame(overlay_box, fg_color="transparent")
        quick_btn_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(quick_btn_frame, text="빠른버튼", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        ctk.CTkSwitch(quick_btn_frame, text="", variable=self.quick_btn_enabled, width=40).pack(side="right")
        ctk.CTkButton(quick_btn_frame, text="설정", width=40, height=20,
                      command=self.open_detect_settings).pack(side="right", padx=5)

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
        create_numeric_entry(tol_frame, self.color_tolerance, width=50, is_float=False).pack(side="right")

        # 클릭 딜레이
        delay_frame = ctk.CTkFrame(parent, fg_color="transparent")
        delay_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(delay_frame, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        create_numeric_entry(delay_frame, self.click_delay, width=50, is_float=True).pack(side="right")

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

        self.inv_color_preview = ctk.CTkFrame(color_box, width=50, height=30, fg_color=self.inv_keep_color.get())
        self.inv_color_preview.pack(pady=5)

        color_row = ctk.CTkFrame(color_box, fg_color="transparent")
        color_row.pack(fill="x")
        inv_color_entry = ctk.CTkEntry(color_row, textvariable=self.inv_keep_color, width=80)
        inv_color_entry.pack(side="left", padx=2)
        inv_color_entry.bind("<KeyRelease>", lambda e: self.update_inv_color_preview())
        ctk.CTkButton(color_row, text="추출", width=50, height=28,
                      command=self.inv_pick_color, fg_color="#28a745").pack(side="left", padx=2)

        tol_row = ctk.CTkFrame(color_box, fg_color="transparent")
        tol_row.pack(fill="x", pady=5)
        ctk.CTkLabel(tol_row, text="허용오차:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
        create_numeric_entry(tol_row, self.inv_tolerance, width=50, is_float=False).pack(side="right")

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

        # 딜레이 설정들
        move_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        move_row.pack(fill="x", pady=1)
        ctk.CTkLabel(move_row, text="이동속도:", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        create_numeric_entry(move_row, self.inv_move_duration, width=45, is_float=True).pack(side="right")

        panel_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        panel_row.pack(fill="x", pady=1)
        ctk.CTkLabel(panel_row, text="패널대기:", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        create_numeric_entry(panel_row, self.inv_panel_delay, width=45, is_float=True).pack(side="right")

        space_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        space_row.pack(fill="x", pady=1)
        ctk.CTkLabel(space_row, text="스페이스:", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        create_numeric_entry(space_row, self.inv_space_delay, width=45, is_float=True).pack(side="right")

        click_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        click_row.pack(fill="x", pady=1)
        ctk.CTkLabel(click_row, text="슬롯간격:", font=ctk.CTkFont(family=DEFAULT_FONT, size=10)).pack(side="left")
        create_numeric_entry(click_row, self.inv_click_delay, width=45, is_float=True).pack(side="right")

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
        create_numeric_entry(grid_frame, self.inv_cols, width=40, is_float=False).pack(side="left", padx=2)
        ctk.CTkLabel(grid_frame, text="행:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left", padx=5)
        create_numeric_entry(grid_frame, self.inv_rows, width=40, is_float=False).pack(side="left", padx=2)

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
        create_numeric_entry(delay_row, self.discard_delay, width=60, is_float=True).pack(side="right")

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

        self.discard_progress_label = ctk.CTkLabel(ctrl_box, text="",
                                                   font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.discard_progress_label.pack(pady=5)

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
        create_numeric_entry(delay_row, self.consume_delay, width=60, is_float=True).pack(side="right")

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

        self.consume_progress_label = ctk.CTkLabel(ctrl_box, text="",
                                                   font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.consume_progress_label.pack(pady=5)

        ctk.CTkLabel(ctrl_box, text="💡 선택한 키를 반복해서 누름",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#888888").pack(pady=5)

    # =========================================
    # 아이템 사기 컨텐츠 (먹기 V2)
    # =========================================
    def create_consume2_content(self, parent):
        """아이템 사기 컨텐츠 생성 (먹기 V2)"""
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 설정
        settings_box = self.create_section_box(row1, "설정", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=5)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=45, height=25,
                      command=self.change_consume2_trigger_key).pack(side="right", padx=2)
        self.consume2_key_display = ctk.CTkLabel(key_row, text=self.consume2_trigger_key.get().upper(),
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                                 text_color="#00ff00")
        self.consume2_key_display.pack(side="right", padx=5)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=self.consume2_trigger_modifier, width=65, height=25).pack(side="right", padx=2)

        delay_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        delay_row.pack(fill="x", pady=5)
        ctk.CTkLabel(delay_row, text="딜레이(ms):", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        create_numeric_entry(delay_row, self.consume2_delay, width=60, is_float=True).pack(side="right")

        action_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        action_row.pack(fill="x", pady=5)
        ctk.CTkLabel(action_row, text="누를 키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(action_row, text="변경", width=45, height=25,
                      command=self.change_consume2_action_key).pack(side="right", padx=2)
        self.consume2_action_display = ctk.CTkLabel(action_row, text=self.consume2_action_key.get().upper(),
                                                    font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
                                                    text_color="#ffaa00")
        self.consume2_action_display.pack(side="right", padx=5)

        # 컨트롤
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        self.consume2_start_btn = ctk.CTkButton(ctrl_box, text="▶ 시작", height=50,
                                               command=self.toggle_consume2_running,
                                               fg_color="#28a745",
                                               font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"))
        self.consume2_start_btn.pack(fill="x", pady=10)

        self.consume2_status_label = ctk.CTkLabel(ctrl_box, text="⏸️ 대기 중",
                                                 font=ctk.CTkFont(family=DEFAULT_FONT, size=14))
        self.consume2_status_label.pack(pady=10)

        self.consume2_progress_label = ctk.CTkLabel(ctrl_box, text="",
                                                   font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.consume2_progress_label.pack(pady=5)

        ctk.CTkLabel(ctrl_box, text="💡 상점에서 우클릭으로 아이템 구매",
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
        create_numeric_entry(delay_row, self.sell_delay, width=60, is_float=True).pack(side="right")

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

        self.sell_progress_label = ctk.CTkLabel(ctrl_box, text="",
                                                font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        self.sell_progress_label.pack(pady=5)

        ctk.CTkLabel(ctrl_box, text="💡 상점에서 우클릭 반복",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#888888").pack(pady=5)

    # =========================================
    # 스킬 자동 사용 컨텐츠
    # =========================================
    def create_skill_auto_content(self, parent):
        """스킬 자동 사용 컨텐츠 생성 - 5개 프리셋 지원"""
        # === 프리셋 선택 탭 ===
        preset_tab_frame = ctk.CTkFrame(parent, fg_color="#2a2a4e", corner_radius=8)
        preset_tab_frame.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(preset_tab_frame, text="프리셋:",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold")).pack(side="left", padx=10)

        self.skill_preset_buttons = []
        for i in range(self.SKILL_PRESET_COUNT):
            btn = ctk.CTkButton(
                preset_tab_frame,
                text=f"P{i + 1}",
                width=50,
                height=30,
                command=lambda idx=i: self.select_skill_preset(idx),
                fg_color=COLORS["primary"] if i == 0 else "transparent",
                hover_color=COLORS["primary_hover"]
            )
            btn.pack(side="left", padx=2, pady=5)
            self.skill_preset_buttons.append(btn)

        # === 프리셋 설정 영역 (동적으로 업데이트) ===
        self.skill_preset_config_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.skill_preset_config_frame.pack(fill="both", expand=True)

        # 초기 UI 빌드 (프리셋 0)
        self.build_skill_preset_ui(0)

        # === 하단: 전체 프리셋 상태 요약 ===
        summary_box = self.create_section_box(parent, "프리셋 상태 요약", "📊")

        self.skill_preset_summary_labels = []
        summary_row = ctk.CTkFrame(summary_box, fg_color="transparent")
        summary_row.pack(fill="x", pady=5)

        for i in range(self.SKILL_PRESET_COUNT):
            preset_frame = ctk.CTkFrame(summary_row, fg_color="#2b2b2b", corner_radius=5)
            preset_frame.pack(side="left", fill="x", expand=True, padx=2, pady=2)

            ctk.CTkLabel(preset_frame, text=f"P{i + 1}",
                         font=ctk.CTkFont(family=DEFAULT_FONT, size=11, weight="bold")).pack(side="left", padx=5, pady=5)

            status_label = ctk.CTkLabel(preset_frame, text="OFF",
                                        text_color="#666666",
                                        font=ctk.CTkFont(family=DEFAULT_FONT, size=10))
            status_label.pack(side="left", padx=2)

            key_label = ctk.CTkLabel(preset_frame, text=self.skill_presets[i]['trigger_key'].get().upper(),
                                     text_color="#ff9900",
                                     font=ctk.CTkFont(family=DEFAULT_FONT, size=10, weight="bold"))
            key_label.pack(side="right", padx=5)

            self.skill_preset_summary_labels.append({
                'status': status_label,
                'key': key_label
            })

        # 도움말
        help_frame = ctk.CTkFrame(parent, fg_color="#2a2a4e", corner_radius=8)
        help_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(help_frame, text="💡 각 프리셋은 독립적인 핫키로 동시 실행 가능",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#cccccc").pack(pady=3)
        ctk.CTkLabel(help_frame, text="💡 Enter: 채팅할 때 pause / F12: 긴급정지",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#cccccc").pack(pady=(0, 3))

    def select_skill_preset(self, preset_idx):
        """프리셋 선택 시 UI 업데이트"""
        self.skill_current_preset_idx.set(preset_idx)

        # 탭 버튼 스타일 업데이트
        for i, btn in enumerate(self.skill_preset_buttons):
            if i == preset_idx:
                btn.configure(fg_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent")

        # 설정 UI 재구축
        self.build_skill_preset_ui(preset_idx)

    def build_skill_preset_ui(self, preset_idx):
        """선택된 프리셋에 대한 설정 UI 구축"""
        # 기존 내용 삭제
        for widget in self.skill_preset_config_frame.winfo_children():
            widget.destroy()

        preset = self.skill_presets[preset_idx]

        # === Row 1: 설정 + 컨트롤 ===
        row1 = ctk.CTkFrame(self.skill_preset_config_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 설정 박스
        settings_box = self.create_section_box(row1, f"설정 (프리셋 {preset_idx + 1})", "⚙️")
        settings_box.master.pack(side="left", fill="both", expand=True, padx=2)

        # 핫키 설정
        key_row = ctk.CTkFrame(settings_box, fg_color="transparent")
        key_row.pack(fill="x", pady=5)
        ctk.CTkLabel(key_row, text="핫키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="left")
        ctk.CTkButton(key_row, text="변경", width=45, height=25,
                      command=lambda: self.change_skill_preset_trigger_key(preset_idx)).pack(side="right", padx=2)

        self.skill_preset_key_display = ctk.CTkLabel(
            key_row, text=preset['trigger_key'].get().upper(),
            font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold"),
            text_color="#00ff00"
        )
        self.skill_preset_key_display.pack(side="right", padx=5)
        ctk.CTkLabel(key_row, text="+", font=ctk.CTkFont(family=DEFAULT_FONT, size=12)).pack(side="right")
        ctk.CTkComboBox(key_row, values=["없음", "Ctrl", "Alt", "Shift"],
                        variable=preset['trigger_modifier'], width=65, height=25).pack(side="right", padx=2)

        # 컨트롤 박스
        ctrl_box = self.create_section_box(row1, "컨트롤", "🎮")
        ctrl_box.master.pack(side="left", fill="both", expand=True, padx=2)

        preset['_start_btn'] = ctk.CTkButton(
            ctrl_box,
            text="⏹️ 중지" if preset['running'] else "▶️ 시작",
            height=50,
            command=lambda: self.toggle_skill_preset_running(preset_idx),
            fg_color=COLORS["danger"] if preset['running'] else COLORS["success"],
            hover_color=COLORS["danger_hover"] if preset['running'] else COLORS["success_hover"],
            font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold")
        )
        preset['_start_btn'].pack(fill="x", pady=5)

        status_text = "⏸️ 대기 중"
        if preset['running']:
            if preset['active']:
                status_text = "⚡ 스킬 실행 중..."
            else:
                status_text = f"🔴 [{preset['trigger_key'].get().upper()}] 키로 시작"

        preset['_status_label'] = ctk.CTkLabel(ctrl_box, text=status_text,
                                               font=ctk.CTkFont(family=DEFAULT_FONT, size=14))
        preset['_status_label'].pack(pady=5)

        preset['_pause_label'] = ctk.CTkLabel(ctrl_box, text="",
                                              font=ctk.CTkFont(family=DEFAULT_FONT, size=12))
        preset['_pause_label'].pack(pady=2)

        # === 스킬 슬롯 영역 ===
        slot_box = self.create_section_box(self.skill_preset_config_frame, "스킬 슬롯 (쿨타임 초 입력)", "🎯")

        preset['_slot_widgets'] = []

        for row_idx in range(3):
            slot_row = ctk.CTkFrame(slot_box, fg_color="transparent")
            slot_row.pack(fill="x", pady=5)

            for col_idx in range(3):
                slot_idx = row_idx * 3 + col_idx
                slot = preset['slots'][slot_idx]

                slot_frame = ctk.CTkFrame(slot_row, fg_color="#2b2b2b", corner_radius=8, width=150)
                slot_frame.pack(side="left", fill="both", expand=True, padx=5)

                header = ctk.CTkFrame(slot_frame, fg_color="transparent")
                header.pack(fill="x", padx=5, pady=5)
                ctk.CTkCheckBox(header, text=f"슬롯 {slot_idx + 1}",
                                variable=slot['enabled'],
                                font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold")).pack(side="left")

                key_frame = ctk.CTkFrame(slot_frame, fg_color="transparent")
                key_frame.pack(fill="x", padx=5, pady=2)
                ctk.CTkLabel(key_frame, text="키:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
                key_label = ctk.CTkLabel(key_frame, text=slot['key'].get().upper(),
                                         font=ctk.CTkFont(family=DEFAULT_FONT, size=11, weight="bold"),
                                         text_color="#00aaff")
                key_label.pack(side="left", padx=5)
                ctk.CTkButton(key_frame, text="변경", width=40, height=22,
                              command=lambda p=preset_idx, s=slot_idx: self.change_skill_preset_slot_key(p, s)).pack(side="right")

                cd_frame = ctk.CTkFrame(slot_frame, fg_color="transparent")
                cd_frame.pack(fill="x", padx=5, pady=2)
                ctk.CTkLabel(cd_frame, text="쿨타임:", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="left")
                ctk.CTkLabel(cd_frame, text="초", font=ctk.CTkFont(family=DEFAULT_FONT, size=11)).pack(side="right")
                create_numeric_entry(cd_frame, slot['cooldown'], width=50, is_float=True).pack(side="right", padx=5)

                # Hold 모드 체크박스
                hold_frame = ctk.CTkFrame(slot_frame, fg_color="transparent")
                hold_frame.pack(fill="x", padx=5, pady=(0, 5))
                ctk.CTkCheckBox(hold_frame, text="Hold",
                                variable=slot['hold'],
                                font=ctk.CTkFont(family=DEFAULT_FONT, size=10),
                                width=20, height=20,
                                checkbox_width=16, checkbox_height=16).pack(side="left")
                ctk.CTkLabel(hold_frame, text="(꾹 누르기)",
                             font=ctk.CTkFont(family=DEFAULT_FONT, size=9),
                             text_color="#888888").pack(side="left", padx=3)

                preset['_slot_widgets'].append({
                    'frame': slot_frame,
                    'key_label': key_label
                })

        # 혼령사 물총 모드
        honryeongsa_frame = ctk.CTkFrame(self.skill_preset_config_frame, fg_color="#3a2a2e", corner_radius=8)
        honryeongsa_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkCheckBox(honryeongsa_frame, text="🔫 혼령사 물총 모드",
                        variable=preset['honryeongsa_mode'],
                        font=ctk.CTkFont(family=DEFAULT_FONT, size=12, weight="bold")).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(honryeongsa_frame, text="스페이스바 누르는 동안 매크로 스페이스 입력 일시정지",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=11), text_color="#aaaaaa").pack(side="left", padx=5)

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

        # 사용법 섹션들 (상세 버전)
        help_sections = [
            ("📌 처음 사용하시는 분들께",
             "이 프로그램은 디아블로4 게임 내에서 반복 작업을 자동화해주는 도구입니다.\n\n"
             "【기본 개념】\n"
             "• 핫키: 기능을 켜고 끄는 단축키입니다 (예: F1, F2 등)\n"
             "• 시작 버튼: 핫키가 작동하도록 기능을 '대기' 상태로 만듭니다\n"
             "• 픽셀/색상: 화면의 특정 색을 인식해서 동작합니다\n\n"
             "【사용 순서】\n"
             "1. 왼쪽 메뉴에서 원하는 기능 탭 클릭\n"
             "2. 필요한 설정 완료 (색상 등록, 영역 설정 등)\n"
             "3. [▶ 시작] 버튼 클릭 → 버튼이 [⏹ 중지]로 바뀜\n"
             "4. 게임으로 돌아가서 핫키 누르면 동작 시작\n"
             "5. 다시 핫키 누르면 동작 멈춤\n\n"
             "【주의사항】\n"
             "• 긴급정지(F12): 모든 동작 즉시 멈춤\n"
             "• 프로그램은 게임 위에 항상 떠있어야 합니다"),

            ("👁️ 벨리알 (아이템 자동 줍기)",
             "바닥에 떨어진 아이템 이름 색상을 인식해서 자동으로 클릭합니다.\n\n"
             "【색상 등록 방법】\n"
             "1. 게임에서 아이템이 바닥에 떨어진 상태로 만들기\n"
             "2. 프로그램에서 [화면추출] 버튼 클릭\n"
             "3. 화면이 어두워지면서 마우스가 십자가로 변함\n"
             "4. 줍고 싶은 아이템 이름 글자 위에 마우스를 올리고 클릭\n"
             "5. 색상이 목록에 추가됨 (여러 색상 등록 가능)\n\n"
             "【제외 색상 등록】\n"
             "• 줍지 말아야 할 아이템이 있다면 [제외 색상 추출] 버튼으로 등록\n"
             "• 예: 흰색 일반 아이템 제외하고 싶을 때\n\n"
             "【검색 영역 설정】\n"
             "1. [영역 설정] 버튼 클릭\n"
             "2. 화면에서 아이템이 떨어지는 범위의 왼쪽 위 모서리 클릭\n"
             "3. 오른쪽 아래 모서리 클릭\n"
             "4. 이 영역 안에서만 아이템을 찾습니다\n\n"
             "【사용하기】\n"
             "1. [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 핫키(기본 F4) 누르면 자동 줍기 시작\n"
             "3. 다시 핫키 누르면 멈춤"),

            ("✨ 신화장난꾸러기 (인벤토리 정리)",
             "인벤토리에서 '신화 장난꾸러기' 아이템만 자동으로 즐겨찾기 등록합니다.\n"
             "나머지 아이템은 버리기 쉽게 정리됩니다.\n\n"
             "【보존할 색상 등록】\n"
             "1. 게임에서 인벤토리를 열고 신화 장난꾸러기 아이템 위에 마우스 올리기\n"
             "2. 아이템 설명창이 뜨면 '신화 장난꾸러기' 글자 확인\n"
             "3. 프로그램에서 [추출] 버튼 클릭\n"
             "4. 보라색 '신화 장난꾸러기' 글자 위 클릭\n\n"
             "【인벤토리 영역 설정】\n"
             "1. 게임에서 인벤토리 열기\n"
             "2. [인벤 영역] 버튼 클릭\n"
             "3. 인벤토리 칸들의 왼쪽 위 첫번째 칸 모서리 클릭\n"
             "4. 오른쪽 아래 마지막 칸 모서리 클릭\n\n"
             "【설명창 영역 설정】\n"
             "1. 아이템 위에 마우스 올려서 설명창 띄우기\n"
             "2. [설명 영역] 버튼 클릭\n"
             "3. 설명창 전체를 드래그로 선택\n\n"
             "【사용하기】\n"
             "1. [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 인벤토리 열고 핫키(기본 F3) 누르기\n"
             "3. 자동으로 각 칸을 확인하며 즐겨찾기 등록\n"
             "4. 완료되면 자동으로 멈춤"),

            ("🗑️ 아이템 버리기",
             "인벤토리 아이템을 Ctrl+클릭으로 빠르게 버립니다.\n\n"
             "【사용 방법】\n"
             "1. 프로그램에서 [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 인벤토리 열기 (I키)\n"
             "3. 버리고 싶은 첫 번째 아이템 위에 마우스 올리기\n"
             "4. 핫키(기본 F1) 누르기\n"
             "5. Ctrl+클릭이 빠르게 반복되면서 아이템 버려짐\n"
             "6. 다시 핫키 누르면 멈춤\n\n"
             "【팁】\n"
             "• 마우스를 옆 칸으로 천천히 움직이면 여러 아이템 버리기 가능\n"
             "• 딜레이 설정으로 버리는 속도 조절 가능"),

            ("💰 아이템 팔기",
             "상점에서 아이템을 우클릭으로 빠르게 판매합니다.\n\n"
             "【사용 방법】\n"
             "1. 프로그램에서 [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 상점 NPC와 대화해서 상점 열기\n"
             "3. 팔고 싶은 첫 번째 아이템 위에 마우스 올리기\n"
             "4. 핫키(기본 F2) 누르기\n"
             "5. 우클릭이 빠르게 반복되면서 아이템 판매됨\n"
             "6. 다시 핫키 누르면 멈춤\n\n"
             "【팁】\n"
             "• 마우스를 옆 칸으로 천천히 움직이면 여러 아이템 판매 가능"),

            ("🍖 아이템 먹기 (소비)",
             "설정한 키를 빠르게 반복합니다. 포션이나 음식 사용에 유용합니다.\n\n"
             "【누를 키 설정】\n"
             "1. '누를 키' 옆의 [변경] 버튼 클릭\n"
             "2. 새 창에서 원하는 키 누르기\n"
             "   • 우클릭: 마우스 오른쪽 버튼\n"
             "   • 좌클릭: 마우스 왼쪽 버튼\n"
             "   • 키보드 키: 아무 키나\n\n"
             "【사용 방법】\n"
             "1. [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 사용할 아이템 위에 마우스 올리기\n"
             "3. 핫키(기본 Mouse5) 누르기\n"
             "4. 설정한 키가 빠르게 반복됨\n"
             "5. 다시 핫키 누르면 멈춤\n\n"
             "【Enter로 일시정지】\n"
             "• 동작 중에 Enter 누르면 일시정지 (채팅할 때 유용)\n"
             "• 다시 Enter 누르면 재개"),

            ("🛒 아이템 사기 (구매)",
             "상점에서 아이템을 빠르게 구매합니다. '먹기'와 동일한 기능이지만\n"
             "별도 핫키로 사용할 수 있습니다.\n\n"
             "【사용 방법】\n"
             "1. [▶ 시작] 버튼 클릭\n"
             "2. 게임에서 상점 열기\n"
             "3. 구매할 아이템 위에 마우스 올리기\n"
             "4. 핫키(기본 Mouse4) 누르기\n"
             "5. 설정한 키가 빠르게 반복되며 구매됨\n"
             "6. 다시 핫키 누르면 멈춤"),

            ("⚡ 스킬 자동 사용 (5개 프리셋)",
             "설정한 쿨타임마다 스킬 키를 자동으로 눌러줍니다.\n"
             "5개의 프리셋을 만들어서 상황에 따라 다르게 사용할 수 있습니다.\n\n"
             "【프리셋 선택】\n"
             "• 상단의 P1, P2, P3, P4, P5 버튼으로 프리셋 전환\n"
             "• 각 프리셋마다 다른 스킬 조합 설정 가능\n"
             "• 여러 프리셋 동시 실행 가능\n\n"
             "【스킬 슬롯 설정】\n"
             "1. 사용할 슬롯의 체크박스 클릭해서 활성화\n"
             "2. '키' 옆 [변경] 버튼 클릭 → 누를 키 설정\n"
             "   (예: 1, 2, 3, 4 또는 좌클릭, 우클릭)\n"
             "3. '쿨타임' 칸에 초 단위로 입력\n"
             "   (예: 0.5 = 0.5초마다, 2 = 2초마다)\n\n"
             "【핫키 설정】\n"
             "• 각 프리셋마다 다른 핫키 설정 가능 (기본: F6~F10)\n"
             "• '핫키' 옆 [변경] 버튼으로 변경\n\n"
             "【사용하기】\n"
             "1. [▶ 시작] 버튼 클릭 → 오버레이에 표시됨\n"
             "2. 게임에서 핫키 누르면 스킬 자동 입력 시작\n"
             "3. 다시 핫키 누르면 멈춤\n\n"
             "【Enter로 일시정지】\n"
             "• 채팅할 때 Enter 누르면 일시정지\n"
             "• 다시 Enter 누르면 재개\n\n"
             "【혼령사 물총 모드】\n"
             "• 스페이스바를 직접 누르고 있을 때는 매크로가 스페이스 스킵"),

            ("📱 퀵버튼 (인벤토리 버튼 3개)",
             "인벤토리나 상점을 열면 화면에 [버리기] [팔기] [묶기] 버튼이 자동으로 나타납니다.\n\n"
             "【픽셀 감지 설정 - 중요!】\n"
             "프로그램이 인벤토리/상점 열림을 감지하려면 픽셀 설정이 필요합니다.\n\n"
             "◆ 픽셀1 설정 (인벤토리 감지용)\n"
             "1. 게임에서 인벤토리 열기 (I키)\n"
             "2. 화면 오른쪽 위를 보면 돋보기 아이콘이 있음\n"
             "3. 프로그램 Home 탭 → 퀵버튼 설정 → [픽셀1 추출] 클릭\n"
             "4. 돋보기 아이콘의 가장 검은색 부분 클릭\n"
             "   (돋보기 중간쯤 제일 어두운 픽셀)\n\n"
             "◆ 픽셀2 설정 (상점 감지용)\n"
             "1. 게임에서 상점 NPC와 대화해서 상점 열기\n"
             "2. 똑같이 오른쪽 위 돋보기 아이콘 찾기\n"
             "3. [픽셀2 추출] 버튼 클릭\n"
             "4. 돋보기의 검은색 부분 클릭\n\n"
             "【버튼 위치 설정】\n"
             "• 버튼이 게임 UI와 겹치면 위치 조정 필요\n"
             "• [버리기 위치], [팔기 위치], [묶기 위치] 버튼으로\n"
             "  각 버튼이 나타날 위치 클릭해서 지정\n\n"
             "【사용하기】\n"
             "1. Home 탭에서 '퀵버튼' 체크박스 켜기\n"
             "2. 게임에서 인벤토리 열면 버튼 3개 자동으로 나타남\n"
             "3. 버튼 클릭하면 해당 기능 바로 실행"),

            ("🛑 긴급 정지",
             "실행 중인 모든 동작을 즉시 멈춥니다.\n\n"
             "【사용 방법】\n"
             "• 기본 키: F12\n"
             "• 언제든 F12 누르면 모든 클릭/매크로 즉시 멈춤\n\n"
             "【키 변경】\n"
             "• Home 탭 → '긴급정지' 옆 [변경] 버튼\n"
             "• 원하는 키 누르기\n\n"
             "【참고】\n"
             "• 긴급정지 눌러도 기능은 '켜진 상태' 유지됨\n"
             "• 동작만 멈추고, 다시 핫키 누르면 재시작 가능\n"
             "• 버그로 클릭이 멈추지 않을 때 꼭 사용하세요!"),

            ("🎨 오버레이 (상태 표시창)",
             "게임 화면 위에 뜨는 작은 상태창입니다.\n"
             "각 기능의 켜짐/꺼짐 상태와 핫키를 보여줍니다.\n\n"
             "【켜기/끄기】\n"
             "• Home 탭 → [오버레이 켜기] 버튼\n\n"
             "【위치 이동】\n"
             "1. [재배치] 버튼 클릭\n"
             "2. 오버레이를 마우스로 드래그해서 원하는 위치로\n"
             "3. Enter 또는 Esc 누르면 고정\n\n"
             "【크기/투명도 조절】\n"
             "• Home 탭에서 슬라이더로 조절 가능\n\n"
             "【상태 표시 의미】\n"
             "• OFF: 기능이 꺼진 상태\n"
             "• ON: 기능이 켜졌고 핫키 대기 중\n"
             "• Working: 현재 동작 실행 중\n"
             "• Pause: 일시정지 상태"),
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
