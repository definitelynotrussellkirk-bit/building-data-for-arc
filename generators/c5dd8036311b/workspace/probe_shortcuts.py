"""Reproduce canonical-fit and generated counterexamples through public Racket apply.

Run through WORK/run_with_racket.py; --out must be a new directory.
The rival inventory is read from the selected generator, never copied here.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    root = find_root(__file__)
    task = "c5dd8036311b"
    gen, source, digest = load_selected_generator(task, root=root)
    shortcuts = gen.CANONICAL_SHORTCUTS
    competitors = gen.LESSON_COMPETITORS
    if not shortcuts or not competitors:
        raise RuntimeError("Missing declared rivals; empty coverage is not a pass")
    pairs = canonical_pairs(task, root=root, labeled_only=True)
    canonical_fit = {
        name: {"matched": sum(rival(deepcopy(p["input"])) == p["output"] for p in pairs),
               "total": len(pairs)}
        for name, rival in shortcuts.items()
    }
    # Select a GENERATED common witness, then verify it using the Racket labels.
    selected = None
    for index in range(24):
        grid = gen.generate(args.seed, index, difficulty="hard")
        prediction = gen.rule_mirror(grid)
        if all(rival(deepcopy(grid)) != prediction for rival in shortcuts.values()):
            selected = (index, grid)
            break
    if selected is None:
        raise RuntimeError("No common generated witness in the first24 requested draws")
    index, generated = selected
    small = [[0] * 8 for _ in range(9)]
    small[4] = [2, 8, 1, 2, 1, 8, 1, 2]
    large = [[0] * 30 for _ in range(30)]
    large[20] = [1] * 30
    for col, color in ((0, 2), (1, 8), (8, 2), (15, 8), (21, 2), (29, 2)):
        large[20][col] = color
    inputs = [generated, small, large]
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    input_path = output / "inputs.json"
    reference_path = output / "racket.json"
    input_path.write_text(json.dumps(inputs) + "\n")
    argv = [sys.executable, "-m", "arcpuzzles", "apply", task,
            "--input", str(input_path), "--out", str(reference_path)]
    completed = subprocess.run(argv, cwd=root, capture_output=True, text=True)
    (output / "apply.stdout.log").write_text(completed.stdout)
    (output / "apply.stderr.log").write_text(completed.stderr)
    if completed.returncode:
        raise RuntimeError(f"Public Racket apply failed: {completed.returncode}")
    reference = json.loads(reference_path.read_text())
    rows = []
    for kind, grid, actual in zip(("generated", "small_hand_witness", "large_hand_witness"),
                                 inputs, reference["results"], strict=True):
        if actual["error"] or not actual["valid_output"]:
            raise RuntimeError("Reference did not produce a valid output")
        rival_outputs = {name: rival(deepcopy(grid)) for name, rival in competitors.items()}
        rows.append({
            "kind": kind, "input": grid, "output": actual["output"],
            "self_check": gen.self_check(grid),
            "rivals": {name: {"output": pred, "disagrees": pred != actual["output"]}
                       for name, pred in rival_outputs.items()},
            "generation": {"seed": args.seed, "sample_index": index, "difficulty": "hard",
                           "overrides": {}} if kind == "generated" else None,
            "membership": "generated_default" if kind == "generated" else "accepted_task_domain_hand_constructed",
        })
    passed = (all(v["matched"] == v["total"] > 0 for v in canonical_fit.values())
              and all(not row["self_check"] and all(r["disagrees"] for r in row["rivals"].values())
                      for row in rows))
    report = {"task_id": task, "status": "passed" if passed else "failed",
              "generator_sha256": digest, "source_path": str(source),
              "rule_hash": reference["executed_rule_hash"],
              "rule_text_sha256": reference["rule_text_sha256"],
              "prototype": False, "training_admitted": False,
              "canonical_fit": canonical_fit, "witnesses": rows,
              "command": argv, "cwd": str(root), "exit_code": completed.returncode,
              "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              "limits": "Five declared rivals and three exact witnesses; no universal identifiability claim."}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "generator_sha256": digest,
                      "canonical_pairs": len(pairs), "shortcuts": len(shortcuts),
                      "racket_witnesses": len(rows), "out": str(output)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
