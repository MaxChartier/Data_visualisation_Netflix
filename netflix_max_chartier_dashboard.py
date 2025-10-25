import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Netflix Engagement & Satisfaction — Max Chartier Style", layout="wide")

def _inject_css():
    st.markdown(
        """
        <style>
        .reportview-container, .main, .block-container{background-color:#111111;} 
        .stApp { background-color: #111111; color: #e6e6e6; }
        .big-red { color: #E50914; font-weight:700; }
        .kpi { background: #141414; padding: 12px; border-radius: 6px; }
        .card { background: linear-gradient(180deg,#121212 0%, #0f0f0f 100%); padding:10px; border-radius:8px;}
        .streamlit-expanderHeader { color: #e6e6e6 }
        a[href] { color: #E50914 }
        </style>
        """,
        unsafe_allow_html=True,
    )

@st.cache_data
def load_data(base_path: str = "."):
    base = Path(base_path)
    users = pd.read_csv(base / "users.csv", parse_dates=["created_at", "subscription_start_date"], infer_datetime_format=True)
    watch = pd.read_csv(base / "watch_history.csv", parse_dates=["watch_date"], infer_datetime_format=True)
    movies = pd.read_csv(base / "movies.csv")
    recs = pd.read_csv(base / "recommendation_logs.csv", parse_dates=["recommendation_date"], infer_datetime_format=True)
    watch["watch_duration_minutes"] = pd.to_numeric(watch.get("watch_duration_minutes"), errors="coerce").fillna(0)
    watch["progress_percentage"] = pd.to_numeric(watch.get("progress_percentage"), errors="coerce")
    users["monthly_spend"] = pd.to_numeric(users.get("monthly_spend"), errors="coerce")
    users["age"] = pd.to_numeric(users.get("age"), errors="coerce")
    return users, watch, movies, recs

