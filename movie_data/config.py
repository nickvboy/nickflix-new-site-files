#!/usr/bin/env python3
"""
Configuration module for the movie data fetching script.
Loads settings from a YAML configuration file and provides
access to configuration values throughout the application.
"""

import os
import yaml
import logging
from typing import Dict, Any, List, Optional

# Default configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

# Logger for this module
logger = logging.getLogger("MovieFetcherConfig")


class ConfigManager:
    """
    Configuration manager that loads settings from a YAML file 
    and provides access to configuration values.
    """
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from the YAML file."""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                return
                
            with open(self.config_file, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
                logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Continue with empty config, defaults will be used
            self.config = {}
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        if not self.config or section not in self.config:
            return default
            
        section_dict = self.config.get(section, {})
        return section_dict.get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Configuration section name
            
        Returns:
            Dictionary containing the section configuration or empty dict if not found
        """
        return self.config.get(section, {})


class MovieConfig:
    """Configuration for movie data collection."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "movie_data"
        
    @property
    def count(self) -> int:
        """Number of movies to fetch."""
        return self.config.get(self.section, "count", 50)
        
    @property
    def min_vote_count(self) -> int:
        """Minimum number of votes a movie should have."""
        return self.config.get(self.section, "min_vote_count", 1000)
        
    @property
    def min_vote_average(self) -> float:
        """Minimum average rating a movie should have."""
        return self.config.get(self.section, "min_vote_average", 6.0)
        
    @property
    def sort_by(self) -> str:
        """Movie selection criteria (popularity.desc, release_date.desc, vote_average.desc)."""
        return self.config.get(self.section, "sort_by", "popularity.desc")
        
    @property
    def download_images(self) -> bool:
        """Whether to download movie images."""
        return self.config.get(self.section, "download_images", True)
        
    @property
    def image_types(self) -> List[str]:
        """Types of images to download (poster, backdrop)."""
        return self.config.get(self.section, "image_types", ["poster", "backdrop"])
        
    @property
    def genres_include(self) -> List[int]:
        """Genres to include (by ID)."""
        return self.config.get(self.section, "genres_include", [])
        
    @property
    def genres_exclude(self) -> List[int]:
        """Genres to exclude (by ID)."""
        return self.config.get(self.section, "genres_exclude", [])
        
    @property
    def release_year_start(self) -> Optional[int]:
        """Start year for release date range filter."""
        return self.config.get(self.section, "release_year_start", None)
        
    @property
    def release_year_end(self) -> Optional[int]:
        """End year for release date range filter."""
        return self.config.get(self.section, "release_year_end", None)
        
    @property
    def language(self) -> str:
        """Language filter (ISO 639-1 codes)."""
        return self.config.get(self.section, "language", "en-US")


class OverpassConfig:
    """Configuration for Overpass API settings."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "theater_data.overpass"
        
    @property
    def base_url(self) -> str:
        """Base URL for Overpass API."""
        return self.config.get(self.section, "base_url", "https://overpass-api.de/api/interpreter")
        
    @property
    def timeout(self) -> int:
        """Timeout for API requests in seconds."""
        return self.config.get(self.section, "timeout", 30)
        
    @property
    def max_retries(self) -> int:
        """Maximum number of retries for failed requests."""
        return self.config.get(self.section, "max_retries", 3)
        
    @property
    def retry_delay(self) -> int:
        """Delay between retries in seconds."""
        return self.config.get(self.section, "retry_delay", 5)
        
    @property
    def query_timeout(self) -> int:
        """Query timeout in seconds."""
        return self.config.get(self.section, "query_timeout", 25)
        
    @property
    def use_area_query(self) -> bool:
        """Whether to use area query (true) or bounding box (false)."""
        return self.config.get(self.section, "use_area_query", True)


