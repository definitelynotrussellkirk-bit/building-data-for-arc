#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK = "b87adf923da8"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_b87", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def digest(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    gen = load_generator()
    seed, index, band = 17, 2, "medium"
    base = gen.generate(seed, index, difficulty=band)
    override_values = {
        "palette_kind=warm": {"palette_kind": "warm"},
        "palette_kind=cool": {"palette_kind": "cool"},
        "texture=warm": {"texture": "warm"},
        "texture=cool": {"texture": "cool"},
        "palette_size=3": {"palette_size": 3},
        "n_distinct_colors=3": {"n_distinct_colors": 3},
        "position_bias=declared": {"position_bias": "prototype_top_left_targets_scattered"},
        "density=sparse": {"density": "sparse"},
        "unknown_typo_axis=999": {"unknown_typo_axis": 999},
    }
    cases = {}
    for name, kwargs in override_values.items():
        try:
            grid = gen.generate(seed, index, difficulty=band, **kwargs)
            cases[name] = {
                "accepted": True,
                "same_as_baseline": grid == base,
                "sha256": digest(grid),
                "self_check": gen.self_check(grid, difficulty=band),
            }
        except Exception as exc:  # retained if validation exists
            cases[name] = {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}

    color_counts = Counter()
    override_color_counts = Counter()
    mismatch_count = 0
    checked = 0
    for difficulty in ("easy", "medium", "hard"):
        for s in range(100):
            grid = gen.generate(s, 0, difficulty=difficulty)
            forced = gen.generate(s, 0, difficulty=difficulty, n_distinct_colors=3)
            checked += 1
            mismatch_count += grid != forced
            colors = {v for row in grid for v in row if v not in (0, 1, 8)}
            forced_colors = {v for row in forced for v in row if v not in (0, 1, 8)}
            color_counts[len(colors)] += 1
            override_color_counts[len(forced_colors)] += 1

    report = {
        "schema": "b87adf923da8-declared-axes-audit-v1",
        "task_id": TASK,
        "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
        "version": getattr(gen, "VERSION", None),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "declared_axes": gen.AXES,
        "single_case": {
            "seed": seed,
            "sample_index": index,
            "difficulty": band,
            "baseline_sha256": digest(base),
            "overrides": cases,
        },
        "n_distinct_colors_census": {
            "cases": checked,
            "declared_default": gen.AXES["n_distinct_colors"]["default"],
            "declared_valid": gen.AXES["n_distinct_colors"]["valid"],
            "actual_distinct_prototype_color_counts": dict(sorted(color_counts.items())),
            "with_override_3_counts": dict(sorted(override_color_counts.items())),
            "baseline_vs_override_output_mismatches": mismatch_count,
        },
        "finding": (
            "Seven advertised semantic controls plus unknown keys are accepted without affecting "
            "the generated grid; n_distinct_colors=3 is contradicted by lawful outputs with only "
            "one or two prototype colors. Only grid_h/grid_w are consumed through gen_ctx, while "
            "texture handles three degenerate names out of band."
        ),
    }
    (HERE / "declared_axes_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    ignored = all(
        row.get("accepted") and row.get("same_as_baseline")
        for row in cases.values()
    )
    contradicted = any(k in color_counts for k in (1, 2)) and mismatch_count == 0
    return 0 if ignored and contradicted else 1


if __name__ == "__main__":
    raise SystemExit(main())
