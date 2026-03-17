import os
import requests
import pandas as pd
import time
import random
from datetime import datetime

class SteamCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'PeakPulse AI Test (for educational use)'})

    def download_community_app_list(self):
        """
        Télécharge la liste complète des apps depuis un dump GitHub quotidien
        Sources fiables 2026 :
        - https://github.com/jsnli/steamappidlist
        - https://github.com/SteamTools-Team/GameList
        """
        # Choix 1 : jsnli (recommandé - structure apps + catégories)
        #url = "https://raw.githubusercontent.com/jsnli/steamappidlist/master/data/apps.json"
    
        # Choix 2 alternatif si le premier change de structure :
        url = "https://raw.githubusercontent.com/SteamTools-Team/GameList/main/games.json"
    
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
        
            data = r.json()
        
            # Selon le repo, la clé peut varier :
            # jsnli → souvent data["apps"] ou directement une liste
            # SteamTools → souvent une liste directe ou {"games": [...]}
            if isinstance(data, dict):
                apps_list = data.get("apps", data.get("games", []))  # flexible
            else:
                apps_list = data  # si c'est déjà une liste
        
            if not apps_list:
                print("⚠️ Pas de liste d'apps trouvée dans le JSON")
                return None
        
            # Normalisation en DataFrame (appid + name au minimum)
            df = pd.DataFrame(apps_list)
        
            # Colonnes typiques : appid, name, parfois type, categories...
            if "appid" not in df.columns and "app_id" in df.columns:
                df = df.rename(columns={"app_id": "appid"})
            if "name" not in df.columns and "title" in df.columns:
                df = df.rename(columns={"title": "name"})
        
            df = df[df["name"].str.strip() != ""]  # nettoie
            df = df.drop_duplicates(subset=["appid"])
        
            os.makedirs("raw", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"raw/steam_app_list_{timestamp}.json"
            df.to_json(filename, orient="records", indent=2)
            df.to_csv(filename.replace(".json", ".csv"), index=False)
        
            print(f"✅ Téléchargé {len(df):,} apps depuis dump communautaire")
            print(f"Fichiers sauvés : {filename} + .csv")
            return df
    
        except Exception as e:
            print(f"Erreur lors du téléchargement du dump : {e}")
            return None

    def get_app_details(self, appid: int):
        """Détails d'un jeu – fonctionne sans clé API"""
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        try:
            r = self.session.get(url, timeout=12)
            if r.status_code != 200:
                return None
            data = r.json()
            app_str = str(appid)
            if app_str in data and data[app_str]["success"]:
                return data[app_str]["data"]
            return None
        except:
            return None

    def collect_sample_games(self, limit=100):
        """Collecte détails pour un échantillon basé sur le dump communautaire"""
    
        # Si pas encore de liste locale, on la télécharge
        csv_path = "raw/steam_app_list_latest.csv"  # ou ton nom
        json_path = "raw/steam_app_list_latest.json"
    
        if not os.path.exists(csv_path) and not os.path.exists(json_path):
            df_apps = self.download_community_app_list()
            if df_apps is None:
                return None
        else:
            # Charge la dernière version locale si disponible
            try:
                df_apps = pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.read_json(json_path, orient="records")
            except:
                df_apps = self.download_community_app_list()
                if df_apps is None:
                    return None
    
        # Prends un échantillon (head, sample random, ou filtre plus tard)
        #sample = df_apps.head(limit)          # ou df_apps.sample(limit)
        #sample = df_apps.sample(n=limit, random_state=42)  # random 100 jeux
        sample = df_apps[df_apps['name'].str.contains('2025|2026', na=False)].head(limit)  # jeux récents
        if 'type' in df_apps.columns:
            sample = sample[sample['type'] == 'game']  # ou 'Game', vérifie la casse
        results = []
        for _, row in sample.iterrows():
            appid = row["appid"]
            details = self.get_app_details(appid)
            if details:
                entry = {
                    "appid": appid,
                    "name": details.get("name", ""),
                    "genres": [g.get("description", "") for g in details.get("genres", [])],
                    "tags": list(details.get("tags", {}).keys()) if "tags" in details else [],
                    "release_date": details.get("release_date", {}).get("date", ""),
                    "collected_at": datetime.now().isoformat()
                }
                results.append(entry)
            time.sleep(1.2)  # prudent pour éviter ban IP temporaire

        if results:
            df = pd.DataFrame(results)
            filename = f"raw/steam_sample_details_{datetime.now():%Y%m%d}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ {len(df)} jeux détaillés sauvés dans {filename}")
            return df
        return None