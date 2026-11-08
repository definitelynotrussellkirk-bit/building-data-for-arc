from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "8ab650d5f4cb"
EXPECTED_SOURCE_SHA256 = "0d1634afe24db5e2c72a7c0445f5eaa95563c8c8a1a12d4c4709e1e6d039153e"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()


def fixed_coordinate_rival(grid: list[list[int]]) -> list[list[int]]:
    """Ignore frame discovery and fill the generator's two fixed interiors."""
    out = [row[:] for row in grid]
    first = grid[2][2]
    for row in range(2, 4):
        for col in range(2, 4):
            out[row][col] = first
    second = grid[6][9]
    for row in range(6, 8):
        for col in range(8, 11):
            out[row][col] = second
    return out


def prepare() -> None:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha256 == EXPECTED_SOURCE_SHA256, (source_path, source_sha256)

    inputs: list[list[list[int]]] = []
    rows = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(4):
            seed = 81_000 + 100 * band_index + sample_index
            grid = generator.generate(seed, sample_index, difficulty=band)
            errors = generator.self_check(grid, difficulty=band)
            assert errors == [], (band, seed, sample_index, errors)
            inputs.append(grid)
            rows.append(
                {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "shape": [len(grid), len(grid[0])],
                    "fixed_marker_values": [grid[2][2], grid[6][9]],
                }
            )

    inputs_path = HERE / "inputs.json"
    inputs_path.write_text(json.dumps(inputs, indent=2) + "\n")
    report = {
        "schema": "arc-peer-probe-preparation-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha256,
        "draws": len(inputs),
        "bands": ["easy", "medium", "hard"],
        "rows": rows,
        "inputs_sha256": hashlib.sha256(inputs_path.read_bytes()).hexdigest(),
    }
    (HERE / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def analyze() -> None:
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    assert source_sha256 == EXPECTED_SOURCE_SHA256, (source_path, source_sha256)
    inputs = json.loads((HERE / "inputs.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["generator_sha256"] == source_sha256
    results = receipt["results"]
    assert len(results) == len(inputs)
    assert all(row.get("error") is None and row.get("valid_output") for row in results)

    matches = [
        fixed_coordinate_rival(grid) == result["output"]
        for grid, result in zip(inputs, results)
    ]
    report = {
        "schema": "arc-peer-bounded-finding-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(ROOT)),
        "generator_sha256": source_sha256,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "protected_racket_executions": len(results),
        "fixed_coordinate_rival_matches": sum(matches),
        "all_generated_labels_fit_shortcut": all(matches),
        "mismatching_indices": [index for index, match in enumerate(matches) if not match],
        "outcome": "finding" if all(matches) else "not_reproduced",
        "finding": (
            "All bounded generated labels are reproduced by a rule that never discovers frames; "
            "it reads and fills only the two generator-fixed coordinate ranges."
        ),
        "scope_limit": "Twelve fresh generated inputs: four per difficulty band; not a universal census.",
    }
    assert report["all_generated_labels_fit_shortcut"], report
    (HERE / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
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
