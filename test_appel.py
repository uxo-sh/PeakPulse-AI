"""
test_appel.py — Fichier de test des valeurs de retour de test_pipeline.py

Ce fichier appelle toutes les fonctions de test_pipeline.py et vérifie :
  - que chaque valeur de retour est bien présente
  - que les types sont corrects
  - que les valeurs sont dans des plages attendues
  - que les DataFrames ont les bonnes colonnes

Utilisation :
    python test_appel.py            ← test complet
    python test_appel.py --quick    ← test rapide uniquement
"""

import sys
import numpy as np
import pandas as pd

# ── Import des fonctions depuis test_pipeline ────────────────────────────────
from test_pipeline import (
    test_feature_engineering_games,
    quick_test,
    find_optimal_threshold,
    print_confusion_matrix,
    analyze_trending_genres,
    predict_exploding_games,
    create_trend_target,
    LEAK_COLS,
    TARGET_COL,
    LABEL_NEG,
    LABEL_POS,
)

# ===========================================================================
# UTILITAIRES D'ASSERTION
# ===========================================================================

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    """Affiche PASS ou FAIL pour un test unitaire."""
    global PASS, FAIL
    status = "✅ PASS" if condition else "❌ FAIL"
    suffix = f"  ← {detail}" if detail else ""
    print(f"  {status}  {label}{suffix}")
    if condition:
        PASS += 1
    else:
        FAIL += 1


def section(title: str) -> None:
    print(f"\n{'═'*65}")
    print(f"  {title}")
    print(f"{'═'*65}")


def subsection(title: str) -> None:
    print(f"\n  ── {title} ──")


# ===========================================================================
# 1. TEST DE find_optimal_threshold
# ===========================================================================

def test_find_optimal_threshold() -> None:
    section("1. TEST — find_optimal_threshold()")

    # Données synthétiques simples
    rng     = np.random.default_rng(42)
    y_true  = rng.integers(0, 2, size=200)
    y_proba = np.clip(y_true * 0.6 + rng.uniform(0, 0.4, size=200), 0, 1)

    result = find_optimal_threshold(y_true, y_proba)

    subsection("Type et clés")
    check("Retour est un dict",           isinstance(result, dict))
    check("Clé 'threshold' présente",     "threshold"  in result)
    check("Clé 'f1' présente",            "f1"         in result)
    check("Clé 'precisions' présente",    "precisions" in result)
    check("Clé 'recalls' présente",       "recalls"    in result)
    check("Clé 'thresholds' présente",    "thresholds" in result)

    subsection("Valeurs")
    thr = result["threshold"]
    f1  = result["f1"]
    check("threshold est un float",       isinstance(thr, float))
    check("threshold dans [0, 1]",        0.0 <= thr <= 1.0,       f"valeur = {thr:.4f}")
    check("f1 est un float",              isinstance(f1, float))
    check("f1 dans [0, 1]",               0.0 <= f1 <= 1.0,        f"valeur = {f1:.4f}")
    check("precisions est un array",      isinstance(result["precisions"], np.ndarray))
    check("recalls est un array",         isinstance(result["recalls"],    np.ndarray))
    check("thresholds est un array",      isinstance(result["thresholds"], np.ndarray))
    check("len(precisions) >= 2",         len(result["precisions"]) >= 2)


# ===========================================================================
# 2. TEST DE print_confusion_matrix
# ===========================================================================

def test_print_confusion_matrix() -> None:
    section("2. TEST — print_confusion_matrix()")

    cm = np.array([[80, 10], [5, 50]])
    result = print_confusion_matrix(cm, LABEL_NEG, LABEL_POS, title="Test CM")

    subsection("Type et clés")
    check("Retour est un dict",           isinstance(result, dict))
    for key in ["vn", "fp", "fn", "vp", "recall", "precision", "f1"]:
        check(f"Clé '{key}' présente",    key in result)

    subsection("Valeurs exactes depuis cm [[80,10],[5,50]]")
    check("vn == 80",                     result["vn"] == 80,       f"vn = {result['vn']}")
    check("fp == 10",                     result["fp"] == 10,       f"fp = {result['fp']}")
    check("fn == 5",                      result["fn"] == 5,        f"fn = {result['fn']}")
    check("vp == 50",                     result["vp"] == 50,       f"vp = {result['vp']}")

    subsection("Métriques calculées")
    check("recall dans [0, 1]",           0.0 <= result["recall"]    <= 1.0, f"recall = {result['recall']:.4f}")
    check("precision dans [0, 1]",        0.0 <= result["precision"] <= 1.0, f"precision = {result['precision']:.4f}")
    check("f1 dans [0, 1]",               0.0 <= result["f1"]        <= 1.0, f"f1 = {result['f1']:.4f}")

    # Vérification recall = vp / (vp + fn)
    expected_recall = 50 / (50 + 5 + 1e-9)
    check("recall cohérent avec vp/fn",   abs(result["recall"] - expected_recall) < 1e-4,
          f"attendu ≈ {expected_recall:.4f}, obtenu {result['recall']:.4f}")


