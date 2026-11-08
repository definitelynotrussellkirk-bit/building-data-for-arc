#!/usr/bin/env python3
"""Reproduce the 05cfa1aabb8a palette-only shortcut against Racket authority."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import types

TASK_ID = "05cfa1aabb8a"
REPO = Path.cwd().resolve()

# The authoring tree stores public staging tools under shared/tools, while
# rule_wrap imports them through the runtime package name ``scripts``.  Create
# the same package alias without changing the audited repository.
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, load_selected_generator

OUT = Path(__file__).with_name("report.json")


def canonical_row():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def panels(grid):
    h, w = len(grid), len(grid[0])
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    bounds = [-1, *dividers, w]
    return [
        [row[bounds[i] + 1 : bounds[i + 1]] for row in grid]
        for i in range(len(bounds) - 1)
        if bounds[i] + 1 < bounds[i + 1]
    ]


def palette_only_rival(grid):
    split = panels(grid)
    if len(split) < 2:
        raise ValueError("need template and board panels")
    template, board = split[0], split[1]
    colors = {v for row in template for v in row if v not in (0, 9)}
    return [[8 if v in colors else 0 for v in row] for row in board]


def apply_rule(bridge, wrapped, grid):
    bridge.define_grid("g", grid)
    out = bridge.eval_text(f"({wrapped} g)")
    return [[int(v) for v in row] for row in out]


def digest(obj):
    return hashlib.sha256(json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def main():
    module, source, source_sha = load_selected_generator(TASK_ID, root=REPO)
    row = canonical_row()
    rule = row["program_solution"]
    wrapped = wrap_rule(rule)
    labeled = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    canonical_results = []
    for pair in labeled:
        rival = palette_only_rival(pair["input"])
        canonical_results.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "fits": rival == pair["output"],
            "input_sha256": digest(pair["input"]),
        })

    generated_results = []
    witness = None
    with RacketBridge(max_calls_before_restart=48) as bridge:
        for band in ("easy", "medium", "hard"):
            for index in range(20):
                grid = module.generate(700 + index, index, difficulty=band)
                intended = apply_rule(bridge, wrapped, grid)
                rival = palette_only_rival(grid)
                generated_results.append({
                    "band": band,
                    "sample_index": index,
                    "fits": rival == intended,
                    "input_sha256": digest(grid),
                })

        # Find one validator-accepted intervention: add a template-colored board
        # cell that does not complete a legal transformed template match.
        for seed in range(1, 40):
            base = module.generate(seed, 0, difficulty="medium", texture="plain")
            split = panels(base)
            template, board = split[0], split[1]
            template_colors = sorted({v for row in template for v in row if v not in (0, 9)})
            first_divider = next(c for c in range(len(base[0])) if all(base[r][c] == 9 for r in range(len(base))))
            for br, row_values in enumerate(board):
                for bc, value in enumerate(row_values):
                    if value != 0:
                        continue
                    for color in template_colors:
                        changed = deepcopy(base)
                        global_c = first_divider + 1 + bc
                        changed[br][global_c] = color
                        errors = module.self_check(changed)
                        if errors:
                            continue
                        intended = apply_rule(bridge, wrapped, changed)
                        rival = palette_only_rival(changed)
                        if rival != intended and rival[br][bc] == 8 and intended[br][bc] == 0:
                            witness = {
                                "seed": seed,
                                "difficulty": "medium",
                                "texture": "plain",
                                "added_global_cell": [br, global_c],
                                "added_board_cell": [br, bc],
                                "added_color": color,
                                "self_check": errors,
                                "input": changed,
                                "racket_output": intended,
                                "palette_only_output": rival,
                                "input_sha256": digest(changed),
                                "racket_output_sha256": digest(intended),
                                "rival_output_sha256": digest(rival),
                            }
                            break
                    if witness:
                        break
                if witness:
                    break
            if witness:
                break

    report = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(REPO)),
        "generator_sha256": source_sha,
        "rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "rival": "mark every board cell whose color occurs in the template panel",
        "canonical": {
            "count": len(canonical_results),
            "fit_count": sum(r["fits"] for r in canonical_results),
            "rows": canonical_results,
        },
        "generated": {
            "count": len(generated_results),
            "fit_count": sum(r["fits"] for r in generated_results),
            "rows": generated_results,
        },
        "counterexample": witness,
        "reproduced": (
            bool(witness)
            and all(r["fits"] for r in canonical_results)
            and all(r["fits"] for r in generated_results)
        ),
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": report["rule_hash"],
        "canonical_fit": f"{report['canonical']['fit_count']}/{report['canonical']['count']}",
        "generated_fit": f"{report['generated']['fit_count']}/{report['generated']['count']}",
        "counterexample_found": witness is not None,
        "reproduced": report["reproduced"],
        "out": str(OUT),
    }, indent=2))
    raise SystemExit(0 if report["reproduced"] else 1)


if __name__ == "__main__":
    main()
