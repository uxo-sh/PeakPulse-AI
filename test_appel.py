"""
test_appel.py — Fichier de test des valeurs de retour de trend_engine_games.py

Ce fichier appelle les fonctions de trend_engine_games.py et vérifie :
  - que chaque valeur de retour est bien présente
  - que les types sont corrects
  - que les valeurs sont dans des plages attendues
"""

import sys
import numpy as np
import pandas as pd

# ── Import des fonctions depuis trend_engine_games ────────────────────────────────
from trend_engine_games import (
    get_games_trend_results,
    find_optimal_threshold,
    analyze_trending_genres,
    predict_exploding_games,
    create_trend_target,
    LEAK_COLS,
    TARGET_COL
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
    check("precisions est une liste",     isinstance(result["precisions"], list))
    check("recalls est une liste",        isinstance(result["recalls"],    list))
    check("thresholds est une liste",     isinstance(result["thresholds"], list))
    check("len(precisions) >= 2",         len(result["precisions"]) >= 2)

# ===========================================================================
# 2. TEST DE analyze_trending_genres (données synthétiques)
# ===========================================================================

def test_analyze_trending_genres() -> None:
    section("2. TEST — analyze_trending_genres()")

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
# 3. TEST DE predict_exploding_games (données synthétiques)
# ===========================================================================

def test_predict_exploding_games() -> None:
    section("3. TEST — predict_exploding_games()")

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

    test_raw_labeled = test_raw.copy()
    test_raw_labeled["_y_true"] = y_test.values
    y_by_name = test_raw_labeled.set_index("name")["_y_true"]

    result = predict_exploding_games(test_raw, y_test, y_proba, top_n=top_n)

    subsection("Type et colonnes")
    check("Retour est un DataFrame",      isinstance(result, pd.DataFrame))
    check("Colonne 'proba_tendance'",     "proba_tendance" in result.columns)
    check("Colonne 'name'",               "name"           in result.columns)
    check("Colonne 'price'",              "price"          in result.columns)

    subsection("Valeurs")
    check(f"Au plus {top_n} lignes",      len(result) <= top_n,  f"lignes = {len(result)}")

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
# 4. TEST DE get_games_trend_results
# ===========================================================================

def test_full_pipeline() -> None:
    section("4. TEST — get_games_trend_results()  [MOTEUR JEUX COMPLET]")

    print("  ⏳ Exécution du moteur complet (peut prendre quelques secondes)...")
    try:
        result = get_games_trend_results()
    except Exception as e:
        print(f"\n  ⛔ Pipeline en erreur : {e}")
        print("     Tests de valeurs ignorés.")
        return

    # ── 4.1 Structure ────────────────────────────────────────────────────────
    subsection("4.1 Structure du dict de retour")
    expected_keys = ["metrics", "trends", "optimal_threshold"]
    check("Retour est un dict",           isinstance(result, dict))
    for key in expected_keys:
        check(f"Clé '{key}' présente",    key in result)

    if not isinstance(result, dict):
        return

    # ── 4.2 Métriques scalaires ───────────────────────────────────────────────
    subsection("4.2 Métriques")
    m = result.get("metrics", {})
    check("'metrics' est un dict", isinstance(m, dict))
    for metric in ["recall", "precision", "f1", "auc"]:
        val = m.get(metric)
        check(f"metrics['{metric}'] présent", val is not None)
        if val is not None:
            check(f"{metric} est un float", isinstance(val, float))
            check(f"{metric} dans [0, 1]", 0.0 <= val <= 1.0)
            
    thr = result.get("optimal_threshold")
    check("optimal_threshold est un float", isinstance(thr, float))
    check("optimal_threshold dans [0, 1]", 0.0 <= thr <= 1.0)

    # ── 4.3 Trends (Liste de Dictionnaires) ────────────────────────────────────
    subsection("4.3 Structure Trends")
    t = result.get("trends", {})
    check("'trends' est un dict", isinstance(t, dict))
    
    eg = t.get("exploding_games")
    check("exploding_games est une liste", isinstance(eg, list))
    if isinstance(eg, list) and len(eg) > 0:
        check("Eléments de la liste sont des dict", isinstance(eg[0], dict))
        check("Présence clé 'proba_tendance' dans l'élément", "proba_tendance" in eg[0])
        
    en = t.get("emergent_genres")
    check("emergent_genres est une liste", isinstance(en, list))

# ===========================================================================
# 5. RÉSUMÉ FINAL
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
    print("  🧪 TEST_APPEL.PY — Validation du Moteur de Jeux")
    print("  Fichier source : trend_engine_games.py")
    print("═" * 65)

    if mode_quick:
        # ── Mode rapide : teste uniquement les fonctions isolées ──
        print("\n  Mode : --quick (fonctions unitaires uniquement)\n")
        test_find_optimal_threshold()
        test_analyze_trending_genres()
        test_predict_exploding_games()
    else:
        # ── Mode complet : toutes les fonctions + pipeline entier ──────────────
        print("\n  Mode : complet\n")
        test_find_optimal_threshold()
        test_analyze_trending_genres()
        test_predict_exploding_games()
        test_full_pipeline()

    print_summary()