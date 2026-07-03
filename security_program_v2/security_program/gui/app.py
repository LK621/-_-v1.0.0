"""
app.py
CustomTkinter 기반 보안 검사 프로그램의 메인 GUI입니다.
왼쪽 사이드바로 화면을 전환하는 구조입니다.

탭 구성:
  🏠 대시보드   - 검사 통계 요약 + 최근 활동
  🌐 URL 검사   - 악성 웹사이트 검사 (단축 URL 추적 포함)
  📁 파일 검사  - VirusTotal 악성 파일 검사
  ✉️ 이메일 검사 - 피싱 이메일 검사 + 첨부파일 검사
  💬 보안 챗봇  - ChatGPT 기반 보안 상담
  🕓 검사 기록  - SQLite 기반 검사 히스토리
  ⚙ 설정       - API 키 / 화면 모드 설정
"""

import customtkinter as ctk

import config
from api_clients.openai_client import OpenAIClient
from api_clients.safe_browsing_client import SafeBrowsingClient
from api_clients.virustotal_client import VirusTotalClient
from gui import theme
from gui.views.chatbot_view import ChatbotView
from gui.views.dashboard import DashboardView
from gui.views.email_view import EmailView
from gui.views.file_view import FileView
from gui.views.history_view import HistoryView
from gui.views.settings_view import SettingsView
from gui.views.url_view import UrlView

NAV_ITEMS = [
    ("🏠", "대시보드"),
    ("🌐", "URL 검사"),
    ("📁", "파일 검사"),
    ("✉️", "이메일 검사"),
    ("💬", "보안 챗봇"),
    ("🕓", "검사 기록"),
    ("⚙", "설정"),
]


class SecurityApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("🛡  보안 검사 프로그램")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        cfg = config.load_config()
        theme.setup_appearance(cfg.get("appearance_mode", "dark"))

        self._build_clients()
        self._build_layout()
        self._show_view(0)

    # ---- API 클라이언트 ----
    def _build_clients(self):
        cfg = config.load_config()
        self.vt_client = VirusTotalClient(cfg.get("virustotal_api_key", ""))
        self.sb_client = SafeBrowsingClient(cfg.get("google_safe_browsing_api_key", ""))
        self.openai_client = OpenAIClient(
            cfg.get("openai_api_key", ""),
            cfg.get("openai_model", "gpt-4o-mini"),
        )

    def reload_clients(self):
        self._build_clients()

    def refresh_dashboard(self):
        self._views[0].refresh()

    # ---- 레이아웃 ----
    def _build_layout(self):
        # 사이드바
        self.sidebar = ctk.CTkFrame(self.root, width=200, fg_color=theme.COLOR_SIDEBAR,
                                    corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # 로고
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(24, 20), padx=16)
        ctk.CTkLabel(logo_frame, text="🛡", font=(theme.FONT_FAMILY, 28)).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="보안 검사\n프로그램",
                     font=(theme.FONT_FAMILY, 13, "bold"),
                     text_color=theme.COLOR_TEXT, justify="left").pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=theme.COLOR_CARD).pack(fill="x", padx=16, pady=(0, 12))

        # 네비게이션 버튼
        self._nav_buttons = []
        for icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                font=theme.FONT_NORMAL,
                height=44, corner_radius=8,
                anchor="w",
                fg_color="transparent",
                text_color=theme.COLOR_SUBTEXT,
                hover_color=theme.COLOR_CARD,
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_buttons.append(btn)

        # 하단 버전 표시
        ctk.CTkLabel(self.sidebar, text="v2.0  ·  Security Scanner",
                     font=theme.FONT_SMALL, text_color=theme.COLOR_SUBTEXT).pack(
            side="bottom", pady=16)

        # 콘텐츠 영역
        self.content = ctk.CTkFrame(self.root, fg_color=theme.COLOR_BG_DARK, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # 뷰 인스턴스 생성 (순서 = NAV_ITEMS 순서와 동일)
        view_classes = [DashboardView, UrlView, FileView, EmailView,
                        ChatbotView, HistoryView, SettingsView]
        self._views = []
        for cls in view_classes:
            view = cls(self.content, self)
            view.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._views.append(view)

        # 네비게이션 버튼에 커맨드 연결
        for i, btn in enumerate(self._nav_buttons):
            btn.configure(command=lambda idx=i: self._show_view(idx))

        self._current = None

    def _show_view(self, index: int):
        if self._current == index:
            return

        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color=theme.COLOR_CARD, text_color=theme.COLOR_TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=theme.COLOR_SUBTEXT)

        self._views[index].lift()
        if hasattr(self._views[index], "on_show"):
            self._views[index].on_show()
        self._current = index


def run():
    root = ctk.CTk()
    SecurityApp(root)
    root.mainloop()
