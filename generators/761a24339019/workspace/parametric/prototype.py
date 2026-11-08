#!/usr/bin/env python3
"""Proposed, unapproved stamp-orientation episodes for ARC task 761a24339019.

The canonical/default setting is the exact selected Racket source.  The only
rule parameter rotates the exemplar offsets 90 degrees clockwise before they
are stamped at each target.  Inputs are drawn independently of that hidden
setting and are admitted only when both programs are total and distinguishable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "761a24339019"
VERSION = "proposed-stamp-transform-v1"
STATUS = "proposed_unapproved"
CANONICAL_SOURCE_SHA256 = "ea6f2120f432585364a8c280cd3d82d441424202f02509d808a6748f2329f93e"
CANONICAL_RULE_HASH = "ea6f2120f432"
TRANSFORMS = ("identity", "rotate_cw")
DEFAULT_SETTINGS = {"stamp_transform": "identity"}
SETTING_COMBINATIONS = tuple({"stamp_transform": name} for name in TRANSFORMS)
OFFSET_TOKEN = "(list (- (first p) (first anchor)) (- (second p) (second anchor)))"
ROTATED_OFFSET_TOKEN = "(list (- (second p) (second anchor)) (- (- (first p) (first anchor))))"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 8
DEFAULT_MAX_ATTEMPTS = 64

# Every motif is 4-connected, touches the anchor at (0, 0), and is not invariant
# under a 90-degree rotation.  The source exemplar itself is never transformed.
MOTIFS = (
    ((0, 1), (0, 2), (1, 1), (2, 1), (2, 2)),
    ((1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
    ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 2)),
    ((0, -1), (1, -1), (1, -2), (2, -2), (2, -3)),
    ((-2, 0), (-1, 0), (-1, 1), (0, 1), (0, 2)),
    ((0, 1), (1, 1), (1, 2), (1, 3), (2, 2), (2, 3)),
)
DEMO_SHAPES = ((10, 13), (12, 16), (15, 12), (16, 18), (11, 17), (18, 15))
QUERY_SHAPES = (
    (30, 30),
    (23, 27),
    (21, 24),
    (17, 22),
    (28, 18),
    (20, 30),
    (16, 25),
    (24, 19),
)
DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIRS8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))


def _sha256(payload: str | bytes) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hashlib.sha256(data).hexdigest()


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a literal list with 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid rows must be literal lists with 1..30 cells")
    width = len(grid[0])
    rows: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular with literal list rows")
        checked: list[int] = []
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("grid cells must be literal integer ARC colors 0..9")
            checked.append(cell)
        rows.append(checked)
    return rows


def grid_sha256(grid: Any) -> str:
    checked = _strict_grid(grid)
    return _sha256(json.dumps(checked, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def normalize_settings(settings: Any = None) -> dict[str, str]:
    if settings is None:
        return dict(DEFAULT_SETTINGS)
    if type(settings) is not dict or set(settings) != {"stamp_transform"}:
        raise ValueError("settings must be a literal dict containing exactly stamp_transform")
    value = settings["stamp_transform"]
    if type(value) is not str or value not in TRANSFORMS:
        raise ValueError("stamp_transform must be one of: " + ", ".join(TRANSFORMS))
    return {"stamp_transform": value}


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str:
        raise ValueError("canonical source must be Racket text")
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("canonical source must be exactly one rule! form")
    if source.count(OFFSET_TOKEN) != 1:
        raise ValueError("canonical source must contain exactly one offset constructor")
    if ROTATED_OFFSET_TOKEN in source:
        raise ValueError("canonical source unexpectedly contains rotated offsets")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    settings: Any = None,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    selected = normalize_settings(settings)
    result = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selected["stamp_transform"] == "rotate_cw":
        result = result.replace(OFFSET_TOKEN, ROTATED_OFFSET_TOKEN, 1)
    return result


def recognize_rule(source: Any, *, root: str | Path | None = None) -> dict[str, str]:
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    matches = [settings for settings in SETTING_COMBINATIONS if source == materialize_rule(settings, root=root)]
    if len(matches) != 1:
        raise ValueError("source is not a recognized stamp-transform rule")
    return dict(matches[0])


def _rule_body(source: str, *, root: str | Path | None = None) -> str:
    recognize_rule(source, root=root)
    return source[len("(rule! ") : -1]


def _grid_literal(grid: Any) -> str:
    checked = _strict_grid(grid)
    return "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in checked) + ")"


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    checked = [_strict_grid(grid) for grid in grids]
    if not checked:
        return []
    literals = [_grid_literal(grid) for grid in checked]
    expression = f"(map (lambda (g) {_rule_body(source, root=root)}) '({' '.join(literals)}))"
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            raw = owned.eval_text(expression)
    else:
        raw = bridge.eval_text(expression)
    if type(raw) is not list or len(raw) != len(checked):
        raise ValueError("Racket rule returned the wrong number of grids")
    return [_strict_grid(grid) for grid in raw]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def _nonzero_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            component = {(start_row, start_col)}
            seen.add((start_row, start_col))
            frontier = [(start_row, start_col)]
            while frontier:
                row, col = frontier.pop()
                for dr, dc in DIRS4:
                    neighbour = row + dr, col + dc
                    if (
                        0 <= neighbour[0] < height
                        and 0 <= neighbour[1] < width
                        and neighbour not in seen
                        and grid[neighbour[0]][neighbour[1]] != 0
                    ):
                        seen.add(neighbour)
                        component.add(neighbour)
                        frontier.append(neighbour)
            components.append(component)
    return components


def _parse_input(grid: Any) -> tuple[list[list[int]], tuple[int, int], tuple[tuple[int, int], ...], tuple[tuple[int, int], ...], set[tuple[int, int]]]:
    checked = _strict_grid(grid)
    if any(cell not in (0, 1, 3) for row in checked for cell in row):
        raise ValueError("stamp inputs may contain only colors 0, 1, and 3")
    components = _nonzero_components(checked)
    exemplars = [
        component
        for component in components
        if 1 in {checked[row][col] for row, col in component}
        and 3 in {checked[row][col] for row, col in component}
    ]
    if len(exemplars) != 1:
        raise ValueError(f"expected exactly one mixed color-1/3 exemplar, got {len(exemplars)}")
    exemplar = exemplars[0]
    anchors = sorted(cell for cell in exemplar if checked[cell[0]][cell[1]] == 1)
    if len(anchors) != 1:
        raise ValueError("exemplar must contain exactly one color-1 anchor")
    anchor = anchors[0]
    offsets = tuple(sorted(
        (row - anchor[0], col - anchor[1])
        for row, col in exemplar
        if checked[row][col] == 3
    ))
    if not offsets:
        raise ValueError("exemplar must contain color-3 motif cells")
    targets = tuple(sorted(
        (row, col)
        for row in range(len(checked))
        for col in range(len(checked[0]))
        if checked[row][col] == 1 and (row, col) != anchor
    ))
    if not targets:
        raise ValueError("input must contain at least one target marker")
    component_by_cell = {cell: component for component in components for cell in component}
    if any(len(component_by_cell[target]) != 1 for target in targets):
        raise ValueError("every target marker must be a singleton nonzero component")
    return checked, anchor, offsets, targets, exemplar


def _transform_offsets(
    offsets: Iterable[tuple[int, int]], settings: Any = None
) -> tuple[tuple[int, int], ...]:
    selected = normalize_settings(settings)
    if selected["stamp_transform"] == "identity":
        return tuple(offsets)
    return tuple((dc, -dr) for dr, dc in offsets)


def independent_output(grid: Any, settings: Any = None) -> list[list[int]]:
    checked, anchor, offsets, targets, _ = _parse_input(grid)
    del anchor
    transformed = _transform_offsets(offsets, settings)
    output = [row[:] for row in checked]
    height, width = len(output), len(output[0])
    for target_row, target_col in targets:
        for dr, dc in transformed:
            row, col = target_row + dr, target_col + dc
            if 0 <= row < height and 0 <= col < width and output[row][col] == 0:
                output[row][col] = 3
    return output


def input_certificate(grid: Any) -> dict[str, Any]:
    checked, anchor, offsets, targets, exemplar = _parse_input(grid)
    height, width = len(checked), len(checked[0])
    footprints: dict[str, list[set[tuple[int, int]]]] = {}
    complete = True
    for settings in SETTING_COMBINATIONS:
        name = settings["stamp_transform"]
        transformed = _transform_offsets(offsets, settings)
        setting_footprints: list[set[tuple[int, int]]] = []
        for target_row, target_col in targets:
            footprint = {(target_row + dr, target_col + dc) for dr, dc in transformed}
            if any(not (0 <= row < height and 0 <= col < width) for row, col in footprint):
                complete = False
            if any(
                0 <= row < height and 0 <= col < width and checked[row][col] != 0
                for row, col in footprint
            ):
                complete = False
            setting_footprints.append(footprint)
        for left in range(len(setting_footprints)):
            for right in range(left + 1, len(setting_footprints)):
                if setting_footprints[left] & setting_footprints[right]:
                    complete = False
        footprints[name] = setting_footprints

    output_hashes = {
        settings["stamp_transform"]: grid_sha256(independent_output(checked, settings))
        for settings in SETTING_COMBINATIONS
    }
    nonzero = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if checked[row][col] != 0
    }
    projected = set(nonzero)
    for setting_footprints in footprints.values():
        for footprint in setting_footprints:
            projected.update(cell for cell in footprint if 0 <= cell[0] < height and 0 <= cell[1] < width)
    rows = [row for row, _ in projected]
    cols = [col for _, col in projected]
    boundary_contact = any(row in (0, height - 1) or col in (0, width - 1) for row, col in projected)
    distractors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if checked[row][col] == 3 and (row, col) not in exemplar
    ]
    return {
        "height": height,
        "width": width,
        "anchor": list(anchor),
        "motif_offsets": [list(offset) for offset in offsets],
        "motif_cells": len(offsets),
        "target_count": len(targets),
        "targets": [list(target) for target in targets],
        "target_row_span": max(row for row, _ in targets) - min(row for row, _ in targets),
        "target_col_span": max(col for _, col in targets) - min(col for _, col in targets),
        "distractor_cells": len(distractors),
        "complete_for_all_settings": complete,
        "setting_outputs_distinct": len(set(output_hashes.values())) == len(SETTING_COMBINATIONS),
        "setting_output_sha256": output_hashes,
        "boundary_contact": boundary_contact,
        "content_bbox_height": max(rows) - min(rows) + 1,
        "content_bbox_width": max(cols) - min(cols) + 1,
    }


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_demos(value: Any) -> int:
    if type(value) is not int or not MIN_DEMOS <= value <= MAX_DEMOS:
        raise ValueError(f"demos must be a literal integer in {MIN_DEMOS}..{MAX_DEMOS}")
    return value


def _validate_queries(value: Any) -> int:
    if type(value) is not int or not MIN_QUERIES <= value <= MAX_QUERIES:
        raise ValueError(f"queries must be a literal integer in {MIN_QUERIES}..{MAX_QUERIES}")
    return value


def _validate_attempts(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 512:
        raise ValueError("max_attempts must be a literal integer in 1..512")
    return value


def parameter_for_seed(seed: Any) -> dict[str, str]:
    checked = _validate_seed(seed)
    return dict(SETTING_COMBINATIONS[checked % len(SETTING_COMBINATIONS)])


def _rng_for_input(seed: int, role: str, slot: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(f"{VERSION}:input:{seed}:{role}:{slot}:{attempt}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _edge_anchor(
    offsets: tuple[tuple[int, int], ...],
    height: int,
    width: int,
    profile: int,
) -> tuple[int, int]:
    rows = [0, *(dr for dr, _ in offsets)]
    cols = [0, *(dc for _, dc in offsets)]
    low_row, high_row = -min(rows), height - 1 - max(rows)
    low_col, high_col = -min(cols), width - 1 - max(cols)
    middle_row = (low_row + high_row) // 2
    middle_col = (low_col + high_col) // 2
    choices = (
        (low_row, middle_col),
        (middle_row, low_col),
        (middle_row, high_col),
        (high_row, middle_col),
    )
    return choices[profile % len(choices)]


def _candidate_targets(
    offsets: set[tuple[int, int]], height: int, width: int
) -> tuple[list[tuple[int, int]], tuple[int, int, int, int]]:
    rows = [0, *(dr for dr, _ in offsets)]
    cols = [0, *(dc for _, dc in offsets)]
    low_row, high_row = -min(rows), height - 1 - max(rows)
    low_col, high_col = -min(cols), width - 1 - max(cols)
    if low_row > high_row or low_col > high_col:
        raise RuntimeError("motif union does not fit target canvas")
    cells = [(row, col) for row in range(low_row, high_row + 1) for col in range(low_col, high_col + 1)]
    return cells, (low_row, high_row, low_col, high_col)


def _draw_input(seed: int, role: str, slot: int, attempt: int) -> list[list[int]]:
    rng = _rng_for_input(seed, role, slot, attempt)
    height, width = (QUERY_SHAPES if role == "query" else DEMO_SHAPES)[slot % (len(QUERY_SHAPES) if role == "query" else len(DEMO_SHAPES))]
    motif = tuple(MOTIFS[rng.randrange(len(MOTIFS))])
    grid = [[0 for _ in range(width)] for _ in range(height)]

    anchor = _edge_anchor(motif, height, width, seed + slot + attempt)
    source_cells = {anchor} | {(anchor[0] + dr, anchor[1] + dc) for dr, dc in motif}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in source_cells):
        raise RuntimeError("source exemplar escaped canvas")
    grid[anchor[0]][anchor[1]] = 1
    for dr, dc in motif:
        grid[anchor[0] + dr][anchor[1] + dc] = 3

    rotated = {(dc, -dr) for dr, dc in motif}
    union_offsets = set(motif) | rotated
    candidates, (low_row, high_row, low_col, high_col) = _candidate_targets(union_offsets, height, width)
    desired = [
        (low_row, low_col),
        (high_row, high_col),
        (low_row, high_col),
        (high_row, low_col),
    ]
    target_count = 4 if role == "query" else 2 + ((seed + slot) % 2)
    reserved: set[tuple[int, int]] = set()
    targets: list[tuple[int, int]] = []
    random_rank = {cell: rng.random() for cell in candidates}
    for goal in desired[:target_count]:
        ordered = sorted(
            candidates,
            key=lambda cell: (
                abs(cell[0] - goal[0]) + abs(cell[1] - goal[1]),
                random_rank[cell],
                cell,
            ),
        )
        selected = None
        for row, col in ordered:
            if grid[row][col] != 0:
                continue
            if any(
                0 <= row + dr < height
                and 0 <= col + dc < width
                and grid[row + dr][col + dc] != 0
                for dr, dc in DIRS8
            ):
                continue
            claimed = {(row, col)} | {(row + dr, col + dc) for dr, dc in union_offsets}
            if claimed & reserved:
                continue
            if any(grid[rr][cc] != 0 for rr, cc in claimed):
                continue
            selected = (row, col)
            reserved.update(claimed)
            break
        if selected is None:
            raise RuntimeError("could not place a complete cross-setting target")
        targets.append(selected)
        grid[selected[0]][selected[1]] = 1

    protected = set(reserved) | set(source_cells)
    for row, col in source_cells | set(targets):
        for dr, dc in DIRS4:
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width:
                protected.add((nr, nc))
    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in protected
    ]
    rng.shuffle(available)
    area = height * width
    distractor_count = min(len(available), max(4, min(42, area // (25 if role == "query" else 34))))
    if role == "query" and slot == 0:
        distractor_count = min(len(available), max(24, distractor_count))

    chosen: list[tuple[int, int]] = []
    quadrant_goals = (
        (height // 4, width // 4),
        (height // 4, 3 * width // 4),
        (3 * height // 4, width // 4),
        (3 * height // 4, 3 * width // 4),
    )
    remaining = set(available)
    for goal in quadrant_goals:
        if not remaining or len(chosen) >= distractor_count:
            break
        cell = min(remaining, key=lambda p: (abs(p[0] - goal[0]) + abs(p[1] - goal[1]), p))
        chosen.append(cell)
        remaining.remove(cell)
    rest = list(remaining)
    rng.shuffle(rest)
    chosen.extend(rest[: max(0, distractor_count - len(chosen))])
    for row, col in chosen:
        grid[row][col] = 3

    certificate = input_certificate(grid)
    if not certificate["complete_for_all_settings"]:
        raise RuntimeError("constructed input is not total for both settings")
    if not certificate["setting_outputs_distinct"]:
        raise RuntimeError("constructed input does not distinguish settings")
    if not certificate["boundary_contact"]:
        raise RuntimeError("constructed input lacks a boundary contact")
    if certificate["target_row_span"] < max(1, height // 3):
        raise RuntimeError("target rows are not sufficiently spread")
    if certificate["target_col_span"] < max(1, width // 3):
        raise RuntimeError("target columns are not sufficiently spread")
    return grid


def episode_inputs(
    seed: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    del root
    checked_seed = _validate_seed(seed)
    demo_count = _validate_demos(demos)
    query_count = _validate_queries(queries)
    attempt_limit = _validate_attempts(max_attempts)
    grids: list[list[list[int]]] = []
    seen: set[str] = set()
    slots = [("demo", slot) for slot in range(demo_count)] + [("query", slot) for slot in range(query_count)]
    for role, slot in slots:
        last_error: Exception | None = None
        for attempt in range(attempt_limit):
            try:
                grid = _draw_input(checked_seed, role, slot, attempt)
                fingerprint = grid_sha256(grid)
                if fingerprint in seen:
                    raise RuntimeError("duplicate input grid")
            except (ValueError, RuntimeError) as error:
                last_error = error
                continue
            grids.append(grid)
            seen.add(fingerprint)
            break
        else:
            raise RuntimeError(
                f"could not construct admitted {role} slot {slot} after {attempt_limit} attempts: {last_error}"
            )
    return grids


def _setting_key(settings: Any) -> str:
    return normalize_settings(settings)["stamp_transform"]


def _generate_episode_with_bridge(
    seed: int,
    selected: dict[str, str],
    demos: int,
    queries: int,
    max_attempts: int,
    bridge: RacketBridge,
    root: Path,
) -> dict[str, Any]:
    grids = episode_inputs(seed, demos=demos, queries=queries, max_attempts=max_attempts, root=root)
    programs = {_setting_key(settings): materialize_rule(settings, root=root) for settings in SETTING_COMBINATIONS}
    predictions: dict[str, list[list[list[int]]]] = {}
    for settings in SETTING_COMBINATIONS:
        key = _setting_key(settings)
        outputs = execute_rule_many(programs[key], grids, bridge=bridge, root=root)
        expected = [independent_output(grid, settings) for grid in grids]
        if outputs != expected:
            raise ValueError(f"Racket/Python disagreement for {key}")
        predictions[key] = outputs

    selected_key = _setting_key(selected)
    selected_outputs = predictions[selected_key]
    train = [
        {"input": copy.deepcopy(grids[index]), "output": copy.deepcopy(selected_outputs[index])}
        for index in range(demos)
    ]
    test = [
        {
            "input": copy.deepcopy(grids[demos + index]),
            "output": copy.deepcopy(selected_outputs[demos + index]),
        }
        for index in range(queries)
    ]

    survivor_keys: list[str] = []
    rival_checks: list[dict[str, Any]] = []
    for settings in SETTING_COMBINATIONS:
        key = _setting_key(settings)
        disagreements = [index for index in range(demos) if predictions[key][index] != selected_outputs[index]]
        if not disagreements:
            survivor_keys.append(key)
        rival_checks.append(
            {
                "settings": dict(settings),
                "matches_all_demonstrations": not disagreements,
                "demonstration_disagreements": disagreements,
            }
        )
    if survivor_keys != [selected_key]:
        raise RuntimeError(f"demonstrations do not identify selected setting: {survivor_keys}")

    query_identification: list[dict[str, Any]] = []
    for query_index in range(queries):
        absolute_index = demos + query_index
        eliminated = [
            dict(settings)
            for settings in SETTING_COMBINATIONS
            if _setting_key(settings) != selected_key
            and predictions[_setting_key(settings)][absolute_index] != selected_outputs[absolute_index]
        ]
        if len(eliminated) != len(SETTING_COMBINATIONS) - 1:
            raise RuntimeError(f"query {query_index} does not distinguish the selected setting")
        query_identification.append(
            {
                "query_index": query_index,
                "selected_setting": dict(selected),
                "eliminated_rivals_that_disagree": eliminated,
                "query_answer_used_for_demo_fit": False,
            }
        )

    return {
        "schema": "761a24339019-stamp-transform-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "settings": dict(selected),
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "train": train,
        "test": test,
        "program_solution": programs[selected_key],
        "program_sha256": _sha256(programs[selected_key]),
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "input_sha256": [grid_sha256(grid) for grid in grids],
        "input_certificates": [input_certificate(grid) for grid in grids],
        "surviving_settings_from_demonstrations": [dict(selected)],
        "rival_checks": rival_checks,
        "query_identification": query_identification,
        "declared_rule_sha256": {key: _sha256(source) for key, source in programs.items()},
        "racket_runtime": copy.deepcopy(bridge.runtime_identity),
    }


def generate_episode(
    seed: Any,
    *,
    settings: Any = None,
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    checked_seed = _validate_seed(seed)
    demo_count = _validate_demos(demos)
    query_count = _validate_queries(queries)
    attempt_limit = _validate_attempts(max_attempts)
    selected = parameter_for_seed(checked_seed) if settings is None else normalize_settings(settings)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _generate_episode_with_bridge(
                checked_seed, selected, demo_count, query_count, attempt_limit, owned, root_path
            )
    return _generate_episode_with_bridge(
        checked_seed, selected, demo_count, query_count, attempt_limit, bridge, root_path
    )


def public_payload(episode: Any) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dict")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return {
            "train": [
                {"input": _strict_grid(pair["input"]), "output": _strict_grid(pair["output"])}
                for pair in train
            ],
            "test": [{"input": _strict_grid(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs are incomplete") from error


def sequential_public_turn(episode: Any, query_index: Any = 0) -> dict[str, Any]:
    public = public_payload(episode)
    if type(query_index) is not int or not 0 <= query_index < len(public["test"]):
        raise ValueError("query_index must select an existing query")
    return {
        "train": copy.deepcopy(public["train"]),
        "test": [copy.deepcopy(public["test"][query_index])],
    }


def sequential_turn_bytes(episode: Any, query_index: Any = 0) -> bytes:
    return public_challenge_bytes(sequential_public_turn(episode, query_index))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _validated_seeds(seeds: Any) -> tuple[int, ...]:
    if isinstance(seeds, (str, bytes, bytearray, dict)):
        raise ValueError("seeds must be a finite iterable of literal integers")
    try:
        values = tuple(_validate_seed(seed) for seed in seeds)
    except TypeError as error:
        raise ValueError("seeds must be a finite iterable of literal integers") from error
    if not values:
        raise ValueError("seeds must contain at least one episode seed")
    if len(values) != len(set(values)):
        raise ValueError("episode seeds must be distinct")
    return values


def _file_record(base: Path, path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"path": path.relative_to(base).as_posix(), "bytes": len(payload), "sha256": _sha256(payload)}


def _write_evidence_with_bridge(
    out: Path,
    seeds: tuple[int, ...],
    demos: int,
    queries: int,
    max_attempts: int,
    bridge: RacketBridge,
    root: Path,
) -> dict[str, Any]:
    public_dir = out / "public"
    private_episode_dir = out / "private" / "episodes"
    private_rule_dir = out / "private" / "rules"
    public_dir.mkdir(parents=True)
    private_episode_dir.mkdir(parents=True)
    private_rule_dir.mkdir(parents=True)

    retained_paths: list[Path] = []
    rule_rows: list[dict[str, Any]] = []
    for settings in SETTING_COMBINATIONS:
        name = settings["stamp_transform"]
        source = materialize_rule(settings, root=root)
        path = private_rule_dir / f"{name}.rkt"
        path.write_text(source, encoding="utf-8")
        retained_paths.append(path)
        rule_rows.append(
            {
                "settings": dict(settings),
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256(source),
                "canonical_default": settings == DEFAULT_SETTINGS,
            }
        )
    if materialize_rule(DEFAULT_SETTINGS, root=root) != canonical_source(root=root):
        raise ValueError("default program is not byte-identical to canonical authority")

    public_ids: set[str] = set()
    episode_rows: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    settings_exercised: set[str] = set()
    for seed in seeds:
        episode = generate_episode(
            seed,
            demos=demos,
            queries=queries,
            max_attempts=max_attempts,
            bridge=bridge,
            root=root,
        )
        public = public_payload(episode)
        public_id = public_challenge_id(public)
        if public_id in public_ids:
            raise ValueError("different seeds produced the same visible public challenge")
        public_ids.add(public_id)
        public_path = public_dir / f"challenge-{public_id}.json"
        public_path.write_bytes(public_challenge_bytes(public))
        retained_paths.append(public_path)

        private = copy.deepcopy(episode)
        private["public_id"] = public_id
        private["public_path"] = public_path.relative_to(out).as_posix()
        private["query_answers"] = [copy.deepcopy(pair["output"]) for pair in private["test"]]
        private_path = private_episode_dir / f"{public_id}.json"
        _write_json(private_path, private)
        retained_paths.append(private_path)

        distinct_inputs.update(private["input_sha256"])
        settings_exercised.add(private["settings"]["stamp_transform"])
        episode_rows.append(
            {
                "public_id": public_id,
                "public_path": public_path.relative_to(out).as_posix(),
                "private_path": private_path.relative_to(out).as_posix(),
                "seed": seed,
                "settings": copy.deepcopy(private["settings"]),
                "program_sha256": private["program_sha256"],
            }
        )

    episode_rows.sort(key=lambda row: row["public_id"])
    manifest: dict[str, Any] = {
        "schema": "761a24339019-stamp-transform-evidence-v1",
        "status": STATUS,
        "approved": False,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "stamp_transform": {"allowed": list(TRANSFORMS), "default": DEFAULT_SETTINGS["stamp_transform"]},
            "fixed_once_per_episode": True,
            "input_constraints_depend_on_settings": False,
        },
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_default_unchanged": True,
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "rules": rule_rows,
        "episodes": episode_rows,
        "counts": {
            "episodes": len(episode_rows),
            "train_pairs": demos * len(episode_rows),
            "query_pairs": queries * len(episode_rows),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(settings_exercised),
        },
        "racket_runtime": copy.deepcopy(bridge.runtime_identity),
        "files": sorted((_file_record(out, path) for path in retained_paths), key=lambda row: row["path"]),
        "manifest_hash_scope": "all retained public/private data files; manifest.json excludes itself",
        "limitations": [
            "Task-local proposed prototype only; no production, approval, or training-admission change.",
            "The finite identity/rotate-cw family does not claim completeness over other stamp transformations.",
            "Finite seed evidence demonstrates bounded behavior, not all procedural seeds.",
            "Public challenges omit seeds, settings, program text, runtime metadata, and query answers.",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def write_evidence(
    out: str | Path,
    *,
    seeds: Any = (0, 1),
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    seed_values = _validated_seeds(seeds)
    demo_count = _validate_demos(demos)
    query_count = _validate_queries(queries)
    attempt_limit = _validate_attempts(max_attempts)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    out_path.mkdir(parents=True, exist_ok=False)
    try:
        if bridge is None:
            with RacketBridge(max_calls_before_restart=128) as owned:
                return _write_evidence_with_bridge(
                    out_path, seed_values, demo_count, query_count, attempt_limit, owned, root_path
                )
        return _write_evidence_with_bridge(
            out_path, seed_values, demo_count, query_count, attempt_limit, bridge, root_path
        )
    except BaseException:
        shutil.rmtree(out_path, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=tuple(args.seeds),
        demos=args.demos,
        queries=args.queries,
        max_attempts=args.max_attempts,
    )
    print(json.dumps({"status": manifest["status"], "out": str(args.out), **manifest["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
