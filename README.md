# 💄 Sugar Insights – Instagram Analytics (Streamlit + SQL)

Interactive dashboard and **live SQL playground** for Sugar Cosmetics' Instagram data
(50,000 posts, 19 Apr 2024 – 19 Apr 2025).

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```
The data is loaded into an in-memory SQLite database; every chart is driven by a SQL query
(see `utils.py`). The full analysis script is `data/sugar_instagram_analysis.sql`.

## What's inside
| Tab | Covers project task |
|---|---|
| 📊 Overview | Task 1 KPIs, Task 2 monthly trend, Task 7 engagement funnel |
| 🏆 Top Posts | Task 3 (top likes), Task 4 (top engagement rate) |
| 🎬 Formats & Timing | Task 5 post-type comparison, Task 6 day-of-week, format × campaign heat-map |
| #️⃣ Hashtags | Task 8 hashtag analysis, hashtag-count and combination analysis |
| 📈 Growth | Follower growth, visit→follow conversion, reach tiers |
| 💡 Strategy | Task 10 recommendations, gaps, campaign ideas, experiment plan |
| 🧪 SQL Playground | Run your own read-only SELECT / WITH queries, chart results, download CSV |

Sidebar filters (post type, campaign, source, month range, hashtag) apply to every tab (Task 9).

## Files
- `app.py` – UI · `utils.py` – SQL/data layer · `data/` – cleaned CSV + SQL script · `assets/` – logo
- Engagement rate = (likes + comments + shares + saves) ÷ reach × 100
