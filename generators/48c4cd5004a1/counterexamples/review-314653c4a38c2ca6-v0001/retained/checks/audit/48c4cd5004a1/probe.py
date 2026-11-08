#!/usr/bin/env python3
"""Read-only, source-bound audit of 48c4cd5004a1; no selected-source edits."""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "48c4cd5004a1"
EXPECTED_SHA = "1e5ce5de6a78eeac2e88074188db482a0671f2de4433e96d67bd60c29130343f"
OUT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def scan(grid, *, remove_checkers=True):
    h, w = len(grid), len(grid[0])
    bg = Counter(value for row in grid for value in row).most_common(1)[0][0]
    icons, checkers = [], []
    for r in range(h - 2):
        for c in range(w - 2):
            border = [grid[r + dr][c + dc] for dr in range(3) for dc in range(3) if (dr, dc) != (1, 1)]
            center = grid[r + 1][c + 1]
            if len(set(border)) == 1 and border[0] != bg and center not in (bg, border[0]):
                icons.append((r, c, border[0], center))
            a, b = grid[r][c], grid[r][c + 1]
            if a != b and a != bg and b != bg and all(grid[r + dr][c + dc] == (a if (dr + dc) % 2 == 0 else b) for dr in range(3) for dc in range(3)):
                checkers.append((r, c))
    blocks = icons + checkers if remove_checkers else icons
    special = {(r + dr, c + dc) for r, c, *_ in blocks for dr in range(3) for dc in range(3)}
    dots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != bg and (r, c) not in special]
    counts = Counter(grid[r][c] for r, c in dots)
    majority = counts.most_common(1)[0][0] if counts else None
    touches = []
    for r, c, *_ in icons:
        perimeter = {(r + dr + ar, c + dc + ac) for dr in range(3) for dc in range(3)
                     for ar, ac in ((-1, 0), (1, 0), (0, -1), (0, 1))}
        touches.append(sorted({grid[rr][cc] for rr, cc in perimeter if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in special and grid[rr][cc] != bg}))
    selected = next((i for i, colors in enumerate(touches) if majority in colors), None)
    any_touch = next((i for i, colors in enumerate(touches) if colors), None)
    def signature(index):
        if index is None:
            return None
        b, center = icons[index][2:]
        return [[b, b, b], [b, center, b], [b, b, b]]
    return {"background": bg, "icons": icons, "checkerboards": checkers,
            "dot_counts": dict(counts), "majority_color": majority,
            "unique_majority": bool(counts) and list(counts.values()).count(max(counts.values())) == 1,
            "touching_colors": touches, "selected_icon": selected,
            "touched_icon_count": sum(bool(colors) for colors in touches),
            "output": signature(selected), "first_touched_output": signature(any_touch)}


def add_competing_touch(grid):
    original = scan(grid)
    selected = original["selected_icon"]
    if selected is None:
        return None
    count = original["dot_counts"][original["majority_color"]]
    candidates = [c for c in range(1, 10) if c != original["majority_color"] and c != original["background"]
                  and original["dot_counts"].get(c, 0) + 1 < count]
    if not candidates:
        return None
    color = min(candidates, key=lambda c: (original["dot_counts"].get(c, 0), c))
    for r, c, border, center in original["icons"][:selected]:
        if (border, center) == original["icons"][selected][2:]:
            continue
        neighbors = [(r - 1, c + d) for d in range(3)] + [(r + 3, c + d) for d in range(3)]
        neighbors += [(r + d, c - 1) for d in range(3)] + [(r + d, c + 3) for d in range(3)]
        for rr, cc in neighbors:
            if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])) or grid[rr][cc] != original["background"]:
                continue
            changed = copy.deepcopy(grid)
            changed[rr][cc] = color
            facts = scan(changed)
            if facts["icons"] == original["icons"] and facts["unique_majority"] and facts["output"] == original["output"] and facts["first_touched_output"] != facts["output"]:
                return {"input": changed, "edit": {"row": rr, "column": cc, "before": original["background"], "after": color}, "facts": facts}
    return None


def add_checkerboard(grid):
    original = scan(grid)
    minority = next((color for colors in original["touching_colors"][:original["selected_icon"]] for color in colors if color != original["majority_color"]), None)
    if minority is None:
        return None
    other = next(color for color in range(1, 10) if color not in (minority, original["majority_color"], original["background"]))
    for r in range(len(grid) - 2):
        for c in range(len(grid[0]) - 2):
            if any(grid[r + dr][c + dc] != original["background"] for dr in range(3) for dc in range(3)):
                continue
            changed = copy.deepcopy(grid)
            for dr in range(3):
                for dc in range(3):
                    changed[r + dr][c + dc] = minority if (dr + dc) % 2 == 0 else other
            facts, rival = scan(changed), scan(changed, remove_checkers=False)
            if facts["icons"] == original["icons"] and len(facts["checkerboards"]) == len(original["checkerboards"]) + 1 and facts["unique_majority"] and facts["output"] == original["output"] and rival["output"] is not None and rival["output"] != facts["output"]:
                return {"input": changed, "edit": {"top": r, "left": c, "colors": [minority, other]}, "facts": facts, "count_checker_cells_rival": rival["output"]}
    return None


