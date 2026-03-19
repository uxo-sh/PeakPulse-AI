# Data Collector - Person 1 (Data Engineer)

## Rôle

Collecte automatique de données brutes depuis Steam et TMDb pour alimenter l'IA PeakPulse.

## Données collectées

### Steam (jeux vidéo) - Mode actuel

- **Source principale** : Dataset statique Kaggle (games.csv + tags + categories)
- **Fichiers bruts** : raw/games.csv, raw/t-games-categories.csv, raw/t-games-tags.csv
- **Rassemblement des datasets** : Utilise `prepare_steam_dataset_v2.py` pour merger les 3 fichiers en un seul dataset nettoyé avec features créées.
- **Fichier prêt pour ML** : processed/steam*v2_cleaned_for_ml*\*.csv (généré par prepare_steam_dataset_v2.py)
- **Ancienne collecte** (temps réel) : toujours disponible dans steam_api.py (pour futur usage)

**Processus de rassemblement** :

1. Charger games.csv (données de base des jeux)
2. Merger avec categories (pivot pour présence/absence de catégories officielles)
3. Merger avec tags (top 5 tags, densité, entropie)
4. Créer features hybrides (ex: roguelike_deckbuilder, survival_crafting)
5. Calculer trend_score_v2 (target pour prédire les tendances)
6. Exporter le dataset final nettoyé

**Colonnes du dataset final** :

- app_id : ID unique Steam
- name : Nom du jeu
- release_date : Date de sortie
- price : Prix
- owners : Nombre moyen d'owners (min_owners + max_owners)/2
- positive, negative : Avis positifs/négatifs
- score_ratio : Ratio positif/total
- days_since_release : Jours depuis sortie
- trend_score_v2 : Score de tendance (target pour ML)
- tag_density, tag_entropy : Métriques des tags
- num_popular_tags : Nombre de tags populaires dans top 5
- has_indie, has_action, has_adventure, has_rpg, has_strategy, has_simulation, has_casual, has_puzzle, has_horror, has_multiplayer, has_early_access, has_free_to_play : Flags booléens pour tags spécifiques
- is_multiplayer, is_coop, is_vr, is_controller : Flags booléens pour catégories officielles
- roguelike_deckbuilder, survival_crafting, cozy_farming : Flags hybrides de genres
- is_free : Jeu gratuit (price == 0)
- name_length : Longueur du nom du jeu
- has_hltb : Présence de données HowLongToBeat
- review_count : Nombre total d'avis
- log_owners, log_days_since_release : Versions log-transformées pour normalisation

### TMDb (films)

- **Source principale** : Dataset Kaggle "The Movies Dataset" (movies_metadata.csv + keywords.csv + ratings.csv + links.csv)
- **Fichiers bruts** : raw/movies_metadata.csv, raw/keywords.csv, raw/ratings.csv, raw/links.csv
- **Rassemblement des datasets** : Utilise `prepare_movies_dataset.py` pour merger les fichiers en un seul dataset nettoyé avec features créées.
- **Fichier prêt pour ML** : processed/movies*cleaned_for_ml*\*.csv (généré par prepare_movies_dataset.py)

**Processus de rassemblement** :

1. Charger movies_metadata.csv (métadonnées : genres, popularity, vote_average, etc.)
2. Merger avec keywords (mots-clés par film)
3. Merger avec ratings (notes utilisateurs via links.csv pour moyennes et comptages)
4. Créer features : genres one-hot, keywords comptage, log transformations, rentabilité, hype, audience cible
5. Calculer trend_score_movies (target pour prédire les tendances)
6. Exporter le dataset final nettoyé

**Mesures anti-bruit** :

- **Gestion des divisions par zéro** : Utilisation de `np.where()` pour éviter les NaN (ex: roi = 0 si budget = 0)
- **Clipping des values** : trend_score_movies limité à [0, 1] pour éviter les outliers extrêmes
- **Seuils statistiques** : Utilisation de percentiles (Q75, médiane) pour flags dynamiques au lieu de seuils fixes
- **Log transformations** : Pour normaliser distributions skewed (popularity, budget, revenue)
- **Handling NaN** : Fillna avec valeurs sensées (0 pour financier, 5 pour ratings utilisateurs)
- **Pondération équilibrée** : Target composée de multiples signaux (popularité, qualité, rentabilité, recence) pour éviter sur-dominance d'une feature

