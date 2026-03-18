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
        url = "https://raw.githubusercontent.com/jsnli/steamappidlist/master/data/games_appid.json"
    
        # Choix 2 alternatif si le premier change de structure :
        url = "https://raw.githubusercontent.com/jsnli/steamappidlist/master/data/games_appid.json"
    
        try:
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    r = self.session.get(url, timeout=15)
                    r.raise_for_status()
                    break
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    time.sleep(2 ** attempt)
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
            df = df[df['name'].str.len() > 3]
            df = df[~df['name'].str.contains(r'(?:DLC|Soundtrack|Demo|Trailer|Editor|SDK|Server|Mod|Beta|Test)', case=False, na=False)]
            df = df[df['name'].str.len() > 3]
            df = df[~df['name'].str.contains(r'(?:DLC|Soundtrack|Demo|Trailer|Editor|SDK|Server|Mod|Beta|Test)', case=False, na=False)]

            os.makedirs("raw", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"raw/steam_app_list_{timestamp}.json"
            latest_json = "raw/steam_app_list_latest.json"
            latest_csv = "raw/steam_app_list_latest.csv"

            df.to_json(filename, orient="records", indent=2)
            df.to_csv(filename.replace(".json", ".csv"), index=False)
            # Keep a copy as "latest" for fast re-use by collect_sample_games
            df.to_json(latest_json, orient="records", indent=2)
            df.to_csv(latest_csv, index=False)

            print(f"✅ Téléchargé {len(df):,} apps depuis dump communautaire")
            print(f"Fichiers sauvés : {filename} + .csv (et mis à jour {latest_json}/csv)")
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

    def collect_sample_games(self, limit=200):
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
    
        
        # Prioriser les jeux récents ou avec nom qui ressemble à un titre récent
        recent_mask = df_apps['name'].str.contains(r'202[4-6]', case=False, na=False)
        if recent_mask.sum() >= limit:
            sample = df_apps[recent_mask].sample(n=limit, random_state=42)
        else:
            # Si pas assez de récents, complète avec random
            sample = df_apps.sample(n=limit, random_state=42)
        results = []
        success_count = 0
            
        for _, row in sample.iterrows():
            appid = int(row["appid"])
            details = self.get_app_details(appid)
            players = self.get_current_players(appid)

            print(f"appid {appid:8d} → details: {'OK' if details else 'ÉCHEC'} | joueurs: {players}")
            if details:
                success_count += 1
                entry = {
                    "appid": appid,
                    "name": details.get("name", ""),
                    "genres": [g.get("description", "") for g in details.get("genres", [])],
                    "tags": list(details.get("tags", {}).keys()) if "tags" in details else [],
                    "release_date": details.get("release_date", {}).get("date", ""),
                    "current_players": players,
                    "collected_at": datetime.now().isoformat()
                }
                results.append(entry)
            time.sleep(2.0)
        print(f"\nRésumé collecte : {success_count}/{len(sample)} succès ({success_count/len(sample)*100:.1f}%)")
        if results:
            df = pd.DataFrame(results)
            filename = f"raw/steam_sample_details_{datetime.now():%Y%m%d_%H%M}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ {len(df)} jeux détaillés sauvés dans {filename}")
            return df
        return None
    
    def get_current_players(self, appid: int) -> int:
        url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
        params = {"appid": appid}
        try:
            r = self.session.get(url, params=params, timeout=8)
            if r.status_code == 200:
                data = r.json()
                return data["response"].get("player_count", 0)
        except:
            pass
        return 0