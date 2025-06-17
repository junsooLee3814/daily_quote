import os
import subprocess
from datetime import datetime
import shutil

# 세대 리스트
GENERATIONS = ['Youth', 'Adults', 'Seniors']

# 카드 이미지 경로
def get_card_path(gen):
    return os.path.join('quote_card', gen, 'quote_card.png')

# 카드별 영상 길이(초) - [인트로, Youth, Adults, Seniors]
DURATIONS = [2, 10, 10, 13]

# 오늘 날짜시간
now_str = datetime.now().strftime('%Y%m%d_%H%M%S')

WIDTH, HEIGHT = 1080, 1920

INTRO_IMG_PATH = os.path.join('assets', 'intro_note.png')
INTRO_OUT_PATH = os.path.join('quote_video', f'intro_note_{now_str}.mp4')
COMBINE_DIR = os.path.join('quote_video', '00combine')
COMBINE_OUT_PATH = os.path.join(COMBINE_DIR, 'merged_quotes.mp4')
FINAL_OUT_PATH = os.path.join(COMBINE_DIR, 'merged_quotes_bgm.mp4')
BGM_PATH = os.path.join('assets', 'bgm.mp3')

# 0. 인트로 영상 생성
def make_intro_video(img_path, out_path, duration):
    if os.path.exists(img_path):
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-t", str(duration),
            "-vf", f"zoompan=z='min(zoom+0.0015,1.1)':d={duration*25}:s={WIDTH}x{HEIGHT}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
        ]
        print("[인트로] " + " ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"[인트로] 인트로 영상 저장 완료: {out_path}")
        return out_path
    print("[인트로] intro_note.png 파일이 없어 인트로 영상 생략")
    return None

# 1. 카드별 명언 이미지 → mp4 생성
def make_card_videos(durations, now_str):
    video_paths = []
    for idx, (gen, duration) in enumerate(zip(GENERATIONS, durations)):
        img_path = get_card_path(gen)
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"카드 이미지가 없습니다: {img_path}")
        gen_dir = os.path.join('quote_video', gen)
        os.makedirs(gen_dir, exist_ok=True)
        out_path = os.path.join(gen_dir, f'merged_{now_str}.mp4')
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-t", str(duration),
            "-vf", f"zoompan=z='min(zoom+0.0015,1.1)':d={duration*25}:s={WIDTH}x{HEIGHT}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
        ]
        print(f"[{gen}] " + " ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"[{gen}] 명언 카드 영상 저장 완료: {out_path}")
        video_paths.append(out_path)
    return video_paths

# 2. 영상 합치기
def merge_videos_ffmpeg(video_paths, out_path):
    with open("video_list.txt", "w", encoding="utf-8") as f:
        for v in video_paths:
            abs_path = os.path.abspath(v).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "video_list.txt",
        "-c", "copy",
        out_path
    ]
    subprocess.run(cmd, check=True)
    os.remove("video_list.txt")
    print(f"[합친 영상 저장 완료] {out_path}")

# 3. 배경음악 삽입
def add_bgm_to_video(video_path, bgm_path, out_path, total_duration):
    cmd_bgm = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter:a", f"volume=0.5,afade=t=in:st=0:d=1,afade=t=out:st={total_duration-1}:d=1",
        "-shortest",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd_bgm, check=True)
    print(f"[배경음악 합친 영상 저장 완료] {out_path}")

# 4. 임시파일 정리
def clean_temp_quote_videos(intro_out_path=None):
    # 세대별 폴더 내 파일 삭제 후 폴더 자체도 삭제
    for gen in GENERATIONS:
        gen_dir = os.path.join('quote_video', gen)
        if os.path.exists(gen_dir):
            for f in os.listdir(gen_dir):
                try:
                    os.remove(os.path.join(gen_dir, f))
                except Exception as e:
                    print(f"[삭제 실패] {os.path.join(gen_dir, f)}: {e}")
            try:
                shutil.rmtree(gen_dir)
            except Exception as e:
                print(f"[폴더 삭제 실패] {gen_dir}: {e}")
    # 00combine 폴더 내 최종파일 제외 모두 삭제
    combine_path = COMBINE_DIR
    if os.path.exists(combine_path):
        for f in os.listdir(combine_path):
            if f != os.path.basename(FINAL_OUT_PATH):
                try:
                    os.remove(os.path.join(combine_path, f))
                except Exception as e:
                    print(f"[삭제 실패] {os.path.join(combine_path, f)}: {e}")
    # 인트로 mp4 삭제
    if intro_out_path and os.path.exists(intro_out_path):
        try:
            os.remove(intro_out_path)
        except Exception as e:
            print(f"[인트로 삭제 실패] {intro_out_path}: {e}")
    print(f"[정리 완료] 최종 파일만 남김: {FINAL_OUT_PATH}")

if __name__ == "__main__":
    intro_duration = DURATIONS[0]
    card_durations = DURATIONS[1:]
    intro_out_path = make_intro_video(INTRO_IMG_PATH, INTRO_OUT_PATH, intro_duration)
    card_video_paths = make_card_videos(card_durations, now_str)
    video_paths = ([intro_out_path] if intro_out_path else []) + card_video_paths
    os.makedirs(COMBINE_DIR, exist_ok=True)
    merge_videos_ffmpeg(video_paths, COMBINE_OUT_PATH)
    total_duration = sum(DURATIONS)
    add_bgm_to_video(COMBINE_OUT_PATH, BGM_PATH, FINAL_OUT_PATH, total_duration)
    clean_temp_quote_videos(intro_out_path=intro_out_path) 