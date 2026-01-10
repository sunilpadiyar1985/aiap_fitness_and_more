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

@st.cache_data
def load_roster():
    SHEET_ID = "1DfUJd33T-12UVOavd6SqCfkcNl8_4sVxcqqXHtBeWpw"
    ROSTER_GID = "175789419"

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={ROSTER_GID}"
    r = pd.read_csv(url)

    r.columns = r.columns.str.strip()
    r["Active from"] = pd.to_datetime(r["Active from"])
    r["Active till"] = pd.to_datetime(r["Active till"], errors="coerce")

    return r

#-------------------
#League Engine
#-------------------

def build_league_history(df, roster_df):

    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    df = df.sort_values("date")

    roster_df = roster_df.copy()
    roster_df["Active from"] = pd.to_datetime(roster_df["Active from"])
    roster_df["Active till"] = pd.to_datetime(roster_df["Active till"], errors="coerce")

    all_months = sorted(df["month"].unique())

    history_rows = []
    prev_month_avg = None
    prev_league = {}

    for i, month in enumerate(all_months):

        month_start = month.to_timestamp()
        month_end = month.to_timestamp("M")

        # -------------------------
        # Active roster for month
        # -------------------------
        active = roster_df[
            (roster_df["Active from"] <= month_end) &
            ((roster_df["Active till"].isna()) | (roster_df["Active till"] >= month_start))
        ]["User"].unique().tolist()

        month_df = df[(df["month"] == month) & (df["User"].isin(active))]

        if month_df.empty:
            continue

        # -------------------------
        # DAILY WINS
        # -------------------------
        daily_max = month_df.groupby("date")["steps"].transform("max")
        month_df["daily_win"] = (month_df["steps"] == daily_max) & (month_df["steps"] > 0)

        # -------------------------
        # MONTHLY KPIs
        # -------------------------
        kpi = month_df.groupby("User").agg(
            total_steps=("steps", "sum"),
            avg_steps=("steps", "mean"),
            best_day=("steps", "max"),
            tenk_days=("steps", lambda x: (x >= 10000).sum()),
            daily_wins=("daily_win", "sum")
        ).reset_index()

        month_df["week"] = month_df["date"].dt.to_period("W").apply(lambda r: r.start_time)
        best_week = (
            month_df.groupby(["User", "week"])["steps"]
            .sum()
            .groupby("User")
            .max()
            .reset_index(name="best_week")
        )

        kpi = kpi.merge(best_week, on="User", how="left").fillna(0)

        # -------------------------
        # LEAGUE PLACEMENT
        # -------------------------
        if i == 0:
            kpi["League"] = "Premier"
        else:
            avg_prev = prev_month_avg.reindex(active).fillna(0)

            premier = avg_prev[avg_prev >= 7000].index.tolist()

            if len(premier) < 6:
                premier = avg_prev.sort_values(ascending=False).head(6).index.tolist()

            kpi["League"] = kpi["User"].apply(
                lambda x: "Premier" if x in premier else "Championship"
            )

        # -------------------------
        # NORMALIZATION
        # -------------------------
        for col in ["total_steps", "best_day", "best_week", "tenk_days", "daily_wins"]:
            max_val = kpi[col].max()
            kpi[col + "_score"] = kpi[col] / max_val if max_val > 0 else 0

        # -------------------------
        # POINTS
        # -------------------------
        kpi["points"] = (
            kpi["total_steps_score"] * 0.5 +
            kpi["best_day_score"]   * 0.1 +
            kpi["best_week_score"]  * 0.1 +
            kpi["tenk_days_score"]  * 0.3 +
            kpi["daily_wins_score"] * 0.2
        )

        kpi["points_display"] = (kpi["points"] * 100).round(0).astype(int)

        # -------------------------
        # LEAGUE RANKING
        # -------------------------
        kpi["Rank"] = (
            kpi.groupby("League")["points"]
            .rank(method="min", ascending=False)
        )

        # -------------------------
        # PROMOTION / RELEGATION
        # -------------------------
        if prev_league:
            kpi["Prev league"] = kpi["User"].map(prev_league)
            kpi["Promoted"] = (kpi["Prev league"] == "Championship") & (kpi["League"] == "Premier")
            kpi["Relegated"] = (kpi["Prev league"] == "Premier") & (kpi["League"] == "Championship")
        else:
            kpi["Promoted"] = False
            kpi["Relegated"] = False

        kpi["Champion"] = kpi["Rank"] == 1
        kpi["Month"] = month.to_timestamp()

        history_rows.append(kpi)

        prev_month_avg = kpi.set_index("User")["avg_steps"]
        prev_league = kpi.set_index("User")["League"].to_dict()

    history = pd.concat(history_rows, ignore_index=True)
    return history
    
