from data_processing.preprocessor import preprocessor
from trend_engine.trend_detector import FeatureEngineeringMovies, FeatureEngineeringGames
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier


def _prepare_ml_data(df, target_col, drop_cols=None, exclude_cols=None):
    if drop_cols is None:
        drop_cols = []
    if exclude_cols is None:
        exclude_cols = []

    if target_col not in df.columns:
        raise ValueError(f"Colonne cible introuvable: {target_col}")

    X = df.drop(columns=drop_cols + [target_col] + exclude_cols, errors="ignore")
    X = X.select_dtypes(include=["number"]).fillna(0)
    y = df[target_col].astype(int).fillna(0)

    return train_test_split(X, y, test_size=0.2, random_state=42)


def _train_evaluate(X_train, X_test, y_train, y_test):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model.score(X_test, y_test)


def main():
    movies_df, steam_df = preprocessor()

    print(f"Preprocessing : movies={len(movies_df)}, steam={len(steam_df)}")

    movies_fe = FeatureEngineeringMovies().fit(movies_df).transform(movies_df)
    games_fe = FeatureEngineeringGames().fit(steam_df).transform(steam_df)

    print(f"Movies FE: {movies_fe.shape}")
    print(f"Games FE: {games_fe.shape}")

    # MOVIES
    if "is_blockbuster" in movies_fe.columns:

        #  On enlève TOUT ce qui leak
        movie_exclude = [
        "budget",
        "revenue",
        "popularity",
        "vote_count",
        "engagement_intensity",
        "popularity_per_day"
    ]

        mX_train, mX_test, my_train, my_test = _prepare_ml_data(
            movies_fe,
            target_col="is_blockbuster",
            drop_cols=["id", "title"],
            exclude_cols=movie_exclude
        )

        score = _train_evaluate(mX_train, mX_test, my_train, my_test)
        print(f"Movie accuracy (clean) = {score:.3f}")

    # GAMES
    target_col = None
    if "is_trending" in games_fe.columns:
        target_col = "is_trending"
    elif "is_free" in games_fe.columns:
        target_col = "is_free"

    if target_col is not None:

        #  enlever les colonnes leak explicites pour l'objectif future-trend
        game_exclude = ["price", "log_price", "score_ratio", "owners", "days_since_release"]

        gX_train, gX_test, gy_train, gy_test = _prepare_ml_data(
            games_fe,
            target_col=target_col,
            drop_cols=["app_id", "name"],
            exclude_cols=game_exclude
        )

        score = _train_evaluate(gX_train, gX_test, gy_train, gy_test)
        print(f"Game accuracy ({target_col}) = {score:.3f}")
    else:
        print("Aucun target de jeu disponible (is_trending/is_free non trouvé). Vérifiez le preprocess.")


if __name__ == "__main__":
    main()