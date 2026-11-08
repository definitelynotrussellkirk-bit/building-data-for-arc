#!/usr/bin/env python3
"""Proposed, unapproved rule variants for ARC task 44690b1b635f.

The approved production generator and its canonical Racket authority stay
unchanged.  This task-local prototype varies only two bounded rule choices:
4- versus 8-neighbor traversal, and which marker color occupies even BFS
levels.  The canonical/default setting is returned byte-for-byte.
"""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "44690b1b635f"
VERSION = "proposed-maze-connectivity-phase-v1"
STATUS = "proposed_unapproved"
CANONICAL_SOURCE_SHA256 = (
    "d78c0152b4b3f003a6ceaf2601ffb3234247354b626267c771a1bcf51d25e618"
)
CANONICAL_RULE_HASH = "72a0e00e932b"
CONNECTIVITIES = ("cardinal", "king")
PHASES = ("center_even", "arm_even")
DEFAULT_SETTINGS = {"connectivity": "cardinal", "phase": "center_even"}
SETTING_COMBINATIONS = tuple(
    {"connectivity": connectivity, "phase": phase}
    for connectivity in CONNECTIVITIES
    for phase in PHASES
)
CARDINAL_TOKEN = "cardinal-deltas"
KING_TOKEN = "all-8-deltas"
CANONICAL_PHASE_BRANCH = (
    "(if (zero? (modulo (third e) 2)) center-color arm-color)"
)
REVERSED_PHASE_BRANCH = (
    "(if (zero? (modulo (third e) 2)) arm-color center-color)"
)
CARDINAL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
KING_DELTAS = CARDINAL_DELTAS + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _sha256(payload: str | bytes) -> str:
    data = payload.encode("utf-8") if isinstance(payload, str) else payload
    return hashlib.sha256(data).hexdigest()


def _strict_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must be a literal list with 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid rows must be literal lists with 1..30 cells")
    width = len(grid[0])
    rows: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular with literal list rows")
        checked: list[int] = []
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("grid cells must be literal integer ARC colors 0..9")
            checked.append(cell)
        rows.append(checked)
    return rows


