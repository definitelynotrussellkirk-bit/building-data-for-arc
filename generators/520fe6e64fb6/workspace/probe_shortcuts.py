"""Reproduce declared canonical shortcuts and a generated Racket counterexample.

Run through review.py run. This is an authoring probe, never a solve helper.
The supported `arcpuzzles apply` command supplies every authoritative label.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "520fe6e64fb6"


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def differences(expected, actual):
    if len(expected) != len(actual) or any(len(a) != len(b) for a, b in zip(expected, actual)):
        return {"shape_mismatch": True}
    return [{"row": r, "column": c, "racket": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row)
            if value != actual[r][c]]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="easy")
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    recipe = {"seed": args.seed, "sample_index": args.sample_index,
              "difficulty": args.difficulty, "overrides": {}}
    grid = gen.generate(args.seed, args.sample_index, difficulty=args.difficulty)
    domain_errors = gen.self_check(grid, difficulty=args.difficulty)
    if domain_errors:
        raise ValueError(f"generated witness outside declared domain: {domain_errors}")
    args.out.mkdir(parents=True, exist_ok=False)
    target = args.out.resolve()
    inputs = [pair["input"] for pair in pairs] + [grid]
    write_json(target / "input.json", {"inputs": inputs})
    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
               "--input", str(target / "input.json"), "--check-generator-domain",
               "--out", str(target / "racket.json")]
    execution = subprocess.run(command, cwd=root, text=True, capture_output=True)
    (target / "apply.stdout.log").write_text(execution.stdout)
    (target / "apply.stderr.log").write_text(execution.stderr)
    write_json(target / "execution.json", {"argv": command, "cwd": str(root),
               "exit_code": execution.returncode, "probe_argv": sys.argv,
               "probe_cwd": str(Path.cwd())})
    if execution.returncode:
        raise RuntimeError(f"Racket application failed; see {target / 'apply.stderr.log'}")
    applied = json.loads((target / "racket.json").read_text())
    if applied["generator_sha256"] != source_hash or applied["executed_rule_hash"] != gen.RULE_HASH:
        raise ValueError("source identity changed during probe")
    results = applied["results"]
    if len(results) != len(inputs) or any(result["error"] for result in results):
        raise ValueError("incomplete Racket output")
    if any(result["input"] != grid for result, grid in zip(results, inputs)):
        raise ValueError("Racket input order or content changed")
    canonical_mismatches = [i for i, (pair, result) in enumerate(zip(pairs, results))
                            if pair["output"] != result["output"]]
    if canonical_mismatches:
        raise ValueError(f"canonical labels differ from Racket: {canonical_mismatches}")
    canonical = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        mismatches = [i for i, result in enumerate(results[:-1])
                      if rival(copy.deepcopy(result["input"])) != result["output"]]
        canonical[name] = {"checked": len(pairs), "mismatches": mismatches}
    if not canonical or any(value["mismatches"] for value in canonical.values()):
        raise ValueError("declared canonical shortcuts did not fit every labeled occurrence")
    expected = results[-1]["output"]
    rivals = {}
    for name, rival in gen.LESSON_COMPETITORS.items():
        output = rival(copy.deepcopy(grid))
        rivals[name] = {"output": output, "differences": differences(expected, output),
                        "fits_canonical": name in canonical}
    if not rivals or any(not record["differences"] for record in rivals.values()):
        raise ValueError("selected sample did not refute every declared lesson rival")
    witness = {
        "schema": "arcpuzzles-task-shortcut-counterexample-v1", "task_id": TASK,
        "generator_sha256": source_hash, "rule_hash": applied["executed_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"], "recipe": recipe,
        "observed_profile": gen.observe_overrides(grid), "self_check": domain_errors,
        "input": grid, "racket_output": expected, "rivals": rivals,
        "canonical_shortcuts": canonical, "canonical_occurrences": len(pairs),
        "unique_canonical_inputs": len({json.dumps(pair["input"]) for pair in pairs}),
        "authority_evidence": str((target / "racket.json").relative_to(root.parent))
            if target.is_relative_to(root.parent) else str(target / "racket.json"),
        "scope": "One actual default-stream sample; finite declared rivals, not a universal proof.",
    }
    write_json(target / "counterexample.json", witness)
    summary = {"status": "passed", "generator_sha256": source_hash,
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "canonical_occurrences": len(pairs), "shortcuts_checked": len(canonical),
               "witness_rivals_refuted": len(rivals), "racket_inputs": len(inputs),
               "recipe": recipe, "source_path": str(source)}
    write_json(target / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
