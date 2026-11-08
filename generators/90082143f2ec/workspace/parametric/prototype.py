#!/usr/bin/env python3
"""Proposed, unapproved outlier-action variants for ARC task 90082143f2ec.

The approved production generator and canonical Racket authority remain fixed.
Both settings recover row/column modes, compare coherence, and choose the more
coherent axis.  ``restore_mode`` is the exact canonical rule; ``mask_zero``
keeps cells agreeing with the selected line mode and replaces outliers by 0.
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

TASK_ID = "90082143f2ec"
VERSION = "proposed-outlier-action-v1"
STATUS = "proposed_unapproved"
ALLOWED_ACTIONS = ("restore_mode", "mask_zero")
DEFAULT_ACTION = "restore_mode"
CANONICAL_RULE_HASH = "a86d1f36d1d2"
CANONICAL_SOURCE_SHA256 = "fce27c64e390c476ffe769e59766ad1fd179890f28233bf99a5c8176623b83e5"
CANONICAL_COL_ACTION = "(cellmap g (r c v) (list-ref col-modes c))"
CANONICAL_ROW_ACTION = "(cellmap g (r c v) (list-ref row-modes r))"
MIN_COUNT = 1
MAX_COUNT = 8
MASK_COL_ACTION = "(cellmap g (r c v) (if (= v (list-ref col-modes c)) v 0))"
MASK_ROW_ACTION = "(cellmap g (r c v) (if (= v (list-ref row-modes r)) v 0))"


def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_action(outlier_action: Any) -> str:
    if type(outlier_action) is not str or outlier_action not in ALLOWED_ACTIONS:
        allowed = ", ".join(ALLOWED_ACTIONS)
        raise ValueError(f"outlier_action must be one of: {allowed}")
    return outlier_action


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(CANONICAL_COL_ACTION) != 1 or source.count(CANONICAL_ROW_ACTION) != 1:
        raise ValueError("pinned canonical source must contain one action per axis")
    if MASK_COL_ACTION in source or MASK_ROW_ACTION in source:
        raise ValueError("pinned canonical source unexpectedly contains mask-zero actions")
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
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    outlier_action: str = DEFAULT_ACTION,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded outlier action."""
    action = _validate_action(outlier_action)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if action == DEFAULT_ACTION:
        return canonical
    return canonical.replace(CANONICAL_COL_ACTION, MASK_COL_ACTION, 1).replace(
        CANONICAL_ROW_ACTION, MASK_ROW_ACTION, 1
    )


def rule_setting(source: Any, *, root: str | Path | None = None) -> str:
    """Recognize only the pinned canonical source or its two-branch variant."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return DEFAULT_ACTION
    alternate = canonical.replace(CANONICAL_COL_ACTION, MASK_COL_ACTION, 1).replace(
        CANONICAL_ROW_ACTION, MASK_ROW_ACTION, 1
    )
    if source == alternate:
        return "mask_zero"
    raise ValueError("source is not the pinned canonical rule or outlier-action variant")


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
        with RacketBridge(max_calls_before_restart=128) as owned:
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
    return {"outlier_action": ALLOWED_ACTIONS[checked % len(ALLOWED_ACTIONS)]}



def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(f"{name} must be a literal integer in {MIN_COUNT}..{MAX_COUNT}")
    return value


def _input_seed(paired_seed: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:input:{paired_seed}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 3,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct lawful inputs independently of the hidden action setting.

    Consecutive seeds are paired: ``2k`` and ``2k+1`` select different rule
    settings but reuse the same input seeds and schedule positions.
    """
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)

    paired_seed = checked_seed // len(ALLOWED_ACTIONS)
    total = demos + queries
    period = int(getattr(generator, "LESSON_SCHEDULE_PERIOD", 1))
    start_index = (paired_seed * total) % max(1, period)
    bands = ("easy", "medium", "hard")
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    for slot in range(total):
        for attempt in range(64):
            grid = generator.generate(
                _input_seed(paired_seed, slot, attempt),
                start_index + slot,
                difficulty=bands[slot % len(bands)],
            )
            if generator.self_check(grid):
                continue
            facts = generator.semantic_observables(grid)
            fingerprint = _grid_fingerprint(grid)
            if facts["noise_count"] > 0 and fingerprint not in seen:
                seen.add(fingerprint)
                grids.append(normalize_grid(grid))
                break
        else:
            raise RuntimeError(f"could not draw a distinct noisy-band input for slot {slot}")
    return grids