# ===========================================================================
# 3. TEST DE analyze_trending_genres (données synthétiques)
# ===========================================================================

def test_analyze_trending_genres() -> None:
    section("3. TEST — analyze_trending_genres()")

    rng = np.random.default_rng(0)
    n   = 200
    X_test = pd.DataFrame({
        "has_action":    rng.integers(0, 2, n),
        "has_rpg":       rng.integers(0, 2, n),
        "has_strategy":  rng.integers(0, 2, n),
        "price":         rng.uniform(0, 60, n),
        "other_feature": rng.standard_normal(n),
    })
    y_pred  = rng.integers(0, 2, n)
    y_proba = np.clip(rng.uniform(0, 1, n), 0, 1)

    result = analyze_trending_genres(X_test, y_pred, y_proba)

    subsection("Type et colonnes")
    check("Retour est un DataFrame",      isinstance(result, pd.DataFrame))
    for col in ["Genre", "Count", "Avg_Proba", "Trend_Ratio", "Avg_Proba_Trend", "Trend_Score"]:
        check(f"Colonne '{col}' présente", col in result.columns)

    subsection("Valeurs")
    check("DataFrame non vide",           len(result) > 0,          f"lignes = {len(result)}")
    check("3 genres détectés max",        len(result) <= 3,         f"lignes = {len(result)}")
    check("Count > 0 pour chaque genre",  (result["Count"] > 0).all())
    check("Avg_Proba dans [0,1]",         result["Avg_Proba"].between(0, 1).all())
    check("Trend_Ratio dans [0,1]",       result["Trend_Ratio"].between(0, 1).all())
    check("Trié par Trend_Score desc",
          result["Trend_Score"].is_monotonic_decreasing or len(result) <= 1)


# ===========================================================================
# 4. TEST DE predict_exploding_games (données synthétiques)
# ===========================================================================

def test_predict_exploding_games() -> None:
    section("4. TEST — predict_exploding_games()")

    rng = np.random.default_rng(7)
    n   = 100
    test_raw = pd.DataFrame({
        "name":      [f"Game_{i}" for i in range(n)],
        "price":     rng.uniform(0, 60, n),
        "has_rpg":   rng.integers(0, 2, n),
        "has_indie": rng.integers(0, 2, n),
    })
    y_test  = pd.Series(rng.integers(0, 2, n))
    y_proba = np.clip(rng.uniform(0, 1, n), 0, 1)
    thr     = 0.5
    top_n   = 10

    # On attache l'étiquette originale AVANT l'appel pour pouvoir vérifier
    # que la watchlist ne contient que des non-tendances (y_test == 0).
    # predict_exploding_games fait reset_index(drop=True) en interne,
    # donc on reconstruit la correspondance via la colonne 'name'.
    test_raw_labeled = test_raw.copy()
    test_raw_labeled["_y_true"] = y_test.values
    y_by_name = test_raw_labeled.set_index("name")["_y_true"]

    result = predict_exploding_games(test_raw, y_test, y_proba, thr, top_n=top_n)

    subsection("Type et colonnes")
    check("Retour est un DataFrame",      isinstance(result, pd.DataFrame))
    check("Colonne 'proba_tendance'",     "proba_tendance" in result.columns)
    check("Colonne 'name'",               "name"           in result.columns)
    check("Colonne 'price'",              "price"          in result.columns)

    subsection("Valeurs")
    check(f"Au plus {top_n} lignes",      len(result) <= top_n,  f"lignes = {len(result)}")

    # Vérification robuste : on retrouve les vraies étiquettes via 'name'
    # (indépendant du reset_index interne à predict_exploding_games)
    if len(result) > 0 and "name" in result.columns:
        true_labels = result["name"].map(y_by_name)
        n_pos_in_watchlist = int((true_labels == 1).sum())
        check("Uniquement des non-tendances",
              n_pos_in_watchlist == 0,
              f"{n_pos_in_watchlist} tendance(s) trouvée(s) dans la watchlist — doit être 0")
    else:
        check("Uniquement des non-tendances", True)

    check("Trié par proba desc",
          result["proba_tendance"].is_monotonic_decreasing or len(result) <= 1)
    check("Probas dans [0,1]",            result["proba_tendance"].between(0, 1).all()
          if len(result) > 0 else True)


