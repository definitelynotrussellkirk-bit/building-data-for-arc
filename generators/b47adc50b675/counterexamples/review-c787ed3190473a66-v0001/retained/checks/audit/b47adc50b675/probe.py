"""Source-bound first-cell versus bbox-corner lesson counterexample."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator

TASK = "b47adc50b675"
EXPECTED_SOURCE = "9668ccecee8f9c789625822d3e48014fd5fe7ef937a786cee4950f298c74f0e3"


def translate(grid, *, first_cell=False):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    r0, c0 = (points[0] if first_cell else
              (min(r for r, c in points), min(c for r, c in points)))
    result = [[0] * len(grid[0]) for _ in grid]
    for r, c in points:
        if 0 <= r-r0 < len(grid) and 0 <= c-c0 < len(grid[0]):
            result[r-r0][c-c0] = 3
    return result


def main():
    module, _, source_sha = load_selected_generator(TASK, root=REPO)
    assert source_sha == EXPECTED_SOURCE
    row = next(json.loads(line) for line in canonical_path(REPO).read_text().splitlines()
               if json.loads(line).get("task_id") == TASK)
    pairs = canonical_pairs(TASK, root=REPO, labeled_only=True)
    canonical_fit = [translate(pair["input"], first_cell=True) == pair["output"] for pair in pairs]
    assert len(pairs) == 3 and all(canonical_fit)
    examined = 0
    for lesson_index in range(7):
        start = lesson_index * 11
        grids = [module.generate(0, index, difficulty="easy") for index in range(start, start+4)]
        examined += 1
        independent = [translate(grid) for grid in grids]
        rival = [translate(grid, first_cell=True) for grid in grids]
        if all(rival[i] == independent[i] for i in range(3)) and rival[3] != independent[3]:
            break
    assert start == 66, "pinned source should reproduce seed0/easy/start66"
    for grid in grids:
        before = deepcopy(grid)
        assert module.self_check(grid) == [] and grid == before
        assert module.rule_mirror(grid) == translate(grid)
    minimal_controls = {"shape_id": 7, "transpose": True, "grid_h": 5,
                        "grid_w": 6, "row_offset": 1, "col_offset": 1}
    minimal = module.generate(0, 69, difficulty="easy", **minimal_controls)
    assert module.self_check(minimal) == []
    assert module.observe_overrides(minimal) == minimal_controls
    (HERE / "input.json").write_text(json.dumps({"inputs": grids + [minimal]}) + "\n")
    expected = [translate(grid) for grid in grids + [minimal]]
    rivals = [translate(grid, first_cell=True) for grid in grids + [minimal]]
    (HERE / "expected.json").write_text(json.dumps(expected) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rivals) + "\n")
    result = {"task_id": TASK, "generator_sha256": source_sha,
              "rule_source_sha256": hashlib.sha256(row["program_solution"].encode()).hexdigest(),
              "declared_rule_hash": module.RULE_HASH,
              "canonical_pairs_checked": len(pairs), "canonical_rival_fit": canonical_fit,
              "bounded_search": {"seed": 0, "difficulty": "easy", "start_rule": "i*11",
                                 "lessons_examined": examined, "draws_examined": examined*4},
              "counterexample": {"seed": 0, "difficulty": "easy", "start": start,
                                 "sample_indices": list(range(start, start+4)),
                                 "observed_controls": [module.observe_overrides(g) for g in grids],
                                 "generator_domain_errors": [module.self_check(g) for g in grids],
                                 "rival_agrees_with_independent_output": [rival[i] == independent[i] for i in range(4)]},
              "minimal_witness_controls": minimal_controls,
              "minimal_witness_domain_errors": module.self_check(minimal),
              "rival_description": "Translate all green cells by the negative of the first row-major green cell, clipping translated cells outside the canvas, instead of using independent bbox row/column minima.",
              "scope": "Python oracle and stored canonical labels only; rescore.py separately verifies actual Racket labels."}
    (HERE / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
