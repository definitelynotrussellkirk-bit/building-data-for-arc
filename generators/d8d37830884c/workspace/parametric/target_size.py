#!/usr/bin/env python3
"""Isolated episode-level target-component-size prototype for d8d37830884c.

The hidden parameter is selected once per episode. Every input contains separate
same-colour 4-connected objects of sizes 5, 6, and 7 (plus a size-3 distractor),
so demonstrations identify which cardinality is recoloured red. All retained
labels and rival predictions are executed by the included Racket bridge.

This module is not imported by the selected production generator.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "d8d37830884c"
VERSION = "0.1.0-prototype"
TARGET_SIZES = (5, 6, 7)
DEFAULT_TARGET_SIZE = 6

Cell = tuple[int, int]
Grid = list[list[int]]

_SHAPES: dict[int, tuple[Cell, ...]] = {
    3: ((0, 0), (0, 1), (1, 0)),
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
}
_SLOTS = ((0, 0), (0, 6), (6, 0), (6, 6))


def _root(root=None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_record(root=None) -> dict[str, Any]:
    matches = []
    with canonical_path(_root(root)).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                matches.append(record)
    if not matches:
        raise ValueError(f"expected a canonical record for {TASK_ID}, found none")

    programs = {record.get("program_solution") for record in matches}
    if len(programs) != 1:
        raise ValueError(
            f"canonical records for {TASK_ID} disagree on program_solution"
        )

    return next(
        (
            record
            for record in matches
            if record.get("content_hash") == TASK_ID
            and record.get("parent_hash") is None
        ),
        matches[0],
    )


def _validate_target_size(target_size: Any) -> int:
    if type(target_size) is not int or target_size not in TARGET_SIZES:
        raise ValueError(f"target_size must be one of {TARGET_SIZES}")
    return target_size


def materialize_program(target_size=DEFAULT_TARGET_SIZE, *, root=None) -> str:
    """Return exact canonical bytes for 6 and a one-token size variant otherwise."""
    selected = _validate_target_size(target_size)
    canonical = canonical_record(root)["program_solution"]
    if selected == DEFAULT_TARGET_SIZE:
        return canonical
    needle = "(= (obj-size obj) 6)"
    if canonical.count(needle) != 1:
        raise ValueError("canonical rule no longer has the expected unique size-6 predicate")
    return canonical.replace(needle, f"(= (obj-size obj) {selected})", 1)


def choose_target_size(seed, selection="seeded") -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if selection == "seeded":
        digest = hashlib.sha256(
            f"{TASK_ID}:{VERSION}:{seed}:target-size".encode("utf-8")
        ).digest()
        return TARGET_SIZES[int.from_bytes(digest[:8], "big") % len(TARGET_SIZES)]
    return _validate_target_size(selection)


def execute_program(bridge: RacketBridge, program: str, grid) -> Grid:
    """Execute an exact ``(rule! (lambda ...))`` program on one grid."""
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith(("(lambda", "(λ")):
        raise ValueError("prototype expects a lambda-bodied rule")
    bridge.define_grid("__target_size_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({body} __target_size_input__)"))


def _bridge_context(bridge):
    return (
        nullcontext(bridge)
        if bridge is not None
        else RacketBridge(timeout=10, startup_timeout=60)
    )


def _normalize(cells: tuple[Cell, ...]) -> tuple[Cell, ...]:
    top = min(row for row, _ in cells)
    left = min(column for _, column in cells)
    return tuple(sorted((row - top, column - left) for row, column in cells))


def _transform(cells: tuple[Cell, ...], code: int) -> tuple[Cell, ...]:
    transformed = list(cells)
    if code >= 4:
        transformed = [(row, -column) for row, column in transformed]
    for _ in range(code % 4):
        transformed = [(column, -row) for row, column in transformed]
    return _normalize(tuple(transformed))


def _rng(seed: int, pair_index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{pair_index}:input".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def prototype_input(seed: int, pair_index: int) -> Grid:
    """Build a parameter-independent scene containing sizes 3, 5, 6, and 7."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")

    rng = _rng(seed, pair_index)
    sizes = [3, 5, 6, 7]
    rng.shuffle(sizes)
    colors = rng.sample(list(range(3, 10)), len(sizes))
    grid = [[0] * 12 for _ in range(12)]

    for slot, size, color in zip(_SLOTS, sizes, colors):
        cells = _transform(_SHAPES[size], rng.randrange(8))
        top = slot[0] + rng.randrange(2)
        left = slot[1] + rng.randrange(2)
        for dr, dc in cells:
            row, column = top + dr, left + dc
            if grid[row][column] != 0:
                raise AssertionError(f"prototype layout overlap at {(row, column)}")
            grid[row][column] = color
    return grid


