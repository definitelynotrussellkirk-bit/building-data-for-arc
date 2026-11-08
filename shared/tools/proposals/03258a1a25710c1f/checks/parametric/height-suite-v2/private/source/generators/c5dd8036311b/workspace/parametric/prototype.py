"""Episode-fixed column heights for the original 72a961c9 ARC family.

This is a proposed, task-local prototype.  Labels come from real Racket, not
from a Python mirror.  The default materializes the exact canonical program.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
from itertools import product
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root, normalize_grid


TASK_ID = "c5dd8036311b"
PROTOTYPE_VERSION = "1.0.0"
HEIGHT_VALUES = (2, 3, 4, 5)
PARAMETER_SPEC = {
    "height_8": {"allowed": list(HEIGHT_VALUES), "default": 3},
    "height_2": {"allowed": list(HEIGHT_VALUES), "default": 4},
}


def sha256(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


@dataclass(frozen=True)
class Parameters:
    height_8: int = 3
    height_2: int = 4

    def __post_init__(self):
        for name, value in self.as_dict().items():
            if type(value) is not int or value not in HEIGHT_VALUES:
                raise ValueError(f"{name} must be a literal integer in {HEIGHT_VALUES}, got {value!r}")

    def as_dict(self) -> dict[str, int]:
        return {"height_8": self.height_8, "height_2": self.height_2}

    def key(self) -> str:
        return f"h8_{self.height_8}_h2_{self.height_2}"


def all_parameters() -> tuple[Parameters, ...]:
    return tuple(Parameters(a, b) for a, b in product(HEIGHT_VALUES, repeat=2))


def _integer(value: Any, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be a literal integer")
    return value


def _rng(seed: int, domain: str) -> random.Random:
    _integer(seed, "seed")
    return random.Random(int(sha256(f"{TASK_ID}:{PROTOTYPE_VERSION}:{domain}:{seed}"), 16))


def choose_parameters(seed: int) -> Parameters:
    """Choose once for the whole episode, independent of the input RNG."""
    rng = _rng(seed, "episode-rule")
    return Parameters(rng.choice(HEIGHT_VALUES), rng.choice(HEIGHT_VALUES))


def canonical_program(root: Path | None = None) -> str:
    """Read the exact selected task through the portable canonical path helper."""
    root = root if root is not None else find_root(__file__)
    records = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    records.append(row)
    if len(records) != 1:
        raise ValueError(f"expected one canonical {TASK_ID} record, got {len(records)}")
    program = records[0]["program_solution"]
    if not isinstance(program, str) or not program.startswith("(rule!"):
        raise ValueError("expected the canonical rule! program")
    return program


def racket_program(parameters: Parameters = Parameters(), *, root: Path | None = None) -> str:
    """Change only the two column-height constants in the canonical Racket.

    The exact template anchor is checked, so a future canonical rewrite fails
    visibly instead of silently changing a different number or stale rule.
    """
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be a validated Parameters value")
    program = canonical_program(root)
    anchor = "(col-h (if (= color 8) 3 4))"
    if program.count(anchor) != 1:
        raise ValueError("canonical height expression changed; review prototype materialization")
    return program.replace(anchor, f"(col-h (if (= color 8) {parameters.height_8} {parameters.height_2}))")


def grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(map(tuple, grid))


def validate_input(grid: Any, parameters: Parameters, *, require_both: bool = False) -> list[str]:
    """Check the supported family; labels may preserve broader canonical behavior."""
    try:
        grid = normalize_grid(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    errors = []
    if len(grid) > 30 or len(grid[0]) > 30:
        errors.append("ARC grids must be at most 30 by 30")
    bar_rows = [r for r, row in enumerate(grid) if 1 in row]
    if len(bar_rows) != 1:
        return errors + ["exactly one row containing color 1 is required"]
    bar = bar_rows[0]
    if any(v not in (1, 2, 8) for v in grid[bar]):
        errors.append("bar must span its row with colors 1, 2, and 8 only")
    if any(v != 0 for r, row in enumerate(grid) if r != bar for v in row):
        errors.append("all non-bar input cells must be zero")
    markers = {v for v in grid[bar] if v in (2, 8)}
    if not markers:
        errors.append("at least one marker is required")
    if require_both and markers != {2, 8}:
        errors.append("this teaching episode requires both marker colors in every pair")
    required = max((parameters.height_8 if v == 8 else parameters.height_2 for v in markers), default=0)
    if bar < required:
        errors.append(f"bar row {bar} clips a height-{required} column")
    return errors


def build_input(seed: int, pair_index: int) -> list[list[int]]:
    """Vary geometry without using the hidden parameters.

    All allowed settings are lawful on every generated input.  Each pair has
    both marker types, so holding out any one pair retains complete evidence.
    Width slots keep the four default pairs distinct for every seed.
    """
    _integer(pair_index, "pair_index")
    if not 0 <= pair_index < 8:
        raise ValueError("pair_index must be in 0..7")
    rng = _rng(seed, f"input-{pair_index}")
    width = 7 + pair_index
    bar_row = rng.randint(max(HEIGHT_VALUES), 9)
    height = bar_row + rng.randint(2, 5)
    grid = [[0] * width for _ in range(height)]
    grid[bar_row] = [1] * width
    n8, n2 = ((1, 1), (1, 2), (2, 1), (2, 2))[pair_index % 4]
    columns = rng.sample(range(width), n8 + n2)
    for col, color in zip(columns, [8] * n8 + [2] * n2, strict=True):
        grid[bar_row][col] = color
    errors = validate_input(grid, Parameters(5, 5), require_both=True)
    if errors:
        raise AssertionError("; ".join(errors))
    return grid


def execute(bridge: Any, program: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute one materialized rule with the included protected Racket bridge."""
    normalized = normalize_grid(grid)
    if not program.startswith("(rule!") or not program.endswith(")"):
        raise ValueError("expected a single rule! wrapper")
    # rule! is a REPL directive.  The bridge executes its callable body directly.
    callable_source = program[len("(rule!"):-1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("expected the reviewed lambda rule template")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"
    return normalize_grid(bridge.eval_text(f"({callable_source} {literal})"))


def make_episode(seed: int, *, bridge: Any, root: Path | None = None,
                 parameters: Parameters | None = None, n_train: int = 3) -> dict[str, Any]:
    _integer(n_train, "n_train")
    if not 1 <= n_train <= 7:
        raise ValueError("n_train must be in 1..7")
    selected = parameters if parameters is not None else choose_parameters(seed)
    program = racket_program(selected, root=root)
    pairs = []
    for index in range(n_train + 1):
        grid = build_input(seed, index)
        pairs.append({"input": grid, "output": execute(bridge, program, grid)})
    return {
        "schema": "c5dd8036311b-parametric-episode-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter_selection": "explicit" if parameters is not None else "seeded-once-per-episode",
        "parameters": selected.as_dict(),
        "program": program,
        "program_sha256": sha256(program),
        "n_train": n_train,
        "pairs": pairs,
    }


def public_challenge(episode: dict[str, Any], *, query_index: int | None = None) -> dict[str, Any]:
    """Project only visible demonstrations and one masked query; no metadata."""
    pairs = episode["pairs"]
    query_index = len(pairs) - 1 if query_index is None else query_index
    if type(query_index) is not int or not 0 <= query_index < len(pairs):
        raise ValueError("query_index must identify an existing pair")
    return {
        "train": [deepcopy(pair) for index, pair in enumerate(pairs) if index != query_index],
        "test": [{"input": deepcopy(pairs[query_index]["input"])}],
    }


def check_identifiability(pairs: list[dict[str, Any]], selected: Parameters,
                         predictions: dict[Parameters, list[list[list[int]]]]) -> dict[str, Any]:
    """Check every declared setting and every one-query holdout.

    Caller must supply actual Racket predictions, retained separately as
    evidence.  A surviving answer-equivalent setting is reported distinctly
    from a setting that fits demonstrations but changes the query answer.
    """
    if len(pairs) < 2 or set(predictions) != set(all_parameters()):
        raise ValueError("at least two pairs and all 16 settings are required")
    if any(len(outputs) != len(pairs) for outputs in predictions.values()):
        raise ValueError("each setting must predict every pair")
    expected = [pair["output"] for pair in pairs]
    if predictions[selected] != expected:
        raise ValueError("selected setting does not reproduce retained labels")
    rotations = []
    for query in range(len(pairs)):
        demos = [i for i in range(len(pairs)) if i != query]
        survivors = []
        ambiguities = []
        eliminated = []
        for setting in all_parameters():
            outputs = predictions[setting]
            mismatch = next((i for i in demos if outputs[i] != expected[i]), None)
            if mismatch is None:
                survivors.append(setting.as_dict())
                if outputs[query] != expected[query]:
                    ambiguities.append({"parameters": setting.as_dict(), "query_prediction": outputs[query]})
            else:
                eliminated.append({"parameters": setting.as_dict(), "distinguishing_demo_index": mismatch})
        rotations.append({
            "query_index": query,
            "demonstration_indexes": demos,
            "surviving_settings": survivors,
            "query_ambiguities": ambiguities,
            "eliminated_settings": eliminated,
            "identified": survivors == [selected.as_dict()],
        })
    return {
        "declared_setting_count": len(predictions),
        "identified_all_rotations": all(row["identified"] for row in rotations),
        "ambiguity_count": sum(len(row["query_ambiguities"]) for row in rotations),
        "rotations": rotations,
        "limits": "Finite 16-setting family check; not universal identification against arbitrary programs.",
    }
