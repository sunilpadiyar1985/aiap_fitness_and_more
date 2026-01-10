import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Steps League – Monthly Results", page_icon="🏃", layout="centered")
page = st.sidebar.radio(
    "Navigate",
    ["🏆 Hall of Fame", "🏠 Monthly Results", "👤 Player Profile"]
)
# ----------------------------
# CONFIG
# ----------------------------
SHEET_ID = "1DfUJd33T-12UVOavd6SqCfkcNl8_4sVxcqqXHtBeWpw"

# ----------------------------
# LOAD DATA (MULTI YEAR, SAFE)
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
            df_long["date"] = pd.to_datetime(df_long["date"], errors="coerce", dayfirst=True)
            df_long["steps"] = pd.to_numeric(df_long["steps"], errors="coerce").fillna(0)
            df_long = df_long.dropna(subset=["date"])

            if not df_long.empty:
                all_data.append(df_long)

        except:
            continue

    if not all_data:
        return pd.DataFrame(columns=["User", "date", "steps", "month"])

    df_all = pd.concat(all_data, ignore_index=True)
    df_all["month"] = df_all["date"].dt.to_period("M")

    return df_all
df = load_data()
# =========================================================
# 🏆 HALL OF FAME — ALL TIME RECORDS
# =========================================================
if page == "🏆 Hall of Fame":

    st.title("🏆 Hall of Fame — All Time Records")
    st.caption("Since the inception of the Steps League")

    d = df.copy().sort_values("date")

    # Trim future empty days
    if (d["steps"] > 0).any():
        last_active = d.loc[d["steps"] > 0, "date"].max()
        d = d[d["date"] <= last_active]

    base = d.groupby("User")

    total_steps = base["steps"].sum()
    avg_steps = base["steps"].mean()
    best_day = base["steps"].max()

    d["week"] = d["date"].dt.to_period("W").apply(lambda r: r.start_time)
    d["month_p"] = d["date"].dt.to_period("M")

    best_week = d.groupby(["User","week"])["steps"].sum().groupby("User").max()
    best_month = d.groupby(["User","month_p"])["steps"].sum().groupby("User").max()

    tenk_pct = (d["steps"] >= 10000).groupby(d["User"]).mean() * 100

    # -------------------------
    # Streaks (max)
    # -------------------------
    def max_streak(series):
        max_s = cur = 0
        for v in series:
            if v:
                cur += 1
                max_s = max(max_s, cur)
            else:
                cur = 0
        return max_s

    streak_10k = {}
    streak_5k = {}

    for user, u in d.groupby("User"):
        u = u.sort_values("date")
        streak_10k[user] = max_streak((u["steps"] >= 10000).tolist())
        streak_5k[user] = max_streak((u["steps"] >= 5000).tolist())

    streak_10k = pd.Series(streak_10k)
    streak_5k = pd.Series(streak_5k)

    # -------------------------
    # RECORD ROW UI
    # -------------------------
    def record_row(title, emoji, series, formatter=lambda x: f"{int(x):,}"):

        top3 = series.sort_values(ascending=False).head(3)

        items = []
        for name, value in top3.items():
            items.append((name, formatter(value)))

        while len(items) < 3:
            items.append(("", ""))

        c0, c1, c2, c3 = st.columns([2.5, 1.5, 1.4, 1.4])

        with c0:
            st.markdown(
                f"""
                <div style="font-size:20px; font-weight:600; line-height:1.3;">
                    {emoji} {title}
                </div>
                """,
                unsafe_allow_html=True
            )

        with c1:
            st.markdown(
                f"""
                <div style="background:#FFD70022;padding:14px;border-radius:14px;text-align:center">
                <div style="font-size:26px;font-weight:700">🥇 {items[0][1]}</div>
                <div style="font-size:14px;color:#444">{items[0][0]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div style="background:#C0C0C022;padding:14px;border-radius:14px;text-align:center">
                <div style="font-size:22px;font-weight:600">🥈 {items[1][1]}</div>
                <div style="font-size:13px;color:#555">{items[1][0]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f"""
                <div style="background:#CD7F3222;padding:14px;border-radius:14px;text-align:center">
                <div style="font-size:20px;font-weight:500">🥉 {items[2][1]}</div>
                <div style="font-size:12px;color:#666">{items[2][0]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------
    # DISPLAY
    # -------------------------
    record_row("Highest total steps (career)", "👣", total_steps)
    record_row("Highest average per day", "📊", avg_steps)
    record_row("Highest steps in a day", "🔥", best_day)
    record_row("Highest steps in a week", "🗓️", best_week)
    record_row("Highest steps in a month", "📆", best_month)
    record_row("Highest 10K completion %", "🏅", tenk_pct, lambda x: f"{x:.2f}%")
    record_row("Longest 10K streak", "⚡", streak_10k, lambda x: f"{int(x)} days")
    record_row("Longest 5K streak", "💪", streak_5k, lambda x: f"{int(x)} days")


if page == "🏠 Monthly Results":
    
    st.title("🏃 Steps League – Monthly Results")
    
    # ----------------------------
    # MONTH SELECTOR (ONLY REAL MONTHS, LAST 6)
    # ----------------------------
    month_totals = (
        df.groupby(df["date"].dt.to_period("M"))["steps"]
        .sum()
        .reset_index()
    )
    
    real_months = month_totals[month_totals["steps"] > 0]["date"].sort_values()
    available_months = real_months.tail(6).tolist()
    
    if not available_months:
        st.warning("No data available yet.")
        st.stop()
    
    selected_month = st.selectbox(
        "Select month",
        available_months[::-1],
        format_func=lambda x: x.strftime("%B %Y")
    )
    
    month_df = df[df["month"] == selected_month]
    
    if month_df["steps"].sum() == 0:
        st.info("📭 Data not available yet for this month.\n\nPlease check back later or contact the admin 🙂")
        st.stop()
    
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
    
    monthly_totals.insert(0, "Rank", range(1, len(monthly_totals) + 1))
    
    st.markdown(f"### Results for {selected_month.strftime('%B %Y')} ⭐")
    
    # ----------------------------
    # PODIUM
    # ----------------------------
    top3 = monthly_totals.head(3).reset_index(drop=True)
    
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
    
    # ----------------------------
    # MONTHLY HIGHLIGHTS
    # ----------------------------
    st.divider()
    st.subheader("🎖️ This month's highlights")
    
    daily = month_df.copy()
    daily["day"] = daily["date"].dt.day
    
    pivot_daily = daily.pivot_table(
        index="User",
        columns="day",
        values="steps",
        aggfunc="sum"
    ).fillna(0)
    
    std_dev = pivot_daily.std(axis=1).fillna(0).sort_values()
    top_consistent = std_dev.head(3)
    
    avg_steps = pivot_daily.mean(axis=1).fillna(0).sort_values(ascending=False)
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
    
    slopes = pivot_daily.apply(slope, axis=1).fillna(0).sort_values(ascending=False)
    top_improved = slopes.head(3)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.success(f"""🎯 **Most consistent**
    
    **{top_consistent.index[0]}** — {int(top_consistent.iloc[0]):,} std dev  
    _{top_consistent.index[1]} — {int(top_consistent.iloc[1]):,}_  
    _{top_consistent.index[2]} — {int(top_consistent.iloc[2]):,}_""")
    
        st.success(f"""⚡ **Highly active**
    
    **{top_active.index[0]}** — {int(top_active.iloc[0]):,} avg steps  
    _{top_active.index[1]} — {int(top_active.iloc[1]):,}_  
    _{top_active.index[2]} — {int(top_active.iloc[2]):,}_""")
    
        st.success(f"""🚀 **Most improved**
    
    **{top_improved.index[0]}** — {int(top_improved.iloc[0]):,} slope  
    _{top_improved.index[1]} — {int(top_improved.iloc[1]):,}_  
    _{top_improved.index[2]} — {int(top_improved.iloc[2]):,}_""")
    
    with c2:
        st.info(f"""🏅 **10K crossed king**
    
    **{top_10k.index[0]}** — {int(top_10k.iloc[0])} days  
    _{top_10k.index[1]} — {int(top_10k.iloc[1])} days_  
    _{top_10k.index[2]} — {int(top_10k.iloc[2])} days_""")
    
        st.info(f"""🥈 **5K crossed king**
    
    **{top_5k.index[0]}** — {int(top_5k.iloc[0])} days  
    _{top_5k.index[1]} — {int(top_5k.iloc[1])} days_  
    _{top_5k.index[2]} — {int(top_5k.iloc[2])} days_""")
    
    # ----------------------------
    # LEADERBOARD
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

# =========================================================
# 👤 PLAYER PROFILE PAGE
# =========================================================
if page == "👤 Player Profile":

    st.title("👤 Player Profile")

    users = sorted(df["User"].unique())
    selected_user = st.selectbox("Select player", users)

    user_df = df[df["User"] == selected_user]

    if user_df.empty:
        st.warning("No data available for this player yet.")
        st.stop()

    # ----------------------------
    # CAREER STATS
    # ----------------------------
    total_steps = int(user_df["steps"].sum())
    avg_steps = int(user_df["steps"].mean())
    active_days = (user_df["steps"] > 0).sum()

    best_day_row = user_df.loc[user_df["steps"].idxmax()]
    best_day = best_day_row["date"].strftime("%d %b %Y")
    best_day_steps = int(best_day_row["steps"])

    monthly_user = (
        user_df.groupby(user_df["date"].dt.to_period("M"))["steps"]
        .sum()
        .reset_index()
        .rename(columns={"date": "month"})
    )

    best_month_row = monthly_user.loc[monthly_user["steps"].idxmax()]
    best_month = best_month_row["month"].strftime("%B %Y")
    best_month_steps = int(best_month_row["steps"])

    days_10k = (user_df["steps"] >= 10000).sum()
    days_5k = (user_df["steps"] >= 5000).sum()

    # ----------------------------
    # PLAYER CARD
    # ----------------------------
    st.subheader("📌 Key stats")

    u = user_df.sort_values("date").copy()
    # ✅ Trim future empty days – keep only up to last active day
    if (u["steps"] > 0).any():
        last_active_date = u.loc[u["steps"] > 0, "date"].max()
        u = u[u["date"] <= last_active_date]
    
    # ---- Basics ----
    total_steps = int(u["steps"].sum())
    avg_steps = int(u["steps"].mean())
    
    non_zero = u[u["steps"] > 0]
    lowest_day = int(non_zero["steps"].min()) if not non_zero.empty else 0
    
    best_day_row = u.loc[u["steps"].idxmax()]
    best_day_steps = int(best_day_row["steps"])
    best_day_date = best_day_row["date"].strftime("%d %b %Y")
    
    # ---- Weekly & monthly records ----
    u["week"] = u["date"].dt.to_period("W").apply(lambda r: r.start_time)
    u["month_p"] = u["date"].dt.to_period("M")
    
    weekly = u.groupby("week")["steps"].sum()
    monthly = u.groupby("month_p")["steps"].sum()
    
    best_week_steps = int(weekly.max())
    best_month_steps = int(monthly.max())
    
    # ---- 10K / 5K coverage ----
    days_total = len(u)
    days_10k = (u["steps"] >= 10000).sum()
    days_5k = (u["steps"] >= 5000).sum()
    
    pct_10k = round((days_10k / days_total) * 100, 2) if days_total else 0
    
    # ---- Streak helpers ----
    def max_streak(series):
        max_s = cur = 0
        for v in series:
            if v:
                cur += 1
                max_s = max(max_s, cur)
            else:
                cur = 0
        return max_s
    
    def current_streak(series):
        cur = 0
        for v in reversed(series):
            if v:
                cur += 1
            else:
                break
        return cur
    
    is_10k = (u["steps"] >= 10000).tolist()
    is_5k = (u["steps"] >= 5000).tolist()
    
    max_10k_streak = max_streak(is_10k)
    max_5k_streak = max_streak(is_5k)
    
    current_10k_streak = current_streak(is_10k)
    current_5k_streak = current_streak(is_5k)
    
    # ---- Layout (3 columns like a stat card) ----
    c1, c2, c3 = st.columns(3)
    
    c1.metric("Overall steps", f"{total_steps:,}")
    c1.metric("Your average", f"{avg_steps:,}")
    c1.metric("Lowest day (non-zero)", f"{lowest_day:,}")
    
    c2.metric("Highest day", f"{best_day_steps:,}", best_day_date)
    c2.metric("Highest week", f"{best_week_steps:,}")
    c2.metric("Highest month", f"{best_month_steps:,}")
    
    c3.metric("Magic 10K covered", f"{pct_10k}%")
    c3.metric("10K streak (max)", f"{max_10k_streak} days")
    c3.metric("5K streak (max)", f"{max_5k_streak} days")
    
    st.caption(
        f"🔥 Current streaks (as of {last_active_date.strftime('%d %b %Y')}) — "
        f"10K: {current_10k_streak} days | 5K: {current_5k_streak} days"
    )
    
    st.divider()

    st.subheader("🏅 Career podiums & trophies")

    # ----------------------------------
    # Build monthly rankings (all-time)
    # ----------------------------------
    all_months = df["month"].dropna().unique()
    
    career_rows = []
    
    for m in all_months:
        mdf = df[df["month"] == m]
    
        if mdf["steps"].sum() == 0:
            continue
    
        table = (
            mdf.groupby("User")["steps"]
            .sum()
            .reset_index()
            .sort_values("steps", ascending=False)
            .reset_index(drop=True)
        )
    
        table["Rank"] = table.index + 1
        table["month"] = m
        career_rows.append(table)
    
    career_df = pd.concat(career_rows, ignore_index=True)
    
    player_hist = career_df[career_df["User"] == selected_user]
    
    # ----------------------------------
    # Career podium stats
    # ----------------------------------
    wins = (player_hist["Rank"] == 1).sum()
    seconds = (player_hist["Rank"] == 2).sum()
    thirds = (player_hist["Rank"] == 3).sum()
    podiums = wins + seconds + thirds
    
    best_rank = int(player_hist["Rank"].min())
    months_played = player_hist["month"].nunique()
    
    # ----------------------------------
    # Trophy cabinet UI
    # ----------------------------------
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("🥇 Wins", wins)
    c2.metric("🥈 Seconds", seconds)
    c3.metric("🥉 Thirds", thirds)
    c4.metric("🏆 Total podiums", podiums)
    
    c1.metric("⭐ Best rank", f"#{best_rank}")
    c2.metric("📆 Months played", months_played)
    
    st.divider()


    # ----------------------------
    # MONTHLY TREND
    # ----------------------------
    st.subheader("📈 Monthly trend")

    monthly_user["month_str"] = monthly_user["month"].astype(str)

    fig = px.line(
        monthly_user,
        x="month_str",
        y="steps",
        markers=True,
        title="Monthly total steps"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Steps",
        height=450
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ----------------------------
    # HISTORY TABLE
    # ----------------------------
    st.subheader("📅 Month by month breakdown")

    u2 = user_df.copy()
    u2["month"] = u2["date"].dt.to_period("M")
    
    monthly_stats = (
    u2.groupby("month")
      .agg(
          total_steps=("steps", "sum"),
          avg_steps=("steps", "mean"),
          best_day=("steps", "max"),
          days_10k=("steps", lambda x: (x >= 10000).sum()),
          days_5k=("steps", lambda x: (x >= 5000).sum()),
      )
      .reset_index()
    )
    
    # ✅ REMOVE future / empty months
    monthly_stats = monthly_stats[monthly_stats["total_steps"] > 0]
    
    # ✅ Latest month first
    monthly_stats = monthly_stats.sort_values("month", ascending=False)
    
    # Formatting
    monthly_stats["month"] = monthly_stats["month"].dt.strftime("%B %Y")
    monthly_stats["avg_steps"] = monthly_stats["avg_steps"].astype(int)
    
    # Friendly column names
    monthly_stats = monthly_stats.rename(columns={
        "month": "Month",
        "total_steps": "Total steps",
        "avg_steps": "Average per day",
        "best_day": "Best single day",
        "days_10k": "Number of 10K days",
        "days_5k": "Number of 5K days"
    })

    
    st.dataframe(monthly_stats, use_container_width=True, hide_index=True)

