/* =====================================================================
   SUGAR COSMETICS - INSTAGRAM PERFORMANCE ANALYTICS  (SQL ANALYSIS)
   Dialect : SQLite 3.35+  (also runs in the Streamlit SQL Playground)
   Table   : posts
   Columns : post_id, post_date (YYYY-MM-DD), post_type, campaign_type,
             hashtags (comma separated), audience_emotion, engagement_source,
             impressions, reach, likes, comments, shares, saves,
             profile_visits, follows

   Engagement Rate (ER) = (likes + comments + shares + saves) / reach * 100

   Data notes
   - The dataset has no Caption column and no "Carousel" post type
     (types are Image / Reel / Story / Video). Posts are therefore
     identified by post_id + date + type + campaign + hashtags.
   - Apr-2024 and Apr-2025 are partial months (data runs 19-Apr-2024 to
     19-Apr-2025), so monthly counts for those two months look low.
   ===================================================================== */


/* ---------------------------------------------------------------------
   0. DATA QUALITY CHECKS
   --------------------------------------------------------------------- */

-- 0.1 Row count, date range, null and duplicate check
SELECT COUNT(*)                         AS total_rows,
       MIN(post_date)                   AS first_post,
       MAX(post_date)                   AS last_post,
       SUM(post_date IS NULL)           AS null_dates,
       SUM(reach IS NULL OR reach = 0)  AS bad_reach
FROM posts;

-- 0.2 Logical consistency: reach should never exceed impressions
SELECT COUNT(*) AS rows_reach_gt_impressions
FROM posts
WHERE reach > impressions;


/* ---------------------------------------------------------------------
   TASK 1 : KPI OVERVIEW
   --------------------------------------------------------------------- */
SELECT COUNT(*)                                                        AS total_posts,
       SUM(likes)                                                      AS total_likes,
       SUM(comments)                                                   AS total_comments,
       SUM(shares)                                                     AS total_shares,
       SUM(saves)                                                      AS total_saves,
       SUM(reach)                                                      AS total_reach,
       SUM(impressions)                                                AS total_impressions,
       SUM(profile_visits)                                             AS total_profile_visits,
       SUM(follows)                                                    AS total_follows,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_engagement_rate_pct,
       ROUND(SUM(likes+comments+shares+saves)*100.0/SUM(reach), 2)     AS weighted_engagement_rate_pct,
       ROUND(SUM(impressions)*1.0/SUM(reach), 2)                       AS impressions_per_reach,
       ROUND(SUM(follows)*100.0/SUM(profile_visits), 2)                AS visit_to_follow_pct
FROM posts;


/* ---------------------------------------------------------------------
   TASK 2 : MONTHLY POSTING TREND  (Month-Year)
   --------------------------------------------------------------------- */
SELECT strftime('%Y-%m', post_date)                                    AS month_year,
       COUNT(*)                                                        AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct,
       SUM(follows)                                                    AS new_follows
FROM posts
GROUP BY month_year
ORDER BY month_year;

-- 2.1 Month-over-month change in posting volume (window function)
WITH m AS (
  SELECT strftime('%Y-%m', post_date) AS month_year, COUNT(*) AS posts
  FROM posts GROUP BY 1
)
SELECT month_year,
       posts,
       LAG(posts) OVER (ORDER BY month_year)                           AS prev_month_posts,
       ROUND((posts - LAG(posts) OVER (ORDER BY month_year)) * 100.0
             / LAG(posts) OVER (ORDER BY month_year), 1)               AS mom_change_pct
FROM m
ORDER BY month_year;


/* ---------------------------------------------------------------------
   TASK 3 : TOP 10 POSTS BY LIKES
   --------------------------------------------------------------------- */
SELECT post_id, post_date, post_type, campaign_type, hashtags,
       likes, comments, shares, saves, reach,
       ROUND((likes+comments+shares+saves)*100.0/reach, 2) AS engagement_rate_pct
FROM posts
ORDER BY likes DESC
LIMIT 10;


/* ---------------------------------------------------------------------
   TASK 4 : TOP 10 POSTS BY ENGAGEMENT RATE  (hidden gems)
   Posts with reach >= 1,000 only, so tiny-reach posts do not dominate.
   --------------------------------------------------------------------- */
SELECT post_id, post_date, post_type, campaign_type, hashtags,
       reach, likes,
       ROUND((likes+comments+shares+saves)*100.0/reach, 2) AS engagement_rate_pct
FROM posts
WHERE reach >= 1000
ORDER BY engagement_rate_pct DESC
LIMIT 10;

