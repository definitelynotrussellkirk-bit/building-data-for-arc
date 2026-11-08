#!/usr/bin/env python3
"""Racket-backed episode-level diagonal-mode prototype for 888fb4310749.

This is proposed task-local authoring evidence, not a production-rule change.
The canonical/default setting stamps both diagonal families.  The alternatives
retain the same source extraction, period, rotated companion, complement color,
clipping, and paint order while keeping only the falling (\\) or rising (/)
diagonal family for the entire episode.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "888fb4310749"
SCHEMA = "888fb4310749-parametric-diagonal-mode-v1"
DIAGONAL_MODES = ("both", "falling", "rising")
DEFAULT_DIAGONAL_MODE = "both"
N_TRAIN = 3
N_TEST = 1
FIXTURE_PROFILES = ("wide_block", "tall_block", "square_block", "edge_anchor")
PARAMETERS = {
    "diagonal_mode": {
        "allowed": DIAGONAL_MODES,
        "default": DEFAULT_DIAGONAL_MODE,
        "meaning": (
            "Which sign families are used when propagating primary and rotated "
            "stamps: both, falling (\\), or rising (/)."
        ),
        "input_constraint": (
            "Episodes use lawful nonzero rectangles on canvases where each mode "
            "produces a distinct result; inputs themselves do not encode the mode."
        ),
    }
}
_MODE_SIGNS = {
    "both": (1, -1),
    "falling": (1,),
    "rising": (-1,),
}
_SIGN_SITE = "(list 1 -1)"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _json_sha256(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(data)


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain Python int")
    return seed


def _validate_mode(diagonal_mode: str) -> str:
    if type(diagonal_mode) is not str or diagonal_mode not in DIAGONAL_MODES:
        raise ValueError(
            f"diagonal_mode must be exactly one of {DIAGONAL_MODES}"
        )
    return diagonal_mode


def choose_parameters(seed: int) -> dict[str, str]:
    """Choose one hidden rule setting exactly once for an episode."""
    _validate_seed(seed)
    return {"diagonal_mode": DIAGONAL_MODES[seed % len(DIAGONAL_MODES)]}


def canonical_program(*, root: str | Path | None = None) -> str:
    """Read the single exact canonical Racket source for this task."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    programs: list[str] = []
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                programs.append(str(row["program_solution"]))
    unique = list(dict.fromkeys(programs))
    if len(unique) != 1:
        raise ValueError(
            f"expected one exact canonical program for {TASK_ID}, found {len(unique)}"
        )
    return unique[0]


def render_program(
    diagonal_mode: str = DEFAULT_DIAGONAL_MODE,
    *,
    root: str | Path | None = None,
) -> str:
    """Instantiate exact Racket; the default setting is byte-identical."""
    diagonal_mode = _validate_mode(diagonal_mode)
    source = canonical_program(root=root)
    if source.count(_SIGN_SITE) != 2:
        raise ValueError(
            "canonical diagonal sign sites changed; manually reassess this prototype"
        )
    if diagonal_mode == DEFAULT_DIAGONAL_MODE:
        return source
    replacement = "(list 1)" if diagonal_mode == "falling" else "(list -1)"
    changed = source.replace(_SIGN_SITE, replacement)
    if changed == source or changed.count(replacement) != 2:
        raise ValueError("diagonal-mode materialization did not alter both sign sites")
    return changed


def _rule_facts(grid: list[list[int]]) -> dict[str, int]:
    cells = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("the prototype requires at least one nonzero cell")
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(column for _, column in cells)
    col1 = max(column for _, column in cells)
    block_height = row1 - row0 + 1
    block_width = col1 - col0 + 1
    color = grid[row0][col0]
    return {
        "row0": row0,
        "col0": col0,
        "block_height": block_height,
        "block_width": block_width,
        "color": color,
        "alt_color": 9 - color,
        "step": block_height + block_width,
    }


def _intersects(
    row0: int,
    col0: int,
    block_height: int,
    block_width: int,
    height: int,
    width: int,
) -> bool:
    return (
        row0 <= height - 1
        and row0 + block_height - 1 >= 0
        and col0 <= width - 1
        and col0 + block_width - 1 >= 0
    )


def _stamp(
    grid: list[list[int]],
    row0: int,
    col0: int,
    block_height: int,
    block_width: int,
    color: int,
) -> None:
    height, width = len(grid), len(grid[0])
    for row in range(row0, row0 + block_height):
        for column in range(col0, col0 + block_width):
            if 0 <= row < height and 0 <= column < width:
                grid[row][column] = color


