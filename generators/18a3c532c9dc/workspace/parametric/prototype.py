#!/usr/bin/env python3
"""Task-local episode-level quadrant-priority prototype; not a production API."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "18a3c532c9dc"
ALLOWED_PRIORITY_MODES = ("canonical", "reversed")
DEFAULT_PRIORITY_MODE = "canonical"

_CANONICAL_STEPS = """                                (v tl)
                                (v (if (!= br 0) br v))
                                (v (if (!= bl 0) bl v))
                                (v (if (!= tr 0) tr v)))"""
_REVERSED_STEPS = """                                (v tr)
                                (v (if (!= bl 0) bl v))
                                (v (if (!= br 0) br v))
                                (v (if (!= tl 0) tl v)))"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_program(root: str | Path) -> str:
    matches = []
    with canonical_path(root).open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    return matches[0]["program_solution"]


def render_program(
    canonical: str,
    priority_mode: str = DEFAULT_PRIORITY_MODE,
) -> str:
    """Instantiate one exact Racket rule for the episode's fixed priority mode."""
    if priority_mode not in ALLOWED_PRIORITY_MODES:
        raise ValueError(f"priority_mode must be one of {ALLOWED_PRIORITY_MODES}")
    if not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("canonical program is not wrapped with rule!")
    if priority_mode == DEFAULT_PRIORITY_MODE:
        return canonical
    if canonical.count(_CANONICAL_STEPS) != 1:
        raise ValueError("canonical priority steps did not match the pinned task rule")
    return canonical.replace(_CANONICAL_STEPS, _REVERSED_STEPS, 1)


