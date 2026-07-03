"""
settings_view.py
설정 화면입니다.
API 키 입력/저장, 다크/라이트 모드 전환, 각 키의 설정 상태 표시를 제공합니다.
"""

import customtkinter as ctk
from tkinter import messagebox

import config
from gui import theme


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.COLOR_BG_DARK)
        self.app = app
        self._vars = {}
        self._build()

    def on_show(self):
        self._load_values()
        self._refresh_status()

    def _build(self):
        ctk.CTkLabel(self, text="⚙  설정", font=theme.FONT_TITLE,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=30, pady=(30, 4))
        ctk.CTkLabel(self,
                     text="API 키는 이 PC의 ~/.security_scanner/config.json 에만 저장됩니다. 외부로 전송되지 않습니다.",
                     font=theme.FONT_SMALL, text_color=theme.COLOR_SUBTEXT).pack(anchor="w", padx=30, pady=(0, 20))

        # ---- API 키 카드 ----
        api_card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        api_card.pack(fill="x", padx=30, pady=(0, 16))
        ctk.CTkLabel(api_card, text="API 키", font=theme.FONT_HEADING,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=20, pady=(16, 8))

        key_defs = [
            ("openai_api_key", "OpenAI (ChatGPT) API Key", "sk-..."),
            ("openai_model", "OpenAI 모델명", "gpt-4o-mini"),
            ("virustotal_api_key", "VirusTotal API Key", ""),
            ("google_safe_browsing_api_key", "Google Safe Browsing API Key", ""),
        ]
        self._status_labels = {}
        for key, label, placeholder in key_defs:
            self._vars[key] = ctk.StringVar()
            row = ctk.CTkFrame(api_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label, font=theme.FONT_SMALL,
                         text_color=theme.COLOR_SUBTEXT, width=250, anchor="w").pack(side="left")
            show = "*" if "key" in key else ""
            entry = ctk.CTkEntry(row, textvariable=self._vars[key],
                                 show=show, font=theme.FONT_NORMAL, height=36,
                                 placeholder_text=placeholder,
                                 fg_color=theme.COLOR_INPUT, border_width=0,
                                 text_color=theme.COLOR_TEXT)
            entry.pack(side="left", fill="x", expand=True)
            status = ctk.CTkLabel(row, text="", font=theme.FONT_SMALL, width=28)
            status.pack(side="left", padx=(8, 0))
            self._status_labels[key] = status

        ctk.CTkButton(api_card, text="API 키 저장", font=theme.FONT_HEADING,
                      height=42, corner_radius=8,
                      fg_color=theme.COLOR_ACCENT, hover_color=theme.COLOR_ACCENT_HOVER,
                      command=self._save).pack(anchor="e", padx=20, pady=16)

        # ---- 화면 설정 카드 ----
        ui_card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        ui_card.pack(fill="x", padx=30, pady=(0, 16))
        ctk.CTkLabel(ui_card, text="화면 설정", font=theme.FONT_HEADING,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=20, pady=(16, 8))

        mode_row = ctk.CTkFrame(ui_card, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(mode_row, text="화면 모드", font=theme.FONT_SMALL,
                     text_color=theme.COLOR_SUBTEXT, width=250, anchor="w").pack(side="left")

        cfg = config.load_config()
        self._mode_var = ctk.StringVar(value=cfg.get("appearance_mode", "dark"))
        ctk.CTkSegmentedButton(mode_row,
                               values=["dark", "light", "system"],
                               variable=self._mode_var,
                               command=self._change_mode,
                               font=theme.FONT_SMALL).pack(side="left")

        # ---- API 발급 안내 카드 ----
        help_card = ctk.CTkFrame(self, fg_color=theme.COLOR_CARD, corner_radius=12)
        help_card.pack(fill="x", padx=30, pady=(0, 30))
        ctk.CTkLabel(help_card, text="API 키 발급 안내", font=theme.FONT_HEADING,
                     text_color=theme.COLOR_TEXT).pack(anchor="w", padx=20, pady=(16, 8))
        links = [
            ("OpenAI", "https://platform.openai.com/api-keys"),
            ("VirusTotal", "https://www.virustotal.com/gui/join-us  →  프로필 > API Key"),
            ("Google Safe Browsing", "https://console.cloud.google.com  →  Safe Browsing API 활성화"),
        ]
        for name, url in links:
            ctk.CTkLabel(help_card, text=f"  • {name} : {url}",
                         font=theme.FONT_SMALL, text_color=theme.COLOR_SUBTEXT,
                         anchor="w").pack(fill="x", padx=20, pady=1)
        ctk.CTkLabel(help_card, text="", height=10).pack()

    def _load_values(self):
        cfg = config.load_config()
        for key, var in self._vars.items():
            var.set(cfg.get(key, ""))

    def _refresh_status(self):
        for key, label in self._status_labels.items():
            val = self._vars[key].get().strip()
            if key == "openai_model":
                label.configure(text="✅" if val else "❌",
                                text_color=theme.COLOR_SAFE if val else theme.COLOR_DANGER)
            else:
                label.configure(text="✅" if val else "❌",
                                text_color=theme.COLOR_SAFE if val else theme.COLOR_DANGER)

    def _save(self):
        data = {k: v.get().strip() for k, v in self._vars.items()}
        if not data.get("openai_model"):
            data["openai_model"] = "gpt-4o-mini"
        config.save_config(data)
        config.save_config({"appearance_mode": self._mode_var.get()})
        self.app.reload_clients()
        self._refresh_status()
        messagebox.showinfo("저장 완료", "API 키가 저장되고 즉시 적용되었습니다.")

    def _change_mode(self, mode: str):
        import customtkinter as ctk
        ctk.set_appearance_mode(mode)
        config.save_config({"appearance_mode": mode})