def main():
    _inject_css()
    st.markdown("<h1 class='big-red'>Netflix Engagement & Satisfaction</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color:#b3b3b3'>A  dashboard created by Max Chartier<br>
    """, unsafe_allow_html=True)

    users, watch, movies, recs = load_data()

    # KPIs
    col1, col2, col3, col4 = st.columns([1.2,1.2,1.2,1.2])
    total_users = int(users["user_id"].nunique())
    total_watch_hours = (watch["watch_duration_minutes"].sum() / 60.0)
    avg_spend = users["monthly_spend"].dropna().mean()
    active_subs = int(users[users.get("is_active") == True].shape[0])
    with col1:
        st.markdown(f"<div class='kpi'><h3 style='color:#E50914'>Users</h3><h2>{total_users:,}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='kpi'><h3 style='color:#E50914'>Watch Hours</h3><h2>{total_watch_hours:,.1f}h</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='kpi'><h3 style='color:#E50914'>Avg Monthly Spend</h3><h2>${avg_spend:,.2f}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='kpi'><h3 style='color:#E50914'>Active Subscriptions</h3><h2>{active_subs:,}</h2></div>", unsafe_allow_html=True)
    st.markdown("---")

    st.header("Retention by Subscription Plan")
    retention = users.groupby('subscription_plan')['is_active'].value_counts().unstack().fillna(0)
    retention_rate = retention.apply(lambda x: x.get(True,0)/(x.get(True,0)+x.get(False,0)), axis=1)
    fig1 = px.bar(retention_rate, title="Retention Rate by Subscription Plan", labels={'value':'Retention Rate','index':'Subscription Plan'})
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("---")


    st.header("Monthly Spend vs. Engagement by Device")
    avg_watch = watch.groupby('user_id')['watch_duration_minutes'].mean()
    engagement = users.copy()
    engagement['avg_watch_duration'] = engagement['user_id'].map(avg_watch)
    fig2 = px.scatter(engagement, x='monthly_spend', y='avg_watch_duration', color='primary_device', hover_data=['subscription_plan'], title="Monthly Spend vs. Engagement by Device")
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("**Most users cluster at low monthly_spend with a wide range of avg_watch_duration meaning many low-paying users still watch a lot. That suggests a large base of low or zero-paying heavy viewers (free trials, shared accounts, or billing issues")
    st.markdown("---")

    st.header("Genre Popularity and Satisfaction")
    genre_watch = watch.merge(movies[['movie_id','genre_primary']], on='movie_id', how='left')
    genre_stats = genre_watch.groupby('genre_primary').agg({'watch_duration_minutes':'sum','user_rating':'mean'}).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=genre_stats['genre_primary'], y=genre_stats['watch_duration_minutes'], name='Total Watch Duration'))
    fig3.add_trace(go.Scatter(x=genre_stats['genre_primary'], y=genre_stats['user_rating'], name='Avg User Rating', yaxis='y2', mode='lines+markers'))
    fig3.update_layout(template="plotly_dark", title="Genre Popularity and Satisfaction", yaxis=dict(title='Total Watch Duration'), yaxis2=dict(title='Avg User Rating', overlaying='y', side='right'))
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("**Here we can observe that adventure is the most watched genre but has a moderate user rating, while thriller have the highest average rating despite lower total watch time. This suggests that while some genres attract more viewers, others may provide a more satisfying experience to their audience.**")
    st.markdown("---")

    st.header("Recommendation CTR by Algorithm Version")
    recs['was_clicked'] = recs['was_clicked'].astype(str)
    ctr = recs.groupby('algorithm_version')['was_clicked'].apply(lambda x: (x=='True').sum()/len(x)).reset_index(name='CTR')
    fig4 = px.bar(ctr, x='algorithm_version', y='CTR', title="Recommendation CTR by Algorithm Version")
    fig4.update_layout(template="plotly_dark")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown("**Can't really tell much from this data as the differences are minimal between algorithm versions.**")
    st.markdown("---")

    st.header("Geographic Distribution of High-Value Users")
    geo_country = users.groupby('country')['monthly_spend'].mean().reset_index()
    geo_country = geo_country.dropna(subset=['monthly_spend'])
    fig5 = px.choropleth(geo_country, locations="country", locationmode="country names", color="monthly_spend", hover_name="country", title="Avg Monthly Spend by Country")
    fig5.update_layout(template="plotly_dark")
    st.plotly_chart(fig5, use_container_width=True)
    st.markdown("**We can observe that the data we have is condensed in the US with a monthly spend amount higher than Canada, so if we wanted to target a country for premium offerings or marketing it would be the US.**")
    st.markdown("---")

    st.header("Content Type Trends Over Time")
    wh_movies = watch.merge(movies[['movie_id','content_type']], on='movie_id', how='left')
    wh_movies['month'] = pd.to_datetime(wh_movies['watch_date'], errors='coerce').dt.to_period('M').astype(str)
    ct_trends = wh_movies.groupby(['month','content_type'])['watch_duration_minutes'].sum().reset_index()
    fig10 = px.line(ct_trends, x='month', y='watch_duration_minutes', color='content_type', title="Monthly Trends: Movies vs. TV Series vs. Documentaries")
    fig10.update_layout(template="plotly_dark")
    st.plotly_chart(fig10, use_container_width=True)
    st.markdown("**Movies show clear “tentpole” spikes every few months (around spring, summer, holidays). Big releases lift total minutes,documentaries are low but stable and TV series have spikes like movies.**")
    st.markdown("---")

    st.header("Engagement by Device Type")
    device_eng = watch.groupby("device_type")["watch_duration_minutes"].sum().reset_index().sort_values("watch_duration_minutes", ascending=False)
    fig_device = px.bar(device_eng, x="device_type", y="watch_duration_minutes", color="device_type", labels={"watch_duration_minutes":"Total Watch Minutes"})
    fig_device.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_device, use_container_width=True)
    st.markdown("Big‑screen devices tend to drive the highest total minutes; mobile is more snack‑sized.")

    # Device session duration distribution: medians and IQR, with optional outlier removal
    st.subheader("Device session duration distribution (median & IQR)")
    sess = watch[["device_type", "watch_duration_minutes"]].dropna()

    def _iqr_filter(group: pd.DataFrame) -> pd.DataFrame:
        q1 = group["watch_duration_minutes"].quantile(0.25)
        q3 = group["watch_duration_minutes"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return group[(group["watch_duration_minutes"] >= lower) & (group["watch_duration_minutes"] <= upper)]

    exclude_outliers = st.checkbox("Exclude outliers (per-device IQR)", value=True, help="Removes sessions outside Q1±1.5×IQR per device")
    sess_f = sess.groupby("device_type", group_keys=False).apply(_iqr_filter) if exclude_outliers else sess

    # Box plot to show IQR per device
    fig_box = px.box(
        sess_f,
        x="device_type",
        y="watch_duration_minutes",
        points=False,
        title="Session duration by device (IQR shown)" if exclude_outliers else "Session duration by device (raw)",
    )
    fig_box.update_layout(template="plotly_dark")
    st.plotly_chart(fig_box, use_container_width=True)

    # Median comparison (filtered)
    med_all = sess.groupby("device_type")["watch_duration_minutes"].median().rename("median_raw")
    med_f = sess_f.groupby("device_type")["watch_duration_minutes"].median().rename("median_filtered")
    med_df = pd.concat([med_all, med_f], axis=1).reset_index()
    fig_med = px.bar(med_df.sort_values("median_filtered", ascending=False), x="device_type", y="median_filtered", color="device_type", labels={"median_filtered": "Median session minutes"}, title="Median session duration by device (filtered)")
    fig_med.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_med, use_container_width=True)

    # Show Q1/Median/Q3 table (filtered)
    qstats = sess_f.groupby("device_type")["watch_duration_minutes"].quantile([0.25, 0.5, 0.75]).unstack()
    qstats.columns = ["Q1", "Median", "Q3"]
    st.dataframe(qstats.sort_values("Median", ascending=False).round(2))
    st.caption("Session lengths are similar across devices; the “big‑screen advantage” in total watch time likely comes from more sessions , not longer session")
    st.markdown("---")

    # Satisfaction by device (user_rating)
    st.header("Satisfaction by Device Type")
    watch_rated = watch.dropna(subset=["user_rating"])
    if not watch_rated.empty:
        device_sat = watch_rated.groupby("device_type")["user_rating"].mean().reset_index()
        fig_sat = px.bar(device_sat, x="device_type", y="user_rating", color="device_type", labels={"user_rating":"Avg User Rating"})
        fig_sat.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_sat, use_container_width=True)
        st.markdown("**Interpretation:** Average user satisfaction by device. Are some devices associated with higher ratings?")
    else:
        st.info("No user ratings available for device analysis.")
    st.markdown("---")

    # Engagement by subscription plan
    st.header("Engagement by Subscription Plan")
    watch_user = watch.groupby("user_id")["watch_duration_minutes"].sum().reset_index().rename({"watch_duration_minutes":"total_watch_mins"}, axis=1)
    users_plan = users.merge(watch_user, on="user_id", how="left").fillna({"total_watch_mins":0})
    plan_eng = users_plan.groupby("subscription_plan")["total_watch_mins"].mean().reset_index()
    fig_plan = px.bar(plan_eng, x="subscription_plan", y="total_watch_mins", color="subscription_plan", labels={"total_watch_mins":"Avg Watch Minutes per User"})
    fig_plan.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_plan, use_container_width=True)
    st.markdown("**Interpretation:** Which plans have the most engaged users?")
    st.markdown("---")

    st.header("Satisfaction by Subscription Plan")
    if not watch_rated.empty:
        user_plan_rating = users.merge(watch_rated[["user_id","user_rating"]], on="user_id", how="inner")
        plan_sat = user_plan_rating.groupby("subscription_plan")["user_rating"].mean().reset_index()
        fig_plan_sat = px.bar(plan_sat, x="subscription_plan", y="user_rating", color="subscription_plan", labels={"user_rating":"Avg User Rating"})
        fig_plan_sat.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_plan_sat, use_container_width=True)
        st.markdown("**Premium + plans seems to be correlated with higher satisfaction")
    else:
        st.info("No user ratings available for plan analysis.")
    st.markdown("---")

    st.header("Engagement by Genre")
    watch_genre = watch.merge(movies[["movie_id","genre_primary"]], on="movie_id", how="left")
    genre_eng = watch_genre.groupby("genre_primary")["watch_duration_minutes"].sum().reset_index().sort_values("watch_duration_minutes", ascending=False)
    fig_genre = px.bar(genre_eng, x="genre_primary", y="watch_duration_minutes", color="genre_primary", labels={"watch_duration_minutes":"Total Watch Minutes"})
    fig_genre.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig_genre, use_container_width=True)
    st.markdown("**Here adventure is the most watched genre")
    st.markdown("---")

    st.header("Satisfaction by Genre")
    if not watch_rated.empty:
        genre_sat = watch_genre.dropna(subset=["user_rating"]).groupby("genre_primary")["user_rating"].mean().reset_index()
        fig_genre_sat = px.bar(genre_sat, x="genre_primary", y="user_rating", color="genre_primary", labels={"user_rating":"Avg User Rating"})
        fig_genre_sat.update_layout(template="plotly_dark", showlegend=False)
        st.plotly_chart(fig_genre_sat, use_container_width=True)
        st.markdown("**Here we can see that adventure doesn't necessarly have the highest user rating despite being the most watched genre")
    else:
        st.info("No user ratings available for genre analysis.")
    st.markdown("---")

    st.header("Recommendation Click-Through Rate by Type")
    if not recs.empty:
        recs['was_clicked'] = recs['was_clicked'].astype(str)
        rec_summary = recs.groupby("recommendation_type").agg(
            impressions=("recommendation_id","count"),
            clicks=("was_clicked", lambda x: (x == "True").sum()),
        ).reset_index()
        rec_summary["clicks"] = rec_summary["clicks"].astype(int)
        rec_summary["ctr"] = rec_summary["clicks"] / rec_summary["impressions"]
        fig_rec = px.bar(rec_summary.sort_values("ctr", ascending=False), x="recommendation_type", y="ctr", labels={"ctr":"Click-through rate"})
        fig_rec.update_layout(template="plotly_dark")
        st.plotly_chart(fig_rec, use_container_width=True)
        st.markdown("**New releases is what works the best to get users to click on recommendations")
    else:
        st.info("No recommendation logs available to analyze.")
    st.markdown("---")

    st.header("Summary & Insights")
    st.markdown("""
-Engagement patterns are stable across devices and plans. Big screens and richer plans drive more total watch time due to more sessions and shared use—not longer sessions. Movies create spikes in engagement; TV Series maintain steady daily use.
-Upsell strategy: Offer UHD/family trials to heavy Basic users; highlight Premium perks contextually.
-Geography: U.S. users have higher spend—prioritize them for Premium bundles; test localized offers in Canada (maybe for plans like premium which is the second least expensive)
    """)
    st.markdown("---")
    st.caption("Files loaded: users.csv, watch_history.csv, movies.csv, recommendation_logs.csv. Narrative and visuals inspired by Max Chartier.")

if __name__ == "__main__":
    main()
