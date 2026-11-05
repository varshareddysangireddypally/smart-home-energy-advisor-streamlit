"""
app.py — Streamlit Dashboard
─────────────────────────────
Smart Home Energy Advisor Agent
IBM Cloud Lite + IBM Granite AI (ibm/granite-4-h-small)

Run with:  streamlit run app.py
"""

import os
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from data.smart_meter import SmartMeterSimulator
from tools.energy_analyzer import EnergyAnalyzer
from agent.granite_client import GraniteClient
from agent.prompt_builder import PromptBuilder
from agent.advisor_agent import INTENT_TOOL_MAP, KEYWORD_INTENT_MAP

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Home Energy Advisor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 10px;
    }
    .chat-user {
        background: #e8f0fe;
        border-radius: 12px 12px 4px 12px;
        padding: 10px 14px;
        margin: 6px 0;
        text-align: right;
    }
    .chat-ai {
        background: #f1f8f1;
        border-radius: 12px 12px 12px 4px;
        padding: 10px 14px;
        margin: 6px 0;
        border-left: 3px solid #22c55e;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 8px;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# ── Cached resources ──────────────────────────────────────────

@st.cache_resource
def get_granite_client():
    return GraniteClient()

@st.cache_resource
def get_prompt_builder():
    return PromptBuilder()

@st.cache_data(ttl=60)
def get_snapshot(rate, peak_mult, offpeak_mult, peak_start, peak_end, history_days):
    sim = SmartMeterSimulator(
        rate=rate,
        peak_multiplier=peak_mult,
        off_peak_multiplier=offpeak_mult,
        peak_start=peak_start,
        peak_end=peak_end,
        history_days=history_days,
    )
    return sim.get_snapshot()


# ── Session state init ────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []   # [{role, content}]
if "history" not in st.session_state:
    st.session_state.history = []    # for Granite context


# ── Sidebar — Configuration ───────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.title("⚡ Energy Advisor")
    st.caption("IBM Granite AI · IBM Cloud Lite")
    st.divider()

    st.subheader("⚙️ Settings")
    rate          = st.number_input("Rate ($/kWh)",        value=float(os.getenv("ENERGY_RATE_PER_KWH", "0.12")), step=0.01, format="%.4f")
    peak_mult     = st.number_input("Peak multiplier",     value=float(os.getenv("PEAK_RATE_MULTIPLIER", "1.5")), step=0.1)
    offpeak_mult  = st.number_input("Off-peak multiplier", value=float(os.getenv("OFF_PEAK_RATE_MULTIPLIER", "0.7")), step=0.1)
    peak_start    = st.slider("Peak start hour",  0, 23, int(os.getenv("PEAK_HOURS_START", "17")))
    peak_end      = st.slider("Peak end hour",    0, 23, int(os.getenv("PEAK_HOURS_END", "21")))
    history_days  = st.slider("History (days)",   7, 90,  int(os.getenv("MAX_HISTORY_DAYS", "30")))

    st.divider()
    if st.button("🔄 Refresh Data"):
        get_snapshot.clear()
        st.rerun()

    granite = get_granite_client()
    if granite.is_demo_mode():
        st.warning("⚠️ Demo mode\nSet IBM credentials in `.env` for live AI.", icon="⚠️")
    else:
        st.success("✅ IBM Granite connected", icon="✅")

    st.divider()
    st.caption(f"Model: `{os.getenv('IBM_GRANITE_MODEL_ID','ibm/granite-4-h-small')}`")
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")


# ── Load data ─────────────────────────────────────────────────

snap     = get_snapshot(rate, peak_mult, offpeak_mult, peak_start, peak_end, history_days)
analyzer = EnergyAnalyzer(snap)
status   = analyzer.get_current_status()
bill     = analyzer.analyze_monthly_bill()
audit    = analyzer.audit_appliances()
schedule = analyzer.get_optimal_schedule()
patterns = analyzer.detect_patterns()
carbon   = analyzer.estimate_carbon()


# ── Header ────────────────────────────────────────────────────

st.title("🏠 Smart Home Energy Advisor Agent")
st.caption(
    f"Meter: **{snap.meter_id}** · "
    f"IBM Granite AI (`ibm/granite-4-h-small`) · "
    f"IBM Cloud Lite · "
    f"Updated: {snap.timestamp.strftime('%Y-%m-%d %H:%M')}"
)
st.divider()


# ── Tab layout ────────────────────────────────────────────────

tab_dash, tab_chat, tab_appliances, tab_schedule, tab_patterns, tab_carbon = st.tabs([
    "📊 Dashboard", "💬 AI Advisor", "🔌 Appliances", "⏰ Schedule", "📈 Patterns", "🌿 Carbon"
])


# ═════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═════════════════════════════════════════════════════════════

with tab_dash:
    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    pk_label = "🔴 Peak" if status["is_peak_hour"] else "🟢 Off-Peak"
    c1.metric("Current Draw",     f"{status['current_draw_kw']} kW")
    c2.metric("Today's Usage",    f"{snap.today_kwh} kWh")
    c3.metric("Month Usage",      f"{snap.month_kwh} kWh")
    c4.metric("Month Cost",       f"${snap.month_cost:.2f}")
    c5.metric("Rate Period",      pk_label)

    st.divider()

    col_left, col_right = st.columns([3, 2])

    # Daily usage bar chart
    with col_left:
        st.markdown('<div class="section-title">📅 Daily Usage — Last 30 Days</div>', unsafe_allow_html=True)
        df_daily = pd.DataFrame([
            {"date": d.date, "kWh": d.total_kwh, "cost": d.total_cost,
             "peak_kWh": d.peak_kwh, "offpeak_kWh": d.off_peak_kwh}
            for d in snap.daily_history
        ])
        fig_daily = go.Figure()
        fig_daily.add_bar(x=df_daily["date"], y=df_daily["offpeak_kWh"],
                          name="Off-Peak kWh", marker_color="#22c55e")
        fig_daily.add_bar(x=df_daily["date"], y=df_daily["peak_kWh"],
                          name="Peak kWh", marker_color="#ef4444")
        fig_daily.update_layout(
            barmode="stack", height=280, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=1.1),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    # Category pie chart
    with col_right:
        st.markdown('<div class="section-title">🥧 Cost by Category</div>', unsafe_allow_html=True)
        cats = bill["category_breakdown_pct"]
        fig_pie = px.pie(
            names=list(cats.keys()),
            values=list(cats.values()),
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig_pie.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                               showlegend=True, legend=dict(orientation="h", y=-0.1))
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Bill summary metrics
    st.divider()
    st.markdown('<div class="section-title">📋 Month Summary</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Daily kWh",    f"{bill['avg_daily_kwh']}")
    m2.metric("Peak Share",       f"{bill['peak_cost_share_pct']}%")
    m3.metric("7-Day Trend",      f"{bill['trend_7day_pct']:+.1f}%",
              delta=f"{bill['trend_7day_pct']:+.1f}%",
              delta_color="inverse")
    m4.metric("High-Usage Days",  len(bill.get("high_bill_flags", [])))


# ═════════════════════════════════════════════════════════════
# TAB 2 — AI CHAT ADVISOR
# ═════════════════════════════════════════════════════════════

with tab_chat:
    st.markdown("### 💬 Ask the Energy Advisor")
    st.caption("Powered by IBM Granite AI · Ask anything about your home's energy usage.")

    # Quick question buttons — shown above chat
    st.markdown("**Quick questions:**")
    q_cols = st.columns(3)
    quick_questions = [
        "Why is my bill so high?",
        "When should I run the washing machine?",
        "Which appliances cost the most?",
        "Show me usage patterns",
        "How can I save energy?",
        "What is my carbon footprint?",
    ]
    quick_q_chosen = None
    for i, q in enumerate(quick_questions):
        if q_cols[i % 3].button(q, key=f"quick_{i}"):
            quick_q_chosen = q

    st.divider()

    # Render full conversation with native chat bubbles (no truncation)
    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["role"] == "user" else "assistant",
                             avatar="🧑" if msg["role"] == "user" else "⚡"):
            st.markdown(msg["content"])

    # Text input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Your question:",
            placeholder="e.g. Why is my bill so high this month?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send ➤", use_container_width=True)

    # Resolve what to ask
    question = None
    if submitted and user_input.strip():
        question = user_input.strip()
    elif quick_q_chosen:
        question = quick_q_chosen

    if question:
        # Classify intent + run tools
        q_lower = question.lower()
        intent = "GENERAL_ADVICE"
        for keywords, detected_intent in KEYWORD_INTENT_MAP:
            if any(kw in q_lower for kw in keywords):
                intent = detected_intent
                break

        tool_fn_map = {
            "current_status":        lambda: status,
            "monthly_bill_analysis": lambda: bill,
            "appliance_audit":       lambda: audit,
            "optimal_schedule":      lambda: schedule,
            "pattern_detection":     lambda: patterns,
            "carbon_estimate":       lambda: carbon,
        }
        tool_names   = INTENT_TOOL_MAP.get(intent, ["current_status"])
        tool_results = [tool_fn_map[n]() for n in tool_names if n in tool_fn_map]

        pb = get_prompt_builder()
        prompt = pb.build_analysis_prompt(
            user_question=question,
            tool_results=tool_results,
            conversation_history=st.session_state.history,
        )

        with st.spinner("🤖 IBM Granite is thinking…"):
            answer = granite.generate(prompt)

        # Store in session
        st.session_state.messages.append({"role": "user",      "content": question})
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.history.append({"role": "user",      "content": question})
        st.session_state.history.append({"role": "assistant", "content": answer})
        if len(st.session_state.history) > 20:
            st.session_state.history = st.session_state.history[-20:]

        st.rerun()

    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.history  = []
        st.rerun()


