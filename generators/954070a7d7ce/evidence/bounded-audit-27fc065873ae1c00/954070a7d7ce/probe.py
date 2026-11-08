"""Bounded, read-only audit of frame-local cross generation and labels.

Run from the packet root through review.py run, using the same interpreter for
the wrapper and payload. Outputs stay beside this script, never in the target.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "954070a7d7ce"
ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
GEN, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)


def independent_output(grid):
    """Find complete 9-border components and draw only their local crosses."""
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    output = copy.deepcopy(grid)
    count = 0
    colors = set()
    while remaining:
        stack = [remaining.pop()]
        component = set(stack)
        while stack:
            r, c = stack.pop()
            for nxt in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        lo_r, hi_r = min(r for r, _ in component), max(r for r, _ in component)
        lo_c, hi_c = min(c for _, c in component), max(c for _, c in component)
        expected = {(r, c) for r in range(lo_r, hi_r+1) for c in range(lo_c, hi_c+1)
                    if r in (lo_r, hi_r) or c in (lo_c, hi_c)}
        assert component == expected
        marks = [(r, c, grid[r][c]) for r in range(lo_r+1, hi_r) for c in range(lo_c+1, hi_c)
                 if grid[r][c] != 0]
        assert len(marks) == 2 and marks[0][2] == marks[1][2]
        top = [mark for mark in marks if mark[0] == lo_r+1 and mark[1] > lo_c+1]
        left = [mark for mark in marks if mark[1] == lo_c+1 and mark[0] > lo_r+1]
        assert len(top) == len(left) == 1
        color = top[0][2]
        colors.add(color)
        for r in range(lo_r+1, hi_r):
            output[r][top[0][1]] = color
        for c in range(lo_c+1, hi_c):
            output[left[0][0]][c] = color
        count += 1
    assert count in (1, 2)
    return output, {"grid_h": height, "grid_w": width, "n_frames": count,
                    "n_distinct_colors": len(colors)}


def main():
    count = 0
    boundaries = []
    for band, height, width, (frames, colors) in itertools.product(
        (None, "easy", "medium", "hard"), range(9,15), range(11,21), ((1,1),(2,1),(2,2))
    ):
        overrides = dict(grid_h=height, grid_w=width, n_frames=frames, n_distinct_colors=colors)
        grid = GEN.generate(71, 11, difficulty=band, **overrides)
        original = copy.deepcopy(grid)
        output, observed = independent_output(grid)
        assert observed == overrides
        assert GEN.observe_overrides(grid) == observed
        assert not GEN.self_check(grid, difficulty=band)
        assert grid == original and output != grid
        assert GEN.generate(71,11,difficulty=band,**overrides) == grid
        count += 1
        if band in ("easy", "hard") and height in (9,14) and width in (11,20):
            boundaries.append({"seed":71,"sample_index":11,"difficulty":band,
                               "overrides":overrides,"input":grid,"expected":output})
    canonical = canonical_pairs(TASK, root=ROOT)
    for index, pair in enumerate(canonical):
        assert not GEN.self_check(pair["input"])
        assert independent_output(pair["input"])[0] == pair["output"]
        boundaries.append({"canonical_pair":index,"input":pair["input"],"expected":pair["output"]})
    applied = Catalog(ROOT).apply(TASK, [row["input"] for row in boundaries], check_generator_domain=True)
    for case, result in zip(boundaries, applied["results"], strict=True):
        assert result["output"] == case["expected"], case
    mutations = GEN.mutation_fixtures()
    assert all(GEN.self_check(grid) for _, grid in mutations)
    report = {
        "schema":"arcpuzzles-focused-audit-v1","task_id":TASK,"status":"no_issue_found",
        "generator_sha256":SOURCE_HASH,"rule_hash":applied["executed_rule_hash"],
        "canonical_rule_text_sha256":applied["rule_text_sha256"],
        "coverage":{"joint_override_cases":count,"seed":71,"sample_index":11,
                    "difficulties":[None,"easy","medium","hard"],"height":[9,14],"width":[11,20],
                    "frame_color_pairs":[[1,1],[2,1],[2,2]],"canonical_pairs":len(canonical),
                    "racket_checked_pairs":len(boundaries),"diagnostic_mutations_rejected":len(mutations)},
        "invocation":{"cwd":str(Path.cwd()),"argv":[sys.executable,*sys.argv]},
        "cases":boundaries,
        "limitations":["One seed/index for the complete finite override matrix; not all random layouts.",
                       "Reference execution covers 24 boundary inputs and the canonical pairs, not every matrix input.",
                       "No universal induction or trained-model performance claim; sources and approvals unchanged."],
    }
    (OUT/"probe.json").write_text(json.dumps(report,indent=2)+"\n")
    (OUT/"racket.json").write_text(json.dumps(applied,indent=2)+"\n")
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
    print(json.dumps({key:report[key] for key in ("task_id","status","generator_sha256","rule_hash","coverage")},indent=2))


if __name__ == "__main__":
    main()
