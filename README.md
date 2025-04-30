# UFO-tracker

UFO-tracker is a data streaming and visualization project that collects UFO sighting reports from Reddit and displays them on an interactive dashboard. The project uses natural language processing to extract location information from Reddit posts, geocodes these locations, stores the data in a PostgreSQL database, and provides a Streamlit-based dashboard to explore recent UFO sightings worldwide.

## Features

- Streams new Reddit posts from UFO-related subreddits in real-time.
- Extracts and geocodes location information from post content using spaCy and Nominatim.
- Stores UFO sighting data in a PostgreSQL database.
- Interactive dashboard with filters for date range and keyword search.
- Visualizes sightings on a map with markers and heatmaps.
- Displays recent sightings by location.

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd UFO-tracker
```

2. Create and activate a Python virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a `.env` file in the project root with the following variables:

```env
# PostgreSQL database credentials
PG_DB=your_database_name
PG_USER=your_database_user
PG_PASSWORD=your_database_password
PG_HOST=your_database_host
PG_PORT=your_database_port  # default is 5432

# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_reddit_user_agent
```

## Usage

### Run the Reddit Streamer

This script fetches recent posts and streams new posts from UFO-related subreddits, extracting and saving sightings to the database.

```bash
python reddit_stream.py
```

### Run the Dashboard

Launch the Streamlit dashboard to explore UFO sightings data.

```bash
streamlit run dashboard.py
```

Use the sidebar filters to select the date range and filter sightings by keyword.

## Dependencies

- Python 3.7+
- praw
- spacy
- geopy
- psycopg2
- streamlit
- pandas
- folium
- pydeck
- streamlit-folium
- python-dotenv

Make sure to download the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

## Database

The project expects a PostgreSQL database with a table named `ufo_sighting` having the following columns:

- post_id (primary key)
- title
- content
- url
- location
- latitude
- longitude
- source
- created_utc (timestamp)

## License

This project is licensed under the MIT License.

---

Feel free to contribute or report issues!
