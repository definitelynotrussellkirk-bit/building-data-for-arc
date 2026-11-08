"""
Auto-scan and suggest — run all features and recommend likely rules.

auto_scan: runs all relevant features, ranks by informativeness.
suggest: maps feature profiles to likely templates/rules.

Toggle: auto_scan_on_load=True during inference, False during training.
"""

import numpy as np
from .features import PAIR_FEATURES, GRID_FEATURES, TASK_FEATURES
from .grid_ops import find_objects, find_enclosed


def auto_scan(task):
    """Run all features on a task. Returns ranked list of (feature_name, score, summary)."""
    results = {}
    summaries = {}

    # Task-level features
    for fname, fn in TASK_FEATURES.items():
        try:
            r = fn(task)
            results[fname] = r
            summaries[fname] = _summarize(fname, r)
        except Exception:
            pass

    # Pair-level features on all train pairs
    for fname, fn in PAIR_FEATURES.items():
        pair_results = []
        for i, pair in enumerate(task["train"]):
            if "output" not in pair:
                continue
            try:
                r = fn(pair["input"], pair["output"])
                pair_results.append(r)
            except Exception:
                pass
        if pair_results:
            results[fname] = pair_results
            summaries[fname] = _summarize_pairs(fname, pair_results)

    # Grid-level features on first input and output
    if task["train"]:
        pair0 = task["train"][0]
        for fname, fn in GRID_FEATURES.items():
            try:
                r_in = fn(pair0["input"])
                results[f"{fname}_input"] = r_in
                summaries[f"{fname}_input"] = _summarize(fname, r_in, "input")
            except Exception:
                pass
            if "output" in pair0:
                try:
                    r_out = fn(pair0["output"])
                    results[f"{fname}_output"] = r_out
                except Exception:
                    pass

    # Score and rank
    scored = []
    for fname, summary in summaries.items():
        score = _score_feature(fname, results.get(fname))
        if score > 0:
            scored.append((fname, score, summary))

    scored.sort(key=lambda x: -x[1])
    return scored, results


def suggest(task, scan_results=None):
    """Suggest likely rules based on feature profile.

    Returns list of (template_expr, confidence, description).
    """
    if scan_results is None:
        _, scan_results = auto_scan(task)

    suggestions = []

    # Check consistent mapping
    cm = scan_results.get("consistent_mapping", {})
    if isinstance(cm, dict) and cm.get("consistent") and cm.get("mapping"):
        mapping = cm["mapping"]
        # Filter to actual changes
        changes = {k: v for k, v in mapping.items() if k != v}
        if changes:
            suggestions.append((
                f'(template! recolor_map {changes})',
                0.95,
                f"consistent color mapping: {changes}"
            ))

    # Check color roles
    cr = scan_results.get("color_roles", {})
    if isinstance(cr, dict):
        sources = [c for c, info in cr.items() if isinstance(info, dict) and info.get("role") == "source"]
        targets = [c for c, info in cr.items() if isinstance(info, dict) and info.get("role") == "target"]
        if sources and targets and len(sources) == 1 and len(targets) == 1:
            suggestions.append((
                f'(rule! (lambda (g) (recolor g {sources[0]} {targets[0]})))',
                0.85,
                f"single source→target: {sources[0]}→{targets[0]}"
            ))

    # Check enclosure
    enc = scan_results.get("enclosure_input", {})
    if isinstance(enc, dict) and enc.get("count", 0) > 0:
        suggestions.append((
            '(template! fill_enclosed)',
            0.70,
            f"enclosed regions detected ({enc['count']} cells)"
        ))

    # Check lattice
    lat = scan_results.get("lattice_input", {})
    if isinstance(lat, dict) and lat.get("detected"):
        suggestions.append((
            f'lattice detected: {lat.get("shape")} tiles, {lat.get("n_signals")} signals',
            0.65,
            "lattice/tile pattern"
        ))

    # Check symmetry
    sym = scan_results.get("symmetry_input", {})
    if isinstance(sym, dict):
        if sym.get("mirror_lr") and not sym.get("mirror_ud"):
            suggestions.append(('(template! complete_symmetry "ud")', 0.50, "has LR symmetry, may need UD"))
        if sym.get("mirror_ud") and not sym.get("mirror_lr"):
            suggestions.append(('(template! complete_symmetry "lr")', 0.50, "has UD symmetry, may need LR"))

    # Check shape change
    sc = scan_results.get("shape_change", [])
    if isinstance(sc, list) and sc:
        ratios = set(tuple(r.get("ratio", (1, 1))) for r in sc if isinstance(r, dict))
        if len(ratios) == 1:
            ratio = list(ratios)[0]
            if ratio != (1.0, 1.0):
                if ratio[0] == ratio[1] and ratio[0] > 1:
                    suggestions.append((
                        f'(template! upscale {int(ratio[0])})',
                        0.60,
                        f"output is {ratio[0]}x scaled"
                    ))

    # Check diff patterns
    diffs = scan_results.get("diff", [])
    if isinstance(diffs, list) and diffs:
        # All same transitions?
        all_trans = [set(d.get("transitions", {}).keys()) for d in diffs if isinstance(d, dict)]
        if all_trans and all(t == all_trans[0] for t in all_trans):
            suggestions.append((
                f'consistent transitions: {all_trans[0]}',
                0.60,
                "same color changes in every pair"
            ))

    # Check object count change
    occ = scan_results.get("object_count_change", [])
    if isinstance(occ, list) and occ:
        deltas = set(r.get("delta", 0) for r in occ if isinstance(r, dict))
        if deltas == {0}:
            suggestions.append(("objects preserved (count unchanged)", 0.30, "same number of objects"))

    suggestions.sort(key=lambda x: -x[1])
    return suggestions


