import os
from dotenv import load_dotenv
load_dotenv()
import csv
import argparse
import requests
import random


def ensure_directory_exists(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def download_image(url, save_path):
    """Download image from URL and save it to specified path."""
    if not url:
        return None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return save_path
        return None
    except:
        return None


def get_api_key():
    """Retrieve the TMDB API key from the environment variable TMDB_API_KEY."""
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        raise ValueError("TMDB_API_KEY not set in environment variables")
    return api_key


def get_movie_details(api_key, movie_id):
    """Retrieve detailed movie information by TMDB movie ID."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None


def get_image_urls(movie_details):
    """Construct full URLs for poster and backdrop images."""
    base_url = "https://image.tmdb.org/t/p/w500"
    poster_path = movie_details.get("poster_path")
    backdrop_path = movie_details.get("backdrop_path")
    poster_url = base_url + poster_path if poster_path else ''
    backdrop_url = base_url + backdrop_path if backdrop_path else ''
    return poster_url, backdrop_url


def get_random_popular_movies(api_key, count=50):
    """Retrieve a list of random popular movies that most people have likely heard of."""
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": api_key,
        "sort_by": "popularity.desc",
        "vote_count.gte": 1000,  # Ensures movies have significant viewership
        "vote_average.gte": 6.0,  # Ensures decent quality
        "page": 1
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Failed to fetch popular movies")
    
    data = response.json()
    total_pages = data.get("total_pages", 1)
    max_pages = min(total_pages, 100)  # First 100 pages will have the most popular movies
    
    movies = {}
    while len(movies) < count:
        random_page = random.randint(1, max_pages)
        params = {
            "api_key": api_key,
            "sort_by": "popularity.desc",
            "vote_count.gte": 1000,
            "vote_average.gte": 6.0,
            "page": random_page
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            page_data = response.json()
            results = page_data.get("results", [])
            random.shuffle(results)
            for movie in results:
                movie_id = movie.get("id")
                if movie_id not in movies:
                    movies[movie_id] = movie
                if len(movies) >= count:
                    break
    
    detailed_movies = []
    for movie in movies.values():
        movie_id = movie.get("id")
        details = get_movie_details(api_key, movie_id)
        if details:
            detailed_movies.append(details)
        else:
            detailed_movies.append(movie)
    return detailed_movies


def write_movies_to_csv(movies, output_csv):
    """Write movie data to CSV file and download images."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_csv)
    
    # Create image directories
    images_base_dir = os.path.join(script_dir, "movie_images")
    posters_dir = os.path.join(images_base_dir, "posters")
    banners_dir = os.path.join(images_base_dir, "banners")
    ensure_directory_exists(posters_dir)
    ensure_directory_exists(banners_dir)
    
    # Create .gitignore in the movie_images directory
    gitignore_path = os.path.join(images_base_dir, ".gitignore")
    with open(gitignore_path, 'w') as f:
        f.write("# Ignore image files in this directory and subdirectories\n")
        f.write("*.jpg\n")
        f.write("*.jpeg\n")
        f.write("*.png\n")
        f.write("*.gif\n")
        f.write("*.webp\n")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        header = ["title", "id", "release_date", "overview", "genres", "poster_url", "backdrop_url", "local_poster_path", "local_banner_path"]
        writer.writerow(header)
        
        for movie in movies:
            movie_id = movie.get("id", "")
            title = movie.get("title", "").replace(" ", "_")  # Use for filename
            genres_data = movie.get("genres")
            genres = ', '.join([g.get("name") for g in genres_data]) if genres_data else ""
            poster_url, backdrop_url = get_image_urls(movie)
            
            # Download and save images
            poster_filename = f"{movie_id}_{title}_poster.jpg"
            banner_filename = f"{movie_id}_{title}_banner.jpg"
            poster_save_path = os.path.join(posters_dir, poster_filename)
            banner_save_path = os.path.join(banners_dir, banner_filename)
            
            local_poster_path = download_image(poster_url, poster_save_path)
            local_banner_path = download_image(backdrop_url, banner_save_path)
            
            # Convert to relative paths for CSV
            if local_poster_path:
                local_poster_path = os.path.relpath(local_poster_path, script_dir)
            if local_banner_path:
                local_banner_path = os.path.relpath(local_banner_path, script_dir)
            
            writer.writerow([
                movie.get("title", ""),
                movie_id,
                movie.get("release_date", ""),
                movie.get("overview", ""),
                genres,
                poster_url,
                backdrop_url,
                local_poster_path or "",
                local_banner_path or ""
            ])


def main():
    parser = argparse.ArgumentParser(description="TMDB API Utility: Retrieve random popular movies and output to CSV")
    parser.add_argument("--output_csv", type=str, default="popular_movies_output.csv", help="Output CSV filename (saved in this folder)")
    parser.add_argument("--count", type=int, default=50, help="Number of random popular movies to retrieve")
    args = parser.parse_args()

    api_key = get_api_key()
    movies = get_random_popular_movies(api_key, count=args.count)
    write_movies_to_csv(movies, args.output_csv)


if __name__ == "__main__":
    main() 