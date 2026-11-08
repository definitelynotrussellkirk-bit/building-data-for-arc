#!/usr/bin/env python3
"""Independent finite-domain probe for generator 56072bfdb820.

The probe enumerates every exact ``pair_index`` × ``bad_mask`` override in
all difficulty bands.  It compares the selected generator's public mirror to
an independent Python translation of the pinned rule, verifies the observable
axes and self-check, and can emit the 144 unique inputs in the JSON shape
accepted by ``python -m arcpuzzles apply``.

It intentionally does not import canonical answers or generator internals.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Sequence

TASK_ID = "56072bfdb820"
TILES = tuple((row, col) for row in range(3) for col in range(3))
PAIRS = tuple(combinations(TILES, 2))
DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))
BANDS = (None, "easy", "medium", "hard")


def _load_generator(path: Path):
    path = path.resolve()
    module_name = f"reference_probe_{TASK_ID}_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _symbols(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    symbols: list[tuple[int, int, int]] = []
    for tile_row, tile_col in TILES:
        row0, col0 = tile_row * 4, tile_col * 4
        values = [grid[row0 + dr][col0 + dc] for dr, dc in DIAMOND]
        if all(value == 7 for value in values):
            continue
        if len(set(values)) != 1:
            raise ValueError(f"non-monochrome diamond at tile {(tile_row, tile_col)}")
        symbols.append((tile_row, tile_col, values[0]))
    return symbols


def _blank_grid(rows: int = 11, cols: int = 11) -> list[list[int]]:
    grid = [[7] * cols for _ in range(rows)]
    if (rows, cols) == (11, 11):
        for row in (3, 7):
            grid[row] = [6] * 11
        for col in (3, 7):
            for row in range(11):
                grid[row][col] = 6
    return grid


def _put_diamond(grid: list[list[int]], tile: tuple[int, int], color: int) -> None:
    row0, col0 = tile[0] * 4, tile[1] * 4
    for dr, dc in DIAMOND:
        grid[row0 + dr][col0 + dc] = color


def independent_rule(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Translate the pinned authority without consulting generator internals."""
    symbols = _symbols(grid)
    if any(color != 2 for _, _, color in symbols):
        return _blank_grid(16, 16)

    twos = [(row, col) for row, col, color in symbols if color == 2]
    if len(twos) != 2:
        raise ValueError(f"expected exactly two color-2 symbols, got {len(twos)}")
    (r1, c1), (r2, c2) = twos
    if c1 == c2:
        row, col = min(r1, r2) - 1, c1
        proposals = ((row, col - 1, 5), (row, col + 1, 8))
    elif r1 == r2:
        row, col = r1, min(c1, c2) - 1
        proposals = ((row - 1, col, 8), (row + 1, col, 5))
    elif c2 < c1:
        proposals = ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    else:
        proposals = ((r2, c2 + 1, 8), (r2 + 1, c2, 5))

    extras = [
        item for item in proposals
        if 0 <= item[0] < 3 and 0 <= item[1] < 3
    ]
    output = _blank_grid()
    # Authority lookup gives observed symbols priority if a proposal collides.
    lookup = {(row, col): color for row, col, color in extras}
    lookup.update({(row, col): color for row, col, color in symbols})
    for tile, color in lookup.items():
        _put_diamond(output, tile, color)
    return output


def _record_mismatch(
    mismatches: list[dict[str, Any]],
    *,
    band: str | None,
    pair_index: int,
    bad_mask: int,
    kind: str,
    detail: Any,
) -> None:
    if len(mismatches) < 50:
        mismatches.append(
            {
                "band": band,
                "pair_index": pair_index,
                "bad_mask": bad_mask,
                "kind": kind,
                "detail": detail,
            }
        )


def _write_new_json(path: Path, payload: Any) -> None:
    path = path.resolve()
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_apply_chunks(
    directory: Path,
    inputs: Sequence[list[list[int]]],
    *,
    chunk_size: int = 64,
) -> list[str]:
    directory = directory.resolve()
    if directory.exists():
        raise FileExistsError(f"refusing to overwrite {directory}")
    directory.mkdir(parents=True)
    files: list[str] = []
    for index, start in enumerate(range(0, len(inputs), chunk_size), start=1):
        filename = f"inputs-{index:03d}.json"
        _write_new_json(
            directory / filename,
            {"inputs": list(inputs[start : start + chunk_size])},
        )
        files.append(filename)
    _write_new_json(
        directory / "manifest.json",
        {
            "schema": "arcpuzzles-apply-input-chunks-v1",
            "task_id": TASK_ID,
            "total_inputs": len(inputs),
            "max_inputs_per_file": chunk_size,
            "files": files,
        },
    )
    return files


