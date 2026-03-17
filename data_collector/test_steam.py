import steam_api

collector = steam_api.SteamCollector()
print("=== Téléchargement du dump communautaire ===")
collector.download_community_app_list()

print("\n=== Collecte détails sur 200 jeux ===")
collector.collect_sample_games(limit=200)