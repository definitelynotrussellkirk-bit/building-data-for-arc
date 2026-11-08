#!/usr/bin/env python3
"""Task-local episode-level threshold prototype; not a production rule API."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root

TASK_ID = "ad92d10d919c"
ALLOWED_THRESHOLDS = (3, 4)
DEFAULT_THRESHOLD = 4

_THRESHOLD_THREE_PROGRAM = """(rule! (let ((dummy 0))
  (for*/fold ((out g)) ((r (in-range 1 (- (rows g) 1)))
                         (c (in-range 1 (- (cols g) 1))))
    (let* ((a (at g (- r 1) (- c 1)))
           (b (at g (- r 1) (+ c 1)))
           (d (at g (+ r 1) (- c 1)))
           (e (at g (+ r 1) (+ c 1)))
           (v (cond
                ((and (not (= a 0))
                      (or (and (= b a) (= d a))
                          (and (= b a) (= e a))
                          (and (= d a) (= e a)))) a)
                ((and (not (= b 0)) (= d b) (= e b)) b)
                (else 0))))
      (if (and (= (at g r c) 0) (not (= v 0)))
          (set-cell out r c v)
          out)))))"""


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


def render_program(canonical: str, required_matches: int = DEFAULT_THRESHOLD) -> str:
    if type(required_matches) is not int or required_matches not in ALLOWED_THRESHOLDS:
        raise ValueError(f"required_matches must be one of {ALLOWED_THRESHOLDS}")
    if not canonical.startswith("(rule! ") or not canonical.endswith(")"):
        raise ValueError("canonical program is not wrapped with rule!")
    if required_matches == DEFAULT_THRESHOLD:
        return canonical
    return _THRESHOLD_THREE_PROGRAM


def execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute exact Racket program bytes with the input bound to ``g``."""
    if not program.startswith("(rule! ") or not program.endswith(")"):
        raise ValueError("expected rule! wrapper")
    bridge.define_grid("g", grid)
    output = bridge.eval_text(program[len("(rule! ") : -1])
    if (
        not isinstance(output, list)
        or not output
        or not isinstance(output[0], list)
        or not output[0]
        or any(not isinstance(row, list) or len(row) != len(output[0]) for row in output)
    ):
        raise ValueError("Racket program did not return a nonempty rectangular grid")
    return output


