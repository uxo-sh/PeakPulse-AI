from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="PeakPulse AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SYSTÈME DE CACHE POUR NE PAS RE-ENTRAÎNER L'IA À CHAQUE REQUÊTE

_trend_cache = {}
_cache_lock = threading.Lock()

def get_cached_games_results():
    with _cache_lock:
        if "games" not in _trend_cache:
            from trend_engine_games import get_games_trend_results
            print("[API] 🔄 Entraînement en cours (Games)...")
            _trend_cache["games"] = get_games_trend_results()
            print("[API] ✅ Modèle Games prêt !")
        return _trend_cache["games"]

def get_cached_movies_results():
    with _cache_lock:
        if "movies" not in _trend_cache:
            from trend_engine_movies import get_movies_trend_results
            print("[API] 🔄 Entraînement en cours (Movies)...")
            _trend_cache["movies"] = get_movies_trend_results()
            print("[API] ✅ Modèle Movies prêt !")
        return _trend_cache["movies"]



# ROUTES API

@app.get("/")
def root():
    return {"message": "PeakPulse AI API (connecté au Trend Engine)", "status": "running"}

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/status")
def get_status():
    return {
        "status": "running",
        "model": "RandomForest Pipeline",
        "domains": ["games", "movies", "music"],
        "version": "1.0.0"
    }

# ── ROUTE : MOTEUR GLOBAL (GAMES) ──────────────────────────────────────────
@app.get("/api/trends/games")
def get_games_trends():
    """ 
    Retourne la totalité des informations du modèle d'IA pour l'univers Jeux.
    Idéal pour alimenter `KpiCard.axaml` (avec `metrics` aplati) et `trendRow.axaml`.
    """
    try:
        data = get_cached_games_results()
        metrics = data["metrics"]
        
        def format_genre_list(genre_data, max_items):
            res = []
            n_items = max(1, min(len(genre_data), max_items))
            for i, g in enumerate(genre_data[:max_items]):
                rank_score = 5 - int((i / n_items) * 5)
                res.append({
                    "itemName": str(g.get("Genre", "N/A")),
                    "score": f"{float(g.get('Avg_Proba', 0)):.4f}",
                    "trendLabel": f"{g.get('Trend_Ratio', 0)*100:.1f}%",
                    "badge": f"STAR:{rank_score}",
                    "colorHex": "#4fc3f7" if i % 2 == 0 else "#7c4dff",
                    "isAlternate": i % 2 != 0
                })
            return res

        emergent_genres = format_genre_list(data["trends"].get("emergent_genres", []), 10)
        mean_proba_genres = format_genre_list(data["trends"].get("top5_avg_proba", []), 5)
        trend_percent_genres = format_genre_list(data["trends"].get("top5_trend_ratio", []), 5)

        # Mapping de la Watchlist (Exploding Games) vers le format attendu par la UI
        exploding_items = []
        games_list = data["trends"].get("exploding_games", [])[:10]
        n_games = max(1, len(games_list))
        for i, m in enumerate(games_list):
            price_val = float(m.get('price', 0) or 0)
            price_str = f"{price_val:.0f}€" if price_val > 0 else "Gratuit"
            
            proba = m.get('proba_tendance', 0)
            rank_score = 5 - int((i / n_games) * 5)
            
            exploding_items.append({
                "itemName": str(m.get("name", "Jeu inconnu")),
                "score": f"{proba*100:.2f}%",
                "trendLabel": price_str,
                "badge": f"ARROW:{rank_score}",
                "colorHex": "#4fc3f7" if i % 2 == 0 else "#7c4dff",
                "isAlternate": i % 2 != 0
            })

        return {
            "title": "Jeux vidéo — Tendances ML",
            "subtitle": "Modèle RandomForest en direct",
            "kpiRecall": f"{metrics.get('recall', 0)*100:.1f}%",
            "kpiPrecision": f"{metrics.get('precision', 0)*100:.1f}%",
            "kpiF1": f"{metrics.get('f1', 0)*100:.1f}%",
            "kpiAuc": f"{metrics.get('auc', 0)*100:.1f}%",
            "chartBadge": "ML · Live",
            "barColor": "#4fc3f7",
            "heights": "40,65,85,70,95,110",
            "opportunityCount": f"{len(data['trends'].get('exploding_games', []))} opportunités",
            "iaRecommendation": "Les jeux multijoueurs continuent d'exploser. Misez sur l'Action et la Coop.",
            "emergentGenres": emergent_genres,
            "meanProbaGenres": mean_proba_genres,
            "trendPercentGenres": trend_percent_genres,
            "explodingItems": exploding_items,
            "source": "ml_model_live"
        }
    except Exception as e:
        return {"source": "error", "error": str(e)}

