"""
각 필터/기법별 색상 플레이스홀더 이미지 생성
assets/filters/1.jpg ~ 28.jpg
실제 사진 파일이 있으면 덮어쓰지 않음
"""

import os
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "filters")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 각 필터의 분위기를 표현하는 그라데이션 색상 (시작색, 끝색)
FILTER_COLORS = {
    # 필름 종류
    1:  ((245, 220, 180), (200, 160, 110)),  # Kodak Portra 400 — 크리미 웜
    2:  ((240, 190, 60),  (180, 120, 30)),   # Kodak Gold 200 — 골든 옐로우
    3:  ((180, 220, 190), (100, 160, 120)),  # Fujifilm Pro 400H — 소프트 그린
    4:  ((220, 60,  60),  (160, 30,  30)),   # Kodak Ektar 100 — 비비드 레드
    5:  ((80,  80,  80),  (30,  30,  30)),   # Ilford HP5 — 흑백
    6:  ((240, 160, 80),  (190, 110, 50)),   # Kodak ColorPlus — 웜 오렌지
    7:  ((140, 200, 140), (80,  150, 80)),   # Fuji Superia 400 — 프레시 그린
    8:  ((40,  40,  100), (10,  10,  60)),   # Cinestill 50D — 다크 네이비
    9:  ((160, 60,  180), (100, 20,  120)),  # Lomography 800 — 비비드 퍼플

    # 감성
    10: ((40,  100, 50),  (10,  60,  20)),   # 녹진한 숲속 — 딥 그린
    11: ((250, 200, 210), (230, 160, 180)),  # 일본식 — 소프트 핑크
    12: ((80,  90,  100), (40,  50,  60)),   # 영국식 — 다크 그레이
    13: ((30,  120, 180), (10,  70,  130)),  # 푸른 느낌 — 딥 블루
    14: ((255, 245, 220), (230, 210, 180)),  # 웨딩 — 아이보리
    15: ((220, 230, 240), (170, 185, 200)),  # 스냅 — 쿨 라이트
    16: ((160, 120, 80),  (100, 70,  40)),   # 35mm 스냅샷 — 웜 브라운

    # 기법 특수효과
    17: ((255, 140, 30),  (200, 80,  10)),   # Halation — 오렌지 글로우
    18: ((255, 230, 100), (220, 180, 50)),   # Bloom — 소프트 옐로우
    19: ((90,  110, 120), (50,  70,  80)),   # Lifted Blacks — 페이디드 그레이
    20: ((120, 30,  160), (60,  10,  100)),  # Chromatic Aberration — 퍼플
    21: ((200, 230, 255), (150, 190, 230)),  # Soft Diffusion — 소프트 블루

    # 기법 노출·빛·현상
    22: ((255, 250, 220), (230, 220, 180)),  # Overexposure — 밝은 화이트
    23: ((30,  30,  40),  (10,  10,  20)),   # Underexposure — 다크
    24: ((255, 235, 200), (220, 195, 160)),  # Diffused Light — 소프트 웜
    25: ((0,   120, 120), (0,   70,  80)),   # Cross Process — 틸 그린
    26: ((240, 200, 210), (200, 150, 165)),  # Soft Focus — 드리미 핑크
    27: ((30,  20,  60),  (10,  5,   30)),   # Vignetting — 다크 비네팅
    28: ((100, 75,  55),  (60,  40,  25)),   # Film Grain — 텍스처 브라운
}

SIZE = (200, 140)


def make_gradient(color1, color2, size=SIZE):
    """세로 그라데이션 이미지 생성"""
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        ratio = y / size[1]
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    # 약간 블러로 부드럽게
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    return img


def generate():
    created = 0
    skipped = 0
    for num, colors in FILTER_COLORS.items():
        for ext in ["jpg", "jpeg", "png", "webp"]:
            existing = os.path.join(OUTPUT_DIR, f"{num}.{ext}")
            if os.path.exists(existing):
                skipped += 1
                break
        else:
            out_path = os.path.join(OUTPUT_DIR, f"{num}.jpg")
            img = make_gradient(colors[0], colors[1])
            img.save(out_path, "JPEG", quality=90)
            created += 1

    print(f"생성: {created}개 / 스킵(실제사진 있음): {skipped}개")
    print(f"저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
