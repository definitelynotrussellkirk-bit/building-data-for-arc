"""Area-ranked components, optionally coalescing color 2 into 1 first.

The canonical sampler and authority are untouched. Python labels are claims;
native qualification and audit.py replay them with protected Racket.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "0f801939eff6"
SETTINGS = ({"merge": "none"}, {"merge": "2_into_1"})
DEFAULT = {"merge": "none"}
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text()
_BODY = CANONICAL_PROGRAM.strip()[len("(rule!"):].rstrip()[:-1].strip()
_LIMIT = 2**63 - 1


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"merge"}
            or type(settings["merge"]) is not str
            or settings["merge"] not in ("none", "2_into_1")):
        raise ValueError("settings must be exactly {'merge': 'none'|'2_into_1'}")
    return settings["merge"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with literal integer colors 0..9")
    return grid


def components(grid, *, eight=False):
    """Independent same-color BFS; returned descriptions are JSON-safe."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (eight or abs(dr) + abs(dc) == 1)]
    seen, found = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            queue, cells = deque([(r, c)]), []
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.append([rr, cc])
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            rows, cols = [p[0] for p in cells], [p[1] for p in cells]
            found.append({"color": color, "size": len(cells), "cells": cells,
                          "anchor": cells[0],
                          "bbox_area": (max(rows)-min(rows)+1)*(max(cols)-min(cols)+1)})
    return found


def preprocess(grid, settings):
    _grid(grid)
    merge = _settings(settings) == "2_into_1"
    return [[1 if merge and cell == 2 else cell for cell in row] for row in grid]


def _strip(parts):
    return [[p["color"] for p in parts for _ in range(p["size"])] or [0]]


def rule_mirror(grid, settings):
    parts = components(preprocess(grid, settings))
    return _strip(sorted(parts, key=lambda p: (-p["size"], p["color"])))


def _rule(body):
    return "(rule!\n  " + body + ")"


def _before(body, settings):
    if _settings(settings) == "2_into_1":
        return "(let ((g (recolor g 2 1)))\n    " + body + ")"
    return body


def program(settings):
    """The default is byte-identical to the selected canonical authority."""
    return CANONICAL_PROGRAM if _settings(settings) == "none" else _rule(_before(_BODY, settings))


def rival_outputs(grid, settings):
    transformed = preprocess(grid, settings)
    parts = components(transformed)
    by_area = lambda p: (-p["size"], p["color"])
    counts = Counter(v for row in transformed for v in row if v)
    other = {"merge": "2_into_1" if settings["merge"] == "none" else "none"}
    rivals = {
        "other_setting": rule_mirror(grid, other),
        "color_frequency": _strip(sorted(
            [{"color": c, "size": n} for c, n in counts.items()], key=by_area)),
        "position_tie": _strip(sorted(parts, key=lambda p: (-p["size"], p["anchor"]))),
        "eight_connected": _strip(sorted(components(transformed, eight=True), key=by_area)),
        "bbox_rank": _strip(sorted(parts, key=lambda p: (-p["bbox_area"], p["color"]))),
        "color_rank": _strip(sorted(parts, key=lambda p: (p["color"], -p["size"]))),
        "scan_order": _strip(sorted(parts, key=lambda p: p["anchor"])),
        "target_first": _strip(sorted(parts, key=lambda p: (p["color"] != 1, *by_area(p)))),
    }
    if settings["merge"] == "2_into_1":
        rivals["rank_then_recolor"] = preprocess(rule_mirror(grid, DEFAULT), settings)
        # Strong scope shortcut: change 2 only in a foreground cluster that has 1.
        mask = [[int(bool(value)) for value in row] for row in grid]
        local = deepcopy(grid)
        for group in components(mask, eight=True):
            if any(grid[r][c] == 1 for r, c in group["cells"]):
                for r, c in group["cells"]:
                    if local[r][c] == 2:
                        local[r][c] = 1
        rivals["local_cluster_recolor"] = rule_mirror(local, DEFAULT)
    return rivals


