import streamlit as st
import pandas as pd
import plotly.express as px

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
    .reset_index(drop=True)
)

# Add proper Rank starting from 1
monthly_totals.insert(0, "Rank", range(1, len(monthly_totals) + 1))

st.markdown(f"### Results for {selected_month.strftime('%B %Y')} ⭐")

# ----------------------------
# PODIUM (winner-style layout)
# ----------------------------
top3 = monthly_totals.head(3).reset_index(drop=True)

if len(top3) >= 1:
    st.markdown("#### 🏆 This month's podium")

    c1, c2, c3 = st.columns([1, 1.4, 1])

    # 🥈 SECOND (slightly lower)
    if len(top3) >= 2:
        with c1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("### 🥈 " + top3.loc[1, "User"])
            st.markdown(f"#### {int(top3.loc[1, 'steps']):,} steps")

    # 🥇 FIRST (highest, most prominent)
    with c2:
        st.markdown("## 🥇 " + top3.loc[0, "User"])
        st.markdown(f"## {int(top3.loc[0, 'steps']):,} steps")
        st.markdown("👑 **Champion of the month**")

    # 🥉 THIRD (lowest)
    if len(top3) >= 3:
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("#### 🥉 " + top3.loc[2, "User"])
            st.markdown(f"##### {int(top3.loc[2, 'steps']):,} steps")

st.divider()

st.subheader("🎖️ This month's highlights")

# --------------------------------
# Build daily matrix for the month
# --------------------------------
daily = month_df.copy()
daily["day"] = daily["date"].dt.day

pivot_daily = daily.pivot_table(
    index="User",
    columns="day",
    values="steps",
    aggfunc="sum"
).fillna(0)

# --------------------------------
# METRICS
# --------------------------------

# 1. Consistent (lowest std dev)
std_dev = pivot_daily.std(axis=1).sort_values()
top_consistent = std_dev.head(3)

# 2. Highly active (highest average)
avg_steps = pivot_daily.mean(axis=1).sort_values(ascending=False)
top_active = avg_steps.head(3)

# 3. 10K crossed
days_10k = (pivot_daily >= 10000).sum(axis=1).sort_values(ascending=False)
top_10k = days_10k.head(3)

# 4. 5K crossed
days_5k = (pivot_daily >= 5000).sum(axis=1).sort_values(ascending=False)
top_5k = days_5k.head(3)

# 5. Most improved (slope)
import numpy as np

def slope(row):
    y = row.values
    x = np.arange(len(y))
    if np.all(y == 0):
        return 0
    return np.polyfit(x, y, 1)[0]

slopes = pivot_daily.apply(slope, axis=1).sort_values(ascending=False)
top_improved = slopes.head(3)

# --------------------------------
# DISPLAY HELPERS
# --------------------------------
def show_top3(title, emoji, series, value_fmt, suffix=""):
    st.markdown(f"### {emoji} {title}")

    names = series.index.tolist()
    values = series.values.tolist()

    # Winner
    st.markdown(f"**{names[0]} — {value_fmt(values[0])}{suffix}**")

    # 2nd & 3rd (smaller)
    if len(names) > 1:
        st.markdown(
            f"<span style='font-size:13px;color:#666'>"
            f"{names[1]} — {value_fmt(values[1])}{suffix}<br>"
            f"{names[2]} — {value_fmt(values[2])}{suffix}"
            f"</span>",
            unsafe_allow_html=True
        )

    st.markdown("---")


# --------------------------------
# LAYOUT
# --------------------------------
c1, c2 = st.columns(2)

with c1:
    show_top3(
        "Most consistent (lowest variation)",
        "🎯",
        top_consistent,
        lambda x: f"{int(x):,}",
        " std dev"
    )

    show_top3(
        "Highly active (highest daily avg)",
        "⚡",
        top_active,
        lambda x: f"{int(x):,}",
        " avg steps"
    )

    show_top3(
        "Most improved (trend)",
        "🚀",
        top_improved,
        lambda x: f"{int(x):,}",
        " slope"
    )

with c2:
    show_top3(
        "10K crossed king",
        "🏅",
        top_10k,
        lambda x: str(int(x)),
        " days"
    )

    show_top3(
        "5K crossed king",
        "🥈",
        top_5k,
        lambda x: str(int(x)),
        " days"
    )


# ----------------------------
# FULL LEADERBOARD
# ----------------------------
st.subheader("📊 Monthly leaderboard")

fig = px.bar(
    monthly_totals,
    x="User",
    y="steps",
    title="Monthly leaderboard",
    text="steps"
)

fig.update_traces(texttemplate='%{text:,}', textposition='outside')

fig.update_layout(
    xaxis_title="",
    yaxis_title="Steps",
    xaxis={'categoryorder':'total descending'},
    height=500
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

