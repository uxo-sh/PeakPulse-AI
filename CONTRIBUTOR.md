# Guide des contributeurs - PeakPulse AI

Bienvenue dans PeakPulse AI ! Ce guide explique la structure du projet, les rôles, les bonnes pratiques et les pièges à éviter.

---

## 📋 Structure du projet

```
ProjetL3_PeakPulse_AI/
├── data_collector/          # Person 1 (Data Engineer) - Collecte & rassemblement
│   ├── raw/                 # Datasets bruts Kaggle (Steam + Films)
│   ├── processed/           # Datasets ML-ready finaux
│   ├── steam_api.py         # Collecte temps réel Steam (legacy)
│   ├── movies_api.py        # Collecte temps réel Films (legacy)
│   └── README.md            # Documentation des données
├── data_processing/         # Person 2 (Data Processing) - Nettoyage & ML features
│   ├── prepare_steam_dataset_v2.py      # Rassemble & prépare jeux
│   ├── prepare_movies_dataset.py        # Rassemble & prépare films
│   └── clean_data.py        # Nettoyage supplémentaire (optionnel)
├── ml_models/               # Person 3 (ML Engineer) - Entraînement & prédictions
│   └── model.py             # Modèles ML (régression, classification, clustering)
├── trend_engine/            # Person 4 (Trend Analyst) - Détection tendances
│   └── trend_detector.py    # Logique tendances temps réel
├── api/                     # Person 5 (API Developer) - Backend API
│   └── app.py               # Flask/FastAPI pour exposer modèles
├── dashboard/               # Person 6 (Frontend) - Dashboard
│   └── Program.cs           # C# / .NET frontend
├── README.md                # Vue d'ensemble projet
├── requirements.txt         # Dépendances Python
└── CONTRIBUTOR.md           # Ce fichier

```

---

## 👥 Rôles et responsabilités

### **Person 1 - Data Engineer** (`data_collector/`)

**Responsabilités** :

- ✅ Collecte données brutes (Kaggle, APIs Steam, TMDb)
- ✅ Rassemble datasets (merges, joins)
- ✅ Stocke dans `raw/` (pas de nettoyage ML)
- ✅ Maintient `data_collector/README.md`

**Machine** : Rassembler 3+ datasets Steam bruts → 1 fichier merged  
**NE PAS** : Créer features ML, transformer colonnes, normaliser (responsabilité Person 2)

---

### **Person 2 - Data Processing** (`data_processing/`)

**Responsabilités** :

- ✅ Nettoie datasets (parse JSON, handle NaN, encoding)
- ✅ Crée features ML (one-hot encoding, log transform, flags hybrides)
- ✅ Génère target (trend_score_v2, trend_score_movies)
- ✅ Produit fichiers finaux dans `processed/`
- ✅ Documenter features dans `data_collector/README.md`

**Machine** : Input = `raw/*.csv` → Output = `processed/*_cleaned_for_ml_*.csv` (toutes colonnes numériques/booléennes)  
**NE PAS** : Entraîner modèles, faire prédictions, modifier logique métier (responsabilité Person 3+)

---

### **Person 3 - ML Engineer** (`ml_models/`)

**Responsabilités** :

- ✅ Entraîne modèles (regression, classification, clustering)
- ✅ Valide avec train/test split
- ✅ Sauvegarde modèles entrainés
- ✅ Documente hyperparamètres et performance

**Machine** : Input = `data_processing/*.csv` → Output = modèles.pkl + métriques  
**NE PAS** : Modifier features (responsabilité Person 2), créer features ad-hoc dans ML (utiliser Person 2)

---

### **Person 4 - Trend Analyst** (`trend_engine/`)

**Responsabilités** :

- ✅ Intègre modèles ML pour détections temps réel
- ✅ Implémenter logique tendance (sliding windows, momentum)
- ✅ Expose résultats pour API

**Machine** : Input = modèles ML + données temps réel → Output = trend alerts/scores  
**NE PAS** : Créer features, entraîner modèles (responsabilité Person 3)

---

### **Person 5 - API Developer** (`api/`)

**Responsabilités** :

- ✅ Crée endpoints pour exposer trend_detector
- ✅ Gère authentification, rate limiting
- ✅ Documente API (Swagger, OpenAPI)

**Machine** : Input = trend_detector → Output = API REST/GraphQL  
**NE PAS** : Faire logique métier dans API (conserver dans trend_engine)

