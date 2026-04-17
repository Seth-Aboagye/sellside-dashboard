import io
import math
import textwrap
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from fpdf import FPDF


st.set_page_config(
    page_title="SellSide Group M&A Intelligence Dashboard | Seth Agyei Aboagye",
    layout="wide",
    initial_sidebar_state="expanded",
)

DESIGNED_BY = "Designed by Seth Agyei Aboagye"


# =========================================================
# CONFIGURATION
# =========================================================
MD_INDUSTRIES: Dict[str, List[str]] = {
    "David Weiss": ["Specialty Chemicals", "Industrial Supply Distribution"],
    "Kevin D. Hoben": ["Industrial", "Packaging", "Distribution"],
    "Timothy J. Meyer": ["Business Services", "Industrial Services", "Facility Services"],
    "Matthew M. Pritchard": ["Healthcare Services", "Pharma Services", "Medical Products"],
    "Michael J. Weber": ["Technology", "IT Services", "Software", "Tech-Enabled Services"],
    "Adam J. Wasserman": ["Consumer", "Retail", "Food & Beverage", "Consumer Services"],
    "William ""Will"" Matthews": ["Aerospace & Defense", "Government Services", "Industrial"],
}

COUNTRY_MAP: Dict[str, Dict[str, float]] = {
    "United States": {"gdp_growth": 2.3, "inflation": 3.1, "mna_activity": 8.8, "political_risk": 2.4},
    "Canada": {"gdp_growth": 1.8, "inflation": 2.7, "mna_activity": 7.1, "political_risk": 2.1},
    "United Kingdom": {"gdp_growth": 1.1, "inflation": 2.9, "mna_activity": 7.0, "political_risk": 2.7},
    "Germany": {"gdp_growth": 0.9, "inflation": 2.5, "mna_activity": 6.2, "political_risk": 2.2},
    "France": {"gdp_growth": 1.0, "inflation": 2.4, "mna_activity": 6.4, "political_risk": 2.3},
    "Netherlands": {"gdp_growth": 1.4, "inflation": 2.6, "mna_activity": 6.6, "political_risk": 1.9},
    "United Arab Emirates": {"gdp_growth": 3.7, "inflation": 2.1, "mna_activity": 6.8, "political_risk": 2.0},
    "Saudi Arabia": {"gdp_growth": 3.2, "inflation": 1.8, "mna_activity": 6.5, "political_risk": 2.8},
    "India": {"gdp_growth": 6.2, "inflation": 4.9, "mna_activity": 7.9, "political_risk": 3.0},
    "Singapore": {"gdp_growth": 2.6, "inflation": 2.3, "mna_activity": 7.7, "political_risk": 1.7},
    "Australia": {"gdp_growth": 2.1, "inflation": 2.8, "mna_activity": 6.7, "political_risk": 1.8},
    "South Africa": {"gdp_growth": 1.2, "inflation": 5.1, "mna_activity": 5.7, "political_risk": 3.7},
}

INDUSTRY_ATTRACTIVENESS = {
    "Specialty Chemicals": 8.2,
    "Industrial Supply Distribution": 7.8,
    "Industrial": 7.6,
    "Packaging": 7.2,
    "Distribution": 7.5,
    "Business Services": 8.1,
    "Industrial Services": 7.7,
    "Facility Services": 7.0,
    "Healthcare Services": 8.7,
    "Pharma Services": 8.5,
    "Medical Products": 8.0,
    "Technology": 8.8,
    "IT Services": 8.1,
    "Software": 9.1,
    "Tech-Enabled Services": 8.4,
    "Consumer": 7.1,
    "Retail": 6.4,
    "Food & Beverage": 7.3,
    "Consumer Services": 7.0,
    "Aerospace & Defense": 8.0,
    "Government Services": 7.6,
}

