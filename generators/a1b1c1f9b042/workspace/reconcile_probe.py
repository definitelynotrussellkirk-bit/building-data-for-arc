#!/usr/bin/env python3
"""Bounded independent probe for the a1b1c1f9b042 reconciliation.

Prepare materializes representative default/boundary inputs and checks the
lesson contract with an independent stable-pack oracle. Verify binds those
inputs to actual canonical Racket outputs from ``arcpuzzles apply``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "a1b1c1f9b042"
RULE_HASH = "8cd149b15ecf"
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("reconciled_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def stable_pack(grid):
    return [
        [value for value in row if value]
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def sort_then_pack(grid):
    return [
        sorted(value for value in row if value)
        + [0] * sum(value == 0 for value in row)
        for row in grid
    ]


def grid_sha256(grid):
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def prepare(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=False)
    records = []
    unique = set()
    default_samples = 0
    boundary_samples = 0

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for base_seed in range(8):
            seed = band_index * 1000 + base_seed
            for sample_index in range(4):
                grid = GEN.generate(seed, sample_index, difficulty=band)
                truth = stable_pack(grid)
                assert GEN.self_check(grid) == []
                assert sort_then_pack(grid) != truth
                assert all(
                    rival(grid) != truth
                    for rival in GEN.LESSON_COMPETITORS.values()
                )
                digest = grid_sha256(grid)
                assert digest not in unique
                unique.add(digest)
                records.append(
                    {
                        "kind": "default",
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "input": grid,
                        "expected": truth,
                        "input_sha256": digest,
                    }
                )
                default_samples += 1

    boundaries = (
        {"grid_h": 2, "grid_w": 4, "palette_size": 2},
        {"grid_h": 3, "grid_w": 6, "palette_size": 9},
        {"grid_h": 4, "grid_w": 5, "palette_size": 7},
        {"grid_h": 8, "grid_w": 10, "palette_size": 9},
    )
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seed = 9000 + band_index
        for sample_index, controls in enumerate(boundaries, start=20):
            grid = GEN.generate(seed, sample_index, difficulty=band, **controls)
            truth = stable_pack(grid)
            observed = GEN.observe_overrides(grid)
            assert observed == controls
            assert GEN.self_check(grid) == []
            assert sort_then_pack(grid) != truth
            digest = grid_sha256(grid)
            assert digest not in unique
            unique.add(digest)
            records.append(
                {
                    "kind": "boundary",
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "controls": controls,
                    "input": grid,
                    "expected": truth,
                    "input_sha256": digest,
                }
            )
            boundary_samples += 1

    rotations = 0
    rival_checks = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(6):
                grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
                pairs = [{"input": grid, "output": stable_pack(grid)} for grid in grids]
                for query_index in range(4):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    query = pairs[query_index]
                    assert GEN.lesson_identifiable(demos, query) == []
                    for rival in GEN.LESSON_COMPETITORS.values():
                        assert any(rival(pair["input"]) != pair["output"] for pair in demos)
                        rival_checks += 1
                    rotations += 1

    invalid_cases = [
        {"difficulty": "expert"},
        {"misspelled_axis": 3},
        {"grid_h": 1},
        {"grid_w": 11},
        {"palette_size": 10},
        {"grid_h": 2, "grid_w": 4, "palette_size": 7},
    ]
    rejected = 0
    for case in invalid_cases:
        difficulty = case.get("difficulty")
        controls = {key: value for key, value in case.items() if key != "difficulty"}
        try:
            GEN.generate(0, 0, difficulty=difficulty, **controls)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(f"invalid case accepted: {case}")

    inputs = [record["input"] for record in records]
    (out_dir / "input.json").write_text(json.dumps(inputs, indent=2) + "\n")
    shard_rows = []
    for shard_index, start in enumerate(range(0, len(inputs), 64)):
        name = f"input-{shard_index:03d}.json"
        shard = inputs[start : start + 64]
        (out_dir / name).write_text(json.dumps(shard, indent=2) + "\n")
        shard_rows.append({"path": name, "start": start, "count": len(shard)})
    (out_dir / "expected.json").write_text(
        json.dumps(records, indent=2) + "\n"
    )
    report = {
        "schema": "a1b1c1f9b042-reconciliation-probe-v1",
        "task_id": TASK,
        "rule_hash": RULE_HASH,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "status": "prepared",
        "default_samples": default_samples,
        "boundary_samples": boundary_samples,
        "unique_inputs": len(unique),
        "lesson_rotations": rotations,
        "declared_rival_demo_checks": rival_checks,
        "invalid_cases_rejected": rejected,
        "racket_shards": shard_rows,
        "racket_parity": "pending",
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


def verify(out_dir: Path, racket_paths: list[Path]):
    records = json.loads((out_dir / "expected.json").read_text())
    all_results = []
    receipts = []
    generator_hashes = set()
    for racket_path in racket_paths:
        receipt = json.loads(racket_path.read_text())
        assert receipt["schema"] == "arcpuzzles-apply-v1"
        assert receipt["task_id"] == TASK
        assert receipt["executed_rule_hash"] == RULE_HASH
        assert receipt["rule_hash_matches_catalog"] is True
        all_results.extend(receipt["results"])
        receipts.append(racket_path.name)
        if receipt.get("generator_sha256"):
            generator_hashes.add(receipt["generator_sha256"])
    assert len(all_results) == len(records)
    mismatches = []
    for global_index, (record, actual) in enumerate(zip(records, all_results)):
        if actual.get("error") is not None or actual.get("output") != record["expected"]:
            mismatches.append(
                {
                    "index": global_index,
                    "receipt_index": actual.get("index"),
                    "error": actual.get("error"),
                    "input_sha256": record["input_sha256"],
                }
            )
    assert not mismatches, mismatches[:3]

    report = json.loads((out_dir / "report.json").read_text())
    report.update(
        {
            "status": "passed",
            "racket_parity": "passed",
            "racket_cases": len(records),
            "racket_mismatches": 0,
            "racket_receipts": receipts,
            "racket_generator_sha256": sorted(generator_hashes),
        }
    )
    (out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--out", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--out", type=Path, required=True)
    verify_parser.add_argument("--racket", type=Path, action="append", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out)
    else:
        verify(args.out, args.racket)


if __name__ == "__main__":
    main()