# ═════════════════════════════════════════════════════════════
# TAB 3 — APPLIANCES
# ═════════════════════════════════════════════════════════════

with tab_appliances:
    st.markdown("### 🔌 Appliance Energy Audit")

    df_app = pd.DataFrame(audit["appliances"])

    # Top consumers bar chart
    st.markdown('<div class="section-title">Monthly Cost by Appliance</div>', unsafe_allow_html=True)
    fig_app = px.bar(
        df_app.head(10),
        x="monthly_cost", y="name",
        orientation="h",
        color="category",
        labels={"monthly_cost": "Monthly Cost ($)", "name": "Appliance"},
        color_discrete_sequence=px.colors.qualitative.Pastel,
        text="monthly_cost",
    )
    fig_app.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis=dict(autorange="reversed"))
    fig_app.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    st.plotly_chart(fig_app, use_container_width=True)

    # Appliance table
    st.markdown('<div class="section-title">Full Appliance Breakdown</div>', unsafe_allow_html=True)
    display_df = df_app[["name", "category", "daily_kwh", "monthly_kwh", "monthly_cost", "smart_controllable", "optimizable"]].copy()
    display_df.columns = ["Appliance", "Category", "Daily kWh", "Monthly kWh", "Monthly Cost ($)", "Smart", "Optimisable"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    a1, a2, a3 = st.columns(3)
    a1.metric("Total Monthly Cost", f"${audit['total_monthly_cost']:.2f}")
    a2.metric("Potential Saving",   f"${audit['potential_monthly_saving']:.2f}/mo")
    a3.metric("Top Consumer",       audit["top_3_consumers"][0])


# ═════════════════════════════════════════════════════════════
# TAB 4 — SCHEDULE OPTIMISER
# ═════════════════════════════════════════════════════════════

with tab_schedule:
    st.markdown("### ⏰ Time-of-Use Schedule Optimiser")
    st.info(
        f"🟢 **Off-peak window:** {schedule['off_peak_window']}  |  "
        f"Rate: **${schedule['off_peak_rate']}/kWh**  |  "
        f"Peak rate: **${schedule['peak_rate']}/kWh**",
        icon="💡"
    )

    df_sched = pd.DataFrame(schedule["shiftable_appliances"])

    # Saving waterfall chart
    st.markdown('<div class="section-title">Monthly Saving if Shifted to Off-Peak</div>', unsafe_allow_html=True)
    fig_sched = px.bar(
        df_sched.sort_values("monthly_saving", ascending=False),
        x="appliance", y="monthly_saving",
        color="monthly_saving",
        color_continuous_scale="Greens",
        labels={"monthly_saving": "Monthly Saving ($)", "appliance": "Appliance"},
        text="monthly_saving",
    )
    fig_sched.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                             coloraxis_showscale=False, xaxis_tickangle=-30)
    fig_sched.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
    st.plotly_chart(fig_sched, use_container_width=True)

    # Hourly rate heatmap
    st.markdown('<div class="section-title">Hourly Electricity Rate ($/kWh)</div>', unsafe_allow_html=True)
    from tools.cost_calculator import CostCalculator
    cc = CostCalculator()
    hours = list(range(24))
    rates = [cc.rate_at_hour(h) for h in hours]
    fig_rate = go.Figure(go.Bar(
        x=[f"{h:02d}:00" for h in hours],
        y=rates,
        marker_color=["#ef4444" if (peak_start <= h < peak_end)
                      else "#22c55e" if (h >= 22 or h < 6)
                      else "#f59e0b"
                      for h in hours],
        text=[f"${r:.3f}" for r in rates],
        textposition="outside",
    ))
    fig_rate.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0),
                           yaxis_title="Rate ($/kWh)")
    st.plotly_chart(fig_rate, use_container_width=True)

    s1, s2 = st.columns(2)
    s1.metric("Total Monthly Saving Potential", f"${schedule['total_monthly_saving_potential']:.2f}")
    s2.metric("Annual Saving Potential", f"${schedule['total_monthly_saving_potential']*12:.2f}")

    # Schedule table
    st.dataframe(df_sched[["appliance","daily_kwh","cost_if_peak","cost_if_offpeak","monthly_saving","recommended_window"]],
                 use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════
# TAB 5 — USAGE PATTERNS
# ═════════════════════════════════════════════════════════════

with tab_patterns:
    st.markdown("### 📈 Usage Patterns & Anomalies")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Avg Daily kWh",      f"{patterns['avg_daily_kwh']}")
    p2.metric("Weekday Avg",        f"{patterns['weekday_avg_kwh']} kWh")
    p3.metric("Weekend Avg",        f"{patterns['weekend_avg_kwh']} kWh",
              delta=f"{patterns['weekend_premium_pct']:+.1f}% vs weekday")
    p4.metric("Anomaly Days",       patterns["total_anomaly_days"])

    col_ph, col_an = st.columns([3, 2])

    # Hourly profile line chart
    with col_ph:
        st.markdown('<div class="section-title">Average Hourly Consumption Profile</div>', unsafe_allow_html=True)
        hp = patterns.get("hourly_profile", {})
        if hp:
            df_hp = pd.DataFrame(
                [{"hour": f"{int(h):02d}:00", "avg_kWh": v} for h, v in sorted(hp.items(), key=lambda x: int(x[0]))]
            )
            fig_hp = go.Figure()
            fig_hp.add_scatter(
                x=df_hp["hour"], y=df_hp["avg_kWh"],
                fill="tozeroy", mode="lines+markers",
                line=dict(color="#3b82f6", width=2),
                marker=dict(size=5),
            )
            # shade peak zone
            fig_hp.add_vrect(
                x0=f"{peak_start:02d}:00", x1=f"{peak_end:02d}:00",
                fillcolor="red", opacity=0.08, line_width=0,
                annotation_text="Peak", annotation_position="top left",
            )
            fig_hp.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                                  yaxis_title="Avg kWh/hr", xaxis_tickangle=-45)
            st.plotly_chart(fig_hp, use_container_width=True)

    # Anomaly days table
    with col_an:
        st.markdown('<div class="section-title">⚠️ High-Usage Anomaly Days</div>', unsafe_allow_html=True)
        anomalies = patterns.get("anomaly_days", [])
        if anomalies:
            df_an = pd.DataFrame(anomalies)
            df_an.columns = ["Date", "kWh", "Std Devs Above Avg"]
            st.dataframe(df_an, use_container_width=True, hide_index=True)
        else:
            st.success("No anomalies detected in the selected period.")

    # Daily trend line
    st.markdown('<div class="section-title">Daily kWh Trend</div>', unsafe_allow_html=True)
    df_daily2 = pd.DataFrame([
        {"date": d.date, "kWh": d.total_kwh}
        for d in snap.daily_history
    ])
    fig_trend = px.line(df_daily2, x="date", y="kWh",
                        labels={"kWh": "Daily kWh", "date": "Date"})
    fig_trend.add_hline(y=patterns["avg_daily_kwh"], line_dash="dot",
                        line_color="orange", annotation_text="Average")
    fig_trend.update_layout(height=240, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_trend, use_container_width=True)


