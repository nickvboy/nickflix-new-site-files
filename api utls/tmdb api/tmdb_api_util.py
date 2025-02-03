import os
from dotenv import load_dotenv
load_dotenv()
import csv
import argparse
import requests
import random


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
    """Retrieve a list of random popular movies from TMDB."""
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": api_key, "page": 1}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Failed to fetch popular movies")
    data = response.json()
    total_pages = data.get("total_pages", 1)
    max_pages = min(total_pages, 500)
    movies = {}
    while len(movies) < count:
        random_page = random.randint(1, max_pages)
        params = {"api_key": api_key, "page": random_page}
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
    """Write movie data to CSV file in the same folder as this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_csv)
    with open(output_path, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.writer(f_out)
        header = ["title", "id", "release_date", "overview", "genres", "poster_url", "backdrop_url"]
        writer.writerow(header)
        
        for movie in movies:
            genres_data = movie.get("genres")
            genres = ', '.join([g.get("name") for g in genres_data]) if genres_data else ""
            poster_url, backdrop_url = get_image_urls(movie)
            writer.writerow([
                movie.get("title", ""),
                movie.get("id", ""),
                movie.get("release_date", ""),
                movie.get("overview", ""),
                genres,
                poster_url,
                backdrop_url
            ])


def main():
    parser = argparse.ArgumentParser(description="TMDB API Utility: Retrieve random popular movies and output to CSV")
    parser.add_argument("--output_csv", type=str, default="movie_data_output.csv", help="Output CSV filename (saved in this folder)")
    parser.add_argument("--count", type=int, default=50, help="Number of random popular movies to retrieve")
    args = parser.parse_args()

    api_key = get_api_key()
    movies = get_random_popular_movies(api_key, count=args.count)
    write_movies_to_csv(movies, args.output_csv)


if __name__ == "__main__":
    main() 