"""
history_view.py
검사 기록(히스토리) 화면입니다.
SQLite에 저장된 검사 내역을 최신순으로 표시하고 전체 삭제를 지원합니다.
"""

import customtkinter as ctk
from tkinter import messagebox

import db
from gui import theme

TYPE_ICON = {"url": "🌐", "file": "📁", "email": "✉️"}


class HistoryView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._build()

    def on_show(self):
        self.refresh()

    def _build(self):
        # 헤더
        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.pack(fill="x", padx=30, pady=(30, 4))
        ctk.CTkLabel(header_row, text="🕓  검사 기록", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(side="left")

        ctk.CTkButton(header_row, text="새로고침", font=theme.FONT_SMALL,
                      width=90, height=34, corner_radius=8,
                      fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_INPUT,
                      command=self.refresh).pack(side="right", padx=(8, 0))

        ctk.CTkButton(header_row, text="전체 삭제", font=theme.FONT_SMALL,
                      width=90, height=34, corner_radius=8,
                      fg_color=theme.COLOR_DANGER, text_color="#ffffff",
                      hover_color="#c0394a",
                      command=self._clear_all).pack(side="right")

        ctk.CTkLabel(self, text="최근 50건의 검사 기록입니다.",
                     font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 16))

        # 컬럼 헤더
        col_frame = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=8, height=36)
        col_frame.pack(fill="x", padx=30, pady=(0, 4))
        col_frame.pack_propagate(False)
        for text, anchor, expand, width in [
            ("결과", "w", False, 60),
            ("유형", "w", False, 60),
            ("대상", "w", True, 0),
            ("요약", "w", True, 0),
            ("시각", "e", False, 150),
        ]:
            ctk.CTkLabel(col_frame, text=text, font=theme.FONT_SMALL,
                         text_color=theme.COLOR_SUBTEXT, anchor=anchor,
                         width=width if not expand else 0).pack(
                side="left", fill="x", expand=expand, padx=10, pady=6
            )

        # 스크롤 가능한 기록 목록
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        records = db.get_recent_scans(50)
        if not records:
            ctk.CTkLabel(self.list_frame, text="아직 검사 기록이 없습니다.",
                         font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(pady=20)
            return

        for rec in records:
            row = ctk.CTkFrame(self.list_frame, fg_color=theme.COLOR_CARD,
                               corner_radius=8, height=40)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            flag = "⚠️" if rec["is_dangerous"] else "✅"
            icon = TYPE_ICON.get(rec["scan_type"], "🔎")
            color = theme.COLOR_DANGER if rec["is_dangerous"] else theme.COLOR_SAFE

            ctk.CTkLabel(row, text=flag, font=theme.FONT_NORMAL,
                         text_color=color, width=50).pack(side="left", padx=6)
            ctk.CTkLabel(row, text=icon, font=theme.FONT_NORMAL,
                         text_color=theme.COLOR_TEXT, width=50).pack(side="left")
            ctk.CTkLabel(row, text=rec["target"][:45], font=theme.FONT_SMALL,
                         text_color=theme.COLOR_TEXT, anchor="w").pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(row, text=rec["summary"][:40], font=theme.FONT_SMALL,
                         text_color=theme.COLOR_SUBTEXT, anchor="w").pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(row, text=rec["created_at"][:16], font=theme.FONT_SMALL,
                         text_color=theme.COLOR_SUBTEXT, width=140).pack(side="right", padx=8)

    def _clear_all(self):
        if messagebox.askyesno("전체 삭제", "모든 검사 기록을 삭제하시겠습니까?"):
            db.clear_history()
            self.refresh()
            self.app.refresh_dashboard()
