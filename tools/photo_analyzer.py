"""
사진 분석 + 필터 선택 기반 프롬프트 생성
1단계: analyze_scene()  - 사진의 장면/빛/구도 파악
2단계: generate_prompt() - 선택한 필터로 최종 프롬프트 생성
"""

import anthropic
import base64
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

FILTERS = {
    # ── 필름 종류 ──────────────────────────────────────────────────────
    1:  {"name": "Kodak Portra 400",
         "desc": "부드러운 피부톤, 크리미한 색감",
         "keywords": "Kodak Portra 400 / soft creamy skin tones / warm natural light / fine film grain / low contrast / highlight blown soft / wedding portrait travel"},
    2:  {"name": "Kodak Gold 200",
         "desc": "따뜻한 노란빛, 레트로 무드",
         "keywords": "Kodak Gold 200 / warm golden tones / slightly coarse grain / retro everyday snapshot / faded color palette / rich saturated colors / family snapshot feeling"},
    3:  {"name": "Fujifilm Pro 400H",
         "desc": "낮은 채도, 청량한 그린톤",
         "keywords": "Fujifilm Pro 400H / low saturation / soft green color shift / dreamy softness / overexposed by one stop / muted desaturated tones / humid forest atmosphere"},
    4:  {"name": "Kodak Ektar 100",
         "desc": "높은 채도, 선명한 디테일",
         "keywords": "Kodak Ektar 100 / high saturation / extremely sharp detail / vivid colors / punchy contrast / no grain / landscape architecture sky"},
    5:  {"name": "Ilford HP5",
         "desc": "흑백, 강한 명암, 거친 그레인",
         "keywords": "Ilford HP5 black and white / strong shadow contrast / heavy visible grain / documentary street photography mood / melancholic realism"},
    6:  {"name": "Kodak ColorPlus",
         "desc": "일상적, 따뜻한 색감, 약간 빛 번짐",
         "keywords": "Kodak ColorPlus / warm everyday tones / slight halation on highlights / natural color rendering / casual snapshot / slightly faded / sunlit warmth"},
    7:  {"name": "Fuji Superia 400",
         "desc": "선명한 색감, 자연스러운 그린",
         "keywords": "Fuji Superia 400 / vivid natural colors / green-leaning midtones / sharp everyday snapshot / medium grain / natural daylight rendering"},
    8:  {"name": "Cinestill 50D",
         "desc": "시네마틱, 텅스텐 빛, 도심 야경",
         "keywords": "Cinestill 50D / cinematic film look / tungsten light / halation glow around lights / urban night scene / blooming highlights / red and orange halation / moody city atmosphere"},
    9:  {"name": "Lomography 800",
         "desc": "실험적, 높은 그레인, 비비드",
         "keywords": "Lomography 800 / heavy grain / vivid experimental colors / strong vignetting / cross-process effect / lomography aesthetic / unpredictable color shifts / lo-fi analog"},

    # ── 감성 ──────────────────────────────────────────────────────────
    10: {"name": "녹진한 숲속 필름 감성",
         "desc": "습한 공기, 그린 그림자, 부드러운 숲",
         "keywords": "Fujifilm Pro 400H aesthetic / overexposed by one stop / green color shift in shadows / humid forest atmosphere / low contrast / dreamy softness / soft film grain / muted desaturated tones"},
    11: {"name": "일본식 필름 감성",
         "desc": "일회용 카메라, 파스텔, 소프트 포커스",
         "keywords": "Fujifilm disposable camera aesthetic / soft pastel tones / pink and cream color shift / natural vignetting on edges / slight lens distortion / quietly Japanese film photography / Moshi Moshi style / soft focus"},
    12: {"name": "영국식 필름 감성",
         "desc": "흐린 날, 회색 하늘, 다큐 무드",
         "keywords": "British film photography aesthetic / overcast diffused daylight / cool grey undertones / strong shadow contrast / heavy visible grain / documentary street photography mood / Ilford HP5 or Kodak Portra on cloudy day"},
    13: {"name": "푸른 느낌 필름 감성",
         "desc": "시안, 블루 색감, 실험적 무드",
         "keywords": "cross-processed film photography / cyan and blue color shift / cool teal shadows / slightly unreal color palette / lomography cross process effect / cold and ethereal atmosphere"},
    14: {"name": "웨딩 필름 감성",
         "desc": "크리미한 화이트, 자연광, 로맨틱",
         "keywords": "Kodak Portra 800 film wedding photography / creamy white tones / soft blown out highlights / warm glowing skin / natural light only no flash / romantic and timeless mood / film grain visible but fine"},
    15: {"name": "스냅 필름 감성",
         "desc": "순간 포착, 플래시, 생활감",
         "keywords": "disposable camera snapshot aesthetic / direct flash photography / slightly flat lighting / vivid candid colors / imperfect composition / caught in the moment / early 2000s party photo feeling"},
    16: {"name": "35mm 스냅샷",
         "desc": "순간 감정, 따뜻한 기억, 빛 번짐",
         "keywords": "35mm film snapshot / Kodak ColorPlus or Fuji Superia 400 / natural sunlight / halation on highlights / light leaks / warm nostalgic tones / candid emotional moment / grain / film border"},

    # ── 기법 (특수 효과) ───────────────────────────────────────────────
    17: {"name": "Halation 빛 번짐",
         "desc": "강한 빛 주변 몽환적 번짐",
         "keywords": "halation effect / light bleeding around bright sources / dreamy glow / warm light halo / analog film halation / soft edges around highlights / Cinestill halation"},
    18: {"name": "Bloom 하이라이트 퍼짐",
         "desc": "밝은 영역이 퍼지는 꿈결 분위기",
         "keywords": "bloom effect / highlight spreading / dreamy soft glow / overexposed highlights bleeding into midtones / ethereal atmosphere / soft hazy light / romantic bloom"},
    19: {"name": "Lifted Blacks 검정 띄우기",
         "desc": "완전한 검정 대신 살짝 회색으로",
         "keywords": "lifted blacks / faded shadows / matte black tones / vintage faded look / soft shadow detail / no pure black / milky shadows / instagram film preset feel"},
    20: {"name": "Chromatic Aberration 색수차",
         "desc": "렌즈 끝 색 번짐, 필름 느낌 강화",
         "keywords": "chromatic aberration / color fringing on edges / lens aberration effect / RGB color split on borders / analog lens distortion / film lens imperfection"},
    21: {"name": "Soft Diffusion 확산 필터",
         "desc": "빛을 부드럽게 퍼뜨려 피부와 경계를 은은하게",
         "keywords": "soft diffusion filter / gentle soft focus / skin smoothing glow / dreamy diffused light / pro-mist filter effect / romantic haze / soft edges / portrait diffusion"},

    # ── 기법 (노출·빛·현상) ────────────────────────────────────────────
    22: {"name": "Overexposure 오버노출",
         "desc": "하이라이트 날림, 부드럽고 몽환적",
         "keywords": "soft overexposed highlights / slightly blown out whites / bright airy atmosphere / overexposed film look / dreamy washed out / wedding bright snap"},
    23: {"name": "Underexposure 언더노출",
         "desc": "그림자 깊어짐, 무게감 있는 분위기",
         "keywords": "slightly underexposed shadows / deep muted tones / dark cinematic mood / heavy shadows / underexposed film / moody dark atmosphere / British film look"},
    24: {"name": "Diffused Light 확산광",
         "desc": "빛이 부드럽게 퍼짐, 피부 표현 좋아짐",
         "keywords": "soft diffused daylight / gentle shadows / light filtered through sheer curtains / diffused window light / flattering skin tone light / soft portrait lighting"},
    25: {"name": "Cross Process 크로스 프로세스",
         "desc": "색이 비현실적으로 변함, 청록 계열",
         "keywords": "cross processed film colors / cyan color shift / unusual color palette / experimental color rendering / lomography cross process / teal and orange shift / surreal color"},
    26: {"name": "Soft Focus 소프트 포커스",
         "desc": "초점이 부드러움, 회상 같은 느낌",
         "keywords": "soft focus / dreamy blur / gentle lens softness / portrait soft focus / romantic haze / vintage soft lens / memory-like blur / Japanese film softness"},
    27: {"name": "Vignetting 비네팅",
         "desc": "가장자리 어두워짐, 중앙 집중",
         "keywords": "subtle vignetting / darkened edges / center-focused composition / natural lens vignette / analog camera vignetting / snapshot vignette / focus drawing"},
    28: {"name": "Film Grain 필름 그레인",
         "desc": "필름 입자 표현, 아날로그 질감",
         "keywords": "fine film grain / visible analog texture / 35mm film grain / heavy grain / natural film noise / analog film feeling / grain overlay / ISO 400 grain"},
}

