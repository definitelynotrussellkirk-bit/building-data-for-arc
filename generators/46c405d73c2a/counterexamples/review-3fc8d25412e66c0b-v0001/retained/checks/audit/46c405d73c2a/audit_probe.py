#!/usr/bin/env python3
"""Read-only semantic/contract audit for generator 46c405d73c2a."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "46c405d73c2a"
ROOT = Path.cwd().resolve()
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def marker_positions(grid):
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                if value in positions:
                    raise ValueError(f"duplicate marker color {value}")
                positions[value] = (r, c)
    return positions


def authority_mirror(grid):
    positions = marker_positions(grid)
    colors = sorted(positions)
    out = []
    for row_index, row_color in enumerate(colors):
        row = []
        rr, rc = positions[row_color]
        for col_index, col_color in enumerate(colors):
            cr, cc = positions[col_color]
            if row_index == col_index:
                row.append(5)
            elif max(abs(rr - cr), abs(rc - cc)) <= 2:
                row.append(8)
            else:
                row.append(0)
        out.append(row)
    return out


def horizontal_only_rival(grid):
    """Canonical-fitting shortcut: only recognize horizontal close pairs."""
    positions = marker_positions(grid)
    colors = sorted(positions)
    out = []
    for row_index, row_color in enumerate(colors):
        row = []
        rr, rc = positions[row_color]
        for col_index, col_color in enumerate(colors):
            cr, cc = positions[col_color]
            if row_index == col_index:
                row.append(5)
            elif rr == cr and abs(rc - cc) <= 2:
                row.append(8)
            else:
                row.append(0)
        out.append(row)
    return out


def frozen(value):
    return tuple(tuple(row) for row in value)


def call_record(fn, *args, **kwargs):
    try:
        value = fn(*args, **kwargs)
    except Exception as exc:  # exact exception is evidence
        return {
            "ok": False,
            "exception": type(exc).__name__,
            "message": str(exc),
        }
    return {"ok": True, "value": value}


def main() -> int:
    sys.path.insert(0, str(ROOT / "shared" / "runtime"))
    from reviewer_support import canonical_pairs
    from arcpuzzles import Catalog

    gen = load_generator()
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_mirror_matches = [authority_mirror(pair["input"]) == pair["output"] for pair in canonical]
    canonical_shortcut_matches = [horizontal_only_rival(pair["input"]) == pair["output"] for pair in canonical]

    # This is an actual production-shaped instance: run_one uses one seed and
    # sequential sample indices for 3 demonstrations plus one query.
    catalog = Catalog(ROOT)
    lesson, = catalog.generate(
        TASK_ID,
        count=1,
        seed=1000,
        sample_index=3,
        n_train=3,
        n_test=1,
        difficulty="easy",
        allow_unapproved=True,
        timeout=180,
    )
    pairs = lesson["train"] + lesson["test"]
    authority_outputs = [pair["output"] for pair in pairs]
    mirror_outputs = [authority_mirror(pair["input"]) for pair in pairs]
    rival_outputs = [horizontal_only_rival(pair["input"]) for pair in pairs]
    demo_fits = [rival_outputs[index] == authority_outputs[index] for index in range(3)]
    query_refuted = rival_outputs[3] != authority_outputs[3]

    # Independent batched Racket parity receipt for the exact witness.
    apply_receipt = catalog.apply(
        TASK_ID,
        [pair["input"] for pair in pairs],
        reference="canonical",
        timeout=180,
    )
    apply_outputs = [entry["output"] for entry in apply_receipt["results"]]

    # Count how often the same canonical-fitting rival survives all three demos
    # but fails on the fourth pair in consecutive 3+1 windows.
    window_stats = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        windows = 300
        ambiguous = 0
        all_demo_fit = 0
        query_refutations = 0
        all_diagonal = 0
        for start in range(windows):
            seed = 20_000 + band_index * 10_000 + start
            grids = [gen.generate(seed, start * 4 + offset, difficulty=band) for offset in range(4)]
            fits = [horizontal_only_rival(grid) == authority_mirror(grid) for grid in grids]
            if all(fits[:3]):
                all_demo_fit += 1
            if not fits[3]:
                query_refutations += 1
            if all(fits[:3]) and not fits[3]:
                ambiguous += 1
            for grid in grids:
                out = authority_mirror(grid)
                if all(out[r][c] == 0 for r in range(len(out)) for c in range(len(out)) if r != c):
                    all_diagonal += 1
        window_stats[band] = {
            "windows": windows,
            "pairs": windows * 4,
            "three_demos_fit_shortcut": all_demo_fit,
            "query_refutes_shortcut": query_refutations,
            "ambiguous_3_demo_1_query_windows": ambiguous,
            "all_zero_off_diagonal_pairs": all_diagonal,
        }

    base = gen.generate(1, 2)
    helpful_palette_outputs = {
        value: frozen(gen.generate(1, 2, palette_kind=value)) == frozen(base)
        for value in gen.PALETTE_KINDS
    }
    helpful_texture_outputs = {
        value: frozen(gen.generate(1, 2, texture=value)) == frozen(base)
        for value in gen.HELPFUL_TEXTURES
    }
    control_contract = {
        "globally_valid_n_markers_7_under_easy": call_record(
            gen.generate, 1, 2, difficulty="easy", n_markers=7
        ),
        "unknown_override_bogus": call_record(gen.generate, 1, 2, bogus=1),
        "invalid_palette_kind": call_record(gen.generate, 1, 2, palette_kind="not-valid"),
        "declared_inert_controls": {
            "palette_kind_same_as_base": helpful_palette_outputs,
            "texture_same_as_base": helpful_texture_outputs,
            "palette_size_7_same_as_base": frozen(gen.generate(1, 2, palette_size=7)) == frozen(base),
            "n_distinct_colors_7_same_as_base": frozen(gen.generate(1, 2, n_distinct_colors=7)) == frozen(base),
            "position_bias_same_as_base": frozen(gen.generate(1, 2, position_bias="varied_distance")) == frozen(base),
            "density_same_as_base": frozen(gen.generate(1, 2, density="sparse")) == frozen(base),
        },
    }
    degenerate_checks = {
        name: gen.self_check(gen.generate(1, 2, texture=name))
        for name in gen.DEGENERATE_TEXTURES
    }

    exact_lesson = {
        "seed": lesson["seed"],
        "requested_sample_index": lesson["sample_index"],
        "accepted_indices": lesson["sample_indices"],
        "difficulty": "easy",
        "demo_shortcut_fits": demo_fits,
        "query_shortcut_refuted": query_refuted,
        "pairs": [
            {
                "role": "demo" if index < 3 else "query",
                "sample_index": lesson["sample_indices"][index],
                "markers": [
                    {"color": color, "row": rc[0], "col": rc[1]}
                    for color, rc in sorted(marker_positions(pair["input"]).items())
                ],
                "input": pair["input"],
                "authority_output": pair["output"],
                "horizontal_only_output": rival_outputs[index],
                "shortcut_fits": rival_outputs[index] == pair["output"],
            }
            for index, pair in enumerate(pairs)
        ],
    }

    problems = []
    if not all(canonical_mirror_matches):
        problems.append("independent mirror disagrees with a canonical pair")
    if not all(canonical_shortcut_matches):
        problems.append("horizontal-only rival does not fit every canonical pair")
    if not all(demo_fits) or not query_refuted:
        problems.append("pinned 3-demo/query shortcut witness no longer reproduces")
    if authority_outputs != mirror_outputs or authority_outputs != apply_outputs:
        problems.append("Racket authority does not match the independent mirror on witness")
    if not apply_receipt.get("rule_hash_matches_catalog"):
        problems.append("canonical rule hash receipt did not match the catalog")

    report = {
        "schema": "46c405d73c2a-readonly-audit/1",
        "status": "pass" if not problems else "probe_error",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_rule_hash": apply_receipt.get("executed_rule_hash"),
        "canonical": {
            "pairs": len(canonical),
            "independent_mirror_matches": canonical_mirror_matches,
            "horizontal_only_shortcut_fits": canonical_shortcut_matches,
        },
        "exact_ambiguous_lesson": exact_lesson,
        "window_census": window_stats,
        "control_contract": control_contract,
        "degenerate_self_check_findings": degenerate_checks,
        "racket_parity": {
            "pairs": len(pairs),
            "rule_hash_matches_catalog": apply_receipt.get("rule_hash_matches_catalog"),
            "all_outputs_match_mirror": authority_outputs == mirror_outputs == apply_outputs,
        },
        "problems": problems,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
