#!/usr/bin/env python3
"""Proposed episode-local ring-spacing and corner-set variants.

The production generator and canonical authority are not changed. Every label is
executed by the bundled protected Racket bridge; the Python transform is only an
independent authoring cross-check.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "5a01897eb8be"
VERSION = "proposed-ring-step-corners-v1"
RING_STEPS = (2, 4)
CORNER_PATTERNS = ("all", "diagonal")
SETTINGS = tuple((ring_step, corners) for ring_step in RING_STEPS for corners in CORNER_PATTERNS)
DEFAULT_RING_STEP = 2
DEFAULT_CORNERS = "all"
_TOOL_STAGE = None
_TOOL_STAGE_ROOT: Path | None = None
_SELECTED_GENERATORS: dict[str, tuple[Any, str]] = {}
_CANONICAL_RECORDS: dict[str, tuple[dict[str, Any], Path]] = {}
_RULE_SOURCES: dict[tuple[str, int, str], str] = {}
_WRAPPED_RULES: dict[str, str] = {}

_CANONICAL_RING_BLOCK = """(define out-size (if has-center (- (* 2 n) 1) (+ (* 2 n) 1)))
     (define ring-sizes
       (map (lambda (i) (+ (if has-center 1 3) (* 2 i))) (range 0 n)))"""
_WIDE_RING_BLOCK = """(define out-size (+ (if has-center 1 3) (* 4 (- n 1))))
     (define ring-sizes
       (map (lambda (i) (+ (if has-center 1 3) (* 4 i))) (range 0 n)))"""
_CANONICAL_L_CELLS = """(define (l-cells arm size)  ;; 4 corner Ls of a size x size ring
       (let ((tl (append (map (lambda (i) (list 0 i)) (range 0 arm))
                         (map (lambda (i) (list i 0)) (range 0 arm)))))
         (append tl
                 (map (lambda (p) (list (first p)
                                        (- (- size 1) (second p))))
                      tl)
                 (map (lambda (p) (list (- (- size 1) (first p))
                                        (second p)))
                      tl)
                 (map (lambda (p) (list (- (- size 1) (first p))
                                        (- (- size 1) (second p))))
                      tl))))"""
_DIAGONAL_L_CELLS = """(define (l-cells arm size)  ;; top-left and bottom-right corner Ls
       (let ((tl (append (map (lambda (i) (list 0 i)) (range 0 arm))
                         (map (lambda (i) (list i 0)) (range 0 arm)))))
         (append tl
                 (map (lambda (p) (list (- (- size 1) (first p))
                                        (- (- size 1) (second p))))
                      tl))))"""


def _sha_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _sha_text(text: str) -> str:
    return _sha_bytes(text.encode("utf-8"))


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha_text(json.dumps(grid, separators=(",", ":"), ensure_ascii=False))


def _grid_copy(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must contain 1..30 rows")
    if any(type(row) is not list or not 1 <= len(row) <= 30 for row in grid):
        raise ValueError("grid rows must contain 1..30 cells")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9, excluding booleans")
    return [row[:] for row in grid]


def _canonical_record(*, root=None) -> tuple[dict[str, Any], Path]:
    resolved = find_root(__file__) if root is None else Path(root).resolve()
    key = str(resolved)
    if key in _CANONICAL_RECORDS:
        return _CANONICAL_RECORDS[key]
    ledger = canonical_path(resolved)
    records = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            records.append(record)
    if not records:
        raise RuntimeError(f"no canonical record found for {TASK_ID}")
    authorities = {record["program_solution"] for record in records}
    if len(authorities) != 1:
        raise RuntimeError(
            f"canonical variants for {TASK_ID} disagree on program_solution"
        )
    result = (records[0], ledger)
    _CANONICAL_RECORDS[key] = result
    return result


def _validate_setting(ring_step: int, corners: str) -> None:
    if type(ring_step) is not int:
        raise TypeError("ring_step must be an integer")
    if ring_step not in RING_STEPS:
        raise ValueError(f"ring_step must be one of {RING_STEPS}")
    if type(corners) is not str:
        raise TypeError("corners must be a string")
    if corners not in CORNER_PATTERNS:
        raise ValueError(f"corners must be one of {CORNER_PATTERNS}")


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"canonical rule has {count} {label} blocks; expected exactly one")
    return source.replace(old, new, 1)


def materialize_rule(
    ring_step: int = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
    *,
    root=None,
) -> str:
    """Return one exact declared rule; the default is byte-identical canonical text."""
    _validate_setting(ring_step, corners)
    resolved = find_root(__file__) if root is None else Path(root).resolve()
    cache_key = (str(resolved), ring_step, corners)
    if cache_key in _RULE_SOURCES:
        return _RULE_SOURCES[cache_key]
    record, _ = _canonical_record(root=resolved)
    source = record["program_solution"]
    if ring_step == 4:
        source = _replace_once(source, _CANONICAL_RING_BLOCK, _WIDE_RING_BLOCK, "ring schedule")
    if corners == "diagonal":
        source = _replace_once(source, _CANONICAL_L_CELLS, _DIAGONAL_L_CELLS, "corner renderer")
    _RULE_SOURCES[cache_key] = source
    return source


def _grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _ensure_rule_tools(*, root=None) -> None:
    """Stage the official portable parser when this review packet omits scripts/."""
    global _TOOL_STAGE, _TOOL_STAGE_ROOT
    resolved = find_root(__file__) if root is None else Path(root).resolve()
    try:
        available = importlib.util.find_spec("scripts.comment_solutions") is not None
    except ModuleNotFoundError:
        available = False
    if available:
        return
    if _TOOL_STAGE is not None and _TOOL_STAGE_ROOT != resolved:
        raise RuntimeError("rule tools were already staged for a different repository root")
    if _TOOL_STAGE is None:
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.runtime import prepare_runtime

        _TOOL_STAGE = tempfile.TemporaryDirectory(prefix="corner-rings-parametric-runtime-")
        prepare_runtime(Catalog(resolved), Path(_TOOL_STAGE.name), TASK_ID)
        # Append only: local puzzle_generators must keep repository precedence;
        # the staged directory supplies the otherwise-missing scripts package.
        sys.path.append(_TOOL_STAGE.name)
        _TOOL_STAGE_ROOT = resolved


def execute_rule(source: str, grid: Any, *, bridge=None, root=None) -> list[list[int]]:
    """Execute a declared exact Racket rule through the production wrapper."""
    normalized = _grid_copy(grid)
    declared = {materialize_rule(*setting, root=root) for setting in SETTINGS}
    if source not in declared:
        raise ValueError("source is not one of the four declared Racket programs")
    _ensure_rule_tools(root=root)
    from puzzle_generators.rule_wrap import wrap_rule

    if source not in _WRAPPED_RULES:
        _WRAPPED_RULES[source] = wrap_rule(source)
    expression = f"({_WRAPPED_RULES[source]} {_grid_literal(normalized)})"
    if bridge is None:
        with RacketBridge() as owned:
            return execute_rule(source, normalized, bridge=owned, root=root)
    return _grid_copy(bridge.eval_text(expression))


def _count_extent(
    grid: list[list[int]], color: int, row: int, col: int, dr: int, dc: int
) -> int:
    height, width = len(grid), len(grid[0])
    length = 0
    while 0 <= row < height and 0 <= col < width and grid[row][col] == color:
        length += 1
        row += dr
        col += dc
    return length


def _color_info(grid: list[list[int]], color: int) -> dict[str, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    max_dim = max(max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)
    arm = 0
    for row, col in cells:
        for dr in (-1, 1):
            for dc in (-1, 1):
                arm = max(
                    arm,
                    min(
                        _count_extent(grid, color, row, col, 0, dc),
                        _count_extent(grid, color, row, col, dr, 0),
                    ),
                )
    return {"color": color, "max_dim": max_dim, "arm": arm}


def _l_cells(arm: int, size: int, corners: str) -> set[tuple[int, int]]:
    top_left = {(0, step) for step in range(arm)} | {(step, 0) for step in range(arm)}
    result: set[tuple[int, int]] = set()
    for row, col in top_left:
        result.add((row, col))
        result.add((size - 1 - row, size - 1 - col))
        if corners == "all":
            result.add((row, size - 1 - col))
            result.add((size - 1 - row, col))
    return result


def python_transform(
    grid: Any,
    ring_step: int = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
) -> list[list[int]]:
    """Independent Python mirror used only to cross-check Racket authoring labels."""
    _validate_setting(ring_step, corners)
    source = _grid_copy(grid)
    background = source[0][0]
    colors = sorted({value for row in source for value in row if value != background})
    if not colors:
        raise ValueError("rule requires at least one non-background color")
    infos = [_color_info(source, color) for color in colors]
    has_center = any(info["max_dim"] == 1 for info in infos)
    start = 1 if has_center else 3
    rings = [start + ring_step * index for index in range(len(infos))]
    available = list(rings)
    exact = [info for info in infos if info["max_dim"] in rings]
    loose = [info for info in infos if info["max_dim"] not in rings]
    assignments: list[tuple[dict[str, int], int]] = []
    for info in loose + sorted(exact, key=lambda item: -item["max_dim"]):
        target = next((ring for ring in available if ring >= info["max_dim"]), None)
        if target is None:
            raise ValueError(
                f"color {info['color']} max-dim {info['max_dim']} fits no remaining ring"
            )
        available.remove(target)
        assignments.append((info, target))

    size = max(rings)
    middle = size // 2
    output = [[background for _ in range(size)] for _ in range(size)]
    for info, ring_size in sorted(assignments, key=lambda item: -item[1]):
        offset = middle - ring_size // 2
        for row, col in _l_cells(min(info["arm"], ring_size), ring_size, corners):
            output[offset + row][offset + col] = info["color"]
    return output


def canonical_parity(*, root=None, bridge=None) -> dict[str, Any]:
    """Check exact default identity and all labeled canonical pairs through Racket."""
    record, ledger = _canonical_record(root=root)
    program = materialize_rule(root=root)
    if program != record["program_solution"]:
        raise RuntimeError("default prototype program differs from canonical authority")
    resolved = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge() as owned:
            return canonical_parity(root=resolved, bridge=owned)
    cases = []
    for pair in canonical_pairs(TASK_ID, root=resolved, labeled_only=True):
        output = execute_rule(program, pair["input"], bridge=bridge, root=resolved)
        cases.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": _grid_hash(pair["input"]),
                "expected_sha256": _grid_hash(pair["output"]),
                "output_sha256": _grid_hash(output),
                "matches": output == pair["output"],
            }
        )
    return {
        "task_id": TASK_ID,
        "canonical_ledger_sha256": _sha_bytes(ledger.read_bytes()),
        "canonical_program": program,
        "program_sha256": _sha_text(program),
        "program_exact_match": True,
        "cases": cases,
        "passed": bool(cases) and all(row["matches"] for row in cases),
    }



def _bounded_integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def choose_parameters(
    seed: int,
    ring_step: int | str = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
) -> tuple[int, str]:
    """Resolve explicit parameters or sample each once for the whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = random.Random(f"{VERSION}:{seed}:parameters")
    chosen_step = rng.choice(RING_STEPS) if ring_step == "sample" else ring_step
    chosen_corners = rng.choice(CORNER_PATTERNS) if corners == "sample" else corners
    _validate_setting(chosen_step, chosen_corners)
    return chosen_step, chosen_corners


