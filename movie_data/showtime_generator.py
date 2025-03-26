#!/usr/bin/env python3
"""
Showtime Generator Module
Generates synthetic showtime data for theaters based on movie releases and theater features.
"""

import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import get_config

# Get configuration
config = get_config()

# Logger for this module
logger = logging.getLogger("ShowtimeGenerator")

class ShowtimeGenerator:
    """Class for generating synthetic showtime data for theaters."""
    
    def __init__(self):
        """Initialize the ShowtimeGenerator with MongoDB connection."""
        # MongoDB connection
        try:
            # Connect to MongoDB
            logger.info("Connecting to MongoDB for showtime generation...")
            self.client = MongoClient("mongodb://localhost:27017/movie_database")
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client["movie_database"]
            
            # Initialize collections
            self.theaters_collection = self.db["theaters"]
            self.movies_collection = self.db["movies"]
            self.showtimes_collection = self.db[config.showtime_generation.collections.showtimes]
            self.operational_hours_collection = self.db[config.showtime_generation.collections.operational_hours]
            
            # Create indexes
            self.showtimes_collection.create_index([
                ("theater_id", 1),
                ("movie_id", 1),
                ("showtime", 1)
            ])
            self.operational_hours_collection.create_index("theater_id", unique=True)
            
            logger.info("MongoDB connection successful for showtime generation")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"CRITICAL ERROR: Failed to connect to MongoDB: {error_msg}")
            logger.error("Check your MongoDB connection settings")
            raise ConnectionError(f"Failed to connect to MongoDB: {error_msg}")
    
    def _parse_time(self, time_str: str) -> datetime:
        """Convert time string to datetime object."""
        return datetime.strptime(time_str, "%H:%M")
    
    def _format_time(self, dt: datetime, format_24h: bool = False) -> str:
        """Format datetime to time string in 12h or 24h format."""
        if format_24h:
            return dt.strftime("%H:%M")
        return dt.strftime("%I:%M %p")
    
    def _generate_operational_hours(self, theater_id: str) -> Dict[str, Any]:
        """
        Generate realistic operational hours for a theater.
        
        Args:
            theater_id: ID of the theater
            
        Returns:
            Dictionary containing operational hours
        """
        # Get weekday and weekend ranges from config
        weekday_config = config.showtime_generation.operating_hours.weekday
        weekend_config = config.showtime_generation.operating_hours.weekend
        
        # Generate random times within ranges
        weekday_opening = self._parse_time(random.choice([
            weekday_config.opening_time_range.min,
            weekday_config.opening_time_range.max
        ]))
        weekday_closing = self._parse_time(random.choice([
            weekday_config.closing_time_range.min,
            weekday_config.closing_time_range.max
        ]))
        
        weekend_opening = self._parse_time(random.choice([
            weekend_config.opening_time_range.min,
            weekend_config.opening_time_range.max
        ]))
        weekend_closing = self._parse_time(random.choice([
            weekend_config.closing_time_range.min,
            weekend_config.closing_time_range.max
        ]))
        
        # Create operational hours document
        operational_hours = {
            "theater_id": theater_id,
            "weekday": {
                "opening": {
                    "12h": self._format_time(weekday_opening),
                    "24h": self._format_time(weekday_opening, True)
                },
                "closing": {
                    "12h": self._format_time(weekday_closing),
                    "24h": self._format_time(weekday_closing, True)
                }
            },
            "weekend": {
                "opening": {
                    "12h": self._format_time(weekend_opening),
                    "24h": self._format_time(weekend_opening, True)
                },
                "closing": {
                    "12h": self._format_time(weekend_closing),
                    "24h": self._format_time(weekend_closing, True)
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return operational_hours
    
    def _get_available_movies(self) -> List[Dict[str, Any]]:
        """
        Get list of movies released within the configured window.
        
        Returns:
            List of movie documents
        """
        # Calculate the cutoff date (current date minus release window)
        cutoff_date = datetime.now() - timedelta(weeks=config.showtime_generation.showtimes.release_window_weeks)
        
        # Query for movies released within the window
        movies = list(self.movies_collection.find({
            "release_date": {"$gte": cutoff_date.isoformat()}
        }))
        
        logger.info(f"Found {len(movies)} movies released within the last {config.showtime_generation.showtimes.release_window_weeks} weeks")
        return movies
    
    def _generate_showtimes_for_movie(
        self,
        movie: Dict[str, Any],
        theater: Dict[str, Any],
        operational_hours: Dict[str, Any],
        buffer_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Generate showtimes for a specific movie at a theater.
        
        Args:
            movie: Movie document
            theater: Theater document
            operational_hours: Theater's operational hours
            buffer_minutes: Buffer time between screenings
            
        Returns:
            List of showtime documents
        """
        showtimes = []
        movie_runtime = movie.get("runtime", 120)  # Default to 120 minutes if not specified
        
        # Get theater's features
        theater_features = theater.get("features", [])
        
        # Generate cutoff date (random date within 3 weeks of release)
        release_date = datetime.fromisoformat(movie["release_date"].replace("Z", "+00:00"))
        max_cutoff = release_date + timedelta(weeks=3)
        cutoff_date = release_date + timedelta(days=random.randint(1, 21))
        
        # Generate showtimes for next 3 weeks
        current_date = datetime.now()
        end_date = current_date + timedelta(weeks=3)
        
        # Get peak hours configuration
        peak_start = self._parse_time(config.showtime_generation.showtimes.peak_hours.start)
        peak_end = self._parse_time(config.showtime_generation.showtimes.peak_hours.end)
        peak_density = config.showtime_generation.showtimes.peak_hours.density_multiplier
        
        current = current_date
        while current <= end_date:
            # Determine if it's a weekend
            is_weekend = current.weekday() >= 5
            
            # Get operational hours for this day
            day_hours = operational_hours["weekend" if is_weekend else "weekday"]
            opening_time = self._parse_time(day_hours["opening"]["24h"])
            closing_time = self._parse_time(day_hours["closing"]["24h"])
            
            # Generate showtimes for this day
            current_time = opening_time
            while current_time + timedelta(minutes=movie_runtime) <= closing_time:
                # Determine if this is a peak hour showing
                is_peak = peak_start <= current_time <= peak_end
                
                # Skip some non-peak showings based on density
                if not is_peak and random.random() > (1 / peak_density):
                    current_time += timedelta(minutes=buffer_minutes)
                    continue
                
                # Generate random view type based on theater features
                available_features = [f for f in theater_features if f in ["2D", "3D", "IMAX", "4DX"]]
                view_type = random.choice(available_features) if available_features else "2D"
                
                # Create showtime document
                showtime = {
                    "theater_id": theater["unique_id"],
                    "movie_id": movie["id"],
                    "movie_title": movie["title"],
                    "theater_name": theater["name"],
                    "theater_address": theater["address"],
                    "view_type": view_type,
                    "date": current.date().isoformat(),
                    "showtime": {
                        "12h": self._format_time(current_time),
                        "24h": self._format_time(current_time, True)
                    },
                    "end_time": {
                        "12h": self._format_time(current_time + timedelta(minutes=movie_runtime)),
                        "24h": self._format_time(current_time + timedelta(minutes=movie_runtime), True)
                    },
                    "cutoff_date": {
                        "12h": self._format_time(cutoff_date),
                        "24h": self._format_time(cutoff_date, True)
                    },
                    "created_at": datetime.now().isoformat()
                }
                
                showtimes.append(showtime)
                current_time += timedelta(minutes=movie_runtime + buffer_minutes)
            
            current += timedelta(days=1)
        
        return showtimes
    
    def generate_showtimes(self) -> Dict[str, Any]:
        """
        Generate synthetic showtimes for all theaters.
        
        Returns:
            Dictionary with statistics about the generation process
        """
        stats = {
            "theaters_processed": 0,
            "movies_processed": 0,
            "showtimes_generated": 0,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Get all theaters
            theaters = list(self.theaters_collection.find())
            if not theaters:
                logger.error("No theaters found in database")
                return stats
            
            # Get available movies
            movies = self._get_available_movies()
            if not movies:
                logger.error("No recent movies found in database")
                return stats
            
            # Process each theater
            for theater in theaters:
                stats["theaters_processed"] += 1
                theater_id = theater["unique_id"]
                
                # Generate and save operational hours
                operational_hours = self._generate_operational_hours(theater_id)
                self.operational_hours_collection.update_one(
                    {"theater_id": theater_id},
                    {"$set": operational_hours},
                    upsert=True
                )
                
                # Determine number of movies for this theater
                min_movies = config.showtime_generation.showtimes.min_movies_per_theater
                max_movies = config.showtime_generation.showtimes.max_movies_per_theater
                
                if max_movies is None:
                    max_movies = len(movies)
                
                num_movies = random.randint(min_movies, max_movies)
                
                # Select movies for this theater
                theater_movies = random.sample(movies, num_movies)
                
                # Generate buffer time for this theater
                buffer_minutes = random.randint(
                    config.showtime_generation.showtimes.buffer_time_range.min,
                    config.showtime_generation.showtimes.buffer_time_range.max
                )
                
                # Generate showtimes for each movie
                for movie in theater_movies:
                    stats["movies_processed"] += 1
                    showtimes = self._generate_showtimes_for_movie(
                        movie,
                        theater,
                        operational_hours,
                        buffer_minutes
                    )
                    
                    # Save showtimes to database
                    if showtimes:
                        self.showtimes_collection.insert_many(showtimes)
                        stats["showtimes_generated"] += len(showtimes)
            
            stats["end_time"] = datetime.now().isoformat()
            logger.info(f"Showtime generation complete. Generated {stats['showtimes_generated']} showtimes for {stats['theaters_processed']} theaters")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating showtimes: {str(e)}")
            stats["error"] = str(e)
            stats["end_time"] = datetime.now().isoformat()
            return stats 