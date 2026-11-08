#!/usr/bin/env python3
"""Proposed, unapproved crossing-mode variants for ARC task a2ad2da63297.

The production generator and canonical Racket authority remain unchanged.  The
canonical/default setting moves each matched opposite-side dot through the
barrier and lands it flush on the other side.  The alternate keeps the same
barrier discovery and lane matching, but compresses each dot flush on its
original side.  One setting is fixed for every demonstration and query in an
episode, and every retained label is executed by the bundled Racket runtime.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a2ad2da63297"
PARENT_FAMILY = "training:1efba499"
VERSION = "proposed-crossing-mode-v1"
STATUS = "proposed_unapproved"
ALLOWED_MODES = ("cross_through", "compress_to_barrier")
DEFAULT_MODE = "cross_through"
CANONICAL_RULE_HASH = "937e30cc1e90"
CANONICAL_SOURCE_SHA256 = (
    "937e30cc1e90881f7f01d4b05e8ec9bbb6a71432bfd75b8e7b744ccc9e2abf1c"
)
MIN_DEMO_COUNT = 2
MAX_DEMO_COUNT = 8
MIN_QUERY_COUNT = 1
MAX_QUERY_COUNT = 8

# Each tuple is canonical destination assignment -> same-side destination.
# All four anchors must occur exactly once before any alternate is materialized.
CROSS_DESTINATIONS = (
    (
        "(acc (set-cell acc (+ bot-bar 1) kc ca))",
        "(acc (set-cell acc (- top-bar 1) kc ca))",
    ),
    (
        "(acc (set-cell acc (- top-bar 1) kc cb))",
        "(acc (set-cell acc (+ bot-bar 1) kc cb))",
    ),
    (
        "(acc (set-cell acc kr (+ right-bar 1) cl))",
        "(acc (set-cell acc kr (- left-bar 1) cl))",
    ),
    (
        "(acc (set-cell acc kr (- left-bar 1) cr))",
        "(acc (set-cell acc kr (+ right-bar 1) cr))",
    ),
)


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any, lo: int, hi: int) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be a literal integer in {lo}..{hi}")
    return value


def _validate_mode(crossing_mode: Any) -> str:
    if type(crossing_mode) is not str or crossing_mode not in ALLOWED_MODES:
        raise ValueError(
            "crossing_mode must be one of: " + ", ".join(ALLOWED_MODES)
        )
    return crossing_mode


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    for canonical, alternate in CROSS_DESTINATIONS:
        if source.count(canonical) != 1:
            raise ValueError(
                "pinned canonical source must contain each crossing destination once"
            )
        if alternate in source:
            raise ValueError(
                "pinned canonical source unexpectedly contains same-side destination"
            )
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Load and hash-check the one canonical Racket source for this task."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    crossing_mode: str = DEFAULT_MODE,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded crossing-mode setting."""
    mode = _validate_mode(crossing_mode)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if mode == DEFAULT_MODE:
        return canonical
    variant = canonical
    for crossing, same_side in CROSS_DESTINATIONS:
        variant = variant.replace(crossing, same_side, 1)
    return variant


def rule_setting(source: Any, *, root: str | Path | None = None) -> str:
    """Recognize only the pinned canonical source or its guarded variant."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return DEFAULT_MODE
    variant = canonical
    for crossing, same_side in CROSS_DESTINATIONS:
        variant = variant.replace(crossing, same_side, 1)
    if source == variant:
        return "compress_to_barrier"
    raise ValueError("source is not the pinned canonical rule or crossing-mode variant")


def _rule_callable(source: str, *, root: str | Path | None = None) -> str:
    rule_setting(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Execute one exact Racket rule over all supplied grids in one request."""
    normalized = [normalize_grid(grid) for grid in grids]
    if not normalized:
        return []
    literals = [
        "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        for grid in normalized
    ]
    expression = f"(map {_rule_callable(source, root=root)} '({' '.join(literals)}))"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def parameter_for_seed(seed: Any) -> dict[str, str]:
    """Choose exactly one episode setting from a validated deterministic seed."""
    checked = _validate_seed(seed)
    return {"crossing_mode": ALLOWED_MODES[checked % len(ALLOWED_MODES)]}


