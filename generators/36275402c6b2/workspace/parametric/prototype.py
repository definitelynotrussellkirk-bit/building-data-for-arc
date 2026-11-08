#!/usr/bin/env python3
"""Proposed, unapproved border-policy variants for ARC task 36275402c6b2.

The selected production generator and canonical Racket authority remain fixed.
This task-local prototype varies only whether source-colour cells on the crop
border are recoloured (canonical) or preserved. One policy is fixed for every
pair in an episode, and every retained label is executed by Racket.
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

TASK_ID = "36275402c6b2"
VERSION = "proposed-border-policy-v1"
STATUS = "proposed_unapproved"
ALLOWED_POLICIES = ("recolour", "preserve")
DEFAULT_POLICY = "recolour"
CANONICAL_RULE_HASH = "08894540e7f2"
CANONICAL_SOURCE_SHA256 = "a806f83cdfb3f7831cfe4c189fee46cdc90677706f05b67cb617dafc2b080f86"
CANONICAL_BRANCH = "(if mapping (first mapping) v)"
PRESERVE_BRANCH = (
    "(if (and mapping (> r 0) (< r (- rect-h 1)) "
    "(> c 0) (< c (- rect-w 1))) (first mapping) v)"
)
MIN_COUNT = 1
MAX_COUNT = 8
MIN_SEED = -(2**63)
MAX_SEED = 2**63 - 1
SIDE_ORDER = ("top", "bottom", "left", "right")
MAX_INPUT_ATTEMPTS = 64


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
    if type(seed) is not int or not MIN_SEED <= seed <= MAX_SEED:
        raise ValueError(
            f"seed must be a literal signed integer in {MIN_SEED}..{MAX_SEED}"
        )
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(f"{name} must be a literal integer in {MIN_COUNT}..{MAX_COUNT}")
    return value


def _validate_policy(border_policy: Any) -> str:
    if type(border_policy) is not str or border_policy not in ALLOWED_POLICIES:
        allowed = ", ".join(ALLOWED_POLICIES)
        raise ValueError(f"border_policy must be one of: {allowed}")
    return border_policy


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(CANONICAL_BRANCH) != 1:
        raise ValueError("pinned canonical source must contain one recolouring branch")
    if PRESERVE_BRANCH in source:
        raise ValueError("pinned canonical source unexpectedly contains preserve branch")
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
    border_policy: str = DEFAULT_POLICY,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one bounded border policy."""
    policy = _validate_policy(border_policy)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if policy == DEFAULT_POLICY:
        return canonical
    return canonical.replace(CANONICAL_BRANCH, PRESERVE_BRANCH, 1)


