"""Bounded source-bound audit: vertical-neighbor filling shortcut."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
TASK_ID = "ad668d162e0a"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def rival(grid):
    """Fill a zero whenever its immediate north/south colors match nonzero."""
    out = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(len(grid[0])):
            if grid[r][c] == 0 and grid[r - 1][c] != 0 and grid[r - 1][c] == grid[r + 1][c]:
                out[r][c] = grid[r - 1][c]
    return out


spec = importlib.util.spec_from_file_location("audited_ad668d162e0a", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
with (REPO / "shared/data/canonical/puzzles.jsonl").open() as stream:
    row = next(item for line in stream if (item := json.loads(line)).get("task_id") == TASK_ID)
canonical = row["train"][1]
samples = [{
    "index": 0,
    "origin": "selected canonical row train[1]",
    "seed": None,
    "sample_index": None,
    "difficulty": "canonical easy",
    "overrides": {},
    "input": canonical["input"],
}]
for index in range(6):
    band = ("easy", "medium", "hard")[index // 2]
    samples.append({
        "index": index + 1,
        "origin": "ordinary generation from explicit audited source path",
        "seed": 20261006,
        "sample_index": index,
        "difficulty": band,
        "overrides": {},
        "input": gen.generate(20261006, index, difficulty=band),
    })
for sample in samples:
    sample["self_check"] = gen.self_check(sample["input"])
    sample["rival_output"] = rival(sample["input"])
save("input.json", {"inputs": [sample["input"] for sample in samples]})
save("rival.json", {"rival": "matching immediate nonzero north/south neighbors", "samples": samples})
save("canonical_expected.json", canonical["output"])
command = [
    "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
    "--input", "../checks/audit/ad668d162e0a/input.json",
    "--out", "../checks/audit/ad668d162e0a/racket.json",
]
run = subprocess.run(command, cwd=PACKET, text=True, capture_output=True)
(HERE / "stdout.txt").write_text(run.stdout)
(HERE / "stderr.txt").write_text(run.stderr)
rule = row["program_solution"]
receipt = {
    "task_id": TASK_ID,
    "phase": "final unchanged audit source",
    "generator_path": str(SOURCE),
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "canonical_row": "repo/shared/data/canonical/puzzles.jsonl task_id=ad668d162e0a",
    "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
    "normalized_rule_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
    "generator_rule_hash": gen.RULE_HASH,
    "command": command,
    "cwd": str(PACKET),
    "effective_payload_cwd": str(REPO),
    "exit_code": run.returncode,
    "probe_command": "PYTHONPATH=repo/src:repo/shared/runtime python3 checks/audit/ad668d162e0a/probe.py",
    "probe_cwd": str(PACKET),
    "seed": 20261006,
    "sample_index_range": [0, 5],
    "ordinary_generation_count": 6,
    "ordinary_generation_overrides": {},
    "evidence_paths": [str(HERE / name) for name in (
        "probe.py", "input.json", "rival.json", "racket.json", "canonical_expected.json",
        "stdout.txt", "stderr.txt", "summary.json", "audit.md",
    )],
}
save("command.json", receipt)
if run.returncode:
    raise SystemExit(run.returncode)
applied = json.loads((HERE / "racket.json").read_text())
comparisons = []
for sample, result in zip(samples, applied["results"], strict=True):
    actual = result["output"]
    sample["racket_output"] = actual
    comparisons.append({
        "index": sample["index"], "origin": sample["origin"],
        "seed": sample["seed"], "sample_index": sample["sample_index"],
        "difficulty": sample["difficulty"], "overrides": sample["overrides"],
        "self_check": sample["self_check"],
        "valid_racket_output": result["valid_output"],
        "rival_matches_racket": sample["rival_output"] == actual,
        "differences": [
            {"row": r, "column": c, "racket": actual[r][c], "rival": value}
            for r, line in enumerate(sample["rival_output"])
            for c, value in enumerate(line) if actual is not None and value != actual[r][c]
        ],
    })
demos = [{"input": sample["input"], "output": sample["racket_output"]} for sample in samples[1:5]]
query = {"input": samples[0]["input"], "output": samples[0]["racket_output"]}
summary = {
    "task_id": TASK_ID,
    "generator_sha256": receipt["generator_sha256"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "rule_hash": applied["executed_rule_hash"],
    "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
    "canonical_racket_matches_stored_output": samples[0]["racket_output"] == canonical["output"],
    "canonical_passes_validator": not samples[0]["self_check"],
    "generated_samples": 6,
    "unique_generated_inputs": len({json.dumps(sample["input"]) for sample in samples[1:]}),
    "generated_rival_matches_racket": sum(item["rival_matches_racket"] for item in comparisons[1:]),
    "lesson_identifiable_four_generated_demos_canonical_query": gen.lesson_identifiable(demos, query),
    "comparisons": comparisons,
}
save("summary.json", summary)
print(json.dumps(summary, indent=2))
