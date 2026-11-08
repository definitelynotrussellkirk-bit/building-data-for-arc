#!/usr/bin/env python3
"""Enumerate bounded gray-completion patches of original candidate windows."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

from reviewer_support import load_selected_generator
from mutation_probe import scan, summary, dump, ROOT, TASK, key


def reds_components(grid):
    reds = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    remaining = set(reds)
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, todo = {first}, [first]
        while todo:
            r, c = todo.pop()
            connected = {p for p in remaining if abs(p[0]-r) <= 2 and abs(p[1]-c) <= 2}
            remaining.difference_update(connected)
            group.update(connected)
            todo.extend(connected)
        groups.append(group)
    return groups


def main():
    gen, source, digest = load_selected_generator(TASK, root=ROOT)
    reports = []
    counts = Counter()
    for (profile_index, transform), template in gen._TEMPLATES.items():
        base = [list(row) for row in template["grid"]]
        original_cs, original_sel, original_out = scan(base)
        reds = set(gen._red_key(base))
        patches = []
        eligible_full_cover_windows = []
        groups = reds_components(base)
        for group in groups:
            possible = []
            for top in range(17):
                for left in range(17):
                    cells = {(r, c) for r in range(top, top+3) for c in range(left, left+3)}
                    if group <= cells and base[top+1][left+1] != 2:
                        possible.append([top, left])
            eligible_full_cover_windows.append({"reds": sorted(map(list, group)), "windows": possible})
        for top in range(17):
            for left in range(17):
                cells = {(r, c) for r in range(top, top+3) for c in range(left, left+3)}
                if base[top+1][left+1] == 2 or not cells.intersection(reds):
                    continue
                fill = sorted(p for p in cells if base[p[0]][p[1]] == 0)
                if not 1 <= len(fill) <= 3:
                    continue
                blockers = [None]
                for old in original_sel:
                    if set(old[3]).intersection(cells):
                        blockers.extend(p for p in old[2] if p not in cells and base[p[0]][p[1]] == 5)
                for blocker in blockers:
                    counts["patches_tried"] += 1
                    changed = deepcopy(base)
                    for r, c in fill:
                        changed[r][c] = 5
                    if blocker is not None:
                        changed[blocker[0]][blocker[1]] = 0
                    cs, selected, actual = scan(changed)
                    if len(selected) != 4 or {p for x in selected for p in x[3]} != reds:
                        continue
                    if [[x[0], x[1]] for x in selected] == [[x[0],x[1]] for x in original_sel]:
                        continue
                    assert actual == gen.rule_mirror(changed)
                    changes = [[r,c,base[r][c],changed[r][c]] for r in range(19) for c in range(19) if base[r][c] != changed[r][c]]
                    entry = {"target": [top,left], "changes": changes, "candidate_count":len(cs), "selected": [[x[0],x[1],len(x[3])] for x in selected], "gray_delta":len(fill)-(blocker is not None), "input":changed, "independent_output": actual, "within_original_candidate_count": 4 <= len(cs) <= 7, "rival_disagreements": {mode: scan(changed, mode)[2] != actual for mode in ("reading_order", "reverse_tie", "cell_overlap", "independent_windows")}}
                    patches.append(entry)
        patches.sort(key=lambda x: (not x["within_original_candidate_count"], len(x["changes"]), x["target"], x["changes"]))
        unique = {tuple(map(tuple,p["changes"])):p for p in patches}
        row = {"profile":template["profile"], "profile_index":profile_index, "transform": transform, "red_groups":eligible_full_cover_windows, "red_group_count":len(groups), "feasible_whole_group_windows":[len(x["windows"]) for x in eligible_full_cover_windows], "patch_count":len(unique), "minimal_patch":patches[0] if patches else None}
        reports.append(row)
        print(json.dumps({k: row[k] for k in ("profile", "transform", "patch_count", "feasible_whole_group_windows")} | {"minimal_changes": row["minimal_patch"]["changes"] if row["minimal_patch"] else None}), flush=True)
    result={"generator_source":str(source), "generator_sha256":digest, "rule_hash":gen.RULE_HASH, "counts":dict(counts), "scope":"Every candidate-relevant 3x3 with1..3zero holes completed to5, optionally one old selected gray cell outside the desired window blocked to0; preserves4selected and everyred covered; candidate count and density effects separately reported.", "templates":reports}
    dump("structural-patch-census.json",result)


if __name__ == "__main__":
    main()
