"""
url_view.py
URL 검사 화면입니다.
단축 URL 자동 풀기 / Safe Browsing / VirusTotal 결과를 표시합니다.
"""

import threading

import customtkinter as ctk

import db
from core.url_scanner import scan_url
from gui import theme


class UrlView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._build()

    def on_show(self):
        pass

    def _build(self):
        ctk.CTkLabel(self, text="🌐  URL 검사", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(self, text="웹사이트 주소를 입력하면 악성 여부를 검사합니다.",
                     font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 20))

        card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        card.pack(fill="x", padx=30)

        ctk.CTkLabel(card, text="검사할 URL", font=theme.FONT_NORMAL,
                     text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=20, pady=(16, 4))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))

        self.url_entry = ctk.CTkEntry(row, placeholder_text="https://example.com",
                                      font=theme.FONT_NORMAL, height=42,
                                      fg_color=theme.COLOR_INPUT, border_width=0,
                                      text_color=theme.COLOR_TEXT)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self._on_scan())

        self.resolve_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(row, text="단축 URL 추적", variable=self.resolve_var,
                        font=theme.FONT_SMALL, text_color=theme.COLOR_SUBTEXT).pack(side="left", padx=(0, 10))

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

    def _on_scan(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status_label.configure(text="⚠  URL을 입력해주세요.", text_color=theme.COLOR_WARNING)
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.scan_btn.configure(state="disabled", text="검사 중...")
        self.status_label.configure(text="검사 중입니다...", text_color=theme.COLOR_SUBTEXT)
        self._set_text("")
        threading.Thread(target=self._worker, args=(url,), daemon=True).start()

    def _worker(self, url):
        try:
            result = scan_url(url, self.app.vt_client, self.app.sb_client,
                              resolve=self.resolve_var.get())
            text = self._format(result)
            db.add_scan_record("url", url, result["is_dangerous"], result["summary"])
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
        lines.append(f"입력 URL      : {r['url']}")
        if r["resolved_url"] != r["url"]:
            lines.append(f"최종 목적지    : {r['resolved_url']}")
        lines.append("")
        lines.append(f"VirusTotal 악성 탐지 : {r['malicious_count']}건")
        lines.append(f"VirusTotal 의심 탐지 : {r['suspicious_count']}건")
        if r.get("safe_browsing"):
            matches = r["safe_browsing"].get("matches")
            if matches:
                threat_types = ", ".join(m.get("threatType", "") for m in matches)
                lines.append(f"Google Safe Browsing : 위협 발견 [{threat_types}]")
            else:
                lines.append("Google Safe Browsing : 위협 없음")
        if r["errors"]:
            lines.append("")
            lines.append("알림:")
            for e in r["errors"]:
                lines.append(f"  • {e}")
        return "\n".join(lines)
