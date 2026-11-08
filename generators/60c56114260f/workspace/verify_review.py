"""Bounded review replay; run through review.py run with --out REPORT.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
from arc_repl.builtins import Grid, _unwrap
from arc_repl.executor import ArcExecutor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    task_id = "60c56114260f"
    module, source, source_hash = load_selected_generator(task_id, root=root)
    pairs = canonical_pairs(task_id, root=root)
    row = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if json.loads(line).get("task_id") == task_id)
    rule = row["program_solution"]
    cases = [{"name": f"canonical/{p['split']}/{p['pair_index']}",
              "input": p["input"], "expected": p["output"]} for p in pairs]
    for index, profile in enumerate(module.GENERAL_PROFILES):
        grid = module.generate(17, index, difficulty="medium", scene_profile=profile)
        cases.append({"name": f"generated/{profile}/s17/i{index}",
                      "input": grid, "expected": module.rule_mirror(grid)})
    with ArcExecutor({"train": [], "test": []}, use_racket=True) as executor:
        rule_result = executor.step(rule)
        assert not rule_result.startswith("ERROR"), rule_result
        runtime = executor.runtime_identity
        assert runtime["backend"] == "racket", runtime
        for case in cases:
            case["actual"] = _unwrap(executor._apply_rule(Grid(case["input"])))
            case["passed"] = case["actual"] == case["expected"]
            assert case["passed"], case

    # Exercise the two repaired bindings (selected source and canonical/base data)
    # from an unrelated working directory. The official task_tests stage separately
    # exercises a copied runtime with no source-tree import dependency.
    test_file = root / "generators" / task_id / "tests/test_generator_60c56114260f.py"
    argv = [sys.executable, "-m", "pytest", str(test_file), "-q", "-k",
            "canonical or public_profiles or source_sync"]
    with tempfile.TemporaryDirectory(prefix="60c5-unrelated-cwd-") as alternate:
        decoy = Path(alternate)
        (decoy / "data/canonical").mkdir(parents=True)
        (decoy / "data/canonical/puzzles.jsonl").write_text("invalid decoy ledger\n")
        (decoy / "generators" / task_id).mkdir(parents=True)
        (decoy / "generators" / task_id / "generator.py").write_text(
            "raise RuntimeError('decoy generator must not load')\n")
        env = os.environ.copy()
        env["ARCPUZZLES_HOME"] = alternate
        result = subprocess.run(argv, cwd=alternate, env=env,
                                capture_output=True, text=True, timeout=60)
        portability = {"argv": argv, "cwd_kind": "unrelated temporary directory",
                       "adversarial_surfaces": ["invalid cwd canonical ledger", "decoy ARCPUZZLES_HOME generator"],
                       "returncode": result.returncode, "stdout": result.stdout,
                       "stderr": result.stderr}
    assert result.returncode == 0, portability
    report = {"schema": "60c56114260f-focused-review-v1", "passed": True,
              "generator_source": source.relative_to(root).as_posix(),
              "generator_sha256": source_hash,
              "test_sha256": hashlib.sha256(test_file.read_bytes()).hexdigest(),
              "canonical_rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
              "runtime": runtime, "cases": cases, "portability": portability,
              "limits": ["Five canonical pairs and one generated sample per general profile; not exhaustive.",
                         "Generator and canonical Racket rule remain unchanged."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "racket_cases": len(cases),
                      "alternate_cwd_exit": result.returncode, "out": str(args.out)}))


if __name__ == "__main__":
    main()
