import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    creds = Credentials.from_authorized_user_file('youtube_uploader/token.json', SCOPES)
    return build('youtube', 'v3', credentials=creds)

def upload_video(file_path, title, description, tags):
    youtube = get_authenticated_service()
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '25'  # 뉴스/정치 카테고리
        },
        'status': {
            'privacyStatus': 'private'
        }
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    response = request.execute()
    print('업로드 성공! 영상 ID:', response['id'])

if __name__ == '__main__':
    # 오늘 날짜 구하기
    today = datetime.now().strftime('%Y%m%d')

    # 제목, 설명, 태그 자동 생성 (글로벌 뉴스용)
    title = f"[글로벌뉴스] {today} 100초요약_글로벌 뉴스!! 이 포스팅은 쿠팡파트너스 활동으로 일정보수를 받습니다"
    description = "100초요약_오늘의 글로벌 주요 뉴스 만나보세요. AI가 자동으로 요약/제작합니다.이 포스팅은 쿠팡파트너스 활동으로 일정보수를 받습니다"
    tags = ["글로벌뉴스", "뉴스요약", "AI뉴스", "세계뉴스", "뉴스", "카드뉴스"]

    # 동영상 파일 경로 (워크플로우에서 보관한 경로와 일치해야 함)
    video_dir = "news_video"
    files = [f for f in os.listdir(video_dir) if f.startswith("merged_news_bgm") and f.endswith(".mp4")]

    if not files:
        raise FileNotFoundError("업로드할 동영상 파일이 없습니다.")
    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(video_dir, x)))
    video_path = os.path.join(video_dir, latest_file)

    upload_video(
        video_path,
        title,
        description,
        tags
    )
