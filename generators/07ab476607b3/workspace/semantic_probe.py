#!/usr/bin/env python3
"""Task-local semantic census for generator 07ab476607b3.

This is intentionally independent of the repository battery. It gives future
reviewers a fast, readable answer to four questions:

* Are every declared axis and boundary override exactly observable?
* Does every difficulty band retain all canonical grid profiles?
* Do the scheduled semantic witnesses actually fire?
* Does each claimed witness separate its named rival rule?

Run from anywhere::

    python3 workspace/semantic_probe.py --per-band 20 --json-out report.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "07ab476607b3"
TASK_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"semantic_probe_{TASK_ID}", TASK_HOME / "generator.py"
    )
    if not spec or not spec.loader:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [
                    pair
                    for split in ("train", "test")
                    for pair in row.get(split, [])
                ]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _override_cases() -> list[dict[str, Any]]:
    return [
        {"grid_h": 10},
        {"grid_h": 13},
        {"grid_w": 11},
        {"grid_w": 15},
        {"a_size": 4},
        {"a_size": 7},
        {"texture": "plain"},
        {"texture": "disjoint_b"},
        {"texture": "clip"},
        {"texture": "empty_diff"},
        {"grid_h": 13, "grid_w": 15, "a_size": 7, "texture": "disjoint_b"},
    ]


def run_probe(per_band: int, seed: int) -> dict[str, Any]:
    gen = _load_generator()
    failures: list[str] = []

    canonical = []
    for index, pair in enumerate(_canonical_pairs()):
        check = gen.self_check(pair["input"])
        mirrored = gen.rule_mirror(pair["input"])
        ok = not check and mirrored == pair["output"]
        canonical.append({"index": index, "accepted": not check, "mirror_exact": mirrored == pair["output"]})
        if not ok:
            failures.append(f"canonical pair {index} failed: {check}")

    bands: dict[str, Any] = {}
    for band in ("easy", "medium", "hard"):
        profile_counts: Counter[str] = Counter()
        texture_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        rival_refutations: Counter[str] = Counter()
        errors: list[dict[str, Any]] = []
        for index in range(per_band):
            grid = gen.generate(seed, index, difficulty=band)
            info = gen.analyze(grid)
            if info["errors"]:
                errors.append({"index": index, "errors": info["errors"]})
                continue
            profile_counts[f"{info['grid_h']}x{info['grid_w']}"] += 1
            texture_counts[str(info["texture"])] += 1
            authoritative = gen.rule_mirror(grid)
            if authoritative != info["output"]:
                errors.append({"index": index, "errors": ["analyzer/mirror mismatch"]})
            for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
                if not predicate(grid):
                    continue
                witness_counts[witness_name] += 1
                for rival_name in gen.WITNESS_RIVALS.get(witness_name, []):
                    if gen.SEMANTIC_RIVALS[rival_name](grid) != authoritative:
                        rival_refutations[f"{witness_name}:{rival_name}"] += 1
        if errors:
            failures.append(f"{band}: {len(errors)} malformed/mismatched sample(s)")
        missing_profiles = {
            "10x11", "10x12", "11x11", "11x12"
        } - set(profile_counts)
        if missing_profiles:
            failures.append(f"{band}: missing canonical profiles {sorted(missing_profiles)}")
        missing_textures = set(gen.HELPFUL_TEXTURES) - set(texture_counts)
        if missing_textures:
            failures.append(f"{band}: missing helpful textures {sorted(missing_textures)}")
        missing_witnesses = set(gen.SEMANTIC_WITNESSES) - set(witness_counts)
        if missing_witnesses:
            failures.append(f"{band}: missing witnesses {sorted(missing_witnesses)}")
        for witness_name, rival_names in gen.WITNESS_RIVALS.items():
            for rival_name in rival_names:
                key = f"{witness_name}:{rival_name}"
                if rival_refutations[key] == 0:
                    failures.append(f"{band}: witness did not refute {key}")
        bands[band] = {
            "profiles": dict(sorted(profile_counts.items())),
            "textures": dict(sorted(texture_counts.items())),
            "witnesses": dict(sorted(witness_counts.items())),
            "rival_refutations": dict(sorted(rival_refutations.items())),
            "errors": errors,
        }

    override_rows: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for index, requested in enumerate(_override_cases()):
            try:
                grid = gen.generate(seed + index, index, difficulty=band, **requested)
                observed = gen.observe_overrides(grid)
                mismatches = {
                    key: {"requested": value, "observed": observed.get(key)}
                    for key, value in requested.items()
                    if observed.get(key) != value
                }
            except Exception as exc:  # counted and reported, never hidden
                observed = None
                mismatches = {"exception": f"{type(exc).__name__}: {exc}"}
            override_rows.append(
                {
                    "band": band,
                    "requested": requested,
                    "observed": observed,
                    "mismatches": mismatches,
                }
            )
            if mismatches:
                failures.append(f"{band} override {requested} failed: {mismatches}")

    try:
        gen.generate(seed, 0, __semantic_probe_unknown_axis__=1)
    except ValueError:
        unknown_override_rejected = True
    else:
        unknown_override_rejected = False
        failures.append("unknown override key was accepted")

    degenerate = gen.generate(seed, 0, texture="no_anchor")
    degenerate_findings = gen.self_check(degenerate)
    if not any("anchor" in finding for finding in degenerate_findings):
        failures.append("no_anchor negative fixture was not rejected by self_check")

    lesson_grids = [gen.generate(seed, index, difficulty="medium") for index in range(4)]
    lesson_demos = [
        {"input": grid, "output": gen.rule_mirror(grid)} for grid in lesson_grids[:3]
    ]
    lesson_query = {
        "input": lesson_grids[3],
        "output": gen.rule_mirror(lesson_grids[3]),
    }
    lesson_findings = gen.lesson_identifiable(lesson_demos, lesson_query)
    if lesson_findings:
        failures.append(f"first scheduled lesson not identifiable: {lesson_findings}")

    return {
        "schema": "07ab476607b3-semantic-probe-v1",
        "task_id": TASK_ID,
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "per_band": per_band,
        "seed": seed,
        "passed": not failures,
        "failures": failures,
        "canonical": canonical,
        "bands": bands,
        "override_cases": override_rows,
        "unknown_override_rejected": unknown_override_rejected,
        "no_anchor_findings": degenerate_findings,
        "lesson_findings": lesson_findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260928)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = run_probe(args.per_band, args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
