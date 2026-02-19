# Novel Writer API

아웃라인을 입력받아 일반 소설 본문 생성을 시도하는 FastAPI 서버입니다.

## 1) 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

또는

python app.py
```

## 2) 확인

```bash
curl -s http://127.0.0.1:8000/health
```

## 3) 생성 API 호출 예시

```bash
curl -s -X POST http://127.0.0.1:8000/v1/novel/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "outline": "폭우가 내리는 밤 오래된 역에서 두 사람이 재회한다.",
    "style": "서정적이고 섬세한 문체",
    "point_of_view": "3인칭",
    "min_chars": 200,
    "max_chars": 1200,
    "dialogue_ratio": 30,
    "temperature": 0.8,
    "max_retries": 1
  }'
```

## 4) OpenAI 연동 선택 사항

- `OPENAI_API_KEY` 미설정 시 더미 텍스트를 반환합니다.
- 실제 모델 사용 시:

```bash
export OPENAI_API_KEY=...your_key...
export OPENAI_MODEL=gpt-4o-mini
```


## 5) 실행이 바로 꺼지는 경우

- `python app.py`를 실행해야 서버 프로세스가 유지됩니다.
- 파일 탐색기에서 더블클릭으로 실행하면 콘솔이 즉시 닫혀 꺼진 것처럼 보일 수 있습니다.
- Windows에서 확장자가 숨겨져 있으면 `requirements`처럼 보여도 실제 파일명은 `requirements.txt`인지 확인하세요.