def rival_programs(settings):
    """Executable counterparts of the finite authoring rivals, not gold rules."""
    _settings(settings)
    other = {"merge": "2_into_1" if settings["merge"] == "none" else "none"}
    area = "(obj-size a)"
    area_b = "(obj-size b)"
    color_tie = "(< (obj-color a) (obj-color b))"
    anchor_a = "(apply min (map (lambda (p) (+ (* 30 (first p)) (second p))) (obj-cells a)))"
    anchor_b = anchor_a.replace("(obj-cells a)", "(obj-cells b)")
    comparisons = {
        "position_tie": f"(if (= {area} {area_b}) (< {anchor_a} {anchor_b}) (> {area} {area_b}))",
        "bbox_rank": f"(let ((aa (* (obj-h a) (obj-w a))) (bb (* (obj-h b) (obj-w b)))) (if (= aa bb) {color_tie} (> aa bb)))",
        "color_rank": f"(if (= (obj-color a) (obj-color b)) (> {area} {area_b}) {color_tie})",
        "scan_order": f"(< {anchor_a} {anchor_b})",
        "target_first": f"(cond [(and (= (obj-color a) 1) (not (= (obj-color b) 1))) #t] [(and (not (= (obj-color a) 1)) (= (obj-color b) 1)) #f] [(= {area} {area_b}) {color_tie}] [else (> {area} {area_b})])",
    }
    result = {"other_setting": program(other)}
    for name, compare in comparisons.items():
        body = f"""(let* ((parts (sort (objects g 0) (lambda (a b) {compare})))
  (row (apply append (map (lambda (obj) (make-list (obj-size obj) (obj-color obj))) parts))))
  (if (empty? row) (list (list 0)) (list row)))"""
        result[name] = _rule(_before(body, settings))
    result["eight_connected"] = _rule(_before(_BODY.replace("(objects g 0)", "(objects-8 g 0)"), settings))
    frequency = """(let* ((flat (apply append g))
  (items (sort (map (lambda (color) (list (count (lambda (v) (= v color)) flat) color)) (grid-colors g 0))
    (lambda (a b) (if (= (first a) (first b)) (< (second a) (second b)) (> (first a) (first b))))))
  (row (apply append (map (lambda (item) (make-list (first item) (second item))) items))))
  (if (empty? row) (list (list 0)) (list row)))"""
    result["color_frequency"] = _rule(_before(frequency, settings))
    if settings["merge"] == "2_into_1":
        result["rank_then_recolor"] = _rule("(recolor " + _BODY + " 2 1)")
        local = """(let* ((mask (map (lambda (row) (map (lambda (v) (if (= v 0) 0 1)) row)) g))
  (clusters (objects-8 mask 0))
  (chosen (filter (lambda (obj) (ormap (lambda (p) (= (list-ref (list-ref g (first p)) (second p)) 1)) (obj-cells obj))) clusters))
  (locations (apply append (map obj-cells chosen)))
  (changed (foldl (lambda (p acc) (if (= (list-ref (list-ref g (first p)) (second p)) 2)
      (set-cell acc (first p) (second p) 1) acc)) g locations)))
  (let ((g changed)) BODY))"""
        result["local_cluster_recolor"] = _rule(local.replace("BODY", _BODY))
    return result


def teaching_check(episode):
    """Fit rivals to demonstrations only; query labels cannot affect this result."""
    settings = episode["settings"]
    _settings(settings)
    train = episode["train"]
    if type(train) is not list or not train:
        raise ValueError("nonempty demonstrations required")
    refuted = {}
    names = None
    for index, pair in enumerate(train):
        _grid(pair["output"])
        if rule_mirror(pair["input"], settings) != pair["output"]:
            raise ValueError("demonstration label disagrees with selected rule")
        rivals = rival_outputs(pair["input"], settings)
        names = list(rivals)
        for name, output in rivals.items():
            if output != pair["output"]:
                refuted.setdefault(name, index)
    survivors = [name for name in names if name not in refuted]
    return {"status": "ambiguous" if survivors else "identified",
            "surviving_rivals": survivors, "refuted_by": refuted,
            "limits": "Demonstration-only check of the named finite rivals; not universal uniqueness."}


