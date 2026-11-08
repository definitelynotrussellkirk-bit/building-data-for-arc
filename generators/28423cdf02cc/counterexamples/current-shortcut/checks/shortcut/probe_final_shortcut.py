"""Final-source, Racket-labelled proof for the fixed-lattice canonical shortcut."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

TASK_ID = "28423cdf02cc"
EXPECTED_GENERATOR_SHA256 = "75ee24dc86a6d294fab9aab46fc47392cab0b7f5dbdaa58a59e63b349acf83c9"


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def fixed_lattice_rival(grid):
    """Stamp only blue centers at r=1 mod 3 and c=5 mod 3 (zero-based)."""
    output = copy.deepcopy(grid)
    template = [row[:3] for row in grid[:3]]
    for row, cells in enumerate(grid):
        for column, value in enumerate(cells):
            if value != 1 or (row - 1) % 3 or (column - 5) % 3:
                continue
            for dy in range(3):
                for dx in range(3):
                    y, x = row - 1 + dy, column - 1 + dx
                    if 0 <= y < len(grid) and 0 <= x < len(grid[0]) and output[y][x] in (0, 1):
                        output[y][x] = template[dy][dx]
    return output


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    repo, outdir = args.repo.resolve(), args.out_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(repo / "src"), str(repo / "shared/runtime")]
    from reviewer_support import canonical_pairs, load_selected_generator
    from arcpuzzles import Catalog

    mod, source, source_hash = load_selected_generator(TASK_ID, root=repo)
    assert source_hash == EXPECTED_GENERATOR_SHA256
    canonical = canonical_pairs(TASK_ID, root=repo, labeled_only=True)
    assert len(canonical) == 4
    rule = next(json.loads(line)["program_solution"]
                for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)
    seed, index, band = 11, 2, "medium"
    grid = mod.generate(seed, index, difficulty=band)
    assert mod.self_check(grid) == []
    assert mod.schedule_profile(seed, index, difficulty=band) == "anti_lattice"
    inputs = [pair["input"] for pair in canonical] + [grid]
    save(outdir / "input.json", {"inputs": inputs})
    receipt = Catalog(repo).apply(TASK_ID, inputs, reference="canonical", timeout=120,
                                 check_generator_domain=True)
    receipt["command"] = [sys.executable, *sys.argv]
    receipt["cwd"] = str(Path.cwd())
    save(outdir / "racket.json", receipt)
    assert receipt["generator_sha256"] == source_hash
    assert receipt["rule_hash_matches_catalog"] and receipt["executed_rule_hash"] == mod.RULE_HASH
    assert all(row["valid_output"] and row["error"] is None for row in receipt["results"])
    assert all(row["generator_domain"] == {"status": "valid", "errors": []} for row in receipt["results"])
    rival_fn = mod.CANONICAL_SHORTCUTS["fixed_canonical_lattice_only"]
    assert all(fixed_lattice_rival(value) == rival_fn(value) for value in inputs)
    canonical_checks = []
    for pair, result in zip(canonical, receipt["results"][:4]):
        rival = fixed_lattice_rival(pair["input"])
        assert result["output"] == pair["output"] == rival
        canonical_checks.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                                 "input": pair["input"], "racket_output": result["output"], "rival_output": rival,
                                 "rival_matches": True, "input_sha256": result["input_sha256"],
                                 "output_sha256": result["output_sha256"]})
    actual = receipt["results"][-1]["output"]
    rival = fixed_lattice_rival(grid)
    differences = [{"row": r, "column": c, "racket": value, "rival": rival[r][c]}
                   for r, row in enumerate(actual) for c, value in enumerate(row) if value != rival[r][c]]
    assert differences
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    ignored = [(r, c) for r, c in markers if (r - 1) % 3 or (c - 5) % 3]
    assert ignored
    assert sha(source.read_bytes()) == source_hash
    witness = {
        "task_id": TASK_ID, "generator_sha256": source_hash, "generator_version": mod.VERSION,
        "rule_hash": receipt["executed_rule_hash"], "canonical_source_sha256": sha(rule),
        "executed_callable_sha256": receipt["rule_text_sha256"],
        "rival": "fixed_canonical_lattice_only", "rival_definition": "Copy the original 3x3 template only at blue markers with (r-1)%3 == 0 and (c-5)%3 == 0; zero-based coordinates.",
        "seed": seed, "sample_index": index, "difficulty": band, "overrides": {},
        "schedule_profile": mod.schedule_profile(seed, index, difficulty=band),
        "default_schedule_emits_witness": True, "generator_domain_errors": [],
        "input": grid, "racket_output": actual, "rival_output": rival,
        "markers": markers, "ignored_markers": ignored, "differing_cell_count": len(differences),
        "differing_cells": differences, "input_dimensions": [len(grid), len(grid[0])],
        "output_dimensions": [len(actual), len(actual[0])],
        "canonical_checks": canonical_checks, "canonical_rival_matches": 4,
        "canonical_labeled_pair_count": 4, "racket_execution_count": 5,
        "racket_receipt_sha256": sha((outdir / "racket.json").read_bytes()),
        "source_unchanged_during_probe": True, "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()), "exit_code": 0,
        "limits": "One emitted witness and all four labeled canonical pairs; no hidden solve answers and no exhaustive claim against undeclared rivals."}
    save(outdir / "witness.json", witness)
    print(json.dumps({k: v for k, v in witness.items() if k not in ("input", "racket_output", "rival_output", "canonical_checks", "differing_cells")}, indent=2))


if __name__ == "__main__":
    main()
