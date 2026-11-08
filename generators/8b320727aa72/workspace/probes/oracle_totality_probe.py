#!/usr/bin/env python3
"""Build a retained counterexample to the strongest canonical-fitting shortcut.

The canonical demonstrations and the production sampler contain only erasures:
foreground values in one anomalous tile become the tile background.  A plausible
shortcut therefore marks only such erasures, rather than marking every
cross-copy disagreement as the canonical Racket program does.

This probe starts from a fully lawful selected-generator sample, inserts one
novel color into a consensus-background coordinate of the anomalous tile, and
materializes both the intended total-rule mirror and the erasure-only rival.
The supported ``arcpuzzles apply`` command remains the label authority; its
result can be attached later with :func:`attach_racket_result`.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[4]
DEPENDENCY_ROOT = (
    REPO if (REPO / "RUNTIME_MANIFEST.json").is_file() else REPO / "shared" / "runtime"
)
if str(DEPENDENCY_ROOT) not in sys.path:
    sys.path.insert(0, str(DEPENDENCY_ROOT))

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "8b320727aa72"
PROBE_VERSION = "oracle-totality-novel-color-v1"
SEED = 20261023
SAMPLE_INDEX = 7
DIFFICULTY = "medium"
OVERRIDES = {
    "n_filled_in_tile": 5,
    "n_disagreements": 1,
    "palette_size": 1,
    "background_color": 8,
    "separator_color": 3,
    "corrupt_tile_index": 24,
    "anchor_position": True,
    "tile_layout": "scattered",
    "disagreement_distribution": "spread",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _erasure_only_rival_output(generator: Any, grid: list[list[int]]) -> list[list[int]]:
    """Mark only foreground-to-background differences; ignore insertions/substitutions."""
    analysis = generator._analyze(grid)
    background = analysis["background_color"]
    output = [list(row) for row in analysis["consensus"]]
    for row, col in analysis["disagreements"]:
        if analysis["consensus"][row][col] != background and analysis["anomaly"][row][col] == background:
            output[row][col] = 1
    return output


def _canonical_rival_fit(generator: Any, root: Path) -> dict[str, Any]:
    """Check the rival against every stored canonical labelled pair for the task."""
    pairs = []
    for line_number, line in enumerate(
        canonical_path(root).read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        row_pairs = list(row.get("train", []))
        test = row.get("test", [])
        if isinstance(test, dict):
            row_pairs.append(test)
        elif isinstance(test, list):
            row_pairs.extend(test)
        for pair_index, pair in enumerate(row_pairs):
            pairs.append((line_number, pair_index, pair))

    fits = 0
    errors = []
    for line_number, pair_index, pair in pairs:
        try:
            predicted = _erasure_only_rival_output(generator, pair["input"])
            if predicted == pair["output"]:
                fits += 1
            else:
                errors.append(
                    {
                        "line": line_number,
                        "pair_index": pair_index,
                        "kind": "output_mismatch",
                    }
                )
        except Exception as exc:  # noqa: BLE001 - retained audit evidence
            errors.append(
                {
                    "line": line_number,
                    "pair_index": pair_index,
                    "kind": "execution_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
    return {"pairs": len(pairs), "fits": fits, "errors": errors}


def _choose_novel_color(grid: list[list[int]], *, background: int, separator: int) -> int:
    present = {value for row in grid for value in row}
    candidates = [
        color
        for color in range(10)
        if color not in present and color not in {1, background, separator}
    ]
    if not candidates:
        candidates = [
            color
            for color in range(10)
            if color not in {1, background, separator}
        ]
    if not candidates:
        raise ValueError("no legal novel non-marker color is available")
    return candidates[0]


def build_counterexample(*, root: Path | str | None = None) -> dict[str, Any]:
    """Return one exact input separating canonical totality from erasure-only marking."""
    resolved_root = Path(root).resolve() if root is not None else find_root(__file__)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID,
        root=resolved_root,
    )
    base = generator.generate(
        SEED,
        SAMPLE_INDEX,
        difficulty=DIFFICULTY,
        **OVERRIDES,
    )
    base_errors = generator.self_check(base, difficulty=DIFFICULTY)
    if base_errors:
        raise AssertionError(f"fixed base sample left the generator domain: {base_errors}")
    base_analysis = generator._analyze(base)
    background = base_analysis["background_color"]
    separator = base_analysis["separator_color"]

    insertion = next(
        (row, col)
        for row in range(5)
        for col in range(5)
        if base_analysis["consensus"][row][col] == background
        and base_analysis["anomaly"][row][col] == background
    )
    inserted_color = _choose_novel_color(
        base,
        background=background,
        separator=separator,
    )
    counterexample = deepcopy(base)
    tile_index = base_analysis["corrupt_tile_index"]
    tile_row, tile_col = divmod(tile_index, 5)
    local_row, local_col = insertion
    global_row = tile_row * 6 + local_row
    global_col = tile_col * 6 + local_col
    counterexample[global_row][global_col] = inserted_color

    intended = generator._canonical_mark_output(counterexample)
    rival = _erasure_only_rival_output(generator, counterexample)
    if intended == rival:
        raise AssertionError("counterexample failed to separate the intended and rival rules")
    if intended[local_row][local_col] != 1 or rival[local_row][local_col] != background:
        raise AssertionError("counterexample does not disagree at the injected coordinate")
    base_intended = generator._canonical_mark_output(base)
    base_rival = _erasure_only_rival_output(generator, base)
    if base_intended != base_rival:
        raise AssertionError("erasure-only rival unexpectedly fails the lawful base grammar")

    canonical_fit = _canonical_rival_fit(generator, resolved_root)
    generator_path = Path(generator_path)
    return {
        "schema": "8b320727aa72-oracle-totality-counterexample-v1",
        "task_id": TASK_ID,
        "probe_version": PROBE_VERSION,
        "claim": (
            "The erasure-only rival fits the canonical erasure demonstrations but "
            "fails the canonical total rule on a background-to-novel-color disagreement."
        ),
        "base_generation": {
            "seed": SEED,
            "sample_index": SAMPLE_INDEX,
            "difficulty": DIFFICULTY,
            "overrides": OVERRIDES,
        },
        "base_generator_domain_errors": base_errors,
        "counterexample_domain_errors": generator.self_check(
            counterexample,
            difficulty=DIFFICULTY,
        ),
        "rival_fits_canonical_erasure_grammar": base_intended == base_rival,
        "canonical_rival_fit": canonical_fit,
        "rival_fits_all_canonical_demonstrations": (
            canonical_fit["pairs"] > 0
            and canonical_fit["fits"] == canonical_fit["pairs"]
            and not canonical_fit["errors"]
        ),
        "production_generator_emits_counterexample_class": False,
        "production_exclusion_reason": (
            "self_check requires every anomaly difference to erase a consensus "
            "foreground value to background"
        ),
        "corrupt_tile_index": tile_index,
        "local_insertion_coordinate": [local_row, local_col],
        "global_insertion_coordinate": [global_row, global_col],
        "background_color": background,
        "separator_color": separator,
        "inserted_color": inserted_color,
        "input": counterexample,
        "intended_python_mirror": intended,
        "erasure_only_rival_output": rival,
        "racket_output": None,
        "racket_verified": False,
        "sources": {
            "generator": str(generator_path.relative_to(resolved_root)),
            "generator_sha256": generator_sha256,
            "probe": str(Path(__file__).resolve().relative_to(resolved_root)),
            "probe_sha256": _sha256_file(Path(__file__).resolve()),
        },
    }


def _extract_apply_output(payload: Any) -> list[list[int]]:
    """Accept the supported apply receipt shapes used by repository versions."""
    if isinstance(payload, dict):
        for key in ("output", "racket_output"):
            value = payload.get(key)
            if isinstance(value, list) and value and isinstance(value[0], list):
                return value
        for key in ("results", "items", "applications"):
            value = payload.get(key)
            if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
                return _extract_apply_output(value[0])
    raise ValueError("could not locate one grid output in the apply receipt")


def attach_racket_result(case: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Bind the supported Racket receipt and reject any mirror disagreement."""
    finalized = deepcopy(case)
    racket_output = _extract_apply_output(receipt)
    if racket_output != finalized["intended_python_mirror"]:
        raise AssertionError("supported Racket output disagrees with intended mirror")
    if racket_output == finalized["erasure_only_rival_output"]:
        raise AssertionError("supported Racket output did not separate the rival")
    finalized["racket_output"] = racket_output
    finalized["racket_verified"] = True
    finalized["apply_receipt"] = receipt
    return finalized


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--racket-result", type=Path)
    args = parser.parse_args(argv)

    case = build_counterexample()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.out_dir / "input.json", case["input"])
    if args.racket_result is not None:
        receipt = json.loads(args.racket_result.read_text(encoding="utf-8"))
        case = attach_racket_result(case, receipt)
    _write_json(args.out_dir / "counterexample.json", case)
    print(args.out_dir / "counterexample.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
