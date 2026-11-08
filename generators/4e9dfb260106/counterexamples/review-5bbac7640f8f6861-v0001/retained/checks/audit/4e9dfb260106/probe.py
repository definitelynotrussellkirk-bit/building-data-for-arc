#!/usr/bin/env python3
"""Reproduce the median-size shortcut for audit target 4e9dfb260106."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, deque
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generator_4e", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def components(grid, color: int):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        q = deque([start])
        cells = {start}
        while q:
            r, c = q.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    cells.add((nr, nc))
                    q.append((nr, nc))
        found.append(cells)
    return found


def crop_mask(cells):
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return [
        [1 if (r, c) in cells else 0 for c in range(left, right + 1)]
        for r in range(top, bottom + 1)
    ]


def median_size_rival(grid):
    blue = sorted(components(grid, 1), key=lambda cells: len(cells))
    if len(blue) != 3 or len({len(cells) for cells in blue}) != 3:
        return [[0]]
    return crop_mask(blue[1])


def grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--per-band", type=int, default=300)
    args = parser.parse_args()
    root = args.root.resolve()
    out_dir = Path(__file__).resolve().parent
    generator_path = root / "repo/generators/4e9dfb260106/generator.py"
    episode_path = out_dir / "episode.jsonl"
    gen = load_module(generator_path)
    episode = json.loads(episode_path.read_text().splitlines()[0])

    exact_pairs = episode["train"] + episode["test"]
    exact = []
    for i, pair in enumerate(exact_pairs):
        grid = pair["input"]
        rival = median_size_rival(grid)
        profile = gen.observe_overrides(grid).get("scene_profile")
        exact.append({
            "split": "train" if i < len(episode["train"]) else "test",
            "pair_index": i if i < len(episode["train"]) else i - len(episode["train"]),
            "sample_index": episode["sample_indices"][i],
            "profile": profile,
            "self_check": gen.self_check(grid, difficulty="medium"),
            "input_sha256": grid_hash(grid),
            "actual_output_sha256": grid_hash(pair["output"]),
            "rival_output_sha256": grid_hash(rival),
            "rival_matches_actual": rival == pair["output"],
        })
    if not all(row["rival_matches_actual"] for row in exact[:3]):
        raise AssertionError("median rival must fit all three retained demonstrations")
    if exact[3]["rival_matches_actual"]:
        raise AssertionError("median rival must fail the retained query")
    if any(row["self_check"] for row in exact):
        raise AssertionError("retained inputs must pass self_check")

    query_grid = episode["test"][0]["input"]
    (out_dir / "input.json").write_text(json.dumps(query_grid, indent=2) + "\n")
    (out_dir / "rival-output.json").write_text(
        json.dumps(median_size_rival(query_grid), indent=2) + "\n"
    )

    bands = {}
    total_survivors = 0
    total_wrong_queries = 0
    profile_counts = Counter()
    for band in ("easy", "medium", "hard"):
        survivors = 0
        wrong_queries = 0
        full_equivalence = 0
        band_profiles = Counter()
        for seed in range(args.per_band):
            rows = []
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError((band, seed, sample_index, errors))
                profile = gen.observe_overrides(grid)["scene_profile"]
                band_profiles[profile] += 1
                actual = gen.rule_mirror(grid)
                rival = median_size_rival(grid)
                rows.append(actual == rival)
            demos_fit = all(rows[:3])
            if demos_fit:
                survivors += 1
                if rows[3]:
                    full_equivalence += 1
                else:
                    wrong_queries += 1
        bands[band] = {
            "lessons": args.per_band,
            "demonstrations_per_lesson": 3,
            "queries_per_lesson": 1,
            "rival_survives_all_demonstrations": survivors,
            "surviving_rival_wrong_on_query": wrong_queries,
            "surviving_rival_equivalent_on_query": full_equivalence,
            "profile_occurrences": dict(sorted(band_profiles.items())),
        }
        total_survivors += survivors
        total_wrong_queries += wrong_queries
        profile_counts.update(band_profiles)

    report = {
        "schema": "arc-audit-median-size-shortcut-v1",
        "task_id": "4e9dfb260106",
        "finding": (
            "The ordinary sampler heavily favors profiles where the count-matching "
            "blue component is the median-sized blue component. A learner can fit "
            "three demonstrations with that shortcut and fail a lawful query."
        ),
        "generator": {
            "version": getattr(gen, "VERSION", None),
            "sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
            "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        },
        "retained_production_lesson": {
            "generation": {
                "seed": episode["seed"],
                "difficulty": episode["provenance"]["difficulty"],
                "sample_indices": episode["sample_indices"],
                "overrides": episode["provenance"]["overrides"],
                "train": len(episode["train"]),
                "test": len(episode["test"]),
            },
            "profiles": [row["profile"] for row in exact],
            "pair_checks": exact,
            "rival_fits_demos": True,
            "rival_fails_query": True,
            "query_differing_cells": sum(
                a != b
                for row_a, row_b in zip(episode["test"][0]["output"], median_size_rival(query_grid))
                for a, b in zip(row_a, row_b)
            ) if (
                len(episode["test"][0]["output"]) == len(median_size_rival(query_grid))
                and all(len(a) == len(b) for a, b in zip(episode["test"][0]["output"], median_size_rival(query_grid)))
            ) else None,
            "lesson_check": episode["lesson_check"],
            "executed_rule_hash": episode["executed_rule_hash"],
        },
        "diagnostic_census": {
            "label_source": "generator rule_mirror; exact retained lesson is separately bound to canonical Racket labels",
            "per_band": args.per_band,
            "total_lessons": args.per_band * 3,
            "total_pair_draws": args.per_band * 3 * 4,
            "rival_survives_all_demonstrations": total_survivors,
            "surviving_rival_wrong_on_query": total_wrong_queries,
            "bands": bands,
            "profile_occurrences": dict(sorted(profile_counts.items())),
        },
        "rival": {
            "name": "always return the median-sized blue component",
            "definition": (
                "Find the three 4-connected blue components, sort them by cell count, "
                "and return the binary bbox crop of the middle-sized component; ignore red."
            ),
        },
        "scope": (
            "The census is finite and uses the generator's Python mirror for labels. "
            "The retained seed-8 episode was materialized by the supported generate command "
            "and its query is independently checked with canonical Racket apply."
        ),
    }

    racket_path = out_dir / "racket.json"
    if racket_path.exists():
        receipt = json.loads(racket_path.read_text())
        results = receipt.get("results", [])
        if len(results) != 1 or results[0].get("error") is not None:
            raise AssertionError("unexpected Racket apply receipt")
        racket_output = results[0]["output"]
        expected = episode["test"][0]["output"]
        rival = median_size_rival(query_grid)
        if racket_output != expected:
            raise AssertionError("Racket output does not match generated query label")
        if racket_output == rival:
            raise AssertionError("Racket output unexpectedly matches median rival")
        report["racket_verification"] = {
            "status": "passed",
            "command": [
                "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
                "4e9dfb260106", "--input", "../checks/audit/4e9dfb260106/input.json",
                "--out", "../checks/audit/4e9dfb260106/racket.json",
            ],
            "cwd": "packet_root",
            "exit_code": 0,
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "input_sha256": results[0].get("input_sha256"),
            "output_sha256": results[0].get("output_sha256"),
            "matches_generated_label": True,
            "differs_from_rival": True,
        }

    (out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "exact_profiles": report["retained_production_lesson"]["profiles"],
        "census_lessons": report["diagnostic_census"]["total_lessons"],
        "survivors": total_survivors,
        "wrong_queries": total_wrong_queries,
        "racket_verified": "racket_verification" in report,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
