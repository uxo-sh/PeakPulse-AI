import os
import glob
import pandas as pd

PROCESSED_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data_collector", "processed")
)


def _find_latest_file(pattern):
    paths = glob.glob(os.path.join(PROCESSED_DIR, pattern))
    if not paths:
        return None
    return sorted(paths)[-1]


def preprocessor():
    """Charge les datasets propres (movies + steam) et renvoie les DataFrames."""
    if not os.path.isdir(PROCESSED_DIR):
        raise FileNotFoundError(f"Dossier de données nettoyées introuvable: {PROCESSED_DIR}")

    movies_file = _find_latest_file("peakpulse_v2_2024*.csv")
    steam_file = _find_latest_file("steam_v2_cleaned_for_ml_*.csv")

    if movies_file is None:
        raise FileNotFoundError("Fichier peakpulse_v2_2024*.csv introuvable dans data_collector/processed")
    if steam_file is None:
        raise FileNotFoundError("Fichier steam_v2_cleaned_for_ml_*.csv introuvable dans data_collector/processed")

    movies_df = pd.read_csv(movies_file, parse_dates=["release_date"], low_memory=False)
    steam_df = pd.read_csv(steam_file, parse_dates=["release_date"], low_memory=False)

    return movies_df, steam_df
