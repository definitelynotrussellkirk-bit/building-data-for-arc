#!/usr/bin/env python3
"""Task-local prototype for a fixed-per-episode projection edge mode.

This module is deliberately separate from the selected production generator
and canonical authority.  It materializes two complete rules:

* ``near`` — the byte-exact canonical/default behavior.
* ``far`` — aligned colored sources paint the opposite bounding-box edge.

Both settings preserve the cyan object, source cells, color roles, and the rule
that diagonal sources are ignored.  The mode is chosen once from the episode
seed and shared by every demonstration and query.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
from pathlib import Path
import shutil
import sys
from typing import Any, Callable

from reviewer_support import canonical_path, find_root, load_selected_generator


TASK_ID = "064e439acd2d"
ALLOWED_EDGE_MODES = ("near", "far")
DEFAULT_EDGE_MODE = "near"
PROTOTYPE_VERSION = "1.0.0"
DEMO_INDICES = (0, 2, 4, 6)
QUERY_INDEX = 8
DIFFICULTY = "medium"
PROTOTYPE_DIR = Path(__file__).resolve().parent
RULE_DIR = PROTOTYPE_DIR / "racket"

_HORIZONTAL_NEAR = """(if (< c cmin)
                               (set-cell acc r cmin color)
                               (set-cell acc r cmax color)))"""
_HORIZONTAL_FAR = """(if (< c cmin)
                               (set-cell acc r cmax color)
                               (set-cell acc r cmin color)))"""
_VERTICAL_NEAR = """(if (< r rmin)
                               (set-cell acc rmin c color)
                               (set-cell acc rmax c color)))"""
_VERTICAL_FAR = """(if (< r rmin)
                               (set-cell acc rmax c color)
                               (set-cell acc rmin c color)))"""


def _validate_edge_mode(edge_mode: str) -> str:
    if not isinstance(edge_mode, str) or edge_mode not in ALLOWED_EDGE_MODES:
        raise ValueError(
            f"edge_mode must be one of {ALLOWED_EDGE_MODES}, got {edge_mode!r}"
        )
    return edge_mode


def choose_edge_mode(seed: int) -> str:
    """Choose one hidden setting for an entire episode."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return ALLOWED_EDGE_MODES[seed % len(ALLOWED_EDGE_MODES)]


def normalized_hash(source: str) -> str:
    """Return the repository's 12-hex whitespace-normalized rule hash."""
    return hashlib.sha256(" ".join(source.split()).encode("utf-8")).hexdigest()[:12]


def _canonical_source(*, root: Path) -> str:
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                return str(row["program_solution"])
    raise FileNotFoundError(f"{TASK_ID}: canonical program_solution not found")


def _far_source(canonical: str) -> str:
    for near, far, label in (
        (_HORIZONTAL_NEAR, _HORIZONTAL_FAR, "horizontal"),
        (_VERTICAL_NEAR, _VERTICAL_FAR, "vertical"),
    ):
        count = canonical.count(near)
        if count != 1:
            raise ValueError(
                f"expected exactly one canonical {label} target clause, found {count}"
            )
        canonical = canonical.replace(near, far)
    return canonical


def racket_source(edge_mode: str, *, root: Path | str) -> str:
    """Materialize the complete Racket rule for one bounded parameter value."""
    mode = _validate_edge_mode(edge_mode)
    canonical = _canonical_source(root=Path(root))
    return canonical if mode == "near" else _far_source(canonical)


def racket_sha256(edge_mode: str, *, root: Path | str) -> str:
    return hashlib.sha256(
        racket_source(edge_mode, root=root).encode("utf-8")
    ).hexdigest()


def rule_path(edge_mode: str) -> Path:
    return RULE_DIR / f"{_validate_edge_mode(edge_mode)}.rkt"