FILTER_LIST_FOR_PROMPT = "\n".join(
    f"{k}. {v['name']} — {v['desc']}" for k, v in FILTERS.items() if k <= 16
)

TECHNIQUE_LIST_FOR_PROMPT = "\n".join(
    f"{k}. {v['name']} — {v['desc']}" for k, v in FILTERS.items() if k >= 17
) + "\n0. 없음 — 기법 없이 필름만 적용"

SCENE_SYSTEM = """당신은 사진 분석 전문가입니다.
사진을 보고 아래 JSON 형식으로만 출력하세요. JSON 외 텍스트 없이.

{
  "subject": "주요 피사체",
  "lighting": "빛의 특성",
  "light_direction": "빛의 방향",
  "exposure": "노출 느낌",
  "mood": "전반적인 분위기",
  "composition": "구도 특징"
}"""

RECOMMEND_SYSTEM = f"""당신은 필름 사진 전문가입니다.
사진 분석 데이터를 보고 가장 어울리는 필터 3개와 추가 기법 1개를 JSON으로만 출력하세요.

필터 목록 (1-16):
{FILTER_LIST_FOR_PROMPT}

기법 목록:
{TECHNIQUE_LIST_FOR_PROMPT}

출력 형식:
{{
  "filters": [
    {{"num": 1, "name": "Kodak Portra 400", "reason": "이유 한 문장"}},
    {{"num": 2, "name": "Kodak Gold 200", "reason": "이유 한 문장"}},
    {{"num": 3, "name": "Fujifilm Pro 400H", "reason": "이유 한 문장"}}
  ],
  "technique": {{"num": 21, "name": "Soft Diffusion 확산 필터", "reason": "이유 한 문장"}}
}}

기법이 필요 없으면 technique.num을 0으로 설정하세요."""

