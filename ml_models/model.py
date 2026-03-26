from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from trend_engine.trend_detector import FeatureEngineeringGames
from data_processing.preprocessor import preprocessor

movies_df, steam_df = preprocessor()

df = steam_df

pipeline = Pipeline(steps=[
    (
        "feature_engeneering",
        FeatureEngineeringGames(),
    ),
    (
        "model",
        RandomForestClassifier(
            # ── Volume d'arbres ────────────────────────────────────────
            n_estimators=300,    # 300 > 200 > 100 : plus stable, variance réduite       

            # ── Contrôle de la profondeur ──────────────────────────────
            max_depth=20,              

            # ── Contrôle du sur-apprentissage ─────────────────────────
            min_samples_leaf=5,       # 5 = bon équilibre généralisation / sensibilité
            min_samples_split=10,      

            # ── Diversité des arbres ───────────────────────────────────
            max_features="sqrt",        
            max_samples=0.8,         # Bagging : chaque arbre voit 80% du train

            # ── Gestion du déséquilibre ────────────────────────────────
            class_weight="balanced",   

            # ── Reproductibilité ───────────────────────────────────────
            random_state=42,
            n_jobs=-1,
        ),
    ),
])