#!/usr/bin/env python3
"""Unapproved episode-level sort-key family for ARC task 8bc2bc6a9bb8."""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)

TASK_ID = "8bc2bc6a9bb8"
ALLOWED_SORT_KEYS = ("occupied_area", "bbox_area")
DEFAULT_SORT_KEY = "occupied_area"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))

_CANONICAL_COMPARATOR = (
    "(lambda (a b) (or (> (obj-size a) (obj-size b)) "
    "(and (= (obj-size a) (obj-size b)) "
    "(e8b-list< (obj-bbox a) (obj-bbox b)))))"
)
_BBOX_COMPARATOR = (
    "(lambda (a b) (or (> (e8b-footprint a) (e8b-footprint b)) "
    "(and (= (e8b-footprint a) (e8b-footprint b)) "
    "(or (> (obj-size a) (obj-size b)) "
    "(and (= (obj-size a) (obj-size b)) "
    "(e8b-list< (obj-bbox a) (obj-bbox b)))))))"
)
_FOOTPRINT_HELPER = (
    "(define (e8b-footprint obj) "
    "(let ((bb (obj-bbox obj))) "
    "(* (+ 1 (- (third bb) (first bb))) "
    "(+ 1 (- (fourth bb) (second bb)))))) "
)


def _validate_sort_key(sort_key: str) -> None:
    if type(sort_key) is not str or sort_key not in ALLOWED_SORT_KEYS:
        raise ValueError(f"sort_key must be one of {ALLOWED_SORT_KEYS}, got {sort_key!r}")


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 8:
        raise ValueError("queries must be an exact integer in 1..8")


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the one exact canonical program for the selected task."""
    matches: list[dict[str, Any]] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, found {len(matches)}")
    source = matches[0].get("program_solution")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"canonical record for {TASK_ID} has no program_solution")
    return source


def program_for(sort_key: str = DEFAULT_SORT_KEY, *, root: Path = ROOT) -> str:
    """Materialize exact Racket for one episode-fixed ranking measure."""
    _validate_sort_key(sort_key)
    source = canonical_source(root=root)
    if sort_key == DEFAULT_SORT_KEY:
        return source
    helper_anchor = "(define (t10-norm-cells cells)"
    if source.count(helper_anchor) != 1 or source.count(_CANONICAL_COMPARATOR) != 1:
        raise ValueError("canonical source no longer matches the guarded sort-key template")
    return source.replace(
        helper_anchor,
        _FOOTPRINT_HELPER + helper_anchor,
        1,
    ).replace(_CANONICAL_COMPARATOR, _BBOX_COMPARATOR, 1)


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute a complete rule through the protected Racket bridge."""
    owns_bridge = bridge is None
    active = RacketBridge(max_calls_before_restart=128) if owns_bridge else bridge
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns_bridge:
            active.shutdown()


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(2, height):
        for col in range(width):
            if grid[row][col] != 8 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _ORTHOGONALS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        2 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            r1 = max(r for r, _ in cells)
            c1 = max(c for _, c in cells)
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "normalized": tuple(sorted((r - r0, c - c0) for r, c in cells)),
                    "size": len(cells),
                    "bbox": (r0, c0, r1, c1),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "footprint": (r1 - r0 + 1) * (c1 - c0 + 1),
                }
            )
    return sorted(result, key=lambda obj: obj["bbox"])


