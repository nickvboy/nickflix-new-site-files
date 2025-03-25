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
        
    @property
    def theater_brands(self) -> List[str]:
        """Theater brands to include."""
        return self.config.get(self.section, "theater_brands", ["amc", "regal", "cinemark"])
        
    @property
    def population_tiers(self) -> Dict[str, Dict[str, Any]]:
        """Population threshold tiers for theater generation."""
        default_tiers = {
            "large_city": {
                "min_population": 500000,
                "max_population": None,
                "min_theaters": 5,
                "max_theaters": 9
            },
            "medium_city": {
                "min_population": 100000,
                "max_population": 500000,
                "min_theaters": 2,
                "max_theaters": 4
            },
            "small_city": {
                "min_population": 0,
                "max_population": 100000,
                "min_theaters": 0,
                "max_theaters": 1
            }
        }
        return self.config.get(self.section, "population_tiers", default_tiers)
        
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