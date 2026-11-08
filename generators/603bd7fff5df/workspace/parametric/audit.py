#!/usr/bin/env python3
"""Reusable bounded learnability and control audit for the halo-depth family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

HERE = Path(__file__).resolve().parent
_PROTO_PATH = HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_audit_parametric_603bd7fff5df_" + hashlib.sha256(str(_PROTO_PATH).encode()).hexdigest(),
    _PROTO_PATH,
)
PROTO = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(PROTO)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_audit(*, seeds: Iterable[int], demo_counts: Iterable[int]) -> dict:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or not demo_counts:
        raise ValueError("seeds and demo_counts must be nonempty")
    failures: list[dict] = []
    episodes_count = pair_count = stress_count = 0
    retained: list[dict] = []

    for seed in seeds:
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("audit seeds must be exact integers in 0..2^63-1")
        minimum_episodes = {
            depth: PROTO.generate(seed, {"halo_depth": depth}, PROTO.MIN_DEMOS, 4)
            for depth in PROTO.HALO_DEPTHS
        }
        for demos in demo_counts:
            if type(demos) is not int or not PROTO.MIN_DEMOS <= demos <= PROTO.MAX_DEMOS:
                raise ValueError("audit demonstration counts must be supported exact integers")
            episodes = (minimum_episodes if demos == PROTO.MIN_DEMOS else {
                depth: PROTO.generate(seed, {"halo_depth": depth}, demos, 4)
                for depth in PROTO.HALO_DEPTHS
            })
            reference_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes[PROTO.DEFAULT_HALO_DEPTH][split]
            ]
            if len({_frozen(grid) for grid in reference_inputs}) != demos + 4:
                failures.append({"seed": seed, "demos": demos, "kind": "duplicate_inputs"})
            for depth, episode in episodes.items():
                episodes_count += 1
                pair_count += demos + 4
                inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                if inputs != reference_inputs:
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "unmatched_inputs"})
                errors = PROTO.episode_errors(episode)
                if errors:
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "episode_errors", "errors": errors})
                expected = {"setting_survivors": [depth], "plausible_rival_survivors": []}
                certificate = PROTO.teaching_certificate(episode)
                if certificate != expected:
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "teaching", "certificate": certificate})
                one = PROTO.generate(seed, {"halo_depth": depth}, demos, 1)
                minimum = minimum_episodes[depth]
                if one["train"] != episode["train"] or one["test"] != episode["test"][:1]:
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "query_prefix"})
                if minimum["train"] != episode["train"][: PROTO.MIN_DEMOS] or minimum["test"] != episode["test"]:
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "demo_prefix"})
                stress = episode["test"][-1]["input"]
                if (len(stress), len(stress[0])) != (30, 30):
                    failures.append({"seed": seed, "demos": demos, "depth": depth, "kind": "missing_30x30"})
                else:
                    stress_count += 1
                if len(retained) < len(PROTO.HALO_DEPTHS):
                    retained.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": episode["settings"],
                        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
                        "teaching_certificate": certificate,
                        "stress_input_sha256": hashlib.sha256(json.dumps(stress, separators=(",", ":")).encode()).hexdigest(),
                    })

    return {
        "schema": "603bd7fff5df-parametric-audit-v1",
        "status": "passed" if not failures else "failed",
        "task_id": PROTO.TASK_ID,
        "prototype_version": PROTO.PROTOTYPE_VERSION,
        "source_sha256": {
            "prototype.py": _source_hash(_PROTO_PATH),
            "audit.py": _source_hash(Path(__file__).resolve()),
            "canonical.rkt": _source_hash(HERE / "canonical.rkt"),
            "halo-depth-0.rkt": _source_hash(HERE / "halo-depth-0.rkt"),
            "halo-depth-2.rkt": _source_hash(HERE / "halo-depth-2.rkt"),
        },
        "counts": {
            "seeds": len(seeds),
            "demo_counts": len(demo_counts),
            "settings": len(PROTO.HALO_DEPTHS),
            "episodes": episodes_count,
            "pairs": pair_count,
            "thirty_by_thirty_queries": stress_count,
        },
        "finite_rivals": sorted(PROTO.PLAUSIBLE_RIVALS),
        "failures": failures,
        "retained_cases": retained,
        "limits": (
            "Finite deterministic seed/count sweep over the three declared settings and five authored rivals; "
            "not a proof against every possible rule. Protected Racket execution is supplied by native qualification."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=128)
    parser.add_argument("--demos", type=int, nargs="+", default=list(range(2, 7)))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.seed_count < 1:
        raise SystemExit("--seed-count must be positive")
    report = run_audit(
        seeds=range(args.seed_start, args.seed_start + args.seed_count),
        demo_counts=args.demos,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "out": str(args.out)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
