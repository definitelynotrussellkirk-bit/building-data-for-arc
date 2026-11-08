"""Bounded, findings-only audit of the advertised distinct-color control.

Run from the packet root:
  python3 run_with_racket.py python3 ../checks/audit/70abd9105769/reproduce.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK_ID = "70abd9105769"
BASELINE_HASH = "615c154654c2665c6b94761da8c67c515de62431f68be6e8a63e5c409fa144ce"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def nonzero_cells(grid):
    return [[r, c, value] for r, row in enumerate(grid) for c, value in enumerate(row) if value]


def inspect_domain(grid):
    """Check the stated domain independently of the generator's self_check."""
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo, cells = [start], {start}
        while todo:
            r, c = todo.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    todo.append(neighbor)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        colors = {grid[r][c] for r, c in cells}
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        components.append({
            "cells": sorted(cells),
            "colors": sorted(colors),
            "bbox": [r0, c0, r1, c1],
            "center": [(r0 + r1) // 2, (c0 + c1) // 2],
            "side": r1 - r0 + 1,
            "filled_odd_square": (
                len(colors) == 1 and r1 - r0 == c1 - c0
                and (r1 - r0 + 1) % 2 == 1
                and len(cells) == (r1 - r0 + 1) ** 2
            ),
        })
    checks = {
        "integer_color_grid_0_to_9": all(type(v) is int and 0 <= v <= 9 for row in grid for v in row),
        "rectangular": all(len(row) == width for row in grid),
        "advertised_dimensions": 5 <= height <= 18 and 5 <= width <= 18,
        "zero_background_present": any(value == 0 for row in grid for value in row),
        "advertised_object_count": 1 <= len(components) <= 6,
        "filled_odd_squares": all(component["filled_odd_square"] for component in components),
        "unique_in_bounds_centers": len({tuple(component["center"]) for component in components}) == len(components)
        and all(0 <= component["center"][0] < height and 0 <= component["center"][1] < width for component in components),
        "background_separates_objects": all(
            max(abs(r - rr), abs(c - cc)) > 1
            for i, component in enumerate(components)
            for other in components[i + 1:]
            for r, c in component["cells"]
            for rr, cc in other["cells"]
        ),
    }
    return {"checks": checks, "in_domain": all(checks.values()), "components": components}


def object_centers(grid, domain):
    output = [[0] * len(grid[0]) for _ in grid]
    for component in domain["components"]:
        r, c = component["center"]
        output[r][c] = component["colors"][0]
    return output


def rival_one_center_per_color(grid):
    """Ignore connected objects; emit the floor bbox center of each color."""
    output = [[0] * len(grid[0]) for _ in grid]
    for color in sorted({value for row in grid for value in row if value}):
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        r = (min(r for r, _ in cells) + max(r for r, _ in cells)) // 2
        c = (min(c for _, c in cells) + max(c for _, c in cells)) // 2
        output[r][c] = color
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = find_root(args.library)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = root / "generators" / TASK_ID / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash == BASELINE_HASH, "Audit is bound to the selected baseline source"
    spec = importlib.util.spec_from_file_location("odd_square_audit_generator", source)
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    seed, sample_index, difficulty = 7, 0, "hard"
    common = {"grid_h": 12, "grid_w": 13, "squares": 3}
    probes = []
    grids = []
    for axis in ("n_distinct_colors", "palette_size"):
        for value in (1, 3):
            overrides = {**common, axis: value}
            grid = generator.generate(seed, sample_index, difficulty=difficulty, **overrides)
            grids.append(grid)
            probes.append({
                "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
                "overrides": overrides,
                "observed_nonzero_colors": sorted({value for row in grid for value in row if value}),
                "observed_nonzero_color_count": len({value for row in grid for value in row if value}),
                "self_check": generator.self_check(grid, difficulty=difficulty),
            })
    generated = grids[0]
    assert all(grid == generated for grid in grids)
    generated_domain = inspect_domain(generated)
    assert generated_domain["in_domain"]
    assert len(generated_domain["components"]) == 3
    assert probes[0]["observed_nonzero_color_count"] == 3
    assert all(probe["self_check"] == [] for probe in probes)

    # Preserve square geometry and background; change only foreground colors.
    witness = [[4 if value else 0 for value in row] for row in generated]
    witness_domain = inspect_domain(witness)
    assert witness_domain["in_domain"]
    witness_self_check = generator.self_check(witness, difficulty=difficulty)
    assert witness_self_check == []
    generated_rival = rival_one_center_per_color(generated)
    witness_rival = rival_one_center_per_color(witness)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert pairs

    applied = Catalog(root).apply(TASK_ID, [generated, witness, *[pair["input"] for pair in pairs]], timeout=120)
    assert applied["reference"] == "canonical"
    assert applied["generator_sha256"] == source_hash
    assert applied["rule_hash_matches_catalog"]
    generated_reference = applied["results"][0]["output"]
    witness_reference = applied["results"][1]["output"]
    assert generated_reference == object_centers(generated, generated_domain)
    assert witness_reference == object_centers(witness, witness_domain)
    assert generated_reference == generated_rival
    assert witness_reference != witness_rival
    canonical_checks = []
    for pair, result in zip(pairs, applied["results"][2:], strict=True):
        check = {
            "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
            "self_check": generator.self_check(pair["input"]),
            "racket_matches_canonical": result["output"] == pair["output"],
            "rival_matches_canonical": rival_one_center_per_color(pair["input"]) == pair["output"],
        }
        assert check["racket_matches_canonical"] and check["rival_matches_canonical"]
        canonical_checks.append(check)

    authority = root / "shared/data/base/solutions/banks/f716aa11d181/easy_119_keep_centers_of_odd_squares__70abd9105769.json"
    evidence = {
        "task_id": TASK_ID, "generator_version": generator.VERSION,
        "generator_sha256": source_hash,
        "generator_sha256_after": hashlib.sha256(source.read_bytes()).hexdigest(),
        "authority_file": str(authority.relative_to(root)),
        "authority_file_sha256": hashlib.sha256(authority.read_bytes()).hexdigest(),
        "executed_rule_hash": applied["executed_rule_hash"],
        "catalog_rule_hash": applied["catalog_rule_hash"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "axes_under_test": {axis: generator.AXES[axis] for axis in ("squares", "palette_size", "n_distinct_colors")},
        "override_probes": probes,
        "all_four_override_inputs_identical": True,
        "generated_domain": generated_domain,
        "generated_reference_nonzero_cells": nonzero_cells(generated_reference),
        "generated_rival_matches_reference": generated_rival == generated_reference,
        "witness_origin": "Recolor every nonzero cell of the retained generated input to color 4; preserve all geometry and background.",
        "witness_is_unmodified_generator_draw": False,
        "witness_self_check": witness_self_check,
        "witness_domain": witness_domain,
        "witness_reference_nonzero_cells": nonzero_cells(witness_reference),
        "witness_rival_nonzero_cells": nonzero_cells(witness_rival),
        "witness_rival_matches_reference": witness_rival == witness_reference,
        "canonical_checks": canonical_checks,
    }
    assert evidence["generator_sha256_after"] == source_hash
    for filename, value in (
        ("generated-input.json", generated),
        ("witness-input.json", witness),
        ("generated-reference-output.json", generated_reference),
        ("generated-rival-output.json", generated_rival),
        ("racket-output.json", witness_reference),
        ("rival-output.json", witness_rival),
        ("reference-results.json", applied),
        ("evidence.json", evidence),
    ):
        write_json(out / filename, value)
    print(json.dumps({
        "task_id": TASK_ID,
        "requested_distinct_colors": 1,
        "observed_distinct_colors": probes[0]["observed_nonzero_color_count"],
        "all_four_override_inputs_identical": True,
        "witness_self_check": witness_self_check,
        "witness_in_domain": witness_domain["in_domain"],
        "witness_reference_nonzero_cells": evidence["witness_reference_nonzero_cells"],
        "witness_rival_nonzero_cells": evidence["witness_rival_nonzero_cells"],
        "canonical_pairs_checked": len(pairs),
        "canonical_pairs_agreeing_with_rival": sum(item["rival_matches_canonical"] for item in canonical_checks),
        "generator_sha256": source_hash,
        "executed_rule_hash": applied["executed_rule_hash"],
        "evidence_directory": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
