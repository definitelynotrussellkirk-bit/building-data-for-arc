"""Findings-only onion-depth audit; run from the public packet wrapper."""
from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "ff4dfc92ad29"
OUT = Path(__file__).resolve().parent
gen, source, digest = load_selected_generator(TASK, root=find_root(__file__))


def components(grid):
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value not in (0, 9)}
    result = []
    while todo:
        start = min(todo)
        todo.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for other in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if other in todo:
                    todo.remove(other)
                    cells.add(other)
                    stack.append(other)
        colors = {}
        for r, c in cells:
            colors[grid[r][c]] = colors.get(grid[r][c], 0) + 1
        color = min(colors, key=lambda x: (-colors[x], x))
        result.append((color, cells))
    return result


def depth(cells):
    remaining, layers = set(cells), 0
    while remaining:
        boundary = {(r, c) for r, c in remaining if any(
            neighbor not in remaining for neighbor in
            ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))}
        remaining -= boundary
        layers += 1
    return layers


def bbox_rival(grid):
    rows = []
    for color, cells in components(grid):
        h = max(r for r, _ in cells) - min(r for r, _ in cells) + 1
        w = max(c for _, c in cells) - min(c for _, c in cells) + 1
        rows.append((min(h, w), color))
    return [[color for _, color in sorted(rows)]]


def onion_output(grid):
    return [[color for _, color in sorted((depth(cells), color)
                                          for color, cells in components(grid))]]


def prepare():
    grids, rows = [], []
    for band in (None, "easy", "medium", "hard"):
        for index in range(6):
            seed = 991 + index
            grid = gen.generate(seed, index, difficulty=band)
            grids.append(grid)
            rows.append({"kind": "ordinary_generated", "seed": seed,
                         "sample_index": index, "difficulty": band,
                         "overrides": {}, "validator_errors": gen.self_check(grid),
                         "bbox_rival": bbox_rival(grid), "onion_python": onion_output(grid)})
    for seed in range(6):
        overrides = {"grid_h": 9, "grid_w": 14}
        grid = gen.generate(seed, 0, difficulty="easy", **overrides)
        grids.append(grid)
        rows.append({"kind": "exact_override_probe", "seed": seed, "sample_index": 0,
                     "difficulty": "easy", "overrides": overrides,
                     "observed_shape": [len(grid), len(grid[0])],
                     "validator_errors": gen.self_check(grid),
                     "bbox_rival": bbox_rival(grid), "onion_python": onion_output(grid)})
    # This connected ring is legal for the selected rule but intentionally
    # outside the generator's rectangle-only validator and emission support.
    grid = [[0] * 21 for _ in range(9)]
    for r in range(1, 8):
        for c in range(1, 8):
            if r in (1, 7) or c in (1, 7):
                grid[r][c] = 7
    for r in range(1, 4):
        for c in range(10, 13):
            grid[r][c] = 2
    for r in range(1, 6):
        for c in range(15, 20):
            grid[r][c] = 4
    grids.append(grid)
    rows.append({"kind": "rule_domain_nonrectangle_counterfactual",
                 "validator_errors": gen.self_check(grid),
                 "bbox_rival": bbox_rival(grid), "onion_python": onion_output(grid),
                 "generated_support": False})
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    canonical = [{"input": pair["input"], "output": pair["output"],
                  "bbox_matches": bbox_rival(pair["input"]) == pair["output"]}
                 for pair in pairs]
    result = {"task_id": TASK, "generator_sha256": digest,
              "source_path": str(source), "rows": rows, "canonical": canonical}
    (OUT / "inputs.json").write_text(json.dumps(grids) + "\n")
    (OUT / "pre_apply.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"inputs": len(grids), "canonical_labeled_slots": len(pairs)}))


def confirm():
    before = json.loads((OUT / "pre_apply.json").read_text())
    actual = json.loads((OUT / "racket.json").read_text())
    assert actual["generator_sha256"] == digest == before["generator_sha256"]
    assert actual["rule_hash_matches_catalog"]
    assert len(actual["results"]) == len(before["rows"]) == 31
    for info, row in zip(before["rows"], actual["results"]):
        assert row["error"] is None and row["valid_output"]
        assert info["onion_python"] == row["output"]
        info["racket_output"] = row["output"]
        info["bbox_rival_matches_racket"] = info["bbox_rival"] == row["output"]
        info["input_sha256"] = row["input_sha256"]
    ordinary = [row for row in before["rows"] if row["kind"] == "ordinary_generated"]
    controls = [row for row in before["rows"] if row["kind"] == "exact_override_probe"]
    summary = {"task_id": TASK, "generator_sha256": digest,
               "rule_hash": actual["executed_rule_hash"],
               "ordinary_generated": len(ordinary),
               "ordinary_validator_accepted": sum(not row["validator_errors"] for row in ordinary),
               "ordinary_bbox_matches_racket": sum(row["bbox_rival_matches_racket"] for row in ordinary),
               "override_cases": len(controls),
               "requested_shape": [9, 14],
               "override_observed_shapes": [row["observed_shape"] for row in controls],
               "override_shape_mismatches": sum(row["observed_shape"] != [9, 14] for row in controls),
               "canonical_labeled_slots": len(before["canonical"]),
               "canonical_bbox_matches": sum(row["bbox_matches"] for row in before["canonical"]),
               "racket_outputs_verified": 31,
               "nonrectangle_counterfactual": before["rows"][-1],
               "domain_limit": "Nonrectangle witness is rule-domain only; generator validator rejects it."}
    (OUT / "confirmed.json").write_text(json.dumps(before, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["confirm"]:
        confirm()
    elif not sys.argv[1:]:
        prepare()
    else:
        raise SystemExit("Usage: probe.py [confirm]")
