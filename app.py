import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.cache_data.clear()
st.cache_resource.clear()

# ============================
# GLOBAL SAFE DEFAULTS
# ============================
top_consistent = pd.Series(dtype=float)
top_active     = pd.Series(dtype=float)
top_10k        = pd.Series(dtype=int)
top_5k         = pd.Series(dtype=int)
top_improved   = pd.Series(dtype=float)
st.set_page_config(page_title="Steps League – Monthly Results", page_icon="🏃", layout="centered", )

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

h1 { font-size: 2.2rem; font-weight: 700; }
h2 { font-size: 1.7rem; font-weight: 600; }
h3 { font-size: 1.35rem; font-weight: 600; }
h4, h5, h6 { font-weight: 500; }

section[data-testid="stSidebar"] {
    background-color: #fafafa;
}

div[data-testid="metric-container"] {
    border-radius: 14px;
    padding: 12px;
    background-color: #f7f8fa;
}
</style>
""", unsafe_allow_html=True)

def hall_card(title, name, sub):
    st.markdown(f"""
    <div style="
        background:#f7f9fc;
        padding:14px;
        border-radius:14px;
        text-align:center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    ">
        <div style="font-size:14px; font-weight:500; color:#666;">{title}</div>
        <div style="font-size:20px; font-weight:600; margin-top:6px; white-space:normal;">
            {name}
        </div>
        <div style="
            display:inline-block;
            margin-top:8px;
            padding:4px 10px;
            background:#e8f7ee;
            color:#1b7f4b;
            border-radius:999px;
            font-size:12px;
            font-weight:500;
        ">
            {sub}
        </div>
    </div>
    """, unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["🏆 Hall of Fame", "🏠 Monthly Results", "👤 Player Profile", "📜 League History", "ℹ️ Readme: Our Dashboard"]
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
            # First attempt (normal)
            df_long["date"] = pd.to_datetime(df_long["date"], errors="coerce", dayfirst=True)
            
            # Second attempt for anything that failed (force format like 1-Dec-2025)
            mask = df_long["date"].isna()
            df_long.loc[mask, "date"] = pd.to_datetime(
                df_long.loc[mask, "date"],
                format="%d-%b-%Y",
                errors="coerce"
            )

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
    r = pd.read_csv(url, dtype=str)

    r.columns = r.columns.str.strip()

    # ✅ normalize Status
    r["Status"] = r["Status"].astype(str).str.strip().str.lower()

    # optional (safe to keep)
    r["Active from"] = pd.to_datetime(r["Active from"], errors="coerce", dayfirst=True)
    r["Active till"] = pd.to_datetime(r["Active till"], errors="coerce", dayfirst=True)

    return r
    
#-------------------
#Badge Engine
#-------------------
BADGE_CATALOG = [
# ---------------- BRONZE ----------------
{"id":"active_30","name":"Active Starter","emoji":"🚶","tier":"Bronze","desc":"30 active days","color":"#cd7f32"},
{"id":"fivek_7","name":"5K Rookie","emoji":"🟦","tier":"Bronze","desc":"7 day 5K streak","color":"#cd7f32"},
{"id":"tenk_3","name":"First 10K","emoji":"🔥","tier":"Bronze","desc":"3 day 10K streak","color":"#cd7f32"},

# ---------------- SILVER ----------------
{"id":"fivek_30","name":"Habit Builder","emoji":"💪","tier":"Silver","desc":"30 day 5K+ streak","color":"#c0c0c0"},
{"id":"tenk_14","name":"Iron Legs","emoji":"🔥","tier":"Silver","desc":"14 day 10K streak","color":"#c0c0c0"},
{"id":"consistent","name":"Ultra Consistent","emoji":"🧱","tier":"Silver","desc":"75% days ≥5K","color":"#c0c0c0"},

# ---------------- GOLD ----------------
{"id":"tenk_30","name":"Elite Grinder","emoji":"⚡","tier":"Gold","desc":"30 day 10K streak","color":"#ffd700"},
{"id":"fivek_60","name":"Habit Beast","emoji":"🦾","tier":"Gold","desc":"60 day 5K+ streak","color":"#ffd700"},
{"id":"prem_3","name":"Champion Core","emoji":"👑","tier":"Gold","desc":"3 Premier titles","color":"#ffd700"},

# ---------------- LEGENDARY ----------------
{"id":"tenk_60","name":"Mythic Engine","emoji":"🐉","tier":"Legendary","desc":"60 day 10K streak","color":"#9b59ff"},
{"id":"prem_5","name":"League Legend","emoji":"🏆","tier":"Legendary","desc":"5 Premier titles","color":"#9b59ff"},
{"id":"longevity_18","name":"Immortal","emoji":"🐐","tier":"Legendary","desc":"18 active months","color":"#9b59ff"},
]

def generate_badges(user, df, league_history):

    earned = set()

    u = df[df["User"] == user].sort_values("date")
    lh = league_history[league_history["User"] == user]
    s = compute_user_streaks(df, user)

    # Activity
    if (u["steps"] > 0).sum() >= 30:
        earned.add("active_30")

    # 5K streaks
    if s and s["active5"]["max"] >= 7:
        earned.add("fivek_7")
    if s and s["active5"]["max"] >= 30:
        earned.add("fivek_30")
    if s and s["active5"]["max"] >= 60:
        earned.add("fivek_60")

    # 10K streaks
    if s and s["10k"]["max"] >= 3:
        earned.add("tenk_3")
    if s and s["10k"]["max"] >= 14:
        earned.add("tenk_14")
    if s and s["10k"]["max"] >= 30:
        earned.add("tenk_30")
    if s and s["10k"]["max"] >= 60:
        earned.add("tenk_60")

    # Consistency
    if (u["steps"] >= 5000).mean() >= 0.75:
        earned.add("consistent")

    # Titles
    prem_titles = ((lh["Champion"]) & (lh["League"]=="Premier")).sum()
    if prem_titles >= 3:
        earned.add("prem_3")
    if prem_titles >= 5:
        earned.add("prem_5")

    # Longevity
    if u["date"].dt.to_period("M").nunique() >= 18:
        earned.add("longevity_18")

    return earned
    
def render_badge_section(title, tier, earned_ids):

    st.markdown(f"##### {title}")

    tier_badges = [b for b in BADGE_CATALOG if b["tier"] == tier]
    cols = st.columns(6)

    for i, badge in enumerate(tier_badges):
        owned = badge["id"] in earned_ids

        color = badge["color"]
        bg = f"linear-gradient(135deg, {color}, #ffffff)" if owned else "#f0f0f0"
        opacity = "1" if owned else "0.35"
        filter_fx = "none" if owned else "grayscale(100%)"
        crown = "👑" if (tier=="Legendary" and owned) else ""

        glow = "0 0 18px rgba(255,215,0,0.6)" if owned else "none"

        with cols[i % 6]:
            st.markdown(f"""
            <div style="
                background:{bg};
                opacity:{opacity};
                filter:{filter_fx};
                padding:14px;
                border-radius:18px;
                text-align:center;
                margin-bottom:14px;
                box-shadow:{glow};
                transition: all 0.25s ease;
            "
            onmouseover="this.style.transform='scale(1.08)'; this.style.boxShadow='0 10px 22px rgba(0,0,0,0.18)'"
            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='{glow}'"
            >
                <div style="font-size:34px">{badge['emoji']}</div>
                <div style="font-size:14px;font-weight:700">{badge['name']} {crown}</div>
                <div style="font-size:11px;color:#333">{badge['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            
def render_badge_cabinet(earned_ids):
    render_badge_section("🥉 Bronze", "Bronze", earned_ids)
    render_badge_section("🥈 Silver", "Silver", earned_ids)
    render_badge_section("🥇 Gold", "Gold", earned_ids)
    render_badge_section("💎 Legendary", "Legendary", earned_ids)


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

    monthly_activity = df.groupby("month")["steps"].sum()
    all_months = sorted(monthly_activity[monthly_activity > 0].index)

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

        # 🔐 Skip months with no real activity
        if month_df["steps"].sum() == 0:
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
            # First ever month → no promotions/relegations
            prev_league = {u: "Premier" for u in kpi["User"]}
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

# -------------------------
# Era Engine
# -------------------------

def build_eras(league_history, min_streak=3):

    lh = league_history.copy()
    lh["Month"] = pd.to_datetime(lh["Month"])

    eras = []

    for league in ["Premier", "Championship"]:

        champs = lh[(lh["League"] == league) & (lh["Champion"] == True)] \
                    .sort_values("Month")

        prev_user = None
        start = None
        count = 0
        last_month = None

        for _, row in champs.iterrows():

            if row["User"] == prev_user:
                count += 1
            else:
                if prev_user and count >= min_streak:
                    eras.append({
                        "League": league,
                        "Champion": prev_user,
                        "Start": start,
                        "End": last_month,
                        "Titles": count
                    })
                prev_user = row["User"]
                start = row["Month"]
                count = 1

            last_month = row["Month"]

        if prev_user and count >= min_streak:
            eras.append({
                "League": league,
                "Champion": prev_user,
                "Start": start,
                "End": last_month,
                "Titles": count
            })

    return pd.DataFrame(eras)

df = load_data()
roster_df = load_roster()
league_history = build_league_history(df, roster_df)

# ----------------------------
# ACTIVE USERS ENGINE
# ----------------------------
today = pd.Timestamp.today().normalize()

active_users_now = set(
    roster_df[roster_df["Status"] == "active"]["User"]
)

def name_with_status(name):
    return name if name in active_users_now else f"{name} 💤"

# ----------------------------
# all_time_record Engine
# ----------------------------

def detect_all_time_records(df):

    d = df.copy().sort_values("date")

    records = []

    # -------- Highest single day --------
    best_day = d.loc[d["steps"].idxmax()]
    records.append({
        "type": "single_day",
        "title": "Highest single-day steps",
        "User": best_day["User"],
        "value": int(best_day["steps"]),
        "date": best_day["date"]
    })

    # -------- Highest week --------
    d["week"] = d["date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly = d.groupby(["User","week"])["steps"].sum().reset_index()
    best_week = weekly.loc[weekly["steps"].idxmax()]

    records.append({
        "type": "single_week",
        "title": "Highest single-week steps",
        "User": best_week["User"],
        "value": int(best_week["steps"]),
        "date": best_week["week"]
    })

    # -------- Highest month --------
    d["month_p"] = d["date"].dt.to_period("M")
    monthly = d.groupby(["User","month_p"])["steps"].sum().reset_index()
    best_month = monthly.loc[monthly["steps"].idxmax()]

    records.append({
        "type": "single_month",
        "title": "Highest single-month steps",
        "User": best_month["User"],
        "value": int(best_month["steps"]),
        "date": best_month["month_p"].to_timestamp()
    })

    return pd.DataFrame(records)


# ======================================================
# 🧱 STREAK ENGINE — CANONICAL (USE EVERYWHERE)
# ======================================================

def build_user_calendar(df, user):
    u = df[df["User"] == user][["date","steps"]].copy()
    if u.empty:
        return pd.DataFrame(columns=["date","steps"])

    u = u.sort_values("date")

    # ✅ only days where user ever existed in the league
    first_active = u.loc[u["steps"] > 0, "date"].min()
    last_active  = u.loc[u["steps"] > 0, "date"].max()

    if pd.isna(first_active) or pd.isna(last_active):
        return pd.DataFrame(columns=["date","steps"])

    u = u[(u["date"] >= first_active) & (u["date"] <= last_active)]
    u = u.set_index("date")

    full_range = pd.date_range(first_active, last_active, freq="D")

    u = u.reindex(full_range, fill_value=0).reset_index()
    u = u.rename(columns={"index":"date"})

    return u

def max_streak_from_bool(series):
    max_s = cur = 0
    for v in series:
        if v:
            cur += 1
            max_s = max(max_s, cur)
        else:
            cur = 0
    return max_s


def current_streak_from_bool(series):
    cur = 0
    for v in reversed(series):
        if v:
            cur += 1
        else:
            break
    return cur

def analyze_streaks(series, dates):
    max_len = 0
    cur_len = 0

    max_end = None
    max_start = None

    cur_start = None

    for i, v in enumerate(series):
        if v:
            if cur_len == 0:
                cur_start = dates[i]
            cur_len += 1

            if cur_len > max_len:
                max_len = cur_len
                max_end = dates[i]
                max_start = cur_start
        else:
            cur_len = 0
            cur_start = None

    # current streak (from end)
    cur_len2 = 0
    cur_start2 = None

    for i in range(len(series)-1, -1, -1):
        if series[i]:
            if cur_len2 == 0:
                cur_start2 = dates[i]
            cur_len2 += 1
        else:
            break

    cur_end2 = dates[-1] if cur_len2 > 0 else None

    return {
        "max": max_len,
        "max_start": max_start,
        "max_end": max_end,
        "current": cur_len2,
        "current_start": cur_start2,
        "current_end": cur_end2
    }

def compute_user_streaks(df, user):

    u = build_user_calendar(df, user)
    if u.empty:
        return None

    dates = u["date"].tolist()

    s10 = analyze_streaks((u["steps"] >= 10000).tolist(), dates)
    s5z = analyze_streaks(((u["steps"] >= 5000) & (u["steps"] < 10000)).tolist(), dates)
    s5a = analyze_streaks((u["steps"] >= 5000).tolist(), dates)

    return {
        "10k": s10,
        "5k_zone": s5z,
        "active5": s5a
    }

# ----------------------------
# recent record moments Engine
# ----------------------------

def recent_record_breaks(records_df, current_month, window_days=7):

    now = pd.Timestamp.today().normalize()

    df = records_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    this_month = df[df["date"].dt.to_period("M") == current_month]

    fresh = this_month[(now - this_month["date"]).dt.days <= window_days]

    return fresh.sort_values("date", ascending=False)

# ----------------------------
# 🧠 LEAGUE EVENTS + NARRATIVE ENGINE
# ----------------------------
@st.cache_data
def build_league_events(df, league_history):

    d = df.copy()
    d = d[d["date"].notna()]
    d = d.sort_values("date")
    
    events = []
    
    # ======================================================
    # 🔥 STREAK RECORDS — CANONICAL & ISOLATED
    # ======================================================
    
    best_10k = 0
    best_5k_zone = 0
    best_active5 = 0
    
    for user in d["User"].unique():
        s = compute_user_streaks(d, user)
        if not s:
            continue
    
        # ----------------------
        # 🔥 10K ELITE STREAK
        # ----------------------
        cur = s["10k"]["max"]
        if cur >= 5 and cur > best_10k:
    
            best_10k = cur
            end_date = s["10k"]["max_end"]
            start_date = s["10k"]["max_start"]
    
            if pd.notna(end_date):
                events.append({
                    "date": end_date,
                    "Month": end_date.to_period("M").to_timestamp(),
                    "User": user,
                    "type": "streak_10k",
                    "value": int(cur),
                    "title": f"Longest 10K streak ever ({cur} days)",
                    "meta": f"{start_date.strftime('%d %b')} → {end_date.strftime('%d %b')}"
                })
    
        # ----------------------
        # 🟦 5K ZONE STREAK
        # ----------------------
        cur = s["5k_zone"]["max"]
        if cur >= 5 and cur > best_5k_zone:
    
            best_5k_zone = cur
            end_date = s["5k_zone"]["max_end"]
            start_date = s["5k_zone"]["max_start"]
    
            if pd.notna(end_date):
                events.append({
                    "date": end_date,
                    "Month": end_date.to_period("M").to_timestamp(),
                    "User": user,
                    "type": "streak_5k_zone",
                    "value": int(cur),
                    "title": f"Longest 5K-zone streak ever ({cur} days)",
                    "meta": f"{start_date.strftime('%d %b')} → {end_date.strftime('%d %b')}"
                })
    
        # ----------------------
        # 💪 ACTIVE 5K+ HABIT
        # ----------------------
        cur = s["active5"]["max"]
        if cur >= 7 and cur > best_active5:
    
            best_active5 = cur
            end_date = s["active5"]["max_end"]
            start_date = s["active5"]["max_start"]
    
            if pd.notna(end_date):
                events.append({
                    "date": end_date,
                    "Month": end_date.to_period("M").to_timestamp(),
                    "User": user,
                    "type": "active_5k_habit",
                    "value": int(cur),
                    "title": f"Longest active 5K+ habit streak ever ({cur} days)",
                    "meta": f"{start_date.strftime('%d %b')} → {end_date.strftime('%d %b')}"
                })

    # ======================================================
    # 🚀 BEST SINGLE DAY EVER
    # ======================================================

    best_day = 0

    for _, row in d.iterrows():
        if row["steps"] > best_day:
            best_day = row["steps"]
            events.append({
                "date": row["date"],
                "Month": row["date"].to_period("M").to_timestamp(),
                "User": row["User"],
                "type": "best_day",
                "value": int(best_day),
                "title": "Highest steps in a single day ever"
            })

    # ======================================================
    # 🗓️ BEST SINGLE WEEK EVER
    # ======================================================

    d["week"] = d["date"].dt.to_period("W").apply(lambda r: r.start_time)
    weekly = d.groupby(["User", "week"])["steps"].sum().reset_index()

    best_week = 0
    for _, row in weekly.sort_values("week").iterrows():
        if row["steps"] > best_week:
            best_week = row["steps"]
            events.append({
                "date": row["week"],
                "Month": row["week"].to_period("M").to_timestamp(),
                "User": row["User"],
                "type": "best_week",
                "value": int(best_week),
                "title": "Highest steps in a week ever"
            })

    # ======================================================
    # 📆 BEST SINGLE MONTH EVER
    # ======================================================

    monthly = (
        d.groupby(["User", d["date"].dt.to_period("M")])["steps"]
         .sum().reset_index()
         .rename(columns={"date": "Month", "steps": "total"})
         .sort_values("Month")
    )

    best_month = 0
    for _, row in monthly.iterrows():
        if row["total"] > best_month:
            best_month = row["total"]
            events.append({
                "date": row["Month"].to_timestamp("M"),
                "Month": row["Month"].to_timestamp(),
                "User": row["User"],
                "type": "best_month",
                "value": int(best_month),
                "title": "Highest steps in a month ever"
            })

    # ======================================================
    # 👑 PREMIER TITLES RECORD
    # ======================================================

    prem = league_history[(league_history["League"]=="Premier") & (league_history["Champion"])].sort_values("Month")
    prem_counts, prem_record = {}, 0

    for _, row in prem.iterrows():
        u = row["User"]
        prem_counts[u] = prem_counts.get(u, 0) + 1
        if prem_counts[u] > prem_record:
            prem_record = prem_counts[u]
            events.append({
                "date": row["Month"],
                "Month": row["Month"].to_period("M").to_timestamp(),
                "User": u,
                "type": "prem_titles",
                "value": prem_record,
                "title": "Most Premier League titles ever"
            })

    # ======================================================
    # 🏆 CHAMPIONSHIP TITLES RECORD
    # ======================================================

    champ = league_history[(league_history["League"]=="Championship") & (league_history["Champion"])].sort_values("Month")
    champ_counts, champ_record = {}, 0

    for _, row in champ.iterrows():
        u = row["User"]
        champ_counts[u] = champ_counts.get(u, 0) + 1
        if champ_counts[u] > champ_record:
            champ_record = champ_counts[u]
            events.append({
                "date": row["Month"],
                "Month": row["Month"].to_period("M").to_timestamp(),
                "User": u,
                "type": "champ_titles",
                "value": champ_record,
                "title": "Most Championship titles ever"
            })

    # ======================================================
    # 🚀 BEST POINTS SEASON EVER
    # ======================================================

    best_points = 0
    for _, row in league_history.sort_values("Month").iterrows():
        if row["points"] > best_points:
            best_points = row["points"]
            events.append({
                "date": row["Month"],
                "Month": row["Month"].to_period("M").to_timestamp(),
                "User": row["User"],
                "type": "best_points",
                "value": int(best_points * 100),
                "title": f"Best season performance ever ({row['League']})"
            })

    # ======================================================
    # 👑 ALL-TIME STEPS LEADER CHANGE (narrative)
    # ======================================================

    totals, current_leader, current_best = {}, None, 0

    for _, row in d.sort_values("date").iterrows():
        u = row["User"]
        totals[u] = totals.get(u, 0) + row["steps"]

        if totals[u] > current_best and u != current_leader:
            prev = current_leader
            current_leader = u
            current_best = totals[u]

            if prev:
                events.append({
                    "date": row["date"],
                    "Month": row["date"].to_period("M").to_timestamp(),
                    "User": u,
                    "type": "leader_change",
                    "value": int(current_best),
                    "title": f"Overtakes {prev} as all-time steps leader"
                })

    # ======================================================
    # 🏆 FIRST EVER 100K DAY
    # ======================================================

    first_100k = False
    for _, row in d.iterrows():
        if row["steps"] >= 100000 and not first_100k:
            first_100k = True
            events.append({
                "date": row["date"],
                "Month": row["date"].to_period("M").to_timestamp(),
                "User": row["User"],
                "type": "first_100k_day",
                "value": int(row["steps"]),
                "title": "First ever 100K steps day"
            })
            
    return pd.DataFrame(events).sort_values("date")
    
def show_global_league_moments(events_df):

    if events_df is None or events_df.empty:
        return

    current_month = pd.Timestamp.today().to_period("M").to_timestamp()

    breaking = (
        events_df[events_df["Month"] == current_month]
        .sort_values("date", ascending=False)
        .drop_duplicates(subset=["type"], keep="first")  # ✅ de-dup here
        .head(5)
    )

    if breaking.empty:
        return

    messages = []
    for _, r in breaking.iterrows():
        messages.append(
            f"🔥 {r['title']} — {name_with_status(r['User'])} set {r['value']:,}"
        )

    ticker_text = "   |   ".join(messages)

    st.markdown(f"""
    <style>
    .ticker-box {{
        background:#fff4f4;
        border-radius:14px;
        padding:8px 14px;
        margin-top:4px;
        margin-bottom:12px;
        font-size:14px;
        font-weight:500;
        border:1px solid #ffd6d6;
        overflow:hidden;
    }}

    .ticker-box marquee {{
        white-space: nowrap;
        line-height: 1.4;
    }}
    </style>

    <div class="ticker-box">
        <marquee behavior="scroll" direction="left" scrollamount="5">
            🚨 {ticker_text}
        </marquee>
    </div>
    """, unsafe_allow_html=True)


league_events = build_league_events(df, league_history)
show_global_league_moments(league_events)

# Data Load Fineshes...

# =========================================================
# 🏆 HALL OF FAME — ALL TIME RECORDS
# =========================================================
if page == "🏆 Hall of Fame":

    st.markdown("### 🏆 Hall of Fame — All Time Records")
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
    tenk_days = (d["steps"] >= 10000).groupby(d["User"]).sum()
    fivek_days = (d["steps"] >= 5000).groupby(d["User"]).sum()
    fivek_pct = (d["steps"] >= 5000).groupby(d["User"]).mean() * 100


    # -------------------------
    # STREAK ENGINE
    # -------------------------
    
    streak_10k = {}
    streak_5k_zone = {}
    streak_active5 = {}
    
    current_10k = {}
    current_5k_zone = {}
    current_active5 = {}
    
    for user in d["User"].unique():
        s = compute_user_streaks(d, user)
        if not s:
            continue
    
        streak_10k[user] = s["10k"]["max"]
        streak_5k_zone[user] = s["5k_zone"]["max"]
        streak_active5[user] = s["active5"]["max"]
        
        current_10k[user] = s["10k"]["current"]
        current_5k_zone[user] = s["5k_zone"]["current"]
        current_active5[user] = s["active5"]["current"]

    streak_10k = pd.Series(streak_10k)
    streak_5k_zone = pd.Series(streak_5k_zone)
    streak_active5 = pd.Series(streak_active5)


    # -------------------------
    # STREAK DISPLAY SERIES (🔥 if active)
    # -------------------------
    def streak_name(name, is_active):
        base = name_with_status(name)
        return f"{base} 🔥" if is_active else base

    streak_10k_display = streak_10k.copy()
    streak_10k_display.index = [
        streak_name(u, current_10k.get(u, 0) > 0)
        for u in streak_10k.index
    ]

    streak_5k_display = streak_5k_zone.copy()
    streak_5k_display.index = [
        streak_name(u, current_5k_zone.get(u, 0) > 0)
        for u in streak_5k_zone.index
    ]


    # -------------------------
    # RECORD ROW UI
    # -------------------------
    def record_row(title, emoji, series, formatter=lambda x: f"{int(x):,}"):

        top3 = series.sort_values(ascending=False).head(3)

        items = []
        for name, value in top3.items():
            items.append((name_with_status(name) if name in active_users_now or "🔥" not in name else name, formatter(value)))

        while len(items) < 3:
            items.append(("", ""))

        c0, c1, c2, c3 = st.columns([2.5, 1.7, 1.6, 1.6])

        with c0:
            st.markdown(f"<div style='font-size:20px;font-weight:600'>{emoji} {title}</div>", unsafe_allow_html=True)

        with c1:
            st.markdown(f"<div style='background:#FFD70022;padding:14px;border-radius:14px;text-align:center'><div style='font-size:26px;font-weight:700'>{items[0][1]}</div><div style='font-size:14px'>{items[0][0]}</div></div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f"<div style='background:#C0C0C022;padding:14px;border-radius:14px;text-align:center'><div style='font-size:22px;font-weight:600'>{items[1][1]}</div><div style='font-size:13px'>{items[1][0]}</div></div>", unsafe_allow_html=True)

        with c3:
            st.markdown(f"<div style='background:#CD7F3222;padding:14px;border-radius:14px;text-align:center'><div style='font-size:20px;font-weight:500'>{items[2][1]}</div><div style='font-size:12px'>{items[2][0]}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------
    # DISPLAY
    # -------------------------
    record_row("Highest total steps (career)", "👣", total_steps)
    record_row("Highest average", "📊", avg_steps)
    record_row("Highest steps in a day", "🔥", best_day)
    record_row("Highest steps in a week", "🗓️", best_week)
    record_row("Highest steps in a month", "📆", best_month)
    record_row("Highest 10K days (all-time)", "🏅", tenk_days, lambda x: f"{int(x)}")
    record_row("Highest 5K days (all-time)", "🥈", fivek_days, lambda x: f"{int(x)}")
    record_row("Highest 10K %completion", "🏅", tenk_pct, lambda x: f"{x:.2f}%")
    record_row("Highest 5K %completion", "📈", fivek_pct, lambda x: f"{x:.2f}%")
    record_row("Longest 10K streak - elite", "⚡", streak_10k, lambda x: f"{int(x)}")
    record_row("Longest active 5K+ habit streak", "💪", streak_active5, lambda x: f"{int(x)}")
    record_row("Longest 5K zone streak (5000–9999)", "🟦", streak_5k_zone, lambda x: f"{int(x)}")

    st.divider()
    st.markdown("###### 🏟️ League Hall of Fame")
    st.caption("All-time league dominance & achievements")

    lh = league_history.copy()
    lh["Month"] = pd.to_datetime(lh["Month"])

    prem_titles = lh[(lh["League"] == "Premier") & (lh["Champion"])]["User"].value_counts()
    champ_titles = lh[(lh["League"] == "Championship") & (lh["Champion"])]["User"].value_counts()
    prem_runner_up = lh[(lh["League"] == "Premier") & (lh["Rank"] == 2)]["User"].value_counts()
    champ_runner_up = lh[(lh["League"] == "Championship") & (lh["Rank"] == 2)]["User"].value_counts()
    prem_months = lh[lh["League"] == "Premier"]["User"].value_counts()
    promotions = lh[lh["Promoted"]]["User"].value_counts()
    relegations = lh[lh["Relegated"]]["User"].value_counts()
    best_season = lh.sort_values("points", ascending=False).groupby("User").first()["points"]

    record_row("Most Premier titles", "👑", prem_titles, lambda x: f"{int(x)}")
    record_row("Most Championship titles", "🏆", champ_titles, lambda x: f"{int(x)}")
    record_row("Most Premier runner-ups", "🥈", prem_runner_up, lambda x: f"{int(x)}")
    record_row("Most Championship runner-ups", "🥈", champ_runner_up, lambda x: f"{int(x)}")
    record_row("Most months in Premier", "🏟️", prem_months, lambda x: f"{int(x)}")
    record_row("Most promotions", "⬆", promotions, lambda x: f"{int(x)}")
    record_row("Most relegations", "⬇", relegations, lambda x: f"{int(x)}")
    record_row("Best single-season performance", "🚀", best_season, lambda x: f"{round(x*100)} pts")

    st.divider()
    st.markdown("### 🐐 GOAT Rankings — All-time greats")
    
    lh = league_history.copy()
    
    goat = lh.groupby("User").agg(
        seasons=("Month","nunique"),
        avg_points=("points","mean"),
        best_season=("points","max"),
        premier_titles=("Champion", lambda x: ((x) & (lh.loc[x.index,"League"]=="Premier")).sum()),
        champ_titles=("Champion", lambda x: ((x) & (lh.loc[x.index,"League"]=="Championship")).sum()),
        premier_months=("League", lambda x: (x=="Premier").sum()),
        promotions=("Promoted","sum")
    ).reset_index()
    
    # Normalization helper
    def norm(s):
        return (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0
    
    goat["GOAT_score"] = (
        norm(goat["premier_titles"]) * 0.30 +
        norm(goat["champ_titles"])   * 0.10 +
        norm(goat["avg_points"])     * 0.20 +
        norm(goat["best_season"])    * 0.15 +
        norm(goat["premier_months"]) * 0.15 +
        norm(goat["seasons"])        * 0.05 +
        norm(goat["promotions"])     * 0.05
    )
    
    goat = goat.sort_values("GOAT_score", ascending=False)
    goat["Rank"] = range(1, len(goat)+1)
    goat["Index"] = (goat["GOAT_score"] * 100).round(1)
    
    st.dataframe(
        goat[["Rank","User","Index","premier_titles","champ_titles","premier_months","seasons"]]
          .rename(columns={
              "premier_titles":"👑 Premier",
              "champ_titles":"🏆 Champ",
              "premier_months":"🏟 Premier months",
              "seasons":"🗓 Seasons"
          }),
        use_container_width=True,
        hide_index=True
    )


if page == "🏠 Monthly Results":
    
    st.markdown("### 🏃 Steps League – Monthly Results")
    current_month = pd.Timestamp.today().to_period("M")
    
    # ----------------------------
    # MONTH SELECTOR (ONLY REAL MONTHS, LAST 6)
    # ----------------------------
    month_totals = (
        df.groupby(df["date"].dt.to_period("M"))["steps"]
        .sum()
        .reset_index()
    )
    
    real_months = month_totals[month_totals["steps"] > 0]["date"].sort_values().unique()
    available_months = list(real_months[-6:])
    
    if not available_months:
        st.warning("No data available yet.")
        st.stop()
    
    selected_month = st.selectbox(
        "Select month",
        available_months[::-1],
        format_func=lambda x: x.strftime("%B %Y")
    )

    is_current_month = (selected_month == current_month)
    month_start = selected_month.to_timestamp()
    month_end = selected_month.to_timestamp("M")
    
    active_users = roster_df[
        (roster_df["Active from"] <= month_end) &
        ((roster_df["Active till"].isna()) | (roster_df["Active till"] >= month_start))
    ]["User"].unique().tolist()

    month_lh = league_history[
        (league_history["Month"].dt.to_period("M") == selected_month) &
        (league_history["User"].isin(active_users))
    ]
    
    month_df = df[
        (df["month"] == selected_month) &
        (df["User"].isin(active_users))
    ]
    
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
    if is_current_month:
        st.info("🕒 **Live month in progress** — standings are based on current data and may change before month end.")

        
    # ----------------------------
    # 🚨 League moments (NEW)
    # ----------------------------
    
    records = detect_all_time_records(df)
    breaking = recent_record_breaks(records, selected_month)
    
    if not breaking.empty:
        st.markdown("## 🚨 League moments")
    
        for _, r in breaking.iterrows():
            st.error(
                f"🔥 **NEW RECORD!** {r['title']} — "
                f"{name_with_status(r['User'])} with {r['value']:,}"
            )

    if is_current_month:
        crown_text = "🗳️ Current leader"
    else:
        crown_text = "👑 Champion of the month"
    # ----------------------------
    # PODIUM
    # ----------------------------
    if len(monthly_totals) < 3:
        st.warning("Not enough active players this month to build a podium.")
        st.stop()
        
    top3 = monthly_totals.head(3).reset_index(drop=True)
    
    st.markdown("###### 🏆 This month's podium" if not is_current_month else "###### 🏁 Current standings")
    p1, p2, p3 = st.columns([1.1, 1.4, 1.1])
    
    # 🥈 SECOND
    with p1:
        st.markdown(
            f"""
            <div style="background:#F4F6F8;padding:16px;border-radius:16px;text-align:center">
                <div style="font-size:18px">🥈 Second</div>
                <div style="font-size:20px;font-weight:600;margin-top:6px">{name_with_status(top3.loc[1,'User'])}</div>
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
                <div style="font-size:24px;font-weight:700;margin-top:6px">{name_with_status(top3.loc[0,'User'])}</div>
                <div style="font-size:17px;color:#444">{int(top3.loc[0,'steps']):,} steps</div>
                <div style="font-size:13px;color:#777;margin-top:4px">{crown_text}</div>
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
                <div style="font-size:20px;font-weight:600;margin-top:6px">{name_with_status(top3.loc[2,'User'])}</div>
                <div style="font-size:15px;color:#555">{int(top3.loc[2,'steps']):,} steps</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ----------------------------
    # MONTHLY HIGHLIGHTS
    # ----------------------------
    st.divider()
    st.markdown("###### 🎖️ This month's highlights")
    
    daily = month_df.copy()
    daily["day"] = daily["date"].dt.day
    
    pivot_daily = daily.pivot_table(
        index="User",
        columns="day",
        values="steps",
        aggfunc="sum"
    ).fillna(0)

    # -----------------------------------
    # FILTER ONLY ACTIVE (NON-ZERO) USERS
    # -----------------------------------
    user_totals = pivot_daily.sum(axis=1)
    active_users = user_totals[user_totals > 0].index
    
    pivot_active = pivot_daily.loc[active_users]
    
    if pivot_active.empty:
        st.info("No activity recorded yet for this month.")
        st.stop()
    # ----------------------------
    # SAFE INITIALIZATION (important for Streamlit reruns)
    # ----------------------------
    top_consistent = pd.Series(dtype=float)
    top_active = pd.Series(dtype=float)
    top_10k = pd.Series(dtype=int)
    top_5k = pd.Series(dtype=int)
    top_improved = pd.Series(dtype=float)

    # ----------------------------
    # MONTHLY HIGHLIGHTS (CLEAN)
    # ----------------------------
    std_dev = pivot_active.std(axis=1).sort_values()
    top_consistent = std_dev.head(3)
    
    avg_steps = pivot_active.mean(axis=1).sort_values(ascending=False)
    top_active = avg_steps.head(3)
    
    days_10k = (pivot_active >= 10000).sum(axis=1).sort_values(ascending=False)
    top_10k = days_10k.head(3)
    
    days_5k = ((pivot_active >= 5000) & (pivot_active < 10000)).sum(axis=1).sort_values(ascending=False)
    top_5k = days_5k.head(3)
    
    def slope(row):
        y = row.values
        x = np.arange(len(y))
        if np.all(y == 0):
            return 0
        return np.polyfit(x, y, 1)[0]
    
    slopes = pivot_active.apply(slope, axis=1).sort_values(ascending=False)
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
    
    premier = month_lh[month_lh["League"] == "Premier"].sort_values("Rank")
    championship = month_lh[month_lh["League"] == "Championship"].sort_values("Rank")
    
    st.divider()
    st.markdown("###### 🏟️ League Tables")
    
    premier = month_lh[month_lh["League"] == "Premier"].sort_values("Rank")
    championship = month_lh[month_lh["League"] == "Championship"].sort_values("Rank")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("###### 🥇 Premier League")
        st.dataframe(
            premier[["Rank","User","points_display","Promoted","Relegated"]]
                .rename(columns={
                    "points_display": "Points",
                    "Promoted": "⬆",
                    "Relegated": "⬇"
                }),
            use_container_width=True,
            hide_index=True
        )
    
    with c2:
        st.markdown("###### 🥈 Championship")
        st.dataframe(
            championship[["Rank","User","points_display","Promoted","Relegated"]]
                .rename(columns={
                    "points_display": "Points",
                    "Promoted": "⬆",
                    "Relegated": "⬇"
                }),
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.markdown("###### ⚠️ Danger zone")
    
    bottom_prem = premier.sort_values("Rank").tail(2)
    top_champ = championship.sort_values("Rank").head(2)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.error("🔥 Premier relegation risk")
        for _, r in bottom_prem.iterrows():
            st.write(f"⬇ {r['User']} — {int(r['points_display'])} pts")
    
    with c2:
        st.success("🚀 Championship promotion push")
        for _, r in top_champ.iterrows():
            st.write(f"⬆ {r['User']} — {int(r['points_display'])} pts")


    st.divider()
    st.markdown("###### 📰 Monthly storylines")
    
    if "top_improved" in locals() and not top_improved.empty and not top_consistent.empty:
    
        dominator = monthly_totals.iloc[0]
        climber = top_improved.index[0] if len(top_improved) > 0 else "—"
        consistent = top_consistent.index[0]
        last_place = monthly_totals.iloc[-1]["User"]
    
        st.success(f"👑 **Dominant force:** {dominator['User']} ruled the month with {int(dominator['steps']):,} steps")
        st.info(f"🚀 **Biggest momentum:** {climber} showed the strongest improvement trend")
        st.warning(f"🧱 **Mr Consistent:** {consistent} was the steadiest performer this month")
        st.error(f"⚠️ **Needs a comeback:** {last_place} will be hungry next month")
    
    else:
        st.caption("Monthly storylines will appear once enough activity data is available.")
        
    # ----------------------------
    # LEADERBOARD
    # ----------------------------
    st.divider()
    st.markdown("###### 📊 Monthly leaderboard")
    
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

    st.markdown("### 👤 Player Profile")

    users = sorted(df["User"].unique())
    display_map = {name_with_status(u): u for u in users}
    
    selected_label = st.selectbox("Select player", list(display_map.keys()))
    selected_user = display_map[selected_label]

    user_df = df[df["User"] == selected_user]

    if user_df.empty:
        st.warning("No data available for this player yet.")
        st.stop()

    # ✅ LEAGUE HISTORY FOR THIS PLAYER (FIX)
    player_lh = league_history[league_history["User"] == selected_user].sort_values("Month")

    # ----------------------------
    # PLAYER CARD — KEY STATS
    # ----------------------------
    st.markdown("###### 📌 Key stats")

    u = user_df.sort_values("date").copy()

    if (u["steps"] > 0).any():
        last_active_date = u.loc[u["steps"] > 0, "date"].max()
        u = u[u["date"] <= last_active_date]

    total_steps = int(u["steps"].sum())
    avg_steps = int(u["steps"].mean())

    non_zero = u[u["steps"] > 0]
    lowest_day = int(non_zero["steps"].min()) if not non_zero.empty else 0

    best_day_row = u.loc[u["steps"].idxmax()]
    best_day_steps = int(best_day_row["steps"])
    best_day_date = best_day_row["date"].strftime("%d %b %Y")

    u["week"] = u["date"].dt.to_period("W").apply(lambda r: r.start_time)
    u["month_p"] = u["date"].dt.to_period("M")

    weekly = u.groupby("week")["steps"].sum()
    monthly = u.groupby("month_p")["steps"].sum()

    # 📈 Improvement trend (slope of monthly steps)
    if len(monthly) >= 2:
        y = monthly.values
        x = np.arange(len(y))
        trend_slope = np.polyfit(x, y, 1)[0]
    else:
        trend_slope = 0
    
    if trend_slope > 5000:
        trend_label = "🚀 Strong upward trend"
    elif trend_slope > 1000:
        trend_label = "📈 Improving steadily"
    elif trend_slope < -5000:
        trend_label = "📉 Strong decline"
    elif trend_slope < -1000:
        trend_label = "⚠️ Slight decline"
    else:
        trend_label = "➖ Mostly stable"
    best_week_steps = int(weekly.max())
    best_week_start = weekly.idxmax()
    best_week_label = f"{best_week_start.strftime('%d %b %Y')}"
    
    best_month_steps = int(monthly.max())
    best_month_period = monthly.idxmax()
    best_month_label = best_month_period.strftime("%B %Y")

    days_total = len(u)
    days_10k = (u["steps"] >= 10000).sum()
    days_5k = (u["steps"] >= 5000).sum()
    pct_10k = round((days_10k / days_total) * 100, 2) if days_total else 0

    def streak_name(name, active):
        base = name_with_status(name)
        return f"{base} 🔥" if active else base
    
    s = compute_user_streaks(df, selected_user)

    max_10k_streak = s["10k"]["max"]
    current_10k_streak = s["10k"]["current"]
    
    max_5k_streak = s["5k_zone"]["max"]
    current_5k_streak = s["5k_zone"]["current"]
    
    max_active5 = s["active5"]["max"]
    current_active5 = s["active5"]["current"]


    c1, c2, c3 = st.columns(3)

    c1.metric("Overall steps", f"{total_steps:,}", "")
    c1.metric("Your average", f"{avg_steps:,}", "")
    c1.metric("Lowest day (non-zero)", f"{lowest_day:,}", "")

    c2.metric("Highest day", f"{best_day_steps:,}", best_day_date)
    c2.metric("Highest week", f"{best_week_steps:,}", best_week_label)
    c2.metric("Highest month", f"{best_month_steps:,}", best_month_label)


    c3.metric("Magic 10K covered", f"{pct_10k}%", "")
    c3.metric("10K streak - elite (max)", f"{max_10k_streak} days", "")
    c3.metric("5K+ habit streak (max)", f"{max_active5} days", "")
    c3.metric("Only 5K streak (max)", f"{max_5k_streak} days", "")

    st.caption(
        f"🔥 Current streaks (as of {last_active_date.strftime('%d %b %Y')}) — "
        f"10K: {current_10k_streak} | 5K+ habit: {current_active5} | 5K zone: {current_5k_streak}"
    )

    st.success(f"📈 **Fitness trend:** {trend_label}")

    st.divider()
    st.markdown("###### 📈 Current form (last 60 days)")
    
    recent = u.sort_values("date").tail(60).copy()
    
    recent["rolling"] = recent["steps"].rolling(7).mean()
    
    fig = px.line(
        recent,
        x="date",
        y=["steps", "rolling"],
        labels={"value": "Steps", "variable": "Legend"},
    )
    
    fig.update_layout(
        height=320,
        xaxis_title="",
        yaxis_title="Steps",
        legend_title="",
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("###### 🧬 Consistency fingerprint")

    bins = {
        "No activity": (u["steps"] == 0).mean(),
        "1–5k": ((u["steps"] > 0) & (u["steps"] < 5000)).mean(),
        "5k–10k": ((u["steps"] >= 5000) & (u["steps"] < 10000)).mean(),
        "10k+": (u["steps"] >= 10000).mean()
    }
    
    finger = pd.DataFrame({
        "Zone": list(bins.keys()),
        "Share": [v * 100 for v in bins.values()]
    })
    
    fig = px.bar(
        finger,
        x="Share",
        y="Zone",
        orientation="h",
        text=finger["Share"].round(1).astype(str) + "%",
    )
    
    fig.update_layout(
        height=260,
        xaxis_title="Career distribution",
        yaxis_title="",
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("###### 🎖️ Badges earned")
    
    earned = generate_badges(selected_user, df, league_history)
    render_badge_cabinet(earned)
    st.divider()
    # ----------------------------
    # TROPHY CABINET
    # ----------------------------
    
    st.markdown("###### 🏆 Trophy cabinet")

    prem_titles = player_lh[(player_lh["League"] == "Premier") & (player_lh["Champion"])].shape[0]
    champ_titles = player_lh[(player_lh["League"] == "Championship") & (player_lh["Champion"])].shape[0]
    prem_runnerups = player_lh[(player_lh["League"] == "Premier") & (player_lh["Rank"] == 2)].shape[0]
    champ_runnerups = player_lh[(player_lh["League"] == "Championship") & (player_lh["Rank"] == 2)].shape[0]
    best_finish = int(player_lh["Rank"].min())
    best_points = int(player_lh["points_display"].max())

    t1, t2, t3, t4, t5, t6 = st.columns(6)

    t1.metric("👑 Premier titles", prem_titles)
    t2.metric("🏆 Championship titles", champ_titles)
    t3.metric("🥈 Premier runner-ups", prem_runnerups)
    t4.metric("🥈 Championship runner-ups", champ_runnerups)
    t5.metric("🏅 Best rank", f"#{best_finish}")
    t6.metric("🚀 Best season", f"{best_points} pts")

    st.divider()
    
    # ----------------------------
    # LEAGUE CAREER SNAPSHOT
    # ----------------------------
    st.divider()
    st.markdown("###### 🧍 League career snapshot")

    first_month = player_lh["Month"].min().strftime("%b %Y")
    last_month = player_lh["Month"].max().strftime("%b %Y")
    seasons = player_lh["Month"].nunique()

    prem_months = (player_lh["League"] == "Premier").sum()
    champ_months = (player_lh["League"] == "Championship").sum()
    promotions = player_lh["Promoted"].sum()
    relegations = player_lh["Relegated"].sum()

    l1, l2, l3, l4 = st.columns(4)

    l1.metric("Seasons played", seasons)
    l2.metric("Premier months", prem_months)
    l3.metric("Promotions", promotions)
    l4.metric("Relegations", relegations)

    st.info(f"🗓️ Active career: **{first_month} → {last_month}**")

    st.divider()
    st.markdown("###### ⚔️ Biggest rivals")
    
    rivals = (
        league_history.groupby(["Month","User"])["points"]
        .mean()
        .unstack()
    )
    
    if selected_user in rivals.columns:
        diffs = rivals.subtract(rivals[selected_user], axis=0).abs().mean().sort_values()
        top_rivals = diffs.drop(selected_user).head(3).index.tolist()
    
        for r in top_rivals:
            h2h = rivals[[selected_user, r]].dropna()
            wins = (h2h[selected_user] > h2h[r]).sum()
            losses = (h2h[selected_user] < h2h[r]).sum()
    
            st.info(f"⚔️ **{r}** — {wins} wins vs {losses} losses | {len(h2h)} battles")

    st.divider()

    # ----------------------------
    # LEAGUE JOURNEY TABLE
    # ----------------------------
    st.divider()
    st.markdown("###### 📜 League journey")

    journey = player_lh.sort_values("Month", ascending=False)[
        ["Month","League","Rank","points_display","Champion","Promoted","Relegated"]
    ].copy()

    journey["Month"] = journey["Month"].dt.strftime("%b %Y")

    st.dataframe(
        journey.rename(columns={
            "points_display": "Points",
            "Champion": "🏆 Champion",
            "Promoted": "⬆ Promoted",
            "Relegated": "⬇ Relegated"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()
    st.markdown("###### 📈 League journey (career path)")
    
    chart_df = player_lh.sort_values("Month").copy()
    
    # Map leagues to vertical positions
    chart_df["league_y"] = chart_df["League"].map({
        "Premier": 1,
        "Championship": -1
    })
    
    chart_df["MonthLabel"] = chart_df["Month"].dt.strftime("%b %Y")
    
    fig = px.line(
        chart_df,
        x="Month",
        y="league_y",
        markers=True,
        title=None
    )
    
    fig.update_traces(
        mode="lines+markers+text",
        text=chart_df["Rank"].apply(lambda x: f"#{int(x)}"),
        textposition="top center"
    )
    
    fig.update_layout(
        height=380,
        yaxis=dict(
            tickmode="array",
            tickvals=[1, -1],
            ticktext=["Premier League", "Championship"],
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor="#999",
            range=[-1.5, 1.5],
            title=""
        ),
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # MONTH BY MONTH BREAKDOWN
    # ----------------------------
    st.divider()
    st.markdown("###### 📅 Month by month breakdown")

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

    monthly_stats = monthly_stats[monthly_stats["total_steps"] > 0]
    monthly_stats = monthly_stats.sort_values("month", ascending=False)

    monthly_stats["month"] = monthly_stats["month"].dt.strftime("%B %Y")
    monthly_stats["avg_steps"] = monthly_stats["avg_steps"].astype(int)

    monthly_stats = monthly_stats.rename(columns={
        "month": "Month",
        "total_steps": "Total steps",
        "avg_steps": "Average per day",
        "best_day": "Best single day",
        "days_10k": "Number of 10K days",
        "days_5k": "Number of 5K days"
    })

    st.dataframe(monthly_stats, use_container_width=True, hide_index=True)

# =========================================================
# 📜 LEAGUE HISTORY — HALL OF CHAMPIONS
# =========================================================
if page == "📜 League History":

    st.markdown("### 📜 League History")
    st.caption("The official record book of the Steps League")

    lh = league_history.copy()
    lh["Month"] = pd.to_datetime(lh["Month"])

    # Only months with real data
    valid = lh.groupby("Month")["points"].sum()
    months = sorted(valid[valid > 0].index, reverse=True)

    if not months:
        st.info("No league history available yet.")
        st.stop()

    # =====================================================
    # 🧠 LEAGUE HISTORY ENGINE (SEPARATED BY LEAGUE)
    # =====================================================
    
    champs = lh[lh["Champion"] == True].copy()
    champs = champs.sort_values("Month")
    
    engines = {}
    
    for league in ["Premier", "Championship"]:
    
        L = champs[champs["League"] == league].copy()
    
        # --- Titles ---
        title_counts = L["User"].value_counts()
    
        # --- Longest streaks ---
        latest_month = champs["Month"].max()
        streaks = []
        
        for user, g in champs.groupby("User"):
            g = g.sort_values("Month")
            current = longest = 1
            prev = None
            active_streak = False
        
            for m in g["Month"]:
                if prev is not None and (m.to_period("M") - prev.to_period("M")) == 1:
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 1
                prev = m
        
            # if user's latest title is in latest league month → streak is active
            if prev.to_period("M") == latest_month.to_period("M"):
                active_streak = True
        
            streaks.append((user, longest, active_streak))

    
        streak_df = pd.DataFrame(streaks, columns=["User","Streak","Active"]) \
              .sort_values("Streak", ascending=False)
    
        # --- Runner ups ---
        runners = lh[(lh["League"] == league) & (lh["Rank"] == 2)]["User"].value_counts()
    
        no_title = runners[~runners.index.isin(title_counts.index)]
    
        # --- Dynasties ---
        dyn = []
    
        for u, t in title_counts.items():
            s = streak_df[streak_df["User"] == u]["Streak"].max()
            if t >= 3 or s >= 3:
                dyn.append({
                    "League": league,
                    "User": u,
                    "Titles": int(t),
                    "Streak": int(s)
                })
    
        engines[league] = {
            "titles": title_counts,
            "streaks": streak_df,
            "runners": runners,
            "no_title": no_title,
            "dynasties": dyn
        }
    
    # Combined dynasties list for display
    dynasties = engines["Premier"]["dynasties"] + engines["Championship"]["dynasties"]

    prem_titles     = engines["Premier"]["titles"]
    prem_streaks    = engines["Premier"]["streaks"]
    prem_no_title   = engines["Premier"]["no_title"]
    
    champ_titles    = engines["Championship"]["titles"]
    champ_streaks   = engines["Championship"]["streaks"]
    champ_no_title  = engines["Championship"]["no_title"]

    # =====================================================
    # 🏟️ HALL BANNERS
    # =====================================================
    st.markdown("#### 🏟️ Hall of Champions")

    b1, b2, b3, b4, b5 = st.columns(5)
    all_streaks = pd.concat([
        prem_streaks.assign(League="Premier"),
        champ_streaks.assign(League="Championship")
    ])
    
    top = all_streaks.sort_values("Streak", ascending=False).iloc[0]
    star = " 🔥" if top["Active"] else ""

    with b1:
        if not prem_titles.empty:
            hall_card("🏅 Most Premier titles", name_with_status(prem_titles.index[0]), f"↑ {int(prem_titles.iloc[0])}")

    with b2:
        if not prem_streaks.empty:
            hall_card("🔥 Longest streak", name_with_status(top["User"]), f"{int(top['Streak'])} months{star}")
            st.caption("* Active streak")
    
    with b3:
        if not prem_no_title.empty:
            hall_card("⚔️ Premier runner-ups", prem_no_title.index[0], f"↑ {int(prem_no_title.iloc[0])}")
    
    with b4:
        if not champ_no_title.empty:
            hall_card("⚔️ Championship runner-ups", champ_no_title.index[0], f"↑ {int(champ_no_title.iloc[0])}")
    
    with b5:
        if dynasties:
            hall_card("👑 Dynasty", dynasties[0]["User"], "Legend status")

    st.divider()

    # =====================================================
    # 👑 DYNASTIES OF THE LEAGUE
    # =====================================================
    
    if dynasties:
        st.markdown("#### 👑 Dynasties of the League")
    
        prem = [d for d in dynasties if d["League"] == "Premier"]
        champ = [d for d in dynasties if d["League"] == "Championship"]
    
        if prem:
            st.markdown("##### 👑 Premier League Dynasties")
            for d in prem:
                st.markdown(f"""
                <div style="
                    background:#fff4d6;
                    padding:14px;
                    border-radius:14px;
                    margin-bottom:10px;
                    border-left:6px solid #f5c542;
                ">
                    👑 <b>{name_with_status(d['User'])}</b> — {d['Titles']} Premier titles | best streak {d['Streak']} months
                </div>
                """, unsafe_allow_html=True)
    
        if champ:
            st.markdown("##### 🏆 Championship Dynasties")
            for d in champ:
                st.markdown(f"""
                <div style="
                    background:#eef6ff;
                    padding:14px;
                    border-radius:14px;
                    margin-bottom:10px;
                    border-left:6px solid #4a90e2;
                ">
                    🏆 <b>{name_with_status(d['User'])}</b> — {d['Titles']} Championship titles | best streak {d['Streak']} months
                </div>
                """, unsafe_allow_html=True)
    
        st.divider()
        
    st.markdown("#### 📜 League Eras (periods of dominance)")

    eras = build_eras(league_history, min_streak=3)
    
    if eras.empty:
        st.info("No true eras yet — the league is still in its early chaos phase 😄")
    else:
        for _, e in eras.sort_values(["League","Titles"], ascending=[False,False]).iterrows():
    
            bg = "#fff4d6" if e["League"] == "Premier" else "#eef6ff"
            icon = "👑" if e["League"] == "Premier" else "🏆"
    
            st.markdown(f"""
            <div style="
                background:{bg};
                padding:14px;
                border-radius:14px;
                margin-bottom:10px;
                border-left:6px solid #6c8cff;
            ">
                {icon} <b>{name_with_status(e['Champion'])}</b> — {e['League']} League<br>
                {e['Start'].strftime("%b %Y")} → {e['End'].strftime("%b %Y")}  
                🔥 {e['Titles']} consecutive titles
            </div>
            """, unsafe_allow_html=True)

    # =====================================================
    # 📊 HISTORY TABLES (LAST 12 MONTHS)
    # =====================================================
    records = []

    for m in months:
        month_df = lh[lh["Month"] == m]

        for league in ["Premier", "Championship"]:
            league_df = month_df[month_df["League"] == league].sort_values("Rank")

            if len(league_df) < 2:
                continue

            winner = league_df.iloc[0]
            runner = league_df.iloc[1]

            records.append({
                "Month": m.strftime("%b %Y"),
                "League": league,
                "Winner": name_with_status(winner["User"]),
                "Winner Points": int(winner["points_display"]),
                "Runner-up": name_with_status(runner["User"]),
                "Runner-up Points": int(runner["points_display"])
            })

    history_df = pd.DataFrame(records)

    prem_hist = history_df[history_df["League"] == "Premier"].drop(columns=["League"])
    champ_hist = history_df[history_df["League"] == "Championship"].drop(columns=["League"])

    st.markdown("#### 🥇 Premier League — Last 12 months, scroll to see more")
    st.dataframe(prem_hist, use_container_width=True, hide_index=True, height=460)

    st.divider()

    st.markdown("#### 🥈 Championship — Last 12 months, scroll to see more")
    st.dataframe(champ_hist, use_container_width=True, hide_index=True, height=460)

    st.caption("🏆 Only winners and runner-ups are shown here. Full tables are in Monthly Results.")

    st.markdown("##### 📊 League flow timeline")
    
    flow = league_history.copy()
    flow["Month"] = pd.to_datetime(flow["Month"])
    
    fig = px.line(
        flow,
        x="Month",
        y="Rank",
        color="User",
        line_group="User",
        markers=True
    )
    
    fig.update_yaxes(autorange="reversed", title="Rank (1 = Champion)")
    fig.update_layout(
        height=550,
        xaxis_title="",
        yaxis_title="League rank",
        legend_title="Players"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

# =========================================================
# ℹ️ ABOUT — STEPS LEAGUE README
# =========================================================
if page == "ℹ️ Readme: Our Dashboard":

    st.markdown("### ℹ️ About the Steps League")
    st.caption("What this dashboard is, and how the league works")

    st.divider()

    st.markdown("###### 🚶 What is this?")
    st.markdown("""
The **Steps League** is a fun, community-driven fitness league built around one simple idea:

> _Move more. Stay consistent. And make it fun._

This dashboard tracks daily step data and turns it into:

• monthly competitions  
• leagues (Premier & Championship)  
• promotions & relegations  
• career records  
• hall of fame stats  

Think of it like **Fantasy Football meets Fitbit** 😄
""")

    st.divider()

    st.markdown("###### 🏟️ The League System")
    st.markdown("""
There are two leagues:

🥇 **Premier League** – the top division  
🥈 **Championship** – the second division  

Every month, players are placed into leagues based on their **average steps in the previous month**.

**How league placement works:**

• First month ever → everyone starts in Premier  
• If your previous month average ≥ **7,000 steps/day** → Premier  
• Otherwise → Championship  
• At least **6 players** are always kept in Premier  
• New players always start in Championship  

Promotions and relegations happen automatically every month.
""")

    st.divider()

    st.markdown("###### 🧮 How points are calculated")
    st.markdown("""
Monthly league winners are **not decided only by total steps**.

Each player earns points based on multiple aspects of performance:

• Total steps  
• Highest single day  
• Highest week  
• Number of 10K days  
• Number of daily wins  

These are combined using weighted scoring and normalized within the month.

The result is a **balanced score** that rewards:

• consistency  
• peak performance  
• staying active regularly  

This means someone who is steady all month can beat someone who only had a few big days.
""")

    st.divider()

    st.markdown("###### 🏆 What the pages show")
    st.markdown("""
#### 📅 Monthly Results
• Step winners  
• Monthly highlights  
• Premier & Championship tables  
• Champions of the month  
• Promotions & relegations  

#### 👤 Player Profile
• Career step stats  
• Streaks and records  
• Trophy cabinet  
• League journey over time  

#### 🏆 Hall of Fame
• All-time fitness records  
• League legends  
• Titles, streaks, dominance stats  

#### 📜 League History
• Full month-by-month archive  
• Past champions  
• Historical league tables  
""")

    st.divider()

    st.markdown("###### ❤️ Why this exists")
    st.markdown("""
This league exists to:

• make walking more fun  
• encourage consistency  
• celebrate improvement  
• build a healthy community habit  

Whether you're chasing trophies or just building a routine — every step counts 👣
""")

    st.success("If something looks wrong, confusing, or interesting — reach out to the league admin 😄")


