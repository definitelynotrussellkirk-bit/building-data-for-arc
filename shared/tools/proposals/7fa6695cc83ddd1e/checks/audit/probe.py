#!/usr/bin/env python3
"""Fresh findings-only replay for the two immutable audit targets."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

ROOT = Path.cwd().resolve()
OUT_ROOT = ROOT.parent / "checks" / "audit"


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_generator(task_id: str):
    path = ROOT / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def one_gap_true(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            if row[c] == 0 and row[c - 1] == 6 and row[c + 1] == 6:
                out[r][c] = 6
    return out


def fill_whole_span(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        sixes = [c for c, value in enumerate(row) if value == 6]
        if len(sixes) >= 2:
            for c in range(min(sixes), max(sixes) + 1):
                if out[r][c] == 0:
                    out[r][c] = 6
    return out


def audit_palette_controls():
    task_id = "6a8c2662e37c"
    gen, path = load_generator(task_id)
    controls = {
        "palette_size": 5,
        "n_distinct_colors": 5,
        "palette_kind": "warm",
        "texture": "warm",
    }
    rows = []
    first = None
    for sample_index in range(32):
        grid = gen.generate(17, sample_index, difficulty="medium", **controls)
        cool = gen.generate(
            17,
            sample_index,
            difficulty="medium",
            **{**controls, "palette_kind": "cool", "texture": "cool"},
        )
        colors = sorted({value for row in grid for value in row})
        row = {
            "seed": 17,
            "sample_index": sample_index,
            "difficulty": "medium",
            "overrides": controls,
            "observed_colors": colors,
            "observed_n_distinct_colors": len(colors),
            "self_check_errors": gen.self_check(grid),
            "warm_equals_cool": grid == cool,
            "input_sha256": digest(grid),
        }
        rows.append(row)
        if first is None and len(colors) != 5:
            first = {**row, "input": grid, "cool_input": cool}
    assert first is not None
    out = {
        "schema": "audit_palette_controls/1",
        "task_id": task_id,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "scope": "seed 17, medium, sample_index 0..31",
        "requested_contract": controls,
        "mismatch_count": sum(row["observed_n_distinct_colors"] != 5 for row in rows),
        "warm_cool_identical_count": sum(row["warm_equals_cool"] for row in rows),
        "draw_count": len(rows),
        "first_counterexample": first,
        "rows": rows,
    }
    directory = OUT_ROOT / task_id
    (directory / "input.json").write_text(json.dumps(first["input"], indent=2) + "\n")
    (directory / "palette_probe.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def audit_whole_span_shortcut():
    task_id = "26872d42d87a"
    gen, path = load_generator(task_id)
    pairs = canonical_pairs(task_id, root=ROOT, labeled_only=True)
    per_band = {}
    for band in ("easy", "medium", "hard"):
        generated = 0
        validator_passes = 0
        rival_matches = 0
        unique = set()
        errors = []
        for seed in range(100):
            try:
                grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            except Exception as exc:  # evidence, not concealment
                errors.append(f"seed={seed}: {type(exc).__name__}: {exc}")
                continue
            generated += 1
            validator_passes += not gen.self_check(grid, difficulty=band)
            rival_matches += fill_whole_span(grid) == one_gap_true(grid)
            unique.add(digest(grid))
        per_band[band] = {
            "generated": generated,
            "validator_passes": validator_passes,
            "rival_matches_true_mirror": rival_matches,
            "unique_inputs": len(unique),
            "generation_errors": errors,
        }

    grid = [
        [5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 6, 0, 6, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 6, 0, 0, 6, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 6, 0, 6, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
    ]
    true_output = one_gap_true(grid)
    rival_output = fill_whole_span(grid)
    out = {
        "schema": "audit_whole_span_shortcut/1",
        "task_id": task_id,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rival_name": "fill_between_leftmost_and_rightmost_6",
        "canonical_pairs": len(pairs),
        "true_mirror_canonical_fits": sum(one_gap_true(p["input"]) == p["output"] for p in pairs),
        "rival_canonical_fits": sum(fill_whole_span(p["input"]) == p["output"] for p in pairs),
        "per_band": per_band,
        "counterexample": {
            "input": grid,
            "input_sha256": digest(grid),
            "self_check_errors": gen.self_check(grid),
            "ordinary_sampler_member": False,
            "true_mirror_output": true_output,
            "rival_output": rival_output,
            "rival_differs": rival_output != true_output,
        },
    }
    directory = OUT_ROOT / task_id
    (directory / "input.json").write_text(json.dumps(grid, indent=2) + "\n")
    (directory / "rival_output.json").write_text(json.dumps(rival_output, indent=2) + "\n")
    (directory / "shortcut_probe.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    palette = audit_palette_controls()
    shortcut = audit_whole_span_shortcut()
    summary = {
        "6a8c2662e37c": {
            "generator_sha256": palette["generator_sha256"],
            "mismatches": f'{palette["mismatch_count"]}/{palette["draw_count"]}',
            "warm_cool_identical": f'{palette["warm_cool_identical_count"]}/{palette["draw_count"]}',
        },
        "26872d42d87a": {
            "generator_sha256": shortcut["generator_sha256"],
            "rival_canonical_fits": f'{shortcut["rival_canonical_fits"]}/{shortcut["canonical_pairs"]}',
            "per_band": {k: v["rival_matches_true_mirror"] for k, v in shortcut["per_band"].items()},
            "counterexample_validator": shortcut["counterexample"]["self_check_errors"],
        },
    }
    print(json.dumps(summary, sort_keys=True))
