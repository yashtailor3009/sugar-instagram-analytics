# Sugar Insights

### Instagram Performance Analytics Dashboard

An interactive analytics dashboard for exploring Instagram post
performance, engagement trends, campaign results, and audience growth
for Sugar Cosmetics.

**Built with Python · Streamlit · Pandas · Plotly · SQL**
:::

------------------------------------------------------------------------

## Overview

**Sugar Insights** is a Streamlit-based dashboard that brings Instagram
performance metrics into a single, interactive interface. Users can
filter the dataset, compare post formats and campaign types, review
top-performing posts, explore hashtag trends, and inspect SQL analysis.

The current dashboard view covers **April 2024 to April 2025** and
displays **50,000 posts**.

## Features

### 📊 Overview

-   KPI cards for total posts, likes, comments, reach, engagement rate,
    shares, saves, profile visits, and new follows.
-   Monthly posting volume and average engagement-rate trends.
-   Engagement funnel from impressions to reach and engagement actions.
-   Expandable SQL explanations for selected views.

### 🏆 Top Posts

-   Top 10 posts ranked by likes.
-   Top 10 posts ranked by engagement rate, with a minimum reach
    threshold of 1,000.
-   Post-level tables with date, format, campaign, and hashtags.
-   Summary insights highlighting patterns among top-performing posts.

### 🎬 Formats & Timing

-   Average likes, comments, shares, and saves by post format.
-   Engagement-rate comparison across formats.
-   Heatmap comparing engagement rate by format and campaign type.
-   Day-of-week analysis with selectable metrics.

### #️⃣ Hashtags

-   Explore hashtag performance within the available dataset.

### 📈 Growth

-   Review growth-related metrics, including profile visits and new
    follows.

### 💡 Strategy

-   Dashboard-based recommendations derived from observed performance
    patterns.

### 🧪 SQL Playground

-   Explore SQL analysis associated with the dashboard.

### 🎛️ Interactive Filters

Filter dashboard views by: - Post type - Campaign type - Engagement
source

## Technology Stack

  Technology             Purpose
  ---------------------- --------------------------------------------
  Python                 Application logic and data analysis
  Streamlit              Interactive web dashboard
  Pandas                 Data loading, transformation, and analysis
  NumPy                  Numerical operations
  Plotly Express         Interactive charts
  Plotly Graph Objects   Custom visualizations
  SQL                    Query-based analysis

## Repository Structure

``` text
sugar-instagram-analytics/
├── .streamlit/
│   └── config.toml
├── assets/
│   ├── favicon.png
│   ├── logo.png
│   ├── logo_1024.png
│   └── logo.svg
├── data/
│   ├── sugar_instagram_analysis.sql
│   └── sugar_instagram_clean.csv
├── app.py
├── utils.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Getting Started

Follow these steps to run the dashboard locally.

### Prerequisites

-   Python 3.10 or a compatible version supported by your installed
    dependencies
-   Git

### 1. Clone the repository

``` bash
git clone https://github.com/yashtailor3009/sugar-instagram-analytics.git
cd sugar-instagram-analytics
```

### 2. Create a virtual environment

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application

``` bash
streamlit run app.py
```

Open the local URL printed in your terminal. By default, Streamlit
usually serves the app at `http://localhost:8501`.

## Deploying to Streamlit Community Cloud

1.  Ensure the project is pushed to GitHub.
2.  Open [Streamlit Community Cloud](https://share.streamlit.io/).
3.  Create a new app and select this repository.
4.  Select the `main` branch.
5.  Set **Main file path** to `app.py`.
6.  Deploy the application.

After a successful deployment, Streamlit Community Cloud will provide a
shareable app URL.

## Data Notes and Limitations

-   The current dashboard view contains 50,000 posts for the April
    2024--April 2025 period.
-   The dataset does not include a caption column. The Top Posts section
    therefore identifies posts using available fields such as post ID,
    format, and campaign.
-   Posting-hour data is not available, so the weekday analysis does not
    determine the best hour to publish.
-   Insights and metrics reflect the supplied project dataset and should
    be interpreted within that context.

## Potential Enhancements

-   Include caption-level analysis if caption data becomes available.
-   Add posting-hour comparisons if timestamp data is available.
-   Document metric definitions and data preparation steps in greater
    detail.

## Author

**Yash Tailor**

-   GitHub: [@yashtailor3009](https://github.com/yashtailor3009)
-   Repository:
    [sugar-instagram-analytics](https://github.com/yashtailor3009/sugar-instagram-analytics)

------------------------------------------------------------------------

