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


def copy_button(text: str, label: str = "📋 복사"):
    safe = text.replace("\\", "\\\\").replace("`", "\\`")
    components.html(f"""
    <button onclick="
        navigator.clipboard.writeText(`{safe}`)
        .then(() => {{ this.innerText='✅ 복사됨'; setTimeout(() => this.innerText='{label}', 2000); }})
        .catch(() => this.innerText='❌ 실패')
    " style="
        background:#2563eb; color:white; border:none;
        padding:8px 20px; border-radius:6px; cursor:pointer;
        font-size:14px; font-weight:600; width:100%;
    ">{label}</button>
    """, height=45)

st.set_page_config(page_title="필름 감성 프롬프트 생성기", page_icon="📷", layout="centered")

st.title("📷 필름 감성 프롬프트 생성기")
st.caption("사진을 올리고 원하는 필터를 선택하면 AI 프롬프트와 인스타그램 문구를 만들어 드립니다.")

st.divider()

# 필터 미리보기 (업로드 전 상시 표시)
with st.expander("🎞 필터 둘러보기 (사진 없이 미리 보기)", expanded=False):
    ASSETS_DIR_PREVIEW = os.path.join(os.path.dirname(__file__), "assets", "filters")
    preview_tab1, preview_tab2, preview_tab3 = st.tabs(["🎞 필름 종류", "🎨 감성", "✨ 기법"])
    def _preview_grid(nums):
        cols = st.columns(3)
        for i, num in enumerate(nums):
            f = FILTERS[num]
            with cols[i % 3]:
                for ext in ["jpg", "jpeg", "png", "webp"]:
                    p = os.path.join(ASSETS_DIR_PREVIEW, f"{num}.{ext}")
                    if os.path.exists(p):
                        st.image(p, use_container_width=True)
                        break
                st.markdown(f"**{f['name']}**  \n{f['desc']}", unsafe_allow_html=False)
    with preview_tab1:
        _preview_grid(range(1, 10))
    with preview_tab2:
        _preview_grid(range(10, 17))
    with preview_tab3:
        _preview_grid(range(17, 29))

st.divider()

# 1단계: 사진 업로드
st.subheader("1. 사진 업로드")
uploaded = st.file_uploader("사진을 선택하세요", type=["jpg", "jpeg", "png", "webp"])

