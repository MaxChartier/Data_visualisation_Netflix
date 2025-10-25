import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Netflix Monetization Gap Analysis | Max Chartier",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def inject_css():
    st.markdown(
        """
        <style>
        /* Main app styling */
        .stApp { 
            background: linear-gradient(135deg, #141414 0%, #0a0a0a 100%);
            color: #fafafa; 
        }
        
        /* Custom header with author */
        .custom-header {
            background: linear-gradient(90deg, #e50914 0%, #b20710 100%);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.3);
        }
        
        .custom-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .custom-header .subtitle {
            color: #f0f0f0;
            font-size: 1.3rem;
            font-weight: 400;
            margin-bottom: 10px;
        }
        
        .author-tag {
            color: #ffffff;
            font-size: 0.95rem;
            font-weight: 500;
            opacity: 0.95;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid rgba(255,255,255,0.3);
        }
        
        /* Enhanced metric cards */
        .metric-card { 
            background: linear-gradient(135deg, #1f1f1f 0%, #141414 100%);
            padding: 25px; 
            border-radius: 12px; 
            border-left: 5px solid #e50914;
            margin: 10px 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(229, 9, 20, 0.4);
        }
        
        /* Enhanced section headers */
        .section-header {
            color: #e50914;
            font-size: 2rem;
            font-weight: 700;
            margin-top: 2.5rem;
            margin-bottom: 1.2rem;
            padding-bottom: 10px;
            border-bottom: 2px solid #e50914;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        }
        
        /* Enhanced insight boxes */
        .insight-box {
            background: linear-gradient(135deg, #1f1f1f 0%, #1a1a1a 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #4a9eff;
            margin: 20px 0;
            box-shadow: 0 3px 10px rgba(0,0,0,0.3);
        }
        
        .insight-box strong {
            color: #4a9eff;
            font-size: 1.1rem;
        }
        
        /* Streamlit metric styling */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #e50914;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 1rem;
            color: #b0b0b0;
        }
        
        /* Divider styling */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, #e50914 50%, transparent 100%);
            margin: 30px 0;
        }
        
        /* Footer styling */
        .footer {
            text-align: center;
            padding: 30px;
            margin-top: 50px;
            background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
            border-radius: 12px;
            border-top: 3px solid #e50914;
        }
        
        .footer-author {
            font-size: 1.2rem;
            font-weight: 600;
            color: #e50914;
            margin-bottom: 8px;
        }
        
        .footer-description {
            color: #b0b0b0;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

@st.cache_data
def load_data():
    base = Path(".")
    users = pd.read_csv(base / "users.csv", parse_dates=["created_at", "subscription_start_date"])
    watch = pd.read_csv(base / "watch_history.csv", parse_dates=["watch_date"])
    movies = pd.read_csv(base / "movies.csv")
    
    watch["watch_duration_minutes"] = pd.to_numeric(watch["watch_duration_minutes"], errors="coerce").fillna(0)
    users["monthly_spend"] = pd.to_numeric(users["monthly_spend"], errors="coerce")
    users["age"] = pd.to_numeric(users["age"], errors="coerce")
    
    return users, watch, movies

def main():
    inject_css()
    
    # Custom header with author attribution
    st.markdown("""
    <div class='custom-header'>
        <h1> The Engagement-Monetization Gap</h1>
        <div class='subtitle'>Why are our most engaged users not our highest spenders?</div>
        <div class='author-tag'> Made by Max Chartier</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    This dashboard walks through a critical business problem: we have users who watch extensively 
    but contribute minimal revenue. Understanding this gap is key to sustainable growth.
    """)
    
    users, watch, movies = load_data()
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Problem: The Data Suggests a Disconnect</div>", unsafe_allow_html=True)
    
    st.markdown("""
    We start with a hypothesis: if users are highly engaged, they should be willing to pay more. 
    But the data tells a different story.
    """)
    
    avg_watch_per_user = watch.groupby('user_id')['watch_duration_minutes'].sum().reset_index()
    avg_watch_per_user.columns = ['user_id', 'total_watch_minutes']
    
    user_engagement = users.merge(avg_watch_per_user, on='user_id', how='left')
    user_engagement['total_watch_minutes'] = user_engagement['total_watch_minutes'].fillna(0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        high_engagement = user_engagement[user_engagement['total_watch_minutes'] > user_engagement['total_watch_minutes'].quantile(0.75)]
        high_eng_low_spend = high_engagement[high_engagement['monthly_spend'] < high_engagement['monthly_spend'].median()]
        pct = (len(high_eng_low_spend) / len(high_engagement) * 100)
        st.metric("High Engagement, Low Spend", f"{pct:.1f}%", help="% of top 25% watchers who spend below median")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        median_spend = user_engagement['monthly_spend'].dropna().median()
        st.metric("Median Monthly Spend", f"${median_spend:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        top_watchers_avg = high_engagement['monthly_spend'].dropna().mean()
        st.metric("Avg Spend (Top Watchers)", f"${top_watchers_avg:.2f}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Where Does the Gap Appear?</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Let's look at the relationship between engagement and spending across all users. 
    Each point represents one user.
    """)
    
    user_engagement_clean = user_engagement.dropna(subset=['monthly_spend'])
    
    fig_scatter = px.scatter(
        user_engagement_clean,
        x='monthly_spend',
        y='total_watch_minutes',
        color='subscription_plan',
        hover_data=['user_id', 'primary_device'],
        title="User Engagement vs Monthly Spend",
        labels={'monthly_spend': 'Monthly Spend ($)', 'total_watch_minutes': 'Total Watch Time (minutes)'}
    )
    fig_scatter.update_layout(template="plotly_dark")
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    **Key Observation:** Notice the dense cluster of users at low spending levels who have high watch time. 
    These are highly engaged but under-monetized. This suggests:
    - Free trials or shared accounts
    - Basic plan users who are heavy consumers
    - Potential for targeted upselling
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### Breaking it down by subscription plan")
    
    plan_analysis = user_engagement_clean.groupby('subscription_plan').agg({
        'monthly_spend': 'mean',
        'total_watch_minutes': 'mean',
        'user_id': 'count'
    }).reset_index()
    plan_analysis.columns = ['subscription_plan', 'avg_spend', 'avg_watch', 'user_count']
    
    fig_plan = go.Figure()
    fig_plan.add_trace(go.Bar(
        x=plan_analysis['subscription_plan'],
        y=plan_analysis['avg_spend'],
        name='Avg Monthly Spend',
        marker_color='#e50914'
    ))
    fig_plan.add_trace(go.Bar(
        x=plan_analysis['subscription_plan'],
        y=plan_analysis['avg_watch'] / 60,
        name='Avg Watch Hours',
        marker_color='#4a9eff',
        yaxis='y2'
    ))
    
    fig_plan.update_layout(
        template="plotly_dark",
        title="Spend and Engagement by Subscription Plan",
        yaxis=dict(title='Avg Monthly Spend ($)'),
        yaxis2=dict(title='Avg Watch Hours', overlaying='y', side='right'),
        barmode='group'
    )
    st.plotly_chart(fig_plan, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    Basic plan users watch nearly as much as Premium users but pay significantly less. 
    This is our monetization opportunity.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Deep Dive: Who Are These High-Engagement, Low-Spend Users?</div>", unsafe_allow_html=True)
    
    target_segment = user_engagement_clean[
        (user_engagement_clean['total_watch_minutes'] > user_engagement_clean['total_watch_minutes'].quantile(0.75)) &
        (user_engagement_clean['monthly_spend'] < user_engagement_clean['monthly_spend'].median())
    ]
    
    st.markdown(f"**Identified {len(target_segment)} users in this segment.**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        device_dist = target_segment['primary_device'].value_counts()
        fig_device = px.pie(
            values=device_dist.values,
            names=device_dist.index,
            title="Primary Devices (Target Segment)",
            color_discrete_sequence=px.colors.sequential.Reds_r
        )
        fig_device.update_layout(template="plotly_dark")
        st.plotly_chart(fig_device, use_container_width=True)
    
    with col2:
        plan_dist = target_segment['subscription_plan'].value_counts()
        fig_plan_dist = px.pie(
            values=plan_dist.values,
            names=plan_dist.index,
            title="Subscription Plans (Target Segment)",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig_plan_dist.update_layout(template="plotly_dark")
        st.plotly_chart(fig_plan_dist, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    These users are predominantly on Basic plans and use a mix of devices. 
    They are clearly invested in the platform (high watch time) but have not upgraded.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### What content are they watching?")
    
    target_user_ids = target_segment['user_id'].tolist()
    target_watch = watch[watch['user_id'].isin(target_user_ids)]
    target_watch = target_watch.merge(movies[['movie_id', 'genre_primary']], on='movie_id', how='left')
    
    genre_engagement = target_watch.groupby('genre_primary')['watch_duration_minutes'].sum().reset_index()
    genre_engagement = genre_engagement.sort_values('watch_duration_minutes', ascending=False).head(10)
    
    fig_genre = px.bar(
        genre_engagement,
        x='watch_duration_minutes',
        y='genre_primary',
        orientation='h',
        title="Top Genres Watched by High-Engagement, Low-Spend Users",
        labels={'watch_duration_minutes': 'Total Watch Minutes', 'genre_primary': 'Genre'},
        color='watch_duration_minutes',
        color_continuous_scale='Reds'
    )
    fig_genre.update_layout(template="plotly_dark")
    st.plotly_chart(fig_genre, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    These users have clear genre preferences. 
    We can use this to personalize upsell messaging around premium content in these genres.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### Engagement patterns over time")
    
    # Complex visualization: Cohort analysis of watch behavior by subscription plan
    watch_with_users = watch.merge(users[['user_id', 'subscription_plan', 'monthly_spend']], on='user_id', how='left')
    watch_with_users['watch_date'] = pd.to_datetime(watch_with_users['watch_date'])
    watch_with_users['year_month'] = watch_with_users['watch_date'].dt.to_period('M').astype(str)
    
    monthly_engagement = watch_with_users.groupby(['year_month', 'subscription_plan'])['watch_duration_minutes'].sum().reset_index()
    
    fig_timeline = px.line(
        monthly_engagement,
        x='year_month',
        y='watch_duration_minutes',
        color='subscription_plan',
        title="Monthly Watch Time Trends by Subscription Plan",
        labels={'watch_duration_minutes': 'Total Watch Minutes', 'year_month': 'Month'},
        markers=True
    )
    fig_timeline.update_layout(template="plotly_dark", xaxis_tickangle=-45)
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    Basic plan users show consistent high engagement over time, yet they remain on the lowest tier. 
    This pattern reinforces that engagement alone doesn't drive upgrades.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### The retention-spend relationship")
    
    # Create meaningful retention analysis by engagement and spend
    retention_df = user_engagement_clean.copy()
    
    # Create spend brackets
    retention_df['spend_bracket'] = pd.cut(
        retention_df['monthly_spend'],
        bins=[0, 5, 10, 15, 100],
        labels=['$0-5', '$5-10', '$10-15', '$15+']
    )
    
    # Create engagement brackets
    retention_df['engagement_level'] = pd.qcut(
        retention_df['total_watch_minutes'], 
        q=4, 
        labels=['Low', 'Medium', 'High', 'Very High'],
        duplicates='drop'
    )
    
    # Calculate retention rate for each combination
    retention_matrix = retention_df.groupby(['engagement_level', 'spend_bracket']).agg({
        'is_active': ['sum', 'count']
    }).reset_index()
    retention_matrix.columns = ['engagement_level', 'spend_bracket', 'active_count', 'total_count']
    retention_matrix['retention_rate'] = (retention_matrix['active_count'] / retention_matrix['total_count'] * 100).round(1)
    
    # Pivot for heatmap
    heatmap_data = retention_matrix.pivot(index='engagement_level', columns='spend_bracket', values='retention_rate')
    
    # Create proper heatmap
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        text=heatmap_data.values,
        texttemplate='%{text:.1f}%',
        textfont={"size": 14},
        colorbar=dict(title="Retention %")
    ))
    
    fig_heatmap.update_layout(
        template="plotly_dark",
        title="Retention Rate by Engagement Level and Monthly Spend",
        xaxis_title="Monthly Spend Bracket",
        yaxis_title="Engagement Level",
        height=500
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    **Analysis:** The heatmap reveals some surprising patterns. Looking at the data:
    
    - **Very High engagement + $0-5 spend**: Only 80.5% retention (red zone) - these heavy users on cheap plans are at risk of churning
    - **Medium engagement**: Consistently high retention (87%+) across all spend levels (green) - these are our most stable users
    - **$15+ spend bracket**: Strong retention (86-87%) across all engagement levels - premium subscribers stay loyal
    - **The sweet spot**: Medium to High engagement with $10-15+ spend shows the best retention (87%+)
    
    The key insight: very high engagement with very low spend is actually a retention risk. These users might be 
    account sharers who eventually get flagged, or they're dissatisfied with Basic plan limitations. Converting them 
    to higher tiers could reduce this churn risk while increasing revenue.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Insights: What's Causing the Gap?</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Based on the analysis, here are the likely drivers of the engagement-monetization gap:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1. Account Sharing")
        st.markdown("""
        High engagement with low spend may indicate multiple people using a single Basic account. 
        Household size data could confirm this.
        """)
        
        hh_analysis = target_segment.dropna(subset=['household_size'])
        if not hh_analysis.empty:
            avg_hh = hh_analysis['household_size'].mean()
            st.metric("Avg Household Size (Target Segment)", f"{avg_hh:.1f}")
            st.markdown(f"Compare to overall average: {user_engagement['household_size'].mean():.1f}")
    
    with col2:
        st.markdown("#### 2. Price Sensitivity")
        st.markdown("""
        Users may be engaged but unwilling to pay for Premium features. 
        Testing targeted discounts or trials could convert them.
        """)
        
        basic_users = target_segment[target_segment['subscription_plan'] == 'Basic']
        st.metric("Basic Plan Users in Segment", f"{len(basic_users)}")
    
    st.markdown("#### 3. Lack of Awareness")
    st.markdown("""
    Users may not understand the value of Premium features (4K, multiple screens, downloads). 
    In-app messaging highlighting these benefits could drive upgrades.
    """)
    
    st.markdown("### Visualizing the opportunity")
    
    # Complex multi-axis visualization showing the financial opportunity
    # Use the retention_df that already has spend_bracket column
    spend_brackets = retention_df.groupby('spend_bracket').agg({
        'user_id': 'count',
        'total_watch_minutes': 'mean',
        'monthly_spend': 'mean',
        'is_active': 'mean'
    }).reset_index()
    spend_brackets.columns = ['spend_bracket', 'user_count', 'avg_watch_minutes', 'avg_spend', 'retention']
    spend_brackets['potential_revenue'] = spend_brackets['user_count'] * spend_brackets['avg_spend']
    
    fig_opportunity = go.Figure()
    
    fig_opportunity.add_trace(go.Bar(
        x=spend_brackets['spend_bracket'],
        y=spend_brackets['user_count'],
        name='User Count',
        marker_color='#e50914',
        yaxis='y'
    ))
    
    fig_opportunity.add_trace(go.Scatter(
        x=spend_brackets['spend_bracket'],
        y=spend_brackets['avg_watch_minutes'],
        name='Avg Watch Minutes',
        mode='lines+markers',
        marker_color='#4a9eff',
        yaxis='y2',
        line=dict(width=3)
    ))
    
    fig_opportunity.add_trace(go.Scatter(
        x=spend_brackets['spend_bracket'],
        y=spend_brackets['retention'] * 1000,
        name='Retention Rate (x1000)',
        mode='lines+markers',
        marker_color='#00ff00',
        yaxis='y3',
        line=dict(width=3, dash='dot')
    ))
    
    fig_opportunity.update_layout(
        template="plotly_dark",
        title="The Monetization Opportunity: User Count, Engagement, and Retention by Spend Level",
        xaxis=dict(title='Monthly Spend Bracket'),
        yaxis=dict(title='User Count', side='left'),
        yaxis2=dict(title='Avg Watch Minutes', overlaying='y', side='right'),
        yaxis3=dict(title='Retention Rate (scaled)', overlaying='y', side='right', anchor='free', position=0.95),
        legend=dict(x=0.01, y=0.99)
    )
    
    st.plotly_chart(fig_opportunity, use_container_width=True)
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Geographic Distribution: Where Are the Opportunities?</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Understanding where our high-engagement, low-spend users are located helps us tailor regional strategies, 
    pricing, and content offerings.
    """)
    
    # Geographic analysis of the target segment
    target_segment_geo = target_segment.groupby('country').agg({
        'user_id': 'count',
        'monthly_spend': 'mean',
        'total_watch_minutes': 'mean'
    }).reset_index()
    target_segment_geo.columns = ['country', 'user_count', 'avg_spend', 'avg_watch_minutes']
    target_segment_geo = target_segment_geo.sort_values('user_count', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Choropleth map showing geographic distribution
        fig_map = px.choropleth(
            target_segment_geo,
            locations='country',
            locationmode='country names',
            color='user_count',
            hover_name='country',
            hover_data={'user_count': True, 'avg_spend': ':.2f', 'avg_watch_minutes': ':.0f'},
            title="Geographic Distribution of High-Engagement, Low-Spend Users",
            color_continuous_scale='Reds',
            labels={'user_count': 'User Count'}
        )
        fig_map.update_layout(
            template="plotly_dark",
            geo=dict(showframe=False, showcoastlines=True, projection_type='natural earth')
        )
        st.plotly_chart(fig_map, use_container_width=True)
    
    with col2:
        st.markdown("#### Top 5 Countries")
        top_countries = target_segment_geo.head(5)
        for idx, row in top_countries.iterrows():
            st.markdown(f"**{row['country']}**")
            st.markdown(f"- Users: {row['user_count']}")
            st.markdown(f"- Avg Spend: ${row['avg_spend']:.2f}")
            st.markdown(f"- Avg Watch: {row['avg_watch_minutes']:.0f} min")
            st.markdown("---")
    
    st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
    st.markdown("""
    The geographic concentration reveals key markets where the engagement-monetization gap is most pronounced. 
    These regions should be prioritized for localized upsell campaigns, regional pricing experiments, and targeted content 
    investments. Countries with high user counts but low average spend represent the biggest opportunity for revenue growth 
    through strategic interventions.
    """)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<div class='section-header'>Implications: What Should We Do?</div>", unsafe_allow_html=True)
    
    st.markdown("""
    Based on this analysis, here are actionable recommendations to close the engagement-monetization gap:
    """)
    
    st.markdown("### 1. Targeted Upsell Campaigns")
    st.markdown("""
    - Identify high-engagement Basic users through automated scoring
    - Offer time-limited Premium trials (7 days) with personalized messaging around their favorite genres
    - Track conversion rates and lifetime value uplift
    """)
    
    st.markdown("### 2. Address Account Sharing")
    st.markdown("""
    - Implement gentle nudges for accounts with high engagement but low spend
    - Offer family plans at a discount for households with multiple viewers
    - Offer the possibility to have an account with profiles in different households
    """)
    
    st.markdown("### 3. Experiment with Pricing")
    st.markdown("""
    - test a mid-tier plan between Basic and Premium
    - Offer dynamic pricing based on engagement levels
    - Test annual subscription discounts for high-engagement users
    """)
    
    st.markdown("### 4. Improve Feature Discovery")
    st.markdown("""
    - Highlight Premium-only content in the genres these users love
    - Show comparison charts in-app
    - Send targeted emails showcasing 4K/HDR content availability
    """)
    
    st.markdown("---")
    
    # Enhanced footer
    st.markdown("""
    <div class='footer'>
        <div class='footer-author'>Created by Max Chartier</div>
        <div class='footer-description'>
            Netflix User Engagement & Monetization Analysis Dashboard<br>
            Data: Netflix user engagement and subscription data
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