df = load_data()
roster_df = load_roster()
league_history = build_league_history(df, roster_df)


###data load ends###

# =========================================================
# 🏆 HALL OF FAME — ALL TIME RECORDS
# =========================================================
if page == "🏆 Hall of Fame":

    st.markdown("## 🏆 Hall of Fame — All Time Records")
    st.caption("Since the inception of the Steps League")

    # -------------------------
    # PODIUM HEADER
    # -------------------------
    h0, h1, h2, h3 = st.columns([2.5, 1.7, 1.4, 1.4])
    
    with h1:
        st.markdown("<div style='text-align:center;font-size:26px'>🥇</div>", unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='text-align:center;font-size:24px'>🥈</div>", unsafe_allow_html=True)
    with h3:
        st.markdown("<div style='text-align:center;font-size:22px'>🥉</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)


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
    # Number of 10K days (all-time)
    tenk_days = (d["steps"] >= 10000).groupby(d["User"]).sum()
    
    # Number of 5K days (all-time)
    fivek_days = (d["steps"] >= 5000).groupby(d["User"]).sum()
    
    # 5K completion percentage
    fivek_pct = (d["steps"] >= 5000).groupby(d["User"]).mean() * 100

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

        c0, c1, c2, c3 = st.columns([2.5, 1.7, 1.6, 1.6])
        

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
                <div style="font-size:26px;font-weight:700"> {items[0][1]}</div>
                <div style="font-size:14px;color:#444">{items[0][0]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div style="background:#C0C0C022;padding:14px;border-radius:14px;text-align:center">
                <div style="font-size:22px;font-weight:600"> {items[1][1]}</div>
                <div style="font-size:13px;color:#555">{items[1][0]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f"""
                <div style="background:#CD7F3222;padding:14px;border-radius:14px;text-align:center">
                <div style="font-size:20px;font-weight:500"> {items[2][1]}</div>
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
    record_row("Highest average", "📊", avg_steps)
    record_row("Highest steps in a day", "🔥", best_day)
    record_row("Highest steps in a week", "🗓️", best_week)
    record_row("Highest steps in a month", "📆", best_month)
    record_row("Highest 10K days (all-time)", "🏅", tenk_days, lambda x: f"{int(x)} days")
    record_row("Highest 5K days (all-time)", "🥈", fivek_days, lambda x: f"{int(x)} days")
    record_row("Highest 10K %completion", "🏅", tenk_pct, lambda x: f"{x:.2f}%")
    record_row("Highest 5K %completion", "📈", fivek_pct, lambda x: f"{x:.2f}%")
    record_row("Longest 10K streak", "⚡", streak_10k, lambda x: f"{int(x)} days")
    record_row("Longest 5K streak", "💪", streak_5k, lambda x: f"{int(x)} days")

    st.divider()
    st.markdown("#### 🏟️ League Hall of Fame")
    st.caption("All-time league dominance & achievements")
    
    lh = league_history.copy()
    
    lh["Month"] = pd.to_datetime(lh["Month"])

    # Titles
    prem_titles = lh[(lh["League"] == "Premier") & (lh["Champion"] == True)]["User"].value_counts()
    champ_titles = lh[(lh["League"] == "Championship") & (lh["Champion"] == True)]["User"].value_counts()
    
    # Runner-up (Rank 2)
    runner_up = lh[lh["Rank"] == 2]["User"].value_counts()
    
    # Premier presence
    prem_months = lh[lh["League"] == "Premier"]["User"].value_counts()
    
    # Promotions / relegations
    promotions = lh[lh["Promoted"] == True]["User"].value_counts()
    relegations = lh[lh["Relegated"] == True]["User"].value_counts()
    
    # Best points season
    best_season = lh.sort_values("points", ascending=False).groupby("User").first()["points"]

    record_row("Most Premier titles", "👑", prem_titles, lambda x: f"{int(x)} titles")
    record_row("Most Championship titles", "🏆", champ_titles, lambda x: f"{int(x)} titles")
    record_row("Most runner-up finishes", "🥈", runner_up, lambda x: f"{int(x)} times")
    record_row("Most months in Premier", "🏟️", prem_months, lambda x: f"{int(x)} months")
    record_row("Most promotions", "⬆", promotions, lambda x: f"{int(x)} promotions")
    record_row("Most relegations", "⬇", relegations, lambda x: f"{int(x)} relegations")
    record_row("Best single-season performance", "🚀", best_season, lambda x: f"{round(x*100)} pts")

if page == "🏠 Monthly Results":
    
    st.markdown("## 🏃 Steps League – Monthly Results")
    
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
    month_lh = league_history[
    league_history["Month"].dt.to_period("M") == selected_month
    ]
    
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
    
    st.markdown(f"#### Results for {selected_month.strftime('%B %Y')} ⭐")
    
    # ----------------------------
    # PODIUM
    # ----------------------------
    top3 = monthly_totals.head(3).reset_index(drop=True)
    
    st.markdown("##### 🏆 This month's podium")
    p1, p2, p3 = st.columns([1.1, 1.4, 1.1])
    
    # 🥈 SECOND
    with p1:
        st.markdown(
            f"""
            <div style="background:#F4F6F8;padding:16px;border-radius:16px;text-align:center">
                <div style="font-size:18px">🥈 Second</div>
                <div style="font-size:20px;font-weight:600;margin-top:6px">{top3.loc[1,'User']}</div>
                <div style="font-size:15px;color:#555">{int(top3.loc[1,'steps']):,} steps</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # 🥇 FIRST
    with p2:
        st.markdown(
            f"""
            <div style="background:#FFF7D6;padding:20px;border-radius:20px;text-align:center">
                <div style="font-size:20px">🥇 Winner</div>
                <div style="font-size:24px;font-weight:700;margin-top:6px">{top3.loc[0,'User']}</div>
                <div style="font-size:17px;color:#444">{int(top3.loc[0,'steps']):,} steps</div>
                <div style="font-size:13px;color:#777;margin-top:4px">👑 Champion of the month</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # 🥉 THIRD
    with p3:
        st.markdown(
            f"""
            <div style="background:#FBF1E6;padding:16px;border-radius:16px;text-align:center">
                <div style="font-size:18px">🥉 Third</div>
                <div style="font-size:20px;font-weight:600;margin-top:6px">{top3.loc[2,'User']}</div>
                <div style="font-size:15px;color:#555">{int(top3.loc[2,'steps']):,} steps</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # ----------------------------
    # MONTHLY HIGHLIGHTS
    # ----------------------------
    st.divider()
    st.markdown("##### 🎖️ This month's highlights")
    
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
    
    {top_consistent.index[0]} — {int(top_consistent.iloc[0]):,} std dev  
    {top_consistent.index[1]} — {int(top_consistent.iloc[1]):,}  
    {top_consistent.index[2]} — {int(top_consistent.iloc[2]):,}""")
    
        st.success(f"""⚡ **Highly active**
    
    {top_active.index[0]} — {int(top_active.iloc[0]):,} avg steps  
    {top_active.index[1]} — {int(top_active.iloc[1]):,} 
    {top_active.index[2]} — {int(top_active.iloc[2]):,}""")
    
        st.success(f"""🚀 **Most improved**
    
    {top_improved.index[0]} — {int(top_improved.iloc[0]):,} slope  
    {top_improved.index[1]} — {int(top_improved.iloc[1]):,} 
    {top_improved.index[2]} — {int(top_improved.iloc[2]):,}""")
    
    with c2:
        st.info(f"""🏅 **10K crossed king**
    
    {top_10k.index[0]} — {int(top_10k.iloc[0])} days  
    {top_10k.index[1]} — {int(top_10k.iloc[1])} days  
    {top_10k.index[2]} — {int(top_10k.iloc[2])} days""")
    
        st.info(f"""🥈 **5K crossed king**
    
    {top_5k.index[0]} — {int(top_5k.iloc[0])} days  
    {top_5k.index[1]} — {int(top_5k.iloc[1])} days  
    {top_5k.index[2]} — {int(top_5k.iloc[2])} days""")
    
    st.divider()
    st.markdown("#### 🏟️ League Results")

    premier = month_lh[month_lh["League"] == "Premier"].sort_values("Rank")
    championship = month_lh[month_lh["League"] == "Championship"].sort_values("Rank")

    # =========================
    # 🥇 PREMIER LEAGUE
    # =========================
    st.markdown("##### 🥇 Premier League")
    
    prem_champ = premier[premier["Champion"] == True]
    
    if not prem_champ.empty:
        champ = prem_champ.iloc[0]
        st.success(f"👑 **Premier Champion:** {champ['User']}  |  {champ['points_display']:.3f} pts")
    
    st.dataframe(
        premier[["Rank","User","points_display","Promoted","Relegated"]]
            .rename(columns={
                "points_display": "Points",
                "Promoted": "⬆ Promoted",
                "Relegated": "⬇ Relegated"
            }),
        use_container_width=True,
        hide_index=True
    )
    st.divider()
    st.markdown("###### 🔁 Promotions & Relegations")
    
    promoted = month_lh[month_lh["Promoted"] == True]["User"].tolist()
    relegated = month_lh[month_lh["Relegated"] == True]["User"].tolist()
    
    c1, c2 = st.columns(2)
    
    with c1:
        if promoted:
            st.success("⬆ **Promoted this month**\n\n" + "\n".join([f"• {u}" for u in promoted]))
        else:
            st.info("⬆ No promotions this month")
    
    with c2:
        if relegated:
            st.error("⬇ **Relegated this month**\n\n" + "\n".join([f"• {u}" for u in relegated]))
        else:
            st.info("⬇ No relegations this month")


    # =========================
    # 🥈 CHAMPIONSHIP
    # =========================
    st.markdown("##### 🥈 Championship")
    
    chmp_champ = championship[championship["Champion"] == True]
    
    if not chmp_champ.empty:
        champ = chmp_champ.iloc[0]
        st.info(f"🏆 **Championship Winner:** {champ['User']}  |  {champ['points']:.3f} pts")
    
    st.dataframe(
        championship[["Rank","User","points_display","Promoted","Relegated"]]
            .rename(columns={
                "points_display": "Points",
                "Promoted": "⬆ Promoted",
                "Relegated": "⬇ Relegated"
            }),
        use_container_width=True,
        hide_index=True
    )
    st.divider()

    st.markdown("###### 🔁 Promotions & Relegations")
    
    promoted = month_lh[month_lh["Promoted"] == True]["User"].tolist()
    relegated = month_lh[month_lh["Relegated"] == True]["User"].tolist()
    
    c1, c2 = st.columns(2)
    
    with c1:
        if promoted:
            st.success("⬆ **Promoted this month**\n\n" + "\n".join([f"• {u}" for u in promoted]))
        else:
            st.info("⬆ No promotions this month")
    
    with c2:
        if relegated:
            st.error("⬇ **Relegated this month**\n\n" + "\n".join([f"• {u}" for u in relegated]))
        else:
            st.info("⬇ No relegations this month")


    
    # ----------------------------
    # LEADERBOARD
    # ----------------------------
    st.divider()
    st.markdown("##### 📊 Monthly leaderboard")
    
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
    #st.dataframe(monthly_totals, use_container_width=True, hide_index=True)

# =========================================================
# 👤 PLAYER PROFILE PAGE
# =========================================================
if page == "👤 Player Profile":

    st.markdown("## 👤 Player Profile")

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
    st.markdown("##### 📌 Key stats")

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

    st.markdown("##### 🏅 Career podiums & trophies")

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
    st.markdown("##### 📈 Monthly trend")

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
    st.markdown("##### 📅 Month by month breakdown")

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

