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
from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "cfadc43e5098"
PROTOTYPE_VERSION = "1.0.0"
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
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_episode_id(episode: dict[str, Any]) -> str:
    """Opaque ID derived only from demos and query inputs visible to a solver."""
    raw = json.dumps(_visible_projection(episode), sort_keys=True, separators=(",", ":"))
    return "episode-" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    visible = _visible_projection(episode)
    return {
        "schema": "arcpuzzles-parametric-blocker-policy-public-v1",
        "episode_id": public_episode_id(episode),
        "train": visible["train"],
        "test": visible["test"],
    }


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check production and every query against the only alternative setting."""
    policy = _validate_policy(episode["parameter"]["blocker_policy"])
    alternative = next(item for item in ALLOWED_BLOCKER_POLICIES if item != policy)
    train = episode["train"]
    queries = episode["test"]
    refuting_demo_indices = [
        index
        for index, pair in enumerate(train)
        if run_racket(bridge, alternative, pair["input"]) != pair["output"]
    ]
    alternative_fits = not refuting_demo_indices
    query_rows = []
    train_inputs = {tuple(map(tuple, pair["input"])) for pair in train}
    all_query_inputs = [tuple(map(tuple, pair["input"])) for pair in queries]
    for index, pair in enumerate(queries):
        alternative_output = run_racket(bridge, alternative, pair["input"])
        query_rows.append({
            "query_index": index,
            "query_input_distinct": (
                all_query_inputs.count(all_query_inputs[index]) == 1
                and all_query_inputs[index] not in train_inputs
            ),
            "query_differs_under_alternative": alternative_output != pair["output"],
            "alternative_refuted_by_demonstrations": not alternative_fits,
            "refuting_demonstration_indices": refuting_demo_indices,
        })
    production_pass = (
        bool(refuting_demo_indices)
        and len(queries) == 4
        and all(row["query_input_distinct"] for row in query_rows)
        and all(row["query_differs_under_alternative"] for row in query_rows)
    )

    all_pairs = train + queries
    rotations = []
    for query_index, held_out in enumerate(all_pairs):
        demonstrations = [pair for index, pair in enumerate(all_pairs) if index != query_index]
        rotation_refuters = [
            index
            for index, pair in enumerate(demonstrations)
            if run_racket(bridge, alternative, pair["input"]) != pair["output"]
        ]
        rotations.append({
            "query_index": query_index,
            "status": "no_ambiguity_found" if rotation_refuters else "ambiguous",
            "alternative_query_differs": (
                run_racket(bridge, alternative, held_out["input"]) != held_out["output"]
            ),
            "refuting_demonstration_count": len(rotation_refuters),
        })
    return {
        "parameter": {"blocker_policy": policy},
        "alternative": {"blocker_policy": alternative},
        "production": {
            "status": "no_ambiguity_found" if production_pass else "ambiguous_or_invalid",
            "actual_demo_count": len(train),
            "actual_query_count": len(queries),
            "alternative_fits_demonstrations": alternative_fits,
            "refuting_demonstration_indices": refuting_demo_indices,
        },
        "queries": query_rows,
        "rotations": rotations,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    out = out.resolve()
    for policy, record in evidence["settings"].items():
        rule_name = policy.replace("_", "-") + ".rkt"
        rule_path = out / "private" / "rules" / rule_name
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(record["racket_text"], encoding="utf-8")
        episode_id = record["public_challenge"]["episode_id"]
        _write_json(out / "private" / f"{episode_id}.json", record["episode"])
        _write_json(out / "public" / f"{episode_id}.json", record["public_challenge"])
    _write_json(out / "report.json", evidence)
    manifest = {
        "schema": "arcpuzzles-parametric-blocker-policy-manifest-v1",
        "files": [],
    }
    for path in sorted(item for item in out.rglob("*") if item.is_file() and item.name != "manifest.json"):
        manifest["files"].append({
            "path": path.relative_to(out).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        })
    _write_json(out / "manifest.json", manifest)


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
