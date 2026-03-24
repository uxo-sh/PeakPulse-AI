"""
Pipeline sklearn dédié aux films (Movies) — Simple Feature Engineering + RandomForest.

Equivalent à ml_models/model.py mais pour les films au lieu de Steam Games.
"""

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.base import BaseEstimator, TransformerMixin

from trend_engine.trend_detector import FeatureEngineeringMovies


class FeatureEngineeringMoviesSimple(BaseEstimator, TransformerMixin):
    """
    Feature engineering simple pour les films :
    - Conserve les colonnes numériques
    - Remplit les NaN avec 0
    - Prêt pour RandomForest
    """
    
    def __init__(self):
        pass
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        
        # Garder SEULEMENT les colonnes numériques ou boolean
        numeric_cols = X.select_dtypes(include=['number', 'bool']).columns.tolist()
        X = X[numeric_cols]
        
        # Remplir les NaN avec 0
        X = X.fillna(0)
        
        return X


pipeline = Pipeline(steps=[
    (
        "feature_engeneering",
        FeatureEngineeringMovies(),
    ),
    (
        "model",
        RandomForestClassifier(
            # ── Volume d'arbres ────────────────────────────────────────
            n_estimators=300,           # 300 > 200 > 100 : plus stable, variance réduite

            # ── Contrôle de la profondeur ──────────────────────────────
            max_depth=20,               # Assez profond pour capter les interactions
                                        # sans mémoriser le train set

            # ── Contrôle du sur-apprentissage ─────────────────────────
            min_samples_leaf=5,         # Bon équilibre généralisation / sensibilité
            min_samples_split=10,       # Évite les splits sur 1-2 exemples

            # ── Diversité des arbres ───────────────────────────────────
            max_features="sqrt",        # Standard classification : sqrt(nb_features)
            max_samples=0.8,            # Bagging : chaque arbre voit 80% du train
                                        # → diversité accrue, moins de surapprentissage

            # ── Gestion du déséquilibre ────────────────────────────────
            class_weight="balanced",    # Critique pour données déséquilibrées
                                        # Poids = n_total / (n_classes × n_class_i)

            # ── Reproductibilité ───────────────────────────────────────
            random_state=42,
            n_jobs=-1,
        ),
    ),
])
