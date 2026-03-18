# data_collector/test_movies.py
from movies_api import MovieCollector

mc = MovieCollector()
mc.collect_recent_or_keyword_movies(keyword="2025 OR 2026", max_results=25)

# Ou personnalise :
# mc.collect_sample_movies(["Avatar", "Titanic", "Parasite", "Everything Everywhere All at Once"])