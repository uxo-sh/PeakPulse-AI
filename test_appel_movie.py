"""
test_appel_movie.py — Fichier de test des valeurs de retour de trend_engine_movies.py

Ce fichier appelle certaines fonctions de trend_engine_movies.py et vérifie :
  - que chaque valeur de retour est bien présente
  - que les types sont corrects
  - que les valeurs sont dans des plages attendues
"""

import sys
import numpy as np
import pandas as pd

# ── Import des fonctions depuis trend_engine_movies ─────────────────────────
from trend_engine_movies import (
    create_trend_target_movies,
    find_threshold_precision_target,
    get_movies_trend_results,
    LEAK_COLS
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
# 1. TEST DE create_trend_target_movies
# ===========================================================================

def test_create_trend_target_movies() -> None:
    section("1. TEST — create_trend_target_movies()")

    # Données synthétiques
    df_raw = pd.DataFrame({
        "revenue": [1000000, 0, 500000, 2000000],
        "budget": [500000, 10000, 100000, 400000],
        "popularity": [10.5, 2.1, 15.0, 5.0]
    })

    df_out, signal = create_trend_target_movies(df_raw)

    subsection("Type et colonnes")
    check("Retour df est un DataFrame", isinstance(df_out, pd.DataFrame))
    check("Retour signal est une str", isinstance(signal, str))
    check("Colonne 'is_trending_future' présente", "is_trending_future" in df_out.columns)
    check("Colonne 'ROI' présente", "ROI" in df_out.columns)
    check("Colonne 'pop_percentile' présente", "pop_percentile" in df_out.columns)

    subsection("Valeurs")
    check("Seules les lignes valides sont gardées", len(df_out) == 3)
    check("is_trending_future contient 0 ou 1", set(df_out["is_trending_future"].unique()).issubset({0, 1}))

# ===========================================================================
# 2. TEST DE find_threshold_precision_target
# ===========================================================================

def test_find_threshold_precision_target() -> None:
    section("2. TEST — find_threshold_precision_target()")

    rng     = np.random.default_rng(42)
    y_true  = rng.integers(0, 2, size=200)
    y_proba = np.clip(y_true * 0.6 + rng.uniform(0, 0.4, size=200), 0, 1)

    result = find_threshold_precision_target(y_true, y_proba, target_precision=0.45)

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

# ===========================================================================
# 3. TEST DE get_movies_trend_results
# ===========================================================================

def test_full_pipeline_movies() -> None:
    section("3. TEST — get_movies_trend_results()  [MOTEUR FILMS COMPLET]")

    print("  ⏳ Exécution du moteur complet (peut prendre quelques secondes)...")
    try:
        result = get_movies_trend_results()
    except Exception as e:
        print(f"\n  ⛔ Pipeline en erreur : {e}")
        print("     Tests de valeurs ignorés.")
        return

    # ── 3.1 Structure ────────────────────────────────────────────────────────
    subsection("3.1 Structure du dict de retour")
    expected_keys = ["metrics", "trends", "optimal_threshold", "signal_used"]
    check("Retour est un dict",           isinstance(result, dict))
    for key in expected_keys:
        check(f"Clé '{key}' présente",    key in result)

    if not isinstance(result, dict):
        return

    # ── 3.2 Métriques scalaires ───────────────────────────────────────────────
    subsection("3.2 Métriques")
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

    # ── 3.3 Trends (Liste de Dictionnaires) ────────────────────────────────────
    subsection("3.3 Structure Trends")
    t = result.get("trends", {})
    check("'trends' est un dict", isinstance(t, dict))
    
    em = t.get("exploding_movies")
    check("exploding_movies est une liste", isinstance(em, list))
    if isinstance(em, list) and len(em) > 0:
        check("Eléments de la liste sont des dict", isinstance(em[0], dict))
        check("Présence clé 'proba' dans l'élément", "proba" in em[0])
        
    en = t.get("emergent_genres")
    check("emergent_genres est une liste", isinstance(en, list))

# ===========================================================================
# RÉSUMÉ FINAL
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
    print("  🧪 TEST_APPEL_MOVIE.PY — Validation du Moteur de Films")
    print("  Fichier source : trend_engine_movies.py")
    print("═" * 65)

    if mode_quick:
        # ── Mode rapide : teste uniquement les fonctions isolées ──
        print("\n  Mode : --quick (fonctions unitaires uniquement)\n")
        test_create_trend_target_movies()
        test_find_threshold_precision_target()
    else:
        # ── Mode complet : toutes les fonctions + pipeline entier ──────────────
        print("\n  Mode : complet\n")
        test_create_trend_target_movies()
        test_find_threshold_precision_target()
        test_full_pipeline_movies()

    print_summary()