FIRST_NAMES = [
    "James", "Olivia", "Liam", "Emma", "Noah", "Ava", "Mason", "Sophia", "Elijah", "Mia",
    "Lucas", "Charlotte", "Amelia", "Benjamin", "Harper", "Ethan", "Abigail", "Henry", "Grace", "Daniel"
]
LAST_NAMES = [
    "Carter", "Brooks", "Murphy", "Turner", "Parker", "Reed", "Bailey", "Price", "Cooper", "Long",
    "Perry", "Bennett", "Howard", "Ward", "Kelly", "Ross", "James", "Powell", "Hughes", "Flores"
]
COMPANY_PREFIX = [
    "Summit", "NorthBridge", "Vertex", "BluePeak", "Cedar", "Atlas", "IronGate", "Nova", "Evercore", "Pioneer",
    "Harbor", "Sterling", "Keystone", "Apex", "Liberty", "Prime", "OakHill", "Mariner", "Signal", "BrightPath"
]
COMPANY_SUFFIX = [
    "Holdings", "Partners", "Group", "Solutions", "Systems", "Services", "Technologies", "Industries", "Distribution", "Labs"
]

DESC_MAP = {
    "Specialty Chemicals": "Produces formulated chemical inputs for industrial and specialty end markets.",
    "Industrial Supply Distribution": "Distributes mission-critical parts, components, and maintenance supplies to industrial buyers.",
    "Industrial": "Manufactures engineered products serving diversified industrial customers.",
    "Packaging": "Provides flexible or rigid packaging products for commercial and consumer applications.",
    "Distribution": "Operates multi-channel distribution networks for business customers.",
    "Business Services": "Offers recurring outsourced services to enterprise and middle-market clients.",
    "Industrial Services": "Provides inspection, maintenance, repair, and technical field services.",
    "Facility Services": "Delivers cleaning, repair, and integrated facility support solutions.",
    "Healthcare Services": "Supports providers, payers, and patients through specialized healthcare services.",
    "Pharma Services": "Offers outsourced solutions across the pharmaceutical value chain.",
    "Medical Products": "Develops and distributes medical devices, supplies, and diagnostics products.",
    "Technology": "Builds digital solutions and products for enterprise transformation.",
    "IT Services": "Provides managed IT, cybersecurity, cloud, and systems integration services.",
    "Software": "Develops software products with recurring revenue and scalable delivery models.",
    "Tech-Enabled Services": "Blends software, data, and services to solve operational challenges.",
    "Consumer": "Serves consumer markets with branded or differentiated products and services.",
    "Retail": "Operates retail platforms across physical, online, or omnichannel models.",
    "Food & Beverage": "Produces branded or private-label food and beverage products.",
    "Consumer Services": "Provides service offerings directly to households and individual customers.",
    "Aerospace & Defense": "Supplies engineered products and services to aerospace and defense customers.",
    "Government Services": "Supports public sector agencies with specialized contracted services.",
}

SERVICE_RATIONALE = {
    "Sell-Side": [
        "Founders may benefit from succession planning and liquidity options.",
        "The company could attract strategic buyers seeking scale, adjacencies, or market expansion.",
        "Margin profile suggests potential valuation uplift if positioned correctly to buyers.",
        "Fragmented industry conditions may support premium valuations from consolidation buyers.",
        "A transaction could help accelerate growth, expand resources, and de-risk ownership concentration.",
    ],
    "Buy-Side": [
        "The company appears positioned to pursue bolt-on acquisitions to expand capabilities or geography.",
        "Cash generation and operating leverage suggest capacity to execute a disciplined acquisition strategy.",
        "A buy-side process could help management identify targets that deepen customer relationships.",
        "The market remains fragmented, creating an opportunity for tuck-ins and platform expansion.",
        "Acquisitions could enhance cross-selling, improve scale economics, and strengthen defensibility.",
    ],
}


# =========================================================
# HELPERS
# =========================================================
def stable_seed(*parts) -> int:
    joined = "|".join(str(p) for p in parts)
    return abs(hash(joined)) % (2**32 - 1)


def make_rng(*parts):
    return np.random.default_rng(stable_seed(*parts))


def company_domain(name: str) -> str:
    cleaned = "".join(ch.lower() for ch in name if ch.isalnum())
    return f"{cleaned}.com"


def person_name(idx: int, rng) -> str:
    first = FIRST_NAMES[idx % len(FIRST_NAMES)]
    last = LAST_NAMES[int(rng.integers(0, len(LAST_NAMES)))]
    return f"{first} {last}"