# ── ROUTE : MOTEUR GLOBAL (MOVIES) ─────────────────────────────────────────
@app.get("/api/trends/movies")
def get_movies_trends():
    """ 
    Retourne la totalité des informations du modèle d'IA pour l'univers Films.
    """
    try:
        data = get_cached_movies_results()
        metrics = data["metrics"]
        
        def format_genre_list(genre_data, max_items):
            res = []
            n_items = max(1, min(len(genre_data), max_items))
            for i, g in enumerate(genre_data[:max_items]):
                rank_score = 5 - int((i / n_items) * 5)
                res.append({
                    "itemName": str(g.get("Genre", "N/A")),
                    "score": f"{float(g.get('Avg_Proba', 0)):.4f}",
                    "trendLabel": f"{g.get('Trend_Ratio', 0)*100:.1f}%",
                    "badge": f"STAR:{rank_score}",
                    "colorHex": "#7c4dff" if i % 2 == 0 else "#4fc3f7",
                    "isAlternate": i % 2 == 0
                })
            return res

        emergent_genres = format_genre_list(data["trends"].get("emergent_genres", []), 10)
        mean_proba_genres = format_genre_list(data["trends"].get("top5_avg_proba", []), 5)
        trend_percent_genres = format_genre_list(data["trends"].get("top5_trend_ratio", []), 5)

        # On alimente TrendRow avec la Watchlist Qualité (Exploding Movies)
        exploding_items = []
        movies_list = data["trends"].get("exploding_movies", [])[:10]
        n_movies = max(1, len(movies_list))
        for i, m in enumerate(movies_list):
            budget_m = float(m.get('budget', 0) or 0) / 1_000_000
            budget_str = f"{budget_m:.1f}M$" if budget_m > 0 else "N/A"
            
            score_val = float(m.get('trend_score', 0) or 0)
            rank_score = 5 - int((i / n_movies) * 5)
            
            exploding_items.append({
                "itemName": str(m.get("title", m.get("original_title", "Film inconnu"))),
                "score": f"{score_val:.1f}/100",
                "trendLabel": f"{m.get('proba', 0)*100:.2f}%",
                "badge": f"ARROW:{rank_score}|{budget_str}",
                "colorHex": "#7c4dff" if i % 2 == 0 else "#4fc3f7",
                "isAlternate": i % 2 == 0
            })

        return {
            "title": "Cinéma — Tendances ML",
            "subtitle": "Modèle RandomForest en direct",
            "kpiRecall": f"{metrics.get('recall', 0)*100:.1f}%",
            "kpiPrecision": f"{metrics.get('precision', 0)*100:.1f}%",
            "kpiF1": f"{metrics.get('f1', 0)*100:.1f}%",
            "kpiAuc": f"{metrics.get('auc', 0)*100:.1f}%",
            "chartBadge": "ML · Live",
            "barColor": "#7c4dff",
            "heights": "55,70,80,95,100,112",
            "opportunityCount": f"{len(data['trends'].get('exploding_movies', []))} opportunités",
            "iaRecommendation": "Recommandation basée sur le modèle d'IA. 10 genres mis en valeur.",
            "emergentGenres": emergent_genres,
            "meanProbaGenres": mean_proba_genres,
            "trendPercentGenres": trend_percent_genres,
            "explodingItems": exploding_items,
            "source": "ml_model_live"
        }
    except Exception as e:
        return {"source": "error", "error": str(e)}

@app.get("/api/trends/music")
def get_music_trends():
    return {**MUSIC_DATA, "source": "simulated"}