def validate_input(grid) -> list[str]:
    """Validate the broader proposed-family input surface."""
    errors: list[str] = []
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    if not 7 <= height <= 30:
        errors.append(f"grid height {height} outside 7..30")
    if not 10 <= width <= 30:
        errors.append(f"grid width {width} outside 10..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be exact integer ARC colors 0..9")

    palette_cols = [col for col, value in enumerate(grid[0]) if value != 0]
    palette = [grid[0][col] for col in palette_cols]
    if not 2 <= len(palette) <= 4:
        errors.append(f"palette must contain 2..4 colors, found {len(palette)}")
    if len(set(palette)) != len(palette) or any(value == 8 for value in palette):
        errors.append("palette colors must be distinct, nonzero, and not placeholder 8")
    if any(b - a < 2 for a, b in zip(palette_cols, palette_cols[1:])):
        errors.append("palette entries must have a zero column between them")
    if height > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be blank")
    if any(grid[r][c] not in (0, 8) for r in range(2, height) for c in range(width)):
        errors.append("body may contain only background 0 and placeholder 8")

    components = _components(grid) if not errors else []
    if len(components) != len(palette):
        errors.append(
            f"component count {len(components)} must equal palette count {len(palette)}"
        )
    sizes = [obj["size"] for obj in components]
    if len(set(sizes)) != len(sizes):
        errors.append("component occupied areas must be distinct")
    if components and 1 not in sizes:
        errors.append("inventory must contain a singleton")
    for index, left in enumerate(components):
        for right in components[index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left["cells"]
                for r2, c2 in right["cells"]
            ):
                errors.append("components must have a one-cell separation moat")
                break
    if components:
        by_area = [obj["size"] for obj in sorted(components, key=lambda obj: (-obj["size"], obj["bbox"]))]
        by_footprint = [
            obj["size"]
            for obj in sorted(
                components,
                key=lambda obj: (-obj["footprint"], -obj["size"], obj["bbox"]),
            )
        ]
        if by_area == by_footprint:
            errors.append("inventory must reverse occupied-area and bbox-area order")
    return errors


def python_apply(grid, *, sort_key: str = DEFAULT_SORT_KEY):
    """Independent diagnostic implementation; Racket remains label authority."""
    _validate_sort_key(sort_key)
    errors = validate_input(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette = [value for value in grid[0] if value != 0]
    components = _components(grid)
    if sort_key == "occupied_area":
        components.sort(key=lambda obj: (-obj["size"], obj["bbox"]))
    else:
        components.sort(
            key=lambda obj: (-obj["footprint"], -obj["size"], obj["bbox"])
        )
    max_height = max(obj["height"] for obj in components)
    total_width = sum(obj["width"] for obj in components) + len(components) - 1
    output = [[0] * total_width for _ in range(max_height)]
    x = 0
    for obj, color in zip(components, palette):
        top = max_height - obj["height"]
        for dr, dc in obj["normalized"]:
            output[top + dr][x + dc] = color
        x += obj["width"] + 1
    return output


def grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def normalized_program_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()


def select_setting(seed: int) -> str:
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}:sort-key:{seed}".encode()).digest()
    return ALLOWED_SORT_KEYS[digest[0] % len(ALLOWED_SORT_KEYS)]


def _line(length: int) -> tuple[tuple[int, int], ...]:
    return tuple((0, col) for col in range(length))


def _l_shape(height: int, width: int, target_size: int) -> tuple[tuple[int, int], ...]:
    cells = [(row, 0) for row in range(height)]
    for col in range(1, width):
        cells.append((height - 1, col))
    extras_needed = target_size - len(cells)
    for row in range(height - 2, -1, -1):
        if extras_needed <= 0:
            break
        cells.append((row, width - 1))
        extras_needed -= 1
    if extras_needed != 0:
        raise ValueError("shape specification cannot realize requested area")
    return tuple(sorted(cells))


def _profile_specs() -> tuple[dict[str, Any], ...]:
    return (
        {
            "dims": (10, 12),
            "shapes": (_line(5), _l_shape(3, 2, 4), ((0, 0),)),
            "anchors": ((2, 0), (4, 9), (8, 4)),
        },
        {
            "dims": (12, 16),
            "shapes": (_line(7), _l_shape(4, 3, 6), ((0, 0), (0, 1)), ((0, 0),)),
            "anchors": ((2, 0), (4, 13), (10, 5), (10, 11)),
        },
        {
            "dims": (14, 18),
            "shapes": (_line(8), _l_shape(4, 3, 7), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0),)),
            "anchors": ((2, 10), (5, 0), (11, 7), (11, 15)),
        },
        {
            "dims": (16, 20),
            "shapes": (_line(9), _l_shape(4, 4, 8), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0),)),
            "anchors": ((2, 0), (5, 16), (13, 2), (13, 12)),
        },
        {
            "dims": (20, 24),
            "shapes": (_line(10), _l_shape(5, 4, 9), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0),)),
            "anchors": ((2, 14), (5, 0), (16, 7), (17, 20)),
        },
        {
            "dims": (24, 28),
            "shapes": (_line(12), _l_shape(6, 4, 11), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0),)),
            "anchors": ((2, 0), (6, 24), (20, 5), (21, 18)),
        },
        {
            "dims": (30, 30),
            "shapes": (_line(15), _l_shape(7, 5, 14), ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 0),)),
            "anchors": ((29, 10), (2, 0), (15, 28), (23, 18)),
        },
    )


