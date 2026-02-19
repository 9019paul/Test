# 일반 소설용 ChatGPT형 AI 설계

이 문서는 작가가 대략 아웃라인을 입력하면, 이를 바탕으로 완성형 소설 에피소드를 생성하는 ChatGPT형 시스템의 설계를 설명합니다.
요구사항은 일반 소설 창작에 맞춰 정리했으며, 성인물/노골적 콘텐츠 생성 로직은 포함하지 않습니다.

## 1) 목표와 핵심 요구사항

- 입력: 작가의 간단한 아웃라인
- 출력: 자연스러운 한국어 소설 본문
- 제어 요소:
  - 문체(서정적, 건조한, 미스터리 톤 등)
  - 시점(1인칭/3인칭/전지적)
  - 대사 비율(예: 20~40%)
  - 분량(예: 6,000~8,000자)
- 강제 규칙:
  - 본문에 괄호 문자 제거
  - 대사는 큰따옴표만 사용
  - 문체 일관성 유지

---

## 2) 시스템 아키텍처

### A. 컴포넌트

1. API 레이어
   - FastAPI 엔드포인트 제공
   - 요청 검증, 응답 포맷팅

2. Prompt Builder
   - 사용자 요청을 시스템 프롬프트 + 사용자 프롬프트로 조립
   - 스타일/시점/분량/금지 규칙 반영

3. Generation Engine
   - LLM 호출
   - 필요 시 장문 생성을 위한 2단계 생성
     - 단계1: 상세 아웃라인 확장
     - 단계2: 본문 생성

4. Post Processor
   - 괄호 제거
   - 인용부호 정규화
   - 길이 검사 및 재생성/추가 생성

5. Validator
   - 금지 규칙 준수 여부 검사
   - 분량 범위 검사
   - 대사 비율 근사 검사

### B. 처리 흐름

1. 요청 수신
2. Pydantic 스키마 검증
3. Prompt 생성
4. LLM 1차 생성
5. 후처리
6. 규칙 검증
7. 실패 시 재시도 전략 실행
8. 최종 결과 반환

---

## 3) 프롬프트 템플릿 설계

아래는 실제 운영에서 사용할 수 있는 템플릿 예시입니다.

### 3-1. 시스템 프롬프트 템플릿

```text
당신은 한국어 장편 소설 전문 작가 어시스턴트다.
입력된 아웃라인을 바탕으로 자연스럽고 몰입감 있는 소설 본문을 작성하라.

절대 규칙:
1) 본문에는 괄호 문자를 사용하지 않는다.
2) 인물 대사는 반드시 큰따옴표로 표기한다.
3) 문체와 시점을 처음부터 끝까지 일관되게 유지한다.
4) 소설 본문만 출력한다. 메타 설명, 요약, 항목 목록은 출력하지 않는다.

작성 규칙:
- 지정된 시점, 문체, 분량, 대사 비율을 준수한다.
- 감정선과 장면 전환이 자연스럽게 이어지도록 작성한다.
- 감각 묘사와 인물 심리 묘사를 충분히 포함한다.
```

### 3-2. 사용자 프롬프트 템플릿

```text
아래 조건으로 소설을 작성해줘.

아웃라인:
{outline}

설정:
- 문체: {style}
- 시점: {point_of_view}
- 목표 분량: {target_chars}자
- 허용 분량 범위: {min_chars}~{max_chars}자
- 목표 대사 비율: {dialogue_ratio}%

작성 지침:
- 장면을 생략하지 말고 자연스럽게 전개해줘.
- 대사는 큰따옴표를 사용해.
- 괄호 문자를 사용하지 마.
- 본문만 출력해.
```

### 3-3. 재시도 프롬프트 템플릿

```text
이전 결과를 아래 기준에 맞게 수정해서 다시 작성해줘.

문제점:
{violations}

수정 기준:
- 분량: {min_chars}~{max_chars}자
- 괄호 문자 완전 제거
- 대사는 큰따옴표만 사용
- 문체 일관성 유지

수정본은 소설 본문만 출력.
```

---

## 4) 금지 규칙 적용 로직

### 4-1. 규칙 정의

1. 괄호 제거
   - 제거 대상: 소괄호, 대괄호, 중괄호, 꺾쇠 등
   - 단순 문자 삭제 + 필요 시 공백 정리

