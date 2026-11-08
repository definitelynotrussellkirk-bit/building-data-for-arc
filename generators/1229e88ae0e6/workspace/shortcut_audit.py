"""Audit standard four-demo ARC episodes against plausible centering shortcuts.

This is a diagnostic Python tool, not Racket authority and not a source of
admitted labels.  It deliberately includes generic rivals in addition to the
ones declared by the generator so an omitted rival can still be discovered.

From the packet root::

  python3 -B repo/generators/1229e88ae0e6/workspace/shortcut_audit.py \
    --out checks/shortcut_audit.json --require-none
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Sequence
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from review_probe import facts, load_generator, specification

TASK_ID = "1229e88ae0e6"
Grid = Sequence[Sequence[int]]
Rival = Callable[[Grid], list[list[int]]]


def _copy(grid: Grid) -> list[list[int]]:
    return [list(row) for row in grid]


def _sorted_colors(grid: Grid, *, reverse: bool) -> list[list[int]]:
    output = specification(grid)
    cells = [
        (row, col)
        for row, values in enumerate(output)
        for col, value in enumerate(values)
        if value != 0
    ]
    colors = sorted(
        (output[row][col] for row, col in cells), reverse=reverse
    )
    for (row, col), color in zip(cells, colors):
        output[row][col] = color
    return output


def _pack_nonzeros(grid: Grid) -> list[list[int]]:
    a = facts(grid)
    height, width = a["shape"]
    bbox_h, bbox_w = a["bbox_shape"]
    target_row, target_col = a["target"]
    colors = [grid[row][col] for row, col in a["cells"]]
    positions = [
        (row, col)
        for row in range(bbox_h)
        for col in range(bbox_w)
    ][:len(colors)]
    output = [[0] * width for _ in range(height)]
    for (row, col), color in zip(positions, colors):
        output[target_row + row][target_col + col] = color
    return output


def _transform_pattern(grid: Grid, operation: str) -> list[list[int]]:
    a = facts(grid)
    height, width = a["shape"]
    bbox_h, bbox_w = a["bbox_shape"]
    source_row, source_col = a["origin"]
    pattern = [
        list(grid[row][source_col:source_col + bbox_w])
        for row in range(source_row, source_row + bbox_h)
    ]
    if operation == "horizontal_flip":
        transformed = [row[::-1] for row in pattern]
    elif operation == "vertical_flip":
        transformed = pattern[::-1]
    elif operation == "rotate_180":
        transformed = [row[::-1] for row in pattern[::-1]]
    elif operation == "transpose":
        transformed = [list(row) for row in zip(*pattern)]
    elif operation == "rotate_90":
        transformed = [list(row) for row in zip(*pattern[::-1])]
    else:
        raise ValueError(f"unknown pattern transform: {operation}")
    motif_h, motif_w = len(transformed), len(transformed[0])
    target_row, target_col = (height - motif_h) // 2, (width - motif_w) // 2
    output = [[0] * width for _ in range(height)]
    for row, values in enumerate(transformed):
        for col, value in enumerate(values):
            if value != 0:
                output[target_row + row][target_col + col] = value
    return output


def _reverse_palette(grid: Grid) -> list[list[int]]:
    output = specification(grid)
    palette = sorted({value for row in output for value in row if value != 0})
    remap = {value: palette[-index - 1] for index, value in enumerate(palette)}
    return [
        [remap[value] if value != 0 else 0 for value in row]
        for row in output
    ]


def _copy_plus_center(grid: Grid) -> list[list[int]]:
    centered = specification(grid)
    return [
        [centered[row][col] or grid[row][col] for col in range(len(grid[0]))]
        for row in range(len(grid))
    ]


def generic_rivals() -> dict[str, Rival]:
    """Rivals worth probing even when a generator forgot to declare them."""
    return {
        "sort_colors_ascending": lambda grid: _sorted_colors(grid, reverse=False),
        "sort_colors_descending": lambda grid: _sorted_colors(grid, reverse=True),
        "pack_nonzeros_in_centered_bbox": _pack_nonzeros,
        "center_then_horizontal_flip": lambda grid: _transform_pattern(
            grid, "horizontal_flip"
        ),
        "center_then_vertical_flip": lambda grid: _transform_pattern(
            grid, "vertical_flip"
        ),
        "center_then_rotate_180": lambda grid: _transform_pattern(
            grid, "rotate_180"
        ),
        "center_then_transpose": lambda grid: _transform_pattern(
            grid, "transpose"
        ),
        "center_then_rotate_90": lambda grid: _transform_pattern(
            grid, "rotate_90"
        ),
        "reverse_palette_after_centering": _reverse_palette,
        "copy_source_and_centered_motif": _copy_plus_center,
    }


def candidate_rivals(module: Any) -> dict[str, Rival]:
    rivals = generic_rivals()
    declared = getattr(module, "SEMANTIC_RIVALS", {})
    if isinstance(declared, dict):
        # Prefer the generator's exact implementation when names overlap, but
        # retain generic candidates the generator never thought to declare.
        rivals.update(declared)
    return dict(sorted(rivals.items()))


def audit(
    module: Any,
    *,
    bands: Sequence[str] = ("easy", "medium", "hard"),
    seeds: Iterable[int] = range(512),
) -> dict[str, Any]:
    """Count rivals that fit all four demos in ordinary 0..4 episodes."""
    seed_values = tuple(seeds)
    rivals = candidate_rivals(module)
    rows = {
        name: {
            "demo_survivals": 0,
            "harmful_query_disagreements": 0,
            "individual_agreements": 0,
            "first_survival": None,
            "first_harmful_survival": None,
            "per_band_demo_survivals": {band: 0 for band in bands},
        }
        for name in rivals
    }
    failures: list[dict[str, Any]] = []
    episodes = 0
    examples = 5
    for band in bands:
        for seed in seed_values:
            grids = [module.generate(seed, index, difficulty=band) for index in range(examples)]
            outputs = [specification(grid) for grid in grids]
            episodes += 1
            for name, rival in rivals.items():
                try:
                    agreements = [
                        rival(grid) == output
                        for grid, output in zip(grids, outputs)
                    ]
                except Exception as exc:  # retain a precise tool defect
                    failures.append({
                        "rival": name,
                        "band": band,
                        "seed": seed,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                row = rows[name]
                row["individual_agreements"] += sum(agreements)
                if all(agreements[:4]):
                    row["demo_survivals"] += 1
                    row["per_band_demo_survivals"][band] += 1
                    evidence = {
                        "band": band,
                        "seed": seed,
                        "agreement_signature": agreements,
                    }
                    if row["first_survival"] is None:
                        row["first_survival"] = evidence
                    if not agreements[4]:
                        row["harmful_query_disagreements"] += 1
                        if row["first_harmful_survival"] is None:
                            row["first_harmful_survival"] = evidence

    for name, row in rows.items():
        if row["demo_survivals"]:
            failures.append({
                "rival": name,
                "demo_survivals": row["demo_survivals"],
                "harmful_query_disagreements": row["harmful_query_disagreements"],
                "first_survival": row["first_survival"],
            })

    return {
        "schema": "centering-episode-shortcut-audit-v1",
        "label_source": "independent_python_specification_not_Racket",
        "bands": list(bands),
        "seed_count": len(seed_values),
        "seed_min": min(seed_values) if seed_values else None,
        "seed_max": max(seed_values) if seed_values else None,
        "episodes_checked": episodes,
        "examples_per_episode": examples,
        "rivals": rows,
        "failures": failures,
        "passed": not failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--start-seed", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=512)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-none", action="store_true")
    args = parser.parse_args()
    if args.seed_count <= 0:
        parser.error("--seed-count must be positive")
    source = args.generator or args.library / f"generators/{TASK_ID}/generator.py"
    module = load_generator(args.library, source)
    result = audit(
        module,
        seeds=range(args.start_seed, args.start_seed + args.seed_count),
    )
    result["generator_path"] = str(source)
    result["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    result["generator_version"] = getattr(module, "VERSION", None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    for name, row in result["rivals"].items():
        print(
            f"{name:40s} demos={row['demo_survivals']:4d} "
            f"harmful={row['harmful_query_disagreements']:4d} "
            f"individual={row['individual_agreements']}/{result['episodes_checked'] * 5}"
        )
    print("episode shortcut gate:", "PASS" if result["passed"] else "FAIL")
    return int(args.require_none and not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