def _transform_body_cell(row: int, col: int, height: int, width: int, mode: int):
    if mode & 1:
        col = width - 1 - col
    if mode & 2:
        row = height + 1 - row
    return row, col


def _palette(rng: random.Random, width: int, count: int) -> tuple[list[int], list[int]]:
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    rng.shuffle(colors)
    chosen = colors[:count]
    starts = list(range(0, width - 2 * count + 2))
    offset = rng.choice(starts) if starts else 0
    columns = [offset + 2 * index for index in range(count)]
    if columns[-1] >= width:
        columns = list(range(0, 2 * count, 2))
    return chosen, columns


def _make_profile_input(seed: int, ordinal: int, profile_index: int) -> list[list[int]]:
    specs = _profile_specs()
    spec = specs[profile_index]
    height, width = spec["dims"]
    digest = hashlib.sha256(
        f"{TASK_ID}:profile:{seed}:{ordinal}:{profile_index}".encode()
    ).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    grid = [[0] * width for _ in range(height)]
    colors, columns = _palette(rng, width, len(spec["shapes"]))
    for color, column in zip(colors, columns):
        grid[0][column] = color
    mode = digest[8] % 4
    for shape, (r0, c0) in zip(spec["shapes"], spec["anchors"]):
        for dr, dc in shape:
            row, col = _transform_body_cell(r0 + dr, c0 + dc, height, width, mode)
            grid[row][col] = 8
    errors = validate_input(grid)
    if errors:
        raise AssertionError(f"invalid curated profile {profile_index}: {errors}")
    return grid


_QUERY_PROFILE_ORDER = (3, 4, 5, 6, 3, 4, 5, 6)


def _query_profile_index(index: int, _count: int) -> int:
    return _QUERY_PROFILE_ORDER[index]


def _sample_inputs(seed: int, demos: int, queries: int) -> list[list[list[int]]]:
    inputs: list[list[list[int]]] = []
    for index in range(demos):
        inputs.append(_make_profile_input(seed, index, index % 3))
    for index in range(queries):
        ordinal = demos + index
        inputs.append(_make_profile_input(seed, ordinal, _query_profile_index(index, queries)))
    hashes = [grid_sha256(grid) for grid in inputs]
    if len(set(hashes)) != len(hashes):
        raise AssertionError("curated sampler emitted duplicate inputs")
    return inputs