def _selected_generator(*, root=None):
    resolved = find_root(__file__) if root is None else Path(root).resolve()
    key = str(resolved)
    if key not in _SELECTED_GENERATORS:
        module, _source, digest = load_selected_generator(TASK_ID, root=resolved)
        _SELECTED_GENERATORS[key] = (module, digest)
    return _SELECTED_GENERATORS[key]


def _boundary_stress_input(seed: int, attempt: int, *, root=None) -> list[list[int]]:
    """Spread six lawful glyphs across a substantive 30x30 query canvas."""
    module, _digest = _selected_generator(root=root)
    token = f"{VERSION}:{seed}:boundary-stress:{attempt}".encode("utf-8")
    derived_seed = int.from_bytes(hashlib.sha256(token).digest()[:8], "big")
    # Profile index 2 is the reviewed six-color, center-bearing grammar.  Only
    # translation changes: every color's cells, bounding box, and corner arm are
    # preserved exactly while the family-specific query reaches ARC's boundary.
    source = _grid_copy(module.generate(derived_seed, 2))
    background = source[0][0]
    colors = sorted({value for row in source for value in row if value != background})
    objects = []
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(source)
            for col, value in enumerate(values)
            if value == color
        ]
        min_row = min(row for row, _ in cells)
        min_col = min(col for _, col in cells)
        max_row = max(row for row, _ in cells)
        max_col = max(col for _, col in cells)
        objects.append(
            {
                "color": color,
                "height": max_row - min_row + 1,
                "width": max_col - min_col + 1,
                "cells": [(row - min_row, col - min_col) for row, col in cells],
            }
        )
    objects.sort(
        key=lambda item: (-max(item["height"], item["width"]), item["color"])
    )
    if len(objects) != 6:
        raise RuntimeError("boundary stress profile did not yield six colors")

    size = 30
    output = [[background for _ in range(size)] for _ in range(size)]
    occupied: set[tuple[int, int]] = set()
    for index, item in enumerate(objects):
        height, width = item["height"], item["width"]
        anchors = (
            (0, 1),
            (0, size - width),
            (size - height, 0),
            (size - height, size - width),
            ((size - height) // 2, 0),
            ((size - height) // 2, size - width),
        )
        top, left = anchors[index]
        absolute = [(top + row, left + col) for row, col in item["cells"]]
        if any(cell in occupied for cell in absolute):
            raise RuntimeError("boundary stress placements overlap")
        occupied.update(absolute)
        for row, col in absolute:
            output[row][col] = item["color"]

    errors = module.self_check(output)
    if errors:
        raise RuntimeError("boundary stress violates source grammar: " + "; ".join(errors))
    return output


def _draw_input(seed: int, split: str, index: int, attempt: int, *, root=None):
    """Draw from a setting-independent stream with split-stable query indices."""
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    if split == "test" and index == 3:
        return _boundary_stress_input(seed, attempt, root=root)
    module, _digest = _selected_generator(root=root)
    token = f"{VERSION}:{seed}:{split}:{index}:{attempt}".encode("utf-8")
    derived_seed = int.from_bytes(hashlib.sha256(token).digest()[:8], "big")
    sample_index = index + (0 if split == "train" else 10_000)
    return _grid_copy(module.generate(derived_seed, sample_index))


def assess_lesson(
    demos,
    query_inputs,
    ring_step: int = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
    *,
    bridge=None,
    root=None,
) -> dict[str, Any]:
    """Fit the finite four-rule family to demonstrations, never query answers."""
    _validate_setting(ring_step, corners)
    if type(demos) is not list or not demos:
        raise ValueError("a lesson needs at least one demonstration")
    if type(query_inputs) is not list or not query_inputs:
        raise ValueError("a lesson needs at least one query input")
    normalized_demos = []
    for pair in demos:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("each demonstration requires input and output grids")
        normalized_demos.append(
            {"input": _grid_copy(pair["input"]), "output": _grid_copy(pair["output"])}
        )
    normalized_queries = [_grid_copy(grid) for grid in query_inputs]
    if bridge is None:
        with RacketBridge() as owned:
            return assess_lesson(
                normalized_demos,
                normalized_queries,
                ring_step,
                corners,
                bridge=owned,
                root=root,
            )

    grids = [pair["input"] for pair in normalized_demos] + normalized_queries
    predictions: dict[str, list[list[list[int]]]] = {}
    for candidate_step, candidate_corners in SETTINGS:
        name = f"{candidate_step}/{candidate_corners}"
        program = materialize_rule(candidate_step, candidate_corners, root=root)
        predictions[name] = [
            execute_rule(program, grid, bridge=bridge, root=root) for grid in grids
        ]
    refutations = {
        name: [
            index
            for index, pair in enumerate(normalized_demos)
            if outputs[index] != pair["output"]
        ]
        for name, outputs in predictions.items()
    }
    survivors = [name for name in predictions if not refutations[name]]
    intended = f"{ring_step}/{corners}"
    identified = survivors == [intended]
    queries = []
    for index, grid in enumerate(normalized_queries):
        offset = len(normalized_demos) + index
        differing = [
            name
            for name, outputs in predictions.items()
            if name != intended and outputs[offset] != predictions[intended][offset]
        ]
        remaining = [name for name in differing if name in survivors]
        queries.append(
            {
                "query_index": index,
                "input_sha256": _grid_hash(grid),
                "output_sha256": _grid_hash(predictions[intended][offset]),
                "differing_rivals": differing,
                "refuting_demo_indices": {
                    name: refutations[name] for name in differing
                },
                "remaining_differing_rivals": remaining,
                "identifiable_from_demos": intended in survivors and not remaining,
            }
        )
    return {
        "identified": identified,
        "surviving_settings": survivors,
        "intended_fits_demos": intended in survivors,
        "demo_refutations": refutations,
        "queries": queries,
        "racket_prediction_count": len(SETTINGS) * len(grids),
        "scope": "the four declared ring-step/corner-set settings only",
    }


def generate_claim_episode(
    *,
    seed: int = 17,
    ring_step: int | str = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
    train: int = 3,
    test: int = 4,
    max_attempts: int = 64,
    root=None,
) -> dict[str, Any]:
    """Return native claim labels without starting protected Racket.

    This path exists for the native promotion worker, which independently
    executes ``program_solution`` through protected Racket and rejects any
    claim-label disagreement.  The richer :func:`generate_episode` path below
    remains the authoring/audit interface and performs its own Racket checks.
    """
    chosen_step, chosen_corners = choose_parameters(seed, ring_step, corners)
    _bounded_integer("train", train, 1, 16)
    _bounded_integer("test", test, 1, 32)
    _bounded_integer("max_attempts", max_attempts, 1, 10_000)

    seen: set[str] = set()
    grids: dict[str, list[list[list[int]]]] = {}
    for split, count in (("train", train), ("test", test)):
        grids[split] = []
        for index in range(count):
            for attempt in range(max_attempts):
                grid = _draw_input(seed, split, index, attempt, root=root)
                fingerprint = _grid_hash(grid)
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                grids[split].append(grid)
                break
            else:
                raise RuntimeError(
                    f"uniqueness sampling exhausted after {max_attempts} attempts "
                    f"for {split}[{index}]"
                )

    def labeled(split: str) -> list[dict[str, list[list[int]]]]:
        return [
            {
                "input": grid,
                "output": python_transform(grid, chosen_step, chosen_corners),
            }
            for grid in grids[split]
        ]

    return {
        "train": labeled("train"),
        "test": labeled("test"),
        "program_solution": materialize_rule(chosen_step, chosen_corners, root=root),
    }


def generate_episode(
    *,
    seed: int = 17,
    ring_step: int | str = DEFAULT_RING_STEP,
    corners: str = DEFAULT_CORNERS,
    train: int = 3,
    test: int = 4,
    max_attempts: int = 64,
    bridge=None,
    root=None,
) -> dict[str, Any]:
    """Return one public lesson and its private reference labels/evidence."""
    chosen_step, chosen_corners = choose_parameters(seed, ring_step, corners)
    _bounded_integer("train", train, 1, 16)
    _bounded_integer("test", test, 1, 32)
    _bounded_integer("max_attempts", max_attempts, 1, 10_000)
    if bridge is None:
        with RacketBridge() as owned:
            return generate_episode(
                seed=seed,
                ring_step=chosen_step,
                corners=chosen_corners,
                train=train,
                test=test,
                max_attempts=max_attempts,
                bridge=owned,
                root=root,
            )

    seen: set[str] = set()
    grids: dict[str, list[list[list[int]]]] = {}
    accepted_attempts: dict[str, list[int]] = {}
    for split, count in (("train", train), ("test", test)):
        grids[split] = []
        accepted_attempts[split] = []
        for index in range(count):
            for attempt in range(max_attempts):
                grid = _draw_input(seed, split, index, attempt, root=root)
                fingerprint = _grid_hash(grid)
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                grids[split].append(grid)
                accepted_attempts[split].append(attempt)
                break
            else:
                raise RuntimeError(
                    f"uniqueness sampling exhausted after {max_attempts} attempts "
                    f"for {split}[{index}]"
                )

    program = materialize_rule(chosen_step, chosen_corners, root=root)
    labels = {
        split: [
            execute_rule(program, grid, bridge=bridge, root=root) for grid in inputs
        ]
        for split, inputs in grids.items()
    }
    for split, inputs in grids.items():
        for grid, label in zip(inputs, labels[split], strict=True):
            if python_transform(grid, chosen_step, chosen_corners) != label:
                raise RuntimeError("independent Python cross-check disagrees with Racket")

    challenge = {
        "train": [
            {"input": grid, "output": label}
            for grid, label in zip(grids["train"], labels["train"], strict=True)
        ],
        "test": [{"input": grid} for grid in grids["test"]],
    }
    lesson_check = assess_lesson(
        challenge["train"],
        grids["test"],
        chosen_step,
        chosen_corners,
        bridge=bridge,
        root=root,
    )
    if not lesson_check["identified"] or not all(
        row["identifiable_from_demos"] for row in lesson_check["queries"]
    ):
        raise RuntimeError("demonstrations did not identify the requested episode rule")
    _module, generator_sha256 = _selected_generator(root=root)
    private = {
        "status": "proposed prototype; no production approval or training admission",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "parameters": {"ring_step": chosen_step, "corners": chosen_corners},
        "program": program,
        "program_sha256": _sha_text(program),
        "answers": labels["test"],
        "train_count": train,
        "test_count": test,
        "unique_input_count": len(seen),
        "accepted_attempts": accepted_attempts,
        "input_sha256": {
            split: [_grid_hash(grid) for grid in inputs]
            for split, inputs in grids.items()
        },
        "shapes": {
            split: [[len(grid), len(grid[0])] for grid in inputs]
            for split, inputs in grids.items()
        },
        "lesson_check": lesson_check,
        "generator_sha256": generator_sha256,
        "reference_execution_count": (
            train + test + lesson_check["racket_prediction_count"]
        ),
    }
    return {"challenge": challenge, "private": private}



def public_identifier(challenge) -> str:
    """Opaque content identity over exactly the visible challenge bytes."""
    return "episode-" + public_challenge_id(challenge)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_json_bytes(value))


def write_episode(episode: dict[str, Any], out: Path | str) -> None:
    """Write one schema-clean public lesson plus explicitly private evidence."""
    if type(episode) is not dict or set(episode) != {"challenge", "private"}:
        raise ValueError("episode must contain exactly challenge and private")
    public_bytes = public_challenge_bytes(episode["challenge"])
    private_bytes = _json_bytes(episode["private"])
    program = episode["private"].get("program")
    if type(program) is not str:
        raise ValueError("private episode must contain its exact program")

    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=False)
    public_dir = destination / "public"
    private_dir = destination / "private"
    public_dir.mkdir()
    private_dir.mkdir()
    (public_dir / "challenge.json").write_bytes(public_bytes)
    (private_dir / "episode.json").write_bytes(private_bytes)
    (private_dir / "program.rkt").write_text(program, encoding="utf-8")