---

### **Person 6 - Frontend** (`dashboard/`)

**Responsabilités** :

- ✅ Affiche données et prédictions via dashboard
- ✅ Gère visualisations (charts, tables)
- ✅ Integration avec API (Person 5)

**Machine** : Input = API endpoints → Output = UI interactif  
**NE PAS** : Logique métier dans frontend (rester dans trends/API)

---

## ✅ Bonnes pratiques globales

### **Data Pipeline**

1. **Nommage fichiers** :
   - Raw : `{source}_{type}.csv` (ex: `games.csv`, `movies_metadata.csv`)
   - Processed : `{type}_cleaned_for_ml_{YYYYMMDD}.csv` (ex: `movies_cleaned_for_ml_20260318.csv`)
   - Modèles : `{type}_model_{version}.pkl` (ex: `trend_model_v1.pkl`)

2. **Documentation** :
   - Chaque script a docstring expliquant entrées/sorties
   - Chaque dataset a colonne-par-colonne dans README.md
   - Commenter **pourquoi**, pas **quoi** (code clair suffit pour quoi)

3. **Versionnage** :
   - Pas de breaking changes sans accord groupe
   - Nouvelles colonnes = nouvelle version dataset
   - Exemple : `steam_v1.csv` → `steam_v2.csv` (v2 inclut features tag_density, etc.)

4. **Validation** :
   - Avant export : `len(df)` > 0, pas de NaN dans colonnes critiques
   - Print stats : `print(f"✅ {len(df)} lignes générées")`
   - Toujours `dropna(subset=[colonnes_crit])` avant export

---

### **Conventions de code Python**

- **Indentation** : 4 espaces
- **Imports** : `pandas as pd`, `numpy as np`, `datetime`
- **Nommage** :
  - Variables numériques : snake_case (`num_genres`, `log_budget`)
  - Flags booléens : `is_*`, `has_*` (`is_profitable`, `has_horror`)
  - Functions : verbe_objet (`parse_genres()`, `count_keywords()`)
- **Docstrings** : Format NumPy/Google
  ```python
  def calculate_roi(revenue, budget):
      """Calcule ROI.

      Args:
          revenue (float): Recettes en dollars
          budget (float): Budget en dollars

      Returns:
          float: Retour sur investissement (ex: 2.0 = +100%)
      """
      return (revenue - budget) / budget if budget > 0 else 0
  ```

---

## ⚠️ Pièges à éviter

### **Person 1 (Data Engineer)**

❌ **NE PAS** : Nettoyer/transformer dans `raw/`

```python
# MAUVAIS
games['owners'] = games['owners'].fillna(0)  # ← C'est du nettoyage ML
games['rating_score'] = games['positive'] / (games['positive'] + games['negative'])  # ← Feature ML
```

✅ **À FAIRE** : Rassembler bruts, laisser nettoyage à Person 2

```python
# BON
games = pd.read_csv('raw/games.csv')
categories = pd.read_csv('raw/t-games-categories.csv')
merged = games.merge(categories, on='app_id', how='left')
merged.to_csv('processed/steam_raw_merged.csv')
```

❌ **NE PAS** : Créer datasets incomplets

```python
# MAUVAIS - colonnes manquantes
df = df[['id', 'title']]  # ← À minima : id, title, date, ratings
```

✅ **À FAIRE** : Tous les champs bruts présents

```python
# BON - toutes colonnes du source
df_final = df[['id', 'title', 'release_date', 'budget', 'revenue',
               'popularity', 'vote_average', 'vote_count', 'genres', 'keywords']]
```

---

### **Person 2 (Data Processing)**

❌ **NE PAS** : Créer features sans handlerdivision par zéro

```python
# MAUVAIS - peut générer inf/NaN
df['roi'] = (df['revenue'] - df['budget']) / df['budget']
df['rating_avg'] = df['positive'] / df['total']  # Si total = 0 → inf
```

✅ **À FAIRE** : Gérer cas limites

```python
# BON
df['roi'] = np.where(df['budget'] > 0,
                     (df['revenue'] - df['budget']) / df['budget'],
                     0)
df['rating_avg'] = np.where(df['total'] > 0,
                            df['positive'] / df['total'],
                            0.5)  # Défaut neutre
```

❌ **NE PAS** : Features hardcodées sans paramètres

```python
# MAUVAIS - magique, difficile à maintenir
df['is_blockbuster'] = df['budget'] > 10000000  # Pourquoi 10M?
```

