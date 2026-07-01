# 🎬 영화 추천 웹앱 (Movie Recommender)

Python + Streamlit + Gemini AI를 활용한 영화 추천 웹앱입니다.

---

## ✨ 주요 기능

- 🔍 **영화 제목 검색** — 키워드로 영화를 빠르게 찾기
- 🎭 **장르별 필터링** — 원하는 장르의 영화만 보기
- 🎬 **영화 목록 카드 뷰** — 포스터, 평점, 연도 정보 제공
- 📋 **상세 정보 보기** — 감독, 출연진, 줄거리 등 상세 정보
- 🤖 **AI 추천 이유** — Gemini AI가 영화를 추천하는 이유를 2~3줄로 생성

---

## 📁 프로젝트 구조

```
movie/
├── app.py            # Streamlit 메인 애플리케이션
├── movies.json       # 영화 더미 데이터
├── requirements.txt  # Python 패키지 의존성
├── .env              # 환경변수 (Gemini API 키)
└── README.md         # 이 파일
```

---

## 🚀 실행 방법

### 1단계: Python 설치 확인
Python 3.8 이상이 설치되어 있어야 합니다.
```bash
python --version
```

### 2단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 3단계: Gemini API 키 설정

1. [Google AI Studio](https://aistudio.google.com/app/apikey)에 접속합니다.
2. API 키를 발급받습니다.
3. `.env` 파일을 열어 API 키를 입력합니다:

```
GEMINI_API_KEY=여기에_발급받은_API_키_입력
```

### 4단계: 앱 실행
```bash
streamlit run app.py
```

브라우저에서 자동으로 `http://localhost:8501`이 열립니다.

---

## 🔑 Gemini API 키 발급 방법

1. [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. **"Create API Key"** 버튼 클릭
4. 생성된 키를 복사하여 `.env` 파일에 붙여넣기

> ⚠️ API 키는 절대 외부에 공유하지 마세요!

---

## 📦 사용된 기술

| 기술 | 용도 |
|------|------|
| Python | 백엔드 로직 |
| Streamlit | 웹 UI 프레임워크 |
| Google Gemini API | AI 영화 추천 이유 생성 |
| python-dotenv | 환경변수 관리 |
| Requests | 포스터 이미지 로딩 |

---

## 🎥 영화 데이터

`movies.json`에 15편의 영화 데이터가 포함되어 있습니다:
- 인셉션, 기생충, 어벤져스, 라라랜드, 인터스텔라
- 올드보이, 타이타닉, 조커, 극한직업, 어바웃 타임
- 다크 나이트, 써니, 매트릭스, 버드박스, 명량

---

## 💡 참고 사항

- Gemini API 키가 없어도 앱은 실행됩니다. (AI 추천 이유 기능만 비활성화)
- 포스터 이미지는 TMDB(The Movie Database)에서 제공합니다.
- 인터넷 연결이 필요합니다.
