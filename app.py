# =============================================
# 🎬 영화 추천 웹앱 - app.py
# Python + Streamlit + Google Gemini AI
# =============================================

import json          # JSON 파일 읽기
import os            # 환경변수 접근
import streamlit as st  # 웹 UI 프레임워크

import requests      # 포스터 이미지 HTTP 요청
from dotenv import load_dotenv  # .env 파일 로드

# ─────────────────────────────────────────────
# 1) 환경변수 로드 (.env 파일에서 API 키 읽기)
# ─────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = st.secrets.get(
    "GEMINI_API_KEY",
    os.getenv("GEMINI_API_KEY", "")
)

# ─────────────────────────────────────────────
# 2) Gemini AI 설정
# ─────────────────────────────────────────────
# API 키가 있을 때만 Gemini 라이브러리를 초기화합니다.
gemini_available = False
gemini_client = None

if GEMINI_API_KEY and GEMINI_API_KEY != "여기에_발급받은_Gemini_API_키를_입력하세요":
    try:
        from google import genai as genai_module  # 최신 google-genai SDK
        gemini_client = genai_module.Client(api_key=GEMINI_API_KEY)
        gemini_available = True
    except Exception as e:
        st.warning(f"Gemini API 초기화 실패: {e}")

# ─────────────────────────────────────────────
# 3) 영화 데이터 로드 함수
# ─────────────────────────────────────────────
@st.cache_data  # 동일한 데이터를 반복 로딩하지 않도록 캐싱
def load_movies():
    """
    movies.json 파일을 읽어 영화 목록을 반환합니다.
    st.cache_data 덕분에 앱이 처음 실행될 때만 파일을 읽습니다.
    """
    # app.py와 같은 폴더에 있는 movies.json 경로를 구합니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "movies.json")

    with open(json_path, "r", encoding="utf-8") as f:
        movies = json.load(f)
    return movies


# ─────────────────────────────────────────────
# 4) 장르 목록 추출 함수
# ─────────────────────────────────────────────
def get_all_genres(movies):
    """
    전체 영화 목록에서 중복 없이 장르를 추출하여 정렬된 리스트로 반환합니다.
    """
    genres = set()
    for movie in movies:
        for g in movie["genre"]:
            genres.add(g)
    return sorted(list(genres))  # 가나다 순 정렬


# ─────────────────────────────────────────────
# 5) 영화 필터링 함수
# ─────────────────────────────────────────────
def filter_movies(movies, search_query, selected_genre):
    """
    검색어(제목)와 장르 필터를 적용하여 조건에 맞는 영화만 반환합니다.

    Args:
        movies (list): 전체 영화 목록
        search_query (str): 제목 검색 키워드
        selected_genre (str): 선택된 장르 ("전체" 이면 필터 없음)

    Returns:
        list: 필터링된 영화 목록
    """
    filtered = movies

    # 5-1) 제목 검색 필터 적용 (대소문자 무시)
    if search_query:
        filtered = [
            m for m in filtered
            if search_query.lower() in m["title"].lower()
        ]

    # 5-2) 장르 필터 적용
    if selected_genre and selected_genre != "전체":
        filtered = [
            m for m in filtered
            if selected_genre in m["genre"]
        ]

    return filtered


