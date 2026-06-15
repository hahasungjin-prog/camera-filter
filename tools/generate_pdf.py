"""
스크린샷 학습 자료 → HTML 생성 → Edge headless PDF 변환
"""

import os
import sys
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.photo_analyzer import FILTERS

OUTPUT_HTML = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "필름감성_가이드.html"))
OUTPUT_PDF  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "필름감성_가이드.pdf"))
EDGE_EXE    = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def filter_rows(start, end):
    rows = ""
    for num in range(start, end):
        f = FILTERS[num]
        rows += f"""
        <tr>
          <td class="num">{num}</td>
          <td class="name">{f['name']}</td>
          <td class="desc">{f['desc']}</td>
          <td class="kw">{f['keywords']}</td>
        </tr>"""
    return rows


def combo_rows():
    combos = [
        ("웨딩 · 인물",   "Kodak Portra 400",       "Diffused Light 확산광",        "Soft Diffusion 확산 필터"),
        ("아기 · 순수",   "일본식 필름 감성",           "Overexposure 오버노출",         "Bloom 하이라이트 퍼짐"),
        ("도시 · 야경",   "Cinestill 50D",           "Underexposure 언더노출",        "Halation 빛 번짐"),
        ("레트로 · 일상", "Kodak Gold 200",          "Film Grain 필름 그레인",         "Vignetting 비네팅"),
        ("숲 · 자연",    "녹진한 숲속 필름 감성",         "Diffused Light 확산광",        "Lifted Blacks 검정 띄우기"),
        ("몽환 · 회상",   "Fujifilm Pro 400H",       "Soft Focus 소프트 포커스",       "Chromatic Aberration 색수차"),
        ("스트리트 · 다큐","영국식 필름 감성",            "Underexposure 언더노출",        "Film Grain 필름 그레인"),
        ("실험 · 아트",   "Lomography 800",          "Cross Process 크로스 프로세스",   "Halation 빛 번짐"),
    ]
    rows = ""
    for i, (sit, film, t1, t2) in enumerate(combos):
        cls = "even" if i % 2 == 0 else ""
        rows += f"""
        <tr class="{cls}">
          <td>{sit}</td><td>{film}</td><td>{t1}</td><td>{t2}</td>
        </tr>"""
    return rows


