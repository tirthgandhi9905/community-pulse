import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Community Pulse — AI Decision Intelligence",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for premium aesthetic
st.markdown("""
<style>
    /* Main container styling */
    .reportview-container {
        background: #0f172a;
    }
    /* Metric Card styling */
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #38bdf8;
        font-weight: 500;
    }
    /* Chat bubbles */
    .chat-bubble-user {
        background-color: #0284c7;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0px 15px;
        margin-bottom: 10px;
        width: fit-content;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-assistant {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0px;
        margin-bottom: 10px;
        width: fit-content;
        max-width: 80%;
    }
</style>
""", unsafe_allow_html=True)

# ---------- DATA INGESTION ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("complaints.csv", parse_dates=["date"])
        return df
    except Exception as e:
        # Fallback dummy data if file is missing
        dates = pd.date_range(start="2026-04-01", end="2026-07-01", freq="D")
        np.random.seed(42)
        dummy_data = {
            "date": np.random.choice(dates, size=600),
            "zone": np.random.choice(["Zone A", "Zone B", "Zone C", "Zone D", "Zone E"], size=600),
            "category": np.random.choice(["Pothole", "Garbage Overflow", "Illegal Parking", "Streetlight Outage", "Water Leak", "Noise Complaint", "Graffiti"], size=600),
            "status": np.random.choice(["Open", "Resolved"], size=600, p=[0.4, 0.6])
        }
        return pd.DataFrame(dummy_data)

df = load_data()

# ---------- SIDEBAR & SETTINGS ----------
st.sidebar.title("🏙️ Community Pulse")
st.sidebar.markdown("AI-Powered Civic Decision Intelligence")

# 1. API Configuration
st.sidebar.subheader("🔑 Gemini AI API Configuration")
env_key = os.environ.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Enter Gemini API Key",
    value=env_key,
    type="password",
    help="Unlock real LLM reasoning, outcome prediction, and conversational analyses. Leave empty to run in smart mock fallback mode."
)

active_api_key = api_key_input if api_key_input else env_key

# Set up Gemini connection function
def get_gemini_response(prompt, system_instruction=""):
    if not active_api_key:
        return None
    try:
        genai.configure(api_key=active_api_key)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {str(e)}"

# 2. Filters
st.sidebar.subheader("📊 Dashboard Filters")
all_zones = sorted(df.zone.unique())
all_cats = sorted(df.category.unique())

selected_zones = st.sidebar.multiselect("Select Zones", all_zones, default=all_zones)
selected_cats = st.sidebar.multiselect("Select Categories", all_cats, default=all_cats)

# Filter dataset
fdf = df[df.zone.isin(selected_zones) & df.category.isin(selected_cats)]

# Active filter status indicator
st.sidebar.info(f"Analyzing {len(fdf)} active complaints ({len(df)} total in database).")

# Quick actions/presets in sidebar
st.sidebar.subheader("⚡ Quick Analytics Presets")
if st.sidebar.button("Show Unresolved Backlog Only"):
    fdf = fdf[fdf.status == "Open"]
    st.sidebar.success("Filtered to open complaints only!")

# ---------- MAIN CONTENT HEADER ----------
st.title("🏙️ Community Pulse — Civic Decision Intelligence Platform")
st.caption("Google Cloud Gen AI APAC Cohort 2 · Intelligent Automation for Smarter Communities")
st.markdown("Transforming unstructured citizen feedbacks and complaints into **risk scores**, **predictive trends**, and **actionable dispatch priorities** in seconds.")

st.markdown("---")