# ─────────────────────────────────────────────
# 6) Gemini AI 추천 이유 생성 함수
# ─────────────────────────────────────────────
def generate_recommendation(movie):
    """
    Gemini AI를 사용하여 해당 영화를 추천하는 이유를 2~3줄로 생성합니다.

    Args:
        movie (dict): 영화 정보 딕셔너리

    Returns:
        str: AI가 생성한 추천 이유 텍스트
    """
    if not gemini_available or gemini_client is None:
        return "⚠️ Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 입력해주세요."

    # Gemini에게 전달할 프롬프트를 작성합니다.
    prompt = f"""
당신은 영화 전문 큐레이터입니다. 아래 영화를 2~3줄로 간결하게 추천하는 이유를 한국어로 작성해주세요.
긍정적이고 흥미로운 톤으로 작성하며, 이 영화만의 독특한 매력을 강조해주세요.

영화 제목: {movie['title']}
장르: {', '.join(movie['genre'])}
개봉연도: {movie['year']}
평점: {movie['rating']}/10
줄거리: {movie['plot']}
감독: {movie['director']}

추천 이유 (2~3줄):
"""

    # 시도할 모델 목록 (앞에서부터 순서대로 폴백 시도)
    models_to_try = ["gemini-2.5-flash"]

    last_error = None
    for model_name in models_to_try:
        try:
            # google-genai SDK로 텍스트 생성 시도
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text.strip()

        except Exception as e:
            err_str = str(e)
            last_error = e

            # 429 할당량 초과 오류 감지
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # 재시도 대기 시간 파싱 (에러 메시지에 포함된 경우)
                import re
                retry_match = re.search(r"retry in ([\d.]+)s", err_str, re.IGNORECASE)
                retry_sec = int(float(retry_match.group(1))) + 1 if retry_match else None

                retry_msg = f" ({retry_sec}초 후 다시 시도해주세요)" if retry_sec else ""
                # 마지막 모델까지 실패한 경우 안내 메시지 반환
                if model_name == models_to_try[-1]:
                    return (
                        f"⏳ **API 무료 할당량을 초과했습니다.**{retry_msg}\n\n"
                        "**해결 방법:**\n"
                        "- 잠시 후 다시 시도해주세요 (일반적으로 1분 이내 해소)\n"
                        "- 하루 요청 한도를 초과한 경우 내일 다시 시도해주세요\n"
                        "- [Google AI Studio](https://aistudio.google.com)에서 사용량을 확인하세요"
                    )
                # 다음 모델로 폴백 계속 시도
                continue
            else:
                # 할당량 외 다른 오류는 즉시 반환
                return f"❌ AI 추천 이유 생성 중 오류가 발생했습니다: {err_str}"

    return f"❌ AI 추천 이유 생성 중 오류가 발생했습니다: {str(last_error)}"


# ─────────────────────────────────────────────
# 7) 별점 표시 함수
# ─────────────────────────────────────────────
def render_stars(rating):
    """
    평점(0~10)을 별점(★☆) 5개 기준으로 변환하여 문자열로 반환합니다.
    예: 8.0 → ★★★★☆
    """
    stars = rating / 2  # 10점 만점 → 5점 만점으로 변환
    full_stars = int(stars)
    half_star = 1 if stars - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    return "⭐" * full_stars + ("✨" if half_star else "") + "☆" * empty_stars


# ─────────────────────────────────────────────
# 8) 포스터 이미지 표시 함수
# ─────────────────────────────────────────────
def show_poster(poster_url, title, width=200):
    """
    포스터 이미지를 표시합니다. 로딩 실패 시 대체 텍스트를 보여줍니다.
    HEAD 검증 없이 바로 렌더링하여 불필요한 네트워크 요청을 줄입니다.

    Args:
        poster_url (str): 포스터 이미지 URL
        title (str): 영화 제목 (이미지 alt 텍스트용)
        width (int): 이미지 너비 (픽셀)
    """
    try:
        # URL 유효성 검사 없이 바로 이미지를 렌더링합니다.
        # (브라우저가 이미지를 직접 로드하므로 별도 HTTP 요청 불필요)
        st.image(poster_url, caption=title, width=width)
    except Exception:
        st.info(f"🎬 [{title}] 포스터 로딩 실패")


# ─────────────────────────────────────────────
# 9) 영화 상세 정보 표시 함수
# ─────────────────────────────────────────────
def show_movie_detail(movie):
    """
    선택한 영화의 상세 정보를 화면에 표시합니다.
    포스터, 기본 정보, 줄거리, AI 추천 이유를 보여줍니다.

    Args:
        movie (dict): 영화 정보 딕셔너리
    """
    st.divider()
    st.subheader(f"🎬 {movie['title']} 상세 정보")

    # 두 열로 나누어 포스터와 정보를 나란히 배치
    col1, col2 = st.columns([1, 2])

    with col1:
        # 왼쪽 열: 포스터 이미지
        show_poster(movie["poster"], movie["title"], width=220)

    with col2:
        # 오른쪽 열: 영화 기본 정보
        st.markdown(f"**📅 개봉연도:** {movie['year']}")
        st.markdown(f"**🎭 장르:** {' · '.join(movie['genre'])}")
        st.markdown(f"**⭐ 평점:** {movie['rating']} / 10  {render_stars(movie['rating'])}")
        st.markdown(f"**🎥 감독:** {movie['director']}")
        st.markdown(f"**🎭 출연진:** {', '.join(movie['cast'])}")

        st.markdown("---")
        st.markdown("**📝 줄거리**")
        st.write(movie["plot"])

    # AI 추천 이유 섹션
    st.markdown("---")
    st.markdown("### 🤖 AI 추천 이유 (Gemini)")

    # AI 추천 버튼을 클릭하면 Gemini API를 호출
    btn_key = f"recommend_btn_{movie['id']}"
    if st.button("✨ AI 추천 이유 보기", key=btn_key):
        with st.spinner("Gemini AI가 추천 이유를 생성하는 중..."):
            recommendation = generate_recommendation(movie)

        # 추천 이유를 파란색 정보 박스로 표시
        st.info(recommendation)


