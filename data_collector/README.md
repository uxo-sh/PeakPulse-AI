# Data Collector - Person 1 (Data Engineer)

## Rôle
Collecte automatique de données brutes depuis Steam et TMDb pour alimenter l'IA PeakPulse.

## Données collectées

### Steam (jeux vidéo)
- **Source** : Dump communautaire GitHub (jsnli/steamappidlist)
- **Fréquence** : Quotidienne (mises à jour automatiques)
- **Fichiers** :
  - `raw/steam_app_list_latest.json/csv` : Liste complète des ~150k apps (filtrée : jeux seulement, pas DLC/etc.)
  - `raw/steam_sample_details_*.csv` : Échantillon de 200 jeux avec détails complets

**Colonnes Steam** :
- appid : ID unique Steam
- name : Nom du jeu
- genres : Liste des genres (ex: ["Action", "Adventure"])
- tags : Liste des tags communautaires (ex: ["Roguelike", "Indie"])
- release_date : Date de sortie
- current_players : Joueurs en ligne actuels
- collected_at : Timestamp de collecte

### TMDb (films)
- **Source** : API OMDb (gratuite, 1000 requêtes/jour)
- **Fichiers** : `raw/movies_*.csv` (si collecté)

**Colonnes Films** :
- title, year, genre, imdb_rating, plot, poster, collected_at

## Scripts principaux

### steam_api.py
- `SteamCollector.download_community_app_list()` : Télécharge et filtre le dump
- `SteamCollector.collect_sample_games(limit=200)` : Collecte détails + joueurs pour 200 jeux
- `SteamCollector.get_current_players(appid)` : Joueurs en ligne

### movies_api.py
- `MovieCollector.collect_sample_movies()` : Films connus
- `MovieCollector.collect_recent_or_keyword_movies(keyword, max_results)` : Films par mot-clé

### Tests
- `test_steam.py` : Lance collecte Steam complète
- `test_movie.py` : Lance collecte films

## Lancement
```bash
# Depuis racine projet
.venv/bin/python data_collector/test_steam.py
.venv/bin/python data_collector/test_movie.py
```

## Remarques pour Person 2 (Data Processing)
- Données brutes dans `raw/` : prêtes pour nettoyage et feature engineering
- Pas de données manquantes critiques (tout est collecté)
- Pour tendances : focus sur `current_players`, `tags`, `genres`, `release_date`
- Éviter re-collecte fréquente (rate limits)

## Prochaines étapes
- Nettoyer tags (regrouper en catégories ML)
- Calculer features (growth, engagement)
- Passer à Person 3 (Trend Analysis)