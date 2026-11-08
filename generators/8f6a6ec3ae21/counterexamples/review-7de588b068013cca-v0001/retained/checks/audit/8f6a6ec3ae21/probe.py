"""Findings-only audit: alternating border decoys leave one-sided rivals."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "8f6a6ec3ae21"
PIN = "a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475"
ROOT = find_root(Path.cwd())
OUT = Path(__file__).resolve().parent
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
assert SOURCE_SHA == PIN, SOURCE_SHA
Grid = list[list[int]]


def intersection_output(grid: Grid, *, filter_left: bool = True,
                        filter_top: bool = True) -> Grid:
    """Independent Python canonical expression and two one-sided rivals."""
    rows = {r for r in range(len(grid))
            if (grid[r][0] == 1 if filter_left else grid[r][0] != 0)}
    cols = {c for c in range(len(grid[0]))
            if (grid[0][c] == 2 if filter_top else grid[0][c] != 0)}
    return [[8 if r in rows and c in cols else 0 for c in range(len(grid[0]))]
            for r in range(len(grid))]


def left_only_output(grid: Grid) -> Grid:
    return intersection_output(grid, filter_top=False)


def top_only_output(grid: Grid) -> Grid:
    return intersection_output(grid, filter_left=False)


RIVALS = {"filter_left_only": left_only_output, "filter_top_only": top_only_output}


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def lesson(seed: int, start: int, band: str):
    pairs = []
    for index in range(start, start + 3):
        grid = GEN.generate(seed, index, difficulty=band)
        expected = intersection_output(grid)
        assert GEN.self_check(grid) == GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == expected
        pairs.append({"input": grid, "output": expected,
                      "generation": {"seed": seed, "sample_index": index,
                                     "difficulty": band, "overrides": {}},
                      "observed_overrides": GEN.observe_overrides(grid)})
    return pairs


def rotations(pairs):
    result = []
    for query_index in range(3):
        indices = [i for i in range(3) if i != query_index]
        demos, query = [pairs[i] for i in indices], pairs[query_index]
        ambiguous = [name for name, rival in RIVALS.items()
                     if all(rival(p["input"]) == p["output"] for p in demos)
                     and rival(query["input"]) != query["output"]]
        result.append({"query_index": query_index, "demo_indices": indices,
                       "ambiguous_rivals": ambiguous,
                       "declared_lesson_identifiable_errors": GEN.lesson_identifiable(demos, query)})
    return result


def main():
    canonical = canonical_pairs(TASK, root=ROOT)
    canonical_checks = []
    for pair in canonical:
        assert intersection_output(pair["input"]) == pair["output"]
        matches = {name: rival(pair["input"]) == pair["output"] for name, rival in RIVALS.items()}
        assert all(matches.values())
        canonical_checks.append({key: pair[key] for key in ("variant", "split", "pair_index")}
                                | {"rival_matches": matches})
    ledger_rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
                   if line.strip() and json.loads(line).get("task_id") == TASK]
    programs = {row["program_solution"] for row in ledger_rows}
    assert len(programs) == 1
    program = programs.pop()
    program_sha = hashlib.sha256(program.encode()).hexdigest()
    dump("authority.json", {"program_solution": program, "canonical_program_sha256": program_sha,
                            "rule_hash": GEN.RULE_HASH, "pairs": canonical, "checks": canonical_checks})
    records = []
    for seed, start, band in itertools.product((10401, 10402, 10403), range(4), ("easy", "medium", "hard")):
        checks = rotations(lesson(seed, start, band))
        records.append({"seed": seed, "start": start, "difficulty": band, "overrides": {}, "rotations": checks})
    ambiguous_count = sum(bool(row["ambiguous_rivals"]) for rec in records for row in rec["rotations"])
    missed_count = sum(bool(row["ambiguous_rivals"]) and not row["declared_lesson_identifiable_errors"]
                       for rec in records for row in rec["rotations"])
    assert ambiguous_count == missed_count == 36
    assert all(not rec["rotations"][2]["ambiguous_rivals"] for rec in records)
    witness_pairs = lesson(10401, 0, "medium")
    assert rotations(witness_pairs)[1]["ambiguous_rivals"] == ["filter_left_only"]
    dump("input.json", witness_pairs[1]["input"])
    dump("lesson-inputs.json", {"inputs": [pair["input"] for pair in witness_pairs]})
    dump("witness.json", {
        "task_id": TASK, "generator_sha256": SOURCE_SHA, "rule_hash": GEN.RULE_HASH,
        "query_index": 1, "demo_indices": [0, 2], "pairs": witness_pairs,
        "rival_name": "filter_left_only",
        "rival_description": "Only color 1 on the left selects rows; every nonzero top cell selects a column. Clear markers and paint the Cartesian product with 8.",
        "rival_outputs": {name: [rival(pair["input"]) for pair in witness_pairs] for name, rival in RIVALS.items()},
        "rotations": rotations(witness_pairs),
        "domain_status": "All three are ordinary default generated inputs, with no overrides or mutations, and pass self_check/strict_canonical_like; not validator-only or out-of-domain witnesses.",
        "output_basis": "Independent Python calculations; public Racket confirmation is separate in racket.json.",
    })
    census = {"seeds": [10401, 10402, 10403], "starts": [0, 1, 2, 3],
              "bands": ["easy", "medium", "hard"], "overrides": {}, "lessons": 36,
              "labeled_pair_slots": 108, "rotations": 108, "ambiguous_rotations": ambiguous_count,
              "ambiguities_unreported_by_declared_competitors": missed_count,
              "production_query_ambiguous_lessons": 0, "all_input_slots_validator_accepted": 108,
              "label_basis": "Independent Python expression; no fresh Racket census labels."}
    dump("census.json", {"summary": census, "lessons": records})
    summary = {
        "schema": "8f6a6ec3ae21-one-sided-audit-v1", "task_id": TASK,
        "generator_sha256": SOURCE_SHA, "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH, "canonical_program_sha256": program_sha,
        "command": f"PYTHONDONTWRITEBYTECODE=1 {sys.executable} review.py run {sys.executable} ../checks/audit/{TASK}/probe.py",
        "invocation_cwd": str(ROOT.parents[1]), "effective_cwd": str(ROOT),
        "exit_code": 0, "status": "generated_lesson_ambiguity_python_confirmed_racket_pending",
        "canonical_demo_count": sum(p["split"] == "train" for p in canonical),
        "canonical_test_count": sum(p["split"] == "test" for p in canonical),
        "canonical_rival_fits": {name: len(canonical) for name in RIVALS}, "census": census,
        "source_argument": "Default decoy sides alternate by sample_index parity. Every consecutive triple has side pattern A,B,A. Holding out the middle leaves two A-only demos: the one-sided rival that filters A correctly still fits both, but includes the B decoy on the query.",
        "scope": "An actual-generated-support rotated-query teaching ambiguity. It is not an incorrect-label finding, a production consecutive-two-demo failure, or a failure against an already declared rival.",
        "source_changes": [], "existing_tests_rerun": False, "public_audit_preset_run": False,
    }
    dump("summary.json", summary)
    print(json.dumps({"status": summary["status"], "generator_sha256": SOURCE_SHA,
                      "canonical_rival_fits": summary["canonical_rival_fits"], "census": census}, indent=2))


if __name__ == "__main__":
    main()
