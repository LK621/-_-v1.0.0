"""
safe_browsing_client.py
Google Safe Browsing API v4를 사용하여 URL의 악성 여부를 확인합니다.
문서: https://developers.google.com/safe-browsing/v4
API 키 발급: https://console.cloud.google.com (Safe Browsing API 활성화 후 API 키 생성)
"""

import requests

API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


class SafeBrowsingClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def check_url(self, url: str) -> dict:
        """URL을 검사하고 위협 매치(threatMatches) 결과를 반환합니다."""
        body = {
            "client": {"clientId": "security-scanner-app", "clientVersion": "1.0.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        resp = requests.post(
            API_URL, params={"key": self.api_key}, json=body, timeout=20
        )
        resp.raise_for_status()
        return resp.json()