# ---------- METRICS SECTION ----------
if len(fdf) > 0:
    total_complaints = len(fdf)
    unresolved_df = fdf[fdf.status == "Open"]
    total_unresolved = len(unresolved_df)
    unresolved_pct = (total_unresolved / total_complaints) * 100
    
    top_cat = fdf.category.value_counts().index[0] if not fdf.empty else "N/A"
    
    # Calculate Risk Ranking per Zone
    agg = fdf.groupby("zone").agg(
        total=("status", "count"),
        open_count=("status", lambda x: (x == "Open").sum())
    ).reset_index()
    agg["open_rate"] = (agg.open_count / agg.total).round(2)
    agg["risk_score"] = ((agg.total / agg.total.max()) * 0.5 + agg.open_rate * 0.5).round(2)
    agg = agg.sort_values("risk_score", ascending=False)
    
    highest_risk_zone = agg.iloc[0].zone if not agg.empty else "N/A"
    highest_risk_score = agg.iloc[0].risk_score if not agg.empty else 0.0
    
    # Render premium HTML metrics grid
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Ingested</div>
            <div class="metric-value">{total_complaints}</div>
            <div class="metric-sub">Complaints Filtered</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Unresolved Backlog</div>
            <div class="metric-value">{total_unresolved}</div>
            <div class="metric-sub">{unresolved_pct:.1f}% Backlog Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top Concern</div>
            <div class="metric-value" style="font-size: 1.5rem; line-height: 2.7rem; color: #f43f5e;">{top_cat}</div>
            <div class="metric-sub">Highest Volume Category</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Critical Zone</div>
            <div class="metric-value" style="color: #fbbf24;">{highest_risk_zone}</div>
            <div class="metric-sub">Risk Score: {highest_risk_score}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("No data matches current filters. Please adjust filters in the sidebar.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)

# ---------- ANALYTICS & VISUALIZATIONS ----------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📈 Complaint Volatility & Trends")
    # Group by date to show trend
    trend = fdf.groupby(fdf["date"].dt.to_period("W")).size().reset_index(name="count")
    trend["date"] = trend["date"].astype(str)
    
    fig_trend = px.line(
        trend, x="date", y="count", 
        markers=True,
        labels={"date": "Week Commencing", "count": "Complaint Count"},
        color_discrete_sequence=["#38bdf8"]
    )
    fig_trend.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#94a3b8",
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=True, gridcolor="#334155"),
        yaxis=dict(showgrid=True, gridcolor="#334155")
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("🍕 Distribution by Complaint Type")
    cat_dist = fdf["category"].value_counts().reset_index()
    cat_dist.columns = ["Category", "Count"]
    
    fig_pie = px.pie(
        cat_dist, values="Count", names="Category",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Tealgrn_r
    )
    fig_pie.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#94a3b8",
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("🚨 Municipal Risk League Table")
    # Pretty dataframe styling
    styled_agg = agg.rename(columns={
        "zone": "City Zone",
        "total": "Total Complaints",
        "open_count": "Open Backlog",
        "open_rate": "Backlog Rate",
        "risk_score": "Composite Risk Score"
    })
    st.dataframe(
        styled_agg.style.background_gradient(cmap="Oranges", subset=["Composite Risk Score"])
        .format({"Backlog Rate": "{:.0%}", "Composite Risk Score": "{:.2f}"}),
        use_container_width=True,
        hide_index=True
    )
    
    st.subheader("📊 Zone Backlog Breakdown")
    zone_backlog = fdf.groupby(["zone", "status"]).size().reset_index(name="count")
    
    fig_bar = px.bar(
        zone_backlog, x="zone", y="count", color="status",
        labels={"zone": "City Zone", "count": "Complaints Count", "status": "Complaint Status"},
        color_discrete_map={"Open": "#ef4444", "Resolved": "#10b981"},
        barmode="group"
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#94a3b8",
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#334155")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ---------- AI ADVISOR INSIGHT GENERATOR ----------
st.subheader("🤖 GenAI Copilot: Operations Advisory Report")

# Prepare text summary of current metrics
def create_summary_text(fdf, agg):
    total = len(fdf)
    unres = (fdf.status == "Open").sum()
    top_z = agg.iloc[0].zone if not agg.empty else "N/A"
    top_z_score = agg.iloc[0].risk_score if not agg.empty else 0.0
    top_c = fdf.category.value_counts().index[0] if not fdf.empty else "N/A"
    
    # Detailed category breakdown for prompt
    cats_str = ""
    for c, count in fdf.category.value_counts().items():
        cats_str += f"- {c}: {count} total complaints\n"
        
    return f"""
    Active Filtered Complaints: {total}
    Open Unresolved Cases: {unres}
    Highest Risk Target: {top_z} (Risk Score: {top_z_score})
    Top Issue Category: {top_c}
    Category Details:
    {cats_str}
    """

summary_text = create_summary_text(fdf, agg)

# Generation logic
with st.spinner("AI is analyzing local dataset and drafting advisory report..."):
    if active_api_key:
        prompt = f"""
        You are the municipal Decision Intelligence engine. Based on the active filters, analyze these metrics:
        {summary_text}
        
        Provide a concise, professional executive recommendation report (max 4-5 bullet points).
        Include:
        1. Identification of the critical sector (zone & category).
        2. High-impact operational resource suggestion (e.g., crew dispatch, utility management).
        3. Risk outlook for next 7 days based on current backlog rate.
        Make it clean and highly tactical.
        """
        sys_inst = "You are a professional city planner and data-driven civic intelligence consultant."
        ai_report = get_gemini_response(prompt, sys_inst)
    else:
        # Fallback Mock Advisor logic (highly localized to actual stats)
        top_zone = agg.iloc[0]
        cat_counts = fdf[fdf.zone == top_zone.zone].category.value_counts()
        top_cat_zone = cat_counts.index[0] if len(cat_counts) else "N/A"
        ai_report = f"""
*Running in Smart Fallback Mode (No Gemini API Key provided. Paste key in sidebar to enable dynamic LLM generation).*

**Executive Advisor Report:**
* **Priority Zone Action**: **{top_zone.zone}** represents the highest operational risk index (**{top_zone.risk_score}**) with **{int(top_zone.open_count)} unresolved tickets** out of {int(top_zone.total)} total complaints.
* **Dominant Risk Vector**: The most pressing complaint category in the critical zone is **{top_cat_zone}**. Field operations should target dispatch crews specifically to this task.
* **Resource Optimization recommendation**: Re-route 15% of maintenance personnel from lower-risk sectors to **{top_zone.zone}** for a 7-day sprint targeting {top_cat_zone.lower()} repairs to clear the backlog.
* **Short-Term Outlook**: If backlog clearing remains unaddressed, community resolution delays for **{top_cat_zone.lower()}** are projected to increase by 12% in the next week.
"""

st.info(ai_report)

st.markdown("---")

# ---------- CONVERSATIONAL CHAT ASSISTANT ----------
st.subheader("💬 Ask Community Pulse AI (RAG)")
st.caption("Interact with the dashboard in natural language: ask for data counts, draft notifications, or request operational predictions.")

# Initialize chat session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Community Pulse Assistant. Ask me anything about the complaints data, or request me to write operational emails, draft staff notifications, or summarize zone risks."}
    ]