-- 4.1 Hidden gems: ER in the top 5% but likes below the median
WITH scored AS (
  SELECT *, (likes+comments+shares+saves)*100.0/reach AS er,
         NTILE(20) OVER (ORDER BY (likes+comments+shares+saves)*100.0/reach DESC) AS er_bucket,
         NTILE(2)  OVER (ORDER BY likes DESC)                                      AS like_half
  FROM posts WHERE reach >= 1000
)
SELECT post_id, post_date, post_type, campaign_type, likes, reach, ROUND(er, 2) AS er_pct
FROM scored
WHERE er_bucket = 1 AND like_half = 2
ORDER BY er DESC
LIMIT 10;


/* ---------------------------------------------------------------------
   TASK 5 : POST TYPE PERFORMANCE COMPARISON
   --------------------------------------------------------------------- */
SELECT post_type,
       COUNT(*)                                                        AS posts,
       ROUND(AVG(likes), 0)                                            AS avg_likes,
       ROUND(AVG(comments), 0)                                         AS avg_comments,
       ROUND(AVG(shares), 0)                                           AS avg_shares,
       ROUND(AVG(saves), 0)                                            AS avg_saves,
       ROUND(AVG(reach), 0)                                            AS avg_reach,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct,
       ROUND(SUM(follows)*100.0/SUM(profile_visits), 2)                AS visit_to_follow_pct
FROM posts
GROUP BY post_type
ORDER BY avg_er_pct DESC;

-- 5.1 Post type x campaign heat-map data
SELECT post_type, campaign_type,
       COUNT(*)                                                        AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct
FROM posts
GROUP BY post_type, campaign_type
ORDER BY avg_er_pct DESC;


/* ---------------------------------------------------------------------
   TASK 6 : DAY-OF-WEEK ANALYSIS
   strftime('%w') -> 0 = Sunday ... 6 = Saturday
   --------------------------------------------------------------------- */
SELECT CASE strftime('%w', post_date)
         WHEN '0' THEN 'Sunday'   WHEN '1' THEN 'Monday'  WHEN '2' THEN 'Tuesday'
         WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'
         ELSE 'Saturday' END                                           AS weekday,
       COUNT(*)                                                        AS posts,
       ROUND(AVG(likes), 0)                                            AS avg_likes,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct
FROM posts
GROUP BY strftime('%w', post_date)
ORDER BY (CAST(strftime('%w', post_date) AS INTEGER) + 6) % 7;   -- Monday first

-- 6.1 Weekday vs weekend
SELECT CASE WHEN strftime('%w', post_date) IN ('0','6') THEN 'Weekend' ELSE 'Weekday' END AS day_group,
       COUNT(*)                                                        AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct
FROM posts
GROUP BY day_group;


/* ---------------------------------------------------------------------
   TASK 7 : ENGAGEMENT FUNNEL
   Impressions -> Reach -> Likes -> Comments -> Shares -> Saves
   (Interactions are measured against Reach; Saves can exceed Shares so a
   strict stage-to-stage drop-off % is not meaningful beyond Reach.)
   --------------------------------------------------------------------- */
WITH f AS (
  SELECT 1 AS step, 'Impressions' AS stage, SUM(impressions) AS total FROM posts UNION ALL
  SELECT 2, 'Reach',    SUM(reach)    FROM posts UNION ALL
  SELECT 3, 'Likes',    SUM(likes)    FROM posts UNION ALL
  SELECT 4, 'Comments', SUM(comments) FROM posts UNION ALL
  SELECT 5, 'Shares',   SUM(shares)   FROM posts UNION ALL
  SELECT 6, 'Saves',    SUM(saves)    FROM posts
)
SELECT step, stage, total,
       ROUND(total * 100.0 / FIRST_VALUE(total) OVER (ORDER BY step), 2)  AS pct_of_impressions,
       CASE WHEN step >= 2
            THEN ROUND(total * 100.0 / (SELECT SUM(reach) FROM posts), 2) END AS pct_of_reach
FROM f
ORDER BY step;


/* ---------------------------------------------------------------------
   TASK 8 : HASHTAG ANALYSIS
   Hashtags are stored as a comma separated list, so a recursive CTE
   splits each post into one row per hashtag.
   --------------------------------------------------------------------- */
WITH RECURSIVE split(post_id, tag, rest) AS (
  SELECT post_id, '', hashtags || ',' FROM posts
  UNION ALL
  SELECT post_id,
         TRIM(SUBSTR(rest, 1, INSTR(rest, ',') - 1)),
         SUBSTR(rest, INSTR(rest, ',') + 1)
  FROM split
  WHERE rest <> ''
),
tags AS (SELECT post_id, tag FROM split WHERE tag <> '')
SELECT t.tag                                                           AS hashtag,
       COUNT(*)                                                        AS times_used,
       ROUND(AVG(p.reach), 0)                                          AS avg_reach,
       ROUND(AVG((p.likes+p.comments+p.shares+p.saves)*100.0/p.reach), 2) AS avg_er_pct,
       ROUND(SUM(p.follows)*1.0/COUNT(*), 1)                           AS avg_follows
