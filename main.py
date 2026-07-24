import os
import urllib.request
import json
import html
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article
import sys

load_dotenv()

client_id = os.environ.get("NAVER_CLIENT_ID")
client_secret = os.environ.get("NAVER_CLIENT_SECRET")

def search_news(keyword):
    encText = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=10&sort=sim"
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            data = json.loads(response.read().decode('utf-8'))
            return data['items']
        return None
    except Exception as e:
        print("API 에러 발생:", e)
        return None

def fetch_naver_news_direct(naver_url):
    """네이버 뉴스(n.news.naver.com) 본문을 BeautifulSoup으로 직접 추출"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # 네이버 모바일/PC 뉴스 본문 태그 지정
            article_body = soup.select_one('#newsct_article') or soup.select_one('#articeBody') or soup.select_one('#dic_area')
            
            if article_body:
                # 불필요한 미디어 및 스크립트/스타일 태그 일괄 제거
                # video, audio, iframe 등의 태그와 그 내부 텍스트를 완전히 잘라냅니다.
                unwanted_tags = [
                    'script', 'style', 'span', 'div', 
                    'video', 'audio', 'iframe', 'figure', 'figcaption',
                    'button', 'form'
                ]
                for extra in article_body.find_all(unwanted_tags):
                    extra.extract()
                
                # 순수 텍스트 추출 및 정제
                content = article_body.get_text(separator=" ", strip=True)
                
                # 남아있을 수 있는 플레이어 관련 노이즈 문자열 최종 정제
                noise_phrases = [
                    "브라우저가 video 태그를 지원하지 않습니다.",
                    "죄송하지만 다른 브라우저를 사용하여 주십시오.",
                    "브라우저가 오디오 태그를 지원하지 않습니다.",
                    "닫기"
                ]
                for phrase in noise_phrases:
                    content = content.replace(phrase, "")

                return content.strip()
    except Exception:
        pass
    return ""

def get_news_content(item):
    """1차: 언론사 자사 사이트 크롤링 -> 2차: 네이버 뉴스 직접 크롤링"""
    original_url = item.get('originallink')
    naver_url = item.get('link')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 1. 언론사 원본 링크로 newspaper3k 시도
    if original_url:
        try:
            article = Article(original_url, language='ko', request_kwargs={'headers': headers})
            article.download()
            article.parse()
            
            # 수집 후 노이즈 정제 함수 실행
            content = clean_article_content(article.text)
            
            # 정제된 본문이 유의미하게 남았을 때만 반환
            if len(content) > 100:
                return content
        except Exception:
            pass

    # 2. 실패했거나 originallink가 없으면 네이버 뉴스 전용 수집기 작동
    if "news.naver.com" in naver_url:
        content = fetch_naver_news_direct(naver_url)
        content = clean_article_content(content)
        if len(content) > 50:
            return content

    return "본문을 가져오지 못했습니다."

def clean_article_content(content):
    """본문 내 동영상 플레이어 찌꺼기 및 흔한 노이즈 문구 제거"""
    if not content:
        return ""
        
    noise_phrases = [
        "브라우저가 video 태그를 지원하지 않습니다.",
        "죄송하지만 다른 브라우저를 사용하여 주십시오.",
        "브라우저가 오디오 태그를 지원하지 않습니다.",
        "기사 섹션 분류 안내",
        "언론사는 개별 기사를 2개 이상 섹션으로 중복 분류할 수 있습니다.",
        "닫기"
    ]
    
    for phrase in noise_phrases:
        content = content.replace(phrase, "")
        
    return content.strip()

def clean_text(text):
    """HTML 특수문자 및 태그 정제"""
    text = html.unescape(text)
    return text.replace("<b>", "").replace("</b>", "").strip()

if __name__ == "__main__":
    # 사용자가 터미널에서 원하는 키워드를 직접 입력하도록 변경
    target_keyword = input("🔍 검색할 뉴스 키워드를 입력하세요: ").strip()
    
    # 아무것도 입력하지 않았을 경우 대비 예외 처리
    if not target_keyword:
        print("⚠️ 검색어가 입력되지 않았습니다. 프로그램을 종료합니다.")
        sys.exit()
        
    print(f"\n[{target_keyword}] 관련 최신 뉴스를 가져옵니다...\n")
    
    news_items = search_news(target_keyword)
    
    if news_items:
        for idx, item in enumerate(news_items, 1):
            title = clean_text(item['title'])
            
            print(f"==================================================")
            print(f"{idx}. {title}")
            print(f"   언론사 링크: {item.get('originallink')}")
            print(f"   네이버 링크: {item.get('link')}")
            print(f"==================================================")
            print("⏳ 본문 수집 중...")
            
            content = get_news_content(item)
            
            print(f"📄 수집된 본문 전체 글자 수: {len(content)}자")
            print(f"📄 본문 내용 요약(앞 150자):\n{content[:150]}...")
            print(f"==================================================\n")