PROMPT_SYSTEM = """당신은 필름 사진 전문가이자 AI 이미지 프롬프트 작성 전문가입니다.
사진을 직접 보고, 선택된 필터 스타일을 적용해서 JSON으로만 출력하세요.

목표: AI 이미지 생성기가 원본 사진을 최대한 재현할 수 있도록 아래 항목을 빠짐없이 묘사하세요.

## 반드시 포함할 세부 항목
1. 피사체: 나이대, 성별, 체형, 헤어스타일, 머리 색상
2. 의상: 옷의 종류(드레스/롬퍼/티셔츠 등), 색상, 패턴(무지/체크/도트 등), 소매 형태
3. 액세서리: 헤어밴드, 모자, 가방, 신발 등 착용한 모든 것
4. 행동/표정: 무엇을 하고 있는지, 어떤 표정인지
5. 공간 관계 (매우 중요): 사진 속 각 피사체·동물·사람이 서로 어떤 위치 관계인지 명확히 기술
   - 예: "child walks AHEAD on the left, THREE geese walk BEHIND following the child"
   - 누가 앞/뒤/옆인지, 이동 방향이 같은지 반드시 명시
   - 동물·사람 수를 정확히 세어 숫자로 표기 (two, three 등)
6. 바닥/표면: 재질(나무/카펫/흙길 등), 색상
7. 배경: 소품, 가구, 식물, 장식물 등 보이는 모든 것
8. 빛: 방향, 세기, 색온도(따뜻한/차가운/중립), 그림자 유무
9. 카메라 앵글: 촬영 거리, 높이, 방향 (피사체 정면/측면/후면 중 무엇인지)

공식: [피사체 상세 묘사] + [공간 관계·수량 명시] + [의상·액세서리 상세] + [배경 상세] + [바닥/표면] + [빛 묘사] + [필름 이름] + [필터 색감/그레인]

{
  "prompt_universal": "범용 프롬프트 — 위 9개 항목 전부 포함, 공간관계·수량 명확히, 필터 적용 (영어, 4-6문장)",
  "prompt_midjourney": "Midjourney 최적화 — 쉼표 구분 키워드, 공간관계·수량 포함 (--ar 4:5 --v 6.1)",
  "prompt_dalle": "DALL-E / ChatGPT 최적화 — 자연스러운 문장으로 장면 완전 묘사 + 필터 (영어)",
  "hook_ko": "인스타그램 도입 훅 문장 (한국어 1문장, 궁금증·공감 유발, 이모지 없이)",
  "cta_ko": "마무리 CTA 문장 (한국어 1문장, 저장·팔로우·댓글 중 하나 유도)",
  "caption_ko": "인스타그램 전체 캡션 초안 (한국어, 훅 + 프롬프트 소개 + CTA, 3-5문장)"
}"""


