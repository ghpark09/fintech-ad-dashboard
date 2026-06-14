# -*- coding: utf-8 -*-
"""핀테크 앱 광고 성과 대시보드 — 메트릭 하이어라키 분석.

탭: Overview · Metric Hierarchy · Channel · Campaign · Ad Group & Creative · Insights
실행: streamlit run dashboard/streamlit_app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from metrics import (BASE, CHANNEL_ORDER, FUNNEL, add_rates, agg, funnel_steps,
                     load_data)
from insights import INSIGHTS
import ui

st.set_page_config(page_title="핀테크 광고 성과 대시보드",
                   page_icon=":material/insights:", layout="wide")
ui.inject()

PALETTE = {"구글": "#4285F4", "페이스북": "#1877F2", "네이버검색": "#03C75A"}
ACCENT = "#4F46E5"
INDIGO_SEQ = ["#312E81", "#4338CA", "#6366F1", "#A5B4FC", "#C7D2FE"]
MONTH_LABELS = {m: f"{m}월" for m in range(1, 13)}

# ── 공통 헬퍼 ──────────────────────────────────────────────
def won(x, dec=0):
    if pd.isna(x):
        return "-"
    return f"{x:,.{dec}f}원"

def pct(x, dec=2):
    if pd.isna(x):
        return "-"
    return f"{x*100:.{dec}f}%"

def big(x):
    if pd.isna(x):
        return "-"
    x = float(x)
    if abs(x) >= 1e8:
        return f"{x/1e8:.2f}억"
    if abs(x) >= 1e4:
        return f"{x/1e4:.1f}만"
    return f"{x:,.0f}"

def style_money(df, cols):
    return df.style.format({c: "{:,.0f}" for c in cols})

def build_hierarchy_dot(t):
    """메트릭 하이어라키 분해 트리(DOT). 반복사용 = 첫거래 × CVR … 식으로 내려감."""
    # (하위단계, 상위단계, 전환율키)
    chain = [
        ("광고노출", "광고클릭", "CTR"),
        ("광고클릭", "앱설치", "CVR_설치"),
        ("앱설치", "앱실행", "CVR_실행"),
        ("앱실행", "회원가입", "CVR_가입"),
        ("회원가입", "계좌개설", "CVR_개설"),
        ("계좌개설", "첫거래", "CVR_첫거래"),
        ("첫거래", "반복사용", "CVR_반복"),
    ]
    cost = {"광고노출": ("CPM", "CPM"), "광고클릭": ("CPC", "CPC"), "앱설치": ("CPI", "CPI"),
            "회원가입": ("CPA 가입", "CPA_가입"), "계좌개설": ("CPA 개설", "CPA_개설"),
            "첫거래": ("CPA 첫거래", "CPA_첫거래"), "반복사용": ("CPA 반복", "CPA_반복")}
    stages = ["광고노출", "광고클릭", "앱설치", "앱실행", "회원가입", "계좌개설", "첫거래", "반복사용"]

    def vnode(s):
        if s == "반복사용":
            fc, ec = "#DCFCE7", "#10B981"; star = "⭐ "
        elif s == "첫거래":
            fc, ec = "#FEE2E2", "#EF4444"; star = "🔻 "
        else:
            fc, ec = "#EEF0FF", "#C7CCF7"; star = ""
        return (f'"v_{s}" [label="{star}{s}\\n{big(t[s])}", fillcolor="{fc}", '
                f'color="{ec}", penwidth=1.6];')

    lines = [
        'digraph G {', 'rankdir=LR; bgcolor="transparent"; nodesep=0.28; ranksep=0.7;',
        'node [shape=box, style="rounded,filled", fontname="Pretendard", fontsize=12, '
        'width=1.2, height=0.5, margin="0.1,0.05"];',
        'edge [fontname="Pretendard", fontsize=11, color="#B6BCE0", fontcolor="#4F46E5", penwidth=1.4];',
    ]
    for s in stages:
        lines.append(vnode(s))
    # 비용 노드
    for s, (lbl, key) in cost.items():
        lines.append(f'"c_{s}" [label="{lbl}\\n{won(t[key])}", fillcolor="#F3E8FF", '
                     f'color="#E2CFFB", fontsize=10];')
    # 전환 엣지 (× CVR)
    for lo, hi, rk in chain:
        lines.append(f'"v_{lo}" -> "v_{hi}" [label="× {pct(t[rk],1)}", penwidth=1.6];')
    # 비용 엣지 (÷ 비용, 같은 행 정렬)
    for s, (lbl, key) in cost.items():
        lines.append(f'{{ rank=same; "c_{s}"; "v_{s}"; }}')
        lines.append(f'"c_{s}" -> "v_{s}" [style=dashed, arrowhead=none, '
                     f'color="#D6C2F5", label="÷비용", fontcolor="#7C3AED"];')
    lines.append("}")
    return "\n".join(lines)

# ── 데이터 ────────────────────────────────────────────────
df = load_data()

# 사이드바 필터
st.sidebar.header(":material/tune: 필터")
months = sorted(df["month"].unique())
sel_months = st.sidebar.multiselect("월 선택", months, default=months,
                                     format_func=lambda m: f"{m}월")
sel_channels = st.sidebar.multiselect("채널", CHANNEL_ORDER, default=CHANNEL_ORDER)
st.sidebar.caption("네이버 브랜드KW는 소재 탭에서 항상 분리 분석 (CLAUDE.md 규칙)")

mask = df["month"].isin(sel_months or months) & df["channel"].isin(sel_channels or CHANNEL_ORDER)
d = df[mask].copy()
if d.empty:
    st.warning("선택된 데이터가 없습니다. 필터를 조정하세요.")
    st.stop()

ui.hero(
    "핀테크 앱 광고 성과 대시보드",
    "메트릭 하이어라키로 매출·전환의 원인을 단계적으로 추적하고, 채널·캠페인·소재까지 드릴다운합니다.",
    ["기간 2025.01 ~ 2025.12", "109,500행", "채널 3 · 캠페인 75",
     "퍼널: 노출→클릭→설치→실행→가입→개설→첫거래→반복사용"],
)

tabs = st.tabs([":material/dashboard: Overview",
                ":material/account_tree: Metric Hierarchy",
                ":material/hub: Channel",
                ":material/campaign: Campaign",
                ":material/category: Ad Group & Creative",
                ":material/lightbulb: Insights"])

# ════════════════════════════════════════════════════════
# 1. OVERVIEW
# ════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("핵심 지표 (KPI)")
    t = agg(d, None).iloc[0]
    c = st.columns(4)
    c[0].metric("총 광고비", f"{big(t['광고비'])}원")
    c[1].metric("총 노출", big(t["광고노출"]))
    c[2].metric("총 클릭", big(t["광고클릭"]))
    c[3].metric("CTR", pct(t["CTR"]))
    c = st.columns(4)
    c[0].metric("앱설치", big(t["앱설치"]))
    c[1].metric("회원가입", big(t["회원가입"]))
    c[2].metric("계좌개설", big(t["계좌개설"]))
    c[3].metric("첫거래", big(t["첫거래"]))
    c = st.columns(4)
    c[0].metric("반복사용", big(t["반복사용"]))
    c[1].metric("CPI (설치단가)", won(t["CPI"]))
    c[2].metric("CPA 회원가입", won(t["CPA_가입"]))
    c[3].metric("CPA 첫거래", won(t["CPA_첫거래"]))

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.markdown("**월별 추이 — 광고비 vs 회원가입 CPA**")
        m = agg(d, "month").sort_values("month")
        fig = go.Figure()
        fig.add_bar(x=m["month"].map(MONTH_LABELS), y=m["광고비"], name="광고비",
                    marker_color="#C7D2FE", yaxis="y1")
        fig.add_trace(go.Scatter(x=m["month"].map(MONTH_LABELS), y=m["CPA_가입"],
                                 name="CPA 회원가입", mode="lines+markers",
                                 line=dict(color=ACCENT, width=3), yaxis="y2"))
        fig.update_layout(
            yaxis=dict(title="광고비"), yaxis2=dict(title="CPA(원)", overlaying="y",
                                                  side="right", showgrid=False),
            legend=dict(orientation="h", y=1.15), height=380, margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")
        st.caption("분기말(3·9·12월) 예산 급증 시 CPA 동반 상승 → 한계효율 체감 (인사이트 #2)")

    with right:
        st.markdown("**채널별 광고비 비중**")
        cc = agg(d, "channel")
        cc["channel"] = pd.Categorical(cc["channel"], CHANNEL_ORDER, ordered=True)
        cc = cc.sort_values("channel")
        fig = px.pie(cc, names="channel", values="광고비", hole=0.5,
                     color="channel", color_discrete_map=PALETTE)
        fig.update_layout(height=380, margin=dict(t=10), legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, width="stretch")

    st.divider()
    st.markdown("**월별 상세 지표**")
    m = agg(d, "month").sort_values("month")
    show = m[["month", "광고비", "광고노출", "광고클릭", "앱설치", "회원가입",
              "계좌개설", "첫거래", "반복사용", "CTR", "CPA_가입", "CPA_첫거래"]].copy()
    show.columns = ["월", "광고비", "노출", "클릭", "설치", "가입", "개설", "첫거래",
                    "반복", "CTR", "CPA가입", "CPA첫거래"]
    st.dataframe(
        show.style.format({"광고비": "{:,.0f}", "노출": "{:,.0f}", "클릭": "{:,.0f}",
                           "설치": "{:,.0f}", "가입": "{:,.0f}", "개설": "{:,.0f}",
                           "첫거래": "{:,.0f}", "반복": "{:,.0f}", "CTR": "{:.2%}",
                           "CPA가입": "{:,.0f}", "CPA첫거래": "{:,.0f}"}),
        width="stretch", hide_index=True)

# ════════════════════════════════════════════════════════
# 2. METRIC HIERARCHY
# ════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("메트릭 하이어라키 — 지표 분해 트리")
    st.caption("최종 결과(반복사용)를 상위에 두고 **반복사용 = 첫거래 × CVR**, "
               "**첫거래 = 계좌개설 × CVR** … 식으로 단계별 원인 지표까지 분해합니다. "
               "왼쪽 보라색 = 비용 지표(÷비용), 화살표 라벨 = 전환율(×CVR).")
    t_all = agg(d, None).iloc[0]
    st.graphviz_chart(build_hierarchy_dot(t_all), use_container_width=True)
    cc = st.columns(3)
    cc[0].metric("최종 결과 · 반복사용", big(t_all["반복사용"]))
    cc[1].metric("🔻 최대 병목 · 첫거래/계좌개설", pct(t_all["CVR_첫거래"], 1))
    cc[2].metric("반복사용 1건당 비용 · CPA 반복", won(t_all["CPA_반복"]))

    st.divider()
    st.markdown("#### 퍼널 시각화 & 단계별 전환율")
    fs = funnel_steps(d)
    left, right = st.columns([3, 2])
    with left:
        fig = go.Figure(go.Funnel(
            y=fs["단계"], x=fs["값"], textinfo="value+percent previous",
            marker=dict(color=["#312E81", "#3730A3", "#4338CA", "#4F46E5",
                               "#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE"])))
        fig.update_layout(height=460, margin=dict(t=20))
        st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("**단계별 전환율**")
        ftab = fs.copy()
        ftab["전환율"] = ftab["직전대비_전환율"]
        ftab = ftab[["단계", "값", "전환율"]]
        st.dataframe(ftab.style.format({"값": "{:,.0f}", "전환율": "{:.1%}"}),
                     width="stretch", hide_index=True, height=330)
        # 노출→클릭(CTR)은 구조적으로 작으므로 병목 판정에서 제외, 클릭 이후 단계만 비교
        post = fs[fs["단계"].isin(FUNNEL[2:])].set_index("단계")["직전대비_전환율"]
        worst = post.idxmin()
        prev_step = FUNNEL[FUNNEL.index(worst) - 1]
        st.error(f"🔻 최대 병목: **{prev_step}→{worst}** 단계 "
                 f"({post.loc[worst]*100:.0f}% 전환)")

    st.divider()
    st.markdown("**CPA = CPM ÷ CTR ÷ 전환율 — 단가 분해 (월별)**")
    m = agg(d, "month").sort_values("month")
    ccol = st.columns(3)
    with ccol[0]:
        fig = px.line(m, x="month", y=["CPM"], markers=True,
                      color_discrete_sequence=[ACCENT])
        fig.update_layout(title="CPM (노출단가) ↑", height=280, showlegend=False,
                          xaxis_title="월", margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")
    with ccol[1]:
        fig = px.line(m, x="month", y=["CTR"], markers=True,
                      color_discrete_sequence=["#10B981"])
        fig.update_layout(title="CTR (거의 일정)", height=280, showlegend=False,
                          xaxis_title="월", margin=dict(t=40))
        fig.update_yaxes(range=[0, m["CTR"].max()*1.4])
        st.plotly_chart(fig, width="stretch")
    with ccol[2]:
        fig = px.line(m, x="month", y=["CPA_가입"], markers=True,
                      color_discrete_sequence=["#EF4444"])
        fig.update_layout(title="CPA 가입 ↑", height=280, showlegend=False,
                          xaxis_title="월", margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")
    st.info("CTR·전환율이 일정한데 CPA가 오른다 → 원인은 **CPM(경매단가) 상승**. "
            "소재 피로도가 아니라 매체 인플레이션 (인사이트 #1·#9)")

    st.divider()
    st.markdown("**차원별 병목 비교 — 단계 전환율 히트맵**")
    dim = st.radio("드릴다운 차원", ["channel", "campaign_objective", "ad_group",
                                  "creative_format"], horizontal=True,
                   format_func=lambda x: {"channel": "채널", "campaign_objective": "캠페인목적",
                                          "ad_group": "광고그룹", "creative_format": "소재"}[x])
    g = agg(d, dim)
    rate_cols = ["CTR", "CVR_설치", "CVR_실행", "CVR_가입", "CVR_개설", "CVR_첫거래", "CVR_반복"]
    hm = g.set_index(dim)[rate_cols]
    fig = px.imshow(hm, text_auto=".1%", aspect="auto", color_continuous_scale="Purples",
                    labels=dict(color="전환율"))
    fig.update_layout(height=80 + 55*len(hm), margin=dict(t=20))
    st.plotly_chart(fig, width="stretch")

# ════════════════════════════════════════════════════════
# 3. CHANNEL ANALYSIS
# ════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("채널 분석")
    c = agg(d, "channel")
    c["channel"] = pd.Categorical(c["channel"], CHANNEL_ORDER, ordered=True)
    c = c.sort_values("channel")

    cols = st.columns(3)
    metric_choice = cols[0].selectbox("막대 지표(절대값)",
        ["광고비", "회원가입", "계좌개설", "첫거래", "반복사용"], index=0)
    cpa_choice = cols[1].selectbox("효율 지표(단가)",
        ["CPA_가입", "CPA_첫거래", "CPA_반복", "CPC", "CPI"], index=1)
    cols[2].metric("최저 효율 채널",
                   c.sort_values("CPA_첫거래", ascending=False)["channel"].iloc[0])

    a, b = st.columns(2)
    with a:
        fig = px.bar(c, x="channel", y=metric_choice, color="channel",
                     color_discrete_map=PALETTE, text_auto=".2s")
        fig.update_layout(title=f"채널별 {metric_choice}", height=360, showlegend=False,
                          margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")
    with b:
        fig = px.bar(c, x="channel", y=cpa_choice, color="channel",
                     color_discrete_map=PALETTE, text_auto=",.0f")
        fig.update_layout(title=f"채널별 {cpa_choice} (낮을수록 효율↑)", height=360,
                          showlegend=False, margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")

    st.markdown("**채널 효율 지도 — 가로:클릭단가(CPC) ↔ 세로:설치전환율(CVR)**")
    mx, my = c["CPC"].mean(), c["CVR_설치"].mean()
    fig = px.scatter(c, x="CPC", y="CVR_설치", color="channel",
                     color_discrete_map=PALETTE, text="channel")
    fig.update_traces(textposition="top center", marker=dict(size=22, line=dict(width=2, color="white")))
    fig.add_vline(x=mx, line_dash="dot", line_color="#CBD5E1")
    fig.add_hline(y=my, line_dash="dot", line_color="#CBD5E1")
    fig.add_annotation(x=c["CPC"].min(), y=c["CVR_설치"].max(), xanchor="left",
                       text="✅ 효율적<br>저단가·고전환", showarrow=False,
                       font=dict(color="#10B981", size=11), align="left")
    fig.add_annotation(x=c["CPC"].max(), y=c["CVR_설치"].min(), xanchor="right",
                       text="⚠ 비효율<br>고단가·저전환", showarrow=False,
                       font=dict(color="#EF4444", size=11), align="right")
    fig.update_layout(height=400, margin=dict(t=20), showlegend=False,
                      xaxis_title="CPC (클릭단가, 원) →", yaxis_title="설치 전환율 ↑")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")
    st.caption("점선 = 채널 평균. 좌상단일수록 효율적 → 구글이 최효율, 네이버검색은 우하단(고단가·저전환). "
               "첫거래 CPA 기준 구글이 네이버의 약 3.6배 효율 (인사이트 #4).")

    st.divider()
    st.markdown("**채널별 월 추이 — CPA 첫거래**")
    cm = agg(d, ["channel", "month"]).sort_values("month")
    fig = px.line(cm, x="month", y="CPA_첫거래", color="channel", markers=True,
                  color_discrete_map=PALETTE)
    fig.update_layout(height=360, xaxis_title="월", margin=dict(t=20))
    st.plotly_chart(fig, width="stretch")

    st.markdown("**채널 지표 요약표**")
    show = c[["channel", "광고비", "광고클릭", "앱설치", "회원가입", "첫거래", "반복사용",
              "CTR", "CVR_설치", "CPC", "CPI", "CPA_가입", "CPA_첫거래"]].copy()
    st.dataframe(show.style.format({
        "광고비": "{:,.0f}", "광고클릭": "{:,.0f}", "앱설치": "{:,.0f}", "회원가입": "{:,.0f}",
        "첫거래": "{:,.0f}", "반복사용": "{:,.0f}", "CTR": "{:.2%}", "CVR_설치": "{:.1%}",
        "CPC": "{:,.0f}", "CPI": "{:,.0f}", "CPA_가입": "{:,.0f}", "CPA_첫거래": "{:,.0f}"}),
        width="stretch", hide_index=True)

# ════════════════════════════════════════════════════════
# 4. CAMPAIGN ANALYSIS
# ════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("캠페인 분석")
    st.markdown("**캠페인 목적별 성과 — 가입은 싸지만 첫거래는?**")
    o = agg(d, "campaign_objective")
    melt = o.melt(id_vars="campaign_objective",
                  value_vars=["CPA_가입", "CPA_개설", "CPA_첫거래", "CPA_반복"],
                  var_name="지표", value_name="단가")
    fig = px.bar(melt, x="지표", y="단가", color="campaign_objective", barmode="group",
                 text_auto=",.0f", color_discrete_sequence=["#4F46E5", "#F59E0B"])
    fig.update_layout(height=380, margin=dict(t=20), yaxis_title="CPA(원)",
                      legend_title="캠페인목적")
    st.plotly_chart(fig, width="stretch")
    st.info("'회원가입' 목적은 CPA_가입은 낮지만 하위 퍼널(첫거래·반복)에서 2~3배 비효율 → "
            "최적화 이벤트를 계좌개설/첫거래로 하향 권장 (인사이트 #8)")

    st.divider()
    st.markdown("**campaign_id별 효율 — 상·하위 (첫거래 30건 이상)**")
    cid = agg(d, ["campaign_id", "campaign_objective"])
    cid = cid[cid["첫거래"] >= 30].copy()
    n = st.slider("표시 개수", 5, 15, 8)
    worst = cid.sort_values("CPA_첫거래", ascending=False).head(n)
    best = cid.sort_values("CPA_첫거래").head(n)
    a, b = st.columns(2)
    with a:
        fig = px.bar(worst.sort_values("CPA_첫거래"), x="CPA_첫거래", y="campaign_id",
                     orientation="h", color_discrete_sequence=["#EF4444"], text_auto=",.0f")
        fig.update_layout(title="최고단가 캠페인(비효율)", height=360, margin=dict(t=40),
                          yaxis_title="")
        st.plotly_chart(fig, width="stretch")
    with b:
        fig = px.bar(best.sort_values("CPA_첫거래", ascending=False), x="CPA_첫거래",
                     y="campaign_id", orientation="h",
                     color_discrete_sequence=["#10B981"], text_auto=",.0f")
        fig.update_layout(title="최저단가 캠페인(효율)", height=360, margin=dict(t=40),
                          yaxis_title="")
        st.plotly_chart(fig, width="stretch")
    st.caption("하위는 대부분 네이버검색_회원가입 캠페인, 상위는 구글_계좌개설 캠페인에 집중.")

    st.markdown("**캠페인 목적별 첫거래 CPA 분포 (캠페인 75개)**")
    fig = px.box(cid, x="campaign_objective", y="CPA_첫거래", color="campaign_objective",
                 points="all", color_discrete_map={"회원가입": "#4F46E5", "계좌개설": "#F59E0B"},
                 labels={"campaign_objective": "캠페인 목적", "CPA_첫거래": "첫거래 CPA (원)"})
    fig.update_layout(height=400, margin=dict(t=20), showlegend=False)
    st.plotly_chart(fig, width="stretch")
    st.caption("각 점 = 캠페인 1개. '회원가입' 목적은 첫거래 CPA가 크게 높은 구간에 몰려 있고, "
               "'계좌개설' 목적은 낮은 구간에 분포 → 가입은 싸게 사도 첫거래까지 잘 안 내려감 (인사이트 #8).")

# ════════════════════════════════════════════════════════
# 5. AD GROUP & CREATIVE
# ════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("광고그룹 & 소재 분석")

    st.markdown("### 광고그룹 (리타겟 vs 논타겟)")
    ag = agg(d, "ad_group")
    a, b = st.columns(2)
    with a:
        fig = px.bar(ag, x="ad_group", y="CVR_설치", color="ad_group", text_auto=".1%",
                     color_discrete_sequence=["#4F46E5", "#94A3B8"])
        fig.update_layout(title="설치 전환율", height=320, showlegend=False, margin=dict(t=40))
        st.plotly_chart(fig, width="stretch")
    with b:
        agc = agg(d, ["channel", "ad_group"])
        fig = px.bar(agc, x="channel", y="CPA_가입", color="ad_group", barmode="group",
                     text_auto=",.0f", color_discrete_sequence=["#4F46E5", "#94A3B8"])
        fig.update_layout(title="채널×그룹 CPA 가입", height=320, margin=dict(t=40),
                          legend_title="그룹")
        st.plotly_chart(fig, width="stretch")
    st.info("리타겟이 전 채널에서 설치 전환 1.3배·CPA 우위. 논타겟은 상단 인지용으로 평가 (인사이트 #6)")

    st.divider()
    st.markdown("### 소재 분석")
    st.caption("디스플레이(이미지·영상, 구글·페북)와 검색(키워드, 네이버)은 CTR 규모가 10배 이상 달라 "
               "**각각 별도 축**으로 비교합니다. 같은 축에 두면 차이가 묻힘.")
    cf = agg(d, "creative_format")
    metric_opt = st.segmented_control(
        "비교 지표", ["CTR", "CVR_설치", "CPA_가입", "CPA_첫거래"], default="CTR",
        key="cf_metric")
    metric_opt = metric_opt or "CTR"
    is_rate = metric_opt in ("CTR", "CVR_설치")
    txt = ".2%" if is_rate else ",.0f"
    better = "높을수록 좋음 ↑" if is_rate else "낮을수록 좋음 ↓"

    def fmt_bar(sub, title, colors):
        sub = sub[sub["creative_format"].isin(colors)]
        if sub.empty:
            st.caption(f"{title}: 선택된 채널 데이터 없음")
            return
        order = sub.sort_values(metric_opt, ascending=is_rate)
        fig = px.bar(order, x="creative_format", y=metric_opt, color="creative_format",
                     text_auto=txt, color_discrete_map=colors)
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(title=f"{title} · {metric_opt}", height=330, showlegend=False,
                          xaxis_title="", margin=dict(t=46))
        st.plotly_chart(fig, width="stretch")

    a, b = st.columns(2)
    with a:
        fmt_bar(cf, "디스플레이 (이미지 vs 영상)",
                {"이미지": "#94A3B8", "영상": "#4F46E5"})
    with b:
        fmt_bar(cf, "검색 (브랜드 vs 일반 키워드)",
                {"브랜드키워드": "#10B981", "일반키워드": "#CBD5E1"})
    st.caption(f"선택 지표: **{metric_opt}** ({better}) · "
               "영상 > 이미지(인사이트 #7), 브랜드KW > 일반KW(인사이트 #5)는 지표를 바꿔도 유지됨.")

    st.markdown("**소재 피로도 점검 — 1월 대비 CTR 지수 (1월 = 100)**")
    cfm = d.groupby(["creative_format", "month"], as_index=False)[BASE].sum()
    cfm = add_rates(cfm).sort_values(["creative_format", "month"])
    cfm["CTR지수"] = cfm["CTR"] / cfm.groupby("creative_format")["CTR"].transform("first") * 100
    fig = px.line(cfm, x="month", y="CTR지수", color="creative_format", markers=True,
                  color_discrete_sequence=["#4F46E5", "#10B981", "#3B82F6", "#F59E0B"])
    fig.add_hline(y=100, line_dash="dash", line_color="#EF4444",
                  annotation_text="1월 기준(100)", annotation_position="top left")
    lo = max(90, np.floor(cfm["CTR지수"].min()) - 1)
    hi = min(110, np.ceil(cfm["CTR지수"].max()) + 1)
    fig.update_layout(height=360, xaxis_title="월", yaxis_title="CTR 지수 (1월=100)")
    fig.update_yaxes(range=[lo, hi], dtick=1)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"각 소재의 1월 CTR을 100으로 환산(축 {lo:.0f}~{hi:.0f}, 1단위). "
               "월별 등락이 ±2% 이내로 작고 추세적 하락이 없음 → 피로도에 의한 CTR 저하는 "
               "관측되지 않음. 단가 상승은 소재보다 CPM 요인으로 추정 (인사이트 #9).")

    st.markdown("**네이버 브랜드KW vs 일반KW 상세 (분리)**")
    nv = agg(d[d["channel"] == "네이버검색"], "creative_format")
    if not nv.empty:
        show = nv[["creative_format", "광고비", "광고클릭", "회원가입", "첫거래",
                   "CTR", "CVR_설치", "CPA_가입", "CPA_첫거래"]]
        st.dataframe(show.style.format({
            "광고비": "{:,.0f}", "광고클릭": "{:,.0f}", "회원가입": "{:,.0f}", "첫거래": "{:,.0f}",
            "CTR": "{:.2%}", "CVR_설치": "{:.1%}", "CPA_가입": "{:,.0f}", "CPA_첫거래": "{:,.0f}"}),
            width="stretch", hide_index=True)
        st.caption("브랜드KW가 일반KW보다 CPA 약 30% 효율적 (인사이트 #5) · CLAUDE.md 규칙: 네이버 브랜드KW는 항상 분리")
    else:
        st.caption("네이버검색이 필터에서 제외되어 표시할 데이터가 없습니다.")

# ════════════════════════════════════════════════════════
# 6. INSIGHTS
# ════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("💡 핵심 인사이트 10선")
    st.caption("각 인사이트 = 현상 → 근거 데이터 → 원인 해석(메트릭 하이어라키) → 추천 액션")
    all_tags = sorted({i["tag"] for i in INSIGHTS})
    c1, c2 = st.columns([3, 2])
    pick = c1.multiselect("주제 필터", all_tags, default=all_tags)
    only_high = c2.toggle("🔴 High 우선순위만 보기", value=False)
    n_high = sum(1 for i in INSIGHTS if i["priority"] == "High")
    st.caption(f"좌측 컬러 바 = 중요도(🔴 High {n_high}개 · 🟡 Medium {10-n_high}개), "
               "칩 = 분석 주제. High부터 정렬됩니다.")
    items = [i for i in INSIGHTS if i["tag"] in pick
             and (not only_high or i["priority"] == "High")]
    items = sorted(items, key=lambda i: (i["priority"] != "High", i["no"]))
    if items:
        ui.insight_cards(items)
    else:
        st.caption("선택된 주제의 인사이트가 없습니다.")

    st.divider()
    st.markdown("#### 요약 — 한 장의 액션 플랜")
    st.caption("표현은 단정 대신 '검토/추정' 기준. 수치는 전수 집계(정확).")
    st.markdown("""
| 우선순위 | 액션 | 근거 인사이트 | 기대효과 | 주의점 |
|---|---|---|---|---|
| 🔴 1 | 계좌개설→첫거래 온보딩 강화 | #3 | 최대 병목(약 51%) 개선, 반복사용과 직결 | 리워드 비용 관리, 어뷰징 방지 |
| 🔴 2 | 예산 구글>페북>네이버 재배분 | #4·#10 | 첫거래 CPA 효율 격차(약 3.6배) 회수 | 네이버 브랜드 방어 트래픽은 유지 |
| 🔴 3 | 캠페인 최적화 이벤트를 첫거래로 하향 | #8 | 가입 편중 완화, 실수익 행동 증대 | 학습 데이터 충분 확보까지 단가 변동 |
| 🟡 4 | 리타겟·영상 비중 확대 | #6·#7 | 설치 전환 약 1.3배, 퍼널 전반 효율↑ | 리타겟 풀 소진·영상 제작비 고려 |
| 🟡 5 | 분기말 예산 평탄화 + 입찰 자동화 | #1·#2·#9 | 한계효율·CPM 상승 방어 | 분기 KPI 일정과의 조율 필요 |
""")