def main():
    root = find_root(__file__)
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    assert source_hash == EXPECTED_SHA, "selected source drifted"
    record = next(json.loads(line) for line in canonical_path(root).read_text().splitlines() if json.loads(line).get("task_id") == TASK)
    report = {"task_id": TASK, "source_sha256": source_hash, "rule_hash": gen.RULE_HASH,
              "rule_sha256": hashlib.sha256(record["program_solution"].encode()).hexdigest(),
              "declared_rivals": sorted(getattr(gen, "CANONICAL_SHORTCUTS", {})),
              "auditor_rivals": ["first_touched_icon_ignoring_vote_counts", "count_checkerboard_cells_as_dots"],
              "sample_plan": {"bands": ["easy", "medium", "hard"], "seeds": [0, 1, 2, 3], "indices": [0, 1, 2, 3]},
              "generated": [], "canonical": [], "override_checks": [], "witnesses": []}
    inputs, identities, first_counterfactual = [], [], None
    for band in report["sample_plan"]["bands"]:
        for seed in report["sample_plan"]["seeds"]:
            for index in report["sample_plan"]["indices"]:
                grid = gen.generate(seed, index, difficulty=band)
                facts = scan(grid)
                identity = {"kind": "generated", "difficulty": band, "seed": seed, "sample_index": index, "overrides": {}}
                report["generated"].append({**identity, "input_sha256": digest(grid), "self_check": gen.self_check(grid), "facts": facts})
                inputs.append(grid)
                identities.append(identity)
                if first_counterfactual is None:
                    witness = add_competing_touch(grid)
                    if witness:
                        first_counterfactual = {**witness, "base": identity, "base_input_sha256": digest(grid)}
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        facts, rival = scan(pair["input"]), scan(pair["input"], remove_checkers=False)
        identity = {"kind": "canonical", "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"]}
        report["canonical"].append({**identity, "input_sha256": digest(pair["input"]), "expected_output": pair["output"], "facts": facts,
                                     "count_checker_cells_rival": rival["output"]})
        inputs.append(pair["input"])
        identities.append(identity)
    assert first_counterfactual is not None
    first_counterfactual.update({"name": "minority_dot_touches_other_icon", "self_check": gen.self_check(first_counterfactual["input"])})
    report["witnesses"].append(first_counterfactual)
    second = add_checkerboard(first_counterfactual["input"])
    assert second is not None
    second.update({"name": "checkerboard_cells_must_be_excluded_from_vote", "base": first_counterfactual["base"],
                   "base_input_sha256": digest(first_counterfactual["input"]), "self_check": gen.self_check(second["input"])})
    report["witnesses"].append(second)
    for witness in report["witnesses"]:
        inputs.append(witness["input"])
        identities.append({"kind": "counterfactual", "name": witness["name"]})
    baseline = gen.generate(0, 0, difficulty="medium")
    for overrides in ({"palette_size": 4}, {"n_distinct_colors": 4}, {"palette_kind": "warm"}, {"texture": "warm"}, {"typo_axis": 123}):
        actual = gen.generate(0, 0, difficulty="medium", **overrides)
        report["override_checks"].append({"seed": 0, "sample_index": 0, "difficulty": "medium", "overrides": overrides,
                                          "input_sha256": digest(actual), "equals_unmodified_draw": actual == baseline,
                                          "foreground_colors": sorted({value for row in actual for value in row if value != 0})})
    report["validator_impostor"] = {"input": [[1, 2, 3]], "self_check": gen.self_check([[1, 2, 3]])}
    report["counts"] = {"generated": len(report["generated"]), "generated_self_check_pass": sum(not row["self_check"] for row in report["generated"]),
                        "generated_one_touched_icon": sum(row["facts"]["touched_icon_count"] == 1 for row in report["generated"]),
                        "generated_checkerboards": sum(len(row["facts"]["checkerboards"]) for row in report["generated"]),
                        "first_touched_fits_generated_python_reference": sum(row["facts"]["first_touched_output"] == row["facts"]["output"] for row in report["generated"]),
                        "first_touched_fits_canonical": sum(row["facts"]["first_touched_output"] == row["expected_output"] for row in report["canonical"]),
                        "count_checker_cells_fits_canonical": sum(row["count_checker_cells_rival"] == row["expected_output"] for row in report["canonical"])}
    for filename, value in (("probe.json", report), ("apply-inputs.json", inputs), ("apply-identities.json", identities)):
        (OUT / filename).write_text(json.dumps(value, separators=(",", ":")) + "\n")
    print(json.dumps({"source_sha256": source_hash, "counts": report["counts"], "apply_input_count": len(inputs)}, sort_keys=True))


if __name__ == "__main__":
    main()
