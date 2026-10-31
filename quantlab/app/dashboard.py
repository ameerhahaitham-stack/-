"""QuantLab dashboard (Streamlit).  Run:  streamlit run app/dashboard.py
It never opens HOLD: the sealed file is only shown as 'sealed' with its hash."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from quantlab import registry
from quantlab.charts import candlestick, trade_charts
from quantlab.config import root
from quantlab.data import load_manifest, load_with_context
from quantlab.replay import Replay

st.set_page_config(page_title="QuantLab", layout="wide")
R = root()
page = st.sidebar.radio("القسم", ["نظرة عامة", "جودة البيانات", "الشارت", "إعادة التشغيل", "السجل والتجارب", "نتائج الاستراتيجيات", "التقارير"])
st.sidebar.caption("HOLD مختوم ولا تفتحه هذه الواجهة.")


def manifest_keys():
    return sorted(load_manifest().keys())


def load_visible(key: str, stage: str) -> pd.DataFrame:
    sym, tf = key.split("_")
    df, es, ee, _ = load_with_context(sym, tf, stage)
    return df


if page == "نظرة عامة":
    st.title("QuantLab — مختبر البحث الكمي")
    ls = registry.lock_status()
    ok, msg = registry.verify_chain()
    c1, c2, c3 = st.columns(3)
    c1.metric("البروتوكول", "مقفل ✔" if ls.get("locked") and ls.get("intact") else ("معدَّل ✖" if ls.get("locked") else "غير مقفل"))
    c2.metric("سلامة السجل", "سليم" if ok else "مكسور")
    c3.metric("تجارب DEV+VALID", registry.trial_count(("dev", "valid")))
    m = load_manifest()
    if m:
        st.subheader("البيانات المستوردة")
        rows = [{"ملف": k, "المصدر": v["source"], "تجريبي(synthetic)": v["synthetic"], "فحص خام": v["raw_status"], "بعد التنظيف": v["clean_status"],
                 "DEV": v["splits"]["dev"]["rows"], "VALID": v["splits"]["valid"]["rows"], "HOLD (مختوم)": v["splits"]["hold"]["rows"]} for k, v in m.items()]
        st.dataframe(pd.DataFrame(rows), width="stretch")
        if any(v["synthetic"] for v in m.values()):
            st.warning("بيانات تجريبية صناعية: لاختبار الكود فقط وليست دليلاً بحثياً.")
    else:
        st.info("لا بيانات بعد. ضع ملفات التصدير في data/incoming ثم شغّل: python -m quantlab.cli ingest")

elif page == "جودة البيانات":
    st.title("جودة البيانات")
    rp = R / "reports" / "data_quality_report.md"
    if rp.exists():
        st.markdown(rp.read_text(encoding="utf-8"))
    else:
        st.info("شغّل: python -m quantlab.cli validate")

elif page == "الشارت":
    st.title("الشارت")
    keys = manifest_keys()
    if not keys:
        st.info("لا بيانات.")
    else:
        key = st.selectbox("الرمز_الإطار", keys)
        stage = st.selectbox("الفترة", ["dev", "valid"])
        df = load_visible(key, stage)
        d0, d1 = df["time"].min().date(), df["time"].max().date()
        rng = st.slider("المدى", min_value=d0, max_value=d1, value=(max(d0, d1 - pd.Timedelta(days=60)), d1))
        view = df[(df["time"].dt.date >= rng[0]) & (df["time"].dt.date <= rng[1])].tail(400)
        st.pyplot(candlestick(view, title=f"{key} ({stage})"))

elif page == "إعادة التشغيل":
    st.title("إعادة تشغيل حركة السعر (لا تظهر الشموع المستقبلية)")
    keys = manifest_keys()
    if not keys:
        st.info("لا بيانات.")
    else:
        key = st.selectbox("الرمز_الإطار", keys, key="rk")
        stage = st.selectbox("الفترة", ["dev", "valid"], key="rs")
        df = load_visible(key, stage)
        sk = f"replay_{key}_{stage}"
        if sk not in st.session_state:
            st.session_state[sk] = Replay(df, start=df["time"].iloc[min(300, len(df) - 1)], window=120)
        rp: Replay = st.session_state[sk]
        c = st.columns(5)
        speed = c[0].number_input("شموع لكل خطوة", 1, 200, rp.speed)
        rp.set_speed(int(speed))
        if c[1].button("◀ رجوع"):
            rp.back(rp.speed)
        if c[2].button("خطوة ▶"):
            rp.step()
        if c[3].button("قفزة ×10"):
            rp.step(rp.speed * 10)
        if c[4].button("إعادة"):
            rp.jump_to(df["time"].iloc[min(300, len(df) - 1)])
        st.caption(f"الآن: {rp.now}  |  الشموع الظاهرة فقط حتى هذه اللحظة")
        st.pyplot(rp.render())

elif page == "السجل والتجارب":
    st.title("سجل الفرضيات والتجارب")
    hy, th = registry.hypotheses_df(), registry.trials_df()
    st.subheader("الفرضيات")
    st.dataframe(hy if len(hy) else pd.DataFrame({"": ["لا فرضيات بعد"]}), width="stretch")
    st.subheader("كل التجارب (عدد التجارب هو أساس تصحيح تعدد الاختبارات)")
    st.dataframe(th.drop(columns=["params"]) if len(th) else pd.DataFrame({"": ["لا تجارب بعد"]}), width="stretch")

elif page == "نتائج الاستراتيجيات":
    st.title("نتائج الاستراتيجيات")
    files = sorted((R / "results").glob("*/*_summary.json"))
    if not files:
        st.info("لا نتائج بعد.")
    else:
        sel = st.selectbox("تجربة", [f"{f.parent.name}/{f.name}" for f in files])
        sp = R / "results" / sel
        js = json.loads(sp.read_text(encoding="utf-8"))
        s = js["summary"]
        st.write(f"**{js['hid']}** — {js['symbol']} {js['tf']} — {js['split'].upper()} — params: {js['params']}")
        keys = ["n_trades", "win_rate", "profit_factor_net", "expectancy_R_net", "expectancy_R_gross", "avg_win_R", "avg_loss_R",
                "max_drawdown_R", "max_losing_streak", "avg_cost_R", "p_raw", "p_adjusted", "p_vs_control"]
        st.dataframe(pd.DataFrame({k: [s.get(k)] for k in keys}).T.rename(columns={0: "القيمة"}))
        st.write("سيناريوهات التكلفة", pd.DataFrame(s["scenarios"]).T)
        tr_path = sp.with_name(sp.name.replace("_summary.json", "_trades.csv"))
        if tr_path.exists():
            tr = pd.read_csv(tr_path, parse_dates=["entry_time", "exit_time"])
            if len(tr):
                tr = tr.sort_values("exit_time")
                tr["cum_R"] = tr["net_R"].cumsum()
                tr["drawdown_R"] = tr["cum_R"].cummax().clip(lower=0) - tr["cum_R"]
                st.line_chart(tr.set_index("exit_time")[["cum_R"]])
                st.line_chart(tr.set_index("exit_time")[["drawdown_R"]])
                st.dataframe(tr)
                st.download_button("تنزيل سجل الصفقات CSV", tr.to_csv(index=False).encode(), file_name=tr_path.name)

elif page == "التقارير":
    st.title("التقارير")
    rd = R / "reports"
    for f in sorted(rd.glob("*.md")):
        with st.expander(f.name):
            st.markdown(f.read_text(encoding="utf-8"))
            st.download_button("تنزيل", f.read_bytes(), file_name=f.name, key=f.name)
    st.download_button("تقرير السجل", __import__("quantlab.report", fromlist=["x"]).registry_report_md().encode(), file_name="registry_report.md")
