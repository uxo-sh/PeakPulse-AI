"""Script de test du modèle ML pipeline - FeatureEngineeringGames seulement."""

from ml_models.model import pipeline
from data_processing.preprocessor import preprocessor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import numpy as np
import pandas as pd


def analyze_trending_genres(X_test, y_pred, y_pred_proba):
    """Analyse les genres qui pourraient devenir tendance selon les prédictions du modèle."""
    print("\n🔮 Étape 8: ANALYSE DES GENRES TENDANCE")
    print("-" * 60)

    try:
        # Identifier les colonnes de genres/tags (colonnes has_XXX)
        genre_cols = [col for col in X_test.columns if col.startswith('has_')]
        
        if not genre_cols:
            print("⚠️ Aucune colonne de genre trouvée (has_XXX)")
            return

        print(f"📌 {len(genre_cols)} genres/tags détectés\n")

        # Créer un DataFrame avec les résultats
        X_test_copy = X_test.copy()
        X_test_copy['prediction'] = y_pred
        X_test_copy['confidence'] = y_pred_proba

        # Analyser par genre
        genre_stats = []
        
        for genre in genre_cols:
            # Jeux avec ce genre
            games_with_genre = X_test_copy[X_test_copy[genre] == 1]
            
            if len(games_with_genre) == 0:
                continue
            
            # Statistiques
            count = len(games_with_genre)
            avg_confidence = games_with_genre['confidence'].mean()
            free_ratio = games_with_genre['prediction'].mean()  # % prédits gratuits
            
            # Confiance moyenne pour les prédictions "gratuit"
            free_games = games_with_genre[games_with_genre['prediction'] == 1]
            avg_conf_free = free_games['confidence'].mean() if len(free_games) > 0 else 0
            
            # Score tendance: confiance * ratio gratuit * popularité
            trend_score = avg_confidence * free_ratio * np.log1p(count)
            
            genre_stats.append({
                'Genre': genre.replace('has_', '').replace('_', ' ').title(),
                'Count': count,
                'Avg_Confidence': avg_confidence,
                'Free_Ratio': free_ratio,
                'Avg_Conf_Free': avg_conf_free,
                'Trend_Score': trend_score
            })
        
        # Convertir en DataFrame et trier
        stats_df = pd.DataFrame(genre_stats).sort_values('Trend_Score', ascending=False)
        
        # Afficher les top genres tendance
        print("🏆 TOP 10 GENRES ÉMERGENTS (Tendance):")
        print(f"{'Rang':<5} | {'Genre':<25} | {'Count':<6} | {'Confiance':<10} | {'% Gratuit':<10} | {'Score':<10}")
        print("-" * 80)
        
        for i, (_, row) in enumerate(stats_df.head(10).iterrows()):
            trend_bar = "🔥" * min(5, int(row['Trend_Score'] / (stats_df['Trend_Score'].max() / 5)))
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Count']:<6.0f} | {row['Avg_Confidence']:<10.4f} | {row['Free_Ratio']:<10.2%} | {trend_bar}")
        
        # Détails des 3 top tendances
        print("\n📈 DÉTAILS DES 3 MEILLEURS GENRES TENDANCE:\n")
        
        for i, (_, row) in enumerate(stats_df.head(3).iterrows()):
            print(f"{i+1}️⃣  {row['Genre'].upper()}")
            print(f"   • Nombre de jeux: {row['Count']:.0f}")
            print(f"   • Confiance moyenne du modèle: {row['Avg_Confidence']:.4f} ({row['Avg_Confidence']*100:.2f}%)")
            print(f"   • % prédits gratuits: {row['Free_Ratio']:.2%}")
            print(f"   • Confiance moyenne (prédits gratuits): {row['Avg_Conf_Free']:.4f}")
            print(f"   • Score tendance: {row['Trend_Score']:.4f}")
            print()
        
        # Genres avec meilleure confiance (peu importe le ratio gratuit)
        print("\n⭐ TOP GENRES PAR CONFIANCE DU MODÈLE:")
        top_conf = stats_df.nlargest(5, 'Avg_Confidence')
        print(f"{'Rang':<5} | {'Genre':<25} | {'Confiance':<10}")
        print("-" * 42)
        for i, (_, row) in enumerate(top_conf.iterrows()):
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Avg_Confidence']:<10.4f}")
        
        # Genres avec meilleur ratio de gratuité
        print("\n💰 TOP GENRES GRATUITS:")
        top_free = stats_df.nlargest(5, 'Free_Ratio')
        print(f"{'Rang':<5} | {'Genre':<25} | {'% Gratuit':<10}")
        print("-" * 42)
        for i, (_, row) in enumerate(top_free.iterrows()):
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Free_Ratio']:<10.2%}")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'analyse des genres: {e}")


