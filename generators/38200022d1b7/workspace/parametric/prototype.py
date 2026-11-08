"""Point reflection with an episode-fixed source-color selection rule.

The canonical rule copies every source. Alternatives bind the color of the
nearest/farthest source CELL by Manhattan distance, then copy every source of
that color. Sampler labels are Python claims until checked by protected Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys


TASK_ID = "38200022d1b7"
MODES = ("all_sources", "nearest_color", "farthest_color")
DEFAULT_SETTINGS = {"mode": "all_sources"}
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
QUERY_SHAPES = ((7, 9), (13, 17), (21, 25), (30, 30))
EXTRA_DEMO_SHAPES = ((9, 9), (11, 13), (17, 23), (25, 27))
SOURCE_PALETTE = (1, 2, 3, 4, 6, 7, 8, 9)


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must contain exactly one declared mode")
    return settings["mode"]


def program(settings):
    """Return the exact canonical text or a standalone executable alternative."""
    mode = _mode(settings)
    if mode == "all_sources":
        return CANONICAL
    comparison = "<" if mode == "nearest_color" else ">"
    return f"""(rule!
  (let* ([pivot (first (find-color g 5))]
         [pr (first pivot)] [pc (second pivot)]
         [sources
          (for*/list ([r (in-range (rows g))] [c (in-range (cols g))]
                      #:when (and (not (= (at g r c) 0))
                                  (not (= (at g r c) 5))))
            (list r c (at g r c)))]
         [distance (lambda (cell)
                     (+ (abs (- (first cell) pr))
                        (abs (- (second cell) pc))))]
         [selected
          (for/fold ([best (first sources)]) ([cell (in-list (rest sources))])
            (if ({comparison} (distance cell) (distance best)) cell best))]
         [color (third selected)])
    (for/fold ([out g]) ([cell (in-list sources)])
      (if (= (third cell) color)
          (set-cell out (- (* 2 pr) (first cell))
                        (- (* 2 pc) (second cell)) color)
          out))))"""


def analyze(grid):
    """Validate the common input grammar and return input-only geometry facts.

    Several extremal cells are allowed only if they share a color. Conflicting
    colors at either distance boundary are outside this unambiguous grammar.
    """
    if (type(grid) is not list or not 7 <= len(grid) <= 30
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in grid)):
        raise ValueError("grid must be rectangular 7..30 with exact colors 0..9")
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if len(pivots) != 1:
        raise ValueError("exactly one color-5 pivot is required")
    pr, pc = pivots[0]
    sources = [[r, c, v] for r, row in enumerate(grid) for c, v in enumerate(row)
               if v not in (0, 5)]
    counts = {color: sum(cell[2] == color for cell in sources)
              for color in sorted({cell[2] for cell in sources})}
    if not 6 <= len(sources) <= 420 or not 3 <= len(counts) <= 4:
        raise ValueError("expected 6..420 source cells using 3..4 source colors")
    if min(counts.values()) < 2:
        raise ValueError("every source color must occur at least twice")
    for r, c, _ in sources:
        rr, cc = 2 * pr - r, 2 * pc - c
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise ValueError("every reflected target must be in bounds")
        if grid[rr][cc] != 0:
            raise ValueError("reflected targets must be blank and disjoint from sources")
    distances = [abs(r - pr) + abs(c - pc) for r, c, _ in sources]
    lo, hi = min(distances), max(distances)
    nearest = {cell[2] for cell, distance in zip(sources, distances) if distance == lo}
    farthest = {cell[2] for cell, distance in zip(sources, distances) if distance == hi}
    if len(nearest) != 1 or len(farthest) != 1 or nearest == farthest:
        raise ValueError("nearest/farthest colors must each be unambiguous and different")
    return {"pivot": [pr, pc], "sources": sources, "colors": list(counts),
            "color_counts": counts, "min_distance": lo, "max_distance": hi,
            "nearest_color": next(iter(nearest)), "farthest_color": next(iter(farthest))}


def selected_color(grid, mode):
    _mode({"mode": mode})
    facts = analyze(grid)
    return None if mode == "all_sources" else facts[mode]


def apply_python(grid, settings):
    """Sampler label claim; the matching protected Racket program is authority."""
    mode = _mode(settings)
    facts = analyze(grid)
    color = None if mode == "all_sources" else facts[mode]
    pr, pc = facts["pivot"]
    out = [row[:] for row in grid]
    for r, c, value in facts["sources"]:
        if color is None or value == color:
            out[2 * pr - r][2 * pc - c] = value
    return out


def _rng(seed, stream, index=0):
    key = f"pivot-color-v1:{seed}:{stream}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _transform(grid, symmetry):
    out = [row[:] for row in grid]
    if symmetry & 1:
        out = [row[::-1] for row in out]
    if symmetry & 2:
        out.reverse()
    if symmetry & 4:
        out = [list(row) for row in zip(*out)]
    return out


def _teaching(seed, index):
    # Constructive two-demo basis: distance metric, color binding, off-center
    # pivot, mean/centroid, frequency, fixed-color and fixed-side distinctions.
    rng = _rng(seed, "teaching-shared")
    palette = rng.sample(SOURCE_PALETTE, 4)
    symmetry = rng.randrange(8)
    if index == 0:
        shape, pivot = (17, 19), (6, 10)
        groups = (
            ((0, -3), (-2, 3), (3, 2)),
            ((4, 4), (-1, -5), (2, -4)),
            ((-2, -2), (0, 6), (-3, -3), (1, 4)),
            ((-4, 1), (3, -1)),
        )
        colors = palette
    else:
        shape, pivot = (19, 21), (8, 11)
        # Near A and far B have greater/lower MEAN distance in the opposite
        # order. The selected colors and selected sides change between demos.
        groups = (
            ((0, 3), (0, 7), (-1, 7), (-1, 6)),
            ((4, 5), (-2, 2), (-2, 3), (-3, 2), (-1, 3)),
            ((2, 2), (2, 3)),
        )
        groups = tuple(tuple((-r, -c) for r, c in group) for group in groups)
        colors = (palette[1], palette[0], palette[2])
    h, w = shape
    pr, pc = pivot
    grid = [[0] * w for _ in range(h)]
    grid[pr][pc] = 5
    for color, group in zip(colors, groups):
        for dr, dc in group:
            grid[pr + dr][pc + dc] = color
    return _transform(grid, symmetry)


def _sample(seed, stream, index, shape):
    """Direct orbit construction: one source at most per antipodal pair."""
    rng = _rng(seed, stream, index)
    h, w = shape
    dense = shape == (30, 30)
    small = shape == (7, 9)
    if dense:
        pr, pc = rng.choice((14, 15)), rng.choice((14, 15))
    elif small:
        pr, pc = 3, 4
    else:
        pr = (h - 1) // 2 + rng.choice((-1, 0, 1))
        pc = (w - 1) // 2 + rng.choice((-1, 0, 1))
    radius_r, radius_c = min(pr, h - 1 - pr), min(pc, w - 1 - pc)
    orbits = [(dr, dc) for dr in range(-radius_r, radius_r + 1)
              for dc in range(-radius_c, radius_c + 1)
              if dr > 0 or (dr == 0 and dc > 0)]
    distance = lambda cell: abs(cell[0]) + abs(cell[1])
    lo, hi = 1, radius_r + radius_c
    near = rng.choice([cell for cell in orbits if distance(cell) == lo])
    far = rng.choice([cell for cell in orbits if distance(cell) == hi])
    interior = [cell for cell in orbits if lo < distance(cell) < hi]
    if dense:
        chosen = list(orbits)  # 420 sources: every pair in the lawful 29x29 box.
    else:
        count = 6 if small else rng.randint(12, min(64, len(interior) + 2))
        chosen = [near, far] + rng.sample(interior, count - 2)
    palette = rng.sample(SOURCE_PALETTE, 3 if small else 4)
    colors = {}
    for cell in chosen:
        if distance(cell) == lo:
            colors[cell] = palette[0]
        elif distance(cell) == hi:
            colors[cell] = palette[1]
    mid = [cell for cell in chosen if lo < distance(cell) < hi]
    rng.shuffle(mid)
    # Guarantee a remote copy for both bound colors and two of every distractor.
    required = [palette[0], palette[1]] + [color for color in palette[2:] for _ in range(2)]
    for i, cell in enumerate(mid):
        colors[cell] = required[i] if i < len(required) else rng.choice(palette)
    grid = [[0] * w for _ in range(h)]
    grid[pr][pc] = 5
    for dr, dc in sorted(chosen):
        sign = rng.choice((-1, 1))
        if dense:
            # Ensure actual input content spans the full lawful 29x29 box.
            sign = {(radius_r, radius_c): 1,
                    (radius_r, -radius_c): -1,
                    (0, radius_c): -1}.get((dr, dc), sign)
        grid[pr + sign * dr][pc + sign * dc] = colors[(dr, dc)]
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _mode(settings)
    training = [_teaching(seed, i) for i in range(2)]
    training += [_sample(seed, "demos", i, EXTRA_DEMO_SHAPES[i]) for i in range(demos - 2)]
    shapes = list(QUERY_SHAPES)
    _rng(seed, "query-order").shuffle(shapes)
    tests = [_sample(seed, "queries", i, shapes[i]) for i in range(queries)]
    grids = training + tests
    if len({json.dumps(grid) for grid in grids}) != len(grids):
        raise RuntimeError("direct sampler unexpectedly repeated an input")
    def pairs(inputs):
        return [{"input": grid, "output": apply_python(grid, settings)} for grid in inputs]
    return {"train": pairs(training), "test": pairs(tests),
            "settings": dict(settings), "seed": seed, "program_solution": program(settings)}


def _public_helpers():
    path = ROOT / "shared/runtime/reviewer_support.py"
    spec = importlib.util.spec_from_file_location("_pivot_public_support", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_turn_bytes(episode, query_index=0):
    """Project one turn without hidden settings, answers, counts or later inputs."""
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return _public_helpers().public_challenge_bytes(visible)


def write_public(episode, outdir, query_index=0):
    content = public_turn_bytes(episode, query_index)
    directory = Path(outdir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (hashlib.sha256(content).hexdigest() + ".json")
    path.write_bytes(content)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mode", choices=MODES, default="all_sources")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new directory")
    episode = generate(args.seed, {"mode": args.mode}, args.demos, args.queries)
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for pair in episode["train"] + episode["test"]:
                actual = _grid(apply(episode["program_solution"], pair["input"]))
                if actual != pair["output"]:
                    raise AssertionError("Python claim differs from protected Racket")
                pair["output"] = actual
        finally:
            bridge.close()
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise AssertionError("protected Racket execution is required")
    args.out.mkdir(parents=True)
    (args.out / "private_episode.json").write_text(json.dumps(episode, indent=2) + "\n")
    public_path = write_public(episode, args.out / "public")
    receipt = {"racket": identity, "checked_pairs": args.demos + args.queries,
               "public_file": str(public_path), "first_query_only": True,
               "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                   for path in (HERE / "prototype.py", HERE / "canonical.rkt")}}
    (args.out / "execution.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
