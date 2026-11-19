import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="HS300 Quant", layout="wide", page_icon="◈")

RISK = {
    "max_single_weight": 0.03,
    "daily_loss_limit": -0.008,
    "weekly_drawdown_limit": -0.03,
    "if_basis_warn": 0.08,
    "max_hedge_ratio": 0.80,
}
COMPLIANCE = {"reported": True}

@st.cache_data
def get_mock_data():
    np.random.seed(42)
    codes = [f"6000{i:02d}" for i in range(20)]
    names = [f"成分股{i}" for i in range(1, 21)]
    data = {
        "code": codes,
        "name": names,
        "score": np.random.uniform(0.3, 0.95, 20),
        "mom_5": np.random.uniform(-0.05, 0.08, 20),
        "mom_20": np.random.uniform(-0.1, 0.15, 20),
        "vol_ratio": np.random.uniform(0.8, 2.0, 20),
        "weight": np.random.uniform(0.01, 0.04, 20)
    }
    df = pd.DataFrame(data)
    df["direction"] = np.where(df["score"] > 0.7, "LONG", np.where(df["score"] < 0.3, "SHORT", "FLAT"))
    return df.sort_values("score", ascending=False)

st.title("◈ HS300 Quant — 沪深300 风控前置执行台")
st.caption("云端体验版 ｜ 风控：强拦截 ｜ 执行：模拟占位")

capital = 1_000_000
daily_pnl_pct = -0.002
weekly_dd_pct = -0.015
hedge_ratio = 0.5
if_basis_annual = 0.065

top = st.columns([2, 2, 2, 3, 2])
top[0].metric("组合净值", f"¥{capital:,.0f}")
top[1].metric("当日盈亏", f"{daily_pnl_pct:+.2%}")
top[2].metric("周回撤", f"{weekly_dd_pct:+.2%}")
basis_color = "🟢" if abs(if_basis_annual) < 0.04 else ("🟡" if abs(if_basis_annual) < RISK["if_basis_warn"] else "🔴")
top[3].metric("IF 年化基差", f"{basis_color} {if_basis_annual:+.2%}")
top[4].metric("合规状态", "✓ 已报备" if COMPLIANCE["reported"] else "✗ 未报备")

st.divider()

signals = get_mock_data()

left, mid, right = st.columns([3, 2, 2])

with left:
    st.subheader("信号热力（前20）")
    show = signals.copy()
    show["score"] = show["score"].round(3)
    show["mom_5"] = show["mom_5"].map("{:+.2%}".format)
    show["mom_20"] = show["mom_20"].map("{:+.2%}".format)
    show["vol_ratio"] = show["vol_ratio"].round(2)
    st.dataframe(show[["code", "name", "score", "mom_5", "mom_20", "direction"]], hide_index=True, height=400)

with mid:
    st.subheader("对冲面板")
    new_ratio = st.slider("IF 对冲比例", 0.0, 1.0, hedge_ratio, 0.05)
    preview_cost = abs(if_basis_annual) * new_ratio
    st.metric("预估年化基差拖累", f"{preview_cost:.2%}")
    if abs(if_basis_annual) > RISK["if_basis_warn"]:
        st.warning(f"基差成本偏高：建议降低对冲比例或暂缓新增对冲。")

with right:
    st.subheader("风控仪表盘")
    st.progress(min(abs(daily_pnl_pct) / abs(RISK["daily_loss_limit"]), 1.0), text="日亏损使用率")
    st.progress(min(abs(weekly_dd_pct) / abs(RISK["weekly_drawdown_limit"]), 1.0), text="周回撤使用率")
    st.progress(min(signals["weight"].max() / RISK["max_single_weight"], 1.0), text="单票最大权重")

st.divider()
st.subheader("待执行篮子")
candidates = signals[signals["direction"] == "LONG"].head(10)
if candidates.empty:
    st.info("当前无 LONG 信号。")
else:
    st.dataframe(candidates[["code", "name", "score"]], hide_index=True)
    if st.button("确认执行（模拟）", type="primary"):
        st.success("已模拟提交订单！")
