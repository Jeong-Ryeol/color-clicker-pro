# -*- coding: utf-8 -*-
"""
메인 윈도우 UI 생성
"""

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk

from constants import VERSION, DEFAULT_FONT, COLORS


class MainWindowMixin:
    """메인 윈도우 UI 믹스인"""

    def setup_ui(self):
        """UI 설정"""
        # === 메인 컨테이너 ===
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # === 왼쪽 사이드바 ===
        self.sidebar = ctk.CTkFrame(main_container, width=140, fg_color=COLORS["sidebar"], corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=(5, 0), pady=5)
        self.sidebar.pack_propagate(False)

        # 사이드바 헤더
        ctk.CTkLabel(self.sidebar, text="Wonryeol",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=(15, 0))
        ctk.CTkLabel(self.sidebar, text="Helper",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                     text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self.sidebar, text=f"v{VERSION}",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=10),
                     text_color=COLORS["text_muted"]).pack(pady=(2, 15))

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
                                        font=ctk.CTkFont(family=DEFAULT_FONT, size=9), text_color=COLORS["text_muted"])
        self.coord_label.pack(pady=10)

        # === 오른쪽 컨텐츠 영역 ===
        self.content_area = ctk.CTkFrame(main_container, fg_color=COLORS["background"], corner_radius=10)
        self.content_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 컨텐츠 프레임들 저장
        self.content_frames = {}

        # === 각 컨텐츠 생성 ===
        # Home
        self.content_frames["home"] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.create_home_content(self.content_frames["home"])

        # 사용법
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
        self.main_frame = self.content_frames["belial"]
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

    def update_mouse_pos(self):
        """마우스 좌표 업데이트"""
        try:
            import win32api
            x, y = win32api.GetCursorPos()
            self.coord_label.configure(text=f"마우스: ({x}, {y})")
        except:
            pass
        self.after(100, self.update_mouse_pos)
