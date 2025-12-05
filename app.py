import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from scipy import stats
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from openai import OpenAI
from supabase import create_client, Client
import altair as alt

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

st.set_page_config(
    page_title="A/B Test Calculator Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary-color: #0066CC;
        --secondary-color: #00A3CC;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: var(--primary-color);
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 500;
        color: #666;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,102,204,0.3);
    }
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E5E7EB;
        transition: all 0.3s ease;
    }
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(0,102,204,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAFB 0%, #FFFFFF 100%);
    }
</style>
""", unsafe_allow_html=True)

pwa_html = """
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#0066CC">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="AB Calculator Pro">
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => navigator.serviceWorker.register('/static/sw.js'));
}
</script>
"""
components.html(pwa_html, height=0)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

def calculate_sample_size(baseline_rate, mde, power, significance, two_tailed=True):
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    if p2 > 1:
        p2 = min(p2, 0.9999)
    p_pooled = (p1 + p2) / 2
    z_alpha = stats.norm.ppf(1 - significance / 2) if two_tailed else stats.norm.ppf(1 - significance)
    z_beta = stats.norm.ppf(power)
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    if denominator == 0:
        return float('inf')
    return int(np.ceil(numerator / denominator))

def calculate_power_for_sample_size(baseline_rate, mde, n, significance, two_tailed=True):
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    if p2 > 1:
        p2 = 0.9999
    z_alpha = stats.norm.ppf(1 - significance / 2) if two_tailed else stats.norm.ppf(1 - significance)
    effect = abs(p2 - p1)
    se = np.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    if se == 0:
        return 1.0
    z_effect = effect / se
    return min(stats.norm.cdf(z_effect - z_alpha), 0.9999)

def get_ai_advice(question, context):
    if not openai_client:
        return "AI assistant unavailable. Please add OPENAI_API_KEY."
    system_prompt = """You are an expert A/B testing consultant. Help users understand test design, sample sizes, statistical concepts, best practices, and how to avoid pitfalls. Keep responses concise but informative."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            max_completion_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def save_calculation(name, baseline_rate, mde, power, significance, test_type, daily_traffic, sample_size_per_variant, total_sample_size, estimated_days, notes=""):
    if not supabase or not st.session_state.user:
        return False, "Not authenticated"
    try:
        supabase.table("test_calculations").insert({
            "user_id": st.session_state.user['id'],
            "name": name,
            "baseline_rate": float(baseline_rate),
            "mde": float(mde),
            "power": float(power),
            "significance": float(significance),
            "test_type": test_type,
            "daily_traffic": int(daily_traffic),
            "sample_size_per_variant": int(sample_size_per_variant),
            "total_sample_size": int(total_sample_size),
            "estimated_days": int(estimated_days) if estimated_days else None,
            "notes": notes
        }).execute()
        return True, "Saved successfully"
    except Exception as e:
        return False, f"Error: {str(e)}"

def load_calculations():
    if not supabase or not st.session_state.user:
        return []
    try:
        result = supabase.table("test_calculations").select("*").eq("user_id", st.session_state.user['id']).order("created_at", desc=True).limit(50).execute()
        return result.data
    except Exception as e:
        return []

def delete_calculation(calc_id):
    if not supabase or not st.session_state.user:
        return False, "Not authenticated"
    try:
        supabase.table("test_calculations").delete().eq("id", calc_id).execute()
        return True, "Deleted"
    except Exception as e:
        return False, f"Error: {str(e)}"

