#!/usr/bin/env python3
"""Proposed episode-level projection-depth extension for b19deac47327.

This file is intentionally isolated from the selected production generator.
The canonical/default setting is projection_depth=1.  The alternative setting
projects each marker two cells toward its matching colored border.  One setting
is chosen once for an entire 3-demonstration + 1-query episode, and all retained
labels are executed from exact materialized Racket source.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "b19deac47327"
PROTOTYPE_VERSION = "projection-depth-v1"
PARAMETER_NAME = "projection_depth"
ALLOWED_PROJECTION_DEPTHS = (1, 2)
DEFAULT_PROJECTION_DEPTH = 1
CANONICAL_RULE_HASH = "2b2e46dd36cc"
CANONICAL_SHA256 = (
    "18c042039414a6bd8745b9ffc3277879010959e3ce76d64d94d4d16925343dd8"
)
N_TRAIN = 3
N_TEST = 1

_HORIZONTAL_CANONICAL = "(nr (if (< (* 2 r) h) (- r 1) (+ r 1)))"
_HORIZONTAL_DEPTH_TWO = "(nr (if (< (* 2 r) h) (- r 2) (+ r 2)))"
_VERTICAL_CANONICAL = "(nc (if (< (* 2 c) w) (- c 1) (+ c 1)))"
_VERTICAL_DEPTH_TWO = "(nc (if (< (* 2 c) w) (- c 2) (+ c 2)))"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_projection_depth(value: Any) -> int:
    if type(value) is not int:
        raise TypeError(
            "projection_depth must be an integer (not bool, float, or string)"
        )
    if value not in ALLOWED_PROJECTION_DEPTHS:
        raise ValueError(
            "projection_depth must be one of "
            f"{ALLOWED_PROJECTION_DEPTHS}, got {value!r}"
        )
    return value


def choose_projection_depth(seed: Any) -> int:
    """Choose the hidden rule setting once for the complete episode."""
    seed = _validate_seed(seed)
    return ALLOWED_PROJECTION_DEPTHS[seed % len(ALLOWED_PROJECTION_DEPTHS)]


def _root(root: Path | str | None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def canonical_source(*, root: Path | str | None = None) -> str:
    """Return the single hash-bound canonical Racket program for this task."""
    root_path = _root(root)
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
            sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one unambiguous canonical program, found {len(sources)}"
        )
    source = sources.pop()
    actual = _sha256_text(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            "canonical program changed; review the projection edit sites again "
            f"({actual} != {CANONICAL_SHA256})"
        )
    if source.count(_HORIZONTAL_CANONICAL) != 1:
        raise ValueError("canonical horizontal projection site is missing or ambiguous")
    if source.count(_VERTICAL_CANONICAL) != 1:
        raise ValueError("canonical vertical projection site is missing or ambiguous")
    return source


def materialize_rule(
    projection_depth: Any = DEFAULT_PROJECTION_DEPTH,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Materialize the exact canonical program or its two-cell alternative."""
    depth = _validate_projection_depth(projection_depth)
    canonical = canonical_source(root=root) if source is None else source
    if not isinstance(canonical, str):
        raise TypeError("source must be a string")
    if _sha256_text(canonical) != CANONICAL_SHA256:
        raise ValueError("source is not the hash-bound canonical program")
    if depth == DEFAULT_PROJECTION_DEPTH:
        return canonical
    return canonical.replace(
        _HORIZONTAL_CANONICAL, _HORIZONTAL_DEPTH_TWO, 1
    ).replace(_VERTICAL_CANONICAL, _VERTICAL_DEPTH_TWO, 1)


def restore_canonical_rule(source: str) -> str:
    """Reverse the one-site depth-two materialization and verify exact recovery."""
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    if _sha256_text(source) == CANONICAL_SHA256:
        return source
    if source.count(_HORIZONTAL_DEPTH_TWO) != 1:
        raise ValueError("source does not contain one depth-two horizontal site")
    if source.count(_VERTICAL_DEPTH_TWO) != 1:
        raise ValueError("source does not contain one depth-two vertical site")
    restored = source.replace(
        _HORIZONTAL_DEPTH_TWO, _HORIZONTAL_CANONICAL, 1
    ).replace(_VERTICAL_DEPTH_TWO, _VERTICAL_CANONICAL, 1)
    if _sha256_text(restored) != CANONICAL_SHA256:
        raise ValueError("depth-two source did not restore to exact canonical authority")
    return restored


