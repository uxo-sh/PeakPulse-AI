import pandas as pd
import os
from datetime import datetime
import numpy as np

RAW_DIR = "../data_collector/raw"
PROCESSED_DIR = "../data_collector/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

print("V2 - Chargement des 3 fichiers...")
games = pd.read_csv(f"{RAW_DIR}/games.csv")
categories = pd.read_csv(f"{RAW_DIR}/t-games-categories.csv")
tags = pd.read_csv(f"{RAW_DIR}/t-games-tags.csv")

# 1. Merge de base
df = games.copy()

# 2. Ajout catégories officielles (presence/absence)
cat_pivot = categories.pivot_table(
    index="app_id",
    columns="categories",
    aggfunc="size",
    fill_value=0
).reset_index()
cat_pivot.columns = ["app_id"] + [f"cat_{c.replace(' ', '_').replace('-', '_')}" for c in cat_pivot.columns[1:]]
df = df.merge(cat_pivot, on="app_id", how="left")

print("Colonnes après merge categories :", df.columns.tolist())

# Plus sûr : fillna(0) + astype(int) + > 0
df["is_multiplayer"] = df["cat_Multi_player"].fillna(0).astype(int) > 0
df["is_coop"]        = (
    (df["cat_Online_Co_op"].fillna(0).astype(int) > 0) |
    (df["cat_Co_op"].fillna(0).astype(int) > 0)
)
df["is_vr"] = (
    (df["cat_VR_Only"].fillna(0).astype(int) > 0) |
    (df["cat_VR_Supported"].fillna(0).astype(int) > 0)
)
df["is_controller"] = (
    (df["cat_Full_controller_support"].fillna(0).astype(int) > 0) |
    (df["cat_Partial_Controller_Support"].fillna(0).astype(int) > 0)
)

# 3. Tags : métriques numériques + comptages de tags populaires
tags_group = tags.groupby("app_id").apply(
    lambda g: pd.Series({
        "tag_density": g["tag_frequencies"].sum() / len(g) if len(g) > 0 else 0,
        "tag_entropy": -(g["tag_frequencies"] / g["tag_frequencies"].sum() * np.log2(g["tag_frequencies"] / g["tag_frequencies"].sum() + 1e-10)).sum() if g["tag_frequencies"].sum() > 0 else 0,
        "top_5_tags": list(g.nlargest(5, "tag_frequencies")["tags"]) if len(g) > 0 else []
    })
).reset_index()

df = df.merge(tags_group, on="app_id", how="left")

# Comptages de tags populaires (pour ML)
popular_tags = ["Indie", "Action", "Adventure", "RPG", "Strategy", "Simulation", "Casual", "Puzzle", "Horror", "Shooter", "Platformer", "Racing", "Sports", "Fighting", "Multiplayer", "Co-op", "Singleplayer", "Early Access", "Free to Play", "VR"]

def count_popular_tags(tags_list, popular_list):
    if not isinstance(tags_list, list):
        return 0
    return sum(1 for tag in tags_list if tag in popular_list)

df["num_popular_tags"] = df["top_5_tags"].apply(lambda x: count_popular_tags(x, popular_tags))

# Flags pour tags spécifiques
df["has_indie"] = df["top_5_tags"].apply(lambda x: "Indie" in x if isinstance(x, list) else False)
df["has_action"] = df["top_5_tags"].apply(lambda x: "Action" in x if isinstance(x, list) else False)
df["has_adventure"] = df["top_5_tags"].apply(lambda x: "Adventure" in x if isinstance(x, list) else False)
df["has_rpg"] = df["top_5_tags"].apply(lambda x: "RPG" in x if isinstance(x, list) else False)
df["has_strategy"] = df["top_5_tags"].apply(lambda x: "Strategy" in x if isinstance(x, list) else False)
df["has_simulation"] = df["top_5_tags"].apply(lambda x: "Simulation" in x if isinstance(x, list) else False)
df["has_casual"] = df["top_5_tags"].apply(lambda x: "Casual" in x if isinstance(x, list) else False)
df["has_puzzle"] = df["top_5_tags"].apply(lambda x: "Puzzle" in x if isinstance(x, list) else False)
df["has_horror"] = df["top_5_tags"].apply(lambda x: "Horror" in x if isinstance(x, list) else False)
df["has_multiplayer"] = df["top_5_tags"].apply(lambda x: "Multiplayer" in x if isinstance(x, list) else False)
df["has_early_access"] = df["top_5_tags"].apply(lambda x: "Early Access" in x if isinstance(x, list) else False)
df["has_free_to_play"] = df["top_5_tags"].apply(lambda x: "Free to Play" in x if isinstance(x, list) else False)

