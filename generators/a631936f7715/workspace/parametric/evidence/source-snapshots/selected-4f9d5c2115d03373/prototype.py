"""Proposed episode-level component-connectivity parameter for a631936f7715.

The canonical task segments magenta cells into 4-connected components, then
recolors each component from its one orthogonally adjacent label.  This bounded
prototype varies only component segmentation (4- versus 8-connectivity); label
lookup remains orthogonal and every retained input has at most one label per
component under either setting.  One value is chosen once per episode.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a631936f7715"
PROTOTYPE_VERSION = "1.1.0"
ALLOWED_CONNECTIVITIES = (4, 8)
DEFAULT_CONNECTIVITY = 4
PARAMETERS = {"component_connectivity": ALLOWED_CONNECTIVITIES}
_BG = 7
_SRC = 6
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

_BFS_4 = """(list (list (- cr 1) cc)
                                                           (list (+ cr 1) cc)
                                                           (list cr (- cc 1))
                                                           (list cr (+ cc 1)))"""
_BFS_8 = """(list (list (- cr 1) cc)
                                                           (list (+ cr 1) cc)
                                                           (list cr (- cc 1))
                                                           (list cr (+ cc 1))
                                                           (list (- cr 1) (- cc 1))
                                                           (list (- cr 1) (+ cc 1))
                                                           (list (+ cr 1) (- cc 1))
                                                           (list (+ cr 1) (+ cc 1)))"""


def _canonical_program() -> str:
    root = find_root(__file__)
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def _validate_connectivity(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("component_connectivity must be integer 4 or 8 (not bool)")
    if value not in ALLOWED_CONNECTIVITIES:
        raise ValueError(f"component_connectivity must be one of {ALLOWED_CONNECTIVITIES}")
    return value


def choose_connectivity(seed: int) -> int:
    """Choose one hidden setting deterministically for a whole episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_CONNECTIVITIES[seed % len(ALLOWED_CONNECTIVITIES)]


def program_for(connectivity: int = DEFAULT_CONNECTIVITY) -> str:
    """Materialize the exact Racket rule for one bounded setting."""
    connectivity = _validate_connectivity(connectivity)
    source = _canonical_program()
    if source.count(_BFS_4) != 1:
        raise RuntimeError("canonical BFS neighbor form changed")
    if connectivity == 8:
        source = source.replace(_BFS_4, _BFS_8)
    return source


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be ARC colors 0..9")
    return len(grid), width