✅ **À FAIRE** : Documenter seuils, utiliser statistiques

```python
# BON - explicite
BLOCKBUSTER_BUDGET_MIN = 10_000_000  # 10M$ threshold (industry standard)
df['is_blockbuster'] = (df['budget'] > BLOCKBUSTER_BUDGET_MIN) & \
                       (df['revenue'] > 100_000_000)  # ET revenue >100M pour validation
```

❌ **NE PAS** : Garder colonnes non-numérique dans output

```python
# MAUVAIS - ML ne peut pas utiliser listes
df_final = df[['title', 'top_5_tags', 'genres_list', 'trend_score']]  # ← listes JSON
```

✅ **À FAIRE** : One-hot encodage ou flags

```python
# BON - toutes numériques/booléennes
df_final = df[['title', 'has_action', 'has_drama', 'num_tags', 'trend_score']]
```

❌ **NE PAS** : Ignorer multicollinéarité

```python
# MAUVAIS - redondance totale
df_final = df[['revenue', 'log_revenue', 'profit', 'roi', 'is_profitable']]
# → revenue, log_revenue, profit, roi = parfaitement corrélés
```

✅ **À FAIRE** : Garder une représentation par concept

```python
# BON - choisir une par catégorie
# Rentabilité : garder SOIT revenue SOIT log_revenue SOIT roi
df_final = df[['log_revenue', 'roi', 'is_profitable']]  # 3 concepts différents
```

---

### **Person 3 (ML Engineer)**

❌ **NE PAS** : Créer features à la volée dans ML

```python
# MAUVAIS - feature engineering dans modèle
X = dataset.copy()
X['new_score'] = X['col1'] * X['col2'] / X['col3']  # ← Doit être dans Person 2
model.fit(X)
```

✅ **À FAIRE** : Utiliser features préparées par Person 2

```python
# BON - features déjà prêtes
X = dataset[['popularity', 'vote_average', 'budget', 'revenue', 'has_action']]
model.fit(X, y)
```

❌ **NE PAS** : Surapprentissage sur petits datasets

```python
# MAUVAIS - pas de validation cross
model.fit(df)  # Toutes les données = pas de test set
y_pred = model.predict(df)  # Prédictions sur training = illusion
```

✅ **À FAIRE** : Validation rigoureuse

```python
# BON
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model.fit(X_train, y_train)
score = model.score(X_test, y_test)  # Évaluation réelle
```

---

### **Global**

❌ **NE PAS** : Committer datasets dans Git

```bash
# MAUVAIS
git add data_collector/processed/*.csv
git commit -m "Add datasets"
```

✅ **À FAIRE** : Gitignore + scripts de génération

```bash
# BON
# .gitignore :
data_collector/raw/*.csv
data_collector/processed/*.csv

# README.md inclut : python data_processing/prepare_*.py
```

❌ **NE PAS** : Renommer colonnes sans coordination

```python
# MAUVAIS - casse Person 3 & 4
df.rename(columns={'popularity': 'pop_score'})  # ↓ ML model expects 'popularity'
```

✅ **À FAIRE** : Annoncer changements, versionner

```python
# BON - si renommage nécessaire :
# 1. Notifier groupe
# 2. Créer nouvelle version dataset
# 3. Mettre à jour modèles
df_v2 = df.rename(columns={'popularity': 'popularity_score'})  # v2
```

---

## 📝 Checklist avant commit

**Data Engineer (Person 1)** ✅ COMPLÉTÉ :

- [x] Tous les fichiers bruts présents en `raw/` (games.csv, t-games-categories.csv, t-games-tags.csv, movies_metadata.csv, keywords.csv, ratings.csv, links.csv)
- [x] Pas de transformation ML appliquée
- [x] README.md à jour avec sources + colonnes
- [x] `print()` final : nombre lignes exportées (60,852 Steam + 45,438 Films)

**Data Processing (Person 2)** ✅ PARTIELLEMENT COMPLÉTÉ (prepare\_\*.py créés, mais scripts spécialisés manquants) :

