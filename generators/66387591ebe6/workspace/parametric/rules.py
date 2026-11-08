"""Racket construction for the separate first-hit rotation family and its rivals."""
from __future__ import annotations


SIZE_TURNS = "(if picked (modulo (- (obj-size picked) 1) 4) 0)"
KEY_TURNS = "(- key 1)"


def build_rule(*, turns=None, selector="first", components="four",
               fallback="0", center="pivot", overlay=False,
               flatten=False, only_hit=False, ray_offset=0, keep_pivot=True):
    """Emit one total rule over the sampler's grammar; options are audit-only."""
    component_grid = "clean"
    component_fn = "objects"
    if components == "eight":
        component_fn = "objects-8"
    elif components == "uncolored":
        component_grid = "(for/list ((row (in-list clean))) (for/list ((v (in-list row))) (if (= v 0) 0 1)))"
    elif components != "four":
        raise ValueError("Unknown component mode")
    hit = "(last hits)" if selector == "last" else "(first hits)"
    selected = f"(if (empty? hits) #f (first (filter (lambda (o) (member {hit} (obj-cells o))) objs)))"
    if selector == "largest":
        selected = "(if (empty? objs) #f (argmax obj-size objs))"
    elif selector == "nearest":
        selected = "(if (empty? objs) #f (argmin (lambda (o) (apply min (map (lambda (p) (+ (abs (- (first p) (first pivot))) (abs (- (second p) (second pivot))))) (obj-cells o)))) objs))"
    elif selector == "scan":
        selected = "(if (empty? objs) #f (first objs))"
    elif selector not in {"first", "last"}:
        raise ValueError("Unknown selection mode")
    turns = turns or f"(if picked (modulo (- (obj-size picked) 1) 4) {fallback})"
    rotation_center = "pivot" if center == "pivot" else "(list (quotient (rows g) 2) (quotient (cols g) 2))"
    moving = "(if picked (obj-cells picked) '())" if only_hit else "cells"
    empty = "(set-cell (empty-grid (rows g) (cols g) 0) 0 0 key)"
    markers = f"(set-cell {empty} (first pivot) (second pivot) 9)" if keep_pivot else empty
    initial = "g" if overlay else markers
    if only_hit:
        initial = f"(for/fold ((base {markers})) ((p (in-list cells)) #:unless (member p moving)) (set-cell base (first p) (second p) (at g (first p) (second p))))"
    color = "(at g (first (first cells)) (second (first cells)))" if flatten else "(at g (first src) (second src))"
    return f'''(rule!
 (let ()
  (define (rotate-about ps pivot turns)
   (map (lambda (p)
    (let* ((y (- (first p) (first pivot)))
           (x (- (second p) (second pivot))) (k (modulo turns 4))
           (ny (cond ((= k 0) y) ((= k 1) x) ((= k 2) (- y)) (else (- x))))
           (nx (cond ((= k 0) x) ((= k 1) (- y)) ((= k 2) (- x)) (else y))))
     (list (+ (first pivot) ny) (+ (second pivot) nx)))) ps))
  (let* ((key (at g 0 0)) (pivot (first (find-color g 9)))
         (cells (filter (lambda (p)
           (and (not (equal? p '(0 0)))
                (not (= (at g (first p) (second p)) 9))
                (not (= (at g (first p) (second p)) 0)))) (grid-positions g)))
         (clean (set-cell (set-cell g 0 0 0) (first pivot) (second pivot) 0))
         (direction (list-ref '((-1 0) (0 1) (1 0) (0 -1)) (modulo (+ (- key 1) {ray_offset}) 4)))
         (ray (for/list ((distance (in-range 1 (max (rows g) (cols g)))))
           (list (+ (first pivot) (* distance (first direction)))
                 (+ (second pivot) (* distance (second direction))))))
         (hits (filter (lambda (p)
           (and (<= 0 (first p)) (< (first p) (rows g))
                (<= 0 (second p)) (< (second p) (cols g))
                (not (= (at clean (first p) (second p)) 0)))) ray))
         (objs ({component_fn} {component_grid} 0))
         (picked {selected})
         (turns {turns}) (moving {moving})
         (rotated (rotate-about moving {rotation_center} turns)))
   (for/fold ((out {initial})) ((src (in-list moving)) (dst (in-list rotated)))
    (if (and (<= 0 (first dst)) (< (first dst) (rows g))
             (<= 0 (second dst)) (< (second dst) (cols g)))
        (set-cell out (first dst) (second dst) {color}) out)))))'''


def rivals(turn_source):
    """Finite, explicitly named alternatives; execution errors are never evidence."""
    base = KEY_TURNS if turn_source == "key" else SIZE_TURNS
    out = {
        "identity": "(rule! (let () g))",
        "fixed_clockwise_1": build_rule(turns="1"),
        "fixed_clockwise_2": build_rule(turns="2"),
        "fixed_clockwise_3": build_rule(turns="3"),
        "key_direct": build_rule(turns="key"),
        "counterclockwise": build_rule(turns=f"(- {base})"),
        "grid_center": build_rule(turns=base, center="grid"),
        "overlay": build_rule(turns=base, overlay=True),
        "flatten_colors": build_rule(turns=base, flatten=True),
        "only_hit_moves": build_rule(turns=base, only_hit=True),
        "erase_pivot": build_rule(turns=base, keep_pivot=False),
        "key_one_rotates": build_rule(turns=f"(if (= key 1) 1 {base})"),
    }
    if turn_source == "key":
        out["hit_size_instead_of_key"] = build_rule()
    else:
        out.update({
            "skip_ray_use_key": build_rule(turns=KEY_TURNS),
            "last_hit": build_rule(selector="last"),
            "largest_component": build_rule(selector="largest"),
            "nearest_component": build_rule(selector="nearest"),
            "scan_first_component": build_rule(selector="scan"),
            "total_foreground": build_rule(turns="(- (length cells) 1)"),
            "global_hit_color": build_rule(turns="(if picked (- (length (filter (lambda (p) (= (at clean (first p) (second p)) (obj-color picked))) cells)) 1) 0)"),
            "eight_connected": build_rule(components="eight"),
            "color_agnostic_four": build_rule(components="uncolored"),
            "hit_color": build_rule(turns="(if picked (- (obj-color picked) 1) 0)"),
            "ray_distance": build_rule(turns="(if (empty? hits) 0 (- (+ (abs (- (first (first hits)) (first pivot))) (abs (- (second (first hits)) (second pivot)))) 1))"),
            "size_without_minus_one": build_rule(turns="(if picked (obj-size picked) 0)"),
            "clamp_size_at_four": build_rule(turns="(if picked (- (min 4 (obj-size picked)) 1) 0)"),
            "no_hit_use_key": build_rule(fallback="(- key 1)"),
            "ray_direction_offset": build_rule(ray_offset=1),
        })
        for turns in range(1, 4):
            out[f"no_hit_fixed_{turns}"] = build_rule(fallback=str(turns))
    return out
