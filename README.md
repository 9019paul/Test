# Character Sheet AI (Resume Style)

사용자가 입력한 설정(성별, 나이, 이름, 국적, 머리 색, 직업, 역할, 능력 등)을 바탕으로,
**이력서 스타일 캐릭터 시트**를 생성하는 CLI 예제입니다.

## 1) 설치

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Windows PowerShell

> PowerShell에서는 `source .venv/bin/activate`가 동작하지 않습니다.
> 아래 명령을 사용하세요.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

만약 실행 정책 에러가 나면(스크립트 실행 차단), 현재 세션에서만 임시 허용:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2) 실행 방법

### A. JSON 파일로 입력

```bash
python3 character_sheet_ai.py --input-json sample_input.json
```

Windows PowerShell에서는 보통 아래가 더 안정적입니다.

```powershell
python .\character_sheet_ai.py --input-json .\sample_input.json
```

### B. 터미널 인터랙티브 입력

```bash
python3 character_sheet_ai.py
```

Windows PowerShell:

```powershell
python .\character_sheet_ai.py
```

## 3) OpenAI API 사용 (선택)

API 키가 설정되어 있고 `openai` 패키지가 설치되어 있으면 LLM 기반 생성 결과를 사용합니다.
없으면 내장 템플릿으로 자동 폴백됩니다.

macOS / Linux:

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="gpt-4.1-mini"  # 선택
python3 character_sheet_ai.py --input-json sample_input.json
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_MODEL="gpt-4.1-mini"  # 선택
python .\character_sheet_ai.py --input-json .\sample_input.json
```

## 4) 커스터마이징 팁

- `build_prompts()`를 수정해 원하는 말투/형식을 지정하세요.
- `sample_input.json`의 필드를 늘려 세계관 전용 설정(소속 팀, 장비, 라이벌 등)을 넣을 수 있습니다.
- 웹 서비스로 확장하려면 FastAPI/Flask로 `settings`를 받아 같은 함수를 호출하면 됩니다.

## 5) 자주 발생하는 오류 빠른 해결

- `source` 명령어를 찾을 수 없음:
  - PowerShell에서는 `source` 대신 `\.venv\Scripts\Activate.ps1`를 사용해야 합니다.
- `pip` 명령어를 찾을 수 없음:
  - `pip` 대신 `python -m pip ...` 또는 `py -m pip ...`를 사용하세요.
- `python3` 명령어를 찾을 수 없음 (Windows):
  - `python ...` 또는 `py ...`를 사용하세요.