def linkedin_url(name: str, company: str) -> str:
    handle = name.lower().replace(" ", "-") + "-" + company.lower().replace(" ", "-")[:18]
    return f"https://www.linkedin.com/in/{handle}"


def phone_number(country: str, rng) -> str:
    code_map = {
        "United States": "+1", "Canada": "+1", "United Kingdom": "+44", "Germany": "+49",
        "France": "+33", "Netherlands": "+31", "United Arab Emirates": "+971", "Saudi Arabia": "+966",
        "India": "+91", "Singapore": "+65", "Australia": "+61", "South Africa": "+27",
    }
    code = code_map.get(country, "+1")
    nums = [str(int(rng.integers(1, 9)))] + [str(int(rng.integers(0, 10))) for _ in range(9)]
    return f"{code} {''.join(nums[:3])}-{''.join(nums[3:6])}-{''.join(nums[6:])}"


def normalize_score(series: pd.Series) -> pd.Series:
    min_v, max_v = series.min(), series.max()
    if math.isclose(max_v, min_v):
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - min_v) / (max_v - min_v) * 100).round(2)


def build_company_name(industry: str, i: int, rng) -> str:
    p = COMPANY_PREFIX[i % len(COMPANY_PREFIX)]
    s = COMPANY_SUFFIX[int(rng.integers(0, len(COMPANY_SUFFIX)))]
    ind_word = industry.split()[0]
    return f"{p} {ind_word} {s}"


def owner_title(rng) -> str:
    return rng.choice(["CEO", "President", "Owner", "Founder & CEO", "Managing Director"])


def get_country_macro(country: str) -> Dict[str, float]:
    return COUNTRY_MAP.get(country, {"gdp_growth": 2.0, "inflation": 3.0, "mna_activity": 6.5, "political_risk": 2.5})


def generate_company_record(industry: str, country: str, service_type: str, i: int) -> dict:
    rng = make_rng(industry, country, service_type, i)
    company = build_company_name(industry, i, rng)
    domain = company_domain(company)
    leader = person_name(i, rng)
    leader_title = owner_title(rng)
    has_direct_email = rng.random() > 0.35
    has_direct_phone = rng.random() > 0.22

    base_rev = {
        "Technology": 180, "Software": 140, "Healthcare Services": 160, "Industrial": 210,
        "Specialty Chemicals": 190, "Business Services": 130, "Aerospace & Defense": 240,
    }.get(industry, 120)

    revenue = float(max(20, rng.normal(base_rev, base_rev * 0.35)))
    ebitda_margin = float(np.clip(rng.normal(0.17 if service_type == "Buy-Side" else 0.14, 0.05), 0.05, 0.35))
    growth = float(np.clip(rng.normal(0.12 if service_type == "Buy-Side" else 0.06, 0.08), -0.08, 0.35))
    debt_to_ebitda = float(np.clip(rng.normal(2.2 if service_type == "Buy-Side" else 3.0, 0.8), 0.2, 6.0))
    recurring_revenue = float(np.clip(rng.normal(0.52, 0.2), 0.05, 0.95))
    employee_count = int(max(40, rng.normal(revenue * 6, revenue * 1.8)))
    customer_concentration = float(np.clip(rng.normal(0.22, 0.1), 0.05, 0.65))
    export_exposure = float(np.clip(rng.normal(0.18, 0.14), 0.0, 0.80))
    esg_score = float(np.clip(rng.normal(67, 12), 35, 95))
    digital_maturity = float(np.clip(rng.normal(62, 14), 20, 95))

    macro = get_country_macro(country)
    ebitda = revenue * ebitda_margin
    industry_attr = INDUSTRY_ATTRACTIVENESS.get(industry, 7.0)
    description = DESC_MAP.get(industry, "Operates in a niche middle-market segment with differentiated capabilities.")
    rationale = rng.choice(SERVICE_RATIONALE[service_type])

    # Derived metrics used in scoring
    scale_score_raw = revenue
    profitability_raw = ebitda_margin * 100
    growth_raw = growth * 100
    balance_sheet_raw = max(0.0, 6 - debt_to_ebitda) * 16.67
    strategic_fit_raw = industry_attr * 10 + digital_maturity * 0.15
    macro_score_raw = (macro["gdp_growth"] * 10) + (macro["mna_activity"] * 8) - (macro["political_risk"] * 10) - (macro["inflation"] * 4)

    return {
        "Company": company,
        "Website": f"https://www.{domain}",
        "Country": country,
        "Industry": industry,
        "Service Type": service_type,
        "Leader Name": leader,
        "Leader Title": leader_title,
        "Phone": phone_number(country, rng) if has_direct_phone else "Not publicly listed",
        "Email": f"{leader.split()[0].lower()}.{leader.split()[1].lower()}@{domain}" if has_direct_email else f"info@{domain}",
        "LinkedIn": linkedin_url(leader, company),
        "Description": description,
        "Why Selected": rationale,
        "Revenue ($M)": round(revenue, 1),
        "EBITDA ($M)": round(ebitda, 1),
        "EBITDA Margin %": round(ebitda_margin * 100, 1),
        "3Y Revenue CAGR %": round(growth * 100, 1),
        "Debt / EBITDA": round(debt_to_ebitda, 2),
        "Recurring Revenue %": round(recurring_revenue * 100, 1),
        "Employees": employee_count,
        "Customer Concentration %": round(customer_concentration * 100, 1),
        "Export Exposure %": round(export_exposure * 100, 1),
        "ESG Score": round(esg_score, 1),
        "Digital Maturity": round(digital_maturity, 1),
        "Industry Attractiveness": industry_attr,
        "GDP Growth %": macro["gdp_growth"],
        "Inflation %": macro["inflation"],
        "M&A Activity Index": macro["mna_activity"],
        "Political Risk": macro["political_risk"],
        "Scale Score Raw": scale_score_raw,
        "Profitability Raw": profitability_raw,
        "Growth Raw": growth_raw,
        "Balance Sheet Raw": balance_sheet_raw,
        "Strategic Fit Raw": strategic_fit_raw,
        "Macro Score Raw": macro_score_raw,
    }


