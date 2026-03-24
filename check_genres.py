import pandas as pd
df = pd.read_csv('data_collector/raw/TMDB_movie_dataset_v11.csv', nrows=2)
print("Genres:", repr(df['genres'].iloc[0]))
print("Keywords:", repr(df['keywords'].iloc[0]))
