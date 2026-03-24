# Architecture du Moteur de Tendance (PeakPulse-AI)

Ce document explique le rôle et la différence entre les différents scripts liés au "Trend Engine" de votre projet. 
Ils sont répartis en trois catégories logiques : l'Exploration, la Production et le Diagnostic.

---

## 1. Le Laboratoire (Les Brouillons d'Exploration)
**Fichiers concernés :** `test_pipeline.py` & `test_pipeline_movie.py`

* **Leur rôle :** C'est le terrain de jeu et d'expérimentation pour calibrer l'Intelligence Artificielle.
* **Ce qu'ils font :** 
  Ils chargent et préparent les données, effectuent l'entraînement des modèles Machine Learning, et crachent des textes massifs directement dans la console (via des dizaines de `print()`). Le terminal se remplit de matrices de confusion logiques, de rapports de classification textuels et de listes de jeux/films avec des emojis enflammés (🔥).
* **Comment les utiliser :** 
  À lancer *manuellement dans le terminal* par le développeur/data-scientiste `python test_pipeline.py` afin de comprendre visuellement comment réagit le modèle IA. **Ils ne doivent jamais être connectés à l'interface visuelle (UI).**

---

## 2. Le Produit Fini (Les Moteurs en Production)
**Fichiers concernés :** `trend_engine_games.py` & `trend_engine_movies.py`

* **Leur rôle :** Ce sont les vrais "Moteurs" de prédiction officiels de l'application. 
* **Ce qu'ils font :** 
  Ils reprennent l'exacte mécanique mathématique du Laboratoire, mais ils sont purgés de tout affichage terminal (`print()`). À la place, ils nettoient les résultats (suppression des redondances de jeux) et emballent tout proprement sous la forme de **dictionnaires Python**.
  *Exemple de structure :*
  ```python
  {
      "metrics": {"recall": 0.85, "precision": 0.75, "f1": 0.80, "auc": 0.90},
      "trends": {
          "emergent_genres": [...],
          "top5_avg_proba": [...],
          "exploding_games": [...] # Nettoyé de tout doublon
      },
      "optimal_threshold": 0.45
  }
  ```
* **Comment les utiliser :** 
  Ils sont construits pour être **importés par l'Interface UI** (Dashboard, `KpiCard.axaml`, `trendRow.axaml`). L'application appelle silencieusement leurs fonctions (`get_games_trend_results()`, `get_movies_trend_results()`) en arrière-plan et répartit la data sur votre écran.

---

## 3. Le Contrôle Qualité (Les Diagnostics de Tests)
**Fichiers concernés :** `test_appel.py` & `test_appel_movie.py`

* **Leur rôle :** Ce sont vos "Tests Unitaires" en tant que développeur, votre filet de sécurité anti-crash.
* **Ce qu'ils font :** 
  Plutôt que d'avoir à lancer tout le visuel pour tester que tout fonctionne, ces scripts appellent silencieusement les fichiers de Production (`trend_engine_...`) et font une liste de vérifications automatiques. Ils vérifient par exemple : *"Est-ce que le fichier ne me renvoie pas une erreur ?", "Est-ce qu'il me donne bien un Dictionnaire ?", "Est-ce que le F1-score est bien décimal ?", "La liste fait-elle bien moins de 20 jeux ?"*
* **Comment les utiliser :** 
  À chaque fois que vous modifiez l'algorithme "deep-down" (l'IA), vous ouvrez votre terminal et tapez `python test_appel.py`. Si le terminal vous affiche **✅ 100% PASS**, vous savez que vous pouvez envoyer cette mise à jour en production les yeux fermés sans faire planter l'interface UI de vos utilisateurs.

---
### 💡 Résumé du Flux de travail idéal :
1. J'expérimente dans mon **Laboratoire** (`test_pipeline.py`).
2. Je trouve la bonne formule. Je la recopie "au propre" dans mon **Moteur de Production** (`trend_engine.py`).
3. Je valide que la formule ne casse aucun format de données avec mon script de **Diagnostic** (`test_appel.py`).
4. Je laisse l'**Interface UI** consommer le Moteur sereinement.
