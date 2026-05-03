import streamlit as st
import pandas as pd
import plotly.express as px

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Amazon Reviews Dashboard", layout="wide")

# ─────────────────────────────────────────────
# ANALYTICAL QUESTION
# ─────────────────────────────────────────────
st.title("📦 Amazon Product Reviews Analysis")
st.subheader("What drives positive and negative customer reviews, and how does helpfulness relate to rating?")
st.markdown("---")

# ─────────────────────────────────────────────
# DATA LOADING & CLEANING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    # Load directly from GitHub raw URL so it works on Streamlit Cloud
    url = "https://raw.githubusercontent.com/TechTitan2/Amazon-Reviews-Streamlit/main/sample.reviews.xlsx"
    df = pd.read_excel(url, sheet_name="Reviews")

    # Convert Unix timestamp to datetime
    df["Date"] = pd.to_datetime(df["Time"], unit="s")
    df["Year"] = df["Date"].dt.year

    # Calculate helpfulness ratio (avoid division by zero)
    df["HelpfulnessRatio"] = df.apply(
        lambda row: row["HelpfulnessNumerator"] / row["HelpfulnessDenominator"]
        if row["HelpfulnessDenominator"] > 0 else None,
        axis=1
    )

    # Classify sentiment based on score
    df["Sentiment"] = df["Score"].apply(
        lambda x: "Positive" if x >= 4 else ("Neutral" if x == 3 else "Negative")
    )

    return df

df = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Filter 1: Star rating multiselect
score_filter = st.sidebar.multiselect(
    "Star Rating",
    options=sorted(df["Score"].unique()),
    default=sorted(df["Score"].unique())
)

# Filter 2: Sentiment filter
sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=df["Sentiment"].unique().tolist(),
    default=df["Sentiment"].unique().tolist()
)

# Filter 3: Year range slider
min_year = int(df["Year"].min())
max_year = int(df["Year"].max())
year_range = st.sidebar.slider(
    "Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Apply all filters
df_filtered = df[
    (df["Score"].isin(score_filter)) &
    (df["Sentiment"].isin(sentiment_filter)) &
    (df["Year"] >= year_range[0]) &
    (df["Year"] <= year_range[1])
]

# ─────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────
total_reviews = len(df_filtered)
avg_rating = df_filtered["Score"].mean() if total_reviews > 0 else 0
pct_positive = (
    (df_filtered["Sentiment"] == "Positive").sum() / total_reviews * 100
    if total_reviews > 0 else 0
)
avg_helpfulness = df_filtered["HelpfulnessRatio"].dropna().mean() if total_reviews > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reviews", f"{total_reviews:,}")
col2.metric("Avg Star Rating", f"{avg_rating:.2f} ⭐")
col3.metric("Positive Reviews", f"{pct_positive:.1f}%")
col4.metric("Avg Helpfulness Score", f"{avg_helpfulness:.1%}" if avg_helpfulness else "N/A")

st.markdown("---")

# ─────────────────────────────────────────────
# VISUALIZATIONS
# ─────────────────────────────────────────────

# Chart 1: Bar chart — Rating distribution
st.subheader("⭐ Rating Distribution")
rating_counts = df_filtered["Score"].value_counts().sort_index().reset_index()
rating_counts.columns = ["Star Rating", "Count"]
fig1 = px.bar(
    rating_counts,
    x="Star Rating",
    y="Count",
    title="Number of Reviews by Star Rating",
    color="Star Rating",
    color_continuous_scale="RdYlGn",
    labels={"Star Rating": "Star Rating (1-5)", "Count": "Number of Reviews"}
)
fig1.update_layout(showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# Chart 2: Line chart — Reviews over time
st.subheader("📅 Review Volume Over Time")
reviews_by_year = df_filtered.groupby("Year").size().reset_index(name="Review Count")
fig2 = px.line(
    reviews_by_year,
    x="Year",
    y="Review Count",
    title="Number of Reviews Per Year",
    markers=True,
    labels={"Year": "Year", "Review Count": "Number of Reviews"}
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Chart 3: Scatter plot — Helpfulness ratio vs. Star rating
st.subheader("🤝 Helpfulness vs. Star Rating")
df_scatter = df_filtered.dropna(subset=["HelpfulnessRatio"])
fig3 = px.scatter(
    df_scatter,
    x="Score",
    y="HelpfulnessRatio",
    color="Sentiment",
    title="Review Helpfulness Ratio vs. Star Rating",
    labels={
        "Score": "Star Rating",
        "HelpfulnessRatio": "Helpfulness Ratio (helpful votes / total votes)",
        "Sentiment": "Sentiment"
    },
    color_discrete_map={"Positive": "green", "Neutral": "orange", "Negative": "red"},
    opacity=0.6
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────
# KEY FINDINGS
# ─────────────────────────────────────────────
st.subheader("📌 Key Findings")
st.markdown("""
- **Positive reviews dominate the dataset**, with 4- and 5-star ratings making up the majority of all reviews. This suggests that customers who bother to leave reviews tend to be satisfied, which may skew aggregate ratings upward and not fully represent the broader customer base.

- **Review volume has grown significantly over time**, reflecting the broader rise of e-commerce and online purchasing behavior. This trend indicates that more customers are relying on peer reviews to make purchasing decisions, making review quality increasingly important for sellers.

- **Higher-rated reviews tend to receive more helpful votes**, suggesting that positive, well-written reviews are more likely to be upvoted by other customers. Negative reviews, while fewer in number, often show high helpfulness ratios — indicating readers find critical feedback particularly useful when evaluating a product.
""")

st.markdown("---")

# ─────────────────────────────────────────────
# OPTIONAL: RAW DATA TABLE + DOWNLOAD BUTTON
# ─────────────────────────────────────────────
with st.expander("🔎 View Filtered Raw Data"):
    st.dataframe(df_filtered[["Id", "Score", "Sentiment", "Date", "HelpfulnessRatio", "Summary"]].reset_index(drop=True))

    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_reviews.csv",
        mime="text/csv"
    )
