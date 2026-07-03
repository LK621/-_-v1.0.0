"""
virustotal_client.py
VirusTotal API v3와 통신하는 클라이언트입니다.
- URL 검사
- 파일 해시 조회 / 업로드 검사
문서: https://docs.virustotal.com/reference/overview
API 키 발급: https://www.virustotal.com/gui/join-us (가입 후 프로필 > API Key)
"""

import base64
import hashlib
import time
from typing import Optional

import requests

API_BASE = "f03dc5244587b0dfc60cdf7eec017bfa9f160af92ff5b42c7b0d4d28776debf5"


class VirusTotalClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict:
        return {"x-apikey": self.api_key}

    def is_configured(self) -> bool:
        return bool(self.api_key)

    # ---------------- URL 검사 ----------------
    def submit_url(self, url: str) -> str:
        """URL을 제출하고 분석 ID를 반환합니다."""
        resp = requests.post(
            f"{API_BASE}/urls",
            headers=self._headers(),
            data={"url": url},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"]["id"]

    def get_url_report(self, url: str) -> dict:
        """이미 분석 기록이 있는 URL은 바로 조회하고, 없으면 새로 제출합니다."""
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        resp = requests.get(
            f"{API_BASE}/urls/{url_id}", headers=self._headers(), timeout=30
        )
        if resp.status_code == 404:
            analysis_id = self.submit_url(url)
            return self.wait_for_analysis(analysis_id)
        resp.raise_for_status()
        return resp.json()

    def wait_for_analysis(self, analysis_id: str, max_wait: int = 30) -> dict:
        """분석이 끝날 때까지 대기 후 결과를 반환합니다."""
        elapsed = 0
        data = {}
        while elapsed < max_wait:
            resp = requests.get(
                f"{API_BASE}/analyses/{analysis_id}",
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("data", {}).get("attributes", {}).get("status")
            if status == "completed":
                return data
            time.sleep(3)
            elapsed += 3
        return data

    # ---------------- 파일 검사 ----------------
    @staticmethod
    def compute_sha256(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_file_report_by_hash(self, file_hash: str) -> Optional[dict]:
        resp = requests.get(
            f"{API_BASE}/files/{file_hash}", headers=self._headers(), timeout=30
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, file_path: str) -> str:
        """32MB 이하 파일을 업로드하고 분석 ID를 반환합니다."""
        with open(file_path, "rb") as f:
            files = {"file": f}
            resp = requests.post(
                f"{API_BASE}/files",
                headers=self._headers(),
                files=files,
                timeout=120,
            )
        resp.raise_for_status()
        return resp.json()["data"]["id"]

    def scan_file(self, file_path: str) -> dict:
        """해시로 먼저 조회하고, 기록이 없으면 업로드 후 분석 결과를 가져옵니다."""
        file_hash = self.compute_sha256(file_path)
        report = self.get_file_report_by_hash(file_hash)
        if report is not None:
            return report

        analysis_id = self.upload_file(file_path)
        analysis = self.wait_for_analysis(analysis_id, max_wait=60)
        time.sleep(2)
        report = self.get_file_report_by_hash(file_hash)
        return report if report is not None else analysis
