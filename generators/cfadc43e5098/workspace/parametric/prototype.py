#!/usr/bin/env python3
"""Proposed blocker-policy parameter for ARC task cfadc43e5098.

The selected canonical generator remains unchanged.  This task-local prototype
varies exactly one predicate: whether a third bounding box blocks a candidate
bridge only when it has the endpoint color (canonical ``same_color``), or
regardless of color (proposed ``any_color``).  A setting is fixed for an entire
episode.  Every retained label is executed by the exact materialized Racket
program through :class:`arc_repl.racket_bridge.RacketBridge`.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "cfadc43e5098"
PROTOTYPE_VERSION = "1.1.0"
ALLOWED_BLOCKER_POLICIES = ("same_color", "any_color")
DEFAULT_BLOCKER_POLICY = "same_color"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent


def _validate_policy(policy: str) -> str:
    if type(policy) is not str or policy not in ALLOWED_BLOCKER_POLICIES:
        raise ValueError(
            f"blocker_policy must be one of {ALLOWED_BLOCKER_POLICIES}, got {policy!r}"
        )
    return policy


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool)")
    if not 1 <= value <= 16:
        raise ValueError(f"{name} must be in 1..16")
    return value


def choose_blocker_policy(seed: int) -> str:
    """Choose one deterministic hidden setting for the complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    digest = hashlib.sha256(f"{TASK_ID}|blocker_policy|{seed}".encode()).digest()
    return ALLOWED_BLOCKER_POLICIES[digest[0] % len(ALLOWED_BLOCKER_POLICIES)]


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if len(programs) != 2 or len(set(programs)) != 1:
        raise RuntimeError(f"expected two identical canonical authorities for {TASK_ID}")
    return programs[0]


def racket_program(blocker_policy: str) -> str:
    """Return the exact Racket authority instantiated for one setting."""
    policy = _validate_policy(blocker_policy)
    canonical = _canonical_program()
    if policy == DEFAULT_BLOCKER_POLICY:
        return canonical
    marker = "(= oc color)"
    if canonical.count(marker) != 1:
        raise RuntimeError("canonical blocker predicate is not uniquely replaceable")
    return canonical.replace(marker, "#t")


def racket_sha256(blocker_policy: str) -> str:
    return hashlib.sha256(racket_program(blocker_policy).encode()).hexdigest()


