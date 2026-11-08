"""Verify the retained public-API witness, or reproduce it in a fresh directory.

Run this through run_with_racket.py from WORK, with payload cwd WORK/repo.
No target module or private Racket runner is imported. Canonical outputs come
only from `python -m arcpuzzles apply --check-generator-domain`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


TASK_ID = "d552baa9e49e"
SEED = 104729


def json_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read_episode(directory):
    lines = (directory / "production.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def prepare_inputs(directory):
    episode = read_episode(directory)
    write_json(directory / "input.json", {
        "inputs": [pair["input"] for pair in episode["train"] + episode["test"]]
    })


def independent_transform(grid, swap=False):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
              if value != 0 and (r, c) != (0, 0)]
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    command = grid[0][0]
    if swap:
        command = {4: 5, 5: 4}.get(command, command)
    if command == 1:
        return [list(row) for row in zip(*crop[::-1])]
    if command == 2:
        return [row[::-1] for row in crop[::-1]]
    if command == 3:
        return [list(row) for row in zip(*crop)]
    if command == 4:
        return [row[::-1] for row in crop]
    if command == 5:
        return [row[:] for row in crop[::-1]]
    raise ValueError(command)


def fresh_run(directory):
    directory.mkdir(parents=True, exist_ok=False)
    commands = []

    def run(args, evidence):
        argv = [sys.executable, "-m", "arcpuzzles", *args]
        result = subprocess.run(argv, text=True, capture_output=True)
        commands.append({"argv": argv, "cwd": str(Path.cwd()),
                         "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr,
                         "evidence_paths": evidence})
        write_json(directory / "fresh_commands.json", commands)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)

    run(["generate", TASK_ID, "--count", "1", "--seed", str(SEED),
         "--sample-index", "1", "--difficulty", "medium", "--timeout", "120",
         "--out", str(directory / "production.jsonl")], ["production.jsonl"])
    prepare_inputs(directory)
    run(["apply", TASK_ID, "--input", str(directory / "input.json"),
         "--check-generator-domain", "--timeout", "120", "--out",
         str(directory / "racket.json")], ["input.json", "racket.json"])


def verify(directory):
    episode = read_episode(directory)
    applied = json.loads((directory / "racket.json").read_text())
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert episode["seed"] == SEED and episode["sample_indices"] == [1, 2, 3, 4]
    assert episode["sampling"]["rejections"] == []
    assert episode["provenance"]["overrides"] == {}
    assert [pair["input"][0][0] for pair in pairs] == [2, 3, 1, 4]
    assert len(applied["results"]) == 4
    source = Path.cwd() / "generators" / TASK_ID / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == applied["generator_sha256"]
    assert source_hash == episode["provenance"]["generator_sha256"]
    rule_sha256 = hashlib.sha256(episode["program"].encode()).hexdigest()
    assert rule_sha256 == applied["rule_text_sha256"]

    details = []
    for index, (pair, result) in enumerate(zip(pairs, applied["results"])):
        assert result["error"] is None and result["valid_output"] is True
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert result["input"] == pair["input"]
        assert result["input_sha256"] == json_hash(pair["input"])
        assert result["output"] == pair["output"]
        assert independent_transform(pair["input"]) == result["output"]
        rival = independent_transform(pair["input"], swap=True)
        details.append({"split": "train" if index < 3 else "test",
                        "sample_index": episode["sample_indices"][index],
                        "command": pair["input"][0][0],
                        "input_sha256": result["input_sha256"],
                        "actual_output": result["output"],
                        "actual_output_sha256": result["output_sha256"],
                        "rival_output": rival, "rival_output_sha256": json_hash(rival),
                        "rival_matches": rival == result["output"],
                        "self_check": result["generator_domain"]})
    assert all(row["rival_matches"] for row in details[:3])
    assert not details[3]["rival_matches"]

    report = {
        "finding_id": "D552-F1-reconfirmed",
        "status": "reproduced_teaching_defect",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": rule_sha256,
        "lead": "review-f9811448dcb983fe:v0001, unresolved D552-F1; same source hash",
        "recipe": {"seed": SEED, "sample_index": 1, "sample_indices": [1, 2, 3, 4],
                   "difficulty": "medium", "overrides": {},
                   "demonstrations": 3, "queries": 1,
                   "ordering": "unmodified public production order"},
        "rival": "Swap command 4 and 5 meanings; preserve commands 1, 2, 3.",
        "domain": "All four are unmodified production inputs, and public apply records self_check valid for each.",
        "lesson_check": episode["lesson_check"],
        "production_rejections": episode["sampling"]["rejections"],
        "count": {"episodes": 1, "unique_inputs": len({row["input_sha256"] for row in details}),
                  "demo_matches": 3, "demo_total": 3, "query_differences": 1, "query_total": 1},
        "query_input": pairs[3]["input"],
        "pairs": details,
        "scope": "One fresh seed/start/band; no broad frequency estimate, query rotations, task_tests, or battery run.",
        "rival_limit": "The swap is a lesson-level ambiguity, not a claim that the rival fits the complete canonical dataset.",
    }
    write_json(directory / "finding.json", report)
    print(json.dumps({"status": report["status"], "counts": report["count"],
                      "generator_sha256": source_hash,
                      "report": str(directory / "finding.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-dir", type=Path)
    args = parser.parse_args()
    evidence = Path(__file__).resolve().parent
    if args.fresh_dir:
        evidence = args.fresh_dir.resolve()
        fresh_run(evidence)
    verify(evidence)
