import json
import glob
import os
import ollama

MODEL_NAME = "qwen2.5:7b"

def get_latest_news_file():
    """가장 최근에 저장된 news_*.json 파일 경로를 찾습니다."""
    files = glob.glob("data/news_*.json")
    
    if not files:
        return None
    
    # 생성 시간 기준 가장 최근 파일 반환
    return max(files, key=os.path.getmtime)

def filter_news_with_llm(keyword, title, content):
    """LLM을 호출하여 뉴스가 키워드의 실제 맥락에 맞는지 YES/NO로 판단합니다."""
    # 본문이 너무 길면 LLM 처리 속도가 느려지므로 앞 800자만 전달
    short_content = content[:800] if content else "본문 없음"
    
    prompt = f"""
다음 뉴스가 지정된 검색 키워드의 실제 주제/맥락과 부합하는 알짜 뉴스인지 판단해주세요.

- 검색 키워드: {keyword}
- 기사 제목: {title}
- 기사 본문 요약: {short_content}

[판단 기준]
1. 단순히 키워드 단어만 포함되어 있고 전혀 다른 주제(예: 동음이의어, 단순 광고)라면 NO입니다.
2. 키워드의 핵심 기술, 시장 동향, 주요 발표와 직접 관련된 뉴스라면 YES입니다.

응답은 다른 설명 없이 반드시 "YES" 또는 "NO" 단 하나로만 답변하세요.
답변:"""

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0} # 환각 최소화, 일관된 답변 도출
        )
        
        result = response['message']['content'].strip().upper()
        # "YES" 문구가 들어가 있으면 참으로 판단
        return "YES" in result
    except Exception as e:
        print(f"⚠️ LLM 호출 실패: {e}")
        return True # 오류 발생 시 일단 안전하게 유지

def main():
    json_file = get_latest_news_file()
    
    if not json_file:
        print("❌ 분석할 news_*.json 파일이 없습니다. main.py를 먼저 실행해 주세요!")
        return

    print(f"📂 최신 뉴스 데이터 파일 읽는 중: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        news_list = json.load(f)

    filtered_news = []
    print(f"🤖 [{MODEL_NAME}] 로컬 LLM 필터링 시작 (총 {len(news_list)}건)...\n")

    for idx, item in enumerate(news_list, 1):
        keyword = item.get('keyword', '')
        title = item.get('title', '')
        content = item.get('content', '')
        
        print(f"[{idx}/{len(news_list)}] 검사 중: {title[:30]}...")
        
        # LLM 의미론적 필터링 판별
        is_relevant = filter_news_with_llm(keyword, title, content)
        
        if is_relevant:
            print("   👉 [합격] 주제에 부합하는 뉴스입니다.")
            item['llm_filtered'] = True
            filtered_news.append(item)
        else:
            print("   👉 [탈락] 관련도가 떨어지는 노이즈 뉴스입니다.")
            item['llm_filtered'] = False

    print(f"\n==================================================")
    print(f"📊 필터링 결과: 총 {len(news_list)}건 중 {len(filtered_news)}건 채택!")
    print(f"==================================================")

    # 필터링 결과 저장
    output_filename = json_file.replace(".json", "_filtered.json")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(filtered_news, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 살아남은 알짜 뉴스가 '{output_filename}' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main()