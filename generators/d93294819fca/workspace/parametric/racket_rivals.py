"""Executable finite rivals for the adjacent gray-bridge prototype.

These are audit counterfactuals, not accepted family settings.  Racket's stable
sort preserves the row-major discovery order used by the Python rivals, including
ties.  Empty eligible sets leave the setting's working grid unchanged.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


_path = Path(__file__).resolve().with_name("prototype.py")
_spec = importlib.util.spec_from_file_location("_d93294819fca_rival_prototype", _path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load adjacent prototype: {_path}")
_prototype = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prototype)

_DIRECTIONS = "'((-1 0) (1 0) (0 -1) (0 1))"
_GREEN = "(filter (lambda (o) (= (obj-color o) 3)) (objects working 0))"
_ORIGINAL = "(filter (lambda (o) (= (obj-color o) 3)) (objects g 0))"


def program(role: str, name: str) -> str:
    """Return a protected-Racket-compatible rival matching ``rival_output``."""
    if (type(role) is not str or role not in _prototype.RIVALS
            or type(name) is not str or name not in _prototype.RIVALS[role]):
        raise ValueError("unknown rival or role")
    if name == "other_setting":
        return _prototype.program({"gray_role": "bridge" if role == "inert" else "inert"})

    working = "g" if role == "inert" or name == "wrong_order" else "(recolor g 5 3)"
    eligible = "comps"
    score = "(obj-size o)"
    comparison = "<"

    if name == "first":
        score = "0"
    elif name == "last":
        eligible, score = "(reverse comps)", "0"
    elif name == "largest":
        comparison = ">"
    elif name == "fixed_size_two":
        eligible = "(filter (lambda (o) (= (obj-size o) 2)) comps)"
    elif name == "bbox_smallest":
        score = """(let ((b (obj-bbox o)))
                   (* (+ 1 (- (third b) (first b)))
                      (+ 1 (- (fourth b) (second b)))))"""
    elif name == "smallest_perimeter":
        score = f"""(for*/sum ([p (in-list (obj-cells o))]
                              [d (in-list {_DIRECTIONS})])
                   (if (member (list (+ (first p) (first d))
                                     (+ (second p) (second d)))
                               (obj-cells o))
                       0 1))"""
    elif name == "ignore_gray_area":
        score = """(for/sum ([p (in-list (obj-cells o))])
                   (if (= (cell-at g (first p) (second p)) 3) 1 0))"""
    elif name == "original_anchor":
        eligible = f"""(let ((anchor
                           (obj-cells
                             (first (sort {_ORIGINAL}
                                          (lambda (a b) (< (obj-size a) (obj-size b))))))))
                     (filter
                       (lambda (o)
                         (andmap (lambda (p) (member p (obj-cells o))) anchor))
                       comps))"""
    elif name in ("smallest_bridged", "smallest_unbridged"):
        if role == "bridge":
            marked = """(ormap (lambda (p)
                                  (= (cell-at g (first p) (second p)) 5))
                                (obj-cells o))"""
        else:
            marked = f"""(for*/or ([p (in-list (obj-cells o))]
                                   [d (in-list {_DIRECTIONS})])
                          (let ((r (+ (first p) (first d)))
                                (c (+ (second p) (second d))))
                            (and (<= 0 r) (< r (rows g))
                                 (<= 0 c) (< c (cols g))
                                 (= (cell-at g r c) 5))))"""
        predicate = marked if name == "smallest_bridged" else f"(not {marked})"
        eligible = f"(filter (lambda (o) {predicate}) comps)"

    body = f"""(let* ((working {working})
                  (comps {_GREEN})
                  (eligible {eligible})
                  (score (lambda (o) {score})))
             (if (empty? eligible)
                 working
                 (paint-cells
                   working
                   (obj-cells
                     (first (sort eligible
                                  (lambda (a b) ({comparison} (score a) (score b))))))
                   4)))"""
    if name == "wrong_order":
        body = f"(recolor {body} 5 3)"
    elif name == "gray_stays_green":
        body = f"""(let ((out {body}))
                   (map-grid out
                     (lambda (r c v)
                       (if (= (cell-at g r c) 5) 3 v))))"""
    return f"(rule!\n  {body})"
