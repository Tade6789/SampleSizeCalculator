import streamlit as st
import numpy as np
from scipy import stats

st.set_page_config(
    page_title="A/B Test Sample Size Calculator",
    page_icon="📊",
    layout="centered"
)

st.title("A/B Test Sample Size Calculator")
st.markdown("Calculate the required sample size for your upcoming A/B test to ensure statistically valid results.")

st.divider()

def calculate_sample_size(baseline_rate, mde, power, significance):
    """
    Calculate required sample size per variant for a two-proportion z-test.
    
    Parameters:
    - baseline_rate: Expected conversion rate for control group (0-1)
    - mde: Minimum detectable effect as relative change (0-1)
    - power: Statistical power (0-1), typically 0.8
    - significance: Significance level (0-1), typically 0.05
    
    Returns:
    - Sample size per variant
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + mde)
    
    if p2 > 1:
        p2 = min(p2, 0.9999)
    
    p_pooled = (p1 + p2) / 2
    
    z_alpha = stats.norm.ppf(1 - significance / 2)
    z_beta = stats.norm.ppf(power)
    
    numerator = (z_alpha * np.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                 z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    
    if denominator == 0:
        return float('inf')
    
    n = numerator / denominator
    
    return int(np.ceil(n))


st.subheader("Test Parameters")

col1, col2 = st.columns(2)

with col1:
    baseline_rate = st.number_input(
        "Baseline Conversion Rate (%)",
        min_value=0.1,
        max_value=99.9,
        value=5.0,
        step=0.1,
        help="Your current conversion rate. For example, if 5 out of 100 visitors convert, enter 5%."
    )
    
    mde = st.number_input(
        "Minimum Detectable Effect (%)",
        min_value=0.1,
        max_value=100.0,
        value=10.0,
        step=0.5,
        help="The smallest relative improvement you want to detect. For example, 10% means detecting a change from 5% to 5.5% conversion rate."
    )

with col2:
    power = st.number_input(
        "Statistical Power (%)",
        min_value=50.0,
        max_value=99.9,
        value=80.0,
        step=5.0,
        help="The probability of detecting a true effect. Industry standard is 80%."
    )
    
    significance = st.number_input(
        "Significance Level (%)",
        min_value=0.1,
        max_value=20.0,
        value=5.0,
        step=0.5,
        help="The probability of a false positive (Type I error). Industry standard is 5%."
    )

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
        significance_decimal
    )
    
    total_sample_size = sample_size_per_variant * 2
    
    st.divider()
    st.subheader("Required Sample Size")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="Per Variant",
            value=f"{sample_size_per_variant:,}",
            help="Number of visitors needed for each variant (control and treatment)"
        )
    
    with col2:
        st.metric(
            label="Total (Both Variants)",
            value=f"{total_sample_size:,}",
            help="Total number of visitors needed across both variants"
        )
    
    st.divider()
    st.subheader("Test Summary")
    
    expected_variant_rate_pct = expected_variant_rate * 100
    absolute_effect = expected_variant_rate_pct - baseline_rate
    
    summary_data = {
        "Parameter": [
            "Control Group Rate",
            "Expected Variant Rate",
            "Absolute Effect",
            "Relative Effect (MDE)",
            "Statistical Power",
            "Significance Level"
        ],
        "Value": [
            f"{baseline_rate:.2f}%",
            f"{expected_variant_rate_pct:.2f}%",
            f"+{absolute_effect:.2f} percentage points",
            f"+{mde:.1f}%",
            f"{power:.0f}%",
            f"{significance:.1f}%"
        ]
    }
    
    st.table(summary_data)
    
    with st.expander("How is this calculated?"):
        st.markdown("""
        This calculator uses the **two-proportion z-test** formula for sample size calculation:
        
        **Key concepts:**
        - **Baseline Conversion Rate**: Your current conversion rate before the test
        - **Minimum Detectable Effect (MDE)**: The smallest relative change you want to be able to detect
        - **Statistical Power**: The probability of detecting a real effect when one exists (avoiding false negatives)
        - **Significance Level**: The probability of detecting an effect when none exists (false positive rate)
        
        **The formula accounts for:**
        1. The pooled variance of both conversion rates
        2. Z-scores for both significance level (two-tailed) and power
        3. The difference between control and variant rates
        
        **Tips for planning your test:**
        - Higher power or lower significance requires more samples
        - Smaller effects are harder to detect and require larger samples
        - Consider your available traffic when setting the MDE
        """)
