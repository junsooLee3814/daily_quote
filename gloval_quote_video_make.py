import subprocess

if __name__ == "__main__":
    print("[1/3] 오늘의 명언(노트) 생성...")
    subprocess.run(["python", "Step2_Quote_Collection.py"], check=True)
    print("[2/3] 명언 카드 이미지 생성...")
    subprocess.run(["python", "step3_2_quote_card_product.py"], check=True)
    print("[3/3] 명언 카드 영상 생성 및 합치기...")
    subprocess.run(["python", "step4_2_quote_video.py"], check=True)
    print("\n[완료] 명언 카드 영상 자동화가 모두 끝났습니다!") 