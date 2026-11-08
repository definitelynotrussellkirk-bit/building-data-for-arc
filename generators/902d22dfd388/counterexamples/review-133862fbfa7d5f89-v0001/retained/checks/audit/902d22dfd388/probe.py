#!/usr/bin/env python3
"""Scoped adversarial probe; uses only this generator and its canonical row."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
TASK = "902d22dfd388"
GENPATH = PACKET / "repo/generators" / TASK / "generator.py"
sys.path.insert(0, str(PACKET / "repo/shared/runtime"))
spec = importlib.util.spec_from_file_location("audit_target", GENPATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def rival(grid):
    """Ignore color 7 and canvas-perimeter cells; crop/center everything else."""
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
             if grid[r][c] not in (0, 7)]
    r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
    c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
    top, left = (h - (r1 - r0 + 1)) // 2, (w - (c1 - c0 + 1)) // 2
    out = [[0] * w for _ in range(h)]
    for r, c in cells:
        out[top + r - r0][left + c - c0] = grid[r][c]
    return out


def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n")


def main():
    with (PACKET / "repo/shared/data/canonical/puzzles.jsonl").open() as source:
        for line in source:
            if '"task_id": "' + TASK + '"' in line:
                row = json.loads(line)
                break
        else:
            raise AssertionError("target canonical row missing")
    canonical = [*row["train"], row["test"]]
    cases = []
    for index, pair in enumerate(canonical):
        cases.append({"id": f"canonical_{index}", "kind": "canonical",
                      "seed": None, "sample_index": None, "difficulty": None,
                      "overrides": {}, "input": pair["input"],
                      "canonical_output": pair["output"]})
    for index in range(4):
        cases.append({"id": f"generated_easy_44_{index}", "kind": "generated_default",
                      "seed": 44, "sample_index": index, "difficulty": "easy",
                      "overrides": {}, "profile": gen.schedule_profile(44, index, "easy"),
                      "input": gen.generate(44, index, difficulty="easy")})
    base = cases[4]["input"]
    adversary = copy.deepcopy(base)
    h, w = len(base), len(base[0])
    assert base[h-1][w-1] not in (0, 7)
    assert base[h-2][w-2] == 0
    adversary[h-2][w-2] = adversary[h-1][w-1]
    adversary[h-1][w-1] = 0
    cases.append({"id": "handbuilt_inward_outside_distractor", "kind": "handbuilt_mutation",
                  "seed": None, "sample_index": None, "difficulty": "easy", "overrides": {},
                  "based_on": {"seed": 44, "sample_index": 1, "difficulty": "easy", "overrides": {}},
                  "mutation": {"from": [h-1, w-1], "to": [h-2, w-2]}, "input": adversary})
    write("input.json", [case["input"] for case in cases])
    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", "../checks/audit/902d22dfd388/input.json",
            "--out", "../checks/audit/902d22dfd388/racket-confirm.json"]
    if not (HERE / "racket-confirm.json").exists():
        completed = subprocess.run(argv, cwd=PACKET, capture_output=True, text=True)
        write("command.json", {"argv": argv, "cwd": str(PACKET),
                               "exit_code": completed.returncode,
                               "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode:
            raise RuntimeError(completed.stderr)
    raw = json.loads((HERE / "racket-confirm.json").read_text())
    # Public apply emits indexed output records plus authority provenance.
    outputs = [result["output"] for result in raw["results"]]
    assert all(result["error"] is None for result in raw["results"])
    assert raw["executed_rule_hash"] == gen.RULE_HASH
    assert raw["rule_hash_matches_catalog"]
    assert len(outputs) == len(cases)
    for case, output in zip(cases, outputs):
        grid = case["input"]
        case.update({"self_check": gen.self_check(grid, difficulty=case["difficulty"]),
                     "strict_canonical_like": gen.strict_canonical_like(grid),
                     "observables": gen.semantic_observables(grid),
                     "racket_output": output, "rival_output": rival(grid),
                     "rival_matches_racket": rival(grid) == output,
                     "mirror_matches_racket": gen.rule_mirror(grid) == output})
        assert case["self_check"] == []
        assert case["strict_canonical_like"] == []
        assert case["mirror_matches_racket"]
        if "canonical_output" in case:
            assert output == case["canonical_output"]
    assert all(case["rival_matches_racket"] for case in cases[:-1])
    assert not cases[-1]["rival_matches_racket"]
    rule = row["program_solution"]
    write("evidence.json", {"task_id": TASK,
          "finding": "canvas-perimeter filtering replaces frame isolation throughout generated distribution",
          "generator_sha256": hashlib.sha256(GENPATH.read_bytes()).hexdigest(),
          "canonical_rule_sha256_exact": hashlib.sha256(rule.encode()).hexdigest(),
          "canonical_rule_sha256_whitespace_normalized": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
          "canonical_rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
          "executed_rule_hash": raw["executed_rule_hash"],
          "executed_rule_text_sha256": raw["rule_text_sha256"],
          "canonical_row_sha256_exact_line": hashlib.sha256(line.encode()).hexdigest(),
          "cases": cases, "reference_command": "command.json"})
    print(json.dumps({"canonical_rival_fit": "3/3", "default_profile_rival_fit": "4/4",
                      "handbuilt_domain_accepted": True, "handbuilt_rival_fit": False,
                      "all_python_mirrors_match_actual_racket": True}))


if __name__ == "__main__":
    main()
