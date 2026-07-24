import json
import os
import ollama

MODEL_NAME = "qwen2.5:7b"

def filter_news_with_llm(keyword, title, content):
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
            options={"temperature": 0.0}
        )
        
        result = response['message']['content'].strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"⚠️ LLM 호출 실패: {e}")
        return True

def run_llm_filter(news_list, source_filename=None):
    """수집된 뉴스 리스트를 받아 LLM 의미론적 필터링을 실행합니다."""
    if not news_list:
        print("❌ 필터링할 뉴스 데이터가 없습니다.")
        return []

    filtered_news = []
    print(f"\n🤖 [{MODEL_NAME}] 로컬 LLM 필터링 시작 (총 {len(news_list)}건)...\n")

    for idx, item in enumerate(news_list, 1):
        keyword = item.get('keyword', '')
        title = item.get('title', '')
        content = item.get('content', '')
        
        print(f"[{idx}/{len(news_list)}] 검사 중: {title[:30]}...")
        
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

    # 필터링 결과 파일 저장
    if source_filename:
        output_dir = "filtered_data"
        os.makedirs(output_dir, exist_ok=True)  # filtered_data 폴더가 없으면 자동 생성

        output_filename = source_filename.replace(".json", "_filtered.json")
        file_path = os.path.join(output_dir, output_filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_news, f, ensure_ascii=False, indent=4)

        print(f"✅ 필터링 완료: 살아남은 알짜 뉴스가 '{file_path}' 파일로 저장되었습니다.")

    return filtered_news