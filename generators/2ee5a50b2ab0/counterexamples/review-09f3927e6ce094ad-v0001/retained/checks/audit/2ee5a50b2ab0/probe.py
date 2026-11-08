#!/usr/bin/env python3
"""Reproduce a lesson-level shortcut in generator 2ee5a50b2ab0.

The intended rule marks both horizontal and vertical line endpoints with color 8.
Because the generator may emit a horizontal line already colored 8, a lawful
three-demonstration lesson can fail to reveal the horizontal branch.  This probe
finds the first such four-pair seed, writes exact inputs for authoritative Racket
labelling, and optionally merges an ``arcpuzzles apply`` receipt.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "2ee5a50b2ab0"


def horizontal_color(module: Any, grid: list[list[int]]) -> int:
    colors = []
    for color, cells in module._components(grid):
        rows = {row for row, _ in cells}
        if len(rows) == 1 and len(cells) >= 2:
            colors.append(color)
    if len(colors) != 1:
        raise AssertionError(f"expected exactly one horizontal component, got {colors}")
    return colors[0]


def vertical_only(module: Any, grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    for _color, cells in module._components(grid):
        rows = sorted({row for row, _ in cells})
        cols = sorted({col for _, col in cells})
        if len(cols) == 1 and len(cells) >= 2:
            output[rows[0]][cols[0]] = 8
            output[rows[-1]][cols[0]] = 8
    return output


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[dict[str, int]]:
    result = []
    for row, (left_row, right_row) in enumerate(zip(left, right, strict=True)):
        for col, (a, b) in enumerate(zip(left_row, right_row, strict=True)):
            if a != b:
                result.append({"row": row, "col": col, "racket": a, "rival": b})
    return result


def extract_racket_outputs(receipt: dict[str, Any]) -> list[list[list[int]]]:
    for key in ("outputs", "output"):
        value = receipt.get(key)
        if key == "outputs" and isinstance(value, list):
            return value
        if key == "output" and isinstance(value, list):
            # A single grid is not expected here, but keep the error explicit.
            if value and isinstance(value[0], list) and value[0] and isinstance(value[0][0], int):
                return [value]
    results = receipt.get("results")
    if isinstance(results, list) and all(isinstance(item, dict) and "output" in item for item in results):
        return [item["output"] for item in results]
    result = receipt.get("result")
    if isinstance(result, dict) and isinstance(result.get("outputs"), list):
        return result["outputs"]
    raise KeyError(f"could not find outputs in Racket receipt keys={sorted(receipt)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--racket-json")
    parser.add_argument("--seed-stop", type=int, default=20_000)
    args = parser.parse_args()

    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = None
    searched = 0
    for seed in range(args.seed_stop):
        searched += 1
        grids = [module.generate(seed, index, difficulty="easy") for index in range(4)]
        colors = [horizontal_color(module, grid) for grid in grids]
        if colors[:3] == [8, 8, 8] and colors[3] != 8:
            selected = (seed, grids, colors)
            break
    if selected is None:
        raise SystemExit(f"no shortcut witness in seeds [0,{args.seed_stop})")

    seed, grids, colors = selected
    rival_outputs = [vertical_only(module, grid) for grid in grids]
    self_checks = [module.self_check(grid, difficulty="easy") for grid in grids]
    if any(self_checks):
        raise AssertionError(f"selected inputs are outside generator domain: {self_checks}")

    report: dict[str, Any] = {
        "schema": "audit-2ee5a50b2ab0-horizontal-shortcut-v2",
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha,
        "generator_version": module.VERSION,
        "search": {
            "seed_start": 0,
            "seed_stop_exclusive": args.seed_stop,
            "seeds_examined": searched,
            "difficulty": "easy",
            "sample_indices": [0, 1, 2, 3],
        },
        "selected": {
            "seed": seed,
            "horizontal_colors": colors,
            "demonstration_indices": [0, 1, 2],
            "query_index": 3,
        },
        "inputs": grids,
        "self_check_errors": self_checks,
        "rival": "mark endpoints of vertical lines only",
        "rival_outputs": rival_outputs,
        "claim": (
            "The vertical-only rival is visually indistinguishable on all three "
            "demonstrations because each sole horizontal line is already color 8, "
            "but differs on the query whose horizontal line is not color 8."
        ),
    }

    (out_dir / "input.json").write_text(json.dumps(grids, indent=2) + "\n")
    (out_dir / "probe-pre-racket.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    if args.racket_json:
        racket_path = Path(args.racket_json)
        racket = json.loads(racket_path.read_text())
        outputs = extract_racket_outputs(racket)
        if len(outputs) != 4:
            raise AssertionError(f"expected four Racket outputs, got {len(outputs)}")
        demo_matches = [rival_outputs[index] == outputs[index] for index in range(3)]
        query_cells = differing_cells(outputs[3], rival_outputs[3])
        report["racket_receipt"] = str(racket_path)
        report["racket"] = {
            "outputs": outputs,
            "receipt_generator_sha256": racket.get("generator_sha256"),
            "executed_rule_hash": racket.get("executed_rule_hash") or racket.get("rule_hash"),
            "domain_checks": racket.get("generator_domain") or racket.get("domain_checks"),
        }
        report["comparison"] = {
            "rival_matches_demonstrations": demo_matches,
            "rival_fits_all_demonstrations": all(demo_matches),
            "rival_matches_query": rival_outputs[3] == outputs[3],
            "query_disagreement_cells": query_cells,
            "reproduced": all(demo_matches) and bool(query_cells),
        }
        if not report["comparison"]["reproduced"]:
            raise AssertionError(f"shortcut did not reproduce: {report['comparison']}")
        (out_dir / "probe.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )

    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "generator_sha256": source_sha,
                "selected_seed": seed,
                "horizontal_colors": colors,
                "self_check_errors": self_checks,
                "racket_merged": bool(args.racket_json),
                "reproduced": report.get("comparison", {}).get("reproduced"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
