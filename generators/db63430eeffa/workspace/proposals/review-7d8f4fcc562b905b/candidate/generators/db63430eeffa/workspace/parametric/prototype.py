#!/usr/bin/env python3
"""Task-local prototype for selecting which endpoint path(s) are painted.

The canonical generator and catalog remain unchanged.  A complete episode fixes
one hidden ``path_mode`` setting across all demonstrations and queries:

* ``both`` (default): the exact canonical rule, painting the union of the
  diagonal-first and straight-first paths;
* ``diagonal_first``: paint only the diagonal-then-straight path;
* ``straight_first``: paint only the straight-then-diagonal path.

All settings preserve endpoint extraction, step directions, major-axis logic,
endpoint colors, and path color.  Only the selected path set changes.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        if str(runtime) not in sys.path:
            sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        if str(ancestor) not in sys.path:
            sys.path.insert(0, str(ancestor))
        break

from reviewer_support import (  # noqa: E402
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "db63430eeffa"
PROTOTYPE_VERSION = "proposed-path-selection-v1"
PATH_MODES = ("both", "diagonal_first", "straight_first")
SETTINGS = PATH_MODES
DEFAULT_PATH_MODE = "both"
DEFAULT_N_TRAIN = 3
DEFAULT_N_TEST = 4
CANONICAL_EXACT_SHA256 = (
    "738576fedc01cbcd29e0e5a381777ed10929461bca3c60994cee0a3fb4010c46"
)
CANONICAL_NORMALIZED_SHA256 = (
    "3e3bf77eb552f1b44d376e68304bd479643b4dce5f09e62b73ff0f17a69e083b"
)
_DIFFICULTY_SCHEDULE = ("easy", "medium", "hard")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalized_source(source: str) -> str:
    return " ".join(source.split())


def _validate_path_mode(path_mode: Any) -> str:
    if path_mode not in PATH_MODES or type(path_mode) is not str:
        raise ValueError(f"path_mode must be one of {PATH_MODES}, got {path_mode!r}")
    return path_mode


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")
    return seed


def _validate_count(name: str, value: Any) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive exact integer")
    return value


def _resolve_root(root: Path | str | None = None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


def canonical_source(*, root: Path | str | None = None) -> str:
    """Return the unique canonical Racket source, pinned by exact hashes."""
    resolved = _resolve_root(root)
    sources: set[str] = set()
    with canonical_path(resolved).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            source = row.get("program_solution")
            if isinstance(source, str) and source.strip():
                sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(sources)}"
        )
    source = next(iter(sources))
    exact = _sha256_text(source)
    normalized = _sha256_text(_normalized_source(source))
    if exact != CANONICAL_EXACT_SHA256:
        raise ValueError(f"canonical exact source hash changed: {exact}")
    if normalized != CANONICAL_NORMALIZED_SHA256:
        raise ValueError(f"canonical normalized source hash changed: {normalized}")
    return source


def _balanced_expression_end(source: str, start: int) -> int:
    """Return one-past-end for the balanced s-expression at ``start``."""
    if start >= len(source) or source[start] != "(":
        raise ValueError("balanced expression must start at '('")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unbalanced canonical Racket source")


def _path_walk_ranges(source: str) -> list[tuple[int, int]]:
    """Locate the two top-level path-building named-let expressions."""
    needle = "\n             (let loop1"
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while True:
        line_start = source.find(needle, cursor)
        if line_start < 0:
            break
        expression_start = line_start + len("\n             ")
        ranges.append(
            (line_start, _balanced_expression_end(source, expression_start))
        )
        cursor = ranges[-1][1]
    if len(ranges) != 2:
        raise ValueError(
            f"expected two canonical path walks, found {len(ranges)}"
        )
    return ranges


def program_for(
    path_mode: str = DEFAULT_PATH_MODE,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize exact executable Racket for one declared path setting."""
    selected = _validate_path_mode(path_mode)
    source = canonical_source(root=root)
    if selected == DEFAULT_PATH_MODE:
        return source
    first, second = _path_walk_ranges(source)
    remove = second if selected == "diagonal_first" else first
    transformed = source[: remove[0]] + source[remove[1] :]
    if transformed == source or transformed.count("(let loop1") != 1:
        raise AssertionError(f"failed to materialize {selected!r} rule")
    return transformed