def _shape(n, color, *, compact=False):
    if compact:
        width = 2 if n <= 4 else 3
        points = [(i // width, i % width) for i in range(n)]
    else:
        height = n // 2 + 1
        points = [(r, 0) for r in range(height)] + [(height-1, c) for c in range(1, n-height+1)]
    return [(r, c, color) for r, c in points]


def _orient(cells, rng):
    turns, reflect = rng.randrange(4), rng.choice((False, True))
    result = []
    for r, c, color in cells:
        if reflect:
            c = -c
        for _ in range(turns):
            r, c = c, -r
        result.append((r, c, color))
    r0, c0 = min(x[0] for x in result), min(x[1] for x in result)
    return [(r-r0, c-c0, color) for r, c, color in result]


def _place(groups, h, w, rng, *, corners=False):
    if corners:
        placed = []
        for index, group in enumerate(groups):
            gh, gw = max(p[0] for p in group)+1, max(p[1] for p in group)+1
            r0 = 0 if index < 2 else h-gh
            c0 = 0 if index % 2 == 0 else w-gw
            placed.append([(r+r0, c+c0, value) for r, c, value in group])
        return placed
    candidates = []
    for group in groups:
        gh, gw = max(p[0] for p in group)+1, max(p[1] for p in group)+1
        options = [(r, c) for r in range(h-gh+1) for c in range(w-gw+1)]
        rng.shuffle(options)
        candidates.append(options)
    chosen = [None] * len(groups)
    nodes = 0
    def visit(index, blocked):
        nonlocal nodes
        if index == len(groups):
            return True
        for r0, c0 in candidates[index]:
            nodes += 1
            if nodes > 50000:
                raise RuntimeError("bounded constructive placement exhausted")
            moved = [(r+r0, c+c0, value) for r, c, value in groups[index]]
            mask = {(r, c) for r, c, _ in moved}
            if mask & blocked:
                continue
            # Group 1 is the larger-color L; it must precede the tied low color.
            if index == 2 and min(mask) <= min((r, c) for r, c, _ in chosen[1]):
                continue
            chosen[index] = moved
            halo = {(r+dr, c+dc) for r, c in mask for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if visit(index+1, blocked | halo):
                return True
        chosen[index] = None
        return False
    if not visit(0, set()):
        raise RuntimeError(f"no complete motif placement on {h}x{w}")
    return chosen


def _input(seed, split, index):
    key = f"{TASK_ID}/coalesce-v1/{seed}/{split}/{index}".encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))
    palette = rng.sample(range(3, 10), 3)
    low, high = sorted(palette[:2])
    extra = palette[2]
    stress = split == "query" and index == 3
    if stress:
        h = w = 30
        a, b, tie = 6, 5, 7
    elif split == "demo":
        h, w = 10 + index, 13 + (seed % 3)
        a, b, tie = (4, 3, 6) if index % 2 == 0 else (2, 2, 5)
    elif index == 0:
        h, w, a, b, tie = 8, 11, 3, 2, 4
    else:
        h, w = ((rng.randrange(21, 30), rng.randrange(21, 30)) if index == 1 else (16, 20))
        a, b, tie = rng.randrange(2, 6), rng.randrange(1, 5), rng.randrange(4, 7)
    # Query 2 contains separated source/target components: recoloring is global,
    # and does not imply that every occurrence of the resulting color coalesces.
    gap = 1 if split == "query" and index == 2 else 0
    joined = [(r, 0, 1) for r in range(a)] + [(a-1, c+1+gap, 2) for c in range(b)]
    if stress:
        joined += [(a, b+1, 2), (a, b+2, 2)]  # diagonal, stays 4-disconnected
    elif split == "demo" and index % 2:
        # Isolated even under 8-connected foreground grouping: demonstrations
        # must teach global recoloring before queries put 2 far from every 1.
        joined.append((a+2, b+3, 2))
    else:
        joined.append((-1, -1, 1))
    groups = [joined, _shape(tie, high), _shape(tie, low, compact=True)]
    if stress:
        groups.append(_shape(3, 1))
    elif split == "demo" and index % 2:
        groups.append(_shape(3, extra))
    elif split == "query" and index == 2:
        groups.append(_shape(2, extra))
    groups = [_orient(group, rng) for group in groups]
    placed = _place(groups, h, w, rng, corners=stress)
    grid = [[0] * w for _ in range(h)]
    for group in placed:
        for r, c, color in group:
            if grid[r][c]:
                raise RuntimeError("constructive placement collision")
            grid[r][c] = color
    if sum(bool(v) for row in grid for v in row) > 30:
        raise RuntimeError("constructed output would exceed ARC width")
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer("seed", seed, 0, _LIMIT)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _settings(settings)
    def pairs(split, count):
        grids = [_input(seed, split, i) for i in range(count)]
        return [{"input": grid, "output": rule_mirror(grid, settings)} for grid in grids]
    episode = {"task_id": TASK_ID, "seed": seed, "settings": deepcopy(settings),
               "train": pairs("demo", demos), "test": pairs("query", queries),
               "program_solution": program(settings)}
    inputs = [json.dumps(p["input"]) for p in episode["train"]+episode["test"]]
    if len(set(inputs)) != len(inputs):
        raise RuntimeError("duplicate input in constructed episode")
    if teaching_check(episode)["surviving_rivals"]:
        raise RuntimeError("constructed demonstrations do not eliminate declared rivals")
    return episode


def public_challenge(episode, query_index=0):
    _integer("query_index", query_index, 0, len(episode["test"])-1)
    # Round-trip the established projection helper for exact, strict visible bytes.
    selected = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(selected))


