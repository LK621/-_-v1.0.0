"""
file_scanner.py
VirusTotal을 이용하여 파일의 악성 여부를 검사합니다.
"""

import os


def scan_file(file_path: str, vt_client) -> dict:
    """
    파일을 VirusTotal로 검사합니다.

    반환값 형태:
    {
        "file_path": str, "file_name": str, "sha256": str | None,
        "malicious_count": int, "suspicious_count": int, "total_engines": int,
        "is_dangerous": bool, "summary": str, "errors": [str, ...],
    }
    """
    result = {
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "sha256": None,
        "malicious_count": 0,
        "suspicious_count": 0,
        "total_engines": 0,
        "is_dangerous": False,
        "summary": "",
        "errors": [],
    }

    if not vt_client or not vt_client.is_configured():
        result["errors"].append("VirusTotal API 키가 설정되지 않았습니다.")
        result["summary"] = "검사를 수행할 수 없습니다 (API 키 확인 필요)."
        return result

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 32:
        result["errors"].append(
            f"파일 크기({file_size_mb:.1f}MB)가 32MB를 초과하여 업로드할 수 없습니다."
        )
        result["summary"] = "파일이 너무 큽니다."
        return result

    try:
        result["sha256"] = vt_client.compute_sha256(file_path)
        report = vt_client.scan_file(file_path)
        attributes = report.get("data", {}).get("attributes", {})
        stats = attributes.get("last_analysis_stats") or attributes.get("stats", {})
        if stats:
            result["malicious_count"] = stats.get("malicious", 0)
            result["suspicious_count"] = stats.get("suspicious", 0)
            result["total_engines"] = sum(stats.values())
            if result["malicious_count"] > 0 or result["suspicious_count"] > 0:
                result["is_dangerous"] = True
    except Exception as e:
        result["errors"].append(f"VirusTotal 오류: {e}")

    if result["is_dangerous"]:
        result["summary"] = (
            f"⚠️ 위험: {result['malicious_count']}개 엔진이 악성으로 탐지했습니다."
        )
    elif result["errors"]:
        result["summary"] = "검사 중 오류가 발생했습니다."
    else:
        result["summary"] = "✅ 안전: 알려진 악성 위협이 발견되지 않았습니다."

    return result
