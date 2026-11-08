#!/usr/bin/env python3
"""Proposed matrix-order variants for ARC task df5e596e5e96.

The canonical setting returns the selected Racket source byte-for-byte.  The
alternate first computes that canonical pairwise relation matrix (stage A),
derives an input-dependent relation signature for every panel (intermediate),
and then permutes both matrix axes by those signatures (stage B).
"""
from __future__ import annotations

import hashlib
import json
from contextlib import nullcontext
from functools import lru_cache
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "df5e596e5e96"
VERSION = "proposed-relation-signature-order-v1"
CANONICAL_SOURCE_SHA256 = "dd7b7aac9913cfda3671bc02b7b8af33716140dd90702a08af92f45f4f8383e4"
GENERATOR_SOURCE_SHA256 = "7eaedfe24e1c2faba9192e342314ad541f643291b3f17397db4754c9effb2ae3"

MATRIX_ORDERS = ("input", "relation_signature")
DEFAULT_SETTINGS = {"matrix_order": "input"}
ALL_SETTINGS = tuple({"matrix_order": value} for value in MATRIX_ORDERS)

_CANONICAL_TAIL = """(let* ((panels (map normalize-binary (split-fixed-panels-row g (rows g) 5))) (n (length panels))) (grid-from-fn n n (lambda (i j) (let* ((a (list-ref panels i)) (b (list-ref panels j)) (rotset (all-rot-supports a)) (dihedral (all-dihedral-supports a))) (cond ((= i j) 8) ((equal? b a) 1) ((member? b rotset) 2) ((member? b dihedral) 3) (else 0))))))))"""

_RELATION_SIGNATURE_TAIL = """(let* ((panels (map normalize-binary (split-fixed-panels-row g (rows g) 5)))
       (n (length panels))
       (matrix
        (grid-from-fn n n
          (lambda (i j)
            (let* ((a (list-ref panels i))
                   (b (list-ref panels j))
                   (rotset (all-rot-supports a))
                   (dihedral (all-dihedral-supports a)))
              (cond ((= i j) 8)
                    ((equal? b a) 1)
                    ((member? b rotset) 2)
                    ((member? b dihedral) 3)
                    (else 0))))))
       (order
        (sort-by (range n)
          (lambda (i)
            (let ((row (list-ref matrix i)))
              (+ (* -1000 (length (filter (lambda (v) (= v 1)) row)))
                 (* -100 (length (filter (lambda (v) (= v 2)) row)))
                 (* -10 (length (filter (lambda (v) (= v 3)) row)))
                 i))))))
  (grid-from-fn n n
    (lambda (i j)
      (at matrix (list-ref order i) (list-ref order j)))))))"""

def _sha256(value: str | bytes) -> str:
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def normalize_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"matrix_order"}:
        raise ValueError("settings must name exactly matrix_order")
    matrix_order = settings["matrix_order"]
    if type(matrix_order) is not str or matrix_order not in MATRIX_ORDERS:
        raise ValueError(f"matrix_order must be one of {MATRIX_ORDERS!r}")
    return {"matrix_order": matrix_order}


def settings_key(settings: Any) -> str:
    return normalize_settings(settings)["matrix_order"]