class TheaterGenerationConfig:
    """Configuration for theater data generation."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "theater_data.generation"
        
    @property
    def population_thresholds(self) -> Dict[str, int]:
        """Population thresholds for different city sizes."""
        return self.config.get(self.section, "population_thresholds", {
            "major_metro": 1000000,
            "large_city": 500000,
            "medium_city": 100000
        })
        
    @property
    def theater_counts(self) -> Dict[str, Dict[str, List[int]]]:
        """Theater counts per brand and city size."""
        return self.config.get(self.section, "theater_counts", {
            "major_metro": {
                "amc": [3, 8],
                "regal": [2, 6],
                "cinemark": [2, 5],
                "other": [1, 3]
            },
            "large_city": {
                "amc": [2, 5],
                "regal": [1, 4],
                "cinemark": [1, 3],
                "other": [1, 2]
            },
            "medium_city": {
                "amc": [1, 3],
                "regal": [1, 2],
                "cinemark": [1, 2],
                "other": [0, 1]
            },
            "small_city": {
                "amc": [0, 2],
                "regal": [0, 1],
                "cinemark": [0, 1],
                "other": [0, 0]
            }
        })
        
    @property
    def naming_patterns(self) -> Dict[str, Dict[str, str]]:
        """Naming patterns for different brands and city sizes."""
        return self.config.get(self.section, "naming_patterns", {
            "amc": {
                "major_metro": "{brand} {city} {number}",
                "large_city": "{brand} {city} {number}",
                "medium_city": "{brand} {city} {number}",
                "small_city": "{brand} {city} {number}"
            },
            "regal": {
                "major_metro": "{brand} {city} {suffix} {number}",
                "large_city": "{brand} {city} {suffix}",
                "medium_city": "{brand} {city} {suffix}",
                "small_city": "{brand} {city} {suffix}"
            },
            "cinemark": {
                "major_metro": "{brand} {city} {suffix} {number}",
                "large_city": "{brand} {city} {suffix}",
                "medium_city": "{brand} {city} {suffix}",
                "small_city": "{brand} {city} {suffix}"
            }
        })
        
    @property
    def suffixes(self) -> Dict[str, List[str]]:
        """Available suffixes for theater names."""
        return self.config.get(self.section, "suffixes", {
            "regal": ["Cinema", "Stadium", "Grande", "Premiere", "Cineplex"],
            "cinemark": ["Theater", "Movies", "Cinema", "Xenon"]
        })
        
    @property
    def features(self) -> Dict[str, int]:
        """Number of features to include by city size."""
        return self.config.get(self.section, "features", {
            "major_metro": 4,  # All features
            "large_city": 3,   # 2D, 3D, and one premium
            "medium_city": 2,  # 2D and 3D
            "small_city": 2    # 2D and 3D
        })
        
    @property
    def available_features(self) -> List[str]:
        """Available features to choose from."""
        return self.config.get(self.section, "available_features", [
            "2D", "3D", "4DX", "IMAX"
        ])
        
    @property
    def feature_distribution(self) -> Dict[str, Dict[str, int]]:
        """Feature distribution rules by city size."""
        return self.config.get(self.section, "feature_distribution", {
            "major_metro": {
                "2D": 100,  # All theaters have 2D
                "3D": 100,  # All theaters have 3D
                "4DX": 40,  # 40% have 4DX
                "IMAX": 30  # 30% have IMAX
            },
            "large_city": {
                "2D": 100,
                "3D": 100,
                "4DX": 30,
                "IMAX": 20
            },
            "medium_city": {
                "2D": 100,
                "3D": 100,
                "4DX": 20,
                "IMAX": 10
            },
            "small_city": {
                "2D": 100,
                "3D": 100,
                "4DX": 10,
                "IMAX": 5
            }
        })
        
    @property
    def street_names(self) -> List[str]:
        """Street name templates."""
        return self.config.get(self.section, "street_names", [
            "Main Street", "Park Avenue", "Market Street", "Broadway",
            "First Avenue", "Second Street", "Oak Street", "Maple Avenue",
            "Pine Street", "Cedar Avenue", "Elm Street", "Washington Avenue",
            "Lake Street", "River Road", "Highland Avenue", "Valley View Drive",
            "Center Street", "Theater District", "Entertainment Boulevard",
            "Cinema Plaza", "Movie Lane", "Showtime Drive"
        ])


class TheaterConfig:
    """Configuration for theater data collection."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "theater_data"
        self.overpass = OverpassConfig(config_manager)
        self.generation = TheaterGenerationConfig(config_manager)
        
    @property
    def theater_brands(self) -> List[str]:
        """Theater brands to include."""
        return self.config.get(self.section, "theater_brands", ["amc", "regal", "cinemark"])
        
    @property
    def city_selection(self) -> str:
        """City selection strategy (population, random, region)."""
        return self.config.get(self.section, "city_selection", "population")
        
    @property
    def batch_size(self) -> int:
        """Number of cities to process in each batch."""
        return self.config.get(self.section, "batch_size", 1)
        
    @property
    def delay_between_cities(self) -> Dict[str, float]:
        """Delay range between cities in seconds."""
        default_delay = {"min": 0.5, "max": 1.0}
        return self.config.get(self.section, "delay_between_cities", default_delay)
        
    @property
    def delay_between_batches(self) -> float:
        """Delay between batches in seconds."""
        return self.config.get(self.section, "delay_between_batches", 5.0)
        
    @property
    def timeout_per_batch(self) -> int:
        """Timeout per batch in seconds."""
        return self.config.get(self.section, "timeout_per_batch", 1800)  # 30 minutes
        
    @property
    def max_batches(self) -> Optional[int]:
        """Maximum number of batches to process."""
        return self.config.get(self.section, "max_batches", None)
        
    @property
    def max_cities(self) -> Optional[int]:
        """Maximum number of cities to process (null for all cities)."""
        return self.config.get(self.section, "max_cities", None)


