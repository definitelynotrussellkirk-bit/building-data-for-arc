"""One finite learnability probe, replayable from this packet's review.py.

Run from packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/2a5919c40197/probe.py
No generator, rule, approval, or audit metadata is modified.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles import Catalog
from arc_repl.isolated_verifier import Limits, verify_candidate
from reviewer_support import load_selected_generator

TASK = "2a5919c40197"
EXPECTED_SOURCE = "d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a"
EXPECTED_RULE = "bb6a3cb8ba31"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def output(grid, ignore_last=False):
    return [[5 if len(set(row[:-1] if ignore_last else row)) == 1 else 0] * len(row)
            for row in grid]


def main():
    generator, path, source_sha = load_selected_generator(TASK, root=ROOT)
    selected = Catalog(ROOT).get(TASK)
    programs = {row["program_solution"] for row in selected["variants"]}
    assert len(programs) == 1, "Reference selection must be unambiguous"
    reference = programs.pop()
    rule_hash = digest(" ".join(reference.split()))[:12]
    assert source_sha == EXPECTED_SOURCE, "Selected source changed; review this probe before reuse"
    assert rule_hash == generator.RULE_HASH == EXPECTED_RULE
    assert reference.count("(row-at g r)") == 1
    rival = reference.replace("(row-at g r)", "(take (row-at g r) (- w 1))")

    # Replay exactly one rotation selected from the already completed 32-seed
    # mirror screen (nomination.json). That fixed-last-query screen had no
    # finding. Its seed 3 has one discrepant pair, sample 1; rotate that pair to
    # the query. No further seeds, rivals, dimensions, or bands are searched.
    seed = 3
    indices = [2, 3, 4, 1]
    grids = [generator.generate(seed, index, difficulty="easy") for index in indices]
    errors = [generator.self_check(grid) for grid in grids]
    assert not any(errors), errors
    matches = [output(grid) == output(grid, True) for grid in grids]
    assert matches == [True, True, True, False], matches
    search = [{"seed": seed, "sample_indices": indices,
               "shapes": [[len(g), len(g[0])] for g in grids],
               "rival_matches_mirror": matches}]
    witness = {"seed": seed, "grids": grids}

    report = {
        "schema": "arcpuzzles-bounded-peer-learnability-v1",
        "task_id": TASK,
        "source_path": path.relative_to(ROOT).as_posix(),
        "source_sha256": source_sha,
        "rule_hash": rule_hash,
        "reference_program": reference,
        "reference_program_sha256": digest(reference),
        "rival_description": "Ignore the final column, classify each remaining row by uniformity, and fill the original full width with 5 or 0.",
        "rival_program": rival,
        "rival_program_sha256": digest(rival),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": "WORK/.venv/bin/python review.py run --receipt checks/2a5919c40197/racket-command.json python3 ../checks/2a5919c40197/probe.py",
        "replay_command": "WORK/.venv/bin/python review.py run python3 ../checks/2a5919c40197/probe.py",
        "payload_argv": sys.argv,
        "payload_cwd": str(Path.cwd()),
        "racket_path": os.environ.get("RACKET_PATH"),
        "discovery_scope": "One mirror screen of seeds 0..31, easy samples 1..4, no fixed-fourth-query finding. The same outputs nominated seed 3 with sample 1 held out. No additional search. Original screen retained in nomination.json; replay needs only this script and the packet.",
        "bounded_replay": {"seeds": [3], "difficulty": "easy", "sample_indices": indices,
                           "rivals": 1, "trials_executed": search},
        "limits": [
            "One rival and at most 32 four-pair lessons; no full suite, battery, or acceptance run.",
            "This rival is not consistent with the complete original canonical training set: its third pair already refutes it.",
            "The question is whether an individual generated three-demo lesson supports this rival while its query distinguishes it.",
            "A survivor is a bounded teaching gap, not proof that the intended rule is unlearnable or that reference labels are incorrect.",
            "The existing declared-rival guarantee concerns first-three-only; this is a different rival and does not contradict that narrower guarantee.",
            "Current source and canonical rule remain unchanged; no approval or training-admission claim."
        ],
    }
    if witness is None:
        report["outcome"] = "bounded_no_finding"
        report["reason"] = "No selected-rival survivor in the predeclared finite search; no claim about other seeds or rivals."
    else:
        grids = witness["grids"]
        task = {"train": [{"input": grid, "output": output(grid)} for grid in grids[:3]],
                "test": [{"input": grids[3]}]}
        limits = Limits(wall_seconds=45, step_seconds=5, cpu_seconds=30, max_pairs=4)
        ref_result = verify_candidate(task, reference, racket_path=os.environ["RACKET_PATH"], limits=limits)
        report["reference_execution"] = ref_result
        assert ref_result["status"] == "pass", ref_result
        # Use the executed reference outputs as visible labels for the rival.
        for pair, actual in zip(task["train"], ref_result["train_outputs"]):
            pair["output"] = actual
        task["test"][0]["output"] = ref_result["test_outputs"][0]
        rival_result = verify_candidate(task, rival, racket_path=os.environ["RACKET_PATH"], limits=limits)
        report["rival_execution"] = rival_result
        report["witness"] = {"seed": witness["seed"], "sample_indices": indices,
                             "difficulty": "easy", "task": task,
                             "self_check_errors": [generator.self_check(g) for g in grids],
                             "lesson_identifiable_reasons": generator.lesson_identifiable(task["train"], task["test"][0])}
        if rival_result["status"] == "pass" and rival_result["hidden_exact"] is False:
            report["outcome"] = "bounded_generated_lesson_ambiguity"
            report["finding"] = "Both exact Racket programs fit all three generated demos, but return different query grids; the current lesson_identifiable hook accepts the lesson."
            report["suggested_next_step"] = "Add ignore-final-column as an explicit lesson competitor and require a demonstration with a mixed row whose prefix excluding the final cell is uniform; then rerun this exact lesson and one small schedule check before selecting any repair."
        else:
            report["outcome"] = "bounded_no_verified_finding"
            report["reason"] = "Python nomination did not establish a surviving divergent rival in protected Racket; inspect execution receipt."
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"outcome": report["outcome"], "source_sha256": source_sha,
                      "trials": len(search), "seed": witness and witness["seed"],
                      "result": str(HERE / "result.json")}))


if __name__ == "__main__":
    main()