def rule_setting(source: Any, *, root: str | Path | None = None) -> str:
    """Recognize only the pinned canonical source or its guarded variant."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    canonical = canonical_source(root=root)
    if source == canonical:
        return DEFAULT_POLICY
    if source == canonical.replace(CANONICAL_BRANCH, PRESERVE_BRANCH, 1):
        return "preserve"
    raise ValueError("source is not the pinned canonical rule or border-policy variant")


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
    """Choose exactly one episode policy while preserving signed seed support."""
    checked = _validate_seed(seed)
    return {"border_policy": ALLOWED_POLICIES[checked & 1]}


def _input_pair_key(seed: int) -> int:
    """Map consecutive even/odd signed seeds to one shared input family."""
    return seed // 2


def _input_seed(seed: int, slot: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:{_input_pair_key(seed)}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") % (2**63)


def _grid_fingerprint(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _border_source_side(generator: Any, grid: Any) -> str:
    analysis = generator._analysis_or_raise(grid)
    crop = analysis["crop"]
    sources = set(analysis["sources"])
    hits: list[str] = []
    height, width = len(crop), len(crop[0])
    for row, values in enumerate(crop):
        for col, value in enumerate(values):
            if value not in sources:
                continue
            if row == 0:
                hits.append("top")
            if row == height - 1:
                hits.append("bottom")
            if col == 0:
                hits.append("left")
            if col == width - 1:
                hits.append("right")
    unique = sorted(set(hits))
    if len(unique) != 1:
        raise ValueError(f"expected exactly one noncorner border-source side, got {unique}")
    return unique[0]


def episode_inputs(
    seed: Any,
    *,
    demo_count: Any = 3,
    query_count: Any = 4,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw paired, distinct odd-profile inputs covering all four crop sides."""
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
        required_side = SIDE_ORDER[slot % len(SIDE_ORDER)]
        for attempt in range(MAX_INPUT_ATTEMPTS):
            sample_index = 2 * (slot + attempt * total) + 1
            grid = generator.generate(
                _input_seed(checked_seed, slot, attempt),
                sample_index,
                difficulty=bands[slot % len(bands)],
            )
            fingerprint = _grid_fingerprint(grid)
            if fingerprint in seen:
                continue
            if _border_source_side(generator, grid) != required_side:
                continue
            seen.add(fingerprint)
            grids.append(normalize_grid(grid))
            break
        else:
            raise RuntimeError(
                "could not draw a distinct border-source witness "
                f"for episode slot {slot} on side {required_side}"
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
    selected = parameter["border_policy"]
    grids = episode_inputs(
        seed,
        demo_count=demo_count,
        query_count=query_count,
        root=root,
    )
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    border_sides = [_border_source_side(generator, grid) for grid in grids]
    programs = {
        policy: materialize_rule(policy, root=root) for policy in ALLOWED_POLICIES
    }
    predictions = {
        policy: execute_rule_many(program, grids, bridge=bridge, root=root)
        for policy, program in programs.items()
    }
    selected_outputs = predictions[selected]

    public = {
        "train": [
            {"input": grids[index], "output": selected_outputs[index]}
            for index in range(demo_count)
        ],
        "test": [
            {"input": grids[demo_count + index]} for index in range(query_count)
        ],
    }

    rival_checks: dict[str, Any] = {}
    for policy in ALLOWED_POLICIES:
        demo_disagreements = [
            index
            for index in range(demo_count)
            if predictions[policy][index] != selected_outputs[index]
        ]
        query_disagreements = [
            index
            for index in range(query_count)
            if predictions[policy][demo_count + index]
            != selected_outputs[demo_count + index]
        ]
        rival_checks[policy] = {
            "matches_all_demonstrations": not demo_disagreements,
            "demonstration_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "demonstration_predictions": predictions[policy][:demo_count],
            "query_predictions": predictions[policy][demo_count:],
        }

    survivors = [
        policy
        for policy in ALLOWED_POLICIES
        if rival_checks[policy]["matches_all_demonstrations"]
    ]
    if survivors != [selected]:
        raise ValueError(f"demonstrations do not identify border_policy: {survivors}")
    rival = next(policy for policy in ALLOWED_POLICIES if policy != selected)
    if rival_checks[rival]["query_disagreements"] != list(range(query_count)):
        raise ValueError("not every query requires the identified border policy")

    public_id = public_challenge_id(public)
    private = {
        "schema": "36275402c6b2-border-policy-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "public_id": public_id,
        "seed": seed,
        "input_pair_key": _input_pair_key(seed),
        "parameter": parameter,
        "demo_count": demo_count,
        "query_count": query_count,
        "program_sha256": _sha256(programs[selected]),
        "input_sha256": [_grid_fingerprint(grid) for grid in grids],
        "border_sides": border_sides,
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
    """Create one Racket-labeled public/private episode under one fixed policy."""
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

    programs = {
        policy: materialize_rule(policy, root=root_path)
        for policy in ALLOWED_POLICIES
    }
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root_path
    )
    del generator

    public_dir = out_path / "public"
    episode_dir = out_path / "private" / "episodes"
    rule_dir = out_path / "private" / "rules"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    rule_dir.mkdir(parents=True)
    for policy, program in programs.items():
        (rule_dir / f"{policy}.rkt").write_text(program, encoding="utf-8")

    episodes: list[dict[str, Any]] = []
    public_ids: set[str] = set()
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
            public_path = public_dir / f"challenge-{public_id}.json"
            private_path = episode_dir / f"{public_id}.json"
            public_path.write_bytes(public_challenge_bytes(public))
            _write_json(private_path, private)
            episodes.append(
                {
                    "public_id": public_id,
                    "public_file": str(public_path.relative_to(out_path)),
                    "private_file": str(private_path.relative_to(out_path)),
                    "seed": seed,
                    "input_pair_key": private["input_pair_key"],
                    "parameter": private["parameter"],
                    "border_sides": private["border_sides"],
                }
            )

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        default_outputs = execute_rule_many(
            programs[DEFAULT_POLICY],
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

    episodes.sort(key=lambda row: row["public_id"])
    prototype_path = Path(__file__).resolve()
    manifest = {
        "schema": "36275402c6b2-border-policy-evidence-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "name": "border_policy",
            "allowed": list(ALLOWED_POLICIES),
            "default": DEFAULT_POLICY,
        },
        "input_constraints": (
            "selected production odd-profile inputs; exactly one noncorner source "
            "cell lies on the crop border; episode slots cycle top/bottom/left/right"
        ),
        "demo_count": demos,
        "query_count": queries,
        "seed_domain": {"minimum": MIN_SEED, "maximum": MAX_SEED},
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_default_unchanged": programs[DEFAULT_POLICY]
        == canonical_source(root=root_path),
        "programs": {
            policy: {
                "file": str((rule_dir / f"{policy}.rkt").relative_to(out_path)),
                "sha256": _sha256(program),
            }
            for policy, program in programs.items()
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
            "prototype only; production remains pinned to canonical recolouring",
            "finite evidence covers only the materialized seeds and two declared settings",
            "identifiability is checked only against the opposite border policy",
            "the authored support has exactly one noncorner border source per input",
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
