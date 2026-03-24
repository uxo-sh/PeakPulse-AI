import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

#game
class FeatureEngineeringGames(BaseEstimator, TransformerMixin):
    """
    Feature engineering pour la prédiction de tendance des jeux Steam.

    Corrections apportées vs version précédente :
    ─────────────────────────────────────────────
    PROBLÈME 1 — Redondance tag résolue :
        Avant : tag_score + tag_density + tag_entropy dans le modèle simultanément
                → 60% de l'importance pour 1 seule information
        Après : tag_score conservé + tag_score_per_tag ajouté
                tag_density / tag_entropy restent mais ne sont plus « triplés »

    PROBLÈME 2 — Trop peu de features originales résolu :
        Avant : seulement tag_score + has_hybrid_genre créés ici
        Après : 6 nouvelles features originales ajoutées :
                • price_tier          → catégorie de prix (0=gratuit … 4=premium)
                • tag_score_per_tag   → qualité moyenne par tag
                • name_length_bucket  → discrétisation longueur du nom
                • is_hltb_and_indie   → interaction hltb × indie
                • is_multiplayer_coop → interaction multi × coop (signal fort)
                • genre_diversity     → nb de genres actifs simultanément

    Règle absolue : X ne doit JAMAIS contenir owners, days_since_release,
    positive, negative au moment du transform (supprimés avant pipeline.fit).
    """

    def __init__(self, epsilon: float = 1e-6):
        self.epsilon = epsilon

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = self._validate_input(X).copy()
        X = self._create_tag_features(X)
        X = self._create_price_features(X)
        X = self._create_name_features(X)
        X = self._create_interaction_features(X)
        X = self._create_genre_diversity(X)
        X = self._create_hybrid_flags(X)
        X = self._final_cleanup(X)
        return X

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_input(self, X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("L'entrée doit être un pandas DataFrame")
        return X

    # ------------------------------------------------------------------
    # 1. Features TAG — redondance corrigée
    # ------------------------------------------------------------------

    def _create_tag_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        CORRECTION REDONDANCE :
        Avant : tag_score + tag_density + tag_entropy tous les trois dans le modèle
                = 3 features qui disent la même chose = 60% de l'importance captée
        Après : tag_score = signal combiné, tag_score_per_tag = signal normalisé
                tag_density et tag_entropy restent pour leur signal propre
                mais on n'ajoute plus une 3e combinaison redondante
        """
        if {"tag_density", "tag_entropy"}.issubset(X.columns):
            X["tag_score"] = X["tag_density"] * X["tag_entropy"]

        # Qualité par tag : évite de favoriser les jeux surchargés en tags
        if {"tag_score", "num_popular_tags"}.issubset(X.columns):
            X["tag_score_per_tag"] = (
                X["tag_score"] / (X["num_popular_tags"] + self.epsilon)
            )

        return X

    # ------------------------------------------------------------------
    # 2. Features PRIX
    # ------------------------------------------------------------------

    def _create_price_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Tiers de prix : gratuit / low-cost / moyen / cher / premium.
        Les jeux F2P et les jeux à < 5€ ont des dynamiques de tendance
        très différentes des jeux à 30€+.
        """
        if "price" not in X.columns:
            return X

        conditions = [
            X["price"] == 0,       # gratuit
            X["price"] < 5,        # low-cost
            X["price"] < 15,       # moyen
            X["price"] < 30,       # cher
        ]
        X["price_tier"] = np.select(conditions, [0, 1, 2, 3], default=4)
        return X

    # ------------------------------------------------------------------
    # 3. Features NOM
    # ------------------------------------------------------------------

    def _create_name_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Longueur du nom + discrétisation en 4 buckets.
        Les noms très courts (ex: DOOM, Rust) ou très longs ont des
        patterns de popularité distincts.
        """
        if "name" not in X.columns:
            return X

        X["name_length"] = X["name"].astype(str).str.len()

        X["name_length_bucket"] = pd.cut(
            X["name_length"],
            bins=[0, 5, 15, 35, np.inf],
            labels=[0, 1, 2, 3],
        ).astype(float)

        return X

    # ------------------------------------------------------------------
    # 4. Features d'INTERACTION
    # ------------------------------------------------------------------

    def _create_interaction_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Interactions entre features : capturent des signaux composites
        qu'aucune feature seule ne peut exprimer.

        • is_hltb_and_indie    : jeu indie référencé sur HowLongToBeat
                                  → communauté engagée, fort potentiel tendance
        • is_multiplayer_coop  : multi + coop simultanément
                                  → signal tendance le plus fort dans les résultats
        • is_vr_multiplayer    : VR + multi = niche en forte croissance
        """
        if {"has_hltb", "has_indie"}.issubset(X.columns):
            X["is_hltb_and_indie"] = (
                X["has_hltb"].astype(bool) & X["has_indie"].astype(bool)
            ).astype(int)

        # Détection flexible du nom de colonne multiplayer
        multi_col = next(
            (c for c in ["is_multiplayer", "has_multiplayer"] if c in X.columns),
            None,
        )
        coop_col = next(
            (c for c in ["has_co_op", "has_coop", "is_coop"] if c in X.columns),
            None,
        )
        if multi_col and coop_col:
            X["is_multiplayer_coop"] = (
                X[multi_col].astype(bool) & X[coop_col].astype(bool)
            ).astype(int)

        if "is_vr" in X.columns and multi_col:
            X["is_vr_multiplayer"] = (
                X["is_vr"].astype(bool) & X[multi_col].astype(bool)
            ).astype(int)

        return X

    # ------------------------------------------------------------------
    # 5. Diversité de genres
    # ------------------------------------------------------------------

    def _create_genre_diversity(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Nombre de genres has_XXX actifs.
        Un jeu couvrant plus de genres touche plus d'audiences
        → potentiel de tendance plus large.
        """
        genre_cols = [c for c in X.columns if c.startswith("has_")]
        if genre_cols:
            X["genre_diversity"] = X[genre_cols].sum(axis=1).astype(int)
        return X

    # ------------------------------------------------------------------
    # 6. Flags hybrides
    # ------------------------------------------------------------------

    def _create_hybrid_flags(self, X: pd.DataFrame) -> pd.DataFrame:
        """Genres hybrides émergents spécifiques."""
        hybrid_cols = [
            "has_roguelike_deckbuilder",
            "has_survival_crafting",
            "has_cozy_farming",
        ]
        present = [c for c in hybrid_cols if c in X.columns]
        if present:
            X["has_hybrid_genre"] = X[present].any(axis=1).astype(int)
        return X

    # ------------------------------------------------------------------
    # 7. Nettoyage final
    # ------------------------------------------------------------------

    def _final_cleanup(self, X: pd.DataFrame) -> pd.DataFrame:
        cols_to_drop = ["app_id", "name", "release_date"]
        return X.drop(columns=[c for c in cols_to_drop if c in X.columns])
    
    #MOVIES 

#MOVIES 

class FeatureEngineeringMoviesV2(BaseEstimator, TransformerMixin):
    """
    Feature Engineering orienté PREDICTION FUTURE (no leakage)

    ✔ Rolling Genre Momentum (temporel)
    ✔ Budget intelligence
    ✔ Market saturation
    ✔ Robust content signals
    """

    def __init__(self, current_year=2026):
        self.current_year = current_year
        self.genre_trend = {}

    def fit(self, X, y=None):
        X = X.copy()

        if "release_date" in X.columns:
            X["release_date"] = pd.to_datetime(X["release_date"])
            X = X.sort_values("release_date")

        if y is not None:
            X["target"] = y
            genre_cols = [c for c in X.columns if c.startswith("has_")]

            # 🔥 Rolling trend (NO LEAKAGE)
            for col in genre_cols:
                trend = (
                    X.groupby(X["release_date"].dt.year)[["target", col]]
                    .apply(lambda df: df[df[col] == 1]["target"].mean())
                    .fillna(0)
                )
                self.genre_trend[col] = trend.to_dict()

        return self

    def transform(self, X):
        X = X.copy()

        X = self._time_features(X)
        X = self._budget_features(X)
        X = self._content_features(X)
        X = self._market_features(X)
        X = self._genre_momentum(X)
        X = self._cleanup(X)

        return X

    # ------------------------

    def _time_features(self, X):
        if "release_date" in X.columns:
            X["release_date"] = pd.to_datetime(X["release_date"], errors="coerce")

            X["year"] = X["release_date"].dt.year.fillna(self.current_year)
            X["month"] = X["release_date"].dt.month.fillna(1)

            X["month_sin"] = np.sin(2 * np.pi * X["month"] / 12)
            X["month_cos"] = np.cos(2 * np.pi * X["month"] / 12)

            X["film_age"] = (self.current_year - X["year"]).clip(lower=0)

        return X

    # ------------------------

    def _budget_features(self, X):
        if "budget" in X.columns:
            X["budget"] = X["budget"].fillna(0)

            X["log_budget"] = np.log1p(X["budget"])
            X["budget_bucket"] = pd.cut(
                X["budget"],
                bins=[0, 2e6, 20e6, 100e6, 1e9],
                labels=[0, 1, 2, 3]
            ).astype(float)

            X["is_blockbuster"] = (X["budget"] > 100e6).astype(int)

        return X

    # ------------------------

    def _content_features(self, X):
        if "num_keywords" in X.columns:
            X["num_keywords"] = X["num_keywords"].fillna(0)

        if "num_genres" in X.columns:
            X["num_genres"] = X["num_genres"].fillna(0)

        X["content_complexity"] = np.log1p(
            X["num_keywords"] * X["num_genres"]
        )

        X["keyword_density"] = X["num_keywords"] / (X["num_genres"] + 1)

        return X

    # ------------------------

    def _market_features(self, X):
        """
        Approximation simple : saturation marché
        """
        if "film_age" in X.columns and "num_genres" in X.columns:
            X["market_pressure"] = X["num_genres"] / (X["film_age"].clip(lower=0) + 1)

        return X

    # ------------------------

    def _genre_momentum(self, X):
        if "year" not in X.columns:
            return X

        genre_cols = [c for c in X.columns if c.startswith("has_")]

        for col in genre_cols:
            trend_map = self.genre_trend.get(col, {})

            X[f"momentum_{col}"] = X.apply(
                lambda row: trend_map.get(row["year"], 0) * row[col],
                axis=1
            )

        return X

    # ------------------------

    def _cleanup(self, X):
        drop_cols = [
            # Leakage direct
            "revenue", "ROI", "popularity",
            "vote_count", "vote_average",
            "avg_user_rating", "num_ratings", "num_unique_users",
            # Dérivés post-release
            "log_revenue", "log_popularity", "log_vote_count",
            # Biais inflation/historique
            "budget", "days_since_release",
            # Inutiles pour le modèle
            "id", "title", "release_date",
            # Encodés en features dérivées (film_age, month_sin/cos)
            "year", "month",
        ]

        X = X.drop(columns=[c for c in drop_cols if c in X.columns], errors="ignore")
        X = X.select_dtypes(include=["number", "bool"])
        X = X.fillna(0)

        return X  