#!/usr/bin/env python3
"""Racket-backed episode-level connectivity prototype for eefadafb2b7b.

This is proposed task-local authoring evidence, not a production-rule change.
The canonical setting remains 8-connectivity byte-for-byte.  The alternative
changes only the cyan component extractor from ``objects-8`` to ``objects``
(4-connectivity), preserving the two red blocks, ring-contact test, bridge
predicate, output shape, and output colors.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
import random
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

TASK_ID = "eefadafb2b7b"
SCHEMA = "eefadafb2b7b-parametric-connectivity-v1"
CONNECTIVITIES = (8, 4)
DEFAULT_CONNECTIVITY = 8
N_TRAIN = 3
N_TEST = 1
FIXTURE_PROFILES = (
    "diagonal_bridge",
    "bbox_decoy",
    "small_bridge",
    "diagonal_bridge",
)
PARAMETERS = {
    "connectivity": {
        "allowed": CONNECTIVITIES,
        "default": DEFAULT_CONNECTIVITY,
        "meaning": "Adjacency used to form cyan components before testing ring contacts.",
        "input_constraint": (
            "Inputs retain exactly two red 2x2 blocks and cyan contacts at both "
            "rings; demonstrations include a diagonal-only cyan bridge."
        ),
    }
}
_CONNECTIVITY_SITE = "(objects-8 cyan-mask 0)"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _json_sha256(value: Any) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(body)


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative plain Python int")
    return seed


def _validate_connectivity(connectivity: int) -> int:
    if type(connectivity) is not int or connectivity not in CONNECTIVITIES:
        raise ValueError(f"connectivity must be exactly one of {CONNECTIVITIES}")
    return connectivity


def choose_parameters(seed: int) -> dict[str, int]:
    """Choose one hidden rule setting exactly once for an episode."""
    _validate_seed(seed)
    return {"connectivity": CONNECTIVITIES[seed % len(CONNECTIVITIES)]}


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
    connectivity: int = DEFAULT_CONNECTIVITY,
    *,
    root: str | Path | None = None,
) -> str:
    """Instantiate exact Racket; the default setting is byte-identical."""
    connectivity = _validate_connectivity(connectivity)
    source = canonical_program(root=root)
    if connectivity == DEFAULT_CONNECTIVITY:
        return source
    if source.count(_CONNECTIVITY_SITE) != 1:
        raise ValueError(
            "canonical connectivity site changed; manually reassess this prototype"
        )
    changed = source.replace(_CONNECTIVITY_SITE, "(objects cyan-mask 0)", 1)
    if changed == source:
        raise ValueError("4-connectivity setting did not change the authority")
    return changed


def _blocks(grid: list[list[int]]) -> list[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return [
        (row, column)
        for row in range(height - 1)
        for column in range(width - 1)
        if all(
            grid[row + dr][column + dc] == 2
            for dr in (0, 1)
            for dc in (0, 1)
        )
    ]


def _touches_ring(
    cell: tuple[int, int], block: tuple[int, int]
) -> bool:
    row, column = cell
    block_row, block_column = block
    return (
        block_row - 1 <= row <= block_row + 2
        and block_column - 1 <= column <= block_column + 2
        and not (
            block_row <= row <= block_row + 1
            and block_column <= column <= block_column + 1
        )
    )


def _components(
    grid: list[list[int]], connectivity: int
) -> list[frozenset[tuple[int, int]]]:
    connectivity = _validate_connectivity(connectivity)
    height, width = len(grid), len(grid[0])
    if connectivity == 8:
        steps = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    else:
        steps = ((-1, 0), (0, -1), (0, 1), (1, 0))

    seen: set[tuple[int, int]] = set()
    result: list[frozenset[tuple[int, int]]] = []
    for row in range(height):
        for column in range(width):
            start = (row, column)
            if grid[row][column] != 8 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: set[tuple[int, int]] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in steps:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == 8
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(frozenset(cells))
    return result


def apply_python(grid: list[list[int]], connectivity: int) -> list[list[int]]:
    """Independent parity oracle for the two bounded connectivity settings."""
    grid = normalize_grid(grid)
    connectivity = _validate_connectivity(connectivity)
    blocks = _blocks(grid)
    if len(blocks) != 2:
        return [[0]]
    bridge = any(
        all(
            any(_touches_ring(cell, block) for cell in component)
            for block in blocks
        )
        for component in _components(grid, connectivity)
    )
    return [[8 if bridge else 0]]


def fixture_inputs(
    seed: int,
    *,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Generate four deterministic inputs independent of connectivity.

    The first demonstration and the query use ``diagonal_bridge``.  Thus the
    demonstrations identify 4 versus 8 connectivity before the query needs the
    distinction, while the middle demonstrations preserve negative and
    orthogonally connected cases from the original family.
    """
    _validate_seed(seed)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)
    grids: list[list[list[int]]] = []
    for index, profile in enumerate(FIXTURE_PROFILES):
        grid = generator.generate(
            700_001 + seed * 97 + index,
            seed * len(FIXTURE_PROFILES) + index,
            difficulty="medium",
            lesson_profile=profile,
        )
        errors = generator.self_check(grid, difficulty="medium")
        if errors:
            raise RuntimeError(f"fixture {index} is invalid: {errors}")
        observed = generator.observe_overrides(grid)
        if observed["lesson_profile"] != profile:
            raise RuntimeError(
                f"fixture {index} requested {profile!r}, observed {observed!r}"
            )
        grids.append(normalize_grid(grid))
    if len({_json_sha256(grid) for grid in grids}) != len(grids):
        raise RuntimeError("connectivity fixture sampler produced duplicate inputs")
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
    connectivity: int,
    grids: list[list[list[int]]],
    outputs: dict[int, list[list[list[int]]]],
    *,
    root: str | Path | None,
    label_authority: str,
) -> dict[str, Any]:
    connectivity = _validate_connectivity(connectivity)
    rival_connectivity = next(
        value for value in CONNECTIVITIES if value != connectivity
    )
    selected = outputs[connectivity]
    rival = outputs[rival_connectivity]
    refuting = [
        index
        for index in range(N_TRAIN)
        if selected[index] != rival[index]
    ]
    query_differs = selected[N_TRAIN] != rival[N_TRAIN]
    if not refuting and query_differs:
        raise RuntimeError(
            "connectivity setting changes the query without a distinguishing demo"
        )
    pairs = [
        {"input": deepcopy(grid), "output": deepcopy(output)}
        for grid, output in zip(grids, selected)
    ]
    program = render_program(connectivity, root=root)
    return {
        "schema": SCHEMA,
        "seed": seed,
        "parameters": {"connectivity": connectivity},
        "parameter_choice": "explicit_once_per_episode",
        "parameter_draw_count": 1,
        "program": program,
        "program_sha256": _sha256_text(program),
        "train": pairs[:N_TRAIN],
        "test": pairs[N_TRAIN:],
        "rival": {
            "parameters": {"connectivity": rival_connectivity},
            "program_sha256": _sha256_text(
                render_program(rival_connectivity, root=root)
            ),
            "status": "distinguished" if refuting else "indistinguishable",
            "refuting_demonstration_indices": refuting,
            "query_differs": query_differs,
            "outputs": {
                "train": deepcopy(rival[:N_TRAIN]),
                "test": deepcopy(rival[N_TRAIN:]),
            },
        },
        "label_authority": label_authority,
    }


