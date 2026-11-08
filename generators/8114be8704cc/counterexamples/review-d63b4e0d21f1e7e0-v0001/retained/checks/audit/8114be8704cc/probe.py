from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path
from typing import Any

TASK_ID = "8114be8704cc"
EXPECTED_GENERATOR_SHA256 = "8b067da41c9991c7672c206f9b9e1b563822edb410fabf94b04282e7d3b7665f"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
INPUT_PATH = HERE / "input.json"
RACKET_PATH = HERE / "racket-output.json"
OUTPUT_PATH = HERE / "probe.json"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def one_wall_interpretation(grid: list[list[int]]) -> list[list[int]]:
    """Interpret only color 1 as wall and every other nonzero as a room seed."""
    h, w = len(grid), len(grid[0])
    out = [[1 if grid[r][c] == 1 else 0 for c in range(w)] for r in range(h)]
    seen: set[tuple[int, int]] = set()
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 1 or (sr, sc) in seen:
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] != 1 and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            seeds = [(r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 1)]
            if seeds:
                min_r = min(r for r, _ in cells)
                max_r = max(r for r, _ in cells)
                min_c = min(c for _, c in cells)
                max_c = max(c for _, c in cells)
                center_r = min_r + (max_r - min_r + 1) // 2
                center_c = min_c + (max_c - min_c + 1) // 2
                out[center_r][center_c] = 8
    return out


def main() -> None:
    generator_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    if generator_sha256 != EXPECTED_GENERATOR_SHA256:
        raise AssertionError(
            f"audited source changed: {generator_sha256} != {EXPECTED_GENERATOR_SHA256}"
        )
    gen = load_module()
    grid = gen.generate(1, 0, difficulty=None)
    INPUT_PATH.write_text(json.dumps(grid, indent=2) + "\n", encoding="utf-8")
    colors = sorted({value for row in grid for value in row})
    if not {7, 9} <= set(colors):
        raise AssertionError(f"seed=1 no longer exposes colors 7 and 9: {colors}")
    validator_errors = gen.self_check(grid)
    if validator_errors:
        raise AssertionError(f"generator rejected its own witness: {validator_errors}")

    frequency: dict[str, Any] = {}
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        draws = 200
        with_wall_colors = 0
        valid = 0
        for i in range(draws):
            sample = gen.generate(811_400 + 1_000 * band_index + i, i, difficulty=band)
            sample_colors = {value for row in sample for value in row}
            with_wall_colors += int(bool(sample_colors & {7, 9}))
            valid += int(not gen.self_check(sample, difficulty=band))
        frequency[str(band)] = {
            "draws": draws,
            "with_7_or_9": with_wall_colors,
            "fraction": with_wall_colors / draws,
            "self_check_pass": valid,
        }

    racket = json.loads(RACKET_PATH.read_text(encoding="utf-8"))
    intended = racket["results"][0]["output"]
    rival = one_wall_interpretation(grid)
    differences = [
        {"row": r, "col": c, "canonical": intended[r][c], "generator_interpretation": rival[r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if intended[r][c] != rival[r][c]
    ]
    variants = {
        "palette_kind_warm": gen.generate(1, 0, palette_kind="warm") == grid,
        "palette_kind_cool": gen.generate(1, 0, palette_kind="cool") == grid,
        "anchor_corner_true": gen.generate(1, 0, anchor_corner=True) == grid,
        "asymmetry_force_true": gen.generate(1, 0, asymmetry_force=True) == grid,
    }

    payload = {
        "schema": "arcpuzzles-audit-probe-v1",
        "classification": "reproduced defect",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha256,
        "rule_hash": racket["executed_rule_hash"],
        "finding": "The generator samples 7 and 9 as interior seed colors, while the canonical Racket authority classifies 1, 7, and 9 as structural walls.",
        "seed": 1,
        "sample_index": 0,
        "difficulty": None,
        "input": grid,
        "input_colors": colors,
        "self_check": validator_errors,
        "canonical_racket_output": intended,
        "generator_domain_interpretation": {
            "description": "Only 1 is a wall; every other nonzero token seeds its 1-bounded room; seeded room centers become 8.",
            "output": rival,
        },
        "differences": differences,
        "outputs_differ": intended != rival,
        "sample_frequency": frequency,
        "secondary_contract_evidence": {
            "advertised_overrides_equal_baseline": variants,
            "note": "These controls are accepted but do not affect the witness; the authority mismatch is the primary defect.",
        },
        "racket_evidence": str(RACKET_PATH.relative_to(WORK)),
    }
    if intended == rival or not differences:
        raise AssertionError("canonical authority unexpectedly matches the generator-domain interpretation")
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "generator_sha256": generator_sha256,
                "colors": colors,
                "self_check": validator_errors,
                "differences": differences,
                "sample_frequency": frequency,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
