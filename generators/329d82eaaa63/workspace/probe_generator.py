#!/usr/bin/env python3
"""Portable evidence probe for generator 329d82eaaa63.

This is intentionally independent of the battery controller.  It gives a future
reviewer one command that checks canonical parity, the four-profile schedule,
all three-of-four query rotations, witness/rival linkage, exact boundary
overrides, and structured width/seed incompatibility.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "329d82eaaa63"


def _root(start: str | Path) -> Path:
    path = Path(start).resolve()
    if path.is_file():
        path = path.parent
    for candidate in (path, *path.parents):
        if (candidate / "generators" / TASK_ID / "generator.py").is_file() and (
            (candidate / "shared/data/canonical/puzzles.jsonl").is_file()
            or (candidate / "data/canonical/puzzles.jsonl").is_file()
        ):
            return candidate
    raise FileNotFoundError(f"could not find task runtime above {start}")


ROOT = _root(__file__)
for candidate in (ROOT / "shared/runtime", ROOT / "src", ROOT):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from reviewer_support import canonical_pairs  # noqa: E402


def _load_generator():
    path = ROOT / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _rotation_report(gen, *, seed: int, per_profile: int) -> dict[str, Any]:
    bands = (None, "easy", "medium", "hard")
    checked = ambiguous = 0
    details = []
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    profile_hits = {name: 0 for name in gen.SCHEDULE_PROFILES}

    for band_index, band in enumerate(bands):
        for block in range(per_profile):
            base = block * len(gen.SCHEDULE_PROFILES)
            grids = [
                gen.generate(seed + 1000 * band_index + block, base + offset, difficulty=band)
                for offset in range(len(gen.SCHEDULE_PROFILES))
            ]
            pairs = [
                {"input": copy.deepcopy(grid), "output": gen.rule_mirror(grid)}
                for grid in grids
            ]
            for offset, grid in enumerate(grids):
                profile_hits[gen.schedule_profile(seed, base + offset, band)] += 1
                for name, predicate in gen.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += int(bool(predicate(grid)))

            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                hook = gen.lesson_identifiable(demos, query)
                survivors = []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if all(rival(demo["input"]) == demo["output"] for demo in demos):
                        if rival(query["input"]) != query["output"]:
                            survivors.append(name)
                checked += 1
                if hook or survivors:
                    ambiguous += 1
                    details.append(
                        {
                            "band": band,
                            "block": block,
                            "query_index": query_index,
                            "hook": hook,
                            "survivors": survivors,
                        }
                    )
    return {
        "checked": checked,
        "ambiguous": ambiguous,
        "details": details,
        "profile_hits": profile_hits,
        "witness_hits": witness_hits,
    }


def _override_report(gen, *, seed: int) -> tuple[dict[str, Any], list[str]]:
    errors = []
    cases = [
        {"grid_h": 3},
        {"grid_h": 18},
        {"grid_w": 4},
        {"grid_w": 24},
        {"n_seeds": 1},
        {"n_seeds": 8},
        {"grid_h": 3, "grid_w": 4, "n_seeds": 1},
        {"grid_h": 18, "grid_w": 24, "n_seeds": 8},
    ]
    observations = []
    for band in (None, "easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(seed + index, index, difficulty=band, **requested)
            observed = gen.observe_overrides(grid)
            mismatch = {key: (value, observed.get(key)) for key, value in requested.items() if observed.get(key) != value}
            if mismatch:
                errors.append(f"{band=} {requested=}: observed mismatch {mismatch}")
            if gen.self_check(grid, difficulty=band):
                errors.append(f"{band=} {requested=}: self_check failed")
            observations.append({"band": band, "requested": requested, "observed": observed})

    structured = False
    try:
        gen.generate(seed, 0, grid_w=4, n_seeds=2)
    except ValueError as exc:
        structured = set(getattr(exc, "incompatible_axes", ())) == {"grid_w", "n_seeds"}
    if not structured:
        errors.append("grid_w=4,n_seeds=2 lacked structured incompatible_axes")

    unknown_rejected = False
    try:
        gen.generate(seed, 0, typo_axis=1)
    except (TypeError, ValueError, KeyError):
        unknown_rejected = True
    if not unknown_rejected:
        errors.append("unknown override was accepted")

    return {
        "cases": len(observations),
        "observations": observations,
        "structured_incompatibility": structured,
        "unknown_key_rejected": unknown_rejected,
    }, errors


def build_report(seed: int, per_profile: int) -> dict[str, Any]:
    gen, source = _load_generator()
    errors: list[str] = []

    canonical = canonical_pairs(TASK_ID, root=ROOT)
    matched = 0
    for pair in canonical:
        reasons = gen.self_check(pair["input"])
        mirror = gen.rule_mirror(pair["input"])
        if reasons:
            errors.append(f"canonical {pair['split']}[{pair['pair_index']}] rejected: {reasons}")
        elif mirror != pair["output"]:
            errors.append(f"canonical {pair['split']}[{pair['pair_index']}] mirror mismatch")
        else:
            matched += 1

    rotations = _rotation_report(gen, seed=seed, per_profile=per_profile)
    if rotations["ambiguous"]:
        errors.append(f"{rotations['ambiguous']} rotated lessons were ambiguous")
    missing_profiles = [name for name, count in rotations["profile_hits"].items() if not count]
    missing_witnesses = [name for name, count in rotations["witness_hits"].items() if not count]
    if missing_profiles:
        errors.append(f"unvisited schedule profiles: {missing_profiles}")
    if missing_witnesses:
        errors.append(f"unfired semantic witnesses: {missing_witnesses}")

    overrides, override_errors = _override_report(gen, seed=seed)
    errors.extend(override_errors)

    unique = set()
    outputs = set()
    for index in range(80):
        grid = gen.generate(seed + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        unique.add(_freeze(grid))
        outputs.add(_freeze(gen.rule_mirror(grid)))
    if len(unique) < 70 or len(outputs) < 70:
        errors.append(f"low diversity: inputs={len(unique)}, outputs={len(outputs)}")

    return {
        "schema": "329d82eaaa63-review-probe-v1",
        "task_id": TASK_ID,
        "status": "clean" if not errors else "issues",
        "errors": errors,
        "source": {
            "path": str(source.relative_to(ROOT)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "version": gen.VERSION,
            "rule_hash": gen.RULE_HASH,
        },
        "canonical": {"total": len(canonical), "matched": matched},
        "rotations": rotations,
        "overrides": overrides,
        "diversity": {"draws": 80, "unique_inputs": len(unique), "unique_outputs": len(outputs)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=329)
    parser.add_argument("--per-profile", type=int, default=5)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_profile <= 0:
        parser.error("--per-profile must be positive")

    report = build_report(args.seed, args.per_profile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "canonical": report["canonical"],
                "rotations": {
                    "checked": report["rotations"]["checked"],
                    "ambiguous": report["rotations"]["ambiguous"],
                },
                "diversity": report["diversity"],
                "out": str(args.out),
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
