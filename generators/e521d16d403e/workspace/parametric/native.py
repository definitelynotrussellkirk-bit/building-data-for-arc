"""Native three-rule family: rank symmetric objects, optionally follow their color.

The retained prototype owns the exact canonical and bbox-area programs. This
module extends its input grammar and adds an input-dependent partner selection.
All labels execute in protected Racket; construction metadata never labels grids.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id, normalize_grid

HERE = Path(__file__).resolve().parent
TASK_ID = "e521d16d403e"
RULES = ("occupied_cells", "bbox_area", "occupied_anchor_partner")
SETTINGS = tuple({"selection_rule": name} for name in RULES)
DEMO_SIZES = ((16, 20), (18, 22), (20, 24), (22, 26), (24, 22), (26, 24))
QUERY_SIZES = ((14, 18), (22, 24), (30, 30), (26, 30))


def _load_prototype():
    path = HERE / "prototype.py"
    name = "_e521_native_prototype_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PROTOTYPE = _load_prototype()


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"selection_rule"}
            or type(settings["selection_rule"]) is not str
            or settings["selection_rule"] not in RULES):
        raise ValueError("settings must contain exactly one declared selection_rule")
    return settings["selection_rule"]


def program(settings):
    """Return the exact reference; the default is byte-identical to canonical."""
    name = _setting(settings)
    if name in ("occupied_cells", "bbox_area"):
        return _PROTOTYPE.materialize_rule(name)
    source = _PROTOTYPE.materialize_rule("occupied_cells")
    needle = "    (let* ((bb (obj-bbox chosen))"
    if source.count(needle) != 1:
        raise ValueError("canonical final crop no longer matches the guarded extension")
    replacement = """    (define anchor-color (obj-color chosen))
    (define partners
      (filter (lambda (o)
                (and (= (obj-color o) anchor-color)
                     (not (equal? (obj-bbox o) (obj-bbox chosen))))) objs))
    (define target (if (empty? partners) chosen (first partners)))
    (let* ((bb (obj-bbox target))"""
    return source.replace(needle, replacement, 1)


def _rng(seed, stream, index):
    material = f"{TASK_ID}/native-v1/{seed}/{stream}/{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _dense(height, width, trim):
    rows = [[1] * width for _ in range(height)]
    if trim:
        for row in rows[1:]:
            row[0] = row[-1] = 0
    return rows


def _cross(height, width, arm_row):
    rows = [[0] * width for _ in range(height)]
    for row in rows:
        row[width // 2] = 1
    rows[arm_row] = [1] * width
    return rows


def _partner(height, width, variant):
    """Connected asymmetric bboxes, including UD-only symmetric distractors."""
    rows = [[1] * width for _ in range(height)]
    rows[0][-1] = 0
    if variant == 0:
        rows[-1][-1] = 0
    return rows


def _scene(seed, stream, index, size):
    rng = _rng(seed, stream, index)
    height, width = size
    phase = index % 2
    if stream == "demo" and index < 2:
        # The first two teaching scenes reverse object order, global rank,
        # partner size rank and proximity. Both identify all three rules.
        dense = _dense(2, 4, False) if phase == 0 else _dense(5, 2, False)
        sparse = _cross(5, 3, 1) if phase == 0 else _cross(3, 5, 1)
    elif stream == "query" and index == 0:
        dense, sparse = _dense(5, 2, False), _cross(3, 5, 1)
    elif stream == "query" and index == 3:
        dense = _dense(rng.choice((7, 8)), 5, True)
        sparse = _cross(7, rng.choice((9, 11)), rng.choice((1, 3, 5)))
    elif min(size) >= 26:
        dense = _dense(rng.choice((5, 6)), rng.choice((7, 8)), True)
        sparse = _cross(rng.choice((9, 11)), 7, rng.choice((2, 4, 6)))
    elif min(size) >= 20:
        dense = _dense(3, rng.choice((5, 6)), bool(rng.randrange(2)))
        sparse = _cross(7, 5, rng.choice((1, 3, 5)))
    else:
        dense = _dense(2, 4, False)
        sparse = _cross(3, 3, 1)

    if sum(map(sum, dense)) <= sum(map(sum, sparse)):
        dense = _dense(len(dense), len(dense[0]), False)

    if stream == "demo" and index == 1:
        pd = [[1, 0], [1, 1], [1, 1]]
        ps = [[1, 0], [1, 1]]
    else:
        ph = min((height - 3) // 2, len(dense) + 1 + rng.randrange(2))
        pw = min((width - 5) // 2, len(dense[0]) + 1)
        pd, ps = _partner(ph, pw, 0), _partner(ph, pw, 1)
        if stream == "query" and index % 2:
            pd, ps = ps, pd

    palette = list(range(1, 10))
    # Deliberately swap the two anchor colors between mandatory demos.
    _rng(seed, "palette", 0 if stream == "demo" and index < 2 else index + 2).shuffle(palette)
    if stream == "demo" and index == 1:
        palette[0], palette[1] = palette[1], palette[0]
    shapes = {"dense": (dense, palette[0]), "sparse": (sparse, palette[1]),
              "pd": (pd, palette[0]), "ps": (ps, palette[1])}

    top_h, left_w = (height - 3) // 2, (width - 5) // 2
    zones = ((0, 0, top_h, left_w),
             (0, left_w + 3, top_h, width - 5 - left_w),
             (top_h + 3, 0, height - 3 - top_h, left_w),
             (top_h + 3, left_w + 3, height - 3 - top_h, width - 5 - left_w))
    if stream == "demo" and index == 0:
        order = ("dense", "ps", "sparse", "pd")
    elif stream == "demo" and index == 1:
        order = ("pd", "sparse", "dense", "ps")
    else:
        order = list(shapes)
        rng.shuffle(order)
    grid = [[0] * width for _ in range(height)]

    def paint(shape, row0, col0, color):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    if not (0 <= row0+r < height and 0 <= col0+c < width):
                        raise AssertionError("constructed object exceeds its board")
                    if grid[row0+r][col0+c]:
                        raise AssertionError("constructed object overlap")
                    grid[row0+r][col0+c] = color

    for zone_index, (name, zone) in enumerate(zip(order, zones)):
        shape, color = shapes[name]
        r0, c0, zh, zw = zone
        rh, cw = zh - len(shape), zw - len(shape[0])
        if min(rh, cw) < 0:
            raise AssertionError("shape does not fit its constructive quadrant")
        if size == (30, 30):
            # Actual large shapes occupy all quadrants and contact board edges.
            dr = 0 if zone_index < 2 else rh
            dc = 0 if zone_index % 2 == 0 else cw
        else:
            dr, dc = rng.randint(0, rh), rng.randint(0, cw)
        paint(shape, r0+dr, c0+dc, color)

    # An extra eligible component defeats minimum-size / two-object shortcuts.
    paint([[1, 1, 1]], top_h + 1, left_w, palette[2])
    # Width-one is excluded even when longer than a legitimate anchor is large.
    bar_length = min(height, max(sum(map(sum, dense)), len(sparse)*len(sparse[0])) + 1)
    bar_row = 0 if size == (30, 30) else rng.randint(0, height - bar_length)
    paint([[1]] * bar_length, bar_row, width-1, palette[3])
    return grid


def sample_inputs(seed, demos=3, queries=4):
    """Construct without retries, using independent demonstration/query streams."""
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    return {"train": [_scene(seed, "demo", i, DEMO_SIZES[i]) for i in range(demos)],
            "test": [_scene(seed, "query", i, QUERY_SIZES[i]) for i in range(queries)]}


def execute(source, grid, bridge):
    """Execute a materialized program through the existing protected runtime."""
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


def generate(seed, settings, demos=3, queries=4):
    source = program(settings)
    inputs = sample_inputs(seed, demos, queries)
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise RuntimeError("native labels require protected Racket")
        pairs = {split: [{"input": grid, "output": execute(source, grid, bridge)}
                         for grid in grids] for split, grids in inputs.items()}
    return {**pairs, "program_solution": source}


def public_turn(episode, query_index=0):
    """Projection only: no controller, future input, turn number or total hint."""
    _integer(query_index, 0, len(episode["test"])-1, "query_index")
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(visible))


def write_examples(out, seed=0, demos=3):
    """Keep four queries private and save only first-turn model-visible files."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    rows = []
    for settings in SETTINGS:
        episode = generate(seed, settings, demos, 4)
        visible = public_turn(episode)
        identity = public_challenge_id(visible)
        public_path = f"public/challenge-{identity}.json"
        private_path = f"private/{identity}.json"
        (out / public_path).write_bytes(public_challenge_bytes(visible))
        private = {**copy.deepcopy(episode), "seed": seed, "settings": settings,
                   "status": "reviewer_example_owner_acceptance_pending"}
        (out / private_path).write_text(json.dumps(private, sort_keys=True) + "\n")
        rows.append({"public_path": public_path, "private_path": private_path,
                     "settings": settings, "demos": demos, "private_queries": 4})
    report = {"task_id": TASK_ID, "seed": seed, "episodes": sorted(rows, key=lambda r: r["public_path"]),
              "visibility": "Each public file is only the first turn. Four queries remain controller-private."}
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args()
    result = write_examples(args.out, args.seed, args.demos)
    print(json.dumps({"episodes": len(result["episodes"]), "out": str(args.out)}))
