"""
==========================================================
AI GlueOps Intelligence Dashboard
Version : 1.0
Author  : Krushnat Kapse
==========================================================
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from router import CopilotRouter
from copilot_ui import render_copilot_ui

# ----------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------

st.set_page_config(
    page_title="AI GlueOps Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"
GEMINI_MODEL = "gemini-3.5-flash-lite"

# ----------------------------------------------------------
# PAGE STYLE
# ----------------------------------------------------------

st.markdown("""
<style>
.block-container{
padding-top:1rem;
padding-bottom:1rem;
}
.metric-card{
background:#fafafa;
padding:15px;
border-radius:10px;
box-shadow:0px 2px 8px rgba(0,0,0,.08);
}
.big-font{
font-size:26px;
font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# TITLE
# ----------------------------------------------------------

st.title("GlueJobs Intelligence Dashboard")
st.caption("Glue Execution Analytics powered by Ollama")

# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(uploaded_file)
    else:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file)

    # Check if 'content' exists and contains stringified JSON/dicts
    if "content" in df.columns:
        parsed_contents = []
        for val in df["content"]:
            if isinstance(val, str) and val.strip().startswith("{"):
                try:
                    parsed_contents.append(json.loads(val))
                except json.JSONDecodeError:
                    parsed_contents.append({})
            elif isinstance(val, dict):
                parsed_contents.append(val)
            else:
                parsed_contents.append({})
        
        content_df = pd.json_normalize(parsed_contents)
        
        if "tags" in content_df.columns:
            tags_list = []
            for t in content_df["tags"]:
                if isinstance(t, str) and t.strip().startswith("{"):
                    try:
                        tags_list.append(json.loads(t))
                    except:
                        tags_list.append({})
                elif isinstance(t, dict):
                    tags_list.append(t)
                else:
                    tags_list.append({})
            tags_df = pd.json_normalize(tags_list)
            content_df = pd.concat([content_df.drop(columns=["tags"], errors="ignore"), tags_df], axis=1)

        df = pd.concat([df.drop(columns=["content"], errors="ignore"), content_df], axis=1)

    # Clean up column names by keeping only the leaf node after dots
    df.columns = [col.split('.')[-1] for col in df.columns]
    
    return df

# ----------------------------------------------------------
# PREPROCESS
# ----------------------------------------------------------

@st.cache_data(show_spinner=False)
def preprocess(df):
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Generate derived time metrics safely if missing
    if "date" in df.columns:
        df["execution_dt"] = pd.to_datetime(df["date"], errors="coerce")
        df["execution_date"] = df["execution_dt"].dt.date
    elif "timestamp" in df.columns:
        df["execution_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["execution_date"] = df["execution_dt"].dt.date
    else:
        df["execution_date"] = datetime.today().date()

    if "duration_hours" in df.columns:
        df["runtime_minutes"] = df["duration_hours"] * 60
    else:
        df["duration_hours"] = 0.0
        df["runtime_minutes"] = 0.0

    if "cost" not in df.columns:
        df["cost"] = 0.0
    if "dpu_hours" not in df.columns:
        df["dpu_hours"] = 0.0
    if "number_of_worker" not in df.columns:
        df["number_of_worker"] = 1

    # Safe runtime bucketing
    def get_bucket(mins):
        if mins < 5: return "< 5 mins"
        elif mins < 15: return "5-15 mins"
        elif mins < 30: return "15-30 mins"
        elif mins < 60: return "30-60 mins"
        else: return "> 60 mins"

    df["runtime_bucket"] = df["runtime_minutes"].apply(get_bucket)
    return df

# ----------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------

st.sidebar.header("Upload")

uploaded_file = st.sidebar.file_uploader(
    "Glue CSV / JSON",
    type=["csv", "xlsx", "json"]
)

if uploaded_file is None:
    st.info("Upload Glue execution dataset (CSV or JSON)")
    st.stop()

df = load_file(uploaded_file)
df = preprocess(df)

# ----------------------------------------------------------
# FILTERS
# ----------------------------------------------------------

st.sidebar.header("Filters")

applications = st.sidebar.multiselect(
    "Application",
    sorted(df["Application_Name"].dropna().unique()) if "Application_Name" in df.columns else [],
    default=sorted(df["Application_Name"].dropna().unique()) if "Application_Name" in df.columns else []
)

business_units = st.sidebar.multiselect(
    "Business Unit",
    sorted(df["Business_Unit"].dropna().unique()) if "Business_Unit" in df.columns else [],
    default=sorted(df["Business_Unit"].dropna().unique()) if "Business_Unit" in df.columns else []
)

environment = st.sidebar.multiselect(
    "Environment",
    sorted(df["Environment"].dropna().unique()) if "Environment" in df.columns else [],
    default=sorted(df["Environment"].dropna().unique()) if "Environment" in df.columns else []
)

if "Application_Name" in df.columns and applications:
    df = df[df["Application_Name"].isin(applications)]
if "Business_Unit" in df.columns and business_units:
    df = df[df["Business_Unit"].isin(business_units)]
if "Environment" in df.columns and environment:
    df = df[df["Environment"].isin(environment)]

# ----------------------------------------------------------
# KPI
# ----------------------------------------------------------

SUCCESS = ["SUCCEEDED"]
FAILED = ["FAILED", "ERROR", "TIMEOUT"]

total_jobs = len(df)
success_jobs = len(df[df["JobRunState"].isin(SUCCESS)]) if "JobRunState" in df.columns else 0
failed_jobs = len(df[df["JobRunState"].isin(FAILED)]) if "JobRunState" in df.columns else 0

success_rate = round(success_jobs / total_jobs * 100, 2) if total_jobs else 0
failure_rate = round(failed_jobs / total_jobs * 100, 2) if total_jobs else 0

total_cost = round(df["cost"].sum(), 2) if "cost" in df.columns else 0.0
total_runtime = round(df["duration_hours"].sum(), 2) if "duration_hours" in df.columns else 0.0
total_dpu = round(df["dpu_hours"].sum(), 2) if "dpu_hours" in df.columns else 0.0
avg_runtime = round(df["duration_hours"].mean(), 2) if "duration_hours" in df.columns else 0.0
avg_cost = round(df["cost"].mean(), 2) if "cost" in df.columns else 0.0

# ----------------------------------------------------------
# TABS
# ----------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overall Summary",
    "💰 Cost Summary",
    "⏱ Runtime Summary",
    "❌ Failures Summary",
    "🤖 AI"
])

