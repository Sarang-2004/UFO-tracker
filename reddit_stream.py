import praw
import re
import time
import spacy
import os
import psycopg2
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Set up Reddit
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)

# Set up Geocoder
geolocator = Nominatim(user_agent="ufo_location_geocoder", timeout=10)

# Subreddit to stream
subreddit = reddit.subreddit("UFOs+aliens+highstrangeness")

def extract_locations(text):
    doc = nlp(text)
    return list(set(ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]))

def geocode_location(location):
    try:
        geo = geolocator.geocode(location)
        if geo:
            return geo.latitude, geo.longitude
    except Exception:
        return None, None
    return None, None

def save_to_db(post_id, title, content, url, location, lat, lon, source, created_utc):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_DB"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ufo_sighting (post_id, title, content, url, location, latitude, longitude, source, created_utc)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (post_id) DO NOTHING;
        """, (post_id, title, content, url, location, lat, lon, source, created_utc))

        conn.commit()
        print(f"✅ Saved post {post_id} to database.")
    except Exception as e:
        print(f"❌ Database insert error for post {post_id}: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

def is_ufo_related(text):
    keywords = ["sighting", "saw a ufo", "seen a ufo", "ufo over", "object in the sky", "bright light", "flying saucer", "UAP", "UFO"]
    return any(kw.lower() in text.lower() for kw in keywords)

def process_text(content, post_id, title, url, source, created_utc):
    if is_ufo_related(content):
        locations = extract_locations(content)
        if locations:
            for loc in locations:
                lat, lon = geocode_location(loc)
                print(f"🛸 {source.title()}: {title}")
                print(f"🔗 {url}")
                print(f"📍 {loc} -> lat: {lat}, lon: {lon}")
                print("-" * 60)
                save_to_db(post_id, title, content, url, loc, lat, lon, source, created_utc)
        else:
            print(f"🛸 {source.title()}: {title}")
            print("📍 No location mentioned.")
            print("-" * 60)

def fetch_recent_ufo_sightings(days=2):
    print(f"🔎 Fetching posts from the past {days} days...")
    start_time = datetime.utcnow() - timedelta(days=days)
    start_timestamp = int(start_time.timestamp())

    for submission in subreddit.new(limit=500):  # Adjust limit as needed
        if submission.created_utc >= start_timestamp:
            content = f"{submission.title}\n{submission.selftext}"
            process_text(content, submission.id, submission.title, submission.url, "submission")

            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list():
                process_text(comment.body, comment.id, submission.title, f"https://reddit.com{comment.permalink}", "comment")

def stream_ufo_sightings():
    print("🌌 Streaming Reddit posts and comments about UFO sightings...")
    for submission in subreddit.stream.submissions(skip_existing=True):
        content = f"{submission.title}\n{submission.selftext}"
        process_text(content, submission.id, submission.title, submission.url, "submission")

        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            process_text(comment.body, comment.id, submission.title, f"https://reddit.com{comment.permalink}", "comment")
        time.sleep(1)

if __name__ == "__main__":
    try:
        fetch_recent_ufo_sightings(days=3)
        stream_ufo_sightings()
    except KeyboardInterrupt:
        print("👋 Stopping stream...")