def execute(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute exact Racket program bytes with the input bound to ``g``."""
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected rule! wrapper")
    bridge.define_grid("g", grid)
    body = program[len("(rule! ") : -1]
    output = bridge.eval_text(f"({body} g)")
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def _place(
    grid: list[list[int]],
    half_height: int,
    half_width: int,
    colors: dict[str, int],
    row: int,
    col: int,
    quadrants: tuple[str, ...],
) -> None:
    for quadrant in quadrants:
        row0 = half_height if quadrant in ("bl", "br") else 0
        col0 = half_width if quadrant in ("tr", "br") else 0
        grid[row0 + row][col0 + col] = colors[quadrant]


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Four lawful inputs; every one distinguishes the two priority modes."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    rng = random.Random(seed ^ 0x18A3C532)
    shapes = ((8, 8), (8, 10), (10, 8), (10, 10))
    grids = []
    for height, width in shapes:
        half_height, half_width = height // 2, width // 2
        palette = rng.sample(range(1, 10), 4)
        colors = dict(zip(("tl", "tr", "bl", "br"), palette))
        grid = [[0] * width for _ in range(height)]
        coordinates = [
            (row, col)
            for row in range(half_height)
            for col in range(half_width)
        ]
        rng.shuffle(coordinates)

        # These shuffled witnesses make both rule settings disagree while
        # retaining the original four-quadrant overlay reasoning structure.
        roles = (
            ("tl", "tr", "bl", "br"),
            ("tl", "br"),
            ("bl", "tr"),
            ("br", "bl"),
        )
        for (row, col), occupied in zip(coordinates[:4], roles):
            _place(
                grid,
                half_height,
                half_width,
                colors,
                row,
                col,
                occupied,
            )

        for row, col in coordinates[4:]:
            for quadrant in ("tl", "tr", "bl", "br"):
                if rng.random() < 0.22:
                    _place(
                        grid,
                        half_height,
                        half_width,
                        colors,
                        row,
                        col,
                        (quadrant,),
                    )
        grids.append(grid)
    return grids


def _build_episode(
    seed: int,
    priority_mode: str,
    canonical: str,
    bridge: RacketBridge,
) -> dict[str, Any]:
    programs = {
        mode: render_program(canonical, mode)
        for mode in ALLOWED_PRIORITY_MODES
    }
    rival_mode = next(mode for mode in ALLOWED_PRIORITY_MODES if mode != priority_mode)
    pairs = []
    rival_outputs = []
    for grid in fixture_inputs(seed):
        chosen_output = execute(bridge, programs[priority_mode], grid)
        rival_output = execute(bridge, programs[rival_mode], grid)
        pairs.append({"input": grid, "output": chosen_output})
        rival_outputs.append(rival_output)

    demo_differences = [
        index
        for index, pair in enumerate(pairs[:3])
        if pair["output"] != rival_outputs[index]
    ]
    query_differs = pairs[3]["output"] != rival_outputs[3]
    if query_differs and not demo_differences:
        raise ValueError("query needs a priority distinction absent from demonstrations")
    return {
        "schema": "18a3c532c9dc-parametric-priority-v1",
        "seed": seed,
        "parameters": {"priority_mode": priority_mode},
        "program": programs[priority_mode],
        "program_sha256": sha256_bytes(programs[priority_mode].encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rival": {
            "priority_mode": rival_mode,
            "demo_differences": demo_differences,
            "query_differs": query_differs,
            "status": "distinguished" if demo_differences else "ambiguous",
            "outputs": {"train": rival_outputs[:3], "test": rival_outputs[3:]},
        },
        "label_authority": "included Racket bridge executing exact instantiated program",
    }


def generate_episode(
    seed: int,
    *,
    priority_mode: str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one priority mode, then keep it fixed for all episode pairs."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    if priority_mode is None:
        selected_mode = random.Random(seed ^ 0x75B8110E).choice(ALLOWED_PRIORITY_MODES)
    else:
        if priority_mode not in ALLOWED_PRIORITY_MODES:
            raise ValueError(f"priority_mode must be one of {ALLOWED_PRIORITY_MODES}")
        selected_mode = priority_mode

    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, selected_mode, canonical, bridge)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, selected_mode, canonical, owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize(output: str | Path, *, seed: int = 75) -> dict[str, Any]:
    """Write two complete episodes and source-bound finite execution evidence."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source_paths = [
        Path(__file__),
        Path(__file__).parents[2] / "tests" / "test_parametric_priority.py",
        Path(__file__).parent / "README.md",
    ]
    source_hashes = {
        str(path.relative_to(root)): sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }

    canonical = canonical_program(root)
    with RacketBridge() as bridge:
        episodes = [
            generate_episode(seed + index, priority_mode=mode, bridge=bridge)
            for index, mode in enumerate(ALLOWED_PRIORITY_MODES)
        ]
        witness_input = fixture_inputs(seed)[0]
        witness_outputs = {
            mode: execute(bridge, render_program(canonical, mode), witness_input)
            for mode in ALLOWED_PRIORITY_MODES
        }
        canonical_checks = []
        for index, pair in enumerate(canonical_pairs(TASK_ID, root=root)):
            actual = execute(bridge, canonical, pair["input"])
            canonical_checks.append(
                {
                    "pair_index": index,
                    "input_sha256": sha256_bytes(
                        json.dumps(pair["input"], separators=(",", ":")).encode()
                    ),
                    "matches": actual == pair["output"],
                }
            )
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        episode["prototype_source_sha256"] = source_hashes
        _write_json(output / "public" / f"episode-{index}.json", public_challenge(episode))
        _write_json(output / "private" / f"episode-{index}.json", episode)
        mode = episode["parameters"]["priority_mode"]
        (output / "private" / f"program-{mode}.rkt").write_text(episode["program"])

    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "different": witness_outputs["canonical"] != witness_outputs["reversed"],
    }
    _write_json(output / "private" / "setting-difference-witness.json", witness)
    _write_json(
        output / "private" / "canonical-default-check.json",
        {
            "all_match": all(row["matches"] for row in canonical_checks),
            "pairs": canonical_checks,
        },
    )

    report = {
        "schema": "18a3c532c9dc-parametric-priority-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameters": {"priority_mode": list(ALLOWED_PRIORITY_MODES)},
        "orders_high_to_low": {
            "canonical": ["tr", "bl", "br", "tl"],
            "reversed": ["tl", "br", "bl", "tr"],
        },
        "default": DEFAULT_PRIORITY_MODE,
        "default_program_exact_canonical": episodes[0]["program"] == canonical,
        "canonical_pairs_checked": len(canonical_checks),
        "canonical_pairs_all_match": all(row["matches"] for row in canonical_checks),
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2]
            for episode in episodes
        ),
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only the canonical priority chain and its complete reversal are proposed.",
            "Evidence covers two retained episode seeds and four controlled inputs per episode.",
            "Every fixture intentionally contains shuffled precedence conflicts, so this is instructional rather than naturalistic sampling.",
            "Only the declared opposite priority setting is compared on these finite episodes.",
            "This task-local prototype has no production API, approval, or universal-seed claim.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=75)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "out": str(args.out),
            }
        )
    )


if __name__ == "__main__":
    main()
