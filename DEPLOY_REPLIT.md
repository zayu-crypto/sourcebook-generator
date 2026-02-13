# 🚀 Replit에 배포하기

## 30초 배포 가이드

### Step 1: Replit 계정 생성 (없으면)
[replit.com](https://replit.com) 에서 가입

### Step 2: 새 프로젝트 생성
1. Replit 대시보드에서 **"Create"** 클릭
2. **"Import from GitHub"** 선택
3. 이 저장소 URL 입력 또는 파일들 직접 업로드

### Step 3: 환경변수 설정 (중요!)
1. 왼쪽 사이드바에서 **"Secrets"** 아이콘 (자물쇠 모양) 클릭
2. **"New Secret"** 버튼 클릭
3. 다음 입력:
   - **Key**: `GOOGLE_GEMINI_API_KEY`
   - **Value**: 당신의 Google Gemini API 키 (from [ai.google.dev](https://ai.google.dev))

### Step 4: 실행
1. 상단의 **"Run"** 버튼 클릭
2. 몇 초 후 새 윈도우에서 앱이 열림
3. 우상단의 공개 링크 복사해서 다른 사람에게 공유!

---

## 🔗 공개 링크 공유하기
- Replit이 자동으로 공개 URL 생성
- 우상단의 링크를 누구에게나 공유 가능
- 다른 사람들은 로그인 없이 그냥 접속해서 사용 가능!

---

## 🐛 문제 해결

### "GOOGLE_GEMINI_API_KEY is not set" 에러
→ Secrets에 API 키 설정했는지 확인 (step 3)

### 앱이 실행 안 됨
→ 콘솔 로그 확인 (Console 탭)
→ requirements.txt가 제대로 설치됐는지 확인

### 이미지가 안 나옴
→ 인터넷 연결 확인
→ 서버 콘솔에서 "🔍 Searching Wikimedia" 로그 확인

---

## 💡 팁
- **여러 버전 관리**: Replit의 "Multiplayer" 기능으로 팀 협업 가능
- **도메인 연결**: Replit Pro에서 커스텀 도메인 가능
- **백업**: GitHub와 자동 연동되어 코드 안전함

**완료!** 이제 다른 사람들도 링크만으로 사용할 수 있습니다 🎉
