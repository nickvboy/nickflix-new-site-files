#!/usr/bin/env python3
"""
Script to fetch movie data from TMDB API, store it in MongoDB with organized collections, 
and output it to a JSON file.

Also includes theater data fetching functionality to locate major theater chains.
"""

import os
import json
import time
import logging
import random
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm
import argparse

# Configure logging
# Create log directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "movie_fetcher.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MovieFetcher")
logger.info(f"Logging to {LOG_FILE}")

LOGGING_LEVEL = logging.INFO

def initialize_logging():
    """Reconfigure logging with current LOGGING_LEVEL."""
    for handler in logger.handlers:
        handler.setLevel(LOGGING_LEVEL)
    logger.setLevel(LOGGING_LEVEL)
    logger.info(f"Logging level set to: {logging.getLevelName(LOGGING_LEVEL)}")

# Load environment variables from project root .env file
load_dotenv()  # This will look for .env in the current working directory
logger.info("Loaded environment variables from .env file")

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if TMDB_API_KEY:
    logger.info("TMDB API key found in environment variables")
else:
    logger.error("TMDB API key not found in environment variables")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/original"

# MongoDB Configuration
MONGODB_CONNECTION_STRING = "mongodb://localhost:27017/movie_database"
MONGODB_DATABASE = "movie_database"
MONGODB_COLLECTION_MOVIES = "movies"
MONGODB_COLLECTION_DIRECTORS = "directors"
MONGODB_COLLECTION_ACTORS = "actors"
MONGODB_COLLECTION_GENRES = "genres"
MONGODB_COLLECTION_CITIES = "cities"
MONGODB_COLLECTION_THEATERS = "theaters"
MONGODB_COLLECTION_PROGRESS = "progress"

# Output file paths
OUTPUT_JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies_data.json")
THEATERS_JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theaters.json")
US_CITIES_JSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_cities.json")

# Custom progress logger for theater processing
def log_progress(message, city=None, level="info"):
    """Log progress with optional city information"""
    if city:
        message = f"[{city}] {message}"
    
    if level == "info":
        logger.info(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
        
    # Also print to console for better visibility
    if level in ["info", "error", "warning"]:
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] {message}")


