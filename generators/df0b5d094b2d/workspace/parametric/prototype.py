#!/usr/bin/env python3
"""Racket-backed move-distance parameter for ARC family df0b5d094b2d.

The marker-8 corner interpretation and full-rectangle reconstruction are
unchanged.  A hidden episode setting chooses whether every rectangle moves one
(the exact canonical/default rule) or two diagonal cells toward its marked
corner.  Input sampling is independent of that setting and keeps both moves
in-bounds and pairwise disjoint, including an exact 30x30 stress query.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "df0b5d094b2d"
ROOT = find_root(__file__)
MOVE_DISTANCES = (1, 2)
DEFAULT_MOVE_DISTANCE = 1
STATUS = "proposed prototype; not production-approved"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 8)
_DEMO_SIZES = ((10, 10), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22))
_DEMO_COUNTS = (2, 3, 4, 2, 3, 4)
_QUERY_SIZES = ((10, 10), (16, 20), (24, 26), (30, 30))
_QUERY_COUNTS = (2, 3, 4, 4)
_DR_ANCHOR = "(dr (if (= mr br1) -1 1))"
_DR_VARIANT = "(dr (if (= mr br1) -2 2))"
_DC_ANCHOR = "(dc (if (= mc bc1) -1 1))"
_DC_VARIANT = "(dc (if (= mc bc1) -2 2))"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid: list[list[int]]) -> str:
    return digest(json.dumps(grid, separators=(",", ":")).encode("utf-8"))


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def _validate_distance(move_distance: int) -> None:
    if type(move_distance) is not int or move_distance not in MOVE_DISTANCES:
        raise ValueError(f"move_distance must be one of {MOVE_DISTANCES}")


def validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be an integer in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(queries) is not int or not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be an integer in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")


def program_for(
    move_distance: int = DEFAULT_MOVE_DISTANCE,
    *,
    root: Path | str = ROOT,
) -> str:
    """Return the exact canonical program or its two-axis distance variant."""
    _validate_distance(move_distance)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_DR_ANCHOR) != 1 or canonical.count(_DC_ANCHOR) != 1:
        raise ValueError("canonical move-distance anchors changed; prototype needs review")
    if move_distance == DEFAULT_MOVE_DISTANCE:
        return canonical
    return canonical.replace(_DR_ANCHOR, _DR_VARIANT, 1).replace(
        _DC_ANCHOR, _DC_VARIANT, 1
    )


def _callable_text(program: str) -> str:
    return wrap_rule(program)


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if any(type(row) is not list or not row for row in grid):
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if not 1 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with 1..30 columns")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC colors 0..9")
    return len(grid), width


def _corner_cells(r0: int, c0: int, r1: int, c1: int) -> tuple[tuple[int, int], ...]:
    return ((r0, c0), (r0, c1), (r1, c0), (r1, c1))


def _direction(corner: int) -> tuple[int, int]:
    return (
        -1 if corner in (0, 1) else 1,
        -1 if corner in (0, 2) else 1,
    )


def _intersects(first: tuple[int, int, int, int], second: tuple[int, int, int, int]) -> bool:
    return (
        max(first[0], second[0]) <= min(first[2], second[2])
        and max(first[1], second[1]) <= min(first[3], second[3])
    )


def _objects(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = _validate_grid(grid)
    colors = sorted({cell for row in grid for cell in row if cell not in (7, 8)})
    if not colors:
        raise ValueError("input contains no colored rectangles")
    objects: list[dict[str, Any]] = []
    expected_markers: set[tuple[int, int]] = set()
    for color in colors:
        cells = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        corners = _corner_cells(r0, c0, r1, c1)
        missing = [index for index, cell in enumerate(corners) if cell not in cells]
        if len(missing) != 1:
            raise ValueError(f"color {color} must omit exactly one bbox corner")
        corner = missing[0]
        marker = corners[corner]
        expected = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if (r, c) != marker
        }
        if cells != expected or grid[marker[0]][marker[1]] != 8:
            raise ValueError(f"color {color} must fill its bbox except marker 8")
        if not (2 <= r1 - r0 + 1 <= 5 and 2 <= c1 - c0 + 1 <= 5):
            raise ValueError(f"color {color} rectangle must be 2..5 by 2..5")
        dr, dc = _direction(corner)
        objects.append(
            {
                "color": color,
                "bbox": (r0, c0, r1, c1),
                "corner": corner,
                "marker": marker,
                "dr": dr,
                "dc": dc,
            }
        )
        expected_markers.add(marker)
    actual_markers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    if actual_markers != expected_markers:
        raise ValueError("marker cells must equal the missing corner of every rectangle")
    for index, first in enumerate(objects):
        for second in objects[index + 1 :]:
            if _intersects(first["bbox"], second["bbox"]):
                raise ValueError("source rectangle bboxes must be disjoint")
    return objects


def transform(grid: list[list[int]], move_distance: int) -> list[list[int]]:
    """Independent Python mirror; evidence labels are executed by Racket."""
    _validate_distance(move_distance)
    h, w = _validate_grid(grid)
    objects = _objects(grid)
    output = [[7 for _ in range(w)] for _ in range(h)]
    output_boxes: list[tuple[int, int, int, int]] = []
    for obj in objects:
        r0, c0, r1, c1 = obj["bbox"]
        dr, dc = obj["dr"] * move_distance, obj["dc"] * move_distance
        box = (r0 + dr, c0 + dc, r1 + dr, c1 + dc)
        if not (0 <= box[0] <= box[2] < h and 0 <= box[1] <= box[3] < w):
            raise ValueError("translated rectangle must remain in bounds")
        if any(_intersects(box, prior) for prior in output_boxes):
            raise ValueError("translated rectangle bboxes must remain disjoint")
        output_boxes.append(box)
        for r in range(box[0], box[2] + 1):
            for c in range(box[1], box[3] + 1):
                output[r][c] = obj["color"]
    return output


def _shape_dimensions(h: int, w: int, count: int, index: int) -> list[tuple[int, int]]:
    if min(h, w) <= 10:
        return [(3, 3)] * count
    if min(h, w) >= 24 and count == 4:
        return [(5, 4), (4, 5), (5, 4), (4, 5)]
    base = 3 if min(h, w) < 18 else 4
    dimensions = []
    for shape_index in range(count):
        rh = min(5, base + ((index + shape_index) % 2))
        rw = min(5, base + ((index + shape_index + 1) % 2))
        dimensions.append((rh, rw))
    return dimensions


def _paint_specs(
    h: int,
    w: int,
    specs: list[tuple[int, int, int, int, int, int]],
) -> list[list[int]]:
    grid = [[7 for _ in range(w)] for _ in range(h)]
    for color, r0, c0, rh, rw, corner in specs:
        marker = _corner_cells(r0, c0, r0 + rh - 1, c0 + rw - 1)[corner]
        for r in range(r0, r0 + rh):
            for c in range(c0, c0 + rw):
                grid[r][c] = 8 if (r, c) == marker else color
    return grid


def sample_input(
    seed: int,
    index: int,
    *,
    size: tuple[int, int] | None = None,
    shape_count: int | None = None,
    root: Path | str = ROOT,
) -> list[list[int]]:
    """Build a setting-neutral scene safe for one- and two-cell moves."""
    del root
    if type(seed) is not int or seed < 0 or type(index) is not int or index < 0:
        raise ValueError("seed and index must be nonnegative Python integers")
    if size is None:
        size = _DEMO_SIZES[index % len(_DEMO_SIZES)]
    if (
        type(size) is not tuple
        or len(size) != 2
        or any(type(value) is not int or not 10 <= value <= 30 for value in size)
    ):
        raise ValueError("size must be a (height, width) pair in 10..30")
    h, w = size
    if shape_count is None:
        shape_count = min(4, 2 + index % 3)
    if type(shape_count) is not int or not 2 <= shape_count <= 4:
        raise ValueError("shape_count must be an integer in 2..4")
    corner_sets = {2: (0, 3), 3: (0, 1, 3), 4: (0, 1, 2, 3)}
    corners = corner_sets[shape_count]
    dimensions = _shape_dimensions(h, w, shape_count, index)
    palette = (1, 2, 3, 4, 5, 6, 9)
    rotation = int(digest(f"{seed}|{index}|df0".encode())[:8], 16) % len(palette)
    colors = [palette[(rotation + offset) % len(palette)] for offset in range(shape_count)]
    specs: list[tuple[int, int, int, int, int, int]] = []
    for shape_index, (corner, (rh, rw), color) in enumerate(zip(corners, dimensions, colors)):
        top = corner in (0, 1)
        left = corner in (0, 2)
        r0 = 2 if top else h - rh - 2
        c0 = 2 if left else w - rw - 2
        if r0 < 2 or c0 < 2:
            raise ValueError("size cannot provide two-cell movement margin")
        specs.append((color, r0, c0, rh, rw, corner))
    grid = _paint_specs(h, w, specs)
    # Both parameter settings must be lawful before the input can enter an episode.
    transform(grid, 1)
    transform(grid, 2)
    return grid


def input_profile(grid: list[list[int]]) -> dict[str, int]:
    objects = _objects(grid)
    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 7
    ]
    rows = [r for r, _ in occupied]
    cols = [c for _, c in occupied]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_count": len(objects),
        "occupied_cells": len(occupied),
        "span_rows": max(rows) - min(rows) + 1,
        "span_cols": max(cols) - min(cols) + 1,
    }


def _distinct_input(
    seed: int,
    index: int,
    size: tuple[int, int],
    shape_count: int,
    seen: set[str],
    *,
    root: Path | str,
) -> list[list[int]]:
    for retry in range(32):
        grid = sample_input(
            seed + retry * 1_000_003,
            index,
            size=size,
            shape_count=shape_count,
            root=root,
        )
        key = grid_digest(grid)
        if key not in seen:
            seen.add(key)
            return grid
    raise ValueError("distinct input budget exhausted; no partial episode")


def episode_inputs(
    seed: int,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    validate_counts(demos, queries)
    seen: set[str] = set()
    demo_grids = [
        _distinct_input(
            seed,
            index,
            _DEMO_SIZES[index],
            _DEMO_COUNTS[index],
            seen,
            root=root,
        )
        for index in range(demos)
    ]
    query_grids = [
        _distinct_input(
            seed ^ 0xDF0B5D09,
            index,
            _QUERY_SIZES[index % len(_QUERY_SIZES)],
            _QUERY_COUNTS[index % len(_QUERY_COUNTS)],
            seen,
            root=root,
        )
        for index in range(queries)
    ]
    return demo_grids, query_grids


def _settings_surviving(
    train_inputs: list[list[list[int]]],
    train_outputs: list[list[list[int]]],
) -> list[dict[str, int]]:
    return [
        {"move_distance": distance}
        for distance in MOVE_DISTANCES
        if all(transform(grid, distance) == output for grid, output in zip(train_inputs, train_outputs))
    ]


def validate_public(public: dict[str, Any]) -> None:
    if type(public) is not dict or set(public) != {"train", "test"}:
        raise ValueError("public challenge must contain only train and test")
    if type(public["train"]) is not list or type(public["test"]) is not list:
        raise ValueError("public train/test must be lists")
    if not public["train"] or not public["test"]:
        raise ValueError("public train/test must be nonempty")
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in public["train"]):
        raise ValueError("public demonstrations require only input and output")
    if any(type(pair) is not dict or set(pair) != {"input"} for pair in public["test"]):
        raise ValueError("public query must contain only input")
    public_challenge_bytes(public)


def sequential_views(public: dict[str, Any]) -> list[dict[str, Any]]:
    validate_public(public)
    return [
        {"train": public["train"], "test": [{"input": pair["input"]}]}
        for pair in public["test"]
    ]


def generate_claimed_episode(
    seed: int,
    move_distance: int,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    _validate_distance(move_distance)
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    train = [{"input": grid, "output": transform(grid, move_distance)} for grid in demo_grids]
    test = [{"input": grid, "output": transform(grid, move_distance)} for grid in query_grids]
    survivors = _settings_surviving(demo_grids, [pair["output"] for pair in train])
    if survivors != [{"move_distance": move_distance}]:
        raise ValueError(f"demonstrations do not identify move_distance: {survivors}")
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(move_distance, root=root),
    }


def generate_episode(
    seed: int,
    bridge,
    *,
    move_distance: int | None = None,
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative Python integer")
    validate_counts(demos, queries)
    selected = MOVE_DISTANCES[seed % 2] if move_distance is None else move_distance
    _validate_distance(selected)
    programs = {distance: program_for(distance, root=root) for distance in MOVE_DISTANCES}
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    all_grids = demo_grids + query_grids
    predictions = {
        distance: [execute(bridge, programs[distance], grid) for grid in all_grids]
        for distance in MOVE_DISTANCES
    }
    for distance in MOVE_DISTANCES:
        for grid, output in zip(all_grids, predictions[distance]):
            if output != transform(grid, distance):
                raise ValueError(f"Python/Racket disagreement for move_distance={distance}")
    selected_outputs = predictions[selected]
    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(demo_grids, selected_outputs[:demos])
        ],
        "test": [{"input": grid} for grid in query_grids],
    }
    rival_checks: dict[str, Any] = {}
    for distance in MOVE_DISTANCES:
        differing = [
            index
            for index in range(demos)
            if predictions[distance][index] != selected_outputs[index]
        ]
        rival_checks[str(distance)] = {
            "matches_all_demonstrations": not differing,
            "distinguishing_demo_indices": differing,
            "demonstration_predictions": predictions[distance][:demos],
            "query_predictions": predictions[distance][demos:],
        }
    survivors = [
        {"move_distance": distance}
        for distance in MOVE_DISTANCES
        if rival_checks[str(distance)]["matches_all_demonstrations"]
    ]
    if survivors != [{"move_distance": selected}]:
        raise ValueError(f"demonstrations do not identify move_distance: {survivors}")
    private = {
        "schema": "df0b5d094b2d-parametric-move-distance-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"move_distance": selected},
        "program_sha256": digest(programs[selected].encode("utf-8")),
        "query_answers": selected_outputs[demos:],
        "surviving_settings": survivors,
        "rival_checks": rival_checks,
        "demo_count": demos,
        "query_count": queries,
        "query_profiles": [input_profile(grid) for grid in query_grids],
        "size_limit": "exact 30x30 exercised by the four-query schedule",
        "public_id": public_challenge_id(public),
        "sequential_public_ids": [public_challenge_id(view) for view in sequential_views(public)],
    }
    verify_episode(public, private, root=root)
    return public, private


def verify_episode(public: dict[str, Any], private: dict[str, Any], *, root: Path | str = ROOT) -> None:
    del root
    validate_public(public)
    if type(private) is not dict:
        raise ValueError("private record must be a dictionary")
    try:
        distance = private["parameter"]["move_distance"]
        answers = private["query_answers"]
    except (KeyError, TypeError) as exc:
        raise ValueError("private record is missing parameter or query answers") from exc
    _validate_distance(distance)
    if type(answers) is not list or len(answers) != len(public["test"]):
        raise ValueError("query answer count does not match public queries")
    for index, pair in enumerate(public["train"]):
        if pair["output"] != transform(pair["input"], distance):
            raise ValueError(f"demonstration label {index} does not match selected rule")
    for index, (pair, answer) in enumerate(zip(public["test"], answers)):
        if answer != transform(pair["input"], distance):
            raise ValueError(f"query answer {index} does not match selected rule")
    survivors = _settings_surviving(
        [pair["input"] for pair in public["train"]],
        [pair["output"] for pair in public["train"]],
    )
    if survivors != [{"move_distance": distance}]:
        raise ValueError(f"demonstrations are underidentified: {survivors}")
    if private.get("public_id") not in (None, public_challenge_id(public)):
        raise ValueError("public identifier does not match visible bytes")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public(path: Path, public: dict[str, Any]) -> None:
    validate_public(public)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(public))


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    validate_counts(demos, queries)
    out = Path(out)
    root = Path(root)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory is not empty: {out}")
    for folder in ("public", "private", "rules", "sequential"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    programs = {distance: program_for(distance, root=root) for distance in MOVE_DISTANCES}
    for distance, program in programs.items():
        (out / "rules" / f"move-distance-{distance}.rkt").write_text(program, encoding="utf-8")

    from arc_repl.racket_bridge import RacketBridge

    episodes = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            public, private = generate_episode(seed, bridge, demos=demos, queries=queries, root=root)
            public_id = public_challenge_id(public)
            _write_public(out / "public" / f"{public_id}.json", public)
            _write_json(out / "private" / f"{public_id}.json", private)
            sequential_ids = []
            for view in sequential_views(public):
                view_id = public_challenge_id(view)
                _write_public(out / "sequential" / f"{view_id}.json", view)
                sequential_ids.append(view_id)
            episodes.append(
                {
                    "public_id": public_id,
                    "seed": seed,
                    "parameter": private["parameter"],
                    "demos": demos,
                    "queries": queries,
                    "sequential_public_ids": sequential_ids,
                }
            )

        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute(bridge, programs[DEFAULT_MOVE_DISTANCE], pair["input"])
            if actual != pair["output"]:
                raise ValueError("canonical default failed a labeled canonical pair")
            if actual != transform(pair["input"], DEFAULT_MOVE_DISTANCE):
                raise ValueError("Python mirror failed a labeled canonical pair")
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "output": actual,
                }
            )
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

        witness = sample_input(991, 3, size=(30, 30), shape_count=4, root=root)
        witness_outputs = {
            str(distance): execute(bridge, programs[distance], witness)
            for distance in MOVE_DISTANCES
        }
        if witness_outputs["1"] == witness_outputs["2"]:
            raise ValueError("shared witness failed to distinguish settings")
        _write_json(out / "private" / "shared-witness.json", {"input": witness, "outputs": witness_outputs})

    _, generator_source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    manifest = {
        "schema": "df0b5d094b2d-parametric-move-distance-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameters": {"move_distance": list(MOVE_DISTANCES)},
        "default": {"move_distance": DEFAULT_MOVE_DISTANCE},
        "limits": {"demos": list(DEMO_LIMITS), "queries": list(QUERY_LIMITS)},
        "materialized_request": {"demos": demos, "queries": queries},
        "episodes": episodes,
        "canonical_default_unchanged": programs[DEFAULT_MOVE_DISTANCE]
        == canonical_record(root=root)["program_solution"],
        "program_sha256": {
            str(distance): digest(program.encode("utf-8"))
            for distance, program in programs.items()
        },
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": digest(Path(__file__).read_bytes()),
        "racket_runtime": runtime_identity,
        "bounded_adversarial_pass": {
            "attempted": [
                "mutated one private query label",
                "inserted an output into a public query",
                "requested demo/query counts outside declared limits",
                "checked saved public files against canonical bytes and full-SHA filenames",
            ],
            "result": (
                "the saved-file check exposed pretty-JSON/canonical-byte drift; "
                "the writer now emits exact public_challenge_bytes and a regression "
                "pins it; the label, leak, and count attacks were rejected"
            ),
        },
        "limitations": [
            "prototype only; production remains pinned to one-cell movement",
            "finite evidence distinguishes only the two declared move distances",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        demos=args.demos,
        queries=args.queries,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