if uploaded:
    st.image(uploaded, width=400)

    # 2단계: 사진 분석
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

    with st.expander("사진 분석 결과 보기", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**피사체:** {scene.get('subject', '')}")
            st.markdown(f"**빛:** {scene.get('lighting', '')}")
            st.markdown(f"**빛 방향:** {scene.get('light_direction', '')}")
        with col2:
            st.markdown(f"**노출:** {scene.get('exposure', '')}")
            st.markdown(f"**분위기:** {scene.get('mood', '')}")
            st.markdown(f"**구도:** {scene.get('composition', '')}")

    st.divider()

    # 3단계: 필터 선택
    st.subheader("2. 필터 선택")

    # 추천 데이터 파싱 (새 형식: dict / 구형식: list 호환)
    rec_data = scene.get("recommendations", {})
    if isinstance(rec_data, dict):
        recommendations = rec_data.get("filters", [])
        rec_technique = rec_data.get("technique")
    else:
        recommendations = rec_data
        rec_technique = None
    recommended_nums = [r["num"] for r in recommendations]

    if recommendations:
        st.markdown("**✨ AI 추천 필터**")
        for r in recommendations:
            st.success(f"**{r['name']}** — {r['reason']}")
        st.markdown("")

    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "filters")

    def _filter_img(num):
        for ext in ["jpg", "jpeg", "png", "webp"]:
            p = os.path.join(ASSETS_DIR, f"{num}.{ext}")
            if os.path.exists(p):
                return p
        return None

    def _card_grid(keys, section_key):
        """이미지 카드 그리드로 필터 선택 UI"""
        current = st.session_state.get("selected_num", recommended_nums[0] if recommended_nums else list(keys)[0])
        cols = st.columns(3)
        for i, num in enumerate(keys):
            f = FILTERS[num]
            is_rec = num in recommended_nums
            is_sel = num == current
            with cols[i % 3]:
                img_path = _filter_img(num)
                if img_path:
                    st.image(img_path, use_container_width=True)
                border = "3px solid #2563eb" if is_sel else ("2px solid #f59e0b" if is_rec else "1px solid #e5e7eb")
                label = ("✅ " if is_sel else "★ " if is_rec else "") + f["name"]
                st.markdown(
                    f'<div style="border:{border};border-radius:6px;padding:4px 6px;'
                    f'background:{"#eff6ff" if is_sel else "#fffbeb" if is_rec else "#fafafa"};'
                    f'margin-bottom:2px;font-size:11px;font-weight:{"700" if is_sel else "400"};'
                    f'text-align:center">{f["desc"]}</div>',
                    unsafe_allow_html=True,
                )
                if st.button(label, key=f"card_{section_key}_{num}", use_container_width=True,
                             type="primary" if is_sel else "secondary"):
                    st.session_state.selected_num = num
                    st.rerun()

    # 전체 필터 목록 — 카드 그리드
    with st.expander("전체 필터 목록에서 직접 선택하기"):
        tab1, tab2 = st.tabs(["🎞 필름 종류", "🎨 감성"])
        with tab1:
            _card_grid(range(1, 10), "film")
        with tab2:
            _card_grid(range(10, 17), "vibe")

    if "selected_num" not in st.session_state:
        st.session_state.selected_num = recommended_nums[0] if recommended_nums else 1
    selected_num = st.session_state.get("selected_num", 1)

    # 기법 — 카드 그리드
    st.markdown("**✨ 추가 기법 효과 (선택사항)**")

    if rec_technique:
        st.info(f"AI 추천 기법: **{rec_technique['name']}** — {rec_technique['reason']}")

    # 기법 가이드 이미지
    guide_path = os.path.join(os.path.dirname(__file__), "assets", "technique_guide.png")
    if os.path.exists(guide_path):
        with st.expander("📖 기법 효과 예시 보기"):
            st.image(guide_path, use_container_width=True)

    cur_tech = st.session_state.get("technique_num")
    tech_cols = st.columns(3)
    # 없음 카드
    with tech_cols[0]:
        is_none_sel = cur_tech is None
        st.markdown(
            f'<div style="border:{"3px solid #2563eb" if is_none_sel else "1px solid #e5e7eb"};'
            f'border-radius:6px;padding:12px 6px;background:{"#eff6ff" if is_none_sel else "#fafafa"};'
            f'text-align:center;font-size:11px;color:#888;margin-bottom:2px">기법 없이<br>필름만 적용</div>',
            unsafe_allow_html=True,
        )
        if st.button("없음" if not is_none_sel else "✅ 없음", key="tech_none", use_container_width=True,
                     type="primary" if is_none_sel else "secondary"):
            st.session_state.technique_num = None
            st.rerun()

    for i, num in enumerate(range(17, 29)):
        f = FILTERS[num]
        is_rec = rec_technique and rec_technique.get("num") == num
        is_sel = cur_tech == num
        col_idx = (i + 1) % 3
        with tech_cols[col_idx]:
            img_path = _filter_img(num)
            if img_path:
                st.image(img_path, use_container_width=True)
            border = "3px solid #2563eb" if is_sel else ("2px solid #f59e0b" if is_rec else "1px solid #e5e7eb")
            st.markdown(
                f'<div style="border:{border};border-radius:6px;padding:4px 6px;'
                f'background:{"#eff6ff" if is_sel else "#fffbeb" if is_rec else "#fafafa"};'
                f'margin-bottom:2px;font-size:11px;text-align:center">{f["desc"]}</div>',
                unsafe_allow_html=True,
            )
            label = ("✅ " if is_sel else "★ " if is_rec else "") + f["name"]
            if st.button(label, key=f"tech_{num}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.technique_num = num
                st.rerun()

    technique_num = st.session_state.get("technique_num")

    # 추천 필터 빠른 선택 버튼
    if recommendations:
        st.markdown("**또는 추천 필터로 바로 생성:**")
        cols = st.columns(len(recommendations))
        for i, (col, r) in enumerate(zip(cols, recommendations)):
            with col:
                if st.button(r["name"], key=f"rec_{i}", use_container_width=True):
                    st.session_state.selected_num = r["num"]
                    st.session_state.quick_generate = True

    st.divider()

    # 4단계: 프롬프트 생성
    st.subheader("3. 프롬프트 생성")

    extra = st.text_input(
        "추가 요소 (선택사항)",
        placeholder="예: a small penguin walking in the center facing left / 벚꽃 날리는 효과 / 고양이 한 마리",
        help="원본에 없지만 프롬프트에 추가하고 싶은 요소를 입력하세요."
    )

    generate_clicked = st.button("✨ 프롬프트 생성하기", type="primary", use_container_width=True)
    quick_generate = st.session_state.pop("quick_generate", False)

    if generate_clicked or quick_generate:
        with st.spinner(f"{FILTERS[selected_num]['name']} 필터 적용 중..."):
            result = generate_prompt(scene, selected_num, technique_num=st.session_state.get("technique_num"), image_path=st.session_state.get("tmp_path"), extra=extra.strip() if extra else None)
            save_result(result)
            st.session_state.result = result

    if st.session_state.get("result"):
        result = st.session_state.result
        st.success(f"필터 적용 완료: **{result.get('filter_name')}**")

        st.markdown("#### AI 이미지 프롬프트")

        st.markdown("**범용 (Midjourney / DALL-E 모두)**")
        st.code(result.get("prompt_universal", ""), language=None)
        copy_button(result.get("prompt_universal", ""), "📋 범용 프롬프트 복사")

        st.markdown("**Midjourney 전용**")
        st.code(result.get("prompt_midjourney", ""), language=None)
        copy_button(result.get("prompt_midjourney", ""), "📋 Midjourney 복사")

        st.markdown("**DALL-E / ChatGPT 전용**")
        st.code(result.get("prompt_dalle", ""), language=None)
        copy_button(result.get("prompt_dalle", ""), "📋 DALL-E 복사")

        st.divider()
        st.markdown("#### 인스타그램 문구")

        st.markdown("**훅 도입문**")
        st.info(result.get("hook_ko", ""))

        st.markdown("**CTA 문장**")
        st.info(result.get("cta_ko", ""))

        st.markdown("**전체 캡션 초안**")
        st.text_area("복사해서 사용하세요", value=result.get("caption_ko", ""), height=150, label_visibility="collapsed")

        st.divider()

        if st.button("📋 노션에 저장하기", use_container_width=True):
            with st.spinner("노션 업로드 중..."):
                try:
                    title = upload(result, image_path=st.session_state.get("tmp_path"))
                    st.success(f"노션 저장 완료: {title}")
                except Exception as e:
                    st.error(f"노션 저장 실패: {e}")
