import streamlit as st
import streamlit.components.v1 as components
import tempfile
import os

try:
    for _k in ["ANTHROPIC_API_KEY", "NOTION_TOKEN", "NOTION_DATABASE_ID"]:
        if _k in st.secrets:
            os.environ[_k] = st.secrets[_k]
except Exception:
    pass

from tools.photo_analyzer import FILTERS, analyze_scene, get_recommendations, generate_prompt, save_result
from tools.notion_uploader import upload

st.set_page_config(page_title="DEVELOP", page_icon="📷", layout="centered")

# ── 인스타 감성 CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp {
    background-color: #FAFAFA !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

#MainMenu, footer { visibility: hidden; }

.block-container {
    max-width: 680px !important;
    padding: 2rem 1.5rem 4rem !important;
}

/* 헤더 */
.ig-header {
    background: linear-gradient(135deg, #F58529 0%, #DD2A7B 50%, #8134AF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.3;
    padding: 4px 2px;
    margin-bottom: 4px;
    display: inline-block;
}
.ig-sub {
    color: #8E8E8E;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

/* 섹션 레이블 */
.ig-section {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #8E8E8E;
    margin: 1.5rem 0 0.6rem;
}

/* 구분선 */
hr { border-color: #DBDBDB !important; margin: 1.2rem 0 !important; }

/* 업로드 영역 */
[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #DBDBDB;
    border-radius: 16px;
    padding: 1rem;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #DD2A7B; }

/* 업로드된 사진 */
[data-testid="stImage"] img {
    border-radius: 12px;
    border: 1px solid #DBDBDB;
}

/* expander */
[data-testid="stExpander"] {
    background: white;
    border: 1px solid #DBDBDB !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-size: 0.85rem;
    font-weight: 600;
    color: #262626;
    padding: 0.7rem 1rem;
}

/* 분석 태그 */
.scene-tag {
    display: inline-block;
    background: #F0F0F0;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    color: #262626;
    margin: 3px 2px;
}
.scene-label {
    font-size: 0.72rem;
    color: #8E8E8E;
    font-weight: 500;
}

/* 추천 배지 */
.rec-card {
    background: white;
    border: 1px solid #DBDBDB;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    align-items: flex-start;
    gap: 10px;
}
.rec-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #F58529, #DD2A7B);
    flex-shrink: 0;
    margin-top: 5px;
}
.rec-name { font-weight: 600; font-size: 0.85rem; color: #262626; }
.rec-reason { font-size: 0.78rem; color: #8E8E8E; margin-top: 1px; }

/* 필터 카드 설명 div */
.filter-desc-sel {
    border: 2px solid #DD2A7B !important;
    border-radius: 8px;
    padding: 4px 6px;
    background: #FFF0F5;
    font-size: 11px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2px;
    color: #262626;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 32px;
}
.filter-desc-rec {
    border: 2px solid #F58529 !important;
    border-radius: 8px;
    padding: 4px 6px;
    background: #FFF8F0;
    font-size: 11px;
    text-align: center;
    margin-bottom: 2px;
    color: #262626;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 32px;
}
.filter-desc-normal {
    border: 1px solid #DBDBDB !important;
    border-radius: 8px;
    padding: 4px 6px;
    background: white;
    font-size: 11px;
    text-align: center;
    margin-bottom: 2px;
    color: #8E8E8E;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 32px;
}

/* 버튼 전체 */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    border: 1px solid #DBDBDB !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F58529, #DD2A7B, #8134AF) !important;
    color: white !important;
    border: none !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #DD2A7B !important;
    color: #DD2A7B !important;
}

/* 생성 버튼 */
.stButton > button[kind="primary"][data-testid*="generate"] {
    padding: 0.7rem !important;
    font-size: 1rem !important;
    letter-spacing: 0.3px;
}

/* 탭 */
[data-testid="stTabs"] [role="tab"] {
    font-size: 0.82rem;
    font-weight: 600;
    color: #8E8E8E;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #262626;
    border-bottom-color: #262626 !important;
}

/* 결과 카드 */
.result-card {
    background: white;
    border: 1px solid #DBDBDB;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.result-card-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #8E8E8E;
    margin-bottom: 0.6rem;
}

/* 인스타 캡션 박스 */
.caption-box {
    background: white;
    border: 1px solid #DBDBDB;
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
.caption-hook {
    font-weight: 700;
    font-size: 0.95rem;
    color: #262626;
    margin-bottom: 0.5rem;
}
.caption-body {
    font-size: 0.85rem;
    color: #262626;
    line-height: 1.6;
    white-space: pre-wrap;
}
.caption-cta {
    font-size: 0.82rem;
    color: #DD2A7B;
    font-weight: 600;
    margin-top: 0.5rem;
}

/* 성공 메시지 */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: none !important;
}

/* 코드 블록 */
[data-testid="stCode"] {
    border-radius: 10px !important;
    font-size: 0.78rem !important;
}

/* 텍스트 인풋 */
[data-testid="stTextInput"] input {
    border-radius: 10px !important;
    border: 1px solid #DBDBDB !important;
    font-size: 0.85rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #DD2A7B !important;
    box-shadow: 0 0 0 2px rgba(221,42,123,0.1) !important;
}
</style>
""", unsafe_allow_html=True)


def copy_button(text: str, label: str = "복사"):
    safe = text.replace("\\", "\\\\").replace("`", "\\`")
    components.html(f"""
    <button onclick="
        navigator.clipboard.writeText(`{safe}`)
        .then(() => {{ this.innerText='✓ 복사됨'; setTimeout(() => this.innerText='{label}', 2000); }})
        .catch(() => this.innerText='실패')
    " style="
        background: linear-gradient(135deg, #F58529, #DD2A7B, #8134AF);
        color: white; border: none;
        padding: 8px 20px; border-radius: 8px; cursor: pointer;
        font-size: 13px; font-weight: 600; width: 100%;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: opacity 0.15s;
    " onmouseover="this.style.opacity=0.85" onmouseout="this.style.opacity=1">{label}</button>
    """, height=44)


# ── 헤더 ─────────────────────────────────────────────────────────────
st.markdown('<div class="ig-header">DEVELOP</div>', unsafe_allow_html=True)
st.markdown('<div class="ig-sub">사진을 올리면 AI가 필름 필터를 분석하고 Midjourney · DALL-E 프롬프트와 인스타 캡션을 만들어 드립니다.</div>', unsafe_allow_html=True)

# ── 필터 미리보기 ──────────────────────────────────────────────────
with st.expander("필터 둘러보기", expanded=False):
    ASSETS_DIR_PREVIEW = os.path.join(os.path.dirname(__file__), "assets", "filters")
    preview_tab1, preview_tab2, preview_tab3 = st.tabs(["필름 종류", "감성", "기법"])

    def _preview_grid(nums):
        num_list = list(nums)
        for row_start in range(0, len(num_list), 3):
            row = num_list[row_start:row_start + 3]
            cols = st.columns(3)
            for col, num in zip(cols, row):
                f = FILTERS[num]
                with col:
                    for ext in ["jpg", "jpeg", "png", "webp"]:
                        p = os.path.join(ASSETS_DIR_PREVIEW, f"{num}.{ext}")
                        if os.path.exists(p):
                            st.image(p, width='stretch')
                            break
                    st.markdown(
                        f"<div style='font-size:0.78rem;font-weight:600;color:#262626;margin:2px 0'>{f['name']}</div>"
                        f"<div style='font-size:0.72rem;color:#8E8E8E;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:28px'>{f['desc']}</div>",
                        unsafe_allow_html=True,
                    )
            st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    with preview_tab1:
        _preview_grid(range(1, 10))
    with preview_tab2:
        _preview_grid(range(10, 17))
    with preview_tab3:
        _preview_grid(range(17, 29))

st.markdown("---")

# ── 1단계: 사진 업로드 ────────────────────────────────────────────
st.markdown('<div class="ig-section">사진 업로드</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("JPG · PNG · WEBP", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

if uploaded:
    st.image(uploaded, width=480)

    # 사진 분석
    if "scene" not in st.session_state or st.session_state.get("last_file") != uploaded.name:
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        st.session_state.tmp_path = tmp_path

        with st.spinner("사진 분석 중..."):
            scene = analyze_scene(tmp_path)
            scene["source_image"] = uploaded.name

        with st.spinner("추천 필터 선정 중..."):
            scene["recommendations"] = get_recommendations(scene)

        st.session_state.scene = scene
        st.session_state.last_file = uploaded.name
        st.session_state.result = None

    scene = st.session_state.scene

    with st.expander("사진 분석 결과", expanded=False):
        tags = {
            "피사체": scene.get("subject", ""),
            "빛": scene.get("lighting", ""),
            "방향": scene.get("light_direction", ""),
            "노출": scene.get("exposure", ""),
            "분위기": scene.get("mood", ""),
            "구도": scene.get("composition", ""),
        }
        html = ""
        for k, v in tags.items():
            if v:
                html += f'<span class="scene-label">{k}</span> <span class="scene-tag">{v}</span> &nbsp;'
        st.markdown(f'<div style="line-height:2.2">{html}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── 2단계: 필터 선택 ─────────────────────────────────────────
    st.markdown('<div class="ig-section">필터 선택</div>', unsafe_allow_html=True)

    rec_data = scene.get("recommendations", {})
    if isinstance(rec_data, dict):
        recommendations = rec_data.get("filters", [])
        rec_technique = rec_data.get("technique")
    else:
        recommendations = rec_data
        rec_technique = None
    recommended_nums = [r["num"] for r in recommendations]

    if recommendations:
        st.markdown('<div style="font-size:0.82rem;font-weight:600;color:#262626;margin-bottom:6px">AI 추천 필터</div>', unsafe_allow_html=True)
        for r in recommendations:
            st.markdown(
                f'<div class="rec-card"><div class="rec-dot"></div>'
                f'<div><div class="rec-name">{r["name"]}</div>'
                f'<div class="rec-reason">{r["reason"]}</div></div></div>',
                unsafe_allow_html=True,
            )

    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "filters")

    def _filter_img(num):
        for ext in ["jpg", "jpeg", "png", "webp"]:
            p = os.path.join(ASSETS_DIR, f"{num}.{ext}")
            if os.path.exists(p):
                return p
        return None

    def _card_grid(keys, section_key):
        current = st.session_state.get("selected_num", recommended_nums[0] if recommended_nums else list(keys)[0])
        cols = st.columns(3)
        for i, num in enumerate(keys):
            f = FILTERS[num]
            is_rec = num in recommended_nums
            is_sel = num == current
            with cols[i % 3]:
                img_path = _filter_img(num)
                if img_path:
                    st.image(img_path, width='stretch')
                if is_sel:
                    css_class = "filter-desc-sel"
                    prefix = "✓ "
                elif is_rec:
                    css_class = "filter-desc-rec"
                    prefix = "★ "
                else:
                    css_class = "filter-desc-normal"
                    prefix = ""
                st.markdown(
                    f'<div class="{css_class}">{f["desc"]}</div>',
                    unsafe_allow_html=True,
                )
                label = prefix + f["name"]
                if st.button(label, key=f"card_{section_key}_{num}", width='stretch',
                             type="primary" if is_sel else "secondary"):
                    st.session_state.selected_num = num
                    st.rerun()

    with st.expander("전체 필터에서 직접 고르기"):
        tab1, tab2 = st.tabs(["필름 종류", "감성"])
        with tab1:
            _card_grid(range(1, 10), "film")
        with tab2:
            _card_grid(range(10, 17), "vibe")

    if "selected_num" not in st.session_state:
        st.session_state.selected_num = recommended_nums[0] if recommended_nums else 1
    selected_num = st.session_state.get("selected_num", 1)

    # ── 기법 ────────────────────────────────────────────────────
    st.markdown('<div class="ig-section" style="margin-top:1.2rem">추가 기법 (선택)</div>', unsafe_allow_html=True)

    if rec_technique:
        st.markdown(
            f'<div class="rec-card"><div class="rec-dot"></div>'
            f'<div><div class="rec-name">추천: {rec_technique["name"]}</div>'
            f'<div class="rec-reason">{rec_technique["reason"]}</div></div></div>',
            unsafe_allow_html=True,
        )

    guide_path = os.path.join(os.path.dirname(__file__), "assets", "technique_guide.png")
    if os.path.exists(guide_path):
        with st.expander("기법 효과 예시 보기"):
            st.image(guide_path, width='stretch')

    cur_tech = st.session_state.get("technique_num")

    # 없음 — 그리드 밖 단독 버튼
    is_none_sel = cur_tech is None
    st.markdown(
        f'<div class="{"filter-desc-sel" if is_none_sel else "filter-desc-normal"}" '
        f'style="margin-bottom:4px;text-align:center">기법 없이 필름만 적용</div>',
        unsafe_allow_html=True,
    )
    if st.button("✓ 없음" if is_none_sel else "없음", key="tech_none", width='stretch',
                 type="primary" if is_none_sel else "secondary"):
        st.session_state.technique_num = None
        st.rerun()

    st.markdown('<div style="margin-top:0.6rem"></div>', unsafe_allow_html=True)

    # 기법 17~28 — 3개씩 명확히 끊어서 4줄 그리드
    TECH_ROWS = [
        [17, 18, 19],
        [20, 28, 22],
        [23, 24, 25],
        [26, 27, 21],
    ]
    for row_nums in TECH_ROWS:
        cols = st.columns(3, gap="medium")
        for col, num in zip(cols, row_nums):
            f = FILTERS[num]
            is_rec = rec_technique and rec_technique.get("num") == num
            is_sel = cur_tech == num
            with col:
                img_path = _filter_img(num)
                if img_path:
                    st.image(img_path, width='stretch')
                if is_sel:
                    css_class, prefix = "filter-desc-sel", "✓ "
                elif is_rec:
                    css_class, prefix = "filter-desc-rec", "★ "
                else:
                    css_class, prefix = "filter-desc-normal", ""
                st.markdown(f'<div class="{css_class}">{f["desc"]}</div>', unsafe_allow_html=True)
                if st.button(prefix + f["name"], key=f"tech_{num}", width='stretch',
                             type="primary" if is_sel else "secondary"):
                    st.session_state.technique_num = num
                    st.rerun()
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)

    technique_num = st.session_state.get("technique_num")

    if recommendations:
        st.markdown('<div style="font-size:0.78rem;color:#8E8E8E;margin:1rem 0 0.4rem">추천 필터로 바로 생성</div>', unsafe_allow_html=True)
        cols = st.columns(len(recommendations))
        for i, (col, r) in enumerate(zip(cols, recommendations)):
            with col:
                if st.button(r["name"], key=f"rec_{i}", width='stretch'):
                    st.session_state.selected_num = r["num"]
                    st.session_state.quick_generate = True

    st.markdown("---")

    # ── 3단계: 프롬프트 생성 ──────────────────────────────────────
    st.markdown('<div class="ig-section">프롬프트 생성</div>', unsafe_allow_html=True)

    extra = st.text_input(
        "추가 요소",
        placeholder="예: 벚꽃 날리는 효과 / a small penguin in the center / 고양이 한 마리",
        label_visibility="collapsed",
    )

    generate_clicked = st.button("✨  프롬프트 생성하기", type="primary", width='stretch')
    quick_generate = st.session_state.pop("quick_generate", False)

    if generate_clicked or quick_generate:
        with st.spinner(f"{FILTERS[selected_num]['name']} 필터 적용 중..."):
            result = generate_prompt(
                scene, selected_num,
                technique_num=st.session_state.get("technique_num"),
                image_path=st.session_state.get("tmp_path"),
                extra=extra.strip() if extra else None,
            )
            save_result(result)
            st.session_state.result = result

    if st.session_state.get("result"):
        result = st.session_state.result

        st.markdown(
            f'<div style="background:linear-gradient(135deg,#F58529,#DD2A7B,#8134AF);'
            f'border-radius:10px;padding:10px 14px;color:white;font-weight:600;font-size:0.88rem;margin:0.8rem 0">'
            f'✓ {result.get("filter_name")} 적용 완료</div>',
            unsafe_allow_html=True,
        )

        # AI 프롬프트
        st.markdown('<div class="ig-section" style="margin-top:1.2rem">AI 이미지 프롬프트</div>', unsafe_allow_html=True)

        for label, key, copy_label in [
            ("범용 · Midjourney / DALL-E", "prompt_universal", "범용 프롬프트 복사"),
            ("Midjourney 전용", "prompt_midjourney", "Midjourney 복사"),
            ("DALL-E / ChatGPT 전용", "prompt_dalle", "DALL-E 복사"),
        ]:
            st.markdown(f'<div style="font-size:0.78rem;font-weight:600;color:#262626;margin:0.8rem 0 0.3rem">{label}</div>', unsafe_allow_html=True)
            st.code(result.get(key, ""), language=None)
            copy_button(result.get(key, ""), copy_label)

        # 인스타 캡션
        st.markdown('<div class="ig-section" style="margin-top:1.5rem">인스타그램 캡션</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="caption-box">'
            f'<div class="caption-hook">{result.get("hook_ko", "")}</div>'
            f'<div class="caption-body">{result.get("caption_ko", "")}</div>'
            f'<div class="caption-cta">{result.get("cta_ko", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        copy_button(result.get("caption_ko", ""), "캡션 전체 복사")

        st.markdown("---")

        if st.button("노션에 저장하기", width='stretch'):
            with st.spinner("노션 업로드 중..."):
                try:
                    title = upload(result, image_path=st.session_state.get("tmp_path"))
                    st.success(f"노션 저장 완료: {title}")
                except Exception as e:
                    st.error(f"노션 저장 실패: {e}")
