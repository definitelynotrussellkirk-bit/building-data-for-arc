"""Findings-only audit: an undeclared horizontal-only endpoint rival."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
SOURCE = REPO / "generators/142a3a64b02a/generator.py"
TASK = "142a3a64b02a"

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")

def horizontal_only(grid):
    """Cap endpoints only of whole horizontal red components; ignore vertical."""
    out = [row[:] for row in grid]
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 2}
    while remaining:
        cell = remaining.pop()
        component, stack = {cell}, [cell]
        while stack:
            r,c = stack.pop()
            for other in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if other in remaining:
                    remaining.remove(other)
                    component.add(other)
                    stack.append(other)
        if len({r for r,c in component}) == 1:
            r = next(iter(component))[0]
            cols = [c for _,c in component]
            out[r][min(cols)] = out[r][max(cols)] = 4
    return out

def main():
    spec = importlib.util.spec_from_file_location("audit_142a3a64b02a_source", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    grids = [module.generate(0, i, difficulty="easy") for i in range(4)]
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            rule = row["program_solution"]
            row_hash = hashlib.sha256(line.encode()).hexdigest()
            break
    save("input.json", {"inputs": grids})
    save("rival-output.json", {"name": "horizontal_whole_red_components_only", "outputs": [horizontal_only(g) for g in grids]})
    (HERE / "selected-rule.rkt").write_text(rule + "\n")
    receipt = {
        "task_id": TASK,
        "generator_path": str(SOURCE),
        "generator_sha256": source_hash,
        "canonical_row_sha256": row_hash,
        "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "normalized_rule_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "declared_rule_hash": module.RULE_HASH,
        "seed": 0, "sample_indices": [0,1,2,3], "difficulty": "easy", "overrides": {},
        "demonstration_indices": [0,1,2], "query_index": 3,
        "probe_invocation": {"command": "PYTHONPATH=repo/src:repo/shared/runtime python3 checks/audit/142a3a64b02a/probe.py", "cwd": str(PACKET), "exit_code": None},
        "commands": [],
        "scope": "One orientation hypothesis, seed 0, four consecutive direct samples plus public production generation. No full battery or census.",
    }
    commands = [
        ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/142a3a64b02a/input.json", "--out", "../checks/audit/142a3a64b02a/racket.json"],
        ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate", TASK, "--count", "1", "--seed", "0", "--sample-index", "0", "--difficulty", "easy", "--train", "3", "--test", "1", "--out", "../checks/audit/142a3a64b02a/production.jsonl"],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, cwd=PACKET, text=True, capture_output=True, timeout=60)
        (HERE / f"command-{index}.stdout.txt").write_text(result.stdout)
        (HERE / f"command-{index}.stderr.txt").write_text(result.stderr)
        receipt["commands"].append({"argv": command, "cwd": str(PACKET), "effective_payload_cwd": str(REPO), "exit_code": result.returncode, "stdout": f"command-{index}.stdout.txt", "stderr": f"command-{index}.stderr.txt"})
        save("command.json", receipt)
        if result.returncode:
            print(result.stdout, result.stderr)
            raise SystemExit(result.returncode)
    authority = json.loads((HERE / "racket.json").read_text())
    pairs = [{"input": g, "output": result["output"]} for g,result in zip(grids,authority["results"])]
    production = json.loads((HERE / "production.jsonl").read_text().splitlines()[0])
    production_pairs = production["train"] + production["test"]
    report = {
        "status": "reproduced_teaching_ambiguity",
        "generator_sha256": source_hash,
        "executed_rule_hash": authority["executed_rule_hash"],
        "racket_agrees_with_python_mirror": [pair["output"] == module.rule_mirror(pair["input"]) for pair in pairs],
        "self_check": [module.self_check(g) for g in grids],
        "rival_matches": [horizontal_only(pair["input"]) == pair["output"] for pair in pairs],
        "lesson_identifiable": module.lesson_identifiable(pairs[:3], pairs[3]),
        "production_pairs_equal_direct_pairs": production_pairs == pairs,
        "production_sample_indices": production.get("sample_indices"),
        "production_rejections": production.get("rejections"),
        "query_difference_cells_zero_based": [[r,c, horizontal_only(grids[3])[r][c], pairs[3]["output"][r][c]] for r in range(len(grids[3])) for c in range(len(grids[3][0])) if horizontal_only(grids[3])[r][c] != pairs[3]["output"][r][c]],
    }
    save("lesson.json", {"seed": 0, "difficulty": "easy", "sample_indices": [0,1,2,3], "overrides": {}, "train": pairs[:3], "test": pairs[3:]})
    save("report.json", report)
    assert report["rival_matches"] == [True,True,True,False]
    assert report["production_pairs_equal_direct_pairs"]
    assert all(report["racket_agrees_with_python_mirror"])
    assert report["lesson_identifiable"] == []
    receipt["probe_invocation"]["exit_code"] = 0
    receipt["evidence_paths"] = [str(p.relative_to(PACKET)) for p in sorted(HERE.iterdir()) if p.is_file()]
    receipt["evidence_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.is_file() and p.name != "command.json"}
    save("command.json", receipt)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