# Render chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble-assistant">{msg["content"]}</div>', unsafe_allow_html=True)

# Smart Helper to answer simple analytical queries in Mock Mode
def parse_mock_query(user_query, summary_str, fdf):
    uq = user_query.lower()
    
    # 1. Draft email notification
    if "email" in uq or "draft" in uq or "write" in uq or "letter" in uq or "notify" in uq:
        zones_found = [z for z in fdf.zone.unique() if z.lower() in uq]
        target_z = zones_found[0] if zones_found else "Zone A"
        cats_found = [c for c in fdf.category.unique() if c.lower() in uq]
        target_c = cats_found[0] if cats_found else "Civic Issues"
        
        return f"""Here is a draft notification email you can send to city crews:

**Subject**: Action Required: Resolve outstanding {target_c} issues in {target_z}

**Dear Dispatch Supervisor,**

The Community Pulse intelligence board has flagged **{target_z}** for critical backlog clearance.
Our records show multiple outstanding **{target_c.lower()}** cases reported by residents.

Please prioritize assigning a local field team to inspect and repair these issues immediately. Provide a status update to the dashboard within 48 hours.

Best regards,
Civic Command Operations Center"""

    # 2. Specific Zone Summary
    for z in fdf.zone.unique():
        if z.lower() in uq:
            z_df = fdf[fdf.zone == z]
            tot = len(z_df)
            op = (z_df.status == "Open").sum()
            cats_count = z_df.category.value_counts().to_dict()
            cats_summary = ", ".join([f"{k} ({v})" for k, v in cats_count.items()])
            return f"In **{z}**, we have a total of **{tot} complaints** (with **{op} unresolved/open**). The categories reported here are: {cats_summary}."
            
    # 3. Specific Category Summary
    for c in fdf.category.unique():
        if c.lower() in uq:
            c_df = fdf[fdf.category == c]
            tot = len(c_df)
            op = (c_df.status == "Open").sum()
            zone_count = c_df.zone.value_counts().to_dict()
            zones_summary = ", ".join([f"{k} ({v})" for k, v in zone_count.items()])
            return f"For the **{c}** category, there are **{tot} total records** across all zones. **{op} remain unresolved**. Distribution by Zone: {zones_summary}."

    # 4. Standard Fallback Advice
    return f"""Based on the current filtered dataset ({len(fdf)} active complaints):
* Top Zone: {fdf.zone.value_counts().index[0] if not fdf.empty else 'N/A'}
* Top Category: {fdf.category.value_counts().index[0] if not fdf.empty else 'N/A'}
* Unresolved Case Count: {(fdf.status == 'Open').sum()}

*(Paste your Gemini API Key in the sidebar to enable open-ended reasoning, translations, and complex analyses!)*"""

# Handle new user input
if user_input := st.chat_input("Ask a question about the complaints or request a draft..."):
    # Add user message to history and render
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)
    
    with st.spinner("Assistant is formulating response..."):
        if active_api_key:
            # RAG Context
            context_prompt = f"""
            You are 'Community Pulse Assistant', a decision support system for city stakeholders.
            You are assisting them with the complaints dataset.
            Here is the current dataset context summary:
            {summary_text}
            
            Answer the following query truthfully, clearly, and concisely based on this context. 
            If the query requests an action like writing an email notification, draft a professional template.
            If they ask about data counts, perform the math based on the context summary.
            
            User Question: {user_input}
            """
            assistant_response = get_gemini_response(context_prompt, "You are a helpful municipal decision intelligence chatbot.")
        else:
            # Local Smart Parser
            assistant_response = parse_mock_query(user_input, summary_text, fdf)
            
    # Add assistant response to history and render
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    st.markdown(f'<div class="chat-bubble-assistant">{assistant_response}</div>', unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("🤖 Built for GenAI APAC Cohort 2 Project Submission. Stack: Streamlit, Plotly, Pandas, Google Gemini API, Docker, Google Cloud Run.")
