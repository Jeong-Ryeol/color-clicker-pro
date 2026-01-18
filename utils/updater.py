# -*- coding: utf-8 -*-
"""
자동 업데이트 기능
"""

import os
import sys
import threading
import urllib.request
import json
from tkinter import messagebox
import customtkinter as ctk

from constants import VERSION, GITHUB_API, GITHUB_REPO, APP_DIR, DEFAULT_FONT


class UpdaterMixin:
    """자동 업데이트 믹스인"""

    def check_for_updates(self):
        """시작 시 업데이트 확인 (백그라운드 스레드에서 실행)"""
        try:
            req = urllib.request.Request(GITHUB_API)
            req.add_header('User-Agent', 'WonryeolHelper')

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

            latest_version = data['tag_name'].lstrip('v')
            if self.compare_versions(latest_version, VERSION) > 0:
                self.after(0, lambda: self.show_update_dialog(data))
        except Exception as e:
            print(f"업데이트 확인 실패 (무시됨): {e}")

    def compare_versions(self, v1, v2):
        """버전 비교 (v1 > v2: 1, v1 < v2: -1, 같으면: 0)"""
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]

        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0

    def show_update_dialog(self, release_data):
        """업데이트 확인 다이얼로그"""
        latest_version = release_data['tag_name'].lstrip('v')
        release_title = release_data.get('name', '') or f'v{latest_version}'
        release_body = release_data.get('body', '') or '변경 사항 없음'

        dialog = ctk.CTkToplevel(self)
        dialog.title("업데이트 알림")
        dialog.geometry("450x500")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 500) // 2
        dialog.geometry(f"450x500+{x}+{y}")

        self.update_result = False

        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main_frame, fg_color="#1a5f2a", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="새 버전이 있습니다!",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=18, weight="bold"),
                     text_color="white").pack(pady=15)

        ctk.CTkLabel(main_frame,
                     text=f"v{VERSION}  →  v{latest_version}",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=16, weight="bold"),
                     text_color="#00aaff").pack(pady=(15, 5))

        ctk.CTkLabel(main_frame, text=release_title,
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                     text_color="#ffaa00").pack(pady=(10, 5))

        notes_frame = ctk.CTkFrame(main_frame, fg_color="#2b2b2b", corner_radius=8, height=200)
        notes_frame.pack(fill="x", padx=20, pady=10)
        notes_frame.pack_propagate(False)

        notes_text = ctk.CTkTextbox(notes_frame, font=ctk.CTkFont(family=DEFAULT_FONT, size=12),
                                     fg_color="#2b2b2b", wrap="word")
        notes_text.pack(fill="both", expand=True, padx=5, pady=5)
        notes_text.insert("1.0", release_body)
        notes_text.configure(state="disabled")

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent", height=60)
        btn_frame.pack(fill="x", padx=20, pady=20, side="bottom")

        def on_update():
            self.update_result = True
            dialog.destroy()

        def on_cancel():
            self.update_result = False
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="업데이트", width=150, height=40,
                      fg_color="#1a5f2a", hover_color="#2a7f3a",
                      font=ctk.CTkFont(family=DEFAULT_FONT, size=14, weight="bold"),
                      command=on_update).pack(side="left", expand=True, padx=10)
        ctk.CTkButton(btn_frame, text="나중에", width=150, height=40,
                      fg_color="#555555", hover_color="#666666",
                      font=ctk.CTkFont(family=DEFAULT_FONT, size=14),
                      command=on_cancel).pack(side="right", expand=True, padx=10)

        dialog.wait_window()

        if self.update_result:
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    threading.Thread(target=self.download_and_update, args=(download_url,), daemon=True).start()
                    return

            messagebox.showerror("오류", "다운로드할 EXE 파일을 찾을 수 없습니다.")

    def download_and_update(self, download_url):
        """업데이트 다운로드 및 적용"""
        try:
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
                exe_dir = os.path.dirname(current_exe)
                new_exe = os.path.join(exe_dir, 'WonryeolHelper_new.exe')
                backup_exe = os.path.join(exe_dir, 'WonryeolHelper_backup.exe')
            else:
                self.after(0, lambda: messagebox.showinfo("알림",
                    "소스 코드 실행 중에는 자동 업데이트가 지원되지 않습니다.\nGitHub에서 최신 버전을 다운로드하세요."))
                return

            self.after(0, self.show_update_progress)

            # 기존 임시 파일 정리
            for f in [new_exe, backup_exe]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

            # 다운로드 (GitHub 리다이렉트 처리)
            req = urllib.request.Request(download_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
            req.add_header('Accept', 'application/octet-stream')

            with urllib.request.urlopen(req, timeout=180) as response:
                file_data = response.read()
                with open(new_exe, 'wb') as f:
                    f.write(file_data)

            # 다운로드 검증 (최소 10MB)
            file_size = os.path.getsize(new_exe)
            if file_size < 10000000:
                raise Exception(f"파일이 불완전합니다 ({file_size // 1048576}MB). 인터넷 연결을 확인하세요.")

            batch_content = f'''@echo off
chcp 65001 > nul
title Wonryeol Helper Updater
echo ========================================
echo   Wonryeol Helper 업데이트 중...
echo ========================================
echo.
echo 프로그램 종료 대기 중...
timeout /t 3 /nobreak > nul

echo 기존 파일 백업 중...
if exist "{backup_exe}" del /f /q "{backup_exe}" 2>nul
timeout /t 1 /nobreak > nul

:move_current
move /y "{current_exe}" "{backup_exe}" 2>nul
if errorlevel 1 (
    echo 프로그램이 아직 실행 중입니다. 재시도...
    timeout /t 2 /nobreak > nul
    goto move_current
)

echo 새 버전 적용 중...
copy /y "{new_exe}" "{current_exe}" > nul
if errorlevel 1 (
    echo 업데이트 실패! 복원 중...
    move /y "{backup_exe}" "{current_exe}"
    echo.
    echo 오류가 발생했습니다. 아무 키나 누르세요...
    pause > nul
    exit /b 1
)

echo.
echo ========================================
echo   업데이트 완료!
echo ========================================
echo.
echo 프로그램을 다시 실행해주세요.
echo.
timeout /t 3 /nobreak > nul
del /f /q "{backup_exe}" 2>nul
del /f /q "{new_exe}" 2>nul
(goto) 2>nul & del /f /q "%~f0"
'''
            batch_path = os.path.join(exe_dir, 'update.bat')
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)

            self.after(0, lambda: messagebox.showinfo("업데이트 완료",
                "업데이트가 다운로드되었습니다.\n\n프로그램을 종료하고 업데이트를 적용합니다.\n\n※ 확인 버튼 클릭 후 약 10초간 기다려주세요!\n\n완료 후 프로그램을 다시 실행해주세요!"))

            import subprocess
            os.chdir(exe_dir)
            subprocess.Popen(f'cmd /c "{batch_path}"', shell=True)
            self.after(500, self.quit)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("업데이트 실패",
                f"업데이트 중 오류:\n{e}\n\nGitHub에서 직접 다운로드해주세요:\nhttps://github.com/{GITHUB_REPO}/releases"))

    def show_update_progress(self):
        """업데이트 진행 중 표시"""
        self.update_dialog = ctk.CTkToplevel(self)
        self.update_dialog.title("업데이트 중")
        self.update_dialog.geometry("300x100")
        self.update_dialog.transient(self)
        self.update_dialog.grab_set()

        ctk.CTkLabel(self.update_dialog, text="업데이트 다운로드 중...",
                     font=ctk.CTkFont(family=DEFAULT_FONT, size=14)).pack(pady=20)
        ctk.CTkLabel(self.update_dialog, text="잠시만 기다려주세요",
                     text_color="gray").pack()
