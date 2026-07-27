import sys
from collector import collect_news
from llm_filter import run_llm_filter
from summarizer import run_summarizer

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 뉴스 수집, 맥락 필터링 & AI 종합 브리핑 에이전트")
    print("=" * 50)
    
    target_keyword = input("\n🔍 검색할 뉴스 키워드를 입력하세요: ").strip()
    
    if not target_keyword:
        print("⚠️ 검색어가 입력되지 않았습니다. 프로그램을 종료합니다.")
        sys.exit()
        
    # 1단계: 뉴스 검색 및 본문 수집
    news_list, raw_filename = collect_news(target_keyword)
    
    # 2단계: 수집된 데이터에 대해 로컬 LLM 맥락 필터링 수행
    if news_list:
        filtered_news = run_llm_filter(news_list, raw_filename)
        
        # 3단계: 알짜 뉴스 개별 요약 + 전체 종합 브리핑 생성
        if filtered_news:
            result_data = run_summarizer(filtered_news, raw_filename)
            
            # 터미널에 종합 브리핑 리포트 출력
            print("\n" + "=" * 50)
            print(f"📌 [{target_keyword}] 오늘 뉴스 종합 브리핑 리포트")
            print("=" * 50)
            print(result_data.get('overall_briefing', ''))
            print("=" * 50)
            print(f"\n🎉 전체 파이프라인 완료! (개별 기사 요약 {result_data.get('total_count')}건 수록)")
        else:
            print("\n⚠️ 필터링을 통과한 알짜 뉴스가 없어 요약을 진행하지 않습니다.")