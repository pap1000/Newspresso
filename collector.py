import os
import urllib.request
import json
import html
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article

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

def clean_article_content(content):
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

def fetch_naver_news_direct(naver_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(naver_url, headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            article_body = soup.select_one('#newsct_article') or soup.select_one('#articeBody') or soup.select_one('#dic_area')
            
            if article_body:
                unwanted_tags = [
                    'script', 'style', 'span', 'div', 
                    'video', 'audio', 'iframe', 'figure', 'figcaption',
                    'button', 'form'
                ]
                for extra in article_body.find_all(unwanted_tags):
                    extra.extract()
                
                content = article_body.get_text(separator=" ", strip=True)
                return clean_article_content(content)
    except Exception:
        pass
    return ""

def get_news_content(item):
    original_url = item.get('originallink')
    naver_url = item.get('link')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    if original_url:
        try:
            article = Article(original_url, language='ko', request_kwargs={'headers': headers})
            article.download()
            article.parse()
            content = clean_article_content(article.text)
            
            if len(content) > 100:
                return content
        except Exception:
            pass

    if "news.naver.com" in naver_url:
        content = fetch_naver_news_direct(naver_url)
        if len(content) > 50:
            return content

    return "본문을 가져오지 못했습니다."

def clean_text(text):
    text = html.unescape(text)
    return text.replace("<b>", "").replace("</b>", "").strip()

def collect_news(target_keyword):
    """뉴스 검색 및 본문 수집 파이프라인 (메인 연동용)"""
    print(f"\n📡 [{target_keyword}] 관련 최신 뉴스를 가져옵니다...\n")
    
    news_items = search_news(target_keyword)
    
    if not news_items:
        print("❌ 수집된 뉴스가 없습니다.")
        return [], None

    collected_data = []

    for idx, item in enumerate(news_items, 1):
        title = clean_text(item['title'])
        origin_link = item.get('originallink')
        naver_link = item.get('link')
        pub_date = item.get('pubDate', '')
        
        print(f"==================================================")
        print(f"{idx}. {title}")
        print(f"   언론사 링크: {origin_link}")
        print(f"   네이버 링크: {naver_link}")
        print(f"==================================================")
        print("⏳ 본문 수집 중...")
        
        content = get_news_content(item)
        print(f"📄 수집된 본문 전체 글자 수: {len(content)}자")
        print(f"==================================================\n")

        news_entry = {
            "id": idx,
            "keyword": target_keyword,
            "title": title,
            "origin_link": origin_link,
            "naver_link": naver_link,
            "pub_date": pub_date,
            "content": content,
            "content_length": len(content)
        }
        collected_data.append(news_entry)

    # 원본 수집 JSON 저장
    filename = None
    if collected_data:
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)  # data 폴더가 없으면 자동 생성

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"news_{target_keyword}_{timestamp}.json"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(collected_data, f, ensure_ascii=False, indent=4)

        print(f"✅ 원본 수집 완료: 총 {len(collected_data)}건 데이터 저장 ({file_path})")

    return collected_data, filename