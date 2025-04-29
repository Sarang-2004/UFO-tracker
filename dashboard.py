import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import folium
import pydeck as pdk
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv

st.set_page_config(page_title="UFO Sightings Tracker", layout="wide")
load_dotenv()

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", 5432)
    )

def fetch_sightings(start_date, end_date, keyword):
    conn = get_connection()
    cursor = conn.cursor()
    end_date = end_date + timedelta(days=1)
    query = """
        SELECT post_id, title, content, url, location, latitude, longitude, source, created_utc
        FROM ufo_sightings
        WHERE created_utc >= %s AND created_utc < %s
        AND latitude IS NOT NULL AND longitude IS NOT NULL
    """

    params = [start_date, end_date]

    # Only add content filter if keyword is not empty
    if keyword:
        query += " AND content ILIKE %s"
        params.append(f"%{keyword}%")

    query += " ORDER BY created_utc DESC LIMIT 100"

    cursor.execute(query, params)
    try:
        cursor.execute(query, params)
        conn.commit()  # Commit the transaction if successful
    except Exception as e:
        conn.rollback()  # Rollback transaction if it fails
        print(f"Database error: {e}")


    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(data, columns=columns)
    cursor.close()
    return df

st.sidebar.title("🔍 Filters")
days_back = st.sidebar.slider("How many days back?", 1, 30, 7)
start_date = datetime.utcnow() - timedelta(days=days_back)
end_date = datetime.utcnow()
keyword = st.sidebar.text_input("Keyword (optional)", "")

st.title("🛸 UFO Sightings Dashboard")
df = fetch_sightings(start_date, end_date, keyword)

st.markdown(f"Showing **{len(df)}** sightings from the past **{days_back}** days")

if not df.empty:
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=2)
    for _, row in df.iterrows():
        popup = f"""
        <strong>{row['title']}</strong><br>
        <a href="{row['url']}" target="_blank">View Post</a><br>
        Source: {row['source']}<br>
        Location: {row['location']}<br>
        Date: {row['created_utc'].strftime('%Y-%m-%d %H:%M')}
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color="purple", icon="eye")
        ).add_to(m)
    st_folium(m, width=1000, height=600)

    df_deck = df.copy()
    df_deck = df_deck[df_deck['latitude'].notnull() & df_deck['longitude'].notnull()]

    # Group by rough locations (e.g., by region/city if location format is clean) — fallback to lat/lon
    grouped = df_deck.groupby(['latitude', 'longitude']).size().reset_index(name='sightings')

    top_locations = df['location'].value_counts().head(5)
    st.subheader("📍 Recent Sightings ")
    for loc, count in top_locations.items():
        st.markdown(f"- **{loc}**: {count} sighting{'s' if count > 1 else ''}")

    # Create PyDeck map layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=grouped,
        get_position='[longitude, latitude]',
        get_radius='sightings * 50000',
        get_fill_color=[255, 0, 0, 160],
        pickable=True,
    )

    # Render PyDeck map
    st.subheader("📍 Heatmap of Sightings ")
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=grouped['latitude'].mean() if not grouped.empty else 37.09,
            longitude=grouped['longitude'].mean() if not grouped.empty else -95.71,
            zoom=3,
            pitch=50
        ),
        tooltip={"text": "Sightings: {sightings}"}
    ))

    
    
else:
    st.warning("No sightings found in that time frame or with that keyword.")

with st.expander("🧾 Show raw data"):
    st.dataframe(df)
