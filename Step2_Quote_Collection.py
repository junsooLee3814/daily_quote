from datetime import datetime
import re
from common_utils import get_gsheet, client

NEWS_SHEET = 'morning_news'
NOTE_SHEET = 'morning_quotes'  # 기존 시트명 재사용

def get_today_news_summary():
    sheet = get_gsheet(NEWS_SHEET)
    today = datetime.now().strftime('%Y-%m-%d')
    all_rows = sheet.get_all_records()
    news_list = [row['card_summary'] for row in all_rows if today in row['date']]
    return '\n'.join(news_list[:5])

def get_notes_by_generation(news_summary):
    today = datetime.now().strftime("%Y년 %m월 %d일 오늘의 한줄노트")
    prompt = f"""
아래는 오늘의 주요 뉴스 요약입니다.

{news_summary}

이 뉴스를 바탕으로 각 세대별(Youth: 20세 미만, Adults: 21~60세, Seniors: 60세 초과)로
각 세대의 이해관계를 분석하고, 각 세대에 맞는 '오늘의 노트'를 1개씩 추천해 주세요.

**중요:**
- 2025년 사람들이 공감할 만한 트렌디한 단어, 신조어, 감성, 밈, 소셜미디어 스타일을 적극 반영해 주세요.
- 각 세대별로 선호하는 언어 스타일(예: MZ세대는 짧고 임팩트 있게, 시니어는 따뜻하고 공감가게 등)을 고려해 주세요.
- 기존 명언/노트의 원문에만 충실하지 말고, 2025년의 사회적 이슈, 유행, 감성, 긍정적 에너지, 희망, 위로, 동기부여 등도 반영해 주세요.
- 너무 딱딱하거나 고전적인 표현은 피하고, 요즘 사람들이 SNS에서 자주 쓰는 말투/톤/밈 등을 적절히 활용해 주세요.
- ※ 주의: 이모지(😊, 🚫 등), 특수문자, 기호(★, ♡ 등)는 절대 사용하지 마세요. 오직 한글, 영문, 숫자, 쉼표, 마침표 등만 사용하세요.

각 노트는 아래 항목을 포함해야 합니다.

1. 일자: {today}
2. 연령대: (Youth/Adults/Seniors)
3. 노트제목: (핵심을 한 문장으로 요약, 트렌디한 키워드/표현 적극 활용)
4. 노트본문: (2~4줄, 한 줄에 15~25자 이내, 요즘 감성/신조어/밈 등 활용)
5. 노트출처: (작가, 책, 출처 등)
6. 노트의미: (이 노트가 주는 교훈, 감상, 해설 등 2~3줄, 한 줄에 15~25자 이내, 2025년 감성/트렌드 반영)

아래와 같은 형식으로 출력해 주세요.

---
연령대: Youth
일자: 2025년 5월 22일 오늘의 한줄노트
노트제목: 미래를 준비하는 힘
노트본문:
오늘의 변화는 내일의 기회
작은 도전이 큰 성장을 만든다
노트출처: 미상
노트의미:
청춘은 도전의 시간!  
실패를 두려워하지 말자  
---
(이 형식으로 각 세대별 1개씩, 총 3개)
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def parse_notes(gpt_response):
    blocks = re.split(r'-{3,}', gpt_response)
    notes = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        연령대 = re.search(r'연령대: ?(.+)', block)
        일자 = re.search(r'일자: ?(.+)', block)
        노트제목 = re.search(r'노트제목: ?(.+)', block)
        노트본문 = re.search(r'노트본문:\n?([\s\S]*?)\n노트출처:', block)
        노트출처 = re.search(r'노트출처: ?(.+)', block)
        노트의미 = re.search(r'노트의미:\n?([\s\S]*)', block)
        notes.append({
            "일자": 일자.group(1).strip() if 일자 else '',
            "연령대": 연령대.group(1).strip() if 연령대 else '',
            "노트제목": 노트제목.group(1).strip() if 노트제목 else '',
            "노트본문": 노트본문.group(1).strip() if 노트본문 else '',
            "노트출처": 노트출처.group(1).strip() if 노트출처 else '',
            "노트의미": 노트의미.group(1).strip() if 노트의미 else ''
        })
    return [n for n in notes if any(n.values())]

def translate_to_english(korean_text):
    prompt = f"다음 문장을 자연스러운 영어 제목으로 번역해줘:\n{korean_text}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def save_notes_to_gsheet(notes):
    sheet = get_gsheet(NOTE_SHEET)
    # 기존 데이터(2행 이하) 모두 삭제
    if sheet.row_count > 1:
        sheet.delete_rows(2, sheet.row_count)
    # 헤더가 없거나 다르면 추가 (삭제/clear 없이!)
    expected_header = ['Date', 'Age Group', 'Note Title', 'Note Title EN', 'Note Body', 'Source', 'Note Meaning']
    current_header = sheet.row_values(1)[:len(expected_header)]
    if current_header != expected_header:
        sheet.insert_row(expected_header, 1)
    for n in notes:
        note_title_en = n.get("Note Title EN", "")
        if not note_title_en and n.get("노트제목", ""):
            note_title_en = translate_to_english(n["노트제목"])
        row_data_dict = {
            'Date': n.get("일자", ""),
            'Age Group': n.get("연령대", ""),
            'Note Title': n.get("노트제목", ""),
            'Note Title EN': note_title_en,
            'Note Body': n.get("노트본문", ""),
            'Source': n.get("노트출처", ""),
            'Note Meaning': n.get("노트의미", "")
        }
        row_data = [row_data_dict[k] for k in expected_header]
        sheet.append_row(row_data)
    print(f"{len(notes)}개의 오늘의 노트가 구글시트에 저장되었습니다.")

if __name__ == "__main__":
    print("[오늘의 뉴스 요약 불러오는 중...]")
    news_summary = get_today_news_summary()
    print("[GPT-4o에게 세대별 오늘의 노트 요청 중...]")
    gpt_response = get_notes_by_generation(news_summary)
    print("\n=== GPT-4o 응답 ===\n")
    print(gpt_response)
    print("\n[노트 파싱 및 구글시트 저장 중...]")
    notes = parse_notes(gpt_response)
    save_notes_to_gsheet(notes)
    print("\n=== 오늘의 세대별 노트 저장 완료 ===") 