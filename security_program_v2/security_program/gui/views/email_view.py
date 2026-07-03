"""
email_view.py
이메일 검사 화면입니다.
.eml 파일 불러오기 / 본문 직접 붙여넣기를 지원하며
본문 링크, 첨부파일, ChatGPT 피싱 분석 결과를 한 화면에 보여줍니다.
"""

import threading

import customtkinter as ctk
from tkinter import filedialog

import db
from core.email_scanner import parse_eml_file, scan_email
from gui import theme


class EmailView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._sender = ""
        self._subject = ""
        self._attachments = []
        self._build()

    def on_show(self):
        pass

    def _build(self):
        ctk.CTkLabel(self, text="✉️  이메일 검사", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(self, text="이메일 본문을 붙여넣거나 .eml 파일을 불러오세요.",
                     font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 12))

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=30, pady=(0, 8))

        ctk.CTkButton(top_row, text="📂  .eml 파일 불러오기",
                      font=theme.FONT_NORMAL, height=38, corner_radius=8,
                      fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                      hover_color=theme.COLOR_INPUT,
                      command=self._load_eml).pack(side="left", padx=(0, 10))

        ctk.CTkButton(top_row, text="✕  내용 지우기",
                      font=theme.FONT_NORMAL, height=38, corner_radius=8,
                      fg_color=theme.COLOR_CARD, text_color=theme.COLOR_SUBTEXT,
                      hover_color=theme.COLOR_INPUT,
                      command=self._clear).pack(side="left")

        self.meta_label = ctk.CTkLabel(top_row, text="", font=theme.FONT_SMALL,
                                       text_color=theme.COLOR_SUBTEXT)
        self.meta_label.pack(side="left", padx=16)

        self.email_text = ctk.CTkTextbox(self, font=theme.FONT_NORMAL, height=180,
                                         fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                                         border_width=0, corner_radius=12)
        self.email_text.pack(fill="x", padx=30)
        self.email_text.insert("end", "여기에 이메일 본문을 붙여넣으세요...")

        self.scan_btn = ctk.CTkButton(self, text="이메일 검사하기", font=theme.FONT_HEADING,
                                      height=44, corner_radius=8,
                                      fg_color=theme.COLOR_ACCENT,
                                      hover_color=theme.COLOR_ACCENT_HOVER,
                                      command=self._on_scan)
        self.scan_btn.pack(anchor="e", padx=30, pady=12)

        self.status_label = ctk.CTkLabel(self, text="", font=theme.FONT_SMALL,
                                         text_color=theme.COLOR_SUBTEXT)
        self.status_label.pack(anchor="w", padx=30, pady=(0, 4))

        self.result_box = ctk.CTkTextbox(self, font=theme.FONT_MONO, state="disabled",
                                         fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                                         border_width=0, corner_radius=12)
        self.result_box.pack(fill="both", expand=True, padx=30, pady=(0, 30))

    def _set_text(self, text):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")

    def _clear(self):
        self.email_text.delete("1.0", "end")
        self.email_text.insert("end", "여기에 이메일 본문을 붙여넣으세요...")
        self._sender = ""
        self._subject = ""
        self._attachments = []
        self.meta_label.configure(text="")
        self._set_text("")

    def _load_eml(self):
        path = filedialog.askopenfilename(title=".eml 파일 선택",
                                          filetypes=[("Email files", "*.eml"), ("All files", "*.*")])
        if not path:
            return
        try:
            parsed = parse_eml_file(path)
            self._sender = parsed["sender"]
            self._subject = parsed["subject"]
            self._attachments = parsed["attachments"]
            self.email_text.delete("1.0", "end")
            self.email_text.insert("end", parsed["body"] or "(본문 없음)")
            att_count = len(self._attachments)
            self.meta_label.configure(
                text=f"발신자: {self._sender[:30]}  |  제목: {self._subject[:30]}"
                     + (f"  |  첨부파일 {att_count}개" if att_count else "")
            )
        except Exception as e:
            self.meta_label.configure(text=f"파일 로드 오류: {e}", text_color=theme.COLOR_DANGER)

    def _on_scan(self):
        body = self.email_text.get("1.0", "end").strip()
        placeholder = "여기에 이메일 본문을 붙여넣으세요..."
        if not body or body == placeholder:
            self.status_label.configure(text="⚠  이메일 본문을 입력해주세요.", text_color=theme.COLOR_WARNING)
            return
        self.scan_btn.configure(state="disabled", text="검사 중...")
        self.status_label.configure(text="링크·첨부파일·피싱 패턴을 분석 중입니다...", text_color=theme.COLOR_SUBTEXT)
        self._set_text("")
        threading.Thread(target=self._worker, args=(body,), daemon=True).start()

    def _worker(self, body):
        try:
            result = scan_email(
                body, self.app.vt_client, self.app.sb_client, self.app.openai_client,
                sender=self._sender, subject=self._subject,
                attachment_paths=self._attachments,
            )
            text = self._format(result)
            target = self._subject or self._sender or "이메일 본문"
            db.add_scan_record("email", target, result["is_dangerous"], result["summary"])
        except Exception as e:
            text = f"오류: {e}"
        self.after(0, lambda: self._done(text))

    def _done(self, text):
        self._set_text(text)
        self.scan_btn.configure(state="normal", text="이메일 검사하기")
        self.status_label.configure(text="검사 완료", text_color=theme.COLOR_SAFE)
        self.app.refresh_dashboard()

    @staticmethod
    def _format(r):
        lines = [r["summary"], ""]
        if r["extracted_urls"]:
            lines.append(f"추출된 링크 ({len(r['extracted_urls'])}개):")
            for ur in r["url_results"]:
                flag = "⚠️" if ur["is_dangerous"] else "✅"
                lines.append(f"  {flag} {ur['url']}")
        else:
            lines.append("본문에서 링크를 찾지 못했습니다.")

        if r["attachment_results"]:
            lines.append("")
            lines.append(f"첨부파일 검사 ({len(r['attachment_results'])}개):")
            for ar in r["attachment_results"]:
                flag = "⚠️" if ar["is_dangerous"] else "✅"
                lines.append(f"  {flag} {ar['file_name']}  ({ar['malicious_count']}개 악성 탐지)")

        if r.get("ai_analysis"):
            ai = r["ai_analysis"]
            lines.append("")
            lines.append(f"ChatGPT 피싱 분석:")
            lines.append(f"  위험도 점수 : {ai.get('risk_score', 'N/A')} / 100")
            lines.append(f"  요약        : {ai.get('summary', '')}")
            for reason in ai.get("reasons") or []:
                lines.append(f"  • {reason}")

        if r["errors"]:
            lines.append("")
            lines.append("알림:")
            for e in r["errors"]:
                lines.append(f"  • {e}")
        return "\n".join(lines)
