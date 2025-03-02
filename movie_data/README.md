# Movie Data Fetcher

This script fetches movie data from The Movie Database (TMDB) API, stores it in a MongoDB database with organized collections, and outputs it to a JSON file.

## Features

- Fetches data for 100 popular movies, including:
  - Movies currently in theaters
  - Upcoming movies
  - Popular movies
- Stores movie details including:
  - Title, overview, release date, popularity, ratings
  - Directors and cast information
  - Movie posters (up to 3 per movie)
  - Movie backdrops/banners (up to 3 per movie)
- Organizes data in MongoDB with separate collections for:
  - Movies
  - Directors
  - Actors
  - Genres
- Exports all movie data to a JSON file
- Avoids re-fetching existing movies (only updates them)
- Logs all operations for tracking

## Requirements

- Python 3.7+
- MongoDB installed and running
- TMDB API key (get one from [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api))

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

2. Configure the `.env` file with your TMDB API key and MongoDB connection details:

```
# TMDB API Configuration
TMDB_API_KEY=your_tmdb_api_key_here

# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb://localhost:27017/
MONGODB_DATABASE=movie_database
MONGODB_COLLECTION_MOVIES=movies
MONGODB_COLLECTION_DIRECTORS=directors
MONGODB_COLLECTION_ACTORS=actors
MONGODB_COLLECTION_GENRES=genres
```

## Usage

Run the script:

```bash
python fetch_movie_data.py
```

The script will:
1. Fetch movie data from TMDB API
2. Store the data in MongoDB with organized collections
3. Output all movies to a JSON file (`movies_data.json`)
4. Log all operations to `movie_fetcher.log`

## Database Structure

The script organizes data into multiple collections:

1. **Movies Collection**: Contains basic movie information with references to directors and actors
2. **Directors Collection**: Contains detailed information about directors
3. **Actors Collection**: Contains detailed information about actors
4. **Genres Collection**: Contains genre information

This structure reduces data duplication and allows for more efficient queries.

## JSON Output

The JSON output combines data from all collections to provide a complete view of each movie, including:

```json
{
  "id": 12345,
  "title": "Movie Title",
  "original_title": "Original Movie Title",
  "overview": "Movie description...",
  "release_date": "2023-01-01",
  "popularity": 123.456,
  "vote_average": 7.8,
  "vote_count": 1000,
  "poster_path": "/path/to/poster.jpg",
  "backdrop_path": "/path/to/backdrop.jpg",
  "genres": [{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}],
  "runtime": 120,
  "status": "Released",
  "tagline": "Movie tagline",
  "budget": 100000000,
  "revenue": 300000000,
  "directors": [
    {
      "id": 12345,
      "name": "Director Name",
      "profile_path": "/path/to/profile.jpg",
      "department": "Directing",
      "job": "Director",
      "popularity": 10.5
    }
  ],
  "cast": [
    {
      "id": 12345,
      "name": "Actor Name",
      "character": "Character Name",
      "profile_path": "/path/to/profile.jpg",
      "gender": 1,
      "popularity": 25.7,
      "order": 0
    }
  ],
  "posters": [
    "https://image.tmdb.org/t/p/original/path/to/poster1.jpg",
    "https://image.tmdb.org/t/p/original/path/to/poster2.jpg",
    "https://image.tmdb.org/t/p/original/path/to/poster3.jpg"
  ],
  "backdrops": [
    "https://image.tmdb.org/t/p/original/path/to/backdrop1.jpg",
    "https://image.tmdb.org/t/p/original/path/to/backdrop2.jpg",
    "https://image.tmdb.org/t/p/original/path/to/backdrop3.jpg"
  ],
  "fetched_at": "2023-01-01T12:00:00.000Z",
  "last_updated": "2023-01-01T12:00:00.000Z"
}
``` 