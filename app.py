import streamlit as st
import pandas as pd
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
# REQUIRED COLUMNS
# ===============================
REQUIRED_COLUMNS = [
    "Service Type",
    "Company",
    "Industry",
    "Country",
    "Website",
    "Email",
    "Phone",
    "LinkedIn",
    "Leader Name",
    "Leader Title",
    "Description",
    "Why Selected",
    "Revenue ($m)",
    "EBITDA ($m)",
    "Growth Rate",
    "EBITDA Margin"
]

OPTIONAL_COLUMNS = [
    "Ownership Type",
    "Valuation Notes",
    "Strategic Notes",
    "Economic Factors",
    "Political Factors",
    "Environmental Factors",
    "Quantitative Notes",
    "Recommendation"
]

# ===============================
# DATA LOADER
# ===============================
@st.cache_data
def load_real_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            "Missing required columns in real_companies.csv: " + ", ".join(missing_cols)
        )

    for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Clean whitespace
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Numeric cleanup
    numeric_cols = ["Revenue ($m)", "EBITDA ($m)", "Growth Rate", "EBITDA Margin"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows missing core values
    df = df.dropna(subset=["Company", "Service Type", "Industry", "Country"])

    # Standardize service type labels
    df["Service Type"] = df["Service Type"].replace({
        "Sellside": "Sell-Side",
        "Sell Side": "Sell-Side",
        "Buyside": "Buy-Side",
        "Buy Side": "Buy-Side"
    })

    # Ensure recommendation exists
    df["Recommendation"] = df["Recommendation"].fillna("").astype(str)

    return df


def safe_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_link(label, url):
    url = safe_text(url)
    if url:
        return f"[{label}]({url})"
    return "Not available"


def safe_mail(email):
    email = safe_text(email)
    if email:
        return f"[{email}](mailto:{email})"
    return "Not available"


# ===============================
# SCORING
# ===============================
def add_priority_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if out.empty:
        out["Priority Score"] = []
        return out

    if out["Revenue ($m)"].notna().any():
        revenue_max = max(out["Revenue ($m)"].max(skipna=True), 1)
    else:
        revenue_max = 1

    growth_component = out["Growth Rate"].fillna(0)
    margin_component = out["EBITDA Margin"].fillna(0)
    revenue_component = out["Revenue ($m)"].fillna(0) / revenue_max
    service_component = out["Service Type"].apply(lambda x: 1.00 if x == "Buy-Side" else 0.90)

    out["Priority Score"] = (
        35 * growth_component +
        35 * margin_component +
        15 * revenue_component +
        15 * service_component
    ) * 100 / 2

    out["Priority Score"] = out["Priority Score"].round(1)

    # Fill recommendation only if blank
    blank_mask = out["Recommendation"].astype(str).str.strip() == ""
    out.loc[blank_mask, "Recommendation"] = out.loc[blank_mask, "Service Type"].apply(
        lambda x: "High-priority Buy-Side Target" if x == "Buy-Side" else "High-priority Sell-Side Target"
    )

    return out


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
        self.cell(0, 10, "SellSide Group M&A Intelligence Dashboard Report", ln=True)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, DESIGNED_BY, ln=True)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
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
    text = text.replace("/", "/ ")
    text = text.replace("_", "_ ")

    if len(text) > max_len:
        text = text[: max_len - 3] + "..."

    return text


def pdf_write_line(pdf, text, width=190, height=6, bold=False):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B" if bold else "", 11 if bold else 10)
    pdf.multi_cell(width, height, text)
    pdf.set_x(pdf.l_margin)


