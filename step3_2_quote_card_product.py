import os
import shutil
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from common_utils import get_gsheet
import unicodedata
import ffmpeg

# 설정값
CARD_WIDTH = 1080
CARD_HEIGHT = 1920
TOP_MARGIN = 250   # 위쪽 인쇄영역 피하기 (로고)
BOTTOM_MARGIN = 220 # 아래쪽 인쇄영역 피하기 (강아지/광고)
LEFT_MARGIN = 80
RIGHT_MARGIN = 80
LINE_SPACING = 1.1  # 더 컴팩트한 줄간격
SECTION_GAP = 40    # 항목 간 간격

# 폰트 크기 및 영상 길이 설정
GEN_FONT_SIZE = 54        # 세대(예: [Youth])
DATE_FONT_SIZE = 44       # 날짜
TITLE_FONT_SIZE = 72      # 노트제목
BODY_FONT_SIZE = 54       # 본문
SOURCE_FONT_SIZE = 38     # 출처
MEANING_FONT_SIZE = BODY_FONT_SIZE  # 의미 글자 크기를 본문과 동일하게
IMG_DURATIONS = [7, 7, 10]  # 카드별 영상 길이(초)

# 이모지 지원 폰트 경로 리스트 (OS별로 경로 다름)
FONT_PATHS = [
    "C:/Windows/Fonts/seguiemj.ttf",            # 이모지 폰트 (항상 제일 위에!)
    os.path.join("assets", "Pretendard-Regular.otf"),  # 한글/영문 폰트
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # 리눅스 이모지
    "/usr/share/fonts/emoji/NotoColorEmoji.ttf",           # 리눅스 이모지(다른 경로)
]

KOR_FONT_PATH = os.path.join("assets", "Pretendard-Regular.otf")
KOR_FONT_BOLD_PATH = os.path.join("assets", "Pretendard-Bold.otf")
EMOJI_FONT_PATH = "C:/Windows/Fonts/seguiemj.ttf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# 폰트 준비 (이모지/한글 분리)
gen_font = load_font(KOR_FONT_PATH, GEN_FONT_SIZE)
date_font = load_font(KOR_FONT_PATH, DATE_FONT_SIZE)
title_font = load_font(KOR_FONT_PATH, TITLE_FONT_SIZE)
body_font = load_font(KOR_FONT_PATH, BODY_FONT_SIZE)
source_font = load_font(KOR_FONT_PATH, SOURCE_FONT_SIZE)
meaning_font = load_font(KOR_FONT_PATH, MEANING_FONT_SIZE)
emoji_gen_font = load_font(EMOJI_FONT_PATH, GEN_FONT_SIZE)
emoji_date_font = load_font(EMOJI_FONT_PATH, DATE_FONT_SIZE)
emoji_title_font = load_font(EMOJI_FONT_PATH, TITLE_FONT_SIZE)
emoji_body_font = load_font(EMOJI_FONT_PATH, BODY_FONT_SIZE)
emoji_source_font = load_font(EMOJI_FONT_PATH, SOURCE_FONT_SIZE)
emoji_meaning_font = load_font(EMOJI_FONT_PATH, MEANING_FONT_SIZE)

# Bold 폰트 준비 ([세대]용)
try:
    gen_font_bold = load_font(KOR_FONT_BOLD_PATH, GEN_FONT_SIZE)
except:
    gen_font_bold = gen_font

# 구글시트에서 세대별 오늘의 노트 불러오기
sheet = get_gsheet('morning_quotes')
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 세대별 1개씩만 추출 (Youth, Adults, Seniors)
generations = ['Youth', 'Adults', 'Seniors']
cards = []
for gen in generations:
    row = df[df['Age Group'] == gen].tail(1)
    if not row.empty:
        cards.append(row.iloc[0])

# 결과 저장 폴더 생성 (시간대별)
now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
result_dir = os.path.join("result_quotes", now_str)
os.makedirs(result_dir, exist_ok=True)

def draw_text_with_letter_spacing(draw, position, text, font, fill, letter_spacing=0):
    x, y = position
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + letter_spacing

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split()
    line = ''
    for word in words:
        test_line = line + (' ' if line else '') + word
        w = draw.textlength(test_line, font=font)
        if w <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

for idx, row in enumerate(cards):
    card = Image.open("assets/card_1080x1560.png").convert("RGBA")
    draw = ImageDraw.Draw(card)
    y = TOP_MARGIN
    max_text_width = CARD_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

    # 1. 세대 (진한 파랑, Bold)
    gen_text = f"[{row['Age Group']}]"
    draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), gen_text, gen_font_bold, fill=(0,60,200,255), letter_spacing=-2)
    y += int(GEN_FONT_SIZE * LINE_SPACING) + SECTION_GAP

    # 2. 일자
    date_text = str(row['Date'])
    draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), date_text, date_font, fill=(80,80,80,255), letter_spacing=-2)
    y += int(DATE_FONT_SIZE * LINE_SPACING) + SECTION_GAP

    # 3. 노트제목 (굵고 크게)
    title_lines = wrap_text(str(row['Note Title']), title_font, max_text_width, draw)
    for line in title_lines[:2]:
        draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), line, title_font, fill=(0,0,0,255), letter_spacing=-2)
        y += int(TITLE_FONT_SIZE * LINE_SPACING)
    y += SECTION_GAP

    # 4. 원본문
    body_lines = wrap_text(str(row['Note Body']), body_font, max_text_width, draw)
    for line in body_lines:
        draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), line, body_font, fill=(34,34,34,255), letter_spacing=-2)
        y += int(BODY_FONT_SIZE * LINE_SPACING)
    y += SECTION_GAP

    # 5. 출처
    draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), str(row['Source']), source_font, fill=(80,80,160,255), letter_spacing=-2)
    y += int(SOURCE_FONT_SIZE * LINE_SPACING) + SECTION_GAP

    # 출처-의미 사이 한 줄 여백 추가
    y += int(BODY_FONT_SIZE * LINE_SPACING)

    # 6. 의미 (진한 녹색)
    if 'Note Meaning' in row and str(row['Note Meaning']).strip():
        meaning_lines = wrap_text(str(row['Note Meaning']), meaning_font, max_text_width, draw)
        for line in meaning_lines:
            draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), line, meaning_font, fill=(0,120,60,255), letter_spacing=-2)
            y += int(MEANING_FONT_SIZE * LINE_SPACING)

    # 세대별 폴더 생성 및 저장 (quote_card/세대/quote_card.png)
    gen_folder = os.path.join('quote_card', row['Age Group'])
    os.makedirs(gen_folder, exist_ok=True)
    out_path = os.path.join(gen_folder, 'quote_card.png')
    card.save(out_path)
    print(f"명언 카드 저장: {out_path}") 