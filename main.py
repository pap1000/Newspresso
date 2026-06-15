import os
import urllib.request
import json
from dotenv import load_dotenv

# .env 파일에 환경 변수로 저장된 키들을 로드
load_dotenv()

# os.environ.get()을 통해 안전하게 키를 가져옴
client_id = os.environ.get("NAVER_CLIENT_ID")
client_secret = os.environ.get("NAVER_CLIENT_SECRET")

def search_news(keyword):
    encText = urllib.parse.quote(keyword)  # 검색어를 URL 인코딩하여 안전하게 전달할 수 있도록 함
    # 뉴스 검색 API URL (최신 10개의 뉴스를 유사도 순으로 가져옴)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=10&sort=sim"
    
    # API 요청을 위한 헤더 설정 (클라이언트 ID와 시크릿 키 포함)
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            data = json.loads(response_body.decode('utf-8'))
            return data['items']
        else:
            print("오류 코드:" + str(rescode))
            return None
    except Exception as e:
        print("에러 발생:", e)
        return None

if __name__ == "__main__":
    # 검색하고 싶은 키워드를 입력
    target_keyword = "인공지능 에이전트"
    print(f"[{target_keyword}] 관련 최신 뉴스를 가져옵니다...\n")
    
    news_items = search_news(target_keyword)
    
    if news_items:
        for idx, item in enumerate(news_items, 1):
            # 뉴스 제목에 섞여 나오는 HTML 태그(<b> 등)를 깔끔하게 제거
            title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
            print(f"{idx}. {title}")
            print(f"   링크: {item['link']}\n")