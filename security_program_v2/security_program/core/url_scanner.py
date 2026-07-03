"""
url_scanner.py
Google Safe Browsing + VirusTotal 결과를 종합하여 URL의 위험도를 평가합니다.
단축 URL(bit.ly 등)은 리다이렉트를 추적해 최종 목적지를 검사합니다.
"""

import requests


def resolve_url(url: str, timeout: int = 10) -> str:
    """
    단축 URL 등 리다이렉트를 따라가 최종 목적지 URL을 반환합니다.
    실패하면 원본 URL을 그대로 반환합니다.
    """
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.url:
            return resp.url
    except requests.RequestException:
        pass

    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout, stream=True)
        final_url = resp.url
        resp.close()
        return final_url or url
    except requests.RequestException:
        return url


def scan_url(url: str, vt_client, sb_client, resolve: bool = True) -> dict:
    """
    URL을 두 가지 엔진으로 검사하고 결과를 종합합니다.

    반환값 형태:
    {
        "url": str,                 # 사용자가 입력한 원본 URL
        "resolved_url": str,        # 리다이렉트 추적 후 최종 URL
        "safe_browsing": dict | None,
        "virustotal": dict | None,
        "malicious_count": int,
        "suspicious_count": int,
        "is_dangerous": bool,
        "summary": str,
        "errors": [str, ...],
    }
    """
    result = {
        "url": url,
        "resolved_url": url,
        "safe_browsing": None,
        "virustotal": None,
        "malicious_count": 0,
        "suspicious_count": 0,
        "is_dangerous": False,
        "summary": "",
        "errors": [],
    }

    target_url = url
    if resolve:
        try:
            resolved = resolve_url(url)
            result["resolved_url"] = resolved
            target_url = resolved
        except Exception:
            pass  # 풀기에 실패해도 원본 URL로 검사를 계속 진행합니다.

    # ---- Google Safe Browsing ----
    if sb_client and sb_client.is_configured():
        try:
            sb_result = sb_client.check_url(target_url)
            result["safe_browsing"] = sb_result
            if sb_result.get("matches"):
                result["is_dangerous"] = True
        except Exception as e:
            result["errors"].append(f"Safe Browsing 오류: {e}")
    else:
        result["errors"].append("Google Safe Browsing API 키가 설정되지 않았습니다.")

    # ---- VirusTotal ----
    if vt_client and vt_client.is_configured():
        try:
            vt_result = vt_client.get_url_report(target_url)
            result["virustotal"] = vt_result
            attributes = vt_result.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats") or attributes.get("stats", {})
            if stats:
                result["malicious_count"] = stats.get("malicious", 0)
                result["suspicious_count"] = stats.get("suspicious", 0)
                if result["malicious_count"] > 0 or result["suspicious_count"] > 0:
                    result["is_dangerous"] = True
        except Exception as e:
            result["errors"].append(f"VirusTotal 오류: {e}")
    else:
        result["errors"].append("VirusTotal API 키가 설정되지 않았습니다.")

    if result["is_dangerous"]:
        result["summary"] = "⚠️ 위험: 이 URL은 악성으로 탐지되었습니다."
    elif not result["safe_browsing"] and not result["virustotal"]:
        result["summary"] = "검사를 수행할 수 없습니다 (API 키 확인 필요)."
    else:
        result["summary"] = "✅ 안전: 알려진 악성 위협이 발견되지 않았습니다."

    return result
