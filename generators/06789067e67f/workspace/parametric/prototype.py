"""Source-bound output-color policy family for 06789067e67f.

Stage A is always the source task's canonical operation: crop each component,
rank by holes/area/color, and pack the crops.  The episode-fixed ``output_colors``
parameter controls Stage B:

* ``original`` is the byte-exact canonical program and leaves packed colors alone.
* ``rank`` consumes the packed intermediate and recolors its left-to-right
  components 1, 2, 3, 4.

The input grammar is matched across settings.  Demonstrations teach the sort's
primary and tie-break keys; exactly four private queries are retained, including
a substantive 30x30 boundary case.  Python transforms are authoring mirrors;
retained semantic evidence replays labels through protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from itertools import permutations
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "06789067e67f"
DEFAULT_SETTINGS = {"output_colors": "original"}
SETTINGS = (
    {"output_colors": "original"},
    {"output_colors": "rank"},
)
PARAMETERS = {"output_colors": ["original", "rank"]}
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = (HERE / "canonical.rkt").read_text()
_RANK = (HERE / "rank.rkt").read_text()


class Shape:
    __slots__ = ("cells", "height", "width")

    def __init__(self, cells: tuple[tuple[int, int], ...], height: int, width: int):
        self.cells = cells
        self.height = height
        self.width = width


def _shape_rows(*rows: str) -> Shape:
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("shape rows must be nonempty and rectangular")
    return Shape(
        tuple((r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == "1"),
        len(rows),
        len(rows[0]),
    )


def _frame(height: int, width: int, dividers: tuple[int, ...] = ()) -> Shape:
    cells = set()
    for r in range(height):
        for c in range(width):
            if r in (0, height - 1) or c in (0, width - 1) or (c in dividers and 0 < r < height - 1):
                cells.add((r, c))
    return Shape(tuple(sorted(cells)), height, width)


def _c_shape(height: int, width: int) -> Shape:
    cells = set(_frame(height, width).cells)
    cells.discard((height // 2, width - 1))
    return Shape(tuple(sorted(cells)), height, width)


RING_3X3 = _shape_rows("111", "101", "111")
RING_3X4 = _shape_rows("1111", "1001", "1111")
TAILED_RING_4X3 = _shape_rows("011", "101", "111", "001")
DOUBLE_3X5 = _shape_rows("11111", "10101", "11111")
C_3X3 = _shape_rows("111", "100", "111")
SOLID_2X2 = _shape_rows("11", "11")
SOLID_2X3 = _shape_rows("111", "111")
SOLID_3X2 = _shape_rows("11", "11", "11")
SOLID_4X4 = _shape_rows("1111", "1111", "1111", "1111")


def _integer(value: object, name: str, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"output_colors"}:
        raise ValueError("settings must name exactly output_colors")
    mode = value["output_colors"]
    if type(mode) is not str or mode not in PARAMETERS["output_colors"]:
        raise ValueError("output_colors must be 'original' or 'rank'")
    return {"output_colors": mode}


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return grid


def program(settings: object) -> str:
    selected = _settings(settings)
    return _CANONICAL if selected == DEFAULT_SETTINGS else _RANK


def digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "rank-colors-v1", seed, stream, index]), 16))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            crop = [[0] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]
            for r, c in cells:
                crop[r - r1][c - c1] = color
            records.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "area": len(cells),
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "crop": crop,
                "holes": _hole_count(crop),
            })
    return records


def _hole_count(crop: list[list[int]]) -> int:
    height, width = len(crop), len(crop[0])
    seen: set[tuple[int, int]] = set()
    holes = 0
    for r in range(height):
        for c in range(width):
            if crop[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            touches = False
            while stack:
                rr, cc = stack.pop()
                if rr in (0, height - 1) or cc in (0, width - 1):
                    touches = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width
                            and crop[nr][nc] == 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches:
                holes += 1
    return holes


def _packed(records: list[dict[str, Any]]) -> list[list[int]]:
    if not 2 <= len(records) <= 4:
        raise ValueError(f"input must contain 2..4 components, found {len(records)}")
    height = max(len(record["crop"]) for record in records)
    width = sum(len(record["crop"][0]) for record in records) + len(records) - 1
    if height > 30 or width > 30:
        raise ValueError(f"packed output must fit 30x30, got {height}x{width}")
    out = [[0] * width for _ in range(height)]
    offset = 0
    for record in records:
        crop = record["crop"]
        for r, row in enumerate(crop):
            out[r][offset : offset + len(row)] = row
        offset += len(crop[0]) + 1
    return out


def canonical_transform(grid: list[list[int]]) -> list[list[int]]:
    records = _components(_grid(grid))
    keys = [(record["holes"], record["area"], record["color"]) for record in records]
    if len(set(keys)) != len(keys):
        raise ValueError("full (holes, area, color) sort keys must be unique")
    records.sort(key=lambda record: (-record["holes"], -record["area"], record["color"]))
    return _packed(records)


def rank_recolor(intermediate: list[list[int]]) -> list[list[int]]:
    records = _components(_grid(intermediate))
    if not 2 <= len(records) <= 4:
        raise ValueError("rank recolor expects 2..4 packed components")
    records.sort(key=lambda record: (record["c1"], record["r1"]))
    out = [row[:] for row in intermediate]
    for rank, record in enumerate(records, start=1):
        for r, c in record["cells"]:
            out[r][c] = rank
    return out


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    selected = _settings(settings)
    intermediate = canonical_transform(grid)
    return intermediate if selected["output_colors"] == "original" else rank_recolor(intermediate)


def skip_pack_counterfactual(grid: list[list[int]]) -> list[list[int]]:
    """Counterfactual B(input): rank components by original left-to-right position."""
    return rank_recolor(_grid(grid))


def _records_for_policy(grid: list[list[int]], policy: str) -> list[dict[str, Any]]:
    records = _components(_grid(grid))
    if policy == "input_position":
        key = lambda record: (record["c1"], record["r1"])
    elif policy == "holes_only":
        key = lambda record: (-record["holes"], record["c1"], record["r1"])
    elif policy == "holes_scan":
        key = lambda record: (-record["holes"],)
    elif policy == "area_only":
        key = lambda record: (-record["area"], record["c1"], record["r1"])
    elif policy == "area_scan":
        key = lambda record: (-record["area"],)
    elif policy == "holes_area_scan":
        key = lambda record: (-record["holes"], -record["area"])
    elif policy == "color_only":
        key = lambda record: (record["color"],)
    elif policy == "bbox_zeros":
        key = lambda record: (
            -(len(record["crop"]) * len(record["crop"][0]) - record["area"]),
            -record["area"],
            record["color"],
        )
    elif policy == "reverse_holes":
        key = lambda record: (record["holes"], -record["area"], record["color"])
    elif policy == "wrong_color_tie":
        key = lambda record: (-record["holes"], -record["area"], -record["color"])
    elif policy == "wrong_area_tie":
        key = lambda record: (-record["holes"], record["area"], record["color"])
    elif policy == "bbox_area":
        key = lambda record: (
            -(len(record["crop"]) * len(record["crop"][0])),
            -record["area"],
            record["color"],
        )
    elif policy == "height_only":
        key = lambda record: (-len(record["crop"]), -record["area"], record["color"])
    elif policy == "width_only":
        key = lambda record: (-len(record["crop"][0]), -record["area"], record["color"])
    elif policy == "source_top":
        key = lambda record: (record["r1"], record["c1"])
    else:
        raise KeyError(policy)
    return sorted(records, key=key)


SORT_RIVALS = (
    "input_position",
    "holes_only",
    "holes_scan",
    "area_only",
    "area_scan",
    "holes_area_scan",
    "color_only",
    "bbox_zeros",
    "reverse_holes",
    "wrong_color_tie",
    "wrong_area_tie",
    "bbox_area",
    "height_only",
    "width_only",
    "source_top",
)


def rival_transform(name: str, grid: list[list[int]], settings: object) -> list[list[int]]:
    selected = _settings(settings)
    if name in SORT_RIVALS:
        intermediate = _packed(_records_for_policy(grid, name))
        return intermediate if selected["output_colors"] == "original" else rank_recolor(intermediate)
    if name == "skip_pack_rank":
        return skip_pack_counterfactual(grid)
    if name == "partial_rank_first":
        intermediate = canonical_transform(grid)
        records = sorted(_components(intermediate), key=lambda record: (record["c1"], record["r1"]))
        out = [row[:] for row in intermediate]
        for r, c in records[0]["cells"]:
            out[r][c] = 1
        return out
    raise KeyError(name)


def _shape_key(shape: Shape, color: int) -> tuple[int, int, int]:
    crop = [[0] * shape.width for _ in range(shape.height)]
    for r, c in shape.cells:
        crop[r][c] = color
    return _hole_count(crop), len(shape.cells), color


def _profile_shapes(profile: str) -> list[Shape]:
    if profile == "tie_holes":
        return [RING_3X3, RING_3X4, DOUBLE_3X5, SOLID_4X4]
    if profile == "tie_area":
        return [RING_3X3, TAILED_RING_4X3, DOUBLE_3X5, C_3X3]
    if profile == "all_solid":
        return [SOLID_2X2, SOLID_2X3, SOLID_3X2, SOLID_4X4]
    if profile == "plain":
        return [DOUBLE_3X5, RING_3X3, C_3X3, SOLID_4X4]
    raise KeyError(profile)


def _colors(rng: random.Random) -> list[int]:
    return rng.sample([2, 3, 5, 6, 7, 8, 9], 4)


def _teaching_colors(rng: random.Random, shapes: list[Shape]) -> list[int]:
    """Choose varied colors without letting color order replace the real sort."""
    palette = tuple(_colors(rng))
    candidates = list(permutations(palette))
    rng.shuffle(candidates)
    for candidate in candidates:
        canonical_order = sorted(
            range(len(shapes)),
            key=lambda i: (
                -_shape_key(shapes[i], candidate[i])[0],
                -_shape_key(shapes[i], candidate[i])[1],
                candidate[i],
            ),
        )
        color_order = sorted(range(len(shapes)), key=lambda i: candidate[i])
        if canonical_order != color_order:
            return list(candidate)
    raise AssertionError("could not construct a color-order counterexample")


def _regular_scene(seed: int, split: str, index: int, profile: str) -> list[list[int]]:
    rng = _rng(seed, f"{split}:{profile}", index)
    shapes = _profile_shapes(profile)
    colors = _teaching_colors(rng, shapes)
    canonical_order = sorted(
        range(4),
        key=lambda i: (-_shape_key(shapes[i], colors[i])[0], -_shape_key(shapes[i], colors[i])[1], colors[i]),
    )
    placement_order = list(reversed(canonical_order))
    gaps = [1 + rng.randrange(2) for _ in range(3)]
    required = sum(shapes[i].width for i in placement_order) + sum(gaps)
    width = min(30, required + rng.randrange(1, 5))
    height = max(12, max(shape.height for shape in shapes) + 7 + rng.randrange(5))
    grid = [[0] * width for _ in range(height)]
    slack = width - required
    left = rng.randrange(slack + 1)
    column = left
    max_shape_height = max(shape.height for shape in shapes)
    aligned_row = rng.choice((0, (height - max_shape_height) // 2, height - max_shape_height))
    for slot, shape_index in enumerate(placement_order):
        shape = shapes[shape_index]
        if profile in {"tie_holes", "tie_area"}:
            # Keep tied objects on the same scan row so source scan order follows
            # the deliberately reversed left-to-right order instead of leaking
            # the missing area/color tie-break through vertical placement.
            row = aligned_row
        elif slot % 3 == 0:
            row = 0
        elif slot % 3 == 1:
            row = height - shape.height
        else:
            row = (height - shape.height) // 2
            # Seed-dependent nuisance motion changes source position without
            # changing the sorted packed intermediate.
            if 0 < row < height - shape.height and rng.randrange(2):
                row += 1
        color = colors[shape_index]
        for dr, dc in shape.cells:
            grid[row + dr][column + dc] = color
        if slot < 3:
            column += shape.width + gaps[slot]
    return grid


def _stress_scene(seed: int) -> list[list[int]]:
    rng = _rng(seed, "query:stress", 3)
    shapes = [_frame(9, 7, (3,)), _frame(9, 6), _shape_rows(*(["11111"] * 8)), _c_shape(8, 5)]
    colors = _colors(rng)
    canonical_order = sorted(
        range(4),
        key=lambda i: (-_shape_key(shapes[i], colors[i])[0], -_shape_key(shapes[i], colors[i])[1], colors[i]),
    )
    placement_order = list(reversed(canonical_order))
    gaps = (2, 3, 2)
    assert sum(shapes[i].width for i in placement_order) + sum(gaps) == 30
    grid = [[0] * 30 for _ in range(30)]
    column = 0
    for slot, shape_index in enumerate(placement_order):
        shape = shapes[shape_index]
        row = 0 if slot % 2 == 0 else 30 - shape.height
        color = colors[shape_index]
        for dr, dc in shape.cells:
            grid[row + dr][column + dc] = color
        if slot < 3:
            column += shape.width + gaps[slot]
    return grid


def _scene(seed: int, split: str, index: int) -> list[list[int]]:
    if split == "query" and index == 3:
        return _stress_scene(seed)
    profiles = ("tie_holes", "tie_area", "plain", "all_solid", "tie_holes", "tie_area")
    offset = 0 if split == "demo" else 2
    return _regular_scene(seed, split, index, profiles[(index + offset) % len(profiles)])


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    records = _components(_grid(grid))
    cells = [cell for record in records for cell in record["cells"]]
    min_r = min(r for r, _ in cells)
    max_r = max(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    max_c = max(c for _, c in cells)
    h, w = len(grid), len(grid[0])
    return {
        "height": h,
        "width": w,
        "components": len(records),
        "foreground_cells": len(cells),
        "row_span": max_r - min_r + 1,
        "column_span": max_c - min_c + 1,
        "touches_boundary": min_r == 0 or min_c == 0 or max_r == h - 1 or max_c == w - 1,
        "keys": sorted((record["holes"], record["area"], record["color"]) for record in records),
    }


def certify(
    episode: dict[str, Any],
    *,
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    selected = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(selected):
        raise ValueError("private program does not match selected setting")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode requires train/test lists")
    _integer(len(train), "demos", *DEMO_LIMITS)
    if len(test) != QUERY_COUNT:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    inputs = []
    for split_name, rows in (("train", train), ("test", test)):
        for index, pair in enumerate(rows):
            if type(pair) is not dict or set(pair) != {"input", "output"}:
                raise ValueError(f"malformed {split_name} pair {index}")
            _grid(pair["input"])
            _grid(pair["output"])
            inputs.append(pair["input"])
    if len({digest(grid) for grid in inputs}) != len(inputs):
        raise ValueError("demonstration and query inputs must be distinct")

    def predict(setting: dict[str, str], grid: list[list[int]]) -> list[list[int]]:
        return transform(grid, setting) if execute is None else execute(program(setting), grid)

    for split_name, rows in (("train", train), ("test", test)):
        for index, pair in enumerate(rows):
            if predict(selected, pair["input"]) != pair["output"]:
                raise ValueError(f"label mismatch in {split_name} pair {index}")
    survivors = [
        dict(candidate)
        for candidate in SETTINGS
        if all(predict(candidate, pair["input"]) == pair["output"] for pair in train)
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")

    rival_names = list(SORT_RIVALS)
    if selected["output_colors"] == "rank":
        rival_names += ["skip_pack_rank", "partial_rank_first"]
    refutations = {}
    for name in rival_names:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if rival_transform(name, pair["input"], selected) != pair["output"]
        ]
        if not disagreements:
            raise ValueError(f"named rival {name!r} survives every demonstration")
        refutations[name] = disagreements
    return {
        "survivors": survivors,
        "demo_only": True,
        "rival_refutations": refutations,
        "racket_checked": execute is not None,
        "queries": [
            {"index": index, "input_sha256": digest(pair["input"]), "output_sha256": digest(pair["output"])}
            for index, pair in enumerate(test)
        ],
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", 0, 2**63 - 1)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    if type(queries) is not int or queries != QUERY_COUNT:
        raise ValueError("queries must be the exact integer 4")
    selected = _settings(DEFAULT_SETTINGS if settings is None else settings)
    train_inputs = [_scene(seed, "demo", index) for index in range(demos)]
    test_inputs = [_scene(seed, "query", index) for index in range(QUERY_COUNT)]
    episode = {
        "schema": "arcpuzzles-06789067e67f-rank-colors-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": selected,
        "train": [{"input": grid, "output": transform(grid, selected)} for grid in train_inputs],
        "test": [{"input": grid, "output": transform(grid, selected)} for grid in test_inputs],
        "program_solution": program(selected),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    _integer(index, "query index", 0, QUERY_COUNT - 1)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != QUERY_COUNT:
        raise ValueError("episode must retain exactly four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


def _datum(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source: str, grid: list[list[int]], *, bridge: Any | None = None) -> list[list[int]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    own = bridge is None
    bridge = RacketBridge(timeout=60) if own else bridge
    try:
        result = bridge.eval_text(f"({wrap_rule(source)} {_datum(_grid(grid))})")
        return _grid(result)
    finally:
        if own:
            bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "canonical.rkt",
        HERE / "rank.rkt",
        HERE / "skip_pack.rkt",
        HERE / "semantic_sweep.py",
        HERE / "adversarial_probe.py",
        HERE.parents[1] / "generator.py",
    ]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths if path.exists()
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", action="append", type=int, default=[])
    parser.add_argument("--output-colors", choices=PARAMETERS["output_colors"], default="original")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    selected_settings = list(SETTINGS) if args.all_settings else [{"output_colors": args.output_colors}]
    seeds = args.seed or [0]
    args.out.mkdir(parents=True)
    public_dir = args.out / "public"
    public_dir.mkdir()
    private_rows = []
    seen = set()
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=60) as bridge:
        runtime = bridge.runtime_identity
        for selected in selected_settings:
            for seed in seeds:
                episode = generate(seed, selected, args.demos, args.queries)
                episode["certificate"] = certify(
                    episode,
                    execute=lambda source, grid: execute_rule(source, grid, bridge=bridge),
                )
                visible = public_turn(episode, 0)
                identifier = public_challenge_id(visible)
                if identifier in seen:
                    raise ValueError(f"duplicate public first turn {identifier}")
                seen.add(identifier)
                (public_dir / f"{identifier}.json").write_bytes(public_challenge_bytes(visible))
                private_rows.append(dict(episode, public_id=identifier))
    manifest = {
        "schema": "arcpuzzles-06789067e67f-rank-colors-evidence-v1",
        "status": "prototype_proposed",
        "runtime": runtime,
        "source_sha256": source_hashes(),
        "episodes": private_rows,
        "public_ids": sorted(seen),
        "finite_scope": "two output-color settings plus named sort/order/bypass rivals",
        "training_admitted": False,
    }
    (args.out / "private.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (args.out / "manifest.json").write_text(json.dumps({
        "schema": manifest["schema"],
        "status": manifest["status"],
        "episode_count": len(private_rows),
        "public_ids": manifest["public_ids"],
        "source_sha256": manifest["source_sha256"],
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "prototype_proposed", "episodes": len(private_rows), "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