def _input_seed(seed_group: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:inputs:{seed_group}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def python_prediction(grid: Any, crossing_mode: str = DEFAULT_MODE) -> list[list[int]]:
    """Independent parity mirror; retained labels still come only from Racket."""
    mode = _validate_mode(crossing_mode)
    source = normalize_grid(grid)
    height, width = len(source), len(source[0])
    counts: dict[int, int] = {}
    for row in source:
        for value in row:
            if value != 0:
                counts[value] = counts.get(value, 0) + 1
    if not counts:
        raise ValueError("grid has no non-background color")
    barrier = max(counts, key=counts.get)
    barrier_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == barrier
    ]
    row_min = min(row for row, _ in barrier_cells)
    row_max = max(row for row, _ in barrier_cells)
    col_min = min(col for _, col in barrier_cells)
    col_max = max(col for _, col in barrier_cells)
    horizontal = (col_max - col_min) > (row_max - row_min)
    output = deepcopy(source)

    if horizontal:
        for col in range(width):
            rows = [row for row, cell_col in barrier_cells if cell_col == col]
            if not rows:
                continue
            top, bottom = min(rows), max(rows)
            above = next(
                (
                    row
                    for row in range(height)
                    if row < top and source[row][col] not in (0, barrier)
                ),
                None,
            )
            below = next(
                (
                    row
                    for row in range(height)
                    if row > bottom and source[row][col] not in (0, barrier)
                ),
                None,
            )
            if above is None or below is None:
                continue
            above_color = source[above][col]
            below_color = source[below][col]
            output[above][col] = 0
            output[below][col] = 0
            if mode == "cross_through":
                output[bottom + 1][col] = above_color
                output[top - 1][col] = below_color
            else:
                output[top - 1][col] = above_color
                output[bottom + 1][col] = below_color
    else:
        for row in range(height):
            cols = [col for cell_row, col in barrier_cells if cell_row == row]
            if not cols:
                continue
            left, right = min(cols), max(cols)
            left_dot = next(
                (
                    col
                    for col in range(width)
                    if col < left and source[row][col] not in (0, barrier)
                ),
                None,
            )
            right_dot = next(
                (
                    col
                    for col in range(width)
                    if col > right and source[row][col] not in (0, barrier)
                ),
                None,
            )
            if left_dot is None or right_dot is None:
                continue
            left_color = source[row][left_dot]
            right_color = source[row][right_dot]
            output[row][left_dot] = 0
            output[row][right_dot] = 0
            if mode == "cross_through":
                output[row][right + 1] = left_color
                output[row][left - 1] = right_color
            else:
                output[row][left - 1] = left_color
                output[row][right + 1] = right_color
    return output


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> tuple[list[list[list[int]]], list[dict[str, Any]]]:
    """Draw distinct lawful inputs independently of the hidden rule setting.

    Adjacent seeds (0/1, 2/3, ...) share one input stream so a comparison of the
    two rule settings can hold every visible input constant.
    """
    checked_seed = _validate_seed(seed)
    demos = _validate_count(
        "demo_count", demo_count, MIN_DEMO_COUNT, MAX_DEMO_COUNT
    )
    queries = _validate_count(
        "query_count", query_count, MIN_QUERY_COUNT, MAX_QUERY_COUNT
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)

    total = demos + queries
    seed_group = checked_seed // len(ALLOWED_MODES)
    bands = ("easy", "medium", "hard")
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    roles: list[dict[str, Any]] = []
    for slot in range(total):
        orientation = "horizontal" if slot % 2 == 0 else "vertical"
        difficulty = bands[slot % len(bands)]
        for attempt in range(64):
            grid = normalize_grid(
                generator.generate(
                    _input_seed(seed_group, slot, attempt),
                    slot + attempt * total,
                    difficulty=difficulty,
                    texture=orientation,
                    pair_count=3,
                )
            )
            errors = generator.self_check(grid, difficulty=difficulty)
            fingerprint = _grid_fingerprint(grid)
            separates = python_prediction(grid, "cross_through") != python_prediction(
                grid, "compress_to_barrier"
            )
            if not errors and fingerprint not in seen and separates:
                seen.add(fingerprint)
                grids.append(grid)
                roles.append(
                    {
                        "slot": slot,
                        "split": "train" if slot < demos else "test",
                        "orientation": orientation,
                        "difficulty": difficulty,
                        "attempt": attempt,
                    }
                )
                break
        else:
            raise RuntimeError(
                f"could not draw distinct separating input for episode slot {slot}"
            )
    return grids, roles


