"""Isolated episode-level edge-policy prototype for ARC task a76216bfa3e8.

The selected production generator and canonical Racket authority remain
unchanged.  One hidden ``edge_policy`` setting is chosen once per episode:

* ``clip`` (canonical/default): stamp the marker into matching partial terminal
  cells, clipping marker pixels that fall outside the cell.
* ``full_only``: stamp only into matching full 3x3 destination cells.

Both settings preserve lattice parsing, marker extraction, exact marker shape,
and the source row-and-column parity selector.  The alternative changes only
whether partial terminal cells are lawful destinations.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from puzzle_generators.base import stable_rng
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "a76216bfa3e8"
PROTOTYPE_VERSION = "1.0.0"
PARAMETER_NAME = "edge_policy"
SETTINGS = ("clip", "full_only")
DEFAULT_SETTING = "clip"
DEFAULT_DEMO_COUNT = 4
DEFAULT_QUERY_COUNT = 4
MAX_PAIR_COUNT = 16
PARAMETER_SPEC = {
    PARAMETER_NAME: {
        "type": "enum[str]",
        "allowed": list(SETTINGS),
        "default": DEFAULT_SETTING,
        "chosen": "once per episode from the deterministic episode seed",
        "input_constraints": (
            "selected-family lattice inputs with odd-parity terminal 2x2 cells; "
            "every retained pair makes clip and full_only disagree"
        ),
    }
}

_PARENT = None

# This exact fragment occurs once in the canonical authority.  The alternative
# adds a structural full-cell condition while leaving every other operation
# byte-for-byte inherited from the canonical source.
_CANONICAL_GUARD = """#:when (and (= (modulo cr 2) (modulo (first marker) 2))
                             (= (modulo cc 2)
                                (modulo (second marker) 2))))"""
_FULL_ONLY_GUARD = """#:when (and (= (modulo cr 2) (modulo (first marker) 2))
                             (= (modulo cc 2)
                                (modulo (second marker) 2))
                             ;; full 3x3 destination cells only
                             (= (- (second (nth row-spans cr))
                                   (first (nth row-spans cr))) 2)
                             (= (- (second (nth col-spans cc))
                                   (first (nth col-spans cc))) 2)))"""


def _root() -> Path:
    return find_root(__file__)


def _load_parent():
    global _PARENT
    if _PARENT is None:
        _PARENT, _, _ = load_selected_generator(TASK_ID, root=_root())
    return _PARENT


def _validate_nonnegative_int(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer (not bool)")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer (not bool)")
    if not 1 <= value <= MAX_PAIR_COUNT:
        raise ValueError(f"{name} must be in 1..{MAX_PAIR_COUNT}")
    return value


def validate_setting(value: Any) -> str:
    if type(value) is not str:
        raise TypeError(f"{PARAMETER_NAME} must be a string")
    if value not in SETTINGS:
        raise ValueError(f"unknown {PARAMETER_NAME}={value!r}; expected one of {SETTINGS}")
    return value


def choose_parameters(seed: Any) -> dict[str, str]:
    """Choose one hidden rule setting for the entire episode."""
    seed = _validate_nonnegative_int(seed, "episode seed")
    rng = stable_rng(seed, f"{TASK_ID}|parametric-rule", PROTOTYPE_VERSION)
    return {PARAMETER_NAME: SETTINGS[rng.randrange(len(SETTINGS))]}


def episode_difficulty(seed: Any) -> str:
    seed = _validate_nonnegative_int(seed, "episode seed")
    return ("easy", "medium", "hard")[(seed // len(SETTINGS)) % 3]


def build_input(episode_seed: Any, pair_index: Any) -> list[list[int]]:
    """Build a lawful lattice scene that distinguishes both edge policies."""
    episode_seed = _validate_nonnegative_int(episode_seed, "episode seed")
    pair_index = _validate_nonnegative_int(pair_index, "pair_index")
    if pair_index >= 8 * MAX_PAIR_COUNT:
        raise ValueError(f"pair_index must be below {8 * MAX_PAIR_COUNT}")

    parent = _load_parent()
    rng = stable_rng(
        episode_seed,
        f"{TASK_ID}|edge-policy-input|pair={pair_index}",
        PROTOTYPE_VERSION,
    )
    input_seed = rng.randrange(2**31)
    grid = parent.generate(
        input_seed,
        pair_index,
        difficulty=episode_difficulty(episode_seed),
        n_cell_rows=8,
        n_cell_cols=8,
        tail_h=2,
        tail_w=2,
        marker_row_parity=1,
        marker_col_parity=1,
    )
    findings = parent.self_check(grid)
    if findings:
        raise RuntimeError("selected generator returned an unlawful input: " + "; ".join(findings))
    if parent.rule_mirror(grid) == parent.rival_skip_partial_cells(grid):
        raise RuntimeError("constructed input does not distinguish edge policies")
    return grid


def apply_python(grid: list[list[int]], edge_policy: Any) -> list[list[int]]:
    """Independent assertion mirror; retained labels are executed by Racket."""
    setting = validate_setting(edge_policy)
    parent = _load_parent()
    findings = parent.self_check(grid)
    if findings:
        raise ValueError("invalid selected-family input: " + "; ".join(findings))
    if setting == "clip":
        return parent.rule_mirror(grid)
    return parent.rival_skip_partial_cells(grid)


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
        raise ValueError(f"expected one canonical program for {TASK_ID}, found {len(programs)}")
    return programs.pop()


def racket_program(edge_policy: Any, *, root: Path | str | None = None) -> str:
    """Materialize the exact Racket authority for one edge-policy setting."""
    setting = validate_setting(edge_policy)
    source = canonical_program(root=root)
    if setting == DEFAULT_SETTING:
        return source
    count = source.count(_CANONICAL_GUARD)
    if count != 1:
        raise ValueError(f"canonical edge-policy edit point is absent or ambiguous (count={count})")
    return source.replace(_CANONICAL_GUARD, _FULL_ONLY_GUARD, 1)


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
        if all(apply_python(pair["input"], setting) == pair["output"] for pair in pairs)
    ]


def build_episode(
    seed: Any,
    *,
    edge_policy: Any | None = None,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
) -> dict[str, Any]:
    """Build a private fixed-setting episode with separate demo/query counts."""
    seed = _validate_nonnegative_int(seed, "episode seed")
    demo_count = _validate_count(demo_count, "demo_count")
    query_count = _validate_count(query_count, "query_count")
    if demo_count + query_count > 2 * MAX_PAIR_COUNT:
        raise ValueError(f"total pair count must be at most {2 * MAX_PAIR_COUNT}")
    setting = (
        choose_parameters(seed)[PARAMETER_NAME]
        if edge_policy is None
        else validate_setting(edge_policy)
    )

    pairs: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    candidate = 0
    attempt_limit = max(64, 8 * (demo_count + query_count))
    while len(pairs) < demo_count + query_count and candidate < attempt_limit:
        grid = build_input(seed, candidate)
        frozen = tuple(tuple(row) for row in grid)
        if frozen not in seen:
            seen.add(frozen)
            pairs.append(
                {
                    "input": grid,
                    "output": apply_python(grid, setting),
                    "sample_index": candidate,
                }
            )
        candidate += 1
    if len(pairs) != demo_count + query_count:
        raise RuntimeError(
            f"could produce only {len(pairs)} distinct inputs for "
            f"{demo_count + query_count} requested pairs"
        )

    train = pairs[:demo_count]
    test = pairs[demo_count:]
    survivors = surviving_settings(train)
    if survivors != [setting]:
        raise RuntimeError(
            f"demonstrations do not uniquely identify {setting!r}; survivors={survivors!r}"
        )
    return {
        "schema": f"{TASK_ID}-edge-policy-private-episode-v1",
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


def grid_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"'({rows})"


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project to visible demos and unlabeled query inputs only."""
    value = json.loads(public_challenge_bytes(episode).decode("utf-8"))
    return {"train": value["train"], "test": value["test"]}


def public_identifier(episode: dict[str, Any]) -> str:
    """Opaque filename derived only from exact visible challenge bytes."""
    return f"challenge-{public_challenge_id(episode)}.json"