def build_html():
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
    font-size: 11px;
    color: #111;
    background: #fff;
  }}

  /* ── 표지 ── */
  .cover {{
    width: 210mm;
    height: 297mm;
    background: #000;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    page-break-after: always;
    color: #fff;
  }}
  .cover h1 {{ font-size: 38px; font-weight: 900; letter-spacing: 2px; margin-bottom: 8px; }}
  .cover h2 {{ font-size: 26px; font-weight: 400; color: #ccc; margin-bottom: 30px; }}
  .cover .sub {{ font-size: 13px; color: #888; margin-bottom: 60px; }}
  .cover .formula {{
    border: 1px solid #444;
    padding: 14px 28px;
    border-radius: 8px;
    font-size: 13px;
    color: #ddd;
    letter-spacing: 1px;
  }}
  .cover .formula span {{ color: #fff; font-weight: 700; }}

  /* ── 본문 ── */
  .page {{
    width: 210mm;
    padding: 14mm 14mm 12mm;
    page-break-after: always;
  }}

  .page-title {{
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 4px;
  }}
  .page-subtitle {{
    font-size: 10px;
    color: #888;
    margin-bottom: 12px;
  }}

  /* 공식 박스 */
  .formula-box {{
    background: #EFF6FF;
    border: 1.5px solid #2563EB;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 8px;
    text-align: center;
  }}
  .formula-box .label {{ font-size: 10px; color: #2563EB; font-weight: 700; margin-bottom: 4px; }}
  .formula-box .eq {{ font-size: 13px; font-weight: 700; color: #111; letter-spacing: 1px; }}

  .example-box {{
    background: #FFFBEB;
    border: 1.5px solid #D97706;
    border-radius: 8px;
    padding: 8px 16px;
    margin-bottom: 14px;
    text-align: center;
    font-size: 10px;
    color: #444;
  }}
  .example-box strong {{ color: #92400E; }}

  /* 섹션 헤더 */
  .section-header {{
    background: #000;
    color: #fff;
    padding: 7px 12px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 700;
    margin: 14px 0 6px;
  }}
  .section-header .badge {{
    display: inline-block;
    background: #fff;
    color: #000;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 3px;
    margin-right: 6px;
  }}
  .section-header .hint {{
    font-size: 9px;
    color: #aaa;
    font-weight: 400;
    margin-left: 8px;
  }}

  /* 필터 테이블 */
  table.filters {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 4px;
  }}
  table.filters th {{
    background: #f3f4f6;
    padding: 5px 8px;
    font-size: 9px;
    color: #555;
    font-weight: 700;
    text-align: left;
    border-bottom: 2px solid #000;
  }}
  table.filters td {{
    padding: 5px 8px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
    font-size: 10px;
  }}
  table.filters tr:nth-child(even) td {{ background: #f9fafb; }}
  td.num {{
    width: 28px;
    text-align: center;
    font-weight: 700;
    background: #000 !important;
    color: #fff;
    font-size: 11px;
  }}
  td.name {{ width: 130px; font-weight: 700; font-size: 11px; }}
  td.desc {{ width: 130px; color: #555; }}
  td.kw {{ color: #777; font-size: 9px; line-height: 1.5; }}

  /* 조합 테이블 */
  table.combo {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 6px;
  }}
  table.combo th {{
    background: #000;
    color: #fff;
    padding: 6px 10px;
    font-size: 10px;
    text-align: center;
  }}
  table.combo td {{
    padding: 6px 10px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 10px;
    text-align: center;
  }}
  table.combo tr.even td {{ background: #f9fafb; }}

  /* TIP */
  .tip {{
    background: #F0FDF4;
    border: 1.5px solid #16A34A;
    border-radius: 8px;
    padding: 10px 16px;
    margin-top: 14px;
    text-align: center;
    font-size: 10px;
    color: #333;
  }}
  .tip strong {{ color: #15803D; }}

  @media print {{
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
</head>
<body>

<!-- 표지 -->
<div class="cover">
  <h1>필름 감성</h1>
  <h2>프롬프트 가이드</h2>
  <div class="sub">Film Aesthetic Prompt Guide &nbsp;·&nbsp; 총 28종 필터 · 기법 정리</div>
  <div class="formula">
    <span>필름</span> &nbsp;+&nbsp; <span>빛</span> &nbsp;+&nbsp; <span>기법</span> &nbsp;+&nbsp; <span>색보정</span> &nbsp;=&nbsp; <span>원하는 필름 감성</span>
  </div>
</div>

<!-- 본문 p1 -->
<div class="page">
  <div class="page-title">필름 사진 감성 프롬프트 가이드</div>
  <div class="page-subtitle">스크린샷 학습 기반 &nbsp;·&nbsp; 총 28개 필터/기법 정리</div>

  <div class="formula-box">
    <div class="label">핵심 공식</div>
    <div class="eq">필름 이름 &nbsp;+&nbsp; 빛 &nbsp;+&nbsp; 기법 &nbsp;+&nbsp; 색보정 &nbsp;=&nbsp; 원하는 필름 감성</div>
  </div>

  <div class="example-box">
    <strong>예시</strong> &nbsp; Kodak Portra 400 &nbsp;+&nbsp; soft diffused daylight &nbsp;+&nbsp; soft overexposed highlights &nbsp;+&nbsp; fine film grain, warm tones &nbsp;=&nbsp; <strong>따뜻한 웨딩 필름 감성 완성!</strong>
  </div>

  <div class="section-header">
    <span class="badge">01</span>필름 종류
    <span class="hint">실제 필름 브랜드 기반 색감 재현</span>
  </div>
  <table class="filters">
    <tr><th>#</th><th>이름</th><th>설명</th><th>AI 프롬프트 키워드</th></tr>
    {filter_rows(1, 10)}
  </table>

  <div class="section-header">
    <span class="badge">02</span>감성
    <span class="hint">분위기 / 스타일 기반 필터</span>
  </div>
  <table class="filters">
    <tr><th>#</th><th>이름</th><th>설명</th><th>AI 프롬프트 키워드</th></tr>
    {filter_rows(10, 17)}
  </table>
</div>

<!-- 본문 p2 -->
<div class="page">
  <div class="section-header">
    <span class="badge">03</span>기법 — 특수 효과
    <span class="hint">필름 위에 얹는 추가 효과 (Halation · Bloom 등)</span>
  </div>
  <table class="filters">
    <tr><th>#</th><th>이름</th><th>설명</th><th>AI 프롬프트 키워드</th></tr>
    {filter_rows(17, 22)}
  </table>

  <div class="section-header">
    <span class="badge">04</span>기법 — 노출 · 빛 · 현상
    <span class="hint">Overexposure · Diffused Light · Film Grain 등</span>
  </div>
  <table class="filters">
    <tr><th>#</th><th>이름</th><th>설명</th><th>AI 프롬프트 키워드</th></tr>
    {filter_rows(22, 29)}
  </table>

  <div class="section-header">
    <span class="badge">05</span>조합 예시
    <span class="hint">필름 + 기법 조합 추천</span>
  </div>
  <table class="combo">
    <tr><th>상황</th><th>필름 / 감성</th><th>기법 1</th><th>기법 2</th></tr>
    {combo_rows()}
  </table>

  <div class="tip">
    <strong>TIP</strong> &nbsp; 필름 이름만 바꿔도, 빛 · 노출 · 기법 · 색보정을 조합하면 완전히 다른 분위기를 만들 수 있습니다!
  </div>
</div>

</body>
</html>"""
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 저장: {OUTPUT_HTML}")


def html_to_pdf():
    cmd = [
        EDGE_EXE,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={OUTPUT_PDF}",
        "--print-to-pdf-no-header",
        f"file:///{OUTPUT_HTML.replace(chr(92), '/')}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if os.path.exists(OUTPUT_PDF):
        print(f"PDF 저장: {OUTPUT_PDF}")
    else:
        print("PDF 변환 실패:", result.stderr[:300])


if __name__ == "__main__":
    build_html()
    html_to_pdf()