def _generate_episode_with_bridge(
    seed: int,
    demo_count: int,
    query_count: int,
    bridge: RacketBridge,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parameter = parameter_for_seed(seed)
    selected = parameter["crossing_mode"]
    grids, roles = episode_inputs(
        seed, demo_count=demo_count, query_count=query_count, root=root
    )
    programs = {mode: materialize_rule(mode, root=root) for mode in ALLOWED_MODES}
    predictions = {
        mode: execute_rule_many(program, grids, bridge=bridge, root=root)
        for mode, program in programs.items()
    }
    parity = all(
        predictions[mode] == [python_prediction(grid, mode) for grid in grids]
        for mode in ALLOWED_MODES
    )
    if not parity:
        raise AssertionError("Racket/Python disagreement on sampled crossing-mode input")

    selected_outputs = predictions[selected]
    candidate_predictions = dict(predictions)
    candidate_predictions["identity"] = deepcopy(grids)
    train = [
        {"input": deepcopy(grids[index]), "output": deepcopy(selected_outputs[index])}
        for index in range(demo_count)
    ]
    test = [
        {"input": deepcopy(grids[demo_count + index])}
        for index in range(query_count)
    ]
    public = {"train": train, "test": test}

    rival_checks: dict[str, Any] = {}
    for name, outputs in candidate_predictions.items():
        demo_disagreements = [
            index
            for index in range(demo_count)
            if outputs[index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if outputs[demo_count + index] != selected_outputs[demo_count + index]
        ]
        rival_checks[name] = {
            "matches_all_demonstrations": not demo_disagreements,
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "demonstration_predictions": outputs[:demo_count],
            "query_predictions": outputs[demo_count:],
        }

    survivors = [
        name
        for name, check in rival_checks.items()
        if check["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify crossing_mode: {survivors}")
    rival = next(mode for mode in ALLOWED_MODES if mode != selected)
    if rival_checks[rival]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified crossing mode")

    public_id = public_challenge_id(public)
    private = {
        "schema": "a2ad2da63297-crossing-mode-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parent_family": PARENT_FAMILY,
        "version": VERSION,
        "public_id": public_id,
        "seed": seed,
        "input_seed_group": seed // len(ALLOWED_MODES),
        "parameter": parameter,
        "demo_count": demo_count,
        "query_count": query_count,
        "roles": roles,
        "program": programs[selected],
        "program_sha256": _sha256(programs[selected]),
        "input_sha256": [_grid_fingerprint(grid) for grid in grids],
        "query_answers": selected_outputs[demo_count:],
        "rival_checks": rival_checks,
        "surviving_candidates_from_demonstrations": survivors,
        "racket_python_parity": parity,
        "limitations": [
            "finite declared candidates: two crossing modes plus identity",
            "sampled inputs use the selected production generator's straight barriers",
            "prototype only; no production, source, variant, or training approval",
        ],
    }
    return public, private


def generate_episode(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one private-labeled/public-redacted episode under one setting."""
    checked_seed = _validate_seed(seed)
    demos = _validate_count(
        "demo_count", demo_count, MIN_DEMO_COUNT, MAX_DEMO_COUNT
    )
    queries = _validate_count(
        "query_count", query_count, MIN_QUERY_COUNT, MAX_QUERY_COUNT
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _generate_episode_with_bridge(
                checked_seed, demos, queries, owned, root_path
            )
    return _generate_episode_with_bridge(
        checked_seed, demos, queries, bridge, root_path
    )


def write_evidence(
    out: str | Path,
    *,
    seeds: Iterable[Any] = (0, 1),
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Materialize exact rules plus privacy-separated public/private evidence."""
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    seed_list = [_validate_seed(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("seeds must contain at least one episode seed")
    if len(seed_list) != len(set(seed_list)):
        raise ValueError("seeds must be distinct")
    demos = _validate_count(
        "demo_count", demo_count, MIN_DEMO_COUNT, MAX_DEMO_COUNT
    )
    queries = _validate_count(
        "query_count", query_count, MIN_QUERY_COUNT, MAX_QUERY_COUNT
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()

    public_dir = out_path / "public"
    episode_dir = out_path / "private" / "episodes"
    rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)

    programs = {mode: materialize_rule(mode, root=root_path) for mode in ALLOWED_MODES}
    for mode, program in programs.items():
        (rule_dir / f"{mode}.rkt").write_text(program, encoding="utf-8")

    _, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    prototype_path = Path(__file__).resolve()
    episodes: list[dict[str, Any]] = []
    public_ids: set[str] = set()

    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_list:
            public, private = _generate_episode_with_bridge(
                seed, demos, queries, bridge, root_path
            )
            public_id = private["public_id"]
            if public_id in public_ids:
                raise ValueError("different seeds produced the same visible public challenge")
            public_ids.add(public_id)
            public_path = public_dir / f"challenge-{public_id}.json"
            public_path.write_bytes(public_challenge_bytes(public))
            private_path = episode_dir / f"{public_id}.json"
            _write_json(private_path, private)
            episodes.append(
                {
                    "public_id": public_id,
                    "public_file": str(public_path.relative_to(out_path)),
                    "private_file": str(private_path.relative_to(out_path)),
                    "seed": seed,
                    "input_seed_group": private["input_seed_group"],
                    "parameter": private["parameter"],
                }
            )

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        default_outputs = execute_rule_many(
            programs[DEFAULT_MODE],
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=root_path,
        )
        canonical_checks = []
        for pair, actual in zip(canonical, default_outputs, strict=True):
            if actual != pair["output"]:
                raise ValueError(
                    "canonical default failed "
                    f"variant {pair['variant']} {pair['split']} pair {pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_fingerprint(pair["input"]),
                    "output_sha256": _grid_fingerprint(actual),
                    "matched": True,
                }
            )
        _write_json(
            out_path / "private" / "canonical-default-check.json",
            canonical_checks,
        )

        witness_inputs, _ = episode_inputs(
            0, demo_count=2, query_count=1, root=root_path
        )
        witness = witness_inputs[0]
        witness_outputs = {
            mode: execute_rule(program, witness, bridge=bridge, root=root_path)
            for mode, program in programs.items()
        }
        if witness_outputs[ALLOWED_MODES[0]] == witness_outputs[ALLOWED_MODES[1]]:
            raise ValueError("distinguishing witness does not separate crossing modes")
        _write_json(
            out_path / "private" / "distinguishing-witness.json",
            {"input": witness, "outputs": witness_outputs},
        )

    manifest = {
        "schema": "a2ad2da63297-crossing-mode-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "parent_family": PARENT_FAMILY,
        "version": VERSION,
        "parameter": {
            "name": "crossing_mode",
            "allowed": list(ALLOWED_MODES),
            "default": DEFAULT_MODE,
            "input_constraints_dependent": [],
        },
        "invariants": [
            "most-frequent non-background color remains the barrier",
            "opposite-side dots are matched by shared barrier lane",
            "only matched pairs move and land flush to the barrier",
            "orientation, grid size, palette and pair placement remain input variation",
        ],
        "demo_count": demos,
        "query_count": queries,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_default_unchanged": programs[DEFAULT_MODE]
        == canonical_source(root=root_path),
        "programs": {
            mode: {
                "file": str((rule_dir / f"{mode}.rkt").relative_to(out_path)),
                "sha256": _sha256(program),
            }
            for mode, program in programs.items()
        },
        "episodes": episodes,
        "selected_generator": {
            "file": str(generator_path.relative_to(root_path)),
            "sha256": generator_sha256,
        },
        "prototype": {
            "file": str(prototype_path.relative_to(root_path)),
            "sha256": _sha256(prototype_path.read_bytes()),
        },
        "racket_runtime": runtime_identity,
        "limitations": [
            "task-local proposed prototype; canonical generator and authority are unchanged",
            "evidence covers the retained seeds, two settings, and a finite rival set",
            "input sampler inherits the production generator's straight-barrier domain",
            "finite demonstrations do not prove uniqueness against arbitrary ARC programs",
        ],
    }
    _write_json(out_path / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=2)
    parser.add_argument("--query-count", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
