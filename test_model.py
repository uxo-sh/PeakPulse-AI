import numpy as np
import pandas as pd
from ml_models.model import pipeline
from data_processing.preprocessor import preprocessor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


def create_temporal_trend_target(df):
    """
    Simule une tendance FUTURE :
    un jeu est tendance s’il a beaucoup d'owners MAIS était récent
    """
    df = df.copy()

    # Normalisation
    owners_norm = (df["owners"] - df["owners"].min()) / (df["owners"].max() - df["owners"].min() + 1e-9)

    # Bonus si jeu récent (important pour tendance)
    recency_bonus = 1 - (df["days_since_release"] / df["days_since_release"].max())

    # Score futur simulé
    future_score = 0.7 * owners_norm + 0.3 * recency_bonus

    df["is_trending_future"] = (future_score >= future_score.quantile(0.85)).astype(int)

    return df


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
            trend_ratio = games_with_genre['prediction'].mean()  # % prédits tendance

            # Confiance moyenne pour les prédictions "tendance"
            trend_games = games_with_genre[games_with_genre['prediction'] == 1]
            avg_conf_trend = trend_games['confidence'].mean() if len(trend_games) > 0 else 0

            # Score tendance: confiance * ratio tendance * popularité
            trend_score = avg_confidence * trend_ratio * np.log1p(count)

            genre_stats.append({
                'Genre': genre.replace('has_', '').replace('_', ' ').title(),
                'Count': count,
                'Avg_Confidence': avg_confidence,
                'Trend_Ratio': trend_ratio,
                'Avg_Conf_Trend': avg_conf_trend,
                'Trend_Score': trend_score
            })
        
        # Convertir en DataFrame et trier
        stats_df = pd.DataFrame(genre_stats).sort_values('Trend_Score', ascending=False)
        
        # Afficher les top genres tendance
        print("🏆 TOP 10 GENRES ÉMERGENTS (Tendance):")
        print(f"{'Rang':<5} | {'Genre':<25} | {'Count':<6} | {'Confiance':<10} | {'% Tendance':<10} | {'Score':<10}")
        print("-" * 80)
        
        for i, (_, row) in enumerate(stats_df.head(10).iterrows()):
            trend_bar = "🔥" * min(5, int(row['Trend_Score'] / (stats_df['Trend_Score'].max() / 5)))
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Count']:<6.0f} | {row['Avg_Confidence']:<10.4f} | {row['Trend_Ratio']:<10.2%} | {trend_bar}")

        # Détails des 3 top tendances
        print("\n📈 DÉTAILS DES 3 MEILLEURS GENRES TENDANCE:\n")

        for i, (_, row) in enumerate(stats_df.head(3).iterrows()):
            print(f"{i+1}️⃣  {row['Genre'].upper()}")
            print(f"   • Nombre de jeux: {row['Count']:.0f}")
            print(f"   • Confiance moyenne du modèle: {row['Avg_Confidence']:.4f} ({row['Avg_Confidence']*100:.2f}%)")
            print(f"   • % prédits tendance: {row['Trend_Ratio']:.2%}")
            print(f"   • Confiance moyenne (prédits tendance): {row['Avg_Conf_Trend']:.4f}")
            print(f"   • Score tendance: {row['Trend_Score']:.4f}")
            print()

        # Genres avec meilleure confiance (peu importe le ratio tendance)
        print("\n⭐ TOP GENRES PAR CONFIANCE DU MODÈLE:")
        top_conf = stats_df.nlargest(5, 'Avg_Confidence')
        print(f"{'Rang':<5} | {'Genre':<25} | {'Confiance':<10}")
        print("-" * 42)
        for i, (_, row) in enumerate(top_conf.iterrows()):
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Avg_Confidence']:<10.4f}")
        
        # Genres avec meilleur ratio tendance
        print("\n💰 TOP GENRES TENDANCE:")
        top_trend = stats_df.nlargest(5, 'Trend_Ratio')
        print(f"{'Rang':<5} | {'Genre':<25} | {'% Tendance':<10}")
        print("-" * 42)
        for i, (_, row) in enumerate(top_trend.iterrows()):
            print(f"{i+1:<5} | {row['Genre']:<25} | {row['Trend_Ratio']:<10.2%}")
        
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
        print("\n🎯 Étape 2: Création d'une vraie cible temporelle...")

        steam_df = create_temporal_trend_target(steam_df)
        target_col = "is_trending_future"

        print("✅ Cible créée : tendance FUTURE simulée")

        # Éliminer les features qui leakent directement la cible pour éviter le sur-apprentissage
        leak_cols = [
            "score_ratio",
            "owners",
            "days_since_release",
            "price",
            "is_free",
            "trend_score",
            "positive",
            "negative",
            "review_count"
        ]
        X = steam_df.drop(columns=[target_col] + leak_cols, errors='ignore')
        y = steam_df[target_col]

        print(f"  • Features: {X.shape[1]} colonnes")
        print(f"  • Target: {target_col}")
        print(f"  • Distribution: {y.value_counts().to_dict()}")

        # Split temporel (simule prédiction future)
        steam_df_sorted = steam_df.sort_values("days_since_release")
        split_index = int(len(steam_df_sorted) * 0.8)

        train_df = steam_df_sorted.iloc[:split_index]
        test_df = steam_df_sorted.iloc[split_index:]

        X_train = train_df.drop(columns=[target_col] + leak_cols, errors='ignore')
        y_train = train_df[target_col]
        X_test = test_df.drop(columns=[target_col] + leak_cols, errors='ignore')
        y_test = test_df[target_col]

        print(f"✅ Split temporel: Train {len(X_train):,} (anciens) | Test {len(X_test):,} (récents)")

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

        try:
            from sklearn.model_selection import cross_val_score, StratifiedKFold
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            f1_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='f1')
            print(f"🧪 F1 cross-val 5-fold: {f1_scores.mean():.4f} ± {f1_scores.std():.4f}")
        except Exception as e:
            print(f"⚠️ Impossible de faire cross-validation F1 : {e}")

        target_label_0 = 'Non-' + ('tendance' if target_col == 'is_trending' else 'gratuit')
        target_label_1 = 'Tendance' if target_col == 'is_trending' else 'Gratuit'

        print("\n📋 Rapport de classification détaillé:")
        print(classification_report(y_test, y_pred, target_names=[target_label_0, target_label_1], digits=4))

        # Matrice de confusion
        cm = confusion_matrix(y_test, y_pred)
        print("\n📈 Matrice de confusion:")
        print(f"         Prédit")
        print(f"         {target_label_0:<7} {target_label_1}")
        print(f"Réel {target_label_0:<7} {cm[0,0]:5d}   {cm[0,1]:5d}")
        print(f"     {target_label_1:<7} {cm[1,0]:5d}   {cm[1,1]:5d}")

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
                true_label = target_label_1 if y_test.iloc[idx] == 1 else target_label_0
                pred_label = target_label_1 if y_pred[idx] == 1 else target_label_0
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
