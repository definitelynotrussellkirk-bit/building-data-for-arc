#!/usr/bin/env python3
"""Proposed episode-level corner-rotation variant for ARC task 144582f287b5.

The selected production generator and canonical authority remain unchanged.  This
standalone authoring tool chooses one source-block rotation per episode,
materializes the matching Racket rule, executes every label through the bundled
Racket bridge, checks all other declared settings as parameter rivals, and writes
answer-masked public challenges separately from private evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "144582f287b5"
CANONICAL_PROGRAM_SHA256 = "5ad0a3ff74fcf99b1f0242009b86e0fbd0fa6903ab8b80f06d32969224b4b7fe"
PARAMETER_NAME = "source_rotation_quarter_turns"
ALLOWED_QUARTER_TURNS = (0, 1, 2, 3)
DEFAULT_QUARTER_TURNS = 0
SOURCE_POSITIONS = ((1, 1), (1, 2), (2, 1), (2, 2))
EPISODE_SPECS = (
    (4, 4, "none"),
    (4, 4, "corners"),
    (6, 6, "source_halo"),
    (7, 5, "edge_midpoints"),
)

# Source coordinates occupying output corners after rotating the extracted 2x2
# source block clockwise by 0, 90, 180, or 270 degrees.
_ROTATED_COORDINATES = {
    0: ((1, 1), (1, 2), (2, 1), (2, 2)),
    1: ((2, 1), (1, 1), (2, 2), (1, 2)),
    2: ((2, 2), (2, 1), (1, 2), (1, 1)),
    3: ((1, 2), (2, 2), (1, 1), (2, 1)),
}


def sha256(data: bytes | str) -> str:
    payload = data.encode() if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    return sha256(json.dumps(grid, separators=(",", ":"), sort_keys=False))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer, not bool")
    return seed


def _validate_turns(quarter_turns: Any) -> int:
    if type(quarter_turns) is not int or quarter_turns not in ALLOWED_QUARTER_TURNS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_QUARTER_TURNS}, not bool"
        )
    return quarter_turns


def choose_quarter_turns(seed: int) -> int:
    """Choose the hidden rule once for the entire episode."""
    seed = _validate_seed(seed)
    return ALLOWED_QUARTER_TURNS[seed % len(ALLOWED_QUARTER_TURNS)]


def canonical_source(*, root: Path | None = None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    matches: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}; found {len(matches)}")
    source = matches[0]
    actual = sha256(source)
    if actual != CANONICAL_PROGRAM_SHA256:
        raise ValueError(
            "canonical program bytes changed; review the task-specific parametric adapter "
            f"(expected {CANONICAL_PROGRAM_SHA256}, got {actual})"
        )
    return source


def _render_rule(coordinates: tuple[tuple[int, int], ...]) -> str:
    if len(coordinates) != 4:
        raise ValueError("corner mapping must contain four source coordinates")
    (tl, tr, bl, br) = coordinates
    return f"""(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (cond
                      ((and (zero? r) (zero? c)) (at g {tl[0]} {tl[1]}))
                      ((and (zero? r) (= c (- w 1))) (at g {tr[0]} {tr[1]}))
                      ((and (= r (- h 1)) (zero? c)) (at g {bl[0]} {bl[1]}))
                      ((and (= r (- h 1)) (= c (- w 1))) (at g {br[0]} {br[1]}))
                      (else 0))))))"""


def materialize_rule(
    quarter_turns: int,
    *,
    root: Path | None = None,
    source: str | None = None,
) -> str:
    """Materialize the exact rule for one bounded parameter setting.

    The default setting returns the selected canonical bytes exactly.  Alternative
    settings change only which of the same four fixed source cells reaches each
    output corner.
    """
    turns = _validate_turns(quarter_turns)
    canonical = canonical_source(root=root) if source is None else source
    if sha256(canonical) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical source SHA-256 does not match the pinned authority")
    if turns == DEFAULT_QUARTER_TURNS:
        return canonical
    return _render_rule(_ROTATED_COORDINATES[turns])


def _grid_literal(grid: list[list[int]]) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"


def racket_application(program: str, grid: list[list[int]]) -> str:
    callable_rule = strip_rule_wrapper(program)
    return f"({callable_rule} {_grid_literal(grid)})"


def execute_rule(
    program: str,
    grid: list[list[int]],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one materialized rule through the bundled Racket runtime."""
    if bridge is None:
        with RacketBridge(timeout=10, startup_timeout=30) as owned:
            return normalize_grid(owned.eval_text(racket_application(program, grid)))
    return normalize_grid(bridge.eval_text(racket_application(program, grid)))


