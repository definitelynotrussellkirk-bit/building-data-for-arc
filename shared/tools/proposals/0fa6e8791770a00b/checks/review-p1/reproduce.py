#!/usr/bin/env python3
"""Reproduce a source-bound historical teaching defect using public Racket labels.

Exit 1 means the retained ambiguity was reproduced, not that current generator
bytes were tested. Exit 2 means the evidence or reference execution failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

HERE = Path(__file__).resolve().parent
TASK_ID = "144c5d002191"
PRIOR_SHA256 = "a3e21d4ea25700280832635bb9af391686399b3b7926cc8944f16d7ee6ae4d14"
RULE_HASH = "c3118b3e9e62"
RULE_TEXT_SHA256 = "97956adc1e0ffa6b5119dd32ae21c67264b86a3119f2cbdc179e98c6ed31f232"
RIVAL_NAME = "row_then_descending_color_marker_order"


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def components(grid):
    """Independent monochromatic four-neighbor flood fill in row-major order."""
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            pending, cells = [(r, c)], []
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and grid[nr][nc] == color and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def rival(grid):
    """Canonical stamping except row ties are broken by descending color."""
    parts = components(grid)
    _, cells = max((part for part in parts if len(part[1]) > 1),
                   key=lambda part: len(part[1]))
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    shape = [(r-r0, c-c0) for r, c in cells]
    markers = sorted((part for part in parts if len(part[1]) == 1),
                     key=lambda part: (part[1][0][0], -part[0], part[1][0][1]))
    out = [[0] * len(grid[0]) for _ in grid]
    for color, [(r, c)] in markers:
        for dr, dc in shape:
            if 0 <= r+dr < len(grid) and 0 <= c+dc < len(grid[0]):
                out[r+dr][c+dc] = color
    return out


def load_prior(root):
    """Execute only captured bytes, using dependencies from this local tree."""
    source = HERE / "prior_generator.py"
    body = source.read_bytes()
    assert hashlib.sha256(body).hexdigest() == PRIOR_SHA256, "Prior source hash changed"
    dependency_root = root / "shared/runtime" if (root / "shared/runtime").is_dir() else root
    package_root = (dependency_root / "puzzle_generators").resolve()
    assert package_root.is_dir() and package_root.is_relative_to(root.resolve())
    for name, module in tuple(sys.modules.items()):
        if name == "puzzle_generators" or name.startswith("puzzle_generators."):
            path = getattr(module, "__file__", None)
            if path is not None:
                assert Path(path).resolve().is_relative_to(package_root), "Foreign runtime dependency"
    module = types.ModuleType("retained_p1_prior_generator")
    module.__file__ = str(source)
    before = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        exec(compile(body, str(source), "exec"), module.__dict__)
    finally:
        sys.path[:] = before
    assert module.RULE_HASH == RULE_HASH
    return module


def write_new_json(name, value):
    with (HERE / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true",
                        help="Retain fresh reference evidence beside this script; refuse existing files")
    args = parser.parse_args()
    root = find_root(__file__)
    prior = load_prior(root)
    capture = json.loads((HERE / "captured_inputs.json").read_text())
    assert capture["input_generator_sha256"] == PRIOR_SHA256
    assert capture["seed"] == 0 and capture["difficulty"] == "medium"
    assert [pair["sample_index"] for pair in capture["pairs"]] == [23, 24, 25, 26]
    inputs = []
    for pair in capture["pairs"]:
        generated = prior.generate(0, pair["sample_index"], difficulty="medium")
        assert generated == pair["input"], "Captured input does not replay from captured generator"
        assert grid_sha256(generated) == pair["input_sha256"], "Input hash mismatch"
        assert prior.self_check(generated) == [], "Historical input violates historical domain"
        inputs.append(generated)

    canonical_fit = []
    for pair in canonical_pairs(TASK_ID, root=root):
        prediction = rival(pair["input"])
        canonical_fit.append({
            "variant_index": pair.get("variant_index"), "split": pair.get("split"),
            "pair_index": pair.get("pair_index"),
            "input_sha256": grid_sha256(pair["input"]),
            "output_sha256": grid_sha256(pair["output"]),
            "rival_output_sha256": grid_sha256(prediction),
            "rival_matches_canonical": prediction == pair["output"],
        })
    assert len(canonical_fit) == 4 and all(row["rival_matches_canonical"] for row in canonical_fit)

    # Catalog.apply supplies canonical Racket labels. Its generator identity is
    # the current reference runtime snapshot, explicitly distinct from the
    # captured source that produced these inputs. No current generate() is called.
    applied = Catalog(root).apply(TASK_ID, inputs, reference="canonical", timeout=45,
                                  check_generator_domain=False)
    assert applied["executed_rule_hash"] == RULE_HASH
    assert applied["rule_text_sha256"] == RULE_TEXT_SHA256
    assert applied["rule_hash_matches_catalog"] is True
    pairs = []
    for capture_pair, result in zip(capture["pairs"], applied["results"], strict=True):
        grid, output = result["input"], result["output"]
        assert grid == capture_pair["input"] and output is not None
        assert result["input_sha256"] == grid_sha256(grid)
        assert result["output_sha256"] == grid_sha256(output)
        prediction = rival(grid)
        differences = [
            {"row": r, "column": c, "reference": value, "rival": prediction[r][c]}
            for r, row in enumerate(output) for c, value in enumerate(row)
            if value != prediction[r][c]
        ]
        pairs.append({
            "sample_index": capture_pair["sample_index"],
            "role": "query" if capture_pair["sample_index"] == 26 else "demonstration",
            "input": grid, "output": output, "rival_output": prediction,
            "input_sha256": result["input_sha256"],
            "output_sha256": result["output_sha256"],
            "rival_output_sha256": grid_sha256(prediction),
            "rival_matches_reference": prediction == output,
            "differing_cells": differences,
        })
    assert all(pair["rival_matches_reference"] for pair in pairs[:3])
    assert pairs[3]["differing_cells"] == [{"row": 3, "column": 4, "reference": 5, "rival": 3}]
    assert prior.lesson_identifiable(pairs[:3], pairs[3]) == [], "Historical hook behavior changed"
    lesson = {
        "schema": "arcpuzzles-historical-teaching-counterexample-v1",
        "status": "teaching_defect_reproduced", "severity": "P1",
        "task_id": TASK_ID, "input_generator_sha256": PRIOR_SHA256,
        "input_generator_file": "prior_generator.py", "rule_hash": RULE_HASH,
        "rule_text_sha256": RULE_TEXT_SHA256,
        "reference_runtime_generator_sha256": applied["generator_sha256"],
        "rival_name": RIVAL_NAME,
        "rival_description": "Stamp in (row, descending color, column) marker order",
        "rival_source_file": "reproduce.py",
        "rival_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": 0, "difficulty": "medium", "start": 23,
        "train_sample_indices": [23, 24, 25], "query_sample_index": 26,
        "overrides": {}, "pairs": pairs, "canonical_rival_fit": canonical_fit,
        "historical_lesson_identifiable_reasons": [],
        "limits": [
            "Historical captured generator only; this is not a failure claim about current generator bytes.",
            "Four-pair lesson and four canonical pairs, not a census or an all-seed proof.",
            "Reference runtime generator identity can differ from the captured input generator identity; Racket rule identity is pinned.",
        ],
    }
    summary = {
        "status": lesson["status"], "task_id": TASK_ID,
        "input_generator_sha256": PRIOR_SHA256,
        "reference_runtime_generator_sha256": applied["generator_sha256"],
        "rule_hash": RULE_HASH, "canonical_fit": "4/4",
        "demo_matches": [pair["rival_matches_reference"] for pair in pairs[:3]],
        "query_matches": pairs[3]["rival_matches_reference"],
        "query_differing_cells": pairs[3]["differing_cells"],
        "historical_lesson_identifiable_reasons": [],
        "expected_exit_code": 1,
    }
    if args.record:
        write_new_json("racket_apply.json", applied)
        write_new_json("lesson.json", lesson)
        write_new_json("summary.json", summary)
    else:
        retained = json.loads((HERE / "lesson.json").read_text())
        assert retained["input_generator_sha256"] == PRIOR_SHA256
        assert retained["rule_text_sha256"] == RULE_TEXT_SHA256
        assert retained["pairs"] == pairs, "Fresh labels differ from retained source-bound evidence"
    print(json.dumps(summary, indent=2))
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "evidence_or_reference_error", "error": str(exc)}), file=sys.stderr)
        raise SystemExit(2)
