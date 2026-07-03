"""
dashboard.py
프로그램 실행 시 첫 화면입니다.
검사 통계(총 검사 수 / 안전 / 위험)와 최근 검사 활동을 보여줍니다.
"""

import customtkinter as ctk

import db
from gui import theme


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self, text="대시보드", font=theme.FONT_TITLE, text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(
            self,
            text="검사 현황을 한눈에 확인하세요.",
            font=theme.FONT_NORMAL,
            text_color=theme.COLOR_SUBTEXT,
        ).pack(anchor="w", padx=30, pady=(0, 20))

        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=30)

        self.card_total = self._stat_card(stats_row, "총 검사 수", theme.COLOR_ACCENT)
        self.card_safe = self._stat_card(stats_row, "안전 판정", theme.COLOR_SAFE)
        self.card_danger = self._stat_card(stats_row, "위험 탐지", theme.COLOR_DANGER)

        ctk.CTkLabel(
            self, text="최근 검사 기록", font=theme.FONT_HEADING, text_color=theme.COLOR_TEXT
        ).pack(anchor="w", padx=30, pady=(28, 8))

        self.recent_box = ctk.CTkScrollableFrame(self, fg_color=theme.COLOR_CARD)
        self.recent_box.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def _stat_card(self, parent, label, color):
        card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=12)
        card.pack(side="left", expand=True, fill="x", padx=(0, 14))
        value_label = ctk.CTkLabel(
            card, text="0", font=(theme.FONT_FAMILY, 28, "bold"), text_color=color
        )
        value_label.pack(anchor="w", padx=18, pady=(16, 0))
        ctk.CTkLabel(
            card, text=label, font=theme.FONT_SMALL, text_color=theme.COLOR_SUBTEXT
        ).pack(anchor="w", padx=18, pady=(0, 16))
        card.value_label = value_label
        return card

    def on_show(self):
        """이 화면이 보일 때마다 최신 통계로 갱신합니다."""
        self.refresh()

    def refresh(self):
        stats = db.get_stats()
        self.card_total.value_label.configure(text=str(stats["total"]))
        self.card_safe.value_label.configure(text=str(stats["safe"]))
        self.card_danger.value_label.configure(text=str(stats["dangerous"]))

        for widget in self.recent_box.winfo_children():
            widget.destroy()

        recent = db.get_recent_scans(limit=10)
        if not recent:
            ctk.CTkLabel(
                self.recent_box,
                text="아직 검사 기록이 없습니다. URL/파일/이메일 검사를 시작해보세요.",
                font=theme.FONT_NORMAL,
                text_color=theme.COLOR_SUBTEXT,
            ).pack(anchor="w", padx=10, pady=10)
            return

        icon_map = {"url": "🌐", "file": "📁", "email": "✉️"}
        for rec in recent:
            flag = "⚠️" if rec["is_dangerous"] else "✅"
            icon = icon_map.get(rec["scan_type"], "🔎")
            row = ctk.CTkFrame(self.recent_box, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(
                row,
                text=f"{flag} {icon} {rec['target'][:60]}",
                font=theme.FONT_NORMAL,
                text_color=theme.COLOR_TEXT,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                row,
                text=rec["created_at"][:16],
                font=theme.FONT_SMALL,
                text_color=theme.COLOR_SUBTEXT,
            ).pack(side="right")
