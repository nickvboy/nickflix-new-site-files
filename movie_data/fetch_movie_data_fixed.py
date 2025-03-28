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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

import requests
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.operations import UpdateOne
from tqdm import tqdm
import argparse

# Import configuration module
from config import get_config, reload_config, Config

# Load environment variables from project root .env file
load_dotenv()  # This will look for .env in the current working directory

# Get configuration
config = get_config()

# Initialize logging
initialize_logging = config.initialize_logging
initialize_logging()

# Logger for this module
logger = logging.getLogger("MovieFetcher")
logger.info(f"Logging to {config.logging.log_file}")

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

# Output file paths from configuration
OUTPUT_JSON_FILE = config.output.get_file_path("movies")
THEATERS_JSON_FILE = config.output.get_file_path("theaters")
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
    if level in ["info", "error", "warning"] and config.logging.log_to_console:
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
        self.config = get_config().movie
        
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
            "append_to_response": "credits,videos,keywords,recommendations",
            "language": self.config.language
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
    
    def get_popular_movies(self, count: int = None, min_vote_count: int = None, min_vote_average: float = None) -> List[Dict]:
        """
        Retrieve popular movies from TMDB API.
        
        Args:
            count: Number of movies to retrieve
            min_vote_count: Minimum number of votes a movie should have
            min_vote_average: Minimum average rating a movie should have
            
        Returns:
            List of movie dictionaries
        """
        # Use config values if not provided
        if count is None:
            count = self.config.count
        if min_vote_count is None:
            min_vote_count = self.config.min_vote_count
        if min_vote_average is None:
            min_vote_average = self.config.min_vote_average
            
        log_progress(f"Fetching {count} popular movies from TMDB API", level="info")
        log_progress(f"Filtering criteria: min_vote_count={min_vote_count}, min_vote_average={min_vote_average}", level="info")
        
        url = f"{self.tmdb_base_url}/discover/movie"
        movies = []
        page = 1
        max_pages = 50  # Safety limit to prevent infinite loops
        
        # Use tqdm to display progress
        progress = tqdm(total=count, desc="Fetching movies")
        
        while len(movies) < count and page <= max_pages:
            params = {
                "api_key": self.api_key,
                "sort_by": self.config.sort_by,
                "vote_count.gte": min_vote_count,
                "vote_average.gte": min_vote_average,
                "page": page,
                "include_adult": False,
                "language": self.config.language
            }
            
            # Add year range filters if configured
            if self.config.release_year_start:
                params["primary_release_date.gte"] = f"{self.config.release_year_start}-01-01"
            if self.config.release_year_end:
                params["primary_release_date.lte"] = f"{self.config.release_year_end}-12-31"
                
            # Add genre filters if configured
            if self.config.genres_include:
                params["with_genres"] = ",".join(str(g) for g in self.config.genres_include)
            if self.config.genres_exclude:
                params["without_genres"] = ",".join(str(g) for g in self.config.genres_exclude)
            
            try:
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if not results:
                        log_progress(f"No more results found on page {page}", level="info")
                        break
                        
                    log_progress(f"Processing {len(results)} movies from page {page}", level="debug")
                    
                    for movie_summary in results:
                        if len(movies) < count:
                            # Get full movie details
                            movie_id = movie_summary.get("id")
                            movie_details = self.get_movie_details(movie_id)
                            
                            if movie_details:
                                movies.append(movie_details)
                                progress.update(1)
                                log_progress(f"Added movie: {movie_details.get('title')}", level="debug")
                            else:
                                log_progress(f"Failed to get details for movie ID {movie_id}", level="warning")
                        else:
                            break
                            
                    # If we've reached the end of available pages, break
                    if page >= data.get("total_pages", 1):
                        log_progress(f"Reached the last page ({page}) of results", level="info")
                        break
                        
                    page += 1
                else:
                    log_progress(f"API request failed with status code: {response.status_code}", level="warning")
                    log_progress(f"Response: {response.text[:200]}", level="debug")
                    break
                    
            except Exception as e:
                log_progress(f"Error fetching popular movies: {str(e)}", level="error")
                time.sleep(2)  # Wait a bit longer before retrying
                continue
                
            # Add a delay to avoid rate limiting
            time.sleep(0.8)
        
        progress.close()
        
        if len(movies) < count:
            log_progress(f"Could only retrieve {len(movies)} out of {count} requested movies", level="warning")
        else:
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
        Only fetches additional movies if needed to reach the target count.
        
        Args:
            count: Number of movies to fetch
            download_images: Whether to download poster and backdrop images
            
        Returns:
            Dictionary with statistics about the process
        """
        log_progress(f"Starting movie data collection. Target count: {count} movies...", level="info")
        
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
            # Check current movie count in database
            current_count = self.movies_collection.count_documents({})
            log_progress(f"Current movie count in database: {current_count}", level="info")
            
            # If we already have enough movies, skip fetching
            if current_count >= count:
                log_progress(f"Database already has {current_count} movies, which meets or exceeds target of {count}. Skipping fetch.", level="info")
                stats["fetched"] = 0
                stats["saved"] = current_count
                stats["end_time"] = datetime.now().isoformat()
                return stats
            
            # Calculate how many more movies we need
            movies_needed = count - current_count
            log_progress(f"Need to fetch {movies_needed} more movies to reach target", level="info")
            
            # Get popular movies
            movies = self.get_popular_movies(count=movies_needed)
            stats["fetched"] = len(movies)
            
            if not movies:
                log_progress("No new movies found to fetch", level="warning")
                stats["end_time"] = datetime.now().isoformat()
                return stats
            
            log_progress(f"Processing and saving {len(movies)} new movies to MongoDB...", level="info")
            
            # Process each movie
            for movie in tqdm(movies, desc="Saving movies to MongoDB"):
                try:
                    # Check if movie already exists
                    existing_movie = self.movies_collection.find_one({"id": movie.get("id")})
                    if existing_movie:
                        log_progress(f"Movie {movie.get('title')} already exists in database, skipping", level="debug")
                        continue
                    
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
            
            # Get final count
            final_count = self.movies_collection.count_documents({})
            log_progress(f"Movie data collection complete. Total movies in database: {final_count}", level="info")
            
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
        # Get configuration
        self.config = get_config()
        
        # Target theater chains from configuration
        self.target_theaters = self.config.theater.theater_brands
        
        # MongoDB connection
        try:
            # Connect to MongoDB
            log_progress("Connecting to MongoDB...", level="info")
            self.client = MongoClient(MONGODB_CONNECTION_STRING)
            # Test connection
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
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")
    
    def process_all_cities(self, batch_size: int = None, delay_between_batches: int = None, max_batches: int = None, timeout_per_batch: int = None) -> Dict:
        """
        Process all cities in the database in batches.
        
        Args:
            batch_size: Number of cities to process in each batch
            delay_between_batches: Delay in seconds between batches
            max_batches: Maximum number of batches to process
            timeout_per_batch: Maximum time in seconds to process each batch
            
        Returns:
            Dictionary with processing statistics
        """
        # Use config values if not provided
        if batch_size is None:
            batch_size = self.config.theater.batch_size
        if delay_between_batches is None:
            delay_between_batches = self.config.theater.delay_between_batches
        if max_batches is None:
            max_batches = self.config.theater.max_batches
        if timeout_per_batch is None:
            timeout_per_batch = self.config.theater.timeout_per_batch
            
        # Initialize statistics
        stats = {
            "total_cities": 0,
            "processed_cities": 0,
            "theaters_found": 0,
            "errors": 0,
            "batches_completed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Get total number of unprocessed cities
            stats["total_cities"] = self.cities_collection.count_documents({
                "processed": {"$ne": True},
                "population": {"$exists": True, "$ne": None}
            })
            
            if stats["total_cities"] == 0:
                log_progress("No unprocessed cities found", level="info")
                return stats
            
            log_progress(f"Found {stats['total_cities']} unprocessed cities to process", level="info")
            
            # Process cities in batches
            batch_num = 1
            while True:
                # Check if we've reached max batches
                if max_batches and batch_num > max_batches:
                    log_progress(f"Reached maximum number of batches ({max_batches})", level="info")
                    break
                
                # Get next batch of cities
                cities = list(self.cities_collection.find(
                    {"processed": {"$ne": True}, "population": {"$exists": True, "$ne": None}},
                    sort=[("population", -1)],  # Process largest cities first
                    limit=batch_size
                ))
                
                if not cities:
                    log_progress("No more cities to process", level="info")
                    break
                
                log_progress(f"Processing batch {batch_num} with {len(cities)} cities", level="info")
                
                # Process this batch
                batch_stats = self.process_batch_of_cities(cities)
                
                # Update overall statistics
                stats["processed_cities"] += batch_stats["processed_cities"]
                stats["theaters_found"] += batch_stats["theaters_found"]
                stats["errors"] += batch_stats["errors"]
                stats["batches_completed"] += 1
                
                # Log progress
                progress = (stats["processed_cities"] / stats["total_cities"]) * 100
                log_progress(f"Progress: {progress:.1f}% ({stats['processed_cities']}/{stats['total_cities']} cities)", level="info")
                
                # Add delay between batches
                if delay_between_batches > 0:
                    log_progress(f"Waiting {delay_between_batches} seconds before next batch", level="info")
                    time.sleep(delay_between_batches)
                
                batch_num += 1
            
            stats["end_time"] = datetime.now().isoformat()
            log_progress("City processing complete", level="info")
            return stats
            
        except Exception as e:
            log_progress(f"Error processing cities: {str(e)}", level="error")
            stats["errors"] += 1
            stats["end_time"] = datetime.now().isoformat()
            return stats

    def generate_theater_id(self) -> str:
        """
        Generate a unique 9-digit theater ID.
        
        Returns:
            str: A 9-digit theater ID
        """
        while True:
            # Generate a random 9-digit number
            theater_id = str(random.randint(100000000, 999999999))
            
            # Check if this ID already exists
            if not self.theaters_collection.find_one({"theater_id": theater_id}):
                return theater_id
    
    def get_city_coordinates(self, city_name: str, use_fallback: bool = True) -> Optional[Dict]:
        """
        Get city coordinates from Nominatim API.
        
        Args:
            city_name: Name of the city to get coordinates for
            use_fallback: Whether to try alternative city name formats if first attempt fails
            
        Returns:
            Dictionary containing city coordinates and bounding box, or None if not found
        """
        # Clean city name
        city_name = city_name.replace(" city", "").replace(" town", "").replace(" village", "")
        
        # Try different query formats
        query_formats = [
            city_name,  # Original name
            f"{city_name}, USA",  # Add country
            city_name.split(",")[0].strip() if "," in city_name else city_name,  # Remove state if present
            f"{city_name.split(',')[0].strip()}, USA" if "," in city_name else f"{city_name}, USA"  # Remove state and add country
        ]
        
        for query in query_formats:
            try:
                # Add delay to respect Nominatim's rate limits
                time.sleep(1)
                
                # Make request to Nominatim
                response = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": query,
                "format": "json",
                        "limit": 1,
                        "addressdetails": 1,
                        "extratags": 1
                    },
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        result = results[0]
                        return {
                            "lat": float(result["lat"]),
                            "lon": float(result["lon"]),
                            "boundingbox": [float(x) for x in result["boundingbox"]],
                            "display_name": result.get("display_name", ""),
                            "osm_type": result.get("osm_type", ""),
                            "osm_id": result.get("osm_id", "")
                        }
                        
            except Exception as e:
                log_progress(f"Error getting coordinates for {query}: {str(e)}", level="warning")
                continue
                
        if use_fallback:
            # Try one last time with a simplified query
            try:
                time.sleep(1)
                simplified_name = city_name.split(",")[0].strip()
                response = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": simplified_name,
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1,
                        "extratags": 1
                    },
                headers=self.headers,
                timeout=10
            )
            
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        result = results[0]
                        return {
                            "lat": float(result["lat"]),
                            "lon": float(result["lon"]),
                            "boundingbox": [float(x) for x in result["boundingbox"]],
                            "display_name": result.get("display_name", ""),
                            "osm_type": result.get("osm_type", ""),
                            "osm_id": result.get("osm_id", "")
                        }
                        
            except Exception as e:
                log_progress(f"Error in fallback coordinate lookup for {simplified_name}: {str(e)}", level="warning")
        
        return None
    
    def fetch_theaters_from_overpass(self, city_data: Dict[str, Any], brand: str) -> List[Dict[str, Any]]:
        """
        Generate synthetic theater data for a city and brand.
        
        Args:
            city_data: Dictionary containing city information
            brand: Theater brand to generate data for
            
        Returns:
            List of theater dictionaries
        """
        try:
            # Get city size based on population
            population = city_data.get('population', 0)
            thresholds = self.config.theater.generation.population_thresholds
            
            if population >= thresholds['major_metro']:
                city_size = 'major_metro'
            elif population >= thresholds['large_city']:
                city_size = 'large_city'
            elif population >= thresholds['medium_city']:
                city_size = 'medium_city'
            else:
                city_size = 'small_city'
            
            # Get theater count range for this brand and city size
            count_range = self.config.theater.generation.theater_counts[city_size].get(brand, [0, 0])
            num_theaters = random.randint(count_range[0], count_range[1])
            
            if num_theaters == 0:
                return []
            
            theaters = []
            city_name = city_data['name']
            state = city_data.get('state', '')
            
            # Get naming pattern for this brand and city size
            naming_pattern = self.config.theater.generation.naming_patterns[brand][city_size]
            
            # Get feature distribution for this city size
            feature_distribution = self.config.theater.generation.feature_distribution[city_size]
            
            for i in range(num_theaters):
                # Generate theater name based on pattern
                theater_name = naming_pattern.format(
                    brand=brand.upper(),
                    city=city_name,
                    number=str(random.randint(8, 24)) if '{number}' in naming_pattern else '',
                    suffix=random.choice(self.config.theater.generation.suffixes.get(brand, ['']))
                ).strip()
                
                # Generate address
                street_number = random.randint(100, 9999)
                street_name = random.choice(self.config.theater.generation.street_names)
                address = f"{street_number} {street_name}"
                
                # Generate random coordinates (US coordinates)
                lat = random.uniform(24.396308, 49.384358)  # US latitude range
                lon = random.uniform(-125.000000, -66.934570)  # US longitude range
                
                # Generate features based on distribution rules
                features = ["2D", "3D"]  # All theaters have 2D and 3D
                
                # Add 4DX based on distribution
                if random.random() * 100 < feature_distribution["4DX"]:
                    features.append("4DX")
                
                # Add IMAX based on distribution
                if random.random() * 100 < feature_distribution["IMAX"]:
                    features.append("IMAX")
                
                # Generate random phone number
                area_code = random.randint(200, 999)
                prefix = random.randint(200, 999)
                line_number = random.randint(1000, 9999)
                phone = f"({area_code}) {prefix}-{line_number}"
                
                # Generate website
                website = f"https://www.{brand.lower()}.com/theaters/{city_name.lower().replace(' ', '-')}-{i+1}"
                
                theater = {
                    'unique_id': f"{brand}_{city_name}_{i+1}",
                    'name': theater_name,
                    'brand': brand,
                    'source_city': city_name,
                    'city_geoid': city_data.get('geoid', ''),
                    'location': {
                        'type': 'Point',
                        'coordinates': [lon, lat]
                    },
                    'address': {
                        'street': address,
                        'city': city_name,
                        'state': state,
                        'zip': f"{random.randint(10000, 99999)}"
                    },
                    'contact': {
                        'phone': phone,
                        'website': website,
                        'opening_hours': {
                            'monday': "10:00-23:00",
                            'tuesday': "10:00-23:00",
                            'wednesday': "10:00-23:00",
                            'thursday': "10:00-23:00",
                            'friday': "10:00-00:00",
                            'saturday': "10:00-00:00",
                            'sunday': "10:00-23:00"
                        }
                    },
                    'features': features,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                theaters.append(theater)
            
            return theaters
            
        except Exception as e:
            logger.error(f"Error generating theater data: {str(e)}")
            return []
    
    def fetch_theaters(self, city_name: str = "Tampa, Florida", city_data: Dict = None) -> List[Dict[str, Any]]:
        """
        Generate theater data for a city.
        
        Args:
            city_name: Name of the city to generate theaters for
            city_data: Optional city data dictionary with additional info
            
        Returns:
            List of theater dictionaries
        """
        if not city_data:
            # Try to get city data from MongoDB
            city_data = self.cities_collection.find_one({"name": city_name.split(",")[0].strip()})
            if not city_data:
                log_progress(f"City data not found for {city_name}", city_name, "error")
                return []
        
        try:
            theaters = []
            city_name = city_data['name']
            state = city_data.get('state', '')
            
            # Generate theaters for each brand
            for brand in self.target_theaters:
                brand_theaters = self.fetch_theaters_from_overpass(city_data, brand)
                theaters.extend(brand_theaters)
            
            # Add delay between cities as configured
            delay = random.uniform(
                self.config.theater.delay_between_cities["min"],
                self.config.theater.delay_between_cities["max"]
            )
            log_progress(f"Adding delay of {delay:.2f} seconds before next city", level="debug")
            time.sleep(delay)
            
            return theaters
            
        except Exception as e:
            log_progress(f"Error generating theaters for {city_name}: {str(e)}", city_name, "error")
            return []
    
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
        operations = []
        mongodb_batch_size = self.config.processing.mongodb_batch_size
        
        for geoid, city_data in tqdm(cities_data.items()):
            # Add geoid to the data
            city_data["geoid"] = geoid
            
            # Set processed flag to False
            city_data["processed"] = False
            city_data["theaters_found"] = 0
            city_data["last_updated"] = datetime.now().isoformat()
            
            try:
                # Add to operations list
                operations.append(
                    UpdateOne(
                    {"geoid": geoid},
                    {"$set": city_data},
                    upsert=True
                    )
                )
                imported_count += 1
                
                # Execute in batches to avoid memory issues with large datasets
                if len(operations) >= mongodb_batch_size:
                    self.cities_collection.bulk_write(operations)
                    operations = []
                    
            except Exception as e:
                log_progress(f"Error importing city {geoid}: {str(e)}", level="error")
                if self.config.processing.error_handling == "abort":
                    raise
        
        # Execute any remaining operations
        if operations:
            try:
                self.cities_collection.bulk_write(operations)
            except Exception as e:
                log_progress(f"Error in final bulk city operation: {str(e)}", level="error")
                if self.config.processing.error_handling == "abort":
                    raise
                
        log_progress(f"Successfully imported {imported_count} cities to MongoDB")
        return imported_count
    
    def save_theaters_to_mongodb(self, theaters: List[Dict[str, Any]], city_geoid: str = None) -> int:
        """
        Save theaters to MongoDB with unique 9-digit IDs.
        
        Args:
            theaters: List of theater dictionaries
            city_geoid: Optional city GEOID
            
        Returns:
            int: Number of theaters saved
        """
        if not theaters:
            return 0
            
        # Generate unique theater IDs
        existing_ids = set(self.theaters_collection.distinct("theater_id"))
        for theater in theaters:
            while True:
                theater_id = self.generate_theater_id()
                if theater_id not in existing_ids:
                    existing_ids.add(theater_id)
                    theater["theater_id"] = theater_id
                    break
        
        # Add city_geoid if provided
        if city_geoid:
            for theater in theaters:
                theater["city_geoid"] = city_geoid
        
        # Save to MongoDB
        result = self.theaters_collection.insert_many(theaters)
        return len(result.inserted_ids)
    
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
    
    def save_theaters(self, theaters: List[Dict[str, Any]], output_file: str = None) -> None:
        """Save theater data to a JSON file for backup or offline use."""
        # Use config if output_file not provided
        if output_file is None:
            output_file = self.config.output.get_file_path("theaters")
            
        log_progress(f"Saving {len(theaters)} theaters to {output_file}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Use indent if pretty JSON is enabled
            indent = 2 if self.config.output.pretty_json else None
            json.dump(theaters, f, ensure_ascii=False, indent=indent)

    def export_all_theaters_to_json(self, output_file=None) -> bool:
        """
        Export all theaters from MongoDB to JSON file and generate brand summary.
        
        Args:
            output_file: Optional custom output file path
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            if output_file is None:
                output_file = config.output.get_file_path("theaters")
            
            # Get all theaters from MongoDB
            theaters = list(self.theaters_collection.find({}, {"_id": 0}))
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Save to JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                if config.output.pretty_json:
                    json.dump(theaters, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(theaters, f, ensure_ascii=False)
            
            # Generate brand summary
            brands = {}
            for theater in theaters:
                brand = theater.get("brand", "other")
                brands[brand] = brands.get(brand, 0) + 1
            
            # Log summary
            log_progress("Theater brand summary:")
            for brand, count in brands.items():
                log_progress(f"  {brand}: {count} theaters")
            
            log_progress(f"Successfully exported {len(theaters)} theaters to {output_file}", level="info")
            return True
            
        except Exception as e:
            log_progress(f"Error exporting theaters to JSON: {str(e)}", level="error")
            return False

    def process_batch_of_cities(self, batch_size_or_cities: Union[int, List[Dict]], stats: Dict = None) -> Dict:
        """
        Process a batch of cities to find theaters.
        
        Args:
            batch_size_or_cities: Either the number of cities to process or a list of city documents
            stats: Optional stats dictionary to update
            
        Returns:
            Dictionary with processing statistics
        """
        if stats is None:
            stats = {
                "processed_cities": 0,
                "theaters_found": 0,
                "errors": 0,
                "status": "success"
            }
        
        try:
            # Get cities to process
            if isinstance(batch_size_or_cities, int):
                # Get next batch of unprocessed cities
                cities = list(self.cities_collection.find(
                    {"processed": {"$ne": True}},
                    limit=batch_size_or_cities
                ))
            else:
                cities = batch_size_or_cities
            
            if not cities:
                log_progress("No cities to process in this batch", level="info")
                return stats
            
            log_progress(f"Processing batch of {len(cities)} cities", level="info")
            
            # Process each city
            for city in cities:
                try:
                    city_name = f"{city['name']}, {city.get('state', '')}"
                    population = city.get('population', 'N/A')
                    log_progress(f"Processing city: {city_name} (Population: {population:,})", level="info")
                    
                    theaters = self.fetch_theaters(city_name, city)
                    
                    if theaters:
                        # Save theaters to MongoDB
                        saved_count = self.save_theaters_to_mongodb(theaters, city.get('geoid'))
                        stats["theaters_found"] += saved_count
                        
                        # Mark city as processed
                        self.mark_city_as_processed(city.get('geoid'), saved_count)
                    else:
                        # Mark city as processed with 0 theaters
                        self.mark_city_as_processed(city.get('geoid'), 0)
                    
                    stats["processed_cities"] += 1
                    
                    # Add delay between cities
                    delay = random.uniform(
                        self.config.theater.delay_between_cities["min"],
                        self.config.theater.delay_between_cities["max"]
                    )
                    time.sleep(delay)
                    
                except Exception as e:
                    log_progress(f"Error processing city {city_name}: {str(e)}", level="error")
                    stats["errors"] += 1
                    if self.config.processing.error_handling == "abort":
                        stats["status"] = "aborted"
                        return stats
            
            return stats
            
        except Exception as e:
            log_progress(f"Error processing batch: {str(e)}", level="error")
            stats["errors"] += 1
            stats["status"] = "error"
            return stats


def process_all_cities_with_theaters(batch_size=None):
    """Process all cities in the US cities database and find theaters in each."""
    log_progress("Starting full processing of all US cities for theaters")
    
    # Get configuration
    config = get_config()
    
    # Use config if batch_size not provided
    if batch_size is None:
        batch_size = config.theater.batch_size
    
    # Initialize theater data with MongoDB - will raise an error if connection fails
    theater_data = TheaterData()
    
    # Import cities to MongoDB
    theater_data.import_cities_to_mongodb()
    
    # Process all cities, starting with largest population
    theater_data.process_all_cities(
        batch_size=batch_size,
        delay_between_batches=config.theater.delay_between_batches,
        max_batches=config.theater.max_batches,
        timeout_per_batch=config.theater.timeout_per_batch
    )
    
    log_progress("Full city processing complete")


def fetch_theater_data(cities=None):
    """
    Standalone function to fetch theater data with MongoDB integration.
    
    Args:
        cities: Optional list of city names to fetch theaters for.
               If None, uses a set of default major cities.
    """
    logger.info("Starting theater data collection process")
    
    # Get configuration
    config = get_config()
    
    theater_data = TheaterData()
    
    # Use provided cities or default to these major cities
    if cities is None:
        cities = [
        "Tampa, Florida", 
        "Orlando, Florida",
        "New York, NY",
        "Los Angeles, CA",
        "Chicago, IL"
        ]
    
    theater_data.fetch_and_save_theaters(cities)
    logger.info("Theater data collection complete")


def fetch_theaters_from_us_cities():
    """Fetch theaters for cities in the us_cities.json file."""
    logger.info("Starting theater data collection from us_cities.json")
    
    # Get configuration
    config = get_config()
    
    theater_data = TheaterData()
    
    # Import cities to MongoDB
    theater_data.import_cities_to_mongodb()
    
    # Get cities by selection strategy
    city_selection = config.theater.city_selection
    if city_selection == "population":
        cities = theater_data.get_cities_by_population()
    elif city_selection == "random":
        # Use process_random_cities instead
        process_random_cities()
        return
    else:
        # Default to population order
        cities = theater_data.get_cities_by_population()
    
    if cities:
        logger.info(f"Processing {len(cities)} cities using {city_selection} selection strategy")
        processed_count = 0
        total_theaters = 0
        
        # Process cities in batches
        batch_size = config.theater.batch_size
        for i in range(0, len(cities), batch_size):
            batch = cities[i:i+batch_size]
            city_names = [f"{city['name']}, {city['state']}" for city in batch]
            
            logger.info(f"Processing batch {i//batch_size + 1}: cities {i+1}-{i+len(batch)} of {len(cities)}")
            
            # Fetch theaters for this batch
            theaters = theater_data.fetch_theaters(city_names)
            
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
                delay = config.theater.delay_between_batches
                logger.info(f"Adding delay of {delay:.2f} seconds before next batch")
                time.sleep(delay)
                
        logger.info(f"Completed processing {processed_count} cities, found {total_theaters} theaters")
        
        # Export all theaters to JSON
        theater_data.export_all_theaters_to_json()
    else:
        logger.error("No cities found to process")
    
    logger.info("Theater data collection from us_cities.json complete")


def process_random_cities(batch_size=None):
    """Process all cities in a randomized order, working through the entire dataset in batches."""
    logger.info("Starting random city processing for all cities in the database")
    
    # Get configuration
    config = get_config()
    
    # Use config if batch_size not provided
    if batch_size is None:
        batch_size = config.theater.batch_size
    
    theater_data = TheaterData()
    
    # Import cities to MongoDB
    theater_data.import_cities_to_mongodb()
    
    # Count total unprocessed cities
    total_cities = theater_data.cities_collection.count_documents({
        "processed": {"$ne": True},
        "population": {"$exists": True, "$ne": None}
    })
    
    # Check if we should limit the number of cities to process
    max_cities = config.theater.max_cities
    if max_cities is not None and max_cities > 0:
        cities_to_process = min(total_cities, max_cities)
        logger.info(f"Found {total_cities} unprocessed cities, but will only process {cities_to_process} as configured")
    else:
        cities_to_process = total_cities
        logger.info(f"Found {total_cities} unprocessed cities to process in random order")
    
    if cities_to_process == 0:
        logger.info("No unprocessed cities found, nothing to do")
        return
            
    # Calculate number of batches needed
    total_batches = (cities_to_process + batch_size - 1) // batch_size
    
    # Process cities in random batches
    cities_processed = 0
    theaters_found = 0
    
    for batch_num in range(1, total_batches + 1):
        # Check if we've reached the max cities limit
        if max_cities is not None and cities_processed >= max_cities:
            logger.info(f"Reached max cities limit of {max_cities}, stopping")
            break
            
        # Calculate how many cities to get for this batch
        if max_cities is not None:
            remaining = max_cities - cities_processed
            batch_size_for_this_batch = min(batch_size, remaining)
        else:
            batch_size_for_this_batch = batch_size
            
        # Create a pipeline to get a random batch of unprocessed cities
        pipeline = [
            {"$match": {"processed": {"$ne": True}, "population": {"$exists": True, "$ne": None}}},
            {"$sample": {"size": batch_size_for_this_batch}}
        ]
        
        # Get a random batch
        city_batch = list(theater_data.cities_collection.aggregate(pipeline))
        
        if not city_batch:
            logger.info("No more cities to process, finished early")
            break
            
        logger.info(f"Processing batch {batch_num}/{total_batches}: {len(city_batch)} random cities")
        
        # Process this batch
        batch_stats = theater_data.process_batch_of_cities(city_batch, delay_between_cities=config.theater.delay_between_cities)
        
        # Update counters
        cities_processed += batch_stats["processed_cities"]
        theaters_found += batch_stats["theaters_found"]
        
        logger.info(f"Batch {batch_num} complete: processed {batch_stats['processed_cities']} cities, found {batch_stats['theaters_found']} theaters")
        logger.info(f"Progress: {cities_processed}/{cities_to_process} cities processed ({(cities_processed/cities_to_process)*100:.1f}%)")
        
        # Add delay between batches
        if batch_num < total_batches:
            delay = config.theater.delay_between_batches
            if delay > 0:
                logger.info(f"Pausing for {delay} seconds before next batch")
                time.sleep(delay)
            
    # Export theaters to JSON
            theater_data.export_all_theaters_to_json()
    
    logger.info(f"Random city processing complete. Processed {cities_processed} cities, found {theaters_found} theaters.")


def fetch_movie_data(count: int = None, download_images: bool = None):
    """Fetch movie data from TMDB API and store in MongoDB."""
    # Get configuration
    config = get_config()
    
    # Use config if parameters not provided
    if count is None:
        count = config.movie.count
        
    if download_images is None:
        download_images = config.movie.download_images
    
    log_progress("Starting movie data collection from TMDB API", level="info")
    
    # Initialize MovieData
    movie_data = MovieData()
    
    # Fetch and save movies
    stats = movie_data.fetch_and_save_movies(count=count, download_images=download_images)
    
    log_progress(f"Movie data collection complete. Fetched {stats['fetched']} movies, saved {stats['saved']} to MongoDB.", level="info")
    
    return stats


def export_collection_to_json(collection: Collection, output_file: str) -> None:
    """
    Export a MongoDB collection to a JSON file.
    
    Args:
        collection: MongoDB collection to export
        output_file: Path to output JSON file
    """
    try:
        # Get all documents from collection
        documents = list(collection.find({}, {"_id": 0}))
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
            
        log_progress(f"Exported {len(documents)} documents to {output_file}", level="info")
    except Exception as e:
        log_progress(f"Error exporting collection to {output_file}: {str(e)}", level="error")


class DataExporter:
    """Class for exporting data from MongoDB collections to JSON files."""
    
    def __init__(self, config: Config):
        """Initialize the DataExporter with configuration."""
        self.config = config
        try:
            # Connect to MongoDB
            log_progress("Connecting to MongoDB for data export...", level="info")
            self.client = MongoClient(MONGODB_CONNECTION_STRING)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DATABASE]
            
            # Initialize collections
            self.movies_collection = self.db[MONGODB_COLLECTION_MOVIES]
            self.theaters_collection = self.db[MONGODB_COLLECTION_THEATERS]
            self.showtimes_collection = self.db[self.config.showtime_generation.collections["showtimes"]]
            
            log_progress("MongoDB connection successful for data export", level="info")
        except Exception as e:
            error_msg = str(e)
            log_progress(f"CRITICAL ERROR: Failed to connect to MongoDB for export: {error_msg}", level="error")
            log_progress("Check your MongoDB connection settings:", level="error")
            log_progress(f"Connection string: {mask_connection_string(MONGODB_CONNECTION_STRING)}", level="error")
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")

    def _write_documents_to_file(self, documents: List[Dict], file_type: str) -> bool:
        """Write documents to a JSON file."""
        try:
            output_path = self.config.output.get_file_path(file_type)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if self.config.output.pretty_json:
                    json.dump(documents, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(documents, f, ensure_ascii=False)
            return True
        except Exception as e:
            log_progress(f"Failed to write {file_type} to file: {e}", level="error")
            return False

    def export_collection(self, collection: Collection, file_type: str) -> bool:
        """Export a MongoDB collection to JSON file."""
        try:
            documents = list(collection.find({}, {'_id': 0}))
            if not documents:
                log_progress(f"No documents found in {collection.name} collection", level="warning")
                return False
            
            success = self._write_documents_to_file(documents, file_type)
            if success:
                log_progress(f"Successfully exported {len(documents)} {collection.name} to {self.config.output.get_file_path(file_type)}", level="info")
            return success
        except Exception as e:
            log_progress(f"Failed to export {collection.name}: {e}", level="error")
            return False

    def export_movies(self) -> bool:
        """Export movies collection to JSON."""
        return self.export_collection(self.movies_collection, "movies")

    def export_theaters(self) -> bool:
        """Export theaters collection to JSON."""
        return self.export_collection(self.theaters_collection, "theaters")

    def export_showtimes(self) -> bool:
        """Export showtimes collection to JSON."""
        return self.export_collection(self.showtimes_collection, "showtimes")

    def export_all_data(self) -> bool:
        """Export all collections to JSON files."""
        try:
            log_progress("Starting export of all data collections...", level="info")
            
            movies_success = self.export_movies()
            theaters_success = self.export_theaters()
            showtimes_success = self.export_showtimes()
            
            all_success = movies_success and theaters_success and showtimes_success
            if all_success:
                log_progress("Successfully exported all collections", level="info")
            else:
                log_progress("Some collections failed to export", level="warning")
            return all_success
        except Exception as e:
            log_progress(f"Failed to export all data: {e}", level="error")
            return False


class ShowtimeGenerator:
    """Class for generating synthetic showtime data."""
    
    def __init__(self):
        """Initialize the ShowtimeGenerator with configuration."""
        self.config = get_config()
        try:
            # Connect to MongoDB
            log_progress("Connecting to MongoDB for showtime generation...", level="info")
            self.client = MongoClient(MONGODB_CONNECTION_STRING)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[MONGODB_DATABASE]
            
            # Initialize collections
            self.movies_collection = self.db[MONGODB_COLLECTION_MOVIES]
            self.theaters_collection = self.db[MONGODB_COLLECTION_THEATERS]
            self.showtimes_collection = self.db[self.config.showtime_generation.collections["showtimes"]]
            
            log_progress("MongoDB connection successful for showtime generation", level="info")
        except Exception as e:
            error_msg = str(e)
            log_progress(f"CRITICAL ERROR: Failed to connect to MongoDB for showtime generation: {error_msg}", level="error")
            log_progress("Check your MongoDB connection settings:", level="error")
            log_progress(f"Connection string: {mask_connection_string(MONGODB_CONNECTION_STRING)}", level="error")
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")
    
    def generate_showtimes(self) -> Dict[str, int]:
        """
        Generate synthetic showtime data for movies and theaters.
        
        Returns:
            Dict containing statistics about the generation process
        """
        stats = {
            "theaters_processed": 0,
            "showtimes_generated": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Get all theaters
            theaters = list(self.theaters_collection.find())
            if not theaters:
                log_progress("No theaters found in database", level="error")
                return stats
            
            log_progress(f"Found {len(theaters)} theaters to process", level="info")
            
            # Get all movies within release window
            release_window = datetime.now() - timedelta(weeks=self.config.showtime_generation.showtimes["release_window_weeks"])
            movies = list(self.movies_collection.find({
                "release_date": {"$exists": True, "$ne": None}
            }))
            
            if not movies:
                log_progress("No movies found in database", level="error")
                return stats
            
            # Filter movies within release window
            movies_in_window = []
            for movie in movies:
                try:
                    release_date = datetime.strptime(movie["release_date"], "%Y-%m-%d")
                    if release_date >= release_window:
                        movies_in_window.append(movie)
                except (ValueError, TypeError):
                    # Skip movies with invalid release dates
                    continue
            
            if not movies_in_window:
                log_progress(f"No movies found within {self.config.showtime_generation.showtimes['release_window_weeks']} week release window", level="error")
                return stats
            
            log_progress(f"Found {len(movies_in_window)} movies within release window", level="info")
            
            # Process each theater
            for theater_idx, theater in enumerate(theaters, 1):
                try:
                    theater_name = theater.get("name", "Unknown Theater")
                    log_progress(f"Processing theater {theater_idx}/{len(theaters)}: {theater_name}", level="info")
                    
                    # Determine number of movies for this theater
                    min_movies = self.config.showtime_generation.showtimes["min_movies_per_theater"]
                    max_movies = self.config.showtime_generation.showtimes["max_movies_per_theater"]
                    
                    if max_movies is None:
                        max_movies = len(movies_in_window)
                    
                    num_movies = random.randint(min_movies, min(max_movies, len(movies_in_window)))
                    log_progress(f"  Will show {num_movies} movies at this theater", level="info")
                    
                    # Select random movies for this theater
                    theater_movies = random.sample(movies_in_window, num_movies)
                    
                    # Generate showtimes for each movie
                    theater_showtimes = 0
                    for movie_idx, movie in enumerate(theater_movies, 1):
                        movie_title = movie.get("title", "Unknown Movie")
                        log_progress(f"    Generating showtimes for movie {movie_idx}/{num_movies}: {movie_title}", level="info")
                        
                        showtimes = self._generate_movie_showtimes(movie, theater)
                        if showtimes:
                            # Save showtimes to MongoDB
                            result = self.showtimes_collection.insert_many(showtimes)
                            num_showtimes = len(result.inserted_ids)
                            theater_showtimes += num_showtimes
                            stats["showtimes_generated"] += num_showtimes
                            log_progress(f"      Generated {num_showtimes} showtimes for {movie_title}", level="info")
                        else:
                            log_progress(f"      No showtimes generated for {movie_title}", level="warning")
                    
                    log_progress(f"  Total showtimes generated for {theater_name}: {theater_showtimes}", level="info")
                    stats["theaters_processed"] += 1
                    
                except Exception as e:
                    log_progress(f"Error processing theater {theater.get('theater_id')}: {str(e)}", level="error")
                    stats["errors"] += 1
            
            stats["end_time"] = datetime.now().isoformat()
            log_progress(f"Showtime generation complete. Generated {stats['showtimes_generated']} showtimes for {stats['theaters_processed']} theaters", level="info")
            return stats
            
        except Exception as e:
            log_progress(f"Error generating showtimes: {str(e)}", level="error")
            stats["errors"] += 1
            stats["end_time"] = datetime.now().isoformat()
            return stats
    
    def _generate_movie_showtimes(self, movie: Dict, theater: Dict) -> List[Dict]:
        """
        Generate showtimes for a specific movie at a theater.
        
        Args:
            movie: Movie document from MongoDB
            theater: Theater document from MongoDB
            
        Returns:
            List of showtime documents
        """
        showtimes = []
        runtime = movie.get("runtime", 120)  # Default to 120 minutes if not specified
        
        # Get operating hours for each day
        for day in range(7):  # 0 = Monday, 6 = Sunday
            day_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][day]
            hours = theater["contact"]["opening_hours"][day_name].split("-")
            
            if not hours or len(hours) != 2:
                continue
            
            opening_time = datetime.strptime(hours[0], "%H:%M").time()
            closing_time = datetime.strptime(hours[1], "%H:%M").time()
            
            # Convert closing time to next day if it's past midnight
            if closing_time < opening_time:
                closing_time = datetime.strptime("23:59", "%H:%M").time()
            
            # Generate showtimes for this day
            current_time = opening_time
            while current_time < closing_time:
                # Check if we have enough time for the movie
                if (datetime.combine(datetime.today(), closing_time) - 
                    datetime.combine(datetime.today(), current_time)).total_seconds() / 60 < runtime:
                    break
                
                # Create showtime document
                showtime = {
                    "movie_id": movie["id"],
                    "theater_id": theater["theater_id"],
                    "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "time": current_time.strftime("%H:%M"),
                    "runtime": runtime,
                    "features": self._get_available_features(movie, theater),
                    "available": True,
                    "created_at": datetime.now().isoformat()
                }
                
                showtimes.append(showtime)
                
                # Add buffer time and movie runtime
                buffer_time = random.randint(
                    self.config.showtime_generation.showtimes["buffer_time_range"]["min"],
                    self.config.showtime_generation.showtimes["buffer_time_range"]["max"]
                )
                total_time = runtime + buffer_time
                
                # Move to next showtime
                current_time = (datetime.combine(datetime.today(), current_time) + 
                              timedelta(minutes=total_time)).time()
        
        return showtimes
    
    def _get_available_features(self, movie: Dict, theater: Dict) -> List[str]:
        """
        Determine available features for a showtime based on movie and theater capabilities.
        
        Args:
            movie: Movie document from MongoDB
            theater: Theater document from MongoDB
            
        Returns:
            List of available features
        """
        features = ["2D"]  # All showings have 2D
        
        # Add 3D if available
        if "3D" in theater["features"]:
            features.append("3D")
        
        # Add 4DX if available
        if "4DX" in theater["features"]:
            features.append("4DX")
        
        # Add IMAX if available
        if "IMAX" in theater["features"]:
            features.append("IMAX")
        
        return features

def main():
    """Main function to run the complete data fetching process."""
    # Setup
    initialize_logging()
    
    # Get configuration
    config = get_config()
    
    # Step 1: Always fetch movie data
    log_progress("STEP 1: FETCHING MOVIE DATA", level="info")
    movie_data = MovieData()
    
    # Always fetch movies each time the program runs
    logger.info("Fetching movie data from TMDB API...")
    movie_stats = movie_data.fetch_and_save_movies(
        count=config.movie.count,
        download_images=config.movie.download_images
    )
    log_progress(f"Movie data collection complete. Fetched {movie_stats['fetched']} movies, saved {movie_stats['saved']} to MongoDB.", level="info")
        
    # Step 2: Import US cities data (if needed)
    log_progress("STEP 2: IMPORTING US CITIES DATA", level="info")
    theater_data = TheaterData()
    theater_data.import_cities_to_mongodb()

    # Step 3: Determine city selection strategy
    log_progress("STEP 3: SELECTING THEATER DATA COLLECTION STRATEGY", level="info")
    city_selection = config.theater.city_selection
    logger.info(f"Using city selection strategy: {city_selection}")
    
    # Step 4: Process cities based on selection strategy
    log_progress("STEP 4: PROCESSING CITIES FOR THEATERS", level="info")
    if city_selection == "random":
        logger.info("Using random sampling of cities")
        process_random_cities(batch_size=config.theater.batch_size)
    else:
        # Default to population-based processing
        logger.info("Using population-based city processing")
        theater_data.process_all_cities(
            batch_size=config.theater.batch_size,
            delay_between_batches=config.theater.delay_between_batches,
            max_batches=config.theater.max_batches,
            timeout_per_batch=config.theater.timeout_per_batch
        )
    
    # Step 5: Export all data
    log_progress("STEP 5: EXPORTING ALL DATA", level="info")
    exporter = DataExporter(config)
    export_results = exporter.export_all_data()
    
    log_progress("DATA FETCHING AND EXPORT COMPLETE", level="info")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch movie and theater data")
    parser.add_argument("--fetch-movies", action="store_true", help="Only fetch movie data from TMDB API")
    parser.add_argument("--fetch-theaters", action="store_true", help="Only fetch theater data")
    parser.add_argument("--export-data", action="store_true", help="Only export data from MongoDB to JSON")
    parser.add_argument("--generate-showtimes", action="store_true", help="Generate synthetic showtime data")
    
    args = parser.parse_args()
    
    # Initialize logging
    initialize_logging()
    
    if args.fetch_movies:
        # Run just the movie fetching process
        log_progress("Running movie data collection only", level="info")
        movie_data = MovieData()
        movie_stats = movie_data.fetch_and_save_movies(
            count=get_config().movie.count,
            download_images=get_config().movie.download_images
        )
        log_progress(f"Movie data collection complete. Fetched {movie_stats['fetched']} movies, saved {movie_stats['saved']} to MongoDB.", level="info")
    elif args.fetch_theaters:
        # Run just the theater fetching process
        log_progress("Running theater data collection only", level="info")
        theater_data = TheaterData()
        theater_data.import_cities_to_mongodb()
        
        # Use configured city selection strategy
        city_selection = get_config().theater.city_selection
        log_progress(f"Using city selection strategy: {city_selection}", level="info")
        
        if city_selection == "random":
            log_progress("Using random sampling of cities", level="info")
            process_random_cities(batch_size=get_config().theater.batch_size)
        else:
            # Default to population-based processing
            log_progress("Using population-based city processing", level="info")
            theater_data.process_all_cities(
                batch_size=get_config().theater.batch_size,
                delay_between_batches=get_config().theater.delay_between_batches,
                max_batches=get_config().theater.max_batches,
                timeout_per_batch=get_config().theater.timeout_per_batch
            )
    elif args.export_data:
        # Run just the data export process
        log_progress("Running data export only", level="info")
        exporter = DataExporter(config)
        export_results = exporter.export_all_data()
    elif args.generate_showtimes:
        # Run just the showtime generation process
        log_progress("Running showtime generation only", level="info")
        generator = ShowtimeGenerator()
        stats = generator.generate_showtimes()
        log_progress(f"Showtime generation complete. Generated {stats['showtimes_generated']} showtimes for {stats['theaters_processed']} theaters", level="info")
    else:
        # No arguments provided, run the complete process
        main()