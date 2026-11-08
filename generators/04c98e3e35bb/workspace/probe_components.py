"""Reproduce the two canonical-fit connectivity counterexamples.

Packet command (from packet root):
  python3 review.py run python3 generators/04c98e3e35bb/workspace/probe_components.py

This probe executes only authored inputs, never draws generator assignments.
"""
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


def rival(grid, *, same_color, diagonal):
    h, w = len(grid), len(grid[0])
    out, seen = [row[:] for row in grid], set()
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0 and
                            (not same_color or grid[nr][nc] == grid[r][c]) and
                            (nr, nc) not in seen):
                        cells.append((nr, nc))
                        seen.add((nr, nc))
            value = 2 if any(rr in (0, h - 1) or cc in (0, w - 1) for rr, cc in cells) else 8
            for rr, cc in cells:
                out[rr][cc] = value
    return out


def main():
    root = find_root(__file__)
    evidence = json.loads((Path(__file__).resolve().parent.parent /
                           "counterexamples/component_contacts.evidence.json").read_text())
    pairs = canonical_pairs("04c98e3e35bb", root=root)
    actual = Catalog(root).apply("04c98e3e35bb", [case["input"] for case in evidence["cases"]])
    assert actual["executed_rule_hash"] == evidence["executed_rule_hash"]
    report = []
    for case, label, options in zip(evidence["cases"], actual["results"],
                                    ({"same_color": False, "diagonal": False},
                                     {"same_color": True, "diagonal": True})):
        assert label["error"] is None and label["output"] == case["canonical_output"]
        fits = [rival(pair["input"], **options) == pair["output"] for pair in pairs]
        prediction = rival(case["input"], **options)
        assert all(fits) and prediction == case["rival_output"]
        assert prediction != label["output"]
        report.append({"name": case["name"], "canonical_pairs_fit": fits,
                       "disagreement_cells": case["disagreement_cells"]})
    print(json.dumps({"executed_rule_hash": actual["executed_rule_hash"], "cases": report}, indent=2))


if __name__ == "__main__":
    main()
