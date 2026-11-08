"""Focused, source-bound audit; Racket execution is a separate public CLI step."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "72dbce4d594b"
EXPECTED_SOURCE = "a6dba3cfd52647f610cd11abab494e063f8d766dc054f70c0e9ba90ee7e67880"


def load(repo):
    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audited_generator", repo / "generators" / TASK / "generator.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    digest = hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    assert digest == EXPECTED_SOURCE, digest
    return gen


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def prepare(repo, out, gen):
    from reviewer_support import canonical_pairs, canonical_path
    selected = [json.loads(line) for line in canonical_path(repo).read_text().splitlines()
                if json.loads(line).get("task_id") == TASK]
    assert len(selected) == 1
    source = selected[0]["program_solution"]
    rule_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert rule_hash == gen.RULE_HASH == "d291f7b88b55"
    cases = []
    def add(grid, kind, **identity):
        assert gen.self_check(grid) == [], (kind, identity, gen.self_check(grid))
        cases.append({"case_index": len(cases), "kind": kind, "input": grid,
                      "self_check_errors": [], "documented_rule_domain_accepted": True,
                      "generator_sha256": EXPECTED_SOURCE, "canonical_rule_hash": rule_hash,
                      **identity})
    for pair in canonical_pairs(TASK, root=repo):
        add(pair["input"], "canonical", variant=pair["variant"], split=pair["split"],
            pair_index=pair["pair_index"], canonical_output=pair["output"],
            seed=None, sample_index=None, overrides=None)
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1):
            for index in range(6):
                grid = gen.generate(seed, index, difficulty=band)
                assert grid == gen.generate(seed, index, difficulty=band)
                add(grid, "default_generated", seed=seed, sample_index=index, difficulty=band,
                    overrides={}, observed_axes=gen.observe_overrides(grid))
    for rank in (1, 2, 3):
        for code in (1, 2, 3, 4):
            overrides = dict(grid_h=11, grid_w=12, rank=rank, transform=code,
                             size_profile="asymmetric_468", red_layout="scattered",
                             green_layout="scattered", target_zone="bottom_right")
            grid = gen.generate(7001, 17, difficulty="medium", **overrides)
            assert gen.observe_overrides(grid) == overrides
            add(grid, "override_generated", seed=7001, sample_index=17, difficulty="medium",
                overrides=overrides, observed_axes=gen.observe_overrides(grid))
    # Test the explicitly documented distinction between the rule grammar and
    # curriculum policy: a target footprint may overlap source objects.
    base = cases[6]
    grid = copy.deepcopy(base["input"])
    old = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8)
    grid[old[0]][old[1]] = 0
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v != 0:
                continue
            grid[r][c] = 8
            if not gen.self_check(grid):
                output = gen.rule_mirror(grid)
                if any(output[rr][cc] == 7 and grid[rr][cc] == 1
                       for rr in range(len(grid)) for cc in range(len(grid[0]))):
                    add(copy.deepcopy(grid), "lawful_overlap_counterfactual",
                        seed=None, sample_index=None, overrides=None,
                        derived_from_case_index=base["case_index"], old_target=list(old),
                        new_target=[r, c], generator_distribution_member=False,
                        domain_reason="Three distinct blue components and legal fixed markers are preserved; the stamp fits. Empty destination is explicitly a curriculum choice, not the validator grammar.")
                    break
            grid[r][c] = 0
        else:
            continue
        break
    assert len(cases) == 54, len(cases)
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "input.json", [case["input"] for case in cases])
    dump(out / "cases.json", cases)
    dump(out / "identity.json", {"task_id": TASK, "generator_sha256": EXPECTED_SOURCE,
                                "canonical_rule_hash": rule_hash,
                                "canonical_rule_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                                "canonical_pair_count": 5, "case_count": len(cases)})
    print(json.dumps({"prepared": len(cases), "canonical_rule_hash": rule_hash}))


def verify(out, gen):
    cases = json.loads((out / "cases.json").read_text())
    result = json.loads((out / "racket.json").read_text())
    print("Racket result keys:", sorted(result))
    assert result["generator_sha256"] == EXPECTED_SOURCE
    assert result["reference"] == "canonical"
    assert result["executed_rule_hash"] == result["catalog_rule_hash"] == gen.RULE_HASH
    records = result["results"]
    assert len(records) == len(cases)
    labels = {}
    parity = []
    for case, record in zip(cases, records):
        output = record["output"]
        assert record["valid_output"] and record["error"] is None
        assert gen.rule_mirror(case["input"]) == output, case["case_index"]
        if case["kind"] == "canonical":
            assert output == case["canonical_output"], case["case_index"]
        labels[case["case_index"]] = output
        parity.append({"case_index": case["case_index"], "kind": case["kind"], "passed": True})
    lessons = []
    rotations = []
    rival_checks = {name: {"demo_survival_count": 0, "query_disagreement_after_survival": 0}
                    for name in gen.LESSON_COMPETITORS}
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1):
            stream = [case for case in cases if case["kind"] == "default_generated"
                      and case["difficulty"] == band and case["seed"] == seed]
            assert len(stream) == 6
            for query_pos in range(6):
                demos = [{"input": c["input"], "output": labels[c["case_index"]]}
                         for pos, c in enumerate(stream) if pos != query_pos]
                query = stream[query_pos]
                findings = gen.lesson_identifiable(demos, {"input": query["input"]})
                row = {"seed": seed, "start": 0, "difficulty": band,
                       "query_position": query_pos, "query_case_index": query["case_index"],
                       "demo_case_indices": [c["case_index"] for pos, c in enumerate(stream) if pos != query_pos],
                       "findings": findings, "passed": not findings}
                rotations.append(row)
                if query_pos == 5:
                    lessons.append(row)
                    assert not findings, row
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        survives = all(rival(d["input"]) == d["output"] for d in demos)
                        rival_checks[name]["demo_survival_count"] += int(survives)
                        rival_checks[name]["query_disagreement_after_survival"] += int(survives and rival(query["input"]) != labels[query["case_index"]])
    report = {"task_id": TASK, "generator_sha256": EXPECTED_SOURCE,
              "canonical_rule_hash": gen.RULE_HASH, "reference_parity": parity,
              "reference_parity_passed": len(parity), "reference_parity_total": len(cases),
              "unique_inputs": len({json.dumps(c["input"], separators=(",", ":")) for c in cases}),
              "production_policy": "Five consecutive demonstrations at sample indices 0..4; index 5 query",
              "production_passed": sum(row["passed"] for row in lessons), "production_total": len(lessons),
              "production_lessons": lessons, "declared_competitors": rival_checks,
              "rotation_policy": "Diagnostic: each of the six positions becomes query, other five are demonstrations",
              "rotation_passed": sum(row["passed"] for row in rotations), "rotation_total": len(rotations),
              "rotations": rotations,
              "limitation": "Rotation failures reproduce the existing ordered-curriculum limitation explicitly documented in notes.md; this audit does not relabel them as a new source defect."}
    dump(out / "report.json", report)
    failure = next(row for row in rotations if not row["passed"])
    rival_name = failure["findings"][0].split("'")[1]
    rival = gen.LESSON_COMPETITORS[rival_name]
    query_case = cases[failure["query_case_index"]]
    demo_cases = [cases[i] for i in failure["demo_case_indices"]]
    dump(out / "known_rotation_witness.json", {
        "classification": "Reproduced documented ordered-curriculum limitation; not a new source defect",
        "task_id": TASK, "generator_sha256": EXPECTED_SOURCE,
        "canonical_rule_hash": gen.RULE_HASH, "rival_name": rival_name,
        "rival_fits_all_five_demos": all(rival(c["input"]) == labels[c["case_index"]] for c in demo_cases),
        "query_identity": {k: query_case[k] for k in ("case_index", "seed", "sample_index", "difficulty", "overrides", "self_check_errors", "documented_rule_domain_accepted")},
        "demo_sample_indices": [c["sample_index"] for c in demo_cases],
        "input": query_case["input"],
        "actual_racket_output": labels[query_case["case_index"]],
        "rival_output": rival(query_case["input"]),
        "authoritative_label_evidence": "WORK/checks/audit/72dbce4d594b/racket.json results[6]",
        "label_command_cwd": "packet_root",
        "label_command": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK,
                          "--input", "../checks/audit/72dbce4d594b/input.json", "--out", "../checks/audit/72dbce4d594b/racket.json"]})
    print(json.dumps({k: report[k] for k in ("reference_parity_passed", "reference_parity_total", "unique_inputs", "production_passed", "production_total", "rotation_passed", "rotation_total")}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    gen = load(args.repo.resolve())
    if args.mode == "prepare":
        prepare(args.repo.resolve(), args.out.resolve(), gen)
    else:
        verify(args.out.resolve(), gen)


if __name__ == "__main__":
    main()
