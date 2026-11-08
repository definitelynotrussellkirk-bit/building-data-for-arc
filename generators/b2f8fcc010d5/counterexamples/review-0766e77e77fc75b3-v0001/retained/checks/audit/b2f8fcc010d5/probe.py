#!/usr/bin/env python3
"""Source-bound audit probe for a canonical-compatible coordinate-swap rival.

The prepare action uses Python only to screen four-pair windows. Its predictions
are hypotheses until compared to the supported Racket apply receipt. No audited
source is edited. Run from WORK with --repo repo and a task-owned --out directory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

TASK_ID = "b2f8fcc010d5"
SOURCE_SHA256 = "33579df7feba0fa18710a5627d504d9fb0bc28a46ba71be40cc42e64df4f7cf8"
POSITIONS = ((0, 0), (1, 1), (0, 4), (1, 3), (2, 2), (3, 1), (4, 0), (3, 3), (4, 4))


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(value).hexdigest()


def reference_mirror(grid):
    flat = [grid[r][c] for r, c in POSITIONS]
    return [flat[0:3], flat[3:6], flat[6:9]]


def corner_swap_rival(grid):
    output = reference_mirror(grid)
    output[0][0], output[2][2] = output[2][2], output[0][0]
    return output


def prepare(repo, out):
    path = repo / "generators" / TASK_ID / "generator.py"
    source = path.read_bytes()
    if digest(source) != SOURCE_SHA256:
        raise ValueError("Audited generator hash changed; re-review before updating the pin")
    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_b2f8fcc010d5", path)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    canonical = []
    rule_texts = []
    for number, line in enumerate((repo / "shared/data/canonical/puzzles.jsonl").read_bytes().splitlines(), 1):
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        rule_texts.append({"line": number,
                           "exact_sha256": digest(row["program_solution"].encode()),
                           "normalized_sha256": digest(" ".join(row["program_solution"].split()).encode())})
        for split in ("train", "test"):
            for index, pair in enumerate(row[split]):
                canonical.append({"split": split, "pair_index": index, **pair})
    assert len(canonical) == 4
    for pair in canonical:
        assert reference_mirror(pair["input"]) == pair["output"]
        assert corner_swap_rival(pair["input"]) == pair["output"]
        assert generator.self_check(pair["input"]) == []

    records = []
    inputs = []
    for pair in canonical:
        grid = pair["input"]
        records.append({"apply_index": len(inputs), "role": "canonical", "split": pair["split"],
                        "pair_index": pair["pair_index"], "input_sha256": digest(grid),
                        "self_check": [], "expected_reference_output": pair["output"],
                        "rival_output": corner_swap_rival(grid)})
        inputs.append(grid)
    counts = []
    all_hashes = set()
    for band in ("easy", "medium", "hard"):
        ambiguous_seeds = []
        for seed in range(128):
            grids = [generator.generate(seed, index, difficulty=band) for index in range(4)]
            for grid in grids:
                assert generator.self_check(grid, difficulty=band) == []
                all_hashes.add(digest(grid))
            agrees = [reference_mirror(grid) == corner_swap_rival(grid) for grid in grids]
            if all(agrees[:3]) and not agrees[3]:
                ambiguous_seeds.append(seed)
        counts.append({"difficulty": band, "seed_range_inclusive": [0, 127],
                       "sample_indices": [0, 1, 2, 3], "train_indices": [0, 1, 2], "query_index": 3,
                       "windows": 128, "ambiguous_corner_swap_windows": len(ambiguous_seeds),
                       "ambiguous_seeds": ambiguous_seeds,
                       "label_basis": "Python screening mirror, not a census of Racket-labelled episodes"})
        assert 67 in ambiguous_seeds
        for index in range(4):
            grid = generator.generate(67, index, difficulty=band)
            records.append({"apply_index": len(inputs), "role": "generated_witness",
                            "seed": 67, "sample_index": index,
                            "split": "train" if index < 3 else "test",
                            "difficulty": band, "overrides": {},
                            "observed_controls": generator.observe_overrides(grid),
                            "input_sha256": digest(grid), "self_check": generator.self_check(grid, difficulty=band),
                            "expected_reference_output": reference_mirror(grid),
                            "rival_output": corner_swap_rival(grid)})
            inputs.append(grid)
    out.mkdir(parents=True, exist_ok=True)
    (out / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
    report = {"schema_version": 1, "task_id": TASK_ID, "generator_version": generator.VERSION,
              "generator_sha256": SOURCE_SHA256, "rule_hash_12": generator.RULE_HASH,
              "canonical_source_records": rule_texts, "rival": "swap only output (0,0) and (2,2)",
              "canonical_fit": {"passes": 4, "total": 4},
              "python_screening": counts,
              "screened_pair_count": 1536, "screened_unique_input_count": len(all_hashes),
              "screened_validator_failures": 0,
              "cross_band_dependence": "Same seed and indices; sampled_kind draw is shared across bands, so band cases are correlated.",
              "racket_apply_records": records,
              "limits": ["Finite named-rival probe; no exhaustive identifiability or all-seed claim.",
                         "Racket outputs must be read from the separate supported apply receipt."]}
    (out / "screening.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"generator_version": generator.VERSION, "generator_sha256": SOURCE_SHA256,
                      "racket_inputs_prepared": len(inputs), "python_windows_screened": 384,
                      "python_ambiguous_windows": sum(row["ambiguous_corner_swap_windows"] for row in counts),
                      "unique_inputs": len(all_hashes)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.repo.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
