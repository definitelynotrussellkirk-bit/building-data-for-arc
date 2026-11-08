from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared" / "runtime"), str(REPO / "shared")]
TASK = "5639e60f0fac"
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_5639", SOURCE)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out = []
    while unseen:
        start = unseen.pop()
        comp, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    comp.add(point)
                    stack.append(point)
        out.append(comp)
    return out


def bbox(comp):
    rows = [r for r, _ in comp]
    cols = [c for _, c in comp]
    return min(rows), min(cols), max(rows), max(cols)


def parts(grid):
    tb = bbox(components(grid, 3)[0])
    cb = bbox(components(grid, 8)[0])
    tr0, tc0, tr1, tc1 = tb
    mask = [[int(grid[r][c] == 3) for c in range(tc0, tc1 + 1)]
            for r in range(tr0, tr1 + 1)]
    return tb, cb, mask


def authority(grid):
    _, (r0, c0, _, _), mask = parts(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            out[r0 + r][c0 + c] = 8 if value else 0
    return out


def fixed_three_row_transfer(grid):
    """Shortcut: stamp only the first three template rows."""
    _, (r0, c0, _, _), mask = parts(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(mask[:3]):
        for c, value in enumerate(row):
            out[r0 + r][c0 + c] = 8 if value else 0
    return out


def counterexample():
    grid = [[0] * 14 for _ in range(10)]
    mask = (
        (1, 1, 0),
        (0, 1, 0),
        (1, 1, 1),
        (1, 0, 1),
    )
    for r, row in enumerate(mask, start=1):
        for c, value in enumerate(row, start=1):
            if value:
                grid[r][c] = 3
    for r in range(4):
        for c in range(3):
            grid[5 + r][9 + c] = 8
    return grid


def canonical_pairs():
    def normalized(pair):
        def grid(value):
            if value and isinstance(value[0], str):
                return [[int(cell) for cell in row] for row in value]
            return value
        return {"input": grid(pair["input"]), "output": grid(pair["output"])}

    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return [normalized(pair) for pair in row.get("train", []) + row.get("test", [])]
    raise RuntimeError("canonical task missing")


def main():
    samples = 0
    self_check_errors = 0
    rival_matches = 0
    template_height_counts = {}
    for band_no, band in enumerate(("easy", "medium", "hard")):
        for index in range(300):
            grid = gen.generate(930000 + band_no * 10000 + index, index, difficulty=band)
            samples += 1
            self_check_errors += bool(gen.self_check(grid))
            height = parts(grid)[0][2] - parts(grid)[0][0] + 1
            template_height_counts[str(height)] = template_height_counts.get(str(height), 0) + 1
            rival_matches += fixed_three_row_transfer(grid) == gen.rule_mirror(grid)

    grid = counterexample()
    py_authority = authority(grid)
    rival = fixed_three_row_transfer(grid)
    assert py_authority != rival
    assert parts(grid)[0][2] - parts(grid)[0][0] + 1 == 4

    canonical = canonical_pairs()
    canonical_fit = sum(fixed_three_row_transfer(pair["input"]) == pair["output"]
                        for pair in canonical)
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    summary = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK,
        "source_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "rival": "stamp only the first three template rows",
        "ordinary_samples": samples,
        "ordinary_self_check_errors": self_check_errors,
        "ordinary_rival_matches": rival_matches,
        "ordinary_template_height_counts": template_height_counts,
        "canonical_pairs": len(canonical),
        "canonical_rival_matches": canonical_fit,
        "counterexample": {
            "template_bbox": parts(grid)[0],
            "canvas_bbox": parts(grid)[1],
            "self_check_errors": gen.self_check(grid),
            "python_authority_differs_from_rival": py_authority != rival,
        },
    }
    (HERE / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (HERE / "python_authority.json").write_text(json.dumps(py_authority, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    (HERE / "distribution_probe.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
