import streamlit as st
from dotenv import load_dotenv
import os
import sys

# ---- Make sure project root is in the path so imports work ----
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Product Launch Intelligence Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# ---------------- Sidebar: API Config ----------------
st.sidebar.header("🔑 API Configuration")

groq_key = st.sidebar.text_input(
    "Groq API Key",
    type="password",
    value=os.getenv("GROQ_API_KEY", ""),
    help="Required – powers the LangChain / Groq LLM agents."
)
firecrawl_key = st.sidebar.text_input(
    "Firecrawl API Key",
    type="password",
    value=os.getenv("FIRECRAWL_API_KEY", ""),
    help="Required – used for deterministic web search."
)

if groq_key:
    os.environ["GROQ_API_KEY"] = groq_key
if firecrawl_key:
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_key

keys_ready = bool(groq_key and firecrawl_key)

# Import workflow only once keys are set (avoids import-time key errors)
if keys_ready:
    from graph.workflow import app as graph_app
else:
    graph_app = None

# ---------------- Session State ----------------
for key in ("competitor_response", "sentiment_response", "metrics_response"):
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------- Main UI ----------------
st.title("🚀 Product Launch Intelligence Agent")
st.markdown("*AI-powered insights for GTM, Product Marketing & Growth Teams — powered by **LangGraph** + **Groq** + **Firecrawl***")

st.divider()

# Company input
st.subheader("🏢 Company Analysis")
col1, col2 = st.columns([3, 1])
with col1:
    company_name = st.text_input(
        label="Company Name",
        placeholder="e.g. OpenAI, Tesla, Spotify",
        label_visibility="collapsed"
    )
with col2:
    if company_name:
        st.success(f"✓ Analyzing **{company_name}**")

st.divider()

# Helper to run the LangGraph pipeline
def run_pipeline(analysis_type: str) -> dict:
    if not keys_ready:
        st.error("⚠️ Please enter both API keys in the sidebar first.")
        return {}
    if not company_name:
        st.error("⚠️ Please enter a company name above.")
        return {}
    state = {
        "company_name": company_name,
        "analysis_type": analysis_type,
        "raw_bullets": None,
        "final_report": None,
        "validation_status": None,
    }
    result = graph_app.invoke(state)
    return {
        "final_report": result.get("final_report", "No report generated."),
        "validation_status": result.get("validation_status", "No validation logs available.")
    }

# Tabs
tabs = st.tabs(["🔍 Competitor Analysis", "💬 Market Sentiment", "📈 Launch Metrics"])

