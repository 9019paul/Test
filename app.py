from __future__ import annotations

import os
import re
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, conint, confloat

app = FastAPI(title="Novel Writer API", version="1.0.0")

BRACKET_PATTERN = re.compile(r"[\(\)\[\]\{\}<>]")


class GenerateRequest(BaseModel):
    outline: str = Field(..., min_length=10, description="작가가 작성한 아웃라인")
    style: str = Field("서정적이고 섬세한 문체", min_length=2)
    point_of_view: Literal["1인칭", "3인칭", "전지적"] = "3인칭"
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
    violations: list[str]


class GenerateResponse(BaseModel):
    text: str
    char_count: int
    validation: ValidationResult
    meta: dict


class ValidateRequest(BaseModel):
    text: str
    point_of_view: Literal["1인칭", "3인칭", "전지적"] = "3인칭"
    min_chars: conint(ge=1) = 6000
    max_chars: conint(ge=1) = 8000


def build_system_prompt() -> str:
    return (
        "당신은 한국어 장편 소설 전문 작가 어시스턴트다. "
        "입력된 아웃라인을 바탕으로 자연스럽고 몰입감 있는 소설 본문을 작성하라. "
        "본문에는 괄호 문자를 사용하지 않는다. "
        "인물 대사는 반드시 큰따옴표로 표기한다. "
        "문체와 시점을 처음부터 끝까지 일관되게 유지한다. "
        "소설 본문만 출력한다."
    )


def build_user_prompt(req: GenerateRequest, violations: list[str] | None = None) -> str:
    base = f"""
아래 조건으로 소설을 작성해줘.

아웃라인:
{req.outline}

설정:
- 문체: {req.style}
- 시점: {req.point_of_view}
- 허용 분량 범위: {req.min_chars}~{req.max_chars}자
- 목표 대사 비율: {req.dialogue_ratio}%

작성 지침:
- 장면을 생략하지 말고 자연스럽게 전개해줘.
- 대사는 큰따옴표를 사용해.
- 괄호 문자를 사용하지 마.
- 본문만 출력해.
""".strip()

    if not violations:
        return base

    return base + "\n\n이전 결과의 문제점: " + ", ".join(violations) + "\n문제점을 모두 해결해서 다시 작성해줘."


def sanitize_text(text: str) -> str:
    text = BRACKET_PATTERN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_quotes(text: str) -> str:
    text = text.replace("‘", '"').replace("’", '"')
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("'", '"')
    return text


def heuristic_style_consistency(text: str, pov: str) -> bool:
    if pov == "1인칭":
        return sum(text.count(m) for m in ["그는", "그녀는", "그들이"]) < 30
    if pov == "3인칭":
        return sum(text.count(m) for m in ["나는", "내가", "내게"]) < 30
    return True


def validate_constraints(text: str, point_of_view: str, min_chars: int, max_chars: int) -> ValidationResult:
    violations: list[str] = []

    length_ok = min_chars <= len(text) <= max_chars
    if not length_ok:
        violations.append(f"분량 위반: {len(text)}자")

    no_brackets = BRACKET_PATTERN.search(text) is None
    if not no_brackets:
        violations.append("괄호 문자 포함")

    quote_rule_ok = "'" not in text and "‘" not in text and "’" not in text
    if not quote_rule_ok:
        violations.append("대사 따옴표 규칙 위반")

    style_consistency_ok = heuristic_style_consistency(text, point_of_view)
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
    """환경변수 OPENAI_API_KEY가 없으면 더미 텍스트를 반환한다."""

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key:
        # 로컬 실행을 위한 더미 응답
        return (
            "비 냄새가 지하도 입구의 찬 공기 속으로 스며들었다. "
            "오래된 시계탑 아래에서 그는 젖은 코트 깃을 세운 채 서 있었다. "
            "그녀가 계단을 올라오자, 멈춰 있던 시간이 다시 움직였다. "
            "\"오래 기다렸어\" 그녀가 말했다. "
            "그는 잠깐 웃다가 고개를 끄덕였다. \"이번엔 도망가지 않을게\" "
            "두 사람은 빗소리 사이로 서로의 표정을 읽으며 천천히 발걸음을 맞췄다."
        )

    # 선택적으로 OpenAI SDK 사용
    try:
        from openai import AsyncOpenAI  # type: ignore
    except ImportError:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되어 있으나 openai 패키지가 없습니다.")

    client = AsyncOpenAI(api_key=api_key)
    response = await client.responses.create(
        model=model,
        temperature=temperature,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text.strip()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/novel/generate", response_model=GenerateResponse)
async def generate_novel(req: GenerateRequest) -> GenerateResponse:
    if req.min_chars > req.max_chars:
        raise HTTPException(status_code=400, detail="min_chars는 max_chars보다 클 수 없습니다.")

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(req)

    last_text = ""
    last_validation = ValidationResult(
        length_ok=False,
        no_brackets=True,
        quote_rule_ok=True,
        style_consistency_ok=True,
        violations=["생성 전 초기 상태"],
    )

    for attempt in range(req.max_retries + 1):
        raw = await call_llm(system_prompt, user_prompt, req.temperature)
        processed = normalize_quotes(sanitize_text(raw))
        validation = validate_constraints(processed, req.point_of_view, req.min_chars, req.max_chars)

        last_text = processed
        last_validation = validation

        if not validation.violations:
            return GenerateResponse(
                text=processed,
                char_count=len(processed),
                validation=validation,
                meta={"retries": attempt, "model": os.getenv("OPENAI_MODEL", "dummy")},
            )

        user_prompt = build_user_prompt(req, validation.violations)

    return GenerateResponse(
        text=last_text,
        char_count=len(last_text),
        validation=last_validation,
        meta={
            "retries": req.max_retries,
            "model": os.getenv("OPENAI_MODEL", "dummy"),
            "warning": "조건 미충족 결과 반환",
        },
    )


@app.post("/v1/novel/validate", response_model=ValidationResult)
async def validate_text(req: ValidateRequest) -> ValidationResult:
    if req.min_chars > req.max_chars:
        raise HTTPException(status_code=400, detail="min_chars는 max_chars보다 클 수 없습니다.")
    return validate_constraints(req.text, req.point_of_view, req.min_chars, req.max_chars)
