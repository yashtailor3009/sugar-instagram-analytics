"""Sugar Cosmetics - Instagram Performance Analytics (Streamlit + SQL)"""
import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import utils as u

BASE = Path(__file__).parent
LOGO = BASE / "assets" / "logo.png"

# ------------------------------------------------------------------ page + theme
st.set_page_config(
    page_title="Sugar Insights | Instagram Analytics",
    page_icon=str(BASE / "assets" / "favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

PINK, MAGENTA, PURPLE, GOLD, INK = "#FF3D8B", "#D1126B", "#6A0DAD", "#D9A93E", "#1B1B2F"
PALETTE = [MAGENTA, PURPLE, GOLD, PINK, "#2E86AB", "#7C3AED"]
SCALE = ["#FFE3EF", PINK, MAGENTA, PURPLE]


def img_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


LOGO_B64 = img_b64(LOGO)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {{ font-family: 'Poppins', sans-serif !important; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1400px; }}
#MainMenu, footer {{ visibility: hidden; }}

/* hero banner */
.hero {{ display:flex; align-items:center; gap:22px; padding:22px 30px; border-radius:24px;
        background: linear-gradient(120deg, #FF3D8B 0%, #D1126B 45%, #6A0DAD 100%);
        color:#fff; box-shadow: 0 14px 40px rgba(209,18,107,.28); margin-bottom: 18px; position:relative; overflow:hidden; }}
.hero:after {{ content:''; position:absolute; right:-60px; top:-60px; width:260px; height:260px; border-radius:50%;
              background: rgba(255,255,255,.10); }}
.hero img {{ width:84px; height:84px; border-radius:22px; box-shadow:0 8px 24px rgba(0,0,0,.25); }}
.hero h1 {{ margin:0; font-size:2rem; font-weight:800; letter-spacing:-.5px; color:#fff; padding:0; }}
.hero p  {{ margin:2px 0 0 0; opacity:.92; font-size:.98rem; }}
.pill {{ display:inline-block; padding:3px 12px; margin:8px 6px 0 0; border-radius:999px; font-size:.74rem;
        background:rgba(255,255,255,.18); border:1px solid rgba(255,255,255,.35); }}

/* KPI cards */
.kpi {{ background:#fff; border-radius:20px; padding:18px 20px; box-shadow:0 6px 22px rgba(27,27,47,.07);
       border:1px solid #F6D3E3; position:relative; overflow:hidden; transition: transform .2s, box-shadow .2s; height:100%; }}
.kpi:hover {{ transform: translateY(-4px); box-shadow:0 14px 30px rgba(209,18,107,.18); }}
.kpi:before {{ content:''; position:absolute; left:0; top:0; bottom:0; width:6px; background:linear-gradient(180deg,{PINK},{PURPLE}); }}
.kpi .ic {{ font-size:1.5rem; }}
.kpi .lb {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.08em; color:#8A7A88; font-weight:600; margin-top:2px; }}
.kpi .vl {{ font-size:1.85rem; font-weight:800; color:{INK}; line-height:1.15; }}
.kpi .sb {{ font-size:.78rem; color:{MAGENTA}; font-weight:500; }}

h2, h3 {{ color:{INK}; font-weight:700 !important; }}
.section-note {{ background:#fff; border-left:5px solid {MAGENTA}; border-radius:12px; padding:12px 16px;
                box-shadow:0 3px 14px rgba(27,27,47,.05); font-size:.9rem; margin:6px 0 14px 0; }}
.card {{ background:#fff; border-radius:20px; padding:16px 18px; border:1px solid #F6D3E3;
        box-shadow:0 6px 22px rgba(27,27,47,.06); height:100%; }}
.card h4 {{ margin:0 0 6px 0; color:{MAGENTA}; font-size:1rem; }}
.card ul {{ margin:0; padding-left:18px; font-size:.88rem; }}
.tag {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:.72rem; font-weight:600; margin-right:6px; }}
.tag.hi {{ background:#FFE3EF; color:{MAGENTA}; }} .tag.mid {{ background:#FFF3D6; color:#9A6B00; }} .tag.lo {{ background:#EEE5FA; color:{PURPLE}; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:8px; background:#fff; padding:8px; border-radius:18px; box-shadow:0 4px 16px rgba(27,27,47,.06); }}
.stTabs [data-baseweb="tab"] {{ border-radius:12px; padding:8px 16px; font-weight:600; height:auto; }}
.stTabs [aria-selected="true"] {{ background:linear-gradient(120deg,{PINK},{MAGENTA}); color:#fff !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: linear-gradient(180deg,#2A0A22 0%, #3A0F4F 100%); }}
section[data-testid="stSidebar"] * {{ color:#FBEAF3; }}
section[data-testid="stSidebar"] [data-baseweb="select"] * {{ color:{INK} !important; }}
section[data-testid="stSidebar"] .stButton button {{ background:{PINK}; color:#fff; border:none; border-radius:12px; font-weight:600; width:100%; }}
.stDownloadButton button, .stButton button[kind="primary"] {{ border-radius:12px; font-weight:600; }}
textarea {{ font-family: 'JetBrains Mono','Fira Code',monospace !important; font-size:.88rem !important; }}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ data
@st.cache_resource(show_spinner="Loading 50,000 posts into SQLite…")
def get_con():
    return u.build_connection(u.load_dataframe())


con = get_con()
MONTHS = u.q(con, "SELECT DISTINCT strftime('%Y-%m', post_date) AS m FROM posts ORDER BY m")["m"].tolist()
ALL_TYPES = u.q(con, "SELECT DISTINCT post_type AS v FROM posts ORDER BY v")["v"].tolist()
ALL_CAMPAIGNS = u.q(con, "SELECT DISTINCT campaign_type AS v FROM posts ORDER BY v")["v"].tolist()
ALL_SOURCES = u.q(con, "SELECT DISTINCT engagement_source AS v FROM posts ORDER BY v")["v"].tolist()

# ------------------------------------------------------------------ helpers

def show_chart(fig, **kw):
    """Full-width Plotly chart that works on old and new Streamlit versions."""
    try:
        st.plotly_chart(fig, width="stretch", **kw)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, **kw)


def show_df(df, **kw):
    """Full-width dataframe that works on old and new Streamlit versions."""
    try:
        st.dataframe(df, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kw)


def style(fig, h=380, legend=True):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Poppins, sans-serif", color=INK, size=12),
        margin=dict(l=10, r=10, t=50, b=10),
        title=dict(font=dict(size=16, color=INK)), showlegend=legend,
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False, linecolor="#EBCFDD")
    fig.update_yaxes(gridcolor="#F3E3EB", zeroline=False)
    return fig


def kpi(icon, label, value, sub=""):
    return f'<div class="kpi"><div class="ic">{icon}</div><div class="lb">{label}</div><div class="vl">{value}</div><div class="sb">{sub}</div></div>'


def human(n):
    n = float(n)
    for unit, d in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= d:
            return f"{n/d:,.2f}{unit}"
    return f"{n:,.0f}"


def note(text):
    st.markdown(f'<div class="section-note">{text}</div>', unsafe_allow_html=True)


def show_sql(sql_text):
    with st.expander("🧾 SQL behind this view"):
        st.code(sql_text.strip(), language="sql")


# ------------------------------------------------------------------ sidebar filters
with st.sidebar:
    st.image(str(LOGO), width=110)
    st.markdown("### Sugar Insights")
    st.caption("Instagram performance analytics")
    st.markdown("---")
    st.markdown("#### 🎛️ Filters")
    f_types = st.multiselect("Post type", ALL_TYPES, default=ALL_TYPES, key="f_types")
    f_camps = st.multiselect("Campaign type", ALL_CAMPAIGNS, default=ALL_CAMPAIGNS, key="f_camps")
    f_srcs = st.multiselect("Engagement source", ALL_SOURCES, default=ALL_SOURCES, key="f_srcs")
    f_months = st.select_slider("Month range", options=MONTHS, value=(MONTHS[0], MONTHS[-1]), key="f_months")
    f_tags = st.multiselect("Hashtag (posts using any)", u.HASHTAGS, default=[], key="f_tags",
                            placeholder="All hashtags")

    def _reset():
        for k in ("f_types", "f_camps", "f_srcs", "f_months", "f_tags"):
            st.session_state.pop(k, None)

    st.button("↺ Reset filters", on_click=_reset)
    st.markdown("---")
    st.caption("Data: 19 Apr 2024 – 19 Apr 2025 · Apr-2024 and Apr-2025 are partial months.")

if not (f_types and f_camps and f_srcs):
    st.warning("Select at least one value in Post type, Campaign type and Engagement source.")
    st.stop()

W, P = u.build_where(f_types, f_camps, f_srcs, f_months[0], f_months[1], f_tags)
K = u.kpis(con, W, P)
if not K["posts"]:
    st.warning("No posts match the current filters.")
    st.stop()

# ------------------------------------------------------------------ hero
active = []
if len(f_types) < len(ALL_TYPES): active.append("Type: " + ", ".join(f_types))
if len(f_camps) < len(ALL_CAMPAIGNS): active.append("Campaign: " + ", ".join(f_camps))
if len(f_srcs) < len(ALL_SOURCES): active.append("Source: " + ", ".join(f_srcs))
if f_tags: active.append("Hashtag: " + ", ".join(f_tags))
active.append(f"{f_months[0]} → {f_months[1]}")
pills = "".join(f'<span class="pill">{a}</span>' for a in active)
st.markdown(
    f"""<div class="hero"><img src="data:image/png;base64,{LOGO_B64}"/>
    <div><h1>Sugar Cosmetics · Instagram Insights</h1>
    <p>Engagement, content and growth analytics powered by SQL · {int(K['posts']):,} posts in view</p>{pills}</div></div>""",
    unsafe_allow_html=True,
)

tabs = st.tabs(["📊 Overview", "🏆 Top Posts", "🎬 Formats & Timing", "#️⃣ Hashtags", "📈 Growth", "💡 Strategy", "🧪 SQL Playground"])

# ================================================================== TAB 1 OVERVIEW
with tabs[0]:
    st.subheader("KPI Overview")
    c = st.columns(5)
    c[0].markdown(kpi("📝", "Total posts", f"{int(K['posts']):,}", "in selected view"), unsafe_allow_html=True)
    c[1].markdown(kpi("❤️", "Total likes", human(K["likes"]), f"{K['likes']/K['posts']:,.0f} per post"), unsafe_allow_html=True)
    c[2].markdown(kpi("💬", "Total comments", human(K["comments"]), f"{K['comments']/K['posts']:,.0f} per post"), unsafe_allow_html=True)
    c[3].markdown(kpi("👁️", "Total reach", human(K["reach"]), f"{K['reach']/K['posts']:,.0f} per post"), unsafe_allow_html=True)
    c[4].markdown(kpi("🔥", "Avg engagement rate", f"{K['er']:.2f}%", "(likes+comments+shares+saves) ÷ reach"), unsafe_allow_html=True)
    st.write("")
    c = st.columns(4)
    c[0].markdown(kpi("🔁", "Total shares", human(K["shares"])), unsafe_allow_html=True)
    c[1].markdown(kpi("🔖", "Total saves", human(K["saves"])), unsafe_allow_html=True)
    c[2].markdown(kpi("🙋", "Profile visits", human(K["visits"]), f"{K['follows']/K['visits']*100:.1f}% convert to follow"), unsafe_allow_html=True)
    c[3].markdown(kpi("➕", "New follows", human(K["follows"]), f"{K['follows']/K['posts']:,.0f} per post"), unsafe_allow_html=True)
    st.write("")

    L, R = st.columns([1.25, 1])
    with L:
        m = u.monthly(con, W, P)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=m["month"], y=m["posts"], name="Posts", marker_color="#F9B8D3",
                             hovertemplate="%{x}<br>%{y:,} posts<extra></extra>"), secondary_y=False)
        fig.add_trace(go.Scatter(x=m["month"], y=m["er"], name="Avg ER %", mode="lines+markers",
                                 line=dict(color=PURPLE, width=3), marker=dict(size=8),
                                 hovertemplate="%{x}<br>ER %{y:.2f}%<extra></extra>"), secondary_y=True)
        fig.update_layout(title="Monthly posting trend & engagement rate")
        fig.update_yaxes(title_text="Posts", secondary_y=False)
        fig.update_yaxes(title_text="Engagement rate %", secondary_y=True, showgrid=False)
        show_chart(style(fig, 400))
    with R:
        f = u.funnel(con, W, P)
        colors = [PURPLE, MAGENTA, PINK, "#FF7FB2", GOLD, "#F2C96B"]
        fig = go.Figure(go.Funnel(y=f["stage"], x=f["total"], textposition="inside",
                                  textinfo="value+percent initial", marker=dict(color=colors),
                                  connector=dict(line=dict(color="#F3E3EB"))))
        fig.update_layout(title="Engagement funnel (Impressions → Saves)")
        show_chart(style(fig, 400, legend=False))
    note("<b>How to read:</b> posting volume is steady at ~3,900–4,300 posts/month (Apr-24 and Apr-25 are partial months). "
         "Of every 100 impressions, ~77 are unique reach; of reached accounts ~15% like, ~1.9% comment, ~0.8% share and ~0.9% save.")
    show_sql("""-- Task 2 & 7 (filters injected into WHERE)
SELECT strftime('%Y-%m', post_date) AS month, COUNT(*) AS posts, AVG((likes+comments+shares+saves)*100.0/reach) AS er
FROM posts WHERE <filters> GROUP BY month ORDER BY month;
SELECT 'Impressions', SUM(impressions) FROM posts UNION ALL SELECT 'Reach', SUM(reach) ... UNION ALL SELECT 'Saves', SUM(saves);""")

# ================================================================== TAB 2 TOP POSTS
with tabs[1]:
    st.subheader("Top 10 posts")
    note("The dataset has no caption column, so each post is labelled <b>#id · format · campaign</b>. "
         "Compare the two lists to find <b>hidden gems</b>: posts with modest likes but outsized engagement relative to reach.")
    a, b = st.columns(2)
    for col, by, title, colr in ((a, "likes", "Top 10 by likes", MAGENTA), (b, "er", "Top 10 by engagement rate (reach ≥ 1,000)", PURPLE)):
        with col:
            t = u.top_posts(con, W, P, by)
            xcol = "likes" if by == "likes" else "er"
            fig = go.Figure(go.Bar(
                x=t[xcol], y=t["label"], orientation="h", marker_color=colr,
                text=t[xcol].map(lambda v: f"{v:,.0f}" if by == "likes" else f"{v:.1f}%"), textposition="outside",
                customdata=t[["post_date", "hashtags", "reach", "likes"]].values,
                hovertemplate="<b>%{y}</b><br>Date %{customdata[0]}<br>%{customdata[1]}<br>Reach %{customdata[2]:,}<br>Likes %{customdata[3]:,}<extra></extra>"))
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(title=title)
            show_chart(style(fig, 440, legend=False))
            show = t[["post_id", "post_date", "post_type", "campaign_type", "hashtags", "likes", "reach", "er"]].copy()
            show["er"] = show["er"].round(2)
            show.columns = ["Post", "Date", "Type", "Campaign", "Hashtags", "Likes", "Reach", "ER %"]
            show_df(show, hide_index=True)
    t1 = u.top_posts(con, W, P, "likes")
    t2 = u.top_posts(con, W, P, "er")
    st.markdown("##### What the winners have in common")
    cc = st.columns(2)
    cc[0].info(f"Top-likes posts: most common campaign **{t1['campaign_type'].mode().iat[0]}**, most common format **{t1['post_type'].mode().iat[0]}**, "
               f"median reach **{t1['reach'].median():,.0f}**.")
    cc[1].success(f"Top-ER posts: most common campaign **{t2['campaign_type'].mode().iat[0]}**, most common format **{t2['post_type'].mode().iat[0]}**, "
                  f"median reach **{t2['reach'].median():,.0f}** - smaller reach, tighter engagement.")
    show_sql("""SELECT post_id, post_date, post_type, campaign_type, hashtags, likes, reach,
       (likes+comments+shares+saves)*100.0/reach AS er
FROM posts WHERE <filters> [AND reach >= 1000]
ORDER BY likes DESC   -- or: ORDER BY er DESC
LIMIT 10;""")

# ================================================================== TAB 3 FORMATS & TIMING
with tabs[2]:
    st.subheader("Post type performance")
    d = u.by_dimension(con, W, P, "post_type")
    mets = [("likes", "Avg likes"), ("comments", "Avg comments"), ("shares", "Avg shares"), ("saves", "Avg saves")]
    fig = make_subplots(rows=1, cols=4, subplot_titles=[m[1] for m in mets])
    for i, (k, lbl) in enumerate(mets, 1):
        fig.add_trace(go.Bar(x=d["grp"], y=d[k], marker_color=PALETTE[:len(d)], text=d[k].round(0),
                             textposition="outside", showlegend=False,
                             hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"), row=1, col=i)
        fig.update_yaxes(range=[0, d[k].max() * 1.22], row=1, col=i)
    show_chart(style(fig, 360, legend=False))

    c1, c2 = st.columns([1, 1])
    with c1:
        er = d.sort_values("er")
        fig = go.Figure(go.Bar(x=er["er"], y=er["grp"], orientation="h", marker_color=MAGENTA,
                               text=er["er"].map("{:.2f}%".format), textposition="outside"))
        lo = max(0, er["er"].min() - 1.0)
        fig.update_xaxes(range=[lo, er["er"].max() + 0.6])
        fig.update_layout(title="Avg engagement rate by post type (axis zoomed)")
        show_chart(style(fig, 330, legend=False))
    with c2:
        tc = u.type_campaign(con, W, P).pivot(index="post_type", columns="campaign_type", values="er")
        fig = px.imshow(tc, text_auto=".2f", aspect="auto", color_continuous_scale=SCALE)
        fig.update_layout(title="Engagement rate: format × campaign", coloraxis_colorbar=dict(title="ER %"))
        show_chart(style(fig, 330, legend=False))

    st.markdown("---")
    st.subheader("Day-of-week analysis")
    mlabel = st.radio("Metric", list(u.METRICS.keys()), horizontal=True, key="dow_metric")
    mcol = {"Engagement Rate (%)": "er", "Avg Likes": "likes", "Avg Comments": "comments", "Avg Shares": "shares",
            "Avg Saves": "saves", "Avg Reach": "reach", "Avg Follows": "follows"}[mlabel]
    wd = u.by_weekday(con, W, P)
    lo, hi = wd[mcol].min(), wd[mcol].max()
    colors = [MAGENTA if v == hi else ("#C9B6E8" if v == lo else "#F9B8D3") for v in wd[mcol]]
    c1, c2 = st.columns([1.4, 1])
    with c1:
        fig = go.Figure(go.Bar(x=wd["weekday"], y=wd[mcol], marker_color=colors,
                               text=wd[mcol].map(lambda v: f"{v:.2f}" if mcol == "er" else f"{v:,.0f}"),
                               textposition="outside"))
        pad = (hi - lo) * 0.25 + 1e-9
        fig.update_yaxes(range=[max(0, lo - pad * 2), hi + pad * 1.5])
        fig.update_layout(title=f"{mlabel} by weekday (best = magenta, lowest = lilac; axis zoomed)")
        show_chart(style(fig, 380, legend=False))
    with c2:
        fig = px.bar(wd, x="weekday", y="posts", color_discrete_sequence=[PURPLE], title="Posts published by weekday")
        show_chart(style(fig, 380, legend=False))
    spread = (hi - lo) / wd[mcol].mean() * 100
    best, worst = wd.loc[wd[mcol].idxmax(), "weekday"], wd.loc[wd[mcol].idxmin(), "weekday"]
    note(f"<b>{best}</b> is highest and <b>{worst}</b> lowest for {mlabel.lower()}, but the gap is only <b>{spread:.1f}%</b> of the average - "
         "weekday is a weak lever in this data (no posting-hour column is available).")
    show_sql("""SELECT CASE strftime('%w', post_date) WHEN '0' THEN 'Sunday' ... END AS weekday,
       AVG((likes+comments+shares+saves)*100.0/reach) AS er
FROM posts WHERE <filters> GROUP BY strftime('%w', post_date);""")

# ================================================================== TAB 4 HASHTAGS
with tabs[3]:
    st.subheader("Hashtag analysis")
    h = u.hashtag_stats(con, W, P)
    hm = st.radio("Rank hashtags by", ["Engagement rate (%)", "Avg reach", "Avg likes", "Avg follows", "Times used"], horizontal=True)
    col = {"Engagement rate (%)": "er", "Avg reach": "reach", "Avg likes": "likes", "Avg follows": "follows", "Times used": "uses"}[hm]
    hs = h.sort_values(col)
    c1, c2 = st.columns([1.3, 1])
    with c1:
        lo = hs[col].min(); hi = hs[col].max()
        fig = go.Figure(go.Bar(x=hs[col], y=hs["hashtag"], orientation="h", marker_color=MAGENTA,
                               text=hs[col].map(lambda v: f"{v:.2f}" if col == "er" else f"{v:,.0f}"), textposition="outside"))
        fig.update_xaxes(range=[max(0, lo - (hi - lo) * 1.5 - 1e-9), hi + (hi - lo) * 0.8 + 1e-9])
        fig.update_layout(title=f"{hm} by hashtag (axis zoomed)")
        show_chart(style(fig, 360, legend=False))
    with c2:
        fig = px.pie(h, names="hashtag", values="uses", hole=.55, color_discrete_sequence=PALETTE, title="Share of hashtag usage")
        fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:,} uses<extra></extra>")
        show_chart(style(fig, 360))

    c1, c2 = st.columns(2)
    with c1:
        n = u.hashtag_count(con, W, P)
        fig = go.Figure(go.Bar(x=n["n_tags"].astype(str) + " hashtag(s)", y=n["er"], marker_color=[PINK, MAGENTA, PURPLE][:len(n)],
                               text=n["er"].map("{:.2f}%".format), textposition="outside"))
        fig.update_yaxes(range=[max(0, n["er"].min() - 0.8), n["er"].max() + 0.4])
        fig.update_layout(title="Does the number of hashtags matter? (ER %)")
        show_chart(style(fig, 340, legend=False))
    with c2:
        combos = u.hashtag_combos(con, W, P, min_posts=max(30, int(K["posts"] * 0.004)))
        st.markdown("**Top hashtag combinations** (min. sample size applied)")
        if len(combos):
            cdf = combos.copy(); cdf["er"] = cdf["er"].round(2); cdf["reach"] = cdf["reach"].round(0)
            cdf.columns = ["Hashtags", "Posts", "ER %", "Avg reach"]
            show_df(cdf, hide_index=True, height=290)
        else:
            st.info("Not enough posts per combination under the current filters.")
    note("Hashtags sit within a narrow band of engagement. Combination-level gaps are larger but rest on small samples (~800 posts) - treat them as <b>hypotheses to A/B test</b>.")
    show_sql("""WITH RECURSIVE split(post_id, tag, rest) AS (
  SELECT post_id, '', hashtags || ',' FROM posts WHERE <filters>
  UNION ALL
  SELECT post_id, TRIM(SUBSTR(rest,1,INSTR(rest,',')-1)), SUBSTR(rest,INSTR(rest,',')+1)
  FROM split WHERE rest <> '')
SELECT s.tag, COUNT(*) AS uses, AVG(p.reach), AVG((p.likes+p.comments+p.shares+p.saves)*100.0/p.reach) AS er
FROM split s JOIN posts p USING (post_id) WHERE s.tag <> '' GROUP BY s.tag;""")

# ================================================================== TAB 5 GROWTH
with tabs[4]:
    st.subheader("Audience growth & conversion")
    m = u.monthly(con, W, P)
    m["cum"] = m["follows"].cumsum()
    m["conv"] = m["follows"] / m["visits"] * 100
    full = m.iloc[1:-1] if len(m) > 2 else m
    c1, c2 = st.columns(2)
    with c1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=m["month"], y=m["follows"], name="New follows", marker_color="#F9B8D3"), secondary_y=False)
        fig.add_trace(go.Scatter(x=m["month"], y=m["cum"], name="Cumulative", mode="lines+markers",
                                 line=dict(color=MAGENTA, width=3)), secondary_y=True)
        fig.update_layout(title="New follows per month & cumulative total")
        fig.update_yaxes(secondary_y=True, showgrid=False)
        show_chart(style(fig, 380))
    with c2:
        fig = px.line(m, x="month", y="conv", markers=True, color_discrete_sequence=[PURPLE],
                      title="Profile-visit → follow conversion (%)")
        fig.update_yaxes(range=[max(0, m["conv"].min() - 3), m["conv"].max() + 3])
        show_chart(style(fig, 380, legend=False))
    c1, c2 = st.columns(2)
    with c1:
        rt = u.reach_tiers(con, W, P)
        fig = go.Figure(go.Bar(x=rt["tier"].str[3:], y=rt["follows_per_100_reach"], marker_color=PALETTE[:len(rt)],
                               text=rt["follows_per_100_reach"].map("{:.2f}".format), textposition="outside"))
        fig.update_yaxes(range=[0, rt["follows_per_100_reach"].max() * 1.3])
        fig.update_layout(title="New follows per 100 accounts reached, by reach tier")
        show_chart(style(fig, 340, legend=False))
    with c2:
        src = u.by_dimension(con, W, P, "engagement_source")
        fig = go.Figure(go.Bar(x=src["grp"], y=src["reach"], marker_color=[MAGENTA, PURPLE, GOLD, PINK][:len(src)],
                               text=src["reach"].map("{:,.0f}".format), textposition="outside"))
        fig.update_yaxes(range=[src["reach"].min() * 0.9, src["reach"].max() * 1.04])
        fig.update_layout(title="Avg reach per post by engagement source")
        show_chart(style(fig, 340, legend=False))
    if len(full) > 1:
        slope = (full["follows"].iloc[-1] - full["follows"].iloc[0]) / full["follows"].iloc[0] * 100
        note(f"Across full months, new follows move only <b>{slope:+.1f}%</b> from first to last - growth is <b>steady rather than accelerating</b>. "
             f"Conversion from profile visit to follow holds near <b>{full['conv'].mean():.1f}%</b>; the lever for growth is getting more people to the profile, not converting those who arrive.")
    show_sql("""SELECT strftime('%Y-%m', post_date) AS month, SUM(follows) AS new_follows,
       SUM(SUM(follows)) OVER (ORDER BY strftime('%Y-%m', post_date)) AS cumulative_follows
FROM posts WHERE <filters> GROUP BY month;""")

# ================================================================== TAB 6 STRATEGY
with tabs[5]:
    st.subheader("Strategic recommendations")
    allw, allp = u.build_where(ALL_TYPES, ALL_CAMPAIGNS, ALL_SOURCES, MONTHS[0], MONTHS[-1], [])
    gt, gw, gc, gs = (u.by_dimension(con, allw, allp, d) for d in ("post_type", "post_type", "campaign_type", "engagement_source"))
    wk = u.by_weekday(con, allw, allp)
    hh = u.hashtag_stats(con, allw, allp)
    nn = u.hashtag_count(con, allw, allp)
    K0 = u.kpis(con, allw, allp)
    note(f"<b>Headline:</b> the account is healthy (avg ER <b>{K0['er']:.1f}%</b>, <b>{human(K0['reach'])}</b> reach) and performance is <b>remarkably uniform</b>. "
         f"Best vs worst format differ by only <b>{gt['er'].max()-gt['er'].min():.2f} pp</b>, weekdays by <b>{wk['er'].max()-wk['er'].min():.2f} pp</b>, "
         f"hashtags by <b>{hh['er'].max()-hh['er'].min():.2f} pp</b>. One-way ANOVA tests (see PDF report) show none of these gaps is statistically significant at 5%. "
         "So the strategy below prioritises <b>experiments and volume levers</b> over chasing a 'winner'.")
    r1 = st.columns(3)
    r1[0].markdown(f"""<div class="card"><h4>🎯 Key takeaways</h4><ul>
    <li>{int(K0['posts']):,} posts → {human(K0['likes'])} likes, {human(K0['comments'])} comments, {K0['er']:.2f}% avg ER</li>
    <li>Content mix is balanced (~25% each format) and engagement share mirrors it</li>
    <li>Funnel: only <b>{K0['shares']/K0['reach']*100:.1f}% share</b> and <b>{K0['saves']/K0['reach']*100:.1f}% save</b> vs <b>{K0['likes']/K0['reach']*100:.1f}% like</b> - high-intent actions are the gap</li>
    <li>Follows ≈ {K0['follows']/K0['posts']:.0f}/post, flat month to month</li></ul></div>""", unsafe_allow_html=True)
    r1[1].markdown(f"""<div class="card"><h4>🗓️ Posting strategy</h4><ul>
    <li><span class="tag mid">Timing</span>Keep a daily cadence; {wk.loc[wk['er'].idxmax(),'weekday']} leads ER ({wk['er'].max():.2f}%) but the edge is small</li>
    <li><span class="tag hi">Format</span>Hold the 4-format mix; lean slightly to {gt.iloc[0]['grp']}s ({gt.iloc[0]['er']:.2f}% ER) and test, don't switch</li>
    <li><span class="tag lo">Hashtags</span>Use 2-3 tags; {int(nn.loc[nn['er'].idxmax(),'n_tags'])}-tag posts lead ({nn['er'].max():.2f}%) vs 1 tag ({nn.iloc[0]['er']:.2f}%)</li>
    <li><span class="tag mid">Source</span>Organic reach per post ({gs.set_index('grp').loc['Organic','reach']:,.0f}) is already on par with paid / collab</li></ul></div>""", unsafe_allow_html=True)
    r1[2].markdown(f"""<div class="card"><h4>🚀 Improve engagement & growth</h4><ul>
    <li>Add save/share hooks: checklists, "send to a friend" CTAs, tutorial series</li>
    <li>Push profile visits ("link in bio", collab tags) - {K0['follows']/K0['visits']*100:.0f}% of visitors already follow</li>
    <li>Once publish-time data exists, test morning vs evening slots</li>
    <li>Scale the top-ER playbooks (Story × Tutorial, Reel × Influencer Collab) and re-measure</li></ul></div>""", unsafe_allow_html=True)
    st.write("")
    r2 = st.columns(2)
    r2[0].markdown("""<div class="card"><h4>🕳️ Gaps & how to close them</h4><ul>
    <li><b>No posting-hour field</b> → capture publish time to find true peak slots</li>
    <li><b>No captions / creative metadata</b> → add caption, CTA, hook and length to analyse copy</li>
    <li><b>No cost data</b> → add spend per post to compute ROI by source</li>
    <li><b>No Carousel type</b> → carousels are an Instagram save-driver; add and test them</li>
    <li><b>No follower baseline</b> → track followers daily to measure true growth rate</li>
    <li><b>Volume ≈ 137 posts/day</b> suggests aggregated or multi-account data → confirm the grain with the data owner</li></ul></div>""", unsafe_allow_html=True)
    r2[1].markdown("""<div class="card"><h4>💄 Campaign ideas aligned with brand goals</h4><ul>
    <li><b>#SugarTutorialSeries</b> - 5-part Story/Reel tutorials with a save-worthy checklist end card</li>
    <li><b>Collab Giveaways</b> - creator co-hosted giveaways (share-to-enter) to lift shares and follows</li>
    <li><b>#BoldLooks × #MakeupGoals UGC</b> - fans post looks; feature the best weekly (this tag pair tops ER in the data, n≈760 - validate)</li>
    <li><b>Vegan & Cruelty-Free Explained</b> - values-led education to differentiate the brand</li>
    <li><b>Festive refresh</b> - Festive Offer has the lowest ER; re-brief creative using Reels + collab voices</li></ul></div>""", unsafe_allow_html=True)
    st.write("")
    st.markdown("##### 🧪 Proposed 4-week experiment plan")
    show_df(pd.DataFrame({
        "Test": ["Save/share CTA end-cards", "2 vs 3 hashtags", "Reel vs Story tutorial", "Collab vs Organic giveaway"],
        "Hypothesis": ["CTA lifts saves+shares per reach by ≥10%", "3 tags beat 1-2 on reach", "Story tutorials hold ER ≥ Reels", "Collab giveaways add ≥10% follows/post"],
        "Primary KPI": ["(shares+saves)/reach", "Reach per post", "ER %", "Follows per post"],
        "Success rule": ["p < 0.05, n ≥ 500/arm", "p < 0.05", "Non-inferiority", "p < 0.05"]}),
        hide_index=True)

# ================================================================== TAB 7 SQL PLAYGROUND
with tabs[6]:
    st.subheader("🧪 Live SQL Playground")
    note("Query the <code>posts</code> table in a live in-memory SQLite database (50,000 rows). The sandbox is <b>read-only</b> - only <code>SELECT</code>/<code>WITH</code> queries run. "
         "Use <b>Ctrl+Enter</b> in the editor, or press <b>Run query</b>.")
    if "sql_text" not in st.session_state:
        st.session_state["sql_text"] = u.EXAMPLES["Task 5 - Post type comparison"]
    if "history" not in st.session_state:
        st.session_state["history"] = []

    def _load_example():
        st.session_state["sql_text"] = u.EXAMPLES[st.session_state["example_pick"]]

    left, right = st.columns([2.3, 1])
    with right:
        st.selectbox("📚 Example queries", list(u.EXAMPLES.keys()), key="example_pick", on_change=_load_example, index=4)
        with st.expander("🗂️ Table schema: posts", expanded=True):
            show_df(pd.DataFrame(u.SCHEMA, columns=["Column", "Type", "Description"]), hide_index=True, height=300)
        st.caption("Engagement rate = (likes+comments+shares+saves) × 100 / reach")
        if u.SQL_FILE.exists():
            st.download_button("⬇️ Download full analysis .sql", u.SQL_FILE.read_bytes(), file_name="sugar_instagram_analysis.sql", mime="text/plain")
    with left:
        st.text_area("SQL editor", key="sql_text", height=260, label_visibility="collapsed")
        b1, b2, _ = st.columns([1, 1, 3])
        run = b1.button("▶ Run query", type="primary")
        def _clear():
            st.session_state["sql_text"] = ""
            st.session_state["ran_once"] = False

        b2.button("🧹 Clear", on_click=_clear)

        if run or st.session_state.get("ran_once"):
            st.session_state["ran_once"] = True
            try:
                res, secs, trunc = u.run_user_sql(con, st.session_state["sql_text"])
                if run:
                    hist = st.session_state["history"]
                    hist.insert(0, st.session_state["sql_text"].strip())
                    st.session_state["history"] = list(dict.fromkeys(hist))[:6]
                st.success(f"✅ {len(res):,} row(s) · {len(res.columns)} column(s) · {secs*1000:.1f} ms" + (" · result capped at 5,000 rows" if trunc else ""))
                show_df(res, hide_index=True, height=min(420, 60 + 35 * len(res)))
                st.download_button("⬇️ Download result as CSV", res.to_csv(index=False).encode(), file_name="query_result.csv", mime="text/csv")

                num_cols = res.select_dtypes("number").columns.tolist()
                if len(res) > 1 and len(res.columns) >= 2 and num_cols:
                    st.markdown("##### 📊 Instant chart")
                    cc = st.columns(4)
                    ctype = cc[0].selectbox("Chart", ["Bar", "Line", "Scatter", "Pie"], key="pg_ctype")
                    xcol = cc[1].selectbox("X / labels", res.columns.tolist(), key="pg_x")
                    ycols = cc[2].multiselect("Y / values", num_cols, default=[c for c in num_cols if c != xcol][:1], key="pg_y")
                    if ycols:
                        try:
                            if ctype == "Bar":
                                fig = px.bar(res, x=xcol, y=ycols, barmode="group", color_discrete_sequence=PALETTE)
                            elif ctype == "Line":
                                fig = px.line(res, x=xcol, y=ycols, markers=True, color_discrete_sequence=PALETTE)
                            elif ctype == "Scatter":
                                fig = px.scatter(res, x=xcol, y=ycols[0], color_discrete_sequence=PALETTE)
                            else:
                                fig = px.pie(res, names=xcol, values=ycols[0], hole=.45, color_discrete_sequence=PALETTE)
                            show_chart(style(fig, 380))
                        except Exception as ex:  # noqa: BLE001
                            st.info(f"Could not draw that chart: {ex}")
            except Exception as ex:  # noqa: BLE001
                st.error(f"⚠️ {ex}")
        if st.session_state["history"]:
            with st.expander("🕘 Recent queries"):
                for i, h_sql in enumerate(st.session_state["history"]):
                    st.code(h_sql, language="sql")
