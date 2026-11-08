#!/usr/bin/env python3
"""Proposed, unapproved extension-length variants for ARC task b8e2a07c1b6c.

The approved production generator and canonical Racket authority remain fixed.
This task-local prototype changes only how many consecutive background cells
are recolored after the arrow's ray exits the orange rectangle: one cell
(canonical) or two cells (alternate).  One setting is fixed for an entire
episode, and every retained label and rival prediction is executed by Racket.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

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

TASK_ID = "b8e2a07c1b6c"
VERSION = "proposed-extension-length-v1"
STATUS = "proposed_unapproved"
PARAMETER = {
    "name": "extension_length",
    "allowed": (1, 2),
    "default": 1,
}
CANONICAL_RULE_HASH = "def70a52d143"
CANONICAL_SOURCE_SHA256 = (
    "7e6a7eb16a212d9b62fd6c9893ce27755d80db7cfb84bf7a75ef8af33f8f02e4"
)
MIN_DEMOS = 2
MAX_DEMOS = 8
MIN_QUERIES = 1
MAX_QUERIES = 8
MAX_TOTAL_SLOTS = MAX_DEMOS + MAX_QUERIES
MAX_INPUT_ATTEMPTS = 128

_DIRECTION_DELTAS = {
    "right": (0, 1),
    "left": (0, -1),
    "down": (1, 0),
    "up": (-1, 0),
    "down_right": (1, 1),
    "down_left": (1, -1),
    "up_right": (-1, 1),
    "up_left": (-1, -1),
}
_DELTA_DIRECTIONS = {delta: name for name, delta in _DIRECTION_DELTAS.items()}
_DIRECTION_CYCLE = tuple(_DIRECTION_DELTAS)

_CANONICAL_TERMINAL = "(set-cell grid r c 7)"
_EXTENSION_TWO_TERMINAL = """(let* ((one (set-cell grid r c 7))
                                 (r2 (+ r dr))
                                 (c2 (+ c dc)))
                            (if (or (< r2 0) (>= r2 h) (< c2 0) (>= c2 w))
                                one
                                (set-cell one r2 c2 7)))"""
_SECOND_ONLY_TERMINAL = """(let ((r2 (+ r dr))
                                (c2 (+ c dc)))
                            (if (or (< r2 0) (>= r2 h) (< c2 0) (>= c2 w))
                                grid
                                (set-cell grid r2 c2 7)))"""
_PAINT_TO_EDGE_TERMINAL = """(let paint ((pr r) (pc c) (painted grid))
                            (if (or (< pr 0) (>= pr h) (< pc 0) (>= pc w))
                                painted
                                (paint (+ pr dr)
                                       (+ pc dc)
                                       (set-cell painted pr pc 7))))"""


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if name == "demo_count":
        low, high = MIN_DEMOS, MAX_DEMOS
    elif name == "query_count":
        low, high = MIN_QUERIES, MAX_QUERIES
    else:  # Internal misuse should remain loud.
        raise ValueError(f"unknown count field: {name}")
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def _validate_extension_length(extension_length: Any) -> int:
    if type(extension_length) is not int or extension_length not in PARAMETER["allowed"]:
        raise ValueError("extension_length must be the literal integer 1 or 2")
    return extension_length


def _root(root: str | Path | None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(_CANONICAL_TERMINAL) != 1:
        raise ValueError("pinned canonical source must contain one terminal paint")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Load and hash-check the one distinct canonical Racket source."""
    root_path = _root(root)
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


def _replace_terminal(canonical: str, terminal: str) -> str:
    if canonical.count(_CANONICAL_TERMINAL) != 1:
        raise ValueError("pinned canonical source has an ambiguous terminal paint")
    return canonical.replace(_CANONICAL_TERMINAL, terminal, 1)


