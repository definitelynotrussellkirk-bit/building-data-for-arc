"""Parametric command-application family for ``d01b33f4a589``.

The exact canonical setting transforms the cropped motif independently for each
corner command.  The alternate applies commands left-to-right to an evolving
motif and packs the four prefix states.  Inputs are shared across settings and
include dense asymmetric motifs up to a substantive 30x30 case.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "d01b33f4a589"
POLICIES = ("independent", "cumulative")
DEFAULT_SETTINGS = {"application_policy": "independent"}
HERE = Path(__file__).resolve().parent

# height, width, motif bbox height, motif bbox width, corner commands
_DEMO_PROFILES = (
    (9, 9, 4, 3, (1, 2, 3, 4)),
    (10, 10, 5, 4, (4, 1, 3, 2)),
    (12, 14, 7, 8, (1, 2, 2, 3)),
    (16, 18, 10, 11, (3, 4, 1, 2)),
    (20, 22, 12, 14, (2, 1, 4, 3)),
    (24, 26, 14, 15, (4, 3, 2, 1)),
)
_QUERY_PROFILES = (
    (14, 16, 8, 9, (1, 3, 2, 4)),
    (18, 21, 11, 13, (2, 4, 1, 3)),
    (24, 27, 13, 15, (3, 1, 4, 2)),
    (30, 30, 14, 15, (4, 2, 3, 1)),
)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _load_selected():
    path = HERE.parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("_d01_selected_for_parametric", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SELECTED = _load_selected()


def _literal_int(name: str, value: object, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be a literal integer in {lower}..{upper}")
    return value


def normalize_settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"application_policy"}:
        raise ValueError("settings must contain exactly application_policy")
    policy = settings["application_policy"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"application_policy must be one of {POLICIES!r}")
    return {"application_policy": policy}


@lru_cache(maxsize=1)
def canonical_program() -> str:
    return (HERE / "canonical.rkt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def cumulative_program() -> str:
    return (HERE / "cumulative.rkt").read_text(encoding="utf-8")


def program(settings: object) -> str:
    policy = normalize_settings(settings)["application_policy"]
    return canonical_program() if policy == "independent" else cumulative_program()


def _grid_copy(grid):
    return [row[:] for row in grid]


def _crop_and_codes(grid: list[list[int]]) -> tuple[list[int], list[list[int]], set[tuple[int, int]]]:
    commands = _SELECTED._corner_values(grid)
    cells, motif = _SELECTED._motif_cells_and_crop(grid)
    return list(commands), motif, set(cells)


def validate_input(value: object) -> list[list[int]]:
    grid, errors = _SELECTED._coerce_arc_grid(value)
    if errors:
        raise ValueError("; ".join(errors))
    assert grid is not None
    height, width = len(grid), len(grid[0])
    codes, motif, cells = _crop_and_codes(grid)
    if any(code not in (1, 2, 3, 4) for code in codes):
        raise ValueError("all four corner commands must be in 1..4")
    if sorted(codes) not in ([1, 2, 3, 4], [1, 2, 2, 3]):
        raise ValueError("commands must be a permutation or the 1/2/2/3 multiset")
    if not cells or not motif:
        raise ValueError("input needs a non-corner motif")
    if any(r in (0, height - 1) or c in (0, width - 1) for r, c in cells):
        raise ValueError("motif must lie strictly inside the corner-command canvas")
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1:
        raise ValueError("motif must be monochrome")
    reached = {next(iter(cells))}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for dr, dc in _NEIGHBORS:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in reached:
                reached.add(nxt)
                frontier.append(nxt)
    if reached != cells:
        raise ValueError("motif must be 4-connected")
    return grid


def _variants(motif: list[list[int]], codes: list[int], policy: str) -> list[list[list[int]]]:
    if policy == "independent":
        return [_SELECTED._transform_code(motif, code) for code in codes]
    if policy == "cumulative":
        current = _grid_copy(motif)
        result = []
        for code in codes:
            current = _SELECTED._transform_code(current, code)
            result.append(current)
        return result
    raise ValueError(f"unknown application policy {policy!r}")


def _paste_nonzero(out, pattern, top: int, left: int):
    for r, row in enumerate(pattern):
        for c, value in enumerate(row):
            if value != 0:
                out[top + r][left + c] = value


def _pack(variants: list[list[list[int]]]) -> list[list[int]]:
    cell_h = max(len(variant) for variant in variants)
    cell_w = max(len(variant[0]) for variant in variants)
    out = [[0 for _ in range(2 * cell_w)] for _ in range(2 * cell_h)]
    for index, variant in enumerate(variants):
        _paste_nonzero(out, variant, (index // 2) * cell_h, (index % 2) * cell_w)
    return out


def transform(value: object, policy: object) -> list[list[int]]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError(f"application policy must be one of {POLICIES!r}")
    grid = validate_input(value)
    codes, motif, _cells = _crop_and_codes(grid)
    return _pack(_variants(motif, codes, policy))


def _rng(seed: int, split: str, slot: int, attempt: int = 0) -> random.Random:
    digest = hashlib.sha256(
        f"d01-application-v1:{seed}:{split}:{slot}:{attempt}".encode()
    ).digest()
    return random.Random(digest)


def _motif_mask(seed: int, split: str, slot: int, height: int, width: int) -> list[list[int]]:
    for attempt in range(128):
        rng = _rng(seed, split, slot, attempt)
        intervals = []
        quarter = max(1, width // 4)
        for row in range(height):
            left = rng.randrange(quarter)
            right_cut = rng.randrange(quarter)
            right = width - 1 - right_cut
            if right - left + 1 < max(2, width // 2):
                right = min(width - 1, left + max(2, width // 2) - 1)
            intervals.append((left, right))
        # Exact bbox and deliberate asymmetry.
        intervals[0] = (0, max(1, width // 2))
        intervals[1] = (0, width - 1)
        intervals[-1] = (max(1, width // 3), width - 1)
        intervals[height // 2] = (0, max(width // 2 + 1, width - 2))
        # Break the otherwise possible 180-degree symmetry, including the
        # smallest 4x3 teaching profile, while preserving row overlap.
        intervals[height - 2] = (0, max(1, width - 2))
        mask = [[1 if left <= c <= right else 0 for c in range(width)] for left, right in intervals]
        orbit = []
        current = mask
        for _ in range(4):
            orbit.append(json.dumps(current, separators=(",", ":")))
            current = _SELECTED._rotate_cw_grid(current)
        if len(set(orbit)) == 4:
            return mask
    raise RuntimeError("failed to construct an asymmetric connected motif")


def _build_input(seed: int, split: str, slot: int, profile: tuple) -> list[list[int]]:
    height, width, body_h, body_w, raw_codes = profile
    mask = _motif_mask(seed, split, slot, body_h, body_w)
    rng = _rng(seed, split, slot, 999)
    max_top = height - body_h - 1
    max_left = width - body_w - 1
    top = rng.randint(1, max_top)
    left = rng.randint(1, max_left)
    color = 1 + rng.randrange(9)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    # The profile fixes a pedagogically chosen command order; seed variation
    # remains in motif geometry, position, and color.
    codes = list(raw_codes)
    grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1] = codes
    for r in range(body_h):
        for c in range(body_w):
            if mask[r][c]:
                grid[top + r][left + c] = color
    validate_input(grid)
    return grid


def _schedule(seed: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    demos = [_build_input(seed, "demo", i, profile) for i, profile in enumerate(_DEMO_PROFILES)]
    queries = [_build_input(seed, "query", i, profile) for i, profile in enumerate(_QUERY_PROFILES)]
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(frozen) != len(set(frozen)):
        raise ValueError("parametric schedule produced duplicate inputs")
    return demos, queries


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    checked_seed = _literal_int("seed", seed, 0, 2**63 - 1)
    checked_demos = _literal_int("demos", demos, 2, 6)
    checked_queries = _literal_int("queries", queries, 1, 4)
    policy = normalize_settings(settings)["application_policy"]
    demo_inputs, query_inputs = _schedule(checked_seed)

    def pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
        return {"input": deepcopy(grid), "output": transform(grid, policy)}

    train = [pair(grid) for grid in demo_inputs[:checked_demos]]
    test = [pair(grid) for grid in query_inputs[:checked_queries]]
    if setting_survivors(train) != [policy]:
        raise ValueError("demonstrations do not uniquely identify application_policy")
    return {"train": train, "test": test, "program_solution": program({"application_policy": policy})}


def setting_survivors(demonstrations: object) -> list[str]:
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("demonstrations must be a nonempty list")
    return [
        policy for policy in POLICIES
        if all(transform(pair["input"], policy) == pair["output"] for pair in demonstrations)
    ]


def analyze_input(value: object) -> dict[str, Any]:
    grid = validate_input(value)
    codes, motif, cells = _crop_and_codes(grid)
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "codes": codes,
        "motif_size": len(cells),
        "bbox_height": len(motif),
        "bbox_width": len(motif[0]),
        "independent_variants": _variants(motif, codes, "independent"),
        "cumulative_variants": _variants(motif, codes, "cumulative"),
    }


def _alias_codes(codes: list[int], source: int, replacement: int) -> list[int]:
    return [replacement if code == source else code for code in codes]


def _rival_variants(motif, codes, name: str, selected_policy: str):
    if name == "fixed_command_order":
        return _variants(motif, [1, 2, 3, 4], selected_policy)
    if name == "reverse_corner_order":
        return _variants(motif, list(reversed(codes)), selected_policy)
    if name.startswith("alias_"):
        source, replacement = map(int, name.removeprefix("alias_").split("_as_"))
        return _variants(motif, _alias_codes(codes, source, replacement), selected_policy)
    if name == "reverse_cumulative":
        current = _grid_copy(motif)
        built = []
        for code in reversed(codes):
            current = _SELECTED._transform_code(current, code)
            built.append(current)
        return list(reversed(built))
    if name == "cumulative_reverse_output":
        return list(reversed(_variants(motif, codes, "cumulative")))
    if name == "reset_after_two":
        current = _grid_copy(motif)
        built = []
        for index, code in enumerate(codes):
            if index == 2:
                current = _grid_copy(motif)
            current = _SELECTED._transform_code(current, code)
            built.append(current)
        return built
    if name == "skip_first_command":
        current = _grid_copy(motif)
        built = [_grid_copy(motif)]
        for code in codes[1:]:
            current = _SELECTED._transform_code(current, code)
            built.append(current)
        return built
    raise ValueError(f"unknown rival {name!r}")


RIVALS = (
    "fixed_command_order",
    "reverse_corner_order",
    "alias_1_as_2",
    "alias_2_as_1",
    "alias_3_as_4",
    "alias_4_as_3",
    "reverse_cumulative",
    "cumulative_reverse_output",
    "reset_after_two",
    "skip_first_command",
)


def rival_survivors(demonstrations: object, *, selected_policy: str) -> list[str]:
    if selected_policy not in POLICIES:
        raise ValueError("unknown selected policy")
    survivors = []
    for name in RIVALS:
        fits = True
        for pair in demonstrations:
            grid = validate_input(pair["input"])
            codes, motif, _ = _crop_and_codes(grid)
            if _pack(_rival_variants(motif, codes, name, selected_policy)) != pair["output"]:
                fits = False
                break
        if fits:
            survivors.append(name)
    return survivors


def _hash_grid(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def dependency(value: object, policy: object) -> dict[str, object]:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown policy")
    grid = validate_input(value)
    codes, motif, _ = _crop_and_codes(grid)
    variants = _variants(motif, codes, policy)
    independent = _variants(motif, codes, "independent")
    return {
        "step_a": "read the corner commands and produce four transformed motif states; cumulative mode applies each command to the previous state",
        "intermediate": "the ordered sequence of input-dependent transformed motif grids",
        "codes": codes,
        "variant_dimensions": [[len(v), len(v[0])] for v in variants],
        "variant_sha256": [_hash_grid(v) for v in variants],
        "independent_variant_sha256": [_hash_grid(v) for v in independent],
        "step_b": "measure the maximum intermediate dimensions and pack those four exact states into the 2-by-2 output",
        "final": _pack(variants),
    }
