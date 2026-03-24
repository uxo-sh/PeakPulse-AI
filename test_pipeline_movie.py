"""
Test du pipeline FeatureEngineeringMovies — version finale.

Même niveau de qualité que test_pipeline.py (Steam/Games) :
─────────────────────────────────────────────────────────────
1. IMPORT PROPRE : utilise le vrai pipeline movies (ml_models/model_movies.py)
   et le vrai FeatureEngineeringMovies — pas de classe inline.

2. CIBLE ROBUSTE (ROI > 2) :
   - ROI = revenue / budget (return on investment)
   - Un film est "tendance" s'il a généré plus de 2x son budget en revenus
   - Signal très fiable : mesure la rentabilité commerciale réelle
   - Filtrage : exclut films avec revenue <= 0 ou budget <= 0
   - Seuil fixe (indépendant del'ensemble d'entraînement)

3. LEAK_COLS adaptés aux films :
   - popularity, revenue, vote_count, vote_average supprimés
   - budget CONSERVÉ (utilisé par FeatureEngineeringMovies)
   - title CONSERVÉ (utilisé par _create_name_features, droppé dans _final_cleanup)

4. GUARD predict_proba : vérifie 2 colonnes avant [:, 1]

5. MÉTRIQUES COMPLÈTES : ROC-AUC, PR-AUC, F1 + cross-val 5-fold

6. MATRICES DE CONFUSION × 2 : seuil optimal + seuil 0.5 (référence)

7. FILMS QUI VONT EXPLOSER : top 20 films haute proba pas encore tendance

8. ANALYSE DES GENRES : par proba moyenne + ratio tendance

9. QUICK TEST : --quick pour vérifier le pipeline en 5 secondes
"""

import numpy as np
import pandas as pd
from ml_models.model_movies import pipeline          # pipeline movies dédiée
from data_processing.preprocessor import preprocessor
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    confusion_matrix,
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    f1_score,
)


# ===========================================================================
# CONSTANTES
# ===========================================================================

# budget     -- CONSERVÉ : utilisé par FeatureEngineeringMovies._create_budget_features
# title      -- CONSERVÉ : utilisé par _create_name_features, droppé dans _final_cleanup
# release_date -- CONSERVÉ si utilisé par le FE, droppé dans _final_cleanup sinon
LEAK_COLS = [
    "popularity",
    "revenue",
    "vote_count",
    "vote_average",
    "log_popularity",
    "log_revenue",
    "log_vote_count",
    "score_ratio",
    "trend_score",
]

TARGET_COL = "is_trending_future"
LABEL_NEG  = "Pas-tendance"
LABEL_POS  = "Tendance"


# ===========================================================================
# 1. CIBLE -- robuste, garantit des positifs dans train ET test
# ===========================================================================

def create_trend_target_movies(train_df: pd.DataFrame, df: pd.DataFrame) -> tuple:
    """
    Un film est 'tendance future' s'il a un ROI > 2.

    Définition du succès commercial :
    ------------------------------------------
    - ROI = revenue / budget (return on investment)
    - ROI > 2 signifie : le film a généré plus de 2x son budget en revenus
    - Signal très fiable : basé sur la rentabilité réelle du film
    - Équilibre naturel : très peu de films atteignent ROI > 2 (~5-10%)

    Filtrage :
    - Exclut les films avec revenue <= 0 ou budget <= 0
    - Seuls les films avec données financières complètes sont considérés

    Seuil fixe (ROI > 2) : indépendant du dataset, comparable d'un set à l'autre
    """
    df = df.copy()

    # Filtre : doivent avoir budget et revenue positifs
    df = df[(df["revenue"] > 0) & (df["budget"] > 0)].copy()

    if len(df) == 0:
        raise ValueError(
            "[ERROR] Aucun film avec revenue > 0 ET budget > 0. "
            "Vérifie les données dans le preprocessor."
        )

    # Calcul du ROI
    df["ROI"] = df["revenue"] / df["budget"]

    # Cible : ROI > 2
    df[TARGET_COL] = (df["ROI"] > 2).astype(int)

    threshold    = 2.0
    signal_used  = "ROI > 2"

    return df, threshold, signal_used


# ===========================================================================
# 2. THRESHOLD TUNING
# ===========================================================================

