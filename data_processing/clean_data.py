# Nettoyage

import pandas as pd
import numpy as np
import ast
from datetime import datetime


def parse_list_from_json(json_str):
    """Parse une chaîne JSON représentant une liste."""
    try:
        parsed = ast.literal_eval(json_str)
        return parsed if isinstance(parsed, list) else []
    except:
        return []


def parse_keywords(keywords_json_str):
    """Parse et extrait les noms des keywords depuis JSON."""
    try:
        keywords_list = ast.literal_eval(keywords_json_str)
        return [item['name'] for item in keywords_list if isinstance(item, dict) and 'name' in item]
    except:
        return []


def parse_genres(genres_json_str):
    """Parse et extrait les noms des genres depuis JSON."""
    try:
        genres_list = ast.literal_eval(genres_json_str)
        return [item['name'] for item in genres_list if isinstance(item, dict) and 'name' in item]
    except:
        return []


def clean_numeric_column(series, fill_value=0):
    """Convertit une colonne en numérique et remplit les valeurs manquantes."""
    return pd.to_numeric(series, errors='coerce').fillna(fill_value)


def validate_dataframe_ids(df, id_column):
    """Valide et nettoie la colonne ID d'un dataframe."""
    if id_column not in df.columns:
        return df
    
    df[id_column] = pd.to_numeric(df[id_column], errors='coerce')
    df = df.dropna(subset=[id_column])
    df[id_column] = df[id_column].astype(int)
    return df


def calculate_days_since_release(date_series):
    """Calcule le nombre de jours depuis la date de sortie jusqu'à aujourd'hui."""
    return (datetime.now() - date_series).dt.days


def create_genre_flags(genres_list, popular_genres):

    flags = {}
    for genre in popular_genres:
        flags[f'has_{genre.lower().replace(" ", "_")}'] = (
            genre in genres_list if isinstance(genres_list, list) else False
        )
    return flags


def create_tag_flags(tags_list, popular_tags):

    flags = {}
    for tag in popular_tags:
        flags[f'has_{tag.lower().replace(" ", "_")}'] = (
            tag in tags_list if isinstance(tags_list, list) else False
        )
    return flags


def handle_missing_values_columns(df, columns_config):
# valeur manquante
    for col, fill_val in columns_config.items():
        if col in df.columns:
            df[col] = df[col].fillna(fill_val)
    return df


def remove_duplicates(df, subset=None, keep='first'):
    """Supprime les doublons dans le dataframe."""
    return df.drop_duplicates(subset=subset, keep=keep)


def validate_date_column(series, errors='coerce'):
    """Convertit une colonne en datetime et gère les erreurs."""
    return pd.to_datetime(series, errors=errors)