# ===========================================================================
# 5. TEST DE quick_test
# ===========================================================================

def test_quick_test() -> None:
    section("5. TEST — quick_test()")

    print("  ⏳ Exécution de quick_test()...")
    result = quick_test()

    subsection("Type et clés")
    check("Retour est un dict",           isinstance(result, dict))
    for key in ["n_games", "probas", "success", "error"]:
        check(f"Clé '{key}' présente",    key in result)

    subsection("Valeurs")
    if result.get("success"):
        check("success == True",          result["success"] is True)
        check("n_games > 0",              isinstance(result["n_games"], int) and result["n_games"] > 0,
              f"n_games = {result['n_games']}")
        check("probas est une liste",     isinstance(result["probas"], list))
        check("5 probabilités retournées",len(result["probas"]) == 5,
              f"len = {len(result['probas'])}")
        check("Probas dans [0,1]",        all(0.0 <= p <= 1.0 for p in result["probas"]),
              f"probas = {result['probas']}")
        check("error est None",           result["error"] is None)
    else:
        print(f"  ⚠️  quick_test a échoué : {result.get('error')}")
        check("error est une str",        isinstance(result.get("error"), str))


# ===========================================================================
# 6. TEST DE test_feature_engineering_games
# ===========================================================================

def test_full_pipeline() -> None:
    section("6. TEST — test_feature_engineering_games()  [PIPELINE COMPLET]")

    print("  ⏳ Exécution du pipeline complet (peut prendre quelques secondes)...")
    result = test_feature_engineering_games()

    # ── 6.1 Structure ────────────────────────────────────────────────────────
    subsection("6.1 Structure du dict de retour")
    expected_keys = [
        "accuracy", "roc_auc", "pr_auc", "f1",
        "optimal_threshold", "threshold_details",
        "confusion_matrix_optimal", "confusion_matrix_default",
        "trending_genres", "exploding_games",
        "cv_scores", "feature_importances",
        "y_proba", "y_pred", "y_test", "X_test", "error",
    ]
    check("Retour est un dict",           isinstance(result, dict))
    for key in expected_keys:
        check(f"Clé '{key}' présente",    key in result)

    # Arrêt anticipé si erreur pipeline
    if result.get("error") is not None:
        print(f"\n  ⛔ Pipeline en erreur : {result['error']}")
        print("     Tests de valeurs ignorés.")
        return

    # ── 6.2 Métriques scalaires ───────────────────────────────────────────────
    subsection("6.2 Métriques scalaires")
    for metric in ["accuracy", "roc_auc", "pr_auc", "f1"]:
        val = result[metric]
        check(f"{metric} est un float",       isinstance(val, float),      f"type = {type(val)}")
        check(f"{metric} dans [0, 1]",        0.0 <= val <= 1.0,           f"valeur = {val:.4f}")

    thr = result["optimal_threshold"]
    check("optimal_threshold est un float",   isinstance(thr, float))
    check("optimal_threshold dans [0, 1]",    0.0 <= thr <= 1.0,           f"valeur = {thr:.4f}")

    # ── 6.3 threshold_details ────────────────────────────────────────────────
    subsection("6.3 threshold_details")
    td = result["threshold_details"]
    check("threshold_details est un dict",    isinstance(td, dict))
    if isinstance(td, dict):
        check("threshold cohérent avec optimal_threshold",
              abs(td.get("threshold", -1) - thr) < 1e-9)
        check("f1 dans threshold_details",    "f1" in td)
        check("precisions array présent",     isinstance(td.get("precisions"), np.ndarray))
        check("recalls array présent",        isinstance(td.get("recalls"),    np.ndarray))
        check("thresholds array présent",     isinstance(td.get("thresholds"), np.ndarray))

    # ── 6.4 confusion_matrix_optimal ─────────────────────────────────────────
    subsection("6.4 confusion_matrix_optimal")
    cm_opt = result["confusion_matrix_optimal"]
    check("cm_optimal est un dict",           isinstance(cm_opt, dict))
    if isinstance(cm_opt, dict):
        for k in ["vn", "fp", "fn", "vp", "recall", "precision", "f1"]:
            check(f"cm_optimal['{k}'] présent", k in cm_opt)
        total = cm_opt.get("vn", 0) + cm_opt.get("fp", 0) + cm_opt.get("fn", 0) + cm_opt.get("vp", 0)
        n_test = len(result["y_test"]) if result["y_test"] is not None else -1
        check("vn+fp+fn+vp == len(y_test)",   total == n_test,             f"{total} vs {n_test}")
        check("recall dans [0,1]",            0.0 <= cm_opt["recall"]    <= 1.0)
        check("precision dans [0,1]",         0.0 <= cm_opt["precision"] <= 1.0)
        check("f1 dans [0,1]",                0.0 <= cm_opt["f1"]        <= 1.0)

    # ── 6.5 confusion_matrix_default ─────────────────────────────────────────
    subsection("6.5 confusion_matrix_default")
    cm_def = result["confusion_matrix_default"]
    check("cm_default est un dict",           isinstance(cm_def, dict))
    if isinstance(cm_def, dict):
        for k in ["vn", "fp", "fn", "vp"]:
            check(f"cm_default['{k}'] présent", k in cm_def)

    # ── 6.6 trending_genres ──────────────────────────────────────────────────
    subsection("6.6 trending_genres")
    tg = result["trending_genres"]
    check("trending_genres est un DataFrame", isinstance(tg, pd.DataFrame))
    if isinstance(tg, pd.DataFrame) and len(tg) > 0:
        for col in ["Genre", "Count", "Avg_Proba", "Trend_Ratio", "Avg_Proba_Trend", "Trend_Score"]:
            check(f"Colonne '{col}' présente",  col in tg.columns)
        check("Avg_Proba dans [0,1]",           tg["Avg_Proba"].between(0, 1).all())
        check("Trend_Ratio dans [0,1]",         tg["Trend_Ratio"].between(0, 1).all())
        check("Trend_Score >= 0",               (tg["Trend_Score"] >= 0).all())
        print(f"  📊 {len(tg)} genre(s) analysé(s)")
        print(f"  🏆 Top genre : {tg.iloc[0]['Genre']}  (score={tg.iloc[0]['Trend_Score']:.4f})")

    # ── 6.7 exploding_games ──────────────────────────────────────────────────
    subsection("6.7 exploding_games")
    eg = result["exploding_games"]
    check("exploding_games est un DataFrame", isinstance(eg, pd.DataFrame))
    if isinstance(eg, pd.DataFrame) and len(eg) > 0:
        check("Colonne 'proba_tendance'",       "proba_tendance" in eg.columns)
        check("Au plus 20 lignes",              len(eg) <= 20,               f"lignes = {len(eg)}")
        check("Probas dans [0,1]",              eg["proba_tendance"].between(0, 1).all())
        check("Trié par proba desc",
              eg["proba_tendance"].is_monotonic_decreasing or len(eg) <= 1)
        print(f"  💥 {len(eg)} jeu(x) à surveiller")
        if "name" in eg.columns:
            print(f"  🔥 N°1 : {eg.iloc[0]['name']}  (proba={eg.iloc[0]['proba_tendance']:.4f})")

    # ── 6.8 cv_scores ────────────────────────────────────────────────────────
    subsection("6.8 cv_scores")
    cv = result["cv_scores"]
    if cv is not None:
        check("cv_scores est un dict",          isinstance(cv, dict))
        for metric in ["f1", "roc_auc", "pr_auc"]:
            if metric in cv:
                m = cv[metric]
                check(f"cv['{metric}']['mean'] présent", "mean" in m)
                check(f"cv['{metric}']['std'] présent",  "std"  in m)
                check(f"cv['{metric}']['values'] liste",
                      isinstance(m.get("values"), list) and len(m["values"]) == 5)
                check(f"cv['{metric}'] mean dans [0,1]",
                      0.0 <= m["mean"] <= 1.0,            f"mean = {m['mean']:.4f}")
        print(f"  📈 CV F1      : {cv['f1']['mean']:.4f} ± {cv['f1']['std']:.4f}")
        print(f"  📈 CV ROC-AUC : {cv['roc_auc']['mean']:.4f} ± {cv['roc_auc']['std']:.4f}")
    else:
        print("  ℹ️  cv_scores = None (cross-val non disponible)")

    # ── 6.9 feature_importances ──────────────────────────────────────────────
    subsection("6.9 feature_importances")
    fi = result["feature_importances"]
    if fi is not None:
        check("feature_importances est un dict", isinstance(fi, dict))
        check("Au moins 1 feature",              len(fi) >= 1,              f"features = {len(fi)}")
        all_floats = all(isinstance(v, float) for v in fi.values())
        check("Toutes importances sont des float", all_floats)
        check("Importances >= 0",                all(v >= 0 for v in fi.values()))
        top_feat = max(fi, key=fi.get)
        print(f"  🌟 Feature la plus importante : '{top_feat}'  ({fi[top_feat]:.6f})")
    else:
        print("  ℹ️  feature_importances = None (non disponible pour ce modèle)")

    # ── 6.10 Arrays y_proba / y_pred / y_test ────────────────────────────────
    subsection("6.10 Arrays y_proba, y_pred, y_test")
    y_proba = result["y_proba"]
    y_pred  = result["y_pred"]
    y_test  = result["y_test"]
    X_test  = result["X_test"]

    check("y_proba est un ndarray",       isinstance(y_proba, np.ndarray))
    check("y_pred est un ndarray",        isinstance(y_pred,  np.ndarray))
    check("y_test est une Series",        isinstance(y_test,  pd.Series))
    check("X_test est un DataFrame",      isinstance(X_test,  pd.DataFrame))

    if y_proba is not None and y_pred is not None and y_test is not None:
        n = len(y_test)
        check("len(y_proba) == len(y_test)", len(y_proba) == n, f"{len(y_proba)} vs {n}")
        check("len(y_pred)  == len(y_test)", len(y_pred)  == n, f"{len(y_pred)} vs {n}")
        check("y_proba dans [0,1]",          ((y_proba >= 0) & (y_proba <= 1)).all())
        check("y_pred contient 0 et 1",      set(np.unique(y_pred)).issubset({0, 1}))
        check("y_test contient 0 et 1",      set(y_test.unique()).issubset({0, 1}))
        check("X_test.shape[0] == n",        X_test.shape[0] == n,
              f"{X_test.shape[0]} vs {n}")

        # Cohérence seuil optimal
        y_pred_recalc = (y_proba >= thr).astype(int)
        check("y_pred cohérent avec optimal_threshold",
              np.array_equal(y_pred, y_pred_recalc),
              "y_pred doit correspondre à (y_proba >= optimal_threshold)")