class ProcessingConfig:
    """Configuration for data processing."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "processing"
        
    @property
    def mongodb_batch_size(self) -> int:
        """Batch size for MongoDB bulk operations."""
        return self.config.get(self.section, "mongodb_batch_size", 500)
        
    @property
    def error_handling(self) -> str:
        """Error handling behavior (skip, abort)."""
        return self.config.get(self.section, "error_handling", "skip")


class OutputConfig:
    """Configuration for data output."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "output"
        
    @property
    def movies_json_file(self) -> str:
        """Path to the movies JSON output file."""
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "movies_data.json")
        return self.config.get(self.section, "movies_json_file", default)
        
    @property
    def theaters_json_file(self) -> str:
        """Path to the theaters JSON output file."""
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "theaters.json")
        return self.config.get(self.section, "theaters_json_file", default)
        
    @property
    def pretty_json(self) -> bool:
        """Whether to format JSON output with indentation."""
        return self.config.get(self.section, "pretty_json", True)


class LoggingConfig:
    """Configuration for logging."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "logging"
        
    @property
    def log_level(self) -> str:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        return self.config.get(self.section, "log_level", "INFO")
        
    @property
    def log_to_console(self) -> bool:
        """Whether to log to console."""
        return self.config.get(self.section, "log_to_console", True)
        
    @property
    def log_to_file(self) -> bool:
        """Whether to log to file."""
        return self.config.get(self.section, "log_to_file", True)
        
    @property
    def log_file(self) -> str:
        """Path to the log file."""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        default = os.path.join(log_dir, "movie_fetcher.log")
        return self.config.get(self.section, "log_file", default)


class ShowtimeGenerationConfig:
    """Configuration for showtime generation."""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize with a ConfigManager.
        
        Args:
            config_manager: ConfigManager instance
        """
        self.config = config_manager
        self.section = "showtime_generation"
    
    @property
    def operating_hours(self) -> Dict[str, Dict]:
        """Operating hours configuration."""
        return self.config.get(self.section, "operating_hours", {
            "weekday": {
                "opening_time_range": {
                    "min": "08:00",
                    "max": "11:00"
                },
                "closing_time_range": {
                    "min": "22:00",
                    "max": "02:00"
                }
            },
            "weekend": {
                "opening_time_range": {
                    "min": "09:00",
                    "max": "11:00"
                },
                "closing_time_range": {
                    "min": "23:00",
                    "max": "03:00"
                }
            }
        })
    
    @property
    def showtimes(self) -> Dict[str, Any]:
        """Showtime generation settings."""
        return self.config.get(self.section, "showtimes", {
            "buffer_time_range": {
                "min": 5,
                "max": 15
            },
            "release_window_weeks": 3,
            "min_movies_per_theater": 1,
            "max_movies_per_theater": None,
            "distribution": "random",
            "peak_hours": {
                "start": "17:00",
                "end": "22:00",
                "density_multiplier": 1.5
            }
        })
    
    @property
    def collections(self) -> Dict[str, str]:
        """MongoDB collection names."""
        return self.config.get(self.section, "collections", {
            "showtimes": "showtimes",
            "operational_hours": "operational_hours"
        })


# Main configuration object
class Config:
    """Main configuration object providing access to all configuration sections."""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize the configuration.
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_manager = ConfigManager(config_file)
        self.movie = MovieConfig(self.config_manager)
        self.theater = TheaterConfig(self.config_manager)
        self.processing = ProcessingConfig(self.config_manager)
        self.output = OutputConfig(self.config_manager)
        self.logging = LoggingConfig(self.config_manager)
        self.showtime_generation = ShowtimeGenerationConfig(self.config_manager)
    
    def initialize_logging(self) -> None:
        """Initialize logging based on configuration."""
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = log_level_map.get(self.logging.log_level, logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.logging.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # Reset root logger
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Configure root logger
        logging.root.setLevel(log_level)
        
        # Format for log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Add console handler if configured
        if self.logging.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logging.root.addHandler(console_handler)
        
        # Add file handler if configured
        if self.logging.log_to_file:
            file_handler = logging.FileHandler(self.logging.log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logging.root.addHandler(file_handler)
        
        logging.info(f"Logging initialized at level {self.logging.log_level}")


# Create a global configuration instance
config = Config()

# Functions for accessing configuration
def get_config() -> Config:
    """Get the global configuration instance."""
    return config

def reload_config(config_file: str = CONFIG_FILE) -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_file: Path to the YAML configuration file
        
    Returns:
        Reloaded configuration instance
    """
    global config
    config = Config(config_file)
    config.initialize_logging()
    return config 