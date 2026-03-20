import pandas as pd
import os
from datetime import datetime
import numpy as np
from clean_data import (
    clean_numeric_column, validate_dataframe_ids, 
    calculate_days_since_release, validate_date_column,
    create_tag_flags
)

RAW_DIR = "../data_collector/raw"
PROCESSED_DIR = "../data_collector/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

print("=" * 60)
print("PREPROCESSING JEUX STEAM - Chargement et nettoyage des données brutes")
print("=" * 60)

# ========== 1. CHARGEMENT DES DATASETS BRUTS ==========
print("\n1. Chargement des datasets bruts...")
games = pd.read_csv(f"{RAW_DIR}/games.csv")
categories = pd.read_csv(f"{RAW_DIR}/t-games-categories.csv")
tags = pd.read_csv(f"{RAW_DIR}/t-games-tags.csv")

# ========== 2. COPIE ET NETTOYAGE DE BASE ==========
print("2. Nettoyage de base...")
df = games.copy()

# ========== 3. FUSION DES CATÉGORIES ==========
print("3. Fusion avec les catégories officielles...")
cat_pivot = categories.pivot_table(
    index="app_id",
    columns="categories",
    aggfunc="size",
    fill_value=0
).reset_index()
cat_pivot.columns = ["app_id"] + [f"cat_{c.replace(' ', '_').replace('-', '_')}" for c in cat_pivot.columns[1:]]
df = df.merge(cat_pivot, on="app_id", how="left")

# Créer des flags booléens simples basés sur les catégories
df["is_multiplayer"] = df.get("cat_Multi_player", 0).fillna(0).astype(int) > 0
df["is_coop"] = (
    (df.get("cat_Online_Co_op", 0).fillna(0).astype(int) > 0) |
    (df.get("cat_Co_op", 0).fillna(0).astype(int) > 0)
)
df["is_vr"] = (
    (df.get("cat_VR_Only", 0).fillna(0).astype(int) > 0) |
    (df.get("cat_VR_Supported", 0).fillna(0).astype(int) > 0)
)
df["is_controller"] = (
    (df.get("cat_Full_controller_support", 0).fillna(0).astype(int) > 0) |
    (df.get("cat_Partial_Controller_Support", 0).fillna(0).astype(int) > 0)
)

# ========== 4. FUSION DES TAGS ==========
print("4. Fusion avec les tags...")
tags_group = tags.groupby("app_id").apply(
    lambda g: pd.Series({
        "tag_density": g["tag_frequencies"].sum() / len(g) if len(g) > 0 else 0,
        "tag_entropy": -(g["tag_frequencies"] / g["tag_frequencies"].sum() * np.log2(g["tag_frequencies"] / g["tag_frequencies"].sum() + 1e-10)).sum() if g["tag_frequencies"].sum() > 0 else 0,
        "top_5_tags": list(g.nlargest(5, "tag_frequencies")["tags"]) if len(g) > 0 else []
    })
).reset_index()

df = df.merge(tags_group, on="app_id", how="left")

# ========== 5. COMPTAGES SIMPLES DE TAGS ==========
print("5. Création de flags pour tags populaires...")
popular_tags = [
    "Indie", "Action", "Adventure", "RPG", "Strategy", "Simulation", 
    "Casual", "Puzzle", "Horror", "Multiplayer", "Co-op", "Singleplayer"
]

def count_popular_tags(tags_list, popular_list):
    if not isinstance(tags_list, list):
        return 0
    return sum(1 for tag in tags_list if tag in popular_list)

df["num_popular_tags"] = df["top_5_tags"].apply(lambda x: count_popular_tags(x, popular_tags))

# Flags simples pour tags populaires
for tag in popular_tags:
    df[f"has_{tag.lower().replace(" ", "_").replace("-", "_")}"] = df["top_5_tags"].apply(
        lambda x: tag in x if isinstance(x, list) else False
    )

# ========== 6. NETTOYAGE DES COLONNES NUMÉRIQUES ==========
print("6. Nettoyage des colonnes numériques...")
df["owners"] = (df["min_owners"] + df["max_owners"]) / 2
df["total_reviews"] = df["positive"] + df["negative"]
df["score_ratio"] = df["positive"] / (df["total_reviews"] + 1)
df["release_date"] = validate_date_column(df["release_date"])
df["days_since_release"] = calculate_days_since_release(df["release_date"])
df["price"] = clean_numeric_column(df["price"], fill_value=0)

# ========== 7. CALCULS SIMPLES DE PRÉTRAITEMENT ==========
print("7. Calculs de prétraitement...")
df["is_free"] = (df["price"] == 0).astype(int)
df["name_length"] = df["name"].str.len()
df["has_hltb"] = df["hltb_single"].notna().astype(int)
df["review_count"] = df["total_reviews"]

# ========== 8. SÉLECTION DES COLONNES FINALES ==========
print("8. Sélection des colonnes finales...")

tag_flags = [f'has_{t.lower().replace(" ", "_").replace("-", "_")}' for t in popular_tags]

final_cols = [
    "app_id", "name", "release_date", "price", "owners", "positive", "negative",
    "score_ratio", "days_since_release",
    "tag_density", "tag_entropy", "num_popular_tags",
] + tag_flags + [
    "is_multiplayer", "is_coop", "is_vr", "is_controller",
    "is_free", "name_length", "has_hltb", "review_count"
]

df_final = df[final_cols].dropna(subset=["name", "release_date"])

# ========== 9. EXPORT ==========
print("9. Export du dataset nettoyé...")
output = f"{PROCESSED_DIR}/steam_v2_cleaned_for_ml_{datetime.now():%Y%m%d}.csv"
df_final.to_csv(output, index=False)

print("\n" + "=" * 60)
print(f"✅ SUCCÈS - {df_final.shape[0]} jeux traités")
print(f"📊 Colonnes: {len(final_cols)}")
print(f"💾 Fichier: {output}")
print("=" * 60)