def show_auth_page():
    st.markdown("<h1 style='text-align: center; margin-bottom: 2rem;'>A/B Test Calculator Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 18px; margin-bottom: 3rem;'>Professional A/B testing calculator with AI insights and test history</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["Sign In", "Sign Up"])
        with auth_tab1:
            with st.form("signin_form"):
                st.subheader("Welcome Back")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                    if not supabase:
                        st.error("Database not configured.")
                    elif email and password:
                        try:
                            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            if response.user:
                                st.session_state.authenticated = True
                                st.session_state.user = response.user
                                profile_result = supabase.table("profiles").select("*").eq("id", response.user.id).maybeSingle().execute()
                                if not profile_result.data:
                                    username = email.split('@')[0]
                                    supabase.table("profiles").insert({"id": response.user.id, "username": username, "full_name": username}).execute()
                                st.success("Signed in successfully")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Sign in failed: {str(e)}")
                    else:
                        st.warning("Please enter email and password")
        with auth_tab2:
            with st.form("signup_form"):
                st.subheader("Create Account")
                email = st.text_input("Email", key="signup_email")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password", key="signup_password")
                password_confirm = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                    if not supabase:
                        st.error("Database not configured.")
                    elif not all([email, username, password]):
                        st.warning("Please fill in all fields")
                    elif len(password) < 6:
                        st.warning("Password must be at least 6 characters")
                    elif password != password_confirm:
                        st.error("Passwords do not match")
                    else:
                        try:
                            response = supabase.auth.sign_up({"email": email, "password": password})
                            if response.user:
                                supabase.table("profiles").insert({"id": response.user.id, "username": username, "full_name": username}).execute()
                                st.success("Account created! You can now sign in.")
                        except Exception as e:
                            st.error(f"Sign up failed: {str(e)}")

def show_sidebar():
    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### Hello, {st.session_state.user.email.split('@')[0]}")
            st.divider()
            if st.button("Sign Out", use_container_width=True):
                try:
                    supabase.auth.sign_out()
                except:
                    pass
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
            st.divider()
            st.markdown("### Quick Stats")
            calculations = load_calculations()
            st.metric("Saved Tests", len(calculations))
            if calculations:
                total_samples = sum(c.get('total_sample_size', 0) for c in calculations)
                st.metric("Total Samples", f"{total_samples:,}")

def show_calculator_tab():
    st.subheader("Test Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        baseline_rate = st.number_input("Baseline Rate (%)", min_value=0.1, max_value=99.9, value=5.0, step=0.1, help="Current conversion rate", key="calc_baseline")
        mde = st.number_input("MDE (%)", min_value=0.1, max_value=100.0, value=10.0, step=0.5, help="Smallest improvement to detect", key="calc_mde")
    with col2:
        power = st.number_input("Power (%)", min_value=50.0, max_value=99.9, value=80.0, step=5.0, help="Probability of detecting effect", key="calc_power")
        significance = st.number_input("Significance (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.5, help="False positive rate", key="calc_sig")
    with col3:
        test_type = st.radio("Test Type", ["Two-tailed", "One-tailed"], help="Two-tailed detects effects in both directions", key="calc_type")
        daily_traffic = st.number_input("Daily Traffic", min_value=0, value=1000, step=100, help="Expected daily visitors", key="calc_traffic")

    two_tailed = test_type == "Two-tailed"
    baseline_decimal = baseline_rate / 100
    mde_decimal = mde / 100
    expected_variant_rate = baseline_decimal * (1 + mde_decimal)

    if expected_variant_rate > 1:
        st.error("Combination results in conversion rate over 100%. Please adjust.")
        return

    sample_size_per_variant = calculate_sample_size(baseline_decimal, mde_decimal, power / 100, significance / 100, two_tailed)
    total_sample_size = sample_size_per_variant * 2

    st.divider()
    st.subheader("Results")
    result_cols = st.columns(4)
    with result_cols[0]:
        st.metric("Per Variant", f"{sample_size_per_variant:,}")
    with result_cols[1]:
        st.metric("Total Sample", f"{total_sample_size:,}")

    if daily_traffic > 0:
        days_needed = np.ceil(total_sample_size / daily_traffic)
        with result_cols[2]:
            if days_needed < 7:
                duration = f"{int(days_needed)} days"
            elif days_needed < 30:
                duration = f"{days_needed / 7:.1f} weeks"
            else:
                duration = f"{days_needed / 30:.1f} months"
            st.metric("Duration", duration)
        with result_cols[3]:
            end_date = datetime.now() + timedelta(days=int(days_needed))
            st.metric("Completion", end_date.strftime("%b %d, %Y"))

    st.divider()
    col_save, col_export = st.columns(2)
    with col_save:
        with st.expander("Save Calculation"):
            calc_name = st.text_input("Test Name", value=f"Test - {datetime.now().strftime('%Y-%m-%d')}")
            calc_notes = st.text_area("Notes", placeholder="Add notes...")
            if st.button("Save to History", use_container_width=True, type="primary"):
                if supabase and st.session_state.user:
                    success, message = save_calculation(calc_name, baseline_rate, mde, power, significance, test_type, daily_traffic, sample_size_per_variant, total_sample_size, days_needed if daily_traffic > 0 else None, calc_notes)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Sign in to save")

    with col_export:
        with st.expander("Export Results"):
            export_data = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "parameters": {"baseline": baseline_rate, "mde": mde, "power": power, "significance": significance, "test_type": test_type},
                "results": {"sample_per_variant": sample_size_per_variant, "total_sample": total_sample_size}
            }
            st.download_button("Download JSON", json.dumps(export_data, indent=2), f"test_{datetime.now().strftime('%Y%m%d_%H%M')}.json", "application/json", use_container_width=True)

    st.divider()
    st.subheader("Power Analysis")
    mde_range = np.linspace(max(0.01, mde_decimal * 0.3), min(0.5, mde_decimal * 3), 50)
    sample_sizes_to_plot = [int(sample_size_per_variant * 0.5), sample_size_per_variant, int(sample_size_per_variant * 1.5), int(sample_size_per_variant * 2)]
    chart_data = []
    for n in sample_sizes_to_plot:
        for m in mde_range:
            power_val = calculate_power_for_sample_size(baseline_decimal, m, n, significance / 100, two_tailed)
            chart_data.append({"MDE (%)": m * 100, "Power": power_val * 100, "Sample Size": f"n={n:,}"})
    df_chart = pd.DataFrame(chart_data)
    power_chart = alt.Chart(df_chart).mark_line(strokeWidth=3).encode(
        x=alt.X("MDE (%):Q", title="Minimum Detectable Effect (%)"),
        y=alt.Y("Power:Q", title="Power (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Sample Size:N", scale=alt.Scale(scheme='category10')),
        tooltip=["MDE (%)", "Power", "Sample Size"]
    ).properties(height=400)
    target_line = alt.Chart(pd.DataFrame({"y": [power]})).mark_rule(strokeDash=[5, 5], color="#FF3333", strokeWidth=2).encode(y="y:Q")
    current_point = alt.Chart(pd.DataFrame({"MDE (%)": [mde], "Power": [power]})).mark_point(size=200, color="#FF3333", filled=True).encode(x="MDE (%):Q", y="Power:Q")
    st.altair_chart(power_chart + target_line + current_point, use_container_width=True)

def show_history_tab():
    st.subheader("Test History")
    if not supabase or not st.session_state.user:
        st.info("Sign in to save and view test history")
        return
    calculations = load_calculations()
    if not calculations:
        st.info("No saved calculations yet. Save from the Calculator tab!")
        return
    for calc in calculations:
        with st.expander(f"{calc['name']} - {pd.to_datetime(calc['created_at']).strftime('%b %d, %Y %H:%M')}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Parameters**")
                st.write(f"Baseline: {calc['baseline_rate']}%")
                st.write(f"MDE: {calc['mde']}%")
                st.write(f"Power: {calc['power']}%")
                st.write(f"Significance: {calc['significance']}%")
            with col2:
                st.markdown("**Results**")
                st.write(f"Sample/Variant: {calc['sample_size_per_variant']:,}")
                st.write(f"Total: {calc['total_sample_size']:,}")
                if calc.get('estimated_days'):
                    st.write(f"Duration: {calc['estimated_days']} days")
            with col3:
                if calc.get('notes'):
                    st.markdown("**Notes**")
                    st.write(calc['notes'])
                if st.button("Delete", key=f"del_{calc['id']}", type="secondary"):
                    success, message = delete_calculation(calc['id'])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

def show_comparison_tab():
    st.subheader("Compare Scenarios")
    with st.form("add_scenario"):
        cols = st.columns(5)
        with cols[0]:
            name = st.text_input("Name", value=f"Scenario {len(st.session_state.scenarios) + 1}")
        with cols[1]:
            baseline = st.number_input("Baseline (%)", min_value=0.1, value=5.0, step=0.1)
        with cols[2]:
            mde = st.number_input("MDE (%)", min_value=0.1, value=10.0, step=0.5)
        with cols[3]:
            power = st.number_input("Power (%)", min_value=50.0, value=80.0, step=5.0)
        with cols[4]:
            sig = st.number_input("Sig (%)", min_value=0.1, value=5.0, step=0.5)
        cols2 = st.columns(3)
        with cols2[0]:
            test_type = st.selectbox("Type", ["Two-tailed", "One-tailed"])
        with cols2[1]:
            traffic = st.number_input("Daily Traffic", min_value=0, value=1000, step=100)
        with cols2[2]:
            st.write("")
            st.write("")
            if st.form_submit_button("Add Scenario", use_container_width=True, type="primary"):
                sample_size = calculate_sample_size(baseline / 100, mde / 100, power / 100, sig / 100, test_type == "Two-tailed")
                days = np.ceil((sample_size * 2) / traffic) if traffic > 0 else None
                st.session_state.scenarios.append({"name": name, "baseline": baseline, "mde": mde, "power": power, "significance": sig, "test_type": test_type, "daily_traffic": traffic, "sample_size_per_variant": sample_size, "total_sample_size": sample_size * 2, "estimated_days": int(days) if days else None})
                st.rerun()

    if st.session_state.scenarios:
        st.divider()
        df = pd.DataFrame(st.session_state.scenarios)
        st.dataframe(df.rename(columns={"name": "Scenario", "baseline": "Baseline (%)", "mde": "MDE (%)", "power": "Power (%)", "significance": "Sig (%)", "test_type": "Type", "daily_traffic": "Traffic", "sample_size_per_variant": "Sample/Variant", "total_sample_size": "Total", "estimated_days": "Days"}), use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            chart = alt.Chart(df).mark_bar().encode(x=alt.X("name:N", title="Scenario", sort=None), y=alt.Y("total_sample_size:Q", title="Total Sample"), color=alt.Color("name:N", legend=None, scale=alt.Scale(scheme='category10')), tooltip=["name", "total_sample_size"]).properties(title="Sample Size Comparison", height=300)
            st.altair_chart(chart, use_container_width=True)
        with col2:
            duration_df = df[df["estimated_days"].notna()]
            if not duration_df.empty:
                chart2 = alt.Chart(duration_df).mark_bar().encode(x=alt.X("name:N", title="Scenario", sort=None), y=alt.Y("estimated_days:Q", title="Days"), color=alt.Color("name:N", legend=None, scale=alt.Scale(scheme='category10')), tooltip=["name", "estimated_days"]).properties(title="Duration Comparison", height=300)
                st.altair_chart(chart2, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("Export Comparison", json.dumps({"date": datetime.now().strftime("%Y-%m-%d"), "scenarios": st.session_state.scenarios}, indent=2), f"comparison_{datetime.now().strftime('%Y%m%d')}.json", "application/json", use_container_width=True)
        with col2:
            if st.button("Clear All", type="secondary", use_container_width=True):
                st.session_state.scenarios = []
                st.rerun()

def show_ai_tab():
    st.subheader("AI A/B Testing Assistant")
    if not openai_client:
        st.warning("AI assistant requires OPENAI_API_KEY.")
        return
    context = f"Baseline: {st.session_state.get('calc_baseline', 5.0)}%, MDE: {st.session_state.get('calc_mde', 10.0)}%, Power: {st.session_state.get('calc_power', 80.0)}%, Sig: {st.session_state.get('calc_sig', 5.0)}%"
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    examples = ["What sample size do I need?", "How long should I run?", "What is statistical power?", "How to choose MDE?", "One-tailed vs two-tailed?", "Common A/B test mistakes?"]
    if not st.session_state.chat_messages:
        st.markdown("**Quick Questions:**")
        cols = st.columns(3)
        for i, q in enumerate(examples):
            with cols[i % 3]:
                if st.button(q, key=f"ex_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": q})
                    with st.spinner("Thinking..."):
                        response = get_ai_advice(q, context)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    st.rerun()
    if prompt := st.chat_input("Ask about A/B testing..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_advice(prompt, context)
            st.markdown(response)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    if st.session_state.chat_messages:
        if st.button("Clear Chat", type="secondary"):
            st.session_state.chat_messages = []
            st.rerun()

def main():
    if not st.session_state.authenticated:
        show_auth_page()
    else:
        show_sidebar()
        st.title("A/B Test Calculator Pro")
        st.markdown("Professional sample size calculator with AI insights and test history tracking")
        tab1, tab2, tab3, tab4 = st.tabs(["Calculator", "Test History", "Comparison", "AI Assistant"])
        with tab1:
            show_calculator_tab()
        with tab2:
            show_history_tab()
        with tab3:
            show_comparison_tab()
        with tab4:
            show_ai_tab()

if __name__ == "__main__":
    main()
