"""Bounded, findings-only singleton-corner audit. No repository writes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
TASK = "61c0bcd32328"
SOURCE = ROOT / "generators" / TASK / "generator.py"


def components(grid, bg):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg or (r, c) in seen:
                continue
            color = grid[r][c]
            cells = {(r, c)}
            seen.add((r, c))
            todo = [(r, c)]
            while todo:
                rr, cc = todo.pop()
                for q in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= q[0] < h and 0 <= q[1] < w and q not in seen
                            and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        cells.add(q)
                        todo.append(q)
            result.append((color, sorted(cells)))
    return result


def rival(grid):
    """Treat singleton objects as noise; copy every larger corner object."""
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row if v != 0).most_common(1)[0][0]
    out = [row[:] for row in grid]
    for color, cells in components(grid, bg):
        if len(cells) == 1:
            continue
        r1, r2 = min(r for r, c in cells), max(r for r, c in cells)
        c1, c2 = min(c for r, c in cells), max(c for r, c in cells)
        if r1 == 0 and c1 == 0:
            dr, dc = 0, w - 1 - c2
        elif r1 == 0 and c2 == w - 1:
            dr, dc = h - 1 - r2, 0
        elif r2 == h - 1 and c2 == w - 1:
            dr, dc = 0, -c1
        elif r2 == h - 1 and c1 == 0:
            dr, dc = -r1, 0
        else:
            continue
        for r, c in cells:
            out[r + dr][c + dc] = color
    return out


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    spec = importlib.util.spec_from_file_location("audited_generator_61c0", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    seed, sample_index, difficulty = 0, 0, "easy"
    overrides = {"scene_profile": "single_tl"}
    original = mod.generate(seed, sample_index, difficulty=difficulty, **overrides)
    analysis = mod._analysis(original)
    assert len(analysis["corner_parts"]) == 1
    corner, part = analysis["corner_parts"][0]
    assert corner == "tl" and (0, 0) in part["cells"] and len(part["cells"]) >= 2
    witness = [row[:] for row in original]
    removed = sorted(part["cells"] - {(0, 0)})
    for r, c in removed:
        witness[r][c] = analysis["background"]
    grids = [original, witness]
    validations = [mod.self_check(g, difficulty=difficulty) for g in grids]
    observations = [mod.observe_overrides(g) for g in grids]
    assert validations == [[], []]
    assert observations == [overrides, overrides]
    rows = []
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open():
        if TASK in line:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    programs = {row["program_solution"] for row in rows}
    assert len(programs) == 1
    program = next(iter(programs))
    pairs = {}
    occurrences = 0
    for row in rows:
        for split in ("train", "test"):
            examples = row[split]
            if isinstance(examples, dict):
                examples = [examples]
            for pair in examples:
                occurrences += 1
                inp = [[int(v) for v in rr] for rr in pair["input"]]
                expected = [[int(v) for v in rr] for rr in pair["output"]]
                pairs.setdefault(tuple(map(tuple, inp)), expected)
    canonical_agreement = []
    for inp, expected in pairs.items():
        inp = list(map(list, inp))
        canonical_agreement.append(rival(inp) == expected)
    assert all(canonical_agreement)
    public_corner_sizes = {}
    for name, grid in mod._PUBLIC_INPUTS.items():
        public_corner_sizes[name] = sorted(len(p["cells"]) for _, p in mod._analysis(grid)["corner_parts"])
    assert all(size >= 2 for sizes in public_corner_sizes.values() for size in sizes)
    assert min(map(len, mod._SHAPES[1:])) == 2
    record = {
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "normalized_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "generator_rule_hash": mod.RULE_HASH,
        "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
        "overrides": overrides,
        "input_order": ["unaltered_generated_control", "singleton_corner_mutation"],
        "mutation": {"retained_cell": [0, 0], "removed_cells": removed,
                     "replacement_background": analysis["background"]},
        "input_shape": [len(original), len(original[0])],
        "self_check": validations,
        "observe_overrides": observations,
        "canonical_occurrences": occurrences,
        "canonical_unique_pairs": len(pairs),
        "rival_matches_canonical_labels": canonical_agreement,
        "public_corner_component_sizes": public_corner_sizes,
        "general_corner_shape_sizes": list(map(len, mod._SHAPES[1:])),
        "rival": "Canonical same-color four-connected corner copying, except ignore singleton components as noise.",
        "preparation_effective_cwd": str(ROOT),
        "preparation_payload_argv": ["python3", *sys.argv],
    }
    save("input.json", {"inputs": grids})
    save("rival.json", {"outputs": [rival(g) for g in grids]})
    save("mirror.json", {"outputs": [mod.rule_mirror(g) for g in grids]})
    save("preparation.json", record)
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
