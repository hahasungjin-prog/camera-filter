"""
Unsplash 무료 사진 1장 다운 → 28가지 필터 적용 → assets/filters/ 저장
Unsplash License: 상업적 사용 포함 무료
"""

import os
import math
import numpy as np
from urllib.request import urlretrieve, Request, urlopen
from PIL import Image, ImageFilter
import io

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "filters")
TMP_DIR    = os.path.join(os.path.dirname(__file__), "..", ".tmp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

W, H = 400, 400

# 필름 종류 베이스 사진 (야외 자연광 인물 → 피부톤+하늘+녹색으로 색감 차이 극대화)
FILM_BASE_URLS = [
    # 시카고 스카이라인 (원본 도시 이미지)
    "https://images.pexels.com/photos/2880507/pexels-photo-2880507.jpeg?auto=compress&cs=tinysrgb&w=400&h=400&fit=crop",
]

BASE_CACHE = os.path.join(TMP_DIR, "film_base.jpg")

# 전체 필터 번호 (1-28 전부 도시 이미지로 생성)
FILM_TYPE_NUMS = list(range(1, 29))


def download_base() -> Image.Image:
    """필름 종류용 베이스 사진 다운로드 (캐시 있으면 재사용)"""
    if os.path.exists(BASE_CACHE):
        print(f"  캐시 사용: {BASE_CACHE}")
        return Image.open(BASE_CACHE).convert("RGB").resize((W, H))

    for url in FILM_BASE_URLS:
        try:
            print(f"  다운로드 시도: {url[:60]}...")
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urlopen(req, timeout=15).read()
            img = Image.open(io.BytesIO(data)).convert("RGB").resize((W, H))
            img.save(BASE_CACHE, "JPEG", quality=92)
            print(f"  저장 완료: {BASE_CACHE}")
            return img
        except Exception as e:
            print(f"  실패: {e}")

    raise RuntimeError("모든 URL 다운로드 실패. 인터넷 연결을 확인하세요.")


# ── 이미지 처리 유틸 ──────────────────────────────────────────────
def arr(img): return np.array(img, dtype=np.float32)
def to_img(a): return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def color_shift(img, r=1.0, g=1.0, b=1.0, r_add=0, g_add=0, b_add=0):
    a = arr(img)
    a[:,:,0] = np.clip(a[:,:,0]*r + r_add, 0, 255)
    a[:,:,1] = np.clip(a[:,:,1]*g + g_add, 0, 255)
    a[:,:,2] = np.clip(a[:,:,2]*b + b_add, 0, 255)
    return to_img(a)

def adjust_saturation(img, factor=1.0):
    a = arr(img)
    gray = (0.299*a[:,:,0] + 0.587*a[:,:,1] + 0.114*a[:,:,2])[:,:,np.newaxis]
    return to_img(gray + (a - gray) * factor)

def adjust_contrast(img, factor=1.0):
    a = arr(img)
    return to_img(128 + (a - 128) * factor)

def lift_blacks(img, lift=20):
    a = arr(img)
    return to_img(a + lift * (1 - a / 255))

def add_grain(img, amount=8):
    a = arr(img)
    noise = np.random.normal(0, amount, a.shape)
    return to_img(a + noise)

def add_vignette(img, strength=0.5):
    a = arr(img)
    rows, cols = a.shape[:2]
    Y, X = np.ogrid[:rows, :cols]
    dist = np.sqrt(((X - cols/2)/(cols/2))**2 + ((Y - rows/2)/(rows/2))**2)
    mask = 1 - np.clip(dist * strength, 0, 1)
    return to_img(a * mask[:,:,np.newaxis])

def add_halation(img, strength=0.4):
    a = arr(img)
    bright = np.clip(a - 180, 0, 255)
    blur = to_img(bright).filter(ImageFilter.GaussianBlur(radius=18))
    halo = arr(blur)
    halo[:,:,0] *= 1.8; halo[:,:,1] *= 0.3; halo[:,:,2] *= 0.2
    return to_img(a + halo * strength)

def add_bloom(img, strength=0.5):
    a = arr(img)
    bright = to_img(np.clip(a - 150, 0, 255))
    blurred = bright.filter(ImageFilter.GaussianBlur(radius=22))
    return to_img(a + arr(blurred) * strength)

def to_bw(img):
    a = arr(img)
    gray = 0.299*a[:,:,0] + 0.587*a[:,:,1] + 0.114*a[:,:,2]
    return to_img(np.stack([gray]*3, axis=2))

def cross_process(img):
    a = arr(img)
    a[:,:,0] = np.clip(a[:,:,0]*0.7, 0, 255)
    a[:,:,2] = np.clip(a[:,:,2]*1.3 + 20, 0, 255)
    mask = arr(img).mean(axis=2) / 255
    a[:,:,0] += mask * 30; a[:,:,1] += mask * 15; a[:,:,2] -= mask * 20
    return to_img(a)

def soft_focus(img, amount=0.35):
    blurred = img.filter(ImageFilter.GaussianBlur(radius=6))
    return to_img(arr(img)*(1-amount) + arr(blurred)*amount)

def add_chromatic(img, shift=5):
    a = arr(img)
    result = np.zeros_like(a)
    result[:,shift:,0]  = a[:,:-shift,0]
    result[:,:,1]        = a[:,:,1]
    result[:,:-shift,2]  = a[:,shift:,2]
    return to_img(result)


# ── 필터별 적용 ───────────────────────────────────────────────────
def apply_filter(base: Image.Image, num: int) -> Image.Image:
    img = base.copy()

    if num == 1:   # Kodak Portra 400
        img = color_shift(img, r=1.08, g=1.02, b=0.88, r_add=8, g_add=3)
        img = adjust_saturation(img, 0.85)
        img = lift_blacks(img, 12)
        img = add_grain(img, 5)

    elif num == 2: # Kodak Gold 200
        img = color_shift(img, r=1.14, g=1.05, b=0.72, r_add=15, g_add=8)
        img = adjust_saturation(img, 1.1)
        img = add_grain(img, 9)

    elif num == 3: # Fujifilm Pro 400H
        img = color_shift(img, r=0.88, g=1.05, b=0.96, g_add=10, b_add=5)
        img = adjust_saturation(img, 0.72)
        img = lift_blacks(img, 18)
        img = add_grain(img, 5)

    elif num == 4: # Kodak Ektar 100
        img = color_shift(img, r=1.15, g=0.95, b=0.88)
        img = adjust_saturation(img, 1.45)
        img = adjust_contrast(img, 1.22)
        img = add_grain(img, 3)

    elif num == 5: # Ilford HP5
        img = to_bw(img)
        img = adjust_contrast(img, 1.4)
        img = add_vignette(img, 0.75)
        img = add_grain(img, 20)

    elif num == 6: # Kodak ColorPlus
        img = color_shift(img, r=1.08, g=0.98, b=0.80, r_add=10)
        img = add_halation(img, 0.25)
        img = add_grain(img, 10)

    elif num == 7: # Fuji Superia 400
        img = color_shift(img, r=0.95, g=1.08, b=0.90, g_add=8)
        img = adjust_saturation(img, 1.12)
        img = add_grain(img, 8)

    elif num == 8: # Cinestill 50D
        img = color_shift(img, r=0.82, g=0.80, b=1.12, b_add=22)
        img = add_halation(img, 0.9)
        img = adjust_contrast(img, 1.18)
        img = add_grain(img, 4)

    elif num == 9: # Lomography 800
        img = cross_process(img)
        img = adjust_saturation(img, 1.6)
        img = add_vignette(img, 1.0)
        img = add_grain(img, 26)

    elif num == 10: # 녹진한 숲속
        img = color_shift(img, r=0.80, g=1.10, b=0.82, g_add=15)
        img = adjust_saturation(img, 0.78)
        img = lift_blacks(img, 16)
        img = add_grain(img, 6)

    elif num == 11: # 일본식 필름
        img = color_shift(img, r=1.05, g=0.95, b=0.95, r_add=18, g_add=6, b_add=10)
        img = adjust_saturation(img, 0.68)
        img = lift_blacks(img, 22)
        img = add_vignette(img, 0.38)
        img = soft_focus(img, 0.2)
        img = add_grain(img, 6)

    elif num == 12: # 영국식 필름
        img = color_shift(img, r=0.88, g=0.88, b=0.95, b_add=6)
        img = adjust_saturation(img, 0.55)
        img = adjust_contrast(img, 1.3)
        img = add_vignette(img, 0.65)
        img = add_grain(img, 18)

    elif num == 13: # 푸른 느낌
        img = cross_process(img)
        img = color_shift(img, r=0.72, g=0.95, b=1.25, b_add=28)
        img = adjust_saturation(img, 1.25)
        img = add_grain(img, 11)

    elif num == 14: # 웨딩 필름
        img = color_shift(img, r=1.05, g=1.02, b=0.90, r_add=14, g_add=9)
        img = adjust_saturation(img, 0.72)
        img = lift_blacks(img, 28)
        img = to_img(np.clip(arr(img)*1.18, 0, 255))
        img = add_grain(img, 4)

    elif num == 15: # 스냅 필름
        img = color_shift(img, r=1.02, g=1.02, b=1.06, r_add=6, g_add=6, b_add=8)
        img = adjust_saturation(img, 1.12)
        img = add_grain(img, 13)

    elif num == 16: # 35mm 스냅샷
        img = color_shift(img, r=1.12, g=0.97, b=0.80, r_add=12)
        img = add_halation(img, 0.32)
        img = add_vignette(img, 0.52)
        img = add_grain(img, 12)

    elif num == 17: # Halation 빛 번짐
        img = add_halation(img, 1.4)
        img = color_shift(img, r=1.06, b=0.88)

    elif num == 18: # Bloom
        img = add_bloom(img, 0.9)
        img = to_img(np.clip(arr(img)*1.12, 0, 255))

    elif num == 19: # Lifted Blacks
        img = lift_blacks(img, 45)
        img = adjust_saturation(img, 0.82)
        img = adjust_contrast(img, 0.82)

    elif num == 20: # Chromatic Aberration
        img = add_chromatic(img, 8)
        img = adjust_contrast(img, 1.12)

    elif num == 21: # Soft Diffusion
        img = soft_focus(img, 0.55)
        img = color_shift(img, r=1.04, g=1.03, b=1.03, r_add=10, g_add=6, b_add=10)

    elif num == 22: # Overexposure
        img = to_img(np.clip(arr(img)*1.4 + 22, 0, 255))
        img = adjust_saturation(img, 0.78)

    elif num == 23: # Underexposure
        img = to_img(np.clip(arr(img)*0.55, 0, 255))
        img = adjust_contrast(img, 1.25)
        img = add_vignette(img, 0.85)

    elif num == 24: # Diffused Light
        img = soft_focus(img, 0.32)
        img = color_shift(img, r=1.06, g=1.03, b=0.93, r_add=12, g_add=6)

    elif num == 25: # Cross Process
        img = cross_process(img)
        img = adjust_saturation(img, 1.35)
        img = adjust_contrast(img, 1.18)

    elif num == 26: # Soft Focus
        img = soft_focus(img, 0.65)
        img = add_grain(img, 4)

    elif num == 27: # Vignetting
        img = add_vignette(img, 1.3)
        img = adjust_contrast(img, 1.12)

    elif num == 28: # Film Grain
        img = add_grain(img, 35)
        img = adjust_saturation(img, 0.88)

    return img


def generate():
    print("필름 종류 베이스 사진 준비 중...")
    base = download_base()
    print(f"  베이스 사진 크기: {base.size}")

    print(f"\n필름 종류 필터 적용 중 ({FILM_TYPE_NUMS})...")
    for num in FILM_TYPE_NUMS:
        out_path = os.path.join(OUTPUT_DIR, f"{num}.jpg")
        result = apply_filter(base, num)
        result.save(out_path, "JPEG", quality=92)
        print(f"  {num:2d}. 완료")

    print(f"\n완료: {len(FILM_TYPE_NUMS)}개 → {OUTPUT_DIR}")
    print("  (11-28은 실사 사진으로 별도 관리, 변경 없음)")


if __name__ == "__main__":
    generate()
