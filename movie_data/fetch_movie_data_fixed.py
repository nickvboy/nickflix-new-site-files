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
from pymongo.operations import UpdateOne
from tqdm import tqdm
import argparse

# Import configuration module
from config import get_config, reload_config

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
OUTPUT_JSON_FILE = config.output.movies_json_file
THEATERS_JSON_FILE = config.output.theaters_json_file
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
        """Save theaters to MongoDB and return count of saved theaters."""
        if not theaters:
            return 0
            
        saved_count = 0
        # Prepare theater operations for bulk insert/update
        operations = []
        mongodb_batch_size = self.config.processing.mongodb_batch_size
        
        for theater in theaters:
            try:
                # Set city_geoid if provided
                if city_geoid:
                    theater["city_geoid"] = city_geoid
                    
                # Add to operations list
                operations.append(
                    UpdateOne(
                    {"unique_id": theater["unique_id"]},
                    {"$set": theater},
                    upsert=True
                    )
                )
                saved_count += 1
                
                # Execute in batches if we reach the batch size
                if len(operations) >= mongodb_batch_size:
                    self.theaters_collection.bulk_write(operations)
                    operations = []
                    
            except Exception as e:
                log_progress(f"Error preparing theater {theater.get('name')}: {str(e)}", level="error")
                if self.config.processing.error_handling == "abort":
                    raise
        
        # Execute any remaining operations
        if operations:
            try:
                self.theaters_collection.bulk_write(operations)
            except Exception as e:
                log_progress(f"Error in bulk theater operation: {str(e)}", level="error")
                saved_count = 0
                if self.config.processing.error_handling == "abort":
                    raise
                
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
    
    def save_theaters(self, theaters: List[Dict[str, Any]], output_file: str = None) -> None:
        """Save theater data to a JSON file for backup or offline use."""
        # Use config if output_file not provided
        if output_file is None:
            output_file = self.config.output.theaters_json_file
            
        log_progress(f"Saving {len(theaters)} theaters to {output_file}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Use indent if pretty JSON is enabled
            indent = 2 if self.config.output.pretty_json else None
            json.dump(theaters, f, ensure_ascii=False, indent=indent)

    def update_cities_with_nominatim_coordinates(self, batch_size=None, delay_between_requests=1) -> Dict[str, int]:
        """
        Fetch bounding box coordinates from Nominatim for cities that need them.
        Updates MongoDB with the coordinates and finds theaters for these cities.
        
        Args:
            batch_size: Number of cities to process at once
            delay_between_requests: Delay in seconds between Nominatim API requests
            
        Returns:
            Dictionary with statistics about the process
        """
        # Use default batch size from processing config if not provided
        if batch_size is None:
            batch_size = self.config.processing.mongodb_batch_size
            
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
        """Get a list of cities that haven't been processed yet, sorted by population."""
        log_progress(f"Retrieving pending cities (limit: {limit})")
        
        # Create index on population field for faster sorting if it doesn't exist
        if "population_-1" not in [idx["name"] for idx in self.cities_collection.list_indexes()]:
            self.cities_collection.create_index([("population", -1)])
            
        # Create index on processed field for faster filtering if it doesn't exist
        if "processed_1" not in [idx["name"] for idx in self.cities_collection.list_indexes()]:
            self.cities_collection.create_index([("processed", 1)])
            
        # Query with projection to only fetch needed fields
        cursor = self.cities_collection.find(
            {
                "processed": {"$ne": True},
                "population": {"$exists": True, "$ne": None}
            },
            {"_id": 0, "name": 1, "state": 1, "geoid": 1, "population": 1}  # Only fetch needed fields
        ).sort("population", -1)
        
        if limit:
            cursor = cursor.limit(limit)
            
        cities = list(cursor)
        log_progress(f"Retrieved {len(cities)} pending cities")
        return cities
    
    def process_batch_of_cities(self, batch_size_or_cities=None, delay_between_cities=None, timeout=None) -> Dict[str, Any]:
        """
        Process a batch of cities to find theaters.
        
        Args:
            batch_size_or_cities: Either a number of cities to process or a list of city documents
            delay_between_cities: Delay in seconds between cities
            timeout: Optional timeout in seconds for the entire batch
            
        Returns:
            Dictionary with statistics about the processed batch
        """
        # Get configuration
        config = get_config()
        
        # Use config if delay parameter not provided
        if delay_between_cities is None:
            delay_between_cities = config.theater.delay_between_cities
            
        if timeout is None:
            timeout = config.theater.timeout_per_batch
        
        # Determine if we received a batch size or a list of cities
        if isinstance(batch_size_or_cities, list):
            # We received a list of city documents
            cities = batch_size_or_cities
            batch_size = len(cities)
            log_progress(f"Starting processing batch of {batch_size} cities")
        else:
            # We received a batch size (or None)
            batch_size = batch_size_or_cities
            if batch_size is None:
                batch_size = config.theater.batch_size
                
            log_progress(f"Starting processing batch of {batch_size} cities")
            
            # Get batch of cities to process
            cities = self.get_pending_cities(limit=batch_size)
        
        # Statistics for this batch
        stats = {
            "batch_size": batch_size,
            "processed_cities": 0,
            "pending_cities": len(cities),
            "theaters_found": 0,
            "errors": 0,
            "batch_start": datetime.now().isoformat(),
            "status": "completed"  # Default status
        }
        
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
                    # Use delay range from config if it's a dictionary
                    if isinstance(delay_between_cities, dict):
                        delay_min = delay_between_cities.get("min", 0.5)
                        delay_max = delay_between_cities.get("max", 1.0)
                        actual_delay = random.uniform(delay_min, delay_max)
                    else:
                        actual_delay = delay_between_cities
                        
                    log_progress(f"Adding delay of {actual_delay:.2f} seconds before next city", level="debug")
                    time.sleep(actual_delay)
            
            except Exception as e:
                log_progress(f"Error processing city {city_name}: {str(e)}", city_name, "error")
                # Mark city as processed with error
                self.mark_city_as_processed(geoid, error=str(e))
                stats["errors"] += 1
                
                if config.processing.error_handling == "abort":
                    log_progress("Aborting batch due to error handling configuration", level="error")
                    stats["status"] = "aborted"
                    break
        
        # Calculate time taken
        end_time = time.time()
        stats["duration_seconds"] = end_time - start_time
        stats["batch_end"] = datetime.now().isoformat()
        
        # Save progress
        self.save_progress(stats)
        
        # Log summary
        log_progress(f"Batch processing complete. Processed {stats['processed_cities']} cities, found {stats['theaters_found']} theaters, encountered {stats['errors']} errors")
        return stats
    
    def process_all_cities(self, batch_size=None, delay_between_batches=None, max_batches=None, timeout_per_batch=None):
        """
        Process all cities in batches, with the ability to resume from where it left off.
        
        Args:
            batch_size: Number of cities to process in each batch
            delay_between_batches: Delay in seconds between batches
            max_batches: Maximum number of batches to process (None = no limit)
            timeout_per_batch: Timeout in seconds for each batch
        """
        # Use config if parameters not provided
        if batch_size is None:
            batch_size = self.config.theater.batch_size
            
        if delay_between_batches is None:
            delay_between_batches = self.config.theater.delay_between_batches
            
        if max_batches is None:
            max_batches = self.config.theater.max_batches
            
        if timeout_per_batch is None:
            timeout_per_batch = self.config.theater.timeout_per_batch
            
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
                    batch_size_or_cities=batch_size,
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
                
                # If batch was aborted and error handling is set to abort, stop processing
                if batch_stats.get("status") == "aborted" and self.config.processing.error_handling == "abort":
                    log_progress("Stopping all processing due to batch abort", level="warning")
                    break
                
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
                
                # Check if we should abort on error
                if self.config.processing.error_handling == "abort":
                    log_progress("Stopping all processing due to error", level="error")
                    break
                    
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
    
    def export_all_theaters_to_json(self, output_file=None):
        """Export all theaters from MongoDB to a JSON file."""
        # Use config if output_file not provided
        if output_file is None:
            output_file = self.config.output.theaters_json_file
            
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
            if self.config.processing.error_handling == "abort":
                raise
    
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
                    delay = random.uniform(0.5, 1.0)  # Reduced from 2-5 seconds to 0.5-1 second
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
    
    # Step 5: Export all theaters to JSON
    log_progress("STEP 5: EXPORTING THEATER DATA", level="info")
    theater_data.export_all_theaters_to_json()
    
    log_progress("DATA FETCHING COMPLETE", level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch movie and theater data")
    parser.add_argument("--fetch-movies", action="store_true", help="Only fetch movie data from TMDB API")
    parser.add_argument("--fetch-theaters", action="store_true", help="Only fetch theater data")
    
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
        
        # Export theaters to JSON
        theater_data.export_all_theaters_to_json()
        log_progress("Theater data collection complete", level="info")
    else:
        # No arguments provided, run the complete process
        main()