def generate_episode_python(
    seed: int,
    *,
    connectivity: int | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a fast parity-oracle episode; retained labels use Racket."""
    _validate_seed(seed)
    chosen = (
        choose_parameters(seed)["connectivity"]
        if connectivity is None
        else _validate_connectivity(connectivity)
    )
    grids = fixture_inputs(seed, root=root)
    outputs = {
        setting: [apply_python(grid, setting) for grid in grids]
        for setting in CONNECTIVITIES
    }
    return _episode_from_outputs(
        seed,
        chosen,
        grids,
        outputs,
        root=root,
        label_authority="independent Python parity oracle (not retained evidence)",
    )


def generate_episode(
    seed: int,
    *,
    connectivity: int | None = None,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Choose one setting and label the complete episode in real Racket."""
    _validate_seed(seed)
    chosen = (
        choose_parameters(seed)["connectivity"]
        if connectivity is None
        else _validate_connectivity(connectivity)
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    grids = fixture_inputs(seed, root=root_path)

    def build(active: RacketBridge) -> dict[str, Any]:
        outputs: dict[int, list[list[list[int]]]] = {}
        for setting in CONNECTIVITIES:
            program = render_program(setting, root=root_path)
            racket_outputs = [
                execute_racket(active, program, grid) for grid in grids
            ]
            python_outputs = [apply_python(grid, setting) for grid in grids]
            if racket_outputs != python_outputs:
                raise RuntimeError(
                    f"Racket/Python parity failure for connectivity={setting}"
                )
            outputs[setting] = racket_outputs
        return _episode_from_outputs(
            seed,
            chosen,
            grids,
            outputs,
            root=root_path,
            label_authority=(
                "protected included Racket bridge executing the exact "
                "instantiated program"
            ),
        )

    with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
        return build(active)


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove hidden settings, reference code, rival labels, and query output."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): {
            "sha256": _sha256_bytes(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "report.json"
    }


def materialize(
    output: str | Path,
    *,
    base_seed: int = 20261020,
) -> dict[str, Any]:
    """Materialize two complete, Racket-labeled connectivity episodes."""
    _validate_seed(base_seed)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    generator, generator_path, generator_sha = load_selected_generator(
        TASK_ID, root=root
    )
    del generator

    source_paths = [
        Path(__file__),
        Path(__file__).parent / "README.md",
        Path(__file__).parents[2] / "tests" / "test_parametric_connectivity.py",
    ]
    source_hashes = {
        str(path.relative_to(root)): _sha256_bytes(path.read_bytes())
        for path in source_paths
        if path.is_file()
    }
    canonical = canonical_program(root=root)
    default = render_program(DEFAULT_CONNECTIVITY, root=root)
    report: dict[str, Any] = {
        "schema": f"{SCHEMA}-report",
        "status": "incomplete",
        "scope": (
            "Proposed task-local extension only; not a canonical rule change, "
            "production axis, approval refresh, or training-admission claim."
        ),
        "parameter_spec": PARAMETERS,
        "choice_policy": (
            "One connectivity value is bound for the entire episode. "
            "Seed choice alternates (8,4); retained evidence explicitly covers both."
        ),
        "invariant_reasoning": (
            "Find the two red 2x2 blocks, form cyan components, and ask whether "
            "one component touches both one-cell block rings. Only component "
            "adjacency changes."
        ),
        "input_policy": {
            "profiles": list(FIXTURE_PROFILES),
            "train_count": N_TRAIN,
            "test_count": N_TEST,
            "parameter_independent": True,
            "distinguishing_demo": "diagonal_bridge at demonstration index 0",
        },
        "limitations": (
            "Only connectivity 8 and 4 are studied. Evidence covers one fixed "
            "four-input episode per setting and the eight canonical labels; it "
            "does not prove identifiability against undeclared rule families."
        ),
        "default_program_exact_canonical": default == canonical,
        "source_hashes": {
            **source_hashes,
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
            for setting in CONNECTIVITIES:
                rule_path = (
                    output
                    / "private"
                    / "rules"
                    / f"connectivity-{setting}.rkt"
                )
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(
                    render_program(setting, root=root), encoding="utf-8"
                )

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_racket(bridge, default, pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "expected": pair["output"],
                        "actual": actual,
                        "passed": actual == pair["output"],
                    }
                )

            # Use one parameter-independent input set for both explicit settings,
            # so the cross-setting execution difference is directly auditable.
            grids = fixture_inputs(base_seed, root=root)
            outputs: dict[int, list[list[list[int]]]] = {}
            for setting in CONNECTIVITIES:
                program = render_program(setting, root=root)
                outputs[setting] = [
                    execute_racket(bridge, program, grid) for grid in grids
                ]
                expected = [apply_python(grid, setting) for grid in grids]
                if outputs[setting] != expected:
                    raise RuntimeError(
                        f"Racket/Python parity failure for connectivity={setting}"
                    )

            for index, setting in enumerate(CONNECTIVITIES, start=1):
                episode = _episode_from_outputs(
                    base_seed,
                    setting,
                    grids,
                    outputs,
                    root=root,
                    label_authority=(
                        "protected included Racket bridge executing exact "
                        "instantiated programs for selected and rival settings"
                    ),
                )
                private_path = (
                    output / "private" / "episodes" / f"episode-{index:03d}.json"
                )
                public_path = output / "public" / f"episode-{index:03d}.json"
                _write_json(private_path, episode)
                _write_json(public_path, public_challenge(episode))
                report["episodes"].append(
                    {
                        "seed": base_seed,
                        "parameters": episode["parameters"],
                        "program_sha256": episode["program_sha256"],
                        "private_path": private_path.relative_to(output).as_posix(),
                        "public_path": public_path.relative_to(output).as_posix(),
                        "rival": episode["rival"],
                    }
                )

            witness = {
                "input": grids[N_TRAIN],
                "input_sha256": _json_sha256(grids[N_TRAIN]),
                "profile": FIXTURE_PROFILES[N_TRAIN],
                "outputs": {
                    str(setting): outputs[setting][N_TRAIN]
                    for setting in CONNECTIVITIES
                },
                "query_outputs_differ": (
                    outputs[CONNECTIVITIES[0]][N_TRAIN]
                    != outputs[CONNECTIVITIES[1]][N_TRAIN]
                ),
            }
            _write_json(
                output / "private" / "cross-setting-witness.json", witness
            )
            report["cross_setting_witness"] = witness

        canonical_passed = sum(
            check["passed"] for check in report["canonical_checks"]
        )
        demos_distinguish = all(
            episode["rival"]["refuting_demonstration_indices"]
            for episode in report["episodes"]
        )
        report.update(
            {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "complete_episodes": len(report["episodes"]),
                "all_labels_and_rivals_executed_in_racket": True,
                "all_episode_demonstrations_distinguish_rival": demos_distinguish,
            }
        )
        report["status"] = (
            "prototype"
            if report["default_program_exact_canonical"]
            and canonical_passed == len(report["canonical_checks"])
            and len(report["episodes"]) == len(CONNECTIVITIES)
            and demos_distinguish
            and report["cross_setting_witness"]["query_outputs_differ"]
            else "failed"
        )
        report["files"] = _inventory(output)
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        _write_json(output / "report.json", report)
        raise

    _write_json(output / "report.json", report)
    return report



# ---------------------------------------------------------------------------
# Native promotion adapter implementation.
# ---------------------------------------------------------------------------

SETTINGS = ({"connectivity": 8}, {"connectivity": 4})
DEMO_PROFILES = (
    "diagonal_bridge",
    "small_bridge",
    "bbox_decoy",
    "split_contacts",
    "small_bridge",
    "diagonal_bridge",
)
DEMO_SHAPES = ((9, 9), (10, 12), (12, 10), (13, 14), (15, 12), (16, 16))
QUERY_PROFILES = (
    "diagonal_bridge",
    "small_bridge",
    "diagonal_bridge",
    "diagonal_bridge",
)
QUERY_SHAPES = ((12, 15), (18, 20), (24, 27), (30, 30))

_CORE_RED = {
    (0, 0), (0, 1), (1, 0), (1, 1),
    (3, 3), (3, 4), (4, 3), (4, 4),
}
_CORE_CYAN = {
    "diagonal_bridge": {(2, 1), (3, 2)},
    "bbox_decoy": {(2, 0), (2, 1), (1, 2), (0, 2), (4, 2)},
    "small_bridge": {(2, 1), (2, 2), (3, 2), (0, 2), (0, 3), (0, 4), (1, 4)},
    "split_contacts": {(0, 2), (0, 3), (4, 2)},
}
_PROFILE_EXPECTED = {
    "diagonal_bridge": {8: [[8]], 4: [[0]]},
    "small_bridge": {8: [[8]], 4: [[8]]},
    "bbox_decoy": {8: [[0]], 4: [[0]]},
    "split_contacts": {8: [[0]], 4: [[0]]},
}
_NATIVE_CANONICAL_PATH = Path(__file__).resolve().with_name("canonical.rkt")


def _native_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain Python int in [{low}, {high}]")
    return value


def _native_settings(settings: Any) -> dict[str, int]:
    if type(settings) is not dict or set(settings) != {"connectivity"}:
        raise ValueError("settings must contain exactly connectivity")
    value = settings["connectivity"]
    if type(value) is not int or value not in CONNECTIVITIES:
        raise ValueError(f"connectivity must be exactly one of {CONNECTIVITIES}")
    return {"connectivity": value}


def _native_canonical() -> str:
    if not _NATIVE_CANONICAL_PATH.is_file():
        raise FileNotFoundError(_NATIVE_CANONICAL_PATH)
    return _NATIVE_CANONICAL_PATH.read_text(encoding="utf-8")


def program(settings: Any) -> str:
    """Return complete exact Racket for one native connectivity setting."""
    connectivity = _native_settings(settings)["connectivity"]
    source = _native_canonical()
    if connectivity == 8:
        return source
    if source.count(_CONNECTIVITY_SITE) != 1:
        raise ValueError("canonical connectivity site changed")
    alternate = source.replace(_CONNECTIVITY_SITE, "(objects cyan-mask 0)", 1)
    if alternate == source:
        raise ValueError("alternate connectivity did not change the program")
    return alternate


def _native_rng(seed: int, role: str, index: int) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}|native-connectivity-v2|{seed}|{role}|{index}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _transform_point(row: int, column: int, transform: int) -> tuple[int, int]:
    if transform >= 4:
        column = 4 - column
    for _ in range(transform % 4):
        row, column = column, 4 - row
    return row, column


def _core_grid(profile: str, transform: int) -> list[list[int]]:
    if profile not in _CORE_CYAN:
        raise ValueError(f"unknown profile: {profile}")
    grid = [[0 for _ in range(5)] for _ in range(5)]
    for row, column in _CORE_RED:
        rr, cc = _transform_point(row, column, transform)
        grid[rr][cc] = 2
    for row, column in _CORE_CYAN[profile]:
        rr, cc = _transform_point(row, column, transform)
        if grid[rr][cc] != 0:
            raise RuntimeError("transformed cyan overlaps red")
        grid[rr][cc] = 8
    return grid


def _core_offset(
    height: int,
    width: int,
    role: str,
    index: int,
    rng: random.Random,
) -> tuple[int, int]:
    min_row = min_column = 2
    max_row, max_column = height - 7, width - 7
    if max_row < min_row or max_column < min_column:
        raise ValueError("native scenes need at least 9x9 canvases")
    if role == "query":
        anchors = (
            (min_row, min_column),
            (min_row, max_column),
            (max_row, min_column),
            ((min_row + max_row) // 2, (min_column + max_column) // 2),
        )
        return anchors[index]
    return rng.randint(min_row, max_row), rng.randint(min_column, max_column)


def _paint_distractors(
    grid: list[list[int]],
    core_row: int,
    core_column: int,
    rng: random.Random,
) -> None:
    """Add a moat-separated large cyan distractor field.

    The one-cell expanded core rectangle contains both red rings and every core
    cyan cell. Leaving it empty prevents distractors from touching a block ring
    or joining the teaching component under either 4- or 8-connectivity.
    """
    height, width = len(grid), len(grid[0])
    forbidden = {
        (row, column)
        for row in range(max(0, core_row - 1), min(height, core_row + 6))
        for column in range(max(0, core_column - 1), min(width, core_column + 6))
    }
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    core_center = (core_row + 2, core_column + 2)
    singleton = max(
        (cell for cell in corners if cell not in forbidden),
        key=lambda cell: abs(cell[0] - core_center[0]) + abs(cell[1] - core_center[1]),
    )
    singleton_halo = {
        (row, column)
        for row in range(max(0, singleton[0] - 1), min(height, singleton[0] + 2))
        for column in range(max(0, singleton[1] - 1), min(width, singleton[1] + 2))
    }

    def paint(row: int, column: int) -> None:
        if (
            (row, column) not in forbidden
            and (row, column) not in singleton_halo
            and grid[row][column] == 0
        ):
            grid[row][column] = 8

    # A moat-separated outer frame is one true 4-connected component whose
    # bounding box spans both red rings.  It therefore gives the visible
    # negative examples a constructive witness against the wrong rule
    # "bridge if a component's bounding box touches both rings".  The reserved
    # singleton halo may remove one corner of the frame; the remaining U-shaped
    # path stays connected and still reaches all four canvas extremes.
    for column in range(width):
        paint(0, column)
        paint(height - 1, column)
    for row in range(1, height - 1):
        paint(row, 0)
        paint(row, width - 1)

    # A deterministic inner zig-zag adds density without crossing the moat.
    for column in range(1, width - 1, 2):
        paint(1, column)
    for row in range(2, height - 2, 2):
        paint(row, width - 2)

    target_cyan = max(18, (height * width) // 9)
    attempts = 0
    while sum(cell == 8 for row in grid for cell in row) < target_cyan:
        attempts += 1
        if attempts > height * width * 20:
            raise RuntimeError("could not place substantive distractor field")
        row = rng.randrange(height)
        column = rng.randrange(width)
        paint(row, column)
        # Grow short local runs so the texture is not merely isolated noise.
        if rng.random() < 0.65:
            dr, dc = rng.choice(((0, 1), (1, 0), (1, 1), (1, -1)))
            neighbor_row, neighbor_column = row + dr, column + dc
            if 0 <= neighbor_row < height and 0 <= neighbor_column < width:
                paint(neighbor_row, neighbor_column)

    # Materialize the reserved singleton after all other noise is painted.
    # Its protected Chebyshev halo makes it a genuine one-cell component.
    if grid[singleton[0]][singleton[1]] != 0:
        raise RuntimeError("reserved singleton cell was overwritten")
    grid[singleton[0]][singleton[1]] = 8


def _native_scene(
    seed: int,
    role: str,
    index: int,
    profile: str,
    shape: tuple[int, int],
) -> list[list[int]]:
    rng = _native_rng(seed, role, index)
    height, width = shape
    grid = [[0 for _ in range(width)] for _ in range(height)]
    transform = rng.randrange(8)
    core = _core_grid(profile, transform)
    core_row, core_column = _core_offset(height, width, role, index, rng)
    for row in range(5):
        for column in range(5):
            value = core[row][column]
            if value:
                grid[core_row + row][core_column + column] = value
    _paint_distractors(grid, core_row, core_column, rng)

    if len(_blocks(grid)) != 2:
        raise RuntimeError("native scene must contain exactly two red 2x2 blocks")
    for connectivity in CONNECTIVITIES:
        observed = apply_python(grid, connectivity)
        expected = _PROFILE_EXPECTED[profile][connectivity]
        if observed != expected:
            raise RuntimeError(
                f"profile {profile} changed under connectivity={connectivity}: "
                f"expected {expected}, observed {observed}"
            )
    return grid


def solve(grid: list[list[int]], settings: Any) -> list[list[int]]:
    connectivity = _native_settings(settings)["connectivity"]
    return apply_python(grid, connectivity)


def generate(
    seed: Any,
    settings: Any,
    demos: Any = 3,
    queries: Any = 4,
) -> dict[str, Any]:
    """Generate a prefix-stable native episode without executing nested Racket."""
    seed = _native_int("seed", seed, 0, 2**63 - 1)
    settings = _native_settings(settings)
    demos = _native_int("demos", demos, 2, 6)
    queries = _native_int("queries", queries, 1, 4)

    train_inputs = [
        _native_scene(seed, "demo", index, DEMO_PROFILES[index], DEMO_SHAPES[index])
        for index in range(demos)
    ]
    test_inputs = [
        _native_scene(seed, "query", index, QUERY_PROFILES[index], QUERY_SHAPES[index])
        for index in range(queries)
    ]
    all_inputs = train_inputs + test_inputs
    serialized = {json.dumps(grid, separators=(",", ":")) for grid in all_inputs}
    if len(serialized) != len(all_inputs):
        raise RuntimeError("native episode produced duplicate inputs")

    def pair(grid: list[list[int]]) -> dict[str, Any]:
        return {"input": deepcopy(grid), "output": solve(grid, settings)}

    return {
        "train": [pair(grid) for grid in train_inputs],
        "test": [pair(grid) for grid in test_inputs],
        "program_solution": program(settings),
    }


def fit_settings(demonstrations: list[dict[str, Any]]) -> list[dict[str, int]]:
    survivors = []
    for setting in SETTINGS:
        if all(
            solve(pair["input"], setting) == normalize_grid(pair["output"])
            for pair in demonstrations
        ):
            survivors.append(dict(setting))
    return survivors


def _any_ring_contacts(grid: list[list[int]]) -> list[list[int]]:
    blocks = _blocks(grid)
    cyan = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == 8
    ]
    bridge = len(blocks) == 2 and all(
        any(_touches_ring(cell, block) for cell in cyan) for block in blocks
    )
    return [[8 if bridge else 0]]


def _bbox_bridge(grid: list[list[int]], connectivity: int = 8) -> list[list[int]]:
    blocks = _blocks(grid)
    if len(blocks) != 2:
        return [[0]]
    for component in _components(grid, connectivity):
        rows = [row for row, _ in component]
        columns = [column for _, column in component]
        bbox = [
            (row, column)
            for row in range(min(rows), max(rows) + 1)
            for column in range(min(columns), max(columns) + 1)
        ]
        if all(any(_touches_ring(cell, block) for cell in bbox) for block in blocks):
            return [[8]]
    return [[0]]


def _extreme_component_bridge(
    grid: list[list[int]], connectivity: int, *, largest: bool
) -> list[list[int]]:
    blocks = _blocks(grid)
    components = _components(grid, connectivity)
    if len(blocks) != 2 or not components:
        return [[0]]
    size = (max if largest else min)(len(component) for component in components)
    bridge = any(
        len(component) == size
        and all(
            any(_touches_ring(cell, block) for cell in component)
            for block in blocks
        )
        for component in components
    )
    return [[8 if bridge else 0]]


def candidate_rules() -> dict[str, Any]:
    return {
        "connectivity_8": lambda grid: apply_python(grid, 8),
        "connectivity_4": lambda grid: apply_python(grid, 4),
        "any_ring_contacts": _any_ring_contacts,
        "bbox_bridge_8": lambda grid: _bbox_bridge(grid, 8),
        "bbox_bridge_4": lambda grid: _bbox_bridge(grid, 4),
        "largest_component_8": lambda grid: _extreme_component_bridge(grid, 8, largest=True),
        "largest_component_4": lambda grid: _extreme_component_bridge(grid, 4, largest=True),
        "smallest_component_8": lambda grid: _extreme_component_bridge(grid, 8, largest=False),
        "always_0": lambda grid: [[0]],
        "always_8": lambda grid: [[8]],
    }


def self_review(episode: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(episode, dict):
        raise ValueError("episode must be an object")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list) or not train or not test:
        raise ValueError("episode needs nonempty train/test lists")
    selected = None
    for setting in SETTINGS:
        if program(setting) == episode.get("program_solution"):
            selected = dict(setting)
            break
    if selected is None:
        raise ValueError("episode program does not match a declared setting")

    survivors = []
    harmful = []
    query_mismatches = {}
    for name, rule in candidate_rules().items():
        if all(rule(pair["input"]) == pair["output"] for pair in train):
            survivors.append(name)
            mismatches = [
                index
                for index, pair in enumerate(test)
                if rule(pair["input"]) != pair["output"]
            ]
            query_mismatches[name] = mismatches
            if mismatches:
                harmful.append(name)
    intended = [
        name for name in survivors if name == f"connectivity_{selected['connectivity']}"
    ]
    return {
        "schema": "eefadafb2b7b-native-self-review-v1",
        "selected": selected,
        "tested_candidates": sorted(candidate_rules()),
        "survivors": survivors,
        "intended_survivors": intended,
        "harmful_survivors": harmful,
        "query_mismatch_indices": query_mismatches,
        "limits": "Finite declared candidates only; not a uniqueness proof.",
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-seed", type=int, default=20261020)
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
