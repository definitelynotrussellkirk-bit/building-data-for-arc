from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime"), str(REPO / "shared")]

TASK = "321b71aa828c"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_321b", SOURCE)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def components8(grid, color=1):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        start = unseen.pop()
        comp, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    p = (r + dr, c + dc)
                    if p in unseen:
                        unseen.remove(p)
                        comp.add(p)
                        stack.append(p)
        out.append(comp)
    return out


def bbox_top(comp):
    return min(r for r, _ in comp), min(c for _, c in comp)


def authority_mirror(grid):
    out = copy.deepcopy(grid)
    objects = components8(grid, 1)
    obj_rows = sorted({bbox_top(o)[0] for o in objects})
    obj_cols = sorted({bbox_top(o)[1] for o in objects})
    markers = [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 1)
    ]
    marker_rows = sorted({r for r, _, _ in markers})
    marker_cols = sorted({c for _, c, _ in markers})
    for obj in objects:
        top_r, top_c = bbox_top(obj)
        ri = obj_rows.index(top_r)
        ci = obj_cols.index(top_c)
        color = grid[marker_rows[ri]][marker_cols[ci]]
        for r, c in obj:
            out[r][c] = color
    return out


FIXED_MARKERS = ((0, 0), (0, 2), (2, 0), (2, 2))
FIXED_OBJECT_TOPS = ((4, 4), (4, 9), (7, 4), (7, 9))


def fixed_coordinate_shortcut(grid):
    """Shortcut exactly matching the selected generator's fixed 2x2 coordinates."""
    out = copy.deepcopy(grid)
    colors = [grid[r][c] for r, c in FIXED_MARKERS]
    by_top = {bbox_top(obj): obj for obj in components8(grid, 1)}
    for top, color in zip(FIXED_OBJECT_TOPS, colors):
        for r, c in by_top.get(top, ()):
            out[r][c] = color
    return out


def canonical_task():
    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise RuntimeError("canonical task missing")


def compact_signature(grid):
    objects = components8(grid, 1)
    markers = [
        (r, c, grid[r][c])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] not in (0, 1)
    ]
    return {
        "marker_positions": sorted([r[:2] for r in markers]),
        "object_tops": sorted([list(bbox_top(o)) for o in objects]),
        "object_sizes": sorted([len(o) for o in objects]),
        "marker_count": len(markers),
        "object_count": len(objects),
        "marker_grid_shape": [len({r for r, _, _ in markers}), len({c for _, c, _ in markers})],
        "object_grid_shape": [len({bbox_top(o)[0] for o in objects}), len({bbox_top(o)[1] for o in objects})],
    }


def main():
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    samples = 0
    self_check_errors = 0
    shortcut_matches = 0
    signature_counts = {}
    generated_batch = []
    recipes = []
    for band_no, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            seed = 321_000 + band_no * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            samples += 1
            self_check_errors += bool(gen.self_check(grid))
            expected = authority_mirror(grid)
            rival = fixed_coordinate_shortcut(grid)
            shortcut_matches += rival == expected
            sig = compact_signature(grid)
            key = json.dumps(sig, sort_keys=True)
            signature_counts[key] = signature_counts.get(key, 0) + 1
            if len(generated_batch) < 60:
                generated_batch.append(grid)
                recipes.append({"seed": seed, "sample_index": index, "difficulty": band})

    task = canonical_task()
    canonical = [
        {"split": split, "pair_index": i, **pair}
        for split in ("train", "test")
        for i, pair in enumerate(task.get(split, []))
    ]
    canonical_records = []
    for pair in canonical:
        rival = fixed_coordinate_shortcut(pair["input"])
        mirror = authority_mirror(pair["input"])
        canonical_records.append({
            "label": f"{pair['split']}[{pair['pair_index']}]",
            "signature": compact_signature(pair["input"]),
            "self_check_errors": gen.self_check(pair["input"]),
            "mirror_matches_label": mirror == pair["output"],
            "shortcut_matches_label": rival == pair["output"],
        })

    # Use the 3x3/six-object canonical training pair as the retained counterexample.
    counter = task["train"][1]
    rival = fixed_coordinate_shortcut(counter["input"])
    assert authority_mirror(counter["input"]) == counter["output"]
    assert rival != counter["output"]

    summary = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "source_sha256": source_sha,
        "rival": "fixed generated coordinates: markers at (0,0),(0,2),(2,0),(2,2); object bboxes at (4,4),(4,9),(7,4),(7,9)",
        "ordinary_samples": samples,
        "ordinary_self_check_errors": self_check_errors,
        "ordinary_shortcut_matches_python_authority": shortcut_matches,
        "ordinary_unique_structural_signatures": len(signature_counts),
        "ordinary_signature_counts": [
            {"count": count, "signature": json.loads(key)}
            for key, count in sorted(signature_counts.items())
        ],
        "canonical_pairs": len(canonical_records),
        "canonical_records": canonical_records,
        "counterexample": {
            "label": "train[1]",
            "self_check_errors": gen.self_check(counter["input"]),
            "signature": compact_signature(counter["input"]),
            "python_authority_differs_from_shortcut": counter["output"] != rival,
        },
        "audit_stage_evidence": {
            "task_tests": "none found",
            "semantic_contract": "none declared",
        },
    }
    (HERE / "distribution_probe.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (HERE / "input.json").write_text(json.dumps(counter["input"], indent=2) + "\n")
    (HERE / "expected_canonical.json").write_text(json.dumps(counter["output"], indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "generated_batch_input.json").write_text(json.dumps(generated_batch, indent=2) + "\n")
    (HERE / "generated_batch_recipes.json").write_text(json.dumps(recipes, indent=2) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