def generate_company_universe(industries: List[str], countries: List[str], per_combo: int, service_type: str) -> pd.DataFrame:
    rows = []
    for ind in industries:
        for country in countries:
            for i in range(per_combo):
                rows.append(generate_company_record(ind, country, service_type, i + 1))
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["Scale Score"] = normalize_score(df["Scale Score Raw"])
    df["Profitability Score"] = normalize_score(df["Profitability Raw"])
    df["Growth Score"] = normalize_score(df["Growth Raw"])
    df["Balance Sheet Score"] = normalize_score(df["Balance Sheet Raw"])
    df["Strategic Fit Score"] = normalize_score(df["Strategic Fit Raw"])
    df["Macro Score"] = normalize_score(df["Macro Score Raw"])

    if service_type == "Sell-Side":
        df["Priority Score"] = (
            0.18 * df["Scale Score"]
            + 0.20 * df["Profitability Score"]
            + 0.10 * (100 - df["Growth Score"])
            + 0.18 * df["Strategic Fit Score"]
            + 0.12 * df["Macro Score"]
            + 0.12 * (100 - df["Balance Sheet Score"])
            + 0.10 * normalize_score(df["Customer Concentration %"])
        ).round(2)
        df["Recommendation"] = np.where(
            df["Priority Score"] >= df["Priority Score"].quantile(0.80),
            "High-priority sell-side outreach",
            np.where(df["Priority Score"] >= df["Priority Score"].quantile(0.50), "Monitor / warm outreach", "Lower near-term priority"),
        )
    else:
        df["Priority Score"] = (
            0.20 * df["Scale Score"]
            + 0.16 * df["Profitability Score"]
            + 0.18 * df["Growth Score"]
            + 0.14 * df["Balance Sheet Score"]
            + 0.16 * df["Strategic Fit Score"]
            + 0.10 * df["Macro Score"]
            + 0.06 * normalize_score(df["Recurring Revenue %"])
        ).round(2)
        df["Recommendation"] = np.where(
            df["Priority Score"] >= df["Priority Score"].quantile(0.80),
            "High-priority buy-side prospect",
            np.where(df["Priority Score"] >= df["Priority Score"].quantile(0.50), "Monitor / selective outreach", "Lower near-term priority"),
        )

    df = df.sort_values(["Priority Score", "Revenue ($M)"], ascending=[False, False]).reset_index(drop=True)
    return df


