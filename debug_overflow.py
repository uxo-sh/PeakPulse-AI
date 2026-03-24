import pandas as pd
import numpy as np
from data_processing.preprocessor import preprocessor
from trend_engine.trend_detector import FeatureEngineeringMoviesV2

df, _ = preprocessor()
# Simulate what the test does
valid = (df["revenue"] > 0) & (df["budget"] > 0) & (df["popularity"] > 0)
df = df[valid].copy()

fe = FeatureEngineeringMoviesV2()
X = df.drop(columns=["popularity","revenue","vote_count","vote_average","avg_user_rating",
    "num_ratings","num_unique_users","log_revenue","log_popularity","log_vote_count",
    "ROI","pop_percentile","trend_score","is_trending_future"], errors="ignore")

X_transformed = fe.fit_transform(X)

print("Columns:", X_transformed.columns.tolist())
print("\nMax values:")
for c in X_transformed.columns:
    mx = X_transformed[c].max()
    if mx > 1e6:
        print(f"  ⚠️  {c}: max={mx}")
    elif mx > 1000:
        print(f"  ⚡ {c}: max={mx}")

print(f"\nOverall max: {X_transformed.max().max()}")
print(f"Overall min: {X_transformed.min().min()}")
print(f"float32 max: {np.finfo(np.float32).max}")
