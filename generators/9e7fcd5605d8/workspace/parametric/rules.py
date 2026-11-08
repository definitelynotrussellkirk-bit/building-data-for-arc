"""Standalone Racket programs for the finite enclosed-hole-count family.

Object membership always uses same-color four-connectivity on background zero.
The connectivity option applies only to zero regions in each object's normalized
bounding-box mask.  This module builds source text; protected Racket is the
execution authority.
"""
from __future__ import annotations


def count_rule(
    min_holes: int,
    *,
    connectivity: int = 4,
    include_exterior: bool = False,
    score: str = "regions",
    exact: bool = False,
    constant: int | None = None,
) -> str:
    """Recolor original object cells to 8 when their score passes, else 4.

    ``regions`` counts retained zero components; ``cells`` sums their areas.
    ``missing`` counts every zero cell in the mask, including exterior cells.
    Only ``include_exterior=True`` retains regions touching the bounding-box rim.
    ``constant`` bypasses the predicate and recolors all foreground to 4 or 8.
    Thresholds are positive exact integers; the finite family itself uses 1 or 2.
    """
    if type(min_holes) is not int or min_holes < 1:
        raise ValueError("min_holes must be a positive exact integer")
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be the exact integer 4 or 8")
    if type(include_exterior) is not bool:
        raise ValueError("include_exterior must be a boolean")
    if type(exact) is not bool:
        raise ValueError("exact must be a boolean")
    if type(score) is not str or score not in ("regions", "cells", "missing"):
        raise ValueError("score must be regions, cells, or missing")
    if constant is not None and (type(constant) is not int or constant not in (4, 8)):
        raise ValueError("constant must be None or the exact integer 4 or 8")

    if constant is not None:
        return f"""(rule!
  (for/fold ((out g)) ((obj (in-list (objects g 0))))
    (paint-cells out (obj-cells obj) {constant})))"""

    finder = "objects" if connectivity == 4 else "objects-8"
    retained = "regions" if include_exterior else """(filter
                 (lambda (region)
                   (not (any? (lambda (p)
                                (or (= (first p) 0) (= (first p) (- h 1))
                                    (= (second p) 0) (= (second p) (- w 1))))
                              region)))
                 regions)"""
    score_expression = {
        "regions": "(length retained)",
        "cells": "(apply + (map length retained))",
        "missing": "(apply + (map length regions))",
    }[score]
    comparison = "=" if exact else ">="
    return f"""(rule!
  (for/fold ((out g)) ((obj (in-list (objects g 0))))
    (let* ((cells (obj-cells obj))
           (bb (bbox-of-cells cells))
           (r0 (first bb))
           (c0 (second bb))
           (h (+ 1 (- (third bb) r0)))
           (w (+ 1 (- (fourth bb) c0)))
           (norm (map (lambda (p)
                        (list (- (first p) r0) (- (second p) c0)))
                      cells))
           (mask (paint-cells (empty-grid h w 0) norm 1))
           (regions (map obj-cells ({finder} mask 1)))
           (retained {retained})
           (hole-score {score_expression}))
      (paint-cells out cells (if ({comparison} hole-score {min_holes}) 8 4)))))"""


def rival_programs(settings: dict) -> dict[str, str]:
    """Return plausible finite rivals, removing identical program text.

    At threshold one, positive enclosed-cell count is observationally equivalent
    to positive enclosed-region count.  ``hole_cell_threshold`` is deliberately
    retained so callers can report that equivalence instead of claiming it was
    refuted.  Duplicate missing-cell programs retain the ``bbox_nonfull`` name.
    """
    if (type(settings) is not dict or set(settings) != {"min_holes"}
            or type(settings["min_holes"]) is not int
            or settings["min_holes"] not in (1, 2)):
        raise ValueError("settings must be exactly {'min_holes': 1 or 2}")
    threshold = settings["min_holes"]
    candidates = {
        "wrong_threshold": count_rule(3 - threshold),
        "bbox_nonfull": count_rule(1, score="missing"),
        "missing_cell_threshold": count_rule(threshold, score="missing"),
        "hole_cell_threshold": count_rule(threshold, score="cells"),
        "including_exterior": count_rule(threshold, include_exterior=True),
        "eight_connected_holes": count_rule(threshold, connectivity=8),
        "exactly_threshold": count_rule(threshold, exact=True),
        "all_foreground_4": count_rule(threshold, constant=4),
        "all_foreground_8": count_rule(threshold, constant=8),
    }
    seen = {count_rule(threshold)}
    result = {}
    for name, program in candidates.items():
        if program not in seen:
            result[name] = program
            seen.add(program)
    return result