def analyze_company_context(row: pd.Series, service_type: str) -> pd.DataFrame:
    industry = row["Industry"]
    country = row["Country"]

    if service_type == "Sell-Side":
        rec = (
            "Position the business around differentiated capabilities, recurring customers, growth adjacency, and buyer synergies. "
            "Tighten KPI reporting, build a clean data room, and prepare a seller narrative focused on value creation and downside protection."
        )
        value_get = (
            "Sell-side value may come from broader buyer coverage, sharper positioning, faster competitive tension, valuation support, "
            "and deal execution discipline that improves certainty and outcome quality."
        )
    else:
        rec = (
            "Clarify acquisition criteria, integration priorities, and synergy targets. Build an acquisition scorecard, financing plan, "
            "and post-close integration roadmap before launching outreach."
        )
        value_get = (
            "Buy-side value may come from a more focused target universe, better screening discipline, valuation guardrails, "
            "and transaction support that improves fit and reduces execution risk."
        )

    bullets = {
        "Service Value": value_get,
        "Industry Information": f"{industry} remains relevant due to consolidation potential, customer specialization, and operational improvement opportunities.",
        "Internal Information": f"Current EBITDA margin is {row['EBITDA Margin %']}%, recurring revenue is {row['Recurring Revenue %']}%, and digital maturity is {row['Digital Maturity']}.",
        "Strategic Information": f"The company operates in {country}, where the M&A activity index is {row['M&A Activity Index']} and GDP growth is {row['GDP Growth %']}%.",
        "Valuation Lens": f"Illustrative valuation considerations include scale, margin profile, customer concentration ({row['Customer Concentration %']}%), and debt leverage ({row['Debt / EBITDA']}x).",
        "Economic Factors": f"Macro conditions include inflation of {row['Inflation %']}% and GDP growth of {row['GDP Growth %']}%.",
        "Political Factors": f"Political risk for the country is modeled at {row['Political Risk']} on an internal low-to-high scale.",
        "Environmental Factors": f"ESG score is {row['ESG Score']}, which can influence buyer perception, diligence, and exit optionality.",
        "Quantitative Factors": f"Revenue is ${row['Revenue ($M)']}M, EBITDA is ${row['EBITDA ($M)']}M, and 3Y revenue CAGR is {row['3Y Revenue CAGR %']}%.",
        "M&A Recommendation": rec,
    }
    return pd.DataFrame({"Dimension": list(bullets.keys()), "Insight": list(bullets.values())})


def build_excel_bytes(dataframes: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
            ws = writer.sheets[safe_name]
            for idx, col in enumerate(df.columns, 1):
                max_len = max(len(str(col)), *(len(str(v)) for v in df[col].head(100).tolist()))
                ws.column_dimensions[chr(64 + idx) if idx <= 26 else 'A'].width = min(max(max_len + 2, 12), 32)
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

    def chapter_title(self, txt):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, txt, ln=True)
        self.ln(1)

    def chapter_body(self, body):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, body)
        self.ln(1)

    def add_df_preview(self, title: str, df: pd.DataFrame, max_rows: int = 8):
        self.chapter_title(title)
        preview = df.head(max_rows).copy()
        cols = list(preview.columns[:6])
        preview = preview[cols]
        for _, row in preview.iterrows():
            text = " | ".join(f"{c}: {row[c]}" for c in cols)
            self.chapter_body(textwrap.shorten(text, width=180, placeholder="..."))


def build_pdf_bytes(summary_text: str, sell_df: pd.DataFrame, buy_df: pd.DataFrame, detail_df: pd.DataFrame) -> bytes:
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(summary_text)
    if not sell_df.empty:
        pdf.add_df_preview("Top Sell-Side Prospects", sell_df)
    if not buy_df.empty:
        pdf.add_df_preview("Top Buy-Side Prospects", buy_df)
    if not detail_df.empty:
        pdf.add_df_preview("Selected Company Analysis", detail_df)
    return bytes(pdf.output(dest="S"))


