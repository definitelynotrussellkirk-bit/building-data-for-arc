"""Exact canonical source and bounded, executable relay-rule alternatives.

Components and the relay are always bound on the original input. Rivals are
private authoring programs; they are never included in public challenges.
"""
from pathlib import Path

MODES = ("direct", "largest_relay")


def _variant(mode, *, contact8=False, components8=False, selector="largest",
             expansion="selected", global_color=False, pixels_only=False):
    if mode not in MODES:
        raise ValueError("Unknown mode")
    selectors = {
        "largest": "(pick-max direct obj-size)",
        "smallest": "(pick-min direct obj-size)",
        "second_largest": "(second (sort direct (lambda (a b) (> (obj-size a) (obj-size b)))))",
        "first": "(first direct)",
        "last": "(last direct)",
        "global": "(pick-max others obj-size)",
        "ignore4": "(let ((eligible (filter (lambda (o) (not (= (obj-color o) 4))) direct))) (if (null? eligible) (pick-max direct obj-size) (pick-max eligible obj-size)))",
        "prefer4": "(let ((yellow (filter (lambda (o) (= (obj-color o) 4)) direct))) (if (null? yellow) (pick-max direct obj-size) (pick-max yellow obj-size)))",
    }
    selected = selectors[selector]
    direct_targets = "direct"
    if mode == "largest_relay":
        direct_targets = "(filter (lambda (o) (or (member o direct) (adjacent? o relay))) others)"
    if expansion == "all":
        direct_targets = "(filter (lambda (o) (or (member o direct) (any? (lambda (d) (adjacent? o d)) direct))) others)"
    elif expansion == "recursive":
        direct_targets = "(for/fold ((reached direct)) ((k (in-range (length objs)))) (filter (lambda (o) (or (member o reached) (any? (lambda (d) (adjacent? o d)) reached))) others))"
    elif expansion == "all_foreground":
        direct_targets = "others"
    elif expansion == "largest_only":
        direct_targets = "(list relay)"
    elif expansion != "selected":
        raise ValueError("Unknown expansion")
    paint_targets = "targets"
    if global_color:
        paint_targets = "(filter (lambda (o) (member (obj-color o) (map obj-color targets))) others)"
    paint_cells = "(obj-cells o)"
    if pixels_only:
        sources = "(list anchor relay)" if mode == "largest_relay" else "(list anchor)"
        paint_cells = f"(filter (lambda (p) (any? (lambda (s) (cell-touches? p s)) {sources})) (obj-cells o))"
    deltas = "all-8-deltas" if contact8 else "cardinal-deltas"
    objects = "objects-8" if components8 else "objects"
    return f"""(rule! (lambda (g)
  (define (cell-touches? p b)
    (any? (lambda (d)
      (member (list (+ (first p) (first d)) (+ (second p) (second d)))
              (obj-cells b))) {deltas}))
  (define (adjacent? a b)
    (any? (lambda (p) (cell-touches? p b)) (obj-cells a)))
  (define objs ({objects} g 0))
  (define anchor (first (filter (lambda (o) (= (obj-color o) 1)) objs)))
  (define others (filter (lambda (o) (not (= (obj-color o) 1))) objs))
  (define direct (filter (lambda (o) (adjacent? o anchor)) others))
  (define relay {selected})
  (define targets {direct_targets})
  (for/fold ((out g)) ((o (in-list {paint_targets})))
    (paint-cells out {paint_cells} 4))))"""


def program(settings):
    """Return complete rule source, preserving the canonical default exactly."""
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly mode=direct|largest_relay")
    if settings["mode"] == "direct":
        return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    return _variant("largest_relay")


def rival_programs(mode):
    """Finite plausible rivals. Successful execution is required for every rival."""
    if type(mode) is not str or mode not in MODES:
        raise ValueError("Unknown mode")
    result = {
        "other_setting": program({"mode": "largest_relay" if mode == "direct" else "direct"}),
        "eight_contact": _variant(mode, contact8=True),
        "eight_components": _variant(mode, components8=True),
        "global_color": _variant(mode, global_color=True),
        "touching_pixels": _variant(mode, pixels_only=True),
        "all_foreground": _variant(mode, expansion="all_foreground"),
        "recursive_flood": _variant(mode, expansion="recursive"),
        "largest_only": _variant(mode, expansion="largest_only"),
    }
    if mode == "largest_relay":
        result.update({
            "smallest_relay": _variant(mode, selector="smallest"),
            "second_largest_relay": _variant(mode, selector="second_largest"),
            "first_relay": _variant(mode, selector="first"),
            "last_relay": _variant(mode, selector="last"),
            "global_largest_relay": _variant(mode, selector="global"),
            "ignore_already4_relay": _variant(mode, selector="ignore4"),
            "prefer_already4_relay": _variant(mode, selector="prefer4"),
            "all_relays": _variant(mode, expansion="all"),
        })
    return result
