"""
chatbot_view.py
ChatGPT 기반 보안 상담 챗봇 화면입니다.
보안 전문가 시스템 프롬프트로 최적화되어 있으며 대화 기록을 유지합니다.
"""

import threading

import customtkinter as ctk

from gui import theme

QUICK_QUESTIONS = [
    "📧 이 이메일이 피싱인지 어떻게 알아요?",
    "🔑 안전한 비밀번호 만드는 법",
    "📱 스미싱 문자를 받았어요",
    "🔒 2단계 인증이란 무엇인가요?",
    "💳 계좌정보가 유출됐을 때 대처법",
    "🛡 공공 Wi-Fi 사용 시 주의점",
]


class ChatbotView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._conversation = []  # [{"role": "user"|"assistant", "content": str}, ...]
        self._build()

    def on_show(self):
        self.input_entry.focus_set()

    def _build(self):
        ctk.CTkLabel(self, text="💬  보안 상담 챗봇", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(self, text="사이버보안 전문가 AI에게 무엇이든 물어보세요.",
                     font=theme.FONT_NORMAL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 12))

        # 빠른 질문 버튼 행
        quick_frame = ctk.CTkFrame(self, fg_color="transparent")
        quick_frame.pack(fill="x", padx=30, pady=(0, 12))
        for q in QUICK_QUESTIONS:
            ctk.CTkButton(quick_frame, text=q, font=theme.FONT_SMALL,
                          height=30, corner_radius=15,
                          fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                          hover_color=theme.COLOR_INPUT,
                          command=lambda text=q: self._quick_ask(text)
                          ).pack(side="left", padx=(0, 8), pady=2)

        # 대화창
        self.chat_box = ctk.CTkTextbox(self, font=theme.FONT_NORMAL, state="disabled",
                                        fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT,
                                        border_width=0, corner_radius=12, wrap="word")
        self.chat_box.pack(fill="both", expand=True, padx=30, pady=(0, 12))

        # 입력 행
        input_row = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        input_row.pack(fill="x", padx=30, pady=(0, 30))

        self.input_entry = ctk.CTkEntry(input_row, placeholder_text="보안 관련 질문을 입력하세요...",
                                         font=theme.FONT_NORMAL, height=46,
                                         fg_color="transparent", border_width=0,
                                         text_color=theme.COLOR_TEXT)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=8)
        self.input_entry.bind("<Return>", lambda e: self._on_send())

        ctk.CTkButton(input_row, text="대화 초기화", font=theme.FONT_SMALL,
                      width=90, height=36, corner_radius=8,
                      fg_color="transparent", text_color=theme.COLOR_SUBTEXT,
                      hover_color=theme.COLOR_INPUT,
                      command=self._clear_chat).pack(side="left", padx=(0, 8))

        self.send_btn = ctk.CTkButton(input_row, text="전송  ↑", font=theme.FONT_HEADING,
                                       width=90, height=36, corner_radius=8,
                                       fg_color=theme.COLOR_ACCENT,
                                       hover_color=theme.COLOR_ACCENT_HOVER,
                                       command=self._on_send)
        self.send_btn.pack(side="left", padx=(0, 8))

        self._append_chat("assistant",
                          "안녕하세요! 저는 사이버보안 전문가 AI입니다.\n"
                          "피싱 메일 식별, 비밀번호 보안, 악성코드 대응, 계정 보호 등\n"
                          "보안 관련 질문이라면 무엇이든 도와드릴게요. 😊")

    def _append_chat(self, role: str, content: str):
        self.chat_box.configure(state="normal")
        if self.chat_box.get("1.0", "end").strip():
            self.chat_box.insert("end", "\n\n")

        if role == "user":
            prefix = "나  ▶"
            color = theme.COLOR_ACCENT
        else:
            prefix = "🛡 보안 AI"
            color = theme.COLOR_SAFE

        self.chat_box.insert("end", f"{prefix}\n", "header")
        self.chat_box.insert("end", content)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _quick_ask(self, text: str):
        bare = text.split(" ", 1)[-1] if " " in text else text
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, bare)
        self._on_send()

    def _on_send(self):
        if not self.app.openai_client.is_configured():
            self._append_chat("assistant",
                              "⚠️ OpenAI API 키가 설정되지 않았습니다.\n설정 탭에서 API 키를 입력해주세요.")
            return
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, "end")
        self.send_btn.configure(state="disabled", text="...")
        self._append_chat("user", text)
        self._conversation.append({"role": "user", "content": text})
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            reply = self.app.openai_client.chat(self._conversation)
        except Exception as e:
            reply = f"오류가 발생했습니다: {e}"
        self._conversation.append({"role": "assistant", "content": reply})
        self.after(0, lambda: self._done(reply))

    def _done(self, reply: str):
        self._append_chat("assistant", reply)
        self.send_btn.configure(state="normal", text="전송  ↑")

    def _clear_chat(self):
        self._conversation = []
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")
        self._append_chat("assistant",
                          "대화가 초기화되었습니다. 새로운 보안 질문을 입력해주세요. 😊")