def grid_sha256(grid: Any) -> str:
    checked = _strict_grid(grid)
    payload = json.dumps(
        checked, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_settings(settings: Any = None) -> dict[str, str]:
    if settings is None:
        return dict(DEFAULT_SETTINGS)
    if type(settings) is not dict:
        raise ValueError("settings must be a literal dict")
    if set(settings) != {"connectivity", "phase"}:
        raise ValueError("settings must contain exactly connectivity and phase")
    connectivity = settings["connectivity"]
    phase = settings["phase"]
    if type(connectivity) is not str or connectivity not in CONNECTIVITIES:
        raise ValueError(
            "connectivity must be one of: " + ", ".join(CONNECTIVITIES)
        )
    if type(phase) is not str or phase not in PHASES:
        raise ValueError("phase must be one of: " + ", ".join(PHASES))
    return {"connectivity": connectivity, "phase": phase}


def _check_canonical_source(source: Any) -> str:
    if type(source) is not str:
        raise ValueError("canonical source must be Racket text")
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("pinned canonical Racket source SHA-256 does not match")
    if source.count(CARDINAL_TOKEN) != 1:
        raise ValueError("canonical source must contain one cardinal-deltas token")
    if KING_TOKEN in source:
        raise ValueError("canonical source unexpectedly contains all-8-deltas")
    if source.count(CANONICAL_PHASE_BRANCH) != 1:
        raise ValueError("canonical source must contain one parity-color branch")
    if REVERSED_PHASE_BRANCH in source:
        raise ValueError("canonical source unexpectedly contains reversed phase")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Load and hash-check the unique canonical Racket source for this task."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    settings: Any = None,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact Racket text for one of the four bounded settings."""
    selected = normalize_settings(settings)
    result = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selected["connectivity"] == "king":
        result = result.replace(CARDINAL_TOKEN, KING_TOKEN, 1)
    if selected["phase"] == "arm_even":
        result = result.replace(
            CANONICAL_PHASE_BRANCH, REVERSED_PHASE_BRANCH, 1
        )
    return result


def recognize_rule(
    source: Any, *, root: str | Path | None = None
) -> dict[str, str]:
    """Recognize only the pinned canonical source or its three guarded variants."""
    if type(source) is not str:
        raise ValueError("variant source must be Racket text")
    matches = [
        settings
        for settings in SETTING_COMBINATIONS
        if source == materialize_rule(settings, root=root)
    ]
    if len(matches) != 1:
        raise ValueError("source is not one recognized connectivity/phase rule")
    return dict(matches[0])


def _rule_callable(source: str, *, root: str | Path | None = None) -> str:
    recognize_rule(source, root=root)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix) : -1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def _grid_literal(grid: Any) -> str:
    checked = _strict_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in checked
    ) + ")"


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Execute one exact recognized Racket rule over all supplied grids."""
    checked = [_strict_grid(grid) for grid in grids]
    if not checked:
        return []
    literals = [_grid_literal(grid) for grid in checked]
    expression = (
        f"(map {_rule_callable(source, root=root)} "
        f"'({' '.join(literals)}))"
    )
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            raw = owned.eval_text(expression)
    else:
        raw = bridge.eval_text(expression)
    return [_strict_grid(grid) for grid in raw]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> list[list[int]]:
    return execute_rule_many(
        source, [grid], bridge=bridge, root=root
    )[0]


def _marker_analysis(grid: Any) -> tuple[list[list[int]], int, int, tuple[int, int]]:
    checked = _strict_grid(grid)
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(checked):
        for col_index, value in enumerate(row):
            if value not in (0, 8):
                positions.setdefault(value, []).append((row_index, col_index))
    if len(positions) != 2:
        raise ValueError("input must contain exactly two non-wall marker colors")
    singleton = [color for color, cells in positions.items() if len(cells) == 1]
    if len(singleton) != 1:
        raise ValueError("exactly one marker color must occur once")
    center_color = singleton[0]
    arm_color = next(color for color in positions if color != center_color)
    if len(positions[arm_color]) < 2:
        raise ValueError("arm marker color must occur at least twice")
    return checked, center_color, arm_color, positions[center_color][0]


def independent_output(grid: Any, settings: Any = None) -> list[list[int]]:
    """Independent Python BFS oracle for one declared rule setting."""
    selected = normalize_settings(settings)
    checked, center_color, arm_color, start = _marker_analysis(grid)
    height, width = len(checked), len(checked[0])
    deltas = (
        CARDINAL_DELTAS
        if selected["connectivity"] == "cardinal"
        else KING_DELTAS
    )
    distances = {start: 0}
    frontier = deque([start])
    while frontier:
        row, col = frontier.popleft()
        for dr, dc in deltas:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and checked[nr][nc] != 8
                and (nr, nc) not in distances
            ):
                distances[(nr, nc)] = distances[(row, col)] + 1
                frontier.append((nr, nc))

    output = [row[:] for row in checked]
    center_on_even = selected["phase"] == "center_even"
    for (row, col), distance in distances.items():
        if checked[row][col] != 0:
            continue
        even_color = center_color if center_on_even else arm_color
        odd_color = arm_color if center_on_even else center_color
        output[row][col] = even_color if distance % 2 == 0 else odd_color
    return output


MIN_COUNT = 1
MAX_COUNT = 8
DEFAULT_MAX_ATTEMPTS = 64


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or not MIN_COUNT <= value <= MAX_COUNT:
        raise ValueError(
            f"{name} must be a literal integer in {MIN_COUNT}..{MAX_COUNT}"
        )
    return value


def _validate_attempts(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 1024:
        raise ValueError("max_attempts must be a literal integer in 1..1024")
    return value


def parameter_for_seed(seed: Any) -> dict[str, str]:
    """Choose exactly one hidden setting once from a deterministic seed."""
    checked = _validate_seed(seed)
    return dict(SETTING_COMBINATIONS[checked % len(SETTING_COMBINATIONS)])


def _distance_map(
    grid: Any, connectivity: str
) -> tuple[list[list[int]], dict[tuple[int, int], int]]:
    selected = normalize_settings(
        {"connectivity": connectivity, "phase": "center_even"}
    )
    checked, _, _, start = _marker_analysis(grid)
    height, width = len(checked), len(checked[0])
    deltas = (
        CARDINAL_DELTAS
        if selected["connectivity"] == "cardinal"
        else KING_DELTAS
    )
    distances = {start: 0}
    frontier = deque([start])
    while frontier:
        row, col = frontier.popleft()
        for dr, dc in deltas:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and checked[nr][nc] != 8
                and (nr, nc) not in distances
            ):
                distances[(nr, nc)] = distances[(row, col)] + 1
                frontier.append((nr, nc))
    return checked, distances


def _wall_mask_sha256(grid: Any) -> str:
    checked = _strict_grid(grid)
    mask = [[8 if cell == 8 else 0 for cell in row] for row in checked]
    return grid_sha256(mask)


def input_certificate(grid: Any) -> dict[str, Any]:
    """Return bounded semantic witnesses for one admitted prototype input."""
    checked, cardinal = _distance_map(grid, "cardinal")
    _, king = _distance_map(grid, "king")
    zeros = {
        (row, col)
        for row in range(len(checked))
        for col in range(len(checked[0]))
        if checked[row][col] == 0
    }
    cardinal_reachable = zeros.intersection(cardinal)
    king_reachable = zeros.intersection(king)
    king_only = king_reachable - cardinal_reachable
    unreachable_king = zeros - king_reachable
    output_hashes = {
        grid_sha256(independent_output(checked, settings))
        for settings in SETTING_COMBINATIONS
    }
    return {
        "height": len(checked),
        "width": len(checked[0]),
        "wall_count": sum(cell == 8 for row in checked for cell in row),
        "wall_mask_sha256": _wall_mask_sha256(checked),
        "cardinal_reachable_zero_count": len(cardinal_reachable),
        "king_reachable_zero_count": len(king_reachable),
        "king_only_reachable_zero_count": len(king_only),
        "unreachable_zero_count_king": len(unreachable_king),
        "four_setting_outputs_pairwise_distinct": len(output_hashes) == 4,
        "setting_output_sha256": sorted(output_hashes),
    }


def _rng_for_input(seed: int, slot: int, attempt: int) -> random.Random:
    digest = hashlib.sha256(
        f"{VERSION}:input:{seed}:{slot}:{attempt}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dihedral(grid: list[list[int]], code: int) -> list[list[int]]:
    result = [row[:] for row in grid]
    if code >= 4:
        result = [list(reversed(row)) for row in result]
    for _ in range(code % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _chebyshev_distance(
    left: tuple[int, int], right: tuple[int, int]
) -> int:
    return max(abs(left[0] - right[0]), abs(left[1] - right[1]))


def _draw_procedural_input(seed: int, slot: int, attempt: int) -> list[list[int]]:
    """Construct three components: cardinal, diagonal-only, and unreachable."""
    rng = _rng_for_input(seed, slot, attempt)
    # Slot-controlled dimensions guarantee shape variation within a normal
    # episode while the RNG controls geometry, palette, and orientation.
    height = 11 + ((slot + attempt) % 5)
    width = 12 + ((seed + 2 * slot + attempt) % 5)
    grid = [[8 for _ in range(width)] for _ in range(height)]

    center_row = rng.randint(4, height - 5)
    center_col = rng.randint(4, width - 5)
    west_length = rng.randint(3, min(5, center_col - 1))
    north_length = rng.randint(2, min(4, center_row - 1))
    south_length = rng.randint(1, min(3, height - center_row - 2))
    branch_col = center_col - rng.randint(2, west_length)

    main_component: set[tuple[int, int]] = {
        (center_row, col)
        for col in range(center_col - west_length, center_col + 1)
    }
    main_component.update(
        (row, center_col - west_length)
        for row in range(center_row - north_length, center_row + 1)
    )
    main_component.update(
        (row, branch_col)
        for row in range(center_row, center_row + south_length + 1)
    )

    diagonal_start = (center_row + 1, center_col + 1)
    diagonal_bottom = min(height - 2, center_row + rng.randint(3, 5))
    diagonal_right = min(width - 2, center_col + rng.randint(3, 5))
    allowed_diagonal = {
        (row, col)
        for row in range(center_row + 1, diagonal_bottom + 1)
        for col in range(center_col + 1, diagonal_right + 1)
    }
    target_size = rng.randint(7, min(15, len(allowed_diagonal)))
    diagonal_component = {diagonal_start}
    frontier = {
        (diagonal_start[0] + dr, diagonal_start[1] + dc)
        for dr, dc in CARDINAL_DELTAS
        if (diagonal_start[0] + dr, diagonal_start[1] + dc)
        in allowed_diagonal
    }
    while len(diagonal_component) < target_size and frontier:
        chosen = rng.choice(sorted(frontier))
        frontier.remove(chosen)
        diagonal_component.add(chosen)
        for dr, dc in CARDINAL_DELTAS:
            neighbor = (chosen[0] + dr, chosen[1] + dc)
            if neighbor in allowed_diagonal and neighbor not in diagonal_component:
                frontier.add(neighbor)

    active = main_component | diagonal_component
    corner_blocks = []
    for top, left in (
        (1, 1),
        (1, width - 3),
        (height - 3, 1),
        (height - 3, width - 3),
    ):
        block = {
            (top, left),
            (top, left + 1),
            (top + 1, left),
            (top + 1, left + 1),
        }
        separation = min(
            _chebyshev_distance(cell, other)
            for cell in block
            for other in active
        )
        corner_blocks.append((separation, sorted(block), block))
    _, _, unreachable_pocket = max(corner_blocks)

    for row, col in active | unreachable_pocket:
        grid[row][col] = 0

    center = (center_row, center_col)
    main_arms = [
        (center_row - north_length, center_col - west_length),
        (center_row + south_length, branch_col),
    ]
    diagonal_arm = max(
        diagonal_component,
        key=lambda cell: (
            abs(cell[0] - center_row) + abs(cell[1] - center_col),
            cell,
        ),
    )
    legal_colors = [color for color in range(1, 10) if color != 8]
    center_color, arm_color = rng.sample(legal_colors, 2)
    grid[center[0]][center[1]] = center_color
    for row, col in main_arms + [diagonal_arm]:
        if (row, col) == center:
            raise RuntimeError("procedural arm overlaps center")
        grid[row][col] = arm_color

    return _dihedral(grid, rng.randrange(8))


def episode_inputs(
    seed: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    root: str | Path | None = None,
) -> list[list[list[int]]]:
    """Draw distinct topology-rich inputs independently of hidden settings."""
    del root  # Inputs are procedural and do not depend on repository state.
    checked_seed = _validate_seed(seed)
    demo_count = _validate_count("demos", demos)
    query_count = _validate_count("queries", queries)
    attempt_limit = _validate_attempts(max_attempts)
    total = demo_count + query_count
    grids: list[list[list[int]]] = []
    seen_inputs: set[str] = set()
    seen_walls: set[str] = set()
    for slot in range(total):
        for attempt in range(attempt_limit):
            grid = _draw_procedural_input(checked_seed, slot, attempt)
            certificate = input_certificate(grid)
            fingerprint = grid_sha256(grid)
            wall_fingerprint = certificate["wall_mask_sha256"]
            accepted = (
                certificate["cardinal_reachable_zero_count"] >= 3
                and certificate["king_only_reachable_zero_count"] >= 3
                and certificate["unreachable_zero_count_king"] >= 3
                and certificate["four_setting_outputs_pairwise_distinct"]
                and fingerprint not in seen_inputs
                and wall_fingerprint not in seen_walls
            )
            if accepted:
                grids.append(grid)
                seen_inputs.add(fingerprint)
                seen_walls.add(wall_fingerprint)
                break
        else:
            raise RuntimeError(
                f"could not construct distinct admitted input for slot {slot} "
                f"after {attempt_limit} attempts"
            )
    return grids


def _setting_key(settings: Any) -> str:
    selected = normalize_settings(settings)
    return f"{selected['connectivity']}:{selected['phase']}"


def _generate_episode_with_bridge(
    seed: int,
    selected: dict[str, str],
    demos: int,
    queries: int,
    max_attempts: int,
    bridge: RacketBridge,
    root: Path,
) -> dict[str, Any]:
    grids = episode_inputs(
        seed,
        demos=demos,
        queries=queries,
        max_attempts=max_attempts,
        root=root,
    )
    programs = {
        _setting_key(settings): materialize_rule(settings, root=root)
        for settings in SETTING_COMBINATIONS
    }
    predictions: dict[str, list[list[list[int]]]] = {}
    for settings in SETTING_COMBINATIONS:
        key = _setting_key(settings)
        outputs = execute_rule_many(
            programs[key], grids, bridge=bridge, root=root
        )
        expected = [independent_output(grid, settings) for grid in grids]
        if outputs != expected:
            raise ValueError(f"Racket/Python disagreement for {key}")
        predictions[key] = outputs

    selected_key = _setting_key(selected)
    selected_outputs = predictions[selected_key]
    train = [
        {
            "input": copy.deepcopy(grids[index]),
            "output": copy.deepcopy(selected_outputs[index]),
        }
        for index in range(demos)
    ]
    test = [
        {
            "input": copy.deepcopy(grids[demos + index]),
            "output": copy.deepcopy(selected_outputs[demos + index]),
        }
        for index in range(queries)
    ]

    survivor_keys = []
    rival_checks = []
    for settings in SETTING_COMBINATIONS:
        key = _setting_key(settings)
        disagreements = [
            index
            for index in range(demos)
            if predictions[key][index] != selected_outputs[index]
        ]
        if not disagreements:
            survivor_keys.append(key)
        rival_checks.append(
            {
                "settings": dict(settings),
                "matches_all_demonstrations": not disagreements,
                "demonstration_disagreements": disagreements,
            }
        )
    if survivor_keys != [selected_key]:
        raise RuntimeError(
            f"demonstrations do not identify selected setting: {survivor_keys}"
        )

    query_identification = []
    for query_index in range(queries):
        absolute = demos + query_index
        eliminated = []
        for settings in SETTING_COMBINATIONS:
            key = _setting_key(settings)
            if key == selected_key:
                continue
            if predictions[key][absolute] != selected_outputs[absolute]:
                eliminated.append(dict(settings))
        if len(eliminated) != len(SETTING_COMBINATIONS) - 1:
            raise RuntimeError(
                f"query {query_index} does not require every selected parameter"
            )
        query_identification.append(
            {
                "query_index": query_index,
                "selected_setting": dict(selected),
                "eliminated_rivals_that_disagree": eliminated,
                "query_answer_used_for_demo_fit": False,
            }
        )

    return {
        "schema": "44690b1b635f-maze-connectivity-phase-episode-v1",
        "status": STATUS,
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "settings": dict(selected),
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "train": train,
        "test": test,
        "program_solution": programs[selected_key],
        "program_sha256": _sha256(programs[selected_key]),
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "input_sha256": [grid_sha256(grid) for grid in grids],
        "input_certificates": [input_certificate(grid) for grid in grids],
        "surviving_settings_from_demonstrations": [dict(selected)],
        "rival_checks": rival_checks,
        "query_identification": query_identification,
        "declared_rule_sha256": {
            key: _sha256(source) for key, source in programs.items()
        },
    }


def generate_episode(
    seed: Any,
    *,
    settings: Any = None,
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Create one Racket-labeled episode under one fixed hidden setting."""
    checked_seed = _validate_seed(seed)
    demo_count = _validate_count("demos", demos)
    query_count = _validate_count("queries", queries)
    attempt_limit = _validate_attempts(max_attempts)
    selected = (
        parameter_for_seed(checked_seed)
        if settings is None
        else normalize_settings(settings)
    )
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    if bridge is None:
        with RacketBridge(max_calls_before_restart=128) as owned:
            return _generate_episode_with_bridge(
                checked_seed,
                selected,
                demo_count,
                query_count,
                attempt_limit,
                owned,
                root_path,
            )
    return _generate_episode_with_bridge(
        checked_seed,
        selected,
        demo_count,
        query_count,
        attempt_limit,
        bridge,
        root_path,
    )


