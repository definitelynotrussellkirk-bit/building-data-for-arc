"""Reproduce a lesson ambiguity using the production runner and exact Racket.

The rival selects exact X components of the unique most frequent foreground
color. A tied foreground color count yields no selected color and no changes.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def rival(grid):
    output = [row[:] for row in grid]
    counts = Counter(color for row in grid for color in row if color)
    leaders = [color for color, count in counts.items() if count == max(counts.values())]
    if len(leaders) != 1:
        return output
    color = leaders[0]
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = {start}
        pending = [start]
        while pending:
            r, c = pending.pop()
            adjacent = {(r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)} & remaining
            cells.update(adjacent)
            remaining.difference_update(adjacent)
            pending.extend(adjacent)
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        if {(r-top, c-left) for r, c in cells} == {(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)}:
            for r, c in cells:
                output[r][c] = 2
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "shared/runtime"))
    from puzzle_generators import runner
    from reviewer_support import canonical_path

    spec = importlib.util.spec_from_file_location("reviewed_selector", args.generator)
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    with canonical_path(root).open() as handle:
        selected = next(json.loads(line) for line in handle if '"task_id": "70f97d6b605b"' in line)
    program = selected["program_solution"]
    # Preserve the selected authority's exact body. The repository does not
    # expose the staged scripts.comment_solutions package used by wrap_rule.
    assert program.startswith("(rule! ") and program.endswith(")")
    callable_text = "(lambda (g) " + program[len("(rule! "):-1] + ")"
    bundle = runner.GeneratorBundle(
        task_id="70f97d6b605b", rule_task_id="70f97d6b605b", rule_source=program,
        rule_callable_text=callable_text,
        rule_file="shared/data/canonical/puzzles.jsonl", generator_module=generator)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        instance = runner.run_one("70f97d6b605b", seed=1, sample_index=0,
                                  n_train=4, n_test=1, difficulty="easy",
                                  bundle=bundle, bridge=bridge, fn_name=fn_name)
        identity = bridge.runtime_identity
    finally:
        bridge.shutdown()
    pairs = instance["train"] + instance["test"]
    matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
    query = instance["test"][0]
    predicted = rival(query["input"])
    different = [[r, c, query["output"][r][c], predicted[r][c]]
                 for r, row in enumerate(query["input"]) for c in range(len(row))
                 if query["output"][r][c] != predicted[r][c]]
    report = {
        "schema": "x-selector-unique-dominant-counterexample-v1",
        "rival": "Recolor exact X components of the unique most frequent foreground color; do nothing on a tie.",
        "generator_sha256": hashlib.sha256(args.generator.read_bytes()).hexdigest(),
        "generator_snapshot": str(args.generator),
        "program_solution_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_identity": identity, "instance": instance,
        "rival_matches": matches, "query_rival_output": predicted,
        "different_query_cells": different,
        "observed_controls": [generator.observe_overrides(pair["input"]) for pair in pairs],
        "self_check_reasons": [generator.self_check(pair["input"]) for pair in pairs],
        "ambiguity_reproduced": all(matches[:-1]) and not matches[-1],
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"ambiguity_reproduced": report["ambiguity_reproduced"],
                      "rival_matches": matches, "different_query_cells": len(different),
                      "accepted_indices": [row["sample_index"] for row in instance["sampling"]["accepted_pairs"]],
                      "rejections": instance["sampling"]["rejections"]}))
    return 0 if report["ambiguity_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
