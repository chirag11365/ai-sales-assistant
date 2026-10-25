import streamlit as st, pandas as pd, sqlite3, plotly.express as px
from ai_sql import question_to_sql, is_safe, run_query, explain, generate_insights

st.set_page_config(page_title="Sales Analytics Assistant", layout="wide")

@st.cache_data
def load():
    con = sqlite3.connect("sales.db")
    df = pd.read_sql("SELECT * FROM sales", con)
    df["order_date"] = pd.to_datetime(df["order_date"])
    return df

df = load()
st.title("Sales Analytics Assistant")

# Sidebar filters
regions = sorted(df.region.unique())
cats = sorted(df.category.unique())
sel_regions = st.sidebar.multiselect("Region", regions, default=regions)
sel_cats = st.sidebar.multiselect("Category", cats, default=cats)
d = df[df.region.isin(sel_regions) & df.category.isin(sel_cats)]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${d.sales.sum():,.0f}")
c2.metric("Profit", f"${d.profit.sum():,.0f}")
c3.metric("Profit margin", f"{d.profit.sum() / d.sales.sum() * 100:.1f}%")
c4.metric("Orders", d.order_id.nunique())

# Ask your data (AI)
st.header("Ask your data")
question = st.text_input("Ask a question, e.g. Which sub-category lost the most money?")
if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        try:
            sql = question_to_sql(question)
            st.code(sql, language="sql")
            if not is_safe(sql):
                st.error("Blocked: only read-only SELECT queries are allowed.")
            else:
                res = run_query(sql)
                st.dataframe(res)
                st.write(explain(question, res))
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# Charts
st.header("Dashboard")
left, right = st.columns(2)

by_region = d.groupby("region", as_index=False)["profit"].sum()
left.plotly_chart(px.bar(by_region, x="region", y="profit",
                         title="Profit by region"), width="stretch")

monthly = d.groupby(d["order_date"].dt.to_period("M").astype(str))["sales"].sum().reset_index()
monthly.columns = ["month", "sales"]
right.plotly_chart(px.line(monthly, x="month", y="sales",
                           title="Monthly revenue"), width="stretch")

sub = d.groupby("sub_category", as_index=False)["profit"].sum().sort_values("profit")
left.plotly_chart(px.bar(sub, x="profit", y="sub_category", orientation="h",
                         color="profit", color_continuous_scale="RdYlGn",
                         title="Profit by sub-category"), width="stretch")

disc = d.groupby("discount", as_index=False)["profit"].mean()
right.plotly_chart(px.bar(disc, x="discount", y="profit",
                          title="Average profit by discount level"), width="stretch")

# AI insights
st.header("AI insights")
if st.button("Generate insights"):
    with st.spinner("Analysing..."):
        try:
            reg = d.groupby("region").profit.sum().round(0).to_dict()
            worst = d.groupby("sub_category").profit.sum().round(0).sort_values().head(5).to_dict()
            bands = pd.cut(d.discount, [-0.01, 0.2, 0.4, 1], labels=["0-20%", "21-40%", "over 40%"])
            by_disc = d.groupby(bands, observed=True).profit.mean().round(1)
            by_disc = {str(k): v for k, v in by_disc.items()}
            facts = (f"Revenue {d.sales.sum():,.0f}; profit {d.profit.sum():,.0f}; "
                     f"margin {d.profit.sum() / d.sales.sum() * 100:.1f}%. "
                     f"Profit by region: {reg}. Five weakest sub-categories by profit: {worst}. "
                     f"Average profit per order by discount band: {by_disc}.")
            st.write(generate_insights(facts))
        except Exception as e:
            st.error(f"Something went wrong: {e}")