def write_episodes(episodes, out: Path | str) -> None:
    """Write a batch after validating every public payload and opaque identity."""
    prepared = []
    for episode in episodes:
        if type(episode) is not dict or "challenge" not in episode:
            raise ValueError("each episode must contain a challenge")
        payload = public_challenge_bytes(episode["challenge"])
        prepared.append((public_identifier(episode["challenge"]), payload, episode))
    if not prepared:
        raise ValueError("episode batch must be nonempty")
    if len({payload for _name, payload, _episode in prepared}) != len(prepared):
        raise ValueError("duplicate public challenge in episode batch")
    if len({name for name, _payload, _episode in prepared}) != len(prepared):
        raise ValueError("duplicate public challenge identifier in episode batch")

    destination = Path(out)
    destination.mkdir(parents=True, exist_ok=False)
    for name, _payload, episode in sorted(prepared, key=lambda row: row[0]):
        write_episode(episode, destination / name)


def _source_hashes(root: Path) -> dict[str, str]:
    task_home = root / "generators" / TASK_ID
    candidates = (
        Path(__file__),
        Path(__file__).with_name("README.md"),
        task_home / "tests" / "test_parametric_corner_rings.py",
        task_home / "generator.py",
        root / "shared/runtime/reviewer_support.py",
        root / "shared/runtime/puzzle_generators/rule_wrap.py",
        root / "shared/runtime/arc_repl/racket_bridge.py",
    )
    return {
        str(candidate.relative_to(root)): _sha_bytes(candidate.read_bytes())
        for candidate in candidates
        if candidate.is_file()
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--ring-step", choices=("2", "4", "sample"))
    parser.add_argument("--corners", choices=(*CORNER_PATTERNS, "sample"))
    parser.add_argument(
        "--train", type=int, default=3, help="demonstrations, 1..16 (default 3)"
    )
    parser.add_argument(
        "--test", type=int, default=4, help="distinct query inputs, 1..32 (default 4)"
    )
    parser.add_argument("--max-attempts", type=int, default=64)
    parser.add_argument(
        "--all-settings",
        action="store_true",
        help="write one episode for each of the four declared settings",
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="new output directory; never overwritten"
    )
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    if args.all_settings and (args.ring_step is not None or args.corners is not None):
        parser.error("--all-settings cannot be combined with parameter overrides")

    requested_step: int | str = (
        DEFAULT_RING_STEP
        if args.ring_step is None
        else args.ring_step
        if args.ring_step == "sample"
        else int(args.ring_step)
    )
    requested_corners = DEFAULT_CORNERS if args.corners is None else args.corners
    settings = (
        SETTINGS
        if args.all_settings
        else (choose_parameters(args.seed, requested_step, requested_corners),)
    )

    root = find_root(__file__)
    with RacketBridge() as bridge:
        parity = canonical_parity(root=root, bridge=bridge)
        if not parity["passed"]:
            raise RuntimeError("canonical parity failed")
        episodes = [
            generate_episode(
                seed=args.seed,
                ring_step=ring_step,
                corners=corners,
                train=args.train,
                test=args.test,
                max_attempts=args.max_attempts,
                bridge=bridge,
                root=root,
            )
            for ring_step, corners in settings
        ]
        contrast_input = _draw_input(args.seed, "test", 97, 0, root=root)
        contrast_outputs = {
            f"{ring_step}/{corners}": execute_rule(
                materialize_rule(ring_step, corners, root=root),
                contrast_input,
                bridge=bridge,
                root=root,
            )
            for ring_step, corners in SETTINGS
        }
        if len({_grid_hash(output) for output in contrast_outputs.values()}) != len(SETTINGS):
            raise RuntimeError("contrast input does not distinguish all four settings")
        runtime_identity = bridge.runtime_identity

    if args.all_settings:
        write_episodes(episodes, args.out)
        private_dir = args.out / "private"
        private_dir.mkdir()
    else:
        write_episode(episodes[0], args.out)
        private_dir = args.out / "private"

    contrast = {
        "input": contrast_input,
        "input_sha256": _grid_hash(contrast_input),
        "outputs": {
            name: {"grid": output, "sha256": _grid_hash(output)}
            for name, output in contrast_outputs.items()
        },
    }
    _write_json(private_dir / "canonical-parity.json", parity)
    _write_json(private_dir / "racket-runtime.json", runtime_identity)
    _write_json(private_dir / "contrast.json", contrast)

    summary = {
        "status": "proposed prototype; no production approval or training admission",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": args.seed,
        "source_sha256": _source_hashes(root),
        "canonical_parity_passed": parity["passed"],
        "canonical_pair_count": len(parity["cases"]),
        "episode_count": len(episodes),
        "query_count": sum(episode["private"]["test_count"] for episode in episodes),
        "all_queries_identified_from_demos": all(
            episode["private"]["lesson_check"]["identified"]
            and all(
                row["identifiable_from_demos"]
                for row in episode["private"]["lesson_check"]["queries"]
            )
            for episode in episodes
        ),
        "reference_execution_count": (
            len(parity["cases"])
            + len(SETTINGS)
            + sum(
                episode["private"]["reference_execution_count"]
                for episode in episodes
            )
        ),
        "episodes": [
            {
                "public_identifier": public_identifier(episode["challenge"]),
                "parameters": episode["private"]["parameters"],
                "program_sha256": episode["private"]["program_sha256"],
                "train_count": episode["private"]["train_count"],
                "test_count": episode["private"]["test_count"],
                "unique_input_count": episode["private"]["unique_input_count"],
                "shapes": episode["private"]["shapes"],
            }
            for episode in episodes
        ],
        "limits": [
            "Finite-family identifiability covers only the four declared settings.",
            "The prototype reuses the reviewed production input sampler; it does not alter production code.",
            "All labels are Racket-executed and Python-cross-checked, but this is bounded review evidence rather than admission.",
        ],
    }
    _write_json(private_dir / "summary.json", summary)
    print(
        json.dumps(
            {
                "out": str(args.out),
                "episodes": len(episodes),
                "queries": summary["query_count"],
                "canonical_pairs": len(parity["cases"]),
                "all_queries_identified_from_demos": summary[
                    "all_queries_identified_from_demos"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
