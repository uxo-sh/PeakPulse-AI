from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from trend_engine.trend_detector import FeatureEngineeringMoviesV2

rf = RandomForestClassifier(
    n_estimators=500,
    max_depth=25,
    min_samples_leaf=3,
    min_samples_split=8,
    max_features="sqrt",
    max_samples=0.8,
    class_weight={0:1, 1:2},  # 🔥 pousse la précision
    random_state=42,
    n_jobs=-1
)

model = CalibratedClassifierCV(
    rf,
    method="isotonic",  # meilleur que sigmoid pour RF
    cv=3
)

pipeline = Pipeline([
    ("features", FeatureEngineeringMoviesV2()),
    ("model", model),
])