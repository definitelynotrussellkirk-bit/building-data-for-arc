#!/usr/bin/env python3
"""Proposed duplicate-key precedence variants for ARC task 83ca9df09514.

This task-local prototype does not change the approved production generator or
canonical Racket authority.  It varies only the traversal order used when two
nonzero key cells align to the same template color: the canonical rightmost key
wins, or an alternate leftmost key wins.  Every output is executed by Racket.
"""
from __future__ import annotations

import argparse
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

TASK_ID = "83ca9df09514"
VERSION = "proposed-duplicate-precedence-v1"
STATUS = "proposed_unapproved"
ALLOWED_PRECEDENCE = ("rightmost_wins", "leftmost_wins")
DEFAULT_PRECEDENCE = "rightmost_wins"
CANONICAL_RULE_HASH = "1dc6f00b70c9"
CANONICAL_SOURCE_SHA256 = "cae56e2f8161ccd2fd21aa8b0d4e0b51318d3e114e626ea9097fab7c2602af87"
CANONICAL_MAPPING_LOOP = "(for ((cc (range 0 w)))"
LEFTMOST_MAPPING_LOOP = "(for ((cc (reverse (range 0 w))))"
MIN_COUNT = 1
MAX_COUNT = 8


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _validate_setting(duplicate_precedence: Any) -> str:
    if (
        type(duplicate_precedence) is not str
        or duplicate_precedence not in ALLOWED_PRECEDENCE
    ):
        allowed = ", ".join(ALLOWED_PRECEDENCE)
        raise ValueError(f"duplicate_precedence must be one of: {allowed}")
    return duplicate_precedence


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(CANONICAL_MAPPING_LOOP) != 1:
        raise ValueError("pinned canonical source must contain one mapping loop")
    if LEFTMOST_MAPPING_LOOP in source:
        raise ValueError("pinned canonical source unexpectedly contains alternate loop")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Load and hash-check the single canonical Racket source for this task."""
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
    duplicate_precedence: str = DEFAULT_PRECEDENCE,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded duplicate-precedence setting."""
    setting = _validate_setting(duplicate_precedence)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if setting == DEFAULT_PRECEDENCE:
        return canonical
    return canonical.replace(CANONICAL_MAPPING_LOOP, LEFTMOST_MAPPING_LOOP, 1)