def _corners(center: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    row, col = center
    return (
        (row - 1, col - 1),
        (row - 1, col + 1),
        (row + 1, col - 1),
        (row + 1, col + 1),
    )


def fixture_inputs(seed: int) -> list[list[list[int]]]:
    """Four controlled inputs; every one distinguishes threshold 3 from 4."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    rng = random.Random(seed ^ 0xAD92D10D)
    grids = []
    shapes = ((7, 9), (8, 10), (7, 10), (8, 9))
    for index, (height, width) in enumerate(shapes):
        grid = [[0] * width for _ in range(height)]
        full_center = (1, 1)
        partial_center = (height - 2, 1)
        mixed_center = (2, width - 3)
        colors = rng.sample(range(1, 10), 4)

        for row, col in _corners(full_center):
            grid[row][col] = colors[0]

        missing = (index + rng.randrange(4)) % 4
        for corner_index, (row, col) in enumerate(_corners(partial_center)):
            if corner_index != missing:
                grid[row][col] = colors[1]

        mixed = (colors[2], colors[3], colors[3], colors[2])
        if index % 2:
            mixed = (colors[2], colors[3], colors[2], colors[3])
        for (row, col), color in zip(_corners(mixed_center), mixed):
            grid[row][col] = color
        grids.append(grid)
    return grids


def _build_episode(
    seed: int,
    threshold: int,
    canonical: str,
    bridge: RacketBridge,
) -> dict[str, Any]:
    programs = {value: render_program(canonical, value) for value in ALLOWED_THRESHOLDS}
    rival_threshold = next(value for value in ALLOWED_THRESHOLDS if value != threshold)
    pairs = []
    rival_outputs = []
    for grid in fixture_inputs(seed):
        chosen_output = execute(bridge, programs[threshold], grid)
        rival_output = execute(bridge, programs[rival_threshold], grid)
        pairs.append({"input": grid, "output": chosen_output})
        rival_outputs.append(rival_output)
    demo_differences = [
        index for index, pair in enumerate(pairs[:3]) if pair["output"] != rival_outputs[index]
    ]
    query_differs = pairs[3]["output"] != rival_outputs[3]
    if query_differs and not demo_differences:
        raise ValueError("query needs a threshold distinction absent from demonstrations")
    return {
        "schema": "ad92d10d919c-parametric-threshold-v1",
        "seed": seed,
        "parameters": {"required_matches": threshold},
        "program": programs[threshold],
        "program_sha256": sha256_bytes(programs[threshold].encode()),
        "train": pairs[:3],
        "test": pairs[3:],
        "rival": {
            "required_matches": rival_threshold,
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
    required_matches: int | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose the threshold once, then keep it fixed for all four pairs."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (bool is not accepted)")
    if required_matches is None:
        threshold = random.Random(seed).choice(ALLOWED_THRESHOLDS)
    else:
        if type(required_matches) is not int or required_matches not in ALLOWED_THRESHOLDS:
            raise ValueError(f"required_matches must be one of {ALLOWED_THRESHOLDS}")
        threshold = required_matches
    root = find_root(__file__)
    canonical = canonical_program(root)
    if bridge is not None:
        return _build_episode(seed, threshold, canonical, bridge)
    with RacketBridge() as owned_bridge:
        return _build_episode(seed, threshold, canonical, owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
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
    with RacketBridge() as bridge:
        episodes = [
            generate_episode(seed + index, required_matches=threshold, bridge=bridge)
            for index, threshold in enumerate((4, 3))
        ]
        witness_input = fixture_inputs(seed)[0]
        canonical = canonical_program(root)
        witness_outputs = {
            str(threshold): execute(bridge, render_program(canonical, threshold), witness_input)
            for threshold in ALLOWED_THRESHOLDS
        }
        runtime_identity = bridge.runtime_identity

    for index, episode in enumerate(episodes):
        episode["prototype_source_sha256"] = source_hashes
        _write_json(output / "public" / f"episode-{index}.json", public_challenge(episode))
        _write_json(output / "private" / f"episode-{index}.json", episode)
        (output / "private" / f"program-{index}.rkt").write_text(episode["program"])

    witness = {
        "input": witness_input,
        "outputs": witness_outputs,
        "different": witness_outputs["3"] != witness_outputs["4"],
    }
    _write_json(output / "private" / "witness.json", witness)
    report = {
        "schema": "ad92d10d919c-parametric-threshold-report-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameters": {"required_matches": list(ALLOWED_THRESHOLDS)},
        "default": DEFAULT_THRESHOLD,
        "default_program_exact_canonical": episodes[0]["program"] == canonical_program(root),
        "complete_episodes": len(episodes),
        "pairs_per_episode": {"train": 3, "test": 1},
        "all_labels_and_rivals_executed_in_racket": True,
        "all_demonstrations_refute_other_declared_setting": all(
            episode["rival"]["demo_differences"] == [0, 1, 2] for episode in episodes
        ),
        "runtime_identity": runtime_identity,
        "source_sha256": source_hashes,
        "limitations": [
            "Only thresholds 3 and 4 are proposed; threshold 4 is the unchanged canonical program.",
            "Evidence covers two retained episode seeds and four controlled inputs per episode.",
            "Fixtures contain one full X, one three-corner X, and one mixed 2+2 control.",
            "Only the declared alternative threshold is exhaustively compared on these finite episodes.",
            "This task-local prototype has no production API, approval, or universal-seed claim.",
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
    print(json.dumps({
        "status": report["status"],
        "complete_episodes": report["complete_episodes"],
        "out": str(args.out),
    }))


if __name__ == "__main__":
    main()
