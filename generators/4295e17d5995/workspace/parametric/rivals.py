"""Executable finite rivals for the matching/opposite wall family.

Each rival is a total Racket grid program over the family's admitted input
grammar.  Except for identity, its source is a checked local transformation of
the exact adjacent canonical authority.  These are a finite teaching audit,
not a claim that the demonstrated rule is uniquely identifiable among all
possible programs.

The nearest/farthest rivals choose each object's direction from the mean of
its original cell columns.  They retain the selected rule's color-group and
component processing order and its settled-result collision scan.  A midpoint
tie chooses right for nearest and left for farthest.
"""
from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from pathlib import Path


_MATCHING = "(list (list lw -1) (list rw 1))"
_OPPOSITE = "(list (list lw 1) (list rw -1))"
_RIGHT_SCAN = "(= (hash-ref result (list r (+ t 1)) 0) bg)"
_LEFT_SCAN = "(= (hash-ref result (list r (- t 1)) 0) bg)"
_SORT_START = "(set! all-objects\n          (sort all-objects"
_OBJECT_START = "(for ((obj all-objects))\n          (let ((min-shift 999))"
_NEIGHBORS_8 = """(list (list (- cr 1) (- cc 1)) (list (- cr 1) cc) (list (- cr 1) (+ cc 1))
                               (list cr (- cc 1)) (list cr (+ cc 1))
                               (list (+ cr 1) (- cc 1)) (list (+ cr 1) cc) (list (+ cr 1) (+ cc 1)))"""
_NEIGHBORS_4 = """(list (list (- cr 1) cc)
                               (list cr (- cc 1)) (list cr (+ cc 1))
                               (list (+ cr 1) cc))"""


def _replace_once(source: str, old: str, new: str, operation: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(
            f"canonical source no longer supports {operation}: "
            f"expected one anchor, found {count}"
        )
    return source.replace(old, new, 1)


@cache
def _canonical() -> str:
    """Read exact local source lazily, after the prototype has been created."""
    return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def _selected(relation: str) -> str:
    source = _canonical()
    if source.count(_MATCHING) != 1:
        raise ValueError("canonical source must contain one matching direction list")
    if relation == "matching":
        return source
    return _replace_once(source, _MATCHING, _OPPOSITE, "opposite-wall direction")


def _position_direction(source: str, *, farthest: bool) -> str:
    left, right = (1, -1) if farthest else (-1, 1)
    replacement = (
        "(for ((obj all-objects))\n"
        "          (let ((dir (if (< (* 2 (apply + (map second obj)))\n"
        "                             (* (- w 1) (length obj)))\n"
        f"                         {left} {right}))\n"
        "                (min-shift 999))"
    )
    return _replace_once(source, _OBJECT_START, replacement, "position-based direction")


def programs(settings: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return named exact Racket sources for the selected episode setting."""
    if settings is None:
        settings = {}
    if not isinstance(settings, Mapping):
        raise TypeError("settings must be a mapping")
    unknown = set(settings) - {"wall_relation"}
    if unknown:
        raise ValueError(f"unknown settings: {sorted(unknown)!r}")
    relation = settings.get("wall_relation", "matching")
    if relation not in ("matching", "opposite"):
        raise ValueError("wall_relation must be 'matching' or 'opposite'")

    source = _selected(relation)
    independent = _replace_once(
        source, _RIGHT_SCAN, "(< (+ t 1) (- w 1))", "ignore rightward settled blockers"
    )
    independent = _replace_once(
        independent, _LEFT_SCAN, "(> (- t 1) 0)", "ignore leftward settled blockers"
    )
    cellwise = _replace_once(
        source,
        _SORT_START,
        "(set! all-objects\n"
        "          (apply append (map (lambda (cells) (map list cells)) all-objects)))\n"
        "        " + _SORT_START,
        "split rigid objects into independently sorted cells",
    )
    connectivity4 = _replace_once(
        source, _NEIGHBORS_8, _NEIGHBORS_4, "use four-neighbor components"
    )
    return {
        "other_setting": _selected("opposite" if relation == "matching" else "matching"),
        "independent_no_blocking": independent,
        "cellwise": cellwise,
        "connectivity4": connectivity4,
        "identity": "(rule! (lambda (g) g))",
        "nearest_wall": _position_direction(source, farthest=False),
        "farthest_wall": _position_direction(source, farthest=True),
    }
