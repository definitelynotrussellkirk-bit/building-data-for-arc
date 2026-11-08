from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "97bcb3b9194e"
EXPECTED_SOURCE_SHA256 = "6e2d6a927f50fd4aa57a1c888cf28c819a01182a27616404495aeb128f3ba144"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
BANDS = ("easy", "medium", "hard")
PERIOD = 12


def prepare() -> None:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha256 == EXPECTED_SOURCE_SHA256, (source_path, source_sha256)

    inputs: list[list[list[int]]] = []
    rows = []
    for band_index, band in enumerate(BANDS):
        seed = 97_000 + band_index
        for sample_index in range(PERIOD):
            grid = generator.generate(seed, sample_index, difficulty=band)
            errors = generator.self_check(grid, difficulty=band)
            assert errors == [], (band, sample_index, errors)
            intended = generator.rule_mirror(grid)
            rival = generator._count_only_4_6(grid)
            witness = rival != intended
            inputs.append(grid)
            rows.append(
                {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "mark_palette": generator.observe_overrides(grid)["mark_palette"],
                    "witness": witness,
                    "intended_output": intended,
                    "rival_output": rival,
                }
            )

    inputs_path = HERE / "inputs.json"
    inputs_path.write_text(json.dumps(inputs, indent=2) + "\n")
    preparation = {
        "schema": "arc-peer-probe-preparation-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha256,
        "draws": len(inputs),
        "rows": rows,
        "inputs_sha256": hashlib.sha256(inputs_path.read_bytes()).hexdigest(),
    }
    (HERE / "preparation.json").write_text(json.dumps(preparation, indent=2) + "\n")
    print(json.dumps({key: value for key, value in preparation.items() if key != "rows"}, indent=2))


def analyze() -> None:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha256 == EXPECTED_SOURCE_SHA256, (source_path, source_sha256)
    preparation = json.loads((HERE / "preparation.json").read_text())
    rows = preparation["rows"]
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["generator_sha256"] == source_sha256
    results = receipt["results"]
    assert len(results) == len(rows)
    assert all(row.get("error") is None and row.get("valid_output") for row in results)

    parity_failures = []
    for index, (row, result) in enumerate(zip(rows, results)):
        if result["output"] != row["intended_output"]:
            parity_failures.append(index)

    rotation_failures = []
    windows_checked = 0
    held_out_rotations_checked = 0
    per_band = {}
    for band in BANDS:
        band_rows = [row for row in rows if row["difficulty"] == band]
        witnesses = [bool(row["witness"]) for row in band_rows]
        assert len(witnesses) == PERIOD
        for start in range(PERIOD):
            indices = [(start + offset) % PERIOD for offset in range(4)]
            window = [witnesses[index] for index in indices]
            windows_checked += 1
            if sum(window) < 2:
                rotation_failures.append({"band": band, "start": start, "window": window})
            for query_offset in range(4):
                demos = [window[offset] for offset in range(4) if offset != query_offset]
                held_out_rotations_checked += 1
                if not any(demos):
                    rotation_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_offset": query_offset,
                            "window": window,
                            "reason": "held-out query leaves no shortcut-rejecting demonstration",
                        }
                    )
        per_band[band] = {
            "witnesses": sum(witnesses),
            "schedule": witnesses,
            "palettes": [row["mark_palette"] for row in band_rows],
        }

    report = {
        "schema": "arc-peer-bounded-no-finding-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha256,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "protected_racket_executions": len(results),
        "python_racket_parity_failures": parity_failures,
        "circular_four_pair_windows_checked": windows_checked,
        "held_out_query_rotations_checked": held_out_rotations_checked,
        "rotation_failures": rotation_failures,
        "per_band": per_band,
        "outcome": "no_finding" if not parity_failures and not rotation_failures else "finding",
        "scope_limit": (
            "One fresh 12-step schedule period in each difficulty band; this only tests the declared "
            "count-only-colors-4-and-6 rival and Racket/Python parity on those 36 inputs."
        ),
    }
    assert report["outcome"] == "no_finding", report
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "analyze"))
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        analyze()


if __name__ == "__main__":
    main()
