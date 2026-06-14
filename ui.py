# -*- coding: utf-8 -*-
"""프리미엄 UI 레이어 — Pretendard 폰트, 카드/히어로 스타일, 통일된 Plotly 테마."""
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

INK = "#1B1F2A"
MUTED = "#667085"
GRID = "#EDEFF5"
ACCENT = "#4F46E5"
CATEGORICAL = ["#4F46E5", "#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#8B5CF6", "#64748B"]

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

html, body, [class*="css"], [data-testid="stAppViewContainer"],
[data-testid="stMarkdownContainer"], .stMarkdown, button, input, select, textarea {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

.block-container { padding-top: 2.6rem; padding-bottom: 3rem; max-width: 1520px; }

/* ── Hero ── */
.hero {
  background: linear-gradient(120deg, #4F46E5 0%, #6D5BF2 45%, #7C3AED 100%);
  border-radius: 20px; padding: 26px 32px; color: #fff;
  box-shadow: 0 12px 30px -12px rgba(79,70,229,.55); margin-bottom: 6px;
}
.hero h1 { color:#fff; font-size: 27px; font-weight: 700; margin:0 0 6px 0; letter-spacing:-.4px; }
.hero p { color: rgba(255,255,255,.82); font-size: 13.5px; margin:0; line-height:1.5; }
.hero .chips { margin-top:14px; display:flex; gap:8px; flex-wrap:wrap; }
.hero .chip {
  background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.22);
  border-radius: 999px; padding: 4px 12px; font-size: 12px; font-weight:500; backdrop-filter: blur(4px);
}

/* ── KPI metric cards ── */
[data-testid="stMetric"] {
  background:#fff; border:1px solid #E9EBF2; border-radius:16px;
  padding:16px 18px 14px; box-shadow:0 1px 2px rgba(16,24,40,.05);
  transition: transform .16s ease, box-shadow .16s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow:0 10px 24px -14px rgba(16,24,40,.35); }
[data-testid="stMetricLabel"] { color:#667085; font-weight:600; font-size:12.5px; }
[data-testid="stMetricValue"] { font-weight:700; letter-spacing:-.5px; color:#101828; }

/* ── Tabs ── */
[data-baseweb="tab-list"] { gap: 4px; border-bottom:1px solid #ECEEF4; }
[data-baseweb="tab"] { font-weight:600; font-size:14px; padding: 9px 14px; border-radius:10px 10px 0 0; color:#667085; }
[data-baseweb="tab"][aria-selected="true"] { color:#4F46E5; }
[data-baseweb="tab-highlight"] { background-color:#4F46E5; height:3px; border-radius:3px; }

/* ── Expander (insight cards) ── */
[data-testid="stExpander"] {
  border:1px solid #E9EBF2 !important; border-radius:14px !important;
  box-shadow:0 1px 2px rgba(16,24,40,.04); overflow:hidden; margin-bottom:6px;
}
[data-testid="stExpander"] summary { font-weight:600; font-size:14.5px; padding:14px 16px; }
[data-testid="stExpander"] summary:hover { color:#4F46E5; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; border:1px solid #E9EBF2; }

/* ── Callouts a touch softer ── */
[data-testid="stAlert"] { border-radius:12px; }

/* ── Section labels (markdown bold above charts) ── */
.block-container [data-testid="stMarkdownContainer"] p strong { color:#101828; }

/* ── Sidebar polish ── */
[data-testid="stSidebar"] [data-testid="stMultiSelect"] span { font-size:13px; }
section[data-testid="stSidebar"] { box-shadow: 1px 0 0 #ECEEF4; }

/* ── Insight cards ── */
.ins-wrap { display:flex; flex-direction:column; gap:14px; }
.ins-card { background:#fff; border:1px solid #E9EBF2; border-radius:16px;
  padding:16px 18px; box-shadow:0 1px 3px rgba(16,24,40,.05); transition:box-shadow .16s ease; }
.ins-card:hover { box-shadow:0 12px 28px -16px rgba(16,24,40,.4); }
.ins-head { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.ins-prio { font-size:10.5px; font-weight:800; padding:3px 10px; border-radius:999px; letter-spacing:.5px; }
.ins-tag { font-size:11px; font-weight:700; padding:3px 10px; border-radius:999px; }
.ins-no { font-size:13px; font-weight:800; color:#CBD5E1; }
.ins-title { font-size:15.5px; font-weight:700; color:#101828; flex:1; min-width:200px; }
.ins-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:10px; }
.ins-cell { background:#F8F9FD; border-radius:12px; padding:11px 13px; font-size:12.5px;
  color:#475467; line-height:1.55; display:flex; flex-direction:column; gap:5px; }
.ins-k { font-size:10px; font-weight:800; color:#98A2B3; letter-spacing:.5px; }
.ins-act { background:#ECFDF3; border:1px solid #D1FADF; border-radius:12px; padding:11px 13px;
  font-size:12.5px; color:#05603A; line-height:1.6; }
.ins-actk { font-weight:800; color:#039855; margin-right:6px; }
@media (max-width:900px){ .ins-grid{ grid-template-columns:1fr; } }
</style>
"""


def _register_plotly_template():
    pio.templates["fintech"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Pretendard, sans-serif", color=INK, size=13),
            colorway=CATEGORICAL,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            barcornerradius=6,
            bargap=0.34,
            margin=dict(t=42, r=14, b=8, l=8),
            xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID,
                       tickfont=dict(color=MUTED), title_font=dict(color=MUTED, size=12)),
            yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID,
                       tickfont=dict(color=MUTED), title_font=dict(color=MUTED, size=12)),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12, color=MUTED)),
            title=dict(font=dict(size=15, color=INK, weight=600), x=0.01, xanchor="left"),
            hoverlabel=dict(bgcolor="white", bordercolor="#E9EBF2",
                            font=dict(family="Pretendard", color=INK, size=12)),
            colorscale=dict(sequential=[
                [0, "#EEF0FF"], [0.5, "#838DF1"], [1, "#322B96"]]),
        )
    )
    pio.templates.default = "fintech"


def inject():
    """앱 최상단에서 1회 호출 — CSS + Plotly 테마 적용."""
    st.html(_CSS)
    _register_plotly_template()


def hero(title: str, subtitle: str, chips: list[str]):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.html(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p>'
        f'<div class="chips">{chip_html}</div></div>'
    )


TAG_COLORS = {"시간": "#3B82F6", "퍼널": "#EF4444", "채널": "#10B981",
              "그룹": "#8B5CF6", "소재": "#F59E0B", "캠페인": "#EC4899"}


def insight_cards(items: list[dict]):
    """인사이트를 컬러 카드(중요도 좌측 바 + 카테고리 칩 + 3열 근거 + 액션)로 렌더."""
    cards = []
    for ins in items:
        pc = "#EF4444" if ins["priority"] == "High" else "#F59E0B"
        tc = TAG_COLORS.get(ins["tag"], "#64748B")
        cards.append(
            f'<div class="ins-card" style="border-left:5px solid {pc}">'
            f'<div class="ins-head">'
            f'<span class="ins-prio" style="background:{pc}1A;color:{pc}">{ins["priority"].upper()}</span>'
            f'<span class="ins-tag" style="background:{tc}1A;color:{tc}">{ins["tag"]}</span>'
            f'<span class="ins-no">#{ins["no"]}</span>'
            f'<span class="ins-title">{ins["title"]}</span></div>'
            f'<div class="ins-grid">'
            f'<div class="ins-cell"><span class="ins-k">🔎 발견된 현상</span><span>{ins["phenomenon"]}</span></div>'
            f'<div class="ins-cell"><span class="ins-k">📊 근거 데이터</span><span>{ins["evidence"]}</span></div>'
            f'<div class="ins-cell"><span class="ins-k">🧠 원인 해석</span><span>{ins["cause"]}</span></div>'
            f'</div>'
            f'<div class="ins-act"><span class="ins-actk">✅ 추천 액션</span>{ins["action"]}</div>'
            f'</div>'
        )
    st.html('<div class="ins-wrap">' + "".join(cards) + "</div>")