def find_optimal_threshold(y_true: np.ndarray, y_proba: np.ndarray) -> float:
    """Seuil qui maximise le F1 via la courbe Precision-Recall."""
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    denom     = precisions + recalls + 1e-9
    f1_scores = np.where(denom == 0, 0, 2 * precisions * recalls / denom)
    best_idx  = int(np.argmax(f1_scores[:-1]))
    best_thr  = float(thresholds[best_idx])
    best_f1   = float(f1_scores[best_idx])
    print(f"   -> Seuil optimal : {best_thr:.4f}  (F1 = {best_f1:.4f})")
    return best_thr


# ===========================================================================
# 3. MATRICE DE CONFUSION -- lisible
# ===========================================================================

def print_confusion_matrix(
    cm: np.ndarray,
    label_neg: str,
    label_pos: str,
    title: str = "",
) -> None:
    """
    Matrice de confusion avec VN/FP/FN/VP explicites.

        cm[0,0] VN : bien prédit Pas-tendance
        cm[0,1] FP : prédit Tendance a tort
        cm[1,0] FN : raté un vrai film tendance
        cm[1,1] VP : bien prédit Tendance
    """
    vn, fp = int(cm[0, 0]), int(cm[0, 1])
    fn, vp = int(cm[1, 0]), int(cm[1, 1])
    w = max(len(label_neg), len(label_pos), 12) + 2

    if title:
        print(f"\n{title}")
    print(f"{'':22}{'--- Prédit ---':^{w*2+3}}")
    print(f"{'':22}{label_neg:^{w}}{label_pos:^{w}}")
    print("-" * (22 + w * 2 + 3))
    print(f"{'| Réel':<6}{label_neg:<16}{vn:^{w}}{fp:^{w}}   <- FP = {fp}")
    print(f"{'|':6}{label_pos:<16}{fn:^{w}}{vp:^{w}}   <- FN = {fn}")
    print("-" * (22 + w * 2 + 3))

    recall    = vp / (vp + fn + 1e-9)
    precision = vp / (vp + fp + 1e-9)
    f1        = 2 * precision * recall / (precision + recall + 1e-9)

    print(f"  VN={vn:>6}  FP={fp:>6}  FN={fn:>6}  VP={vp:>6}")
    print(f"  Recall    = {recall:.4f}   (parmi tous les vrais tendance, combien détectés)")
    print(f"  Precision = {precision:.4f}   (parmi tous les prédits tendance, combien vrais)")
    print(f"  F1        = {f1:.4f}")


# ===========================================================================
# 4. FILMS QUI VONT EXPLOSER
# ===========================================================================

def predict_exploding_films(
    test_raw: pd.DataFrame,
    y_test: pd.Series,
    y_proba: np.ndarray,
    optimal_threshold: float,
    top_n: int = 20,
) -> None:
    """
    Top N films avec la plus haute probabilité de tendance
    parmi ceux que la cible actuelle ne classe PAS encore tendance.
    Ce sont les films a surveiller : le modele pense qu'ils vont exploser.
    """
    print(f"\n{'='*65}")
    print("[FILM] FILMS QUI VONT EXPLOSER (hautes proba, pas encore tendance)")
    print(f"{'='*65}")

    candidates                   = test_raw.copy().reset_index(drop=True)
    candidates["proba_tendance"] = y_proba

    mask      = y_test.values == 0
    watchlist = (
        candidates[mask]
        .nlargest(top_n, "proba_tendance")
        .reset_index(drop=True)
    )

    genre_cols = [c for c in watchlist.columns if c.startswith("has_")]

    print(f"\n{'#':<4} | {'Film':<36} | {'Proba':>6} | {'Budget':>8} | Genres principaux")
    print("-" * 88)

    for i, row in watchlist.iterrows():
        title  = str(row.get("title", "N/A"))[:34]
        proba  = row["proba_tendance"]
        budget = (
            f"{row['budget']/1e6:.0f}M$"
            if "budget" in row.index and pd.notna(row["budget"]) and row["budget"] > 0
            else "?"
        )
        genres = ", ".join(
            c.replace("has_", "").replace("_", " ").title()
            for c in genre_cols if row.get(c, 0) == 1
        )[:32]
        stars = "*" * min(5, int(proba * 7))
        print(f"{i+1:<4} | {title:<36} | {proba:>6.4f} | {budget:>8} | {genres}  {stars}")

    print(f"\n  [TIP] {top_n} films avec le plus fort potentiel selon le modele")
    print(f"     Seuil de decision utilisé : {optimal_threshold:.4f}")


