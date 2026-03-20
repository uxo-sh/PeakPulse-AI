from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

pipeline = Pipeline(steps=[
    ("feature_engeneering",FeatureEngeneeringGame()), // ilay resaka mijery tendance mihitsy
    ("preprocessing",preprocessor), // nom an'ilay preprocessing ataonlisany any 
    ("model",RandomForestClassifier(n_estimators = 100 , max_depth =None,random_state=42))
])