# ---- Competitor Analysis ----
with tabs[0]:
    st.markdown("### 🔍 Competitor Launch Analysis")
    with st.expander("ℹ️ About this agent", expanded=False):
        st.markdown("""
        **Launch Analyst** — Senior GTM Strategist  
        - Fetches top 3 web results via Firecrawl (deterministic, no schema errors)  
        - Extracts positioning, strengths, weaknesses & learnings  
        - Formats an executive-ready Markdown report  
        """)

    if not company_name:
        st.info("👆 Enter a company name above to get started.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            btn = st.button("🚀 Analyze Competitor Strategy", key="btn_competitor", type="primary", use_container_width=True)
        with c2:
            if st.session_state.competitor_response:
                st.success("✅ Analysis complete")
            else:
                st.info("⏳ Ready to analyze")

        if btn:
            with st.spinner("🔍 Searching and analyzing…"):
                try:
                    st.session_state.competitor_response = run_pipeline("competitor")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if st.session_state.competitor_response:
            st.divider()
            with st.expander("🛡️ Scraped Data Validation Report", expanded=True):
                st.markdown(st.session_state.competitor_response.get("validation_status", "No validation logs available."))
            st.divider()
            st.markdown(st.session_state.competitor_response.get("final_report"))

# ---- Market Sentiment ----
with tabs[1]:
    st.markdown("### 💬 Market Sentiment Analysis")
    with st.expander("ℹ️ About this agent", expanded=False):
        st.markdown("""
        **Sentiment Analyst** — Consumer Perception Expert  
        - Fetches top 3 web results focused on reviews, social, and press  
        - Identifies positive & negative themes  
        - Outputs a concise sentiment brief  
        """)

    if not company_name:
        st.info("👆 Enter a company name above to get started.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            btn = st.button("📊 Analyze Market Sentiment", key="btn_sentiment", type="primary", use_container_width=True)
        with c2:
            if st.session_state.sentiment_response:
                st.success("✅ Analysis complete")
            else:
                st.info("⏳ Ready to analyze")

        if btn:
            with st.spinner("💬 Fetching sentiment signals…"):
                try:
                    st.session_state.sentiment_response = run_pipeline("sentiment")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if st.session_state.sentiment_response:
            st.divider()
            with st.expander("🛡️ Scraped Data Validation Report", expanded=True):
                st.markdown(st.session_state.sentiment_response.get("validation_status", "No validation logs available."))
            st.divider()
            st.markdown(st.session_state.sentiment_response.get("final_report"))

# ---- Launch Metrics ----
with tabs[2]:
    st.markdown("### 📈 Launch Performance Metrics")
    with st.expander("ℹ️ About this agent", expanded=False):
        st.markdown("""
        **Metrics Analyst** — Launch Performance Expert  
        - Fetches top 3 web results for KPIs, traction, and press data  
        - Extracts adoption numbers, revenue signals, and qualitative cues  
        - Outputs an executive KPI dashboard  
        """)

    if not company_name:
        st.info("👆 Enter a company name above to get started.")
    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            btn = st.button("📊 Analyze Launch Metrics", key="btn_metrics", type="primary", use_container_width=True)
        with c2:
            if st.session_state.metrics_response:
                st.success("✅ Analysis complete")
            else:
                st.info("⏳ Ready to analyze")

        if btn:
            with st.spinner("📈 Analyzing launch performance…"):
                try:
                    st.session_state.metrics_response = run_pipeline("metrics")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        if st.session_state.metrics_response:
            st.divider()
            with st.expander("🛡️ Scraped Data Validation Report", expanded=True):
                st.markdown(st.session_state.metrics_response.get("validation_status", "No validation logs available."))
            st.divider()
            st.markdown(st.session_state.metrics_response.get("final_report"))

# ---------------- Sidebar: Status ----------------
st.sidebar.divider()
st.sidebar.markdown("### 🤖 System Status")
if keys_ready:
    st.sidebar.success("✅ All Agents Online")
else:
    st.sidebar.error("❌ API keys required")

st.sidebar.divider()
st.sidebar.markdown("### 🎯 Agents")
for icon, name, desc in [
    ("🔍", "Launch Analyst", "Positioning & GTM strategy"),
    ("💬", "Sentiment Analyst", "Consumer perception"),
    ("📈", "Metrics Analyst", "KPIs & traction"),
]:
    st.sidebar.markdown(f"**{icon} {name}**")
    st.sidebar.caption(desc)

if company_name:
    st.sidebar.divider()
    st.sidebar.markdown("### 📊 Analysis Status")
    st.sidebar.markdown(f"**Company:** {company_name}")
    for icon, label, state_key in [
        ("🔍", "Competitor Analysis", "competitor_response"),
        ("💬", "Sentiment Analysis", "sentiment_response"),
        ("📈", "Metrics Analysis", "metrics_response"),
    ]:
        if st.session_state[state_key]:
            st.sidebar.success(f"{icon} {label} ✓")
        else:
            st.sidebar.info(f"{icon} {label} ⏳")

    st.sidebar.divider()
    if st.sidebar.button("🔄 Clear All Results", use_container_width=True):
        st.session_state.competitor_response = None
        st.session_state.sentiment_response = None
        st.session_state.metrics_response = None
        st.rerun()
