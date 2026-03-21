from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from trend_engine.trend_detector import FeatureEngineeringGames
from data_processing.preprocessor import preprocessor

pipeline = Pipeline(steps=[
    ("feature_engeneering",FeatureEngineeringGames()), # ilay resaka mijery tendance mihitsy
    ("preprocessing",preprocessor), # nom an'ilay preprocessing ataonlisany any 
    ("model",RandomForestClassifier(n_estimators = 100 , max_depth =None,random_state=42))
])