def rule_setting(source: Any, *, root: str | Path | None = None) -> str:
    """Recognize only the pinned canonical source or its guarded alternate."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return DEFAULT_PRECEDENCE
    alternate = canonical.replace(CANONICAL_MAPPING_LOOP, LEFTMOST_MAPPING_LOOP, 1)
    if source == alternate:
        return "leftmost_wins"
    raise ValueError("source is not a recognized duplicate-precedence rule")


def _rule_callable(source: str, *, root: str | Path | None = None) -> str:
    rule_setting(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


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
    literals = [_grid_literal(grid) for grid in normalized]
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
    """Execute one exact Racket rule over one normalized grid."""
    return execute_rule_many(source, [grid], bridge=bridge, root=root)[0]


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(f"{name} must be a literal integer in {MIN_COUNT}..{MAX_COUNT}")
    return value


def parameter_for_seed(seed: Any) -> dict[str, str]:
    """Choose one duplicate-precedence setting for the entire episode."""
    checked = _validate_seed(seed)
    return {
        "duplicate_precedence": ALLOWED_PRECEDENCE[
            checked % len(ALLOWED_PRECEDENCE)
        ]
    }


def _input_seed(block: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:inputs:{block}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _template_row(grid: list[list[int]]) -> int:
    counts = [sum(value != 0 for value in row) for row in grid]
    maximum = max(counts)
    if counts.count(maximum) != 1:
        raise ValueError("input must have one uniquely densest template row")
    row = counts.index(maximum)
    if maximum != len(grid[0]):
        raise ValueError("template row must occupy every column")
    return row


def _conflicting_key_rows(grid: list[list[int]]) -> list[int]:
    template_row = _template_row(grid)
    template = grid[template_row]
    conflicts: list[int] = []
    for row_index, row in enumerate(grid):
        if row_index == template_row or not any(row):
            continue
        grouped: dict[int, list[int]] = {}
        for column, value in enumerate(row):
            if value != 0:
                grouped.setdefault(template[column], []).append(value)
        if any(len(values) >= 2 and len(set(values)) >= 2 for values in grouped.values()):
            conflicts.append(row_index)
    return conflicts


def _inject_conflicts(grid: Any, *, salt: int) -> list[list[int]]:
    """Change one duplicate reveal per key row into a real precedence conflict."""
    output = [row[:] for row in normalize_grid(grid)]
    template_row = _template_row(output)
    template = output[template_row]
    key_rows = [
        row_index
        for row_index, row in enumerate(output)
        if row_index != template_row and any(row)
    ]
    if not key_rows:
        raise ValueError("prototype input must contain at least one sparse key row")

    for ordinal, row_index in enumerate(key_rows):
        row = output[row_index]
        grouped_columns: dict[int, list[int]] = {}
        for column, value in enumerate(row):
            if value != 0:
                grouped_columns.setdefault(template[column], []).append(column)
        repeated = [
            columns for columns in grouped_columns.values() if len(columns) >= 2
        ]
        if not repeated:
            raise ValueError(f"key row {row_index} has no duplicate template-group reveal")
        columns = min(repeated, key=lambda values: (values[0], values[-1]))
        left_column, right_column = min(columns), max(columns)
        left_value = row[left_column]
        used = {value for value in row if value != 0}
        start = (salt + row_index + ordinal) % 9
        replacement = None
        for offset in range(9):
            candidate = 1 + ((start + offset) % 9)
            if candidate != left_value and candidate not in used:
                replacement = candidate
                break
        if replacement is None:
            raise ValueError(f"cannot allocate a conflicting ARC color for row {row_index}")
        row[right_column] = replacement

    if set(_conflicting_key_rows(output)) != set(key_rows):
        raise ValueError("every nonblank sparse row must contain a true duplicate conflict")
    return output


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct paired inputs independently of the hidden setting.

    Consecutive seeds selecting opposite settings share the same inputs, so a
    bounded comparison isolates the rule change rather than the sampler.
    """
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)

    total = demos + queries
    input_block = checked_seed // len(ALLOWED_PRECEDENCE)
    bands = ("easy", "medium", "hard")
    positions = ("top", "middle", "bottom", "random")
    layouts = ("prefix", "shifted", "scattered")
    seen: set[str] = set()
    grids: list[list[list[int]]] = []

    for slot in range(total):
        for attempt in range(64):
            sample_index = slot + attempt * total
            base = generator.generate(
                _input_seed(input_block, slot, attempt),
                sample_index,
                difficulty=bands[slot % len(bands)],
                grid_h=6 + (slot % 7),
                grid_w=8 + (slot % 6),
                n_keys=1 + (slot % 4),
                n_groups=2 + (slot % 3),
                template_position=positions[slot % len(positions)],
                key_layout=layouts[slot % len(layouts)],
            )
            grid = _inject_conflicts(
                base,
                salt=(input_block * 131 + slot * 17 + attempt),
            )
            fingerprint = _grid_fingerprint(grid)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            grids.append(grid)
            break
        else:
            raise RuntimeError(
                f"could not construct a distinct conflict input for episode slot {slot}"
            )
    return grids


