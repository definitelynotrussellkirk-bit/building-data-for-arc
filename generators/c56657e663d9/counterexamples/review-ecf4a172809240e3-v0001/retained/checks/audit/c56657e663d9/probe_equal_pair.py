"""Bounded, source-bound replay of the equal-color transpose-pair audit.

From the outer packet directory:
  PYTHONDONTWRITEBYTECODE=1 python3 review.py run python3 -B \
      ../checks/audit/c56657e663d9/probe_equal_pair.py

The probe writes only beside this file. Racket remains the label authority;
the mirror below is an explicitly independent candidate used for comparison.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "c56657e663d9"
EXPECTED_SOURCE = "32cb702d7541bd27bb708987618122862924f630a0820055d7aad5e80c74bdd3"
EXPECTED_RAW_RULE = "58e0408dcdeb9d358ef365a3bf03e4864c79ffb198a1913e4b18b0e70c63dbe7"
HERE = Path(__file__).resolve().parent
try:
    # Task-owned retained evidence can locate its enclosing library/runtime.
    REPO = find_root(__file__)
except FileNotFoundError:
    # In a review packet, checks/ and repo/ are siblings below WORK/.
    REPO = find_root(Path(__file__).resolve().parents[3] / "repo")


def mirror(grid):
    """Nonzero transposed cells win; empty partners preserve current cells."""
    return [
        [grid[c][r] if grid[c][r] else grid[r][c] for c in range(len(grid))]
        for r in range(len(grid))
    ]


def duplicate_cancel(grid):
    """Plausible wrong rule: identical occupied partners cancel each other."""
    out = mirror(grid)
    for r in range(len(grid)):
        for c in range(r + 1, len(grid)):
            if grid[r][c] != 0 and grid[r][c] == grid[c][r]:
                out[r][c] = out[c][r] = 0
    return out


def pair_profile(grid):
    counts = dict(upper_only=0, lower_only=0, different=0, equal=0, diagonal=0)
    for r in range(len(grid)):
        counts["diagonal"] += grid[r][r] != 0
        for c in range(r + 1, len(grid)):
            a, b = grid[r][c], grid[c][r]
            if a and not b:
                counts["upper_only"] += 1
            elif b and not a:
                counts["lower_only"] += 1
            elif a and b:
                counts["equal" if a == b else "different"] += 1
    return counts


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    gen, source, source_sha = load_selected_generator(TASK, root=REPO)
    assert source_sha == EXPECTED_SOURCE, (source_sha, EXPECTED_SOURCE)
    selected = []
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    selected.append(row)
    assert len(selected) == 1
    raw_rule_sha = hashlib.sha256(selected[0]["program_solution"].encode()).hexdigest()
    assert raw_rule_sha == EXPECTED_RAW_RULE

    canonical = []
    for pair in canonical_pairs(TASK, root=REPO):
        grid, expected = pair["input"], pair["output"]
        row = {
            "split": pair["split"], "pair_index": pair["pair_index"],
            "shape": [len(grid), len(grid[0])],
            "self_check": gen.self_check(grid),
            "profile": pair_profile(grid),
            "mirror_matches_canonical": mirror(grid) == expected,
            "rival_matches_canonical": duplicate_cancel(grid) == expected,
        }
        assert not row["self_check"]
        assert row["mirror_matches_canonical"] and row["rival_matches_canonical"]
        canonical.append(row)

    bands = []
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        summary = {
            "difficulty": difficulty, "count": 100,
            "seed_formula": f"{701000 + 1000 * band_index} + i, i=0..99",
            "sample_index_formula": "i, i=0..99",
            "self_check_passes": 0, "mirror_rival_matches": 0,
            "equal_pair_instances": 0, "upper_only_instances": 0,
            "lower_only_instances": 0, "different_pair_instances": 0,
        }
        for index in range(100):
            grid = gen.generate(701000 + 1000 * band_index + index, index,
                                difficulty=difficulty)
            errors = gen.self_check(grid)
            assert not errors, (difficulty, index, errors)
            summary["self_check_passes"] += 1
            profile = pair_profile(grid)
            summary["mirror_rival_matches"] += mirror(grid) == duplicate_cancel(grid)
            summary["equal_pair_instances"] += profile["equal"] > 0
            summary["upper_only_instances"] += profile["upper_only"] > 0
            summary["lower_only_instances"] += profile["lower_only"] > 0
            summary["different_pair_instances"] += profile["different"] > 0
        assert summary["mirror_rival_matches"] == 100
        assert summary["equal_pair_instances"] == 0
        bands.append(summary)

    # Six occupied cells retain all three usual teaching relations and add
    # exactly one equal-color pair. All declared observable axes remain valid.
    witness = [[0] * 6 for _ in range(6)]
    for r, c, color in ((0, 1, 3), (1, 0, 7), (0, 3, 4),
                        (4, 2, 7), (1, 5, 3), (5, 1, 3)):
        witness[r][c] = color
    errors = gen.self_check(witness)
    assert not errors, errors
    intended, rival = mirror(witness), duplicate_cancel(witness)
    differing_cells = [
        [r, c] for r in range(6) for c in range(6)
        if intended[r][c] != rival[r][c]
    ]
    assert differing_cells == [[1, 5], [5, 1]]
    result = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK,
        "repo_at_run": str(REPO), "source_path": str(source.relative_to(REPO)),
        "source_sha256": source_sha, "raw_canonical_rule_sha256": raw_rule_sha,
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_pairs": canonical, "generated_bands": bands,
        "witness": {
            "input": "input.json", "self_check": errors,
            "pair_profile": pair_profile(witness),
            "observed_axes": gen.observe_overrides(witness),
            "independent_mirror_output": intended, "rival_output": rival,
            "differing_cells_zero_based": differing_cells,
        },
        "authority_status": "pending separate supported arcpuzzles apply execution",
        "scope": "100 default draws per band; canonical pairs and one authored witness; no battery",
    }
    write_json("input.json", witness)
    write_json("probe.json", result)
    print(json.dumps({"task_id": TASK, "source_sha256": source_sha,
                      "canonical_rival_matches": len(canonical),
                      "sampled_rival_matches": 300,
                      "sampled_equal_pair_instances": 0,
                      "witness_self_check": errors,
                      "witness_difference_cells": differing_cells}))


def verify_racket():
    """Compare the separate supported apply result without resampling."""
    _, _, source_sha = load_selected_generator(TASK, root=REPO)
    assert source_sha == EXPECTED_SOURCE
    report = json.loads((HERE / "probe.json").read_text(encoding="utf-8"))
    authority = json.loads((HERE / "racket.json").read_text(encoding="utf-8"))
    grid = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    assert authority["task_id"] == authority["rule_task_id"] == TASK
    assert authority["generator_sha256"] == source_sha
    assert authority["reference"] == "canonical"
    assert authority["executed_rule_hash"] == "38eb4ea53ac4"
    assert authority["rule_hash_matches_catalog"] is True
    assert authority["rule_text_sha256"] == "3197d74bb12080f48a1425d48387b5ac44b5416a2f0266022cd15d1fb9b158e5"
    assert len(authority["results"]) == 1
    result = authority["results"][0]
    assert result["valid_output"] is True and result["error"] is None
    assert result["input"] == grid
    assert result["output"] == mirror(grid)
    assert result["output"] == report["witness"]["independent_mirror_output"]
    assert result["output"] != duplicate_cancel(grid)
    report["authority_status"] = "verified supported Racket result equals the independent mirror and refutes the rival"
    report["authority"] = {
        "path": "racket.json", "executed_rule_hash": authority["executed_rule_hash"],
        "rule_text_sha256": authority["rule_text_sha256"],
        "generator_sha256": authority["generator_sha256"],
        "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
        "racket_equals_independent_mirror": True, "racket_refutes_rival": True,
    }
    write_json("probe.json", report)
    print(json.dumps({"authority_verified": True, "executed_rule_hash": authority["executed_rule_hash"],
                      "rival_difference_cells": report["witness"]["differing_cells_zero_based"]}))


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify-racket"]:
        verify_racket()
    elif not sys.argv[1:]:
        main()
    else:
        raise SystemExit("usage: probe_equal_pair.py [--verify-racket]")
