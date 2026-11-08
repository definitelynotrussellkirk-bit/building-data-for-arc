#!/usr/bin/env python3
"""Proposed task-local midpoint tie prototype for ``ee6a99e8b7f9``.

The selected canonical rule sends each exterior pink marker to the lower-indexed
center cell when its rectangle has an even width or height.  This prototype adds
one hidden episode-level parameter while preserving every object role and all
other geometry:

``pink_center_tie = lower`` (canonical/default)
    Use floor((lo + hi) / 2), exactly the selected Racket authority.

``pink_center_tie = upper`` (proposed alternative)
    Use ceil((lo + hi) / 2) on an even axis; odd axes are unchanged.

The parameter is chosen once per episode.  Every generated prototype pair uses
one of the selected generator's even-axis witness profiles, so each demonstration
and query distinguishes both settings.  Saved labels are produced by executing
the exact materialized Racket program.  ``python_apply`` is a secondary parity
oracle only; this module does not alter the production generator or authority.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
TASK_HOME = HERE.parents[1]
ROOT = HERE.parents[3]
TASK_ID = "ee6a99e8b7f9"
PARAMETER_NAME = "pink_center_tie"
ALLOWED_VALUES = ("lower", "upper")
DEFAULT_VALUE = "lower"
PROTOTYPE_VERSION = "1.0.0"
PROTOTYPE_SEEDS = {"lower": 2300, "upper": 2301}
_SAMPLE_INDICES = (2, 3, 6, 7)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_LOWER_ROW = "(mid-r (quotient (+ r1 r2) 2))"
_LOWER_COL = "(mid-c (quotient (+ c1 c2) 2))"
_UPPER_ROW = "(mid-r (quotient (+ r1 r2 1) 2))"
_UPPER_COL = "(mid-c (quotient (+ c1 c2 1) 2))"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _validate_setting(setting: str) -> str:
    if type(setting) is not str:
        raise TypeError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_VALUES}, got {type(setting).__name__}"
        )
    if setting not in ALLOWED_VALUES:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_VALUES}, got {setting!r}")
    return setting


def _load_selected_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(f"{TASK_ID}_selected_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    """Return the selected canonical Racket program verbatim."""
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise RuntimeError(f"canonical program missing for {TASK_ID}")
                return program
    raise KeyError(f"canonical task not found: {TASK_ID}")


def program_for(setting: str) -> str:
    """Materialize the exact Racket program for one tie setting."""
    chosen = _validate_setting(setting)
    program = canonical_program()
    if chosen == DEFAULT_VALUE:
        return program
    if program.count(_LOWER_ROW) != 1 or program.count(_LOWER_COL) != 1:
        raise RuntimeError("canonical midpoint program shape changed; refusing a silent rewrite")
    return program.replace(_LOWER_ROW, _UPPER_ROW, 1).replace(_LOWER_COL, _UPPER_COL, 1)


def choose_setting(seed: int) -> str:
    """Choose one hidden setting deterministically for a complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    return ALLOWED_VALUES[seed % len(ALLOWED_VALUES)]


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal integer ARC colors 0..9")
    return len(grid), width


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = _validate_grid(grid)
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] in (5, 6)
    }
    found: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (row + dr, col + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    queue.append(point)
                    cells.add(point)
        r1, r2 = min(row for row, _ in cells), max(row for row, _ in cells)
        c1, c2 = min(col for _, col in cells), max(col for _, col in cells)
        if len(cells) != (r2 - r1 + 1) * (c2 - c1 + 1):
            raise ValueError(f"color-{color} component is not a filled rectangle")
        found.append({"color": color, "bbox": (r1, c1, r2, c2), "cells": cells})
    return sorted(found, key=lambda shape: shape["bbox"])


def _side_for(dot: tuple[int, int], bbox: tuple[int, int, int, int]) -> str | None:
    row, col = dot
    r1, c1, r2, c2 = bbox
    if r1 <= row <= r2 and col == c1 - 1:
        return "left"
    if r1 <= row <= r2 and col == c2 + 1:
        return "right"
    if c1 <= col <= c2 and row == r1 - 1:
        return "above"
    if c1 <= col <= c2 and row == r2 + 1:
        return "below"
    return None


def python_apply(grid: list[list[int]], setting: str) -> list[list[int]]:
    """Independent Python mirror used only to cross-check executed Racket."""
    chosen = _validate_setting(setting)
    height, width = _validate_grid(grid)
    if any(value not in {5, 6, 8, 9} for row in grid for value in row):
        raise ValueError("prototype inputs use only colors 5, 6, 8, and 9")
    shapes = _components(grid)
    if not shapes:
        raise ValueError("prototype input has no rectangles")
    dots = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9
    ]
    if not dots:
        raise ValueError("prototype input has no exterior marker dots")

    links: list[tuple[tuple[int, int], int, str]] = []
    counts = [0] * len(shapes)
    for dot in dots:
        hits = [
            (index, side)
            for index, shape in enumerate(shapes)
            if (side := _side_for(dot, shape["bbox"])) is not None
        ]
        if len(hits) != 1:
            raise ValueError(f"dot {dot} must be adjacent to exactly one rectangle")
        index, side = hits[0]
        counts[index] += 1
        links.append((dot, index, side))
    if any(count == 0 for count in counts):
        raise ValueError("every rectangle must have at least one associated dot")

    output = deepcopy(grid)
    for shape in shapes:
        if shape["color"] == 5:
            for row, col in shape["cells"]:
                output[row][col] = 8

    offset = int(chosen == "upper")
    for (row, col), index, side in links:
        shape = shapes[index]
        r1, c1, r2, c2 = shape["bbox"]
        if shape["color"] == 6:
            output[row][col] = 8
            if side in ("left", "right"):
                target = (row, (c1 + c2 + offset) // 2)
            else:
                target = ((r1 + r2 + offset) // 2, col)
        else:
            target = {
                "left": (row, c1),
                "right": (row, c2),
                "above": (r1, col),
                "below": (r2, col),
            }[side]
        output[target[0]][target[1]] = 9
    return output


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return four selected-generator inputs that expose the tie parameter."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    generator = _load_selected_generator()
    inputs: list[list[list[int]]] = []
    for position, sample_index in enumerate(_SAMPLE_INDICES):
        grid = generator.generate(
            seed * 1009 + position,
            sample_index,
            difficulty="hard",
        )
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(f"selected generator emitted invalid prototype input: {errors}")
        if python_apply(grid, "lower") == python_apply(grid, "upper"):
            raise AssertionError(
                f"sample_index={sample_index} did not expose {PARAMETER_NAME}"
            )
        inputs.append(grid)
    if len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) != len(inputs):
        raise AssertionError("prototype episode contains duplicate inputs")
    return inputs


def run_program(program: str, grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Execute one exact Racket program over a batch; no Python fallback."""
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be nonempty Racket source")
    materialized = list(grids)
    if not materialized:
        return []
    for grid in materialized:
        _validate_grid(grid)

    src_path = ROOT / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parametric-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "request.json").write_text(
            json.dumps({"program": program, "grids": materialized}),
            encoding="utf-8",
        )
        worker = r'''import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", worker], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(
                "Racket worker failed: "
                + result.get("stderr", "")
                + result.get("stdout", "")
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(materialized):
            raise RuntimeError("Racket worker returned an incomplete batch")
        for output in outputs:
            _validate_grid(output)
        return outputs


def build_episode(seed: int, setting: str | None = None) -> dict[str, Any]:
    """Choose one hidden setting once, then label a four-pair episode in Racket."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    chosen = choose_setting(seed) if setting is None else _validate_setting(setting)
    program = program_for(chosen)
    inputs = episode_inputs(seed)
    outputs = run_program(program, inputs)
    generator = _load_selected_generator()
    for index, (grid, output) in enumerate(zip(inputs, outputs)):
        mirror = python_apply(grid, chosen)
        if output != mirror:
            raise AssertionError(f"Racket/Python mismatch at pair {index} for {chosen}")
        if chosen == DEFAULT_VALUE and output != generator.rule_mirror(grid):
            raise AssertionError(f"default prototype diverged from selected rule at pair {index}")
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(inputs, outputs)
    ]
    return {
        "schema": "ee6a99e8b7f9_parametric_episode/1",
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            PARAMETER_NAME: chosen,
            "chosen_once_per_episode": True,
            "rule_sha256": _sha256_text(program),
            "label_authority": "executed_racket",
        },
        "train": pairs[:3],
        "test": pairs[3:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, rule source, and query answer."""
    meta = episode.get("meta", {})
    return {
        "schema": "ee6a99e8b7f9_parametric_public/1",
        "meta": {
            "task_id": TASK_ID,
            "prototype": True,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": meta.get("seed"),
        },
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _cell_disagreements(first: list[list[int]], second: list[list[int]]) -> int:
    return sum(
        left != right
        for row_left, row_right in zip(first, second)
        for left, right in zip(row_left, row_right)
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(out_dir: Path = HERE) -> dict[str, Any]:
    """Write rules, complete episodes, public views, and hash-bound evidence."""
    out_dir = Path(out_dir)
    rules_dir = out_dir / "rules"
    episodes_dir = out_dir / "episodes"
    challenges_dir = out_dir / "challenges"
    for directory in (rules_dir, episodes_dir, challenges_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generator_path = TASK_HOME / "generator.py"
    source_path = Path(__file__).resolve()
    settings: dict[str, Any] = {}
    written: list[Path] = []
    for setting in ALLOWED_VALUES:
        rival = next(value for value in ALLOWED_VALUES if value != setting)
        seed = PROTOTYPE_SEEDS[setting]
        program = program_for(setting)
        rule_path = rules_dir / f"{setting}.rkt"
        rule_path.write_text(program + "\n", encoding="utf-8")
        written.append(rule_path)

        episode = build_episode(seed, setting=setting)
        episode_path = episodes_dir / f"{setting}.json"
        challenge_path = challenges_dir / f"{setting}.json"
        _write_json(episode_path, episode)
        _write_json(challenge_path, public_challenge(episode))
        written.extend((episode_path, challenge_path))

        all_pairs = episode["train"] + episode["test"]
        rival_outputs = run_program(program_for(rival), [pair["input"] for pair in all_pairs])
        disagreements = [
            _cell_disagreements(pair["output"], rival_output)
            for pair, rival_output in zip(all_pairs, rival_outputs)
        ]
        if not all(count > 0 for count in disagreements):
            raise AssertionError(f"parameter rival survived one or more pairs for {setting}")
        settings[setting] = {
            "seed": seed,
            "rival": rival,
            "rule_path": rule_path.relative_to(out_dir).as_posix(),
            "rule_sha256": _sha256_bytes(rule_path.read_bytes()),
            "program_sha256_without_trailing_newline": _sha256_text(program),
            "racket_program": program,
            "episode_path": episode_path.relative_to(out_dir).as_posix(),
            "public_challenge_path": challenge_path.relative_to(out_dir).as_posix(),
            "label_authority": "executed_racket",
            "demo_cell_disagreements_vs_rival": disagreements[:3],
            "query_cell_disagreements_vs_rival": disagreements[3:],
            "all_pairs_distinguish_rival": all(count > 0 for count in disagreements),
        }

    evidence = {
        "schema": "ee6a99e8b7f9_parametric_prototype/1",
        "status": "proposed_prototype",
        "production_integration": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_VALUES),
            "default": DEFAULT_VALUE,
            "chosen_once_per_episode": True,
            "invariant_reasoning": [
                "identify filled gray and pink rectangles",
                "associate each exterior dot with exactly one rectangle edge",
                "erase gray rectangles and copy gray dots to the inner edge",
                "retain pink rectangles, clear pink source dots, and move them to a center axis",
            ],
            "dependent_input_constraints": [
                "each pair has at least one pink rectangle with an even axis",
                "a pink exterior dot approaches along that even axis",
                "three demonstrations each distinguish lower from upper before the query",
            ],
        },
        "prototype_source": source_path.relative_to(ROOT).as_posix(),
        "prototype_source_sha256": _sha256_bytes(source_path.read_bytes()),
        "selected_generator": generator_path.relative_to(ROOT).as_posix(),
        "selected_generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "canonical_program_sha256": _sha256_text(canonical_program()),
        "settings": settings,
        "reproduction": {
            "working_directory": "WORK/repo",
            "command": (
                "python3 generators/ee6a99e8b7f9/workspace/parametric/prototype.py "
                "materialize --out ../checks/parametric/pink-center-tie-v1"
            ),
        },
        "limitations": [
            "prototype only; not wired into the production API or approval catalog",
            "bounded evidence covers two retained four-pair episodes, not every seed",
            "the parameter affects only pink rectangles with an even approached axis",
            "odd-axis pink rectangles and all gray behavior are identical across settings",
            "the production canonical authority remains the lower setting only",
        ],
    }
    evidence_path = out_dir / "evidence.json"
    _write_json(evidence_path, evidence)
    written.append(evidence_path)

    manifest = {
        "schema": "ee6a99e8b7f9_parametric_manifest/1",
        "files": {
            path.relative_to(out_dir).as_posix(): _sha256_bytes(path.read_bytes())
            for path in sorted(written)
        },
    }
    _write_json(out_dir / "manifest.json", manifest)
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("materialize", "show"), nargs="?", default="materialize")
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args(argv)
    if args.command == "materialize":
        evidence = materialize(args.out)
    else:
        evidence = json.loads((args.out / "evidence.json").read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "parameter": evidence["parameter"],
                "settings": {
                    name: {
                        "rule_sha256": details["rule_sha256"],
                        "demo_cell_disagreements_vs_rival": details[
                            "demo_cell_disagreements_vs_rival"
                        ],
                        "query_cell_disagreements_vs_rival": details[
                            "query_cell_disagreements_vs_rival"
                        ],
                    }
                    for name, details in evidence["settings"].items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