# ==========================================================
# EXECUTIVE DASHBOARD
# ==========================================================

with tab1:
    st.header("Executive Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Jobs", f"{total_jobs:,}")
    col2.metric("Success Rate", f"{success_rate}%")
    col3.metric("Failure Rate", f"{failure_rate}%")
    col4.metric("Total Cost ($)", f"{total_cost:,.2f}")

    col5, col6, col7 = st.columns(3)
    col5.metric("Runtime (Hours)", f"{total_runtime:,.2f}")
    col6.metric("DPU Hours", f"{total_dpu:,.2f}")
    col7.metric("Average Runtime", f"{avg_runtime:.2f} hrs")

    st.divider()

    left, right = st.columns((1, 2))

    with left:
        if "JobRunState" in df.columns:
            status_df = df["JobRunState"].value_counts().reset_index()
            status_df.columns = ["Status", "Count"]
            fig = px.pie(status_df, names="Status", values="Count", hole=.45, title="Job Status Distribution")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if "execution_date" in df.columns:
            trend = df.groupby("execution_date", as_index=False).size()
            trend.columns = ["Execution Date", "Jobs"]
            fig = px.line(trend, x="Execution Date", y="Jobs", markers=True, title="Daily Job Execution Trend")
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    left, right = st.columns(2)

    with left:
        if "Application_Name" in df.columns and "cost" in df.columns:
            cost_app = df.groupby("Application_Name", as_index=False)["cost"].sum().sort_values("cost", ascending=False).head(10)
            fig = px.bar(cost_app, x="Application_Name", y="cost", text_auto=".2s", title="Top 10 Applications by Cost")
            fig.update_layout(xaxis_title="Application", yaxis_title="Cost", height=450)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        if "runtime_minutes" in df.columns:
            fig = px.histogram(df, x="runtime_minutes", nbins=30, title="Runtime Distribution")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# COST DASHBOARD
# ==========================================================