# ===========================================================================
# 5. ANALYSE DES GENRES TENDANCE
# ===========================================================================

def analyze_trending_genres(
    X_test: pd.DataFrame,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
) -> None:
    """Analyse les genres par probabilité moyenne et ratio de prédictions tendance."""
    print(f"\n{'='*65}")
    print("[REEL]  ANALYSE DES GENRES TENDANCE")
    print(f"{'='*65}")

    try:
        genre_cols = [c for c in X_test.columns if c.startswith("has_")]
        if not genre_cols:
            print("[WARN]  Aucune colonne has_XXX trouvée dans X_test")
            return

        print(f"[DATA] {len(genre_cols)} genres détectés\n")

        df          = X_test.copy()
        df["pred"]  = y_pred
        df["proba"] = y_proba

        rows = []
        for col in genre_cols:
            sub = df[df[col] == 1]
            if len(sub) == 0:
                continue
            count           = len(sub)
            avg_proba       = sub["proba"].mean()
            trend_ratio     = sub["pred"].mean()
            trend_sub       = sub[sub["pred"] == 1]
            avg_proba_trend = trend_sub["proba"].mean() if len(trend_sub) > 0 else 0.0
            # Score : proba_moyenne x log(volume) = équilibre signal + représentativité
            trend_score     = avg_proba * np.log1p(count)
            rows.append({
                "Genre":           col.replace("has_", "").replace("_", " ").title(),
                "Count":           count,
                "Avg_Proba":       avg_proba,
                "Trend_Ratio":     trend_ratio,
                "Avg_Proba_Trend": avg_proba_trend,
                "Trend_Score":     trend_score,
            })

        stats     = pd.DataFrame(rows).sort_values("Trend_Score", ascending=False)
        max_score = stats["Trend_Score"].max()

        # -- Top 10 --
        print("[BEST] TOP 10 GENRES ÉMERGENTS:")
        print(f"{'Rang':<5}|{'Genre':<22}|{'Count':>6}|{'Proba moy':>10}|{'% Tendance':>11}| Score")
        print("-" * 68)
        for i, (_, r) in enumerate(stats.head(10).iterrows()):
            nb_f = int(r["Trend_Score"] / (max_score / 5)) if max_score > 0 else 0
            bar  = "[F]" * min(5, nb_f)
            print(
                f"{i+1:<5}|{r['Genre']:<22}|{r['Count']:>6.0f}|"
                f"{r['Avg_Proba']:>10.4f}|{r['Trend_Ratio']:>10.2%} | {bar}"
            )

        # -- Détails top 3 --
        print("\n[STATS] DÉTAILS DES 3 MEILLEURS GENRES:\n")
        for i, (_, r) in enumerate(stats.head(3).iterrows()):
            print(f"  {i+1}) {r['Genre'].upper()}")
            print(f"     * Films dans ce genre       : {r['Count']:.0f}")
            print(f"     * Proba tendance moyenne    : {r['Avg_Proba']:.4f} ({r['Avg_Proba']*100:.2f}%)")
            print(f"     * % prédits tendance        : {r['Trend_Ratio']:.2%}")
            print(f"     * Proba moy (prédits tend.) : {r['Avg_Proba_Trend']:.4f}")
            print(f"     * Score tendance            : {r['Trend_Score']:.4f}\n")

        # -- Classements complémentaires --
        print("[STAR] TOP 5 PAR PROBABILITÉ MOYENNE:")
        print(f"{'Rang':<5}|{'Genre':<22}|{'Proba moy':>10}")
        print("-" * 42)
        for i, (_, r) in enumerate(stats.nlargest(5, "Avg_Proba").iterrows()):
            print(f"{i+1:<5}|{r['Genre']:<22}|{r['Avg_Proba']:>10.4f}")

        print("\n[CHART] TOP 5 PAR % PRÉDIT TENDANCE:")
        print(f"{'Rang':<5}|{'Genre':<22}|{'% Tendance':>11}")
        print("-" * 42)
        for i, (_, r) in enumerate(stats.nlargest(5, "Trend_Ratio").iterrows()):
            print(f"{i+1:<5}|{r['Genre']:<22}|{r['Trend_Ratio']:>10.2%}")

    except Exception as e:
        print(f"[WARN]  Erreur analyse genres : {e}")


