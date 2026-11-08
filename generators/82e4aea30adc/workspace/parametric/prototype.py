#!/usr/bin/env python3
"""Task-local episode-level interior-area threshold prototype."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "82e4aea30adc"
ALLOWED_THRESHOLDS = (1, 2)
DEFAULT_THRESHOLD = 1

_CANONICAL_TEST = "(fc (if (= (* ih iw) 1) 5 7))"
_THRESHOLD_TWO_TEST = "(fc (if (<= (* ih iw) 2) 5 7))"
_CANONICAL_COMMENT = (
    ";; A one-cell interior is gray; every larger interior is orange."
)
_THRESHOLD_TWO_COMMENT = (
    ";; Interiors of area at most two are gray; larger interiors are orange."
)
_LEGAL_FRAME_COLORS = (1, 2, 3, 4, 6, 8, 9)
_SHAPE_SETS = (
    ((3, 3), (3, 4), (3, 5)),
    ((3, 3), (4, 3), (4, 4)),
    ((3, 3), (3, 4), (5, 3)),
    ((3, 3), (4, 3), (3, 6)),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_program(root: str | Path) -> str:
    matches: list[dict[str, Any]] = []
    with canonical_path(root).open() as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one canonical row for {TASK_ID}")
    return str(matches[0]["program_solution"])


def render_program(
    canonical: str,
    gray_max_interior_area: int = DEFAULT_THRESHOLD,
) -> str:
    if (
        type(gray_max_interior_area) is not int
        or gray_max_interior_area not in ALLOWED_THRESHOLDS
    ):
        raise ValueError(
            f"gray_max_interior_area must be one of {ALLOWED_THRESHOLDS}"
        )
    if not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("canonical program is not wrapped with rule!")
    if gray_max_interior_area == DEFAULT_THRESHOLD:
        return canonical
    if canonical.count(_CANONICAL_TEST) != 1:
        raise ValueError("canonical area test was not found exactly once")
    program = canonical.replace(_CANONICAL_TEST, _THRESHOLD_TWO_TEST, 1)
    if program.count(_CANONICAL_COMMENT) == 1:
        program = program.replace(
            _CANONICAL_COMMENT,
            _THRESHOLD_TWO_COMMENT,
            1,
        )
    return program


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
    expression = f"({body} g)" if body.lstrip().startswith("(lambda") else body
    output = bridge.eval_text(expression)
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(
            not isinstance(row, list) or len(row) != len(output[0])
            for row in output
        )
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def _draw_outline(
    grid: list[list[int]],
    row: int,
    col: int,
    height: int,
    width: int,
    color: int,
) -> None:
    for rr in range(row, row + height):
        for cc in range(col, col + width):
            if rr in (row, row + height - 1) or cc in (
                col,
                col + width - 1,
            ):
                grid[rr][cc] = color


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Four lawful scenes, each containing interior areas 1, 2, and >2."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    rng = random.Random(seed ^ 0x82E4AEA3)
    grids: list[list[list[int]]] = []
    height, width = 11, 23
    columns = (1, 7, 14)
    for shapes in _SHAPE_SETS:
        grid = [[0] * width for _ in range(height)]
        colors = rng.sample(_LEGAL_FRAME_COLORS, len(shapes))
        for (frame_h, frame_w), col, color in zip(shapes, columns, colors):
            row = 1 + rng.randrange(height - frame_h - 1)
            _draw_outline(grid, row, col, frame_h, frame_w, color)
        grids.append(grid)
    return grids


def _build_episode(
    seed: int,
    threshold: int,
    canonical: str,
    bridge: RacketBridge,
) -> dict[str, Any]:
    root = find_root(__file__)
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    programs = {
        value: render_program(canonical, value) for value in ALLOWED_THRESHOLDS
    }
    rival_threshold = next(
        value for value in ALLOWED_THRESHOLDS if value != threshold
    )
    pairs: list[dict[str, list[list[int]]]] = []
    rival_outputs: list[list[list[int]]] = []
    for grid in fixture_inputs(seed):
        errors = generator.self_check(grid)
        if errors:
            raise ValueError("prototype fixture is not canonical-like: " + errors[0])
        chosen_output = execute(bridge, programs[threshold], grid)
        rival_output = execute(bridge, programs[rival_threshold], grid)
        pairs.append({"input": grid, "output": chosen_output})
        rival_outputs.append(rival_output)
    demo_differences = [
        index
        for index, pair in enumerate(pairs[:3])
        if pair["output"] != rival_outputs[index]
    ]
    query_differs = pairs[3]["output"] != rival_outputs[3]
    if query_differs and not demo_differences:
        raise ValueError("query distinction is absent from demonstrations")
    return {
        "schema": "82e4aea30adc-parametric-interior-threshold-v1",
        "seed": seed,
        "parameters": {"gray_max_interior_area": threshold},
        "program": programs[threshold],
        "program_sha256": sha256_bytes(programs[threshold].encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rival": {
            "gray_max_interior_area": rival_threshold,
            "demo_differences": demo_differences,
            "query_differs": query_differs,
            "status": "distinguished" if demo_differences else "ambiguous",
            "outputs": {
                "train": rival_outputs[:3],
                "test": rival_outputs[3:],
            },
        },
        "label_authority": (
            "included Racket bridge executing the exact instantiated program"
        ),
    }


def generate_episode(
    seed: int,
    *,
    gray_max_interior_area: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose the threshold once and keep it fixed for all four pairs."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    if gray_max_interior_area is None:
        threshold = random.Random(seed).choice(ALLOWED_THRESHOLDS)
    else:
        if (
            type(gray_max_interior_area) is not int
            or gray_max_interior_area not in ALLOWED_THRESHOLDS
        ):
            raise ValueError(
                f"gray_max_interior_area must be one of {ALLOWED_THRESHOLDS}"
            )
        threshold = gray_max_interior_area
    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, threshold, canonical, bridge)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, threshold, canonical, owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def materialize(output: str | Path, *, seed: int = 23) -> dict[str, Any]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    source_paths = [
        Path(__file__),
        Path(__file__).parents[2] / "tests" / "test_parametric_threshold.py",
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
            generate_episode(
                seed + index,
                gray_max_interior_area=threshold,
                bridge=bridge,
            )
            for index, threshold in enumerate(ALLOWED_THRESHOLDS)
        ]
        witness_input = fixture_inputs(seed)[0]
        witness_outputs = {
            str(threshold): execute(
                bridge,
                render_program(canonical, threshold),
                witness_input,
            )
            for threshold in ALLOWED_THRESHOLDS
        }
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        episode["prototype_source_sha256"] = source_hashes
        _write_json(
            output / "public" / f"episode-{index}.json",
            public_challenge(episode),
        )
        _write_json(output / "private" / f"episode-{index}.json", episode)
        (output / "private" / f"program-{index}.rkt").write_text(
            episode["program"]
        )

    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "different": witness_outputs["1"] != witness_outputs["2"],
    }
    _write_json(output / "private" / "witness.json", witness)
    report = {
        "schema": "82e4aea30adc-parametric-interior-threshold-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameters": {
            "gray_max_interior_area": list(ALLOWED_THRESHOLDS)
        },
        "default": DEFAULT_THRESHOLD,
        "default_program_exact_canonical": (
            episodes[0]["program"] == canonical
        ),
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
            "Only thresholds 1 and 2 are proposed; threshold 1 is the unchanged canonical program.",
            "The parameter is selected once per episode, never per example or object.",
            "Evidence covers two retained seeds and four controlled lawful inputs per episode.",
            "Every fixture contains interior areas 1, 2, and greater than 2.",
            "This task-local prototype has no production API or approval claim.",
        ],
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=23)
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