def encode_image(image_path: str) -> tuple:
    path = Path(image_path)
    ext = path.suffix.lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    # 1차: 그대로 파싱
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2차: { 시작 위치부터 중첩 깊이로 정확한 끝 찾기
    start = raw.find("{")
    if start != -1:
        depth, end = 0, -1
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass

    # 3차: rfind로 마지막 } 까지 자르기
    last = raw.rfind("}")
    if last > 0:
        try:
            return json.loads(raw[:last + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON 파싱 실패 (앞 200자): {raw[:200]}")


def analyze_scene(image_path: str) -> dict:
    """1단계: 사진의 장면/빛/구도 파악."""
    if not ANTHROPIC_API_KEY:
        raise ValueError(".env에 ANTHROPIC_API_KEY가 없습니다.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    image_data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SCENE_SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": "이 사진을 JSON으로 분석해주세요."},
            ],
        }],
    )
    result = _parse_json(message.content[0].text)
    result["source_image"] = str(Path(image_path).name)
    return result


def get_recommendations(scene: dict) -> dict:
    """사진 분석 기반 필터 3개 + 기법 1개 추천 (텍스트 전용, 별도 호출)."""
    empty = {"filters": [], "technique": None}
    if not ANTHROPIC_API_KEY:
        return empty
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        scene_text = (
            f"피사체: {scene.get('subject', '')}\n"
            f"빛: {scene.get('lighting', '')} / {scene.get('light_direction', '')}\n"
            f"노출: {scene.get('exposure', '')}\n"
            f"분위기: {scene.get('mood', '')}\n"
            f"구도: {scene.get('composition', '')}"
        )
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=RECOMMEND_SYSTEM,
            messages=[{"role": "user", "content": scene_text}],
        )
        result = _parse_json(message.content[0].text)
        if isinstance(result, dict):
            filters = result.get("filters", [])
            technique = result.get("technique")
            if technique and technique.get("num", 0) == 0:
                technique = None
            return {"filters": filters if isinstance(filters, list) else [], "technique": technique}
        return empty
    except Exception:
        return empty


def generate_prompt(scene: dict, filter_num: int, technique_num: int = None, image_path: str = None, extra: str = None) -> dict:
    """2단계: 선택한 필터 기준으로 최종 프롬프트 생성. 이미지 경로가 있으면 Vision 사용."""
    if not ANTHROPIC_API_KEY:
        raise ValueError(".env에 ANTHROPIC_API_KEY가 없습니다.")

    selected = FILTERS[filter_num]
    technique = FILTERS.get(technique_num) if technique_num else None
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    technique_text = ""
    if technique:
        technique_text = (
            f"\n\n추가 기법 효과: {technique['name']}\n"
            f"기법 설명: {technique['desc']}\n"
            f"기법 키워드: {technique['keywords']}\n"
            f"→ 위 필름 스타일에 이 기법을 함께 적용해서 프롬프트에 반영하세요."
        )

    extra_text = f"\n\n추가 요소 (반드시 포함): {extra}" if extra else ""

    user_text = f"""이 사진을 직접 보고, 아래 필터를 적용한 AI 이미지 프롬프트를 JSON으로 생성해주세요.

선택한 필터: {selected['name']}
필터 설명: {selected['desc']}
필터 키워드: {selected['keywords']}{technique_text}{extra_text}

사진에 보이는 피사체, 의상, 배경, 행동, 색상, 구도를 최대한 구체적으로 묘사해서
AI가 이 사진과 최대한 비슷한 이미지를 생성할 수 있는 프롬프트를 만들어주세요."""

    # 이미지 경로가 있으면 Vision으로, 없으면 텍스트 분석으로
    if image_path and os.path.exists(image_path):
        image_data, media_type = encode_image(image_path)
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
            {"type": "text", "text": user_text},
        ]
    else:
        fallback = (
            f"피사체: {scene.get('subject', '')}, "
            f"빛: {scene.get('lighting', '')}, "
            f"분위기: {scene.get('mood', '')}\n\n{user_text}"
        )
        content = fallback

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=PROMPT_SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    result = _parse_json(message.content[0].text)
    result["filter_name"] = selected["name"] + (f" + {technique['name']}" if technique else "")
    result["filter_desc"] = selected["desc"] + (f" / {technique['desc']}" if technique else "")
    result["source_image"] = scene.get("source_image", "")
    return result


def save_result(result: dict, output_dir: str = ".tmp") -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "analysis.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return path
