#!/usr/bin/env python3
"""Racket-backed episode-level selection-order prototype for 0a7f0faace31.

The canonical/default setting selects the first eligible component in row-major
object order.  The only alternate setting selects the last eligible component.
The production generator and selected canonical authority remain unchanged.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "0a7f0faace31"
SCHEMA = "0a7f0faace31-selection-order-prototype-v1"
PROTOTYPE_VERSION = "1.0.0"
SELECTION_ORDERS = ("first", "last")
DEFAULT_SELECTION_ORDER = "first"


def sha256(value: bytes | str) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("seed must be non-negative")
    return seed


def _validate_selection_order(selection_order: str) -> str:
    if type(selection_order) is not str or selection_order not in SELECTION_ORDERS:
        raise ValueError(
            f"selection_order must be exactly one of {SELECTION_ORDERS}, "
            f"got {selection_order!r}"
        )
    return selection_order


def canonical_rule(*, root: Path | str | None = None) -> str:
    """Load the one exact selected canonical program for this task."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    matches: list[str] = []
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record["program_solution"])
    unique = list(dict.fromkeys(matches))
    if len(unique) != 1:
        raise ValueError(
            f"expected one exact canonical rule for {TASK_ID}; found {len(unique)}"
        )
    return unique[0]


def instantiate_rule(
    selection_order: str = DEFAULT_SELECTION_ORDER,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact Racket program for one selection-order setting."""
    selection_order = _validate_selection_order(selection_order)
    source = canonical_rule(root=root)
    if selection_order == "first":
        return source
    if source.count("glyphs))") != 1:
        raise ValueError(
            "canonical selection site changed; manually reassess this prototype"
        )
    changed = source.replace("glyphs))", "(reverse glyphs)))", 1)
    if changed == source:
        raise ValueError("selection_order='last' did not change the authority")
    return changed


def choose_selection_order(seed: int) -> str:
    """Choose one hidden parameter value deterministically for a whole episode."""
    seed = _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}|selection-order|{seed}".encode()).digest()
    return SELECTION_ORDERS[digest[0] % len(SELECTION_ORDERS)]


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Independent same-color cardinal components in row-major discovery order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color in (5, 7) or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in (
                    (r - 1, c),
                    (r + 1, c),
                    (r, c - 1),
                    (r, c + 1),
                ):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (min(rows), min(columns), max(rows), max(columns)),
                }
            )
    return result


def apply_python(grid: list[list[int]], selection_order: str) -> list[list[int]]:
    """Independent mirror; retained labels are still produced by Racket."""
    selection_order = _validate_selection_order(selection_order)
    grid = normalize_grid(grid)
    guide_cells = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 7
    ]
    if not guide_cells:
        raise ValueError("input has no 7 guide cells")
    gr0 = min(row for row, _ in guide_cells)
    gc0 = min(column for _, column in guide_cells)
    gr1 = max(row for row, _ in guide_cells)
    gc1 = max(column for _, column in guide_cells)
    eligible = []
    for obj in _components(grid):
        r0, c0, r1, c1 = obj["bbox"]
        center = ((r0 + r1) // 2, (c0 + c1) // 2)
        if gr0 <= center[0] <= gr1 and gc0 <= center[1] <= gc1:
            eligible.append(obj)
    if not eligible:
        raise ValueError("input has no eligible component")
    selected = eligible[0] if selection_order == "first" else eligible[-1]
    r0, c0, r1, c1 = selected["bbox"]
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def generate_inputs(
    seed: int, *, root: Path | str | None = None
) -> list[list[list[int]]]:
    """Generate four lawful teaching inputs for one episode."""
    seed = _validate_seed(seed)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)
    sample_indices = (0, 1, 3, 4)
    bands = ("easy", "medium", "hard", "medium")
    styles = ("corners", "dashed", "two_corners", "corners")
    inputs = []
    for offset, (sample_index, band, style) in enumerate(
        zip(sample_indices, bands, styles)
    ):
        input_seed = 200_000 + seed * 101 + offset
        grid = generator.generate(
            input_seed,
            sample_index,
            difficulty=band,
            texture="teaching",
            frame_style=style,
        )
        problems = generator.self_check(grid, difficulty=band)
        if problems:
            raise RuntimeError(
                f"invalid parametric input {offset}: {problems}"
            )
        if generator.observe_overrides(grid)["texture"] != "teaching":
            raise RuntimeError(f"input {offset} lost the teaching witness")
        inputs.append(normalize_grid(grid))
    fingerprints = {
        json.dumps(grid, sort_keys=True, separators=(",", ":")) for grid in inputs
    }
    if len(fingerprints) != len(inputs):
        raise RuntimeError("prototype input sampler produced duplicate grids")
    return inputs


def build_episode(
    seed: int,
    *,
    selection_order: str | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build a complete four-pair episode with provisional Python labels."""
    seed = _validate_seed(seed)
    chosen = (
        choose_selection_order(seed)
        if selection_order is None
        else _validate_selection_order(selection_order)
    )
    inputs = generate_inputs(seed, root=root)
    return {
        "schema": SCHEMA,
        "seed": seed,
        "parameters": {"selection_order": chosen},
        "parameter_choice": (
            "sha256_seed_once_per_episode"
            if selection_order is None
            else "explicit_once_per_episode"
        ),
        "pairs": [
            {"input": grid, "output": apply_python(grid, chosen)}
            for grid in inputs
        ],
        "racket_program": instantiate_rule(chosen, root=root),
        "prototype_version": PROTOTYPE_VERSION,
    }


def _evaluate_racket(
    bridge: RacketBridge, program: str, grid: list[list[int]]
) -> list[list[int]]:
    bridge.define_grid("g", normalize_grid(grid))
    function = strip_rule_wrapper(program)
    return normalize_grid(bridge.eval_text(f"({function} g)"))


def _rotation_report(
    pairs: list[dict[str, Any]], rival_outputs: list[list[list[int]]]
) -> list[dict[str, Any]]:
    rotations = []
    for query_index in range(len(pairs)):
        demos = [index for index in range(len(pairs)) if index != query_index]
        refuting = [
            index
            for index in demos
            if rival_outputs[index] != pairs[index]["output"]
        ]
        query_differs = rival_outputs[query_index] != pairs[query_index]["output"]
        rotations.append(
            {
                "query_index": query_index,
                "demonstration_indices": demos,
                "refuting_demonstration_indices": refuting,
                "rival_fits_demonstrations": not refuting,
                "rival_query_differs": query_differs,
                "status": (
                    "ambiguous"
                    if not refuting and query_differs
                    else "no_ambiguity_found"
                ),
            }
        )
    return rotations


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return three labeled demonstrations and one unlabeled query."""
    pairs = episode["pairs"]
    return {
        "schema": "0a7f0faace31-selection-order-public-v1",
        "train": deepcopy(pairs[:3]),
        "test": [{"input": deepcopy(pairs[3]["input"])}],
    }


def _find_seed(order: str, start: int, used: set[int]) -> int:
    order = _validate_selection_order(order)
    seed = _validate_seed(start)
    while seed in used or choose_selection_order(seed) != order:
        seed += 1
    return seed


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def materialize(out: Path, *, seed_start: int = 1700) -> dict[str, Any]:
    """Execute both settings with Racket and retain public/private evidence."""
    seed_start = _validate_seed(seed_start)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    public_dir = out / "public"
    public_dir.mkdir()
    root = find_root(__file__)
    _, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    source_path = Path(__file__).resolve()

    used: set[int] = set()
    episodes = []
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for offset, order in enumerate(SELECTION_ORDERS):
            seed = _find_seed(order, seed_start + offset, used)
            used.add(seed)
            episode = build_episode(seed, root=root)
            if episode["parameters"]["selection_order"] != order:
                raise AssertionError("seed selection did not bind the requested order")

            program = episode["racket_program"]
            for pair in episode["pairs"]:
                racket_output = _evaluate_racket(bridge, program, pair["input"])
                python_output = apply_python(pair["input"], order)
                if racket_output != python_output:
                    raise AssertionError("Racket/Python prototype parity failure")
                pair["output"] = racket_output

            rival = next(value for value in SELECTION_ORDERS if value != order)
            rival_program = instantiate_rule(rival, root=root)
            rival_outputs = [
                _evaluate_racket(bridge, rival_program, pair["input"])
                for pair in episode["pairs"]
            ]
            rotations = _rotation_report(episode["pairs"], rival_outputs)
            if any(row["status"] != "no_ambiguity_found" for row in rotations):
                raise AssertionError("parameter rival survives a query rotation")
            if any(
                rival_output == pair["output"]
                for pair, rival_output in zip(episode["pairs"], rival_outputs)
            ):
                raise AssertionError("a prototype pair does not expose selection_order")

            public = public_challenge(episode)
            public_path = public_dir / f"selection_{order}_seed_{seed}.json"
            _write_json(public_path, public)
            episodes.append(
                {
                    **episode,
                    "program_sha256": sha256(program),
                    "counterfactual": {
                        "selection_order": rival,
                        "program": rival_program,
                        "program_sha256": sha256(rival_program),
                        "outputs": rival_outputs,
                    },
                    "rotation_checks": rotations,
                    "public_challenge": str(public_path.relative_to(out)),
                    "public_challenge_sha256": sha256(
                        json.dumps(public, sort_keys=True, separators=(",", ":"))
                    ),
                }
            )

    first_episode = next(
        row for row in episodes if row["parameters"]["selection_order"] == "first"
    )
    witness_input = first_episode["pairs"][0]["input"]
    witness = {
        "input": witness_input,
        "first_output": apply_python(witness_input, "first"),
        "last_output": apply_python(witness_input, "last"),
    }
    if witness["first_output"] == witness["last_output"]:
        raise AssertionError("retained parameter witness does not distinguish settings")

    report = {
        "schema": SCHEMA,
        "status": "prototype",
        "task_id": TASK_ID,
        "scope": (
            "Proposed task-local parametric extension only; canonical authority, "
            "production generation, and approval state are unchanged."
        ),
        "parameter_spec": {
            "selection_order": {
                "allowed": list(SELECTION_ORDERS),
                "original_default": DEFAULT_SELECTION_ORDER,
                "meaning": (
                    "Choose the first or last row-major 4-connected component "
                    "whose floored bbox center lies inside the all-7 guide bbox."
                ),
            }
        },
        "input_constraints": (
            "Each retained input is a lawful production teaching board with at "
            "least two eligible components whose raw crops differ."
        ),
        "invariant_reasoning": [
            "form the inclusive bbox of all 7 guide cells",
            "enumerate non-5/7 same-color 4-connected components in row-major order",
            "keep components whose floored bbox center lies inside the guide bbox",
            "choose according to the episode-level order and return its raw bbox crop",
        ],
        "canonical_default": {
            "selection_order": DEFAULT_SELECTION_ORDER,
            "program": canonical_rule(root=root),
            "program_sha256": sha256(canonical_rule(root=root)),
        },
        "distinguishing_witness": witness,
        "episodes": episodes,
        "prototype_source": str(source_path.relative_to(root)),
        "prototype_source_sha256": sha256(source_path.read_bytes()),
        "selected_generator": str(Path(generator_path).relative_to(root)),
        "selected_generator_sha256": generator_sha,
        "run_command": [
            "python3",
            "review.py",
            "run",
            "python3",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            "--out",
            "../checks/parametric",
        ],
        "limitations": [
            "Evidence covers one deterministic four-pair episode per setting, not every seed or every plausible selection policy.",
            "The alternate last-eligible rule is proposed only; it is not a canonical rule change or training approval.",
            "Inputs deliberately use the existing compound teaching construction; ordinary one-eligible boards cannot reveal this parameter.",
        ],
    }
    _write_json(out / "evidence.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=1700)
    args = parser.parse_args()
    report = materialize(args.out, seed_start=args.seed_start)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": [
                    {
                        "seed": row["seed"],
                        "selection_order": row["parameters"]["selection_order"],
                        "program_sha256": row["program_sha256"],
                        "public_challenge": row["public_challenge"],
                    }
                    for row in report["episodes"]
                ],
                "evidence": str(Path(args.out) / "evidence.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