def rule_callable(source: str) -> str:
    """Extract the callable body from one plain ``(rule! BODY)`` form."""
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    text = source.strip()
    prefix = "(rule! "
    if not text.startswith(prefix) or not text.endswith(")"):
        raise ValueError("expected one plain (rule! BODY) form")
    body = text[len(prefix) : -1].strip()
    if not body.startswith("(lambda"):
        raise ValueError("prototype expects a lambda-bodied canonical rule")
    return body


def _grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return f"'({rows})"


def execute_rule(
    source: str,
    grid: list[list[int]],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact materialized rule through the protected Racket bridge."""
    normalized = normalize_grid(grid)
    expression = f"({rule_callable(source)} {_grid_literal(normalized)})"
    if bridge is not None:
        return normalize_grid(bridge.eval_text(expression))
    with RacketBridge(
        timeout=30, startup_timeout=60, max_calls_before_restart=128
    ) as owned_bridge:
        return normalize_grid(owned_bridge.eval_text(expression))


def _solid_color(values: list[int]) -> int | None:
    if values and len(set(values)) == 1 and values[0] not in (0, 1):
        return values[0]
    return None


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    normalized = normalize_grid(grid)
    height, width = len(normalized), len(normalized[0])
    top = _solid_color(normalized[0])
    bottom = _solid_color(normalized[-1])
    left = _solid_color([row[0] for row in normalized])
    right = _solid_color([row[-1] for row in normalized])
    horizontal = top is not None and bottom is not None
    vertical = left is not None and right is not None
    if horizontal == vertical:
        raise ValueError("expected exactly one solid opposite-border orientation")
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == 1
    ]
    if not markers:
        raise ValueError("expected at least one color-1 marker")
    if horizontal:
        assert top is not None and bottom is not None
        if top == bottom:
            raise ValueError("opposite border colors must differ")
        return {
            "grid": normalized,
            "height": height,
            "width": width,
            "orientation": "horizontal",
            "edge_colors": [top, bottom],
            "markers": markers,
        }
    assert left is not None and right is not None
    if left == right:
        raise ValueError("opposite border colors must differ")
    return {
        "grid": normalized,
        "height": height,
        "width": width,
        "orientation": "vertical",
        "edge_colors": [left, right],
        "markers": markers,
    }


def _destinations(
    facts: dict[str, Any], projection_depth: int
) -> list[tuple[int, int, int]]:
    depth = _validate_projection_depth(projection_depth)
    height = facts["height"]
    width = facts["width"]
    first_color, second_color = facts["edge_colors"]
    result: list[tuple[int, int, int]] = []
    for row, col in facts["markers"]:
        if facts["orientation"] == "horizontal":
            first_half = 2 * row < height
            target = (row - depth if first_half else row + depth, col)
        else:
            first_half = 2 * col < width
            target = (row, col - depth if first_half else col + depth)
        target_row, target_col = target
        if not (0 <= target_row < height and 0 <= target_col < width):
            raise ValueError(
                f"depth {depth} projects marker {(row, col)} out of bounds"
            )
        if facts["grid"][target_row][target_col] != 0:
            raise ValueError(
                f"depth {depth} destination {(target_row, target_col)} is not background"
            )
        result.append(
            (target_row, target_col, first_color if first_half else second_color)
        )
    coordinates = [(row, col) for row, col, _ in result]
    if len(set(coordinates)) != len(coordinates):
        raise ValueError(f"depth {depth} has colliding marker destinations")
    return result


def input_observation(grid: list[list[int]]) -> dict[str, Any]:
    """Return source-independent structural facts and parameter safety."""
    facts = _facts(grid)
    safe: list[int] = []
    destination_hashes: dict[str, str] = {}
    for depth in ALLOWED_PROJECTION_DEPTHS:
        try:
            destinations = _destinations(facts, depth)
        except ValueError:
            continue
        safe.append(depth)
        destination_hashes[str(depth)] = _sha256_json(destinations)
    return {
        "height": facts["height"],
        "width": facts["width"],
        "orientation": facts["orientation"],
        "edge_colors": list(facts["edge_colors"]),
        "marker_count": len(facts["markers"]),
        "markers_in_both_halves": _markers_in_both_halves(facts),
        "safe_for_depths": safe,
        "destination_sha256_by_depth": destination_hashes,
    }


def _markers_in_both_halves(facts: dict[str, Any]) -> bool:
    if facts["orientation"] == "horizontal":
        flags = [2 * row < facts["height"] for row, _ in facts["markers"]]
    else:
        flags = [2 * col < facts["width"] for _, col in facts["markers"]]
    return any(flags) and not all(flags)


def python_mirror(
    grid: list[list[int]], *, projection_depth: Any
) -> list[list[int]]:
    """Independent Python audit mirror of the parameterized Racket rule."""
    depth = _validate_projection_depth(projection_depth)
    facts = _facts(grid)
    output = [row[:] for row in facts["grid"]]
    for row, col, color in _destinations(facts, depth):
        output[row][col] = color
    return output


def _input_seed(episode_seed: int, slot: int, attempt: int) -> int:
    payload = f"{PROTOTYPE_VERSION}:{episode_seed}:{slot}:{attempt}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (
        2**63 - 1
    )


def episode_inputs(
    seed: Any, *, root: Path | str | None = None
) -> tuple[list[list[list[int]]], str, str]:
    """Draw four parameter-independent inputs safe under every allowed setting."""
    seed = _validate_seed(seed)
    root_path = _root(root)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root_path
    )
    orientations = ("horizontal", "vertical", "horizontal", "vertical")
    edge_pairs = ("2_4", "8_3", "5_9", "3_4")
    counts = (6, 7, 8, 9)
    inputs: list[list[list[int]]] = []
    seen: set[str] = set()
    for slot in range(N_TRAIN + N_TEST):
        accepted: list[list[int]] | None = None
        for attempt in range(2000):
            grid = normalize_grid(
                generator.generate(
                    _input_seed(seed, slot, attempt),
                    slot,
                    difficulty="medium",
                    grid_h=15,
                    grid_w=15,
                    orientation=orientations[slot],
                    marker_count=counts[slot],
                    edge_pair=edge_pairs[slot],
                    side_balance="balanced",
                    edge_marker_mode="none",
                    midline_marker=False,
                )
            )
            observation = input_observation(grid)
            input_hash = _sha256_json(grid)
            if observation["safe_for_depths"] != list(ALLOWED_PROJECTION_DEPTHS):
                continue
            if not observation["markers_in_both_halves"]:
                continue
            if python_mirror(grid, projection_depth=1) == python_mirror(
                grid, projection_depth=2
            ):
                continue
            if input_hash in seen:
                continue
            accepted = grid
            seen.add(input_hash)
            break
        if accepted is None:
            raise RuntimeError(
                f"could not draw a depth-safe distinguishing input for slot {slot}"
            )
        inputs.append(accepted)
    return inputs, str(generator_path), generator_sha


def _pair_record(
    grid: list[list[int]], output: list[list[int]]
) -> dict[str, Any]:
    return {
        "input": copy.deepcopy(grid),
        "output": copy.deepcopy(output),
        "input_sha256": _sha256_json(grid),
        "output_sha256": _sha256_json(output),
        "input_observation": input_observation(grid),
    }


def make_episode(
    seed: Any,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete, coherent, Racket-labeled parametric episode."""
    seed = _validate_seed(seed)
    selected = choose_projection_depth(seed)
    root_path = _root(root)
    inputs, generator_path, generator_sha = episode_inputs(seed, root=root_path)
    canonical = canonical_source(root=root_path)
    sources = {
        depth: materialize_rule(depth, root=root_path, source=canonical)
        for depth in ALLOWED_PROJECTION_DEPTHS
    }

    def build(live_bridge: RacketBridge) -> dict[str, Any]:
        outputs: dict[int, list[list[list[int]]]] = {}
        for depth, source in sources.items():
            depth_outputs = [
                execute_rule(source, grid, bridge=live_bridge) for grid in inputs
            ]
            mirrors = [
                python_mirror(grid, projection_depth=depth) for grid in inputs
            ]
            if depth_outputs != mirrors:
                raise AssertionError(
                    f"Racket/Python disagreement at projection_depth={depth}"
                )
            outputs[depth] = depth_outputs

        pairs = [
            _pair_record(grid, output)
            for grid, output in zip(inputs, outputs[selected], strict=True)
        ]
        rivals: list[dict[str, Any]] = []
        ambiguities: list[dict[str, Any]] = []
        for depth in ALLOWED_PROJECTION_DEPTHS:
            train_mismatches = [
                index
                for index in range(N_TRAIN)
                if outputs[depth][index] != outputs[selected][index]
            ]
            query_mismatches = [
                index
                for index in range(N_TEST)
                if outputs[depth][N_TRAIN + index]
                != outputs[selected][N_TRAIN + index]
            ]
            if depth == selected:
                status = "selected"
            elif train_mismatches:
                status = "refuted_by_demonstrations"
            else:
                status = "ambiguous"
                ambiguities.append(
                    {
                        PARAMETER_NAME: depth,
                        "query_mismatch_indices": query_mismatches,
                    }
                )
            rivals.append(
                {
                    PARAMETER_NAME: depth,
                    "racket_sha256": _sha256_text(sources[depth]),
                    "status": status,
                    "demonstration_mismatch_indices": train_mismatches,
                    "query_mismatch_indices": query_mismatches,
                    "predictions": copy.deepcopy(outputs[depth]),
                }
            )

        return {
            "schema": "arc-parametric-prototype-episode-v1",
            "status": "proposed_unapproved",
            "approved": False,
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            "parameter_selection": "chosen_once_per_episode",
            "parameters": {PARAMETER_NAME: selected},
            "allowed_projection_depths": list(ALLOWED_PROJECTION_DEPTHS),
            "default_projection_depth": DEFAULT_PROJECTION_DEPTH,
            "input_constraints_depend_on_parameter": False,
            "generator_path": generator_path,
            "generator_sha256": generator_sha,
            "canonical_rule_hash": CANONICAL_RULE_HASH,
            "canonical_sha256": CANONICAL_SHA256,
            "racket_source": sources[selected],
            "racket_sha256": _sha256_text(sources[selected]),
            "train": pairs[:N_TRAIN],
            "test": pairs[N_TRAIN:],
            "parameter_rivals": rivals,
            "ambiguities": ambiguities,
            "limits": [
                "Only projection depths 1 and 2 are materialized.",
                "Evidence is bounded to generated 15x15 collision-free inputs.",
                "This proposal does not alter canonical authority or production outputs.",
            ],
        }

    if bridge is not None:
        return build(bridge)
    with RacketBridge(
        timeout=30, startup_timeout=60, max_calls_before_restart=128
    ) as owned_bridge:
        return build(owned_bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only demonstrations and an unlabeled query, as deep copies."""
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _file_rows(out: Path) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(out).as_posix(),
            "sha256": _sha256_bytes(path.read_bytes()),
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "report.json"
    ]


def write_evidence(
    seeds: Iterable[Any],
    *,
    out: Path | str,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Retain hash-bound public/private evidence without overwriting prior runs."""
    output = Path(out)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite evidence directory: {output}")
    output.mkdir(parents=True)
    root_path = _root(root)
    seed_values = tuple(_validate_seed(seed) for seed in seeds)
    if not seed_values:
        raise ValueError("at least one episode seed is required")

    canonical = canonical_source(root=root_path)
    programs = {
        depth: materialize_rule(depth, root=root_path, source=canonical)
        for depth in ALLOWED_PROJECTION_DEPTHS
    }
    rule_paths: dict[int, str] = {}
    for depth, source in programs.items():
        relative = Path("private/rules") / f"projection-depth-{depth}.rkt"
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_paths[depth] = relative.as_posix()

    episodes: list[dict[str, Any]] = []
    private_episodes: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    canonical_count = 0
    with RacketBridge(
        timeout=30, startup_timeout=60, max_calls_before_restart=128
    ) as bridge:
        for index, seed in enumerate(seed_values):
            episode = make_episode(seed, root=root_path, bridge=bridge)
            depth = episode["parameters"][PARAMETER_NAME]
            episode["racket_path"] = rule_paths[depth]
            private_path = Path("private") / f"episode-{index:03d}.json"
            public_path = Path("public") / f"episode-{index:03d}.json"
            public = public_challenge(episode)
            _write_json(output / private_path, episode)
            _write_json(output / public_path, public)
            private_episodes.append(episode)
            episodes.append(
                {
                    "seed": seed,
                    PARAMETER_NAME: depth,
                    "racket_sha256": episode["racket_sha256"],
                    "racket_path": rule_paths[depth],
                    "public_path": public_path.as_posix(),
                    "private_path": private_path.as_posix(),
                    "public_sha256": _sha256_json(public),
                    "private_sha256": _sha256_json(episode),
                }
            )

        for pair in canonical_pairs(TASK_ID, root=root_path):
            actual = execute_rule(programs[DEFAULT_PROJECTION_DEPTH], pair["input"], bridge=bridge)
            expected = normalize_grid(pair["output"])
            mirror = python_mirror(
                pair["input"], projection_depth=DEFAULT_PROJECTION_DEPTH
            )
            passed = actual == expected == mirror
            canonical_rows.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _sha256_json(pair["input"]),
                    "expected_sha256": _sha256_json(expected),
                    "actual_sha256": _sha256_json(actual),
                    "passed": passed,
                }
            )
            canonical_count += 1
            if not passed:
                raise AssertionError(
                    "default projection depth failed canonical replay at "
                    f"{pair['split']}[{pair['pair_index']}]"
                )

        witness_input = private_episodes[0]["train"][0]["input"]
        witness_outputs = {
            str(depth): execute_rule(programs[depth], witness_input, bridge=bridge)
            for depth in ALLOWED_PROJECTION_DEPTHS
        }

    _write_json(
        output / "private/canonical_replay.json",
        {
            "task_id": TASK_ID,
            "canonical_sha256": CANONICAL_SHA256,
            "projection_depth": DEFAULT_PROJECTION_DEPTH,
            "pairs": canonical_rows,
            "all_passed": all(row["passed"] for row in canonical_rows),
        },
    )
    witness = {
        "input": witness_input,
        "input_sha256": _sha256_json(witness_input),
        "outputs": witness_outputs,
        "output_sha256_by_depth": {
            depth: _sha256_json(value) for depth, value in witness_outputs.items()
        },
        "rule_sha256_by_depth": {
            str(depth): _sha256_text(programs[depth])
            for depth in ALLOWED_PROJECTION_DEPTHS
        },
        "different": witness_outputs["1"] != witness_outputs["2"],
    }
    if not witness["different"]:
        raise AssertionError("retained witness does not distinguish projection depths")
    _write_json(output / "private/distinguishing_witness.json", witness)

    ambiguous_count = sum(
        1
        for episode in private_episodes
        for rival in episode["parameter_rivals"]
        if rival["status"] == "ambiguous"
    )
    settings = {
        episode["parameters"][PARAMETER_NAME] for episode in private_episodes
    }
    report = {
        "schema": "b19deac47327-parametric-projection-depth-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_PROJECTION_DEPTHS),
            "canonical_default": DEFAULT_PROJECTION_DEPTH,
            "selected_once_per_episode": True,
            "input_constraints_depend_on_parameter": False,
            "semantics": (
                "Each color-1 marker paints the matching border color exactly "
                "projection_depth cells toward that border."
            ),
        },
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_sha256": CANONICAL_SHA256,
        "prototype_path": str(Path(__file__).resolve()),
        "prototype_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        "counts": {
            "episodes": len(private_episodes),
            "settings_covered": len(settings),
            "ambiguous_parameter_rivals": ambiguous_count,
            "canonical_pairs_checked": canonical_count,
            "demonstrations": len(private_episodes) * N_TRAIN,
            "queries": len(private_episodes) * N_TEST,
            "racket_rule_applications": (
                len(private_episodes)
                * len(ALLOWED_PROJECTION_DEPTHS)
                * (N_TRAIN + N_TEST)
                + canonical_count
                + len(ALLOWED_PROJECTION_DEPTHS)
            ),
        },
        "episodes": episodes,
        "canonical_replay": "private/canonical_replay.json",
        "distinguishing_witness": "private/distinguishing_witness.json",
        "limits": [
            "This is a proposed, unapproved workspace extension; production generator and canonical authority remain unchanged.",
            "Evidence covers only the retained seeds, two declared settings, and one bounded input grammar.",
            "The prototype rejects inputs where either setting would clip, collide, or overwrite a non-background cell.",
        ],
    }
    report["files"] = _file_rows(output)
    _write_json(output / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    evidence = subparsers.add_parser("evidence", help="materialize retained evidence")
    evidence.add_argument("--seeds", nargs="+", type=int, required=True)
    evidence.add_argument("--out", type=Path, required=True)

    episode = subparsers.add_parser("episode", help="print one private episode")
    episode.add_argument("--seed", type=int, required=True)

    args = parser.parse_args(argv)
    if args.command == "evidence":
        report = write_evidence(tuple(args.seeds), out=args.out)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "episodes": report["counts"]["episodes"],
                    "settings_covered": report["counts"]["settings_covered"],
                    "out": str(args.out),
                },
                sort_keys=True,
            )
        )
        return 0
    if args.command == "episode":
        print(json.dumps(make_episode(args.seed), indent=2, sort_keys=True))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
