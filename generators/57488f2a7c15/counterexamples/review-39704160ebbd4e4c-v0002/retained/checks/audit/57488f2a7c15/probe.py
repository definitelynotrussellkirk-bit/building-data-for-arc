#!/usr/bin/env python3
"""Reproduce the completed-color shortcut on an ordinary five-demo lesson.

From WORK:
  python3 checks/audit/57488f2a7c15/probe.py

For a fresh independent replay, use --out checks/audit/57488f2a7c15/replay.
This script writes evidence only. Reference labels come from the native API
and the public Racket apply command, never from the rival implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

TASK = "57488f2a7c15"
EXPECTED_SHA = "695c31b0bf2506cde10a9f240b78d59f1bb5efd85038186bc9f532d4305eeaa7"
SEED, START, BAND = 0, 17, "easy"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def completed_colors(grid):
    return {grid[r][c] for r in range(len(grid)) for c in range(r + 1, len(grid))
            if grid[r][c] and grid[r][c] == grid[c][r]}


def rival(grid):
    """A color with any completed off-diagonal pair is already finished."""
    done = completed_colors(grid)
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color and color not in done:
                output[c][r] = color
    return output


def omitted_sources(grid):
    done = completed_colors(grid)
    return [{"source": [r, c], "destination": [c, r], "color": value}
            for r, row in enumerate(grid) for c, value in enumerate(row)
            if value in done and r != c and not grid[c][r]]


def materialize(out):
    from arcpuzzles import Catalog
    from reviewer_support import canonical_pairs, find_root, load_selected_generator

    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK, root=root)
    assert digest == EXPECTED_SHA, (source, digest)
    catalog = Catalog(root=root)
    # Deliberately omit n_train: this verifies the current public default.
    episode, = catalog.generate(TASK, seed=SEED, sample_index=START,
                                difficulty=BAND, count=1, n_test=1, timeout=120)
    dump(out / "episode.json", episode)
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 5 and len(episode["test"]) == 1
    assert [p["input"] for p in pairs] == [
        generator.generate(SEED, i, difficulty=BAND) for i in range(START, START + 6)]
    assert all(generator.self_check(p["input"], difficulty=BAND) == [] for p in pairs)
    query = episode["test"][0]["input"]
    dump(out / "input.json", query)
    dump(out / "rival.json", rival(query))
    canonical = canonical_pairs(TASK, root=root)
    dump(out / "canonical-pairs.json", canonical)
    report = catalog.apply(TASK, [p["input"] for p in canonical], timeout=120)
    dump(out / "canonical-racket.json", report)
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    selected = [line for line in ledger.read_bytes().splitlines()
                if json.loads(line).get("task_id") == TASK]
    assert len(selected) == 1
    row = json.loads(selected[0])
    dump(out / "hashes.json", {
        "task_id": TASK, "generator_sha256": digest,
        "generator_path": str(source.relative_to(root)),
        "canonical_rule_hash": catalog.describe(TASK)["rule_hash"],
        "raw_rule_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
        "canonical_row_sha256_no_newline": hashlib.sha256(selected[0]).hexdigest(),
        "canonical_ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    print(json.dumps({"phase": "audit", "generated_episodes": 1,
                      "generated_racket_labels": 6, "canonical_apply_labels": len(canonical),
                      "train_count": len(episode["train"]), "seed": SEED,
                      "sample_index": START, "difficulty": BAND,
                      "generator_sha256": digest}))


def verify(out):
    from reviewer_support import find_root, load_selected_generator

    generator, _, digest = load_selected_generator(TASK, root=find_root(__file__))
    assert digest == EXPECTED_SHA
    episode = json.loads((out / "episode.json").read_text())
    reference = json.loads((out / "racket.json").read_text())
    canonical = json.loads((out / "canonical-pairs.json").read_text())
    canonical_reference = json.loads((out / "canonical-racket.json").read_text())
    inputs = episode["train"] + episode["test"]
    query = episode["test"][0]
    assert reference["rule_hash_matches_catalog"]
    assert len(reference["results"]) == 1
    assert reference["results"][0]["valid_output"]
    actual = reference["results"][0]["output"]
    assert actual == query["output"]
    assert json.loads((out / "input.json").read_text()) == query["input"]
    assert json.loads((out / "rival.json").read_text()) == rival(query["input"])
    demo_agreement = [rival(p["input"]) == p["output"] for p in episode["train"]]
    assert all(demo_agreement)
    assert rival(query["input"]) != actual
    assert canonical_reference["rule_hash_matches_catalog"]
    canonical_agreement = []
    for pair, result in zip(canonical, canonical_reference["results"], strict=True):
        assert result["valid_output"] and result["output"] == pair["output"]
        canonical_agreement.append(rival(pair["input"]) == result["output"])
    assert len(canonical_agreement) == 5 and all(canonical_agreement)
    declared_result = generator.lesson_identifiable(episode["train"], query)
    assert declared_result == []
    differences = [{"position": [r, c], "racket": value,
                    "rival": rival(query["input"])[r][c]}
                   for r, row in enumerate(actual) for c, value in enumerate(row)
                   if rival(query["input"])[r][c] != value]
    assessment = {
        "status": "reproduced_teaching_counterexample", "phase": "audit",
        "task_id": TASK, "generator_sha256": digest,
        "seed": SEED, "sample_index": START, "difficulty": BAND,
        "overrides": {}, "n_train_requested": None, "n_train_actual": 5,
        "n_test": 1, "accepted_sample_indices": list(range(START, START + 6)),
        "demonstration_agreement": demo_agreement,
        "canonical_agreement": canonical_agreement,
        "query_agrees": False, "query_differences": differences,
        "declared_rivals_count": len(generator.LESSON_COMPETITORS),
        "declared_lesson_identifiable": declared_result,
        "native_lesson_check": episode.get("lesson_check"),
        "demonstration_policy": episode["provenance"]["demonstration_policy"],
        "self_check_errors": [generator.self_check(p["input"], difficulty=BAND) for p in inputs],
        "completed_colors": [sorted(completed_colors(p["input"])) for p in inputs],
        "omitted_sources": [omitted_sources(p["input"]) for p in inputs],
        "scope": "One ordinary ordered production lesson, six generated labels, five canonical labels, one independent query rerun. No prevalence or universal identifiability claim.",
    }
    dump(out / "assessment.json", assessment)
    print(json.dumps(assessment))


def reproduce(out):
    script = Path(__file__).resolve()
    work = next(p for p in script.parents if (p / "run_with_racket.py").is_file())
    repo = work / "repo"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("episode.json", "input.json", "racket.json", "assessment.json", "commands.json"):
        if (out / name).exists():
            raise FileExistsError(f"Use a fresh --out directory: {out / name}")
    script_arg = "../" + str(script.relative_to(work))
    out_arg = "../" + str(out.relative_to(work))
    prefix = ["python3", "run_with_racket.py", "python3"]
    jobs = [
        ("materialize", prefix + [script_arg, "--mode", "materialize", "--out", out_arg]),
        ("apply", prefix + ["-m", "arcpuzzles", "apply", TASK,
                             "--input", out_arg + "/input.json", "--out", out_arg + "/racket.json"]),
        ("verify", prefix + [script_arg, "--mode", "verify", "--out", out_arg]),
    ]
    commands = []
    for name, argv in jobs:
        start = time.monotonic()
        run = subprocess.run(argv, cwd=work, text=True, capture_output=True)
        (out / f"{name}.stdout.txt").write_text(run.stdout)
        (out / f"{name}.stderr.txt").write_text(run.stderr)
        commands.append({"phase": "audit", "cwd": str(work),
                         "effective_payload_cwd": str(repo), "argv": argv,
                         "exit_code": run.returncode, "elapsed_seconds": round(time.monotonic() - start, 3),
                         "stdout": f"{name}.stdout.txt", "stderr": f"{name}.stderr.txt"})
        dump(out / "commands.json", {"task_id": TASK, "phase": "audit", "commands": commands,
                                      "executed_count": len(commands),
                                      "exit_zero_count": sum(c["exit_code"] == 0 for c in commands),
                                      "nonzero_exit_count": sum(c["exit_code"] != 0 for c in commands)})
        print(f"{name}: exit {run.returncode}", flush=True)
        if run.returncode:
            print(run.stderr, file=sys.stderr)
            return run.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("reproduce", "materialize", "verify"), default="reproduce")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.mode == "reproduce":
        return reproduce(out)
    {"materialize": materialize, "verify": verify}[args.mode](out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
