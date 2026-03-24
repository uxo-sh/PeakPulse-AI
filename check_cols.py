import pandas as pd
df = pd.read_csv('data_collector/raw/TMDB_movie_dataset_v11.csv', nrows=1000)
print('STATUS VALUES:', df['status'].unique())
print('PRODUCTION EXAMPLES:', df['production_companies'].dropna().head(5).tolist())