def build_pdf_bytes(df_export: pd.DataFrame) -> bytes:
    pdf = PDFReport(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()

    if df_export.empty:
        pdf_write_line(pdf, "No records available for export.")
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
            website = clean_pdf_text(r.get("Website", ""), 70)
            linkedin = clean_pdf_text(r.get("LinkedIn", ""), 70)
            score = clean_pdf_text(r.get("Priority Score", ""), 10)
            recommendation = clean_pdf_text(r.get("Recommendation", ""), 70)
            rationale = clean_pdf_text(r.get("Why Selected", ""), 120)

            pdf_write_line(pdf, f"{idx + 1}. {company}", bold=True)
            pdf_write_line(pdf, f"Service Type: {service_val}")
            pdf_write_line(pdf, f"Industry: {industry_val}")
            pdf_write_line(pdf, f"Country: {country_val}")
            pdf_write_line(pdf, f"Leader: {leader}")
            pdf_write_line(pdf, f"Email: {email}")
            pdf_write_line(pdf, f"Phone: {phone}")
            pdf_write_line(pdf, f"Website: {website}")
            pdf_write_line(pdf, f"LinkedIn: {linkedin}")
            pdf_write_line(pdf, f"Priority Score: {score}")
            pdf_write_line(pdf, f"Recommendation: {recommendation}")
            pdf_write_line(pdf, f"Why Selected: {rationale}")
            pdf.ln(2)

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    elif isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1", errors="replace")

    return pdf_bytes


# ===============================
# LOAD DATA
# ===============================
try:
    base_df = load_real_data("real_companies.csv")
except FileNotFoundError:
    st.error("File not found: real_companies.csv. Put the file in the same folder as app.py.")
    st.stop()
except Exception as e:
    st.error(f"Could not load real_companies.csv: {e}")
    st.stop()

base_df = add_priority_scores(base_df)

# ===============================
# SIDEBAR FILTERS
# ===============================
with st.sidebar:
    all_service_types = sorted([x for x in base_df["Service Type"].dropna().unique().tolist() if str(x).strip() != ""])
    all_industries = sorted([x for x in base_df["Industry"].dropna().unique().tolist() if str(x).strip() != ""])
    all_countries = sorted([x for x in base_df["Country"].dropna().unique().tolist() if str(x).strip() != ""])

    service_type = st.multiselect(
        "Service Type",
        all_service_types,
        default=all_service_types
    )

    industry = st.multiselect(
        "Industry",
        all_industries,
        default=all_industries
    )

    country = st.multiselect(
        "Country",
        all_countries,
        default=all_countries
    )

    max_revenue_value = int(max(base_df["Revenue ($m)"].fillna(0).max(), 100))
    revenue_min = st.slider("Minimum Revenue ($m)", 0, max_revenue_value, 0)

    score_threshold = st.slider("Minimum Priority Score", 0, 100, 0)

    show_all = st.checkbox("Show all filtered companies", value=False)

    max_display = max(len(base_df), 5)
    default_display = min(30, max_display)
    num_companies = st.slider(
        "Number of companies to display",
        5,
        max_display,
        default_display
    )

# ===============================
# FILTERED DATA
# ===============================
df = base_df.copy()

if service_type:
    df = df[df["Service Type"].isin(service_type)]

if industry:
    df = df[df["Industry"].isin(industry)]

if country:
    df = df[df["Country"].isin(country)]

df = df[df["Revenue ($m)"].fillna(0) >= revenue_min]

if score_threshold > 0:
    df = df[df["Priority Score"].fillna(0) >= score_threshold]

df = df.sort_values(["Priority Score", "Revenue ($m)"], ascending=[False, False])

if not show_all:
    df = df.head(num_companies)

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
        <b>1. Place a verified <code>real_companies.csv</code> file in the same folder as <code>app.py</code>.</b><br>
        The dashboard reads only the real company data you provide in that CSV.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>2. Start with the filters in the left sidebar.</b><br>
        Choose service type, industries, countries, minimum revenue, minimum priority score, and either show all companies or limit the final list to a selected number.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>3. Use the Prospect List tab.</b><br>
        Review company name, leadership, website, email, LinkedIn link, and why each firm was selected.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>4. Use Company Intelligence.</b><br>
        Select a company to see detailed business, contact, and M&A-related information.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>5. Use Charts.</b><br>
        Compare revenue, EBITDA, and priority score visually.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="guide-box">
        <b>6. Use Exports.</b><br>
        Download the currently filtered results to Excel or PDF.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Priority Score")
    st.write(
        "The Priority Score combines growth, profitability, scale, and service-type relevance. It is meant to help rank prospects, not replace analyst judgment."
    )

# ===============================
# OVERVIEW TAB
# ===============================
with tab_overview:
    st.subheader("Overview")

    if df.empty:
        st.warning("No companies match the current filters.")
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Prospects", len(df))
        c2.metric("Avg Revenue ($m)", round(df["Revenue ($m)"].mean(), 1))
        c3.metric("Avg EBITDA Margin", f"{round(df['EBITDA Margin'].mean() * 100, 1)}%")
        c4.metric("Avg Priority Score", round(df["Priority Score"].mean(), 1))
        c5.metric("Buy-Side / Sell-Side", f"{(df['Service Type'] == 'Buy-Side').sum()} / {(df['Service Type'] == 'Sell-Side').sum()}")

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
            st.markdown(f"### {safe_text(selected_row['Company'])}")
            st.write(f"**Service Type:** {safe_text(selected_row['Service Type'])}")
            st.write(f"**Industry:** {safe_text(selected_row['Industry'])}")
            st.write(f"**Country:** {safe_text(selected_row['Country'])}")
            st.write(f"**Leader:** {safe_text(selected_row['Leader Name'])} ({safe_text(selected_row['Leader Title'])})")
            st.write(f"**Phone:** {safe_text(selected_row['Phone']) or 'Not available'}")
            st.markdown(f"**Email:** {safe_mail(selected_row['Email'])}")
            st.markdown(f"**Website:** {safe_link(safe_text(selected_row['Website']) or 'Open Website', selected_row['Website'])}")
            st.markdown(f"**LinkedIn:** {safe_link('Open LinkedIn', selected_row['LinkedIn'])}")
            st.write(f"**Description:** {safe_text(selected_row['Description'])}")

        with right:
            revenue_val = selected_row["Revenue ($m)"]
            ebitda_val = selected_row["EBITDA ($m)"]
            growth_val = selected_row["Growth Rate"]
            margin_val = selected_row["EBITDA Margin"]

            st.metric("Revenue ($m)", "-" if pd.isna(revenue_val) else round(revenue_val, 1))
            st.metric("EBITDA ($m)", "-" if pd.isna(ebitda_val) else round(ebitda_val, 1))
            st.metric("Growth Rate", "-" if pd.isna(growth_val) else f"{round(growth_val * 100, 1)}%")
            st.metric("EBITDA Margin", "-" if pd.isna(margin_val) else f"{round(margin_val * 100, 1)}%")
            st.metric("Priority Score", "-" if pd.isna(selected_row["Priority Score"]) else selected_row["Priority Score"])

        st.markdown("### Strategic Rationale")
        st.write(safe_text(selected_row["Why Selected"]))

        st.markdown("### Recommendation")
        st.success(safe_text(selected_row["Recommendation"]))

        extra_sections = {
            "Strategic Notes": "Strategic Information",
            "Valuation Notes": "Valuation",
            "Economic Factors": "Economic Factors",
            "Political Factors": "Political Factors",
            "Environmental Factors": "Environmental Factors",
            "Quantitative Notes": "Quantitative Factors"
        }

        for col, title in extra_sections.items():
            val = safe_text(selected_row[col])
            if val:
                st.markdown(f"### {title}")
                st.write(val)

# ===============================
# CHARTS TAB
# ===============================
with tab_charts:
    st.subheader("Comparison Charts")

    chart_df = df.dropna(subset=["Revenue ($m)", "Priority Score"])

    if chart_df.empty:
        st.info("No chart data available for the selected filters.")
    else:
        y_column = "EBITDA ($m)" if chart_df["EBITDA ($m)"].notna().any() else "Priority Score"

        scatter_fig = px.scatter(
            chart_df,
            x="Revenue ($m)",
            y=y_column,
            size="Priority Score",
            color="Service Type",
            hover_name="Company",
            title=f"Revenue vs {y_column} by Company"
        )
        st.plotly_chart(scatter_fig, use_container_width=True)

        top_df = chart_df.sort_values("Priority Score", ascending=False)
        if not show_all:
            top_df = top_df.head(min(10, len(top_df)))
        else:
            top_df = top_df.head(min(20, len(top_df)))

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
            "<div class='small-note'>Exports reflect the currently filtered dataset from real_companies.csv.</div>",
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