**Colonnes du dataset final** :

- **Identifiants** : id, title, release_date
- **Métriques de production** : budget, revenue, runtime, profit, roi, profit_ratio
- **Métriques TMDB** : popularity, vote_average, vote_count, avg_user_rating, num_ratings, num_unique_users
- **Temporal** : days_since_release
- **Target** : trend_score_movies (score pondéré pour prédire tendances)
- **Rentabilité** : is_profitable, is_high_roi, is_efficient, boxoffice_per_minute, budget_runtime_ratio
- **Qualité** : quality_score, critic_audience_gap, high_engagement
- **Hype & Momentum** : is_hotly_anticipated, early_success_ratio, hype_score
- **Diversité créative** : num_genres, num_keywords, genre_diversity_flag, is_crossover_genre
- **Audience cible** : family_friendly, adult_focused, niche_appeal
- **Flags hybrides** : is_blockbuster, high_rated, cult_classic
- **Log transformations** : log_popularity, log_budget, log_revenue, log_vote_count
- **Genres** : has_drama, has_comedy, has_action, has_adventure, has_thriller, has_romance, has_horror, has_science_fiction, has_crime, has_animation, has_fantasy, has_mystery, has_family, has_documentary

## Scripts principaux

### prepare_steam_dataset_v2.py (dans data_processing/)

- Rassemble les 3 datasets bruts Steam en un seul fichier ML-ready
- Génère features et target
- Lance avec : `python prepare_steam_dataset_v2.py` (depuis data_processing/)

### prepare_movies_dataset.py (dans data_processing/)

- Rassemble les datasets films (metadata, keywords, ratings) en un seul fichier ML-ready
- Génère features et target pour tendances films
- Lance avec : `python prepare_movies_dataset.py` (depuis data_processing/)

### steam_api.py (2.0)

- `SteamCollector.download_community_app_list()` : Télécharge et filtre le dump
- `SteamCollector.collect_sample_games(limit=200)` : Collecte détails + joueurs pour 200 jeux
- `SteamCollector.get_current_players(appid)` : Joueurs en ligne

### movies_api.py (2.0)

- `MovieCollector.collect_sample_movies()` : Films connus
- `MovieCollector.collect_recent_or_keyword_movies(keyword, max_results)` : Films par mot-clé

### Tests (2.0)

- `test_steam.py` : Lance collecte Steam complète
- `test_movie.py` : Lance collecte films

## Lancement (2.0)

```bash
# Depuis racine projet
.venv/bin/python data_collector/test_steam.py
.venv/bin/python data_collector/test_movie.py
```

## Remarques pour Person 2 (Data Processing)

- **Datasets finaux** :
  - Jeux : processed/steam*v2_cleaned_for_ml*\*.csv (~60k lignes, 39 colonnes)
  - Films : processed/movies*cleaned_for_ml*\*.csv (~45k lignes, 56 colonnes avec 31 nouvelles features optimisées)
- **Targets** : trend_score_v2 (jeux) et trend_score_movies (films) - scores composites pondérés pour prédire popularité/tendance
- **Features** : 100% numériques/booléennes (pas de texte ou listes), optimisées pour ML avec mesures anti-bruit
- **Transformations** : Log normalization pour distributions skewed, seuils statistiques (percentiles) pour flags dynamiques
- **Prêt pour entraînement ML** : Pas de NaN critiques, pas de divisions par zéro, clipping des outliers, pondérations équilibrées
- **Cas d'usage** : Prédiction régression (trend_score), classification (trending vs. non-trending), clustering multi-domaines (jeux + films)

## Prochaines étapes

- Nettoyer tags (regrouper en catégories ML)
- Calculer features (growth, engagement)
- Passer à Person 3 (Trend Analysis)
