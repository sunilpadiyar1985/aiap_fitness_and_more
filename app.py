import streamlit as st
import pandas as pd

st.set_page_config(page_title="Steps League – Monthly Results", page_icon="🏃", layout="centered")

# ----------------------------
# CONFIG
# ----------------------------
SHEET_ID = "1DfUJd33T-12UVOavd6SqCfkcNl8_4sVxcqqXHtBeWpw"
GID = "0"  # change later for other year tabs

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.strip()

    user_col = df.columns[0]

    df_long = df.melt(
        id_vars=[user_col],
        var_name="date",
        value_name="steps"
    )

    df_long = df_long.rename(columns={user_col: "User"})

    df_long["date"] = pd.to_datetime(df_long["date"], format="%d-%b-%y", errors="coerce")
    df_long["steps"] = pd.to_numeric(df_long["steps"], errors="coerce").fillna(0)

    df_long = df_long.dropna(subset=["date"])
    df_long["month"] = df_long["date"].dt.to_period("M")

    return df_long


df = load_data()

st.title("🏃 Steps League – Monthly Results")

# ----------------------------
# MONTH SELECTOR
# ----------------------------
months = sorted(df["month"].unique())
latest_month = months[-1]

selected_month = st.selectbox(
    "Select month",
    options=months,
    index=len(months) - 1,
    format_func=lambda x: x.strftime("%B %Y")
)

month_df = df[df["month"] == selected_month]

# ----------------------------
# AGGREGATE
# ----------------------------
monthly_totals = (
    month_df.groupby("User")["steps"]
    .sum()
    .reset_index()
    .sort_values("steps", ascending=False)
)

st.subheader(f"Results for {selected_month.strftime('%B %Y')} ⭐")

# ----------------------------
# PODIUM
# ----------------------------
top3 = monthly_totals.head(3)

if len(top3) > 0:
    col1, col2, col3 = st.columns(3)

    medals = ["🥇", "🥈", "🥉"]
    cols = [col1, col2, col3]

    for i in range(min(3, len(top3))):
        cols[i].metric(
            f"{medals[i]} {top3.iloc[i]['User']}",
            f"{int(top3.iloc[i]['steps']):,} steps"
        )

st.divider()

# ----------------------------
# FULL LEADERBOARD
# ----------------------------
st.subheader("📊 Monthly leaderboard")

st.bar_chart(
    monthly_totals.set_index("User")["steps"]
)

st.dataframe(monthly_totals, use_container_width=True)