def materialize_rule(
    extension_length: Any = 1,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded extension-length setting."""
    setting = _validate_extension_length(extension_length)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if setting == 1:
        return canonical
    return _replace_terminal(canonical, _EXTENSION_TWO_TERMINAL)


def _rival_programs(*, root: str | Path | None = None) -> dict[str, str]:
    canonical = canonical_source(root=root)
    return {
        "extension_length_1": canonical,
        "extension_length_2": _replace_terminal(canonical, _EXTENSION_TWO_TERMINAL),
        "second_exterior_only": _replace_terminal(canonical, _SECOND_ONLY_TERMINAL),
        "paint_to_grid_edge": _replace_terminal(canonical, _PAINT_TO_EDGE_TERMINAL),
    }


def rule_setting(source: Any, *, root: str | Path | None = None) -> int:
    """Recognize only the pinned canonical source and its bounded length-2 variant."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    programs = _rival_programs(root=root)
    if source == programs["extension_length_1"]:
        return 1
    if source == programs["extension_length_2"]:
        return 2
    raise ValueError("source is not the pinned canonical rule or length-2 variant")


def _program_name(source: Any, *, root: str | Path | None = None) -> str:
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    matches = [
        name for name, program in _rival_programs(root=root).items() if source == program
    ]
    if len(matches) != 1:
        raise ValueError("source is not one of the four reviewed Racket programs")
    return matches[0]


def _rule_callable(source: str, *, root: str | Path | None = None) -> str:
    _program_name(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def _grid_literal(grid: Sequence[Sequence[int]]) -> str:
    return "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Execute one reviewed Racket rule over all grids in one protected request."""
    normalized = [normalize_grid(grid) for grid in grids]
    if not normalized:
        return []
    literals = [_grid_literal(grid) for grid in normalized]
    expression = f"(map {_rule_callable(source, root=root)} '({' '.join(literals)}))"
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    if type(result) is not list or len(result) != len(normalized):
        raise ValueError("Racket rule returned the wrong number of grids")
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def parameter_for_seed(seed: Any) -> dict[str, int]:
    """Choose one episode-fixed setting from a validated deterministic seed."""
    checked = _validate_seed(seed)
    return {"extension_length": PARAMETER["allowed"][checked % 2]}


def ray_facts(grid: Any) -> dict[str, Any]:
    """Recover the arrow direction and every in-grid cell after the body exit."""
    value = normalize_grid(grid)
    h, w = len(value), len(value[0])
    heads = [
        (r, c)
        for r, row in enumerate(value)
        for c, color in enumerate(row)
        if color == 2
    ]
    if len(heads) != 1:
        raise ValueError(f"expected exactly one red head, found {len(heads)}")
    hr, hc = heads[0]
    adjacent_tail: list[tuple[int, int]] = []
    for dr, dc in _DIRECTION_DELTAS.values():
        nr, nc = hr + dr, hc + dc
        if 0 <= nr < h and 0 <= nc < w and value[nr][nc] == 6:
            adjacent_tail.append((dr, dc))
    if len(adjacent_tail) != 1:
        raise ValueError(
            "head must have exactly one adjacent magenta tail cell; "
            f"found {len(adjacent_tail)}"
        )
    tail_dr, tail_dc = adjacent_tail[0]
    dr, dc = -tail_dr, -tail_dc
    direction = _DELTA_DIRECTIONS[(dr, dc)]

    r, c = hr + dr, hc + dc
    orange_run: list[tuple[int, int]] = []
    while 0 <= r < h and 0 <= c < w and value[r][c] == 7:
        orange_run.append((r, c))
        r += dr
        c += dc
    if not orange_run:
        raise ValueError("arrow ray must cross at least one orange cell")
    exterior_cells: list[tuple[int, int]] = []
    while 0 <= r < h and 0 <= c < w:
        exterior_cells.append((r, c))
        r += dr
        c += dc
    if not exterior_cells:
        raise ValueError("arrow ray exits the grid before an exterior target")
    return {
        "head": (hr, hc),
        "delta": (dr, dc),
        "direction": direction,
        "orange_run": orange_run,
        "exterior_cells": exterior_cells,
    }


def _input_seed(seed: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:input:{seed}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct lawful inputs without consulting the hidden setting.

    Each slot owns a fixed direction and retry schedule.  Neither the selected
    extension length nor the requested total count changes any earlier slot, so
    increasing the query count is a strict prefix extension.
    """
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = _root(root)
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)

    total = demos + queries
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    for slot in range(total):
        direction = _DIRECTION_CYCLE[slot % len(_DIRECTION_CYCLE)]
        # Vary dimensions/trail while retaining enough body span for diagonals.
        shape_h = 7 + (slot % 3)
        shape_w = 7 + ((slot // 3) % 3)
        trail_len = 2 + (slot % 3)
        for attempt in range(MAX_INPUT_ATTEMPTS):
            grid = generator.generate(
                _input_seed(checked_seed, slot, attempt),
                slot + attempt * MAX_TOTAL_SLOTS,
                difficulty=("easy", "medium", "hard")[slot % 3],
                grid_h=18,
                grid_w=18,
                shape_h=shape_h,
                shape_w=shape_w,
                trail_len=trail_len,
                arrow_direction=direction,
            )
            if generator.self_check(grid):
                continue
            facts = ray_facts(grid)
            if len(facts["exterior_cells"]) < 3:
                continue
            if any(
                grid[r][c] not in {5, 8, 9}
                for r, c in facts["exterior_cells"][:3]
            ):
                continue
            fingerprint = _grid_fingerprint(grid)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            grids.append(normalize_grid(grid))
            break
        else:
            raise RuntimeError(
                f"could not draw a distinct three-cell exterior witness for slot {slot}"
            )
    return grids


def _generate_episode_with_bridge(
    seed: int,
    demo_count: int,
    query_count: int,
    bridge: RacketBridge,
    root: Path,
    *,
    extension_length: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parameter = (
        parameter_for_seed(seed)
        if extension_length is None
        else {"extension_length": _validate_extension_length(extension_length)}
    )
    selected = parameter["extension_length"]
    grids = episode_inputs(
        seed,
        demo_count=demo_count,
        query_count=query_count,
        root=root,
    )
    programs = _rival_programs(root=root)
    predictions = {
        name: execute_rule_many(program, grids, bridge=bridge, root=root)
        for name, program in programs.items()
    }
    selected_name = f"extension_length_{selected}"
    selected_outputs = predictions[selected_name]

    public = {
        "train": [
            {"input": grids[index], "output": selected_outputs[index]}
            for index in range(demo_count)
        ],
        "test": [
            {"input": grids[demo_count + index]}
            for index in range(query_count)
        ],
    }
    rival_checks: dict[str, Any] = {}
    for name, outputs in predictions.items():
        demo_disagreements = [
            index
            for index in range(demo_count)
            if outputs[index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if outputs[demo_count + index]
            != selected_outputs[demo_count + index]
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
    if survivors != [selected_name]:
        raise ValueError(
            "demonstrations do not uniquely identify extension_length: "
            f"{survivors}"
        )
    expected_demo_disagreements = list(range(demo_count))
    expected_query_disagreements = list(range(query_count))
    for name, check in rival_checks.items():
        if name == selected_name:
            continue
        if check["demonstration_disagreements"] != expected_demo_disagreements:
            raise ValueError(f"rival {name} survives at least one demonstration")
        if check["query_disagreements"] != expected_query_disagreements:
            raise ValueError(f"query set does not require the selected rule against {name}")

    public_id = public_challenge_id(public)
    selected_program = programs[selected_name]
    private = {
        "schema": "b8e2a07c1b6c-extension-length-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "public_id": public_id,
        "seed": seed,
        "parameter": parameter,
        "parameter_draw_count": 1,
        "demo_count": demo_count,
        "query_count": query_count,
        "program_sha256": _sha256(selected_program),
        "input_sha256": [_grid_fingerprint(grid) for grid in grids],
        "query_answers": selected_outputs[demo_count:],
        "rival_checks": rival_checks,
        "surviving_rivals_from_demonstrations": survivors,
        "racket_runtime": bridge.runtime_identity,
    }
    return public, private


def generate_episode(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
    extension_length: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one private-labeled/public-redacted episode under one fixed rule."""
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    selected = (
        None
        if extension_length is None
        else _validate_extension_length(extension_length)
    )
    root_path = _root(root)
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _generate_episode_with_bridge(
                checked_seed,
                demos,
                queries,
                owned,
                root_path,
                extension_length=selected,
            )
    return _generate_episode_with_bridge(
        checked_seed,
        demos,
        queries,
        bridge,
        root_path,
        extension_length=selected,
    )


def _preflight_batch(
    episodes: Iterable[tuple[dict[str, Any], dict[str, Any]]],
) -> list[tuple[dict[str, Any], dict[str, Any], str]]:
    materialized = list(episodes)
    if not materialized:
        raise ValueError("episodes must contain at least one public/private pair")
    checked: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    seen: set[str] = set()
    for index, item in enumerate(materialized):
        if type(item) not in {tuple, list} or len(item) != 2:
            raise ValueError(f"episode {index} must be one public/private pair")
        public, private = item
        if type(public) is not dict or type(private) is not dict:
            raise ValueError(f"episode {index} must contain dictionaries")
        public_id = public_challenge_id(public)
        if public_id in seen:
            raise ValueError(f"duplicate visible public challenge: {public_id}")
        seen.add(public_id)
        if private.get("public_id") != public_id:
            raise ValueError(f"episode {index} private public_id does not match visible bytes")
        checked.append((public, private, public_id))
    return checked


def write_batch(
    episodes: Iterable[tuple[dict[str, Any], dict[str, Any]]],
    out: str | Path,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Write a pre-generated batch only after duplicate/privacy preflight passes."""
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    checked = _preflight_batch(episodes)
    root_path = _root(root)
    programs = _rival_programs(root=root_path)

    public_dir = out_path / "public"
    episode_dir = out_path / "private" / "episodes"
    rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)

    for length in PARAMETER["allowed"]:
        (rule_dir / f"extension-length-{length}.rkt").write_text(
            materialize_rule(length, root=root_path), encoding="utf-8"
        )
    (rule_dir / "second-exterior-only.rkt").write_text(
        programs["second_exterior_only"], encoding="utf-8"
    )
    (rule_dir / "paint-to-grid-edge.rkt").write_text(
        programs["paint_to_grid_edge"], encoding="utf-8"
    )

    rows: list[dict[str, Any]] = []
    for public, private, public_id in checked:
        public_path = public_dir / f"{public_id}.json"
        private_path = episode_dir / f"{public_id}.json"
        public_path.write_bytes(public_challenge_bytes(public))
        _write_json(private_path, private)
        rows.append(
            {
                "public_id": public_id,
                "public_file": str(public_path.relative_to(out_path)),
                "private_file": str(private_path.relative_to(out_path)),
                "seed": private.get("seed"),
                "parameter": private.get("parameter"),
            }
        )

    public_ids = sorted(row["public_id"] for row in rows)
    manifest = {
        "schema": "b8e2a07c1b6c-extension-length-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": PARAMETER["name"],
            "allowed": list(PARAMETER["allowed"]),
            "default": PARAMETER["default"],
        },
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_default_unchanged": materialize_rule(1, root=root_path)
        == canonical_source(root=root_path),
        "demo_count": checked[0][1].get("demo_count"),
        "query_count": checked[0][1].get("query_count"),
        "public_ids": public_ids,
        "episodes": sorted(rows, key=lambda row: row["public_id"]),
        "programs": {
            name: {
                "sha256": _sha256(program),
                "file": (
                    f"private/rules/extension-length-{name.rsplit('_', 1)[1]}.rkt"
                    if name.startswith("extension_length_")
                    else f"private/rules/{name.replace('_', '-')}.rkt"
                ),
            }
            for name, program in programs.items()
        },
        "limitations": [
            "prototype only; production remains pinned to extension_length=1",
            "finite evidence covers only the materialized seeds and four declared rivals",
            "input generation supports 2..8 demonstrations and 1..8 queries",
        ],
    }
    _write_json(out_path / "manifest.json", manifest)
    return manifest


def write_evidence(
    out: str | Path,
    *,
    seeds: Iterable[Any] = (0, 1),
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Materialize rules plus privacy-separated public/private Racket evidence."""
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    seed_list = [_validate_seed(seed) for seed in seeds]
    if not seed_list:
        raise ValueError("seeds must contain at least one episode seed")
    if len(seed_list) != len(set(seed_list)):
        raise ValueError("seeds must be distinct")
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = _root(root)

    episodes: list[tuple[dict[str, Any], dict[str, Any]]] = []
    canonical_checks: list[dict[str, Any]] = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for seed in seed_list:
            episodes.append(
                _generate_episode_with_bridge(
                    seed, demos, queries, bridge, root_path
                )
            )

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        default_outputs = execute_rule_many(
            materialize_rule(1, root=root_path),
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=root_path,
        )
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
        runtime_identity = bridge.runtime_identity

    manifest = write_batch(episodes, out_path, root=root_path)
    _write_json(
        out_path / "private" / "canonical-default-check.json", canonical_checks
    )
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    del generator
    prototype_path = Path(__file__).resolve()
    manifest.update(
        {
            "selected_generator": {
                "file": str(generator_path.relative_to(root_path)),
                "sha256": generator_sha256,
            },
            "prototype": {
                "file": str(prototype_path.relative_to(root_path)),
                "sha256": _sha256(prototype_path.read_bytes()),
            },
            "canonical_replay_pairs": len(canonical_checks),
            "racket_runtime": runtime_identity,
        }
    )
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
