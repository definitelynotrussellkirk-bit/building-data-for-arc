#!/usr/bin/env python3
"""Exhaustive local curriculum/override probe for generator 06b4c496c6cf.

Run from the staged repository through the packet wrapper, for example:

    python3 review.py run python3 generators/06b4c496c6cf/workspace/probe_curriculum.py \
      --out ../checks/curriculum-probe.json

The probe binds its report to the generator source hash, checks every cyclic
schedule start and every held-out query position for several seeds/bands,
verifies all declared canonical shortcuts really fit the canonical examples,
and exercises exact override boundaries.  It is task-specific evidence, not a
replacement for the shared battery or lesson census.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "06b4c496c6cf"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "probe_06b4c496c6cf_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _pair(grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def run_probe(seeds: list[int]) -> dict[str, Any]:
    root = find_root(__file__)
    generator_path = GENERATOR_PATH
    source_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    failures: list[dict[str, Any]] = []

    canonical = canonical_pairs(TASK_ID, root=root)
    canonical_checks = 0
    for rival_name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair_index, pair in enumerate(canonical):
            canonical_checks += 1
            try:
                actual = rival(pair["input"])
            except Exception as exc:  # pragma: no cover - retained evidence path
                failures.append(
                    {
                        "kind": "canonical_rival_error",
                        "rival": rival_name,
                        "pair_index": pair_index,
                        "error": repr(exc),
                    }
                )
                continue
            if actual != pair["output"]:
                failures.append(
                    {
                        "kind": "canonical_rival_mismatch",
                        "rival": rival_name,
                        "pair_index": pair_index,
                    }
                )

    cycle = len(GEN._TEXTURE_SCHEDULE)
    lesson_windows = 0
    query_rotations = 0
    unique_inputs: set[str] = set()
    for difficulty in ("easy", "medium", "hard"):
        for seed in seeds:
            for start in range(cycle):
                pairs = []
                textures = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                    unique_inputs.add(_grid_hash(grid))
                    pairs.append(_pair(grid))
                    textures.append(GEN.observe_overrides(grid)["texture"])
                lesson_windows += 1
                standard = GEN.lesson_identifiable(pairs[:-1], pairs[-1])
                if standard:
                    failures.append(
                        {
                            "kind": "standard_lesson",
                            "difficulty": difficulty,
                            "seed": seed,
                            "start": start,
                            "textures": textures,
                            "reasons": standard,
                        }
                    )
                for query_index, query in enumerate(pairs):
                    query_rotations += 1
                    demos = [
                        pair for index, pair in enumerate(pairs) if index != query_index
                    ]
                    reasons = GEN.lesson_identifiable(demos, query)
                    if reasons:
                        failures.append(
                            {
                                "kind": "query_rotation",
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "textures": textures,
                                "reasons": reasons,
                            }
                        )

    override_cases = 0
    declared_incompatible = 0
    for difficulty in (None, "easy", "medium", "hard"):
        for texture in GEN.TEXTURES:
            for grid_h, grid_w in ((10, 12), (18, 22)):
                for marker_count in (1, 2, 6):
                    request = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "marker_count": marker_count,
                        "texture": texture,
                    }
                    incompatible = texture in {"overlap_pair", "pair_markers"} and marker_count == 1
                    if incompatible:
                        declared_incompatible += 1
                        try:
                            GEN.generate(99173, override_cases, difficulty=difficulty, **request)
                        except ValueError:
                            continue
                        failures.append(
                            {
                                "kind": "declared_incompatible_accepted",
                                "difficulty": difficulty,
                                "request": request,
                            }
                        )
                        continue

                    override_cases += 1
                    try:
                        grid = GEN.generate(
                            99173,
                            override_cases,
                            difficulty=difficulty,
                            **request,
                        )
                    except Exception as exc:
                        failures.append(
                            {
                                "kind": "override_generation_error",
                                "difficulty": difficulty,
                                "request": request,
                                "error": repr(exc),
                            }
                        )
                        continue
                    observed = GEN.observe_overrides(grid)
                    self_check = GEN.self_check(grid, difficulty=difficulty)
                    if observed != request or self_check:
                        failures.append(
                            {
                                "kind": "override_contract",
                                "difficulty": difficulty,
                                "request": request,
                                "observed": observed,
                                "self_check": self_check,
                            }
                        )

    return {
        "schema": "06b4c496c6cf-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "generator_sha256": source_sha,
        "seeds": seeds,
        "bands": ["easy", "medium", "hard"],
        "schedule": list(GEN._TEXTURE_SCHEDULE),
        "examples_needed": GEN.EXAMPLES_NEEDED,
        "declared_competitors": sorted(GEN.LESSON_COMPETITORS),
        "canonical_pairs": len(canonical),
        "canonical_rival_checks": canonical_checks,
        "lesson_windows": lesson_windows,
        "query_rotations": query_rotations,
        "unique_generated_inputs": len(unique_inputs),
        "override_cases": override_cases,
        "declared_incompatible_cases": declared_incompatible,
        "failure_count": len(failures),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seeds",
        default="1701,22691,81173",
        help="comma-separated integer seeds",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = run_probe(seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
