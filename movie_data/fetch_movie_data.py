#!/usr/bin/env python3
"""
Script to fetch movie data from TMDB API, store it in MongoDB with organized collections, 
and output it to a JSON file.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("movie_data/movie_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MovieFetcher")

# Load environment variables
load_dotenv("movie_data/.env")

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"

# MongoDB Configuration
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
MONGODB_COLLECTION_MOVIES = os.getenv("MONGODB_COLLECTION_MOVIES")
MONGODB_COLLECTION_DIRECTORS = os.getenv("MONGODB_COLLECTION_DIRECTORS")
MONGODB_COLLECTION_ACTORS = os.getenv("MONGODB_COLLECTION_ACTORS")
MONGODB_COLLECTION_GENRES = os.getenv("MONGODB_COLLECTION_GENRES")

# Output file path
OUTPUT_JSON_FILE = "movie_data/movies_data.json"


class TMDBClient:
    """Client for interacting with The Movie Database (TMDB) API."""

    def __init__(self, api_key: str):
        """Initialize the TMDB client with the API key."""
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json;charset=utf-8"
        }

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the TMDB API."""
        if params is None:
            params = {}
        
        params["api_key"] = self.api_key
        
        url = f"{TMDB_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Error making request to {url}: {response.status_code} - {response.text}")
            response.raise_for_status()
        
        return response.json()

    def get_popular_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get a list of popular movies."""
        return self._make_request("movie/popular", {"page": page})["results"]

    def get_now_playing_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get a list of movies now playing in theaters."""
        return self._make_request("movie/now_playing", {"page": page})["results"]

    def get_upcoming_movies(self, page: int = 1) -> List[Dict[str, Any]]:
        """Get a list of upcoming movies."""
        return self._make_request("movie/upcoming", {"page": page})["results"]

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Get detailed information about a movie."""
        return self._make_request(f"movie/{movie_id}", {"append_to_response": "credits,images"})


class MovieDatabase:
    """Class for interacting with the MongoDB database with multiple collections."""

    def __init__(self, connection_string: str, database_name: str):
        """Initialize the MongoDB client with multiple collections."""
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        
        # Initialize collections
        self.movies_collection: Collection = self.db[MONGODB_COLLECTION_MOVIES]
        self.directors_collection: Collection = self.db[MONGODB_COLLECTION_DIRECTORS]
        self.actors_collection: Collection = self.db[MONGODB_COLLECTION_ACTORS]
        self.genres_collection: Collection = self.db[MONGODB_COLLECTION_GENRES]
        
        # Create indexes for faster lookups
        self.movies_collection.create_index("id", unique=True)
        self.directors_collection.create_index("id", unique=True)
        self.actors_collection.create_index("id", unique=True)
        self.genres_collection.create_index("id", unique=True)

    def movie_exists(self, movie_id: int) -> bool:
        """Check if a movie already exists in the database."""
        return self.movies_collection.count_documents({"id": movie_id}) > 0

    def update_movie(self, movie_data: Dict[str, Any], directors: List[Dict[str, Any]], 
                    actors: List[Dict[str, Any]], genres: List[Dict[str, Any]]) -> None:
        """Update a movie and related entities in their respective collections."""
        # Update timestamp
        timestamp = datetime.now().isoformat()
        movie_data["last_updated"] = timestamp
        
        # Store directors in their collection and keep references
        director_refs = []
        for director in directors:
            director["last_updated"] = timestamp
            self.directors_collection.update_one(
                {"id": director["id"]},
                {"$set": director},
                upsert=True
            )
            director_refs.append({"id": director["id"], "name": director["name"]})
        
        # Store actors in their collection and keep references
        actor_refs = []
        for actor in actors:
            actor["last_updated"] = timestamp
            self.actors_collection.update_one(
                {"id": actor["id"]},
                {"$set": actor},
                upsert=True
            )
            actor_refs.append({
                "id": actor["id"], 
                "name": actor["name"], 
                "character": actor.get("character")
            })
        
        # Store genres in their collection
        for genre in genres:
            genre["last_updated"] = timestamp
            self.genres_collection.update_one(
                {"id": genre["id"]},
                {"$set": genre},
                upsert=True
            )
        
        # Update movie with references instead of full objects
        movie_data["director_refs"] = director_refs
        movie_data["actor_refs"] = actor_refs
        
        # Update movie in database
        self.movies_collection.update_one(
            {"id": movie_data["id"]},
            {"$set": movie_data},
            upsert=True
        )

    def get_all_movies_with_details(self) -> List[Dict[str, Any]]:
        """Get all movies with their full details for JSON export."""
        movies = list(self.movies_collection.find({}, {"_id": 0}))
        
        # For each movie, replace references with full objects for the JSON output
        for movie in movies:
            # Get full director objects
            if "director_refs" in movie:
                director_ids = [d["id"] for d in movie["director_refs"]]
                directors = list(self.directors_collection.find(
                    {"id": {"$in": director_ids}}, 
                    {"_id": 0}
                ))
                movie["directors"] = directors
                del movie["director_refs"]
            
            # Get full actor objects
            if "actor_refs" in movie:
                actor_ids = [a["id"] for a in movie["actor_refs"]]
                actors = list(self.actors_collection.find(
                    {"id": {"$in": actor_ids}}, 
                    {"_id": 0}
                ))
                # Sort actors to match the original order in actor_refs
                actor_map = {actor["id"]: actor for actor in actors}
                movie["cast"] = [
                    {**actor_map[ref["id"]], "character": ref.get("character")}
                    for ref in movie["actor_refs"]
                    if ref["id"] in actor_map
                ]
                del movie["actor_refs"]
        
        return movies


def process_movie_data(movie_details: Dict[str, Any]) -> tuple:
    """Process and format the movie data into separate entities."""
    # Extract directors
    directors = [
        {
            "id": crew_member["id"],
            "name": crew_member["name"],
            "profile_path": crew_member.get("profile_path"),
            "department": crew_member.get("department"),
            "job": crew_member.get("job"),
            "popularity": crew_member.get("popularity", 0)
        }
        for crew_member in movie_details.get("credits", {}).get("crew", [])
        if crew_member["job"] == "Director"
    ]

    # Extract top cast (actors)
    actors = [
        {
            "id": cast_member["id"],
            "name": cast_member["name"],
            "character": cast_member["character"],
            "profile_path": cast_member.get("profile_path"),
            "gender": cast_member.get("gender"),
            "popularity": cast_member.get("popularity", 0),
            "order": cast_member.get("order", 0)
        }
        for cast_member in movie_details.get("credits", {}).get("cast", [])[:10]  # Get top 10 actors
    ]

    # Extract genres
    genres = movie_details.get("genres", [])

    # Extract posters (up to 3)
    posters = [
        f"{TMDB_IMAGE_BASE_URL}{poster['file_path']}"
        for poster in movie_details.get("images", {}).get("posters", [])[:3]
    ]

    # Extract backdrops (banners) (up to 3)
    backdrops = [
        f"{TMDB_IMAGE_BASE_URL}{backdrop['file_path']}"
        for backdrop in movie_details.get("images", {}).get("backdrops", [])[:3]
    ]

    # Create the processed movie data
    processed_movie = {
        "id": movie_details["id"],
        "title": movie_details["title"],
        "original_title": movie_details["original_title"],
        "overview": movie_details["overview"],
        "release_date": movie_details["release_date"],
        "popularity": movie_details["popularity"],
        "vote_average": movie_details["vote_average"],
        "vote_count": movie_details["vote_count"],
        "poster_path": movie_details.get("poster_path"),
        "backdrop_path": movie_details.get("backdrop_path"),
        "genres": genres,
        "runtime": movie_details.get("runtime"),
        "status": movie_details.get("status"),
        "tagline": movie_details.get("tagline"),
        "budget": movie_details.get("budget"),
        "revenue": movie_details.get("revenue"),
        "posters": posters,
        "backdrops": backdrops,
        "fetched_at": datetime.now().isoformat()
    }

    return processed_movie, directors, actors, genres


def main():
    """Main function to fetch movie data and store it in MongoDB."""
    # Check if API key is set
    if not TMDB_API_KEY:
        logger.error("TMDB API key not found. Please set it in the .env file.")
        return

    # Initialize TMDB client
    tmdb_client = TMDBClient(TMDB_API_KEY)
    
    # Initialize MongoDB client
    movie_db = MovieDatabase(
        MONGODB_CONNECTION_STRING,
        MONGODB_DATABASE
    )

    # Lists to store movie IDs
    movie_ids = set()
    
    # Get now playing movies (in theaters)
    logger.info("Fetching movies now playing in theaters...")
    for page in range(1, 6):  # Get 5 pages (100 movies)
        now_playing = tmdb_client.get_now_playing_movies(page)
        for movie in now_playing:
            movie_ids.add(movie["id"])
            if len(movie_ids) >= 50:
                break
        if len(movie_ids) >= 50:
            break

    # Get upcoming movies
    logger.info("Fetching upcoming movies...")
    for page in range(1, 3):  # Get 2 pages (40 movies)
        upcoming = tmdb_client.get_upcoming_movies(page)
        for movie in upcoming:
            movie_ids.add(movie["id"])
            if len(movie_ids) >= 75:
                break
        if len(movie_ids) >= 75:
            break

    # Get popular movies to fill the rest
    logger.info("Fetching popular movies...")
    for page in range(1, 6):  # Get 5 pages (100 movies)
        popular = tmdb_client.get_popular_movies(page)
        for movie in popular:
            movie_ids.add(movie["id"])
            if len(movie_ids) >= 100:
                break
        if len(movie_ids) >= 100:
            break

    # Process each movie
    logger.info(f"Processing {len(movie_ids)} movies...")
    for movie_id in tqdm(list(movie_ids)[:100]):
        try:
            # Check if movie already exists in the database
            if movie_db.movie_exists(movie_id):
                logger.info(f"Movie ID {movie_id} already exists in the database. Updating...")
            
            # Get detailed movie information
            movie_details = tmdb_client.get_movie_details(movie_id)
            
            # Process the movie data into separate entities
            processed_movie, directors, actors, genres = process_movie_data(movie_details)
            
            # Update the movie and related entities in the database
            movie_db.update_movie(processed_movie, directors, actors, genres)
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.25)
        
        except Exception as e:
            logger.error(f"Error processing movie ID {movie_id}: {str(e)}")

    # Export all movies to a JSON file
    logger.info("Exporting all movies to JSON file...")
    all_movies = movie_db.get_all_movies_with_details()
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_JSON_FILE), exist_ok=True)
    
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_movies, f, ensure_ascii=False, indent=2)

    logger.info(f"Successfully exported {len(all_movies)} movies to {OUTPUT_JSON_FILE}")


if __name__ == "__main__":
    main() 