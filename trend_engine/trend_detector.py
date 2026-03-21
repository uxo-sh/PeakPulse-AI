import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


#  GAMES 
class FeatureEngineeringGames(BaseEstimator, TransformerMixin):

    def __init__(self, epsilon=1e-6):
        self.epsilon = epsilon

    def fit(self, X, y=None):
        self.columns_ = X.columns
        return self

    def transform(self, X):
        X = self._validate_input(X).copy()

        X = self._create_core_features(X)
        X = self._create_tag_features(X)
        X = self._log_normalization(X)
        X = self._create_hybrid_flags(X)
        X = self._create_free_feature(X)
        X = self._final_cleanup(X)

        return X

    def _validate_input(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("L'entrée doit être un pandas DataFrame")
        return X

    def _create_core_features(self, X):
        if {"positive", "negative"}.issubset(X.columns):
            total = X["positive"] + X["negative"] + self.epsilon
            X["review_quality_ratio"] = X["positive"] / total

        if {"owners", "days_since_release"}.issubset(X.columns):
            X["owners_per_day"] = X["owners"] / (X["days_since_release"] + 1)

        return X

    def _create_tag_features(self, X):
        if {"tag_density", "tag_entropy"}.issubset(X.columns):
            X["tag_score"] = X["tag_density"] * X["tag_entropy"]
        return X

    def _log_normalization(self, X):
        for col in ["owners", "days_since_release"]:
            if col in X.columns:
                X[f"log_{col}"] = np.log1p(np.clip(X[col], 0, None))
        return X

    def _create_hybrid_flags(self, X):
        if {"has_roguelike_deckbuilder", "has_survival_crafting", "has_cozy_farming"}.issubset(X.columns):
            X["has_hybrid_genre"] = (
                X["has_roguelike_deckbuilder"] |
                X["has_survival_crafting"] |
                X["has_cozy_farming"]
            ).astype(int)
        return X

    def _create_free_feature(self, X):
        """Crée la feature is_free: 1 si price == 0, sinon 0."""
        if "price" in X.columns:
            X["is_free"] = (X["price"] == 0).astype(int)
        return X

    def _final_cleanup(self, X):
        #  IMPORTANT : supprimer price car on prédit is_free
        cols_to_drop = ["app_id", "release_date", "name", "price"]
        return X.drop(columns=[c for c in cols_to_drop if c in X.columns])


#MOVIES 
class FeatureEngineeringMovies(BaseEstimator, TransformerMixin):

    def __init__(self, epsilon=1e-6):
        self.epsilon = epsilon

    def fit(self, X, y=None):
        self.columns_ = X.columns
        return self

    def transform(self, X):
        X = self._validate_input(X).copy()

        X = self._handle_time_features(X)
        X = self._create_safe_features(X)
        X = self._create_business_flags(X)  # target ici
        X = self._create_additional_features(X)
        X = self._final_cleanup(X)

        return X

    def _validate_input(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("L'entrée doit être un pandas DataFrame")
        return X

    def _handle_time_features(self, X):
        if "release_date" in X.columns:
            X["release_date"] = pd.to_datetime(X["release_date"], errors="coerce")
            month = X["release_date"].dt.month.fillna(1)
            X["month_sin"] = np.sin(2 * np.pi * month / 12)
            X["month_cos"] = np.cos(2 * np.pi * month / 12)

        if {"popularity", "days_since_release"}.issubset(X.columns):
            X["popularity_per_day"] = X["popularity"] / (X["days_since_release"] + 1)

        return X

    def _create_safe_features(self, X):
        #  IMPORTANT : PAS de revenue/budget ici
        if {"vote_average", "avg_user_rating"}.issubset(X.columns):
            X["sentiment_gap"] = np.abs(X["vote_average"] - X["avg_user_rating"])

        return X

    def _create_business_flags(self, X):
        # Target (on la garde mais on supprimera les sources après)
        if {"budget", "revenue"}.issubset(X.columns):
            threshold = X["revenue"].quantile(0.8)
            X["is_blockbuster"] = (X["revenue"] > threshold).astype(int)
        return X

    def _create_additional_features(self, X):
        if {"vote_count", "popularity"}.issubset(X.columns):
            X["engagement_intensity"] = X["vote_count"] * X["popularity"]

        if {"vote_average", "avg_user_rating"}.issubset(X.columns):
            avg_rating_norm = X["avg_user_rating"].fillna(5) * 2
            X["quality_score"] = X["vote_average"] * 0.6 + avg_rating_norm * 0.4

        return X

    def _final_cleanup(self, X):
        cols_to_drop = ["release_date", "id", "title", "budget", "revenue", "log_budget", "log_revenue"]
        return X.drop(columns=[c for c in cols_to_drop if c in X.columns])