def make_summary(sell_df: pd.DataFrame, buy_df: pd.DataFrame) -> str:
    parts = []
    if not sell_df.empty:
        top_sell = sell_df.iloc[0]
        parts.append(
            f"Top sell-side priority is {top_sell['Company']} in {top_sell['Industry']} ({top_sell['Country']}), with a priority score of {top_sell['Priority Score']}."
        )
    if not buy_df.empty:
        top_buy = buy_df.iloc[0]
        parts.append(
            f"Top buy-side priority is {top_buy['Company']} in {top_buy['Industry']} ({top_buy['Country']}), with a priority score of {top_buy['Priority Score']}."
        )
    parts.append(
        "Recommendations are based on a composite of scale, profitability, growth, strategic fit, macro environment, and service-specific readiness indicators."
    )
    return " ".join(parts)


def render_metric_row(df: pd.DataFrame, label: str):
    if df.empty:
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{label} Prospects", f"{len(df):,}")
    c2.metric("Average Revenue ($M)", f"{df['Revenue ($M)'].mean():.1f}")
    c3.metric("Average EBITDA Margin", f"{df['EBITDA Margin %'].mean():.1f}%")
    c4.metric("Average Priority Score", f"{df['Priority Score'].mean():.1f}")


def scatter_chart(df: pd.DataFrame, title: str):
    if df.empty:
        st.info("No data available for this view.")
        return
    fig = px.scatter(
        df,
        x="Revenue ($M)",
        y="EBITDA Margin %",
        color="Country",
        size="Priority Score",
        hover_name="Company",
        hover_data=["Industry", "Leader Name", "Recommendation"],
        title=title,
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def bar_priority_chart(df: pd.DataFrame, title: str):
    if df.empty:
        return
    top_df = df.head(10).sort_values("Priority Score")
    fig = px.bar(
        top_df,
        x="Priority Score",
        y="Company",
        color="Industry",
        orientation="h",
        title=title,
        hover_data=["Country", "Leader Name", "Revenue ($M)"]
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


def radar_chart(row: pd.Series, title: str):
    metrics = ["Scale Score", "Profitability Score", "Growth Score", "Balance Sheet Score", "Strategic Fit Score", "Macro Score"]
    vals = [row[m] for m in metrics]
    vals += vals[:1]
    labels = metrics + metrics[:1]
    fig = go.Figure(
        data=go.Scatterpolar(r=vals, theta=labels, fill="toself", name=row["Company"])
    )
    fig.update_layout(title=title, polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=500)
    st.plotly_chart(fig, use_container_width=True)


def comparison_chart(df: pd.DataFrame):
    if df.empty:
        return
    metrics = ["Revenue ($M)", "EBITDA Margin %", "3Y Revenue CAGR %", "Recurring Revenue %", "Priority Score"]
    options = st.multiselect("Comparison metrics", metrics, default=["Revenue ($M)", "Priority Score"])
    compare_companies = st.multiselect("Select companies to compare", df["Company"].tolist(), default=df["Company"].head(min(5, len(df))).tolist())
    if options and compare_companies:
        comp = df[df["Company"].isin(compare_companies)][["Company"] + options].set_index("Company")
        fig = go.Figure()
        for metric in options:
            fig.add_trace(go.Bar(name=metric, x=comp.index.tolist(), y=comp[metric].tolist()))
        fig.update_layout(barmode="group", title="Selected Company Comparison", height=520)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comp.reset_index(), use_container_width=True)


def show_data_table(df: pd.DataFrame, key: str):
    if df.empty:
        st.warning("No records found. Increase countries, industries, or number of companies.")
        return
    columns_to_show = [
        "Company", "Website", "Country", "Industry", "Leader Name", "Leader Title", "Phone",
        "Email", "LinkedIn", "Description", "Why Selected", "Revenue ($M)", "EBITDA ($M)",
        "EBITDA Margin %", "3Y Revenue CAGR %", "Priority Score", "Recommendation"
    ]
    search = st.text_input(f"Search within {key}", key=f"search_{key}")
    filtered = df.copy()
    if search:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False))
        filtered = filtered[mask.any(axis=1)]
    st.dataframe(filtered[columns_to_show], use_container_width=True, hide_index=True)