def _validate_plain_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty rectangle")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    height = len(grid)
    if height < 3 or width < 3:
        raise ValueError("grid must contain the fixed source coordinates")
    return height, width


def python_apply(grid: list[list[int]], quarter_turns: int) -> list[list[int]]:
    """Independent small oracle used only to cross-check Racket evidence."""
    turns = _validate_turns(quarter_turns)
    height, width = _validate_plain_grid(grid)
    coordinates = _ROTATED_COORDINATES[turns]
    values = [grid[row][col] for row, col in coordinates]
    output = [[0] * width for _ in range(height)]
    output[0][0], output[0][width - 1] = values[0], values[1]
    output[height - 1][0], output[height - 1][width - 1] = values[2], values[3]
    return output


def _decoy_positions(pattern: str, height: int, width: int) -> tuple[tuple[int, int], ...]:
    if pattern == "none":
        return ()
    if pattern == "corners":
        return ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    if pattern == "source_halo":
        return ((0, 1), (1, 0), (2, 3), (3, 2))
    if pattern == "edge_midpoints":
        return (
            (0, width // 2),
            (height // 2, width - 1),
            (height - 1, (width - 1) // 2),
            ((height - 1) // 2, 0),
        )
    raise ValueError(f"unknown prototype decoy pattern {pattern!r}")


def episode_inputs(seed: int) -> list[list[list[int]]]:
    """Return four parameter-independent input witnesses for one episode.

    Consecutive seeds 0..3 deliberately share inputs while selecting different
    rotations, making setting differences attributable to the rule rather than
    to input sampling.
    """
    seed = _validate_seed(seed)
    data_seed = seed // len(ALLOWED_QUARTER_TURNS)
    rng = random.Random((data_seed + 1) * 1_000_003)
    grids: list[list[list[int]]] = []
    for height, width, pattern in EPISODE_SPECS:
        source_and_decoy = rng.sample(range(1, 10), 5)
        grid = [[0] * width for _ in range(height)]
        for (row, col), value in zip(SOURCE_POSITIONS, source_and_decoy[:4]):
            grid[row][col] = value
        decoy_color = (
            source_and_decoy[0]
            if pattern == "corners" and height == 4 and width == 4
            else source_and_decoy[4]
        )
        for row, col in _decoy_positions(pattern, height, width):
            grid[row][col] = decoy_color
        grids.append(grid)
    return grids


def _build_episode_with_bridge(
    seed: int,
    *,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    turns = choose_quarter_turns(seed)
    inputs = episode_inputs(seed)
    programs = {
        value: materialize_rule(value, root=root) for value in ALLOWED_QUARTER_TURNS
    }
    outputs: dict[int, list[list[list[int]]]] = {value: [] for value in ALLOWED_QUARTER_TURNS}
    execution_checks: list[dict[str, Any]] = []
    for pair_index, grid in enumerate(inputs):
        for value in ALLOWED_QUARTER_TURNS:
            output = execute_rule(programs[value], grid, bridge=bridge)
            oracle = python_apply(grid, value)
            outputs[value].append(output)
            execution_checks.append(
                {
                    "pair_index": pair_index,
                    "parameters": {PARAMETER_NAME: value},
                    "input_sha256": grid_sha256(grid),
                    "program_sha256": sha256(programs[value]),
                    "application_sha256": sha256(racket_application(programs[value], grid)),
                    "output_sha256": grid_sha256(output),
                    "oracle_match": output == oracle,
                }
            )

    labelled_pairs = [
        {"input": copy.deepcopy(grid), "output": copy.deepcopy(outputs[turns][index])}
        for index, grid in enumerate(inputs)
    ]
    rivals: list[dict[str, Any]] = []
    ambiguities: list[int] = []
    for rival in ALLOWED_QUARTER_TURNS:
        if rival == turns:
            continue
        demo_mismatches = [
            index for index in range(3) if outputs[rival][index] != outputs[turns][index]
        ]
        query_mismatches = [0] if outputs[rival][3] != outputs[turns][3] else []
        status = "refuted_by_demonstrations" if demo_mismatches else "ambiguous"
        if not demo_mismatches:
            ambiguities.append(rival)
        rivals.append(
            {
                "parameters": {PARAMETER_NAME: rival},
                "status": status,
                "demonstration_mismatch_indices": demo_mismatches,
                "query_mismatch_indices": query_mismatches,
            }
        )

    return {
        "schema": "arcpuzzles-task-parametric-episode-v1",
        "task_id": TASK_ID,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": {PARAMETER_NAME: turns},
        "parameter_selection": (
            f"ALLOWED_QUARTER_TURNS[seed % {len(ALLOWED_QUARTER_TURNS)}], "
            "chosen once before all pair labels"
        ),
        "racket_source": programs[turns],
        "racket_sha256": sha256(programs[turns]),
        "programs": [
            {
                "parameters": {PARAMETER_NAME: value},
                "sha256": sha256(programs[value]),
                "source": programs[value],
            }
            for value in ALLOWED_QUARTER_TURNS
        ],
        "train": labelled_pairs[:3],
        "test": labelled_pairs[3:],
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
        "execution_checks": execution_checks,
        "input_specs": [
            {"height": height, "width": width, "decoy_pattern": pattern}
            for height, width, pattern in EPISODE_SPECS
        ],
        "limitations": [
            "Only the four declared quarter-turn settings are tested as parameter rivals.",
            "Inputs keep the source block at fixed cells (1,1)..(2,2) and use four finite decoy profiles.",
            "Distinct source colors make orientation directly identifiable; repeated source colors are outside this prototype sampler.",
            "This prototype is not a production parametric API and carries no canonical approval.",
        ],
    }


def build_episode(
    seed: int,
    *,
    root: Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    root = find_root(__file__) if root is None else Path(root)
    _validate_seed(seed)
    if bridge is None:
        with RacketBridge(timeout=10, startup_timeout=30) as owned:
            return _build_episode_with_bridge(seed, root=root, bridge=owned)
    return _build_episode_with_bridge(seed, root=root, bridge=bridge)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return demonstrations plus input-only queries, omitting hidden metadata."""
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _relative_file_record(path: Path, out: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(out).as_posix(),
        "sha256": sha256(path.read_bytes()),
        "bytes": path.stat().st_size,
    }


def write_evidence(
    seeds: Iterable[int],
    *,
    out: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    """Write bounded Racket-backed evidence for all four parameter settings."""
    root = find_root(__file__) if root is None else Path(root)
    normalized_seeds = tuple(_validate_seed(seed) for seed in seeds)
    if len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("evidence seeds must be unique")
    represented = {choose_quarter_turns(seed) for seed in normalized_seeds}
    if represented != set(ALLOWED_QUARTER_TURNS):
        raise ValueError(
            "evidence seeds must demonstrate every quarter-turn setting; "
            f"represented={sorted(represented)}"
        )

    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    written: list[Path] = []

    programs = {
        value: materialize_rule(value, root=root) for value in ALLOWED_QUARTER_TURNS
    }
    program_rows: list[dict[str, Any]] = []
    for value, source in programs.items():
        path = out / "rules" / f"source_rotation_quarter_turns_{value}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        written.append(path)
        program_rows.append(
            {
                "parameters": {PARAMETER_NAME: value},
                "path": path.relative_to(out).as_posix(),
                "sha256": sha256(source),
                "byte_identical_to_canonical": source == canonical_source(root=root),
            }
        )

    canonical_checks: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    episodes: list[dict[str, Any]] = []
    with RacketBridge(timeout=10, startup_timeout=30) as bridge:
        runtime_identity = bridge.runtime_identity
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(programs[DEFAULT_QUARTER_TURNS], pair["input"], bridge=bridge)
            canonical_checks.append(
                {
                    "split": pair.get("split"),
                    "variant": pair.get("variant"),
                    "pair_index": pair.get("pair_index"),
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output_sha256": grid_sha256(actual),
                    "passed": actual == pair["output"],
                }
            )

        for seed in normalized_seeds:
            episode = _build_episode_with_bridge(seed, root=root, bridge=bridge)
            episodes.append(episode)
            private_path = out / "private" / f"episode_seed_{seed}.json"
            public_path = out / "public" / f"challenge_seed_{seed}.json"
            _write_json(private_path, episode)
            _write_json(public_path, public_challenge(episode))
            written.extend((private_path, public_path))
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "private_path": private_path.relative_to(out).as_posix(),
                    "public_path": public_path.relative_to(out).as_posix(),
                    "ambiguous_parameter_rivals": len(episode["ambiguities"]),
                    "racket_execution_checks": len(episode["execution_checks"]),
                }
            )

        witness_grid = episode_inputs(normalized_seeds[0])[0]
        witness_outputs = {
            str(value): execute_rule(programs[value], witness_grid, bridge=bridge)
            for value in ALLOWED_QUARTER_TURNS
        }

    canonical_path_out = out / "canonical_default_checks.json"
    witness_path = out / "setting_difference_witness.json"
    _write_json(canonical_path_out, canonical_checks)
    _write_json(
        witness_path,
        {
            "input": witness_grid,
            "input_sha256": grid_sha256(witness_grid),
            "outputs_by_quarter_turns": witness_outputs,
            "output_sha256_by_quarter_turns": {
                value: grid_sha256(grid) for value, grid in witness_outputs.items()
            },
            "all_outputs_distinct": len(
                {json.dumps(grid, separators=(",", ":")) for grid in witness_outputs.values()}
            )
            == len(ALLOWED_QUARTER_TURNS),
        },
    )
    written.extend((canonical_path_out, witness_path))

    all_checks = [row for episode in episodes for row in episode["execution_checks"]]
    all_rivals = [row for episode in episodes for row in episode["parameter_rivals"]]
    report: dict[str, Any] = {
        "schema": "arcpuzzles-task-parametric-prototype-v1",
        "task_id": TASK_ID,
        "status": "proposed_unapproved",
        "approved": False,
        "passed": (
            programs[DEFAULT_QUARTER_TURNS] == canonical_source(root=root)
            and all(row["passed"] for row in canonical_checks)
            and all(row["oracle_match"] for row in all_checks)
            and all(row["status"] == "refuted_by_demonstrations" for row in all_rivals)
            and len({choose_quarter_turns(seed) for seed in normalized_seeds})
            == len(ALLOWED_QUARTER_TURNS)
        ),
        "parameter_contract": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_QUARTER_TURNS),
            "original_default": DEFAULT_QUARTER_TURNS,
            "meaning": "clockwise quarter-turns applied to the extracted fixed 2x2 source before corner scatter",
            "chosen_once_per_episode": True,
            "selection": f"ALLOWED_QUARTER_TURNS[seed % {len(ALLOWED_QUARTER_TURNS)}]",
        },
        "input_constraints": {
            "source_positions": [list(position) for position in SOURCE_POSITIONS],
            "source_colors": "four pairwise-distinct nonzero ARC colors",
            "episode_specs": [
                {"height": h, "width": w, "decoy_pattern": pattern}
                for h, w, pattern in EPISODE_SPECS
            ],
            "same_inputs_for_seed_residue_block": True,
        },
        "canonical_authority_changed": False,
        "canonical_program_sha256": sha256(canonical_source(root=root)),
        "canonical_ledger_sha256": sha256(canonical_path(root).read_bytes()),
        "runtime": runtime_identity,
        "payload": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "seeds": list(normalized_seeds),
        "programs": program_rows,
        "episodes": episode_rows,
        "counts": {
            "settings_materialized": len(program_rows),
            "episodes": len(episodes),
            "complete_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
            "racket_setting_pair_executions": len(all_checks),
            "oracle_matches": sum(row["oracle_match"] for row in all_checks),
            "parameter_rivals_checked": len(all_rivals),
            "ambiguous_parameter_rivals": sum(
                row["status"] != "refuted_by_demonstrations" for row in all_rivals
            ),
            "canonical_pairs_checked": len(canonical_checks),
            "canonical_pairs_passed": sum(row["passed"] for row in canonical_checks),
        },
        "limitations": [
            "Bounded evidence covers only the saved seeds, four declared rotations, and finite input profiles.",
            "Parameter-rival checks do not establish uniqueness against every possible program.",
            "Repeated source colors, translated source blocks, arbitrary decoys, and other scatter targets are outside this prototype sampler.",
            "No selected generator, canonical Racket authority, catalog approval, or production API was changed.",
        ],
    }
    report["files"] = [_relative_file_record(path, out) for path in sorted(written)]
    _write_json(out / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3])
    args = parser.parse_args()
    try:
        report = write_evidence(args.seeds, out=args.out)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "passed": report["passed"],
                "parameter_contract": report["parameter_contract"],
                "counts": report["counts"],
                "out": str(Path(args.out)),
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
