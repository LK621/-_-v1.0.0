"""
email_scanner.py
이메일 본문(.eml 파일 또는 직접 입력한 텍스트)을 분석하여
피싱/악성 여부를 종합적으로 판단합니다.
- 본문에서 URL을 추출해 url_scanner로 검사
- 첨부파일을 추출해 file_scanner(VirusTotal)로 검사
- ChatGPT(OpenAI)로 텍스트 자체의 피싱 패턴을 분석
"""

import email
import os
import re
import tempfile
from email import policy

from core.file_scanner import scan_file
from core.url_scanner import scan_url

URL_REGEX = re.compile(r"https?://[^\s\"'<>\)\]]+")


def parse_eml_file(file_path: str) -> dict:
    """
    .eml 파일을 파싱하여 제목/발신자/본문/첨부파일을 추출합니다.
    첨부파일은 임시 폴더에 저장되며, 저장된 경로 목록을 반환합니다.
    """
    with open(file_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    subject = msg.get("subject", "") or ""
    sender = msg.get("from", "") or ""

    body = ""
    attachments = []

    if msg.is_multipart():
        tmp_dir = tempfile.mkdtemp(prefix="secscan_email_")
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            if content_type == "text/plain" and disposition != "attachment":
                try:
                    body += part.get_content()
                except Exception:
                    pass
            elif disposition == "attachment" or part.get_filename():
                filename = part.get_filename() or "attachment.bin"
                safe_name = os.path.basename(filename)
                save_path = os.path.join(tmp_dir, safe_name)
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        with open(save_path, "wb") as out:
                            out.write(payload)
                        attachments.append(save_path)
                except Exception:
                    continue
    else:
        body = msg.get_content()

    return {
        "subject": subject,
        "sender": sender,
        "body": body,
        "attachments": attachments,
    }


def extract_urls(text: str) -> list:
    return list(dict.fromkeys(URL_REGEX.findall(text)))  # 중복 제거, 순서 유지


def scan_email(
    email_text: str,
    vt_client,
    sb_client,
    openai_client,
    sender: str = "",
    subject: str = "",
    attachment_paths: list = None,
) -> dict:
    """
    이메일 본문(+첨부파일)을 분석합니다.

    반환값 형태:
    {
        "subject": str, "sender": str,
        "extracted_urls": [str, ...], "url_results": [dict, ...],
        "attachment_results": [dict, ...],
        "ai_analysis": dict | None, "is_dangerous": bool,
        "summary": str, "errors": [str, ...],
    }
    """
    result = {
        "subject": subject,
        "sender": sender,
        "extracted_urls": [],
        "url_results": [],
        "attachment_results": [],
        "ai_analysis": None,
        "is_dangerous": False,
        "summary": "",
        "errors": [],
    }

    # ---- 본문 내 링크 검사 ----
    urls = extract_urls(email_text)
    result["extracted_urls"] = urls

    for url in urls:
        url_result = scan_url(url, vt_client, sb_client)
        result["url_results"].append(url_result)
        if url_result["is_dangerous"]:
            result["is_dangerous"] = True

    # ---- 첨부파일 검사 ----
    for path in attachment_paths or []:
        try:
            att_result = scan_file(path, vt_client)
            result["attachment_results"].append(att_result)
            if att_result["is_dangerous"]:
                result["is_dangerous"] = True
        except Exception as e:
            result["errors"].append(f"첨부파일 검사 오류({os.path.basename(path)}): {e}")

    # ---- ChatGPT 텍스트 분석 ----
    if openai_client and openai_client.is_configured():
        try:
            full_text = f"제목: {subject}\n발신자: {sender}\n\n{email_text}"
            ai_result = openai_client.analyze_text(full_text)
            result["ai_analysis"] = ai_result
            if ai_result.get("is_suspicious") or ai_result.get("risk_score", 0) >= 60:
                result["is_dangerous"] = True
        except Exception as e:
            result["errors"].append(f"ChatGPT 분석 오류: {e}")
    else:
        result["errors"].append("OpenAI API 키가 설정되지 않았습니다.")

    if result["is_dangerous"]:
        result["summary"] = "⚠️ 위험: 이 이메일은 피싱/악성으로 의심됩니다."
    else:
        result["summary"] = "✅ 안전: 특별한 위협이 발견되지 않았습니다."

    return result