def make_episode(
    seed: int,
    *,
    sort_key: str | None = None,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one private episode and derive every label in matching Racket."""
    _validate_seed(seed)
    _validate_counts(demos, queries)
    selected = select_setting(seed) if sort_key is None else sort_key
    _validate_sort_key(selected)
    rival = next(value for value in ALLOWED_SORT_KEYS if value != selected)
    inputs = _sample_inputs(seed, demos, queries)
    programs = {setting: program_for(setting, root=root) for setting in ALLOWED_SORT_KEYS}
    outputs: dict[str, list[list[list[int]]]] = {setting: [] for setting in ALLOWED_SORT_KEYS}

    owns_bridge = bridge is None
    active = RacketBridge(max_calls_before_restart=128) if owns_bridge else bridge
    try:
        for grid in inputs:
            for setting in ALLOWED_SORT_KEYS:
                actual = execute_rule(programs[setting], grid, bridge=active)
                expected = python_apply(grid, sort_key=setting)
                if actual != expected:
                    raise AssertionError(f"Racket/Python parity failed for {setting}")
                outputs[setting].append(actual)
    finally:
        if owns_bridge:
            active.shutdown()

    pairs = [
        {"input": grid, "output": outputs[selected][index]}
        for index, grid in enumerate(inputs)
    ]
    demo_mismatches = [
        index for index in range(demos) if outputs[selected][index] != outputs[rival][index]
    ]
    query_mismatches = [
        index
        for index in range(queries)
        if outputs[selected][demos + index] != outputs[rival][demos + index]
    ]
    status = "refuted_by_demonstrations" if demo_mismatches else "ambiguous_queries"
    program = programs[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"sort_key": selected},
        "seed": seed,
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program": program,
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_program_sha256": normalized_program_sha256(program),
        "input_sha256": [grid_sha256(grid) for grid in inputs],
        "parameter_rivals": [
            {
                "sort_key": rival,
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        ],
        "ambiguities": [] if demo_mismatches else [rival],
    }



def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return canonical bytes containing only visible demonstrations and queries."""
    return _public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    """Return the SHA-256 of exactly the visible public bytes."""
    return _public_challenge_id(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return a detached public challenge with all query answers removed."""
    return json.loads(public_bytes(episode))


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project one query turn without exposing total-count or final-turn hints."""
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index must identify an existing exact-integer query")
    projected = {
        "train": episode["train"],
        "test": [episode["test"][query_index]],
    }
    return json.loads(_public_challenge_bytes(projected))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _difference_coordinates(left, right) -> list[list[int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return []
    return [
        [row, col]
        for row, (a, b) in enumerate(zip(left, right))
        for col, (av, bv) in enumerate(zip(a, b))
        if av != bv
    ]


def write_evidence(
    *,
    seed: int,
    out: str | Path,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Atomically write Racket-backed public/private evidence for both settings."""
    _validate_seed(seed)
    _validate_counts(demos, queries)
    root = Path(root).resolve()
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))

    try:
        context = nullcontext(bridge) if bridge is not None else RacketBridge(
            max_calls_before_restart=128
        )
        with context as active_bridge:
            canonical_program = program_for(DEFAULT_SORT_KEY, root=root)
            canonical_rows = []
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical_program, pair["input"], bridge=active_bridge)
                row = {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                    "matches": actual == pair["output"],
                }
                canonical_rows.append(row)
            if not canonical_rows or not all(row["matches"] for row in canonical_rows):
                raise AssertionError("canonical occupied-area program failed a labeled pair")

            episodes = []
            private_episodes: dict[str, dict[str, Any]] = {}
            distinct_inputs: set[str] = set()
            for setting in ALLOWED_SORT_KEYS:
                episode = make_episode(
                    seed,
                    sort_key=setting,
                    demos=demos,
                    queries=queries,
                    root=root,
                    bridge=active_bridge,
                )
                rule_rel = Path("private/rules") / f"sort-{setting}.rkt"
                private_rel = Path("private") / f"episode-{setting}.json"
                rule_path = temp / rule_rel
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(episode["program"], encoding="utf-8")

                private = dict(episode)
                private["racket_path"] = rule_rel.as_posix()
                private["racket_sha256"] = _file_sha256(rule_path)
                _write_json(temp / private_rel, private)
                private_episodes[setting] = private

                visible_id = public_id(private)
                public_rel = Path("public") / f"challenge-{visible_id}.json"
                public_path = temp / public_rel
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(public_bytes(private))

                for pair in private["train"] + private["test"]:
                    distinct_inputs.add(grid_sha256(pair["input"]))
                rival = private["parameter_rivals"][0]
                episodes.append(
                    {
                        "sort_key": setting,
                        "seed": seed,
                        "train_count": len(private["train"]),
                        "query_count": len(private["test"]),
                        "private_path": private_rel.as_posix(),
                        "private_sha256": _file_sha256(temp / private_rel),
                        "public_path": public_rel.as_posix(),
                        "public_sha256": _file_sha256(public_path),
                        "public_id": visible_id,
                        "racket_path": rule_rel.as_posix(),
                        "racket_sha256": _file_sha256(rule_path),
                        "normalized_racket_sha256": private[
                            "normalized_program_sha256"
                        ],
                        "rival_status": rival["status"],
                        "rival_demonstration_mismatch_indices": rival[
                            "demonstration_mismatch_indices"
                        ],
                        "rival_query_mismatch_indices": rival[
                            "query_mismatch_indices"
                        ],
                    }
                )

            area_inputs = [
                pair["input"]
                for pair in private_episodes["occupied_area"]["train"]
                + private_episodes["occupied_area"]["test"]
            ]
            bbox_inputs = [
                pair["input"]
                for pair in private_episodes["bbox_area"]["train"]
                + private_episodes["bbox_area"]["test"]
            ]
            if area_inputs != bbox_inputs:
                raise AssertionError("sort setting changed the episode input draws")
            witness_input = area_inputs[0]
            witness_outputs = {
                setting: execute_rule(
                    program_for(setting, root=root), witness_input, bridge=active_bridge
                )
                for setting in ALLOWED_SORT_KEYS
            }

        witness = {
            "schema": "arcpuzzles-parametric-setting-witness-v1",
            "task_id": TASK_ID,
            "parameter": "sort_key",
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                setting: grid_sha256(output)
                for setting, output in witness_outputs.items()
            },
            "difference_coordinates": _difference_coordinates(
                witness_outputs["occupied_area"], witness_outputs["bbox_area"]
            ),
        }
        if not witness["difference_coordinates"]:
            raise AssertionError("retained witness does not separate sort settings")
        _write_json(temp / "setting-difference-witness.json", witness)
        _write_json(temp / "canonical-default-check.json", canonical_rows)

        prototype_path = Path(__file__).resolve()
        generator_path = root / "generators" / TASK_ID / "generator.py"
        test_path = root / "generators" / TASK_ID / "tests" / "test_parametric_sort_key.py"
        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "status": "proposed_unapproved",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "parameter": {
                "name": "sort_key",
                "allowed_values": list(ALLOWED_SORT_KEYS),
                "original_default": DEFAULT_SORT_KEY,
                "selection_scope": "once_per_episode",
                "input_constraints_depend_on_parameter": False,
            },
            "reasoning_invariants": [
                "read the sparse top-row palette from left to right",
                "extract and normalize all color-8 body components",
                "rank every component by one episode-fixed geometric measure",
                "recolor ranked components in palette order",
                "bottom-align and pack with one blank column between objects",
            ],
            "episodes": episodes,
            "sources": {
                "canonical_ledger": {
                    "path": canonical_path(root).relative_to(root).as_posix(),
                    "sha256": _file_sha256(canonical_path(root)),
                },
                "generator": {
                    "path": generator_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(generator_path),
                },
                "prototype": {
                    "path": prototype_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(prototype_path),
                },
                "focused_test": {
                    "path": test_path.relative_to(root).as_posix(),
                    "sha256": _file_sha256(test_path),
                },
            },
            "canonical_default": {
                "program_sha256": hashlib.sha256(canonical_program.encode()).hexdigest(),
                "normalized_program_sha256": normalized_program_sha256(
                    canonical_program
                ),
                "pairs": canonical_rows,
                "all_match": all(row["matches"] for row in canonical_rows),
            },
            "witness_path": "setting-difference-witness.json",
            "counts": {
                "episodes": len(episodes),
                "train_pairs": sum(row["train_count"] for row in episodes),
                "query_pairs": sum(row["query_count"] for row in episodes),
                "distinct_input_grids": len(distinct_inputs),
                "settings_exercised": len(episodes),
                "canonical_pairs_checked": len(canonical_rows),
                "ambiguous_parameter_rivals": sum(
                    row["rival_status"] != "refuted_by_demonstrations"
                    for row in episodes
                ),
                "racket_rule_applications": 2 * (demos + queries) * 2
                + len(canonical_rows)
                + 2,
            },
            "limits": {
                "demos": [2, 6],
                "queries": [1, 8],
                "max_grid": [30, 30],
            },
            "limitations": [
                "identifiability is checked only against the declared opposite sort key",
                "finite demonstrations do not prove unique induction against every program",
                "the prototype remains separate from canonical generation and approval",
            ],
        }
        _write_json(temp / "report.json", report)

        files = []
        for candidate in sorted(temp.rglob("*")):
            if candidate.is_file():
                files.append(
                    {
                        "path": candidate.relative_to(temp).as_posix(),
                        "bytes": candidate.stat().st_size,
                        "sha256": _file_sha256(candidate),
                    }
                )
        manifest = {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "status": "proposed_unapproved",
            "files": files,
        }
        _write_json(temp / "manifest.json", manifest)
        temp.rename(out)
        return report
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main(argv: list[str] | None = None, *, bridge: RacketBridge | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Materialize and Racket-verify both sort-key settings."
    )
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(
        seed=args.seed,
        out=args.out,
        demos=args.demos,
        queries=args.queries,
        bridge=bridge,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": report["task_id"],
                "out": str(args.out),
                "counts": report["counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