def materialize_rules(*, root: Path | str) -> dict[str, str]:
    """Write exact complete sources and return their raw SHA-256 hashes."""
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for mode in ALLOWED_EDGE_MODES:
        source = racket_source(mode, root=root)
        rule_path(mode).write_text(source, encoding="utf-8")
        hashes[mode] = hashlib.sha256(source.encode("utf-8")).hexdigest()
    return hashes


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty rectangular list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def python_transform(grid: list[list[int]], edge_mode: str) -> list[list[int]]:
    """Independent assertion mirror; Racket remains label authority."""
    _validate_grid(grid)
    mode = _validate_edge_mode(edge_mode)
    cyan = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not cyan:
        raise ValueError("edge-mode prototype requires at least one cyan cell")
    rmin = min(r for r, _ in cyan)
    rmax = max(r for r, _ in cyan)
    cmin = min(c for _, c in cyan)
    cmax = max(c for _, c in cyan)
    output = copy.deepcopy(grid)
    # Match canonical color order and row-major find-color order exactly.
    for color in (1, 2, 3, 4, 5, 6, 7, 9):
        dots = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        for r, c in dots:
            if rmin <= r <= rmax:
                if mode == "near":
                    target_c = cmin if c < cmin else cmax
                else:
                    target_c = cmax if c < cmin else cmin
                output[r][target_c] = color
            elif cmin <= c <= cmax:
                if mode == "near":
                    target_r = rmin if r < rmin else rmax
                else:
                    target_r = rmax if r < rmin else rmin
                output[target_r][c] = color
    return output


def _racket_literal(value: Any) -> str:
    if isinstance(value, list):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is not int or not 0 <= value <= 9:
        raise ValueError(f"not an ARC literal: {value!r}")
    return str(value)


def _callable_racket_source(source: str) -> str:
    """Peel the selected plain ``(rule! <lambda>)`` wrapper."""
    stripped = source.strip()
    prefix = "(rule! "
    if not stripped.startswith(prefix) or not stripped.endswith(")"):
        raise ValueError("expected a plain (rule! <lambda>) program")
    callable_source = stripped[len(prefix):-1].strip()
    if not callable_source.startswith("(lambda "):
        raise ValueError("prototype rule body must be a lambda")
    return callable_source


