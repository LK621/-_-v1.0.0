# 🛡 보안 검사 프로그램

ChatGPT(OpenAI) · VirusTotal · Google Safe Browsing API를 이용해
**악성 웹사이트 / 악성 파일 / 피싱 이메일**을 검사하는 GUI 프로그램입니다.

## 폴더 구조

```
security_program/
├── main.py                  # 실행 진입점
├── config.py                # API 키 저장/로드 (로컬 config.json)
├── requirements.txt
├── api_clients/
│   ├── virustotal_client.py     # VirusTotal API 연동
│   ├── safe_browsing_client.py  # Google Safe Browsing API 연동
│   └── openai_client.py         # ChatGPT API 연동 (피싱 텍스트 분석)
├── core/
│   ├── url_scanner.py        # URL 검사 로직 (위 두 API 종합)
│   ├── file_scanner.py       # 파일 검사 로직 (VirusTotal)
│   └── email_scanner.py      # 이메일 검사 로직 (.eml 파싱 + URL 추출 + ChatGPT 분석)
└── gui/
    ├── app.py     # 메인 화면 (탭: URL / 파일 / 이메일 / 설정)
    └── styles.py  # 다크 테마 디자인
```

## 1. 설치

```bash
cd security_program
pip install -r requirements.txt
```

Python 3.9 이상 권장 (tkinter는 표준 라이브러리로 보통 기본 포함되어 있습니다.
Linux에서 tkinter가 없다는 오류가 나오면 `sudo apt install python3-tk` 로 설치하세요).

## 2. 실행

```bash
python main.py
```

## 3. API 키 발급 및 입력

프로그램을 실행한 뒤 **⚙ 설정** 탭에서 아래 키를 입력하고 "저장"을 누르면
이 PC의 `~/.security_scanner/config.json` 파일에 안전하게 저장됩니다.
(키는 외부로 전송되지 않으며, 본인 PC에서 각 서비스로 직접 요청을 보낼 때만 사용됩니다.)

| 서비스 | 발급 위치 | 용도 |
|---|---|---|
| OpenAI(ChatGPT) | https://platform.openai.com/api-keys | 이메일/텍스트 피싱 패턴 분석 |
| VirusTotal | https://www.virustotal.com/gui/join-us (가입 후 프로필 > API Key) | URL/파일 악성 여부 검사 |
| Google Safe Browsing | https://console.cloud.google.com (Safe Browsing API 활성화 후 API 키 생성) | URL 악성 여부 검사 |

> ⚠️ API 키는 채팅창 등 외부에 절대 붙여넣지 말고, 프로그램의 **설정 탭**에 직접 입력하세요.

## 4. 사용법

- **🌐 URL 검사**: 검사할 주소를 입력하고 "검사하기" 클릭
- **📁 파일 검사**: "파일 선택"으로 검사할 파일을 고른 뒤 "검사하기" 클릭 (VirusTotal 무료 API는 32MB 이하 파일만 업로드 가능)
- **✉️ 이메일 검사**: 이메일 본문을 붙여넣거나 `.eml` 파일을 불러온 뒤 "이메일 검사하기" 클릭
  - 본문 속 링크를 자동 추출해 악성 여부를 검사하고, ChatGPT가 문구의 피싱 가능성을 분석합니다.

## 5. 참고 사항

- VirusTotal 무료 API는 분당 요청 수에 제한이 있습니다 (보통 분당 4회). 연속 검사 시 지연이 발생할 수 있습니다.
- 본 프로그램은 참고용 보안 진단 도구이며, 100% 탐지를 보장하지 않습니다. 의심스러운 파일/링크는 실행/접속을 피하는 것이 가장 안전합니다.
- 코드를 기능별로 분리해두었으므로 `core/` 폴더의 검사 로직만 따로 가져와 다른 프로젝트(CLI, 웹서버 등)에도 재사용할 수 있습니다.
