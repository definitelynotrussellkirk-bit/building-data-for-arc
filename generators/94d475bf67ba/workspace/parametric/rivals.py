"""Executable, task-local shortcut programs for nested-frame ownership.

Every source is evaluated by the unchanged protected Racket runtime.  The
``raw_contained_count`` counterfactual changes only the frame score: selection
uses all zero input cells inside a frame before subtracting inner ownership,
while painting still uses the true smallest-enclosing-frame ownership regions.

``all_fill`` is byte-identical to the canonical family setting and must not be
treated as a distinguishable hypothesis when that setting is the target.
"""
from pathlib import Path


def _replace(source: str, old: str, new: str) -> str:
    """Fail on source drift instead of silently returning the intended rule."""
    if source.count(old) != 1:
        raise ValueError(f"expected exactly one Racket mutation anchor: {old!r}")
    return source.replace(old, new, 1)


def programs() -> dict[str, str]:
    """Return complete runnable programs, loading only adjacent resources.

    Outermost/innermost choose one true ownership region.  Two-level truncation
    ignores the deepest operative frame before assigning ownership and scoring.
    Maximum-color ownership assigns each zero to its highest-colored enclosing
    frame before scoring.  Tie-first keeps only the smallest tied frame.
    Border-count adds colored perimeter cells to the owned-zero selection score.
    Selected-containment keeps true scores but paints the smallest selected
    enclosing frame even when an unselected smaller frame owns that zero.
    """
    home = Path(__file__).resolve().parent
    canonical = (home / "canonical.rkt").read_text(encoding="utf-8")
    largest = (home / "largest_owned.rkt").read_text(encoding="utf-8")
    score = "(define (score obj) (owned-count obj))"
    chosen = "(define chosen selected)"
    return {
        "raw_contained_count": _replace(
            largest, score, "(define (score obj) (raw-contained-count obj))"
        ),
        "outermost_only": _replace(
            largest,
            chosen,
            "(define chosen (if (empty? frames) '() (list (last frames))))",
        ),
        "innermost_only": _replace(
            largest,
            chosen,
            "(define chosen (if (empty? frames) '() (list (first frames))))",
        ),
        "all_fill": canonical,
        "canonical_two_levels": _replace(
            canonical,
            "                              frames)))",
            "                              (drop frames (max 0 (- (length frames) 2))))))",
        ),
        "canonical_maximum_color_owner": _replace(
            canonical,
            "(obj-color (first hits))",
            "(obj-color (first (sort hits "
            "(lambda (a b) (> (obj-color a) (obj-color b))))))",
        ),
        "two_levels_only": _replace(
            largest,
            "(define ownership-frames frames)",
            "(define ownership-frames (drop frames (max 0 (- (length frames) 2))))",
        ),
        "maximum_color_owner": _replace(
            largest,
            "(if (empty? hits) #f (first hits))",
            "(if (empty? hits) #f "
            "(first (sort hits (lambda (a b) (> (obj-color a) (obj-color b))))))",
        ),
        "tie_first_only": _replace(
            largest,
            chosen,
            "(define chosen (if (empty? selected) '() (list (first selected))))",
        ),
        "border_count_in_score": _replace(
            largest, score, "(define (score obj) (+ (owned-count obj) (obj-size obj)))"
        ),
        "selected_containment_paint": _replace(
            largest,
            "(let ((who (owner r c)))",
            "(let* ((hits (filter (lambda (obj) (inside? obj r c)) chosen)) "
            "(who (if (empty? hits) #f (first hits))))",
        ),
    }
