#!/usr/bin/env python3
"""Audit probe for 61f255726e2e, including a strict-validator counterexample."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK = "61f255726e2e"
GENERATOR = Path("generators") / TASK / "generator.py"
OUT = Path("../checks/audit") / TASK
BANDS = ("easy", "medium", "hard")
SAMPLES_PER_BAND = 150


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            result.append((color, cells, (min(rs), min(cs), max(rs), max(cs))))
    return result


def independent_outline(grid):
    out = [[0 for _ in row] for row in grid]
    for color, _cells, (r1, c1, r2, c2) in components(grid):
        for c in range(c1, c2 + 1):
            out[r1][c] = color
            out[r2][c] = color
        for r in range(r1, r2 + 1):
            out[r][c1] = color
            out[r][c2] = color
    return out


def has_interior_blob(grid):
    for _color, cells, (r1, c1, r2, c2) in components(grid):
        if r2 - r1 + 1 >= 3 and c2 - c1 + 1 >= 3:
            if any(r1 < r < r2 and c1 < c < c2 for r, c in cells):
                return True
    return False


def main() -> None:
    module = load_generator()
    OUT.mkdir(parents=True, exist_ok=True)

    generated_failures = []
    sampled = 0
    for band in BANDS:
        for sample_index in range(SAMPLES_PER_BAND):
            grid = module.generate(20261011, sample_index, difficulty=band)
            sampled += 1
            errors = module.self_check(grid)
            oracle = independent_outline(grid)
            if errors:
                generated_failures.append({"band": band, "sample_index": sample_index, "kind": "self_check", "errors": errors})
            if not has_interior_blob(grid):
                generated_failures.append({"band": band, "sample_index": sample_index, "kind": "missing_interior_witness"})
            if module._draw(grid, hollow=True, keep_input=False) != oracle:
                generated_failures.append({"band": band, "sample_index": sample_index, "kind": "oracle_mismatch"})
            if module._fill_bbox(grid) == oracle:
                generated_failures.append({"band": band, "sample_index": sample_index, "kind": "fill_rival_not_refuted"})
            if module._outline_over_input(grid) == oracle:
                generated_failures.append({"band": band, "sample_index": sample_index, "kind": "keep_input_rival_not_refuted"})

    override_failures = []
    override_cases = 0
    for band in BANDS:
        for h in (7, 14):
            for w in (9, 16):
                for n_hollow in (1, 2):
                    for n_thin in (0, 3):
                        override_cases += 1
                        try:
                            grid = module.generate(
                                7, override_cases, difficulty=band,
                                grid_h=h, grid_w=w,
                                n_hollow=n_hollow, n_thin=n_thin,
                            )
                            observed = module.observe_overrides(grid)
                            wanted = {
                                "grid_h": h,
                                "grid_w": w,
                                "n_hollow": n_hollow,
                                "n_thin": n_thin,
                            }
                            if observed != wanted:
                                override_failures.append({"band": band, "wanted": wanted, "observed": observed})
                        except Exception as exc:  # noqa: BLE001 - capture exact audit failure
                            override_failures.append({
                                "band": band,
                                "wanted": {"grid_h": h, "grid_w": w, "n_hollow": n_hollow, "n_thin": n_thin},
                                "exception": f"{type(exc).__name__}: {exc}",
                            })

    # Outside both the generated axis domain and every canonical profile, with
    # no required hollow/interior witness.  The strict validator nevertheless
    # accepts it as a lawful canonical-like instance.
    counterexample = [[0] * 20 for _ in range(20)]
    counterexample[0][0] = 1
    counterexample[1][0] = 1
    counterexample[1][1] = 1
    self_errors = module.self_check(counterexample)
    strict_errors = module.strict_canonical_like(counterexample)
    counter_oracle = independent_outline(counterexample)

    summary = {
        "schema": "arc-audit-reproducer-v1",
        "task_id": TASK,
        "generator_path": str(GENERATOR),
        "generator_sha256": sha256(GENERATOR),
        "declared_rule_hash": module.RULE_HASH,
        "version": module.VERSION,
        "generated_probe": {
            "seed": 20261011,
            "bands": list(BANDS),
            "samples_per_band": SAMPLES_PER_BAND,
            "denominator": sampled,
            "failures": generated_failures,
        },
        "override_corner_probe": {
            "seed": 7,
            "denominator": override_cases,
            "failures": override_failures,
        },
        "counterexample": {
            "dimensions": [20, 20],
            "object_count": 1,
            "has_interior_blob": has_interior_blob(counterexample),
            "self_check": self_errors,
            "strict_canonical_like": strict_errors,
            "documented_domain_violations": [
                "grid_h=20 is outside AXES grid_h 7..14",
                "grid_w=20 is outside AXES grid_w 9..16",
                "no hollow >=3x3 object with an interior blob cell",
                "dimensions match no canonical profile",
            ],
            "accepted_by_strict_validator": strict_errors == [],
            "input_path": "checks/audit/61f255726e2e/input.json",
            "oracle_path": "checks/audit/61f255726e2e/independent_expected.json",
        },
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/61f255726e2e/reproduce.py",
        ],
        "effective_cwd": "WORK/repo",
    }
    if generated_failures or override_failures:
        raise AssertionError(summary)
    if self_errors or strict_errors:
        raise AssertionError("counterexample unexpectedly rejected")

    (OUT / "probe.json").write_text(json.dumps(summary, indent=2) + "\n")
    (OUT / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (OUT / "independent_expected.json").write_text(json.dumps(counter_oracle, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
