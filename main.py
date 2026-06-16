import os
import urllib.request
import json
from dotenv import load_dotenv
from newspaper import Article

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

def get_news_content(url):
    try:
        # Article 객체를 생성할 때 언어 설정을 한국어('ko')로 설정
        article = Article(url, language='ko')
        article.download() # 웹사이트 다운로드
        article.parse()    # 본문 텍스트 분석 및 정제
        
        content = article.text
        
        # 네이버 뉴스 특유의 상단 안내 문구 노이즈 제거
        noise_text = "기사 섹션 분류 안내\n\n기사의 섹션 정보는 해당 언론사의 분류를 따르고 있습니다. 언론사는 개별 기사를 2개 이상 섹션으로 중복 분류할 수 있습니다."
        if content.startswith("기사 섹션 분류 안내"):
            content = content.replace(noise_text, "").strip()
            
        return content
    except Exception as e:
        # 크롤링이 막히는 경우
        return f"본문을 긁어오지 못했습니다. (이유: {e})"

if __name__ == "__main__":
    # 검색하고 싶은 키워드를 입력
    target_keyword = "인공지능 에이전트"
    print(f"[{target_keyword}] 관련 최신 뉴스를 가져옵니다...\n")
    
    news_items = search_news(target_keyword)
    
    if news_items:
        for idx, item in enumerate(news_items, 1):
            # HTML 태그 제거 및 제목 정리
            title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"')
            news_url = item['link']
            
            print(f"==================================================")
            print(f"{idx}. {title}")
            print(f"   링크: {news_url}")
            print(f"==================================================")
            print("⏳ 본문 수집 중...")
            
            # 본문을 수집하여 출력
            content = get_news_content(news_url)
            
            # 본문 출력
            print(f"📄 수집된 본문 전체 글자 수: {len(content)}자")
            print(f"📄 본문 전체 내용:\n{content}")
            print(f"==================================================\n")