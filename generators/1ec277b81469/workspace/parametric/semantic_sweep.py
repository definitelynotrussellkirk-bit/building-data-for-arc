"""Many-seed semantic shortcut sweep for the 1ec277b81469 family.

This complements the protected-Racket probe.  It cheaply searches many fresh
seeds for stochastic two-demonstration teaching holes involving rank, position,
frequency, color extent, connectivity, partial-intermediate, and whole-component
shortcuts.  It is intentionally task-local so a future author can rerun it after
changing the sampler before paying for native qualification.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK_ID = "1ec277b81469"


def _load_prototype():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_sweep_1ec277b81469", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _bbox(component):
    rows = [row for row, _ in component["cells"]]
    cols = [col for _, col in component["cells"]]
    return min(rows), min(cols), max(rows), max(cols)


def _metric(component, name):
    r1, c1, r2, c2 = _bbox(component)
    height, width = r2 - r1 + 1, c2 - c1 + 1
    return {"area": height * width, "height": height, "width": width}[name]


def _fill_bbox(grid, component):
    output = deepcopy(grid)
    r1, c1, r2, c2 = _bbox(component)
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            output[row][col] = 9
    return output


def _components_8(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _multicolor_components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append({"color": -1, "cells": tuple(sorted(cells))})
    return result


def _recolor_component(grid, component):
    output = deepcopy(grid)
    for row, col in component["cells"]:
        output[row][col] = 9
    return output


def rival_outputs(proto, source):
    intermediate = proto._right_pack(source)
    components = proto._components(intermediate)
    largest = max(components, key=lambda component: len(component["cells"]))
    ordered = sorted(components, key=lambda component: len(component["cells"]), reverse=True)
    frequencies = Counter(value for row in intermediate for value in row if value)
    modal_color = max(frequencies, key=lambda color: (frequencies[color], -color))
    modal_component = max(
        (component for component in components if component["color"] == modal_color),
        key=lambda component: len(component["cells"]),
    )
    all_largest_color = {
        "color": largest["color"],
        "cells": tuple(
            (row, col)
            for row, values in enumerate(intermediate)
            for col, value in enumerate(values)
            if value == largest["color"]
        ),
    }
    original_components = proto._components(source)
    original_largest = max(original_components, key=lambda component: len(component["cells"]))
    multicolor = max(_multicolor_components(intermediate), key=lambda component: len(component["cells"]))
    fixed = deepcopy(intermediate)
    for row in range(min(3, len(fixed))):
        for col in range(min(3, len(fixed[0]))):
            fixed[row][col] = 9
    return {
        "largest_bbox_area": _fill_bbox(
            intermediate,
            max(components, key=lambda component: (_metric(component, "area"), len(component["cells"]))),
        ),
        "largest_bbox_height": _fill_bbox(
            intermediate,
            max(components, key=lambda component: (_metric(component, "height"), len(component["cells"]))),
        ),
        "largest_bbox_width": _fill_bbox(
            intermediate,
            max(components, key=lambda component: (_metric(component, "width"), len(component["cells"]))),
        ),
        "largest_8_connected": _fill_bbox(
            intermediate, max(_components_8(intermediate), key=lambda component: len(component["cells"]))
        ),
        "largest_multicolor": _fill_bbox(intermediate, multicolor),
        "most_frequent_color": _fill_bbox(intermediate, modal_component),
        "all_cells_of_largest_color": _fill_bbox(intermediate, all_largest_color),
        "first_component": _fill_bbox(intermediate, components[0]),
        "smallest_component": _fill_bbox(
            intermediate, min(components, key=lambda component: len(component["cells"]))
        ),
        "second_largest_component": _fill_bbox(
            intermediate, ordered[1] if len(ordered) > 1 else ordered[0]
        ),
        "topmost_component": _fill_bbox(
            intermediate, min(components, key=lambda component: (_bbox(component)[0], _bbox(component)[1]))
        ),
        "bottommost_component": _fill_bbox(
            intermediate, max(components, key=lambda component: (_bbox(component)[2], len(component["cells"])))
        ),
        "rightmost_component": _fill_bbox(
            intermediate, max(components, key=lambda component: (_bbox(component)[3], len(component["cells"])))
        ),
        "largest_component_only": _recolor_component(intermediate, largest),
        "skip_right_pack": _fill_bbox(source, original_largest),
        "fixed_top_left": fixed,
    }


def build_report(*, seed_count=200):
    if type(seed_count) is not int or not 1 <= seed_count <= 10_000:
        raise ValueError("seed_count must be an exact integer in 1..10000")
    proto = _load_prototype()
    survivor_rows = []
    target_colors = set()
    target_sizes = set()
    target_bboxes = set()
    rival_names = None
    for seed in range(seed_count):
        episode = proto.generate(seed, {"finish": "fill_largest_bbox"}, 2, 4)
        expected_train = [pair["output"] for pair in episode["train"]]
        outputs_by_rival = {}
        for pair in episode["train"]:
            summary = proto.stage_summary(pair["input"])
            target_colors.add(summary["largest_color"])
            target_sizes.add(summary["largest_size"])
            target_bboxes.add(tuple(summary["largest_bbox"]))
            for name, output in rival_outputs(proto, pair["input"]).items():
                outputs_by_rival.setdefault(name, []).append(output)
        if rival_names is None:
            rival_names = tuple(sorted(outputs_by_rival))
        elif tuple(sorted(outputs_by_rival)) != rival_names:
            raise ValueError("rival inventory changed within one sweep")
        for name, outputs in outputs_by_rival.items():
            if outputs != expected_train:
                continue
            expected_queries = [pair["output"] for pair in episode["test"]]
            actual_queries = [rival_outputs(proto, pair["input"])[name] for pair in episode["test"]]
            changed = [
                index
                for index, (actual, expected) in enumerate(zip(actual_queries, expected_queries))
                if actual != expected
            ]
            survivor_rows.append(
                {
                    "seed": seed,
                    "rival": name,
                    "query_differences": changed,
                    "ambiguous": bool(changed),
                }
            )
    ambiguous = [row for row in survivor_rows if row["ambiguous"]]
    report = {
        "schema": "arcpuzzles-parametric-semantic-sweep-v1",
        "status": "passed" if not survivor_rows else "failed",
        "task_id": TASK_ID,
        "seed_count": seed_count,
        "episodes": seed_count,
        "demos_per_episode": 2,
        "queries_per_episode": 4,
        "rivals": list(rival_names or ()),
        "rival_count": len(rival_names or ()),
        "survivors": survivor_rows,
        "survivor_count": len(survivor_rows),
        "ambiguous_count": len(ambiguous),
        "coverage": {
            "target_colors": sorted(target_colors),
            "target_size_count": len(target_sizes),
            "target_sizes": sorted(target_sizes),
            "target_bbox_count": len(target_bboxes),
        },
        "limits": (
            "Finite deterministic seed sweep over authored Python mirrors.  Protected-Racket "
            "execution remains the authority for labels and is exercised separately."
        ),
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = build_report(seed_count=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "seed_count": report["seed_count"],
                "rival_count": report["rival_count"],
                "survivor_count": report["survivor_count"],
                "ambiguous_count": report["ambiguous_count"],
                "coverage": report["coverage"],
            }
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
