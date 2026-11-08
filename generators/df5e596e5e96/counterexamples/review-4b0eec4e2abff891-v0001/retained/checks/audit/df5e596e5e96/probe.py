"""Findings-only audit of reflection/rotation priority on symmetric supports."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "df5e596e5e96"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def hashed(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def normalized(cells):
    top, left = min(row for row, _ in cells), min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def rotations(cells):
    answer = []
    current = normalized(cells)
    for _ in range(4):
        answer.append(current)
        current = normalized({(col, -row) for row, col in current})
    return answer


def reflection_first_rival(grid):
    panels = [normalized({(row, col) for row in range(5) for col in range(5)
                          if grid[row][start + col] != 0})
              for start in range(0, len(grid[0]), 6)]
    result = []
    for row, left in enumerate(panels):
        reflected = rotations({(rr, -cc) for rr, cc in left})
        rotated = rotations(left)
        result.append([
            8 if row == col else 1 if left == right else
            3 if right in reflected else 2 if right in rotated else 0
            for col, right in enumerate(panels)
        ])
    return result


def symmetric_witness():
    # First two panels are distinct rotations of a T tetromino. Because T is
    # reflection-symmetric, a reflected rotation also maps one to the other.
    panels = [
        [(0, 0), (0, 1), (0, 2), (1, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (0, 2), (1, 0)],
    ]
    offsets = [(1, 1), (1, 1), (2, 0)]
    grid = [[0] * 17 for _ in range(5)]
    for index, (cells, (top, left)) in enumerate(zip(panels, offsets)):
        for row, col in cells:
            grid[top + row][index * 6 + left + col] = 4
    return grid


def source_binding(generator_path, generator_sha):
    ledger = canonical_path(ROOT)
    rows = [json.loads(line) for line in ledger.open() if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
    if len(programs) != 1:
        raise AssertionError("canonical authority is ambiguous")
    program = programs.pop()
    return {
        "generator_path": str(generator_path.relative_to(ROOT)),
        "generator_sha256": generator_sha,
        "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_program": program,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def prepare():
    gen, path, source_sha = load_selected_generator(TASK, root=ROOT)
    binding = source_binding(path, source_sha)
    witness = symmetric_witness()
    expected = [[8, 2, 0], [2, 8, 0], [0, 0, 8]]
    assert gen.self_check(witness) == []
    assert gen.strict_canonical_like(witness) == []
    assert gen.rule_mirror(witness) == expected
    assert reflection_first_rival(witness) == [[8, 3, 0], [3, 8, 0], [0, 0, 8]]
    cases = [{"kind": "symmetric_priority_witness", "input": witness,
              "expected_output": expected, "rival_output": reflection_first_rival(witness),
              "self_check": gen.self_check(witness),
              "strict_canonical_like": gen.strict_canonical_like(witness)}]
    canonical_results = []
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        rival = reflection_first_rival(pair["input"])
        result = {"kind": "canonical", "variant": pair["variant"], "split": pair["split"],
                  "pair_index": pair["pair_index"], "input": pair["input"],
                  "expected_output": pair["output"], "rival_output": rival,
                  "rival_matches": rival == pair["output"], "self_check": gen.self_check(pair["input"])}
        cases.append(result)
        canonical_results.append({key: value for key, value in result.items()
                                  if key not in ("input", "expected_output", "rival_output")})
    for difficulty in (None, "easy", "medium", "hard"):
        for n_panels in (3, 4, 5):
            for sample_index in range(4):
                grid = gen.generate(1700, sample_index, difficulty=difficulty, n_panels=n_panels)
                cases.append({"kind": "generated", "seed": 1700, "sample_index": sample_index,
                              "difficulty": difficulty, "overrides": {"n_panels": n_panels},
                              "input": grid, "expected_output": gen.rule_mirror(grid),
                              "rival_output": reflection_first_rival(grid),
                              "self_check": gen.self_check(grid)})
    assert len(cases) == 54
    write("inputs.json", {"inputs": [case["input"] for case in cases]})
    write("cases.json", {"source_binding": binding, "cases": cases})
    matches, total, failures, domain_failures = 0, 0, [], []
    for difficulty in (None, "easy", "medium", "hard"):
        for n_panels in (3, 4, 5):
            for seed in range(16):
                for sample_index in range(8):
                    grid = gen.generate(seed, sample_index, difficulty=difficulty, n_panels=n_panels)
                    total += 1
                    errors = gen.self_check(grid)
                    if errors:
                        domain_failures.append({"seed": seed, "sample_index": sample_index,
                                               "difficulty": difficulty, "n_panels": n_panels,
                                               "errors": errors})
                    if reflection_first_rival(grid) == gen.rule_mirror(grid):
                        matches += 1
                    else:
                        failures.append({"seed": seed, "sample_index": sample_index,
                                         "difficulty": difficulty, "n_panels": n_panels})
    write("mirror-census.json", {
        "scope": "Python-mirror census; Racket confirmation is the separate 54-input apply batch",
        "source_binding": binding, "seed_range": [0, 15], "sample_index_range": [0, 7],
        "difficulty": [None, "easy", "medium", "hard"], "n_panels": [3, 4, 5],
        "count": total, "rival_matches": matches, "rival_mismatches": failures,
        "self_check_failures": domain_failures, "canonical": canonical_results,
    })
    print(json.dumps({"prepared_inputs": len(cases), "census_count": total,
                      "rival_matches": matches,
                      "canonical_rival_matches": sum(row["rival_matches"] for row in canonical_results),
                      "generator_sha256": source_sha}))


def summarize():
    gen, path, source_sha = load_selected_generator(TASK, root=ROOT)
    cases_record = json.loads((OUT / "cases.json").read_text())
    cases = cases_record["cases"]
    receipt = json.loads((OUT / "racket.json").read_text())
    assert receipt["generator_sha256"] == source_sha == cases_record["source_binding"]["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    results = receipt["results"]
    assert len(results) == len(cases)
    comparisons = []
    for index, (case, result) in enumerate(zip(cases, results)):
        assert result["error"] is None
        actual = result["output"]
        assert actual == case["expected_output"]
        comparisons.append({"index": index, "kind": case["kind"], "input_sha256": hashed(case["input"]),
                            "self_check": case["self_check"], "expected_matches_racket": True,
                            "rival_matches_racket": case["rival_output"] == actual})
    demos = [{"input": case["input"], "output": results[index]["output"]}
             for index, case in enumerate(cases)
             if case["kind"] == "generated" and case["difficulty"] is None
             and case["overrides"] == {"n_panels": 5} and case["sample_index"] in (0, 1, 2)]
    query = {"input": cases[0]["input"], "output": results[0]["output"]}
    assert len(demos) == 3
    rival_fits_demos = all(reflection_first_rival(pair["input"]) == pair["output"] for pair in demos)
    assert rival_fits_demos
    hook = gen.lesson_identifiable(demos, query)
    write("lesson-witness.json", {
        "train": demos, "test": [query], "rival_query_output": reflection_first_rival(query["input"]),
        "rival_fits_all_demos": rival_fits_demos, "generator_lesson_identifiable": hook,
        "demo_recipe": {"seed": 1700, "sample_indices": [0, 1, 2], "difficulty": None,
                        "overrides": {"n_panels": 5}},
        "query_origin": "hand-constructed lawful validator-domain input; absent from generated motif-role support",
    })
    canonical_witnesses = []
    for index, case in enumerate(cases):
        if case["kind"] != "canonical" or case["rival_output"] == results[index]["output"]:
            continue
        canonical_query = {"input": case["input"], "output": results[index]["output"]}
        canonical_witnesses.append({
            "variant": case["variant"], "split": case["split"], "pair_index": case["pair_index"],
            "train": demos, "test": [canonical_query], "rival_query_output": case["rival_output"],
            "rival_fits_all_demos": rival_fits_demos,
            "generator_lesson_identifiable": gen.lesson_identifiable(demos, canonical_query),
            "self_check": gen.self_check(case["input"]),
            "query_origin": "unaltered canonical pair, used as an audit query after three generated demonstrations",
        })
    write("canonical-lesson-witness.json", canonical_witnesses)
    write("assessment.json", {
        "status": "finding", "severity": "teaching_coverage", "task_id": TASK,
        "finding": "Generated lessons do not distinguish reflection priority from rotation priority on symmetric supports.",
        "source_binding": cases_record["source_binding"],
        "racket_identity": {key: receipt.get(key) for key in (
            "generator_sha256", "catalog_rule_hash", "executed_rule_hash", "rule_hash_matches_catalog",
            "rule_text_sha256", "reference", "runtime_identity")},
        "input_count": len(cases), "comparisons": comparisons,
        "racket_generated_rival_matches": sum(row["kind"] == "generated" and row["rival_matches_racket"] for row in comparisons),
        "racket_canonical_rival_matches": sum(row["kind"] == "canonical" and row["rival_matches_racket"] for row in comparisons),
        "canonical_priority_witnesses": [
            {key: witness[key] for key in ("variant", "split", "pair_index", "self_check", "generator_lesson_identifiable")}
            for witness in canonical_witnesses
        ],
        "witness": {"input": query["input"], "authoritative_output": query["output"],
                    "rival_output": reflection_first_rival(query["input"]),
                    "self_check": gen.self_check(query["input"]),
                    "strict_canonical_like": gen.strict_canonical_like(query["input"]),
                    "generator_lesson_identifiable": hook},
        "limits": "No mislabeled sampled input was found. Broad census uses Python mirror; authoritative confirmation covers 54 inputs. The rival is refuted by canonical train[3], so it is a generated-curriculum coverage gap, not a canonical-fitting shortcut. Hand-made query is validator-valid but not emitted by the current role/motif schedule. No target source was edited.",
        "proposed_fix": "Add a rotated symmetric motif pair to ordinary lessons and declare a reflection-before-rotation rival; preserve exact-match precedence and the pinned Racket rule.",
    })
    print(json.dumps({"racket_inputs": len(cases), "rival_fits_three_demos": rival_fits_demos,
                      "lesson_hook": hook, "witness_expected": query["output"],
                      "witness_rival": reflection_first_rival(query["input"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "summarize"))
    arguments = parser.parse_args()
    prepare() if arguments.phase == "prepare" else summarize()
