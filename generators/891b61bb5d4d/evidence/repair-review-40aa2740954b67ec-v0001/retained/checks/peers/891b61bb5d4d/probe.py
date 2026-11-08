from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import find_root, load_selected_generator

TASK_ID = "891b61bb5d4d"
EXPECTED_SHA256 = "3bbd358d00a9648d8bdc829c944b0a2c317d8f5aef0d5b36d4f0557f6e886268"
MAX_SEEDS = 512
DEMOS = 3
QUERY_INDICES = (3, 4, 5, 6)


def digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def canonical_program(root: Path) -> str:
    for line in (root / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise ValueError(f"canonical program missing for {TASK_ID}")


def boxes(grid):
    positions = {}
    for color in (1, 2):
        pts = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(pts) != 2:
            return None
        rows = [p[0] for p in pts]
        cols = [p[1] for p in pts]
        positions[color] = (min(rows), min(cols), max(rows), max(cols))
    return positions


def paint(grid, coords):
    out = deepcopy(grid)
    for r, c in coords:
        out[r][c] = 8
    return out


def rect(box):
    r0, c0, r1, c1 = box
    return {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def canonical_python(grid):
    found = boxes(grid)
    if found is None:
        return deepcopy(grid)
    overlap = rect(found[1]) & rect(found[2])
    return paint(grid, overlap)


def rival_preserve_markers(grid):
    found = boxes(grid)
    if found is None:
        return deepcopy(grid)
    overlap = {(r, c) for r, c in rect(found[1]) & rect(found[2]) if grid[r][c] not in (1, 2)}
    return paint(grid, overlap)


def rival_union(grid):
    found = boxes(grid)
    if found is None:
        return deepcopy(grid)
    return paint(grid, rect(found[1]) | rect(found[2]))


def rival_enclosing_box(grid):
    found = boxes(grid)
    if found is None:
        return deepcopy(grid)
    r0 = min(found[1][0], found[2][0]); c0 = min(found[1][1], found[2][1])
    r1 = max(found[1][2], found[2][2]); c1 = max(found[1][3], found[2][3])
    return paint(grid, rect((r0, c0, r1, c1)))


def rival_blue_box(grid):
    found = boxes(grid)
    return deepcopy(grid) if found is None else paint(grid, rect(found[1]))


def rival_red_box(grid):
    found = boxes(grid)
    return deepcopy(grid) if found is None else paint(grid, rect(found[2]))


def rival_overlap_border(grid):
    found = boxes(grid)
    if found is None:
        return deepcopy(grid)
    cells = rect(found[1]) & rect(found[2])
    if not cells:
        return deepcopy(grid)
    rows = [r for r, _ in cells]; cols = [c for _, c in cells]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    border = {(r, c) for r, c in cells if r in (r0, r1) or c in (c0, c1)}
    return paint(grid, border)


RIVALS = {
    "preserve_original_markers": rival_preserve_markers,
    "paint_union": rival_union,
    "paint_enclosing_box": rival_enclosing_box,
    "paint_blue_box": rival_blue_box,
    "paint_red_box": rival_red_box,
    "paint_overlap_border_only": rival_overlap_border,
}


def search(module):
    for seed in range(MAX_SEEDS):
        demo_grids = [module.generate(seed, index, difficulty="medium") for index in range(DEMOS)]
        demo_outputs = [canonical_python(grid) for grid in demo_grids]
        for query_index in QUERY_INDICES:
            query_grid = module.generate(seed, query_index, difficulty="medium")
            query_output = canonical_python(query_grid)
            for name, rival in RIVALS.items():
                if all(rival(grid) == output for grid, output in zip(demo_grids, demo_outputs)) and rival(query_grid) != query_output:
                    return {
                        "seed": seed,
                        "query_sample_index": query_index,
                        "rival": name,
                        "demo_grids": demo_grids,
                        "query_grid": query_grid,
                    }
    return None


def main() -> None:
    here = Path(__file__).resolve()
    root = find_root(here)
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SHA256:
        raise ValueError(f"peer source changed: {source_sha256}")
    found = search(module)
    program = canonical_program(root)
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    records = []
    try:
        if found is not None:
            grids = found["demo_grids"] + [found["query_grid"]]
        else:
            grids = [module.generate(0, index, difficulty="medium") for index in range(DEMOS + 1)]
        for index, grid in enumerate(grids):
            errors = module.self_check(grid)
            if errors:
                raise AssertionError(f"current self_check rejected record {index}: {errors}")
            canonical_output = apply(program, grid)
            python_output = canonical_python(grid)
            if canonical_output != python_output:
                raise AssertionError(f"search mirror diverged from protected Racket on record {index}")
            rival_outputs = {name: rival(grid) for name, rival in RIVALS.items()}
            records.append(
                {
                    "role": "query" if index == len(grids) - 1 else "demo",
                    "index": index,
                    "input": grid if found is not None else None,
                    "canonical_output": canonical_output if found is not None else None,
                    "input_sha256": digest(grid),
                    "canonical_output_sha256": digest(canonical_output),
                    "rival_output_sha256": {name: digest(output) for name, output in rival_outputs.items()},
                    "rivals_agree": {name: output == canonical_output for name, output in rival_outputs.items()},
                }
            )
    finally:
        bridge.close()

    if found is not None:
        chosen = found["rival"]
        demos_agree = all(record["rivals_agree"][chosen] for record in records[:-1])
        query_disagrees = not records[-1]["rivals_agree"][chosen]
        if not demos_agree or not query_disagrees:
            raise AssertionError("stored ambiguity did not replay")
        verdict = "finding"
        explanations = {
            "preserve_original_markers": (
                "A rival that fills the rectangle intersection but preserves original 1/2 marker cells "
                "fits every visible demonstration and changes the protected-Racket query label.",
                "Guarantee at least one demonstration where a marker lies inside the overlap and is overwritten by 8.",
            ),
            "paint_overlap_border_only": (
                "A rival that paints only the border of the rectangle intersection fits all three thin-overlap "
                "demonstrations and changes the protected-Racket query, whose overlap has interior cells.",
                "Guarantee at least one demonstration with overlap height and width both at least 3, or reject lessons where the border-only rival survives.",
            ),
        }
        explanation, next_action = explanations.get(
            chosen,
            (
                f"The explicit rival {chosen!r} fits every visible demonstration but changes the protected-Racket query label.",
                f"Add a lesson schedule or lesson_identifiable gate that guarantees a demonstration refuting {chosen!r}.",
            ),
        )
        finding = {
            "kind": "visible_demo_query_ambiguity",
            "rival": chosen,
            "seed": found["seed"],
            "demonstrations": DEMOS,
            "query_sample_index": found["query_sample_index"],
            "explanation": explanation,
            "next_action": next_action,
        }
    else:
        verdict = "bounded_no_finding"
        finding = None

    result = {
        "schema": "arcpuzzles-bounded-peer-learnability-v1",
        "task_id": TASK_ID,
        "source_path": source_path.relative_to(root).as_posix(),
        "source_sha256": source_sha256,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "racket": identity,
        "scope": {
            "searched_seeds": MAX_SEEDS,
            "demonstrations": DEMOS,
            "query_sample_indices": list(QUERY_INDICES),
            "rivals": sorted(RIVALS),
        },
        "protected_racket_evaluations": len(records),
        "verdict": verdict,
        "finding": finding,
        "records": records,
        "limits": "Bounded search over six explicit rivals; prevalence and universal ambiguity were not measured.",
    }
    here.with_name("result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": verdict, "finding": finding, "racket_evaluations": len(records)}, sort_keys=True))


if __name__ == "__main__":
    main()