# ===========================================================================
# 6. TEST PRINCIPAL
# ===========================================================================

def test_feature_engineering_movies() -> None:
    print("\n" + "=" * 65)
    print("[FILM] TEST DU PIPELINE - FeatureEngineeringMovies")
    print("=" * 65)

    try:
        # -- Étape 1 : Chargement --
        print("\n[IN] Etape 1: Chargement des donnees films...")
        movies_df, _ = preprocessor()
        print(f"[OK] {len(movies_df):,} films chargés")
        print(f"   Colonnes disponibles : {list(movies_df.columns)}")

        # -- Étape 2 : Split temporel --
        print("\n[SPLIT] Etape 2: Split temporel (80% train / 20% test)...")

        sort_col = "days_since_release" if "days_since_release" in movies_df.columns else "release_date"
        movies_sorted = (
            movies_df
            .sort_values(sort_col)
            .reset_index(drop=True)
        )
        split_idx = int(len(movies_sorted) * 0.80)
        train_raw = movies_sorted.iloc[:split_idx].copy()
        test_raw  = movies_sorted.iloc[split_idx:].copy()

        print(f"[OK] Train : {len(train_raw):,} films  |  Test : {len(test_raw):,} films")
        print(f"   * Train -> films les plus anciens")
        print(f"   * Test  -> films les plus récents")

        # -- Étape 3 : Construction de la cible --
        print("\n[TARGET] Etape 3: Construction de la cible (ROI > 2)...")
        train_raw, roi_thr, signal = create_trend_target_movies(train_raw, train_raw)
        test_raw,  _,       _      = create_trend_target_movies(train_raw, test_raw)

        train_dist    = train_raw[TARGET_COL].value_counts().sort_index().to_dict()
        test_dist     = test_raw[TARGET_COL].value_counts().sort_index().to_dict()
        train_pos_pct = train_dist.get(1, 0) / len(train_raw) * 100
        test_pos_pct  = test_dist.get(1, 0)  / len(test_raw)  * 100

        print(f"   * Signal utilisé                : {signal}")
        print(f"   * Seuil de rentabilité          : ROI > {roi_thr:.1f}")
        print(f"   * Train -> {train_dist}  ({train_pos_pct:.1f}% positifs)")
        print(f"   * Test  -> {test_dist}   ({test_pos_pct:.1f}% positifs)")

        # Guards : 0 positifs -> erreur claire
        n_pos_train = train_dist.get(1, 0)
        n_pos_test  = test_dist.get(1, 0)

        if n_pos_train == 0:
            raise ValueError(
                f"[ERROR] 0 positifs dans le train ! "
                f"Seuil ROI = {roi_thr:.1f} trop strict. "
                f"Baisse le seuil ROI dans create_trend_target_movies (essaie ROI > 1.5)."
            )
        if n_pos_test == 0:
            raise ValueError(
                f"[ERROR] 0 positifs dans le test ! "
                f"Les films récents n'atteignent pas ROI > {roi_thr:.1f}. "
                f"Baisse le seuil ROI dans create_trend_target_movies."
            )

        print(f"[OK] Cible valide : {n_pos_train:,} positifs train | {n_pos_test:,} positifs test")

        # -- Étape 4 : Préparation des features --
        print("\n[TOOL] Etape 4: Preparation des features...")

        # budget -> CONSERVÉ (utilisé par FeatureEngineeringMovies)
        # title  -> CONSERVÉ (utilisé par _create_name_features, droppé dans _final_cleanup)
        X_train = train_raw.drop(columns=[TARGET_COL] + LEAK_COLS, errors="ignore")
        y_train = train_raw[TARGET_COL]
        X_test  = test_raw.drop(columns=[TARGET_COL] + LEAK_COLS, errors="ignore")
        y_test  = test_raw[TARGET_COL]

        print(f"[OK] {X_train.shape[1]} features")
        print(f"   Colonnes X_train : {list(X_train.columns)}")

        # -- Étape 5 : Entraînement --
        print("\n[ROCKET] Etape 5: Entrainement du pipeline...")
        pipeline.fit(X_train, y_train)

        n_classes = len(pipeline.named_steps["model"].classes_)
        print(f"[OK] Pipeline entraine -- {n_classes} classe(s) apprises")

        if n_classes < 2:
            raise ValueError(
                "[ERROR] Le modele n'a appris qu'UNE seule classe. "
                "Il faut des positifs ET des négatifs dans le train. "
                "Verifie create_trend_target_movies."
            )

        # -- Étape 6 : Probabilités --
        print("\n[CRYSTAL] Etape 6: Calcul des probabilites...")
        proba_matrix = pipeline.predict_proba(X_test)

        # Guard predict_proba : vérifie 2 colonnes
        if proba_matrix.shape[1] < 2:
            raise ValueError(
                f"[ERROR] predict_proba retourne {proba_matrix.shape[1]} colonne(s). "
                "Le modele n'a appris qu'une classe -- cible trop déséquilibrée."
            )

        y_proba = proba_matrix[:, 1]
        print(f"[OK] Probabilites : min={y_proba.min():.4f} | max={y_proba.max():.4f} | mean={y_proba.mean():.4f}")

        # -- Étape 7 : Threshold tuning --
        print("\n[SLIDER] Etape 7: Recherche du seuil optimal...")
        optimal_thr = find_optimal_threshold(y_test.values, y_proba)
        y_pred      = (y_proba >= optimal_thr).astype(int)

        # -- Étape 8 : Métriques --
        print("\n[STATS] Etape 8: RÉSULTATS DE PERFORMANCE")
        print("-" * 65)

        accuracy = accuracy_score(y_test, y_pred)
        roc_auc  = roc_auc_score(y_test, y_proba)
        pr_auc   = average_precision_score(y_test, y_proba)
        f1       = f1_score(y_test, y_pred, zero_division=0)

        print(f"  Accuracy            : {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"  ROC-AUC             : {roc_auc:.4f}  <- sépare bien les classes ?")
        print(f"  PR-AUC              : {pr_auc:.4f}  <- détecte bien les tendances ?")
        print(f"  F1 (seuil optimal)  : {f1:.4f}")

        try:
            from sklearn.model_selection import cross_val_score, StratifiedKFold

            X_all  = pd.concat([X_train, X_test], ignore_index=True)
            y_all  = pd.concat([y_train, y_test], ignore_index=True)
            cv     = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            f1_cv  = cross_val_score(pipeline, X_all, y_all, cv=cv, scoring="f1", n_jobs=-1)
            roc_cv = cross_val_score(pipeline, X_all, y_all, cv=cv, scoring="roc_auc", n_jobs=-1)
            pr_cv  = cross_val_score(pipeline, X_all, y_all, cv=cv, scoring="average_precision", n_jobs=-1)

            print(f"\n  Cross-validation 5-fold :")
            print(f"    F1      : {f1_cv.mean():.4f} +/- {f1_cv.std():.4f}")
            print(f"    ROC-AUC : {roc_cv.mean():.4f} +/- {roc_cv.std():.4f}")
            print(f"    PR-AUC  : {pr_cv.mean():.4f} +/- {pr_cv.std():.4f}")
        except Exception as e:
            print(f"  [WARN] Cross-val impossible : {e}")

        # -- Étape 9 : Rapport de classification --
        print(f"\n[REPORT] Rapport de classification (seuil = {optimal_thr:.4f}) :")
        print(
            classification_report(
                y_test, y_pred,
                target_names=[LABEL_NEG, LABEL_POS],
                digits=4,
                zero_division=0,
            )
        )

        # -- Étape 10 : Matrices de confusion --
        cm_opt = confusion_matrix(y_test, y_pred)
        print_confusion_matrix(
            cm_opt, LABEL_NEG, LABEL_POS,
            title=f"[MAT1] Matrice -- seuil OPTIMAL ({optimal_thr:.4f})",
        )

        cm_05 = confusion_matrix(y_test, (y_proba >= 0.5).astype(int))
        print_confusion_matrix(
            cm_05, LABEL_NEG, LABEL_POS,
            title="[MAT2] Matrice -- seuil PAR DEFAUT (0.50) [reference]",
        )

        # -- Étape 11 : Analyse des erreurs --
        print(f"\n[SEARCH] Etape 11: ANALYSE DES ERREURS")
        print("-" * 65)
        errors_mask = y_pred != y_test.values
        n_errors    = int(errors_mask.sum())
        print(f"[ERROR] {n_errors:,} erreurs sur {len(y_test):,} ({n_errors/len(y_test)*100:.2f}%)")

        if n_errors > 0:
            err_idx = np.where(errors_mask)[0]
            print(f"\n  {'#':<3} | {'Réel':<13} | {'Prédit':<13} | {'Proba':>6} | Film")
            print("  " + "-" * 72)
            for k, idx in enumerate(err_idx[:10]):
                rl = LABEL_POS if y_test.iloc[idx] == 1 else LABEL_NEG
                pl = LABEL_POS if y_pred[idx]      == 1 else LABEL_NEG
                try:
                    title = str(test_raw.iloc[idx]["title"])[:36]
                except Exception:
                    title = "N/A"
                print(f"  {k+1:<3} | {rl:<13} | {pl:<13} | {y_proba[idx]:>6.4f} | {title}")

        # -- Étape 12 : Features importantes --
        print(f"\n[STAR] Etape 12: FEATURES LES PLUS IMPORTANTES")
        print("-" * 65)
        try:
            model = pipeline.named_steps["model"]
            fe    = pipeline.named_steps["feature_engeneering"]
            if hasattr(model, "feature_importances_"):
                X_tr    = fe.fit_transform(X_train)
                f_names = (
                    list(X_tr.columns)
                    if hasattr(X_tr, "columns")
                    else [f"f{i}" for i in range(X_tr.shape[1])]
                )
                imps    = model.feature_importances_
                indices = np.argsort(imps)[::-1]

                print(f"\n  {'Rang':<5}| {'Feature':<32}| {'Importance':>10} | Graphique")
                print("  " + "-" * 65)
                for i in range(min(15, len(f_names))):
                    idx = indices[i]
                    imp = imps[idx]
                    nm  = str(f_names[idx])[:32]
                    bar = "[#]" * int(imp * 40)
                    print(f"  {i+1:<5}| {nm:<32}| {imp:>10.6f} | {bar}")
        except Exception as e:
            print(f"  [WARN] Features impossibles a extraire : {e}")

        # -- Étape 13 : Genres tendance --
        analyze_trending_genres(X_test, y_pred, y_proba)

        # -- Étape 14 : Films qui vont exploser --
        predict_exploding_films(test_raw, y_test, y_proba, optimal_thr, top_n=20)

        print("\n" + "=" * 65)
        print("[OK] TEST TERMINA AVEC SUCCES!")
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"\n[ERROR] ERREUR : {e}")
        import traceback
        traceback.print_exc()


# ===========================================================================
# 7. TEST RAPIDE
# ===========================================================================

def quick_test() -> None:
    print("\n[!] TEST RAPIDE - FeatureEngineeringMovies")
    print("-" * 40)
    try:
        movies_df, _ = preprocessor()
        print(f"[OK] {len(movies_df):,} films chargés")

        sample   = movies_df.copy()
        sample   = sample[(sample["revenue"] > 0) & (sample["budget"] > 0)]
        sample["ROI"] = sample["revenue"] / sample["budget"]
        
        X_sample = sample.drop(columns=LEAK_COLS + [TARGET_COL] + ["ROI"], errors="ignore")
        y_sample = (sample["ROI"] > 2).astype(int)

        if len(y_sample[y_sample == 1]) == 0 or len(y_sample[y_sample == 0]) == 0:
            print("[WARN] Pas assez de films avec ROI > 2, using smaller sample")
            return

        pipeline.fit(X_sample, y_sample)
        proba = pipeline.predict_proba(X_sample.head(5))[:, 1]
        print(f"[OK] Probabilites : {proba.round(3)}")
        print("[SUCCESS] PIPELINE FONCTIONNEL!")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    else:
        test_feature_engineering_movies()
