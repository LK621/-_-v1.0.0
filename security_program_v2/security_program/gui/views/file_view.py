"""
file_view.py
파일 검사 화면입니다.
파일을 선택하면 SHA256 해시를 계산하고 VirusTotal로 검사합니다.
"""

import os
import threading

import customtkinter as ctk
from tkinter import filedialog

import db
from core.file_scanner import scan_file
from gui import theme


class FileView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._build()

    def on_show(self):
        pass

    def _build(self):
        ctk.CTkLabel(self, text="📁  파일 검사", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(self, text="파일을 선택하면 VirusTotal로 악성 여부를 검사합니다. (32MB 이하)",
                     font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 20))

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        card.pack(fill="x", padx=30)

        ctk.CTkLabel(card, text="검사할 파일", font=theme.FONT_NORMAL,
                     text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=20, pady=(16, 4))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))

        self.path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(row, textvariable=self.path_var,
                                       placeholder_text="파일 경로...",
                                       font=theme.FONT_NORMAL, height=42,
                                       fg_color=theme.COLOR_INPUT, border_width=0,
                                       text_color=theme.COLOR_TEXT)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(row, text="파일 선택", font=theme.FONT_NORMAL,
                      width=100, height=42, corner_radius=8,
                      fg_color=theme.COLOR_INPUT, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_CARD,
                      command=self._browse).pack(side="left", padx=(0, 10))

        self.scan_btn = ctk.CTkButton(row, text="검사하기", font=theme.FONT_HEADING,
                                      width=110, height=42, corner_radius=8,
                                      fg_color=theme.COLOR_ACCENT,
                                      hover_color=theme.COLOR_ACCENT_HOVER,
                                      command=self._on_scan)
        self.scan_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="", font=theme.FONT_SMALL,
                                         text_color=theme.COLOR_SUBTEXT)
        self.status_label.pack(anchor="w", padx=30, pady=(12, 4))

        self.result_box = ctk.CTkTextbox(self, font=theme.FONT_MONO, state="disabled",
                                         fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                                         border_width=0, corner_radius=12)
        self.result_box.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def _set_text(self, text):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")

    def _browse(self):
        path = filedialog.askopenfilename(title="검사할 파일 선택")
        if path:
            self.path_var.set(path)

    def _on_scan(self):
        path = self.path_var.get().strip()
        if not path or not os.path.isfile(path):
            self.status_label.configure(text="⚠  유효한 파일을 선택해주세요.", text_color=theme.COLOR_WARNING)
            return
        self.scan_btn.configure(state="disabled", text="검사 중...")
        self.status_label.configure(text="파일 해시를 계산하고 VirusTotal에 조회 중...", text_color=theme.COLOR_SUBTEXT)
        self._set_text("")
        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _worker(self, path):
        try:
            result = scan_file(path, self.app.vt_client)
            text = self._format(result)
            db.add_scan_record("file", result["file_name"], result["is_dangerous"], result["summary"])
        except Exception as e:
            text = f"오류: {e}"
        self.after(0, lambda: self._done(text))

    def _done(self, text):
        self._set_text(text)
        self.scan_btn.configure(state="normal", text="검사하기")
        self.status_label.configure(text="검사 완료", text_color=theme.COLOR_SAFE)
        self.app.refresh_dashboard()

    @staticmethod
    def _format(r):
        lines = [r["summary"], ""]
        lines.append(f"파일명    : {r['file_name']}")
        lines.append(f"SHA256   : {r['sha256'] or '계산 실패'}")
        lines.append(f"파일 경로 : {r['file_path']}")
        lines.append("")
        lines.append(f"악성 탐지 : {r['malicious_count']}건 / 의심 : {r['suspicious_count']}건")
        if r["total_engines"]:
            lines.append(f"검사 엔진 : 총 {r['total_engines']}개")
        if r["errors"]:
            lines.append("")
            lines.append("알림:")
            for e in r["errors"]:
                lines.append(f"  • {e}")
        return "\n".join(lines)
