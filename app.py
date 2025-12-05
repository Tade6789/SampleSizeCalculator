import streamlit as st
import streamlit.components.v1 as components
import numpy as np
from scipy import stats
import pandas as pd
import json
from datetime import datetime
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

st.set_page_config(
    page_title="A/B Test Sample Size Calculator",
    page_icon="📊",
    layout="wide"
)

pwa_html = """
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#FF4B4B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="AB Calculator">
<script>
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registered');
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}
</script>
"""
components.html(pwa_html, height=0)

st.title("A/B Test Sample Size Calculator")
st.markdown("Calculate the required sample size for your upcoming A/B test to ensure statistically valid results.")

def calculate_sample_size(baseline_rate, mde, power, significance, two_tailed=True):
    """
    Calculate required sample size per variant for a two-proportion z-test.
    
    Parameters:
    - baseline_rate: Expected conversion rate for control group (0-1)
    - mde: Minimum detectable effect as relative change (0-1)
    - power: Statistical power (0-1), typically 0.8
    - significance: Significance level (0-1), typically 0.05
    - two_tailed: Whether to use two-tailed test (default True)
    
    Returns:
    - Sample size per variant
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    
    if p2 > 1:
        p2 = min(p2, 0.9999)
    
    p_pooled = (p1 + p2) / 2
    
    if two_tailed:
        z_alpha = stats.norm.ppf(1 - significance / 2)
    else:
        z_alpha = stats.norm.ppf(1 - significance)
    
    z_beta = stats.norm.ppf(power)
    
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                 z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    
    if denominator == 0:
        return float('inf')
    
    n = numerator / denominator
    
    return int(np.ceil(n))


def calculate_power_for_sample_size(baseline_rate, mde, n, significance, two_tailed=True):
    """Calculate power given a sample size."""
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    
    if p2 > 1:
        p2 = 0.9999
    
    p_pooled = (p1 + p2) / 2
    
    if two_tailed:
        z_alpha = stats.norm.ppf(1 - significance / 2)
    else:
        z_alpha = stats.norm.ppf(1 - significance)
    
    effect = abs(p2 - p1)
    se = np.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    
    if se == 0:
        return 1.0
    
    z_effect = effect / se
    power = stats.norm.cdf(z_effect - z_alpha)
    
    return min(power, 0.9999)


if 'scenarios' not in st.session_state:
    st.session_state.scenarios = []

if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

def get_ai_advice(question, context):
    """Get AI advice about A/B testing using OpenAI."""
    if not openai_client:
        return "AI assistant is not available. Please add your OpenAI API key."
    
    system_prompt = """You are an expert A/B testing consultant and statistician. 
You help users understand:
- How to design effective A/B tests
- Sample size requirements and statistical concepts
- Best practices for running experiments
- How to interpret results and avoid common pitfalls
- Statistical power, significance levels, and effect sizes

Keep responses concise but informative. Use the context provided about the user's current test parameters when relevant."""
    
    try:
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context about my current A/B test:\n{context}\n\nMy question: {question}"}
            ],
            max_completion_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

tab1, tab2, tab3 = st.tabs(["Calculator", "Comparison Mode", "AI Assistant"])