def export_batch(episodes, output_dir):
    """Publish first turns only; controller banks and all semantics stay private.

    Validation and duplicate-visible detection finish before creating output_dir.
    IDs depend only on exact first-turn visible bytes, never future queries.
    This authoring writer does not grant native acceptance or training admission.
    """
    if type(episodes) not in (list, tuple) or not episodes:
        raise ValueError("a nonempty episode batch is required")
    pending, ids = [], set()
    # Check visible duplicates before private label validation, including two
    # contradictory hidden banks claiming the same visible first-turn lesson.
    for episode in episodes:
        visible = public_challenge(episode)
        identity = public_challenge_id(visible)
        if identity in ids:
            raise ValueError("duplicate visible public challenge")
        ids.add(identity)
        pending.append((identity, public_challenge_bytes(visible), deepcopy(episode)))
    serialized = []
    for identity, visible_bytes, episode in pending:
        _settings(episode["settings"])
        _integer("demos", len(episode["train"]), 2, 6)
        _integer("queries", len(episode["test"]), 1, 4)
        code = episode.get("program_solution", episode.get("program"))
        if code != program(episode["settings"]):
            raise ValueError("private program differs from selected rule")
        seen = set()
        for pair in episode["train"] + episode["test"]:
            _grid(pair["input"])
            _grid(pair["output"])
            fingerprint = json.dumps(pair["input"])
            if fingerprint in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(fingerprint)
            if rule_mirror(pair["input"], episode["settings"]) != pair["output"]:
                raise ValueError("private label disagrees with selected rule")
        if teaching_check(episode)["surviving_rivals"]:
            raise ValueError("underidentified demonstrations")
        private_bytes = (json.dumps(episode, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False) + "\n").encode("utf-8")
        serialized.append((identity, visible_bytes, private_bytes))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    (output / "public").mkdir()
    (output / "private").mkdir()
    for identity, visible_bytes, private_bytes in sorted(serialized):
        (output / "public" / (identity + ".json")).write_bytes(visible_bytes)
        (output / "private" / (identity + ".json")).write_bytes(private_bytes)
    return {"episodes": len(pending), "public_dir": str(output / "public"),
            "private_dir": str(output / "private"), "training_admitted": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--merge", choices=("none", "2_into_1", "both"), default="both")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.merge == "both" else ({"merge": args.merge},)
    print(json.dumps(export_batch([generate(args.seed, setting, args.demos, args.queries)
                                   for setting in settings], args.out), sort_keys=True))


if __name__ == "__main__":
    main()