def apply_python(
    grid: list[list[int]], diagonal_mode: str
) -> list[list[int]]:
    """Independent parity oracle for the three bounded mode settings."""
    grid = normalize_grid(grid)
    diagonal_mode = _validate_mode(diagonal_mode)
    facts = _rule_facts(grid)
    height, width = len(grid), len(grid[0])
    row0, col0 = facts["row0"], facts["col0"]
    block_height = facts["block_height"]
    block_width = facts["block_width"]
    step = facts["step"]
    signs = _MODE_SIGNS[diagonal_mode]
    output = deepcopy(grid)

    for multiple in range(-40, 41):
        for sign in signs:
            diagonal_row = row0 + multiple * step
            diagonal_col = col0 + sign * multiple * step
            rotated_row = diagonal_row + block_height
            rotated_col = diagonal_col + (
                block_width if sign == 1 else -block_height
            )
            if _intersects(
                rotated_row,
                rotated_col,
                block_width,
                block_height,
                height,
                width,
            ):
                _stamp(
                    output,
                    rotated_row,
                    rotated_col,
                    block_width,
                    block_height,
                    facts["alt_color"],
                )

    same_anchors: list[tuple[int, int]] = []
    for multiple in range(-40, 41):
        for sign in signs:
            anchor = (
                row0 + multiple * step,
                col0 + sign * multiple * step,
            )
            if (
                _intersects(
                    anchor[0],
                    anchor[1],
                    block_height,
                    block_width,
                    height,
                    width,
                )
                and anchor not in same_anchors
            ):
                same_anchors.append(anchor)
    for anchor_row, anchor_col in same_anchors:
        _stamp(
            output,
            anchor_row,
            anchor_col,
            block_height,
            block_width,
            facts["color"],
        )
    return output


def fixture_inputs(
    seed: int,
    *,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Select four deterministic lawful inputs that distinguish every mode."""
    _validate_seed(seed)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)
    grids: list[list[list[int]]] = []
    used: set[str] = set()
    for index, profile in enumerate(FIXTURE_PROFILES):
        selected = None
        for offset in range(256):
            candidate_seed = 700_001 + seed * 97 + index * 10_003 + offset
            sample_index = seed * len(FIXTURE_PROFILES) + index + offset * 17
            grid = generator.generate(
                candidate_seed,
                sample_index,
                difficulty="hard",
                scene_profile=profile,
            )
            if generator.self_check(grid):
                continue
            outputs = [apply_python(grid, mode) for mode in DIAGONAL_MODES]
            if len({_json_sha256(output) for output in outputs}) != len(DIAGONAL_MODES):
                continue
            digest = _json_sha256(grid)
            if digest in used:
                continue
            selected = normalize_grid(grid)
            used.add(digest)
            break
        if selected is None:
            raise RuntimeError(
                f"could not find a mode-distinguishing fixture for {profile!r}"
            )
        grids.append(selected)
    return grids


def _racket_datum(grid: list[list[int]]) -> str:
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def execute_racket(
    bridge: RacketBridge,
    program: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one grid through the protected real-Racket bridge."""
    grid = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.lstrip().startswith("(lambda"):
        raise ValueError("expected the selected task's native Racket lambda")
    result = bridge.eval_text(f"({function} '{_racket_datum(grid)})")
    return normalize_grid(result)


def _episode_from_outputs(
    seed: int,
    diagonal_mode: str,
    grids: list[list[list[int]]],
    outputs: dict[str, list[list[list[int]]]],
    *,
    root: str | Path | None,
    parameter_choice: str,
    label_authority: str,
) -> dict[str, Any]:
    diagonal_mode = _validate_mode(diagonal_mode)
    selected = outputs[diagonal_mode]
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(grids, selected)
    ]
    rivals: dict[str, Any] = {}
    for rival_mode in DIAGONAL_MODES:
        if rival_mode == diagonal_mode:
            continue
        rival_outputs = outputs[rival_mode]
        refuting = [
            index
            for index in range(N_TRAIN)
            if selected[index] != rival_outputs[index]
        ]
        query_differs = selected[N_TRAIN] != rival_outputs[N_TRAIN]
        if query_differs and not refuting:
            raise RuntimeError(
                f"{rival_mode} changes the query without a distinguishing demo"
            )
        rivals[rival_mode] = {
            "parameters": {"diagonal_mode": rival_mode},
            "program_sha256": _sha256_text(
                render_program(rival_mode, root=root)
            ),
            "status": "distinguished" if refuting else "indistinguishable",
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
            "outputs": {
                "train": deepcopy(rival_outputs[:N_TRAIN]),
                "test": deepcopy(rival_outputs[N_TRAIN:]),
            },
        }
    program = render_program(diagonal_mode, root=root)
    return {
        "schema": SCHEMA,
        "seed": seed,
        "parameters": {"diagonal_mode": diagonal_mode},
        "parameter_choice": parameter_choice,
        "parameter_draw_count": 1,
        "program": program,
        "program_sha256": _sha256_text(program),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "rivals": rivals,
        "label_authority": label_authority,
    }