2. 큰따옴표 대사
   - 대사 추정 패턴에서 작은따옴표를 큰따옴표로 정규화
   - 한국어 따옴표 변형 기호도 표준 큰따옴표로 통일 가능

3. 문체 일관성
   - 휴리스틱 검사:
     - 문장 종결 어미 분포 검사
     - 1인칭과 3인칭 혼용 탐지
     - 지나친 구어체 전환 탐지
   - 위반 시 재생성 지시

### 4-2. 검증/보정 파이프라인

1. Raw 생성 결과 수신
2. sanitize_text
   - 괄호 문자 제거
   - 줄바꿈 정리
3. normalize_quotes
   - 작은따옴표/변형 인용부호를 큰따옴표로 통일
4. validate_constraints
   - 길이 범위
   - 괄호 포함 여부
   - 대사 따옴표 규칙
   - 시점/문체 일관성 점수
5. 실패 시 retry_generate
   - 위반 항목만 요약해 재프롬프트

---

## 5) FastAPI API 스펙

### 5-1. 엔드포인트

- `POST /v1/novel/generate`
  - 아웃라인 기반 소설 생성
- `POST /v1/novel/validate`
  - 생성 결과 규칙 검증만 수행

### 5-2. 요청/응답 스키마

#### GenerateRequest

```json
{
  "outline": "폭우가 내리던 밤, 오래된 역에서 두 사람이 재회한다.",
  "style": "서정적이고 섬세한 문체",
  "point_of_view": "3인칭 제한 시점",
  "min_chars": 6000,
  "max_chars": 8000,
  "dialogue_ratio": 30,
  "temperature": 0.8,
  "max_retries": 2
}
```

#### GenerateResponse

```json
{
  "text": "소설 본문...",
  "char_count": 7124,
  "validation": {
    "length_ok": true,
    "no_brackets": true,
    "quote_rule_ok": true,
    "style_consistency_ok": true,
    "violations": []
  },
  "meta": {
    "retries": 1,
    "model": "gpt-4.1"
  }
}
```

---

## 6) Python/FastAPI 예시 코드

아래 코드는 개념 검증용 예시입니다.
환경에 맞게 실제 LLM SDK 호출부를 교체하면 바로 확장 가능합니다.

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint, confloat


app = FastAPI(title="Novel Writer API", version="0.1.0")


class GenerateRequest(BaseModel):
    outline: str = Field(..., min_length=10)
    style: str = Field(..., min_length=2)
    point_of_view: Literal["1인칭", "3인칭", "전지적"]
    min_chars: conint(ge=500, le=50000) = 6000
    max_chars: conint(ge=500, le=50000) = 8000
    dialogue_ratio: conint(ge=0, le=100) = 30
    temperature: confloat(ge=0.0, le=2.0) = 0.8
    max_retries: conint(ge=0, le=5) = 2


class ValidationResult(BaseModel):
    length_ok: bool
    no_brackets: bool
    quote_rule_ok: bool
    style_consistency_ok: bool
    violations: List[str]


class GenerateResponse(BaseModel):
    text: str
    char_count: int
    validation: ValidationResult
    meta: dict


BRACKET_PATTERN = re.compile(r"[\(\)\[\]\{\}<>]")


def build_system_prompt() -> str:
    return (
        "당신은 한국어 소설 전문 작가 어시스턴트다. "
        "입력 아웃라인을 기반으로 완성된 소설 본문만 작성하라. "
        "본문에는 괄호 문자를 쓰지 말고, 대사는 반드시 큰따옴표를 사용하라. "
        "문체와 시점을 끝까지 일관되게 유지하라."
    )


def build_user_prompt(req: GenerateRequest) -> str:
    return f"""
아래 조건으로 소설을 작성해줘.

아웃라인:
{req.outline}

설정:
- 문체: {req.style}
- 시점: {req.point_of_view}
- 허용 분량: {req.min_chars}~{req.max_chars}자
- 목표 대사 비율: {req.dialogue_ratio}%

규칙:
- 괄호 문자를 사용하지 마.
- 대사는 큰따옴표만 사용.
- 본문만 출력.
""".strip()


def sanitize_text(text: str) -> str:
    text = BRACKET_PATTERN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def normalize_quotes(text: str) -> str:
    # 작은따옴표/변형 따옴표를 큰따옴표로 단순 정규화
    text = text.replace("‘", '"').replace("’", '"')
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("'", '"')
    return text


