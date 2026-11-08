#!/usr/bin/env python3
"""Bounded learnability and grammar audit for the 97c9b7818f99 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ADAPTER = HERE / "adapter.py"


def _adapter():
    name = "_97c9_parametric_audit_" + hashlib.sha256(str(ADAPTER).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load adapter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict) -> list:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run_audit(*, seed_start: int, seed_count: int) -> dict:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative exact integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 256:
        raise ValueError("seed_count must be an exact integer in 1..256")
    module = _adapter()
    failures: list[str] = []
    episodes = 0
    exact_30x30_pairs = 0
    gray_seed_pairs = 0
    min_region_cells = None
    max_region_cells = 0
    for seed in range(seed_start, seed_start + seed_count):
        for demos in (2, 3, 6):
            by_mode = {}
            for mode in module.MODES:
                try:
                    episode = module.generate(seed, {"finish": mode}, demos, 4)
                    certificate = module.certificate(
                        episode["train"], [pair["input"] for pair in episode["test"]]
                    )
                    if certificate["survivors"] != [mode]:
                        failures.append(
                            f"seed {seed} demos {demos} mode {mode}: survivors {certificate['survivors']}"
                        )
                    missing = set(module.HYPOTHESES) - {mode} - set(certificate["query_disagreements"])
                    if missing:
                        failures.append(
                            f"seed {seed} demos {demos} mode {mode}: query-agreeing rivals {sorted(missing)}"
                        )
                    by_mode[mode] = episode
                    for pair in episode["train"] + episode["test"]:
                        info = module.observe(pair["input"])
                        exact_30x30_pairs += int(
                            (len(pair["input"]), len(pair["input"][0])) == (30, 30)
                        )
                        gray_seed_pairs += int(info["includes_gray_seed"])
                        local_min = min(info["region_sizes"].values())
                        min_region_cells = local_min if min_region_cells is None else min(min_region_cells, local_min)
                        max_region_cells = max(max_region_cells, max(info["region_sizes"].values()))
                    episodes += 1
                except Exception as exc:
                    failures.append(
                        f"seed {seed} demos {demos} mode {mode}: {type(exc).__name__}: {exc}"
                    )
            if set(by_mode) == set(module.MODES):
                left, right = (by_mode[mode] for mode in module.MODES)
                if _inputs(left) != _inputs(right):
                    failures.append(f"seed {seed} demos {demos}: inputs depend on hidden setting")
    source_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            ADAPTER,
            HERE / "canonical.rkt",
            HERE / "highlight_smallest_region.rkt",
            HERE / "skip_region_sizes.rkt",
        )
    }
    return {
        "schema": "97c9b7818f99-parametric-self-audit-v1",
        "status": "passed" if not failures else "failed",
        "seed_start": seed_start,
        "seed_count": seed_count,
        "demo_counts": [2, 3, 6],
        "query_count": 4,
        "settings": list(module.MODES),
        "declared_hypotheses": len(module.HYPOTHESES),
        "episodes": episodes,
        "exact_30x30_pairs": exact_30x30_pairs,
        "gray_seed_pairs": gray_seed_pairs,
        "observed_region_size_range": [min_region_cells, max_region_cells],
        "source_sha256": source_hashes,
        "failures": failures,
        "scope": "Finite deterministic Python-mirror audit; protected Racket parity is checked by focused tests and native qualification.",
    }


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=32)
    args = parser.parse_args()
    report = run_audit(seed_start=args.seed_start, seed_count=args.seed_count)
    write_report(args.out, report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "episodes",
                    "exact_30x30_pairs",
                    "gray_seed_pairs",
                    "failures",
                )
            }
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
