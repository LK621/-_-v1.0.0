"""
openai_client.py
ChatGPT(OpenAI) API를 사용하여 이메일/텍스트의 피싱 가능성을 분석합니다.
문서: https://platform.openai.com/docs/api-reference/chat
API 키 발급: https://platform.openai.com/api-keys
"""

import json

import requests

API_URL = "Your Key"
SYSTEM_PROMPT = (
    "당신은 보안 분석가입니다. 사용자가 제공하는 이메일이나 텍스트가 "
    "피싱(phishing), 사기, 악성 시도일 가능성을 분석하세요. "
    "반드시 아래 JSON 형식으로만 답변하고, 다른 설명은 절대 추가하지 마세요.\n"
    '{"risk_score": 0-100 사이 정수, "is_suspicious": true 또는 false, '
    '"reasons": ["근거1", "근거2"], "summary": "한국어 한 줄 요약"}'
)


# 보안 상담 챗봇용 시스템 프롬프트
CHATBOT_SYSTEM_PROMPT = (
    "당신은 친절하고 신뢰할 수 있는 사이버보안 전문가 비서입니다. "
    "사용자의 보안 관련 질문(피싱/스미싱 식별, 비밀번호 관리, 악성코드 대응, "
    "개인정보 보호, 네트워크/Wi-Fi 보안, 계정 탈취 대응, 금융 사기 예방 등)에 "
    "정확하고 실용적인 조언을 한국어로 제공하세요. "
    "전문 용어는 쉬운 말로 풀어서 설명하고, 필요하면 단계별로 안내하세요. "
    "답변은 너무 길지 않게, 핵심을 명확히 전달하세요. "
    "단, 악성코드 제작, 해킹 공격 방법, 타인 계정 무단 접근, 불법 사찰 등 "
    "악의적이거나 불법적인 요청에는 절대 답변하지 말고, 정중히 거절하며 "
    "왜 도와줄 수 없는지 짧게 안내하세요."
)


class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def analyze_text(self, text: str) -> dict:
        """텍스트(이메일 본문 등)를 분석하여 위험도(JSON)를 반환합니다."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text[:6000]},
            ],
            "temperature": 0.2,
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "risk_score": 0,
                "is_suspicious": False,
                "reasons": [],
                "summary": content,
            }

    def chat(self, conversation: list) -> str:
        """
        보안 상담 챗봇 대화를 처리합니다.
        conversation: [{"role": "user"|"assistant", "content": str}, ...] 형태의 대화 기록
        반환값: 어시스턴트의 답변 텍스트
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT}]
        messages.extend(conversation[-20:])  # 최근 20턴만 전송(토큰 절약)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
        }
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=40)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