def _racket_literal(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is int:
        return str(value)
    raise TypeError(f"cannot encode Racket literal: {value!r}")


def run_racket(bridge: RacketBridge, blocker_policy: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute one grid through the exact instantiated program."""
    if not isinstance(bridge, RacketBridge):
        raise TypeError("bridge must be a live RacketBridge")
    callable_source = strip_rule_wrapper(racket_program(blocker_policy))
    grid_literal = "'" + _racket_literal(grid)
    result = bridge.eval_text(f"({callable_source} {grid_literal})")
    if not isinstance(result, list):
        raise RuntimeError(f"Racket returned a non-grid result: {result!r}")
    return result


@lru_cache(maxsize=1)
def _generator():
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module, source_path, source_sha256


def _production_seed(seed: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}|episode-inputs|{seed}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _episode_inputs(seed: int, count: int) -> list[list[list[int]]]:
    """Select distinct production-lawful inputs that distinguish both policies."""
    module, _, _ = _generator()
    witness = module.SEMANTIC_WITNESSES["different_color_obstacle_does_not_block"]
    selected: list[list[list[int]]] = []
    seen = set()
    production_seed = _production_seed(seed)
    start = int.from_bytes(hashlib.sha256(f"start|{seed}".encode()).digest()[:2], "big")
    bands = (None, "easy", "medium", "hard")
    for offset in range(5000):
        sample_index = start + offset
        grid = module.generate(
            production_seed,
            sample_index,
            difficulty=bands[offset % len(bands)],
        )
        key = tuple(map(tuple, grid))
        if key in seen or module.self_check(grid) or not witness(grid):
            continue
        selected.append(deepcopy(grid))
        seen.add(key)
        if len(selected) == count:
            return selected
    raise RuntimeError(f"found only {len(selected)} distinguishing inputs; needed {count}")


def build_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    blocker_policy: str | None = None,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private, fully labeled episode with a fixed parameter setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    if demos + queries > 24:
        raise ValueError("demo_count + query_count must not exceed 24")
    policy = choose_blocker_policy(seed) if blocker_policy is None else _validate_policy(blocker_policy)
    inputs = _episode_inputs(seed, demos + queries)
    pairs = [
        {"input": deepcopy(grid), "output": run_racket(bridge, policy, grid)}
        for grid in inputs
    ]
    return {
        "schema": "arcpuzzles-parametric-blocker-policy-private-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"blocker_policy": policy},
        "racket_sha256": racket_sha256(policy),
        "train": pairs[:demos],
        "test": pairs[demos:],
    }


def _visible_projection(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the shared, validated visible projection without private pair fields."""
    return json.loads(public_challenge_bytes(episode))


def public_episode_id(episode: dict[str, Any]) -> str:
    """Opaque ID hashing exactly the bytes written to the public challenge file."""
    return "episode-" + public_challenge_id(episode)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    visible = _visible_projection(episode)
    return {
        "schema": "arcpuzzles-parametric-blocker-policy-public-v1",
        "episode_id": public_episode_id(episode),
        "train": visible["train"],
        "test": visible["test"],
    }


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check labels separately from demo-only setting survival and query disagreement."""
    policy = _validate_policy(episode["parameter"]["blocker_policy"])
    alternative = next(item for item in ALLOWED_BLOCKER_POLICIES if item != policy)
    train = episode["train"]
    queries = episode["test"]
    all_pairs = train + queries
    # Execute every lawful setting once per pair. Query labels never participate
    # in the production survivor filter; they are checked only for validity.
    outputs = {
        setting: [run_racket(bridge, setting, pair["input"]) for pair in all_pairs]
        for setting in ALLOWED_BLOCKER_POLICIES
    }
    refuters = {
        setting: [index for index, pair in enumerate(train)
                  if outputs[setting][index] != pair["output"]]
        for setting in ALLOWED_BLOCKER_POLICIES
    }
    survivors = [setting for setting in ALLOWED_BLOCKER_POLICIES if not refuters[setting]]
    demo_mismatches = refuters[policy]
    query_mismatches = [
        index for index, pair in enumerate(queries)
        if outputs[policy][len(train) + index] != pair["output"]
    ]
    labels_valid = not demo_mismatches and not query_mismatches
    alternative_fits = not refuters[alternative]
    train_inputs = {tuple(map(tuple, pair["input"])) for pair in train}
    query_inputs = [tuple(map(tuple, pair["input"])) for pair in queries]
    query_rows = []
    for index, pair in enumerate(queries):
        pair_index = len(train) + index
        predictions = {tuple(map(tuple, outputs[setting][pair_index])) for setting in survivors}
        disagreement = len(predictions) > 1
        query_rows.append({
            "query_index": index,
            "query_input_distinct": (
                query_inputs.count(query_inputs[index]) == 1
                and query_inputs[index] not in train_inputs
            ),
            "reference_label_valid": index not in query_mismatches,
            "query_differs_under_alternative": (
                outputs[alternative][pair_index] != outputs[policy][pair_index]
            ),
            "alternative_refuted_by_demonstrations": not alternative_fits,
            "refuting_demonstration_indices": refuters[alternative],
            "surviving_settings_disagree": disagreement,
            "status": ("no_consistent_setting" if not survivors else
                       "ambiguous" if disagreement else "no_ambiguity_found"),
        })
    counts_valid = 1 <= len(train) <= 16 and 1 <= len(queries) <= 16 and len(all_pairs) <= 24
    distinct_queries = all(row["query_input_distinct"] for row in query_rows)
    ambiguity_status = (
        "no_consistent_setting" if not survivors else
        "ambiguous" if any(row["surviving_settings_disagree"] for row in query_rows) else
        "no_ambiguity_found"
    )
    production_status = (
        "invalid_labels" if not labels_valid else
        "invalid_episode" if not counts_valid or not distinct_queries else
        ambiguity_status
    )

    rotations = []
    for query_index, held_out in enumerate(all_pairs):
        demo_indices = [index for index in range(len(all_pairs)) if index != query_index]
        rotation_refuters = {
            setting: [index for index in demo_indices
                      if outputs[setting][index] != all_pairs[index]["output"]]
            for setting in ALLOWED_BLOCKER_POLICIES
        }
        rotation_survivors = [setting for setting in ALLOWED_BLOCKER_POLICIES
                              if not rotation_refuters[setting]]
        predictions = {tuple(map(tuple, outputs[setting][query_index]))
                       for setting in rotation_survivors}
        disagreement = len(predictions) > 1
        rotation_ambiguity = (
            "no_consistent_setting" if not rotation_survivors else
            "ambiguous" if disagreement else "no_ambiguity_found"
        )
        rotations.append({
            "query_index": query_index,
            "status": "invalid_labels" if not labels_valid else rotation_ambiguity,
            "ambiguity_status": rotation_ambiguity,
            "reference_labels_valid": labels_valid,
            "surviving_settings": rotation_survivors,
            "surviving_settings_disagree": disagreement,
            "alternative_query_differs": (
                outputs[alternative][query_index] != outputs[policy][query_index]
            ),
            "refuting_demonstration_count": len(rotation_refuters[alternative]),
        })
    return {
        "parameter": {"blocker_policy": policy},
        "alternative": {"blocker_policy": alternative},
        "production": {
            "status": production_status,
            "ambiguity_status": ambiguity_status,
            "actual_demo_count": len(train),
            "actual_query_count": len(queries),
            "counts_valid": counts_valid,
            "reference_labels_valid": labels_valid,
            "demonstration_label_mismatch_indices": demo_mismatches,
            "query_label_mismatch_indices": query_mismatches,
            "surviving_settings": survivors,
            "alternative_fits_demonstrations": alternative_fits,
            "refuting_demonstration_indices": refuters[alternative],
        },
        "queries": query_rows,
        "rotations": rotations,
    }


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_evidence(
    bridge: RacketBridge,
    *,
    seed: int,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build retained evidence for both settings, including exact Racket text."""
    module, source_path, source_sha256 = _generator()
    settings = {}
    for policy in ALLOWED_BLOCKER_POLICIES:
        episode = build_episode(
            bridge,
            seed,
            blocker_policy=policy,
            demo_count=demo_count,
            query_count=query_count,
        )
        settings[policy] = {
            "is_canonical_default": policy == DEFAULT_BLOCKER_POLICY,
            "racket_text": racket_program(policy),
            "racket_sha256": racket_sha256(policy),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "analysis": analyze_episode(bridge, episode),
        }
    first = settings[DEFAULT_BLOCKER_POLICY]["episode"]["train"][0]["input"]
    default_output = run_racket(bridge, DEFAULT_BLOCKER_POLICY, first)
    alternative_output = run_racket(bridge, "any_color", first)
    return {
        "schema": "arcpuzzles-parametric-blocker-policy-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "request": {"demo_count": demo_count, "query_count": query_count},
        "parameter": {
            "name": "blocker_policy",
            "allowed_values": list(ALLOWED_BLOCKER_POLICIES),
            "default": DEFAULT_BLOCKER_POLICY,
            "dependent_input_constraints": [
                "same-color endpoint boxes form a midpoint-aligned bridge candidate",
                "a differently colored third box intersects the bridge rectangle",
            ],
        },
        "source": {
            "generator_path": str(source_path),
            "generator_sha256": source_sha256,
            "prototype_path": str(Path(__file__).resolve()),
            "prototype_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "rule_wrap_sha256": hashlib.sha256(
                Path(strip_rule_wrapper.__code__.co_filename).read_bytes()
            ).hexdigest(),
        },
        "distinguishing_witness": {
            "input": first,
            "default_output": default_output,
            "alternative_output": alternative_output,
            "outputs_differ": default_output != alternative_output,
        },
        "settings": settings,
        "limits": [
            "bounded two-setting prototype, not selected production behavior",
            "identifiability is checked only against the other blocker-policy setting",
            "generated inputs are sampled from the current production manifold",
        ],
    }


def materialize(out: Path, evidence: dict[str, Any]) -> None:
    """Preflight the complete batch, then write new public files in content-ID order.

    The in-memory public_challenge record retains its legacy metadata shape.
    Public files instead contain exactly the shared visible projection bytes.
    Existing output targets are refused so old exports cannot join a new batch.
    """
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(f"output target already exists: {out}")
    out = out.resolve()
    report = deepcopy(evidence)
    public_records = {}
    artifacts = {}
    for policy, record in report["settings"].items():
        _validate_policy(policy)
        episode = record["episode"]
        raw = public_challenge_bytes(episode)
        episode_id = public_episode_id(episode)
        if episode_id in public_records:
            raise ValueError(f"duplicate public payload or content-ID collision: {episode_id}")
        public_records[episode_id] = raw
        # Rebuild cached projection metadata from the episode as well. Neither
        # a stale cached ID nor private data may redirect the public artifact.
        record["public_challenge"] = public_challenge(episode)
        rule_name = policy.replace("_", "-") + ".rkt"
        artifacts[f"private/rules/{rule_name}"] = record["racket_text"].encode("utf-8")
        artifacts[f"private/{episode_id}.json"] = _json_bytes(episode)
    artifacts["report.json"] = _json_bytes(report)
    for episode_id, raw in public_records.items():
        artifacts[f"public/{episode_id}.json"] = raw
    manifest = {
        "schema": "arcpuzzles-parametric-blocker-policy-manifest-v1",
        "files": [{
            "path": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        } for name, raw in sorted(artifacts.items())],
    }
    artifacts["manifest.json"] = _json_bytes(manifest)
    # All validation, duplicate detection and serialization happen before the
    # first directory or file is created. This is deliberately a fresh export.
    out.mkdir(parents=True, exist_ok=False)
    for name in sorted(name for name in artifacts if not name.startswith("public/")):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artifacts[name])
    # Keep this pass separate from private policy iteration: public creation
    # order is a function of visible content IDs alone.
    for episode_id in sorted(public_records):
        path = out / "public" / f"{episode_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(public_records[episode_id])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demo-count", type=int, default=2)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=64) as bridge:
        evidence = build_evidence(
            bridge,
            seed=args.seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
    materialize(args.out, evidence)
    print(json.dumps({
        "status": evidence["status"],
        "seed": args.seed,
        "demo_count": args.demo_count,
        "query_count": args.query_count,
        "settings": {
            name: record["analysis"]["production"]["status"]
            for name, record in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