def run_probe(
    generator_path: str | Path,
    *,
    inputs_out: str | Path | None = None,
    inputs_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run the exhaustive probe and return a compact JSON-serializable report."""
    generator_path = Path(generator_path).resolve()
    generator = _load_generator(generator_path)
    mismatches: list[dict[str, Any]] = []
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    unique_outputs: set[tuple[tuple[int, ...], ...]] = set()
    default_probe_outputs: set[tuple[tuple[int, ...], ...]] = set()
    apply_inputs: list[list[list[int]]] = []
    valid_extra_census = {0: 0, 1: 0, 2: 0}
    cases = 0

    for band in BANDS:
        for pair_index in range(len(PAIRS)):
            for bad_mask in range(4):
                cases += 1
                requested = {"pair_index": pair_index, "bad_mask": bad_mask}
                try:
                    grid = generator.generate(
                        1701,
                        23,
                        difficulty=band,
                        **requested,
                    )
                except Exception as exc:  # report all domain failures together
                    _record_mismatch(
                        mismatches,
                        band=band,
                        pair_index=pair_index,
                        bad_mask=bad_mask,
                        kind="generate_exception",
                        detail=f"{type(exc).__name__}: {exc}",
                    )
                    continue

                frozen_input = _freeze(grid)
                unique_inputs.add(frozen_input)
                if band is None:
                    apply_inputs.append([list(row) for row in grid])

                errors = generator.self_check(
                    grid,
                    difficulty=band,
                    meta={"overrides": requested},
                )
                if errors:
                    _record_mismatch(
                        mismatches,
                        band=band,
                        pair_index=pair_index,
                        bad_mask=bad_mask,
                        kind="self_check",
                        detail=errors,
                    )

                observed = generator.observe_overrides(grid)
                if observed != requested:
                    _record_mismatch(
                        mismatches,
                        band=band,
                        pair_index=pair_index,
                        bad_mask=bad_mask,
                        kind="override_observation",
                        detail={"expected": requested, "observed": observed},
                    )

                expected = independent_rule(grid)
                actual = generator.rule_mirror(grid)
                unique_outputs.add(_freeze(expected))
                if actual != expected:
                    _record_mismatch(
                        mismatches,
                        band=band,
                        pair_index=pair_index,
                        bad_mask=bad_mask,
                        kind="rule_mirror",
                        detail="selected mirror disagrees with independent translation",
                    )

                if band is None and bad_mask == 0:
                    extras = sum(
                        color in (5, 8) for _, _, color in _symbols(expected)
                    )
                    if extras not in valid_extra_census:
                        _record_mismatch(
                            mismatches,
                            band=band,
                            pair_index=pair_index,
                            bad_mask=bad_mask,
                            kind="unexpected_extra_count",
                            detail=extras,
                        )
                    else:
                        valid_extra_census[extras] += 1

    expected_census = {0: 20, 1: 12, 2: 4}
    if valid_extra_census != expected_census:
        _record_mismatch(
            mismatches,
            band=None,
            pair_index=-1,
            bad_mask=-1,
            kind="valid_extra_census",
            detail={"expected": expected_census, "observed": valid_extra_census},
        )
    if len(unique_inputs) != 144:
        _record_mismatch(
            mismatches,
            band=None,
            pair_index=-1,
            bad_mask=-1,
            kind="unique_input_count",
            detail={"expected": 144, "observed": len(unique_inputs)},
        )
    # Every valid pair has its own rendered output, while all contaminated
    # cases collapse to the shared 16x16 color-7 result: 36 + 1 outputs.
    if len(unique_outputs) != 37:
        _record_mismatch(
            mismatches,
            band=None,
            pair_index=-1,
            bad_mask=-1,
            kind="unique_output_count",
            detail={"expected": 37, "observed": len(unique_outputs)},
        )

    for episode in range(24):
        for sample_index in range(6):
            grid = generator.generate(episode * 101, sample_index)
            default_probe_outputs.add(_freeze(independent_rule(grid)))
    expected_default_codom = int(getattr(generator, "EXPECTED_OUTPUT_CODOMAIN", -1))
    if len(default_probe_outputs) != expected_default_codom:
        _record_mismatch(
            mismatches,
            band=None,
            pair_index=-1,
            bad_mask=-1,
            kind="default_probe_unique_output_count",
            detail={
                "expected": expected_default_codom,
                "observed": len(default_probe_outputs),
            },
        )

    # De-duplicate while preserving pair-index/bad-mask enumeration order.
    ordered_unique: list[list[list[int]]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for grid in apply_inputs:
        frozen = _freeze(grid)
        if frozen not in seen:
            seen.add(frozen)
            ordered_unique.append(grid)
    if inputs_out is not None:
        _write_new_json(Path(inputs_out), {"inputs": ordered_unique})
    if inputs_dir is not None:
        _write_apply_chunks(Path(inputs_dir), ordered_unique)

    return {
        "schema": "reference-probe-56072bfdb820-v1",
        "task_id": TASK_ID,
        "status": "pass" if not mismatches else "fail",
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "bands": [band if band is not None else "default" for band in BANDS],
        "cases": cases,
        "unique_inputs": len(unique_inputs),
        "unique_outputs": len(unique_outputs),
        "default_probe_unique_outputs": len(default_probe_outputs),
        "valid_extra_census": {str(key): value for key, value in valid_extra_census.items()},
        "mismatches": mismatches,
    }


def _parser() -> argparse.ArgumentParser:
    default_generator = Path(__file__).resolve().parents[1] / "generator.py"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=default_generator)
    parser.add_argument("--out", type=Path, help="write compact report; refuses overwrite")
    parser.add_argument(
        "--inputs-out",
        type=Path,
        help="write all 144 unique exact-override inputs in one analysis file",
    )
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        help="write 64/64/16 chunks accepted by `arcpuzzles apply`",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = run_probe(
        args.generator,
        inputs_out=args.inputs_out,
        inputs_dir=args.inputs_dir,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        _write_new_json(args.out, report)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