def _generate_episode_with_bridge(
    seed: int,
    demo_count: int,
    query_count: int,
    bridge: RacketBridge,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parameter = parameter_for_seed(seed)
    selected = parameter["duplicate_precedence"]
    grids = episode_inputs(
        seed,
        demo_count=demo_count,
        query_count=query_count,
        root=root,
    )
    programs = {
        setting: materialize_rule(setting, root=root)
        for setting in ALLOWED_PRECEDENCE
    }
    predictions = {
        setting: execute_rule_many(program, grids, bridge=bridge, root=root)
        for setting, program in programs.items()
    }
    selected_outputs = predictions[selected]

    train = [
        {"input": grids[index], "output": selected_outputs[index]}
        for index in range(demo_count)
    ]
    test = [
        {"input": grids[demo_count + index]}
        for index in range(query_count)
    ]
    public = {"train": train, "test": test}

    rival_checks: dict[str, Any] = {}
    for setting in ALLOWED_PRECEDENCE:
        demo_disagreements = [
            index
            for index in range(demo_count)
            if predictions[setting][index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if predictions[setting][demo_count + index]
            != selected_outputs[demo_count + index]
        ]
        rival_checks[setting] = {
            "matches_all_demonstrations": not demo_disagreements,
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "demonstration_predictions": predictions[setting][:demo_count],
            "query_predictions": predictions[setting][demo_count:],
        }

    survivors = [
        setting
        for setting in ALLOWED_PRECEDENCE
        if rival_checks[setting]["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(
            f"demonstrations do not identify duplicate_precedence: {survivors}"
        )
    unselected = next(setting for setting in ALLOWED_PRECEDENCE if setting != selected)
    if rival_checks[unselected]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified precedence setting")

    private = {
        "schema": "83ca9df09514-duplicate-precedence-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "parameter": parameter,
        "demo_count": demo_count,
        "query_count": query_count,
        "program_sha256": _sha256(programs[selected]),
        "input_sha256": [_grid_fingerprint(grid) for grid in grids],
        "query_answers": selected_outputs[demo_count:],
        "rival_checks": rival_checks,
        "surviving_settings_from_demonstrations": survivors,
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
    """Create one public-redacted/private-labeled episode under one setting."""
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _generate_episode_with_bridge(
                checked_seed, demos, queries, owned, root_path
            )
    return _generate_episode_with_bridge(
        checked_seed, demos, queries, bridge, root_path
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
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
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = find_root(__file__) if root is None else Path(root).resolve()

    public_dir = out_path / "public"
    episode_dir = out_path / "private" / "episodes"
    rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)

    programs = {
        setting: materialize_rule(setting, root=root_path)
        for setting in ALLOWED_PRECEDENCE
    }
    for setting, program in programs.items():
        (rule_dir / f"{setting}.rkt").write_text(program, encoding="utf-8")

    _, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    prototype_path = Path(__file__).resolve()
    episodes: list[dict[str, Any]] = []
    public_ids: set[str] = set()

    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_list:
            public, private = _generate_episode_with_bridge(
                seed, demos, queries, bridge, root_path
            )
            public_id = public_challenge_id(public)
            if public_id in public_ids:
                raise ValueError("different seeds produced the same visible public challenge")
            public_ids.add(public_id)
            private = {**private, "public_id": public_id}

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
                    "parameter": private["parameter"],
                }
            )

        episodes.sort(key=lambda row: row["public_id"])
        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        default_outputs = execute_rule_many(
            programs[DEFAULT_PRECEDENCE],
            [pair["input"] for pair in canonical],
            bridge=bridge,
            root=root_path,
        )
        canonical_checks = []
        for pair, actual in zip(canonical, default_outputs, strict=True):
            expected = pair["output"]
            if actual != expected:
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

        witness = episode_inputs(
            0, demo_count=1, query_count=1, root=root_path
        )[0]
        witness_outputs = {
            setting: execute_rule(
                program, witness, bridge=bridge, root=root_path
            )
            for setting, program in programs.items()
        }
        if witness_outputs["rightmost_wins"] == witness_outputs["leftmost_wins"]:
            raise ValueError("distinguishing witness does not separate settings")
        _write_json(
            out_path / "private" / "distinguishing-witness.json",
            {"input": witness, "outputs": witness_outputs},
        )

    manifest = {
        "schema": "83ca9df09514-duplicate-precedence-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": "duplicate_precedence",
            "allowed": list(ALLOWED_PRECEDENCE),
            "default": DEFAULT_PRECEDENCE,
        },
        "input_constraints": (
            "one uniquely dense template row; every nonblank sparse key row "
            "contains two conflicting reveals aligned to one template color"
        ),
        "demo_count": demos,
        "query_count": queries,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_default_unchanged": programs[DEFAULT_PRECEDENCE]
        == canonical_source(root=root_path),
        "programs": {
            setting: {
                "file": str((rule_dir / f"{setting}.rkt").relative_to(out_path)),
                "sha256": _sha256(program),
            }
            for setting, program in programs.items()
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
            "prototype only; production remains pinned to canonical rightmost precedence",
            "finite evidence covers only the materialized seeds and two declared settings",
            "identifiability is checked only against the opposite precedence setting",
            "input generation currently supports 1..8 demonstrations and 1..8 queries",
            "conflicting duplicate keys extend the production generator's accepted input grammar",
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