# Hybrid genre flags (exemples)
def has_tag(tags_list, keywords):
    if not isinstance(tags_list, list):
        return False
    return any(any(k.lower() in str(t).lower() for k in keywords) for t in tags_list)

df["roguelike_deckbuilder"] = df["top_5_tags"].apply(
    lambda x: has_tag(x, ["Roguelike", "Roguelite"]) and has_tag(x, ["Deckbuilding", "Card Game", "Card Battler"])
)
df["survival_crafting"] = df["top_5_tags"].apply(
    lambda x: has_tag(x, ["Survival"]) and has_tag(x, ["Crafting"])
)
df["cozy_farming"] = df["top_5_tags"].apply(
    lambda x: has_tag(x, ["Farming Sim", "Farming"]) and has_tag(x, ["Cozy", "Relaxing"])
)

# 4. Recalcul trend_score amélioré (on peut pondérer plus les nouveaux signaux)
df["owners"] = (df["min_owners"] + df["max_owners"]) / 2
df["total_reviews"] = df["positive"] + df["negative"]
df["score_ratio"] = df["positive"] / (df["total_reviews"] + 1)
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["days_since_release"] = (datetime.now() - df["release_date"]).dt.days

df["trend_score_v2"] = (
    0.35 * (df["owners"] / df["owners"].max()) +
    0.25 * df["score_ratio"] +
    0.20 * (1 / (df["days_since_release"] / 365 + 1)) +
    0.10 * (df["tag_density"] / df["tag_density"].max()) +
    0.10 * (df["is_multiplayer"].astype(int) * 0.5 + df["is_coop"].astype(int) * 0.3)
)

# Features supplémentaires pour ML
df["is_free"] = (df["price"] == 0).astype(int)
df["name_length"] = df["name"].str.len()
df["has_hltb"] = df["hltb_single"].notna().astype(int)
df["review_count"] = df["total_reviews"]
df["log_owners"] = np.log1p(df["owners"])  # Log pour normaliser la distribution
df["log_days_since_release"] = np.log1p(df["days_since_release"])

# 5. Export
final_cols = [
    "app_id", "name", "release_date", "price", "owners", "positive", "negative",
    "score_ratio", "days_since_release", "trend_score_v2",
    "tag_density", "tag_entropy", "num_popular_tags",
    "has_indie", "has_action", "has_adventure", "has_rpg", "has_strategy", "has_simulation", "has_casual", "has_puzzle", "has_horror", "has_multiplayer", "has_early_access", "has_free_to_play",
    "is_multiplayer", "is_coop", "is_vr", "is_controller",
    "roguelike_deckbuilder", "survival_crafting", "cozy_farming",
    "is_free", "name_length", "has_hltb", "review_count", "log_owners", "log_days_since_release"
]

df_final = df[final_cols].dropna(subset=["name", "release_date"])

output = f"{PROCESSED_DIR}/steam_v2_cleaned_for_ml_{datetime.now():%Y%m%d}.csv"
df_final.to_csv(output, index=False)

print(f"✅ V2 générée : {df_final.shape[0]} lignes")
print("Colonnes ajoutées :", [c for c in df_final.columns if c not in ["app_id", "name", "release_date", "price", "owners", "positive", "negative", "score_ratio", "days_since_release", "trend_score"]])