def exact_program_hash(
    path_mode: str = DEFAULT_PATH_MODE,
    *,
    root: Path | str | None = None,
) -> str:
    return _sha256_text(program_for(path_mode, root=root))


def normalized_program_hash(
    path_mode: str = DEFAULT_PATH_MODE,
    *,
    root: Path | str | None = None,
) -> str:
    return _sha256_text(_normalized_source(program_for(path_mode, root=root)))


def _validate_grid(grid: Any) -> list[list[int]]:
    normalized = normalize_grid(grid)
    eights = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 8
    ]
    if len(eights) != 2:
        raise ValueError(f"expected exactly two color-8 endpoints, found {len(eights)}")
    (r1, c1), (r2, c2) = eights
    if r1 == r2 or c1 == c2:
        raise ValueError("endpoints must differ in both row and column")
    return normalized


def solve(grid: Any, *, path_mode: str = DEFAULT_PATH_MODE) -> list[list[int]]:
    """Pure Python mirror for tests; retained labels are rechecked in Racket."""
    selected = _validate_path_mode(path_mode)
    normalized = _validate_grid(grid)
    height, width = len(normalized), len(normalized[0])
    endpoints = [
        (row, col)
        for row, values in enumerate(normalized)
        for col, value in enumerate(values)
        if value == 8
    ]
    (r1, c1), (r2, c2) = endpoints
    dr, dc = r2 - r1, c2 - c1
    row_step = 1 if dr > 0 else -1
    col_step = 1 if dc > 0 else -1
    diagonal_steps = min(abs(dr), abs(dc))
    straight_steps = abs(abs(dr) - abs(dc))
    major_is_row = abs(dr) > abs(dc)
    path: set[tuple[int, int]] = set()

    def walk(diagonal_first: bool) -> None:
        row, col = r1, c1
        segments = (
            (("diagonal", diagonal_steps), ("straight", straight_steps))
            if diagonal_first
            else (("straight", straight_steps), ("diagonal", diagonal_steps))
        )
        for kind, steps in segments:
            for _ in range(steps):
                path.add((row, col))
                if kind == "diagonal":
                    row += row_step
                    col += col_step
                elif major_is_row:
                    row += row_step
                else:
                    col += col_step
        path.add((row, col))

    if selected in ("both", "diagonal_first"):
        walk(True)
    if selected in ("both", "straight_first"):
        walk(False)

    output = [[0] * width for _ in range(height)]
    for row, col in path:
        output[row][col] = 3
    output[r1][c1] = 8
    output[r2][c2] = 8
    return output


def selected_generator(*, root: Path | str | None = None):
    return load_selected_generator(TASK_ID, root=_resolve_root(root))


def _derived_generation_seed(episode_seed: int, pair_index: int, attempt: int) -> int:
    material = f"{TASK_ID}:{PROTOTYPE_VERSION}:{episode_seed}:{pair_index}:{attempt}"
    return int(hashlib.sha256(material.encode("utf-8")).hexdigest()[:16], 16)