# ─────────────────────────────────────────────
# 10) 영화 카드 목록 표시 함수
# ─────────────────────────────────────────────
def show_movie_cards(movies, cols_per_row=3):
    """
    영화 목록을 카드 형태로 격자 배치하여 표시합니다.
    빠른 로딩을 위해 카드에는 포스터 없이 제목·장르·평점·연도만 표시합니다.
    포스터는 '상세 보기' 클릭 후 상세 정보 패널에서만 불러옵니다.

    Args:
        movies (list): 표시할 영화 목록
        cols_per_row (int): 한 행에 표시할 카드 수 (기본 3개)
    """
    # 영화 목록을 cols_per_row 개씩 묶어서 행 단위로 처리
    for row_start in range(0, len(movies), cols_per_row):
        row_movies = movies[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)

        for col, movie in zip(cols, row_movies):
            with col:
                # ─── 포스터 없이 텍스트 정보만 표시 (로딩 속도 개선) ───

                # 영화 제목 (굵게, 약간 크게)
                st.markdown(f"### {movie['title']}")

                # 장르 태그들
                genre_tags = " ".join([f"`{g}`" for g in movie["genre"]])
                st.markdown(genre_tags)

                # 평점 (별점 포함) 과 개봉연도
                st.markdown(
                    f"⭐ **{movie['rating']}** / 10 &nbsp;&nbsp; 📅 {movie['year']}",
                    unsafe_allow_html=True
                )

                # 상세 보기 버튼 (클릭 시 포스터 포함 상세 정보 표시)
                if st.button("🎬 상세 보기", key=f"detail_{movie['id']}"):
                    st.session_state["selected_movie_id"] = movie["id"]

                st.markdown("---")


