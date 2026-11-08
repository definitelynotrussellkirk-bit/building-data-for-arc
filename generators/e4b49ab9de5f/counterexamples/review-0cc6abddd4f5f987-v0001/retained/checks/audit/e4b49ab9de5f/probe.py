"""Focused findings-only audit. All authority outputs come from the public apply CLI."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
PACKET = WORK.parent
REPO = WORK / "repo"
TASK = "e4b49ab9de5f"
SOURCE = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
EXPECTED_SOURCE = "65e916351e71762f7f33ce15ba81c95a92a7cd0fc8f04fb929a8686b2124c0fe"


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def canonical_row():
    with CANONICAL.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row, sha_bytes(line.encode())
    raise RuntimeError("Canonical task absent")


def bindings():
    row, row_hash = canonical_row()
    rule_sha = sha_bytes(row["program_solution"].encode())
    return {
        "task_id": TASK,
        "generator_sha256": sha_file(SOURCE),
        "expected_assignment_generator_sha256": EXPECTED_SOURCE,
        "raw_canonical_program_sha256": rule_sha,
        "rule_hash": sha_bytes(" ".join(row["program_solution"].split()).encode())[:12],
        "canonical_row_sha256_including_newline": row_hash,
        "generator_path": str(SOURCE),
        "canonical_path": str(CANONICAL),
    }


def selected_module():
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("selected_audit_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    identity = bindings()
    assert identity["generator_sha256"] == EXPECTED_SOURCE, identity
    row, _ = canonical_row()
    module = selected_module()
    cases = []
    for difficulty in ("easy", "medium", "hard"):
        grid = module.generate(20261012, 0, difficulty=difficulty)
        cases.append({
            "name": "generated_" + difficulty,
            "origin": "selected generate function",
            "seed": 20261012,
            "sample_index": 0,
            "difficulty": difficulty,
            "overrides": {},
            "input": grid,
            "self_check": module.self_check(grid, difficulty=difficulty),
        })
    for index, pair in enumerate(row["train"]):
        grid = pair["input"]
        cases.append({
            "name": "canonical_train_" + str(index),
            "origin": "canonical training input",
            "canonical_variant": 0,
            "train_index": index,
            "input": grid,
            "self_check": module.self_check(grid),
        })
    for case in cases:
        case["top_row_nonzero_count"] = sum(v != 0 for v in case["input"][0])
    write("input.json", [case["input"] for case in cases])
    write("cases.json", {"bindings": identity, "cases": cases})
    task_home = SOURCE.parent
    write("context.json", {
        "bindings": identity,
        "notes": (task_home / "notes.md").read_text(),
        "notes_sha256": sha_file(task_home / "notes.md"),
        "associated_notes_bytes": (task_home / "evidence/associated_notes.jsonl").stat().st_size,
        "review_index_exists": (task_home / "evidence/review_index.json").exists(),
        "canonical_training_inputs": len(row["train"]),
        "canonical_training_inputs_with_top_row_color": sum(any(pair["input"][0]) for pair in row["train"]),
        "source_mechanism": "generate samples colored rows from range(1, h) for every normal difficulty branch; self_check flags any active top-row cell",
    })
    print(json.dumps({"prepared_inputs": len(cases), "bindings": identity}))


def drop_first_row_then_pack(grid):
    """Deliberately wrong rival; this function is never used as the authority."""
    out = [[0 for _ in grid[0]] for _ in grid]
    for col in range(len(grid[0])):
        values = [grid[row][col] for row in range(1, len(grid)) if grid[row][col] != 0]
        for row, value in enumerate(values):
            out[row][col] = value
    return out


def analyze():
    cases_record = json.loads((HERE / "cases.json").read_text())
    authority = json.loads((HERE / "racket.json").read_text())
    identity = bindings()
    previous = cases_record["bindings"]
    assert identity["generator_sha256"] == previous["generator_sha256"], "Source changed during audit"
    assert identity["canonical_row_sha256_including_newline"] == previous["canonical_row_sha256_including_newline"], "Canonical row changed during audit"
    # The initial audit script mislabeled the raw program hash as the runtime
    # callable-text hash; retain that failed attempt and accept the raw binding.
    assert identity["raw_canonical_program_sha256"] == previous.get("raw_canonical_program_sha256", previous.get("rule_text_sha256")), "Raw program changed"
    assert authority["generator_sha256"] == EXPECTED_SOURCE, authority
    assert authority["executed_rule_hash"] == identity["rule_hash"], authority
    assert authority["rule_hash_matches_catalog"], authority
    identity["executed_rule_callable_sha256"] = authority["rule_text_sha256"]
    results = []
    for case, observed in zip(cases_record["cases"], authority["results"], strict=True):
        assert observed["error"] is None, observed
        assert case["input"] == observed["input"], observed
        prediction = drop_first_row_then_pack(case["input"])
        differences = [
            {"row": r, "column": c, "racket": observed["output"][r][c], "rival": prediction[r][c]}
            for r in range(len(prediction)) for c in range(len(prediction[0]))
            if prediction[r][c] != observed["output"][r][c]
        ]
        results.append({**case, "racket_output": observed["output"], "rival_output": prediction,
                        "rival_matches_racket": not differences, "different_cells": differences,
                        "racket_input_sha256": observed["input_sha256"],
                        "racket_output_sha256": observed["output_sha256"]})
    generated = results[:3]
    canonical = results[3:]
    summary = {
        "status": "confirmed_generator_coverage_shortcut_and_validator_conflict",
        "bindings": identity,
        "generated_draws": 3,
        "generated_seed": 20261012,
        "generated_sample_index": 0,
        "generated_difficulties": ["easy", "medium", "hard"],
        "generated_rival_matches": sum(r["rival_matches_racket"] for r in generated),
        "generated_validator_passes": sum(not r["self_check"] for r in generated),
        "canonical_training_inputs": 4,
        "canonical_rival_mismatches": sum(not r["rival_matches_racket"] for r in canonical),
        "canonical_validator_rejections": sum(bool(r["self_check"]) for r in canonical),
        "unique_inputs": len({json.dumps(r["input"], separators=(",", ":")) for r in results}),
        "scope": "Three selected-generator draws and all four canonical training inputs; no battery, curriculum census, or solver/private data read.",
        "qualification": "Normal generation excludes row 0 by source construction, independent of the three sampled demonstrations. Explicit degenerate texture branches are excluded from that claim.",
        "authority": {"command": authority["command"], "cwd": authority["cwd"], "path": "checks/audit/e4b49ab9de5f/racket.json"},
    }
    write("witness.json", {"summary": summary, "cases": results})
    write("summary.json", summary)
    assert summary["generated_rival_matches"] == 3, summary
    assert summary["generated_validator_passes"] == 3, summary
    assert summary["canonical_rival_mismatches"] == 3, summary
    assert summary["canonical_validator_rejections"] == 3, summary
    print(json.dumps(summary))


def run(rescore=False):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PATH"] = str(WORK / ".venv-review/bin") + os.pathsep + env.get("PATH", "")
    env["TMPDIR"] = str(HERE / "tmp")
    (HERE / "tmp").mkdir(exist_ok=True)
    steps = [
        ("prepare", ["python3", str(Path(__file__).relative_to(PACKET)), "prepare"]),
        ("racket_apply", ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK,
                          "--input", "../checks/audit/e4b49ab9de5f/input.json", "--out", "../checks/audit/e4b49ab9de5f/racket.json",
                          "--check-generator-domain"]),
        ("analyze", ["python3", str(Path(__file__).relative_to(PACKET)), "analyze"]),
    ]
    if rescore:
        steps = [("analyze_v2", ["python3", str(Path(__file__).relative_to(PACKET)), "analyze"])]
    receipts = json.loads((HERE / "commands.json").read_text()) if rescore else []
    for name, argv in steps:
        before = bindings()
        started = datetime.now(timezone.utc).isoformat()
        proc = subprocess.run(argv, cwd=PACKET, env=env, capture_output=True, text=True)
        (HERE / (name + ".stdout.log")).write_text(proc.stdout)
        (HERE / (name + ".stderr.log")).write_text(proc.stderr)
        receipt = {
            "name": name, "argv": argv, "cwd": str(PACKET), "exit_code": proc.returncode,
            "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
            "python3_resolved_path": shutil.which("python3", path=env["PATH"]),
            "environment": {key: env[key] for key in ("PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "PATH", "TMPDIR")},
            "source_and_rule_before": before, "source_and_rule_after": bindings(),
            "audit_script_sha256": sha_file(Path(__file__)),
            "stdout_path": "checks/audit/e4b49ab9de5f/" + name + ".stdout.log",
            "stderr_path": "checks/audit/e4b49ab9de5f/" + name + ".stderr.log",
        }
        receipts.append(receipt)
        write("commands.json", receipts)
        print(json.dumps({"step": name, "exit_code": proc.returncode}), flush=True)
        if proc.returncode:
            print(proc.stdout + proc.stderr, file=sys.stderr)
            raise SystemExit(proc.returncode)


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze, "run": run, "rescore": lambda: run(rescore=True)}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
