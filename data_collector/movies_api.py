import requests
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
OMDB_KEY = os.getenv("OMDB_API_KEY")  # obtiens-la ici : https://www.omdbapi.com/apikey.aspx

class MovieCollector:
    def __init__(self):
        if not OMDB_KEY:
            print("⚠️  OMDB_API_KEY manquante dans .env → mode limité")
        self.session = requests.Session()

    def search_movie(self, title: str):
        """Recherche basique par titre"""
        if not OMDB_KEY:
            return None
        url = "http://www.omdbapi.com/"
        params = {"t": title, "apikey": OMDB_KEY, "type": "movie"}
        try:
            r = self.session.get(url, params=params, timeout=10)
            data = r.json()
            if data.get("Response") == "True":
                return data
            else:
                print(f"Erreur OMDb pour '{title}': {data.get('Error')}")
        except Exception as e:
            print(e)
        return None

    def collect_sample_movies(self, titles_list=None):
        """Exemple avec une petite liste de films connus"""
        if titles_list is None:
            titles_list = ["Inception", "The Matrix", "Dune", "Oppenheimer", "Interstellar"]

        results = []
        for title in titles_list:
            data = self.search_movie(title)
            if data:
                results.append({
                    "title": data.get("Title"),
                    "year": data.get("Year"),
                    "genre": data.get("Genre"),
                    "imdb_rating": data.get("imdbRating"),
                    "plot": data.get("Plot")[:200],
                    "poster": data.get("Poster"),
                    "collected_at": datetime.now().isoformat()
                })
            time.sleep(1.5)  # respect limite gratuite

        if results:
            df = pd.DataFrame(results)
            filename = f"raw/movies_sample_{datetime.now():%Y%m%d}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ {len(df)} films collectés dans {filename}")
            return df
        return None