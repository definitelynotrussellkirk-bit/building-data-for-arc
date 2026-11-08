"""Native two-rule family for assembling four row-grouped objects.

The default is the canonical left-to-right lower-row order.  The alternative
binds the top-left object's observed color and places its lower-row partner
first.  Inputs are setting-independent; labels execute in protected Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "b98cdd1751a7"
RULES = ("left_right", "match_top_left_color")
SETTINGS = tuple({"bottom_order": value} for value in RULES)
DEMO_SIZES = ((14, 18), (16, 20), (18, 22), (20, 24), (22, 26), (24, 28))
QUERY_SIZES = ((15, 19), (21, 25), (26, 28), (30, 30))


def _canonical_source():
    root = find_root(__file__)
    rows = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            rows.append(row)
    if len(rows) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, got {len(rows)}")
    source = rows[0].get("program_solution")
    if not isinstance(source, str) or not source.startswith("(rule!"):
        raise ValueError("canonical row has no materialized rule source")
    return source


CANONICAL_SOURCE = _canonical_source()
_BOTTOM_BINDING = (
    "(bot (sort-by (filter (lambda (o) (>= (min-of fst (obj-cells o)) mid-r)) objs) "
    "(lambda (o) (min-of snd (obj-cells o)))))"
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"bottom_order"}
            or type(settings["bottom_order"]) is not str
            or settings["bottom_order"] not in RULES):
        raise ValueError("settings must contain exactly one declared bottom_order")
    return settings["bottom_order"]


def program(settings):
    """Materialize a total rule; the default is byte-identical to canonical."""
    rule = _setting(settings)
    if rule == "left_right":
        return CANONICAL_SOURCE
    if CANONICAL_SOURCE.count(_BOTTOM_BINDING) != 1:
        raise ValueError("canonical lower-row binding no longer matches guarded extension")
    replacement = (
        "(bot-spatial (sort-by (filter (lambda (o) (>= (min-of fst (obj-cells o)) mid-r)) objs) "
        "(lambda (o) (min-of snd (obj-cells o))))) "
        "(cue-color (obj-color (fst top))) "
        "(bot (append "
        "(filter (lambda (o) (= (obj-color o) cue-color)) bot-spatial) "
        "(filter (lambda (o) (not (= (obj-color o) cue-color))) bot-spatial)))"
    )
    return CANONICAL_SOURCE.replace(_BOTTOM_BINDING, replacement, 1)


def _rng(seed, stream, index):
    material = f"{TASK_ID}/native-v1/{seed}/{stream}/{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _normalize(shape):
    r0 = min(row for row, _ in shape)
    c0 = min(col for _, col in shape)
    return tuple(sorted((row - r0, col - c0) for row, col in shape))


def _variants(shape):
    variants = set()
    current = tuple(shape)
    for mirrored in (False, True):
        transformed = tuple((row, -col) if mirrored else (row, col) for row, col in current)
        for _ in range(4):
            variants.add(_normalize(transformed))
            transformed = tuple((col, -row) for row, col in transformed)
    return tuple(sorted(variants))


_SHAPES = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
)
_SHAPE_VARIANTS = tuple(_variants(shape) for shape in _SHAPES)


def _anchors(height, width, stream, index, rng):
    if (height, width) == (30, 30):
        return ((0, 0), (0, 27), (27, 0), (27, 27))
    mode = (index + (0 if stream == "demo" else 1)) % 3
    if mode == 0:
        top_row = 1 + rng.randrange(max(1, min(3, height // 4)))
        bottom_row = height - 3 - rng.randrange(max(1, min(3, height // 4)))
    elif mode == 1:
        top_row = 0
        bottom_row = (height - 1) // 2
    else:
        top_row = (height + 1) // 2
        bottom_row = height - 3
    if bottom_row - top_row < 4:
        raise AssertionError("constructive row bands are not separated")
    left_col = rng.randrange(0, min(3, width - 6))
    right_margin = rng.randrange(0, min(3, width - 6))
    right_col = width - 3 - right_margin
    return ((top_row, left_col), (top_row, right_col),
            (bottom_row, left_col), (bottom_row, right_col))


def _scene(seed, stream, index, size):
    rng = _rng(seed, stream, index)
    height, width = size
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if stream == "demo" and index == 0:
        cue_color, other_color = max(palette[0], palette[1]), min(palette[0], palette[1])
        match_on_left = True
    elif stream == "demo" and index == 1:
        cue_color, other_color = min(palette[0], palette[1]), max(palette[0], palette[1])
        match_on_left = False
    else:
        cue_color, other_color = palette[0], palette[1]
        match_on_left = index % 2 == 0

    shape_ids = rng.sample(range(len(_SHAPE_VARIANTS)), 4)
    shapes = [rng.choice(_SHAPE_VARIANTS[shape_id]) for shape_id in shape_ids]
    anchors = _anchors(height, width, stream, index, rng)
    bottom_colors = ((cue_color, other_color) if match_on_left
                     else (other_color, cue_color))
    colors = (cue_color, other_color, *bottom_colors)
    grid = [[0] * width for _ in range(height)]
    for shape, color, (row0, col0) in zip(shapes, colors, anchors):
        for row, col in shape:
            rr, cc = row0 + row, col0 + col
            if not (0 <= rr < height and 0 <= cc < width):
                raise AssertionError("constructed shape exceeds its board")
            if grid[rr][cc] != 0:
                raise AssertionError("constructed shapes overlap")
            grid[rr][cc] = color
    return grid


def sample_inputs(seed, demos=3, queries=4):
    """Construct matched, prefix-stable input streams without rejection loops."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    return {
        "train": [_scene(seed, "demo", index, DEMO_SIZES[index])
                  for index in range(demos)],
        "test": [_scene(seed, "query", index, QUERY_SIZES[index])
                 for index in range(queries)],
    }


def execute(source, grid, bridge):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def generate(seed, settings, demos=3, queries=4):
    source = program(settings)
    inputs = sample_inputs(seed, demos, queries)
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("native labels require protected Racket")
        pairs = {
            split: [
                {"input": grid, "output": execute(source, grid, bridge)}
                for grid in grids
            ]
            for split, grids in inputs.items()
        }
    return {**pairs, "program_solution": source}


def public_turn(episode, query_index=0):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(visible))


def write_examples(out, seed=0, demos=3):
    """Write private four-query episodes and hash-named first-turn projections."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    index = []
    for settings in SETTINGS:
        episode = generate(seed, settings, demos, 4)
        visible = public_turn(episode)
        identity = public_challenge_id(visible)
        public_path = out / "public" / f"challenge-{identity}.json"
        private_path = out / "private" / f"{identity}.json"
        public_path.write_bytes(public_challenge_bytes(visible))
        private_path.write_text(json.dumps({"settings": settings, **episode}, indent=2) + "\n")
        index.append({"id": identity, "settings": settings,
                      "public": public_path.relative_to(out).as_posix(),
                      "private": private_path.relative_to(out).as_posix()})
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args(argv)
    write_examples(args.out, args.seed, args.demos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