def canonical_source(*, root: str | Path | None = None) -> str:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    sources = {
        row["program_solution"]
        for line in canonical_path(root_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(sources) != 1:
        raise ValueError(f"expected one canonical source for {TASK_ID}, found {len(sources)}")
    source = sources.pop()
    if _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source differs from the pinned task rule")
    if source.count(_CANONICAL_TAIL) != 1:
        raise ValueError("pinned canonical source lacks the guarded matrix tail")
    return source


def program(settings: Any, *, root: str | Path | None = None) -> str:
    checked = normalize_settings(settings)
    source = canonical_source(root=root)
    if checked == DEFAULT_SETTINGS:
        return source
    return source.replace(_CANONICAL_TAIL, _RELATION_SIGNATURE_TAIL, 1)


@lru_cache(maxsize=8)
def _selected_generator(root_text: str):
    module, _source, digest = load_selected_generator(TASK_ID, root=Path(root_text))
    if digest != GENERATOR_SOURCE_SHA256:
        raise ValueError("selected generator differs from the prototype's pinned input grammar")
    return module


def relation_signature_order(matrix: Any) -> list[int]:
    normalized = normalize_grid(matrix)
    n = len(normalized)
    if n != len(normalized[0]):
        raise ValueError("relation matrix must be square")
    return sorted(
        range(n),
        key=lambda index: (
            -1000 * normalized[index].count(1)
            - 100 * normalized[index].count(2)
            - 10 * normalized[index].count(3)
            + index
        ),
    )


def transform(
    grid: Any,
    settings: Any,
    *,
    root: str | Path | None = None,
) -> list[list[int]]:
    checked = normalize_settings(settings)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator = _selected_generator(str(root_path))
    matrix = normalize_grid(generator.rule_mirror(normalize_grid(grid)))
    if checked["matrix_order"] == "input":
        return matrix
    order = relation_signature_order(matrix)
    return [[matrix[order[row]][order[col]] for col in range(len(order))] for row in range(len(order))]


def _grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    if type(source) is not str or not source.strip():
        raise ValueError("source must be a nonempty Racket rule")
    expression = f"({wrap_rule(source)} {_grid_literal(grid)})"
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        return normalize_grid(active.eval_text(expression))

AUDIT_RIVALS = (
    "reverse_input",
    "relation_degree",
    "row_sum",
    "rotation_count",
    "color_order",
)


def _validated_seed(seed: Any) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _validated_count(value: Any, *, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be a literal integer in {minimum}..{maximum}")
    return value


def _permute(matrix: Any, order: list[int]) -> list[list[int]]:
    normalized = normalize_grid(matrix)
    return [[normalized[order[row]][order[col]] for col in range(len(order))] for row in range(len(order))]


def _panel_colors(grid: Any) -> list[int]:
    normalized = normalize_grid(grid)
    width = len(normalized[0])
    if len(normalized) != 5 or (width + 1) % 6:
        raise ValueError("expected a five-row fixed-panel input")
    n = (width + 1) // 6
    colors = []
    for panel in range(n):
        values = {
            normalized[row][panel * 6 + col]
            for row in range(5)
            for col in range(5)
            if normalized[row][panel * 6 + col] != 0
        }
        if len(values) != 1:
            raise ValueError("each panel must have exactly one foreground color")
        colors.append(values.pop())
    return colors


def rival_order(grid: Any, matrix: Any, name: str) -> list[int]:
    normalized = normalize_grid(matrix)
    n = len(normalized)
    if name == "reverse_input":
        return list(reversed(range(n)))
    if name == "relation_degree":
        return sorted(
            range(n),
            key=lambda index: (-sum(value in (1, 2, 3) for value in normalized[index]), index),
        )
    if name == "row_sum":
        return sorted(range(n), key=lambda index: (-sum(normalized[index]), index))
    if name == "rotation_count":
        return sorted(range(n), key=lambda index: (-normalized[index].count(2), index))
    if name == "color_order":
        colors = _panel_colors(grid)
        return sorted(range(n), key=lambda index: (colors[index], index))
    raise ValueError(f"unknown audit rival {name!r}")


def rival_transform(
    grid: Any,
    name: str,
    *,
    root: str | Path | None = None,
) -> list[list[int]]:
    canonical = transform(grid, DEFAULT_SETTINGS, root=root)
    return _permute(canonical, rival_order(grid, canonical, name))


def _frozen(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in normalize_grid(grid))


def _thawed(grid: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    return [list(row) for row in grid]


def _audit_coverage(grid: Any, *, root: str | Path) -> frozenset[tuple[str, str]]:
    coverage: set[tuple[str, str]] = set()
    for settings in ALL_SETTINGS:
        correct = transform(grid, settings, root=root)
        for name in AUDIT_RIVALS:
            if rival_transform(grid, name, root=root) != correct:
                coverage.add((settings_key(settings), name))
    return frozenset(coverage)


@lru_cache(maxsize=64)
def _input_schedule_cached(
    seed: int,
    root_text: str,
) -> tuple[tuple[tuple[tuple[int, ...], ...], ...], tuple[tuple[tuple[int, ...], ...], ...]]:
    root = Path(root_text)
    generator = _selected_generator(root_text)
    goals = {(settings_key(settings), name) for settings in ALL_SETTINGS for name in AUDIT_RIVALS}
    seen: set[tuple[tuple[int, ...], ...]] = set()
    candidates: list[tuple[int, tuple[tuple[int, ...], ...], frozenset[tuple[str, str]]]] = []

    for sample_index in range(256):
        grid = generator.generate(seed, sample_index, difficulty="hard", n_panels=5)
        key = _frozen(grid)
        if key in seen or generator.self_check(grid, difficulty="hard"):
            continue
        outputs = {_frozen(transform(grid, settings, root=root)) for settings in ALL_SETTINGS}
        if len(outputs) != len(ALL_SETTINGS):
            continue
        seen.add(key)
        candidates.append((sample_index, key, _audit_coverage(grid, root=root)))

    selected: list[tuple[int, tuple[tuple[int, ...], ...], frozenset[tuple[str, str]]]] = []
    uncovered = set(goals)
    remaining = list(candidates)
    for _slot in range(2):
        if not remaining:
            break
        best = min(remaining, key=lambda row: (-len(row[2] & uncovered), row[0]))
        selected.append(best)
        remaining.remove(best)
        uncovered -= best[2]
    if uncovered:
        raise ValueError(f"could not construct two-demo shortcut coverage: {sorted(uncovered)!r}")
    selected.extend(remaining[: 6 - len(selected)])
    if len(selected) != 6:
        raise ValueError("could not construct six unique distinguishing demonstrations")

    demos = tuple(row[1] for row in selected)
    query_values: list[tuple[tuple[int, ...], ...]] = []
    for offset in range(512):
        sample_index = 1_000_000 + offset
        grid = generator.generate(seed, sample_index, difficulty="hard", n_panels=5)
        key = _frozen(grid)
        if key in seen or generator.self_check(grid, difficulty="hard"):
            continue
        outputs = {_frozen(transform(grid, settings, root=root)) for settings in ALL_SETTINGS}
        if len(outputs) != len(ALL_SETTINGS):
            continue
        seen.add(key)
        query_values.append(key)
        if len(query_values) == 8:
            break
    if len(query_values) != 8:
        raise ValueError("could not construct eight unique distinguishing queries")
    return demos, tuple(query_values)


def _input_schedule(
    seed: int,
    *,
    root: str | Path | None = None,
) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    demos, queries = _input_schedule_cached(seed, str(root_path))
    return [_thawed(grid) for grid in demos], [_thawed(grid) for grid in queries]


def fit_settings(
    demonstrations: Any,
    *,
    root: str | Path | None = None,
) -> list[dict[str, str]]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    survivors = []
    for settings in ALL_SETTINGS:
        try:
            fits = all(
                transform(pair["input"], settings, root=root) == normalize_grid(pair["output"])
                for pair in demonstrations
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("each demonstration needs valid input and output grids") from exc
        if fits:
            survivors.append(dict(settings))
    return survivors


def audit_episode(
    episode: Any,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = normalize_settings(episode.get("settings"))
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode needs nonempty train and test lists")
    rivals: dict[str, dict[str, Any]] = {}
    ambiguous = []
    for name in AUDIT_RIVALS:
        fits_all = all(
            rival_transform(pair["input"], name, root=root) == normalize_grid(pair["output"])
            for pair in train
        )
        changed_queries = [
            index
            for index, pair in enumerate(test)
            if rival_transform(pair["input"], name, root=root) != normalize_grid(pair["output"])
        ]
        rivals[name] = {
            "fits_all_demos": fits_all,
            "changed_query_indices": changed_queries,
        }
        if fits_all and changed_queries:
            ambiguous.append(name)
    return {
        "settings": settings,
        "rivals": rivals,
        "ambiguous_rivals": ambiguous,
        "limits": "Finite declared rival audit only; not a universal uniqueness proof.",
    }


def generate_episode(
    seed: Any,
    settings: Any,
    *,
    demos: Any = 3,
    queries: Any = 4,
    root: str | Path | None = None,
) -> dict[str, Any]:
    checked_seed = _validated_seed(seed)
    checked_settings = normalize_settings(settings)
    checked_demos = _validated_count(demos, name="demos", minimum=2, maximum=6)
    checked_queries = _validated_count(queries, name="queries", minimum=1, maximum=8)
    demo_inputs, query_inputs = _input_schedule(checked_seed, root=root)

    def pair(grid: Any) -> dict[str, list[list[int]]]:
        return {
            "input": normalize_grid(grid),
            "output": transform(grid, checked_settings, root=root),
        }

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    survivors = fit_settings(train, root=root)
    if survivors != [checked_settings]:
        raise ValueError(f"demonstrations do not uniquely identify settings: {survivors!r}")
    episode = {
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "seed": checked_seed,
        "settings": checked_settings,
        "train": train,
        "test": test,
        "program_solution": program(checked_settings, root=root),
    }
    audit = audit_episode(episode, root=root)
    unrefuted = [name for name, row in audit["rivals"].items() if row["fits_all_demos"]]
    if unrefuted:
        raise ValueError(f"demonstrations leave declared shortcut rivals: {unrefuted!r}")
    return episode


def verify_episode(
    episode: Any,
    *,
    root: str | Path | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = normalize_settings(episode.get("settings"))
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("episode needs nonempty train and test lists")
    pairs = train + test
    sources = {settings_key(candidate): program(candidate, root=root) for candidate in ALL_SETTINGS}
    manager = nullcontext(bridge) if bridge is not None else RacketBridge(max_calls_before_restart=256)
    with manager as active:
        survivors = []
        for candidate in ALL_SETTINGS:
            source = sources[settings_key(candidate)]
            if all(execute_rule(source, pair["input"], bridge=active) == pair["output"] for pair in train):
                survivors.append(dict(candidate))
        checks = []
        selected_source = sources[settings_key(settings)]
        for index, pair in enumerate(pairs):
            racket_output = execute_rule(selected_source, pair["input"], bridge=active)
            python_output = transform(pair["input"], settings, root=root)
            checks.append(
                {
                    "pair_index": index,
                    "program_sha256": _sha256(selected_source),
                    "matches_python": racket_output == python_output == normalize_grid(pair["output"]),
                }
            )
    return {
        "settings": settings,
        "label_count": len(pairs),
        "surviving_settings": survivors,
        "program_checks": checks,
        "audit": audit_episode(episode, root=root),
    }
