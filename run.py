"""
사진 -> 분석 -> 필터 선택 -> 프롬프트 생성 -> 노션 저장
사용법: python run.py [이미지 경로]
"""

import sys
import os
from pathlib import Path
from tools.photo_analyzer import FILTERS, analyze_scene, generate_prompt, save_result


def show_filter_menu():
    print("\n" + "=" * 50)
    print("  필터를 선택하세요")
    print("=" * 50)
    print("\n  [필름 종류]")
    for i in range(1, 6):
        f = FILTERS[i]
        print(f"  {i:2}.  {f['name']:<22} {f['desc']}")
    print("\n  [감성]")
    for i in range(6, 12):
        f = FILTERS[i]
        print(f"  {i:2}.  {f['name']:<22} {f['desc']}")
    print()


def get_filter_choice() -> int:
    while True:
        try:
            choice = int(input("  번호 입력 (1-11): ").strip())
            if 1 <= choice <= 11:
                return choice
            print("  1~11 사이 숫자를 입력해주세요.")
        except (ValueError, KeyboardInterrupt):
            print("\n  취소됐습니다.")
            sys.exit(0)


def save_txt(result: dict, image_path: str):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    stem = Path(image_path).stem
    txt_path = os.path.join(output_dir, f"{stem}_result.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== 필름 감성 프롬프트 분석 결과 ===\n\n")
        f.write(f"원본 파일  : {result.get('source_image', '')}\n")
        f.write(f"선택 필터  : {result.get('filter_name', '')} ({result.get('filter_desc', '')})\n\n")
        f.write(f"[범용 프롬프트]\n{result.get('prompt_universal', '')}\n\n")
        f.write(f"[Midjourney]\n{result.get('prompt_midjourney', '')}\n\n")
        f.write(f"[DALL-E / ChatGPT]\n{result.get('prompt_dalle', '')}\n\n")
        f.write(f"[인스타 훅 도입문]\n{result.get('hook_ko', '')}\n\n")
        f.write(f"[CTA 문장]\n{result.get('cta_ko', '')}\n\n")
        f.write(f"[전체 캡션 초안]\n{result.get('caption_ko', '')}\n")
    return txt_path


def main():
    if len(sys.argv) < 2:
        print("사용법: python run.py [이미지 경로]")
        print("예시:   python run.py input/photo.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"\n오류: 파일을 찾을 수 없습니다 -> {image_path}")
        sys.exit(1)

    print("\n" + "=" * 50)
    print(f"  사진 로드: {Path(image_path).name}")
    print("=" * 50)

    # 1단계: 사진 분석
    print("\n[1/3] 사진 분석 중...")
    scene = analyze_scene(image_path)
    print(f"      피사체: {scene.get('subject', '')}")
    print(f"      빛    : {scene.get('lighting', '')}")
    print(f"      분위기: {scene.get('mood', '')}")

    # 2단계: 필터 선택
    show_filter_menu()
    choice = get_filter_choice()
    selected = FILTERS[choice]
    print(f"\n  선택됨: {selected['name']}")

    # 3단계: 프롬프트 생성
    print("\n[2/3] 프롬프트 생성 중...")
    result = generate_prompt(scene, choice)
    save_result(result)

    print("\n" + "-" * 50)
    print(f"  필터       : {result.get('filter_name', '')}")
    print(f"\n  [범용 프롬프트]")
    print(f"  {result.get('prompt_universal', '')}")
    print(f"\n  [Midjourney]")
    print(f"  {result.get('prompt_midjourney', '')}")
    print(f"\n  [훅 도입문]")
    print(f"  {result.get('hook_ko', '')}")
    print(f"\n  [CTA 문장]")
    print(f"  {result.get('cta_ko', '')}")
    print("-" * 50)

    txt_path = save_txt(result, image_path)
    print(f"\n  텍스트 저장됨: {txt_path}")

    # 4단계: 노션 저장
    print("\n[3/3] 노션 업로드 중...")
    from tools.notion_uploader import upload
    title = upload(result)
    print(f"      완료: {title}")

    print("\n" + "=" * 50)
    print("  완료! 노션에서 결과를 확인하세요.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
