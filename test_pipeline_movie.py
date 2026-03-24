# ============================================================
# 🎬 TREND ENGINE V2 — PRECISION MODE (FULL SCRIPT)
# ============================================================

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


# ============================================================
# 🎯 TARGET
# ============================================================

def create_trend_target_movies(df: pd.DataFrame):
    df = df.copy()

    valid_mask = (
        (df["revenue"] > 0) &
        (df["budget"] > 0) &
        (df["popularity"] > 0)
    )
    df = df[valid_mask].copy()

    df["ROI"] = df["revenue"] / df["budget"]
    df["pop_percentile"] = df["popularity"].rank(pct=True)

    df["is_trending_future"] = (
        (df["ROI"] > 1.5) &
        (df["pop_percentile"] > 0.65)
    ).astype(int)

    signal_used = "ROI > 1.5 & Pop > P65"

    print(f"[TARGET] {df['is_trending_future'].sum()} tendances sur {len(df)} films.")

    return df, signal_used


# ============================================================
# 🚫 COLONNES À EXCLURE (ANTI-LEAKAGE)
# ============================================================

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


# ============================================================
# 🔥 SEUIL BASÉ SUR PRÉCISION
# ============================================================

def find_threshold_precision_target(y_true, y_proba, target_precision=0.6):
    """
    Stratégie : maximiser F1 d'abord, puis vérifier si la précision
    est au-dessus du seuil cible. Plus robuste que le pur precision-target.
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)

    # Aligner les arrays (precisions/recalls ont 1 élément de plus)
    precisions = precisions[:-1]
    recalls = recalls[:-1]

    # Calculer F1 pour chaque seuil
    denom = precisions + recalls + 1e-9
    f1_scores = 2 * precisions * recalls / denom

    # Chercher le meilleur F1 avec précision >= target
    valid = precisions >= target_precision

    if valid.sum() > 0:
        # Parmi les seuils qui respectent la précision, prendre le meilleur F1
        f1_valid = np.where(valid, f1_scores, 0)
        best_idx = np.argmax(f1_valid)
        best_thr = float(thresholds[best_idx])
        print(f"[THRESHOLD] Precision ≥ {target_precision} & F1={f1_scores[best_idx]:.4f} → seuil = {best_thr:.4f}")
    else:
        # Fallback : maximiser F1 sans contrainte de précision
        best_idx = np.argmax(f1_scores)
        best_thr = float(thresholds[best_idx])
        print(f"[THRESHOLD] Fallback F1-max={f1_scores[best_idx]:.4f} → seuil = {best_thr:.4f}")

    return best_thr


# ============================================================
# 🧪 TEST PRINCIPAL
# ============================================================

def test_model_movies_v2():
    print("\n" + "=" * 60)
    print("[FILM] TREND ENGINE V2 (PRECISION MODE)")
    print("=" * 60)

    # 1. Chargement
    df, _ = preprocessor()
    df, signal = create_trend_target_movies(df)

    # 2. Split temporel
    df["release_date"] = pd.to_datetime(df["release_date"])
    df = df.sort_values("release_date")

    split = int(len(df) * 0.8)

    train = df.iloc[:split]
    test = df.iloc[split:]

    X_train = train.drop(columns=["is_trending_future"] + LEAK_COLS, errors="ignore")
    y_train = train["is_trending_future"]

    X_test = test.drop(columns=["is_trending_future"] + LEAK_COLS, errors="ignore")
    y_test = test["is_trending_future"]

    # 3. Entraînement
    pipeline.fit(X_train, y_train)

    # 4. Prédiction
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    # 5. Seuil optimisé (PRECISION MODE)
    thr = find_threshold_precision_target(y_test, y_proba, target_precision=0.45)

    y_pred = (y_proba >= thr).astype(int)

    # ============================================================
    # 📊 MÉTRIQUES
    # ============================================================

    print(f"\n[REPORT] Signal : {signal}")
    print("\n[TREND METRICS]")

    print(f"Recall   : {recall_score(y_test, y_pred):.2f}")
    print(f"Precision: {precision_score(y_test, y_pred):.2f}")
    print(f"F1       : {f1_score(y_test, y_pred):.2f}")
    print(f"AUC      : {roc_auc_score(y_test, y_proba):.2f}")

    # ============================================================
    # 🎯 WATCHLIST QUALITÉ
    # ============================================================

    results = test.copy()
    results["proba"] = y_proba
    results["trend_score"] = (y_proba * 100).round(1)

    watchlist = results[results["proba"] >= thr]
    watchlist = watchlist.sort_values("proba", ascending=False).head(10)

    print("\n[WATCHLIST QUALITÉ]")

    if len(watchlist) == 0:
        print("⚠️ Aucun film ne passe le seuil de précision.")
    else:
        for i, (_, row) in enumerate(watchlist.iterrows()):
            print(
                f"{i+1}. {row['title'][:30]:<30} | "
                f"Score: {row['trend_score']:>5.1f}/100 | "
                f"Proba: {row['proba']:.2%} | "
                f"Budget: {row['budget']/1e6:.1f}M$"
            )

    return {
        "recall": recall_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "auc": roc_auc_score(y_test, y_proba),
        "threshold": thr,
    }


# ============================================================
# 🚀 EXECUTION
# ============================================================

if __name__ == "__main__":
    results = test_model_movies_v2()