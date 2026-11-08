"""Bounded source-bound replay of the retained missing-black-pair finding."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

TASK = "38b5470ad5f5"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[1] / "repo"


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(raw(value)).hexdigest()


def main():
    catalog = Catalog(ROOT)
    selected = catalog.describe(TASK)
    source = ROOT / selected["generator"]
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    canonical = {row["program_solution"] for row in
                 catalog._variants()[selected.get("rule_task_id", TASK)]}
    assert len(canonical) == 1
    program = next(iter(canonical))
    target = "(!= (at g r c) bg)"
    assert program.count(target) == 2
    rival = program.replace(target, "(and (!= (at g r c) bg) (!= (at g r c) 0))")
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HOME):
        from reviewer_support import canonical_pairs, load_selected_generator
        generator, path, source_sha = load_selected_generator(TASK, root=ROOT)
        assert path == source and source_sha == before
        execute, identity, bridge = _real_evaluator(runtime)
        try:
            draws = []
            for seed in (0, 17):
                for sample_index in range(7):
                    inp = _grid(generator.generate(seed, sample_index))
                    actual = _grid(execute(program, inp))
                    alternative = _grid(execute(rival, inp))
                    draws.append({"seed": seed, "sample_index": sample_index,
                                  "role": "demo" if sample_index < 3 else "query",
                                  "input": inp, "output": actual, "rival_output": alternative,
                                  "has_zero": any(0 in row for row in inp),
                                  "rival_agrees": actual == alternative})
            fixture = next(pair for pair in canonical_pairs(TASK, root=ROOT)
                           if pair["variant"] == 0 and pair["split"] == "train"
                           and pair["pair_index"] == 2)
            inp = _grid(fixture["input"])
            actual = _grid(execute(program, inp))
            alternative = _grid(execute(rival, inp))
            assert actual == _grid(fixture["output"])
            assert actual != alternative
            assert generator.self_check(inp) == []
        finally:
            bridge.close()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    assert all(draw["rival_agrees"] and not draw["has_zero"] for draw in draws)
    witness = {"task_id": TASK, "generator_sha256": before,
               "rule_hash": selected["rule_hash"], "program": program,
               "rival_program": rival, "racket": identity,
               "train": [{"input": row["input"], "output": row["output"]}
                         for row in draws if row["seed"] == 0 and row["role"] == "demo"],
               "test": [{"input": inp, "output": actual, "rival_output": alternative}],
               "query_origin": "canonical variant 0 train[2], held out from the generated demonstrations",
               "query_reachable_from_current_generator": False,
               "self_check_errors": [],
               "different_cell_count": sum(a != b for ar, br in zip(actual, alternative)
                                           for a, b in zip(ar, br)),
               "finding": "Zero-as-background fits generated demonstrations but fails the canonical black-pair branch."}
    execution = {"schema": "arcpuzzles-peer-bounded-replay-v1", "task_id": TASK,
                 "generator_sha256": before, "program": program, "rival_program": rival,
                 "racket": identity, "draws": draws}
    for filename, value in (("executions.json", execution), ("witness.json", witness)):
        with (HOME / filename).open("xb") as handle:
            handle.write(raw(value))
    report = {"schema": "arcpuzzles-peer-bounded-report-v1", "task_id": TASK,
              "status": "existing_missing_canonical_branch_reproduced",
              "generator_sha256": before, "rule_hash": selected["rule_hash"],
              "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
              "rival_program_sha256": hashlib.sha256(rival.encode()).hexdigest(),
              "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "source_approved": selected["approved"], "racket": identity,
              "seeds": [0, 17], "samples_per_seed": 7,
              "demos_per_seed": 3, "queries_per_seed": 4,
              "generated_draws": len(draws), "unique_generated_inputs": len({digest(r["input"]) for r in draws}),
              "generated_draws_with_zero": sum(r["has_zero"] for r in draws),
              "generated_rival_agreements": sum(r["rival_agrees"] for r in draws),
              "canonical_witness_different_cells": witness["different_cell_count"],
              "racket_evaluations": 2 * (len(draws) + 1),
              "evidence": {name: hashlib.sha256((HOME / name).read_bytes()).hexdigest()
                           for name in ("executions.json", "witness.json")},
              "payload_argv": list(sys.argv),
              "command": ["python3", "review.py", "run", "python3", "../checks/38b5470ad5f5/probe.py"],
              "command_cwd": "outer packet extraction directory; wrapper selects WORK/repo",
              "command_exit_code": 0,
              "source_changed": False, "owner_checked": False, "training_admitted": False,
              "limits": "One retained rival, two seeds, default difficulty and 14 draws. The failure is a canonical-domain coverage gap: "
                        "the held-out black query is not produced by current palettes. No generated-query disagreement, new fix, full battery, "
                        "native approval, or training admission is claimed. Existing unresolved evidence is confirmed, not cleared."}
    with (HOME / "report.json").open("xb") as handle:
        handle.write(raw(report))
    print(json.dumps({key: report[key] for key in ("status", "generated_draws", "generated_draws_with_zero",
                                                  "generated_rival_agreements", "canonical_witness_different_cells",
                                                  "racket_evaluations", "training_admitted")}, indent=2))


if __name__ == "__main__":
    main()