def generate_episode_python(
    seed: int,
    *,
    diagonal_mode: str | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a fast parity-oracle episode; retained labels use Racket."""
    _validate_seed(seed)
    chosen = (
        choose_parameters(seed)["diagonal_mode"]
        if diagonal_mode is None
        else _validate_mode(diagonal_mode)
    )
    grids = fixture_inputs(seed, root=root)
    outputs = {
        mode: [apply_python(grid, mode) for grid in grids]
        for mode in DIAGONAL_MODES
    }
    return _episode_from_outputs(
        seed,
        chosen,
        grids,
        outputs,
        root=root,
        parameter_choice=(
            "deterministic_seed_once_per_episode"
            if diagonal_mode is None
            else "explicit_once_per_episode"
        ),
        label_authority="independent Python parity oracle (not retained evidence)",
    )


def generate_episode(
    seed: int,
    *,
    diagonal_mode: str | None = None,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one setting and label the complete episode in real Racket."""
    _validate_seed(seed)
    chosen = (
        choose_parameters(seed)["diagonal_mode"]
        if diagonal_mode is None
        else _validate_mode(diagonal_mode)
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    grids = fixture_inputs(seed, root=root_path)

    def build(active: RacketBridge) -> dict[str, Any]:
        outputs: dict[str, list[list[list[int]]]] = {}
        for mode in DIAGONAL_MODES:
            program = render_program(mode, root=root_path)
            racket_outputs = [
                execute_racket(active, program, grid) for grid in grids
            ]
            python_outputs = [apply_python(grid, mode) for grid in grids]
            if racket_outputs != python_outputs:
                raise RuntimeError(
                    f"Racket/Python parity failure for diagonal_mode={mode}"
                )
            outputs[mode] = racket_outputs
        return _episode_from_outputs(
            seed,
            chosen,
            grids,
            outputs,
            root=root_path,
            parameter_choice=(
                "deterministic_seed_once_per_episode"
                if diagonal_mode is None
                else "explicit_once_per_episode"
            ),
            label_authority=(
                "protected included Racket bridge executing exact instantiated "
                "programs for selected and rival settings"
            ),
        )

    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
        return build(active)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden settings, reference code, rival labels, and query output."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _first_seed_for(base_seed: int, mode: str) -> int:
    mode = _validate_mode(mode)
    for seed in range(base_seed, base_seed + len(DIAGONAL_MODES) * 2):
        if choose_parameters(seed)["diagonal_mode"] == mode:
            return seed
    raise AssertionError(f"could not resolve seed for {mode}")


def _inventory(root: Path, *, exclude: set[str] | None = None) -> list[dict[str, Any]]:
    excluded = exclude or set()
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256_bytes(path.read_bytes()),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in excluded
    ]


def materialize(
    output: str | Path,
    *,
    base_seed: int = 20261023,
) -> dict[str, Any]:
    """Materialize three complete, Racket-labeled diagonal-mode episodes."""
    _validate_seed(base_seed)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    canonical = canonical_program(root=root)
    default = render_program(DEFAULT_DIAGONAL_MODE, root=root)
    source_paths = [
        Path(__file__),
        Path(__file__).parent / "README.md",
        Path(__file__).parents[2] / "tests" / "test_parametric_diagonal_mode.py",
        Path(__file__).parents[2]
        / "counterexamples"
        / "fixed_36_color_shortcut.json",
    ]
    report: dict[str, Any] = {
        "schema": f"{SCHEMA}-report",
        "status": "incomplete",
        "scope": (
            "Proposed task-local extension only; not a canonical rule change, "
            "production axis, approval refresh, or training-admission claim."
        ),
        "parameter_spec": PARAMETERS,
        "choice_policy": (
            "One diagonal_mode is selected deterministically from the episode "
            "seed and reused for all demonstrations and the query."
        ),
        "invariant_reasoning": (
            "Extract the nonzero rectangle, use period height+width, stamp the "
            "rotated complementary-color companion first, then source-color "
            "same-orientation stamps, clipping at the canvas. Only the active "
            "diagonal sign family changes."
        ),
        "input_policy": {
            "profiles": list(FIXTURE_PROFILES),
            "train_count": N_TRAIN,
            "test_count": N_TEST,
            "parameter_independent": True,
            "all_pairs_distinguish_all_modes": True,
        },
        "limitations": [
            "Only both, falling, and rising sign-family settings are studied.",
            "Evidence covers one deterministic four-input episode per setting plus the four canonical labels.",
            "Pairwise mode rivals are checked; undeclared rule families remain unproven.",
            "The prototype is isolated and does not alter the selected production generator or authority.",
        ],
        "default_program_exact_canonical": default == canonical,
        "source_hashes": {
            **{
                str(path.relative_to(root)): _sha256_bytes(path.read_bytes())
                for path in source_paths
                if path.is_file()
            },
            str(generator_path.relative_to(root)): generator_sha,
            "canonical_program": _sha256_text(canonical),
        },
        "invocation": {
            "cwd": str(Path.cwd()),
            "argv": [sys.executable, *sys.argv],
        },
        "episodes": [],
        "canonical_checks": [],
    }

    try:
        with RacketBridge() as bridge:
            report["runtime"] = bridge.runtime_identity
            for mode in DIAGONAL_MODES:
                rule_path = output / "private" / "rules" / f"diagonal-{mode}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(render_program(mode, root=root), encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_racket(bridge, default, pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "expected_sha256": _json_sha256(pair["output"]),
                        "actual_sha256": _json_sha256(actual),
                        "passed": actual == pair["output"],
                    }
                )

            for index, mode in enumerate(DIAGONAL_MODES, start=1):
                episode_seed = _first_seed_for(base_seed, mode)
                episode = generate_episode(
                    episode_seed,
                    root=root,
                    bridge=bridge,
                )
                if episode["parameters"] != {"diagonal_mode": mode}:
                    raise AssertionError("seed-selected mode did not match requested coverage")
                private_path = (
                    output / "private" / "episodes" / f"episode-{index:03d}.json"
                )
                public_path = output / "public" / f"episode-{index:03d}.json"
                _write_json(private_path, episode)
                _write_json(public_path, public_challenge(episode))
                report["episodes"].append(
                    {
                        "seed": episode_seed,
                        "parameters": episode["parameters"],
                        "parameter_choice": episode["parameter_choice"],
                        "program_sha256": episode["program_sha256"],
                        "private_path": private_path.relative_to(output).as_posix(),
                        "public_path": public_path.relative_to(output).as_posix(),
                        "rivals": episode["rivals"],
                    }
                )

            witness_grid = fixture_inputs(base_seed, root=root)[N_TRAIN]
            witness_outputs = {
                mode: execute_racket(
                    bridge,
                    render_program(mode, root=root),
                    witness_grid,
                )
                for mode in DIAGONAL_MODES
            }
            if any(
                witness_outputs[mode] != apply_python(witness_grid, mode)
                for mode in DIAGONAL_MODES
            ):
                raise RuntimeError("cross-mode witness failed Racket/Python parity")
            witness = {
                "input": witness_grid,
                "input_sha256": _json_sha256(witness_grid),
                "profile": FIXTURE_PROFILES[N_TRAIN],
                "outputs": witness_outputs,
                "output_sha256": {
                    mode: _json_sha256(value)
                    for mode, value in witness_outputs.items()
                },
                "all_outputs_pairwise_distinct": (
                    len({_json_sha256(value) for value in witness_outputs.values()})
                    == len(DIAGONAL_MODES)
                ),
                "all_outputs_from_executed_racket": True,
            }
            _write_json(output / "private" / "cross-mode-witness.json", witness)
            report["cross_mode_witness"] = witness

        canonical_passed = sum(
            check["passed"] for check in report["canonical_checks"]
        )
        demos_distinguish = all(
            all(
                rival["refuting_demonstration_indices"]
                for rival in episode["rivals"].values()
            )
            for episode in report["episodes"]
        )
        report.update(
            {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "complete_episodes": len(report["episodes"]),
                "all_labels_and_rivals_executed_in_racket": True,
                "all_episode_demonstrations_distinguish_rivals": demos_distinguish,
            }
        )
        report["status"] = (
            "prototype"
            if report["default_program_exact_canonical"]
            and canonical_passed == len(report["canonical_checks"])
            and len(report["episodes"]) == len(DIAGONAL_MODES)
            and demos_distinguish
            and report["cross_mode_witness"]["all_outputs_pairwise_distinct"]
            else "failed"
        )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        _write_json(output / "report.json", report)
        raise

    _write_json(output / "report.json", report)
    manifest = {
        "schema": "arc-parametric-evidence-manifest-v1",
        "task_id": TASK_ID,
        "files": _inventory(output, exclude={"manifest.json"}),
    }
    _write_json(output / "manifest.json", manifest)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261023)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = materialize(args.out, base_seed=args.base_seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "complete_episodes": report["complete_episodes"],
                "canonical_labels_passed": report["canonical_labels_passed"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return int(report["status"] != "prototype")


if __name__ == "__main__":
    raise SystemExit(main())
