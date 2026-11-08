#!/usr/bin/env python3
"""Replay the independent review's finite D4/corner-preservation check.

From the packet root:
  WORK/.venv/bin/python review.py run python3 \
    ../checks/additional-ticket-001/corner_geometry_check.py \
    --out ../checks/additional-ticket-001/corner-geometry.json

The source defaults to the proposal alongside this script. This is a focused
Python geometry check; it performs no Racket execution or owner integration.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys


TASK_ID = "36343a80035c"
PROFILES = (
    "unit_plus_tall2",
    "wide2_plus_tall3",
    "unit_plus_tall4",
    "square4_plus_tall2",
)
SHAPE_INDICES = (0, 1, 2)
D4_CODES = tuple(range(8))
EMBEDDINGS = (
    (9, 9, 0, 0),
    (9, 14, 0, 0),
    (9, 14, 0, 5),
    (14, 9, 0, 0),
    (14, 9, 5, 0),
    (14, 14, 0, 0),
    (14, 14, 5, 5),
    (14, 14, 2, 3),
)
COLORS = (3, 5, 7)
WALL_COLOR = 3
CORNER_RNG_SEED = 77


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outside(grid):
    """Independent border-first flood; no generator traversal helpers."""
    height, width = len(grid), len(grid[0])
    seen = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] == 0 and (r in (0, height - 1) or c in (0, width - 1))
    }
    pending = deque(seen)
    while pending:
        r, c = pending.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < height and 0 <= nc < width
                    and grid[nr][nc] == 0 and (nr, nc) not in seen):
                seen.add((nr, nc))
                pending.append((nr, nc))
    return seen


def holes(grid):
    exterior = outside(grid)
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 0 and (r, c) not in exterior}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    script = Path(__file__).resolve()
    source = (args.source or script.parent / "proposal" / "generators"
              / TASK_ID / "generator.py").resolve(strict=True)
    candidate_hash = sha256(source)
    script_hash = sha256(script)
    spec = importlib.util.spec_from_file_location("corner_geometry_candidate", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    failures = []
    attempted = mutations = no_ops = 0
    if tuple(gen.SCENE_PROFILES) != PROFILES:
        failures.append({"check": "profile_factor_identity",
                         "observed": list(gen.SCENE_PROFILES)})
    for profile in PROFILES:
        for shape in SHAPE_INDICES:
            base = gen._base_scene(profile, COLORS, shape)
            for code in D4_CODES:
                motif = gen._dihedral(base, code)
                for height, width, top, left in EMBEDDINGS:
                    attempted += 1
                    case = {"profile": profile, "shape_index": shape, "D4_code": code,
                            "height": height, "width": width, "top": top, "left": left}
                    try:
                        grid = [[0] * width for _ in range(height)]
                        for r, row in enumerate(motif):
                            grid[top + r][left:left + 9] = row
                        before = [row[:] for row in grid]
                        before_holes = holes(grid)
                        gen._ensure_small_border_region(
                            grid, WALL_COLOR, random.Random(CORNER_RNG_SEED))
                        mutations += grid != before
                        no_ops += grid == before
                        after_holes = holes(grid)
                        if after_holes != before_holes:
                            failures.append({"case": case, "check": "enclosed_cells_preserved",
                                             "added": sorted(after_holes - before_holes),
                                             "removed": sorted(before_holes - after_holes)})
                        if not gen._has_small_border_region(grid):
                            failures.append({"case": case, "check": "small_border_region"})
                        observed = gen.observe_overrides(grid)
                        if observed != {"scene_profile": profile, "palette_kind": "canonical"}:
                            failures.append({"case": case, "check": "exact_axes",
                                             "observed": observed})
                    except Exception as error:
                        failures.append({"case": case, "check": "execution",
                                         "error": f"{type(error).__name__}: {error}"})
    if sha256(source) != candidate_hash or sha256(script) != script_hash:
        failures.append({"check": "source_bytes_stable_during_check"})
    receipt = {
        "schema": "focused-corner-geometry-check-v1",
        "task_id": TASK_ID,
        "candidate_sha256": candidate_hash,
        "candidate_version": gen.VERSION,
        "script_sha256": script_hash,
        "python_version": sys.version.split()[0],
        "factors": {
            "profiles": PROFILES, "shape_indices": SHAPE_INDICES, "D4_codes": D4_CODES,
            "embeddings": [dict(zip(("height", "width", "top", "left"), case))
                           for case in EMBEDDINGS],
            "colors": COLORS, "wall_color": WALL_COLOR,
            "corner_rng_seed_reinitialized_per_case": CORNER_RNG_SEED,
        },
        "counts": {"expected_cases": 768, "attempted_cases": attempted,
                   "mutations": mutations, "no_ops": no_ops, "failures": len(failures)},
        "independent_oracle": (
            "This script seeds a 4-neighbor flood from every physical-border zero, "
            "without invoking generator traversal helpers. Non-reached zeros form "
            "the enclosed-cell sets compared before/after the helper. Small-border "
            "presence and exact axes are separately checked with candidate observers."
        ),
        "failures": failures,
        "status": "passed" if not failures else "failed",
        "scope": (
            "Finite Python geometry replay of 4 profiles x 3 shape indices x 8 D4 "
            "codes x 8 embedding cases, one canonical palette and one corner RNG "
            "seed. No claim of exhaustive padding/randomness/palette coverage; "
            "no Racket execution, owner acceptance, integration or training admission."
        ),
    }
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: receipt[key] for key in (
        "status", "candidate_sha256", "script_sha256", "counts")}, sort_keys=True))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
