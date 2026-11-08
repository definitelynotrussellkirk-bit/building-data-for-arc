#!/usr/bin/env python3
"""Proposed episode-level docking-distance parameter for 54628ce9692d.

This task-local authoring prototype does not alter the selected production
rule.  It chooses one docking distance for an entire episode, materializes the
corresponding Racket program, and obtains every retained label by executing the
bundled Racket runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "54628ce9692d"
PROTOTYPE_VERSION = "proposed-docking-distance-v1"
ALLOWED_DOCKING_DISTANCES = (1, 2)
DEFAULT_DOCKING_DISTANCE = 1
CANONICAL_RULE_HASH = "9b6d1153ebca"
CANONICAL_SOURCE_SHA256 = (
    "9ddc1ad5a626057fc08c9394a736d0e06f1c3da45ce732d1908e62f36b8aa662"
)
CANONICAL_ROW_STEP = "(list-ref from 4)"
CANONICAL_COL_STEP = "(list-ref from 5)"
ALTERNATIVE_ROW_STEP = "(* 2 (list-ref from 4))"
ALTERNATIVE_COL_STEP = "(* 2 (list-ref from 5))"


def _sha256(value: str | bytes) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CANONICAL_ROW_STEP) != 1:
        raise ValueError("canonical source must contain exactly one row docking step")
    if source.count(CANONICAL_COL_STEP) != 1:
        raise ValueError("canonical source must contain exactly one column docking step")
    if ALTERNATIVE_ROW_STEP in source or ALTERNATIVE_COL_STEP in source:
        raise ValueError("canonical source unexpectedly contains alternative steps")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources = {
        row.get("program_solution")
        for row in (
            json.loads(line)
            for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row.get("task_id") == TASK_ID
    }
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    docking_distance=DEFAULT_DOCKING_DISTANCE, *, root=None, source=None
) -> str:
    if type(docking_distance) is not int or docking_distance not in ALLOWED_DOCKING_DISTANCES:
        raise ValueError("docking_distance must be literal integer 1 or 2")
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if docking_distance == DEFAULT_DOCKING_DISTANCE:
        return canonical
    alternative = canonical.replace(
        CANONICAL_ROW_STEP, ALTERNATIVE_ROW_STEP, 1
    ).replace(CANONICAL_COL_STEP, ALTERNATIVE_COL_STEP, 1)
    if alternative.count(ALTERNATIVE_ROW_STEP) != 1:
        raise ValueError("failed to materialize the row docking-distance change")
    if alternative.count(ALTERNATIVE_COL_STEP) != 1:
        raise ValueError("failed to materialize the column docking-distance change")
    return alternative


def restore_canonical_rule(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    restored = source.replace(
        ALTERNATIVE_ROW_STEP, CANONICAL_ROW_STEP, 1
    ).replace(ALTERNATIVE_COL_STEP, CANONICAL_COL_STEP, 1)
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    restored = restore_canonical_rule(source)
    del restored
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    return source[len("(rule! ") : -1]


def execute_rule(source: str, grid, *, bridge=None):
    grid = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def parameters_for_seed(seed: int) -> dict[str, int]:
    _validate_seed(seed)
    return {
        "docking_distance": random.Random(seed).choice(
            ALLOWED_DOCKING_DISTANCES
        )
    }


def _candidate_grid(module, rng: random.Random, *, slot: int, attempt: int):
    piece_counts = (2, 3, 4, 3)
    bands = ("easy", "medium", "hard", "medium")
    background = rng.randrange(2, 10)
    generator_seed = rng.randrange(2**63)
    sample_index = rng.randrange(1_000_000_000)
    return module.generate(
        generator_seed,
        sample_index,
        difficulty=bands[slot],
        n_pieces=piece_counts[slot],
        background_color=background,
    ), {
        "slot": slot,
        "attempt": attempt,
        "generator_seed": generator_seed,
        "sample_index": sample_index,
        "difficulty": bands[slot],
        "n_pieces": piece_counts[slot],
        "background_color": background,
    }


def _make_episode(seed: int, *, root: Path, bridge: RacketBridge):
    rng = random.Random(seed)
    distance = rng.choice(ALLOWED_DOCKING_DISTANCES)
    rival_distance = next(
        value for value in ALLOWED_DOCKING_DISTANCES if value != distance
    )
    selected_source = materialize_rule(distance, root=root)
    rival_source = materialize_rule(rival_distance, root=root)
    module, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )

    labeled = []
    rival_outputs = []
    recipes = []
    for slot in range(4):
        for attempt in range(32):
            grid, recipe = _candidate_grid(
                module, rng, slot=slot, attempt=attempt
            )
            selected_output = execute_rule(selected_source, grid, bridge=bridge)
            rival_output = execute_rule(rival_source, grid, bridge=bridge)
            if selected_output == rival_output:
                continue
            labeled.append(
                {
                    "fixture_id": f"slot-{slot}-attempt-{attempt}",
                    "input": copy.deepcopy(grid),
                    "output": selected_output,
                }
            )
            rival_outputs.append(rival_output)
            recipes.append(recipe)
            break
        else:
            raise RuntimeError(
                f"could not find a distinguishing lawful input for slot {slot}"
            )

    train = labeled[:3]
    test = labeled[3:]
    demonstration_mismatches = [
        index
        for index, pair in enumerate(train)
        if pair["output"] != rival_outputs[index]
    ]
    query_mismatches = [
        index
        for index, pair in enumerate(test)
        if pair["output"] != rival_outputs[len(train) + index]
    ]
    ambiguities = []
    if demonstration_mismatches != list(range(len(train))):
        ambiguities.append(
            "the other distance was not refuted by every demonstration"
        )
    if query_mismatches != list(range(len(test))):
        ambiguities.append("the declared distances agree on a retained query")

    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {"docking_distance": distance},
        "parameter_selected_once": True,
        "input_constraints_depend_on_parameter": False,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "generator_path": str(generator_path),
        "generator_sha256": generator_sha256,
        "input_recipes": recipes,
        "train": train,
        "test": test,
        "parameter_rivals": [
            {
                "docking_distance": rival_distance,
                "racket_sha256": _sha256(rival_source),
                "status": (
                    "refuted_by_every_demonstration"
                    if demonstration_mismatches == list(range(len(train)))
                    else "not_fully_refuted"
                ),
                "demonstration_mismatch_indices": demonstration_mismatches,
                "query_mismatch_indices": query_mismatches,
                "outputs": rival_outputs,
            }
        ],
        "ambiguities": ambiguities,
    }


def make_episode(seed: int, *, root=None, bridge=None):
    _validate_seed(seed)
    root = find_root(__file__) if root is None else Path(root)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, root=root, bridge=owned)
    return _make_episode(seed, root=root, bridge=bridge)


def public_challenge(episode):
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _canonical_replay(*, root: Path, bridge: RacketBridge):
    source = canonical_source(root=root)
    rows = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        actual = execute_rule(source, pair["input"], bridge=bridge)
        if actual != pair["output"]:
            raise AssertionError(
                f"canonical replay mismatch at variant={pair['variant']} "
                f"split={pair['split']} pair={pair['pair_index']}"
            )
        rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "input_sha256": grid_sha256(pair["input"]),
                "output_sha256": grid_sha256(actual),
            }
        )
    return {
        "status": "pass",
        "pairs_checked": len(rows),
        "canonical_source_sha256": _sha256(source),
        "pairs": rows,
    }


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _files_manifest(root: Path):
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in {"report.json", "failure.json"}:
            continue
        body = path.read_bytes()
        rows.append(
            {"path": relative, "bytes": len(body), "sha256": _sha256(body)}
        )
    return rows


def write_evidence(seeds, *, out, root=None):
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("at least one seed is required")
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__) if root is None else Path(root)

    try:
        with RacketBridge() as bridge:
            replay = _canonical_replay(root=root, bridge=bridge)
            episodes = [
                make_episode(seed, root=root, bridge=bridge) for seed in seeds
            ]

        private = out / "private"
        public = out / "public"
        rules = private / "rules"
        snapshots = private / "source_snapshot"
        rules.mkdir(parents=True)
        public.mkdir(parents=True)
        snapshots.mkdir(parents=True)

        _write_json(private / "canonical_replay.json", replay)
        for distance in ALLOWED_DOCKING_DISTANCES:
            (rules / f"docking-distance-{distance}.rkt").write_text(
                materialize_rule(distance, root=root), encoding="utf-8"
            )

        episode_rows = []
        ambiguity_count = 0
        for index, episode in enumerate(episodes):
            distance = episode["parameters"]["docking_distance"]
            private_path = private / f"episode-{index:03d}.json"
            public_path = public / f"episode-{index:03d}.json"
            saved = copy.deepcopy(episode)
            saved["racket_path"] = (
                f"private/rules/docking-distance-{distance}.rkt"
            )
            _write_json(private_path, saved)
            _write_json(public_path, public_challenge(episode))
            ambiguity_count += len(episode["ambiguities"])
            episode_rows.append(
                {
                    "seed": episode["seed"],
                    "docking_distance": distance,
                    "racket_sha256": episode["racket_sha256"],
                    "public_path": public_path.relative_to(out).as_posix(),
                    "private_path": private_path.relative_to(out).as_posix(),
                    "ambiguities": len(episode["ambiguities"]),
                }
            )

        source_path = Path(__file__).resolve()
        test_path = source_path.parents[2] / "tests" / "test_parametric_variant.py"
        shutil.copy2(source_path, snapshots / source_path.name)
        shutil.copy2(test_path, snapshots / test_path.name)

        covered = {row["docking_distance"] for row in episode_rows}
        if covered != set(ALLOWED_DOCKING_DISTANCES):
            raise AssertionError(
                f"retained seeds cover distances {sorted(covered)}, expected "
                f"{list(ALLOWED_DOCKING_DISTANCES)}"
            )
        if ambiguity_count:
            raise AssertionError(
                f"retained episodes contain {ambiguity_count} ambiguity finding(s)"
            )

        report = {
            "schema": "arcpuzzles-proposed-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "status": "proposed_unapproved",
            "approved": False,
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
            "prototype_sha256": _sha256(source_path.read_bytes()),
            "parameter": {
                "name": "docking_distance",
                "allowed_values": list(ALLOWED_DOCKING_DISTANCES),
                "original_default": DEFAULT_DOCKING_DISTANCE,
                "selected_once_per_episode": True,
                "input_constraints_depend_on_parameter": False,
                "meaning": (
                    "Manhattan distance between the two equal-color marker "
                    "cells after each docking edge is applied"
                ),
            },
            "invariants": [
                "same irregular pieces, color roles, paired-marker tree, and crop",
                "same outward port inference and transitive tree placement",
                "distance 1 is byte-exact canonical behavior",
                "distance 2 leaves one background cell between paired markers",
            ],
            "episodes": episode_rows,
            "counts": {
                "episodes": len(episodes),
                "settings_covered": len(covered),
                "demonstrations": 3 * len(episodes),
                "queries": len(episodes),
                "ambiguous_parameter_rivals": ambiguity_count,
                "canonical_pairs_checked": replay["pairs_checked"],
                "racket_rule_applications": (
                    replay["pairs_checked"] + 8 * len(episodes)
                ),
            },
            "limits": [
                "finite evidence for two declared distances and retained seeds",
                "inputs remain the selected generator's five published morphology families",
                "refuting the declared distance rival does not prove universal induction",
                "distance 2 can create visually tight or overlapping bodies on other unseen morphologies",
                "prototype status does not change canonical approval or production APIs",
            ],
        }
        report["files"] = _files_manifest(out)
        _write_json(out / "report.json", report)
        return report
    except Exception as exc:
        _write_json(
            out / "failure.json",
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "seeds": list(seeds),
            },
        )
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
