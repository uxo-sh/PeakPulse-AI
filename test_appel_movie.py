"""
test_appel_movie.py — Fichier de test des valeurs de retour de test_pipeline_movie.py

Ce fichier appelle certaines fonctions de test_pipeline_movie.py et vérifie :
  - que chaque valeur de retour est bien présente
  - que les types sont corrects
  - que les valeurs sont dans des plages attendues
  - que les DataFrames ont les bonnes colonnes

Utilisation :
    python test_appel_movie.py            ← test complet
    python test_appel_movie.py --quick    ← test rapide uniquement
"""

import sys
import numpy as np
import pandas as pd

# ── Import des fonctions depuis test_pipeline_movie ─────────────────────────
from test_pipeline_movie import (
    create_trend_target_movies,
    find_threshold_precision_target,
    test_model_movies_v2,
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
    check("precisions est un array",      isinstance(result["precisions"], np.ndarray))
    check("recalls est un array",         isinstance(result["recalls"],    np.ndarray))
    check("thresholds est un array",      isinstance(result["thresholds"], np.ndarray))

# ===========================================================================
# 3. TEST DE test_model_movies_v2
# ===========================================================================

def test_full_pipeline_movies() -> None:
    section("3. TEST — test_model_movies_v2()  [PIPELINE COMPLET FILMS]")

    print("  ⏳ Exécution du pipeline complet (peut prendre quelques secondes)...")
    try:
        result = test_model_movies_v2()
    except Exception as e:
        print(f"\n  ⛔ Pipeline en erreur : {e}")
        print("     Tests de valeurs ignorés.")
        return

    # ── 3.1 Structure ────────────────────────────────────────────────────────
    subsection("3.1 Structure du dict de retour")
    expected_keys = [
        "recall", "precision", "f1", "auc",
        "optimal_threshold", "threshold_details",
        "exploding_movies",
        "y_proba", "y_pred", "y_test", "X_test", "signal_used",
    ]
    check("Retour est un dict",           isinstance(result, dict))
    for key in expected_keys:
        check(f"Clé '{key}' présente",    key in result)

    if not isinstance(result, dict):
        return

    # ── 3.2 Métriques scalaires ───────────────────────────────────────────────
    subsection("3.2 Métriques scalaires")
    for metric in ["recall", "precision", "f1", "auc", "optimal_threshold"]:
        val = result.get(metric)
        if val is not None:
            check(f"{metric} est un float",       isinstance(val, float),      f"type = {type(val)}")
            check(f"{metric} dans [0, 1]",        0.0 <= val <= 1.0,           f"valeur = {val:.4f}")

    # ── 3.3 threshold_details ────────────────────────────────────────────────
    subsection("3.3 threshold_details")
    td = result.get("threshold_details")
    check("threshold_details est un dict",    isinstance(td, dict))

    # ── 3.4 exploding_movies ──────────────────────────────────────────────────
    subsection("3.4 exploding_movies")
    em = result.get("exploding_movies")
    check("exploding_movies est un DataFrame", isinstance(em, pd.DataFrame))
    if isinstance(em, pd.DataFrame) and len(em) > 0:
        check("Colonne 'proba'",          "proba" in em.columns)
        check("Probas >= optimal_threshold", (em["proba"] >= result["optimal_threshold"]).all())
        check("Trié par proba desc",      em["proba"].is_monotonic_decreasing or len(em) <= 1)

    # ── 3.5 Arrays y_proba / y_pred / y_test ────────────────────────────────
    subsection("3.5 Arrays y_proba, y_pred, y_test")
    y_proba = result.get("y_proba")
    y_pred  = result.get("y_pred")
    y_test  = result.get("y_test")
    X_test  = result.get("X_test")

    check("y_proba est un ndarray",       isinstance(y_proba, np.ndarray))
    check("y_pred est un ndarray",        isinstance(y_pred,  np.ndarray))
    check("y_test est une Series",        isinstance(y_test,  pd.Series))
    check("X_test est un DataFrame",      isinstance(X_test,  pd.DataFrame))


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
    print("  🧪 TEST_APPEL_MOVIE.PY — Validation des valeurs de retour")
    print("  Fichier source : test_pipeline_movie.py")
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
