"""Reproduce the two assigned adversarial audit findings."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PACKET = Path(__file__).resolve().parents[2]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def grid_hash(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def divider(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(rows) + len(cols) != 1:
        raise ValueError(f"not one divider: rows={rows}, cols={cols}")
    return ("row", rows[0]) if rows else ("col", cols[0])


def blocked_targets(grid):
    kind, d = divider(grid)
    h, w = len(grid), len(grid[0])
    hits = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 7:
                continue
            rr, cc = ((2 * d - r, c) if kind == "row" else (r, 2 * d - c))
            if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 0:
                hits.append({"orange": [r, c], "target": [rr, cc], "target_color": grid[rr][cc]})
    return hits


def overwrite_rival(grid):
    kind, d = divider(grid)
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 7:
                continue
            rr, cc = ((2 * d - r, c) if kind == "row" else (r, 2 * d - c))
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 1
    return out


def intended_reflect(grid):
    kind, d = divider(grid)
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 7:
                continue
            rr, cc = ((2 * d - r, c) if kind == "row" else (r, 2 * d - c))
            if 0 <= rr < h and 0 <= cc < w and out[rr][cc] == 0:
                out[rr][cc] = 1
    return out


def canonical_pairs(task_id: str):
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return row["train"] + test
    raise RuntimeError(task_id)


def audit_f151():
    task = "f151fbd31cb2"
    gen, source = load(task)
    left = gen.generate(31415, 7, difficulty="hard", shape_key=1, color_key=2)
    right = gen.generate(31415, 7, difficulty="hard", shape_key=4, color_key=8)
    colors = {value for row in left for value in row}
    actual_shape = [value for value in (1, 4) if value in colors]
    actual_color = [value for value in (2, 6, 8) if value in colors]
    report = {
        "schema": "assigned-audit-f151fbd31cb2-v1",
        "task_id": task,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "command": ["python3", "checks/audit/audit_probe.py"],
        "cwd": "packet_root",
        "seed": 31415,
        "sample_index": 7,
        "difficulty": "hard",
        "request_a": {"shape_key": 1, "color_key": 2},
        "request_b": {"shape_key": 4, "color_key": 8},
        "byte_identical_outputs": left == right,
        "grid_hash_a": grid_hash(left),
        "grid_hash_b": grid_hash(right),
        "actual_shape_key_colors_present": actual_shape,
        "actual_color_key_colors_present": actual_color,
        "input": left,
        "finding": "Advertised shape_key and color_key exact overrides are not consumed; contradictory requests produce an identical grid.",
    }
    out = PACKET / "checks" / "audit" / task / "override-inert.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    return report


def audit_8c6():
    task = "8c6b703c91e5"
    gen, source = load(task)
    pairs = canonical_pairs(task)
    canonical_mismatches = [
        i for i, pair in enumerate(pairs)
        if overwrite_rival(pair["input"]) != pair["output"]
    ]

    lessons = 250
    demo_count = int(gen.EXAMPLES_NEEDED)
    lessons_refuting = 0
    inputs_with_block = 0
    unique = set()
    witness = None
    for lesson in range(lessons):
        seed = 7001 + lesson
        has_counterexample = False
        for offset in range(demo_count):
            sample_index = lesson * demo_count + offset
            grid = gen.generate(seed, sample_index, difficulty=("easy", "medium", "hard")[lesson % 3])
            unique.add(grid_hash(grid))
            hits = blocked_targets(grid)
            if hits:
                inputs_with_block += 1
                has_counterexample = True
                if witness is None:
                    intended = intended_reflect(grid)
                    rival = overwrite_rival(grid)
                    if intended != rival:
                        witness = {
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": ("easy", "medium", "hard")[lesson % 3],
                            "blocked_targets": hits,
                            "input": grid,
                            "intended_python": intended,
                            "overwrite_rival": rival,
                        }
        lessons_refuting += has_counterexample
    if witness is None:
        raise AssertionError("sampler search found no blocked-target witness")

    report = {
        "schema": "assigned-audit-8c6b703c91e5-v1",
        "task_id": task,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "command": ["python3", "checks/audit/audit_probe.py"],
        "cwd": "packet_root",
        "rival": "Reflect every orange cell to blue even when the reflected target is already nonzero (overwrite decorations).",
        "canonical_pairs_checked": len(pairs),
        "canonical_rival_mismatch_indices": canonical_mismatches,
        "canonical_fit_count": len(pairs) - len(canonical_mismatches),
        "sampling": {
            "lessons": lessons,
            "demos_per_lesson": demo_count,
            "generated_inputs": lessons * demo_count,
            "distinct_inputs": len(unique),
            "seeds": "7001 + lesson",
            "sample_indices": "lesson*4 through lesson*4+3",
            "difficulty": "cycles easy, medium, hard",
            "inputs_with_blocked_target": inputs_with_block,
            "lessons_refuting_rival": lessons_refuting,
            "lessons_where_rival_survives": lessons - lessons_refuting,
            "warning": "Finite deterministic sample; not an IID confidence interval or universal claim.",
        },
        "witness": witness,
        "finding": "The overwrite rival fits every public pair. The unscheduled random sampler emits counterexamples, but many four-demo lessons contain none.",
    }
    base = PACKET / "checks" / "audit" / task
    (base / "overwrite-shortcut.json").write_text(json.dumps(report, indent=2) + "\n")
    (base / "input.json").write_text(json.dumps({"input": witness["input"]}, indent=2) + "\n")
    return report


def main():
    f = audit_f151()
    c = audit_8c6()
    print(json.dumps({
        "f151fbd31cb2": {
            "byte_identical_outputs": f["byte_identical_outputs"],
            "actual_shape_key_colors_present": f["actual_shape_key_colors_present"],
            "actual_color_key_colors_present": f["actual_color_key_colors_present"],
        },
        "8c6b703c91e5": {
            "canonical_fit_count": c["canonical_fit_count"],
            "canonical_pairs_checked": c["canonical_pairs_checked"],
            "sampling": c["sampling"],
            "witness_seed": c["witness"]["seed"],
            "witness_sample_index": c["witness"]["sample_index"],
        },
    }, indent=2))


if __name__ == "__main__":
    main()
