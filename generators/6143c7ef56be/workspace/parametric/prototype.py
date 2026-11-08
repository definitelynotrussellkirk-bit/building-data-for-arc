#!/usr/bin/env python3
"""Proposed native parametric family for ARC task 6143c7ef56be.

The canonical/default setting collapses four quadrant markers into the cyan
2x2 block.  The two alternatives add a genuinely sequential operation:

1. choose the unique nearest or farthest marker by Manhattan distance to its
   corresponding destination cell in the collapsed block;
2. use that selected marker record to paint an L-shaped route into the block.

Racket is the label authority.  Python mirrors are diagnostics and evidence
helpers only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import sys
import tempfile
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    public_challenge_bytes as _public_challenge_bytes,
    public_challenge_id as _public_challenge_id,
)


TASK_ID = "6143c7ef56be"
ALLOWED_ROUTE_MARKERS = ("none", "nearest", "farthest")
DEFAULT_ROUTE_MARKER = "none"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)
_QUADRANTS = ("tl", "tr", "bl", "br")
_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)

# Distances are respectively 4/2/6/5, 4/6/2/5, 6/4/5/2, and 2/5/4/6.
# Thus every scene has unique extrema while the selected quadrant rotates.
_DISTANCE_TEMPLATES = (
    {"tl": (2, 2), "tr": (1, 1), "bl": (3, 3), "br": (2, 3)},
    {"tl": (1, 3), "tr": (3, 3), "bl": (1, 1), "br": (2, 3)},
    {"tl": (3, 3), "tr": (2, 2), "bl": (2, 3), "br": (1, 1)},
    {"tl": (1, 1), "tr": (2, 3), "bl": (2, 2), "br": (3, 3)},
)


def _validate_route_marker(route_marker: str) -> None:
    if type(route_marker) is not str or route_marker not in ALLOWED_ROUTE_MARKERS:
        raise ValueError(
            f"route_marker must be one of {ALLOWED_ROUTE_MARKERS}, got {route_marker!r}"
        )


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 8:
        raise ValueError("queries must be an exact integer in 1..8")


def canonical_source(*, root: Path = ROOT) -> str:
    """Return the one unique exact canonical program for this task."""
    programs: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"canonical record for {TASK_ID} lacks program_solution")
            programs.append(source)
    unique = list(dict.fromkeys(programs))
    if len(unique) != 1:
        raise ValueError(
            f"expected one unique canonical program for {TASK_ID}, found {len(unique)}"
        )
    return unique[0]


def _route_program(route_marker: str) -> str:
    reducer = "min-of" if route_marker == "nearest" else "max-of"
    return f"""(rule! (lambda (g)
         (let* ((cyan (find-color g 8))
                (cr1 (min-of first cyan))
                (cc1 (min-of second cyan))
                (colors (filter (lambda (v) (and (!= v 0) (!= v 8))) (grid-colors g)))
                (mapping (map (lambda (v)
                                (let ((pos (first (find-color g v))))
                                  (list (if (< (first pos) cr1) 0 1)
                                        (if (< (second pos) cc1) 0 1)
                                        v)))
                              colors))
                (base (reduce (lambda (out m)
                                (let ((rr (+ cr1 (first m)))
                                      (cc (+ cc1 (second m))))
                                  (if (zero? (at out rr cc))
                                      (set-cell out rr cc (third m))
                                      out)))
                              (empty-grid h w 0)
                              mapping))
                (candidates
                  (map (lambda (m)
                         (let* ((v (third m))
                                (pos (first (find-color g v)))
                                (tr (+ cr1 (first m)))
                                (tc (+ cc1 (second m)))
                                (distance (+ (abs (- (first pos) tr))
                                             (abs (- (second pos) tc)))))
                           (list distance (first pos) (second pos) tr tc v)))
                       mapping))
                (best-distance ({reducer} first candidates))
                (chosen (find-first (lambda (candidate)
                                      (= (first candidate) best-distance))
                                    candidates))
                (with-vertical
                  (draw-line base
                             (second chosen) (third chosen)
                             (fourth chosen) (third chosen)
                             (list-ref chosen 5))))
           (draw-line with-vertical
                      (fourth chosen) (third chosen)
                      (fourth chosen) (list-ref chosen 4)
                      (list-ref chosen 5)))))"""


def program_for(
    route_marker: str = DEFAULT_ROUTE_MARKER, *, root: Path = ROOT
) -> str:
    """Materialize exact Racket for one episode-fixed route setting."""
    _validate_route_marker(route_marker)
    if route_marker == DEFAULT_ROUTE_MARKER:
        return canonical_source(root=root)
    return _route_program(route_marker)


def execute_rule(program: str, grid, *, bridge: RacketBridge | None = None):
    """Execute a complete rule through the protected Racket bridge."""
    owns_bridge = bridge is None
    active = (
        RacketBridge(max_calls_before_restart=128, timeout=20)
        if owns_bridge
        else bridge
    )
    try:
        active.define_grid("g", grid)
        return active.eval_text(f"({wrap_rule(program)} g)")
    finally:
        if owns_bridge:
            active.shutdown()


def _valid_grid_shape(grid) -> tuple[int, int] | None:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return None
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return None
    return len(grid), width


def analyze_input(grid) -> dict[str, Any]:
    """Analyze the shared proposed grammar and retain exact marker facts."""
    result: dict[str, Any] = {"errors": []}
    errors: list[str] = result["errors"]
    shape = _valid_grid_shape(grid)
    if shape is None:
        errors.append("grid must be a nonempty rectangular list of rows")
        return result
    height, width = shape
    if not (8 <= height <= 30 and 8 <= width <= 30):
        errors.append(f"grid dimensions must be within 8..30, got {height}x{width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be exact integer ARC colors 0..9")
        return result

    cyan = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if len(cyan) != 4:
        errors.append(f"expected exactly four cyan cells, got {len(cyan)}")
        return result
    block_row = min(row for row, _ in cyan)
    block_col = min(col for _, col in cyan)
    expected = {
        (block_row, block_col),
        (block_row, block_col + 1),
        (block_row + 1, block_col),
        (block_row + 1, block_col + 1),
    }
    if set(cyan) != expected:
        errors.append("cyan cells must form one solid 2x2 block")
        return result

    raw_markers = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 8)
    ]
    if len(raw_markers) != 4:
        errors.append(f"expected exactly four marker cells, got {len(raw_markers)}")
        return result
    colors = [color for _, _, color in raw_markers]
    if len(set(colors)) != 4:
        errors.append("marker colors must be pairwise distinct")

    markers: dict[str, dict[str, Any]] = {}
    for row, col, color in raw_markers:
        vertical = "t" if row < block_row else "b" if row > block_row + 1 else None
        horizontal = "l" if col < block_col else "r" if col > block_col + 1 else None
        if vertical is None or horizontal is None:
            errors.append(f"marker at ({row}, {col}) is not in a strict quadrant")
            continue
        quadrant = vertical + horizontal
        if quadrant in markers:
            errors.append(f"more than one marker lies in quadrant {quadrant}")
            continue
        target_row = block_row + (1 if vertical == "b" else 0)
        target_col = block_col + (1 if horizontal == "r" else 0)
        markers[quadrant] = {
            "quadrant": quadrant,
            "row": row,
            "col": col,
            "color": color,
            "target_row": target_row,
            "target_col": target_col,
            "distance": abs(row - target_row) + abs(col - target_col),
        }
    missing = [quadrant for quadrant in _QUADRANTS if quadrant not in markers]
    if missing:
        errors.append(f"missing marker quadrant(s): {', '.join(missing)}")

    if len(markers) == 4:
        distances = [marker["distance"] for marker in markers.values()]
        minimum = min(distances)
        maximum = max(distances)
        if distances.count(minimum) != 1:
            errors.append("nearest marker distance must be unique")
        if distances.count(maximum) != 1:
            errors.append("farthest marker distance must be unique")
        if minimum == maximum:
            errors.append("nearest and farthest markers must differ")

    result.update(
        {
            "height": height,
            "width": width,
            "block_row": block_row,
            "block_col": block_col,
            "markers": markers,
        }
    )
    return result


def validate_input(grid) -> list[str]:
    return list(analyze_input(grid)["errors"])


def _canonical_output(facts: dict[str, Any]) -> list[list[int]]:
    output = [[0] * facts["width"] for _ in range(facts["height"])]
    block_row = facts["block_row"]
    block_col = facts["block_col"]
    for quadrant in _QUADRANTS:
        marker = facts["markers"][quadrant]
        output[marker["target_row"]][marker["target_col"]] = marker["color"]
    return output


def _selected_marker(facts: dict[str, Any], route_marker: str) -> dict[str, Any] | None:
    if route_marker == "none":
        return None
    key = min if route_marker == "nearest" else max
    selected_distance = key(marker["distance"] for marker in facts["markers"].values())
    matches = [
        marker
        for marker in facts["markers"].values()
        if marker["distance"] == selected_distance
    ]
    if len(matches) != 1:
        raise ValueError(f"{route_marker} marker is not unique")
    return matches[0]


def _paint_route(output: list[list[int]], marker: dict[str, Any]) -> None:
    color = marker["color"]
    source_row, source_col = marker["row"], marker["col"]
    target_row, target_col = marker["target_row"], marker["target_col"]
    for row in range(min(source_row, target_row), max(source_row, target_row) + 1):
        output[row][source_col] = color
    for col in range(min(source_col, target_col), max(source_col, target_col) + 1):
        output[target_row][col] = color


def python_apply(grid, *, route_marker: str = DEFAULT_ROUTE_MARKER):
    """Independent diagnostic mirror; Racket remains output authority."""
    _validate_route_marker(route_marker)
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = _canonical_output(facts)
    marker = _selected_marker(facts, route_marker)
    if marker is not None:
        _paint_route(output, marker)
    return output


def sequential_trace(grid, *, route_marker: str) -> dict[str, Any]:
    """Expose the Step-A intermediate used causally by Step B."""
    _validate_route_marker(route_marker)
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    marker = _selected_marker(facts, route_marker)
    intermediate = None
    if marker is not None:
        intermediate = {
            "quadrant": marker["quadrant"],
            "color": marker["color"],
            "source": [marker["row"], marker["col"]],
            "target": [marker["target_row"], marker["target_col"]],
            "manhattan_distance": marker["distance"],
        }
    return {
        "step_a": (
            "select no route marker"
            if marker is None
            else f"select the unique {route_marker} marker by block-corner Manhattan distance"
        ),
        "intermediate_value": intermediate,
        "step_b": (
            "emit only the canonical collapsed 2x2"
            if marker is None
            else "paint a vertical-then-horizontal route from the selected marker into its destination cell"
        ),
        "output": python_apply(grid, route_marker=route_marker),
    }


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|{PROTOTYPE_VERSION}|{seed}|{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(seed: int, index: int, *, force_30: bool = False) -> list[list[int]]:
    rng = _rng(seed, index)
    if force_30:
        height = width = 30
    else:
        height = 12 + rng.randrange(7)
        width = 12 + rng.randrange(7)
    block_row = rng.randint(4, height - 6)
    block_col = rng.randint(4, width - 6)
    template = _DISTANCE_TEMPLATES[(seed + index) % len(_DISTANCE_TEMPLATES)]
    colors = rng.sample(_PALETTE, 4)

    grid = [[0] * width for _ in range(height)]
    for row in (block_row, block_row + 1):
        for col in (block_col, block_col + 1):
            grid[row][col] = 8

    for quadrant, color in zip(_QUADRANTS, colors):
        dr, dc = template[quadrant]
        if quadrant == "tl":
            row, col = block_row - dr, block_col - dc
        elif quadrant == "tr":
            row, col = block_row - dr, block_col + 1 + dc
        elif quadrant == "bl":
            row, col = block_row + 1 + dr, block_col - dc
        else:
            row, col = block_row + 1 + dr, block_col + 1 + dc
        grid[row][col] = color

    errors = validate_input(grid)
    if errors:
        raise AssertionError(f"internal scene construction failed: {errors}")
    return grid


def grid_sha256(grid) -> str:
    return hashlib.sha256(
        json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def normalized_program_sha256(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode("utf-8")).hexdigest()


def _sample_inputs(seed: int, demos: int, queries: int) -> tuple[list, list]:
    seen: set[str] = set()

    def unique_scene(index: int, *, force_30: bool = False):
        for attempt in range(64):
            grid = _scene(seed, index + attempt * 10_000, force_30=force_30)
            digest = grid_sha256(grid)
            if digest not in seen:
                seen.add(digest)
                return grid
        raise RuntimeError("could not construct a distinct deterministic input")

    train = [unique_scene(index) for index in range(demos)]
    test = [
        unique_scene(100 + index, force_30=(index == 3))
        for index in range(queries)
    ]
    return train, test


def _corner_copy(grid) -> list[list[int]]:
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = [[0] * facts["width"] for _ in range(facts["height"])]
    row, col = facts["block_row"], facts["block_col"]
    output[row][col] = grid[0][0]
    output[row][col + 1] = grid[0][-1]
    output[row + 1][col] = grid[-1][0]
    output[row + 1][col + 1] = grid[-1][-1]
    return output


def _fixed_top_left_route(grid) -> list[list[int]]:
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = _canonical_output(facts)
    _paint_route(output, facts["markers"]["tl"])
    return output


def _mismatch_indices(pairs: list[dict[str, Any]], rival) -> list[int]:
    return [
        index
        for index, pair in enumerate(pairs)
        if rival(pair["input"]) != pair["output"]
    ]


def _audit_episode(
    train: list[dict[str, Any]],
    *,
    chosen: str,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    finite_survivors: list[str] = []
    finite_rows: list[dict[str, Any]] = []
    for candidate in ALLOWED_ROUTE_MARKERS:
        program = program_for(candidate, root=root)
        mismatches = [
            index
            for index, pair in enumerate(train)
            if execute_rule(program, pair["input"], bridge=bridge) != pair["output"]
        ]
        if not mismatches:
            finite_survivors.append(candidate)
        if candidate != chosen:
            finite_rows.append(
                {
                    "route_marker": candidate,
                    "status": (
                        "survives_demonstrations"
                        if not mismatches
                        else "refuted_by_demonstrations"
                    ),
                    "demonstration_mismatch_indices": mismatches,
                }
            )

    shortcut_rows = {}
    for name, rival in (
        ("corner_copy", _corner_copy),
        ("fixed_top_left_route", _fixed_top_left_route),
    ):
        mismatches = _mismatch_indices(train, rival)
        shortcut_rows[name] = {
            "status": (
                "refuted_by_demonstrations"
                if mismatches
                else "survives_demonstrations"
            ),
            "demonstration_mismatch_indices": mismatches,
        }

    return {
        "finite_survivors": finite_survivors,
        "finite_parameter_rivals": finite_rows,
        **shortcut_rows,
    }


def make_episode(
    seed: int,
    *,
    route_marker: str = DEFAULT_ROUTE_MARKER,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one paired episode and derive every private label in Racket."""
    _validate_seed(seed)
    _validate_route_marker(route_marker)
    _validate_counts(demos, queries)
    program = program_for(route_marker, root=root)
    train_inputs, test_inputs = _sample_inputs(seed, demos, queries)

    owns_bridge = bridge is None
    active = (
        RacketBridge(max_calls_before_restart=128, timeout=20)
        if owns_bridge
        else bridge
    )
    try:
        def label(grid):
            output = execute_rule(program, grid, bridge=active)
            mirror = python_apply(grid, route_marker=route_marker)
            if output != mirror:
                raise AssertionError(
                    f"Racket/Python drift for route_marker={route_marker}"
                )
            return {"input": copy.deepcopy(grid), "output": output}

        train = [label(grid) for grid in train_inputs]
        test = [label(grid) for grid in test_inputs]
        audit = _audit_episode(
            train, chosen=route_marker, root=root, bridge=active
        )
    finally:
        if owns_bridge:
            active.shutdown()

    ambiguities: list[str] = []
    if audit["finite_survivors"] != [route_marker]:
        ambiguities.append(
            f"finite survivors were {audit['finite_survivors']!r}, expected {[route_marker]!r}"
        )
    for name in ("corner_copy", "fixed_top_left_route"):
        if audit[name]["status"] != "refuted_by_demonstrations":
            ambiguities.append(f"shortcut rival {name} survived demonstrations")

    return {
        "schema": "arcpuzzles-parametric-route-marker-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"route_marker": route_marker},
        "program": program,
        "program_sha256": hashlib.sha256(program.encode("utf-8")).hexdigest(),
        "program_normalized_sha256": normalized_program_sha256(program),
        "train": train,
        "test": test,
        "audit": audit,
        "ambiguities": ambiguities,
        "reference": "proposed_parametric",
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Detached projection containing demos and query inputs only."""
    return json.loads(_public_challenge_bytes(episode))


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    if type(index) is not int or not 0 <= index < len(episode.get("test", [])):
        raise ValueError("query index out of range")
    challenge = {
        "train": episode["train"],
        "test": [episode["test"][index]],
    }
    return json.loads(_public_challenge_bytes(challenge))


def public_id(episode: dict[str, Any]) -> str:
    return _public_challenge_id(episode)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def write_evidence(
    *,
    seed: int,
    out: Path,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
    root: Path = ROOT,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write a compact, source-bound proposed-evidence bundle atomically."""
    _validate_seed(seed)
    _validate_counts(demos, queries)
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}-", dir=out.parent))

    owns_bridge = bridge is None
    active = (
        RacketBridge(max_calls_before_restart=128, timeout=20)
        if owns_bridge
        else bridge
    )
    try:
        episode_rows = []
        episodes = []
        for setting in ALLOWED_ROUTE_MARKERS:
            episode = make_episode(
                seed,
                route_marker=setting,
                demos=demos,
                queries=queries,
                root=root,
                bridge=active,
            )
            episodes.append(episode)
            pid = public_id(episode)
            private_path = Path("private") / f"episode-{setting}.json"
            public_path = Path("public") / f"challenge-{pid}.json"
            racket_path = Path("racket") / f"route-marker-{setting}.rkt"
            for relative in (private_path, public_path, racket_path):
                (temp / relative).parent.mkdir(parents=True, exist_ok=True)
            (temp / private_path).write_bytes(_json_bytes(episode))
            (temp / public_path).write_bytes(_public_challenge_bytes(episode))
            (temp / racket_path).write_text(episode["program"] + "\n", encoding="utf-8")
            episode_rows.append(
                {
                    "route_marker": setting,
                    "public_id": pid,
                    "public_path": public_path.as_posix(),
                    "private_path": private_path.as_posix(),
                    "racket_path": racket_path.as_posix(),
                    "program_sha256": episode["program_sha256"],
                    "finite_survivors": episode["audit"]["finite_survivors"],
                }
            )

        default_program = program_for(DEFAULT_ROUTE_MARKER, root=root)
        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            observed = execute_rule(default_program, pair["input"], bridge=active)
            canonical_checks.append(observed == pair["output"])

        unique_inputs = {
            grid_sha256(pair["input"])
            for episode in episodes
            for pair in episode["train"] + episode["test"]
        }
        shortcut_refuted = sum(
            episode["audit"][name]["status"] == "refuted_by_demonstrations"
            for episode in episodes
            for name in ("corner_copy", "fixed_top_left_route")
        )
        report = {
            "schema": "arcpuzzles-parametric-route-marker-evidence-v1",
            "task_id": TASK_ID,
            "status": "proposed_unapproved",
            "approved": False,
            "parameter": {
                "name": "route_marker",
                "allowed_values": list(ALLOWED_ROUTE_MARKERS),
                "original_default": DEFAULT_ROUTE_MARKER,
                "selection_scope": "once_per_episode",
                "input_constraints_depend_on_parameter": False,
            },
            "request": {"seed": seed, "demos": demos, "queries": queries},
            "counts": {
                "episodes": len(episodes),
                "train_pairs": len(episodes) * demos,
                "query_pairs": len(episodes) * queries,
                "distinct_input_grids": len(unique_inputs),
                "settings_exercised": len(episodes),
                "ambiguous_parameter_rivals": sum(
                    bool(episode["ambiguities"]) for episode in episodes
                ),
                "shortcut_rivals_refuted": shortcut_refuted,
            },
            "canonical_default": {
                "program_sha256": hashlib.sha256(
                    default_program.encode("utf-8")
                ).hexdigest(),
                "pairs_checked": len(canonical_checks),
                "all_match": all(canonical_checks),
            },
            "sequential_dependency": {
                "step_a": "select the unique nearest/farthest marker by Manhattan distance to its corresponding collapsed-block cell",
                "intermediate": "selected quadrant, color, source coordinate, destination coordinate, and distance",
                "step_b": "paint the selected color along a vertical-then-horizontal route into that destination",
                "why_b_depends_on_a": "changing the selected marker changes the route's source, destination, color, and painted cells",
            },
            "racket": {
                key: active.runtime_identity[key]
                for key in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256", "bridge_sha256")
                if key in active.runtime_identity
            },
            "episodes": episode_rows,
            "limitations": [
                "bounded to the declared three settings and deterministic sampled seeds",
                "shortcut audit covers the retained outer-corner rival and a fixed-top-left route rival, not every conceivable learner",
                "prototype status does not imply training admission until native qualification and owner acceptance",
            ],
        }
        (temp / "report.json").write_bytes(_json_bytes(report))

        files = []
        for path in sorted(p for p in temp.rglob("*") if p.is_file()):
            relative = path.relative_to(temp).as_posix()
            files.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bytes": path.stat().st_size,
                }
            )
        manifest = {
            "schema": "arcpuzzles-parametric-evidence-manifest-v1",
            "task_id": TASK_ID,
            "files": files,
        }
        (temp / "manifest.json").write_bytes(_json_bytes(manifest))
        temp.rename(out)
        return report
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    finally:
        if owns_bridge:
            active.shutdown()


def main(argv=None, *, bridge: RacketBridge | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    parser.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(
        seed=args.seed,
        demos=args.demos,
        queries=args.queries,
        out=args.out,
        bridge=bridge,
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