class MovieData:
    """Class for fetching and managing movie data from TMDB API."""
    
    def __init__(self):
        """Initialize MovieData with TMDB API configuration."""
        if not TMDB_API_KEY:
            raise ValueError("TMDB API key not found. Please set it in the .env file.")
            
        self.api_key = TMDB_API_KEY
        self.tmdb_base_url = TMDB_BASE_URL
        self.tmdb_image_base_url = TMDB_IMAGE_BASE_URL
        
        # Set up HTTP headers for API requests
        self.headers = {
            "User-Agent": "NickFlix Movie Fetcher/1.0 (nickflix@example.com)",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://nickflix.example.com"
        }
        
        # MongoDB connection
        try:
            # Connect to MongoDB
            log_progress("Connecting to MongoDB for movie data...", level="info")
            self.client = MongoClient(MONGODB_CONNECTION_STRING)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DATABASE]
            
            # Initialize collections
            self.movies_collection = self.db[MONGODB_COLLECTION_MOVIES]
            self.directors_collection = self.db[MONGODB_COLLECTION_DIRECTORS]
            self.actors_collection = self.db[MONGODB_COLLECTION_ACTORS]
            self.genres_collection = self.db[MONGODB_COLLECTION_GENRES]
            
            # Create indexes
            self.movies_collection.create_index("id", unique=True)
            self.directors_collection.create_index("id", unique=True)
            self.actors_collection.create_index("id", unique=True)
            self.genres_collection.create_index("id", unique=True)
            
            log_progress("MongoDB connection successful for movie data", level="info")
        except Exception as e:
            error_msg = str(e)
            log_progress(f"CRITICAL ERROR: Failed to connect to MongoDB: {error_msg}", level="error")
            log_progress("Check your MongoDB connection settings:", level="error")
            log_progress(f"Connection string: {mask_connection_string(MONGODB_CONNECTION_STRING)}", level="error")
            log_progress(f"Database name: {MONGODB_DATABASE}", level="error")
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")
    
    def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Retrieve detailed information about a specific movie from TMDB API.
        
        Args:
            movie_id: TMDB movie ID
            
        Returns:
            Dictionary containing movie details or None if unsuccessful
        """
        log_progress(f"Fetching details for movie ID: {movie_id}", level="debug")
        
        url = f"{self.tmdb_base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "append_to_response": "credits,videos,keywords,recommendations"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                movie_data = response.json()
                log_progress(f"Successfully retrieved data for movie: {movie_data.get('title', 'Unknown')}", level="debug")
                return movie_data
            else:
                log_progress(f"Failed to retrieve data for movie ID {movie_id}. Status code: {response.status_code}", level="warning")
                return None
        except Exception as e:
            log_progress(f"Error fetching movie details for ID {movie_id}: {str(e)}", level="error")
            return None
    
    def get_popular_movies(self, count: int = 50, min_vote_count: int = 1000, min_vote_average: float = 6.0) -> List[Dict]:
        """
        Retrieve popular movies from TMDB API.
        
        Args:
            count: Number of movies to retrieve
            min_vote_count: Minimum number of votes a movie should have
            min_vote_average: Minimum average rating a movie should have
            
        Returns:
            List of movie dictionaries
        """
        log_progress(f"Fetching {count} popular movies from TMDB API", level="info")
        
        url = f"{self.tmdb_base_url}/discover/movie"
        movies = []
        page = 1
        
        # Use tqdm to display progress
        progress = tqdm(total=count, desc="Fetching movies")
        
        while len(movies) < count:
            params = {
                "api_key": self.api_key,
                "sort_by": "popularity.desc",
                "vote_count.gte": min_vote_count,
                "vote_average.gte": min_vote_average,
                "page": page,
                "include_adult": False,
                "language": "en-US"
            }
            
            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    for movie in results:
                        if len(movies) < count:
                            # Get full movie details
                            movie_id = movie.get("id")
                            movie_details = self.get_movie_details(movie_id)
                            
                            if movie_details:
                                movies.append(movie_details)
                                progress.update(1)
                        else:
                            break
                            
                    # If no more results or we've reached the end, break
                    if not results or page >= data.get("total_pages", 1):
                        break
                        
                    page += 1
                else:
                    log_progress(f"Failed to retrieve popular movies. Status code: {response.status_code}", level="warning")
                    break
                    
            except Exception as e:
                log_progress(f"Error fetching popular movies: {str(e)}", level="error")
                break
                
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        
        progress.close()
        log_progress(f"Successfully retrieved {len(movies)} movies", level="info")
        return movies
    
    def process_movie_data(self, movie: Dict) -> Dict:
        """
        Process raw movie data to extract relevant information.
        
        Args:
            movie: Raw movie data dictionary from TMDB API
            
        Returns:
            Processed movie dictionary
        """
        # Create structured movie object
        processed_movie = {
            "id": movie.get("id"),
            "title": movie.get("title"),
            "original_title": movie.get("original_title"),
            "overview": movie.get("overview"),
            "tagline": movie.get("tagline"),
            "release_date": movie.get("release_date"),
            "runtime": movie.get("runtime"),
            "vote_average": movie.get("vote_average"),
            "vote_count": movie.get("vote_count"),
            "popularity": movie.get("popularity"),
            "status": movie.get("status"),
            "genres": [genre.get("id") for genre in movie.get("genres", [])],
            "budget": movie.get("budget"),
            "revenue": movie.get("revenue"),
            "poster_path": movie.get("poster_path"),
            "backdrop_path": movie.get("backdrop_path"),
            "imdb_id": movie.get("imdb_id"),
            "homepage": movie.get("homepage"),
            "original_language": movie.get("original_language"),
            
            # Extract video data (trailers)
            "videos": [
                {
                    "key": video.get("key"),
                    "name": video.get("name"),
                    "site": video.get("site"),
                    "type": video.get("type")
                }
                for video in movie.get("videos", {}).get("results", [])
                if video.get("site") == "YouTube" and video.get("type") == "Trailer"
            ],
            
            # Extract recommendations
            "recommendations": [
                {
                    "id": rec.get("id"),
                    "title": rec.get("title")
                }
                for rec in movie.get("recommendations", {}).get("results", [])[:5]
            ],
            
            # Extract keywords
            "keywords": [
                {
                    "id": keyword.get("id"),
                    "name": keyword.get("name")
                }
                for keyword in movie.get("keywords", {}).get("keywords", [])
            ],
            
            # Add additional metadata
            "last_updated": datetime.now().isoformat(),
            "poster_url": f"{self.tmdb_image_base_url}{movie.get('poster_path')}" if movie.get("poster_path") else None,
            "backdrop_url": f"{self.tmdb_image_base_url}{movie.get('backdrop_path')}" if movie.get("backdrop_path") else None
        }
        
        # Process cast and crew
        cast = []
        directors = []
        
        for person in movie.get("credits", {}).get("cast", [])[:10]:  # Get top 10 cast members
            cast.append({
                "id": person.get("id"),
                "name": person.get("name"),
                "character": person.get("character"),
                "profile_path": person.get("profile_path"),
                "order": person.get("order")
            })
            
        for person in movie.get("credits", {}).get("crew", []):
            if person.get("job") == "Director":
                directors.append({
                    "id": person.get("id"),
                    "name": person.get("name"),
                    "profile_path": person.get("profile_path")
                })
        
        processed_movie["cast"] = cast
        processed_movie["directors"] = directors
        
        return processed_movie
    
    def save_movie_to_mongodb(self, movie: Dict) -> bool:
        """
        Save processed movie data to MongoDB.
        
        Args:
            movie: Processed movie dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract related data for separate collections
            cast = movie.pop("cast", [])
            directors = movie.pop("directors", [])
            
            # Update or insert movie
            self.movies_collection.update_one(
                {"id": movie["id"]},
                {"$set": movie},
                upsert=True
            )
            
            # Process directors
            for director in directors:
                self.directors_collection.update_one(
                    {"id": director["id"]},
                    {"$set": {
                        **director,
                        "last_updated": datetime.now().isoformat()
                    }},
                    upsert=True
                )
            
            # Process actors
            for actor in cast:
                self.actors_collection.update_one(
                    {"id": actor["id"]},
                    {"$set": {
                        **actor,
                        "last_updated": datetime.now().isoformat()
                    }},
                    upsert=True
                )
            
            # Process genres
            for genre_id in movie.get("genres", []):
                # Get genre info from the original movie data
                genre_name = next((genre["name"] for genre in movie.get("genres_original", []) if genre["id"] == genre_id), "Unknown")
                
                self.genres_collection.update_one(
                    {"id": genre_id},
                    {"$set": {
                        "id": genre_id,
                        "name": genre_name,
                        "last_updated": datetime.now().isoformat()
                    }},
                    upsert=True
                )
            
            return True
        except Exception as e:
            log_progress(f"Error saving movie to MongoDB: {str(e)}", level="error")
            return False
    
    def download_movie_images(self, movie: Dict, base_path: str = "movie_data/images") -> Dict[str, str]:
        """
        Download poster and backdrop images for a movie.
        
        Args:
            movie: Movie dictionary with poster_url and backdrop_url
            base_path: Base directory to save images to
            
        Returns:
            Dictionary with paths to downloaded images
        """
        image_paths = {
            "poster_path": None,
            "backdrop_path": None
        }
        
        # Create directories if they don't exist
        poster_dir = os.path.join(base_path, "posters")
        backdrop_dir = os.path.join(base_path, "backdrops")
        os.makedirs(poster_dir, exist_ok=True)
        os.makedirs(backdrop_dir, exist_ok=True)
        
        # Download poster
        if movie.get("poster_url"):
            try:
                movie_id = movie.get("id")
                title = movie.get("title", "").replace(" ", "_")
                poster_filename = f"{movie_id}_{title}_poster.jpg"
                poster_path = os.path.join(poster_dir, poster_filename)
                
                response = requests.get(movie.get("poster_url"), headers=self.headers, timeout=20)
                if response.status_code == 200:
                    with open(poster_path, "wb") as f:
                        f.write(response.content)
                    image_paths["poster_path"] = poster_path
                    log_progress(f"Downloaded poster for movie {movie.get('title')}", level="debug")
            except Exception as e:
                log_progress(f"Error downloading poster for movie {movie.get('title')}: {str(e)}", level="warning")
        
        # Download backdrop
        if movie.get("backdrop_url"):
            try:
                movie_id = movie.get("id")
                title = movie.get("title", "").replace(" ", "_")
                backdrop_filename = f"{movie_id}_{title}_backdrop.jpg"
                backdrop_path = os.path.join(backdrop_dir, backdrop_filename)
                
                response = requests.get(movie.get("backdrop_url"), headers=self.headers, timeout=20)
                if response.status_code == 200:
                    with open(backdrop_path, "wb") as f:
                        f.write(response.content)
                    image_paths["backdrop_path"] = backdrop_path
                    log_progress(f"Downloaded backdrop for movie {movie.get('title')}", level="debug")
            except Exception as e:
                log_progress(f"Error downloading backdrop for movie {movie.get('title')}: {str(e)}", level="warning")
        
        return image_paths
    
    def fetch_and_save_movies(self, count: int = 50, download_images: bool = True) -> Dict[str, Any]:
        """
        Fetch popular movies, process them, and save to MongoDB.
        
        Args:
            count: Number of movies to fetch
            download_images: Whether to download poster and backdrop images
            
        Returns:
            Dictionary with statistics about the process
        """
        log_progress(f"Starting movie data collection. Fetching {count} movies...", level="info")
        
        stats = {
            "requested": count,
            "fetched": 0,
            "saved": 0,
            "with_images": 0,
            "errors": 0,
            "genres": set(),
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Get popular movies
            movies = self.get_popular_movies(count=count)
            stats["fetched"] = len(movies)
            
            log_progress(f"Processing and saving {len(movies)} movies to MongoDB...", level="info")
            
            # Process each movie
            for movie in tqdm(movies, desc="Saving movies to MongoDB"):
                try:
                    # Save original genres before processing
                    movie["genres_original"] = movie.get("genres", [])
                    
                    # Process movie data
                    processed_movie = self.process_movie_data(movie)
                    
                    # Download images if requested
                    if download_images:
                        image_paths = self.download_movie_images(processed_movie)
                        if image_paths.get("poster_path") or image_paths.get("backdrop_path"):
                            stats["with_images"] += 1
                    
                    # Save to MongoDB
                    if self.save_movie_to_mongodb(processed_movie):
                        stats["saved"] += 1
                        
                        # Track genres
                        for genre in movie.get("genres", []):
                            stats["genres"].add(genre.get("name"))
                    
                except Exception as e:
                    log_progress(f"Error processing movie {movie.get('title', 'Unknown')}: {str(e)}", level="error")
                    stats["errors"] += 1
            
            stats["end_time"] = datetime.now().isoformat()
            stats["genres"] = list(stats["genres"])
            
            log_progress(f"Movie data collection complete. Saved {stats['saved']} out of {stats['fetched']} movies.", level="info")
            
            # Generate summary statistics
            genres_summary = {}
            for genre_name in stats["genres"]:
                count = self.movies_collection.count_documents({"genres_original.name": genre_name})
                genres_summary[genre_name] = count
            
            log_progress("Genre statistics:", level="info")
            for genre, count in sorted(genres_summary.items(), key=lambda x: x[1], reverse=True):
                log_progress(f"  {genre}: {count} movies", level="info")
            
            return stats
        
        except Exception as e:
            log_progress(f"Error in fetch_and_save_movies: {str(e)}", level="error")
            stats["errors"] += 1
            stats["end_time"] = datetime.now().isoformat()
            return stats


class TheaterData:
    """Class for fetching and managing theater location data."""
    
    def __init__(self):
        """Initialize TheaterData with default configuration."""
        self.headers = {
            "User-Agent": "NickFlix Theater Locator/1.0 (nickflix@example.com)",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://nickflix.example.com"
        }
        # Target theater chains - we'll only collect these
        self.target_theaters = ["amc", "regal", "cinemark"]
        
        # MongoDB connection - No fallback anymore
        try:
            # Connect to MongoDB
            log_progress("Connecting to MongoDB...", level="info")
            self.client = MongoClient(MONGODB_CONNECTION_STRING)
            # Test connection - this will raise an exception if connection fails
            self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DATABASE]
            
            # Initialize collections
            self.cities_collection = self.db[MONGODB_COLLECTION_CITIES]
            self.theaters_collection = self.db[MONGODB_COLLECTION_THEATERS]
            self.progress_collection = self.db[MONGODB_COLLECTION_PROGRESS]
            
            # Create indexes
            self.cities_collection.create_index("geoid", unique=True)
            self.theaters_collection.create_index("unique_id")
            self.theaters_collection.create_index("brand")
            self.theaters_collection.create_index("city_geoid")
            
            log_progress("MongoDB connection successful", level="info")
        except Exception as e:
            error_msg = str(e)
            log_progress(f"CRITICAL ERROR: Failed to connect to MongoDB: {error_msg}", level="error")
            log_progress("Check your MongoDB connection settings:", level="error")
            log_progress(f"Connection string: {mask_connection_string(MONGODB_CONNECTION_STRING)}", level="error")
            log_progress(f"Database name: {MONGODB_DATABASE}", level="error")
            
            # Add specific guidance based on error message
            if "timed out" in error_msg:
                log_progress("Connection timed out. This could be due to:", level="error")
                log_progress("1. MongoDB server is not running or not accessible", level="error")
                log_progress("2. Firewall is blocking the connection", level="error")
                log_progress("3. MongoDB server address is incorrect", level="error")
                log_progress("4. Network connectivity issues", level="error")
                log_progress("Suggested actions:", level="error")
                log_progress("- Verify the MongoDB server is running", level="error")
                log_progress("- Check if the MongoDB host is reachable (try ping command)", level="error")
                log_progress("- Verify MongoDB port is open (default: 27017)", level="error")
                log_progress("- Check if MongoDB connection string is correct in .env file", level="error")
            elif "Authentication failed" in error_msg:
                log_progress("Authentication failed. This could be due to:", level="error")
                log_progress("1. Incorrect username or password", level="error")
                log_progress("2. User does not have access to the database", level="error")
                log_progress("Suggested actions:", level="error")
                log_progress("- Verify username and password in the connection string", level="error")
                log_progress("- Check if the user has appropriate permissions", level="error")
            elif "not valid" in error_msg:
                log_progress("Invalid MongoDB connection string. Please check the format:", level="error")
                log_progress("Format should be: mongodb://[username:password@]host[:port]/[database]", level="error")
            
            log_progress("Please fix the MongoDB connection and try again.", level="error")
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")
    
    def get_city_coordinates(self, city_name: str, use_fallback: bool = True) -> Dict[str, Any]:
        """Get geographic coordinates for a city using Nominatim or fallback data."""
        log_progress(f"Getting coordinates for {city_name}", city_name)
        
        # Define fallback coordinates for common cities
        fallback_coordinates = {
            "tampa, florida": {
                "boundingbox": ["27.9269509", "28.1740211", "-82.5329168", "-82.3015008"],
                "display_name": "Tampa, Hillsborough County, Florida, United States"
            },
            "new york, ny": {
                "boundingbox": ["40.4774991", "40.9175771", "-74.2590899", "-73.7002721"],
                "display_name": "New York City, New York, United States"
            },
            "los angeles, ca": {
                "boundingbox": ["33.7036928", "34.3373061", "-118.6681759", "-118.1552891"],
                "display_name": "Los Angeles, Los Angeles County, California, United States"
            },
            "chicago, il": {
                "boundingbox": ["41.6443428", "42.0230669", "-87.9402669", "-87.5236609"],
                "display_name": "Chicago, Cook County, Illinois, United States"
            },
            "houston, tx": {
                "boundingbox": ["29.5216759", "30.1105087", "-95.7619805", "-95.0137483"],
                "display_name": "Houston, Harris County, Texas, United States"
            },
            "philadelphia, pa": {
                "boundingbox": ["39.8669060", "40.1379919", "-75.2802976", "-74.9557629"],
                "display_name": "Philadelphia, Philadelphia County, Pennsylvania, United States"
            },
            "san antonio, tx": {
                "boundingbox": ["29.2733861", "29.7604981", "-98.7261377", "-98.2699455"],
                "display_name": "San Antonio, Bexar County, Texas, United States"
            },
            "san diego, ca": {
                "boundingbox": ["32.5343699", "33.0845412", "-117.2897284", "-116.9072855"],
                "display_name": "San Diego, San Diego County, California, United States"
            },
            "dallas, tx": {
                "boundingbox": ["32.6170157", "33.0164441", "-97.0084028", "-96.5559534"],
                "display_name": "Dallas, Dallas County, Texas, United States"
            },
            "jacksonville, fl": {
                "boundingbox": ["30.1009328", "30.5868733", "-82.0261417", "-81.3892418"],
                "display_name": "Jacksonville, Duval County, Florida, United States"
            }
        }
        
        # Clean and simplify the city name for better results
        # Remove suffixes like "city" and simplify state codes
        simplified_city = city_name.lower()
        simplified_city = simplified_city.replace(" city", "").strip()
        
        # Extract primary city name for searching
        primary_city = simplified_city.split(',')[0].strip() if ',' in simplified_city else simplified_city
        
        # Create a mapping of simplified city names
        city_key = simplified_city
        
        # Try to get from Nominatim API
        try:
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            nominatim_params = {
                "q": primary_city,  # Use simplified primary city name
                "format": "json",
                "limit": 1
            }
            
            log_progress(f"Making request to Nominatim API for {primary_city}", city_name, "debug")
            nominatim_response = requests.get(
                nominatim_url, 
                params=nominatim_params, 
                headers=self.headers,
                timeout=10
            )
            
            if nominatim_response.status_code != 200:
                log_progress(f"Nominatim API returned status code {nominatim_response.status_code}", city_name, "warning")
                
                if use_fallback and city_key in fallback_coordinates:
                    log_progress(f"Using fallback coordinates for {city_name}", city_name)
                    return self._expand_bounding_box(fallback_coordinates[city_key])
                else:
                    raise ValueError(f"Failed to get data from Nominatim API. Status code: {nominatim_response.status_code}")
                    
            nominatim_data = nominatim_response.json()
            
            if not nominatim_data:
                log_progress(f"No data returned from Nominatim API for {city_name}", city_name, "warning")
                
                # Try with just the city name without state
                if "," in simplified_city:
                    primary_city = simplified_city.split(',')[0].strip()
                    log_progress(f"Retrying with just city name: {primary_city}", city_name)
                    
                    nominatim_params["q"] = primary_city
                    nominatim_response = requests.get(
                        nominatim_url, 
                        params=nominatim_params, 
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if nominatim_response.status_code == 200:
                        nominatim_data = nominatim_response.json()
                
                # If still no data, use fallback
                if not nominatim_data:
                    if use_fallback and city_key in fallback_coordinates:
                        log_progress(f"Using fallback coordinates for {city_name}", city_name)
                        return self._expand_bounding_box(fallback_coordinates[city_key])
                    else:
                        raise ValueError(f"City not found: {city_name}")
                    
            log_progress(f"Successfully retrieved coordinates for {city_name}", city_name)
            return self._expand_bounding_box(nominatim_data[0])
            
        except Exception as e:
            log_progress(f"Error getting coordinates for {city_name}: {str(e)}", city_name, "error")
            
            if use_fallback and city_key in fallback_coordinates:
                log_progress(f"Using fallback coordinates for {city_name}", city_name)
                return self._expand_bounding_box(fallback_coordinates[city_key])
            else:
                raise
    
    def _expand_bounding_box(self, location_data: Dict) -> Dict:
        """Expand the bounding box to ensure it covers a reasonable area around the city center."""
        # Ensure we have a bounding box
        if "boundingbox" not in location_data or len(location_data["boundingbox"]) < 4:
            # If no bounding box but we have lat/lon, create one
            if "lat" in location_data and "lon" in location_data:
                try:
                    lat = float(location_data["lat"])
                    lon = float(location_data["lon"])
                    # Create a 10km x 10km bounding box around the point (approximately)
                    # 0.1 degrees is roughly 11km at the equator
                    location_data["boundingbox"] = [
                        str(lat - 0.05),  # south
                        str(lat + 0.05),  # north
                        str(lon - 0.05),  # west
                        str(lon + 0.05)   # east
                    ]
                    log_progress(f"Created bounding box around point: {location_data['boundingbox']}")
                except (ValueError, KeyError) as e:
                    log_progress(f"Failed to create bounding box from lat/lon: {str(e)}", level="warning")
            return location_data
        
        try:
            # Convert bounding box values to float
            south = float(location_data["boundingbox"][0])
            north = float(location_data["boundingbox"][1])
            west = float(location_data["boundingbox"][2])
            east = float(location_data["boundingbox"][3])
            
            # Calculate current dimensions
            lat_span = north - south
            lon_span = east - west
            
            # Check if bounding box is too small (less than ~5km)
            min_span = 0.05  # approximately 5.5km at the equator
            
            # Expand box if needed to ensure minimum coverage
            if lat_span < min_span:
                center_lat = (north + south) / 2
                south = center_lat - min_span / 2
                north = center_lat + min_span / 2
                log_progress(f"Expanded latitude range to ensure minimum coverage: {south} to {north}")
                
            if lon_span < min_span:
                center_lon = (east + west) / 2
                west = center_lon - min_span / 2
                east = center_lon + min_span / 2
                log_progress(f"Expanded longitude range to ensure minimum coverage: {west} to {east}")
            
            # Update the bounding box
            location_data["boundingbox"] = [str(south), str(north), str(west), str(east)]
            
        except (ValueError, IndexError) as e:
            log_progress(f"Error expanding bounding box: {str(e)}", level="warning")
            
        return location_data
    
    def fetch_theaters(self, city_name: str = "Tampa, Florida", city_data: Dict = None) -> List[Dict[str, Any]]:
        """
        Generate sample theaters for a city based on the city name and target theater brands.
        No API calls are made - simply generates theaters using brand names.
        
        Args:
            city_name: Name of the city to generate theaters for
            city_data: Optional city data dictionary with additional info
            
        Returns:
            List of theater dictionaries with name and brand information
        """
        log_progress(f"Generating theaters for {city_name}", city_name)
        
        # Clean city name
        query_city_name = city_name
        for suffix in [" city", " town", " village", " CDP"]:
            query_city_name = query_city_name.replace(suffix, "")
        
        # If city name has a comma (e.g., "Tampa, Florida"), extract the main city part
        if "," in query_city_name:
            query_city_name = query_city_name.split(",")[0].strip()
            
        # Extract geoid from city_data if available
        city_geoid = city_data.get("geoid") if city_data else None
        
        # Get population from city_data if available - larger cities get more theaters
        population = city_data.get("population", 0) if city_data else 0
        
        # Determine how many theaters to generate based on population
        if population > 1000000:  # Large city
            num_theaters = random.randint(8, 15)
        elif population > 250000:  # Medium city
            num_theaters = random.randint(4, 8)
        elif population > 50000:   # Small city
            num_theaters = random.randint(1, 4)
        else:                      # Very small city/town
            num_theaters = random.randint(0, 2)
            
        log_progress(f"Generating {num_theaters} theaters for {query_city_name} (population: {population})", city_name)
        
        # Generate theater data
        theaters = []
        target_theaters = self.target_theaters
        
        # Theater name templates for different brands
        theater_templates = {
            "amc": [
                "{city} AMC {number}",
                "AMC {city} {number}",
                "AMC {city} Mall {number}"
            ],
            "regal": [
                "Regal {city} {number}",
                "Regal {city} Stadium {number}",
                "{city} Regal Cinema"
            ],
            "cinemark": [
                "Cinemark {city} {number}",
                "Cinemark {city} Mall",
                "{city} Cinemark"
            ]
        }
        
        # Generate theaters for each brand
        for i in range(num_theaters):
            # Randomly select a brand
            brand = random.choice(target_theaters)
            
            # Randomly select a template for this brand
            template = random.choice(theater_templates[brand])
            
            # Generate a number for the theater (if the template has {number})
            number = random.randint(8, 24)
            
            # Generate theater name
            name = template.format(city=query_city_name, number=number)
            
            # Generate a unique ID
            unique_id = f"{brand}-{query_city_name.lower().replace(' ', '-')}-{i}"
            
            # Create theater info
            theater_info = {
            "unique_id": unique_id,
                "name": name,
                "brand": brand,
                "source_city": city_name,
                "city_geoid": city_geoid,
                "last_updated": datetime.now().isoformat()
            }
            
            theaters.append(theater_info)
            log_progress(f"Added theater: {name} ({brand})", city_name)
        
        log_progress(f"Generated {len(theaters)} theaters for {query_city_name}", city_name)
        return theaters
    
    def load_cities_from_json(self, json_file=US_CITIES_JSON_FILE) -> Dict[str, Dict]:
        """Load cities from the JSON file."""
        log_progress(f"Loading cities from {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                cities_data = json.load(f)
                
            log_progress(f"Loaded {len(cities_data)} cities from JSON file")
            return cities_data
        except Exception as e:
            log_progress(f"Error loading cities from JSON file: {str(e)}", level="error")
            return {}
    
    def import_cities_to_mongodb(self, json_file=US_CITIES_JSON_FILE) -> int:
        """Import cities from JSON to MongoDB and return count."""
        log_progress(f"Importing cities from {json_file} to MongoDB")
        
        # Load cities from JSON
        cities_data = self.load_cities_from_json(json_file)
        if not cities_data:
            return 0
            
        # Process and insert cities
        imported_count = 0
        for geoid, city_data in tqdm(cities_data.items()):
            # Add geoid to the data
            city_data["geoid"] = geoid
            
            # Set processed flag to False
            city_data["processed"] = False
            city_data["theaters_found"] = 0
            city_data["last_updated"] = datetime.now().isoformat()
            
            try:
                # Insert or update city in MongoDB
                self.cities_collection.update_one(
                    {"geoid": geoid},
                    {"$set": city_data},
                    upsert=True
                )
                imported_count += 1
            except Exception as e:
                log_progress(f"Error importing city {geoid}: {str(e)}", level="error")
                
        log_progress(f"Successfully imported {imported_count} cities to MongoDB")
        return imported_count
    
    def save_theaters_to_mongodb(self, theaters: List[Dict[str, Any]], city_geoid: str = None) -> int:
        """Save theaters to MongoDB and return count of saved theaters."""
        saved_count = 0
        for theater in theaters:
            try:
                # Set city_geoid if provided
                if city_geoid:
                    theater["city_geoid"] = city_geoid
                    
                # Update or insert theater
                self.theaters_collection.update_one(
                    {"unique_id": theater["unique_id"]},
                    {"$set": theater},
                    upsert=True
                )
                saved_count += 1
            except Exception as e:
                log_progress(f"Error saving theater {theater.get('name')}: {str(e)}", level="error")
                
        return saved_count
    
    def mark_city_as_processed(self, city_geoid: str, theaters_found: int = 0, error: str = None) -> bool:
        """Mark a city as processed in MongoDB."""
        try:
            update_data = {
                "processed": True,
                "theaters_found": theaters_found,
                "processed_at": datetime.now().isoformat()
            }
            
            if error:
                update_data["error"] = error
                
            self.cities_collection.update_one(
                {"geoid": city_geoid},
                {"$set": update_data}
            )
            return True
        except Exception as e:
            log_progress(f"Error marking city {city_geoid} as processed: {str(e)}", level="error")
            return False
    
    def save_progress(self, progress_data: Dict[str, Any]) -> bool:
        """Save progress data to MongoDB."""
        try:
            progress_data["timestamp"] = datetime.now().isoformat()
            self.progress_collection.insert_one(progress_data)
            return True
        except Exception as e:
            log_progress(f"Error saving progress: {str(e)}", level="error")
            return False
    
    def get_last_progress(self) -> Dict[str, Any]:
        """Get the last progress record from MongoDB."""
        try:
            progress = self.progress_collection.find_one(
                sort=[("timestamp", -1)]
            )
            return progress or {}
        except Exception as e:
            log_progress(f"Error getting last progress: {str(e)}", level="error")
            return {}
    
    def save_theaters(self, theaters: List[Dict[str, Any]], output_file: str = THEATERS_JSON_FILE) -> None:
        """Save theater data to a JSON file for backup or offline use."""
        log_progress(f"Saving {len(theaters)} theaters to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(theaters, f, ensure_ascii=False, indent=2)

    def update_cities_with_nominatim_coordinates(self, batch_size=100, delay_between_requests=1) -> Dict[str, int]:
        """
        Fetch bounding box coordinates from Nominatim for cities that need them.
        Updates MongoDB with the coordinates and finds theaters for these cities.
        
        Args:
            batch_size: Number of cities to process at once
            delay_between_requests: Delay in seconds between Nominatim API requests
            
        Returns:
            Dictionary with statistics about the process
        """
        log_progress("Starting Nominatim coordinate update for cities", level="info")
        
        # Get cities that have no bounding box coordinates but have names
        # We look for cities that haven't been processed and have a name
        cities_to_update = list(self.cities_collection.find({
            "$or": [
                {"boundingbox": {"$exists": False}},
                {"boundingbox": None}
            ],
            "processed": False,
            "$or": [
                {"city": {"$exists": True, "$ne": ""}},
                {"name": {"$exists": True, "$ne": ""}}
            ]
        }).limit(batch_size))
        
        if not cities_to_update:
            log_progress("No cities found that need coordinate updates", level="info")
            return {"cities_processed": 0, "cities_updated": 0, "cities_with_errors": 0, "theaters_found": 0}
        
        log_progress(f"Found {len(cities_to_update)} cities that need coordinate updates", level="info")
        
        stats = {
            "cities_processed": 0,
            "cities_updated": 0,
            "cities_with_errors": 0,
            "theaters_found": 0
        }
        
        for city in cities_to_update:
            stats["cities_processed"] += 1
            city_geoid = city.get("geoid")
            
            # Get city name for Nominatim query
            city_name = city.get("name") or city.get("city", "")
            state_name = city.get("state_name") or city.get("state", "")
            
            # Format city name for Nominatim query
            if state_name:
                query_city_name = f"{city_name}, {state_name}"
            else:
                query_city_name = city_name
                
            log_progress(f"Processing city: {query_city_name} (GEOID: {city_geoid})", query_city_name)
            
            try:
                # Get coordinates from Nominatim
                location_data = self.get_city_coordinates(query_city_name, use_fallback=False)
                
                if not location_data or "boundingbox" not in location_data:
                    log_progress(f"No coordinates found for {query_city_name}", query_city_name, "warning")
                    stats["cities_with_errors"] += 1
                    continue
                
                # Update city with bounding box coordinates
                update_data = {
                    "boundingbox": location_data["boundingbox"],
                    "display_name": location_data.get("display_name", ""),
                    "coordinates_updated": datetime.now().isoformat()
                }
                
                # Add lat/lon if available
                if "lat" in location_data and "lon" in location_data:
                    update_data["lat"] = float(location_data["lat"])
                    update_data["lon"] = float(location_data["lon"])
                
                # Update the city in MongoDB
                self.cities_collection.update_one(
                    {"geoid": city_geoid},
                    {"$set": update_data}
                )
                
                log_progress(f"Updated coordinates for {query_city_name}", query_city_name)
                stats["cities_updated"] += 1
                
                # Optional: Fetch theaters for this city now that we have coordinates
                try:
                    # Use the updated city data to fetch theaters
                    updated_city = self.cities_collection.find_one({"geoid": city_geoid})
                    theaters = self.fetch_theaters(query_city_name, updated_city)
                    
                    if theaters:
                        # Save theaters to MongoDB
                        saved_count = self.save_theaters_to_mongodb(theaters, city_geoid)
                        stats["theaters_found"] += saved_count
                        
                        # Mark city as processed
                        self.mark_city_as_processed(city_geoid, saved_count)
                        log_progress(f"Found and saved {saved_count} theaters for {query_city_name}", query_city_name)
                    else:
                        # Mark as processed but with 0 theaters
                        self.mark_city_as_processed(city_geoid, 0)
                        log_progress(f"No theaters found for {query_city_name}", query_city_name)
                except Exception as e:
                    log_progress(f"Error fetching theaters for {query_city_name}: {str(e)}", query_city_name, "error")
                    # Mark as processed but with error
                    self.mark_city_as_processed(city_geoid, 0, str(e))
            
            except Exception as e:
                log_progress(f"Error updating coordinates for {query_city_name}: {str(e)}", query_city_name, "error")
                stats["cities_with_errors"] += 1
            
            # Add delay between requests to avoid rate limiting
            if delay_between_requests > 0:
                time.sleep(delay_between_requests)
        
        log_progress(f"Finished Nominatim coordinate update. Stats: {stats}", level="info")
        return stats
    
    def get_cities_by_population(self, limit=None, skip=0) -> List[Dict[str, Any]]:
        """Get cities sorted by population (highest first)."""
        # Find cities with population data and sort by population (descending)
        cursor = self.cities_collection.find(
            {"population": {"$exists": True, "$ne": None}},
            {"_id": 0}
        ).sort("population", -1).skip(skip)
        
        if limit:
            cursor = cursor.limit(limit)
            
        cities = list(cursor)
        log_progress(f"Retrieved {len(cities)} cities sorted by population (skip={skip}, limit={limit})")
        return cities
    
    def get_pending_cities(self, limit=None) -> List[Dict[str, Any]]:
        """Get cities that have not been processed yet, sorted by population."""
        # Find cities that haven't been processed and have population data
        cursor = self.cities_collection.find(
            {
                "processed": {"$ne": True},
                "population": {"$exists": True, "$ne": None}
            },
            {"_id": 0}
        ).sort("population", -1)
        
        if limit:
            cursor = cursor.limit(limit)
            
        cities = list(cursor)
        log_progress(f"Retrieved {len(cities)} pending cities")
        return cities
    
    def process_batch_of_cities(self, batch_size=10, delay_between_cities=3, timeout=None) -> Dict[str, Any]:
        """
        Process a batch of cities to find theaters.
        
        Args:
            batch_size: Number of cities to process in this batch
            delay_between_cities: Delay in seconds between cities
            timeout: Optional timeout in seconds for the entire batch
            
        Returns:
            Dictionary with statistics about the processed batch
        """
        log_progress(f"Starting processing batch of {batch_size} cities")
        
        # Statistics for this batch
        stats = {
            "batch_size": batch_size,
            "processed_cities": 0,
            "pending_cities": 0,
            "theaters_found": 0,
            "errors": 0,
            "batch_start": datetime.now().isoformat(),
            "status": "completed"  # Default status
        }
        
        # Get batch of cities to process
        cities = self.get_pending_cities(limit=batch_size)
        stats["pending_cities"] = len(cities)
        
        if not cities:
            log_progress("No pending cities found to process")
            return stats
        
        start_time = time.time()
        
        # Process each city
        for i, city in enumerate(cities):
            city_name = f"{city['name']}, {city['state']}"
            geoid = city["geoid"]
            
            log_progress(f"Processing city {i+1}/{len(cities)}: {city_name} (Population: {city.get('population', 'N/A')})", city_name)
            
            try:
                # Check if timeout is reached
                if timeout and (time.time() - start_time) > timeout:
                    log_progress(f"Timeout reached after processing {i} cities", level="warning")
                    stats["status"] = "timeout"
                    break
                
                # Fetch theaters for this city
                theaters = self.fetch_theaters(city_name, city)
                theaters_count = len(theaters)
                
                # Save theaters to MongoDB
                saved_count = self.save_theaters_to_mongodb(theaters, city_geoid=geoid)
                log_progress(f"Saved {saved_count} theaters to MongoDB", city_name)
                
                # Mark city as processed
                self.mark_city_as_processed(geoid, theaters_found=theaters_count)
                
                # Update stats
                stats["processed_cities"] += 1
                stats["theaters_found"] += theaters_count
                
                # Add delay between cities to avoid rate limits (except for the last city)
                if i < len(cities) - 1:
                    actual_delay = random.uniform(delay_between_cities, delay_between_cities + 2)
                    log_progress(f"Adding delay of {actual_delay:.2f} seconds before next city", level="debug")
                    time.sleep(actual_delay)
            
            except Exception as e:
                log_progress(f"Error processing city {city_name}: {str(e)}", city_name, "error")
                # Mark city as processed with error
                self.mark_city_as_processed(geoid, error=str(e))
                stats["errors"] += 1
        
        # Calculate time taken
        end_time = time.time()
        stats["duration_seconds"] = end_time - start_time
        stats["batch_end"] = datetime.now().isoformat()
        
        # Save progress
        self.save_progress(stats)
        
        # Log summary
        log_progress(f"Batch processing complete. Processed {stats['processed_cities']} cities, found {stats['theaters_found']} theaters, encountered {stats['errors']} errors")
        return stats
    
    def process_all_cities(self, batch_size=10, delay_between_batches=30, max_batches=None, timeout_per_batch=1800):
        """
        Process all cities in batches, with the ability to resume from where it left off.
        
        Args:
            batch_size: Number of cities to process in each batch
            delay_between_batches: Delay in seconds between batches
            max_batches: Maximum number of batches to process (None = no limit)
            timeout_per_batch: Timeout in seconds for each batch
        """
        log_progress(f"Starting processing of all cities in batches of {batch_size}")
        
        # Get the total number of cities
        total_pending = self.cities_collection.count_documents({
            "processed": {"$ne": True},
            "population": {"$exists": True, "$ne": None}
        })
        
        # Calculate the estimated number of batches
        estimated_batches = (total_pending + batch_size - 1) // batch_size
        max_batches = min(estimated_batches, max_batches) if max_batches else estimated_batches
        
        log_progress(f"Found {total_pending} pending cities, estimated {estimated_batches} batches needed")
        
        # Summary stats
        summary = {
            "total_pending_start": total_pending,
            "start_time": datetime.now().isoformat(),
            "batches_completed": 0,
            "cities_processed": 0,
            "theaters_found": 0,
            "errors": 0
        }
        
        # Process batches
        for batch_num in range(1, max_batches + 1):
            try:
                # Get updated pending count
                pending_count = self.cities_collection.count_documents({
                    "processed": {"$ne": True},
                    "population": {"$exists": True, "$ne": None}
                })
                
                if pending_count == 0:
                    log_progress("No more pending cities, processing complete!")
                    break
                    
                log_progress(f"Starting batch {batch_num}/{max_batches} ({pending_count} cities remaining)")
                
                # Process a batch
                batch_stats = self.process_batch_of_cities(
                    batch_size=batch_size,
                    delay_between_cities=3,
                    timeout=timeout_per_batch
                )
                
                # Update summary
                summary["batches_completed"] += 1
                summary["cities_processed"] += batch_stats.get("processed_cities", 0)
                summary["theaters_found"] += batch_stats.get("theaters_found", 0)
                summary["errors"] += batch_stats.get("errors", 0)
                
                # Save summary progress
                summary["last_update"] = datetime.now().isoformat()
                self.save_progress({"type": "summary", **summary})
                
                # Log batch summary
                log_progress(f"Completed batch {batch_num}/{max_batches}: processed {batch_stats.get('processed_cities', 0)} cities, found {batch_stats.get('theaters_found', 0)} theaters")
                
                # Check if we should continue
                if batch_num < max_batches and pending_count > 0:
                    log_progress(f"Adding delay of {delay_between_batches} seconds before next batch")
                    time.sleep(delay_between_batches)
                else:
                    log_progress("All batches completed or no more pending cities")
                    break
                    
            except KeyboardInterrupt:
                log_progress("Processing interrupted by user", level="warning")
                break
            except Exception as e:
                log_progress(f"Error during batch {batch_num}: {str(e)}", level="error")
                summary["errors"] += 1
                # Continue with next batch after a delay
                log_progress(f"Continuing with next batch after delay of {delay_between_batches} seconds")
                time.sleep(delay_between_batches)
        
        # Calculate final stats
        summary["end_time"] = datetime.now().isoformat()
        total_pending_end = self.cities_collection.count_documents({
            "processed": {"$ne": True},
            "population": {"$exists": True, "$ne": None}
        })
        summary["total_pending_end"] = total_pending_end
        
        # Save final summary
        self.save_progress({"type": "final_summary", **summary})
        
        # Export all theaters to JSON
        self.export_all_theaters_to_json()
        
        log_progress(f"Theater data collection complete. Processed {summary['cities_processed']} cities, found {summary['theaters_found']} theaters.")
    
    def export_all_theaters_to_json(self, output_file=THEATERS_JSON_FILE):
        """Export all theaters from MongoDB to a JSON file."""
        try:
            # Get all theaters from MongoDB
            theaters = list(self.theaters_collection.find({}, {"_id": 0}))
            
            # Save to JSON file
            self.save_theaters(theaters, output_file)
            
            # Generate brand summary
            brands = {}
            for theater in theaters:
                brand = theater.get("brand", "other")
                if brand not in brands:
                    brands[brand] = 0
                brands[brand] += 1
            
            log_progress("Theater brand summary:")
            for brand, count in brands.items():
                log_progress(f"  {brand}: {count} theaters")
                
        except Exception as e:
            log_progress(f"Error exporting theaters to JSON: {str(e)}", level="error")
    
    def fetch_theaters_in_cities(self, cities: List[str]) -> List[Dict[str, Any]]:
        """Fetch theaters in multiple cities and combine results."""
        all_theaters = []
        
        for city in cities:
            try:
                log_progress(f"Fetching theaters in {city}", city)
                city_theaters = self.fetch_theaters(city)
                all_theaters.extend(city_theaters)
                
                # Add delay between cities to avoid rate limits
                if city != cities[-1]:  # Skip delay after last city
                    delay = random.uniform(2, 5)
                    log_progress(f"Adding delay of {delay:.2f} seconds before next city", city, "debug")
                    time.sleep(delay)
            except Exception as e:
                log_progress(f"Error fetching theaters in {city}: {str(e)}", city, "error")
                # Continue with next city even if one fails
        
        return all_theaters
    
    def fetch_and_save_theaters(self, cities: List[str] = None) -> None:
        """Fetch theaters in specified cities and save them to JSON."""
        if cities is None:
            cities = ["Tampa, Florida", "Orlando, Florida", "New York, NY", "Los Angeles, CA"]
            
        log_progress(f"Fetching theaters in {len(cities)} cities: {', '.join(cities)}")
        
        all_theaters = self.fetch_theaters_in_cities(cities)
        self.save_theaters(all_theaters)
        
        log_progress(f"Completed theater data collection: {len(all_theaters)} theaters saved")


def process_all_cities_with_theaters(batch_size=3):
    """Process all cities in the US cities database and find theaters in each."""
    log_progress("Starting full processing of all US cities for theaters")
    
    # Initialize theater data with MongoDB - will raise an error if connection fails
    theater_data = TheaterData()
    
    # Import cities to MongoDB
    theater_data.import_cities_to_mongodb()
    
    # Process all cities, starting with largest population
    theater_data.process_all_cities(
        batch_size=batch_size,   # Process cities per batch (default 3)
        delay_between_batches=10,   # Wait 10 seconds between batches (reduced from 30)
        max_batches=None,       # No limit on batches (process all)
        timeout_per_batch=1800  # 30 minutes timeout per batch
    )
    
    log_progress("Full city processing complete")


def fetch_theater_data():
    """Standalone function to fetch theater data with MongoDB integration."""
    logger.info("Starting theater data collection process")
    theater_data = TheaterData()
    theater_data.fetch_and_save_theaters([
        "Tampa, Florida", 
        "Orlando, Florida",
        "New York, NY",
        "Los Angeles, CA",
        "Chicago, IL"
    ])
    logger.info("Theater data collection complete")


def fetch_theaters_from_us_cities():
    """Fetch theaters for cities in the us_cities.json file."""
    logger.info("Starting theater data collection from us_cities.json")
    theater_data = TheaterData()
    
    # Import cities to MongoDB
    theater_data.import_cities_to_mongodb()
    
    # Process all cities sorted by population (not just top 10)
    cities = theater_data.get_cities_by_population()
    if cities:
        logger.info(f"Processing {len(cities)} cities by population order")
        processed_count = 0
        total_theaters = 0
        
        # Process cities in batches of 10 to avoid overwhelming
        batch_size = 10
        for i in range(0, len(cities), batch_size):
            batch = cities[i:i+batch_size]
            city_names = [f"{city['name']}, {city['state']}" for city in batch]
            
            logger.info(f"Processing batch {i//batch_size + 1}: cities {i+1}-{i+len(batch)} of {len(cities)}")
            
            # Fetch theaters for this batch
            theaters = theater_data.fetch_theaters_in_cities(city_names)
            
            # Save theaters to MongoDB
            for city_data, city_name in zip(batch, city_names):
                city_theaters = [t for t in theaters if t["source_city"] == city_name]
                if city_theaters:
                    saved = theater_data.save_theaters_to_mongodb(city_theaters, city_data.get("geoid"))
                    theater_data.mark_city_as_processed(city_data["geoid"], len(city_theaters))
                    logger.info(f"Saved {saved} theaters for {city_name}")
                    total_theaters += saved
                else:
                    theater_data.mark_city_as_processed(city_data["geoid"], 0)
                    logger.info(f"No theaters found for {city_name}")
                
                processed_count += 1
            
            # Add delay between batches
            if i + batch_size < len(cities):
                delay = random.uniform(5, 10)
                logger.info(f"Adding delay of {delay:.2f} seconds before next batch")
                time.sleep(delay)
                
        logger.info(f"Completed processing {processed_count} cities, found {total_theaters} theaters")
        
        # Export all theaters to JSON
        theater_data.export_all_theaters_to_json()
    else:
        logger.error("No cities found to process")
    
    logger.info("Theater data collection from us_cities.json complete")


def process_random_cities(batch_size=10):
    """Process a random batch of cities from the database."""
    logger.info(f"Starting theater data collection for {batch_size} random cities")
    theater_data = TheaterData()
    
    # Get total count of cities
    total_cities = theater_data.cities_collection.count_documents({
        "population": {"$exists": True, "$ne": None}
    })
    
    if total_cities == 0:
        logger.error("No cities found in database")
        return
    
    # Get random cities across different population ranges
    # We'll divide the population range into segments to ensure diversity
    random_cities = []
    
    try:
        # Get population range (min/max)
        max_pop = theater_data.cities_collection.find_one(
            {"population": {"$exists": True, "$ne": None}},
            sort=[("population", -1)]
        )
        min_pop = theater_data.cities_collection.find_one(
            {"population": {"$exists": True, "$ne": None}},
            sort=[("population", 1)]
        )
        
        if not max_pop or not min_pop:
            logger.error("Could not determine population range")
            return
            
        max_population = max_pop.get("population", 0)
        min_population = min_pop.get("population", 0)
        
        # Create population ranges to sample from
        segments = 5  # Number of population segments to create
        samples_per_segment = batch_size // segments
        extra_samples = batch_size % segments
        
        pop_range = max_population - min_population
        segment_size = pop_range / segments if pop_range > 0 else 1
        
        for i in range(segments):
            segment_samples = samples_per_segment + (1 if i < extra_samples else 0)
            if segment_samples <= 0:
                continue
                
            low = min_population + (i * segment_size)
            high = min_population + ((i + 1) * segment_size)
            
            # Get random cities from this population segment
            segment_cities = list(theater_data.cities_collection.aggregate([
                {"$match": {
                    "population": {"$gte": low, "$lt": high},
                    "processed": {"$ne": True}
                }},
                {"$sample": {"size": segment_samples}},
                {"$project": {"_id": 0}}
            ]))
            
            random_cities.extend(segment_cities)
        
        # If we don't have enough cities, get more randomly
        if len(random_cities) < batch_size:
            more_needed = batch_size - len(random_cities)
            more_cities = list(theater_data.cities_collection.aggregate([
                {"$match": {"population": {"$exists": True, "$ne": None}}},
                {"$sample": {"size": more_needed}},
                {"$project": {"_id": 0}}
            ]))
            random_cities.extend(more_cities)
        
        # Process the random cities
        if random_cities:
            logger.info(f"Processing {len(random_cities)} random cities")
            city_names = [f"{city['name']}, {city['state']}" for city in random_cities]
            
            for city, city_name in zip(random_cities, city_names):
                log_progress(f"Fetching theaters for random city: {city_name} (Population: {city.get('population', 'N/A')})", city_name)
                
                try:
                    # Fetch theaters
                    theaters = theater_data.fetch_theaters(city_name, city)
                    
                    # Save theaters
                    if theaters:
                        saved_count = theater_data.save_theaters_to_mongodb(theaters, city.get("geoid"))
                        log_progress(f"Found and saved {saved_count} theaters for {city_name}", city_name)
                        theater_data.mark_city_as_processed(city["geoid"], saved_count)
                    else:
                        log_progress(f"No theaters found for {city_name}", city_name)
                        theater_data.mark_city_as_processed(city["geoid"], 0)
                        
                except Exception as e:
                    log_progress(f"Error processing {city_name}: {str(e)}", city_name, "error")
                
                # Add delay between cities
                if city != random_cities[-1]:
                    delay = random.uniform(2, 5)
                    time.sleep(delay)
            
            # Export all theaters
            theater_data.export_all_theaters_to_json()
            logger.info("Random cities processing complete")
        else:
            logger.error("No random cities found to process")
    
    except Exception as e:
        logger.error(f"Error in process_random_cities: {str(e)}")


# Function to mask sensitive parts of the connection string for logging
def mask_connection_string(conn_string):
    """Mask username and password in connection string for safe logging."""
    if not conn_string:
        return "None"
    # Mask username and password in MongoDB URI
    masked = re.sub(r'(mongodb:\/\/)[^:]+:[^@]+(@)', r'\1****:****\2', conn_string)
    return masked


def test_mongodb_connection():
    """Test connection to MongoDB and print diagnostic information."""
    try:
        log_progress("Testing MongoDB connection...", level="info")
        log_progress(f"Connection string: {mask_connection_string(MONGODB_CONNECTION_STRING)}", level="info")
        log_progress(f"Database name: {MONGODB_DATABASE}", level="info")
        
        # Create a client with explicit timeout
        client = MongoClient(MONGODB_CONNECTION_STRING, serverSelectionTimeoutMS=10000)
        
        # Test connection with ping
        log_progress("Attempting to ping MongoDB server...", level="info")
        client.admin.command('ping')
        
        # If we get here, connection was successful
        log_progress("SUCCESS: MongoDB connection successful!", level="info")
        
        # Get server information
        server_info = client.server_info()
        log_progress(f"MongoDB server version: {server_info.get('version', 'unknown')}", level="info")
        
        # Test database access
        log_progress(f"Testing access to database: {MONGODB_DATABASE}", level="info")
        db = client[MONGODB_DATABASE]
        collections = db.list_collection_names()
        log_progress(f"Collections in database: {', '.join(collections) if collections else 'None'}", level="info")
        
        # Success
        log_progress("SUCCESS: MongoDB connection test completed successfully", level="info")
        return True
        
    except Exception as e:
        error_msg = str(e)
        log_progress(f"FAILED: MongoDB connection test failed: {error_msg}", level="error")
        
        # Try to extract the host from the connection string
        try:
            if '@' in MONGODB_CONNECTION_STRING:
                host = MONGODB_CONNECTION_STRING.split('@')[1].split('/')[0]
            else:
                host = MONGODB_CONNECTION_STRING.split('//')[1].split('/')[0]
                
            # Handle port if present
            if ':' in host:
                host, port_str = host.split(':')
                port = int(port_str)
            else:
                port = 27017  # Default MongoDB port
                
            log_progress(f"Extracted MongoDB host: {host}, port: {port}", level="info")
        except Exception:
            log_progress("Could not extract host from connection string", level="warning")
            host = "unknown"
            port = 27017
        
        # Add network diagnostics
        if "timed out" in error_msg or "No servers found" in error_msg:
            log_progress("Running network diagnostics...", level="info")
            
            # Try ping
            try:
                import subprocess
                log_progress(f"Pinging {host}...", level="info")
                ping_result = subprocess.run(['ping', '-n', '3', host], capture_output=True, text=True)
                if ping_result.returncode == 0:
                    log_progress(f"SUCCESS: Ping to {host} successful:", level="info")
                    # Extract RTT from ping output
                    lines = ping_result.stdout.split('\n')
                    for line in lines:
                        if "Average" in line:
                            log_progress(f"  {line.strip()}", level="info")
                            break
                else:
                    log_progress(f"FAILED: Ping to {host} failed:", level="error")
                    log_progress(ping_result.stdout, level="error")
            except Exception as ping_error:
                log_progress(f"Error during ping test: {str(ping_error)}", level="error")
            
            # Try socket connection
            try:
                import socket
                log_progress(f"Testing socket connection to {host}:{port}...", level="info")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                result = s.connect_ex((host, port))
                s.close()
                if result == 0:
                    log_progress(f"SUCCESS: Socket connection to {host}:{port} successful", level="info")
                    log_progress("Port is open but MongoDB server may have authentication issues", level="info")
                else:
                    log_progress(f"FAILED: Socket connection to {host}:{port} failed with code {result}", level="error")
                    log_progress("MongoDB port is not reachable. Possible reasons:", level="error")
                    log_progress("1. MongoDB server is not running", level="error")
                    log_progress("2. Firewall is blocking the connection", level="error")
                    log_progress("3. Server address is incorrect", level="error")
                    log_progress("4. Server is not configured to accept external connections", level="error")
            except Exception as socket_error:
                log_progress(f"Error during socket test: {str(socket_error)}", level="error")
        
        # Provide a summary of the issue
        log_progress("Summary of MongoDB connection issues:", level="error")
        if "timed out" in error_msg or "No servers found" in error_msg:
            log_progress("• Connection timeout - Server is unreachable", level="error")
            log_progress("  - Check if the MongoDB server is running", level="error")
            log_progress("  - Verify the MongoDB host address is correct", level="error")
            log_progress("  - Check if firewalls are blocking the connection", level="error")
            log_progress("  - Try using a different MongoDB instance or hosting provider", level="error")
        elif "Authentication failed" in error_msg:
            log_progress("• Authentication failed - Check your username and password", level="error")
        elif "not valid" in error_msg:
            log_progress("• Invalid connection string format", level="error")
        else:
            log_progress(f"• Unexpected error: {error_msg}", level="error")
            
        log_progress("Please fix the MongoDB connection settings in your .env file:", level="error")
        log_progress("MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/database", level="error")
        return False


def fetch_movie_data(count: int = 50, download_images: bool = True):
    """Fetch movie data from TMDB API and store in MongoDB."""
    log_progress("Starting movie data collection from TMDB API", level="info")
    
    # Initialize MovieData
    movie_data = MovieData()
    
    # Fetch and save movies
    stats = movie_data.fetch_and_save_movies(count=count, download_images=download_images)
    
    log_progress(f"Movie data collection complete. Fetched {stats['fetched']} movies, saved {stats['saved']} to MongoDB.", level="info")
    
    return stats


def main():
    """Main function to fetch movie data and store it in MongoDB."""
    # Check if API key is set
    if not TMDB_API_KEY:
        logger.error("TMDB API key not found. Please set it in the .env file.")
        return
        
    logger.info("Starting full data collection process (movies and theaters)")
    
    # Set verbose logging as default
    global LOGGING_LEVEL
    LOGGING_LEVEL = logging.DEBUG
    initialize_logging()
    
    try:
        # Test MongoDB connection
        log_progress("Testing MongoDB connection...", level="info")
        client = MongoClient(MONGODB_CONNECTION_STRING)
        client.admin.command('ping')
        db = client[MONGODB_DATABASE]
        
        # Create collections if they don't exist
        collections_to_check = [
            MONGODB_COLLECTION_MOVIES,
            MONGODB_COLLECTION_DIRECTORS,
            MONGODB_COLLECTION_ACTORS,
            MONGODB_COLLECTION_GENRES,
            MONGODB_COLLECTION_CITIES,
            MONGODB_COLLECTION_THEATERS,
            MONGODB_COLLECTION_PROGRESS
        ]
        
        for collection_name in collections_to_check:
            if collection_name not in db.list_collection_names():
                log_progress(f"Creating collection: {collection_name}", level="info")
                db.create_collection(collection_name)
            
        log_progress("MongoDB connection successful", level="info")
        
        # Step 1: Fetch movie data from TMDB API
        log_progress("STEP 1: FETCHING MOVIE DATA", level="info")
        movie_stats = fetch_movie_data(count=50, download_images=True)
        log_progress(f"Movie data collection complete. Fetched {movie_stats['fetched']} movies, saved {movie_stats['saved']} to MongoDB.", level="info")
        
        # Step 2: Import cities to MongoDB
        log_progress("STEP 2: IMPORTING CITIES DATA", level="info")
        theater_data = TheaterData()
        imported_count = theater_data.import_cities_to_mongodb()
        log_progress(f"Imported {imported_count} cities to MongoDB", level="info")
        
        # Step 3: Update coordinates for cities
        log_progress("STEP 3: UPDATING CITY COORDINATES", level="info")
        coordinate_stats = theater_data.update_cities_with_nominatim_coordinates(batch_size=20)
        log_progress(f"Updated coordinates for {coordinate_stats['cities_updated']} cities", level="info")
        
        # Step 4: Process all cities for theaters with specified batch size
        log_progress("STEP 4: PROCESSING ALL CITIES FOR THEATERS", level="info")
        theater_data.process_all_cities(batch_size=3, delay_between_batches=10, max_batches=None, timeout_per_batch=1800)
        
        # Output a summary
        log_progress("DATA COLLECTION COMPLETE", level="info")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch movie and theater data")
    parser.add_argument("--theaters-only", action="store_true", help="Fetch theater data only")
    parser.add_argument("--city-theaters", action="store_true", help="Process all cities for theaters, starting with highest population")
    parser.add_argument("--all-cities", action="store_true", help="Process all cities in batches")
    parser.add_argument("--random-cities", action="store_true", help="Process a random batch of cities across different population ranges")
    parser.add_argument("--batch-size", type=int, default=3, help="Number of cities to process in each batch (default: 3)")
    parser.add_argument("--test-mongodb", action="store_true", help="Test MongoDB connection")
    parser.add_argument("--update-coordinates", action="store_true", help="Update missing city coordinates using Nominatim")
    parser.add_argument("--fetch-movies", action="store_true", help="Fetch movie data from TMDB API")
    parser.add_argument("--movie-count", type=int, default=50, help="Number of movies to fetch (default: 50)")
    parser.add_argument("--no-images", action="store_true", help="Skip downloading movie images")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Default to verbose logging
    LOGGING_LEVEL = logging.DEBUG if args.verbose else logging.INFO
    initialize_logging()
    
    # Check if any arguments were provided
    any_args_provided = any([
        args.theaters_only, args.city_theaters, args.all_cities, args.random_cities,
        args.test_mongodb, args.update_coordinates, args.fetch_movies
    ])
    
    if args.test_mongodb:
        test_mongodb_connection()
    elif args.theaters_only:
        fetch_theater_data()
    elif args.city_theaters:
        fetch_theaters_from_us_cities()
    elif args.all_cities:
        process_all_cities_with_theaters(args.batch_size)
    elif args.random_cities:
        process_random_cities(args.batch_size)
    elif args.update_coordinates:
        # Initialize theater data
        theater_data = TheaterData()
        # Update coordinates for cities that need them
        stats = theater_data.update_cities_with_nominatim_coordinates()
        print(f"Coordinate update complete. Results: {stats}")
    elif args.fetch_movies:
        # Fetch movie data from TMDB API
        download_images = not args.no_images
        stats = fetch_movie_data(count=args.movie_count, download_images=download_images)
        print(f"Movie data collection complete. Results: {stats}")
    else:
        # No arguments provided, run the complete process using main()
        main()