def heuristic_style_consistency(text: str, pov: str) -> bool:
    # 단순 휴리스틱 예시: 시점 혼용 탐지
    if pov == "1인칭":
        third_person_markers = ["그는", "그녀는", "그들이"]
        count = sum(text.count(m) for m in third_person_markers)
        return count < 30
    if pov == "3인칭":
        first_person_markers = ["나는", "내가", "내게"]
        count = sum(text.count(m) for m in first_person_markers)
        return count < 30
    return True


def validate_constraints(text: str, req: GenerateRequest) -> ValidationResult:
    violations: List[str] = []

    char_count = len(text)
    length_ok = req.min_chars <= char_count <= req.max_chars
    if not length_ok:
        violations.append(f"분량 위반: {char_count}자")

    no_brackets = BRACKET_PATTERN.search(text) is None
    if not no_brackets:
        violations.append("괄호 문자 포함")

    # 간단 규칙: 작은따옴표가 남아있으면 실패
    quote_rule_ok = "'" not in text and "‘" not in text and "’" not in text
    if not quote_rule_ok:
        violations.append("대사 따옴표 규칙 위반")

    style_consistency_ok = heuristic_style_consistency(text, req.point_of_view)
    if not style_consistency_ok:
        violations.append("시점/문체 일관성 낮음")

    return ValidationResult(
        length_ok=length_ok,
        no_brackets=no_brackets,
        quote_rule_ok=quote_rule_ok,
        style_consistency_ok=style_consistency_ok,
        violations=violations,
    )


async def call_llm(system_prompt: str, user_prompt: str, temperature: float) -> str:
    # 실제 환경에서는 OpenAI/사내 LLM SDK 호출로 교체
    # 아래는 예시 더미 구현
    return (
        "비가 창문을 두드리는 소리가 오래된 역사의 벽을 타고 흘렀다. "
        "...중략... "
        "\"이제는 떠나지 않을게\" 라고 그가 말했다."
    )


@app.post("/v1/novel/generate", response_model=GenerateResponse)
async def generate_novel(req: GenerateRequest):
    if req.min_chars > req.max_chars:
        raise HTTPException(status_code=400, detail="min_chars는 max_chars보다 클 수 없습니다.")

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(req)

    last_text = ""
    last_validation = None

    for attempt in range(req.max_retries + 1):
        raw = await call_llm(system_prompt, user_prompt, req.temperature)
        processed = normalize_quotes(sanitize_text(raw))
        validation = validate_constraints(processed, req)

        last_text = processed
        last_validation = validation

        if not validation.violations:
            return GenerateResponse(
                text=processed,
                char_count=len(processed),
                validation=validation,
                meta={"retries": attempt, "model": "your-model-name"},
            )

        user_prompt = (
            build_user_prompt(req)
            + "\n\n이전 결과의 문제점: "
            + ", ".join(validation.violations)
            + "\n문제점을 모두 해결해서 다시 작성해줘."
        )

    return GenerateResponse(
        text=last_text,
        char_count=len(last_text),
        validation=last_validation,
        meta={"retries": req.max_retries, "model": "your-model-name", "warning": "조건 미충족 결과 반환"},
    )


class ValidateRequest(BaseModel):
    text: str
    point_of_view: Literal["1인칭", "3인칭", "전지적"]
    min_chars: conint(ge=1) = 6000
    max_chars: conint(ge=1) = 8000


@app.post("/v1/novel/validate", response_model=ValidationResult)
async def validate_text(req: ValidateRequest):
    dummy = GenerateRequest(
        outline="dummy outline text",
        style="dummy style",
        point_of_view=req.point_of_view,
        min_chars=req.min_chars,
        max_chars=req.max_chars,
    )
    return validate_constraints(req.text, dummy)
```

---

## 7) 운영 팁

- 장문 품질을 높이려면 1회 생성보다 분할 생성이 안정적입니다.
  - 예: 장면 1, 2, 3으로 나누어 생성 후 연결
- 문체 일관성은 프롬프트만으로 100% 보장하기 어렵기 때문에, 검증 + 재시도 루프가 핵심입니다.
- 대사 비율은 정밀 제어가 어려워 근사 제어로 설계하고 허용 오차를 두는 것이 좋습니다.

