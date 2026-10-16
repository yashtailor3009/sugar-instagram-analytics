"""Data + SQL layer for the Sugar Cosmetics Instagram Analytics app.
Kept free of Streamlit imports so it can be unit-tested on its own."""
from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
DATA_FILE = BASE / "data" / "sugar_instagram_clean.csv"
SQL_FILE = BASE / "data" / "sugar_instagram_analysis.sql"

ER = "(likes+comments+shares+saves)*100.0/reach"   # engagement-rate expression (% of reach)

HASHTAGS = ["#BoldLooks", "#CrueltyFree", "#MakeupGoals", "#SugarCosmetics", "#VeganBeauty"]

# label -> SQL aggregate used by the metric toggles
METRICS = {
    "Engagement Rate (%)": f"AVG({ER})",
    "Avg Likes": "AVG(likes)",
    "Avg Comments": "AVG(comments)",
    "Avg Shares": "AVG(shares)",
    "Avg Saves": "AVG(saves)",
    "Avg Reach": "AVG(reach)",
    "Avg Follows": "AVG(follows)",
}

SCHEMA = [
    ("post_id", "INTEGER", "Unique row id added during cleaning"),
    ("post_date", "TEXT (YYYY-MM-DD)", "Date the post was published"),
    ("post_type", "TEXT", "Image / Reel / Story / Video"),
    ("campaign_type", "TEXT", "Giveaway, Tutorial, Product Launch, Festive Offer, Influencer Collab"),
    ("hashtags", "TEXT", "Comma separated hashtags used (1-3 per post)"),
    ("audience_emotion", "TEXT", "Dominant audience emotion tag"),
    ("engagement_source", "TEXT", "Organic / Paid / Influencer / Collab"),
    ("impressions", "INTEGER", "Total views incl. repeats"),
    ("reach", "INTEGER", "Unique accounts reached"),
    ("likes", "INTEGER", "Likes"),
    ("comments", "INTEGER", "Comments"),
    ("shares", "INTEGER", "Shares"),
    ("saves", "INTEGER", "Saves"),
    ("profile_visits", "INTEGER", "Profile visits driven by the post"),
    ("follows", "INTEGER", "New follows driven by the post"),
]

