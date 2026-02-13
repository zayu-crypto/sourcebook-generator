# Sourcebook Generator

전문가가 Learning Outcome을 입력하면, 핵심자료(이미지 포함), 핵심질문(Essential Question), 탐색큐(Search Cues)가 포함된 카드 10개를 자동으로 생성하는 웹 애플리케이션입니다.

## 기능

✨ **자동 카드 생성**: AI(Google Gemini)가 Outcome 기반으로 10개 카드 생성  
🖼️ **Wikimedia 이미지**: 각 카드에 실제 역사적 자료 이미지 자동 포함  
✅ **카드 선택**: 수업에 적합한 카드 선택  
📄 **PDF 내보내기**: 선택된 카드를 PDF로 다운로드  
💾 **JSON 저장**: 데이터를 JSON 형식으로 저장  

## 기술 스택

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python, Flask
- **AI**: Google Generative AI (Gemini)
- **Image Source**: Wikimedia Commons API
- **PDF Export**: html2pdf.js

## 🚀 빠른 시작 (배포)

**다른 사람들과 공유하고 싶다면?**

→ [DEPLOY_REPLIT.md](DEPLOY_REPLIT.md) 참고 (5분이면 끝!)  
→ Replit에서 배포하면 링크로 바로 공유 가능

## 설치 및 실행 (로컬)

### 필수 요구사항

- Python 3.9+
- Google Gemini API Key

### 1. 환경 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 `GOOGLE_GEMINI_API_KEY`를 입력합니다.

```
GOOGLE_GEMINI_API_KEY=your_api_key_here
```

[Google Gemini API Key 발급받기](https://aistudio.google.com/app/apikey)

### 2. 서버 실행

```bash
pip install -r server/requirements.txt
python3 server/app.py
```

서버는 `http://localhost:5000`에서 실행됩니다

서버는 `http://localhost:5000`에서 실행됩니다.

### 3. 클라이언트 실행

```bash
cd client
# 간단한 HTTP 서버 실행 (Python)
python -m http.server 8000

# 또는 Node.js 사용
npx http-server -p 8000
```

브라우저에서 `http://localhost:8000`으로 접속합니다.

## 사용 방법

### 1. Learning Outcome 입력
교수자가 수업의 학습 목표(Learning Outcome)을 상세히 입력합니다.

### 2. 카드 자동 생성
"카드 생성" 버튼을 클릭하면 AI가 10개의 카드를 생성합니다.

각 카드는 다음 3가지를 포함합니다:
- **원천증거**: 이론을 증명하는 실제 자료, 사례, 논문 초록 등
- **핵심질문**: 지속적인 탐구를 유도하는 본질적인 질문
- **탐색큐**: 학생들의 연구를 위한 검색어, 논문, 아카이브 위치

### 3. 카드 선택
각 카드를 클릭하거나 체크박스로 선택합니다. (최소 1개 필수)

### 4. 내보내기
- **PDF**: 선택된 카드를 인쇄 가능한 PDF로 다운로드
- **JSON**: 데이터를 JSON 형식으로 저장

## 프로젝트 구조

```
sourcebook-generator/
├── server/
│   ├── package.json        # 백엔드 의존성
│   ├── server.js           # Express 서버
│   ├── gemini.js           # Gemini AI 로직
│   └── .env.example        # 환경변수 예시
└── client/
    ├── index.html          # 메인 HTML
    ├── styles.css          # 스타일시트
    └── app.js              # 클라이언트 JavaScript
```

## Sourcebook Guideline

이 프로젝트는 다음 가이드라인을 따릅니다:

- **학습자 주도**: 학생들이 가공된 정보를 수동적으로 읽는 게 아니라, 키워드를 기반으로 스스로 탐색하도록 함
- **최소한의 정보**: 수업에 필요한 정보를 탐색하는 방향성 제시
- **본질적 질문**: 단순 정보 찾기를 넘어 지속적인 탐구를 유도하는 질문
- **Cross-talk Session**: 학생들이 그룹별로 소주제를 연구하고 상호 강의하는 방식 지원

## API 명세

### POST `/api/generate-cards`

**요청:**
```json
{
  "outcome": "Learning Outcome 텍스트"
}
```

**응답:**
```json
{
  "cards": [
    {
      "id": 1,
      "title": "카드 제목",
      "primaryEvidence": "원천증거 내용",
      "essentialQuestion": "핵심질문",
      "searchCues": ["큐1", "큐2", "큐3"]
    }
  ]
}
```

## 트러블슈팅

### "GOOGLE_GEMINI_API_KEY is not set" 경고
- `.env` 파일을 확인하고 API 키를 입력해주세요

### CORS 오류
- 서버가 `http://localhost:5000`에서 실행 중인지 확인하세요
- `app.js`의 `API_BASE_URL`을 확인하세요

### 카드 생성 실패
- Google Gemini API 할당량을 확인하세요
- API 키의 유효성을 확인하세요

## 라이선스

MIT

## 기여

이슈나 개선사항은 언제든지 환영합니다!
