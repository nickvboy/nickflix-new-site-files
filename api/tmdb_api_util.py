import random
import requests

def get_random_popular_movies(url, params, count, max_pages):
    movies = {}
    while len(movies) < count:
        random_page = random.randint(1, max_pages)
        params["page"] = random_page
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