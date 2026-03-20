import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureEngineeringGames(BaseEstimator, TransformerMixin):
    
    def __init__(self, epsilon=1e-6):
        self.epsilon = epsilon
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        if not hasattr(self, 'columns_'):
            raise ValueError("Le transformeur doit être 'fit' avant transformation")
        
        X = self._validate_input(X).copy()
        X = self._create_core_features(X)
        X = self._create_tag_features(X)
        X = self._log_normalization(X)
        X = self._create_hybrid_flags(X)
        X = self._final_cleanup(X)
        
        return X
    
    def _validate_input(self, X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("L'entrée doit être un pandas DataFrame")
        return X
    
    def _create_core_features(self, X):
        if {"positive", "negative"}.issubset(X.columns):
            total_reviews = X["positive"] + X["negative"] + self.epsilon
            X["review_quality_ratio"] = X["positive"] / total_reviews
        
        if {"owners", "days_since_release"}.issubset(X.columns):
            X["owners_per_day"] = X["owners"] / (X["days_since_release"] + 1)
        
        return X
    
    def _create_tag_features(self, X):
        if {"tag_density", "tag_entropy"}.issubset(X.columns):
            X["tag_score"] = X["tag_density"] * X["tag_entropy"]
        
        return X
    
    def _log_normalization(self, X):
        log_cols = ["owners", "price", "days_since_release"]
        
        for col in log_cols:
            if col in X.columns:
                X[f"log_{col}"] = np.log1p(np.clip(X[col], a_min=0, a_max=None))
        
        return X
    
    def _create_hybrid_flags(self, X):
        # Crée un flag pour identifier les jeux avec des genres hybrides (ex: roguelike + deckbuilder, survival + crafting, cozy + farming)
        if {"has_roguelike_deckbuilder", "has_survival_crafting", "has_cozy_farming"}.issubset(X.columns):
            X["has_hybrid_genre"] = (
                X["has_roguelike_deckbuilder"] | 
                X["has_survival_crafting"] | 
                X["has_cozy_farming"]
            ).astype(int)
        
        return X
    
    def _final_cleanup(self, X):
        cols_to_drop = ["app_id", "release_date", "name"]
        cols_to_drop = [c for c in cols_to_drop if c in X.columns]
        
        return X.drop(columns=cols_to_drop, errors="ignore")


# ========== FEATURE ENGINEERING POUR FILMS ==========
class FeatureEngineeringMovies(BaseEstimator, TransformerMixin):
    
    def __init__(self, epsilon=1e-6):
        self.epsilon = epsilon
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        if not hasattr(self, 'columns_'):
            raise ValueError("Le transformeur doit être 'fit' avant transformation")
        
        X = self._validate_input(X).copy()
        X = self._handle_time_features(X)
        X = self._create_ratios(X)
        X = self._create_profitability_features(X)
        X = self._create_business_flags(X)
        X = self._log_normalization(X)
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
        
        if "release_date" in X.columns:
            month = X["release_date"].dt.month.fillna(1)
            X["month_sin"] = np.sin(2 * np.pi * month / 12)
            X["month_cos"] = np.cos(2 * np.pi * month / 12)
        
        if {"popularity", "days_since_release"}.issubset(X.columns):
            X["popularity_per_day"] = X["popularity"] / (X["days_since_release"] + 1)
        
        return X
    
    def _create_ratios(self, X):
        if {"revenue", "budget"}.issubset(X.columns):
            X["roi"] = X["revenue"] / (X["budget"] + 1)
            X["profit"] = X["revenue"] - X["budget"]
        
        if {"vote_average", "avg_user_rating"}.issubset(X.columns):
            X["sentiment_gap"] = np.abs(X["vote_average"] - X["avg_user_rating"])
        
        if {"revenue", "runtime"}.issubset(X.columns):
            X["efficiency_ratio"] = X["revenue"] / (X["runtime"] + 1)
        
        return X
    
    def _create_profitability_features(self, X):
        if {"revenue", "budget"}.issubset(X.columns):
            X["is_profitable"] = (X["revenue"] > X["budget"]).astype(int)
            X["profit_ratio"] = np.where(
                X["revenue"] > 0,
                (X["revenue"] - X["budget"]) / X["revenue"],
                0
            )
        
        return X
    
    def _create_business_flags(self, X):
        if {"budget", "revenue"}.issubset(X.columns):
            X["is_blockbuster"] = (
                (X["budget"] > 1e7) & (X["revenue"] > 1e8)
            ).astype(int)
        
        if {"vote_average", "popularity"}.issubset(X.columns):
            X["cult_classic"] = (
                (X["vote_average"] > 7.5) & (X["popularity"] < 20)
            ).astype(int)
        
        if {"vote_average"}.issubset(X.columns):
            X["high_rated"] = (X["vote_average"] > 7.0).astype(int)
        
        return X
    
    def _log_normalization(self, X):
        log_cols = ["budget", "revenue", "popularity", "vote_count"]
        
        for col in log_cols:
            if col in X.columns:
                X[f"log_{col}_eng"] = np.log1p(np.clip(X[col], a_min=0, a_max=None))
        
        return X
    
    def _create_additional_features(self, X):
        if {"budget", "vote_average"}.issubset(X.columns):
            X["budget_rating_interaction"] = X["budget"] * X["vote_average"]
        
        if {"vote_count", "popularity"}.issubset(X.columns):
            X["engagement_intensity"] = X["vote_count"] * X["popularity"]
        
        if {"vote_average", "avg_user_rating"}.issubset(X.columns):
            avg_rating_normalized = X["avg_user_rating"].fillna(5) * 2  # 5/5 → 10/10
            X["quality_score"] = (
                X["vote_average"] * 0.6 + avg_rating_normalized * 0.4
            )
        
        return X
    
    def _final_cleanup(self, X):
        cols_to_drop = ["release_date", "id", "title"]
        cols_to_drop = [c for c in cols_to_drop if c in X.columns]
        
        return X.drop(columns=cols_to_drop, errors="ignore")
