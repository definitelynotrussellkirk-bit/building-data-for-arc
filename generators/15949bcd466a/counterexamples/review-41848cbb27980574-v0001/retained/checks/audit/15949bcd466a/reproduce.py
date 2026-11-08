"""Read-only, source-bound reproduction of the tile-majority audit findings."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "15949bcd466a"
EXPECTED_SOURCE = "681016157a2ee18e52d3deb6f558a28d616cede64afe88e62e5a5904ac8b950d"
sys.dont_write_bytecode = True


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return sha256(json.dumps(grid, separators=(",", ":")).encode())


def tile_majorities(grid):
    counts = []
    winners = []
    for top, left in ((0, 0), (0, 3), (3, 0), (3, 3)):
        tally = Counter(grid[r][c] for r in range(top, top+2)
                        for c in range(left, left+2) if grid[r][c] != 0)
        winners.append(min(tally, key=lambda color: (-tally[color], color)) if tally else 0)
        counts.append(max(tally.values(), default=0))
    return counts, [winners[:2], winners[2:]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", choices=("prepare", "verify"), default="prepare")
    parser.add_argument("--racket", type=Path,
                        help="Existing public arcpuzzles apply receipt; default: alongside --out")
    args = parser.parse_args()
    repo = args.repo.resolve()
    path = repo / "generators" / TASK / "generator.py"
    assert sha256(path.read_bytes()) == EXPECTED_SOURCE, "Assigned audit source changed"
    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audited_tile_majority", path)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    canonical_rows = [line for line in (repo / "shared/data/canonical/puzzles.jsonl").read_bytes().splitlines()
                      if json.loads(line).get("task_id") == TASK]
    assert len(canonical_rows) == 1
    rule = json.loads(canonical_rows[0])["program_solution"]
    identity = {
        "generator_sha256": EXPECTED_SOURCE,
        "generator_version": gen.VERSION,
        "canonical_rule_source_sha256": sha256(rule.encode()),
        "canonical_rule_normalized_sha256": sha256(" ".join(rule.split()).encode()),
        "canonical_row_sha256_no_newline": sha256(canonical_rows[0]),
    }
    if args.phase == "verify":
        out = json.loads(args.out.read_text())
        for key, value in identity.items():
            assert out[key] == value, f"Changed source identity: {key}"
        racket_path = args.racket or args.out.parent / "racket.json"
        record = json.loads(racket_path.read_text())
        assert record["task_id"] == TASK
        assert record["generator_sha256"] == EXPECTED_SOURCE
        assert record["rule_hash_matches_catalog"] is True
        assert record["executed_rule_hash"] == identity["canonical_rule_normalized_sha256"][:12]
        assert len(record["results"]) == 2
        inputs = json.loads((args.out.parent / "input.json").read_text())
        for index, key in enumerate(("majority_count_witness", "divider_alias_witness")):
            witness = out[key]
            actual = record["results"][index]
            assert actual["input"] == inputs[index] == witness["input"]
            assert actual["input_sha256"] == grid_hash(witness["input"])
            assert actual["valid_output"] is True and actual["error"] is None
            assert gen.self_check(witness["input"]) == witness["validator_errors"] == []
            fixed_output = tile_majorities(witness["input"])[1]
            witness["input_sha256"] = actual["input_sha256"]
            witness["actual_racket_output"] = actual["output"]
            witness["rival_output"] = fixed_output
            witness["rival_name"] = "fixed_2_by_2_tile_majority"
            witness["rival_matches_racket"] = fixed_output == actual["output"]
            witness["validator_accepts"] = True
        assert out["majority_count_witness"]["rival_matches_racket"] is True
        assert out["divider_alias_witness"]["rival_matches_racket"] is False
        assert out["divider_alias_witness"]["actual_racket_output"] == [[1, 2]]
        out["divider_alias_witness"].pop("prediction", None)
        out["divider_alias_witness"]["observed_geometry"] = "Rows 0, 1, and 2 are full-9 dividers, so only the two bottom tiles remain and the actual output is 1x2"
        assert out["scan"]["identical_majority_3_and_4_pairs"] == 60
        assert out["scan"]["wrong_majority_requests"] == 105
        assert out["scan"]["identical_palette_kind_families"] == 60
        out["reference_status"] = "Existing actual public Racket receipt verified against unchanged source and both exact inputs"
        out["executed_rule_hash"] = record["executed_rule_hash"]
        out["racket_callable_text_sha256"] = record["rule_text_sha256"]
        out["racket_receipt_sha256"] = sha256(racket_path.read_bytes())
        out["reproducer_sha256"] = sha256(Path(__file__).read_bytes())
        out["reference_command"] = record["command"]
        out["reference_command_cwd"] = record["cwd"]
        args.out.write_text(json.dumps(out, indent=2) + "\n")
        print(json.dumps({"task_id": TASK, "phase": "verify", "verified_reference_inputs": 2,
                          "validator_accepted": 2, "fixed_tile_rival_matches": 1,
                          "executed_rule_hash": out["executed_rule_hash"],
                          "racket_callable_text_sha256": out["racket_callable_text_sha256"]}))
        return
    identical = 0
    wrong_request_cases = 0
    total_request_cases = 0
    example = None
    palette_identical = 0
    scan_cases = []
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            a = gen.generate(seed, 3, difficulty=band, majority_count=3)
            b = gen.generate(seed, 3, difficulty=band, majority_count=4)
            identical += a == b
            for requested, grid in ((3, a), (4, b)):
                actual, intended = tile_majorities(grid)
                total_request_cases += 1
                wrong = any(count != requested for count in actual)
                wrong_request_cases += wrong
                if wrong and example is None:
                    example = dict(seed=seed, sample_index=3, difficulty=band,
                                   overrides={"majority_count": requested},
                                   input=grid, observed_majority_counts=actual,
                                   intended_majority_output=intended,
                                   validator_errors=gen.self_check(grid))
            variants = [gen.generate(seed, 3, difficulty=band, palette_kind=kind)
                        for kind in gen.PALETTE_KINDS]
            palette_identical += all(grid == variants[0] for grid in variants)
            scan_cases.append({"seed": seed, "sample_index": 3, "difficulty": band,
                               "majority_count_3_input_sha256": grid_hash(a),
                               "majority_count_4_input_sha256": grid_hash(b),
                               "observed_majority_counts": tile_majorities(a)[0],
                               "palette_input_sha256_by_kind": {
                                   kind: grid_hash(grid) for kind, grid in zip(gen.PALETTE_KINDS, variants)}})
    divider_alias = [[9, 9, 9, 9, 9] for _ in range(3)] + [
        [1, 1, 9, 2, 2], [1, 1, 9, 2, 2]]
    out = {
        "schema": "arcpuzzles-focused-audit-159-v2",
        "task_id": TASK,
        **identity,
        "source_stage": "unchanged assigned audit source",
        "scan": {"bands": ["easy", "medium", "hard"], "seeds": [0, 19],
                 "seed_range_inclusive": True,
                 "sample_index": 3, "paired_draws": 60,
                 "identical_majority_3_and_4_pairs": identical,
                 "wrong_majority_requests": wrong_request_cases,
                 "majority_requests": total_request_cases,
                 "identical_palette_kind_families": palette_identical,
                 "palette_kinds": list(gen.PALETTE_KINDS), "palette_families": 60,
                 "palette_draws": 60 * len(gen.PALETTE_KINDS),
                 "majority_unique_inputs": len({case[key] for case in scan_cases
                                                for key in ("majority_count_3_input_sha256", "majority_count_4_input_sha256")}),
                 "palette_unique_inputs": len({value for case in scan_cases
                                               for value in case["palette_input_sha256_by_kind"].values()})},
        "scan_cases": scan_cases,
        "findings": [
            {"id": "A-159-1", "kind": "ignored_override",
             "claim": "majority_count and palette_kind do not control the declared variation",
             "source_locations": ["generators/15949bcd466a/generator.py:33-45", "generators/15949bcd466a/generator.py:49-89"]},
            {"id": "A-159-2", "kind": "validator_domain_geometry_mismatch",
             "claim": "self_check accepts full-9 top tiles that Racket instead parses as additional divider rows",
             "source_locations": ["generators/15949bcd466a/generator.py:128-149"],
             "scope": "validator-only; outside ordinary sampled tile palette"}],
        "majority_count_witness": example,
        "divider_alias_witness": {
            "seed": None, "sample_index": None, "overrides": None,
            "construction": "Two all-9 top tiles in a fixed 5x5 lattice, with bottom winners 1 and 2",
            "input": divider_alias,
            "validator_errors": gen.self_check(divider_alias),
            "documented_fixed_tile_output": [[9, 9], [1, 2]],
            "generated_support": False,
            "scope": "validator-only: ordinary sampler excludes 9 inside tiles",
            "normal_sampler_domain": False,
            "documented_domain_qualification": "Satisfies the written fixed-lattice/strict-majority invariants, but uses tile color 9, which ordinary generation excludes",
            "prediction": "Racket recognizes extra full-9 divider rows and returns a 1x2 output"},
        "reference_status": "Actual Racket outputs recorded separately in racket.json",
        "limits": ["A-159-1 concerns ignored overrides, not an incorrect reference label.",
                   "A-159-2 is validator-only; the ordinary sampler does not emit this input.",
                   "No full battery or exhaustive domain/lesson census was run."],
    }
    out["majority_count_witness"]["generated_support"] = True
    out["majority_count_witness"]["documented_generator_domain"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2)+"\n")
    (args.out.parent / "input.json").write_text(json.dumps([example["input"], divider_alias])+"\n")
    print(json.dumps({"task_id": TASK, "source": out["generator_sha256"], "scan": out["scan"],
                      "divider_alias_validator_errors": out["divider_alias_witness"]["validator_errors"]}))


if __name__ == "__main__":
    main()
