import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    f1_score,
    recall_score,
    precision_score,
)
from ml_models.model_movies import pipeline
from data_processing.preprocessor import preprocessor

LEAK_COLS = [
    "popularity",
    "revenue",
    "vote_count",
    "vote_average",
    "ROI",
    "pop_percentile",
    "trend_score",
    "avg_user_rating",
    "num_ratings",
    "num_unique_users",
    "log_revenue",
    "log_popularity",
    "log_vote_count",
]

def create_trend_target_movies(df: pd.DataFrame):
    df = df.copy()
    valid_mask = (df["revenue"] > 0) & (df["budget"] > 0) & (df["popularity"] > 0)
    df = df[valid_mask].copy()
    df["ROI"] = df["revenue"] / df["budget"]
    df["pop_percentile"] = df["popularity"].rank(pct=True)
    df["is_trending_future"] = ((df["ROI"] > 1.5) & (df["pop_percentile"] > 0.65)).astype(int)
    signal_used = "ROI > 1.5 & Pop > P65"
    return df, signal_used

def find_threshold_precision_target(y_true, y_proba, target_precision=0.45):
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    precisions = precisions[:-1]
    recalls = recalls[:-1]
    denom = precisions + recalls + 1e-9
    f1_scores = 2 * precisions * recalls / denom
    valid = precisions >= target_precision
    if valid.sum() > 0:
        f1_valid = np.where(valid, f1_scores, 0)
        best_idx = int(np.argmax(f1_valid))
    else:
        best_idx = int(np.argmax(f1_scores))
    
    best_thr = float(thresholds[best_idx])
    best_f1  = float(f1_scores[best_idx])

    return {
        "threshold": best_thr,
        "f1": best_f1,
        "precisions": precisions.tolist(),
        "recalls": recalls.tolist(),
        "thresholds": thresholds.tolist(),
    }

def analyze_trending_genres_movies(X_test: pd.DataFrame, y_pred: np.ndarray, y_proba: np.ndarray) -> pd.DataFrame:
    empty_df = pd.DataFrame(columns=["Genre", "Count", "Avg_Proba", "Trend_Ratio", "Avg_Proba_Trend", "Trend_Score"])
    genre_cols = [c for c in X_test.columns if c.startswith("has_")]
    if not genre_cols:
        return empty_df

    df = X_test.copy()
    df["pred"]  = y_pred
    df["proba"] = y_proba

    rows = []
    for col in genre_cols:
        sub = df[df[col] == 1]
        if len(sub) == 0:
            continue
        count = len(sub)
        avg_proba = sub["proba"].mean()
        trend_ratio = sub["pred"].mean()
        trend_sub = sub[sub["pred"] == 1]
        avg_proba_trend = trend_sub["proba"].mean() if len(trend_sub) > 0 else 0.0
        trend_score = avg_proba * np.log1p(count)
        rows.append({
            "Genre": col.replace("has_", "").replace("_", " ").title(),
            "Count": count,
            "Avg_Proba": avg_proba,
            "Trend_Ratio": trend_ratio,
            "Avg_Proba_Trend": avg_proba_trend,
            "Trend_Score": trend_score,
        })
    stats = pd.DataFrame(rows).sort_values("Trend_Score", ascending=False)
    return stats.reset_index(drop=True)

def get_movies_trend_results() -> dict:
    df, _ = preprocessor()
    df, signal = create_trend_target_movies(df)

    df["release_date"] = pd.to_datetime(df["release_date"])
    df = df.sort_values("release_date")
    split = int(len(df) * 0.8)

    train = df.iloc[:split]
    test = df.iloc[split:]

    X_train = train.drop(columns=["is_trending_future"] + LEAK_COLS, errors="ignore")
    y_train = train["is_trending_future"]
    X_test = test.drop(columns=["is_trending_future"] + LEAK_COLS, errors="ignore")
    y_test = test["is_trending_future"]

    pipeline.fit(X_train, y_train)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    threshold_details = find_threshold_precision_target(y_test, y_proba, target_precision=0.45)
    thr = threshold_details["threshold"]
    y_pred = (y_proba >= thr).astype(int)

    results = test.copy().reset_index(drop=True)
    results["proba"] = y_proba
    results["trend_score"] = (y_proba * 100).round(1)

    watchlist_full = results[results["proba"] >= thr].sort_values("proba", ascending=False)
    trending_genres_df = analyze_trending_genres_movies(X_test, y_pred, y_proba)
    
    # Transformation des dataframes en listes de dictionnaires
    emergent_genres = trending_genres_df.head(10).to_dict(orient="records") if not trending_genres_df.empty else []
    top5_avg_proba = trending_genres_df.nlargest(5, "Avg_Proba").to_dict(orient="records") if not trending_genres_df.empty else []
    top5_trend_ratio = trending_genres_df.nlargest(5, "Trend_Ratio").to_dict(orient="records") if not trending_genres_df.empty else []

    return {
        "metrics": {
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "auc": float(roc_auc_score(y_test, y_proba))
        },
        "trends": {
            "emergent_genres": emergent_genres,
            "top5_avg_proba": top5_avg_proba,
            "top5_trend_ratio": top5_trend_ratio,
            "exploding_movies": watchlist_full.to_dict(orient="records")
        },
        "optimal_threshold": thr,
        "signal_used": signal
    }

if __name__ == "__main__":
    results = get_movies_trend_results()
