import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import re

# ===============================
# CONFIG
# ===============================
st.set_page_config(
    page_title="SellSide DealNavigator | Seth Agyei Aboagye",
    layout="wide",
    initial_sidebar_state="expanded"
)

DESIGNED_BY = "Designed by Seth Agyei Aboagye"

# ===============================
# STYLING
# ===============================
st.markdown(
    """
    <style>
    .main-banner {
        background-color:#eef4fb;
        padding:12px 16px;
        border-radius:10px;
        font-weight:600;
        margin-bottom:16px;
        border:1px solid #d7e6f5;
    }
    .guide-box {
        background-color:#f8fafc;
        padding:14px 16px;
        border-radius:10px;
        border:1px solid #e5e7eb;
        margin-bottom:12px;
    }
    .small-note {
        color:#475569;
        font-size:0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ===============================
# HEADER
# ===============================
st.title("SellSide Group M&A Intelligence Dashboard")
st.caption(
    "Dynamic prospecting, company intelligence, prioritization, comparison, and export workflow for buy-side and sell-side coverage."
)
st.markdown(
    f"""
    <div class="main-banner">
        {DESIGNED_BY}
    </div>
    """,
    unsafe_allow_html=True
)

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("Dashboard Controls")
    st.markdown(f"**{DESIGNED_BY}**")

    service_type = st.multiselect(
        "Service Type",
        ["Sell-Side", "Buy-Side"],
        default=["Sell-Side", "Buy-Side"]
    )

    industry = st.multiselect(
        "Industry",
        [
            "Tech",
            "Healthcare",
            "Industrial",
            "Distribution",
            "Facility Services",
            "Industrial Services",
            "Manufacturing",
            "Business Services"
        ],
        default=["Industrial", "Distribution", "Facility Services"]
    )

    country = st.multiselect(
        "Country",
        [
            "United States",
            "Canada",
            "United Kingdom",
            "Germany",
            "France",
            "Netherlands",
            "Australia"
        ],
        default=["United States", "Canada", "United Kingdom"]
    )

    companies_per_combo = st.slider("Companies per industry-country combination", 1, 10, 4)
    num_companies = st.slider("Display top prospects", 5, 100, 30)
    revenue_min = st.slider("Minimum Revenue ($m)", 10, 500, 50)
    score_threshold = st.slider("Minimum Priority Score", 0, 100, 20)

# ===============================
# DATA GENERATION
# ===============================
def generate_data(industries, countries, n_per_combo, selected_services):
    rng = np.random.default_rng(42)

    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Chris", "Sophia", "Daniel", "Olivia"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Anderson", "Clark", "Miller", "Davis", "Hall", "Turner"]
    company_prefix = ["Vertex", "NorthBridge", "Summit", "BluePeak", "Evercore", "WestGate", "IronStone", "Lakeview", "Crestline", "Pioneer"]

    rows = []
    for svc in selected_services:
        for ind in industries:
            for ctry in countries:
                for i in range(n_per_combo):
                    revenue = int(rng.integers(20, 600))
                    ebitda_cap = max(6, int(revenue * 0.28))
                    ebitda = int(rng.integers(5, ebitda_cap))
                    growth = round(float(rng.uniform(0.02, 0.30)), 2)
                    margin = round(ebitda / revenue, 2)

                    leader_first = rng.choice(first_names)
                    leader_last = rng.choice(last_names)
                    leader_name = f"{leader_first} {leader_last}"

                    company_name = f"{rng.choice(company_prefix)} {ind} {i+1}"

                    domain_name = company_name.lower().replace(" ", "").replace("&", "and")

                    if svc == "Sell-Side":
                        rationale = rng.choice([
                            "Founder-owned; likely succession need",
                            "Strong niche positioning; attractive to acquirers",
                            "Margin expansion opportunity",
                            "Potential strategic premium in fragmented market",
                            "Likely seller candidate due to scale inflection",
                            "Could benefit from broader buyer outreach",
                            "Positioned well for a structured sale process"
                        ])
                    else:
                        rationale = rng.choice([
                            "Expansion-oriented platform candidate",
                            "Strong balance sheet for acquisitions",
                            "Likely consolidator in fragmented market",
                            "Strategic buyer fit with adjacency expansion",
                            "Add-on acquisition potential",
                            "Can use M&A to accelerate market entry",
                            "Well-positioned for capability expansion"
                        ])

                    rows.append({
                        "Service Type": svc,
                        "Company": company_name,
                        "Industry": ind,
                        "Country": ctry,
                        "Revenue ($m)": revenue,
                        "EBITDA ($m)": ebitda,
                        "Growth Rate": growth,
                        "EBITDA Margin": margin,
                        "Leader Name": leader_name,
                        "Leader Title": rng.choice(["CEO", "President", "Owner", "Managing Director"]),
                        "Website": f"https://www.{domain_name}.com",
                        "Email": f"info@{domain_name}.com",
                        "Phone": f"+1-555-{int(rng.integers(100,999))}-{int(rng.integers(1000,9999))}",
                        "LinkedIn": f"https://www.linkedin.com/in/{leader_first.lower()}-{leader_last.lower()}",
                        "Description": f"{company_name} is a {ind.lower()} company operating in {ctry} with strategic relevance for {svc.lower()} advisory opportunities.",
                        "Why Selected": rationale
                    })
    return pd.DataFrame(rows)

# ===============================
# BUILD DATASET
# ===============================
if service_type and industry and country:
    df = generate_data(industry, country, companies_per_combo, service_type)

    if not df.empty:
        df = df[df["Revenue ($m)"] >= revenue_min].copy()
else:
    df = pd.DataFrame()

# ===============================
# SCORING
# ===============================
if not df.empty:
    max_revenue = max(df["Revenue ($m)"].max(), 1)

    df["Priority Score"] = (
        35 * df["Growth Rate"] +
        35 * df["EBITDA Margin"] +
        15 * (df["Revenue ($m)"] / max_revenue) +
        15 * np.where(df["Service Type"] == "Buy-Side", 1.00, 0.90)
    ) * 100 / 2

    df["Priority Score"] = df["Priority Score"].round(1)

    df["Recommendation"] = np.where(
        df["Service Type"] == "Buy-Side",
        np.where(df["Priority Score"] >= 50, "High-priority Buy-Side Target", "Monitor / Secondary Buy-Side Target"),
        np.where(df["Priority Score"] >= 50, "High-priority Sell-Side Target", "Monitor / Secondary Sell-Side Target")
    )

    df = df[df["Priority Score"] >= score_threshold].copy()
    df = df.sort_values(["Priority Score", "Revenue ($m)"], ascending=[False, False]).head(num_companies)

# ===============================
# EXPORT HELPERS
# ===============================
def build_excel_bytes(df_export: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Prospects")
    return output.getvalue()

class PDFReport(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "SellSide Group M&A Intelligence Dashboard Report", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, DESIGNED_BY, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

def clean_pdf_text(value, max_len=140):
    if pd.isna(value):
        return ""

    text = str(value)

    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text).strip()

    text = text.replace("https://", "https:// ")
    text = text.replace("http://", "http:// ")
    text = text.replace("www.", "www. ")
    text = text.replace("@", "@ ")

    if len(text) > max_len:
        text = text[: max_len - 3] + "..."

    return text

def build_pdf_bytes(df_export: pd.DataFrame) -> bytes:
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    if df_export.empty:
        pdf.cell(0, 8, "No records available for export.", new_x="LMARGIN", new_y="NEXT")
    else:
        export_reset = df_export.reset_index(drop=True)

        for idx, r in export_reset.iterrows():
            company = clean_pdf_text(r.get("Company", ""), 60)
            service_val = clean_pdf_text(r.get("Service Type", ""), 30)
            industry_val = clean_pdf_text(r.get("Industry", ""), 40)
            country_val = clean_pdf_text(r.get("Country", ""), 30)
            leader = clean_pdf_text(r.get("Leader Name", ""), 40)
            email = clean_pdf_text(r.get("Email", ""), 50)
            phone = clean_pdf_text(r.get("Phone", ""), 25)
            score = clean_pdf_text(r.get("Priority Score", ""), 10)
            recommendation = clean_pdf_text(r.get("Recommendation", ""), 70)
            rationale = clean_pdf_text(r.get("Why Selected", ""), 120)

            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, f"{idx + 1}. {company}")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"Service Type: {service_val}")
            pdf.multi_cell(0, 6, f"Industry: {industry_val}")
            pdf.multi_cell(0, 6, f"Country: {country_val}")
            pdf.multi_cell(0, 6, f"Leader: {leader}")
            pdf.multi_cell(0, 6, f"Email: {email}")
            pdf.multi_cell(0, 6, f"Phone: {phone}")
            pdf.multi_cell(0, 6, f"Priority Score: {score}")
            pdf.multi_cell(0, 6, f"Recommendation: {recommendation}")
            pdf.multi_cell(0, 6, f"Why Selected: {rationale}")
            pdf.ln(2)

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    elif isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1", errors="replace")

    return pdf_bytes

# ===============================
# TABS
# ===============================
tab_guide, tab_overview, tab_prospects, tab_intelligence, tab_charts, tab_exports = st.tabs(
    ["Guide", "Overview", "Prospect List", "Company Intelligence", "Charts", "Exports"]
)

# ===============================
# GUIDE TAB
# ===============================
with tab_guide:
    st.subheader("How to Use This Dashboard")

    st.markdown(
        """
        <div class="guide-box">
        <b>1. Start with the filters in the left sidebar.</b><br>
        Choose the service type, industries, countries, minimum revenue, the number of companies per industry-country combination, and the number of top prospects to display.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>2. Go to the Overview tab.</b><br>
        This tab gives you a quick summary of how many prospects match your filters, the average revenue, average EBITDA margin, and average priority score.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>3. Review the Prospect List tab.</b><br>
        This tab shows the filtered list for both sell-side and buy-side opportunities. You can review company name, industry, country, leadership contact, website, LinkedIn, why the company was selected, and the recommendation.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>4. Use the Company Intelligence tab for deeper analysis.</b><br>
        Select any company from the dropdown to view its profile, strategic rationale, contact details, growth, EBITDA margin, and recommendation.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>5. Use the Charts tab to compare companies visually.</b><br>
        The scatter chart compares revenue and EBITDA while the bar chart highlights the highest-priority targets. These visuals help identify which prospects may deserve more attention.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>6. Use the Exports tab to download your results.</b><br>
        Export the filtered prospect list to Excel or PDF for presentation, review, or sharing.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Recommended Workflow")
    st.write("1. Select service type, industries, and countries")
    st.write("2. Adjust the revenue and priority score filters")
    st.write("3. Review the overview metrics")
    st.write("4. Study the prospect table")
    st.write("5. Select a company for deeper intelligence")
    st.write("6. Review the comparison charts")
    st.write("7. Export the final output to Excel or PDF")

    st.markdown("### What the Priority Score Means")
    st.write(
        "The Priority Score is a simple composite measure that combines growth, profitability, scale, and service-type relevance. A higher score indicates a stronger candidate for immediate outreach or further M&A evaluation."
    )

# ===============================
# OVERVIEW TAB
# ===============================
with tab_overview:
    st.subheader("Overview")

    if df.empty:
        st.warning("No companies match the current filters. Try broadening the industries, countries, or lowering the minimum filters.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Prospects", len(df))
        c2.metric("Avg Revenue ($m)", round(df["Revenue ($m)"].mean(), 1))
        c3.metric("Avg EBITDA Margin", f"{round(df['EBITDA Margin'].mean() * 100, 1)}%")
        c4.metric("Avg Priority Score", round(df["Priority Score"].mean(), 1))

        st.dataframe(
            df[[
                "Company", "Service Type", "Industry", "Country",
                "Revenue ($m)", "EBITDA ($m)", "Growth Rate",
                "EBITDA Margin", "Priority Score", "Recommendation"
            ]],
            use_container_width=True
        )

# ===============================
# PROSPECT LIST TAB
# ===============================
with tab_prospects:
    st.subheader("Prospect List")

    if df.empty:
        st.info("No prospect data available for the selected filters.")
    else:
        display_df = df[[
            "Company", "Service Type", "Industry", "Country",
            "Leader Name", "Leader Title", "Phone", "Email",
            "Website", "LinkedIn", "Description", "Why Selected",
            "Priority Score", "Recommendation"
        ]].copy()

        st.dataframe(display_df, use_container_width=True)

# ===============================
# COMPANY INTELLIGENCE TAB
# ===============================
with tab_intelligence:
    st.subheader("Company Intelligence")

    if df.empty:
        st.info("No companies available to analyze.")
    else:
        selected_company = st.selectbox("Select a company", df["Company"].tolist())
        selected_row = df[df["Company"] == selected_company].iloc[0]

        left, right = st.columns([1.2, 1])

        with left:
            st.markdown(f"### {selected_row['Company']}")
            st.write(f"**Service Type:** {selected_row['Service Type']}")
            st.write(f"**Industry:** {selected_row['Industry']}")
            st.write(f"**Country:** {selected_row['Country']}")
            st.write(f"**Leader:** {selected_row['Leader Name']} ({selected_row['Leader Title']})")
            st.write(f"**Phone:** {selected_row['Phone']}")
            st.markdown(f"**Email:** [{selected_row['Email']}](mailto:{selected_row['Email']})")
            st.markdown(f"**Website:** [{selected_row['Website']}]({selected_row['Website']})")
            st.markdown(f"**LinkedIn:** [Open Profile]({selected_row['LinkedIn']})")
            st.write(f"**Description:** {selected_row['Description']}")

        with right:
            st.metric("Revenue ($m)", selected_row["Revenue ($m)"])
            st.metric("EBITDA ($m)", selected_row["EBITDA ($m)"])
            st.metric("Growth Rate", f"{round(selected_row['Growth Rate'] * 100, 1)}%")
            st.metric("EBITDA Margin", f"{round(selected_row['EBITDA Margin'] * 100, 1)}%")
            st.metric("Priority Score", selected_row["Priority Score"])

        st.markdown("### Strategic Rationale")
        st.write(selected_row["Why Selected"])

        st.markdown("### Recommendation")
        st.success(selected_row["Recommendation"])

        st.markdown("### M&A Guidance")
        if selected_row["Service Type"] == "Sell-Side":
            st.write(
                "This company may benefit from sell-side preparation through stronger financial reporting, a clear equity story, buyer targeting, and pre-sale operational cleanup to improve valuation."
            )
        else:
            st.write(
                "This company may benefit from buy-side preparation through acquisition screening, synergy mapping, disciplined valuation, financing readiness, and integration planning."
            )

# ===============================
# CHARTS TAB
# ===============================
with tab_charts:
    st.subheader("Comparison Charts")

    if df.empty:
        st.info("No chart data available for the selected filters.")
    else:
        scatter_fig = px.scatter(
            df,
            x="Revenue ($m)",
            y="EBITDA ($m)",
            size="Priority Score",
            color="Service Type",
            hover_name="Company",
            title="Revenue vs EBITDA by Company"
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

        top_df = df.sort_values("Priority Score", ascending=False).head(10)
        bar_fig = px.bar(
            top_df,
            x="Priority Score",
            y="Company",
            color="Service Type",
            orientation="h",
            title="Top Prospects by Priority Score"
        )
        bar_fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(bar_fig, use_container_width=True)

# ===============================
# EXPORTS TAB
# ===============================
with tab_exports:
    st.subheader("Export Files")

    if df.empty:
        st.info("No data available to export.")
    else:
        excel_bytes = build_excel_bytes(df)
        pdf_bytes = build_pdf_bytes(df)

        st.download_button(
            "Download Excel",
            data=excel_bytes,
            file_name="sellside_dashboard_prospects.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="sellside_dashboard_report.pdf",
            mime="application/pdf"
        )

        st.markdown(
            "<div class='small-note'>If you change filters, export files will reflect the currently displayed dataset.</div>",
            unsafe_allow_html=True
        )

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown(
    "<div style='text-align:center; font-size:14px;'>Designed and developed by Seth Agyei Aboagye</div>",
    unsafe_allow_html=True
)

