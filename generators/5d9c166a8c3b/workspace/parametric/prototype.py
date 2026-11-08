"""A separate, bounded all/largest-final-bbox family for 5d9c166a8c3b.

The canonical source is preserved exactly.  Python outputs are claims for the
native worker to execute independently in protected Racket.  ``audit.py`` also
executes all saved example labels in Racket before writing public/private files.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "5d9c166a8c3b"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)
SCOPES = ("all", "largest_bbox")
_MERGED = "(define merged-groups (merge-fixed groups))"
_TAIL = "\n                     merged-groups)))))"
_OVERLAP = """(or
                   (not (or (< r1b r2a) (< r2b r1a)))
                   (not (or (< c1b c2a) (< c2b c1a))))"""

_STATIC = """
             (define (node-linked? node members)
               (not (null? (filter
                 (lambda (member) (boxes-overlap? (cells-bbox node) (cells-bbox member)))
                 members))))
             (define (static-expand members pending)
               (let* ((yes (filter (lambda (node) (node-linked? node members)) pending))
                      (no (filter (lambda (node) (not (node-linked? node members))) pending)))
                 (if (null? yes)
                     (list (apply append members) no)
                     (static-expand (append members yes) no))))
             (define (static-groups pending)
               (if (null? pending) '()
                   (let ((part (static-expand (list (first pending)) (cdr pending))))
                     (cons (first part) (static-groups (second part))))))
