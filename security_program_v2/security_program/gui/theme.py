"""
theme.py
CustomTkinter 기반 UI에서 사용하는 색상/폰트/레이아웃 상수와
전역 다크/라이트 모드 설정 함수를 정의합니다.
"""

import customtkinter as ctk

# ---- 색상 팔레트 (다크 테마 기준) ----
COLOR_BG_DARK = "#1a1b26"
COLOR_SIDEBAR = "#16161e"
COLOR_CARD = "#24283b"
COLOR_INPUT = "#1f2335"
COLOR_ACCENT = "#7aa2f7"
COLOR_ACCENT_HOVER = "#5d87e0"
COLOR_DANGER = "#f7768e"
COLOR_SAFE = "#9ece6a"
COLOR_WARNING = "#e0af68"
COLOR_TEXT = "#c0caf5"
COLOR_SUBTEXT = "#9099c4"

# ---- 폰트 ----
FONT_FAMILY = "맑은 고딕"
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_HEADING = (FONT_FAMILY, 15, "bold")
FONT_NORMAL = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_MONO = ("Consolas", 12)


def setup_appearance(mode: str = "dark", color_theme: str = "blue") -> None:
    """전역 다크/라이트 모드 및 색상 테마를 설정합니다."""
    try:
        ctk.set_appearance_mode(mode)
        ctk.set_default_color_theme(color_theme)
    except Exception:
        pass
