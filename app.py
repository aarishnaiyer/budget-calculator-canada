"""

Streamlit Web Application for International Student Cost Estimator

"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import requests

S3_BASE_URL = "https://intl-student-budget-data.s3.amazonaws.com"

@st.cache_data(show_spinner=False)
def load_json(name: str):
    url = f"{S3_BASE_URL}/{name}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()
try:
    PROGRAMS = load_json("programs.json")
    CITY_DATA = load_json("city_data.json")
    UNIVERSITIES = load_json("universities.json")
except requests.RequestException:
    st.error("Unable to load budget data. Please try again later.")
    st.stop()
# ============================================================================
# CONFIG
# ============================================================================

st.set_page_config(page_title="Canada Student Budget", page_icon="🍁", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #FF0000; text-align: center; margin-bottom: 0.5rem;}
    .sub-header {font-size: 1.1rem; color: #666; text-align: center; margin-bottom: 1.5rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🍁 Canada Student Budget Calculator</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Plan Your International Student Expenses</p>", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR INPUTS
# ============================================================================

with st.sidebar:
    st.header("🎓 University & Program")
    
    # Group universities by city for better UX
    uni_options = []
    for uni, data in UNIVERSITIES.items():
        if uni == "Custom/Other":
            uni_options.append(uni)
        else:
            city_short = data['city'].split()[0]
            tuition_k = data['tuition'] // 1000
            uni_options.append(f"{uni} ({city_short}, ${tuition_k}k)")
    
    uni_display = st.selectbox("Select university:", uni_options)
    
    # Extract actual university name
    if "Custom/Other" in uni_display:
        uni = "Custom/Other"
    else:
        uni = uni_display.split(" (")[0]
    
    # Always show program selection
    program_options = [f"{PROGRAMS[p]['emoji']} {p}" for p in PROGRAMS.keys()]
    program_display = st.selectbox("Select your program/major:", program_options, 
                                     help="Different programs have different tuition rates")
    program = program_display.split(" ", 1)[1]  # Remove emoji
    
    if uni == "Custom/Other":
        city = st.selectbox("Select city:", list(CITY_DATA.keys()))
        tuition = st.number_input("Annual Tuition (CAD)", min_value=0, value=25000, step=1000)
    else:
        city = UNIVERSITIES[uni]["city"]
        base_tuition = UNIVERSITIES[uni]["tuition"]
        
        # Show info about tuition calculation
        multiplier = PROGRAMS[program]["multiplier"]
        if multiplier != 1.0:
            st.info(f"ℹ️ {program} tuition is typically {multiplier}x the base rate")
        
        # Calculate adjusted tuition based on program
        adjusted_tuition = int(base_tuition * multiplier)
        
        tuition = st.number_input(
            f"Annual Tuition (CAD)", 
            min_value=0, 
            value=adjusted_tuition, 
            step=1000,
            help=f"Estimated for {program}: ${base_tuition:,} × {multiplier} = ${adjusted_tuition:,}"
        )
        st.caption(f"📍 {city} | Base rate: ${base_tuition:,}/year")
    
    st.header("🏠 Housing")
    rent = st.number_input("Monthly Rent (CAD)", min_value=0, value=1200, step=50)
    
    rent_incl_util = st.checkbox("Rent includes utilities")
    utilities = 0 if rent_incl_util else st.number_input(
        "Utilities (CAD/month)", min_value=0, value=CITY_DATA[city]["utilities"], step=10)
    
    rent_incl_internet = st.checkbox("Rent includes internet")
    internet = 0 if rent_incl_internet else st.number_input(
        "Internet & Phone (CAD/month)", min_value=0, value=CITY_DATA[city]["internet_phone"], step=5)
    
    transport_covered = st.checkbox("Free transit pass from university")
    
    st.header("🎉 Lifestyle")
    dining = st.number_input("Dining Out (monthly)", min_value=0, value=200, step=20)
    entertainment = st.number_input("Entertainment (monthly)", min_value=0, value=100, step=10)
    social = st.number_input("Social Activities (monthly)", min_value=0, value=150, step=10)
    shopping = st.number_input("Shopping (monthly)", min_value=0, value=100, step=10)
    misc = st.number_input("Miscellaneous (monthly)", min_value=0, value=100, step=10)
    
    st.header("☀️ Summer (4 months)")
    summer_type = st.radio("Where will you be?",
        ["Staying in same city", "Moving to another city", "Going home"])
    
    summer_city = city
    summer_rent = rent
    if summer_type == "Moving to another city":
        summer_city = st.selectbox("Summer city:", [c for c in CITY_DATA.keys() if c != city])
        summer_rent = st.number_input("Summer rent", min_value=0, value=1000, step=50)

# ============================================================================
# CALCULATIONS
# ============================================================================

city_costs = CITY_DATA[city]

monthly_expenses = {
    "Rent": rent,
    "Groceries": city_costs["groceries"],
    "Utilities": utilities,
    "Internet & Phone": internet,
    "Transportation": 0 if transport_covered else city_costs["transportation"],
    "Dining Out": dining,
    "Entertainment": entertainment,
    "Social": social,
    "Shopping": shopping,
    "Miscellaneous": misc
}

monthly_total = sum(monthly_expenses.values())
fall_winter_total = monthly_total * 8

if summer_type == "Going home":
    summer_total = 0
elif summer_type == "Staying in same city":
    summer_total = monthly_total * 4
else:
    sc = CITY_DATA[summer_city]
    summer_monthly = summer_rent + sc["groceries"] + sc["utilities"] + sc["internet_phone"] + sc["transportation"]
    summer_total = summer_monthly * 4

annual_total = fall_winter_total + summer_total + tuition

# ============================================================================
# DISPLAY
# ============================================================================

# Header with university and program info
st.info(f"🎓 **{uni}** | 📍 {city} | 📚 {program} | 💰 Tuition: ${tuition:,}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Monthly", f"${monthly_total:,.0f}", "Fall/Winter")
col2.metric("8 Months", f"${fall_winter_total:,.0f}", "Fall + Winter")
col3.metric("4 Months", f"${summer_total:,.0f}", "Summer")
col4.metric("Annual Total", f"${annual_total:,.0f}", "All-in")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Breakdown", "📈 Charts", "💾 Export"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Expenses")
        df = pd.DataFrame({
            'Category': monthly_expenses.keys(),
            'Amount': monthly_expenses.values()
        })
        df = df[df['Amount'] > 0]
        st.dataframe(df.style.format({'Amount': '${:,.2f}'}), hide_index=True, use_container_width=True)
        st.metric("Total", f"${monthly_total:,.0f}")
    
    with col2:
        st.subheader("Annual Summary")
        summary = pd.DataFrame({
            'Period': ['Fall & Winter (8mo)', 'Summer (4mo)', 'Tuition', 'TOTAL'],
            'Amount': [fall_winter_total, summer_total, tuition, annual_total]
        })
        st.dataframe(summary.style.format({'Amount': '${:,.2f}'}), hide_index=True, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Distribution")
        data = {k: v for k, v in monthly_expenses.items() if v > 0}
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = plt.cm.Set3(range(len(data)))
        ax.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f"${monthly_total:,.0f}/month", fontsize=14, fontweight='bold')
        st.pyplot(fig)
    
    with col2:
        st.subheader("Annual Breakdown")
        fig, ax = plt.subplots(figsize=(8, 6))
        periods = ['Fall/Winter', 'Summer', 'Tuition']
        amounts = [fall_winter_total, summer_total, tuition]
        bars = ax.bar(periods, amounts, color=['#2E86AB', '#F18F01', '#A23B72'])
        ax.set_ylabel("Amount (CAD)", fontweight='bold')
        ax.set_title(f"Total: ${annual_total:,.0f}", fontsize=14, fontweight='bold')
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h, f'${h:,.0f}', 
                   ha='center', va='bottom', fontweight='bold')
        st.pyplot(fig)

with tab3:
    st.subheader("Download Your Budget")
    
    export_data = pd.DataFrame({
        'Category': ['University', 'City', 'Program', '', 'MONTHLY EXPENSES'] + 
                    list(monthly_expenses.keys()) + 
                    ['', 'ANNUAL SUMMARY', 'Fall & Winter Total', 'Summer Total', 
                     'Tuition', 'ANNUAL TOTAL'],
        'Amount': [uni, city, program, '', ''] + 
                  list(monthly_expenses.values()) + 
                  ['', '', fall_winter_total, summer_total, tuition, annual_total]
    })
    
    csv = export_data.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"budget_{uni.replace(' ', '_')}_{program.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    st.info("💡 **Tip:** You can screenshot the charts above for your records!")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    Made for international students 🍁 | Data based on 2024 estimates
</div>
""", unsafe_allow_html=True)