def _summarize(fname, result, context=""):
    """One-line summary of a feature result."""
    prefix = f"({context}) " if context else ""
    if isinstance(result, dict):
        if "error" in result:
            return f"{prefix}{fname}: {result['error']}"
        if "detected" in result:
            return f"{prefix}{fname}: {'yes' if result['detected'] else 'no'}"
        if "count" in result:
            return f"{prefix}{fname}: {result['count']} items"
        if "consistent" in result:
            return f"{prefix}{fname}: {'consistent' if result['consistent'] else 'varies'}"
        # Generic: first 3 keys
        keys = [k for k in result if not k.startswith("_")][:3]
        parts = [f"{k}={result[k]}" for k in keys]
        return f"{prefix}{fname}: {', '.join(parts)}"
    if isinstance(result, list):
        return f"{prefix}{fname}: {len(result)} items"
    return f"{prefix}{fname}: {result}"


def _summarize_pairs(fname, pair_results):
    """Summarize pair-level results across all pairs."""
    if not pair_results:
        return f"{fname}: no results"
    if isinstance(pair_results[0], dict):
        # Summarize first pair
        r = pair_results[0]
        if "changed" in r:
            total_changed = sum(p.get("changed", 0) for p in pair_results)
            return f"{fname}: {total_changed} total changes across {len(pair_results)} pairs"
        if "vanished" in r:
            total = {k: sum(p.get(k, 0) for p in pair_results)
                    for k in ["vanished", "appeared", "recolored"]}
            return f"{fname}: {total}"
    return f"{fname}: {len(pair_results)} pairs analyzed"


def _score_feature(fname, result):
    """Score how informative a feature is (0-1)."""
    if result is None:
        return 0

    scores = {
        "consistent_mapping": 0.95,
        "color_roles": 0.85,
        "frames": 0.82,
        "lines": 0.80,
        "regularity": 0.78,
        "motion": 0.76,
        "scattered": 0.74,
        "shape_change": 0.72,
        "diff": 0.70,
        "change_type": 0.65,
        "object_count_change": 0.55,
        "enclosure_input": 0.50,
        "lattice_input": 0.50,
        "symmetry_input": 0.45,
        "periodicity_input": 0.40,
    }

    base = scores.get(fname, 0.20)

    # Boost if result is actually informative
    if isinstance(result, dict):
        if result.get("consistent"):
            base += 0.1
        if result.get("detected"):
            base += 0.1
        if result.get("count", 0) > 0:
            base += 0.05

    return min(base, 1.0)
