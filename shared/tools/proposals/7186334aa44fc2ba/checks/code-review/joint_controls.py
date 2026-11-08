"""Bounded independent exact-control and construction review; no source edits."""
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from additional_rivals import components

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1] / "repo"
SOURCE = REPO / "generators/899e2a4cfac9/generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
spec = importlib.util.spec_from_file_location("review_generator", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def edge_set(group, h, w):
    return {edge for r, c in group for value, target, edge in
            ((r, 0, "top"), (r, h-1, "bottom"), (c, 0, "left"), (c, w-1, "right"))
            if value == target}


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    legal_counts = [(n, k) for n in range(4, 8) for k in range(3, min(n, 6)+1)]
    cases = itertools.chain(
        itertools.product(range(6, 13), range(7, 15), legal_counts, (None, "easy", "medium", "hard"), range(4)),
        itertools.product((6,), (7,), legal_counts, (None, "easy", "medium", "hard"), range(4, 128)),
    )
    checked, failures, survivor_counts, edge_coverage = 0, [], Counter(), Counter()
    for h, w, (n, k), band, index in cases:
        request = {"grid_h": h, "grid_w": w, "n_blobs": n, "n_distinct_colors": k}
        try:
            grid = gen.generate("independent-joint-review", index, difficulty=band, **request)
            groups = components(grid)
            observed = {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blobs": len(groups),
                        "n_distinct_colors": len({v for row in grid for v in row})}
            if observed != request:
                raise AssertionError((observed, request))
            if gen.self_check(grid) or gen.strict_canonical_like(grid):
                raise AssertionError("validator rejected generated grid")
            edges = [edge_set(group, h, w) for group in groups]
            isolated_edges = {next(iter(edge)) for edge in edges if len(edge) == 1}
            if n >= 6 and len(isolated_edges) != 4:
                raise AssertionError(("lost default edge witness", isolated_edges))
            outside = [g for g, edge in zip(groups, edges) if edge]
            inside = [g for g, edge in zip(groups, edges) if not edge]
            if not set(map(len, outside)) & set(map(len, inside)):
                raise AssertionError("lost equal-size opposite roles")
            color = lambda group: grid[next(iter(group))[0]][next(iter(group))[1]]
            if not set(map(color, outside)) & set(map(color, inside)):
                raise AssertionError("lost repeated-color opposite roles")
            if sum(v == 0 for row in grid for v in row) * 2 <= h * w:
                raise AssertionError("background no longer dominant")
            survivor_counts[len(inside)] += 1
            edge_coverage[len(isolated_edges)] += 1
        except Exception as exc:
            failures.append({"band": band, "index": index, "request": request,
                             "error": repr(exc)})
            if len(failures) >= 10:
                break
        checked += 1
    result = {"source_sha256": source_hash, "post_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "joint_axis_settings": 56 * len(legal_counts), "bands": [None, "easy", "medium", "hard"],
              "replays_per_setting": 4, "minimum_shape_replays_per_count_and_band": 128,
              "checked": checked, "failures": failures,
              "survivor_counts": dict(survivor_counts), "isolated_edge_coverage": dict(edge_coverage)}
    (HERE / "joint-controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    assert not failures
    assert result["source_sha256"] == result["post_source_sha256"], "Source changed while review ran"


if __name__ == "__main__":
    main()
