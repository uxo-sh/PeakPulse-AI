import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator , TransFormerMixin

#Games
class FeatureEngeneeringGames(BaseEstimator,TransFormerMixin):
    def __init__(self, e=1e-6):
        self.e = e
    def fit(self, X ,y= None):
        self.columns = set(X.columns)
        return self
    
    def transform(self ,X):
        check_is_filled(self,"columns_")

        X = self._validate_input(X).copy()
        X = self.__create_core_features(X)
        X = self._create_tag_density(X)
        X = self._normalisation(X)
        X = self._create_binary_feature(X)
        X = self._final_cleanup(X)

        return X

        def _validate_input(self,X):
            if not isinstance(X, pd.DataFrame):
                raise TypeError("L'input doit être un pandas DataFrame")
            return X 

        def _create_core_features(self,X):
            if {"positive","negative"}.issubset(X.columns):
                X["review_ration-rate"] = X["positive"]/(X["positive"] + X["negative"] + self.e)

            if{"owners","day_since_release"}.issubset(X.columns):
                X["owners_per_day"] = X["owners"] / (X["day_since_release"]+1)

            return X 
        
        def _create_tag_density(self,X):
            if{"tag_density","tag_entropy"}.issubset(X.columns):
                X["tag_score"] = X["tag_density"] * X["tag_entropy"] 
            return X 
        
        def _normalisation(self,X):
            log_col = ["owners","price","day_since_release"]

            for col in log_col:
                if col in X.columns:
                    X[f"log_{col}"] = np.log1p(np.clip(X[col], a_min = 0,a_max =None))
            
            return X
        
        def _create_binary_feature(self,X):
            if "price" in X.columns:
                X["is_free"] = (X["price"] == 0).astype(int)
            
            return X

        def _final_cleanup(self,X):
            cols_to_drop = ["app_id","release_date","name"]

            return X.drop(columns = [for c in cols_to_drop if c in X.columns] ,errors="ignore")

#Movies
class FeatureEngeneeringMovies(BaseEstimator,TransFormerMixin):
    def fit(self, X ,y= None):
        self.columns = set(X.columns)
        return self
    
    def transform(self ,X):
        check_is_filled(self,"columns_")

        X = self._validate_input(X).copy()
        X = self._handle_time_feature(X)
        X = self._create_ratio(X)
        X = self._create_business_flags(X)
        X = self._normalisation(X)
        X = self._create_additional_features(X)
        X = self._final_cleanup(X)

        return X

    def _validate_input(self,X):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("L'input doit être un pandas DataFrame")
        return X 
    

    def _handle_time_feature(self,X):
        if "release_date" in X.columns:
            X["release_date"] = pd.to.datetime(X["release_date"] ,errors="coerce")
        
        month = X["release_date"].dt.month.fillna(1)

        X["month_sin"] = np.sin(2 * np.pi * month / 12)
        X["month_cos"] = np.cos(2 * np.pi * month / 12)

        if {"popularity","date_since_release"}.issubset(X.columns):
            X["score_per_day"] = X["popularity"] / (X["day_since_release"]+1)

        return X
    
    def _create_ratio(self,X):
        if{"revenue","budget"}.issubset(X.columns):
            X["roi"] = X["revenue"]/(X["budget"]+1)

        if{"vote_average","avg_user_rating"}.issubset(X.columns):
            X["semtiment_gape"] = np.abs(X["vote_average"]-X["avg_user_rating"])

        if{"revenue","runtime"}.issubset(X.columns) :
            X["effeciency"] = X["revenue"] /(X["runtime"]+1)

        return X

    def _create_business_flags(self,X):
        if{"revenue","budget"}.issubset(X.columns):
            X["is_blockbuster"] = ((X["budget"] > 1e7) & (X["revenue"] > 1e8 )).astype(int)

        if{"vote_average","popularity"};issubset(X.columns): 
            X["cult_classic"] = ((X["vote_average"] > 7.5) & (X["popularity"] < 20)).astype(int)
        
        return X 

    def _normalisation(self,X):
        log_col = ["budget","revenue","popularity","vote_count"]

        for col in log_col:
            if col in X.columns:
                X[f"log_{col}"] = np.log1p(np.clip(X[col], a_min = 0,a_max =None))
        
        return X

    def _create_additional_features(self,X):
        if{"budget","vote_average"}.issubset(X.columns):
            X["budget_x_rating"] = X["budget"] * X["vote_average"]

        if{"vote_count","popularity"}.issubset(X.columns):
            X["engagemnet_intensity"] = X["vote_count"] * X["popularity"]

    def _final_cleanup(self,X):
        cols_to_drop = ["release_date","id","title"]

        return X.drop(columns = [for c in cols_to_drop if c in X.columns] ,errors="ignore")
