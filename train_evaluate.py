"""Module pour analyser et visualiser les features pour prise de décision."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from data_processing.preprocessor import preprocessor
from trend_engine.trend_detector import FeatureEngineeringMovies, FeatureEngineeringGames


def get_features_summary():
    movies_df, steam_df = preprocessor()

    movies_fe = FeatureEngineeringMovies().fit(movies_df).transform(movies_df)
    games_fe = FeatureEngineeringGames().fit(steam_df).transform(steam_df)

    return movies_fe, games_fe


# =========================
# 🎯 GRAPHE 1 : QUALITÉ vs SUCCÈS
# =========================
def plot_quality_vs_success_movies(df):
    plt.figure()
    plt.scatter(df["vote_average"], df["popularity"])
    plt.xlabel("Qualité (vote_average)")
    plt.ylabel("Popularité")
    plt.title("Films : Qualité vs Succès")
    plt.show()


def plot_quality_vs_success_games(df):
    plt.figure()
    plt.scatter(df["score_ratio"], df["owners"])
    plt.xlabel("Qualité (score_ratio)")
    plt.ylabel("Nombre de joueurs (owners)")
    plt.title("Jeux : Qualité vs Succès")
    plt.show()


# =========================
# 📈 GRAPHE 2 : CROISSANCE TEMPORELLE
# =========================
def plot_growth_movies(df):
    plt.figure()
    plt.scatter(df["days_since_release"], df["popularity_per_day"])
    plt.xlabel("Temps depuis sortie")
    plt.ylabel("Popularité par jour")
    plt.title("Films : Croissance dans le temps")
    plt.show()


def plot_growth_games(df):
    plt.figure()
    plt.scatter(df["days_since_release"], df["owners_per_day"])
    plt.xlabel("Temps depuis sortie")
    plt.ylabel("Joueurs par jour")
    plt.title("Jeux : Croissance dans le temps")
    plt.show()


# =========================
# 🏷️ GRAPHE 3 : IMPACT DES GENRES
# =========================
def plot_genre_impact_movies(df):
    genre_cols = [col for col in df.columns if "has_" in col]

    genre_scores = {}
    for col in genre_cols:
        genre_scores[col] = df[df[col] == True]["popularity"].mean()

    plt.figure()
    plt.bar(genre_scores.keys(), genre_scores.values())
    plt.xticks(rotation=90)
    plt.title("Impact des genres sur la popularité (Films)")
    plt.show()


def plot_genre_impact_games(df):
    genre_cols = [col for col in df.columns if "has_" in col]

    genre_scores = {}
    for col in genre_cols:
        genre_scores[col] = df[df[col] == True]["owners"].mean()

    plt.figure()
    plt.bar(genre_scores.keys(), genre_scores.values())
    plt.xticks(rotation=90)
    plt.title("Impact des genres sur le succès (Jeux)")
    plt.show()


# =========================
# 🔥 GRAPHE 4 : CORRÉLATION
# =========================
def plot_correlation(df, name):
    plt.figure()
    corr = df.select_dtypes(include=["number"]).corr()
    sns.heatmap(corr)
    plt.title(f"Corrélation des features - {name}")
    plt.show()


# =========================
# 🚀 MAIN
# =========================
def main():
    try:
        movies_fe, games_fe = get_features_summary()

        # Graphes principaux
        plot_quality_vs_success_movies(movies_fe)
        plot_quality_vs_success_games(games_fe)

        plot_growth_movies(movies_fe)
        plot_growth_games(games_fe)

        plot_genre_impact_movies(movies_fe)
        plot_genre_impact_games(games_fe)

        plot_correlation(movies_fe, "Movies")
        plot_correlation(games_fe, "Games")

    except Exception as e:
        print(f"Erreur : {e}")


if __name__ == "__main__":
    main()