def _choose_path_mode(seed: int) -> str:
    digest = hashlib.sha256(
        f"{TASK_ID}:{PROTOTYPE_VERSION}:setting:{seed}".encode("utf-8")
    ).digest()
    return PATH_MODES[digest[0] % len(PATH_MODES)]


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_episode(
    seed: Any,
    *,
    path_mode: str | None = None,
    n_train: Any = DEFAULT_N_TRAIN,
    n_test: Any = DEFAULT_N_TEST,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Build one deterministic fixed-setting episode with distinct inputs."""
    episode_seed = _validate_seed(seed)
    train_count = _validate_count("n_train", n_train)
    test_count = _validate_count("n_test", n_test)
    selected = (
        _choose_path_mode(episode_seed)
        if path_mode is None
        else _validate_path_mode(path_mode)
    )
    resolved = _resolve_root(root)
    generator, source_path, source_sha256 = selected_generator(root=resolved)
    pairs: list[dict[str, Any]] = []
    seen_inputs: set[str] = set()

    for pair_index in range(train_count + test_count):
        difficulty = _DIFFICULTY_SCHEDULE[pair_index % len(_DIFFICULTY_SCHEDULE)]
        for attempt in range(200):
            generation_seed = _derived_generation_seed(
                episode_seed, pair_index, attempt
            )
            grid = generator.generate(
                generation_seed,
                pair_index,
                difficulty=difficulty,
            )
            errors = generator.self_check(grid, difficulty=difficulty)
            if errors:
                raise AssertionError(
                    f"selected generator emitted invalid input {pair_index}: {errors}"
                )
            normalized = normalize_grid(grid)
            digest = _grid_digest(normalized)
            if digest in seen_inputs:
                continue
            counterfactuals = {
                mode: solve(normalized, path_mode=mode) for mode in PATH_MODES
            }
            if len(
                {tuple(map(tuple, value)) for value in counterfactuals.values()}
            ) != len(PATH_MODES):
                continue
            seen_inputs.add(digest)
            pairs.append(
                {
                    "input": normalized,
                    "output": counterfactuals[selected],
                    "input_sha256": digest,
                    "sampling": {
                        "seed": generation_seed,
                        "sample_index": pair_index,
                        "attempt": attempt,
                        "difficulty": difficulty,
                    },
                }
            )
            break
        else:
            raise AssertionError(
                f"could not sample distinct path-discriminating input {pair_index}"
            )

    source_relative = (
        source_path.relative_to(resolved).as_posix()
        if source_path.is_relative_to(resolved)
        else source_path.name
    )
    program = program_for(selected, root=resolved)
    return {
        "schema": "arcpuzzles-path-selection-episode-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "parameters": {"path_mode": selected},
        "program": program,
        "program_sha256": _sha256_text(program),
        "generator_source": {
            "path": source_relative,
            "sha256": source_sha256,
        },
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "meta": {
            "seed": episode_seed,
            "n_train": train_count,
            "n_test": test_count,
            "input_generation_shared_across_settings": True,
        },
    }


def analyze_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Check finite declared-rival identifiability from demonstrations only."""
    if not isinstance(episode, dict):
        raise ValueError("episode must be a dictionary")
    selected = _validate_path_mode(episode["parameters"]["path_mode"])
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode must have nonempty train and test lists")

    surviving: list[str] = []
    demo_mismatches: dict[str, list[int]] = {}
    query_mismatches: dict[str, list[int]] = {}
    for mode in PATH_MODES:
        demo_bad = [
            index
            for index, pair in enumerate(train)
            if solve(pair["input"], path_mode=mode) != pair["output"]
        ]
        query_bad = [
            index
            for index, pair in enumerate(test)
            if solve(pair["input"], path_mode=mode) != pair["output"]
        ]
        demo_mismatches[mode] = demo_bad
        query_mismatches[mode] = query_bad
        if not demo_bad:
            surviving.append(mode)

    query_digests = [_grid_digest(normalize_grid(pair["input"])) for pair in test]
    train_digests = {_grid_digest(normalize_grid(pair["input"])) for pair in train}
    return {
        "selected_mode": selected,
        "declared_rivals": [mode for mode in PATH_MODES if mode != selected],
        "surviving_modes": surviving,
        "identified": surviving == [selected],
        "demo_mismatches": demo_mismatches,
        "query_mismatches": query_mismatches,
        "all_queries_distinct": len(set(query_digests)) == len(query_digests),
        "queries_disjoint_from_demos": not (set(query_digests) & train_digests),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project only visible demonstrations and answer-masked query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_challenge(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_challenge(episode))


def public_filename(episode: dict[str, Any]) -> str:
    return f"challenge-{public_id(episode)}.json"
