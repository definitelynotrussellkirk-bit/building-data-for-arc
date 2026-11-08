#!/usr/bin/env python3
"""Deterministic, source-bound probes for the two assigned audit targets."""
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid: list[list[int]], value: int = 0) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != value or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            comp: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.popleft()
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                if (rr, cc) in seen or grid[rr][cc] != value:
                    continue
                seen.add((rr, cc))
                comp.add((rr, cc))
                todo.extend(((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)))
            out.append(comp)
    return out


def wall_gap_rival(grid: list[list[int]]) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) != 1:
        raise ValueError(f"expected one wall color, got {sorted(colors)}")
    wall = next(iter(colors))
    wall_rows = {r for r, row in enumerate(grid) if sum(v == wall for v in row) >= 0.7 * w}
    wall_cols = {c for c in range(w) if sum(grid[r][c] == wall for r in range(h)) >= 0.7 * h}
    out = [row[:] for row in grid]
    for comp in components(grid):
        merged = any(r in wall_rows or c in wall_cols for r, c in comp)
        color = 4 if merged else 3
        for r, c in comp:
            out[r][c] = color
    return out


def audit_953() -> dict:
    module, digest = load_generator("953db766893d")
    canonical = list(module._PUBLIC_INPUTS.items())
    canonical_rows = []
    for name, grid in canonical:
        expected = module.rule_mirror(grid)
        actual = wall_gap_rival(grid)
        canonical_rows.append({"profile": name, "matches": actual == expected})

    per_band = {}
    total = Counter()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        counts = Counter()
        profiles = Counter()
        first_mismatch = None
        for i in range(500):
            seed = 953_000_000 + band_index * 100_000 + i
            sample_index = i * 13 + 5
            grid = module.generate(seed, sample_index, difficulty=band)
            errs = module.self_check(grid, difficulty=band)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(errs)
            match = wall_gap_rival(grid) == module.rule_mirror(grid)
            counts["rival_matches"] += match
            if not match and first_mismatch is None:
                first_mismatch = {
                    "seed": seed,
                    "sample_index": sample_index,
                    "difficulty": band,
                    "grid": grid,
                }
            profiles[module.observe_overrides(grid)["scene_profile"]] += 1
        counts["rival_disagreements"] = counts["samples"] - counts["rival_matches"]
        total.update(counts)
        per_band[str(band)] = {
            **dict(counts),
            "profile_counts": dict(sorted(profiles.items())),
            "first_mismatch": first_mismatch,
        }
    return {
        "task_id": "953db766893d",
        "generator_sha256": digest,
        "rule_hash": module.RULE_HASH,
        "rival": "wall_gap_incidence",
        "canonical_public_profiles": canonical_rows,
        "per_band": per_band,
        "totals": dict(total),
        "sampling": "500 deterministic draws in each of None/easy/medium/hard; seed=953000000+band_index*100000+i, sample_index=13*i+5",
    }


def target_coords(grid: list[list[int]], color: int, *, exclude_legend: bool = True) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, v in enumerate(row)
        if v == color and (not exclude_legend or (r, c) != (0, 0))
    ]


def audit_d586() -> dict:
    module, digest = load_generator("d5869f5c395e")
    mapping = {5: 2, 6: 3, 4: 4}
    per_band = {}
    total = Counter()
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        counts = Counter()
        legends = Counter()
        first_diagonal = None
        for i in range(500):
            seed = 586_000_000 + band_index * 100_000 + i
            sample_index = i * 17 + 7
            grid = module.generate(seed, sample_index, difficulty=band)
            legend = grid[0][0]
            legends[legend] += 1
            counts["samples"] += 1
            counts["legend_outside_4_5_6"] += legend not in mapping
            coords = target_coords(grid, mapping[legend])
            counts["target_pair_not_exactly_two"] += len(coords) != 2
            if len(coords) == 2:
                aligned = coords[0][0] == coords[1][0] or coords[0][1] == coords[1][1]
                counts["axis_aligned_targets"] += aligned
                counts["diagonal_targets"] += not aligned
                if not aligned and first_diagonal is None:
                    first_diagonal = {
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": band,
                        "grid": grid,
                    }
        total.update(counts)
        per_band[str(band)] = {
            **dict(counts),
            "legend_counts": {str(k): v for k, v in sorted(legends.items())},
            "first_diagonal": first_diagonal,
        }

    witness = json.loads((ROOT / "checks/audit/d5869f5c395e/input.json").read_text())
    witness_color4 = target_coords(witness, 4)
    return {
        "task_id": "d5869f5c395e",
        "generator_sha256": digest,
        "rule_hash": getattr(module, "RULE_HASH", "c33c9bf33cd3"),
        "rival": "axis_aligned_only",
        "per_band": per_band,
        "totals": dict(total),
        "canonical_counterexample": {
            "legend": witness[0][0],
            "color4_coords_zero_based": [list(x) for x in witness_color4],
            "color4_axis_aligned": (
                len(witness_color4) == 2
                and (witness_color4[0][0] == witness_color4[1][0]
                     or witness_color4[0][1] == witness_color4[1][1])
            ),
        },
        "sampling": "500 deterministic draws in each of None/easy/medium/hard; seed=586000000+band_index*100000+i, sample_index=17*i+7",
    }


def main() -> None:
    result = {
        "schema": "assigned-audit-probes-v1",
        "audits": {
            "953db766893d": audit_953(),
            "d5869f5c395e": audit_d586(),
        },
    }
    out = ROOT / "checks/audit/sample-probes.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(out)


if __name__ == "__main__":
    main()