with tab1:
    st.divider()
    st.subheader("Test Parameters")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        baseline_rate = st.number_input(
            "Baseline Conversion Rate (%)",
            min_value=0.1,
            max_value=99.9,
            value=5.0,
            step=0.1,
            help="Your current conversion rate. For example, if 5 out of 100 visitors convert, enter 5%.",
            key="main_baseline"
        )
        
        mde = st.number_input(
            "Minimum Detectable Effect (%)",
            min_value=0.1,
            max_value=100.0,
            value=10.0,
            step=0.5,
            help="The smallest relative improvement you want to detect. For example, 10% means detecting a change from 5% to 5.5% conversion rate.",
            key="main_mde"
        )
    
    with col2:
        power = st.number_input(
            "Statistical Power (%)",
            min_value=50.0,
            max_value=99.9,
            value=80.0,
            step=5.0,
            help="The probability of detecting a true effect. Industry standard is 80%.",
            key="main_power"
        )
        
        significance = st.number_input(
            "Significance Level (%)",
            min_value=0.1,
            max_value=20.0,
            value=5.0,
            step=0.5,
            help="The probability of a false positive (Type I error). Industry standard is 5%.",
            key="main_significance"
        )
    
    with col3:
        test_type = st.radio(
            "Test Type",
            options=["Two-tailed", "One-tailed"],
            index=0,
            help="Two-tailed: Detect effects in either direction. One-tailed: Only detect effects in one direction (requires less samples but more assumptions).",
            key="main_test_type"
        )
        
        daily_traffic = st.number_input(
            "Expected Daily Traffic (optional)",
            min_value=0,
            max_value=10000000,
            value=0,
            step=100,
            help="Enter your expected daily visitors to estimate test duration. Leave at 0 to skip duration estimate.",
            key="main_traffic"
        )
    
    two_tailed = test_type == "Two-tailed"
    baseline_decimal = baseline_rate / 100
    mde_decimal = mde / 100
    power_decimal = power / 100
    significance_decimal = significance / 100
    
    expected_variant_rate = baseline_decimal * (1 + mde_decimal)
    
    if expected_variant_rate > 1:
        st.error("The combination of baseline rate and MDE results in a conversion rate over 100%. Please adjust your inputs.")
    else:
        sample_size_per_variant = calculate_sample_size(
            baseline_decimal,
            mde_decimal,
            power_decimal,
            significance_decimal,
            two_tailed
        )
        
        total_sample_size = sample_size_per_variant * 2
        
        st.divider()
        st.subheader("Required Sample Size")
        
        result_cols = st.columns(3 if daily_traffic > 0 else 2)
        
        with result_cols[0]:
            st.metric(
                label="Per Variant",
                value=f"{sample_size_per_variant:,}",
                help="Number of visitors needed for each variant (control and treatment)"
            )
        
        with result_cols[1]:
            st.metric(
                label="Total (Both Variants)",
                value=f"{total_sample_size:,}",
                help="Total number of visitors needed across both variants"
            )
        
        if daily_traffic > 0:
            days_needed = np.ceil(total_sample_size / daily_traffic)
            weeks_needed = days_needed / 7
            
            with result_cols[2]:
                if days_needed < 7:
                    duration_text = f"{int(days_needed)} days"
                elif days_needed < 30:
                    duration_text = f"{weeks_needed:.1f} weeks"
                else:
                    duration_text = f"{days_needed / 30:.1f} months"
                
                st.metric(
                    label="Estimated Duration",
                    value=duration_text,
                    help=f"Based on {daily_traffic:,} daily visitors"
                )
        
        st.divider()
        
        viz_col, summary_col = st.columns([1.2, 1])
        
        with viz_col:
            st.subheader("Power Curve")
            st.caption("See how power changes with different effect sizes and sample sizes")
            
            mde_range = np.linspace(max(0.01, mde_decimal * 0.3), min(0.5, mde_decimal * 3), 50)
            
            sample_sizes_to_plot = [
                int(sample_size_per_variant * 0.5),
                sample_size_per_variant,
                int(sample_size_per_variant * 1.5),
                int(sample_size_per_variant * 2)
            ]
            
            chart_data = []
            for n in sample_sizes_to_plot:
                for m in mde_range:
                    power_val = calculate_power_for_sample_size(
                        baseline_decimal, m, n, significance_decimal, two_tailed
                    )
                    chart_data.append({
                        "MDE (%)": m * 100,
                        "Power": power_val * 100,
                        "Sample Size": f"n={n:,}"
                    })
            
            df_chart = pd.DataFrame(chart_data)
            
            import altair as alt
            
            power_chart = alt.Chart(df_chart).mark_line(strokeWidth=2).encode(
                x=alt.X("MDE (%):Q", title="Minimum Detectable Effect (%)"),
                y=alt.Y("Power:Q", title="Statistical Power (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("Sample Size:N", title="Sample Size per Variant"),
                tooltip=["MDE (%)", "Power", "Sample Size"]
            ).properties(
                height=300
            ).interactive()
            
            target_line = alt.Chart(pd.DataFrame({"y": [power]})).mark_rule(
                strokeDash=[5, 5], color="red"
            ).encode(y="y:Q")
            
            current_point = alt.Chart(pd.DataFrame({
                "MDE (%)": [mde],
                "Power": [power],
                "label": ["Current Settings"]
            })).mark_point(size=150, color="red", filled=True).encode(
                x="MDE (%):Q",
                y="Power:Q",
                tooltip=["label", "MDE (%)", "Power"]
            )
            
            st.altair_chart(power_chart + target_line + current_point, width="stretch")
            st.caption("Red dashed line = target power level. Red dot = current settings.")
        
        with summary_col:
            st.subheader("Test Summary")
            
            expected_variant_rate_pct = expected_variant_rate * 100
            absolute_effect = expected_variant_rate_pct - baseline_rate
            
            summary_data = {
                "Parameter": [
                    "Test Type",
                    "Control Group Rate",
                    "Expected Variant Rate",
                    "Absolute Effect",
                    "Relative Effect (MDE)",
                    "Statistical Power",
                    "Significance Level"
                ],
                "Value": [
                    test_type,
                    f"{baseline_rate:.2f}%",
                    f"{expected_variant_rate_pct:.2f}%",
                    f"+{absolute_effect:.2f} pp",
                    f"+{mde:.1f}%",
                    f"{power:.0f}%",
                    f"{significance:.1f}%"
                ]
            }
            
            st.table(summary_data)
            
            export_data = {
                "calculation_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "parameters": {
                    "baseline_conversion_rate": baseline_rate,
                    "minimum_detectable_effect": mde,
                    "statistical_power": power,
                    "significance_level": significance,
                    "test_type": test_type
                },
                "results": {
                    "sample_size_per_variant": sample_size_per_variant,
                    "total_sample_size": total_sample_size,
                    "expected_variant_rate": round(expected_variant_rate_pct, 2),
                    "absolute_effect": round(absolute_effect, 2)
                }
            }
            
            if daily_traffic > 0:
                export_data["duration_estimate"] = {
                    "daily_traffic": daily_traffic,
                    "estimated_days": int(days_needed)
                }
            
            st.download_button(
                label="Export Results (JSON)",
                data=json.dumps(export_data, indent=2),
                file_name=f"ab_test_calculation_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        
        with st.expander("How is this calculated?"):
            st.markdown(f"""
            This calculator uses the **two-proportion z-test** formula for sample size calculation.
            
            **Test Type: {test_type}**
            - **Two-tailed test**: Detects effects in either direction (increase OR decrease). More conservative, requires larger sample size.
            - **One-tailed test**: Only detects effects in one direction. Requires smaller sample size but assumes you know the direction of effect.
            
            **Key concepts:**
            - **Baseline Conversion Rate**: Your current conversion rate before the test
            - **Minimum Detectable Effect (MDE)**: The smallest relative change you want to be able to detect
            - **Statistical Power**: The probability of detecting a real effect when one exists (avoiding false negatives)
            - **Significance Level**: The probability of detecting an effect when none exists (false positive rate)
            
            **The formula accounts for:**
            1. The pooled variance of both conversion rates
            2. Z-scores for both significance level ({'two-tailed' if two_tailed else 'one-tailed'}) and power
            3. The difference between control and variant rates
            
            **Tips for planning your test:**
            - Higher power or lower significance requires more samples
            - Smaller effects are harder to detect and require larger samples
            - Consider your available traffic when setting the MDE
            - One-tailed tests require ~20% fewer samples but should only be used when you're certain about effect direction
            """)

with tab2:
    st.subheader("Compare Multiple Scenarios")
    st.markdown("Add different test configurations to compare sample sizes and durations side-by-side.")
    
    with st.form("add_scenario"):
        st.markdown("**Add New Scenario**")
        
        form_cols = st.columns(5)
        
        with form_cols[0]:
            scenario_name = st.text_input("Scenario Name", value=f"Scenario {len(st.session_state.scenarios) + 1}")
        
        with form_cols[1]:
            scenario_baseline = st.number_input("Baseline Rate (%)", min_value=0.1, max_value=99.9, value=5.0, step=0.1, key="scenario_baseline")
        
        with form_cols[2]:
            scenario_mde = st.number_input("MDE (%)", min_value=0.1, max_value=100.0, value=10.0, step=0.5, key="scenario_mde")
        
        with form_cols[3]:
            scenario_power = st.number_input("Power (%)", min_value=50.0, max_value=99.9, value=80.0, step=5.0, key="scenario_power")
        
        with form_cols[4]:
            scenario_significance = st.number_input("Significance (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.5, key="scenario_sig")
        
        form_cols2 = st.columns(3)
        
        with form_cols2[0]:
            scenario_test_type = st.selectbox("Test Type", ["Two-tailed", "One-tailed"], key="scenario_test_type")
        
        with form_cols2[1]:
            scenario_traffic = st.number_input("Daily Traffic", min_value=0, max_value=10000000, value=1000, step=100, key="scenario_traffic")
        
        with form_cols2[2]:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Add Scenario", use_container_width=True)
        
        if submitted:
            scenario_two_tailed = scenario_test_type == "Two-tailed"
            scenario_baseline_dec = scenario_baseline / 100
            scenario_mde_dec = scenario_mde / 100
            
            sample_size = calculate_sample_size(
                scenario_baseline_dec,
                scenario_mde_dec,
                scenario_power / 100,
                scenario_significance / 100,
                scenario_two_tailed
            )
            
            days = np.ceil((sample_size * 2) / scenario_traffic) if scenario_traffic > 0 else None
            
            st.session_state.scenarios.append({
                "name": scenario_name,
                "baseline": scenario_baseline,
                "mde": scenario_mde,
                "power": scenario_power,
                "significance": scenario_significance,
                "test_type": scenario_test_type,
                "daily_traffic": scenario_traffic,
                "sample_size_per_variant": sample_size,
                "total_sample_size": sample_size * 2,
                "estimated_days": int(days) if days else None
            })
            st.rerun()
    
    if st.session_state.scenarios:
        st.divider()
        
        comparison_df = pd.DataFrame(st.session_state.scenarios)
        
        display_df = comparison_df.rename(columns={
            "name": "Scenario",
            "baseline": "Baseline (%)",
            "mde": "MDE (%)",
            "power": "Power (%)",
            "significance": "Sig. (%)",
            "test_type": "Test Type",
            "daily_traffic": "Daily Traffic",
            "sample_size_per_variant": "Sample/Variant",
            "total_sample_size": "Total Sample",
            "estimated_days": "Est. Days"
        })
        
        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )
        
        chart_cols = st.columns(2)
        
        with chart_cols[0]:
            sample_chart = alt.Chart(comparison_df).mark_bar().encode(
                x=alt.X("name:N", title="Scenario", sort=None),
                y=alt.Y("total_sample_size:Q", title="Total Sample Size"),
                color=alt.Color("name:N", legend=None),
                tooltip=["name", "total_sample_size"]
            ).properties(
                title="Sample Size Comparison",
                height=250
            )
            st.altair_chart(sample_chart, width="stretch")
        
        with chart_cols[1]:
            duration_df = comparison_df[comparison_df["estimated_days"].notna()]
            if not duration_df.empty:
                duration_chart = alt.Chart(duration_df).mark_bar().encode(
                    x=alt.X("name:N", title="Scenario", sort=None),
                    y=alt.Y("estimated_days:Q", title="Estimated Days"),
                    color=alt.Color("name:N", legend=None),
                    tooltip=["name", "estimated_days"]
                ).properties(
                    title="Duration Comparison",
                    height=250
                )
                st.altair_chart(duration_chart, width="stretch")
            else:
                st.info("Add scenarios with daily traffic to see duration comparison.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            comparison_export = {
                "export_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "scenarios": st.session_state.scenarios
            }
            st.download_button(
                label="Export Comparison (JSON)",
                data=json.dumps(comparison_export, indent=2),
                file_name=f"ab_test_comparison_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
        
        with col2:
            if st.button("Clear All Scenarios", type="secondary"):
                st.session_state.scenarios = []
                st.rerun()
    else:
        st.info("Add scenarios using the form above to compare different test configurations.")

with tab3:
    st.subheader("AI A/B Testing Assistant")
    st.markdown("Ask questions about A/B testing, experiment design, or get advice on your current test setup.")
    
    if not openai_client:
        st.warning("AI assistant requires an OpenAI API key. Please add your OPENAI_API_KEY in the Secrets tab.")
    else:
        current_context = f"""
- Baseline conversion rate: {st.session_state.get('main_baseline', 5.0)}%
- Minimum detectable effect: {st.session_state.get('main_mde', 10.0)}%
- Statistical power: {st.session_state.get('main_power', 80.0)}%
- Significance level: {st.session_state.get('main_significance', 5.0)}%
- Test type: {st.session_state.get('main_test_type', 'Two-tailed')}
- Daily traffic: {st.session_state.get('main_traffic', 0)}
"""
        
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        example_questions = [
            "What sample size do I need for my test?",
            "How long should I run my A/B test?",
            "What is statistical power and why does it matter?",
            "How do I choose the right MDE for my test?",
            "When should I use a one-tailed vs two-tailed test?",
            "What are common mistakes in A/B testing?"
        ]
        
        if not st.session_state.chat_messages:
            st.markdown("**Example questions you can ask:**")
            cols = st.columns(2)
            for i, q in enumerate(example_questions):
                with cols[i % 2]:
                    if st.button(q, key=f"example_{i}", use_container_width=True):
                        st.session_state.chat_messages.append({"role": "user", "content": q})
                        with st.spinner("Thinking..."):
                            response = get_ai_advice(q, current_context)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        st.rerun()
        
        if prompt := st.chat_input("Ask about A/B testing..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_ai_advice(prompt, current_context)
                st.markdown(response)
            
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        if st.session_state.chat_messages:
            if st.button("Clear Chat History", type="secondary"):
                st.session_state.chat_messages = []
                st.rerun()
