"""Bounded peer check: exact-domino rival on one default four-pair lesson."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(sys.argv[1]).resolve()
TASK = "8e8d21720efb"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
from reviewer_support import load_selected_generator


def domino_rival(grid):
    """Keep only same-colour cardinal components containing exactly two cells."""
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c]}
    out = [[0] * w for _ in range(h)]
    sizes = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        sizes.append(len(cells))
        if len(cells) == 2:
            for r, c in cells:
                out[r][c] = color
    return out, sorted(sizes)


module, source, source_hash = load_selected_generator(TASK, root=ROOT)
programs = {row["program_solution"] for row in Catalog(ROOT)._variants()[TASK]}
assert len(programs) == 1
program = programs.pop()
pairs = []
with _local_imports(ROOT / "shared/runtime", source.parent):
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        for index in range(1, 5):
            grid = module.generate(0, index, difficulty="medium")
            errors = module.self_check(grid)
            assert not errors, errors
            output = apply(program, grid)
            rival, sizes = domino_rival(grid)
            pairs.append({"sample_index": index, "role": "query" if index == 4 else "demo",
                "input": grid, "output": output, "rival_output": rival,
                "component_sizes": sizes, "self_check_errors": errors,
                "profile": module.classify_profile(grid), "rival_matches": rival == output})
    finally:
        bridge.close()

demos_fit = all(pair["rival_matches"] for pair in pairs[:3])
query_differs = not pairs[3]["rival_matches"]
hook_reasons = module.lesson_identifiable(
    [{"input": p["input"], "output": p["output"]} for p in pairs[:3]],
    {"input": pairs[3]["input"], "output": pairs[3]["output"]})
report = {
    "schema": "8e8d21720efb-bounded-peer-check-v1", "task_id": TASK,
    "source_sha256": source_hash, "declared_rule_hash": module.RULE_HASH,
    "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
    "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "runtime_identity": identity, "seed": 0, "difficulty": "medium",
    "policy": "one default consecutive four-pair window, demos 1/2/3 and query 4; no overrides",
    "rival": "keep exactly size-2 same-colour cardinal components; erase all other components",
    "rival_fits_all_demos": demos_fit, "rival_changes_query": query_differs,
    "query_changed_cells": sum(a != b for ra, rb in zip(pairs[3]["output"], pairs[3]["rival_output"]) for a, b in zip(ra, rb)),
    "declared_lesson_hook_reasons": hook_reasons, "pairs": pairs,
    "outcome": "source-bound learnability finding" if demos_fit and query_differs else "no finding",
    "limits": "One lesson and one undeclared rival. No prevalence, solve accuracy, approval change, or label defect claimed."
}
assert demos_fit and query_differs
assert not hook_reasons
destination = Path(__file__).with_name("peer-result.json")
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key: report[key] for key in ("outcome", "source_sha256", "declared_rule_hash", "rival_fits_all_demos", "rival_changes_query", "query_changed_cells", "declared_lesson_hook_reasons")}))
