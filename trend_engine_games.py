import numpy as np
import pandas as pd
from ml_models.model import pipeline
from data_processing.preprocessor import preprocessor
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    f1_score,
    recall_score,
    precision_score
)

LEAK_COLS = [
    "owners",
    "days_since_release",
    "score_ratio",
    "is_free",
    "trend_score",
    "positive",
    "negative",
    "review_count",
]

TARGET_COL = "is_trending_future"

def create_trend_target(train_df: pd.DataFrame, df: pd.DataFrame) -> tuple:
    df = df.copy()
    owners_threshold = train_df["owners"].quantile(0.70)
    df[TARGET_COL] = (df["owners"] > owners_threshold).astype(int)
    return df, owners_threshold

def find_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> dict:
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    denom = precisions + recalls + 1e-9
    f1_scores = np.where(denom == 0, 0, 2 * precisions * recalls / denom)
    best_idx = int(np.argmax(f1_scores[:-1]))
    best_thr = float(thresholds[best_idx])
    best_f1 = float(f1_scores[best_idx])
    return {
        "threshold": best_thr,
        "f1": best_f1,
        "precisions": precisions.tolist(),
        "recalls": recalls.tolist(),
        "thresholds": thresholds.tolist(),
    }

def predict_exploding_games(test_raw: pd.DataFrame, y_test: pd.Series, y_proba: np.ndarray, top_n: int = 20) -> pd.DataFrame:
    candidates = test_raw.copy().reset_index(drop=True)
    candidates["proba_tendance"] = y_proba
    mask = y_test.values == 0
    watchlist = candidates[mask]
    
    # Suppression des doublons basés sur le nom pour éviter la redondance dans l'UI
    if "name" in watchlist.columns:
        watchlist = watchlist.drop_duplicates(subset=["name"])
        
    watchlist = watchlist.nlargest(top_n, "proba_tendance").reset_index(drop=True)
    return watchlist

def analyze_trending_genres(X_test: pd.DataFrame, y_pred: np.ndarray, y_proba: np.ndarray) -> pd.DataFrame:
    empty_df = pd.DataFrame(columns=["Genre", "Count", "Avg_Proba", "Trend_Ratio", "Avg_Proba_Trend", "Trend_Score"])
    genre_cols = [c for c in X_test.columns if c.startswith("has_")]
    if not genre_cols:
        return empty_df

    df = X_test.copy()
    df["pred"] = y_pred
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

def get_games_trend_results() -> dict:
    _, steam_df = preprocessor()
    steam_sorted = steam_df.sort_values("days_since_release").reset_index(drop=True)
    split_idx = int(len(steam_sorted) * 0.80)
    train_raw = steam_sorted.iloc[:split_idx].copy()
    test_raw = steam_sorted.iloc[split_idx:].copy()

    train_raw, owners_thr = create_trend_target(train_raw, train_raw)
    test_raw, _ = create_trend_target(train_raw, test_raw)

    X_train = train_raw.drop(columns=[TARGET_COL] + LEAK_COLS, errors="ignore")
    y_train = train_raw[TARGET_COL]
    X_test = test_raw.drop(columns=[TARGET_COL] + LEAK_COLS, errors="ignore")
    y_test = test_raw[TARGET_COL]

    pipeline.fit(X_train, y_train)
    
    proba_matrix = pipeline.predict_proba(X_test)
    y_proba = proba_matrix[:, 1]
    
    threshold_details = find_optimal_threshold(y_test.values, y_proba)
    optimal_thr = threshold_details["threshold"]
    y_pred = (y_proba >= optimal_thr).astype(int)

    trending_genres_df = analyze_trending_genres(X_test, y_pred, y_proba)
    exploding_games_df = predict_exploding_games(test_raw, y_test, y_proba, top_n=20)
    
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
            "exploding_games": exploding_games_df.to_dict(orient="records")
        },
        "optimal_threshold": optimal_thr
    }

if __name__ == "__main__":
    results = get_games_trend_results()
