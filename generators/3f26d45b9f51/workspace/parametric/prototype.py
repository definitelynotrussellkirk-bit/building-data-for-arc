"""Task-local parametric prototype for lattice connection direction.

The selected production generator and canonical Racket authority remain
unchanged. One hidden ``connection_axes`` setting is selected once per episode:

* ``both`` (canonical/default): fill same-color intervals on rows and columns.
* ``horizontal``: fill only row intervals.
* ``vertical``: fill only column intervals.

All settings keep the original lattice parsing, modal divider role, marker
colors, inclusive outermost-span rule, and preservation of unconnected markers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "3f26d45b9f51"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "connection_axes"
SETTINGS = ("both", "horizontal", "vertical")
DEFAULT_SETTING = "both"
DEFAULT_DEMO_COUNT = 3
DEFAULT_QUERY_COUNT = 4
MAX_PAIR_COUNT = 16

_PARENT = None

_HORIZONTAL_BINDING = """             ;; In every coarse row, fill from the leftmost to rightmost
             ;; same-color marker; rows with fewer than two markers do nothing.
             (acc2 (reduce (lambda (a cr)
               (let* ((cols-here (map snd
                                  (filter (lambda (cp) (= (fst cp) cr)) cpositions))))
                 (if (< (length cols-here) 2) a
                   (let* ((cmin (min-list cols-here))
                          (cmax (max-list cols-here)))
                     (reduce (lambda (a2 cc)
                       (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                         (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                           pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                       a (range cmin (+ cmax 1)))))))
             acc crow-set)))"""

_VERTICAL_RESULT = """        ;; Apply the same interval rule independently down every coarse column.
        ;; Singleton or off-line markers therefore remain untouched.
        (reduce (lambda (a cc)
          (let* ((rows-here (map fst
                             (filter (lambda (cp) (= (snd cp) cc)) cpositions))))
            (if (< (length rows-here) 2) a
              (let* ((rmin (min-list rows-here))
                     (rmax (max-list rows-here)))
                (reduce (lambda (a2 cr)
                  (let* ((pr (* 3 cr)) (pc (* 3 cc)))
                    (set-cell (set-cell (set-cell (set-cell a2 pr pc mc)
                      pr (+ pc 1) mc) (+ pr 1) pc mc) (+ pr 1) (+ pc 1) mc)))
                  a (range rmin (+ rmax 1)))))))
          acc2 ccol-set))"""


def _root() -> Path:
    return find_root(__file__)


def _load_parent():
    global _PARENT
    if _PARENT is None:
        _PARENT, _, _ = load_selected_generator(TASK_ID, root=_root())
    return _PARENT


def _validate_nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool, float, or string)")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer (not bool, float, or string)")
    if not 1 <= value <= MAX_PAIR_COUNT:
        raise ValueError(f"{name} must be in 1..{MAX_PAIR_COUNT}")
    return value


def validate_setting(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in SETTINGS:
        raise ValueError(
            f"unknown {PARAMETER_NAME}={value!r}; expected one of {SETTINGS}"
        )
    return value


def choose_setting(seed: Any, value: Any | None = None) -> str:
    """Choose one hidden setting deterministically for the complete episode."""
    seed = _validate_nonnegative_int(seed, "seed")
    if value is not None:
        return validate_setting(value)
    return SETTINGS[seed % len(SETTINGS)]


def episode_difficulty(seed: Any) -> str:
    seed = _validate_nonnegative_int(seed, "seed")
    # Keep the rule setting and scene difficulty balanced but non-aliased:
    # each aligned block of three seeds covers all settings at one difficulty,
    # and each setting sees all three difficulties over a nine-seed cycle.
    return ("easy", "medium", "hard")[(seed // len(SETTINGS)) % 3]


def build_input(seed: Any, pair_index: Any) -> list[list[int]]:
    """Build one selected-family input lawful under every axis setting."""
    seed = _validate_nonnegative_int(seed, "seed")
    pair_index = _validate_nonnegative_int(pair_index, "pair_index")
    parent = _load_parent()
    grid = parent.generate(
        seed,
        pair_index,
        difficulty=episode_difficulty(seed),
    )
    findings = parent.self_check(grid)
    if findings:
        raise RuntimeError(
            "selected generator returned an unlawful input: " + "; ".join(findings)
        )
    return grid


def apply_python(grid: list[list[int]], connection_axes: Any) -> list[list[int]]:
    """Independent assertion mirror; retained evidence labels are executed by Racket."""
    setting = validate_setting(connection_axes)
    parent = _load_parent()
    findings = parent.self_check(grid)
    if findings:
        raise ValueError("invalid selected-family input: " + "; ".join(findings))
    if setting == "both":
        return parent._solve_python(grid)
    return parent._solve_with_axes(
        grid,
        horizontal=setting == "horizontal",
        vertical=setting == "vertical",
    )


def canonical_program(*, root: Path | str | None = None) -> str:
    root_path = _root() if root is None else Path(root)
    programs = set()
    with canonical_path(root_path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError(
            f"expected one canonical program for {TASK_ID}, found {len(programs)}"
        )
    return programs.pop()


def _derive_alternative_program(source: str, connection_axes: Any) -> str:
    """Derive one alternate source from two unique, exact canonical edit points."""
    setting = validate_setting(connection_axes)
    if setting == DEFAULT_SETTING:
        return source
    for name, fragment in (
        ("horizontal binding", _HORIZONTAL_BINDING),
        ("vertical result", _VERTICAL_RESULT),
    ):
        count = source.count(fragment)
        if count != 1:
            raise ValueError(
                f"canonical {name} edit point is absent or ambiguous (count={count})"
            )
    if setting == "horizontal":
        return source.replace(_VERTICAL_RESULT, "        acc2)", 1)
    return source.replace(_HORIZONTAL_BINDING, "             (acc2 acc))", 1)


def racket_program(
    connection_axes: Any, *, root: Path | str | None = None
) -> str:
    setting = validate_setting(connection_axes)
    source = canonical_program(root=root)
    if setting == DEFAULT_SETTING:
        return source
    return _derive_alternative_program(source, setting)


def surviving_settings(demonstrations: Iterable[dict[str, Any]]) -> list[str]:
    pairs = list(demonstrations)
    if not pairs:
        raise ValueError("at least one demonstration is required")
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise ValueError(f"demonstration {index} must contain input and output")
    return [
        setting
        for setting in SETTINGS
        if all(
            apply_python(pair["input"], setting) == pair["output"]
            for pair in pairs
        )
    ]


def build_episode(
    seed: Any,
    *,
    connection_axes: Any | None = None,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build a deterministic private episode with one fixed hidden rule setting."""
    seed = _validate_nonnegative_int(seed, "seed")
    demo_count = _validate_count(demo_count, "demo_count")
    query_count = _validate_count(query_count, "query_count")
    setting = choose_setting(seed, connection_axes)
    total = demo_count + query_count
    if total > 2 * MAX_PAIR_COUNT:
        raise ValueError(f"total pair count must be at most {2 * MAX_PAIR_COUNT}")

    pairs: list[dict[str, Any]] = []
    seen: set[bytes] = set()
    candidate_index = 0
    attempt_limit = max(64, total * 8)
    while len(pairs) < total and candidate_index < attempt_limit:
        grid = build_input(seed, candidate_index)
        visible = json.dumps(grid, separators=(",", ":")).encode("utf-8")
        if visible not in seen:
            seen.add(visible)
            pairs.append(
                {
                    "input": grid,
                    "output": apply_python(grid, setting),
                    "sample_index": candidate_index,
                }
            )
        candidate_index += 1
    if len(pairs) != total:
        raise RuntimeError(
            f"could produce only {len(pairs)} distinct inputs for requested {total} pairs"
        )

    train = pairs[:demo_count]
    test = pairs[demo_count:]
    survivors = surviving_settings(train)
    if survivors != [setting]:
        raise RuntimeError(
            f"demonstrations do not uniquely identify {setting!r}; survivors={survivors!r}"
        )

    return {
        "schema": f"{TASK_ID}-connection-axes-private-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "difficulty": episode_difficulty(seed),
        "parameter": {
            "name": PARAMETER_NAME,
            "value": setting,
            "default": DEFAULT_SETTING,
        },
        "counts": {"demonstrations": demo_count, "queries": query_count},
        "racket_program": racket_program(setting),
        "train": train,
        "test": test,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible demonstrations and unlabeled query inputs."""
    return json.loads(public_challenge_bytes(episode).decode("utf-8"))


def public_identifier(episode: dict[str, Any]) -> str:
    """Return an opaque filename derived only from exact visible challenge bytes."""
    return f"episode-{public_challenge_id(episode)}.json"