EXAMPLES = {
    "Task 1 - KPI overview": f"""SELECT COUNT(*) AS total_posts,
       SUM(likes) AS total_likes,
       SUM(comments) AS total_comments,
       SUM(reach) AS total_reach,
       ROUND(AVG({ER}), 2) AS avg_engagement_rate_pct
FROM posts;""",
    "Task 2 - Monthly posting trend": f"""SELECT strftime('%Y-%m', post_date) AS month_year,
       COUNT(*) AS posts,
       ROUND(AVG({ER}), 2) AS avg_er_pct
FROM posts
GROUP BY month_year
ORDER BY month_year;""",
    "Task 3 - Top 10 posts by likes": f"""SELECT post_id, post_date, post_type, campaign_type, hashtags,
       likes, reach, ROUND({ER}, 2) AS er_pct
FROM posts
ORDER BY likes DESC
LIMIT 10;""",
    "Task 4 - Top 10 posts by engagement rate": f"""SELECT post_id, post_date, post_type, campaign_type, reach, likes,
       ROUND({ER}, 2) AS er_pct
FROM posts
WHERE reach >= 1000
ORDER BY er_pct DESC
LIMIT 10;""",
    "Task 5 - Post type comparison": f"""SELECT post_type,
       COUNT(*) AS posts,
       ROUND(AVG(likes)) AS avg_likes,
       ROUND(AVG(comments)) AS avg_comments,
       ROUND(AVG(shares)) AS avg_shares,
       ROUND(AVG(saves)) AS avg_saves,
       ROUND(AVG({ER}), 2) AS avg_er_pct
FROM posts
GROUP BY post_type
ORDER BY avg_er_pct DESC;""",
    "Task 6 - Day of week": f"""SELECT CASE strftime('%w', post_date)
         WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
         WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
         ELSE 'Saturday' END AS weekday,
       COUNT(*) AS posts,
       ROUND(AVG({ER}), 2) AS avg_er_pct
FROM posts
GROUP BY strftime('%w', post_date)
ORDER BY (CAST(strftime('%w', post_date) AS INTEGER) + 6) % 7;""",
    "Task 7 - Engagement funnel": """SELECT 'Impressions' AS stage, SUM(impressions) AS total FROM posts
UNION ALL SELECT 'Reach',    SUM(reach)    FROM posts
UNION ALL SELECT 'Likes',    SUM(likes)    FROM posts
UNION ALL SELECT 'Comments', SUM(comments) FROM posts
UNION ALL SELECT 'Shares',   SUM(shares)   FROM posts
UNION ALL SELECT 'Saves',    SUM(saves)    FROM posts;""",
    "Task 8 - Hashtag performance (recursive split)": f"""WITH RECURSIVE split(post_id, tag, rest) AS (
  SELECT post_id, '', hashtags || ',' FROM posts
  UNION ALL
  SELECT post_id, TRIM(SUBSTR(rest, 1, INSTR(rest, ',') - 1)), SUBSTR(rest, INSTR(rest, ',') + 1)
  FROM split WHERE rest <> ''
)
SELECT s.tag AS hashtag, COUNT(*) AS times_used,
       ROUND(AVG(p.reach)) AS avg_reach,
       ROUND(AVG((p.likes+p.comments+p.shares+p.saves)*100.0/p.reach), 2) AS avg_er_pct
FROM split s JOIN posts p USING (post_id)
WHERE s.tag <> ''
GROUP BY s.tag
ORDER BY avg_er_pct DESC;""",
    "Campaign type performance": f"""SELECT campaign_type, COUNT(*) AS posts,
       ROUND(AVG({ER}), 2) AS avg_er_pct,
       ROUND(AVG(follows), 1) AS avg_follows
FROM posts
GROUP BY campaign_type
ORDER BY avg_er_pct DESC;""",
    "Organic vs Paid vs Influencer": f"""SELECT engagement_source, COUNT(*) AS posts,
       ROUND(AVG(reach)) AS avg_reach,
       ROUND(AVG({ER}), 2) AS avg_er_pct
FROM posts
GROUP BY engagement_source
ORDER BY avg_er_pct DESC;""",
    "Cumulative follower growth (window fn)": """SELECT strftime('%Y-%m', post_date) AS month_year,
       SUM(follows) AS new_follows,
       SUM(SUM(follows)) OVER (ORDER BY strftime('%Y-%m', post_date)) AS cumulative_follows
FROM posts
GROUP BY month_year
ORDER BY month_year;""",
    "Month-over-month change (LAG)": """WITH m AS (
  SELECT strftime('%Y-%m', post_date) AS month_year, COUNT(*) AS posts
  FROM posts GROUP BY 1
)
SELECT month_year, posts,
       ROUND((posts - LAG(posts) OVER (ORDER BY month_year)) * 100.0
             / LAG(posts) OVER (ORDER BY month_year), 1) AS mom_change_pct
FROM m;""",
    "Blank editor - write your own": "SELECT * FROM posts LIMIT 20;",
}


# ----------------------------------------------------------------- loading
def load_dataframe() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    df["post_date"] = pd.to_datetime(df["post_date"]).dt.strftime("%Y-%m-%d")
    return df


def build_connection(df: pd.DataFrame) -> sqlite3.Connection:
    """In-memory SQLite database, locked to read-only after loading."""
    con = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("posts", con, index=False, if_exists="replace")
    con.execute("CREATE INDEX idx_date ON posts(post_date)")
    con.execute("CREATE INDEX idx_type ON posts(post_type)")
    con.commit()
    con.execute("PRAGMA query_only = ON")        # no writes possible from the playground
    return con


