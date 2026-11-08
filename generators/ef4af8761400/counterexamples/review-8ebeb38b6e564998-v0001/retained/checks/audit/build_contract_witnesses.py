#!/usr/bin/env python3
"""Build source-bound, findings-only evidence for the assigned audit targets.

This script deliberately does not edit either audited generator. It loads the
exact source selected from the packet repository, checks canonical examples,
probes declared axes, and writes compact JSON receipts under WORK/checks/audit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve()
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, load_selected_generator  # noqa: E402

BANDS = ("easy", "medium", "hard")


def sha_grid(grid: list[list[int]]) -> str:
    body = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(body).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def intended_smear(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value in (0, 5):
                continue
            rr = r + 1
            while rr < h and grid[rr][c] == 0:
                out[rr][c] = value
                rr += 1
    return out


def intended_reflect(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if len(pivots) != 1:
        raise ValueError(f"expected one pivot, got {pivots}")
    pr, pc = pivots[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            for rr, cc in ((r, c), (2 * pr - r, c), (r, 2 * pc - c), (2 * pr - r, 2 * pc - c)):
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    out[rr][cc] = 1
    return out


def upper_left_only_rival(grid: list[list[int]]) -> list[list[int]]:
    """Reflect only sources strictly above and left of the first pivot."""
    out = [row[:] for row in grid]
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not pivots:
        return out
    pr, pc = pivots[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1 or not (r < pr and c < pc):
                continue
            for rr, cc in ((r, c), (2 * pr - r, c), (r, 2 * pc - c), (2 * pr - r, 2 * pc - c)):
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    out[rr][cc] = 1
    return out


def pivot_and_sources(grid: list[list[int]]) -> tuple[tuple[int, int] | None, list[tuple[int, int]]]:
    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    return (pivots[0] if len(pivots) == 1 else None), sources


def capture_call(fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = fn()
    except Exception as exc:  # audit receipt: record exact public behavior
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"accepted": True, "error": None, "value": value}


def build_smear_report() -> dict[str, Any]:
    task = "69dbf44065e2"
    gen, source, source_sha = load_selected_generator(task, root=REPO)
    pairs = canonical_pairs(task, root=REPO, labeled_only=True)
    canonical_rows = []
    for pair in pairs:
        expected = pair["output"]
        calculated = intended_smear(pair["input"])
        canonical_rows.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "intended_matches_label": calculated == expected,
            "self_check_errors": gen.self_check(pair["input"]),
        })

    seed, index, band = 314159, 2, "medium"
    base = gen.generate(seed, index, difficulty=band)
    probes = {}
    for axis, values in {
        "palette_size": (1, 9),
        "n_distinct_colors": (1, 9),
    }.items():
        low = gen.generate(seed, index, difficulty=band, **{axis: values[0]})
        high = gen.generate(seed, index, difficulty=band, **{axis: values[1]})
        probes[axis] = {
            "requests": [values[0], values[1]],
            "low_output_sha256": sha_grid(low),
            "high_output_sha256": sha_grid(high),
            "outputs_identical": low == high,
            "identical_to_unoverridden": low == base == high,
        }

    invalid_difficulty = capture_call(lambda: gen.generate(seed, index, difficulty="not-a-band"))
    if invalid_difficulty.get("accepted"):
        value = invalid_difficulty.pop("value")
        invalid_difficulty["output_sha256"] = sha_grid(value)
        invalid_difficulty["same_as_default_else_branch"] = value == gen.generate(seed, index, difficulty=None)

    all_zero = [[0] * 8 for _ in range(8)]
    degenerate = gen.generate(seed, index, difficulty=band, texture="no_color_cells")
    report = {
        "schema": "arcpuzzles-assigned-audit-contract-witness-v1",
        "task_id": task,
        "mode": "findings-only",
        "generator_source": str(source.relative_to(REPO)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical": canonical_rows,
        "axis_equivalence_witness": {
            "request_base": {"seed": seed, "sample_index": index, "difficulty": band},
            "base_output_sha256": sha_grid(base),
            "probes": probes,
            "finding": (
                "The advertised palette_size and n_distinct_colors overrides are accepted but do not alter "
                "the generated grid for this bound request; both endpoint requests are byte-identical."
            ),
        },
        "strict_call_witness": {
            "request": {"seed": seed, "sample_index": index, "difficulty": "not-a-band"},
            **invalid_difficulty,
        },
        "self_check_witnesses": {
            "all_zero_8x8": {"grid": all_zero, "errors": gen.self_check(all_zero)},
            "texture_no_color_cells": {"grid": degenerate, "errors": gen.self_check(degenerate)},
        },
        "finding": (
            "The generator exposes ineffective axes and accepts a malformed difficulty. Its self_check also "
            "accepts zero-trigger inputs, so it cannot enforce the stated invariant that something smears."
        ),
    }
    out_dir = WORK / "checks" / "audit" / f"{task}-contract-witness"
    write_json(out_dir / "base_input.json", base)
    write_json(out_dir / "report.json", report)
    return {"task_id": task, "report": str((out_dir / "report.json").relative_to(WORK)), "sha": source_sha}


def build_reflection_report() -> dict[str, Any]:
    task = "ef4af8761400"
    gen, source, source_sha = load_selected_generator(task, root=REPO)
    pairs = canonical_pairs(task, root=REPO, labeled_only=True)
    canonical_rows = []
    for pair in pairs:
        pivot, sources = pivot_and_sources(pair["input"])
        expected = pair["output"]
        intended = intended_reflect(pair["input"])
        rival = upper_left_only_rival(pair["input"])
        canonical_rows.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "pivot": pivot,
            "source_cells": sources,
            "all_sources_strictly_upper_left": bool(pivot) and all(r < pivot[0] and c < pivot[1] for r, c in sources),
            "intended_matches_label": intended == expected,
            "rival_matches_label": rival == expected,
            "self_check_errors": gen.self_check(pair["input"]),
        })

    sampled = []
    total = upper_left_only = rival_fits = 0
    per_band = 100
    for band_index, band in enumerate(BANDS):
        band_upper_left = band_rival_fits = 0
        for sample_index in range(per_band):
            seed = 880000 + band_index * 10000 + sample_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            pivot, sources = pivot_and_sources(grid)
            upper_left = bool(pivot) and bool(sources) and all(r < pivot[0] and c < pivot[1] for r, c in sources)
            rival_fit = upper_left_only_rival(grid) == intended_reflect(grid)
            total += 1
            upper_left_only += int(upper_left)
            rival_fits += int(rival_fit)
            band_upper_left += int(upper_left)
            band_rival_fits += int(rival_fit)
        sampled.append({
            "difficulty": band,
            "samples": per_band,
            "all_sources_upper_left": band_upper_left,
            "rival_fits_intended": band_rival_fits,
        })

    witness = [[0] * 9 for _ in range(9)]
    witness[4][4] = 2
    witness[6][6] = 1
    intended = intended_reflect(witness)
    rival = upper_left_only_rival(witness)
    racket_path = WORK / "checks" / "audit" / f"{task}-quadrant-shortcut" / "racket.json"
    racket = json.loads(racket_path.read_text(encoding="utf-8"))
    racket_output = racket["results"][0]["output"]
    out_dir = WORK / "checks" / "audit" / f"{task}-quadrant-shortcut"
    write_json(out_dir / "intended_output.json", intended)
    write_json(out_dir / "rival_output.json", rival)

    report = {
        "schema": "arcpuzzles-assigned-audit-quadrant-shortcut-v1",
        "task_id": task,
        "mode": "findings-only",
        "generator_source": str(source.relative_to(REPO)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical": canonical_rows,
        "sampling": {
            "seed_formula": "880000 + band_index*10000 + sample_index",
            "bands": sampled,
            "total_samples": total,
            "all_sources_upper_left": upper_left_only,
            "rival_fits_intended": rival_fits,
        },
        "counterexample": {
            "input_path": "input.json",
            "intended_output_path": "intended_output.json",
            "rival_output_path": "rival_output.json",
            "racket_receipt_path": "racket.json",
            "self_check_errors": gen.self_check(witness),
            "local_intended_matches_racket": intended == racket_output,
            "rival_differs_from_intended": rival != intended,
            "pivot": [4, 4],
            "source": [6, 6],
        },
        "rival": (
            "Reflect only color-1 sources strictly above and left of the pivot; leave color-1 sources in the "
            "other three quadrants unchanged."
        ),
        "finding": (
            "Every labeled canonical source and all 300 sampled production sources lie strictly upper-left of "
            "the pivot, so this quadrant-gated rival fits them all. The generator self_check accepts a lower-right "
            "source; canonical Racket reflects it to all four quadrants while the rival leaves it alone."
        ),
        "limits": [
            "The 300-example sampler is finite; the source code itself places every generated source at pr-a, pc-b with a,b>=1.",
            "The Racket receipt is the output authority for the retained counterexample; the local transform is only a cross-check.",
        ],
    }
    write_json(out_dir / "probe.json", report)
    return {"task_id": task, "report": str((out_dir / "probe.json").relative_to(WORK)), "sha": source_sha}


def main() -> int:
    rows = [build_smear_report(), build_reflection_report()]
    print(json.dumps({"reports": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