# ═════════════════════════════════════════════════════════════
# TAB 6 — CARBON FOOTPRINT
# ═════════════════════════════════════════════════════════════

with tab_carbon:
    st.markdown("### 🌿 Carbon Footprint Estimator")

    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Monthly kWh",          f"{carbon['monthly_kwh']}")
    cc2.metric("Monthly CO₂",          f"{carbon['monthly_kg_co2']} kg")
    cc3.metric("Annual CO₂ (est.)",    f"{round(carbon['monthly_kg_co2']*12/1000,2)} tonnes")
    cc4.metric("Trees to Offset/yr",   f"{carbon['trees_to_offset_annually']}")

    st.info(f"📌 Emission factor: **{carbon['emission_factor_kg_per_kwh']} kg CO₂e/kWh**  ({carbon['note']})")

    # Monthly CO2 gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=carbon["monthly_kg_co2"],
        delta={"reference": 200, "increasing": {"color": "red"}, "decreasing": {"color": "green"}},
        title={"text": "Monthly CO₂ (kg)", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 600]},
            "bar":  {"color": "#22c55e"},
            "steps": [
                {"range": [0,   150], "color": "#bbf7d0"},
                {"range": [150, 300], "color": "#fef9c3"},
                {"range": [300, 600], "color": "#fee2e2"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 300,
            },
        },
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Per-appliance CO2 breakdown
    st.markdown('<div class="section-title">CO₂ by Appliance (monthly)</div>', unsafe_allow_html=True)
    df_co2 = pd.DataFrame(audit["appliances"])[["name", "monthly_kwh"]].copy()
    df_co2["monthly_kg_co2"] = (df_co2["monthly_kwh"] * carbon["emission_factor_kg_per_kwh"]).round(2)
    df_co2 = df_co2.sort_values("monthly_kg_co2", ascending=True).tail(10)
    fig_co2 = px.bar(df_co2, x="monthly_kg_co2", y="name", orientation="h",
                     color="monthly_kg_co2", color_continuous_scale="RdYlGn_r",
                     labels={"monthly_kg_co2": "Monthly CO₂ (kg)", "name": ""},
                     text="monthly_kg_co2")
    fig_co2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                           coloraxis_showscale=False)
    fig_co2.update_traces(texttemplate="%{text} kg", textposition="outside")
    st.plotly_chart(fig_co2, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────
st.divider()
st.caption(
    "⚡ Smart Home Energy Advisor Agent · IBM Agentic AI Project · Problem Statement No. 31  |  "
    "IBM Cloud Lite + IBM Granite AI (`ibm/granite-4-h-small`)"
)
