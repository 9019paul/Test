#!/usr/bin/env python3
"""사용자 설정을 바탕으로 캐릭터 시트를 이력서 형태로 생성하는 간단한 CLI 도구."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


def build_prompts(settings: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "너는 세계관 작가이자 캐릭터 디자이너다. "
        "사용자가 입력한 설정을 바탕으로, 이력서 스타일의 캐릭터 시트를 한국어로 작성하라. "
        "사실이 아닌 내용은 단정하지 말고, 필요한 경우 자연스럽게 보완하되 과도한 확장은 피하라."
    )

    user_prompt = (
        "다음 설정을 기반으로 캐릭터 시트를 작성해줘.\\n"
        "반드시 아래 섹션 순서를 지켜줘:\\n"
        "1) 기본 정보\\n"
        "2) 핵심 요약(3줄)\\n"
        "3) 성격/가치관\\n"
        "4) 능력/스킬\\n"
        "5) 배경 스토리(요약)\\n"
        "6) 약점/리스크\\n"
        "7) 추천 스토리 훅 3개\\n\\n"
        f"[입력 설정]\\n{json.dumps(settings, ensure_ascii=False, indent=2)}"
    )
    return system_prompt, user_prompt


def render_fallback_sheet(settings: dict[str, Any]) -> str:
    """LLM 없이도 사용할 수 있는 기본 템플릿 출력."""
    basic = {
        "이름": settings.get("name", "미정"),
        "성별": settings.get("gender", "미정"),
        "나이": settings.get("age", "미정"),
        "국적": settings.get("nationality", "미정"),
        "머리 색": settings.get("hair_color", "미정"),
        "직업": settings.get("job", "미정"),
        "소속/역할": settings.get("role", "미정"),
        "능력": settings.get("ability", "미정"),
    }

    lines = ["# 캐릭터 시트 (이력서 스타일)", "", "## 1) 기본 정보"]
    lines.extend(f"- {k}: {v}" for k, v in basic.items())

    personality = settings.get("personality", "침착하고 목표 지향적이며, 상황 판단이 빠름")
    values = settings.get("values", "동료 보호, 약속 준수")
    background = settings.get("background", "과거 사건을 계기로 현재 역할을 선택함")
    risk = settings.get("weakness", "감정이 격해질 때 판단력이 흔들릴 수 있음")

    lines.extend(
        [
            "",
            "## 2) 핵심 요약(3줄)",
            f"- {basic['직업']}로 활동하며 {basic['소속/역할']} 포지션을 맡고 있다.",
            f"- 주 능력은 '{basic['능력']}'이며, 실전 대응력과 문제 해결력이 강점이다.",
            f"- 핵심 동기는 '{values}'이며, 이 신념이 행동 기준이 된다.",
            "",
            "## 3) 성격/가치관",
            f"- 성격: {personality}",
            f"- 가치관: {values}",
            "",
            "## 4) 능력/스킬",
            f"- 대표 능력: {basic['능력']}",
            "- 전술 스킬: 현장 분석, 위기 대처, 팀 협업",
            "",
            "## 5) 배경 스토리(요약)",
            f"- {background}",
            "",
            "## 6) 약점/리스크",
            f"- {risk}",
            "",
            "## 7) 추천 스토리 훅 3개",
            "- 중요한 임무에서 개인 신념과 조직 규율이 충돌한다.",
            "- 주 능력의 부작용이 커져 통제법을 찾아야 한다.",
            "- 숙적(또는 과거 인연)과 재회하며 숨겨진 진실이 드러난다.",
        ]
    )
    return "\n".join(lines)


def try_generate_with_openai(system_prompt: str, user_prompt: str) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
    )
    return response.output_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="캐릭터 시트 생성기")
    parser.add_argument(
        "--input-json",
        help="캐릭터 설정 JSON 파일 경로 (예: sample_input.json)",
    )
    return parser.parse_args()


def load_settings(input_json: str | None) -> dict[str, Any]:
    if input_json:
        with open(input_json, "r", encoding="utf-8") as f:
            return json.load(f)

    # 인터랙티브 입력
    prompts = {
        "name": "이름",
        "gender": "성별",
        "age": "나이",
        "nationality": "국적",
        "hair_color": "머리 색",
        "job": "직업",
        "role": "히어로/빌런/중립 등의 역할",
        "ability": "능력",
        "personality": "성격",
        "values": "가치관",
        "background": "배경 스토리(짧게)",
        "weakness": "약점",
    }
    settings: dict[str, Any] = {}
    print("캐릭터 설정을 입력하세요. 빈 값이면 기본값이 사용됩니다.")
    for key, label in prompts.items():
        settings[key] = input(f"- {label}: ").strip()
    return settings


def main() -> None:
    args = parse_args()
    settings = load_settings(args.input_json)
    system_prompt, user_prompt = build_prompts(settings)

    generated = try_generate_with_openai(system_prompt, user_prompt)
    if generated:
        print(generated)
        return

    print(render_fallback_sheet(settings))


if __name__ == "__main__":
    main()