# ─────────────────────────────────────────────
# 11) 메인 앱 함수
# ─────────────────────────────────────────────
def main():
    """
    Streamlit 앱의 메인 진입점입니다.
    페이지 설정, 사이드바, 영화 목록, 상세 정보를 구성합니다.
    """

    # ── 페이지 기본 설정 ──────────────────────
    st.set_page_config(
        page_title="🎬 영화 추천 앱",   # 브라우저 탭 제목
        page_icon="🎬",                  # 브라우저 탭 아이콘
        layout="wide",                   # 넓은 레이아웃 사용
        initial_sidebar_state="expanded" # 사이드바 기본 펼침
    )

    # ── 전체 스타일 커스터마이징 ──────────────
    st.markdown("""
    <style>
        /* 앱 전체 배경색 */
        .stApp {
            background-color: #0f0f1a;
            color: #e0e0e0;
        }

        /* ─── 사이드바 ─── */
        [data-testid="stSidebar"] {
            background-color: #1a1a2e;
        }
        /* 사이드바 모든 텍스트를 밝게 */
        [data-testid="stSidebar"] * {
            color: #f0f0f0 !important;
        }
        /* 사이드바 레이블 */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stSlider label {
            color: #f5c518 !important;
            font-weight: 600;
        }
        /* 사이드바 입력 필드 */
        [data-testid="stSidebar"] input {
            background-color: #0f0f1a !important;
            color: #f0f0f0 !important;
            border: 1px solid #555 !important;
        }
        /* 사이드바 셀렉트박스 */
        [data-testid="stSidebar"] .stSelectbox > div > div {
            background-color: #0f0f1a !important;
            color: #f0f0f0 !important;
            border: 1px solid #555 !important;
        }
        /* 사이드바 슬라이더 숫자 */
        [data-testid="stSidebar"] .stSlider p {
            color: #f0f0f0 !important;
        }
        /* 사이드바 구분선 */
        [data-testid="stSidebar"] hr {
            border-color: #444;
        }
        /* 사이드바 도움말(help) 아이콘 */
        [data-testid="stSidebar"] .stTooltipIcon {
            color: #aaa !important;
        }

        /* ─── 제목 ─── */
        h1, h2, h3 {
            color: #f5c518;
        }

        /* ─── 버튼 ─── */
        .stButton > button {
            background-color: #e50914;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            transition: background-color 0.2s;
        }
        .stButton > button:hover {
            background-color: #b20710;
            color: white;
        }

        /* ─── 정보 박스 (AI 추천) ─── */
        .stInfo {
            background-color: #1e3a5f;
            border-left: 4px solid #f5c518;
        }

        /* ─── 메인 입력 필드 ─── */
        .stTextInput > div > div > input {
            background-color: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #444;
        }

        /* ─── 상세 정보 앵커 ─── */
        #detail-anchor {
            display: block;
            position: relative;
            top: -80px;
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── 상단 헤더 ────────────────────────────
    st.title("🎬 영화 추천 웹앱")
    st.caption("Powered by Google Gemini AI · 좋아하는 영화를 찾고 AI 추천 이유를 확인해보세요!")

    # Gemini API 키 상태 안내
    if not gemini_available:
        st.warning(
            "⚠️ **Gemini API 키가 설정되지 않았습니다.**  \n"
            "`.env` 파일에 `GEMINI_API_KEY`를 입력하면 AI 추천 이유 기능을 사용할 수 있습니다.  \n"
            "[API 키 발급 → Google AI Studio](https://aistudio.google.com/app/apikey)",
            icon="🔑"
        )
    else:
        st.success("✅ Gemini AI 연결 완료! AI 추천 이유 기능을 사용할 수 있습니다.", icon="🤖")

    # ── 영화 데이터 로드 ──────────────────────
    all_movies = load_movies()

    # ── 세션 스테이트 초기화 ──────────────────
    # 세션 스테이트: 페이지가 새로 고침되어도 값이 유지되는 저장소
    if "selected_movie_id" not in st.session_state:
        st.session_state["selected_movie_id"] = None

    # ── 사이드바: 검색 & 필터 UI ─────────────
    with st.sidebar:
        st.header("🔍 영화 검색 & 필터")
        st.markdown("---")

        # 제목 검색 입력 필드
        search_query = st.text_input(
            "🎬 영화 제목 검색",
            placeholder="예: 인셉션, 기생충...",
            help="영화 제목의 일부를 입력하면 검색됩니다."
        )

        st.markdown("---")

        # 장르 선택 (멀티셀렉트가 아닌 단일 선택으로 구현)
        all_genres = get_all_genres(all_movies)
        selected_genre = st.selectbox(
            "🎭 장르 선택",
            options=["전체"] + all_genres,  # "전체"를 맨 앞에 추가
            help="원하는 장르를 선택하면 해당 장르의 영화만 표시됩니다."
        )

        st.markdown("---")

        # 평점 필터 슬라이더
        min_rating = st.slider(
            "⭐ 최소 평점",
            min_value=0.0,
            max_value=10.0,
            value=0.0,         # 기본값: 모든 평점
            step=0.5,
            help="선택한 평점 이상의 영화만 표시됩니다."
        )

        st.markdown("---")

        # 선택 초기화 버튼
        if st.button("🔄 선택 초기화"):
            st.session_state["selected_movie_id"] = None
            st.rerun()  # 페이지를 새로 고침하여 초기화 반영

    # ── 메인 영역 ──────────────────────────────
    # 필터링 적용
    filtered_movies = filter_movies(all_movies, search_query, selected_genre)
    filtered_movies = [m for m in filtered_movies if m["rating"] >= min_rating]

    selected_id = st.session_state.get("selected_movie_id")

    # ── 상세 정보를 영화 목록보다 먼저 표시 ──────
    # 버튼 클릭 시 상단에서 바로 확인할 수 있도록 목록 위에 배치합니다.
    if selected_id is not None:
        selected_movie = next(
            (m for m in all_movies if m["id"] == selected_id), None
        )
        if selected_movie:
            # 앵커 태그를 삽입하고 JS로 해당 위치로 자동 스크롤합니다.
            st.markdown('<a id="detail-anchor"></a>', unsafe_allow_html=True)
            st.components.v1.html(
                "<script>document.getElementById('detail-anchor')"
                ".scrollIntoView({behavior: 'smooth'});</script>",
                height=0
            )
            show_movie_detail(selected_movie)
            st.markdown("---")

    # ── 영화 목록 ────────────────────────────
    st.markdown(f"### 🎥 영화 목록 ({len(filtered_movies)}편)")

    if not filtered_movies:
        st.info("😔 검색 결과가 없습니다. 다른 키워드나 장르로 검색해보세요.")
    else:
        show_movie_cards(filtered_movies, cols_per_row=3)


# ─────────────────────────────────────────────
# 12) 앱 실행 진입점
# ─────────────────────────────────────────────
# Python에서 이 파일을 직접 실행할 때만 main()을 호출합니다.
# (다른 파일에서 import 될 때는 실행되지 않습니다)
if __name__ == "__main__":
    main()