def service_recommendation_text(df: pd.DataFrame, service_type: str) -> str:
    if df.empty:
        return "No recommendations available."
    top = df.head(3)
    names = ", ".join(top["Company"].tolist())
    if service_type == "Sell-Side":
        return (
            f"Focus sell-side outreach on {names}. These companies rank highest on positioning fit, profitability, and readiness for a well-run sale process. "
            f"For each, build a concise equity story, prepare diligence materials early, reduce customer concentration where possible, and frame strategic buyer synergies clearly."
        )
    return (
        f"Focus buy-side outreach on {names}. These companies rank highest on scale, growth, strategic fit, and balance sheet capacity. "
        f"For each, define acquisition criteria, synergy logic, valuation guardrails, and integration priorities before engaging targets."
    )


# =========================================================
# UI
# =========================================================
st.title("SellSide Group M&A Intelligence Dashboard")
st.caption(
    "Dynamic prospecting, company intelligence, prioritization, comparison, and export workflow for buy-side and sell-side coverage."
)
st.markdown(
    """
    <div style="
        background-color:#eef4fb;
        padding:10px 14px;
        border-radius:8px;
        font-weight:600;
        margin-bottom:12px;">
        Designed by Seth Agyei Aboagye
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Dashboard Controls")
    st.markdown(f"**{DESIGNED_BY}**")
    md_choice = st.multiselect("Managing Director(s)", list(MD_INDUSTRIES.keys()), default=list(MD_INDUSTRIES.keys())[:3])

    md_industries = sorted({industry for md in md_choice for industry in MD_INDUSTRIES.get(md, [])})
    selected_industries = st.multiselect("Industries", sorted(set(INDUSTRY_ATTRACTIVENESS.keys())), default=md_industries[: min(5, len(md_industries))] if md_industries else list(INDUSTRY_ATTRACTIVENESS.keys())[:4])

    selected_countries = st.multiselect("Countries", list(COUNTRY_MAP.keys()), default=["United States", "Canada", "United Kingdom"])
    per_combo = st.slider("Companies per industry-country combination", 1, 15, 4)
    top_n = st.slider("Display top prospects", 5, 100, 30)
    include_sell = st.checkbox("Build Sell-Side List", value=True)
    include_buy = st.checkbox("Build Buy-Side List", value=True)

if not selected_industries or not selected_countries or (not include_sell and not include_buy):
    st.warning("Select at least one industry, one country, and one service type.")
    st.stop()

sell_df = generate_company_universe(selected_industries, selected_countries, per_combo, "Sell-Side").head(top_n) if include_sell else pd.DataFrame()
buy_df = generate_company_universe(selected_industries, selected_countries, per_combo, "Buy-Side").head(top_n) if include_buy else pd.DataFrame()

summary_text = make_summary(sell_df, buy_df)

st.markdown("### Executive Summary")
st.write(summary_text)

main_tabs = st.tabs([
    "Prospect Lists",
    "Charts & Comparison",
    "Company Intelligence",
    "Recommendations",
    "Exports",
    "Methodology",
])

with main_tabs[0]:
    if include_sell:
        st.subheader("Sell-Side Prospect List")
        render_metric_row(sell_df, "Sell-Side")
        show_data_table(sell_df, "sell_side")
    if include_buy:
        st.subheader("Buy-Side Prospect List")
        render_metric_row(buy_df, "Buy-Side")
        show_data_table(buy_df, "buy_side")

with main_tabs[1]:
    chart_tabs = st.tabs(["Sell-Side Charts", "Buy-Side Charts", "Cross-Company Comparison"])
    with chart_tabs[0]:
        if include_sell:
            scatter_chart(sell_df, "Sell-Side: Revenue vs EBITDA Margin")
            bar_priority_chart(sell_df, "Top Sell-Side Priority Scores")
        else:
            st.info("Sell-side list not enabled.")
    with chart_tabs[1]:
        if include_buy:
            scatter_chart(buy_df, "Buy-Side: Revenue vs EBITDA Margin")
            bar_priority_chart(buy_df, "Top Buy-Side Priority Scores")
        else:
            st.info("Buy-side list not enabled.")
    with chart_tabs[2]:
        comparison_source = sell_df if not sell_df.empty else buy_df
        comparison_chart(comparison_source)

with main_tabs[2]:
    detail_source_name = st.radio("Select list for company deep dive", [x for x in ["Sell-Side", "Buy-Side"] if (x == "Sell-Side" and not sell_df.empty) or (x == "Buy-Side" and not buy_df.empty)], horizontal=True)
    detail_source = sell_df if detail_source_name == "Sell-Side" else buy_df
    selected_company = st.selectbox("Select a company", detail_source["Company"].tolist())
    selected_row = detail_source[detail_source["Company"] == selected_company].iloc[0]

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.subheader(selected_row["Company"])
        st.markdown(f"**Website:** [{selected_row['Website']}]({selected_row['Website']})")
        st.write(f"**Primary Contact:** {selected_row['Leader Name']} ({selected_row['Leader Title']})")
        st.write(f"**Phone:** {selected_row['Phone']}")
        st.markdown(f"**Email:** [{selected_row['Email']}](mailto:{selected_row['Email']})")
        st.markdown(f"**LinkedIn:** [Open Profile]({selected_row['LinkedIn']})")
        st.write(f"**Description:** {selected_row['Description']}")
        st.write(f"**Why selected:** {selected_row['Why Selected']}")

        analysis_df = analyze_company_context(selected_row, detail_source_name)
        st.subheader("Detailed Analysis")
        st.dataframe(analysis_df, use_container_width=True, hide_index=True)
    with c2:
        radar_chart(selected_row, f"{selected_company} Score Profile")

with main_tabs[3]:
    if include_sell:
        st.subheader("Sell-Side Recommendation")
        st.write(service_recommendation_text(sell_df, "Sell-Side"))
        st.dataframe(sell_df[["Company", "Industry", "Country", "Priority Score", "Recommendation"]].head(10), use_container_width=True, hide_index=True)
    if include_buy:
        st.subheader("Buy-Side Recommendation")
        st.write(service_recommendation_text(buy_df, "Buy-Side"))
        st.dataframe(buy_df[["Company", "Industry", "Country", "Priority Score", "Recommendation"]].head(10), use_container_width=True, hide_index=True)

with main_tabs[4]:
    st.subheader("Export Reports")
    detail_analysis_df = analyze_company_context(selected_row, detail_source_name)
    export_book = {}
    if include_sell:
        export_book["Sell-Side Prospects"] = sell_df
    if include_buy:
        export_book["Buy-Side Prospects"] = buy_df
    export_book["Selected Company Analysis"] = detail_analysis_df
    excel_bytes = build_excel_bytes(export_book)
    pdf_bytes = build_pdf_bytes(summary_text, sell_df, buy_df, detail_analysis_df)

    st.download_button(
        "Download Excel Workbook",
        data=excel_bytes,
        file_name="sellside_group_dashboard_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        "Download PDF Report",
        data=pdf_bytes,
        file_name="sellside_group_dashboard_report.pdf",
        mime="application/pdf",
    )

with main_tabs[5]:
    st.subheader("How the scoring works")
    st.markdown(
        """
        **Sell-Side Priority Score** emphasizes:
        - scale
        - profitability
        - strategic fit
        - macro attractiveness
        - some urgency indicators such as slower growth or greater owner-risk style characteristics

        **Buy-Side Priority Score** emphasizes:
        - scale
        - growth
        - profitability
        - balance sheet capacity
        - strategic fit
        - recurring revenue and macro support

        **Important note:** This version is structured to help you present an investment-banking style workflow. It uses synthetic data generation so the dashboard works immediately. To make it live, connect the fetch layer to APIs such as Apollo, Crunchbase, Clearbit, SEC/Companies House, World Bank, and Yahoo Finance.
        """
    )

    st.subheader("Suggested API upgrades")
    st.code(
        """
# Suggested production data sources
# 1. Apollo / Clearbit / Crunchbase -> company and executive data
# 2. Yahoo Finance / Alpha Vantage -> market and valuation data
# 3. World Bank / IMF / OECD -> macro data
# 4. SEC EDGAR / Companies House -> filings and ownership
# 5. News API / GDELT -> strategic and market developments
        """,
        language="python",
    )



st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 14px;'>Designed and developed by Seth Agyei Aboagye</div>",
    unsafe_allow_html=True
)

