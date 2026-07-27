import os
import json
import ollama

MODEL_NAME = "qwen2.5:7b"

def summarize_news_with_llm(title, content):
    """뉴스 단건에 대해 30초 요약본을 생성합니다."""
    short_content = content[:1500] if content else "본문 없음"
    
    prompt = f"""
다음 뉴스를 읽고 바쁜 직장인이 30초 만에 파악할 수 있도록 핵심을 정리해주세요.

- 기사 제목: {title}
- 기사 본문: {short_content}

[작성 양식]
1. 한 줄 요약: (기사의 가장 중요한 핵심을 1문장으로 정리)
2. 핵심 포인트:
   - (주요 내용 1)
   - (주요 내용 2)
   - (주요 내용 3)
3. 키워드: (#키워드1 #키워드2 #키워드3 형태)

위 양식을 엄격히 지켜서 한국어로 작성해주세요.
답변:"""

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ 개별 요약 호출 실패: {e}")
        return "요약 생성 실패"

def generate_overall_briefing(keyword, summarized_news_list):
    """개별 요약문들을 바탕으로 키워드 전체 종합 브리핑 리포트를 생성합니다."""
    # 개별 뉴스들의 핵심 요약만 끌어모아 종합 프롬프트 재료 생성
    combined_summaries = ""
    for idx, item in enumerate(summarized_news_list, 1):
        combined_summaries += f"\n[기사 {idx}] {item.get('title')}\n{item.get('summary')}\n"

    prompt = f"""
당신은 IT/경제 전문 뉴스 에널리스트입니다. 
오늘 수집된 '{keyword}' 관련 뉴스 개별 요약문들을 종합하여, 1분 만에 읽을 수 있는 [오늘의 종합 동향 브리핑]을 작성해주세요.

[개별 뉴스 요약 모음]
{combined_summaries}

[작성 양식]
1. 📊 오늘 한 줄 종합: (전체 기사들을 아우르는 오늘의 핵심 트렌드 1문장)
2. 💡 주요 이슈 TOP 3:
   - (가장 비중이 크거나 중요한 뉴스 흐름 1)
   - (두 번째 주요 뉴스 흐름 2)
   - (세 번째 주요 뉴스 흐름 3)
3. 🎯 한줄 인사이트: (이 키워드의 향후 전망이나 관전 포인트)

위 양식을 엄격히 지켜서 깔끔하고 명확한 한국어로 작성해주세요.
답변:"""

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3} # 종합 리포트의 자연스러운 문장 연결을 위해 0.3 설정
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ 종합 브리핑 생성 실패: {e}")
        return "종합 브리핑 생성 실패"

def run_summarizer(filtered_news_list, source_filename=None):
    """개별 요약 및 전체 종합 브리핑을 연달아 수행합니다."""
    if not filtered_news_list:
        print("❌ 요약할 뉴스 데이터가 없습니다.")
        return [], ""

    keyword = filtered_news_list[0].get('keyword', '뉴스')
    summarized_news = []
    
    print(f"\n📝 [{MODEL_NAME}] 1단계: 개별 뉴스 요약 시작 (총 {len(filtered_news_list)}건)...\n")

    for idx, item in enumerate(filtered_news_list, 1):
        title = item.get('title', '')
        content = item.get('content', '')
        
        print(f"[{idx}/{len(filtered_news_list)}] 요약 중: {title[:30]}...")
        
        summary_result = summarize_news_with_llm(title, content)
        item['summary'] = summary_result
        summarized_news.append(item)

    # 2단계: 전체 종합 브리핑 생성
    print(f"\n📊 [{MODEL_NAME}] 2단계: '{keyword}' 전체 종합 브리핑 생성 중...")
    overall_briefing = generate_overall_briefing(keyword, summarized_news)

    # 결과 데이터 구조화
    final_output = {
        "keyword": keyword,
        "total_count": len(summarized_news),
        "overall_briefing": overall_briefing,
        "articles": summarized_news
    }

    # 파일 저장 (summary_data/ 폴더)
    if source_filename:
        output_dir = "summary_data"
        os.makedirs(output_dir, exist_ok=True)

        base_name = source_filename.replace("_filtered.json", "").replace(".json", "")
        output_filename = f"{base_name}_summary.json"
        file_path = os.path.join(output_dir, output_filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=4)

        print(f"\n✅ 완성! 브리핑 리포트가 '{file_path}' 파일로 저장되었습니다.")

    return final_output