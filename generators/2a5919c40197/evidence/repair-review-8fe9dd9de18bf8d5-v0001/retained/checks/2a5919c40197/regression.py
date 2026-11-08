"""Focused proposal checks; selected source is never overwritten.

From packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/2a5919c40197/regression.py
Red regression only:
  WORK/.venv/bin/python review.py run python3 ../checks/2a5919c40197/regression.py --selected --witness-only
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
EXPECTED = "d222d3cf44d694716979214022e8f461ee2995df4a635c868b291e9a3a82178a"
RIVAL = "ignore the final column of each row"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def label(grid):
    return [[5 if all(v == row[0] for v in row) else 0] * len(row) for row in grid]


def final_change(grid):
    return any(all(v == row[0] for v in row[:-1]) and row[-1] != row[0] for row in grid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected", action="store_true")
    parser.add_argument("--witness-only", action="store_true")
    args = parser.parse_args()
    selected, selected_path, selected_sha = load_selected_generator(TASK, root=ROOT)
    assert selected_sha == EXPECTED
    candidate_path = selected_path if args.selected else HERE / "proposed_generator.py"
    if args.selected:
        candidate = selected
    else:
        spec = importlib.util.spec_from_file_location("peer_proposed_2a5919c40197", candidate_path)
        candidate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate)
    report = {"schema": "arcpuzzles-peer-proposal-regression-v1", "task_id": TASK,
              "selected_sha256": selected_sha, "candidate_sha256": sha(candidate_path),
              "regression_sha256": sha(__file__), "argv": sys.argv,
              "cwd": str(Path.cwd()), "checks": [],
              "integration_status": "owner_selection_pending",
              "limits": ["Focused checks only; no battery, full suite, approval or training admission.",
                         "Schedule checks use an independent Python full-row label; four changed inputs are additionally checked through protected Racket.",
                         "Boundary tests temporarily replace only the candidate module dimension draw, exercising real row construction at height three."]}
    try:
        original = json.loads((HERE / "result.json").read_text())
        task = original["witness"]["task"]
        reasons = candidate.lesson_identifiable(task["train"], task["test"][0])
        assert any(RIVAL in reason for reason in reasons), (
            "saved divergent-rival lesson must be rejected; got", reasons)
        report["checks"].append({"name": "saved_ambiguity_rejected", "reasons": reasons})
        if not args.witness_only:
            assert candidate.RULE_HASH == selected.RULE_HASH == "bb6a3cb8ba31"
            assert candidate.EXAMPLES_NEEDED == selected.EXAMPLES_NEEDED == 3
            assert candidate.SCHEDULE_PROFILES == selected.SCHEDULE_PROFILES
            assert RIVAL in candidate.LESSON_COMPETITORS
            assert RIVAL not in candidate.CANONICAL_SHORTCUTS
            rotations, scenes, labels_for_racket = 0, [], []
            for band in (None, "easy", "medium", "hard"):
                for seed in (0, 3):
                    pairs = []
                    for index in range(5):
                        grid = candidate.generate(seed, index, difficulty=band)
                        assert candidate.self_check(grid) == []
                        assert candidate.schedule_profile(seed, index, band) == selected.schedule_profile(seed, index, band)
                        if index % 2:
                            assert final_change(grid), (band, seed, index)
                            assert candidate._has_late_change_after_three(grid)
                            assert candidate.LESSON_COMPETITORS[RIVAL](grid) != label(grid)
                            if seed == 3 and index == 1:
                                labels_for_racket.append({"input": grid, "output": label(grid)})
                        else:
                            assert grid == selected.generate(seed, index, difficulty=band), "anchor stream changed"
                        pairs.append({"input": grid, "output": label(grid)})
                        scenes.append({"seed": seed, "sample_index": index, "difficulty": band,
                                       "input": grid, "output": label(grid)})
                    for start in (0, 1):
                        window = pairs[start:start + 4]
                        for query_index in range(4):
                            demos = [p for i, p in enumerate(window) if i != query_index]
                            assert candidate.lesson_identifiable(demos, window[query_index]) == [], (band, seed, start, query_index)
                            rotations += 1
            report["checks"].append({"name": "schedule_and_query_rotations", "scenes": len(scenes),
                                     "lessons": 16, "rotations": rotations, "data": scenes})
            boundaries = []
            original_dimensions = candidate._broad_dimensions
            try:
                for width in (4, 5):
                    candidate._broad_dimensions = lambda ctx, width=width: (3, width)
                    grid = candidate.generate(3, 1, difficulty="easy", scene_profile="width_extension")
                    assert (len(grid), len(grid[0])) == (3, width)
                    assert candidate.self_check(grid) == []
                    assert final_change(grid) and candidate._has_late_change_after_three(grid)
                    if width > 4:
                        assert any(row[0] == row[-1] and len(set(row)) > 1 for row in grid), "interior witness lost"
                    boundaries.append({"height": 3, "width": width, "input": grid, "output": label(grid)})
            finally:
                candidate._broad_dimensions = original_dimensions
            report["checks"].append({"name": "minimum_height_width_feasibility", "cases": boundaries})
            programs = {v["program_solution"] for v in Catalog(ROOT).get(TASK)["variants"]}
            assert len(programs) == 1
            reference = programs.pop()
            racket = verify_candidate({"train": labels_for_racket, "test": []}, reference,
                                      racket_path=os.environ["RACKET_PATH"],
                                      limits=Limits(wall_seconds=45, step_seconds=5, cpu_seconds=30, max_pairs=4))
            report["protected_racket"] = {"program": reference,
                                           "program_sha256": hashlib.sha256(reference.encode()).hexdigest(),
                                           "task": {"train": labels_for_racket, "test": []}, "result": racket}
            assert racket["status"] == "pass", racket
            report["checks"].append({"name": "four_changed_samples_reference_labels", "pairs": len(labels_for_racket)})
        assert sha(selected_path) == EXPECTED
        report["selected_source_unchanged"] = True
        report["status"] = "pass"
    except Exception as error:
        report["status"] = "fail"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    out = HERE / ("regression-before.json" if args.selected else "regression-result.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]),
                      "result": str(out), "error": report.get("error")}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