# ----------------------------------------------------------------- filters
def build_where(post_types, campaigns, sources, m_from, m_to, hashtags) -> tuple[str, dict]:
    """Return (WHERE clause, named params) for the sidebar filters."""
    conds, params = [], {}

    def in_clause(col, values, prefix):
        keys = []
        for i, v in enumerate(values):
            k = f"{prefix}{i}"
            params[k] = v
            keys.append(f":{k}")
        conds.append(f"{col} IN ({', '.join(keys)})")

    in_clause("post_type", post_types, "pt")
    in_clause("campaign_type", campaigns, "cp")
    in_clause("engagement_source", sources, "es")
    params["m_from"], params["m_to"] = m_from, m_to
    conds.append("strftime('%Y-%m', post_date) BETWEEN :m_from AND :m_to")
    if hashtags:
        ors = []
        for i, h in enumerate(hashtags):
            params[f"h{i}"] = f"%{h}%"
            ors.append(f"hashtags LIKE :h{i}")
        conds.append("(" + " OR ".join(ors) + ")")
    return "WHERE " + " AND ".join(conds), params


def q(con: sqlite3.Connection, sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql_query(sql, con, params=params or {})


# ----------------------------------------------------------------- dashboard queries (all SQL)
def kpis(con, w, p):
    return q(con, f"""
        SELECT COUNT(*) AS posts, SUM(likes) AS likes, SUM(comments) AS comments,
               SUM(shares) AS shares, SUM(saves) AS saves, SUM(reach) AS reach,
               SUM(impressions) AS impressions, SUM(profile_visits) AS visits,
               SUM(follows) AS follows, AVG({ER}) AS er
        FROM posts {w}""", p).iloc[0]


def monthly(con, w, p):
    return q(con, f"""
        SELECT strftime('%Y-%m', post_date) AS month, COUNT(*) AS posts,
               AVG({ER}) AS er, SUM(follows) AS follows, SUM(reach) AS reach,
               SUM(profile_visits) AS visits
        FROM posts {w} GROUP BY month ORDER BY month""", p)


def funnel(con, w, p):
    return q(con, f"""
        SELECT 1 AS step, 'Impressions' AS stage, SUM(impressions) AS total FROM posts {w}
        UNION ALL SELECT 2, 'Reach',    SUM(reach)    FROM posts {w}
        UNION ALL SELECT 3, 'Likes',    SUM(likes)    FROM posts {w}
        UNION ALL SELECT 4, 'Comments', SUM(comments) FROM posts {w}
        UNION ALL SELECT 5, 'Shares',   SUM(shares)   FROM posts {w}
        UNION ALL SELECT 6, 'Saves',    SUM(saves)    FROM posts {w}
        ORDER BY step""", p)


def top_posts(con, w, p, by="likes", n=10):
    order = "likes" if by == "likes" else "er"
    extra = "" if by == "likes" else ("AND reach >= 1000" if w else "WHERE reach >= 1000")
    return q(con, f"""
        SELECT post_id, post_date, post_type, campaign_type, hashtags,
               likes, comments, shares, saves, reach, {ER} AS er,
               '#' || post_id || ' · ' || post_type || ' · ' || campaign_type AS label
        FROM posts {w} {extra}
        ORDER BY {order} DESC LIMIT {int(n)}""", p)


def by_dimension(con, w, p, dim):
    return q(con, f"""
        SELECT {dim} AS grp, COUNT(*) AS posts,
               AVG(likes) AS likes, AVG(comments) AS comments, AVG(shares) AS shares,
               AVG(saves) AS saves, AVG(reach) AS reach, AVG(follows) AS follows,
               AVG({ER}) AS er
        FROM posts {w} GROUP BY grp ORDER BY er DESC""", p)


def by_weekday(con, w, p):
    return q(con, f"""
        SELECT CASE strftime('%w', post_date)
                 WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
                 WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
                 ELSE 'Saturday' END AS weekday,
               COUNT(*) AS posts, AVG(likes) AS likes, AVG(comments) AS comments,
               AVG(shares) AS shares, AVG(saves) AS saves, AVG(reach) AS reach,
               AVG(follows) AS follows, AVG({ER}) AS er
        FROM posts {w}
        GROUP BY strftime('%w', post_date)
        ORDER BY (CAST(strftime('%w', post_date) AS INTEGER) + 6) % 7""", p)


def type_campaign(con, w, p):
    return q(con, f"""
        SELECT post_type, campaign_type, AVG({ER}) AS er, COUNT(*) AS posts
        FROM posts {w} GROUP BY post_type, campaign_type""", p)


def hashtag_stats(con, w, p):
    return q(con, f"""
        WITH RECURSIVE split(post_id, tag, rest) AS (
          SELECT post_id, '', hashtags || ',' FROM posts {w}
          UNION ALL
          SELECT post_id, TRIM(SUBSTR(rest, 1, INSTR(rest, ',') - 1)),
                 SUBSTR(rest, INSTR(rest, ',') + 1)
          FROM split WHERE rest <> ''
        )
        SELECT s.tag AS hashtag, COUNT(*) AS uses,
               AVG(p.reach) AS reach, AVG(p.likes) AS likes, AVG(p.follows) AS follows,
               AVG((p.likes+p.comments+p.shares+p.saves)*100.0/p.reach) AS er
        FROM split s JOIN posts p USING (post_id)
        WHERE s.tag <> ''
        GROUP BY s.tag ORDER BY er DESC""", p)


def hashtag_count(con, w, p):
    return q(con, f"""
        SELECT LENGTH(hashtags) - LENGTH(REPLACE(hashtags, ',', '')) + 1 AS n_tags,
               COUNT(*) AS posts, AVG(reach) AS reach, AVG({ER}) AS er
        FROM posts {w} GROUP BY n_tags ORDER BY n_tags""", p)


def hashtag_combos(con, w, p, min_posts=100):
    return q(con, f"""
        SELECT hashtags, COUNT(*) AS posts, AVG({ER}) AS er, AVG(reach) AS reach
        FROM posts {w} GROUP BY hashtags HAVING COUNT(*) >= {int(min_posts)}
        ORDER BY er DESC LIMIT 15""", p)


def reach_tiers(con, w, p):
    return q(con, f"""
        SELECT CASE WHEN reach < 10000 THEN '1. < 10K' WHEN reach < 20000 THEN '2. 10K-20K'
                    WHEN reach < 30000 THEN '3. 20K-30K' ELSE '4. 30K+' END AS tier,
               COUNT(*) AS posts, AVG({ER}) AS er,
               SUM(follows)*100.0/SUM(reach) AS follows_per_100_reach
        FROM posts {w} GROUP BY tier ORDER BY tier""", p)


# ----------------------------------------------------------------- playground
_FORBIDDEN = re.compile(r"\b(attach|detach|pragma|insert|update|delete|drop|alter|create|replace|vacuum|reindex)\b", re.I)


def run_user_sql(con, sql: str, max_rows: int = 5000):
    """Validate and run a read-only query. Returns (df, seconds, truncated)."""
    s = sql.strip()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)                 # drop block comments
    s = "\n".join(l for l in s.splitlines() if not l.strip().startswith("--")).strip()
    s = s.rstrip(";").strip()
    if not s:
        raise ValueError("Please type a query first.")
    if ";" in s:
        raise ValueError("Only one statement can be run at a time.")
    if not re.match(r"^(select|with)\b", s, re.I):
        raise ValueError("Only SELECT / WITH queries are allowed in this playground.")
    # strip string literals before keyword check so 'Replace' inside text is fine
    probe = re.sub(r"'[^']*'", "''", s)
    bad = _FORBIDDEN.search(probe)
    if bad and bad.group(1).lower() != "replace":
        raise ValueError(f"'{bad.group(1).upper()}' is not allowed - the playground is read-only.")
    t0 = time.perf_counter()
    cur = con.execute(s)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchmany(max_rows + 1)
    secs = time.perf_counter() - t0
    truncated = len(rows) > max_rows
    return pd.DataFrame(rows[:max_rows], columns=cols), secs, truncated