# ===========================================================================
# 7. RÉSUMÉ FINAL
# ===========================================================================

def print_summary() -> None:
    global PASS, FAIL
    total = PASS + FAIL
    pct   = (PASS / total * 100) if total > 0 else 0

    print("\n" + "═" * 65)
    print("  📋 RÉSUMÉ DES TESTS")
    print("═" * 65)
    print(f"  Total  : {total}")
    print(f"  ✅ PASS : {PASS}  ({pct:.1f}%)")
    print(f"  ❌ FAIL : {FAIL}")

    bar_len   = 40
    filled    = int(bar_len * PASS / total) if total > 0 else 0
    bar       = "█" * filled + "░" * (bar_len - filled)
    print(f"\n  [{bar}]  {pct:.0f}%")

    if FAIL == 0:
        print("\n  🎉 TOUS LES TESTS SONT PASSÉS!")
    else:
        print(f"\n  ⚠️  {FAIL} test(s) échoué(s) — vérifiez les messages ❌ ci-dessus.")
    print("═" * 65 + "\n")


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    mode_quick = len(sys.argv) > 1 and sys.argv[1] == "--quick"

    print("\n" + "═" * 65)
    print("  🧪 TEST_APPEL.PY — Validation des valeurs de retour")
    print("  Fichier source : test_pipeline.py")
    print("═" * 65)

    if mode_quick:
        # ── Mode rapide : teste uniquement les fonctions isolées + quick_test ──
        print("\n  Mode : --quick (fonctions unitaires + quick_test)\n")
        test_find_optimal_threshold()
        test_print_confusion_matrix()
        test_analyze_trending_genres()
        test_predict_exploding_games()
        test_quick_test()
    else:
        # ── Mode complet : toutes les fonctions + pipeline entier ──────────────
        print("\n  Mode : complet\n")
        test_find_optimal_threshold()
        test_print_confusion_matrix()
        test_analyze_trending_genres()
        test_predict_exploding_games()
        test_quick_test()
        test_full_pipeline()

    print_summary()