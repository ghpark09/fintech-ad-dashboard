# -*- coding: utf-8 -*-
"""데이터 로딩 · 메트릭 계산 레이어 (캐시 적용)."""
import glob
import os
import numpy as np
import pandas as pd
import streamlit as st

# 퍼널 단계 (순서 고정)
FUNNEL = ["광고노출", "광고클릭", "앱설치", "앱실행", "회원가입", "계좌개설", "첫거래", "반복사용"]
BASE = ["광고노출", "광고클릭", "광고비", "앱설치", "앱실행", "회원가입", "계좌개설", "첫거래", "반복사용"]

CHANNEL_ORDER = ["구글", "페이스북", "네이버검색"]


def _find_xlsx():
    here = os.path.dirname(__file__)
    for d in (here, os.path.join(here, "..")):
        hits = glob.glob(os.path.join(d, "*.xlsx"))
        if hits:
            return hits[0]
    raise FileNotFoundError("핀테크 데이터 xlsx를 찾을 수 없습니다.")


@st.cache_data(show_spinner="데이터 로딩 중…")
def load_data():
    df = pd.read_excel(_find_xlsx())
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    return df.sort_values("date").reset_index(drop=True)


def add_rates(g: pd.DataFrame) -> pd.DataFrame:
    """집계된 합계 프레임에 비율·단가 지표를 추가한다."""
    g = g.copy()
    safe = lambda a, b: np.where(b > 0, a / b, np.nan)
    g["CTR"] = safe(g["광고클릭"], g["광고노출"])
    g["CVR_설치"] = safe(g["앱설치"], g["광고클릭"])
    g["CVR_실행"] = safe(g["앱실행"], g["앱설치"])
    g["CVR_가입"] = safe(g["회원가입"], g["앱실행"])
    g["CVR_개설"] = safe(g["계좌개설"], g["회원가입"])
    g["CVR_첫거래"] = safe(g["첫거래"], g["계좌개설"])
    g["CVR_반복"] = safe(g["반복사용"], g["첫거래"])
    g["CPM"] = safe(g["광고비"], g["광고노출"]) * 1000
    g["CPC"] = safe(g["광고비"], g["광고클릭"])
    g["CPI"] = safe(g["광고비"], g["앱설치"])
    g["CPA_가입"] = safe(g["광고비"], g["회원가입"])
    g["CPA_개설"] = safe(g["광고비"], g["계좌개설"])
    g["CPA_첫거래"] = safe(g["광고비"], g["첫거래"])
    g["CPA_반복"] = safe(g["광고비"], g["반복사용"])
    return g


def agg(df: pd.DataFrame, by) -> pd.DataFrame:
    """by 기준 합계 + 비율 지표. by=None이면 전체 1행."""
    if by is None:
        g = df[BASE].sum().to_frame().T
    else:
        g = df.groupby(by, as_index=False)[BASE].sum()
    return add_rates(g)


def funnel_steps(df: pd.DataFrame) -> pd.DataFrame:
    """퍼널 단계별 절대값 + 단계 전환율 표."""
    tot = df[FUNNEL].sum()
    rows = []
    prev = None
    for s in FUNNEL:
        v = int(tot[s])
        conv = np.nan if prev is None else v / prev if prev else np.nan
        rows.append({"단계": s, "값": v, "직전대비_전환율": conv})
        prev = v
    return pd.DataFrame(rows)