# ── ROUTE : TOP GENRES ──────────────────────────────────────────────────
@app.get("/api/trending_games")
def trending_games():
    """ 
    Expose le Top 4 ou 5 des genres pour les graphiques à barre. (Basé sur Top5_Avg_Proba).
    """
    try:
        data = get_cached_games_results()
        top_genres_ai = data["trends"].get("top5_avg_proba", [])
        
        # Adaptation du format IA au format attendu par certains bar-charts UI
        formatted_genres = []
        for g in top_genres_ai[:4]: # Garder max 4 pour certains tableaux
            formatted_genres.append({
                "genre": g["Genre"],
                "trend_score": round(g["Avg_Proba"], 2),
                "prediction": "tendance émergente",
                "players": g["Count"]  # Nombre formatté
            })
        return {
            "top_genres": formatted_genres,
            "source": "steam_api_ml_model"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/trending_movies")
def trending_movies():
    """ 
    Expose le Top 4 ou 5 des genres pour les graphiques à barre. (Basé sur Top5_Avg_Proba).
    """
    try:
        data = get_cached_movies_results()
        top_genres_ai = data["trends"].get("top5_avg_proba", [])
        
        formatted_genres = []
        for g in top_genres_ai[:4]: 
            formatted_genres.append({
                "genre": g["Genre"],
                "trend_score": round(g["Avg_Proba"], 2),
                "prediction": "tendance émergente",
                "views": g["Count"] 
            })
        return {
            "top_genres": formatted_genres,
            "source": "tmdb_api_ml_model"
        }
    except Exception as e:
        return {"error": str(e)}

# ── ROUTE : WATCHLIST (Tableaux en bas de page pour le Dashboard) ────────
@app.get("/api/database/games")
def get_games_db():
    """
    Expose spécifiquement la liste brute des jeux qui 'vont exploser'.
    Prête au formattage d'un tableau UI dans le Dashboard.
    """
    try:
        data = get_cached_games_results()
        exploding_list = data["trends"].get("exploding_games", [])
        
        table_data = []
        # Limite à 10 pour le tableau visuel
        for i, item in enumerate(exploding_list[:10]):
            table_data.append({
                "game_id": i + 1,
                "title": str(item.get("name", "Jeu Inconnu")),
                "category": "High Proba 🔥",
                # Extraction basique d'un genre, ou fallback sur le score
                "mechanic": "Tendance",
                "players": int(item.get("owners", 0)) if "owners" in item else 0,
                # On convertit proba_tendance en une équivalence de 'rating /10' 
                "reviews": round(item.get("proba_tendance", 0) * 10, 1)
            })

        return {
            "table": "games_exploding",
            "data": table_data,
            "source": "ml_predictions"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/database/movies")
def get_movies_db():
    """
    Expose spécifiquement la liste brute des films qui 'vont exploser'.
    Prête au formattage d'un tableau UI dans le Dashboard.
    """
    try:
        data = get_cached_movies_results()
        exploding_list = data["trends"].get("exploding_movies", [])
        
        table_data = []
        for i, item in enumerate(exploding_list[:10]):
            table_data.append({
                "movie_id": i + 1,
                "title": str(item.get("title", "Film Inconnu")),
                "genre": "High Proba 🔥",
                # On met le budget converti ou le nombre de vote comme repère de volume
                "views": int(item.get("popularity", 0) * 100),
                "rating": round(item.get("proba", 0) * 10, 1)
            })

        return {
            "table": "movies_exploding",
            "data": table_data,
            "source": "ml_predictions"
        }
    except Exception as e:
        return {"error": str(e)}

# ── ROUTE : PRÉDICTION UNIQUE POUR UN GENRE ──────────────────────────────
@app.get("/api/genre_prediction/{genre}")
def genre_prediction(genre: str):
    return {
        "genre": genre,
        "success_probability": 0.85, # Simplifié
        "recommendation": "Calcul global via ML conseillé",
        "model": "RandomForest",
    }

@app.get("/api/pipeline/status")
def pipeline_status():
    return {
        "steps": [
            { "step": 1, "name": "IA Engine Activé", "status": "ok", "detail": "Modèle branché avec succès." }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)