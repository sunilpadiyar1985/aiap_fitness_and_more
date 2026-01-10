import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

    YEAR_SHEETS = {
        "2024": "1074409226",
        "2025": "0",
        "2026": "541668566"
    }

    all_data = []

    for year, gid in YEAR_SHEETS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

        try:
            df = pd.read_csv(url)

            # if sheet exists but is empty
            if df.empty:
                continue

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

            if not df_long.empty:
                all_data.append(df_long)

        except Exception as e:
            # skip sheets that are empty / not ready
            continue

    if not all_data:
        return pd.DataFrame(columns=["User", "date", "steps", "month"])

    df_all = pd.concat(all_data, ignore_index=True)
    df_all["month"] = df_all["date"].dt.to_period("M")

    return df_all
df = load_data()

st.title("🏃 Steps League – Monthly Results")

# ----------------------------
# MONTH SELECTOR (last 6 real months only)
# ----------------------------

all_months = (
    df["date"]
    .dropna()
    .dt.to_period("M")
    .sort_values()
    .unique()
)

available_months = list(all_months[-6:])

if not available_months:
    st.warning("No data available yet.")
    st.stop()

selected_month = st.selectbox(
    "Select month",
    available_months[::-1],
    format_func=lambda x: x.strftime("%B %Y")
)

month_df = df[df["month"] == selected_month]

if month_df.empty:
    st.info("📭 Data not available yet for this month.\n\nPlease check back later or contact the admin 🙂")
    st.stop()


# ----------------------------
# PODIUM
# ----------------------------
top3 = monthly_totals.head(3).reset_index(drop=True)

if len(top3) >= 1:
    st.markdown("#### 🏆 This month's podium")

    c1, c2, c3 = st.columns([1, 1.4, 1])

    if len(top3) >= 2:
        with c1:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("### 🥈 " + top3.loc[1, "User"])
            st.markdown(f"#### {int(top3.loc[1, 'steps']):,} steps")

    with c2:
        st.markdown("## 🥇 " + top3.loc[0, "User"])
        st.markdown(f"## {int(top3.loc[0, 'steps']):,} steps")
        st.markdown("👑 **Champion of the month**")

    if len(top3) >= 3:
        with c3:
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            st.markdown("#### 🥉 " + top3.loc[2, "User"])
            st.markdown(f"##### {int(top3.loc[2, 'steps']):,} steps")

st.divider()
st.subheader("🎖️ This month's highlights")

# ----------------------------
# DAILY MATRIX
# ----------------------------
daily = month_df.copy()
daily["day"] = daily["date"].dt.day

pivot_daily = daily.pivot_table(
    index="User",
    columns="day",
    values="steps",
    aggfunc="sum"
).fillna(0)

# ----------------------------
# METRICS
# ----------------------------
std_dev = pivot_daily.std(axis=1).sort_values()
top_consistent = std_dev.head(3)

avg_steps = pivot_daily.mean(axis=1).sort_values(ascending=False)
top_active = avg_steps.head(3)

days_10k = (pivot_daily >= 10000).sum(axis=1).sort_values(ascending=False)
top_10k = days_10k.head(3)

days_5k = (pivot_daily >= 5000).sum(axis=1).sort_values(ascending=False)
top_5k = days_5k.head(3)

def slope(row):
    y = row.values
    x = np.arange(len(y))
    if np.all(y == 0):
        return 0
    return np.polyfit(x, y, 1)[0]

slopes = pivot_daily.apply(slope, axis=1).sort_values(ascending=False)
top_improved = slopes.head(3)

# ----------------------------
# DISPLAY (KEEPING COLORED BLOCK STYLE)
# ----------------------------
c1, c2 = st.columns(2)

with c1:
    st.success(
        f"""🎯 **Most consistent**

**{top_consistent.index[0]}** — {int(top_consistent.iloc[0]):,} std dev  
_{top_consistent.index[1]} — {int(top_consistent.iloc[1]):,}_  
_{top_consistent.index[2]} — {int(top_consistent.iloc[2]):,}_"""
    )

    st.success(
        f"""⚡ **Highly active**

**{top_active.index[0]}** — {int(top_active.iloc[0]):,} avg steps  
_{top_active.index[1]} — {int(top_active.iloc[1]):,}_  
_{top_active.index[2]} — {int(top_active.iloc[2]):,}_"""
    )

    st.success(
        f"""🚀 **Most improved**

**{top_improved.index[0]}** — {int(top_improved.iloc[0]):,} slope  
_{top_improved.index[1]} — {int(top_improved.iloc[1]):,}_  
_{top_improved.index[2]} — {int(top_improved.iloc[2]):,}_"""
    )

with c2:
    st.info(
        f"""🏅 **10K crossed king**

**{top_10k.index[0]}** — {int(top_10k.iloc[0])} days  
_{top_10k.index[1]} — {int(top_10k.iloc[1])} days_  
_{top_10k.index[2]} — {int(top_10k.iloc[2])} days_"""
    )

    st.info(
        f"""🥈 **5K crossed king**

**{top_5k.index[0]}** — {int(top_5k.iloc[0])} days  
_{top_5k.index[1]} — {int(top_5k.iloc[1])} days_  
_{top_5k.index[2]} — {int(top_5k.iloc[2])} days_"""
    )

# ----------------------------
# FULL LEADERBOARD
# ----------------------------
st.divider()
st.subheader("📊 Monthly leaderboard")

fig = px.bar(
    monthly_totals,
    x="User",
    y="steps",
    text="steps"
)

fig.update_traces(texttemplate='%{text:,}', textposition='outside')
fig.update_layout(
    xaxis_title="",
    yaxis_title="Steps",
    xaxis={'categoryorder': 'total descending'},
    height=500
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(monthly_totals, use_container_width=True, hide_index=True)
