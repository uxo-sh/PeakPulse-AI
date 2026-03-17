# data_collector/test_movies.py
from movies_api import MovieCollector

mc = MovieCollector()
mc.collect_sample_movies()  # utilise la liste par défaut ["Inception", ...]

# Ou personnalise :
# mc.collect_sample_movies(["Avatar", "Titanic", "Parasite", "Everything Everywhere All at Once"])