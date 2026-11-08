#!/usr/bin/env python3
"""Bounded adversarial replay for the 2dacb90452ce scale-factor prototype.

The script writes machine-readable JSON itself so the outer Racket runner's
console preamble can be retained separately without corrupting the evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "2dacb90452ce"
WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
PROTOTYPE_PATH = REPO / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_prototype():
    spec = importlib.util.spec_from_file_location("scale_factor_prototype_probe", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prototype: {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid_key(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_probe() -> dict:
    module = _load_prototype()
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=REPO)
    findings: list[dict] = []
    sampler_cases = 0
    sampler_inputs = 0

    random.seed(0x2DACB904)
    random_state = random.getstate()
    for seed_offset in range(16):
        for demo_count in (1, 2, 3):
            for query_count in (4, 6):
                sampler_cases += 1
                seed = 41_000 + seed_offset
                try:
                    grids = module.generate_inputs(
                        seed,
                        demo_count=demo_count,
                        query_count=query_count,
                        root=REPO,
                    )
                    expected = demo_count + query_count
                    sampler_inputs += len(grids)
                    if len(grids) != expected:
                        findings.append(
                            {
                                "surface": "sampler_count",
                                "seed": seed,
                                "demo_count": demo_count,
                                "query_count": query_count,
                                "expected": expected,
                                "actual": len(grids),
                            }
                        )
                    if len({_grid_key(grid) for grid in grids}) != len(grids):
                        findings.append(
                            {
                                "surface": "sampler_uniqueness",
                                "seed": seed,
                                "demo_count": demo_count,
                                "query_count": query_count,
                            }
                        )
                    for index, grid in enumerate(grids):
                        errors = generator.self_check(grid)
                        if errors:
                            findings.append(
                                {
                                    "surface": "sampler_lawfulness",
                                    "seed": seed,
                                    "index": index,
                                    "errors": list(errors),
                                }
                            )
                        height = len(grid)
                        width = len(grid[0]) if grid else 0
                        if not (2 <= height == width <= 5 and height * 3 <= 30 and width * 3 <= 30):
                            findings.append(
                                {
                                    "surface": "sampler_bounds",
                                    "seed": seed,
                                    "index": index,
                                    "shape": [height, width],
                                }
                            )
                        if any(type(cell) is not int for row in grid for cell in row):
                            findings.append(
                                {
                                    "surface": "sampler_numeric_types",
                                    "seed": seed,
                                    "index": index,
                                }
                            )
                except Exception as exc:  # retained bounded evidence, not silent failure
                    findings.append(
                        {
                            "surface": "sampler_exception",
                            "seed": seed,
                            "demo_count": demo_count,
                            "query_count": query_count,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
    if random.getstate() != random_state:
        findings.append({"surface": "global_rng_state", "error": "sampler changed global RNG state"})

    racket_episodes = 0
    racket_labels = 0
    counterfactual_labels = 0
    public_projection_checks = 0
    with RacketBridge() as bridge:
        for seed in range(52_000, 52_016):
            try:
                episode = module.generate_episode(
                    bridge,
                    seed,
                    demo_count=2,
                    query_count=4,
                    root=REPO,
                )
                racket_episodes += 1
                factor = episode["parameters"]["scale_factor"]
                program = module.program_for_scale_factor(factor, root=REPO)
                analysis = module.analyze_episode(bridge, episode, root=REPO)
                if analysis["status"] != "no_ambiguity_found":
                    findings.append(
                        {
                            "surface": "lesson_identifiability",
                            "seed": seed,
                            "analysis": analysis,
                        }
                    )
                counterfactual_labels += len(analysis["pair_checks"])
                for index, pair in enumerate(episode["pairs"]):
                    racket_labels += 1
                    expected = module.evaluate(bridge, program, pair["input"])
                    if pair["output"] != expected:
                        findings.append(
                            {"surface": "racket_parity", "seed": seed, "pair_index": index}
                        )
                    in_height = len(pair["input"])
                    in_width = len(pair["input"][0])
                    out_height = len(pair["output"])
                    out_width = len(pair["output"][0])
                    if [out_height, out_width] != [in_height * factor, in_width * factor]:
                        findings.append(
                            {
                                "surface": "racket_shape",
                                "seed": seed,
                                "pair_index": index,
                                "factor": factor,
                                "input_shape": [in_height, in_width],
                                "output_shape": [out_height, out_width],
                            }
                        )
                    if any(type(cell) is not int for row in pair["output"] for cell in row):
                        findings.append(
                            {"surface": "racket_numeric_types", "seed": seed, "pair_index": index}
                        )

                public = module.public_challenge(episode)
                payload = public_challenge_bytes(public)
                public_id = public_challenge_id(public)
                public_projection_checks += 1
                if set(public) != {"train", "test"} or len(public["train"]) != 2 or len(public["test"]) != 4:
                    findings.append({"surface": "public_counts", "seed": seed})
                if any(set(pair) != {"input"} for pair in public["test"]):
                    findings.append({"surface": "public_query_answers", "seed": seed})
                lowered = payload.decode("utf-8").lower()
                leaked = [
                    term
                    for term in ("seed", "scale_factor", "racket", "parameters", "rival", "sha256")
                    if term in lowered
                ]
                if leaked:
                    findings.append({"surface": "public_field_leakage", "seed": seed, "terms": leaked})

                altered = deepcopy(episode)
                altered["seed"] = seed + 999_999
                altered["parameters"]["scale_factor"] = 3 if factor == 2 else 2
                for pair in altered["pairs"][2:]:
                    pair["output"] = [[9]]
                altered_public = module.public_challenge(altered)
                if public_challenge_bytes(altered_public) != payload or public_challenge_id(altered_public) != public_id:
                    findings.append({"surface": "public_id_private_dependence", "seed": seed})
            except Exception as exc:  # retain exact bounded failure if one appears
                findings.append(
                    {
                        "surface": "racket_episode_exception",
                        "seed": seed,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    report = {
        "schema": "scale-factor-adversarial-v2",
        "status": "no_findings" if not findings else "findings",
        "findings": findings,
        "sampler_cases": sampler_cases,
        "sampler_inputs": sampler_inputs,
        "racket_episodes": racket_episodes,
        "racket_labels": racket_labels,
        "counterfactual_labels": counterfactual_labels,
        "public_projection_checks": public_projection_checks,
        "probe_scope": {
            "sampler_seeds": [41_000, 41_015],
            "demo_counts": [1, 2, 3],
            "query_counts": [4, 6],
            "episode_seeds": [52_000, 52_015],
            "declared_rivals": [2, 3],
        },
        "sources": {
            "generator_path": generator_path.relative_to(REPO).as_posix(),
            "generator_sha256": generator_sha,
            "prototype_path": PROTOTYPE_PATH.relative_to(REPO).as_posix(),
            "prototype_sha256": _sha256(PROTOTYPE_PATH),
            "rule_sha256": {
                str(factor): module.sha256(module.program_for_scale_factor(factor, root=REPO))
                for factor in module.SCALE_FACTORS
            },
        },
        "limits": [
            "Finite deterministic seeds only.",
            "Identifiability is checked only against the declared alternative scale factor.",
            "This probe does not grant production, variant, or training approval.",
        ],
    }
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.out.exists() and not args.overwrite:
        parser.error(f"refusing to overwrite existing file: {args.out}")
    report = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "out": str(args.out.resolve()),
                "status": report["status"],
                "findings": len(report["findings"]),
            },
            sort_keys=True,
        )
    )
    return 0 if not report["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
