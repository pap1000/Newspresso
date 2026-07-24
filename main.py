import sys
from collector import collect_news
from llm_filter import run_llm_filter

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 뉴스 수집 & 맥락 필터링 에이전트 파이프라인")
    print("=" * 50)
    
    target_keyword = input("\n🔍 검색할 뉴스 키워드를 입력하세요: ").strip()
    
    if not target_keyword:
        print("⚠️ 검색어가 입력되지 않았습니다. 프로그램을 종료합니다.")
        sys.exit()
        
    # 1단계: 뉴스 검색 및 본문 수집
    news_list, saved_filename = collect_news(target_keyword)
    
    # 2단계: 수집된 데이터에 대해 즉시 로컬 LLM 필터링 수행
    if news_list:
        final_news = run_llm_filter(news_list, saved_filename)
        print(f"\n🎉 전체 작업 완료! 최종 {len(final_news)}건의 알짜 뉴스가 가려졌습니다.")