def _components(grid: list[list[int]], connectivity: int) -> list[list[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    directions = _DIRS4 if _validate_connectivity(connectivity) == 4 else _DIRS8
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != _SRC or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in directions:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == _SRC
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def apply_python(grid: list[list[int]], connectivity: int = DEFAULT_CONNECTIVITY) -> list[list[int]]:
    """Independent Python mirror used for authoring and parity checks."""
    height, width = _validate_grid(grid)
    connectivity = _validate_connectivity(connectivity)
    output = [[_BG for _ in range(width)] for _ in range(height)]
    for cells in _components(grid, connectivity):
        labels: list[int] = []
        for row, col in cells:
            for dr, dc in _DIRS4:  # label semantics stay canonical/orthogonal
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    value = grid[nr][nc]
                    if value not in (_BG, _SRC):
                        labels.append(value)
        label = labels[-1] if labels else _SRC
        for row, col in cells:
            output[row][col] = label
    return output


def _transform(row: int, col: int, code: int, size: int = 7) -> tuple[int, int]:
    """Apply one of the eight square dihedral transforms."""
    if code >= 4:
        col = size - 1 - col
        code -= 4
    for _ in range(code):
        row, col = col, size - 1 - row
    return row, col


def _build_input(seed: int, index: int) -> list[list[int]]:
    """Build a lawful witness where the two settings necessarily disagree."""
    rng = random.Random((seed << 16) ^ (index * 0x9E3779B1) ^ 0xA631936F)
    colors = [1, 2, 3, 4, 5, 8, 9]
    rng.shuffle(colors)
    label_a, label_c, marker = colors[:3]
    code = (seed + 3 * index) % 8

    # A and B are separate 4-components but touch diagonally.  Only A is
    # labelled, so 4-connectivity preserves B as magenta while 8-connectivity
    # merges A+B and recolors all four cells.  C is an ordinary labelled
    # control component and the isolated marker preserves the distractor role.
    roles = {
        label_a: {(1, 1)},
        _SRC: {(2, 1), (2, 2), (3, 3), (4, 3), (5, 5), (5, 6)},
        label_c: {(4, 6)},
        marker: {(0, 6)},
    }
    grid = [[_BG for _ in range(7)] for _ in range(7)]
    for value, cells in roles.items():
        for row, col in cells:
            nr, nc = _transform(row, col, code)
            grid[nr][nc] = value
    return grid


def build_inputs(seed: int, count: int) -> list[list[list[int]]]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(count) is not int or count < 1:
        raise ValueError("count must be a positive integer")
    return [_build_input(seed, index) for index in range(count)]


def build_episode(
    seed: int,
    *,
    connectivity: int | None = None,
    n_train: int = 3,
    n_test: int = 1,
) -> dict[str, Any]:
    """Build a complete episode with one fixed hidden connectivity setting."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(n_train) is not int or n_train < 1:
        raise ValueError("n_train must be a positive integer")
    if type(n_test) is not int or n_test < 1:
        raise ValueError("n_test must be a positive integer")
    selected = choose_connectivity(seed) if connectivity is None else _validate_connectivity(connectivity)
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    inputs = build_inputs(seed, n_train + n_test)
    input_keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(input_keys) != len(set(input_keys)):
        raise RuntimeError("prototype sampler produced duplicate episode inputs")
    pairs = []
    for index, grid in enumerate(inputs):
        errors = generator.self_check(grid)
        if errors:
            raise RuntimeError(f"prototype input {index} violates selected grammar: {errors}")
        pairs.append(
            {
                "input": grid,
                "output": apply_python(grid, selected),
                "sampling": {"seed": seed, "input_index": index},
            }
        )
    return {
        "schema": "a631936f7715-parametric-episode-v1",
        "scope": "proposed prototype; not selected canonical execution",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameters": {"component_connectivity": selected},
        "counts": {"demonstrations": n_train, "queries": n_test},
        "program": program_for(selected),
        "generator_source": str(source_path),
        "generator_sha256": source_sha256,
        "train": pairs[:n_train],
        "test": pairs[n_train:],
    }


def episode_errors(episode: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(episode, dict):
        return ["episode must be a mapping"]
    parameters = episode.get("parameters")
    try:
        connectivity = _validate_connectivity(parameters.get("component_connectivity"))
    except (AttributeError, TypeError, ValueError) as exc:
        return [f"invalid parameters: {exc}"]
    if episode.get("program") != program_for(connectivity):
        errors.append("program does not match selected connectivity")
    root = find_root(__file__)
    generator, _path, expected_sha = load_selected_generator(TASK_ID, root=root)
    if episode.get("generator_sha256") != expected_sha:
        errors.append("generator source hash drifted")
    train = episode.get("train")
    test = episode.get("test")
    expected_counts = {
        "demonstrations": len(train) if isinstance(train, list) else None,
        "queries": len(test) if isinstance(test, list) else None,
    }
    if episode.get("counts") != expected_counts:
        errors.append("counts do not match train/test lengths")
    rival = 8 if connectivity == 4 else 4
    seen_inputs: dict[str, str] = {}
    for split in ("train", "test"):
        pairs = episode.get(split)
        if not isinstance(pairs, list) or not pairs:
            errors.append(f"{split} must be a nonempty list")
            continue
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                errors.append(f"{split}[{index}] lacks input/output")
                continue
            input_key = json.dumps(pair["input"], sort_keys=True, separators=(",", ":"))
            previous = seen_inputs.get(input_key)
            if previous is not None:
                errors.append(f"{split}[{index}] duplicate input of {previous}")
            else:
                seen_inputs[input_key] = f"{split}[{index}]"
            grammar_errors = generator.self_check(pair["input"])
            if grammar_errors:
                errors.append(f"{split}[{index}] outside grammar: {grammar_errors}")
            selected_output = apply_python(pair["input"], connectivity)
            if pair["output"] != selected_output:
                errors.append(f"{split}[{index}] label does not match selected setting")
            if apply_python(pair["input"], rival) == selected_output:
                errors.append(f"{split}[{index}] does not distinguish the rival setting")
    return errors


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return only visible demonstrations and query inputs."""
    errors = episode_errors(episode)
    if errors:
        raise ValueError(f"invalid episode: {errors}")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_batch(episodes: list[dict[str, Any]], output_dir: str | Path) -> dict[str, Any]:
    """Write public challenges by visible-content ID and keep private data separate."""
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("episodes must be a nonempty list")

    prepared: list[dict[str, Any]] = []
    for index, episode in enumerate(episodes):
        errors = episode_errors(episode)
        if errors:
            raise ValueError(f"episode {index} invalid: {errors}")
        public_bytes = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        program = episode["program"]
        program_bytes = (program.rstrip() + "\n").encode("utf-8")
        program_sha256 = hashlib.sha256(program_bytes).hexdigest()
        prepared.append(
            {
                "public_id": public_id,
                "public_bytes": public_bytes,
                "episode": deepcopy(episode),
                "program_bytes": program_bytes,
                "program_sha256": program_sha256,
            }
        )

    prepared.sort(key=lambda row: row["public_id"])
    ids = [row["public_id"] for row in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate visible public challenge ID")

    demonstration_counts = {len(row["episode"]["train"]) for row in prepared}
    query_counts = {len(row["episode"]["test"]) for row in prepared}
    if len(demonstration_counts) != 1 or len(query_counts) != 1:
        raise ValueError("all exported episodes must use the same demonstration/query counts")

    destination = Path(output_dir)
    if destination.exists():
        raise FileExistsError(f"output directory already exists: {destination}")

    public_dir = destination / "public"
    episode_dir = destination / "private" / "episodes"
    program_dir = destination / "private" / "programs"
    public_dir.mkdir(parents=True)
    episode_dir.mkdir(parents=True)
    program_dir.mkdir(parents=True)

    manifest_rows: list[dict[str, Any]] = []
    for row in prepared:
        public_id = row["public_id"]
        public_relative = Path("public") / f"{public_id}.json"
        private_relative = Path("private") / "episodes" / f"{public_id}.json"
        program_relative = Path("private") / "programs" / f"{row['program_sha256']}.rkt"
        (destination / public_relative).write_bytes(row["public_bytes"])
        (destination / private_relative).write_bytes(_json_bytes(row["episode"]))
        program_path = destination / program_relative
        if not program_path.exists():
            program_path.write_bytes(row["program_bytes"])
        manifest_rows.append(
            {
                "public_id": public_id,
                "public_path": public_relative.as_posix(),
                "private_episode_path": private_relative.as_posix(),
                "program_path": program_relative.as_posix(),
                "program_sha256": row["program_sha256"],
                "component_connectivity": row["episode"]["parameters"][
                    "component_connectivity"
                ],
            }
        )

    manifest = {
        "schema": "a631936f7715-parametric-export-v1",
        "scope": "proposed prototype; only public/ is model-visible",
        "counts": {
            "episodes": len(prepared),
            "demonstrations_per_episode": next(iter(demonstration_counts)),
            "queries_per_episode": next(iter(query_counts)),
        },
        "episodes": manifest_rows,
    }
    (destination / "private" / "manifest.json").write_bytes(_json_bytes(manifest))
    return manifest
