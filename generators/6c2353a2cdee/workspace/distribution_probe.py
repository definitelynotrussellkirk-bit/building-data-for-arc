#!/usr/bin/env python3
"""Task-linked before/after distribution probe for ARC task 6c2353a2cdee.

The official distribution gate compares broad marginals.  This probe records the
rule-relevant panel grammar that distinguished the canonical examples from the
pre-review generator: per-panel size, connectivity, row support, width, border
touching, code grammar, and whether all three overlap counts are visible.

It is intentionally self-contained and can compare any two generator source
files that expose ``generate(seed, sample_index, *, difficulty=...)``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Iterable

TASK_ID = "6c2353a2cdee"
PANEL_STARTS = (0, 6, 12)
BANDS = ("easy", "medium", "hard")
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_module(path: Path):
    path = path.resolve()
    name = f"probe_{path.stem}_{_sha256(path)[:12]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _panel_cells(grid: list[list[int]], panel_index: int) -> set[tuple[int, int]]:
    left = PANEL_STARTS[panel_index]
    return {
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][left + col] != 0
    }


def _component_count(cells: set[tuple[int, int]]) -> int:
    unseen = set(cells)
    components = 0
    while unseen:
        components += 1
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in CARDINAL:
                nxt = (row + dr, col + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
    return components


def _codes(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(value for value in grid[6][left : left + 5] if value != 0)
        for left in PANEL_STARTS
    )


def _panel_binary(grid: list[list[int]], panel_index: int) -> list[list[int]]:
    left = PANEL_STARTS[panel_index]
    return [
        [1 if grid[row][left + col] != 0 else 0 for col in range(5)]
        for row in range(5)
    ]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return _rotate_cw(grid)
    if code == 3:
        return _rotate_180(grid)
    if code == 4:
        return _rotate_ccw(grid)
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    return [row[:] for row in grid]


def _authority_output(grid: list[list[int]]) -> list[list[int]] | None:
    code_blocks = _codes(grid)
    if any(len(block) != 1 for block in code_blocks):
        return None
    transformed = [
        _transform(_panel_binary(grid, index), code_blocks[index][0])
        for index in range(3)
    ]
    return [
        [
            {0: 0, 1: 2, 2: 4, 3: 8}[
                sum(panel[row][col] != 0 for panel in transformed)
            ]
            for col in range(5)
        ]
        for row in range(5)
    ]


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _safe_self_check(module: Any, grid: list[list[int]], difficulty: str | None) -> bool:
    check = getattr(module, "self_check", None)
    if not callable(check):
        return False
    try:
        return not check(grid, difficulty=difficulty)
    except TypeError:
        return not check(grid)


def _summarize_grids(
    grids: Iterable[tuple[list[list[int]], str | None, list[list[int]] | None]],
    *,
    module: Any | None,
    source_path: Path | None,
    generation_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    panel_sizes: list[int] = []
    component_counts: list[int] = []
    panel_widths: list[int] = []
    code_frequencies: Counter[int] = Counter()
    sample_count = 0
    panel_count = 0
    connected_panels = 0
    middle_rows_panels = 0
    border_touch_panels = 0
    exact_one_code_blocks = 0
    all_count_palette = 0
    self_check_accepts = 0
    unique_grids: set[tuple[tuple[int, ...], ...]] = set()
    per_band: dict[str, dict[str, int]] = {
        band: {"samples": 0, "connected_panels": 0, "panels": 0}
        for band in (*BANDS, "canonical")
    }

    for grid, band, provided_output in grids:
        sample_count += 1
        label = band or "canonical"
        per_band.setdefault(label, {"samples": 0, "connected_panels": 0, "panels": 0})
        per_band[label]["samples"] += 1
        unique_grids.add(_grid_key(grid))
        if module is None or _safe_self_check(module, grid, band):
            self_check_accepts += 1

        for panel_index in range(3):
            cells = _panel_cells(grid, panel_index)
            size = len(cells)
            components = _component_count(cells)
            rows = {row for row, _ in cells}
            cols = {col for _, col in cells}
            width = max(cols) - min(cols) + 1 if cols else 0
            panel_sizes.append(size)
            component_counts.append(components)
            panel_widths.append(width)
            panel_count += 1
            per_band[label]["panels"] += 1
            if components == 1:
                connected_panels += 1
                per_band[label]["connected_panels"] += 1
            if rows == {1, 2, 3}:
                middle_rows_panels += 1
            if any(row in {0, 4} or col in {0, 4} for row, col in cells):
                border_touch_panels += 1

        blocks = _codes(grid)
        for block in blocks:
            if len(block) == 1:
                exact_one_code_blocks += 1
                code_frequencies[block[0]] += 1

        output = provided_output if provided_output is not None else _authority_output(grid)
        if output is not None:
            palette = {value for row in output for value in row}
            if {2, 4, 8} <= palette:
                all_count_palette += 1

    def fraction(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 6) if denominator else 0.0

    report: dict[str, Any] = {
        "source_path": str(source_path) if source_path else "canonical ledger",
        "source_sha256": _sha256(source_path) if source_path else None,
        "samples": sample_count,
        "panels": panel_count,
        "unique_input_fraction": fraction(len(unique_grids), sample_count),
        "self_check_accept_fraction": fraction(self_check_accepts, sample_count),
        "connected_panel_fraction": fraction(connected_panels, panel_count),
        "middle_rows_panel_fraction": fraction(middle_rows_panels, panel_count),
        "border_touch_panel_fraction": fraction(border_touch_panels, panel_count),
        "exact_one_code_block_fraction": fraction(exact_one_code_blocks, panel_count),
        "all_count_palette_fraction": fraction(all_count_palette, sample_count),
        "panel_cells": {
            "min": min(panel_sizes) if panel_sizes else None,
            "median": median(panel_sizes) if panel_sizes else None,
            "max": max(panel_sizes) if panel_sizes else None,
        },
        "components_per_panel": {
            "min": min(component_counts) if component_counts else None,
            "median": median(component_counts) if component_counts else None,
            "max": max(component_counts) if component_counts else None,
        },
        "panel_width": {
            "min": min(panel_widths) if panel_widths else None,
            "median": median(panel_widths) if panel_widths else None,
            "max": max(panel_widths) if panel_widths else None,
        },
        "code_frequencies": {str(key): value for key, value in sorted(code_frequencies.items())},
        "per_band": {
            label: {
                **counts,
                "connected_panel_fraction": fraction(
                    counts["connected_panels"], counts["panels"]
                ),
            }
            for label, counts in per_band.items()
            if counts["samples"]
        },
        "generation_failures": generation_failures or [],
    }
    return report


def summarize_generator(
    path: Path,
    *,
    samples_per_band: int,
    seed_base: int,
) -> dict[str, Any]:
    module = _load_module(path)
    rows: list[tuple[list[list[int]], str | None, list[list[int]] | None]] = []
    failures: list[dict[str, Any]] = []
    for band_index, band in enumerate(BANDS):
        for sample_index in range(samples_per_band):
            seed = seed_base + band_index * 100_003 + sample_index * 7_919
            try:
                grid = module.generate(seed, sample_index, difficulty=band)
            except Exception as exc:  # preserve exact failing draw in the report
                failures.append(
                    {
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            rows.append(([list(map(int, row)) for row in grid], band, None))
    report = _summarize_grids(
        rows, module=module, source_path=path, generation_failures=failures
    )
    report["version"] = getattr(module, "VERSION", None)
    report["rule_hash"] = getattr(module, "RULE_HASH", None)
    return report


def summarize_canonical(path: Path) -> dict[str, Any]:
    record = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                record = row
                break
    if record is None:
        raise KeyError(f"canonical task {TASK_ID} not found in {path}")
    rows = []
    for split in ("train", "test"):
        for pair in record[split]:
            rows.append(
                (
                    [list(map(int, row)) for row in pair["input"]],
                    "canonical",
                    [list(map(int, row)) for row in pair["output"]],
                )
            )
    report = _summarize_grids(rows, module=None, source_path=None)
    report["ledger_path"] = str(path)
    report["ledger_sha256"] = _sha256(path)
    report["splits"] = {"train": len(record["train"]), "test": len(record["test"])}
    return report


def compare_sources(
    *,
    before_path: Path,
    after_path: Path,
    canonical_path: Path,
    samples_per_band: int = 40,
    seed_base: int = 7331,
) -> dict[str, Any]:
    if samples_per_band <= 0:
        raise ValueError("samples_per_band must be positive")
    return {
        "schema": "arc-generator-task-linked-distribution/1",
        "task_id": TASK_ID,
        "sample_policy": {
            "bands": list(BANDS),
            "samples_per_band": samples_per_band,
            "total_attempted_per_source": samples_per_band * len(BANDS),
            "seed_base": seed_base,
            "seed_formula": "seed_base + band_index*100003 + sample_index*7919",
            "sample_index_range": [0, samples_per_band - 1],
        },
        "canonical": summarize_canonical(canonical_path),
        "before": summarize_generator(
            before_path, samples_per_band=samples_per_band, seed_base=seed_base
        ),
        "after": summarize_generator(
            after_path, samples_per_band=samples_per_band, seed_base=seed_base
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=40)
    parser.add_argument("--seed-base", type=int, default=7331)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = compare_sources(
        before_path=args.before,
        after_path=args.after,
        canonical_path=args.canonical,
        samples_per_band=args.samples_per_band,
        seed_base=args.seed_base,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "task_id": TASK_ID,
        "out": str(args.out),
        "before_connected": report["before"]["connected_panel_fraction"],
        "after_connected": report["after"]["connected_panel_fraction"],
        "canonical_connected": report["canonical"]["connected_panel_fraction"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