def _racket_outputs(source: str, grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketBridge

    callable_source = _callable_racket_source(source)
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define prototype-rule {callable_source})")
        result = bridge.eval_text(f"(map prototype-rule '{_racket_literal(grids)})")
    if not isinstance(result, list) or len(result) != len(grids):
        raise RuntimeError("unexpected Racket result shape")
    return result


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_episode(*, root: Path | str, seed: int) -> dict[str, Any]:
    """Build four labelled demonstrations and one labelled query."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    mode = choose_edge_mode(seed)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=Path(root))
    indexed_inputs = [
        (
            index,
            module.generate(seed, index, difficulty=DIFFICULTY),
        )
        for index in (*DEMO_INDICES, QUERY_INDEX)
    ]
    pairs = [
        {
            "sample_index": index,
            "input": copy.deepcopy(grid),
            "output": python_transform(grid, mode),
        }
        for index, grid in indexed_inputs
    ]
    return {
        "schema": "arcpuzzles-parametric-edge-mode-episode-v1",
        "status": "prototype",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "difficulty": DIFFICULTY,
        "parameter": {"edge_mode": mode},
        "selected_generator_path": str(source_path.relative_to(Path(root))),
        "selected_generator_sha256": source_sha,
        "train": pairs[:-1],
        "test": pairs[-1:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Public presentation: labelled demos, unlabelled query, no hidden rule."""
    return {
        "schema": "arcpuzzles-parametric-edge-mode-public-v1",
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def _racket_runtime_metadata() -> dict[str, Any]:
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError(
            "racket executable not found; run through review.py run or run_with_racket.py"
        )
    path = Path(executable).resolve()
    return {
        "executable": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build_report(
    *,
    root: Path | str,
    seeds: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Execute both exact Racket settings and retain bounded evidence."""
    root = Path(root).resolve()
    seeds = dict(seeds or {"near": 18, "far": 19})
    if set(seeds) != set(ALLOWED_EDGE_MODES):
        raise ValueError(f"seeds must have exactly keys {ALLOWED_EDGE_MODES}")
    for mode, seed in seeds.items():
        if choose_edge_mode(seed) != mode:
            raise ValueError(f"seed {seed} selects {choose_edge_mode(seed)!r}, not {mode!r}")

    module, selected_source_path, selected_source_sha = load_selected_generator(
        TASK_ID, root=root
    )
    sources = {mode: racket_source(mode, root=root) for mode in ALLOWED_EDGE_MODES}
    if sources[DEFAULT_EDGE_MODE] != _canonical_source(root=root):
        raise AssertionError("near setting is not byte-exact canonical source")
    if normalized_hash(sources[DEFAULT_EDGE_MODE]) != module.RULE_HASH:
        raise AssertionError("default prototype no longer matches selected RULE_HASH")
    for mode, source in sources.items():
        retained = rule_path(mode).read_text(encoding="utf-8")
        if retained != source:
            raise AssertionError(f"retained {mode}.rkt differs from materialized rule")

    episodes: dict[str, Any] = {}
    public: dict[str, Any] = {}
    all_pairs_disagree = True
    for mode in ALLOWED_EDGE_MODES:
        alternative = "far" if mode == "near" else "near"
        episode = build_episode(root=root, seed=seeds[mode])
        pairs = [*episode["train"], *episode["test"]]
        inputs = [pair["input"] for pair in pairs]
        racket_outputs = _racket_outputs(sources[mode], inputs)
        alternative_outputs = _racket_outputs(sources[alternative], inputs)
        python_outputs = [python_transform(grid, mode) for grid in inputs]
        if racket_outputs != python_outputs:
            raise AssertionError(f"{mode}: Python/Racket output mismatch")

        executed_pairs = []
        for offset, (pair, actual, rival) in enumerate(
            zip(pairs, racket_outputs, alternative_outputs)
        ):
            if actual != pair["output"]:
                raise AssertionError(f"{mode}: episode label mismatch at pair {offset}")
            disagreement = actual != rival
            all_pairs_disagree &= disagreement
            split = "train" if offset < len(episode["train"]) else "test"
            pair_index = offset if split == "train" else offset - len(episode["train"])
            executed_pairs.append(
                {
                    "split": split,
                    "pair_index": pair_index,
                    "sample_index": pair["sample_index"],
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_edge_mode": alternative,
                    "alternative_racket_output": rival,
                    "settings_disagree": disagreement,
                    "input_sha256": _digest(pair["input"]),
                    "output_sha256": _digest(actual),
                }
            )
        demo_disagreements = [
            row["settings_disagree"] for row in executed_pairs if row["split"] == "train"
        ]
        query_disagreements = [
            row["settings_disagree"] for row in executed_pairs if row["split"] == "test"
        ]
        if not demo_disagreements or not all(demo_disagreements):
            raise AssertionError(f"{mode}: not every retained demo refutes {alternative}")
        if not query_disagreements or not all(query_disagreements):
            raise AssertionError(f"{mode}: retained query does not require the parameter")

        episodes[mode] = {
            "edge_mode": mode,
            "is_canonical_default": mode == DEFAULT_EDGE_MODE,
            "seed": seeds[mode],
            "difficulty": DIFFICULTY,
            "demonstration_indices": list(DEMO_INDICES),
            "query_index": QUERY_INDEX,
            "racket_path": str(rule_path(mode).relative_to(root)),
            "racket_text": sources[mode],
            "racket_sha256": hashlib.sha256(sources[mode].encode("utf-8")).hexdigest(),
            "racket_rule_hash": normalized_hash(sources[mode]),
            "episode": episode,
            "executed_pairs": executed_pairs,
            "all_pairs_match_python_and_racket": True,
            "every_demo_refutes_alternative_setting": all(demo_disagreements),
            "query_requires_setting": all(query_disagreements),
        }
        public[mode] = public_challenge(episode)

    if not all_pairs_disagree:
        raise AssertionError("at least one retained pair does not distinguish edge modes")

    prototype_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "arcpuzzles-parametric-edge-mode-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "parameter": {
            "name": "edge_mode",
            "allowed_values": list(ALLOWED_EDGE_MODES),
            "canonical_default": DEFAULT_EDGE_MODE,
            "selection": "ALLOWED_EDGE_MODES[seed % 2], once per episode",
            "input_constraints": (
                "Same as selected generator: one solid cyan line/rectangle, exterior "
                "colored sources with distinct aligned targets, optional diagonal decoy."
            ),
        },
        "invariants_across_settings": [
            "cyan region geometry and cells are preserved except painted targets",
            "source cells remain in place",
            "source colors are copied without recoloring",
            "diagonal sources remain ignored",
            "only near versus opposite bounding-box target edge changes",
        ],
        "prototype_source_path": str(Path(__file__).resolve().relative_to(root)),
        "prototype_source_sha256": prototype_sha,
        "selected_generator_path": str(selected_source_path.relative_to(root)),
        "selected_generator_sha256": selected_source_sha,
        "racket_runtime": _racket_runtime_metadata(),
        "settings": episodes,
        "public_challenges": public,
        "all_retained_pairs_distinguish_settings": all_pairs_disagree,
        "limits": [
            "Bounded evidence for near seed 18 and far seed 19, not production approval.",
            "The selected generator and canonical Racket authority remain fixed to near.",
            "The retained demonstrations distinguish only the declared near/far parameter rival.",
            "Projection-target collisions remain outside the selected generator's declared domain.",
        ],
    }



# ---------------------------------------------------------------------------
# Native promotion API and deterministic matched episode bank.
# ---------------------------------------------------------------------------

DEFAULT = {"edge_mode": DEFAULT_EDGE_MODE}
PARAMETERS = {"edge_mode": list(ALLOWED_EDGE_MODES)}
SETTINGS = [{"edge_mode": mode} for mode in ALLOWED_EDGE_MODES]
REPO = PROTOTYPE_DIR.parents[3]
CANONICAL_FILE = PROTOTYPE_DIR / "canonical.rkt"

# Shape, cyan bounds, number of aligned sources, number of diagonal decoys.
# The first two demonstrations deliberately cover a rectangle and a line so
# two visible examples separate the declared settings and the retained rivals.
_DEMO_PROFILES = (
    ((9, 11), (2, 6, 3, 7), 8, 2),
    ((10, 12), (5, 5, 3, 8), 6, 2),
    ((11, 13), (2, 8, 6, 6), 7, 2),
    ((12, 16), (3, 8, 4, 11), 10, 2),
    ((14, 18), (1, 10, 5, 14), 12, 3),
    ((16, 21), (4, 12, 3, 16), 14, 3),
)
_QUERY_PROFILES = (
    ((12, 15), (3, 8, 4, 10), 10, 2),
    ((18, 20), (2, 14, 5, 15), 14, 3),
    ((24, 27), (5, 18, 4, 21), 18, 4),
    ((30, 30), (6, 23, 5, 24), 24, 4),
)
_SOURCE_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_RIVAL_NAMES = (
    "border_only",
    "project_diagonal_to_corner",
    "rectangle_only",
    "one_per_color",
    "move_sources",
    "horizontal_projection_only",
    "vertical_projection_only",
    "ignore_touching_sources",
)


def _integer(value: Any, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"edge_mode"}:
        raise ValueError("settings must name exactly edge_mode")
    mode = settings["edge_mode"]
    if type(mode) is not str or mode not in ALLOWED_EDGE_MODES:
        raise ValueError("edge_mode must be 'near' or 'far'")
    return {"edge_mode": mode}


def _color_grid(grid: Any) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _grid(grid: Any) -> list[list[int]]:
    value = _color_grid(grid)
    if not any(cell == 8 for row in value for cell in row):
        raise ValueError("projection-edge inputs require a cyan region")
    return value


def program(settings: Any) -> str:
    chosen = _settings(settings)
    if not CANONICAL_FILE.is_file():
        raise FileNotFoundError(f"missing exact canonical source: {CANONICAL_FILE}")
    canonical = CANONICAL_FILE.read_text(encoding="utf-8")
    live = _canonical_source(root=REPO)
    if canonical != live:
        raise ValueError("pinned canonical.rkt differs from the selected catalog program")
    return canonical if chosen["edge_mode"] == "near" else _far_source(canonical)


def transform(grid: Any, settings: Any) -> list[list[int]]:
    value = _grid(grid)
    return python_transform(value, _settings(settings)["edge_mode"])


def _stable_rng(seed: int, domain: str, index: int) -> random.Random:
    token = hashlib.sha256(
        json.dumps([TASK_ID, "edge-mode-native-v2", seed, domain, index], separators=(",", ":")).encode()
    ).hexdigest()
    return random.Random(int(token, 16))


def _candidate_sources(
    height: int,
    width: int,
    bounds: tuple[int, int, int, int],
    seed: int,
    profile_index: int,
) -> list[tuple[int, int, str, tuple[int, int], tuple[int, int]]]:
    rmin, rmax, cmin, cmax = bounds
    rows = [rmin] if rmin == rmax else list(range(rmin + 1, rmax))
    cols = [cmin] if cmin == cmax else list(range(cmin + 1, cmax))
    if not rows:
        rows = list(range(rmin, rmax + 1))
    if not cols:
        cols = list(range(cmin, cmax + 1))

    by_side: dict[str, list[tuple[int, int, str, tuple[int, int], tuple[int, int]]]] = {
        side: [] for side in ("left", "top", "right", "bottom")
    }
    for offset, row in enumerate(rows):
        left_choices = list(dict.fromkeys(c for c in (cmin - 1, 0, cmin - 2) if 0 <= c < cmin))
        right_choices = list(dict.fromkeys(c for c in (cmax + 1, width - 1, cmax + 2) if cmax < c < width))
        left = left_choices[(seed + profile_index + offset) % len(left_choices)]
        right = right_choices[(seed * 3 + profile_index + offset) % len(right_choices)]
        by_side["left"].append((row, left, "left", (row, cmin), (row, cmax)))
        by_side["right"].append((row, right, "right", (row, cmax), (row, cmin)))
    for offset, col in enumerate(cols):
        top_choices = list(dict.fromkeys(r for r in (rmin - 1, 0, rmin - 2) if 0 <= r < rmin))
        bottom_choices = list(dict.fromkeys(r for r in (rmax + 1, height - 1, rmax + 2) if rmax < r < height))
        top = top_choices[(seed * 5 + profile_index + offset) % len(top_choices)]
        bottom = bottom_choices[(seed * 7 + profile_index + offset) % len(bottom_choices)]
        by_side["top"].append((top, col, "top", (rmin, col), (rmax, col)))
        by_side["bottom"].append((bottom, col, "bottom", (rmax, col), (rmin, col)))

    order = ("left", "top", "right", "bottom")
    candidates = []
    for offset in range(max(len(by_side[side]) for side in order)):
        for side in order:
            if offset < len(by_side[side]):
                candidates.append(by_side[side][offset])
    return candidates


def _scene(
    seed: int,
    index: int,
    *,
    query_slot: int | None = None,
) -> list[list[int]]:
    profiles = _QUERY_PROFILES if query_slot is not None else _DEMO_PROFILES
    slot = query_slot if query_slot is not None else index
    (height, width), bounds, source_count, decoy_count = profiles[slot]
    rmin, rmax, cmin, cmax = bounds
    grid = [[0] * width for _ in range(height)]
    for r in range(rmin, rmax + 1):
        for c in range(cmin, cmax + 1):
            grid[r][c] = 8

    candidates = _candidate_sources(height, width, bounds, seed, index)
    used_near: set[tuple[int, int]] = set()
    used_far: set[tuple[int, int]] = set()
    selected = []
    for candidate in candidates:
        _, _, _, near_target, far_target = candidate
        if near_target in used_near or far_target in used_far:
            continue
        selected.append(candidate)
        used_near.add(near_target)
        used_far.add(far_target)
        if len(selected) == source_count:
            break
    if len(selected) != source_count:
        raise RuntimeError(f"profile {slot} has only {len(selected)} collision-free sources")

    rng = _stable_rng(seed, "query" if query_slot is not None else "demo", index)
    shift = rng.randrange(len(_SOURCE_COLORS))
    palette = _SOURCE_COLORS[shift:] + _SOURCE_COLORS[:shift]
    for source_index, (r, c, _side, _near, _far) in enumerate(selected):
        color = palette[source_index % len(palette)]
        if source_index == 4:
            color = palette[0]  # one repeated color with two distinct targets
        grid[r][c] = color

    diagonal_candidates = (
        (max(0, rmin - 2), max(0, cmin - 2)),
        (max(0, rmin - 2), min(width - 1, cmax + 2)),
        (min(height - 1, rmax + 2), min(width - 1, cmax + 2)),
        (min(height - 1, rmax + 2), max(0, cmin - 2)),
    )
    placed = 0
    for offset, (r, c) in enumerate(diagonal_candidates):
        if placed == decoy_count:
            break
        if not (r < rmin or r > rmax) or not (c < cmin or c > cmax):
            continue
        if grid[r][c] != 0:
            continue
        grid[r][c] = palette[(source_count + offset) % len(palette)]
        placed += 1
    if placed != decoy_count:
        raise RuntimeError(f"profile {slot} could place only {placed} diagonal decoys")

    _validate_scene(grid)
    return grid


def _scene_geometry(grid: list[list[int]]) -> tuple[tuple[int, int, int, int], list[tuple[int, int, int]]]:
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if not cyan:
        raise ValueError("missing cyan region")
    bounds = (
        min(r for r, _ in cyan),
        max(r for r, _ in cyan),
        min(c for _, c in cyan),
        max(c for _, c in cyan),
    )
    dots = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    return bounds, dots


def _targets_for_source(
    r: int,
    c: int,
    bounds: tuple[int, int, int, int],
) -> tuple[tuple[int, int] | None, tuple[int, int] | None, str | None]:
    rmin, rmax, cmin, cmax = bounds
    if rmin <= r <= rmax:
        if c < cmin:
            return (r, cmin), (r, cmax), "horizontal"
        if c > cmax:
            return (r, cmax), (r, cmin), "horizontal"
    if cmin <= c <= cmax:
        if r < rmin:
            return (rmin, c), (rmax, c), "vertical"
        if r > rmax:
            return (rmax, c), (rmin, c), "vertical"
    return None, None, None


def _validate_scene(grid: list[list[int]]) -> None:
    _color_grid(grid)
    bounds, dots = _scene_geometry(grid)
    rmin, rmax, cmin, cmax = bounds
    cyan = {(r, c) for r in range(rmin, rmax + 1) for c in range(cmin, cmax + 1)}
    actual = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    if actual != cyan:
        raise ValueError("cyan region must be a solid line or rectangle")
    near_targets: set[tuple[int, int]] = set()
    far_targets: set[tuple[int, int]] = set()
    aligned = 0
    for r, c, _ in dots:
        if rmin <= r <= rmax and cmin <= c <= cmax:
            raise ValueError("colored source lies inside cyan region")
        near, far, _ = _targets_for_source(r, c, bounds)
        if near is None:
            continue
        aligned += 1
        if near in near_targets or far in far_targets:
            raise ValueError("projection target collision is outside the family grammar")
        near_targets.add(near)
        far_targets.add(far)
    if aligned < 4:
        raise ValueError("scene needs at least four aligned sources")


def _adjacent_to_bbox(r: int, c: int, bounds: tuple[int, int, int, int]) -> bool:
    rmin, rmax, cmin, cmax = bounds
    return (
        (rmin <= r <= rmax and c in (cmin - 1, cmax + 1))
        or (cmin <= c <= cmax and r in (rmin - 1, rmax + 1))
    )


def _variant_prediction(grid: list[list[int]], settings: dict[str, str], variant: str) -> list[list[int]]:
    if variant not in _RIVAL_NAMES:
        raise ValueError(f"unknown rival {variant!r}")
    chosen = _settings(settings)
    mode = chosen["edge_mode"]
    bounds, dots = _scene_geometry(grid)
    rmin, rmax, cmin, cmax = bounds
    output = [list(row) for row in grid]
    if variant == "rectangle_only" and (rmin == rmax or cmin == cmax):
        return output
    seen_colors: set[int] = set()
    ordered = sorted(dots, key=lambda dot: (dot[2], dot[0], dot[1]))
    for r, c, color in ordered:
        if variant == "one_per_color":
            if color in seen_colors:
                continue
            seen_colors.add(color)
        if variant == "border_only" and r not in (0, len(grid) - 1) and c not in (0, len(grid[0]) - 1):
            continue
        near, far, axis = _targets_for_source(r, c, bounds)
        if axis is None:
            if variant != "project_diagonal_to_corner":
                continue
            target = (min(max(r, rmin), rmax), min(max(c, cmin), cmax))
        else:
            if variant == "horizontal_projection_only" and axis != "horizontal":
                continue
            if variant == "vertical_projection_only" and axis != "vertical":
                continue
            if variant == "ignore_touching_sources" and _adjacent_to_bbox(r, c, bounds):
                continue
            target = near if mode == "near" else far
        if variant == "move_sources":
            output[r][c] = 0
        output[target[0]][target[1]] = color
    return output


def _apply_python(source: str, grid: list[list[int]]) -> list[list[int]]:
    for setting in SETTINGS:
        if program(setting) == source:
            return transform(grid, setting)
    raise ValueError("unknown edge-mode program")


def certify(
    episode: dict[str, Any],
    execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    _integer(len(test), 1, 4, "queries")

    seen_inputs: set[str] = set()
    for pair in train + test:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each private pair must contain exactly input and output")
        grid = _grid(pair["input"])
        output = _color_grid(pair["output"])
        if (len(output), len(output[0])) != (len(grid), len(grid[0])):
            raise ValueError("projection-edge outputs must preserve dimensions")
        key = _digest(grid)
        if key in seen_inputs:
            raise ValueError("all demonstration and query inputs must be distinct")
        seen_inputs.add(key)

    apply = execute or _apply_python
    records = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        disagreements = [
            index
            for index, (prediction, pair) in enumerate(zip(predictions, train))
            if prediction != pair["output"]
        ]
        records.append({"settings": dict(setting), "disagreeing_demo_indices": disagreements})
    survivors = [row["settings"] for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify the chosen setting: {survivors}")

    rival_first_refutation = {}
    for rival in _RIVAL_NAMES:
        first = next(
            (
                index
                for index, pair in enumerate(train)
                if _variant_prediction(pair["input"], chosen, rival) != pair["output"]
            ),
            None,
        )
        if first is None:
            raise ValueError(f"demonstrations leave declared rival alive: {rival}")
        rival_first_refutation[rival] = first

    for pair in train + test:
        if apply(program(chosen), pair["input"]) != pair["output"]:
            raise ValueError("retained label disagrees with selected rule")
    queries = [
        {
            "input_sha256": _digest(pair["input"]),
            "output_sha256": _digest(pair["output"]),
            "selected_rule_matches": True,
            "survivors": survivors,
        }
        for pair in test
    ]
    return {
        "scope": "two declared edge modes plus eight explicit finite rivals",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": records,
        "rival_first_refutation": rival_first_refutation,
        "all_declared_rivals_refuted": True,
        "queries": queries,
    }


def generate(
    seed: int,
    settings: dict[str, str] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _integer(seed, -(2**63), 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    chosen = _settings({"edge_mode": choose_edge_mode(seed)} if settings is None else settings)

    train = []
    for index in range(demos):
        grid = _scene(seed, index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for slot in range(queries):
        grid = _scene(seed, 10_000 + slot, query_slot=slot)
        test.append({"input": grid, "output": transform(grid, chosen)})

    source = program(chosen)
    episode = {
        "schema": "arcpuzzles-projection-edge-parametric-v2",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": hashlib.sha256(source.encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


class RacketRunner:
    """One live protected bridge for a bounded evidence batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc: Any) -> None:
        self.bridge.close()


def public_turn_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    """Model-visible one-query turn with no future query or private metadata."""
    from reviewer_support import public_challenge_bytes

    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    if type(query_index) is not int or not 0 <= query_index < len(test):
        raise ValueError("query_index must select one retained query")
    return public_challenge_bytes({"train": train, "test": [test[query_index]]})

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    parser.add_argument("--near-seed", type=int, default=18)
    parser.add_argument("--far-seed", type=int, default=19)
    args = parser.parse_args()

    root = find_root(__file__)
    materialize_rules(root=root)
    report = build_report(
        root=root,
        seeds={"near": args.near_seed, "far": args.far_seed},
    )
    report["execution"] = {
        "argv": list(sys.argv),
        "cwd": os.getcwd(),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for mode, challenge in report["public_challenges"].items():
            (args.write_public / f"{mode}_public.json").write_text(
                json.dumps(challenge, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    print(
        json.dumps(
            {
                "status": report["status"],
                "parameter": report["parameter"],
                "all_retained_pairs_distinguish_settings": report[
                    "all_retained_pairs_distinguish_settings"
                ],
                "settings": {
                    mode: {
                        "seed": setting["seed"],
                        "racket_sha256": setting["racket_sha256"],
                        "racket_rule_hash": setting["racket_rule_hash"],
                        "every_demo_refutes_alternative_setting": setting[
                            "every_demo_refutes_alternative_setting"
                        ],
                        "query_requires_setting": setting["query_requires_setting"],
                    }
                    for mode, setting in report["settings"].items()
                },
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
