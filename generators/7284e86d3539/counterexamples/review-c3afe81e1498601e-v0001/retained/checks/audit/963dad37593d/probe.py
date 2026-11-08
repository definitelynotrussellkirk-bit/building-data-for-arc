"""Reproduce current 963dad37593d audit findings without editing the target."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path.cwd()
TASK_ID = "963dad37593d"
OUT = ROOT.parent / "checks" / "audit" / TASK_ID
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location("audit_generator_963", SOURCE)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)
canonical = json.loads((OUT / "canonical.json").read_text())


def digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def leading_prefix_rank(grid) -> int:
    rank = 0
    for value in grid[0]:
        if value != 1:
            break
        rank += 1
    return rank


def header_count(grid) -> int:
    return sum(value == 1 for value in grid[0])


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def crop_for_rank(grid, rank):
    if rank < 1:
        return None
    comps = components(grid)
    comps.sort(key=lambda cells: (-len(cells), min(cells)))
    if rank > len(comps):
        return None
    cells = comps[rank - 1]
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    chosen = set(cells)
    return [[8 if (r, c) in chosen else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def prefix_rival(grid):
    return crop_for_rank(grid, leading_prefix_rank(grid))


records = []
for difficulty in ("easy", "medium", "hard"):
    for seed in range(20):
        grid = gen.generate(seed, 0, difficulty=difficulty)
        count = header_count(grid)
        prefix = leading_prefix_rank(grid)
        records.append({
            "kind": "generated",
            "seed": seed,
            "sample_index": 0,
            "difficulty": difficulty,
            "overrides": {},
            "input": grid,
            "input_sha256": digest(grid),
            "self_check": gen.self_check(grid, difficulty=difficulty),
            "header_count": count,
            "leading_prefix_rank": prefix,
            "prefix_equals_count": prefix == count,
            "header_positions": [c for c, value in enumerate(grid[0]) if value == 1],
            "rival_output": prefix_rival(grid),
        })

# The second labelled training pair has three blue cells shifted right by one.
pair = canonical["variants"][0]["train"][1]
records.append({
    "kind": "canonical_witness",
    "variant": 0,
    "split": "train",
    "pair_index": 1,
    "input": pair["input"],
    "expected_canonical_output": pair["output"],
    "input_sha256": digest(pair["input"]),
    "self_check": gen.self_check(pair["input"]),
    "header_count": header_count(pair["input"]),
    "leading_prefix_rank": leading_prefix_rank(pair["input"]),
    "prefix_equals_count": leading_prefix_rank(pair["input"]) == header_count(pair["input"]),
    "header_positions": [c for c, value in enumerate(pair["input"][0]) if value == 1],
    "rival_output": prefix_rival(pair["input"]),
})

(OUT / "input.json").write_text(json.dumps([row["input"] for row in records], indent=2) + "\n")
(OUT / "cases.json").write_text(json.dumps({
    "task_id": TASK_ID,
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "selected_rule_hash": canonical["rule_hash"],
    "rival_claim": "Leading blue prefix fits generated samples only; canonical shifted-header pair refutes it.",
    "cases": records,
}, indent=2) + "\n")

# Probe advertised controls that are not consumed by the implementation.
baseline = gen.generate(0, 0, difficulty="medium")
override_values = {
    "grid_h": [9, 16],
    "grid_w": [10, 18],
    "palette_kind": ["default", "warm", "cool", "varied"],
    "palette_size": [4],
    "position_bias": ["header_top_objects_below"],
    "n_distinct_colors": [4],
    "density": ["sparse"],
    "texture": ["default", "warm", "cool", "varied"],
}
override_rows = []
for axis, values in override_values.items():
    for value in values:
        try:
            grid = gen.generate(0, 0, difficulty="medium", **{axis: value})
            override_rows.append({
                "axis": axis,
                "value": value,
                "raised": None,
                "identical_to_baseline": grid == baseline,
                "input_sha256": digest(grid),
                "self_check": gen.self_check(grid, difficulty="medium"),
            })
        except Exception as exc:  # retain exact behavior rather than hiding it
            override_rows.append({
                "axis": axis,
                "value": value,
                "raised": f"{type(exc).__name__}: {exc}",
                "identical_to_baseline": None,
            })

hard_ranks = []
for seed in range(100):
    grid = gen.generate(seed, 0, difficulty="hard")
    hard_ranks.append(header_count(grid))

(OUT / "overrides.json").write_text(json.dumps({
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "baseline": {"seed": 0, "sample_index": 0, "difficulty": "medium",
                 "input_sha256": digest(baseline), "input": baseline},
    "checks": override_rows,
    "hard_default_rank_counts": {str(rank): hard_ranks.count(rank) for rank in sorted(set(hard_ranks))},
    "advertised_rank_valid": "1..3",
}, indent=2) + "\n")

print(json.dumps({
    "generated_cases": len(records) - 1,
    "all_generated_prefix_equal_count": all(r["prefix_equals_count"] for r in records[:-1]),
    "canonical_header_count": records[-1]["header_count"],
    "canonical_prefix_rank": records[-1]["leading_prefix_rank"],
    "override_cases": len(override_rows),
    "identical_nonraising_overrides": sum(r.get("identical_to_baseline") is True for r in override_rows),
    "hard_rank_above_advertised": sum(rank > 3 for rank in hard_ranks),
}))
