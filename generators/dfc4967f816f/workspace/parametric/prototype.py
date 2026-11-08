#!/usr/bin/env python3
"""Racket-backed output-color parameter for ARC family dfc4967f816f.

The vertical-symmetry classifier is unchanged.  One hidden episode setting picks
which color marks a symmetric 3x3 tile: 8 is the exact canonical/default rule and
4 is the proposed alternative.  Input sampling is independent of that setting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "dfc4967f816f"
ROOT = find_root(__file__)
OUTPUT_COLORS = (8, 4)
DEFAULT_OUTPUT_COLOR = 8
STATUS = "proposed prototype; not production-approved"
_CANONICAL_ANCHOR = " 8 0"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 8)
_QUERY_TILE_SCHEDULE = (3, 4, 5, 6)
_DEMO_TILE_SCHEDULE = (4, 5, 3, 6, 4, 5)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid: list[list[int]]) -> str:
    return digest(json.dumps(grid, separators=(",", ":")).encode("utf-8"))


def canonical_record(*, root: Path | str = ROOT) -> dict[str, Any]:
    with canonical_path(Path(root)).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise ValueError(f"canonical task not found: {TASK_ID}")


def _validate_output_color(output_color: int) -> None:
    if type(output_color) is not int or output_color not in OUTPUT_COLORS:
        raise ValueError(f"output_color must be one of {OUTPUT_COLORS}")


def validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be an integer in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if type(queries) is not int or not QUERY_LIMITS[0] <= queries <= QUERY_LIMITS[1]:
        raise ValueError(f"queries must be an integer in {QUERY_LIMITS[0]}..{QUERY_LIMITS[1]}")


def program_for(output_color: int = DEFAULT_OUTPUT_COLOR, *, root: Path | str = ROOT) -> str:
    """Return the exact canonical rule or its one-literal output-color variant."""
    _validate_output_color(output_color)
    canonical = canonical_record(root=root)["program_solution"]
    if canonical.count(_CANONICAL_ANCHOR) != 1:
        raise ValueError("canonical output-color anchor changed; prototype needs review")
    if output_color == DEFAULT_OUTPUT_COLOR:
        return canonical
    return canonical.replace(_CANONICAL_ANCHOR, f" {output_color} 0", 1)


def _callable_text(program: str) -> str:
    return f"(lambda (g) {strip_rule_wrapper(program)})"


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def application(program: str, grid: list[list[int]]) -> str:
    return f"({_callable_text(program)} {_grid_literal(grid)})"


def execute(bridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    return bridge.eval_text(application(program, grid))


def _generator(*, root: Path | str = ROOT):
    module, _, _ = load_selected_generator(TASK_ID, root=Path(root))
    return module


def tile_count(grid: list[list[int]]) -> int:
    width = len(grid[0]) if grid else 0
    if len(grid) != 3 or width < 11 or (width + 1) % 4:
        raise ValueError("grid does not encode a one-row strip of 3x3 tiles")
    count = (width + 1) // 4
    if not 3 <= count <= 6:
        raise ValueError("tile count must be in 3..6")
    return count


def transform(grid: list[list[int]], output_color: int) -> list[list[int]]:
    """Independent Python claim used by the adapter; evidence uses Racket labels."""
    _validate_output_color(output_color)
    gen = _generator()
    errors = gen.self_check(grid)
    if errors:
        raise ValueError("invalid symmetry strip: " + "; ".join(errors))
    return [[output_color if flag else 0 for flag in gen._tile_flags(grid)]]


def sample_input(
    seed: int,
    index: int,
    *,
    tile_cols: int | None = None,
    root: Path | str = ROOT,
) -> list[list[int]]:
    """Draw one setting-neutral input with a deterministic exact tile count."""
    if type(seed) is not int or type(index) is not int or index < 0:
        raise ValueError("seed and index must be nonnegative Python integers")
    if tile_cols is None:
        tile_cols = _DEMO_TILE_SCHEDULE[index % len(_DEMO_TILE_SCHEDULE)]
    if type(tile_cols) is not int or not 3 <= tile_cols <= 6:
        raise ValueError("tile_cols must be an integer in 3..6")
    gen = _generator(root=root)
    foreground = 1 + int(
        digest(f"{seed}|{index}|foreground".encode("utf-8"))[:8], 16
    ) % 8
    difficulty = ("easy", "medium", "hard")[index % 3]
    return gen.generate(
        seed ^ 0x0DFC4967,
        index,
        difficulty=difficulty,
        tile_cols=tile_cols,
        foreground_color=foreground,
    )


def _distinct_input(
    seed: int,
    base_index: int,
    tile_cols: int,
    seen: set[str],
    *,
    root: Path | str,
) -> list[list[int]]:
    for retry in range(32):
        grid = sample_input(seed, base_index + retry * 10_000, tile_cols=tile_cols, root=root)
        key = grid_digest(grid)
        if key not in seen:
            seen.add(key)
            return grid
    raise ValueError("distinct input budget exhausted; no partial episode")


def episode_inputs(
    seed: int,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    validate_counts(demos, queries)
    seen: set[str] = set()
    demo_grids = [
        _distinct_input(
            seed,
            100 + index * 97,
            _DEMO_TILE_SCHEDULE[index],
            seen,
            root=Path(root),
        )
        for index in range(demos)
    ]
    query_grids = [
        _distinct_input(
            seed,
            10_000 + index * 97,
            _QUERY_TILE_SCHEDULE[index % len(_QUERY_TILE_SCHEDULE)],
            seen,
            root=Path(root),
        )
        for index in range(queries)
    ]
    return demo_grids, query_grids


def _settings_surviving(
    train_inputs: list[list[list[int]]],
    train_outputs: list[list[list[int]]],
) -> list[dict[str, int]]:
    return [
        {"output_color": color}
        for color in OUTPUT_COLORS
        if all(transform(grid, color) == output for grid, output in zip(train_inputs, train_outputs))
    ]


def validate_public(public: dict[str, Any]) -> None:
    if type(public) is not dict or set(public) != {"train", "test"}:
        raise ValueError("public challenge must contain only train and test")
    if type(public["train"]) is not list or type(public["test"]) is not list:
        raise ValueError("public train/test must be lists")
    if not public["train"] or not public["test"]:
        raise ValueError("public train/test must be nonempty")
    if any(type(pair) is not dict or set(pair) != {"input", "output"} for pair in public["train"]):
        raise ValueError("public demonstrations require only input and output")
    if any(type(pair) is not dict or set(pair) != {"input"} for pair in public["test"]):
        raise ValueError("public query must contain only input")
    public_challenge_bytes(public)


def sequential_views(public: dict[str, Any]) -> list[dict[str, Any]]:
    validate_public(public)
    return [
        {"train": public["train"], "test": [{"input": pair["input"]}]}
        for pair in public["test"]
    ]


def generate_claimed_episode(
    seed: int,
    output_color: int,
    demos: int,
    queries: int,
    *,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    _validate_output_color(output_color)
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    train = [{"input": grid, "output": transform(grid, output_color)} for grid in demo_grids]
    test = [{"input": grid, "output": transform(grid, output_color)} for grid in query_grids]
    survivors = _settings_surviving(demo_grids, [pair["output"] for pair in train])
    if survivors != [{"output_color": output_color}]:
        raise ValueError(f"demonstrations do not identify output_color: {survivors}")
    return {"train": train, "test": test, "program_solution": program_for(output_color, root=root)}


def generate_episode(
    seed: int,
    bridge,
    *,
    output_color: int | None = None,
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative Python integer")
    validate_counts(demos, queries)
    selected = OUTPUT_COLORS[seed % len(OUTPUT_COLORS)] if output_color is None else output_color
    _validate_output_color(selected)
    programs = {color: program_for(color, root=root) for color in OUTPUT_COLORS}
    demo_grids, query_grids = episode_inputs(seed, demos, queries, root=root)
    all_grids = demo_grids + query_grids
    predictions = {
        color: [execute(bridge, programs[color], grid) for grid in all_grids]
        for color in OUTPUT_COLORS
    }
    selected_outputs = predictions[selected]
    public = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(demo_grids, selected_outputs[:demos])
        ],
        "test": [{"input": grid} for grid in query_grids],
    }
    rival_checks: dict[str, Any] = {}
    for color in OUTPUT_COLORS:
        differing = [
            index
            for index in range(demos)
            if predictions[color][index] != selected_outputs[index]
        ]
        rival_checks[str(color)] = {
            "matches_all_demonstrations": not differing,
            "distinguishing_demo_indices": differing,
            "demonstration_predictions": predictions[color][:demos],
            "query_predictions": predictions[color][demos:],
        }
    survivors = [
        {"output_color": color}
        for color in OUTPUT_COLORS
        if rival_checks[str(color)]["matches_all_demonstrations"]
    ]
    if survivors != [{"output_color": selected}]:
        raise ValueError(f"demonstrations do not identify output_color: {survivors}")
    private = {
        "schema": "dfc4967f816f-parametric-output-color-v2",
        "status": STATUS,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"output_color": selected},
        "program_sha256": digest(programs[selected].encode("utf-8")),
        "query_answers": selected_outputs[demos:],
        "surviving_settings": survivors,
        "rival_checks": rival_checks,
        "demo_count": demos,
        "query_count": queries,
        "query_tile_counts": [tile_count(grid) for grid in query_grids],
        "size_limit": "3x23; the 3x3-tile grammar cannot form an exact 30x30 grid",
        "public_id": public_challenge_id(public),
        "sequential_public_ids": [public_challenge_id(view) for view in sequential_views(public)],
    }
    verify_episode(public, private, root=root)
    return public, private


def verify_episode(public: dict[str, Any], private: dict[str, Any], *, root: Path | str = ROOT) -> None:
    del root
    validate_public(public)
    if type(private) is not dict:
        raise ValueError("private record must be a dictionary")
    try:
        color = private["parameter"]["output_color"]
        answers = private["query_answers"]
    except (KeyError, TypeError) as exc:
        raise ValueError("private record is missing parameter or query answers") from exc
    _validate_output_color(color)
    if type(answers) is not list or len(answers) != len(public["test"]):
        raise ValueError("query answer count does not match public queries")
    for index, pair in enumerate(public["train"]):
        expected = transform(pair["input"], color)
        if pair["output"] != expected:
            raise ValueError(f"demonstration label {index} does not match selected rule")
    for index, (pair, answer) in enumerate(zip(public["test"], answers)):
        expected = transform(pair["input"], color)
        if answer != expected:
            raise ValueError(f"query answer {index} does not match selected rule")
    survivors = _settings_surviving(
        [pair["input"] for pair in public["train"]],
        [pair["output"] for pair in public["train"]],
    )
    if survivors != [{"output_color": color}]:
        raise ValueError(f"demonstrations are underidentified: {survivors}")
    if private.get("public_id") not in (None, public_challenge_id(public)):
        raise ValueError("public identifier does not match visible bytes")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_public(path: Path, public: dict[str, Any]) -> None:
    validate_public(public)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(public))


def write_evidence(
    out: Path | str,
    *,
    seeds: tuple[int, ...] | list[int] = (0, 1),
    demos: int = 3,
    queries: int = 4,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    validate_counts(demos, queries)
    out = Path(out)
    root = Path(root)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"output directory is not empty: {out}")
    for folder in ("public", "private", "rules", "sequential"):
        (out / folder).mkdir(parents=True, exist_ok=True)
    programs = {color: program_for(color, root=root) for color in OUTPUT_COLORS}
    for color, program in programs.items():
        (out / "rules" / f"output-color-{color}.rkt").write_text(program, encoding="utf-8")

    from arc_repl.racket_bridge import RacketBridge

    episodes = []
    with RacketBridge(max_calls_before_restart=256) as bridge:
        runtime_identity = bridge.runtime_identity
        for seed in seeds:
            public, private = generate_episode(
                seed, bridge, demos=demos, queries=queries, root=root
            )
            public_id = public_challenge_id(public)
            _write_public(out / "public" / f"{public_id}.json", public)
            _write_json(out / "private" / f"{public_id}.json", private)
            sequential_ids = []
            for view in sequential_views(public):
                view_id = public_challenge_id(view)
                _write_public(out / "sequential" / f"{view_id}.json", view)
                sequential_ids.append(view_id)
            episodes.append(
                {
                    "public_id": public_id,
                    "seed": seed,
                    "parameter": private["parameter"],
                    "demos": demos,
                    "queries": queries,
                    "sequential_public_ids": sequential_ids,
                }
            )

        canonical_checks = []
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute(bridge, programs[DEFAULT_OUTPUT_COLOR], pair["input"])
            if actual != pair["output"]:
                raise ValueError("canonical default failed a labeled canonical pair")
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "output": actual,
                }
            )
        _write_json(out / "private" / "canonical-checks.json", canonical_checks)

        witness = sample_input(991, 0, tile_cols=4, root=root)
        witness_outputs = {
            str(color): execute(bridge, programs[color], witness) for color in OUTPUT_COLORS
        }
        if witness_outputs["8"] == witness_outputs["4"]:
            raise ValueError("shared witness failed to distinguish settings")
        _write_json(
            out / "private" / "shared-witness.json",
            {"input": witness, "outputs": witness_outputs},
        )

    _, generator_source, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    manifest = {
        "schema": "dfc4967f816f-parametric-output-color-evidence-v2",
        "status": STATUS,
        "task_id": TASK_ID,
        "parameters": {"output_color": list(OUTPUT_COLORS)},
        "default": {"output_color": DEFAULT_OUTPUT_COLOR},
        "limits": {"demos": list(DEMO_LIMITS), "queries": list(QUERY_LIMITS)},
        "materialized_request": {"demos": demos, "queries": queries},
        "episodes": episodes,
        "canonical_default_unchanged": programs[DEFAULT_OUTPUT_COLOR]
        == canonical_record(root=root)["program_solution"],
        "program_sha256": {
            str(color): digest(program.encode("utf-8")) for color, program in programs.items()
        },
        "generator_source": str(Path(generator_source).relative_to(root)),
        "generator_sha256": generator_sha256,
        "prototype_source_sha256": digest(Path(__file__).read_bytes()),
        "racket_runtime": runtime_identity,
        "bounded_adversarial_pass": {
            "attempted": [
                "mutated one private query label",
                "inserted an output into a public query",
                "requested demo/query counts outside declared limits",
                "checked saved public files against canonical bytes and full-SHA filenames",
            ],
            "result": (
                "the saved-file check exposed pretty-JSON/canonical-byte drift; "
                "the writer now emits exact public_challenge_bytes and a regression "
                "pins it; the label, leak, and count attacks were rejected"
            ),
        },
        "limitations": [
            "prototype only; production remains pinned to canonical output color 8",
            "the one-row 3x3-tile grammar reaches 3x23 at six tiles, not 30x30",
            "finite evidence distinguishes only the declared output-color settings",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=args.seeds,
        demos=args.demos,
        queries=args.queries,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
