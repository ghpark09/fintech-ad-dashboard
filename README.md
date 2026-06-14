# 핀테크 앱 광고 성과 대시보드

디지털마케팅 기말과제 — 메트릭 하이어라키 기반 데이터 분석 + Streamlit 대시보드.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
# 브라우저: http://localhost:8501
```

데이터(`핀테크_테이터분석.xlsx`)는 상위 폴더 또는 같은 폴더에 두면 자동 인식됩니다.
Streamlit Cloud 배포 시 xlsx를 이 폴더로 복사하세요.

## 구성

| 파일 | 역할 |
|------|------|
| `streamlit_app.py` | 대시보드 본체 (6개 탭) |
| `metrics.py` | 데이터 로딩 · 퍼널/CPA 지표 계산 (캐시) |
| `insights.py` | 도출한 10개 인사이트 정의 |
| `.streamlit/config.toml` | 테마 |

## 탭

1. **Overview** — KPI 카드, 월별 광고비 vs CPA, 채널 비중
2. **Metric Hierarchy** — 퍼널 차트, 단계 전환율, CPA=CPM÷CTR÷전환율 분해, 차원별 병목 히트맵
3. **Channel Analysis** — 채널별 절대성과·효율, CPC vs 전환율 산점도
4. **Campaign Analysis** — 목적별 CPA 비교, 캠페인 상·하위, 광고비 vs 첫거래 산점도
5. **Ad Group & Creative** — 리타겟/논타겟, 이미지/영상/키워드, 소재 피로도, 네이버 브랜드KW 분리
6. **Insights** — 10개 인사이트(현상→근거→원인→액션) + 액션 플랜

## 분석 데이터 정확도

모든 수치는 원본 109,500행 **전수 집계(정확)**. 추정·보정 없음.
