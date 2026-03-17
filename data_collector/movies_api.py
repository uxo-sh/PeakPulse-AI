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
    
    def search_movies_by_keyword(self, keyword="2026", max_results=20):
        if not OMDB_KEY:
            return []
        url = "http://www.omdbapi.com/"
        results = []
        for page in range(1, 3):  # max 2 pages pour limiter
            params = {"s": keyword, "type": "movie", "page": page, "apikey": OMDB_KEY}
            r = self.session.get(url, params=params)
            data = r.json()
            if data.get("Response") == "True":
                results.extend(data.get("Search", []))
            time.sleep(1.5)
        return results[:max_results]

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
    
    def collect_recent_or_keyword_movies(self, keyword="2025 OR 2026", max_results=30):
        if not OMDB_KEY:
            print("Clé OMDB manquante")
            return None
        url = "http://www.omdbapi.com/"
        results = []
        page = 1
        while len(results) < max_results and page <= 5:
            params = {"s": keyword, "type": "movie", "page": page, "apikey": OMDB_KEY}
            try:
                r = self.session.get(url, params=params, timeout=10)
                data = r.json()
                if data.get("Response") == "True":
                    for item in data.get("Search", []):
                        details = self.search_movie(item["Title"])
                        if details:
                            results.append({
                                "title": details.get("Title"),
                                "year": details.get("Year"),
                                "genre": details.get("Genre"),
                                "imdb_rating": details.get("imdbRating"),
                                "plot": details.get("Plot")[:200],
                                "poster": details.get("Poster"),
                                "collected_at": datetime.now().isoformat()
                            })
                        if len(results) >= max_results:
                            break
                    page += 1
                else:
                    break
            except:
                break
            time.sleep(1.5)
        if results:
            df = pd.DataFrame(results)
            filename = f"data_collector/raw/movies_keyword_{keyword.replace(' ', '_')}_{datetime.now():%Y%m%d}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ {len(df)} films collectés (recherche: {keyword})")
            return df
        return None