"""


def _replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Canonical source marker changed; re-review the transformation")
    return text.replace(old, new, 1)


def _scope(settings):
    if type(settings) is not dict or set(settings) != {"fill_scope"}:
        raise ValueError("settings must contain exactly fill_scope")
    scope = settings["fill_scope"]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError("fill_scope must be all or largest_bbox")
    return scope


@functools.lru_cache(maxsize=64)
def rule_program(scope, grouping="fixed", selection=None, outline=False):
    """Materialize true programs and finite diagnostic counterfactuals."""
    if scope not in SCOPES:
        raise ValueError("unknown fill scope")
    text = Path(__file__).with_name("canonical.rkt").read_text()
    if grouping == "static_graph":
        text = _replace_once(text, _MERGED, _STATIC + "(define merged-groups (static-groups groups))")
    elif grouping == "one_pass":
        text = _replace_once(text, _MERGED, "(define merged-groups (do-merge groups))")
    elif grouping == "original":
        text = _replace_once(text, _MERGED, "(define merged-groups groups)")
    elif grouping == "global":
        text = _replace_once(text, _MERGED,
                             "(define merged-groups (if (null? groups) '() (list (apply append groups))))")
    elif grouping in ("row", "column"):
        predicate = ("(not (or (< r1b r2a) (< r2b r1a)))" if grouping == "row"
                     else "(not (or (< c1b c2a) (< c2b c1a)))")
        text = _replace_once(text, _OVERLAP, predicate)
    elif grouping == "direct_pairs":
        expr = """(append groups
               (flatmap (lambda (a)
                 (map (lambda (b) (append a b))
                   (filter (lambda (b) (boxes-overlap? (cells-bbox a) (cells-bbox b))) groups)))
                 groups))"""
        text = _replace_once(text, _MERGED, "(define merged-groups " + expr + ")")
    elif grouping != "fixed":
        raise ValueError("unknown grouping")

    effective = selection or scope
    if effective != "all":
        area = """(define (group-area group)
               (let ((bb (cells-bbox group)))
                 (* (+ 1 (- (third bb) (first bb)))
                    (+ 1 (- (nth bb 3) (second bb))))))"""
        score = "length" if effective == "foreground_count" else "group-area"
        extremum = "min-list" if effective == "smallest_bbox" else "max-list"
        select = f"""(if (null? merged-groups) '()
               (let ((best ({extremum} (map {score} merged-groups))))
                 (filter (lambda (group) (= ({score} group) best)) merged-groups)))"""
        if effective == "first_maximum":
            select = """(let ((winners """ + select + """))
               (if (null? winners) '()
                   (let ((top (min-list (map (lambda (group) (first (cells-bbox group))) winners))))
                     (filter (lambda (group) (= (first (cells-bbox group)) top)) winners))))"""
        if effective not in ("largest_bbox", "foreground_count", "smallest_bbox", "first_maximum"):
            raise ValueError("unknown selection")
        text = _replace_once(text, "(reduce (lambda (gg group)",
                             area + "\n             (define active-groups " + select + ")\n"
                             + "             (reduce (lambda (gg group)")
        text = _replace_once(text, _TAIL, "\n                     active-groups)))))")
    if outline:
        text = _replace_once(text, "(if (zero? (at g (first rc) (second rc)))",
                             "(if (and (zero? (at g (first rc) (second rc))) "
                             "(or (= (first rc) r1) (= (first rc) r2) "
                             "(= (second rc) c1) (= (second rc) c2)))")
    return text


def program(settings):
    return rule_program(_scope(settings))


def _static_groups(components):
    pending = list(components)
    answer = []
    while pending:
        nodes, pending = [pending[0]], pending[1:]
        while True:
            hits = [node for node in pending if any(
                gen._row_or_column_overlap(gen._bbox(node), gen._bbox(member)) for member in nodes)]
            if not hits:
                break
            pending = [node for node in pending if node not in hits]
            nodes.extend(hits)
        answer.append([cell for node in nodes for cell in node])
    return answer


def _area(group):
    r0, c0, r1, c1 = gen._bbox(group)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _one_pass(components):
    """Exactly the canonical do-merge, without its outer fixed-point loop."""
    if len(components) < 2:
        return list(components)
    cur, rest = components[0], components[1:]
    matches = [group for group in rest
               if gen._row_or_column_overlap(gen._bbox(cur), gen._bbox(group))]
    others = [group for group in rest if group not in matches]
    if not matches:
        return [cur] + _one_pass(rest)
    return _one_pass([cur + [cell for group in matches for cell in group]] + others)


def groups(grid, grouping="fixed"):
    components = gen._components(grid)
    if grouping == "static_graph":
        return _static_groups(components)
    if grouping == "one_pass":
        return _one_pass(components)
    if grouping == "original":
        return components
    if grouping == "global":
        return [[cell for component in components for cell in component]] if components else []
    if grouping == "direct_pairs":
        return components + [a + b for a in components for b in components
                             if gen._row_or_column_overlap(gen._bbox(a), gen._bbox(b))]
    predicate = {"fixed": gen._row_or_column_overlap,
                 "row": gen._row_overlap, "column": gen._column_overlap}.get(grouping)
    if predicate is None:
        raise ValueError("unknown grouping")
    return gen._merge_fixed(components, predicate)


def solve(grid, scope, *, grouping="fixed", selection=None, outline=False):
    errors, _, _ = gen._shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    selected = groups(grid, grouping)
    effective = selection or scope
    if selected and effective != "all":
        score = len if effective == "foreground_count" else _area
        best = (min if effective == "smallest_bbox" else max)(map(score, selected))
        selected = [group for group in selected if score(group) == best]
        if effective == "first_maximum":
            # Final groups have disjoint row spans.  Geometric ordering avoids
            # depending on Python/Racket implementation-specific merge order.
            top = min(gen._bbox(group)[0] for group in selected)
            selected = [group for group in selected if gen._bbox(group)[0] == top]
    output = gen._fill_groups(grid, selected)
    if outline:
        output = [row[:] for row in grid]
        for group in selected:
            r0, c0, r1, c1 = gen._bbox(group)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if (r in (r0, r1) or c in (c0, c1)) and grid[r][c] == 0:
                        output[r][c] = 2
    return output


def _int_bound(name, value, lo, hi=None):
    if type(value) is not int or value < lo or (hi is not None and value > hi):
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi if hi is not None else 'unbounded'}")


def _rectangle(grid, r, c, h, w, color):
    for rr in range(r, r + h):
        for cc in range(c, c + w):
            grid[rr][cc] = color


def _scene(rng, height, width, role, orientation):
    # Build before transpose, preserving the caller's requested final dimensions.
    h, w = (width, height) if orientation >= 4 else (height, width)
    if role == "tie":
        ah, aw = (h - 1) // 2, (w - 1) // 2
        bh, bw = ah, aw
    else:
        fraction = 0.60 if role == "bridge_wins" else 0.40
        ah = min(h - 3, max(3, int((h - 1) * fraction)))
        aw = min(w - 3, max(3, int((w - 1) * fraction)))
        bh, bw = h - ah - 1, w - aw - 1
        if role == "bridge_wins":
            while bh * bw >= ah * aw:
                if bh > 2 and (bh >= bw or bw == 2):
                    bh -= 1
                elif bw > 2:
                    bw -= 1
                else:
                    raise ValueError("size cannot fit a distinguishing productive distractor")
        elif bh * bw <= ah * aw:
            # At 7x7 no larger second bbox fits.  Explicitly record the lawful
            # tie profile rather than claiming a role reversal at that size.
            role = "tie"
            ah, aw = (h - 1) // 2, (w - 1) // 2
            bh, bw = ah, aw
    grid = [[0] * w for _ in range(h)]
    color = rng.choice((1, 3, 4, 5, 6, 7, 8, 9))
    top = rng.randint(1, max(1, ah // 5))
    lower = rng.randint(1, max(1, ah // 5))
    left = rng.randint(1, max(1, aw // 5))
    right = rng.randint(1, max(1, aw // 5))
    middle = rng.randint(1, max(1, aw // 5))
    middle_c = rng.randint(left, aw - right - middle)
    r0 = rng.randint(0, h - ah - bh - 1)
    c0 = rng.randint(0, w - aw - bw - 1)
    _rectangle(grid, r0, c0, top, left, color)
    _rectangle(grid, r0, c0 + aw - right, top, right, color)
    _rectangle(grid, r0 + ah - lower, c0 + middle_c, lower, middle, color)
    # A productive connected object, not a no-op singleton.  Its density also
    # opposes choosing by original foreground count instead of final bbox area.
    rb, cb = r0 + ah + 1, c0 + aw + 1
    band_r, band_c = max(1, bh // 2), max(1, bw // 3)
    _rectangle(grid, rb, cb, band_r, bw, color)
    _rectangle(grid, rb, cb, bh, band_c, color)
    if orientation >= 4:
        grid = [list(row) for row in zip(*grid)]
    if orientation & 1:
        grid = list(reversed(grid))
    if orientation & 2:
        grid = [list(reversed(row)) for row in grid]
    errors = gen.self_check(grid)
    if errors:
        raise AssertionError("constructed scene is outside canonical grammar: " + "; ".join(errors))
    return grid, role


def generate(seed, settings, demos=3, queries=4, *, height=None, width=None):
    scope = _scope(settings)
    _int_bound("seed", seed, 0)
    _int_bound("demos", demos, 2, 6)
    _int_bound("queries", queries, 1, 4)
    for name, value in (("height", height), ("width", width)):
        if value is not None:
            _int_bound(name, value, 7, 30)
    pairs, seen, actual_roles, attempts = [], set(), [], 0
    roles = ("bridge_wins", "tie", "single_wins")
    for index in range(demos + queries):
        phase = "demo" if index < demos else "query"
        local_index = index if phase == "demo" else index - demos
        role = roles[local_index % len(roles)]
        for retry in range(64):
            attempts += 1
            # No setting or total query count in this stream.  Matched inputs
            # and first-query prefixes are guaranteed by construction.
            rng = random.Random(f"bbox-v1:{seed}:{phase}:{local_index}:{retry}")
            if phase == "demo":
                h, w = rng.randint(9, 20), rng.randint(9, 20)
            elif local_index == 0:
                h, w = 30, 30
            elif local_index == 1:
                h, w = rng.randint(21, 29), rng.randint(21, 29)
            else:
                h, w = rng.randint(7, 30), rng.randint(7, 30)
            orientation = rng.randrange(8)
            if phase == "demo" and local_index == 0:
                # Encounter the isolated middle component BEFORE the two
                # aligned ends.  A retained prefix must be revisited after
                # their merge: one recursive merge scan is insufficient.
                orientation = rng.choice((1, 3))
            elif phase == "demo" and local_index == 1:
                # The transposed tie example teaches new row-span overlap,
                # complementing the first example's new column-span overlap.
                orientation = rng.randrange(4, 8)
            grid, actual_role = _scene(rng, height or h, width or w, role, orientation)
            signature = json.dumps(grid, separators=(",", ":"))
            if signature not in seen:
                seen.add(signature)
                pairs.append({"input": grid, "output": solve(grid, scope)})
                actual_roles.append(actual_role)
                break
        else:
            raise RuntimeError("bounded distinct-input sampler exhausted 64 attempts")
    episode = {"train": pairs[:demos], "test": pairs[demos:],
               "program_solution": program(settings), "settings": dict(settings),
               "seed": seed, "training_admitted": False,
               "sampling": {"attempts": attempts, "roles": actual_roles,
                            "labels": "python_claims_require_protected_racket_verification"}}
    check = teaching_check(episode, scope)
    if check["ambiguous_queries"]:
        raise RuntimeError("constructed lesson has a live query-changing rival: "
                           + repr(check["ambiguous_queries"]))
    return episode


def rival_specs(scope):
    result = {"opposite_setting": {"scope": "largest_bbox" if scope == "all" else "all"}}
    result.update({name: {"scope": scope, "grouping": grouping} for name, grouping in [
        ("static_initial_graph", "static_graph"), ("row_only", "row"),
        ("single_merge_pass", "one_pass"),
        ("column_only", "column"), ("original_components", "original"),
        ("direct_pairs", "direct_pairs"), ("global_bbox", "global")]})
    result["foreground_count"] = {"scope": scope, "selection": "foreground_count"}
    result["smallest_bbox"] = {"scope": scope, "selection": "smallest_bbox"}
    result["one_tie_winner"] = {"scope": scope, "selection": "first_maximum"}
    result["outline_only"] = {"scope": scope, "outline": True}
    return result


def teaching_check(episode, scope, *, evaluate=None):
    """Fit finite rivals to demos only; query answers never select a rule.

    ``evaluate(program, grid)`` can be the live protected-Racket executor.
    Runtime errors propagate, so an invalid rival cannot count as eliminated.
    """
    rows, ambiguous = {}, []
    for name, spec in rival_specs(scope).items():
        def apply(grid):
            if evaluate is None:
                return solve(grid, **spec)
            return evaluate(rule_program(**spec), grid)
        mismatch = [i for i, pair in enumerate(episode["train"])
                    if apply(pair["input"]) != pair["output"]]
        disagreements = ([] if mismatch else [i for i, pair in enumerate(episode["test"])
                                               if apply(pair["input"]) != pair["output"]])
        rows[name] = {"fits_demonstrations": not mismatch,
                      "distinguishing_demo_indices": mismatch,
                      "query_disagreements": disagreements}
        if disagreements:
            ambiguous.append({"rival": name, "queries": disagreements})
    return {"rivals": rows, "ambiguous_queries": ambiguous,
            "scope": "finite declared rivals, not universal rule identifiability"}


def first_turn_bytes(episode):
    return public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})