def public_payload(episode: Any) -> dict[str, Any]:
    """Project a private labeled episode to its exact visible challenge."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dict")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    try:
        return {
            "train": [
                {
                    "input": _strict_grid(pair["input"]),
                    "output": _strict_grid(pair["output"]),
                }
                for pair in train
            ],
            "test": [{"input": _strict_grid(pair["input"])} for pair in test],
        }
    except (KeyError, TypeError) as error:
        raise ValueError("episode pairs are incomplete") from error



def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _validated_seeds(seeds: Any) -> tuple[int, ...]:
    if isinstance(seeds, (str, bytes, bytearray, dict)):
        raise ValueError("seeds must be a finite iterable of literal integers")
    try:
        values = tuple(_validate_seed(seed) for seed in seeds)
    except TypeError as error:
        raise ValueError("seeds must be a finite iterable of literal integers") from error
    if not values:
        raise ValueError("seeds must contain at least one episode seed")
    if len(values) != len(set(values)):
        raise ValueError("episode seeds must be distinct")
    return values


def _rule_filename(settings: Any) -> str:
    selected = normalize_settings(settings)
    return f"{selected['connectivity']}-{selected['phase']}.rkt"


def _file_record(base: Path, path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(base).as_posix(),
        "bytes": len(payload),
        "sha256": _sha256(payload),
    }


def _write_evidence_with_bridge(
    out: Path,
    seeds: tuple[int, ...],
    demos: int,
    queries: int,
    max_attempts: int,
    bridge: RacketBridge,
    root: Path,
) -> dict[str, Any]:
    public_dir = out / "public"
    private_episode_dir = out / "private" / "episodes"
    private_rule_dir = out / "private" / "rules"
    public_dir.mkdir(parents=True)
    private_episode_dir.mkdir(parents=True)
    private_rule_dir.mkdir(parents=True)

    programs: dict[str, str] = {}
    rule_rows: list[dict[str, Any]] = []
    retained_paths: list[Path] = []
    for settings in SETTING_COMBINATIONS:
        key = _setting_key(settings)
        source = materialize_rule(settings, root=root)
        programs[key] = source
        rule_path = private_rule_dir / _rule_filename(settings)
        rule_path.write_text(source, encoding="utf-8")
        retained_paths.append(rule_path)
        rule_rows.append(
            {
                "settings": dict(settings),
                "path": rule_path.relative_to(out).as_posix(),
                "sha256": _sha256(source),
                "canonical_default": settings == DEFAULT_SETTINGS,
            }
        )

    canonical = canonical_source(root=root)
    if programs[_setting_key(DEFAULT_SETTINGS)] != canonical:
        raise ValueError("default program is not byte-identical to canonical authority")

    public_ids: set[str] = set()
    episode_rows: list[dict[str, Any]] = []
    distinct_inputs: set[str] = set()
    settings_exercised: set[str] = set()
    for seed in seeds:
        episode = generate_episode(
            seed,
            demos=demos,
            queries=queries,
            max_attempts=max_attempts,
            bridge=bridge,
            root=root,
        )
        public = public_payload(episode)
        public_bytes = public_challenge_bytes(public)
        public_id = public_challenge_id(public)
        if public_id in public_ids:
            raise ValueError("different seeds produced the same visible public challenge")
        public_ids.add(public_id)

        public_path = public_dir / f"challenge-{public_id}.json"
        public_path.write_bytes(public_bytes)
        retained_paths.append(public_path)

        private = copy.deepcopy(episode)
        private["public_id"] = public_id
        private["public_path"] = public_path.relative_to(out).as_posix()
        private["query_answers"] = [
            copy.deepcopy(pair["output"]) for pair in private["test"]
        ]
        private_path = private_episode_dir / f"{public_id}.json"
        _write_json(private_path, private)
        retained_paths.append(private_path)

        distinct_inputs.update(private["input_sha256"])
        settings_exercised.add(_setting_key(private["settings"]))
        episode_rows.append(
            {
                "public_id": public_id,
                "public_path": public_path.relative_to(out).as_posix(),
                "private_path": private_path.relative_to(out).as_posix(),
                "seed": seed,
                "settings": copy.deepcopy(private["settings"]),
                "program_sha256": private["program_sha256"],
            }
        )

    episode_rows.sort(key=lambda row: row["public_id"])
    file_rows = sorted(
        (_file_record(out, path) for path in retained_paths),
        key=lambda row: row["path"],
    )
    manifest: dict[str, Any] = {
        "schema": "44690b1b635f-maze-connectivity-phase-evidence-v1",
        "status": STATUS,
        "approved": False,
        "task_id": TASK_ID,
        "version": VERSION,
        "parameter": {
            "connectivity": {
                "allowed": list(CONNECTIVITIES),
                "default": DEFAULT_SETTINGS["connectivity"],
            },
            "phase": {
                "allowed": list(PHASES),
                "default": DEFAULT_SETTINGS["phase"],
            },
            "fixed_once_per_episode": True,
            "input_constraints_depend_on_settings": False,
        },
        "canonical_source_sha256": CANONICAL_SOURCE_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_default_unchanged": True,
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "rules": rule_rows,
        "episodes": episode_rows,
        "counts": {
            "episodes": len(episode_rows),
            "train_pairs": demos * len(episode_rows),
            "query_pairs": queries * len(episode_rows),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len(settings_exercised),
        },
        "files": file_rows,
        "manifest_hash_scope": "all retained public/private data files; manifest.json excludes itself",
        "limitations": [
            "Task-local proposed prototype only; no production generator, catalog, approval, or training-admission change.",
            "The declared family contains exactly four connectivity/phase settings and does not claim completeness over other maze hypotheses.",
            "The finite seed evidence demonstrates bounded behavior; it is not a proof over all procedural seeds.",
            "Public challenges intentionally omit seeds, settings, rule text, hashes, and query answers.",
        ],
    }
    _write_json(out / "manifest.json", manifest)
    return manifest


def write_evidence(
    out: str | Path,
    *,
    seeds: Any = (0, 1, 2, 3),
    demos: Any = 3,
    queries: Any = 4,
    max_attempts: Any = DEFAULT_MAX_ATTEMPTS,
    bridge: RacketBridge | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Write atomic privacy-separated evidence for a finite seed set."""
    out_path = Path(out)
    if out_path.exists():
        raise FileExistsError(f"output directory already exists: {out_path}")
    seed_values = _validated_seeds(seeds)
    demo_count = _validate_count("demos", demos)
    query_count = _validate_count("queries", queries)
    attempt_limit = _validate_attempts(max_attempts)
    root_path = find_root(__file__) if root is None else Path(root).resolve()

    out_path.mkdir(parents=True, exist_ok=False)
    try:
        if bridge is None:
            with RacketBridge(max_calls_before_restart=128) as owned:
                return _write_evidence_with_bridge(
                    out_path,
                    seed_values,
                    demo_count,
                    query_count,
                    attempt_limit,
                    owned,
                    root_path,
                )
        return _write_evidence_with_bridge(
            out_path,
            seed_values,
            demo_count,
            query_count,
            attempt_limit,
            bridge,
            root_path,
        )
    except BaseException:
        shutil.rmtree(out_path, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3])
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    args = parser.parse_args(argv)
    manifest = write_evidence(
        args.out,
        seeds=tuple(args.seeds),
        demos=args.demos,
        queries=args.queries,
        max_attempts=args.max_attempts,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "out": str(args.out),
                "episodes": manifest["counts"]["episodes"],
                "train_pairs": manifest["counts"]["train_pairs"],
                "query_pairs": manifest["counts"]["query_pairs"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