FROM tags t
JOIN posts p USING (post_id)
GROUP BY t.tag
ORDER BY avg_er_pct DESC;

-- 8.1 Does the NUMBER of hashtags matter?
SELECT LENGTH(hashtags) - LENGTH(REPLACE(hashtags, ',', '')) + 1       AS hashtag_count,
       COUNT(*)                                                        AS posts,
       ROUND(AVG(reach), 0)                                            AS avg_reach,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2)        AS avg_er_pct
FROM posts
GROUP BY hashtag_count
ORDER BY hashtag_count;

-- 8.2 Best hashtag combinations (min 500 posts)
SELECT hashtags, COUNT(*) AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct
FROM posts
GROUP BY hashtags
HAVING COUNT(*) >= 500
ORDER BY avg_er_pct DESC
LIMIT 10;


/* ---------------------------------------------------------------------
   TASK 9 : DASHBOARD SUPPORT QUERIES (filter-ready examples)
   Replace the filter values to mimic the dashboard slicers.
   --------------------------------------------------------------------- */
SELECT strftime('%Y-%m', post_date) AS month_year,
       post_type,
       COUNT(*)  AS posts,
       SUM(likes) AS likes,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct
FROM posts
WHERE post_type = 'Reel'
  AND post_date BETWEEN '2024-06-01' AND '2024-12-31'
  AND hashtags LIKE '%#MakeupGoals%'
GROUP BY month_year, post_type
ORDER BY month_year;


/* ---------------------------------------------------------------------
   EXTRA INSIGHT QUERIES (support Task 10 recommendations)
   --------------------------------------------------------------------- */

-- E1 Campaign type performance
SELECT campaign_type, COUNT(*) AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct,
       ROUND(AVG(follows), 1)                                   AS avg_follows,
       ROUND(SUM(follows)*100.0/SUM(profile_visits), 2)         AS visit_to_follow_pct
FROM posts GROUP BY campaign_type ORDER BY avg_er_pct DESC;

-- E2 Engagement source (Organic vs Paid vs Influencer vs Collab)
SELECT engagement_source, COUNT(*) AS posts,
       ROUND(AVG(reach), 0)                                     AS avg_reach,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct,
       ROUND(SUM(follows)*100.0/SUM(reach), 3)                  AS follows_per_100_reach
FROM posts GROUP BY engagement_source ORDER BY avg_er_pct DESC;

-- E3 Audience emotion
SELECT audience_emotion, COUNT(*) AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct,
       ROUND(AVG(follows), 1)                                   AS avg_follows
FROM posts GROUP BY audience_emotion ORDER BY avg_er_pct DESC;

-- E4 Follower growth: monthly follows with running total
SELECT strftime('%Y-%m', post_date) AS month_year,
       SUM(follows)                                             AS new_follows,
       SUM(SUM(follows)) OVER (ORDER BY strftime('%Y-%m', post_date)) AS cumulative_follows,
       ROUND(SUM(follows)*1.0/COUNT(*), 1)                      AS follows_per_post
FROM posts
GROUP BY month_year
ORDER BY month_year;

-- E5 Reach tiers: does bigger reach mean better engagement?
SELECT CASE WHEN reach < 10000 THEN '1. < 10K'
            WHEN reach < 20000 THEN '2. 10K-20K'
            WHEN reach < 30000 THEN '3. 20K-30K'
            ELSE '4. 30K+' END                                  AS reach_tier,
       COUNT(*)                                                 AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct,
       ROUND(SUM(follows)*100.0/SUM(reach), 3)                  AS follows_per_100_reach
FROM posts GROUP BY reach_tier ORDER BY reach_tier;

-- E6 Content mix share vs engagement share (is any format over/under-used?)
SELECT post_type,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM posts), 1)                      AS share_of_posts_pct,
       ROUND(SUM(likes+comments+shares+saves) * 100.0 /
             (SELECT SUM(likes+comments+shares+saves) FROM posts), 1)                 AS share_of_engagement_pct
FROM posts GROUP BY post_type;

-- E7 Best 5 type x campaign x source combinations (min 200 posts)
SELECT post_type, campaign_type, engagement_source, COUNT(*) AS posts,
       ROUND(AVG((likes+comments+shares+saves)*100.0/reach), 2) AS avg_er_pct
FROM posts
GROUP BY post_type, campaign_type, engagement_source
HAVING COUNT(*) >= 200
ORDER BY avg_er_pct DESC
LIMIT 5;
