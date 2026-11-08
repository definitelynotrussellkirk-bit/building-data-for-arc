"""Read-only audit; prepare eight grids and call the supported public apply once."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from reviewer_support import canonical_pairs, canonical_path

TASK = "8e6c44aee812"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_run_per_color(grid):
    """Keep each color's first complete diagonal run, discard later runs."""
    diag = [grid[i][i] for i in range(min(len(grid), len(grid[0])))]
    while diag and diag[-1] == 0:
        diag.pop()
    seen, sequence = set(), []
    previous, keep = None, False
    for value in diag:
        if value != previous:
            keep = value not in seen
            seen.add(value)
            previous = value
        if keep:
            sequence.append(value)
    return [[sequence[max(r, c) % len(sequence)] for c in range(2 * len(grid[0]))]
            for r in range(2 * len(grid))]


def main():
    source = REPO / "generators" / TASK / "generator.py"
    before = sha(source)
    spec = importlib.util.spec_from_file_location("audited_generator_8e6c44aee812", source)
    gen = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gen
    spec.loader.exec_module(gen)
    canonical = canonical_pairs(TASK, root=REPO, labeled_only=True)
    with canonical_path(REPO).open() as handle:
        rows = (json.loads(line) for line in handle if line.strip())
        records = [row for row in rows if row.get("task_id") == TASK]
    assert len(records) == 1
    generated = [{"seed": 0, "sample_index": i, "difficulty": "easy", "overrides": {},
                  "input": gen.generate(0, i, difficulty="easy")} for i in range(5, 9)]
    inputs = [row["input"] for row in canonical] + [row["input"] for row in generated]
    (HERE / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
    python = WORK / ".venv/bin/python"
    command = [str(python), "review.py", "run", str(python), "-m", "arcpuzzles", "apply", TASK,
               "--input", f"../checks/audit/{TASK}/input.json",
               "--out", f"../checks/audit/{TASK}/racket.json"]
    env = os.environ.copy()
    env["TMPDIR"] = "/dev/shm/arc-review-604d32c6dec0-tmp"
    result = subprocess.run(command, cwd=WORK.parent, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (HERE / "apply.log").write_text(result.stdout)
    report = {"schema": "arcpuzzles-focused-shortcut-audit-v1", "task_id": TASK,
              "generator_sha256": before,
              "rule_text_sha256": hashlib.sha256(records[0]["program_solution"].encode()).hexdigest(),
              "script_sha256": sha(Path(__file__)), "input_sha256": sha(HERE / "input.json"),
              "command": {"argv": command, "cwd": str(WORK.parent), "payload_cwd": str(REPO),
                          "env": {"TMPDIR": env["TMPDIR"]}, "exit_code": result.returncode},
              "notes_sha256": sha(source.parent / "notes.md"),
              "review_index_present": (source.parent / "evidence/review_index.json").is_file()}
    if report["review_index_present"]:
        report["review_index_sha256"] = sha(source.parent / "evidence/review_index.json")
    if result.returncode:
        report["status"] = "reference_execution_failed"
        (HERE / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return result.returncode
    applied = json.loads((HERE / "racket.json").read_text())
    outputs = applied["results"]
    assert len(outputs) == len(inputs) and all(row["error"] is None and row["valid_output"] for row in outputs)
    report["public_apply"] = {key: applied[key] for key in ["generator_sha256", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog"]}
    report["public_apply_report_sha256"] = sha(HERE / "racket.json")
    report["canonical"] = [{"split": pair["split"], "pair_index": pair["pair_index"],
                              "reference_matches_label": row["output"] == pair["output"],
                              "rival_matches_label": first_run_per_color(pair["input"]) == pair["output"],
                              "self_check": gen.self_check(pair["input"])}
                             for pair, row in zip(canonical, outputs[:len(canonical)], strict=True)]
    report["generated"] = []
    for draw, row in zip(generated, outputs[len(canonical):], strict=True):
        rival = first_run_per_color(draw["input"])
        report["generated"].append({**draw, "output": row["output"], "rival_output": rival,
                                    "diagonal": [draw["input"][i][i] for i in range(len(draw["input"]))],
                                    "self_check": gen.self_check(draw["input"]),
                                    "observed_axes": gen.observe_overrides(draw["input"]),
                                    "rival_matches_reference": rival == row["output"]})
    demos = [{"input": row["input"], "output": row["output"]} for row in report["generated"][:3]]
    query = {key: report["generated"][3][key] for key in ("input", "output")}
    report["lesson_identifiable_reasons"] = gen.lesson_identifiable(demos, query)
    report["rival_in_declared_competitors"] = "first_run_per_color" in gen.LESSON_COMPETITORS
    report["generator_source_stable"] = before == sha(source)
    report["reproduced_shortcut_gap"] = (report["generator_source_stable"]
        and all(row["reference_matches_label"] and row["rival_matches_label"] for row in report["canonical"])
        and all(not row["self_check"] for row in report["generated"])
        and all(row["rival_matches_reference"] for row in report["generated"][:3])
        and not report["generated"][3]["rival_matches_reference"]
        and report["lesson_identifiable_reasons"] == [])
    report["classification"] = "reproduced shortcut / finite lesson-contract gap; no incorrect reference label alleged"
    (HERE / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ["generator_sha256", "rule_text_sha256", "public_apply", "canonical", "lesson_identifiable_reasons", "generator_source_stable", "reproduced_shortcut_gap", "classification"]}, indent=2))
    print(json.dumps([{key: row[key] for key in ["sample_index", "diagonal", "observed_axes", "self_check", "rival_matches_reference"]} for row in report["generated"]], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
