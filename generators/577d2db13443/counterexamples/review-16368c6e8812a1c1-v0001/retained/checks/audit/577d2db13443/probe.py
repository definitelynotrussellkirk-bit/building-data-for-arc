"""Findings-only audit. Reference labels come exclusively from public CLI apply."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "577d2db13443"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
GENERATOR = REPO / "generators" / TASK / "generator.py"
EXPECTED_GENERATOR = "806f53221ad5dca44db6230fcadb9d0b8606f954126206d5adf194008c18a23a"
SEED = 5772026
BANDS = ("easy", "medium", "hard")


def load_generator():
    digest = hashlib.sha256(GENERATOR.read_bytes()).hexdigest()
    assert digest == EXPECTED_GENERATOR, digest
    spec = importlib.util.spec_from_file_location("audited_generator_577d2db13443", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selected_canonical():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError("selected canonical row missing")


def as_grid(rows):
    return [[int(cell) for cell in row] for row in rows]


def rival(grid):
    """Cap nonzero segments; split further only around horizontal singletons.

    This detects short isolated colors but ignores boundaries joining two runs
    of length >= 2. It does not call the generator's row-run parser/oracle.
    """
    result = [row[:] for row in grid]
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            left = row[c - 1] if c else 0
            right = row[c + 1] if c + 1 < width else 0
            if left == 0 or right == 0:
                result[r][c] = 1
            if value != left and value != right:
                result[r][c] = 1
                if left:
                    result[r][c - 1] = 1
                if right:
                    result[r][c + 1] = 1
    return result


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    gen = load_generator()
    canonical = selected_canonical()
    records = []
    for split in ("train", "test"):
        for index, pair in enumerate(canonical[split]):
            records.append({"name": f"canonical_{split}_{index}", "kind": "canonical",
                            "input": as_grid(pair["input"]),
                            "canonical_output": as_grid(pair["output"]),
                            "seed": None, "sample_index": None, "overrides": None})
    for band in BANDS:
        for index in range(7):
            records.append({"name": f"generated_{band}_{index}", "kind": "generated",
                            "input": gen.generate(SEED, index, difficulty=band),
                            "seed": SEED, "sample_index": index, "difficulty": band,
                            "overrides": {}})
    base = as_grid(canonical["train"][0]["input"])
    for name, row in (("adjacent_long_long", "022224440000"),
                      ("adjacent_pair_pair", "000224400000")):
        grid = [line[:] for line in base]
        grid[1] = [int(cell) for cell in row]
        records.append({"name": name, "kind": "manual_canonical_mutation", "input": grid,
                        "seed": None, "sample_index": None, "overrides": None,
                        "construction": "Replace canonical train[0] row 1 with " + row,
                        "declared_invariant_and_validator_domain": True,
                        "in_generator_sampling_support": False})
    rule = canonical["program_solution"]
    for record in records:
        grid = record["input"]
        record["self_check"] = gen.self_check(grid)
        record["strict_canonical_like"] = gen.strict_canonical_like(grid)
        record["observed_axes"] = gen.observe_overrides(grid)
        record["rival_output"] = rival(grid)
    dump("input.json", [record["input"] for record in records])
    dump("cases.json", {
        "task_id": TASK, "source_state": "unchanged audit baseline",
        "generator_sha256": EXPECTED_GENERATOR,
        "generator_rule_hash": gen.RULE_HASH,
        "canonical_program_solution_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "sampler": "direct selected generate(seed=5772026, sample_index=0..6 inclusive, difficulty=band), no overrides",
        "lesson_policy": "For each band, 3 consecutive demos then the next query; starts 0..3 inclusive (all 4 schedule phases). Windows overlap.",
        "cases": records,
    })
    print(json.dumps({"prepared_inputs": len(records), "output": "checks/audit/577d2db13443/input.json"}))


def analyze():
    gen = load_generator()
    data = json.loads((HERE / "cases.json").read_text())
    reference = json.loads((HERE / "racket.json").read_text())
    assert reference["generator_sha256"] == EXPECTED_GENERATOR
    assert reference["executed_rule_hash"] == gen.RULE_HASH
    assert reference["rule_hash_matches_catalog"]
    assert len(reference["results"]) == len(data["cases"])
    for record, answer in zip(data["cases"], reference["results"]):
        assert answer["input"] == record["input"]
        assert answer["valid_output"] and answer["error"] is None
        record["actual_racket_output"] = answer["output"]
        record["input_sha256"] = answer["input_sha256"]
        record["output_sha256"] = answer["output_sha256"]
        record["rival_agrees"] = record["rival_output"] == answer["output"]
        record["differing_cells_zero_based"] = [
            {"row": r, "column": c, "racket": value, "rival": record["rival_output"][r][c]}
            for r, row in enumerate(answer["output"])
            for c, value in enumerate(row) if record["rival_output"][r][c] != value
        ]
        assert record["self_check"] == []
        assert record["strict_canonical_like"] == []
    canonical = [case for case in data["cases"] if case["kind"] == "canonical"]
    generated = [case for case in data["cases"] if case["kind"] == "generated"]
    boundary = [case for case in data["cases"] if case["kind"] == "manual_canonical_mutation"]
    for case in canonical:
        assert case["actual_racket_output"] == case["canonical_output"]
        assert case["rival_agrees"]
    assert all(case["rival_agrees"] for case in generated)
    assert all(not case["rival_agrees"] for case in boundary)
    shortcuts = {
        name: {"matches": sum(fn(case["input"]) == case["actual_racket_output"] for case in canonical),
               "denominator": len(canonical)}
        for name, fn in gen.CANONICAL_SHORTCUTS.items()
    }
    assert all(item["matches"] == item["denominator"] for item in shortcuts.values())
    competitors = {
        name: {"canonical_matches": sum(fn(case["input"]) == case["actual_racket_output"] for case in canonical),
               "canonical_denominator": len(canonical),
               "generated_disagreements": sum(fn(case["input"]) != case["actual_racket_output"] for case in generated),
               "generated_denominator": len(generated)}
        for name, fn in gen.LESSON_COMPETITORS.items()
    }
    lessons = []
    for band in BANDS:
        by_index = {case["sample_index"]: case for case in generated if case["difficulty"] == band}
        for start in range(4):
            demos = [{"input": by_index[i]["input"], "output": by_index[i]["actual_racket_output"]}
                     for i in range(start, start + 3)]
            query = by_index[start + 3]
            reasons = gen.lesson_identifiable(demos, {"input": query["input"], "output": query["actual_racket_output"]})
            assert reasons == [], reasons
            surviving = [name for name, fn in gen.LESSON_COMPETITORS.items()
                         if all(fn(pair["input"]) == pair["output"] for pair in demos)]
            accepted_boundary_queries = []
            for case in boundary:
                boundary_reasons = gen.lesson_identifiable(demos, {"input": case["input"], "output": case["actual_racket_output"]})
                assert boundary_reasons == [], boundary_reasons
                accepted_boundary_queries.append(case["name"])
            lessons.append({"difficulty": band, "seed": SEED, "start": start,
                            "demo_indices": list(range(start, start + 3)), "query_index": start + 3,
                            "lesson_identifiable": reasons, "declared_surviving_competitors": surviving,
                            "audit_rival_survives_demonstrations": all(rival(pair["input"]) == pair["output"] for pair in demos),
                            "accepted_boundary_query_names": accepted_boundary_queries})
    identities = {key: reference[key] for key in ("generator_sha256", "executed_rule_hash", "rule_text_sha256")}
    identities["canonical_program_solution_sha256"] = data["canonical_program_solution_sha256"]
    command = {"cwd": "packet_root", "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                "--input", "../checks/audit/577d2db13443/input.json", "--out", "../checks/audit/577d2db13443/racket.json"],
               "actual_wrapper_cwd": str(ROOT), "actual_apply_cwd": reference["cwd"], "exit_code": 0}
    dump("counterexamples.json", {"task_id": TASK, "classification": "reproduced distribution shortcut",
         **identities, "reference_command": command, "cases": boundary})
    report = {"task_id": TASK, "classification": "reproduced distribution shortcut", **identities,
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "actual_reference_successes": len(data["cases"]), "actual_reference_denominator": len(data["cases"]),
              "validator_successes": len(data["cases"]), "validator_denominator": len(data["cases"]),
              "canonical_rival_matches": sum(case["rival_agrees"] for case in canonical), "canonical_denominator": len(canonical),
              "generated_rival_matches": sum(case["rival_agrees"] for case in generated), "generated_denominator": len(generated),
              "generated_unique_inputs": len({case["input_sha256"] for case in generated}),
              "boundary_rival_failures": sum(not case["rival_agrees"] for case in boundary), "boundary_denominator": len(boundary),
              "canonical_shortcuts_from_live_declaration": shortcuts,
              "competitors_from_live_declaration": competitors,
              "sampler": data["sampler"], "lesson_policy": data["lesson_policy"],
              "lesson_denominator": len(lessons), "lessons": lessons,
              "scope_limit": "21 generated inputs and 12 overlapping lesson windows are a finite check. The broader absence of adjacent nonsingleton runs follows from the selected packing and placement source, not a random-sample confidence claim."}
    dump("findings.json", report)
    dump("cases.json", data)
    print(json.dumps({key: value for key, value in report.items() if key not in ("lessons", "competitors_from_live_declaration")}))


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
