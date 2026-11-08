#!/usr/bin/env python3
"""Bounded adversarial probe for the 4de2bae05c7d native family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


HOME = Path(__file__).resolve().parent
TASK_HOME = HOME.parents[1]
TEST_PATHS = [
    TASK_HOME / "tests/test_generator_4de2bae05c7d.py",
    TASK_HOME / "tests/test_parametric_4de2bae05c7d.py",
]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = load("audit_family_4de2bae05c7d", HOME / "family.py")
A = load("audit_adapter_4de2bae05c7d", HOME / "adapter.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def selected_size(facts: dict[str, Any], mode: str) -> int:
    key = facts[f"post_{mode}_blue"]
    return len(key)


def record_dimension_observation(
    fixed_dimensions: dict[str, set[int]],
    examples: dict[str, set[str]],
    dimension_key: str,
    input_key: str,
    selected_size_value: int,
) -> None:
    """Record a matched input once even when it is reused across settings."""
    fixed_dimensions.setdefault(dimension_key, set()).add(selected_size_value)
    examples.setdefault(dimension_key, set()).add(input_key)


def validate_dimension_crossing(
    fixed_dimensions: dict[str, set[int]],
    observation_counts: dict[str, int],
    *,
    minimum_observations: int = 12,
) -> list[str]:
    """Reject stable dimension/answer-size confounding only when sampled enough.

    Sparse exact-size groups can coincide by chance; treating a three-sample
    group as universal evidence makes the probe itself nondeterministically
    overfit. Common groups must expose every intended selected-size value.
    """
    checked: list[str] = []
    for key, values in sorted(fixed_dimensions.items()):
        if observation_counts.get(key, 0) < minimum_observations:
            continue
        ensure(len(values) >= 3, f"fixed-dimension group {key} exposes only {values}")
        checked.append(key)
    return checked


def run(seeds: int) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "seeds": seeds,
        "episodes": 0,
        "pairs": 0,
        "minimum_lessons": 0,
        "rival_checks": 0,
        "query_identifiability_checks": 0,
        "count_boundary_episodes": 0,
        "malformed_rejections": 0,
        "crossed_control_groups": {},
    }
    fixed_dimensions: dict[str, set[int]] = {}
    dimension_examples: dict[str, set[str]] = {}
    fixed_intermediate: dict[int, set[str]] = {}
    selected_locations: dict[str, set[tuple[int, int]]] = {
        "largest": set(),
        "smallest": set(),
    }
    all_profiles: set[str] = set()
    first_query_profiles: set[str] = set()

    for seed in range(seeds):
        episodes = {
            mode: A.generate(seed, {"postprocess": mode}, 3, 4)
            for mode in F.MODES
        }
        metrics["episodes"] += len(episodes)
        canonical_inputs = [
            pair["input"]
            for pair in episodes["canonical"]["train"] + episodes["canonical"]["test"]
        ]
        ensure(
            len({F.grid_key(grid) for grid in canonical_inputs}) == 7,
            f"seed {seed}: duplicate minimum-lesson input",
        )
        for mode, episode in episodes.items():
            pairs = episode["train"] + episode["test"]
            metrics["pairs"] += len(pairs)
            ensure(
                [pair["input"] for pair in pairs] == canonical_inputs,
                f"seed {seed} mode {mode}: setting changed input grammar",
            )
            for pair in pairs:
                errors = F.validate_scene(pair["input"])
                ensure(not errors, f"seed {seed} mode {mode}: {errors}")
                ensure(
                    pair["output"] == F.apply_mode(pair["input"], mode),
                    f"seed {seed} mode {mode}: Python label mismatch",
                )
                facts = F.scene_facts(pair["input"])
                all_profiles.add(facts["profile"])
                dimension_key = f"{facts['profile']}:{facts['height']}x{facts['width']}"
                record_dimension_observation(
                    fixed_dimensions,
                    dimension_examples,
                    dimension_key,
                    F.grid_key(pair["input"]),
                    selected_size(facts, "largest"),
                )
                fixed_intermediate.setdefault(selected_size(facts, "largest"), set()).add(
                    dimension_key
                )
                for rank in ("largest", "smallest"):
                    cells = facts[f"post_{rank}_blue"]
                    selected_locations[rank].add(cells[0])
                    ensure(
                        F.rank_original_then_recolor(pair["input"], rank)
                        != F.apply_mode(pair["input"], rank),
                        f"seed {seed}: rank-before-{rank} shortcut survived",
                    )
                    ensure(
                        F.recolor_only_new_targets(pair["input"], rank)
                        != F.apply_mode(pair["input"], rank),
                        f"seed {seed}: partial-intermediate-{rank} shortcut survived",
                    )
                ensure(
                    F.rank_after_bbox(pair["input"], "largest")
                    != F.apply_mode(pair["input"], "largest"),
                    f"seed {seed}: bbox-largest shortcut survived",
                )
                ensure(
                    F.rank_after_eight_connectivity(pair["input"], "largest")
                    != F.apply_mode(pair["input"], "largest"),
                    f"seed {seed}: 8-connected-largest shortcut survived",
                )
            demos = episode["train"]
            metrics["minimum_lessons"] += 1
            for name, rival in F.RIVALS[mode].items():
                metrics["rival_checks"] += 1
                ensure(
                    any(rival(pair["input"]) != pair["output"] for pair in demos),
                    f"seed {seed} mode {mode}: rival fits every demo: {name}",
                )
            for query in episode["test"]:
                metrics["query_identifiability_checks"] += 1
                reasons = F.lesson_identifiable(demos, query["input"], mode)
                ensure(
                    not reasons,
                    f"seed {seed} mode {mode}: lesson hole: {reasons}",
                )
        first_query_profiles.add(F.scene_facts(episodes["largest"]["test"][0]["input"])["profile"])

        if seed % 4 == 0:
            for demos, queries in ((3, 1), (6, 1), (6, 4)):
                for mode in F.MODES:
                    episode = A.generate(seed, {"postprocess": mode}, demos, queries)
                    ensure(len(episode["train"]) == demos, "demo boundary mismatch")
                    ensure(len(episode["test"]) == queries, "query boundary mismatch")
                    ensure(
                        len({F.grid_key(p["input"]) for p in episode["train"] + episode["test"]})
                        == demos + queries,
                        "boundary-count episode contains duplicates",
                    )
                    metrics["count_boundary_episodes"] += 1

    # Cross the intended intermediate against dimensions/profile positions.
    dimension_counts = {
        key: len(input_keys) for key, input_keys in dimension_examples.items()
    }
    checked_dimension_groups = validate_dimension_crossing(
        fixed_dimensions, dimension_counts
    )
    ensure(
        checked_dimension_groups,
        "no fixed-dimension group had enough observations to audit",
    )
    for size, groups in fixed_intermediate.items():
        ensure(len(groups) >= 4, f"post-largest size {size} occurs in too few nuisance groups")
    ensure(len(selected_locations["largest"]) >= seeds, "largest selection appears fixed")
    ensure(len(selected_locations["smallest"]) >= seeds, "smallest selection appears fixed")
    ensure(first_query_profiles >= {"minimum", "boundary", "dense"}, "first query role is insufficiently shuffled")
    ensure(all_profiles >= {"minimum", "boundary", "standard", "wide", "tall", "dense"}, "profile coverage missing")

    # Authored-certificate/verifier negative cases.
    episode = A.generate(991, {"postprocess": "largest"}, 3, 4)
    demos = episode["train"]
    query = episode["test"][0]["input"]
    mutations = []
    mutations.append((demos[:1] + demos[:1] + demos[2:], query, "duplicate"))
    mutations.append((demos, demos[0]["input"], "duplicate"))
    forged = json.loads(json.dumps(demos))
    forged[0]["output"][0][0] = (forged[0]["output"][0][0] + 1) % 10
    mutations.append((forged, query, "mislabeled"))
    for value in (True, 1.5):
        malformed = json.loads(json.dumps(query))
        malformed[0][0] = value
        mutations.append((demos, malformed, "invalid"))
    ragged = json.loads(json.dumps(query))
    ragged[0].pop()
    mutations.append((demos, ragged, "invalid"))
    for mutated_demos, mutated_query, expected in mutations:
        reasons = F.lesson_identifiable(mutated_demos, mutated_query, "largest")
        ensure(any(expected in reason for reason in reasons), f"mutation escaped: {expected}: {reasons}")
        metrics["malformed_rejections"] += 1

    metrics["crossed_control_groups"] = {
        "fixed_dimensions": {
            key: {"observations": dimension_counts[key], "selected_sizes": sorted(values)}
            for key, values in sorted(fixed_dimensions.items())
        },
        "checked_dimension_groups": checked_dimension_groups,
        "fixed_intermediate": {str(key): sorted(values) for key, values in sorted(fixed_intermediate.items())},
        "largest_selected_origins": len(selected_locations["largest"]),
        "smallest_selected_origins": len(selected_locations["smallest"]),
        "first_query_profiles": sorted(first_query_profiles),
        "all_profiles": sorted(all_profiles),
    }
    sources = [
        HOME / "adversarial_probe.py",
        HOME / "adapter.py",
        HOME / "family.py",
        HOME / "promotion.json",
        HOME / "canonical.rkt",
        HOME / "largest.rkt",
        HOME / "smallest.rkt",
        HOME / "rank-before-largest.rkt",
        *TEST_PATHS,
    ]
    return {
        "schema": "arcpuzzles-task-parametric-adversarial-v1",
        "task_id": "4de2bae05c7d",
        "status": "passed",
        "scope": (
            "Bounded Python semantic/sampler/certificate audit. Racket execution, "
            "public projection, and owner acceptance are separate."
        ),
        "metrics": metrics,
        "source_sha256": {path.relative_to(TASK_HOME.parent.parent).as_posix(): digest(path) for path in sources},
        "finite_limits": (
            "Finite rival banks and sampled seeds do not establish universal uniqueness, "
            "learning benefit, owner acceptance, or training admission."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 512:
        parser.error("--seeds must be 1..512")
    try:
        report = run(args.seeds)
    except BaseException as error:
        report = {
            "schema": "arcpuzzles-task-parametric-adversarial-v1",
            "task_id": "4de2bae05c7d",
            "status": "failed",
            "error": f"{type(error).__name__}: {error}",
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        raise
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], **report["metrics"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