with tab2:
    st.header("💰 Cost Analytics Dashboard")

    max_cost = round(df["cost"].max(), 2) if "cost" in df.columns else 0.0
    min_cost = round(df["cost"].min(), 2) if "cost" in df.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cost", f"${total_cost:,.2f}")
    c2.metric("Average Cost", f"${avg_cost:,.2f}")
    c3.metric("Maximum Cost", f"${max_cost:,.2f}")
    c4.metric("Minimum Cost", f"${min_cost:,.2f}")

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        cols_to_show = [c for c in ["job_name", "Application_Name", "Business_Unit", "Environment", "cost"] if c in df.columns]
        top_jobs = df.sort_values("cost", ascending=False)[cols_to_show].head(10) if "cost" in df.columns else pd.DataFrame()
        st.subheader("Top 10 Expensive Jobs")
        st.dataframe(top_jobs, use_container_width=True, height=380)

    with right:
        if not top_jobs.empty and "job_name" in top_jobs.columns:
            fig = px.bar(top_jobs, x="cost", y="job_name", orientation="h", text_auto=".2s", title="Top Expensive Jobs")
            fig.update_layout(height=380, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if "Business_Unit" in df.columns and "cost" in df.columns:
            bu = df.groupby("Business_Unit", as_index=False)["cost"].sum().sort_values("cost", ascending=False)
            fig = px.bar(bu, x="Business_Unit", y="cost", text_auto=".2s", title="Cost by Business Unit")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "Environment" in df.columns and "cost" in df.columns:
            env = df.groupby("Environment", as_index=False)["cost"].sum()
            fig = px.pie(env, names="Environment", values="cost", hole=.45, title="Cost by Environment")
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    if "execution_date" in df.columns and "cost" in df.columns:
        daily = df.groupby("execution_date", as_index=False)["cost"].sum()
        fig = px.line(daily, x="execution_date", y="cost", markers=True, title="Daily Cost Trend")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# RUNTIME DASHBOARD
# ==========================================================

with tab3:
    st.header("⏱ Runtime Analytics Dashboard")

    max_runtime = round(df["duration_hours"].max(), 2) if "duration_hours" in df.columns else 0.0
    min_runtime = round(df["duration_hours"].min(), 2) if "duration_hours" in df.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Runtime (hrs)", f"{total_runtime:,.2f}")
    c2.metric("Average Runtime", f"{avg_runtime:.2f} hrs")
    c3.metric("Maximum Runtime", f"{max_runtime:.2f} hrs")
    c4.metric("Minimum Runtime", f"{min_runtime:.2f} hrs")

    st.divider()

    left, right = st.columns([1.1, 1])

    with left:
        cols_to_show = [c for c in ["job_name", "Application_Name", "Business_Unit", "duration_hours", "cost"] if c in df.columns]
        longest = df.sort_values("duration_hours", ascending=False)[cols_to_show].head(10) if "duration_hours" in df.columns else pd.DataFrame()
        st.subheader("Top 10 Longest Running Jobs")
        st.dataframe(longest, use_container_width=True, height=380)

    with right:
        if not longest.empty and "job_name" in longest.columns:
            fig = px.bar(longest, x="duration_hours", y="job_name", orientation="h", text_auto=".2f", title="Longest Running Jobs")
            fig.update_layout(height=380, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# FAILURE DASHBOARD
# ==========================================================

with tab4:
    st.header("❌ Failure Analytics Dashboard")

    failed_df = df[df["JobRunState"].isin(FAILED)] if "JobRunState" in df.columns else pd.DataFrame()
    successful_df = df[df["JobRunState"].isin(SUCCESS)] if "JobRunState" in df.columns else pd.DataFrame()

    total_failed = len(failed_df)
    total_success = len(successful_df)
    wasted_cost = round(failed_df["cost"].sum(), 2) if "cost" in failed_df.columns else 0.0
    wasted_runtime = round(failed_df["duration_hours"].sum(), 2) if "duration_hours" in failed_df.columns else 0.0
    wasted_dpu = round(failed_df["dpu_hours"].sum(), 2) if "dpu_hours" in failed_df.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Failed Jobs", f"{total_failed:,}")
    c2.metric("Failure %", f"{failure_rate}%")
    c3.metric("Estimated Wasted Cost", f"${wasted_cost:,.2f}")
    c4.metric("Lost Runtime", f"{wasted_runtime:.2f} hrs")

    st.divider()
    st.subheader("Failed Job Executions")
    if not failed_df.empty:
        failed_cols = [c for c in ["job_name", "Application_Name", "Business_Unit", "Environment", "duration_hours", "dpu_hours", "cost", "JobRunState"] if c in failed_df.columns]
        st.dataframe(failed_df[failed_cols], use_container_width=True, height=350)
    else:
        st.success("🎉 No failed executions found in selection.")

# ==========================================================
# AI COPILOT DASHBOARD
# ==========================================================

with tab5:
    def render_ai_tab(
        df: pd.DataFrame,
        OLLAMA_URL: str = "http://localhost:11434/api/generate",
        OLLAMA_MODEL: str = "qwen2.5:3b",
        GEMINI_MODEL: str = "gemini-2.5-flash",
        **kwargs
    ) -> None:
        if df is None or df.empty:
            st.warning("⚠️ No Glue operations dataframe provided. Please upload or load data.")
            return

        if "copilot_router" not in st.session_state:
            st.session_state["copilot_router"] = CopilotRouter(
            df=df,
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL,
            gemini_model=GEMINI_MODEL,
        )
        else:
            st.session_state["copilot_router"].update_dataframe(df)

        router: CopilotRouter = st.session_state["copilot_router"]
        render_copilot_ui(router)

    render_ai_tab(
        df=df,
        OLLAMA_URL=OLLAMA_URL,
        OLLAMA_MODEL=OLLAMA_MODEL,
        GEMINI_MODEL=GEMINI_MODEL,
    )