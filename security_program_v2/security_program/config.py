"""
config.py
API 키 및 환경설정을 관리하는 모듈입니다.
설정은 사용자 홈 디렉토리의 ~/.security_scanner/config.json 파일에 저장됩니다.
(API 키는 본인 PC에만 저장되며 외부로 전송되지 않습니다.)
"""

import json
import os

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".security_scanner")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "openai_api_key": "",
    "google_safe_browsing_api_key": "",
    "virustotal_api_key": "",
    "openai_model": "gpt-4o-mini",
    "appearance_mode": "dark",
}


def _ensure_config_dir() -> None:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> dict:
    """저장된 설정 파일을 불러옵니다. 없으면 기본값을 반환합니다."""
    _ensure_config_dir()
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """설정을 파일에 저장합니다."""
    _ensure_config_dir()
    current = load_config()
    current.update(config)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)


def get_api_key(name: str) -> str:
    return load_config().get(name, "")


def set_api_key(name: str, value: str) -> None:
    save_config({name: value})