def test_feature_engineering_games():
    """Test du pipeline FeatureEngineeringGames uniquement."""
    print("\n" + "="*60)
    print("🎮 TEST DU PIPELINE - FeatureEngineeringGames")
    print("="*60)

    try:
        # 1. Charger les données
        print("\n📥 Étape 1: Chargement des données Steam...")
        movies_df, steam_df = preprocessor()
        print(f"✅ {len(steam_df):,} jeux Steam chargés")

        # 2. Préparer les données
        print("\n🎯 Étape 2: Préparation des données...")
        target_col = 'is_free'

        if target_col not in steam_df.columns:
            print(f"❌ Colonne cible '{target_col}' introuvable")
            print(f"Colonnes disponibles: {list(steam_df.columns)}")
            return

        X = steam_df.drop(columns=[target_col], errors='ignore')
        y = steam_df[target_col]

        print(f"  • Features: {X.shape[1]} colonnes")
        print(f"  • Target: {target_col}")
        print(f"  • Distribution: {y.value_counts().to_dict()}")

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"✅ Train: {len(X_train):,} | Test: {len(X_test):,}")

        # 3. Entraîner le modèle
        print("\n🚀 Étape 3: Entraînement du pipeline...")
        pipeline.fit(X_train, y_train)
        print("✅ Pipeline entraîné avec succès")

        # 4. Prédictions
        print("\n🔮 Étape 4: Prédictions...")
        y_pred = pipeline.predict(X_test)
        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
        print(f"✅ Prédictions générées pour {len(X_test):,} exemples")

        # 5. Évaluation
        print("\n📊 Étape 5: RÉSULTATS DE PERFORMANCE")
        print("-" * 60)

        accuracy = accuracy_score(y_test, y_pred)
        print(f"🎯 Accuracy globale: {accuracy:.4f} ({accuracy*100:.2f}%)")

        print("\n📋 Rapport de classification détaillé:")
        print(classification_report(y_test, y_pred, target_names=['Payant', 'Gratuit'], digits=4))

        # Matrice de confusion
        cm = confusion_matrix(y_test, y_pred)
        print("\n📈 Matrice de confusion:")
        print(f"         Prédit")
        print(f"         Payant  Gratuit")
        print(f"Réel Payant   {cm[0,0]:5d}   {cm[0,1]:5d}")
        print(f"     Gratuit  {cm[1,0]:5d}   {cm[1,1]:5d}")

        # 6. Analyse des erreurs
        print("\n🔍 Étape 6: ANALYSE DES ERREURS")
        print("-" * 60)

        errors_mask = y_pred != y_test
        n_errors = errors_mask.sum()
        error_rate = n_errors / len(X_test) * 100

        print(f"❌ Total d'erreurs: {n_errors:,} sur {len(X_test):,} ({error_rate:.2f}%)")

        if n_errors > 0:
            error_indices = np.where(errors_mask)[0]
            print(f"\nExemples d'erreurs (10 premiers):")
            print(f"{'#':<3} | {'Réel':<8} | {'Prédit':<8} | {'Confiance':<10} | Nom du jeu")
            print("-" * 80)
            for i, idx in enumerate(error_indices[:10]):
                true_label = "Gratuit" if y_test.iloc[idx] == 1 else "Payant"
                pred_label = "Gratuit" if y_pred[idx] == 1 else "Payant"
                confidence = y_pred_proba[idx]
                try:
                    game_name = X_test.iloc[idx]['name'][:40]
                except:
                    game_name = 'N/A'
                print(f"{i+1:<3} | {true_label:<8} | {pred_label:<8} | {confidence:<10.4f} | {game_name}")

        # 7. Features importantes
        print("\n🌟 Étape 7: FEATURES LES PLUS IMPORTANTES")
        print("-" * 60)

        try:
            model = pipeline.named_steps['model']
            if hasattr(model, 'feature_importances_'):
                # Récupérer les noms de features après feature engineering
                fe_transformer = pipeline.named_steps['feature_engeneering']
                X_transformed = fe_transformer.fit_transform(X_train)
                feature_names = X_transformed.columns if hasattr(X_transformed, 'columns') else [f"Feature_{i}" for i in range(X_transformed.shape[1])]

                importances = model.feature_importances_
                indices = np.argsort(importances)[::-1]

                print(f"\nTop 15 features les plus importantes:")
                print(f"{'Rang':<5} | {'Feature':<40} | {'Importance':<12} | {'Graphique':<20}")
                print("-" * 80)

                for i in range(min(15, len(feature_names))):
                    idx = indices[i]
                    importance = importances[idx]
                    feature_name = str(feature_names[idx])[:40]
                    score = "█" * int(importance * 30) if importance > 0 else ""
                    print(f"{i+1:<5} | {feature_name:<40} | {importance:<12.6f} | {score}")

        except Exception as e:
            print(f"⚠️ Impossible d'extraire les features importantes: {e}")

        # 8. Analyse des genres tendance
        analyze_trending_genres(X_test, y_pred, y_pred_proba)

        print("\n" + "="*60)
        print("✅ TEST TERMINÉ AVEC SUCCÈS!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ ERREUR lors du test: {e}")
        import traceback
        traceback.print_exc()


def quick_test():
    """Test rapide pour vérifier que le pipeline fonctionne."""
    print("\n⚡ TEST RAPIDE - FeatureEngineeringGames")
    print("-" * 40)

    try:
        movies_df, steam_df = preprocessor()
        print(f"✅ Données chargées: {len(steam_df):,} jeux")

        # Test sur petit sample
        sample = steam_df.head(100).copy()
        X_sample = sample.drop('is_free', axis=1)
        y_sample = sample['is_free']

        pipeline.fit(X_sample, y_sample)
        print("✅ Feature engineering + modèle: OK")

        pred = pipeline.predict(X_sample.head(5))
        print(f"✅ Prédictions: {pred}")

        print("\n🎉 PIPELINE FONCTIONNEL!")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        test_feature_engineering_games()