def _generate_episode_with_bridge(
    seed: int,
    demo_count: int,
    query_count: int,
    bridge: RacketBridge,
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    parameter = parameter_for_seed(seed)
    selected = parameter["outlier_action"]
    grids = episode_inputs(
        seed,
        demo_count=demo_count,
        query_count=query_count,
        root=root,
    )
    programs = {action: materialize_rule(action, root=root) for action in ALLOWED_ACTIONS}
    predictions = {
        action: execute_rule_many(program, grids, bridge=bridge, root=root)
        for action, program in programs.items()
    }
    selected_outputs = predictions[selected]

    if any(
        predictions[ALLOWED_ACTIONS[0]][index] == predictions[ALLOWED_ACTIONS[1]][index]
        for index in range(len(grids))
    ):
        raise ValueError("at least one retained input does not distinguish outlier_action")

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
    for action in ALLOWED_ACTIONS:
        demo_disagreements = [
            index
            for index in range(demo_count)
            if predictions[action][index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if predictions[action][demo_count + index]
            != selected_outputs[demo_count + index]
        ]
        rival_checks[action] = {
            "matches_all_demonstrations": not demo_disagreements,
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "demonstration_predictions": predictions[action][:demo_count],
            "query_predictions": predictions[action][demo_count:],
        }

    survivors = [
        action
        for action in ALLOWED_ACTIONS
        if rival_checks[action]["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify outlier_action: {survivors}")
    unselected = next(action for action in ALLOWED_ACTIONS if action != selected)
    if rival_checks[unselected]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified outlier action")

    public_id = public_challenge_id(public)
    private = {
        "schema": "90082143f2ec-outlier-action-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "public_id": public_id,
        "seed": seed,
        "paired_input_key": seed // len(ALLOWED_ACTIONS),
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
    demo_count: Any = 3,
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
    return _generate_episode_with_bridge(checked_seed, demos, queries, bridge, root_path)


def write_evidence(
    out: str | Path,
    *,
    seeds: Iterable[Any] = (0, 1),
    demo_count: Any = 3,
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
    programs = {action: materialize_rule(action, root=root_path) for action in ALLOWED_ACTIONS}
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    del generator

    records: list[dict[str, Any]] = []
    canonical_checks: list[dict[str, Any]] = []
    runtime_identity: Any
    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_list:
            public, private = _generate_episode_with_bridge(
                seed, demos, queries, bridge, root_path
            )
            records.append({"public": public, "private": private})

        public_ids = [row["private"]["public_id"] for row in records]
        if len(public_ids) != len(set(public_ids)):
            raise ValueError("different seeds produced the same visible public challenge")

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        default_outputs = execute_rule_many(
            programs[DEFAULT_ACTION],
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

    records.sort(key=lambda row: row["private"]["public_id"])
    public_dir = out_path / "public"
    episode_dir = out_path / "private" / "episodes"
    rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)

    for action, program in programs.items():
        (rule_dir / f"{action}.rkt").write_text(program, encoding="utf-8")

    episodes: list[dict[str, Any]] = []
    for row in records:
        public = row["public"]
        private = row["private"]
        public_id = private["public_id"]
        public_path = public_dir / f"challenge-{public_id}.json"
        private_path = episode_dir / f"{public_id}.json"
        public_path.write_bytes(public_challenge_bytes(public))
        _write_json(private_path, private)
        episodes.append(
            {
                "public_id": public_id,
                "public_file": str(public_path.relative_to(out_path)),
                "private_file": str(private_path.relative_to(out_path)),
                "seed": private["seed"],
                "paired_input_key": private["paired_input_key"],
                "parameter": private["parameter"],
            }
        )

    _write_json(out_path / "private" / "canonical-default-check.json", canonical_checks)
    first_public = records[0]["public"]
    first_private = records[0]["private"]
    witness_input = first_public["train"][0]["input"]
    _write_json(
        out_path / "private" / "distinguishing-witness.json",
        {
            "input": witness_input,
            "outputs": {
                action: first_private["rival_checks"][action][
                    "demonstration_predictions"
                ][0]
                for action in ALLOWED_ACTIONS
            },
        },
    )

    prototype_path = Path(__file__).resolve()
    manifest = {
        "schema": "90082143f2ec-outlier-action-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": "outlier_action",
            "allowed": list(ALLOWED_ACTIONS),
            "default": DEFAULT_ACTION,
        },
        "invariant_reasoning": (
            "both settings compute row/column modes, compare coherence, choose the "
            "more coherent axis, and classify each cell against that axis mode"
        ),
        "demo_count": demos,
        "query_count": queries,
        "paired_seed_policy": "seeds 2k and 2k+1 share all visible input grids",
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_default_unchanged": programs[DEFAULT_ACTION]
        == canonical_source(root=root_path),
        "programs": {
            action: {
                "file": str((rule_dir / f"{action}.rkt").relative_to(out_path)),
                "sha256": _sha256(program),
            }
            for action, program in programs.items()
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
            "prototype only; production remains pinned to canonical restore_mode",
            "finite evidence covers only the materialized seeds and two declared settings",
            "identifiability is checked only against the opposite outlier_action setting",
            "input generation supports 1..8 demonstrations and 1..8 queries",
        ],
    }
    _write_json(out_path / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=3)
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
