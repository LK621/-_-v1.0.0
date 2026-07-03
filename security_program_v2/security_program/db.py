"""
db.py
검사 기록(History)을 SQLite에 저장하고 조회하는 모듈입니다.
DB 파일 위치: ~/.security_scanner/history.db
"""

import os
import sqlite3
from datetime import datetime

from config import CONFIG_DIR

DB_PATH = os.path.join(CONFIG_DIR, "history.db")


def _ensure_dir() -> None:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)


def init_db() -> None:
    """검사 기록 테이블이 없으면 생성합니다."""
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_type TEXT NOT NULL,      -- 'url' | 'file' | 'email'
                target TEXT NOT NULL,         -- 검사 대상(URL, 파일명, 이메일 제목 등)
                is_dangerous INTEGER NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_scan_record(scan_type: str, target: str, is_dangerous: bool, summary: str) -> None:
    """검사 결과를 기록에 추가합니다."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO scans (scan_type, target, is_dangerous, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                scan_type,
                (target or "")[:300],
                int(is_dangerous),
                (summary or "")[:500],
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_scans(limit: int = 50) -> list:
    """최근 검사 기록을 가져옵니다 (최신순)."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "SELECT scan_type, target, is_dangerous, summary, created_at "
            "FROM scans ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "scan_type": r[0],
            "target": r[1],
            "is_dangerous": bool(r[2]),
            "summary": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


def get_stats() -> dict:
    """전체 통계(총 검사 수, 위험 탐지 수, 유형별 개수)를 반환합니다."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        total = conn.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        dangerous = conn.execute(
            "SELECT COUNT(*) FROM scans WHERE is_dangerous=1"
        ).fetchone()[0]
        by_type_rows = conn.execute(
            "SELECT scan_type, COUNT(*) FROM scans GROUP BY scan_type"
        ).fetchall()
    finally:
        conn.close()

    return {
        "total": total,
        "dangerous": dangerous,
        "safe": total - dangerous,
        "by_type": {r[0]: r[1] for r in by_type_rows},
    }


def clear_history() -> None:
    """모든 검사 기록을 삭제합니다."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM scans")
        conn.commit()
    finally:
        conn.close()
