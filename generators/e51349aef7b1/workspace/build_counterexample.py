#!/usr/bin/env python3
"""Materialize and independently verify the strongest canonical shortcut witness."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root

HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
TASK_ID = "e51349aef7b1"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load("e51349aef7b1_counterexample_gen", HOME / "generator.py")
PROBE = load("e51349aef7b1_counterexample_probe", HOME / "workspace" / "probe_semantics.py")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    params = {
        "seed": 712,
        "sample_index": 0,
        "difficulty": None,
        "panel_n": 5,
        "c_cells": 6,
        "palette_id": 0,
    }
    grid = GEN.generate(
        params["seed"],
        params["sample_index"],
        difficulty=params["difficulty"],
        panel_n=params["panel_n"],
        c_cells=params["c_cells"],
        palette_id=params["palette_id"],
    )
    a, b, _ = PROBE.split(grid)
    intended = PROBE.intended(grid)
    rival = PROBE.uncropped_rival(grid)

    apply_result = Catalog(ROOT).apply(TASK_ID, [grid], reference="canonical", timeout=180)
    item = apply_result["results"][0]
    racket_output = item["output"]
    assertions = {
        "racket_valid_output": bool(item["valid_output"] and item["error"] is None),
        "rule_hash_matches_catalog": bool(apply_result["rule_hash_matches_catalog"]),
        "racket_equals_independent_intended": racket_output == intended,
        "rival_disagrees": rival != intended,
        "cropped_first_match_is_rotation_cw": PROBE.match_codes(a, b, cropped=True)[0] == 2,
        "full_panels_have_no_match": PROBE.match_codes(a, b, cropped=False) == [],
    }
    if not all(assertions.values()):
        raise SystemExit(f"counterexample verification failed: {assertions}")

    authority_path = ROOT / "shared/data/base/solutions/banks/dc02f6f7c147/H105__e51349aef7b1.json"
    authority = json.loads(authority_path.read_text())
    raw_code = authority["racket_target"]["raw_code"]
    record = {
        "schema": "arc-generator-counterexample-v1",
        "task_id": TASK_ID,
        "title": "Uncropped full-panel matching defaults to identity after independent A/B translation",
        "shortcut": (
            "Search for the first transform on the complete padded A and B panels; "
            "if none matches, use identity; then transform cropped C and recolor with B."
        ),
        "why_it_fits_canonical": (
            "All five canonical A/B pairs are positioned so the first complete-panel match "
            "selects the same effective code as the cropped authority."
        ),
        "generator_parameters": params,
        "generator_sha256": hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest(),
        "authority_file": str(authority_path.relative_to(ROOT)),
        "authority_file_sha256": hashlib.sha256(authority_path.read_bytes()).hexdigest(),
        "rule_source_sha256": hashlib.sha256(raw_code.encode()).hexdigest(),
        "input": grid,
        "cropped_match_codes": PROBE.match_codes(a, b, cropped=True),
        "full_panel_match_codes": PROBE.match_codes(a, b, cropped=False),
        "intended_output": intended,
        "rival_output": rival,
        "canonical_racket_output": racket_output,
        "assertions": assertions,
        "reproduction": (
            "python3 review.py run python3 generators/e51349aef7b1/workspace/"
            "build_counterexample.py --out generators/e51349aef7b1/counterexamples/"
            "uncropped_full_panels.json"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "cropped_match_codes": record["cropped_match_codes"],
        "full_panel_match_codes": record["full_panel_match_codes"],
        "assertions": assertions,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
