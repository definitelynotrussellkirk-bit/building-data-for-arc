#!/usr/bin/env python3
"""Build compact, replayable adversarial-audit witnesses for assigned targets."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

TARGET_META = {
    "ebe355c22d70": {
        "generator_sha256": "490e5aadd6435ecc5880a64e9a365a67403595403d676419c99c5458e3d6a2e5",
        "rule_hash": "cd9402783d01",
    },
    "9296fec26a94": {
        "generator_sha256": "f26d313356f9a07e8fcd695f590e247e79893602b40d86c6412c29a993e12986",
        "rule_hash": "9f6888cf24e7",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_grid(value: Any) -> list[list[int]]:
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return [[int(cell) for cell in row] for row in value]


def canonical_records(path: Path) -> dict[str, dict[str, Any]]:
    wanted = set(TARGET_META)
    out = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") in wanted:
                out[row["task_id"]] = row
    if set(out) != wanted:
        raise RuntimeError(f"missing canonical records: {wanted - set(out)}")
    return out


def two_points(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def orientation(grid: list[list[int]]) -> str:
    points = sorted(two_points(grid))
    if len(points) != 2:
        return "malformed"
    (_, c0), (_, c1) = points
    return "positive_slope" if c1 > c0 else "negative_slope" if c1 < c0 else "aligned"


def positive_slope_only_rival(grid: list[list[int]]) -> list[list[int]]:
    points = sorted(two_points(grid))
    if len(points) != 2:
        return []
    (r0, c0), (r1, c1) = points
    if r1 <= r0 or c1 <= c0:
        return []
    return [[8] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]


def target_windows(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    found = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            values = [grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]]
            nonzero = [value for value in values if value]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                found.append((r, c, nonzero[0]))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(runtime)
    sys.path.insert(0, str(runtime))
    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import load_gen, load_rules, rule_application

    canon_path = runtime / "data/canonical/puzzles.jsonl"
    records = canonical_records(canon_path)
    rules = load_rules(TARGET_META)
    if set(rules) != set(TARGET_META):
        raise RuntimeError(f"missing rules: {set(TARGET_META) - set(rules)}")

    ebe = load_gen("ebe355c22d70")
    block = load_gen("9296fec26a94")

    with RacketBridge(max_calls_before_restart=48) as bridge:
        # EBE: ordinary data is one orientation only, while canonical data uses both.
        generated_orientation = {"positive_slope": 0, "negative_slope": 0, "aligned": 0, "malformed": 0}
        generated_rival_checked = 0
        generated_rival_matches = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for index in range(300):
                seed = 17 + band_index * 100_003 + index * 7_919
                grid = normalize_grid(ebe.generate(seed, index, difficulty=band))
                generated_orientation[orientation(grid)] += 1
                if index < 10:
                    actual = normalize_grid(bridge.eval_text(rule_application(rules["ebe355c22d70"], grid)))
                    generated_rival_checked += 1
                    generated_rival_matches += positive_slope_only_rival(grid) == actual

        ebe_pairs = list(records["ebe355c22d70"]["train"])
        test_value = records["ebe355c22d70"]["test"]
        ebe_pairs.extend(test_value if isinstance(test_value, list) else [test_value])
        canonical_orientation = {"positive_slope": 0, "negative_slope": 0, "aligned": 0, "malformed": 0}
        for pair in ebe_pairs:
            canonical_orientation[orientation(normalize_grid(pair["input"]))] += 1
        counter_pair = next(
            pair for pair in ebe_pairs if orientation(normalize_grid(pair["input"])) == "negative_slope"
        )
        counter_input = normalize_grid(counter_pair["input"])
        counter_actual = normalize_grid(
            bridge.eval_text(rule_application(rules["ebe355c22d70"], counter_input))
        )
        counter_declared = normalize_grid(counter_pair["output"])
        assert counter_actual == counter_declared
        ebe_report = {
            "schema": "arc-generator-audit-counterexample/1",
            "task_id": "ebe355c22d70",
            **TARGET_META["ebe355c22d70"],
            "canonical_ledger_sha256": sha256(canon_path),
            "finding": "ordinary generation has zero negative-slope corner pairs although 2/3 canonical pairs use that orientation",
            "sample_policy": {
                "bands": ["easy", "medium", "hard"],
                "draws_per_band": 300,
                "total_draws": 900,
                "seed_formula": "17 + band_index*100003 + sample_index*7919",
                "sample_index_range": [0, 299],
            },
            "generated_orientation_counts": generated_orientation,
            "canonical_orientation_counts": canonical_orientation,
            "shortcut_probe": {
                "name": "positive_slope_only_crop",
                "definition": "sort blue points by row; only handle c_bottom > c_top; emit the solid-8 bbox, otherwise emit []",
                "generated_racket_matches": generated_rival_matches,
                "generated_racket_checks": generated_rival_checked,
            },
            "counterexample": {
                "source": "canonical visible pair",
                "input": counter_input,
                "actual_racket_output": counter_actual,
                "rival_output": positive_slope_only_rival(counter_input),
                "validator_errors": ebe.self_check(counter_input),
                "belongs_to_task_domain": True,
                "ordinary_generator_supports_orientation": False,
            },
            "command": {
                "cwd": "packet_root",
                "argv": [
                    "python3", "checks/audits/audit_witness_probe.py",
                    "--runtime", "audit_runtime",
                    "--out-dir", "checks/audits",
                ],
            },
        }
        (out_dir / "ebe355c22d70_orientation_gap.json").write_text(
            json.dumps(ebe_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # 9296: a legal exact block_count override is silently under-realized.
        mismatch_seed = 240
        mismatch_grid = normalize_grid(
            block.generate(mismatch_seed, mismatch_seed, difficulty="easy", block_count=3)
        )
        mismatch_windows = target_windows(mismatch_grid)
        mismatch_actual = normalize_grid(
            bridge.eval_text(rule_application(rules["9296fec26a94"], mismatch_grid))
        )
        mismatch_count = 0
        first_mismatch = None
        for seed in range(1000):
            grid = normalize_grid(block.generate(seed, seed, difficulty="easy", block_count=3))
            observed = len(target_windows(grid))
            if observed != 3:
                mismatch_count += 1
                if first_mismatch is None:
                    first_mismatch = {"seed": seed, "sample_index": seed, "observed": observed}

        texture_results = {}
        helpful = ("default", "warm", "cool", "varied")
        for texture in helpful:
            identical = 0
            total = 0
            for band_index, band in enumerate(("easy", "medium", "hard")):
                for index in range(20):
                    seed = 31 + band_index * 10_007 + index * 101
                    plain = normalize_grid(block.generate(seed, index, difficulty=band))
                    textured = normalize_grid(block.generate(seed, index, difficulty=band, texture=texture))
                    identical += plain == textured
                    total += 1
            texture_results[texture] = {"byte_identical": identical, "draws": total}

        unknown_plain = normalize_grid(block.generate(17, 4, difficulty="easy"))
        unknown_grid = normalize_grid(
            block.generate(17, 4, difficulty="easy", __override_contract_unknown_axis__=123)
        )
        declared_rejection = None
        try:
            block.generate(0, 0, difficulty="easy", grid_h=4)
        except Exception as exc:
            declared_rejection = f"{type(exc).__name__}: {exc}"

        block_report = {
            "schema": "arc-generator-audit-counterexample/1",
            "task_id": "9296fec26a94",
            **TARGET_META["9296fec26a94"],
            "canonical_ledger_sha256": sha256(canon_path),
            "finding": "exact block_count=3 can return only two targets; self_check still accepts the draw",
            "sample_policy": {
                "difficulty": "easy",
                "override": {"block_count": 3},
                "seed_range": [0, 999],
                "sample_index": "equal to seed",
                "total_draws": 1000,
            },
            "mismatch_count": mismatch_count,
            "first_mismatch": first_mismatch,
            "counterexample": {
                "seed": mismatch_seed,
                "sample_index": mismatch_seed,
                "difficulty": "easy",
                "overrides": {"block_count": 3},
                "input": mismatch_grid,
                "actual_racket_output": mismatch_actual,
                "rival_output": None,
                "requested_blocks": 3,
                "observed_target_windows": len(mismatch_windows),
                "observed_windows": mismatch_windows,
                "validator_errors": block.self_check(
                    mismatch_grid,
                    difficulty="easy",
                    meta={"overrides": {"block_count": 3}},
                ),
                "belongs_to_documented_generator_domain": True,
            },
            "additional_contract_reproducers": {
                "helpful_texture_byte_identity": texture_results,
                "unknown_override_accepted": unknown_grid == unknown_plain,
                "declared_grid_h_4_rejected_in_easy": declared_rejection,
            },
            "command": {
                "cwd": "packet_root",
                "argv": [
                    "python3", "checks/audits/audit_witness_probe.py",
                    "--runtime", "audit_runtime",
                    "--out-dir", "checks/audits",
                ],
            },
        }
        (out_dir / "9296fec26a94_block_count_underfill.json").write_text(
            json.dumps(block_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    print(json.dumps({
        "ebe_generated_orientation_counts": generated_orientation,
        "ebe_shortcut_matches": [generated_rival_matches, generated_rival_checked],
        "9296_mismatch_count": mismatch_count,
        "9296_first_mismatch": first_mismatch,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