- [x] Input CSV charge sans erreur : `pd.read_csv(..., low_memory=False)`
- [x] Aucune colonne NaN critique
- [x] 100% colonnes numériques/booléennes (pas de JSON, listes, strings) - 39 colonnes Steam, 56 colonnes Films
- [x] Target (trend_score) entre 0-1 (clipped ou normalized)
- [x] Test rapide : `df.dtypes` = all float64/int64/bool
- [x] README.md : colonnes documentées (colonne-par-colonne + utilité ML)
- [x] `print()` final : nombre lignes + colonnes ajoutées
- [ ] Créer `clean_data.py` : Script de nettoyage générique (handle outliers, duplicates, encoding)
- [ ] Créer `tag_classifier.py` : Classification automatique des tags Steam (mapping tags → catégories)
- [ ] Implémenter mapping tags Steam (tag → catégorie principale)
- [ ] Créer système de catégories hiérarchiques pour tags
- [ ] Ajouter calculs features avancés (si nécessaire)
- [ ] Tests unitaires pour fonctions de nettoyage

**ML Engineer (Person 3)** ⏳ EN ATTENTE :

- [ ] Train/test split effectué
- [ ] Performance > baseline (cas échéant)
- [ ] Features du dataset Person 2 utilisées (pas de création ad-hoc)
- [ ] Modèle sauvegardé avec version
- [ ] Documente hyperparamètres et résultats dans `ml_models/README.md`

**Trend Analyst (Person 4)** ⏳ EN ATTENTE :

- [ ] Modèle ML chargé sans erreur
- [ ] Tests temps réel sur données récentes
- [ ] Alerts/scores générés correctement
- [ ] Documente logique tendances dans `trend_engine/README.md`

**API Developer (Person 5)** ⏳ EN ATTENTE :

- [ ] Endpoints testés avec curl/Postman
- [ ] Documentation Swagger générée
- [ ] Rate limiting activé
- [ ] Créé `api/README.md` avec exemples

**Frontend (Person 6)** ⏳ EN ATTENTE :

- [ ] Dashboard affiche données API correctement
- [ ] Pas d'erreur console
- [ ] Tests UI sur navigateurs clés

---

## 🚀 Workflow typique

### **Ajouter nouvel dataset Films**

1. **Person 1** : Place `raw/new_films_dataset.csv`
2. **Person 2** :
   ```bash
   cd data_processing
   python prepare_movies_dataset.py  # Met à jour processed/movies_cleaned_for_ml_*.csv
   ```
3. **Person 3** : Retrain modèles avec nouvelles colonnes
4. **Person 4** : Test trend_detector avec new model
5. **Person 5** : Redeploy API
6. **Person 6** : Update dashboard

### **Ajouter nouvelles features**

1. **Person 2** : Ajoute logique dans `prepare_*.py`
2. **Person 2** : Régenère dataset : `python prepare_*.py`
3. **Person 2-3** : Notifie Person 3 de nouvelles colonnes
4. **Person 3** : Retrain modèles (sinon risque de features inutilisées)
5. **Test** : `X.shape[1]` = nombre colonnes attendues

---

## 📞 Questions fréquentes

**Q: "Puis-je modifier une colonne existante ?"**  
R: Oui, mais :

- Notifie le groupe (peut casser dépendances Person 3+)
- Crée nouvelle version dataset (`v2`, `v3`)
- Retrain modèles obligatoire

**Q: "Combien de colonnes = max ?"**  
R: Pas de max strict, mais :

- > 50 colonnes = risque multicollinéarité
- Utiliser feature selection (correlation, importance) avant ML

**Q: "Je dois créer une feature urgente !"**  
R: Demander à Person 2. Workflow :

1. Décris feature (définition, utilité)
2. Person 2 ajoute à `prepare_*.py`
3. Régénère dataset
4. Person 3 retrain

**Q: "Mes modèles ont baisse performance ?"**  
R: Checklist :

- [ ] Dataset régénéré récemment ? → Oui : peut être nouvelles données
- [ ] Features changées ? → Person 2 à notifier
- [ ] Train/test split ? → Éviter data leakage
- [ ] Hyperparamètres ? → Essayer grid search

---

## 📚 Documentation par domaine

- **Données** : `data_collector/README.md`
- **Features ML** : `data_collector/README.md` (colonnes 1-56 films + 1-39 jeux)
- **API** : À créer en `api/README.md`
- **Modèles** : À créer en `ml_models/README.md`
- **Trends** : À créer en `trend_engine/README.md`

---

## 💬 Questions ?

- Consultez README.md principal
- Vérifiez checklist au-dessus
- Posez questions dans Issues/Discussions

**Merci de maintenir la qualité du projet ! 🎯**
