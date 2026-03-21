"""Module pour évaluer et visualiser les features après engineering."""

import pandas as pd
from data_processing.preprocessor import preprocessor
from trend_engine.trend_detector import FeatureEngineeringMovies, FeatureEngineeringGames


def get_features_summary():
    """Récupère et analyse les features après engineering."""
    movies_df, steam_df = preprocessor()

    # Feature engineering
    movies_fe = FeatureEngineeringMovies().fit(movies_df).transform(movies_df)
    games_fe = FeatureEngineeringGames().fit(steam_df).transform(steam_df)

    return movies_fe, games_fe


def display_features_table(df, name, max_rows=10):
    """Affiche un tableau des features avec statistiques."""
    print(f"\n{'='*60}")
    print(f"FEATURES ENGINEERING - {name.upper()}")
    print(f"{'='*60}")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nColonnes disponibles:")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")

    print(f"\nAperçu des premières {max_rows} lignes:")
    print(df.head(max_rows).to_string(index=False))

    print(f"\nStatistiques descriptives:")
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        stats = df[numeric_cols].describe().round(3)
        print(stats.to_string())
    else:
        print("Aucune colonne numérique trouvée.")

    print(f"\nTypes de données:")
    print(df.dtypes.value_counts())


def main():
    """Fonction principale pour afficher les tableaux de features."""
    try:
        movies_fe, games_fe = get_features_summary()

        display_features_table(movies_fe, "Movies")
        display_features_table(games_fe, "Games")

        print(f"\n{'='*60}")
        print("RÉSUMÉ COMPARATIF")
        print(f"{'='*60}")
        print(f"Movies: {movies_fe.shape[0]} échantillons, {movies_fe.shape[1]} features")
        print(f"Games:  {games_fe.shape[0]} échantillons, {games_fe.shape[1]} features")

        # Comparaison des colonnes communes
        common_cols = set(movies_fe.columns) & set(games_fe.columns)
        print(f"Colonnes communes: {len(common_cols)}")
        if common_cols:
            print("Colonnes communes:", ", ".join(sorted(common_cols)))

    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")


if __name__ == "__main__":
    main()