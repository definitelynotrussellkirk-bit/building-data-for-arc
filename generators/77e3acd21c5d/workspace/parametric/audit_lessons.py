#!/usr/bin/env python3
"""Bounded, reusable curriculum audit for 77e3acd21c5d tie policies.

The audit is intentionally finite.  It checks the declared nine settings plus
three plausible structural shortcuts against demonstrations only, then records
whether any survivor changes a query.  Native qualification remains the Racket
source of truth for labels.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_audit_77e3acd21c5d_prototype", HERE / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(HERE / "prototype.py")
PROTOTYPE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = PROTOTYPE
_SPEC.loader.exec_module(PROTOTYPE)


def _prepare_scene(grid):
    sampler = PROTOTYPE.generator()
    facts = sampler._require_scene(grid)
    blank = facts["blank"]
    blank_color = next(iter(blank["colors"]))
    selected = {
        "widest": facts["source"],
        "first": facts["markers"][0],
        "largest_area": max(facts["markers"], key=lambda item: item["h"] * item["w"]),
    }
    sources = {}
    for name, source in selected.items():
        _body, marker_color, offsets = sampler._component_marker_facts(grid, source)
        sources[name] = {
            "height": source["h"],
            "width": source["w"],
            "marker_color": marker_color,
            "offsets": offsets,
        }
    return {
        "blank_height": blank["h"],
        "blank_width": blank["w"],
        "blank_color": blank_color,
        "sources": sources,
    }


def _render_prepared(scene, parameters, *, selector="widest", zipped=False):
    try:
        source = scene["sources"][selector]
    except KeyError as exc:
        raise ValueError(selector) from exc
    output = [
        [scene["blank_color"]] * scene["blank_width"]
        for _ in range(scene["blank_height"])
    ]
    for marker_row, marker_col in source["offsets"]:
        rows = PROTOTYPE._axis_landings(
            marker_row, source["height"], scene["blank_height"], parameters.row_ties
        )
        columns = PROTOTYPE._axis_landings(
            marker_col, source["width"], scene["blank_width"], parameters.column_ties
        )
        if zipped and len(rows) > 1 and len(columns) > 1:
            positions = tuple(zip(rows, columns))
        else:
            positions = tuple(product(rows, columns))
        for row, column in positions:
            if 0 <= row < scene["blank_height"] and 0 <= column < scene["blank_width"]:
                output[row][column] = source["marker_color"]
    return output


def _render(grid, parameters, *, selector="widest", zipped=False):
    return _render_prepared(
        _prepare_scene(grid), parameters, selector=selector, zipped=zipped
    )


def _extra_rivals(parameters):
    return {
        "first_multicolor_source": lambda grid: _render(grid, parameters, selector="first"),
        "largest_area_source": lambda grid: _render(grid, parameters, selector="largest_area"),
        "diagonal_zip_on_double_tie": lambda grid: _render(grid, parameters, zipped=True),
    }


def _input_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def audit(*, seed_start: int = 0, seed_count: int = 16) -> dict:
    if type(seed_start) is not int or seed_start < 0:
        raise ValueError("seed_start must be a nonnegative literal integer")
    if type(seed_count) is not int or not 1 <= seed_count <= 4096:
        raise ValueError("seed_count must be a literal integer in 1..4096")

    failures = []
    episodes = 0
    exact_30x30_pairs = 0
    setting_dependent_query_pairs = 0
    harmful_rival_survivors = 0
    public_prefix_checks = 0
    for seed in range(seed_start, seed_start + seed_count):
        pool = PROTOTYPE.sample_inputs(seed, demo_count=6, query_count=4)
        demonstrations = pool["demonstrations"]
        queries = pool["queries"]
        all_inputs = demonstrations + queries
        prepared = [_prepare_scene(grid) for grid in all_inputs]
        if len({_input_key(grid) for grid in all_inputs}) != 10:
            failures.append({"seed": seed, "finding": "duplicate_input"})
        if not (len(queries[-1]) == 30 and len(queries[-1][0]) == 30):
            failures.append({"seed": seed, "finding": "missing_exact_30x30_query"})

        matrices = {
            parameters.key: [_render_prepared(scene, parameters) for scene in prepared]
            for parameters in PROTOTYPE.ALL_PARAMETERS
        }
        for query_index in range(6, 10):
            if len({PROTOTYPE.object_sha256(outputs[query_index]) for outputs in matrices.values()}) > 1:
                setting_dependent_query_pairs += 1

        for parameters in PROTOTYPE.ALL_PARAMETERS:
            truth = matrices[parameters.key]
            rival_outputs = {
                "first_multicolor_source": [
                    _render_prepared(scene, parameters, selector="first")
                    for scene in prepared
                ],
                "largest_area_source": [
                    _render_prepared(scene, parameters, selector="largest_area")
                    for scene in prepared
                ],
                "diagonal_zip_on_double_tie": [
                    _render_prepared(scene, parameters, zipped=True)
                    for scene in prepared
                ],
            }
            for demo_count in range(2, 7):
                episodes += 1
                exact_30x30_pairs += 1
                survivors = [
                    key for key, outputs in matrices.items()
                    if outputs[:demo_count] == truth[:demo_count]
                ]
                if survivors != [parameters.key]:
                    failures.append({
                        "seed": seed,
                        "setting": parameters.as_dict(),
                        "demo_count": demo_count,
                        "finding": "finite_setting_ambiguity",
                        "survivors": survivors,
                    })
                for name, outputs in rival_outputs.items():
                    fits = outputs[:demo_count] == truth[:demo_count]
                    changes_query = any(
                        actual != expected
                        for actual, expected in zip(outputs[6:], truth[6:])
                    )
                    if fits and changes_query:
                        harmful_rival_survivors += 1
                        failures.append({
                            "seed": seed,
                            "setting": parameters.as_dict(),
                            "demo_count": demo_count,
                            "finding": "harmful_structural_rival",
                            "rival": name,
                        })

                episode = {
                    "train": [
                        {"input": deepcopy(grid), "output": deepcopy(output)}
                        for grid, output in zip(demonstrations[:demo_count], truth[:demo_count])
                    ],
                    "test": [
                        {"input": deepcopy(grid), "output": deepcopy(output)}
                        for grid, output in zip(queries, truth[6:])
                    ],
                    "program_solution": PROTOTYPE.materialize_rule(parameters),
                }
                first = PROTOTYPE.public_challenge(episode, revealed_queries=1)
                full = PROTOTYPE.public_challenge(episode, revealed_queries=4)
                public_prefix_checks += 1
                if first["train"] != full["train"] or first["test"] != full["test"][:1]:
                    failures.append({
                        "seed": seed,
                        "setting": parameters.as_dict(),
                        "demo_count": demo_count,
                        "finding": "public_prefix_instability",
                    })

    summary = {
        "seeds": seed_count,
        "settings": len(PROTOTYPE.ALL_PARAMETERS),
        "demo_counts": [2, 3, 4, 5, 6],
        "episodes": episodes,
        "exact_30x30_pairs": exact_30x30_pairs,
        "setting_dependent_query_pairs": setting_dependent_query_pairs,
        "public_prefix_checks": public_prefix_checks,
        "harmful_rival_survivors": harmful_rival_survivors,
        "failures": len(failures),
    }
    return {
        "schema": "arc-parametric-lesson-audit-v1",
        "task_id": PROTOTYPE.TASK_ID,
        "status": "pass" if not failures else "fail",
        "summary": summary,
        "declared_structural_rivals": [
            "first_multicolor_source",
            "largest_area_source",
            "diagonal_zip_on_double_tie",
        ],
        "limitations": (
            "Finite audit over declared settings/rivals and requested seeds; "
            "not a proof of universal lesson uniqueness."
        ),
        "failures": failures,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(seed_start=args.seed_start, seed_count=args.seeds)
    payload = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
