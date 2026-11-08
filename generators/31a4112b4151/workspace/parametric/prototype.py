"""Parametric target-scope family for anchored prototype stamping.

The canonical setting stamps the extracted prototype at every color-9 target.
The alternative first uses the extracted offsets to identify exactly those
locations whose stamp would be clipped, then stamps only that input-derived set.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "31a4112b4151"
SCOPES = ("all_targets", "clipped_targets")
DEFAULT_SCOPE = "all_targets"
HERE = Path(__file__).resolve().parent

PROFILES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 1), (1, 0), (1, 1)),
    ((1, -1), (1, 0), (1, 1)),
    ((-1, 1), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
    ((-1, 0), (0, -1), (0, 1), (1, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((-1, 0), (0, 1), (1, -1), (1, 0), (1, 1)),
    ((-1, 0), (0, 1), (1, -1), (1, 0), (1, 1), (2, 1)),
)
DEMO_SIZES = ((9, 10), (10, 12), (12, 9), (14, 14), (16, 13), (18, 18))
QUERY_SIZES = ((13, 17), (20, 16), (24, 24), (30, 30))
DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load_base():
    source = HERE.parents[1] / "generator.py"
    name = "_base_31a_" + hashlib.sha256(str(source).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()


def _scope(settings: dict[str, Any]) -> str:
    if type(settings) is not dict or set(settings) != {"target_scope"}:
        raise ValueError("settings must contain exactly target_scope")
    scope = settings["target_scope"]
    if type(scope) is not str or scope not in SCOPES:
        raise ValueError(f"target_scope must be one of {SCOPES}")
    return scope


def _integer(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: dict[str, Any]) -> str:
    scope = _scope(settings)
    filename = "canonical.rkt" if scope == DEFAULT_SCOPE else "clipped_targets.rkt"
    source = (HERE / "rules" / filename).read_text(encoding="utf-8")
    if not source.strip():
        raise ValueError(f"empty retained rule: {filename}")
    return source


def _rng(seed: int, bank: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|v1|{seed}|{bank}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _adjacent(cell: tuple[int, int], cells: Iterable[tuple[int, int]]) -> bool:
    return any(abs(cell[0] - r) + abs(cell[1] - c) == 1 for r, c in cells)


def _status(target: tuple[int, int], offsets: tuple[tuple[int, int], ...], h: int, w: int) -> tuple[int, int]:
    visible = sum(0 <= target[0] + dr < h and 0 <= target[1] + dc < w for dr, dc in offsets)
    return visible, len(offsets) - visible


def _choose(candidates: list[tuple[int, int]], *, anchor: tuple[int, int], selected: list[tuple[int, int]], rng: random.Random) -> tuple[int, int]:
    lawful = [cell for cell in candidates if not _adjacent(cell, selected)]
    if not lawful:
        raise ValueError("scene profile has no nonadjacent target candidate")
    # Spatial spread first, stable random tie-breaking second.
    keyed = [(abs(r-anchor[0]) + abs(c-anchor[1]), rng.random(), (r, c)) for r, c in lawful]
    return max(keyed)[2]


def _build_scene(seed: int, bank: str, index: int) -> list[list[int]]:
    sizes = DEMO_SIZES if bank == "demo" else QUERY_SIZES
    if not 0 <= index < len(sizes):
        raise ValueError("scene index outside retained bank")
    h, w = sizes[index]
    rng = _rng(seed, bank, index)
    if bank == "query" and index == 3:
        profile_index = 5 + seed % 3  # substantive 5-6 cell 30x30 stress
    else:
        profile_index = (index + (0 if bank == "demo" else 3) + seed % len(PROFILES)) % len(PROFILES)
    offsets = PROFILES[profile_index]
    color = 1 + ((seed * 5 + index * 3 + (0 if bank == "demo" else 2)) % 8)

    feasible = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if all(0 <= r + dr < h and 0 <= c + dc < w for dr, dc in offsets)
    ]
    if bank == "query" and index == 3:
        anchor = min(feasible, key=lambda p: (p[0] + p[1], p[0], p[1]))
    else:
        interior = [p for p in feasible if 1 <= p[0] < h - 1 and 1 <= p[1] < w - 1]
        anchor = rng.choice(interior or feasible)

    proto_cells = {anchor, *((anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets)}
    extras = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in proto_cells and not _adjacent((r, c), proto_cells)
    ]
    partial = [cell for cell in extras if 0 < _status(cell, offsets, h, w)[0] < len(offsets)]
    full = [cell for cell in extras if _status(cell, offsets, h, w)[1] == 0]

    selected: list[tuple[int, int]] = [anchor]
    # Two distinct clipped destinations refute "only the first clipped target".
    for _ in range(2):
        cell = _choose(partial, anchor=anchor, selected=selected, rng=rng)
        selected.append(cell)
        partial = [candidate for candidate in partial if candidate != cell]
    full_extra = _choose(full, anchor=anchor, selected=selected, rng=rng)
    selected.append(full_extra)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[anchor[0]][anchor[1]] = 9
    for dr, dc in offsets:
        grid[anchor[0] + dr][anchor[1] + dc] = color
    for r, c in selected[1:]:
        grid[r][c] = 9

    facts = inspect_scene(grid)
    if len(facts["targets"]) != 4:
        raise AssertionError("constructed target count drift")
    clipped = [t for t in facts["targets"] if facts["clipped_by_target"][t] > 0]
    unclipped = [t for t in facts["targets"] if facts["clipped_by_target"][t] == 0]
    if len(clipped) < 2 or len(unclipped) < 2:
        raise AssertionError("constructed scene lost target-scope contrast")
    if _BASE.self_check(grid):
        raise AssertionError("constructed scene is outside the reviewed base grammar: " + "; ".join(_BASE.self_check(grid)))
    return grid


def inspect_scene(grid: list[list[int]]) -> dict[str, Any]:
    analysis = _BASE.analyze_scene(grid)
    if analysis["errors"] or analysis["facts"] is None:
        raise ValueError("outside anchored-prototype grammar: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "height": facts["height"],
        "width": facts["width"],
        "anchor": tuple(facts["anchor"]),
        "targets": [tuple(t) for t in facts["targets"]],
        "offsets": [tuple(item) for item in facts["offsets"]],
        "clipped_by_target": {tuple(k): v for k, v in facts["clipped_by_target"].items()},
    }


def solve(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    scope = _scope(settings)
    facts = inspect_scene(grid)
    targets = facts["targets"]
    if scope == "clipped_targets":
        targets = [target for target in targets if facts["clipped_by_target"][target] > 0]
    out = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for tr, tc in targets:
        for dr, dc, value in facts["offsets"]:
            rr, cc = tr + dr, tc + dc
            if 0 <= rr < facts["height"] and 0 <= cc < facts["width"]:
                out[rr][cc] = value
    return out


def _pairs(seed: int, settings: dict[str, Any], bank: str, count: int) -> list[dict[str, Any]]:
    return [
        {"input": grid, "output": solve(grid, settings)}
        for grid in (_build_scene(seed, bank, index) for index in range(count))
    ]


def generate(seed: int, settings: dict[str, Any], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    _scope(settings)
    return {
        "train": _pairs(seed, settings, "demo", demos),
        "test": _pairs(seed, settings, "query", queries),
        "program_solution": program(settings),
    }


def dependency_trace(grid: list[list[int]], settings: dict[str, Any]) -> dict[str, Any]:
    scope = _scope(settings)
    facts = inspect_scene(grid)
    selected = facts["targets"] if scope == "all_targets" else [
        target for target in facts["targets"] if facts["clipped_by_target"][target] > 0
    ]
    output = solve(grid, settings)
    return {
        "step_a": "extract_template_and_select_clipped_targets",
        "intermediate": {
            "template_offsets": [list(item) for item in facts["offsets"]],
            "selected_targets": [list(item) for item in selected],
        },
        "step_b": "stamp_extracted_template_at_selected_targets",
        "why_b_depends_on_a": "The stamp coordinates and destination set are both computed from the extracted input prototype; changing the selected target set changes the final support.",
        "output": output,
        "counterfactual_all_targets_output": solve(grid, {"target_scope": "all_targets"}),
    }


def _rival(grid: list[list[int]], name: str, first_offsets: list[tuple[int, int, int]] | None = None) -> list[list[int]]:
    facts = inspect_scene(grid)
    targets = facts["targets"]
    offsets = facts["offsets"] if first_offsets is None else first_offsets
    if name == "always_all_targets":
        chosen = targets
    elif name == "always_clipped_targets":
        chosen = [t for t in targets if facts["clipped_by_target"][t] > 0]
    elif name == "unclipped_targets_only":
        chosen = [t for t in targets if facts["clipped_by_target"][t] == 0]
    elif name == "prototype_origin_only":
        chosen = [facts["anchor"]]
    elif name == "first_clipped_target_only":
        clipped = [t for t in targets if facts["clipped_by_target"][t] > 0]
        chosen = clipped[:1]
    else:
        raise ValueError(name)
    out = [[0 for _ in range(facts["width"])] for _ in range(facts["height"])]
    for tr, tc in chosen:
        for dr, dc, value in offsets:
            rr, cc = tr + dr, tc + dc
            if 0 <= rr < facts["height"] and 0 <= cc < facts["width"]:
                out[rr][cc] = value
    return out


def bounded_audit(*, seeds: Iterable[int] = range(16), demos: int = 2, queries: int = 4) -> dict[str, Any]:
    seeds = list(seeds)
    harmful: list[dict[str, Any]] = []
    rival_names = (
        "always_all_targets",
        "always_clipped_targets",
        "unclipped_targets_only",
        "prototype_origin_only",
        "first_clipped_target_only",
        "fixed_first_demo_shape",
    )
    for seed in seeds:
        for scope in SCOPES:
            settings = {"target_scope": scope}
            episode = generate(seed, settings, demos, queries)
            first_offsets = inspect_scene(episode["train"][0]["input"])["offsets"]
            for rival in rival_names:
                def predict(pair):
                    fixed = first_offsets if rival == "fixed_first_demo_shape" else None
                    mode = "always_all_targets" if rival == "fixed_first_demo_shape" else rival
                    return _rival(pair["input"], mode, fixed)
                survives = all(predict(pair) == pair["output"] for pair in episode["train"])
                disagrees = any(predict(pair) != pair["output"] for pair in episode["test"])
                if survives and disagrees:
                    harmful.append({"seed": seed, "settings": settings, "rival": rival})
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "episodes": len(seeds) * len(SCOPES),
        "demos": demos,
        "queries": queries,
        "rivals": list(rival_names),
        "harmful_survivors": harmful,
        "limits": "Finite deterministic audit; absence of survivors is not universal uniqueness.",
    }
