#!/usr/bin/env python3
"""Proposed, unapproved overlap-precedence variants for ARC task 0ae119475d57.

The approved production generator and canonical Racket authority remain fixed.
This task-local prototype changes only which aligned panel wins when both cells
are nonzero: the lower panel (canonical) or the upper panel (alternate).  One
setting is chosen per episode, and every retained label is executed by Racket.
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

TASK_ID = "0ae119475d57"
VERSION = "proposed-overlap-precedence-v1"
STATUS = "proposed_unapproved"
ALLOWED_PRECEDENCE = ("lower_wins", "upper_wins")
DEFAULT_PRECEDENCE = "lower_wins"
CANONICAL_RULE_HASH = "c286c869b037"
CANONICAL_SOURCE_SHA256 = "d9187ff88e80c4f19b71b0b33eb220d5115aa0703e2b675c9ceeb1a532d0bdd1"
CANONICAL_BRANCH = "(if (!= bot 0) bot top)"
UPPER_BRANCH = "(if (!= top 0) top bot)"
MIN_COUNT = 1
MAX_COUNT = 8


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
    if type(value) is not int or not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(f"{name} must be a literal integer in {MIN_COUNT}..{MAX_COUNT}")
    return value


def _validate_setting(overlap_precedence: Any) -> str:
    if (
        type(overlap_precedence) is not str
        or overlap_precedence not in ALLOWED_PRECEDENCE
    ):
        allowed = ", ".join(ALLOWED_PRECEDENCE)
        raise ValueError(f"overlap_precedence must be one of: {allowed}")
    return overlap_precedence


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(CANONICAL_BRANCH) != 1:
        raise ValueError("pinned canonical source must contain one lower-precedence branch")
    if UPPER_BRANCH in source:
        raise ValueError("pinned canonical source unexpectedly contains alternate branch")
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
    overlap_precedence: str = DEFAULT_PRECEDENCE,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded precedence setting."""
    setting = _validate_setting(overlap_precedence)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if setting == DEFAULT_PRECEDENCE:
        return canonical
    return canonical.replace(CANONICAL_BRANCH, UPPER_BRANCH, 1)


def rule_setting(source: Any, *, root: str | Path | None = None) -> str:
    """Recognize only the pinned canonical source or its one guarded variant."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return DEFAULT_PRECEDENCE
    if source == canonical.replace(CANONICAL_BRANCH, UPPER_BRANCH, 1):
        return "upper_wins"
    raise ValueError("source is not the pinned canonical rule or precedence variant")


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
    return {"overlap_precedence": ALLOWED_PRECEDENCE[checked % len(ALLOWED_PRECEDENCE)]}


def _input_seed(seed: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:{seed}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 2,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct lawful inputs independently of the hidden rule setting."""
    checked_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)

    total = demos + queries
    bands = ("easy", "medium", "hard")
    seen: set[str] = set()
    grids: list[list[list[int]]] = []
    for slot in range(total):
        for attempt in range(64):
            grid = generator.generate(
                _input_seed(checked_seed, slot, attempt),
                slot + attempt * total,
                difficulty=bands[slot % len(bands)],
            )
            fingerprint = _grid_fingerprint(grid)
            overlap = generator.SEMANTIC_WITNESSES["true_overlap_lower_wins"](grid)
            if fingerprint not in seen and overlap:
                seen.add(fingerprint)
                grids.append(normalize_grid(grid))
                break
        else:
            raise RuntimeError(
                f"could not draw a distinct overlap witness for episode slot {slot}"
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
    selected = parameter["overlap_precedence"]
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
            f"demonstrations do not identify overlap_precedence: {survivors}"
        )
    unselected = next(setting for setting in ALLOWED_PRECEDENCE if setting != selected)
    if rival_checks[unselected]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified precedence setting")

    public_id = public_challenge_id(public)
    private = {
        "schema": "0ae119475d57-overlap-precedence-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "public_id": public_id,
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
    """Create one private-labeled/public-redacted episode under one setting."""
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

    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    del generator
    prototype_path = Path(__file__).resolve()
    episodes: list[dict[str, Any]] = []
    public_ids: set[str] = set()
    buffered: list[tuple[str, bytes, dict[str, Any], int]] = []

    with RacketBridge(max_calls_before_restart=128) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seed_list:
            public, private = _generate_episode_with_bridge(
                seed, demos, queries, bridge, root_path
            )
            public_id = private["public_id"]
            if public_id in public_ids:
                raise ValueError("different seeds produced the same visible public challenge")
            public_ids.add(public_id)
            buffered.append((public_id, public_challenge_bytes(public), private, seed))

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
            out_path / "private" / "canonical-default-check.json", canonical_checks
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
        if witness_outputs["lower_wins"] == witness_outputs["upper_wins"]:
            raise ValueError("distinguishing witness does not separate precedence settings")
        _write_json(
            out_path / "private" / "distinguishing-witness.json",
            {"input": witness, "outputs": witness_outputs},
        )

    # Publish only after the complete batch has executed. Public write order and
    # the private association index follow visible-content IDs, never seed order.
    for public_id, payload, private, seed in sorted(buffered, key=lambda row: row[0]):
        public_path = public_dir / f"challenge-{public_id}.json"
        public_path.write_bytes(payload)
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

    manifest = {
        "schema": "0ae119475d57-overlap-precedence-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": "overlap_precedence",
            "allowed": list(ALLOWED_PRECEDENCE),
            "default": DEFAULT_PRECEDENCE,
        },
        "input_constraints": (
            "unchanged 5+1+5 aligned panels; every authored input contains a "
            "true overlap plus top-only, bottom-only and blank positions"
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
            "prototype only; production remains pinned to canonical lower precedence",
            "finite evidence covers only the materialized seeds and two declared settings",
            "identifiability is checked only against the opposite precedence setting",
            "input generation currently supports 1..8 demonstrations and 1..8 queries",
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
