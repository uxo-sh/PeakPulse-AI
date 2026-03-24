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
        best_idx = int(np.argmax(f1_valid))
        best_thr = float(thresholds[best_idx])
        best_f1  = float(f1_scores[best_idx])
        print(f"[THRESHOLD] Precision ≥ {target_precision} & F1={best_f1:.4f} → seuil = {best_thr:.4f}")
    else:
        # Fallback : maximiser F1 sans contrainte de précision
        best_idx = int(np.argmax(f1_scores))
        best_thr = float(thresholds[best_idx])
        best_f1  = float(f1_scores[best_idx])
        print(f"[THRESHOLD] Fallback F1-max={best_f1:.4f} → seuil = {best_thr:.4f}")

    return {
        "threshold": best_thr,
        "f1": best_f1,
        "precisions": precisions,
        "recalls": recalls,
        "thresholds": thresholds,
    }


# ============================================================
# 🔮 ANALYSE DES GENRES TENDANCE — MOVIES
# ============================================================

def analyze_trending_genres_movies(
    X_test: pd.DataFrame,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> pd.DataFrame:
    """
    Analyse les genres par probabilité moyenne et ratio de prédictions tendance.
    Identique à analyze_trending_genres() dans le pipeline games,
    adapté aux colonnes has_* issues du feature engineering movies.

    Genres attendus :
        has_drama, has_comedy, has_action, has_adventure, has_thriller,
        has_romance, has_horror, has_science_fiction, has_crime,
        has_animation, has_fantasy, has_mystery, has_family, has_documentary

    Retourne :
        pd.DataFrame : stats avec colonnes Genre, Count, Avg_Proba,
                       Trend_Ratio, Avg_Proba_Trend, Trend_Score.
                       Trié par Trend_Score décroissant.
    """
    print(f"\n{'='*60}")
    print("🔮 ANALYSE DES GENRES TENDANCE — FILMS")
    print(f"{'='*60}")

    empty_df = pd.DataFrame(columns=[
        "Genre", "Count", "Avg_Proba", "Trend_Ratio",
        "Avg_Proba_Trend", "Trend_Score"
    ])

    try:
        genre_cols = [c for c in X_test.columns if c.startswith("has_")]
        if not genre_cols:
            print("⚠️  Aucune colonne has_XXX trouvée dans X_test.")
            print("    → Vérifier que LEAK_COLS ne filtre pas les has_*")
            return empty_df

        print(f"📌 {len(genre_cols)} genres détectés\n")

        df          = X_test.copy()
        df["pred"]  = y_pred
        df["proba"] = y_proba

        rows = []
        for col in genre_cols:
            sub = df[df[col] == 1]
            if len(sub) == 0:
                continue
            count           = len(sub)
            avg_proba       = sub["proba"].mean()
            trend_ratio     = sub["pred"].mean()
            trend_sub       = sub[sub["pred"] == 1]
            avg_proba_trend = trend_sub["proba"].mean() if len(trend_sub) > 0 else 0.0
            trend_score     = avg_proba * np.log1p(count)
            rows.append({
                "Genre":           col.replace("has_", "").replace("_", " ").title(),
                "Count":           count,
                "Avg_Proba":       avg_proba,
                "Trend_Ratio":     trend_ratio,
                "Avg_Proba_Trend": avg_proba_trend,
                "Trend_Score":     trend_score,
            })

        stats     = pd.DataFrame(rows).sort_values("Trend_Score", ascending=False)
        max_score = stats["Trend_Score"].max()

        print("🏆 TOP 10 GENRES ÉMERGENTS:")
        print(f"{'Rang':<5}│{'Genre':<22}│{'Count':>6}│{'Proba moy':>10}│{'% Tendance':>11}│ Score")
        print("─" * 68)
        for i, (_, r) in enumerate(stats.head(10).iterrows()):
            nb_f = int(r["Trend_Score"] / (max_score / 5)) if max_score > 0 else 0
            bar  = "🔥" * min(5, nb_f)
            print(
                f"{i+1:<5}│{r['Genre']:<22}│{r['Count']:>6.0f}│"
                f"{r['Avg_Proba']:>10.4f}│{r['Trend_Ratio']:>10.2%} │ {bar}"
            )

        print("\n📈 DÉTAILS DES 3 MEILLEURS GENRES:\n")
        for i, (_, r) in enumerate(stats.head(3).iterrows()):
            print(f"  {i+1}️⃣  {r['Genre'].upper()}")
            print(f"     • Films dans ce genre       : {r['Count']:.0f}")
            print(f"     • Proba tendance moyenne    : {r['Avg_Proba']:.4f} ({r['Avg_Proba']*100:.2f}%)")
            print(f"     • % prédits tendance        : {r['Trend_Ratio']:.2%}")
            print(f"     • Proba moy (prédits tend.) : {r['Avg_Proba_Trend']:.4f}")
            print(f"     • Score tendance            : {r['Trend_Score']:.4f}\n")

        print("⭐ TOP 5 PAR PROBABILITÉ MOYENNE:")
        print(f"{'Rang':<5}│{'Genre':<22}│{'Proba moy':>10}")
        print("─" * 42)
        for i, (_, r) in enumerate(stats.nlargest(5, "Avg_Proba").iterrows()):
            print(f"{i+1:<5}│{r['Genre']:<22}│{r['Avg_Proba']:>10.4f}")

        print("\n💰 TOP 5 PAR % PRÉDIT TENDANCE:")
        print(f"{'Rang':<5}│{'Genre':<22}│{'% Tendance':>11}")
        print("─" * 42)
        for i, (_, r) in enumerate(stats.nlargest(5, "Trend_Ratio").iterrows()):
            print(f"{i+1:<5}│{r['Genre']:<22}│{r['Trend_Ratio']:>10.2%}")

        return stats.reset_index(drop=True)

    except Exception as e:
        print(f"⚠️  Erreur analyse genres : {e}")
        return empty_df


# ============================================================
# 🧪 TEST PRINCIPAL
# ============================================================

def test_model_movies_v2() -> dict:
    """
    Test du modèle sur les films.
    Retourne un dict complet de statistiques et DataFrames,
    à l'image de ce qui se fait pour les jeux.
    """
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
    threshold_details = find_threshold_precision_target(y_test, y_proba, target_precision=0.45)
    thr = threshold_details["threshold"]

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

    results = test.copy().reset_index(drop=True)
    results["proba"] = y_proba
    results["trend_score"] = (y_proba * 100).round(1)

    # On retourne tous les films potentiellement en tendance
    watchlist_full = results[results["proba"] >= thr].sort_values("proba", ascending=False)
    watchlist_top10 = watchlist_full.head(10)

    print("\n[WATCHLIST QUALITÉ]")

    if len(watchlist_top10) == 0:
        print("⚠️ Aucun film ne passe le seuil de précision.")
    else:
        for i, (_, row) in enumerate(watchlist_top10.iterrows()):
            title = str(row.get('title', 'N/A'))[:30]
            budget = row.get('budget', 0) / 1e6
            print(
                f"{i+1}. {title:<30} | "
                f"Score: {row['trend_score']:>5.1f}/100 | "
                f"Proba: {row['proba']:.2%} | "
                f"Budget: {budget:.1f}M$"
            )

    # ============================================================
    # 🔮 GENRES TENDANCE
    # ============================================================

    trending_genres_df = analyze_trending_genres_movies(X_test, y_pred, y_proba)

    # Valeurs de retour enrichies pour utilisation externe
    return {
        "recall":            float(recall_score(y_test, y_pred)),
        "precision":         float(precision_score(y_test, y_pred)),
        "f1":                float(f1_score(y_test, y_pred)),
        "auc":               float(roc_auc_score(y_test, y_proba)),
        "optimal_threshold": thr,
        "threshold_details": threshold_details,
        "exploding_movies":  watchlist_full,
        "trending_genres":   trending_genres_df,
        "y_proba":           y_proba,
        "y_pred":            y_pred,
        "y_test":            y_test,
        "X_test":            X_test,
        "signal_used":       signal
    }


# ============================================================
# 🚀 EXECUTION
# ============================================================

if __name__ == "__main__":
    results = test_model_movies_v2()