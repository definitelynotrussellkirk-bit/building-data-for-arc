"""Bounded canonical label/validator probe for the largest supported frame.

Run from this packet's repo through review.py run. The output directory must
be new. This is a four-input geometry probe, not a generator qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


TASK_ID = "bedcbc1cb6fb"
from reviewer_support import find_root

ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]

from arcpuzzles import Catalog
from arcpuzzles.runtime import apply_rule


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry(grid):
    blues = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 1]
    r1, r2 = min(r for r, _ in blues), max(r for r, _ in blues)
    c1, c2 = min(c for _, c in blues), max(c for _, c in blues)
    markers = [grid[k][k] for k in range(min(len(grid), len(grid[0])))
               if grid[k][k] not in (0, 1)]
    return (r1, c1, r2, c2), markers


def geometric_expected(grid):
    """Use distance to the frame, independently of nested fill loops."""
    (r1, c1, r2, c2), markers = geometry(grid)
    expected = [row[:] for row in grid]
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            depth = min(r - r1, c - c1, r2 - r, c2 - c)
            expected[r][c] = markers[min(depth - 1, len(markers) - 1)]
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)

    spec = importlib.util.spec_from_file_location("bedcbc_boundary_generator", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(generator)

    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in canonical_path.read_text().splitlines()]
    selected = [row for row in rows if row.get("task_id") == TASK_ID]
    programs = {row["program_solution"] for row in selected}
    assert len(programs) == 1, "canonical rule must be unambiguous"
    program = next(iter(programs))
    normalized_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()
    assert normalized_hash[:12] == generator.RULE_HASH

    profile = "five_markers_20x20"
    variants = ("canonical", "down_one", "right_one", "down_right")
    inputs = [generator.generate(20261024, index, difficulty="hard",
                                 scene_profile=profile, layout_variant=variant)
              for index, variant in enumerate(variants)]
    applied = apply_rule(Catalog(ROOT), TASK_ID, inputs, reference="canonical",
                         allow_unapproved=True, check_generator_domain=True,
                         timeout=60)
    (out / "racket-application.json").write_text(json.dumps(applied) + "\n")

    checks = []
    failures = []
    for variant, grid, result in zip(variants, inputs, applied["results"], strict=True):
        bbox, markers = geometry(grid)
        r1, c1, r2, c2 = bbox
        output = result["output"]
        interior_counts = Counter(output[r][c] for r in range(r1 + 1, r2)
                                  for c in range(c1 + 1, c2)) if output else Counter()
        assertions = {
            "requested_axes_observed": generator.observe_overrides(grid) == {
                "scene_profile": profile, "layout_variant": variant},
            "self_check_accepts": generator.self_check(grid) == [],
            "worker_domain_accepts": result["generator_domain"]["status"] == "valid",
            "racket_valid_output": result["valid_output"] is True,
            "racket_matches_geometric_expected": output == geometric_expected(grid),
            "mirror_matches_racket": output == generator.rule_mirror(grid),
            "all_five_markers_visible": set(interior_counts) == set(markers),
            "innermost_marker_fills_3x4_center": interior_counts[markers[-1]] == 12,
            "right_boundary_matches_requested_offset": (c2 == len(grid[0]) - 1)
                == (variant in ("right_one", "down_right")),
        }
        checks.append({"sample_index": variants.index(variant), "variant": variant,
                       "frame_bbox": bbox, "marker_colors": markers,
                       "interior_color_counts": dict(interior_counts),
                       "assertions": assertions})
        failures.extend(f"{variant}: {name}" for name, passed in assertions.items() if not passed)

    edge_grid = inputs[-1]
    r1, c1, r2, c2 = geometry(edge_grid)[0]
    mutations = []
    for name, r, c, value in (
        ("missing_right_boundary_cell", (r1 + r2) // 2, c2, 0),
        ("extra_blue_inside_frame", r1 + 1, c1 + 1, 1),
    ):
        mutant = [row[:] for row in edge_grid]
        before = mutant[r][c]
        mutant[r][c] = value
        errors = generator.self_check(mutant)
        observed = generator.observe_overrides(mutant)
        passed = bool(errors) and observed == {}
        mutations.append({"name": name, "base_variant": "down_right",
                          "cell": [r, c], "before": before, "after": value,
                          "self_check_errors": errors, "observed": observed,
                          "rejected": passed})
        if not passed:
            failures.append(f"mutation not rejected: {name}")

    if not applied["rule_hash_matches_catalog"]:
        failures.append("executed canonical rule hash differs from catalog")
    if applied["generator_sha256"] != sha256(SOURCE):
        failures.append("executed generator source differs from inspected source")

    summary = {
        "schema": "bedcbc1cb6fb-bounded-boundary-probe-v1",
        "task_id": TASK_ID,
        "outcome": "no_finding" if not failures else "finding",
        "focus": "largest nonsquare frame, legal translations, and malformed boundary rejection",
        "generator_sha256": sha256(SOURCE),
        "probe_sha256": sha256(Path(__file__)),
        "canonical_path": str(canonical_path.relative_to(ROOT)),
        "canonical_row_count": len(selected),
        "canonical_rule_normalized_sha256": normalized_hash,
        "canonical_rule_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "executed_rule_hash": applied["executed_rule_hash"],
        "seed": 20261024,
        "difficulty": "hard",
        "scene_profile": profile,
        "lawful_racket_cases": len(checks),
        "validator_mutations": len(mutations),
        "checks": checks,
        "mutations": mutations,
        "failures": failures,
        "limits": [
            "Only the five-marker 20x20 profile and its four legal offsets were executed.",
            "No full batteries, distribution census, or parametric work was performed.",
            "Existing row-major-vs-diagonal teaching limitation is outside this probe and remains open.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: summary[key] for key in
                      ("task_id", "outcome", "generator_sha256", "executed_rule_hash",
                       "lawful_racket_cases", "validator_mutations", "failures")}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