def generate_episode(seed, *, target_size="seeded", root=None, bridge=None) -> dict[str, Any]:
    """Generate three demonstrations and one query under one fixed setting."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    selected = choose_target_size(seed, target_size)
    programs = {size: materialize_program(size, root=root) for size in TARGET_SIZES}
    inputs = [prototype_input(seed, pair_index) for pair_index in range(4)]

    with _bridge_context(bridge) as active:
        predictions = {
            size: [execute_program(active, program, grid) for grid in inputs]
            for size, program in programs.items()
        }

    selected_outputs = predictions[selected]
    rivals = {
        str(size): {
            "demo_refutations": [
                index
                for index in range(3)
                if predictions[size][index] != selected_outputs[index]
            ],
            "query_differs": predictions[size][3] != selected_outputs[3],
        }
        for size in TARGET_SIZES
    }
    identified = all(
        rivals[str(size)]["demo_refutations"]
        for size in TARGET_SIZES
        if size != selected
    )
    query_separates = all(
        rivals[str(size)]["query_differs"]
        for size in TARGET_SIZES
        if size != selected
    )

    return {
        "schema": "component-target-size-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": seed,
        "parameter": {"target_size": selected},
        "program": programs[selected],
        "program_sha256": _sha256_text(programs[selected]),
        "train": [
            {"input": inputs[index], "output": selected_outputs[index]}
            for index in range(3)
        ],
        "test": [{"input": inputs[3], "output": selected_outputs[3]}],
        "all_setting_outputs": {str(size): outputs for size, outputs in predictions.items()},
        "assessment": {
            "identified": bool(identified),
            "query_separates_settings": bool(query_separates),
            "rivals": rivals,
        },
    }


def _public_episode(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_evidence(seed, out_dir, *, root=None) -> dict[str, Any]:
    """Execute every setting and retain private evidence plus solver-safe exports."""
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    programs = {size: materialize_program(size, root=root) for size in TARGET_SIZES}
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        episodes = [
            generate_episode(seed + index, target_size=size, root=root, bridge=bridge)
            for index, size in enumerate(TARGET_SIZES)
        ]
        witness_input = prototype_input(seed + 100, 0)
        witness_outputs = {
            str(size): execute_program(bridge, program, witness_input)
            for size, program in programs.items()
        }

    artifacts: list[Path] = []
    for size, program in programs.items():
        rule_path = out / "private" / "rules" / f"target-size-{size}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(program, encoding="utf-8")
        artifacts.append(rule_path)

    for index, episode in enumerate(episodes):
        private_path = out / "private" / f"episode-{index:03d}.json"
        public_path = out / "public" / f"episode-{index:03d}.json"
        _write_json(private_path, episode)
        _write_json(public_path, _public_episode(episode))
        artifacts.extend((private_path, public_path))

    witness_path = out / "private" / "differing-witness.json"
    _write_json(witness_path, {"input": witness_input, "outputs": witness_outputs})
    artifacts.append(witness_path)

    root_path = _root(root)
    source = Path(__file__).resolve()
    identified = sum(bool(episode["assessment"]["identified"]) for episode in episodes)
    separated = sum(
        bool(episode["assessment"]["query_separates_settings"])
        for episode in episodes
    )
    distinct_witness_outputs = len(
        {json.dumps(output, separators=(",", ":")) for output in witness_outputs.values()}
    )
    report = {
        "schema": "component-target-size-evidence-v1",
        "status": (
            "pass"
            if identified == len(TARGET_SIZES)
            and separated == len(TARGET_SIZES)
            and distinct_witness_outputs == len(TARGET_SIZES)
            else "fail"
        ),
        "task_id": TASK_ID,
        "prototype": "proposed; isolated; not selected or approved",
        "parameter": {
            "name": "target_size",
            "allowed_values": list(TARGET_SIZES),
            "default": DEFAULT_TARGET_SIZE,
            "resolution": "once per episode",
            "input_constraint": "every pair contains distinct 4-connected objects of sizes 5, 6, and 7",
            "invariant_reasoning": "segment same-colour nonzero objects and classify them by cardinality",
        },
        "episodes_identified": identified,
        "episodes_total": len(episodes),
        "query_separation_count": separated,
        "episode_seeds": [episode["seed"] for episode in episodes],
        "programs": {
            str(size): {
                "sha256": _sha256_text(program),
                "path": f"private/rules/target-size-{size}.rkt",
                "canonical_default": size == DEFAULT_TARGET_SIZE,
            }
            for size, program in programs.items()
        },
        "differing_witness": "private/differing-witness.json",
        "source": {
            "path": str(source.relative_to(root_path)),
            "sha256": _sha256_file(source),
            "canonical_rule_sha256": _sha256_text(canonical_record(root)["program_solution"]),
        },
        "runtime": racket_runtime_status(),
        "artifact_hashes": {
            str(path.relative_to(out)): _sha256_file(path)
            for path in sorted(artifacts)
        },
        "limitations": [
            "Only target sizes 5, 6, and 7 are assessed.",
            "Each episode contains all three candidate sizes, deliberately making the parameter directly identifiable.",
            "The finite three-episode run checks only the other declared target-size settings as rivals.",
            "This prototype does not alter production generation, canonical authority, or approval state.",
        ],
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("evidence", "episode"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--target-size", default="seeded")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    selection: str | int
    if args.target_size == "seeded":
        selection = "seeded"
    else:
        try:
            selection = int(args.target_size)
        except ValueError as exc:
            raise SystemExit("--target-size must be seeded, 5, 6, or 7") from exc

    if args.command == "evidence":
        payload = build_evidence(args.seed, args.out)
        printable = payload
    else:
        payload = generate_episode(args.seed, target_size=selection)
        _write_json(Path(args.out), payload)
        printable = payload["assessment"]
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
