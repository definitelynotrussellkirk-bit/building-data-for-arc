#!/usr/bin/env python3
"""Source-bound anti-diagonal fill / activated-relay parametric family.

The default fill_only setting returns the selected canonical Racket source
byte-for-byte.  activated_projection first completes every canonical
anti-diagonal span.  It then finds the unique color-8 relay adjacent to a cell
that was zero in the input but became colored during that fill, takes the new
cell's color and the input-dependent outward direction, recolors the relay, and
casts the color through post-fill zeros until the next completed object or edge.
Inputs are sampled independently of the hidden episode setting.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "d57b7deebba2"
VERSION = "anti-diagonal-activated-relay-v1"
PARAMETER_NAME = "relay_policy"
ALLOWED_SETTINGS = ("fill_only", "activated_projection")
DEFAULT_SETTING = "fill_only"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1
GENERATOR_SHA256 = "c20aebc584ad035299206e01dc82780bd26091dd47526ca75fcbf888e13144e6"
CANONICAL_SHA256 = "ed160322904363626371b0706df39668c5e4afc5c89df1577a193cc1c7888676"
ACTIVATED_SHA256 = "b7ac51690fcd6edc8b8e1f3b8e4978d23ce5ccb1b48614d253f47808d13c74df"
RELAY_COLOR = 8
SPAN_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_HOME = Path(__file__).resolve().parent
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# h, w, span count, relay count, active direction, blocker relay, stress
_DEMO_PROFILES = (
    (8, 10, 3, 3, "right", False, False),
    (9, 12, 3, 4, "down", True, False),
    (10, 11, 4, 4, "left", False, False),
    (11, 14, 4, 5, "up", True, False),
    (12, 13, 5, 5, "right", False, False),
    (14, 16, 5, 6, "down", True, False),
)
_QUERY_PROFILES = (
    (9, 13, 4, 4, "up", True, False),
    (13, 11, 4, 5, "left", False, False),
    (17, 19, 6, 6, "down", True, False),
    (30, 30, 8, 8, "right", True, True),
)


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _exact_integer(value, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(value) -> str:
    if type(value) is not str or value not in ALLOWED_SETTINGS:
        raise ValueError(f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}")
    return value


def validate_settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER_NAME}:
        raise ValueError(f"settings must contain exactly {PARAMETER_NAME}")
    return _setting(settings[PARAMETER_NAME])


def validate_request(seed, demos, queries) -> tuple[int, int, int]:
    return (
        _exact_integer(seed, "seed", 0, MAX_SEED),
        _exact_integer(demos, "demos", MIN_DEMOS, MAX_DEMOS),
        _exact_integer(queries, "queries", MIN_QUERIES, MAX_QUERIES),
    )


def _canonical_catalog_program() -> str:
    programs = set()
    with canonical_path(find_root(__file__)).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one exact canonical program for the selected task")
    return programs.pop()


def canonical_program() -> str:
    source = (_HOME / "canonical.rkt").read_text(encoding="utf-8")
    if _sha256(source) != CANONICAL_SHA256 or source != _canonical_catalog_program():
        raise ValueError("Canonical authority changed; re-review exact source binding")
    return source


def activated_program() -> str:
    source = (_HOME / "activated_projection.rkt").read_text(encoding="utf-8")
    if _sha256(source) != ACTIVATED_SHA256:
        raise ValueError("Activated-projection program changed without review")
    required = ("(canonical-fill g)", "newly-filled-neighbors", "(at filled r c)")
    if any(token not in source for token in required):
        raise ValueError("Activated-projection program lost its reviewed two-stage structure")
    return source


def program_for(relay_policy: str) -> str:
    setting = _setting(relay_policy)
    return canonical_program() if setting == DEFAULT_SETTING else activated_program()


def program(settings) -> str:
    return program_for(validate_settings(settings))


def _grid(value) -> list[list[int]]:
    if (
        type(value) is not list
        or not 5 <= len(value) <= 30
        or type(value[0]) is not list
        or not 5 <= len(value[0]) <= 30
    ):
        raise ValueError("grid dimensions must be exact lists in 5..30")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors 0..9")
    return [row[:] for row in value]


def _neighbors(cell: tuple[int, int], h: int, w: int) -> Iterable[tuple[int, int]]:
    r, c = cell
    for dr, dc in _CARDINAL:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def canonical_fill_python(value) -> list[list[int]]:
    source = _grid(value)
    out = deepcopy(source)
    colors = []
    for row in source:
        for color in row:
            if color and color not in colors:
                colors.append(color)
    h, w = len(source), len(source[0])
    for color in colors:
        for diag in range(h + w):
            cells = [
                (r, c)
                for r, row in enumerate(source)
                for c, value in enumerate(row)
                if value == color and r + c == diag
            ]
            if len(cells) < 2:
                continue
            r0 = min(r for r, _ in cells)
            r1 = max(r for r, _ in cells)
            for r in range(r0, r1 + 1):
                c = diag - r
                if 0 <= r < h and 0 <= c < w:
                    out[r][c] = color
    return out


def _new_neighbors(original, filled, relay: tuple[int, int]) -> list[tuple[int, int]]:
    h, w = len(original), len(original[0])
    return [
        cell
        for cell in _neighbors(relay, h, w)
        if original[cell[0]][cell[1]] == 0 and filled[cell[0]][cell[1]] != 0
    ]


def _ray_cells(filled, relay: tuple[int, int], direction: tuple[int, int]) -> list[tuple[int, int]]:
    h, w = len(filled), len(filled[0])
    dr, dc = direction
    r, c = relay[0] + dr, relay[1] + dc
    cells = []
    while 0 <= r < h and 0 <= c < w and filled[r][c] == 0:
        cells.append((r, c))
        r += dr
        c += dc
    return cells


def activation_record(value) -> dict:
    original = _grid(value)
    filled = canonical_fill_python(original)
    relays = [
        (r, c)
        for r, row in enumerate(original)
        for c, cell in enumerate(row)
        if cell == RELAY_COLOR and len(_new_neighbors(original, filled, (r, c))) == 1
    ]
    if len(relays) != 1:
        raise ValueError(f"input must have exactly one activated relay, found {len(relays)}")
    relay = relays[0]
    neighbor = _new_neighbors(original, filled, relay)[0]
    direction = (relay[0] - neighbor[0], relay[1] - neighbor[1])
    color = filled[neighbor[0]][neighbor[1]]
    ray = _ray_cells(filled, relay, direction)
    if color in (0, RELAY_COLOR) or not ray:
        raise ValueError("activated relay must carry a non-relay span color onto a nonempty ray")
    return {
        "relay": list(relay),
        "newly_filled_neighbor": list(neighbor),
        "color": color,
        "direction": list(direction),
        "ray_cells": [list(cell) for cell in ray],
    }


def _project(
    filled: list[list[int]],
    relay: tuple[int, int],
    direction: tuple[int, int],
    color: int,
    *,
    recolor_relay: bool = True,
) -> list[list[int]]:
    out = deepcopy(filled)
    if recolor_relay:
        out[relay[0]][relay[1]] = color
    for r, c in _ray_cells(filled, relay, direction):
        out[r][c] = color
    return out


def _correct_projection(value) -> list[list[int]]:
    original = _grid(value)
    filled = canonical_fill_python(original)
    record = activation_record(original)
    return _project(
        filled,
        tuple(record["relay"]),
        tuple(record["direction"]),
        record["color"],
    )


def solve_python(value, relay_policy: str) -> list[list[int]]:
    setting = _setting(relay_policy)
    return canonical_fill_python(value) if setting == "fill_only" else _correct_projection(value)


def _any_filled_neighbor(original, filled, relay: tuple[int, int]) -> list[tuple[int, int]]:
    return [
        cell
        for cell in _neighbors(relay, len(original), len(original[0]))
        if filled[cell[0]][cell[1]] != 0
    ]


def _solve_variant(value, variant: str) -> list[list[int]]:
    original = _grid(value)
    filled = canonical_fill_python(original)
    if variant == "fill_only":
        return filled
    if variant == "activated_projection":
        return _correct_projection(original)
    record = activation_record(original)
    relay = tuple(record["relay"])
    neighbor = tuple(record["newly_filled_neighbor"])
    color = record["color"]
    if variant == "toward_span":
        direction = (neighbor[0] - relay[0], neighbor[1] - relay[1])
        return _project(filled, relay, direction, color)
    if variant == "marker_color":
        return _project(filled, relay, tuple(record["direction"]), RELAY_COLOR)
    if variant == "leave_relay_gray":
        return _project(
            filled,
            relay,
            tuple(record["direction"]),
            color,
            recolor_relay=False,
        )
    if variant == "diagonal_down_left":
        return _project(filled, relay, (1, -1), color)
    if variant == "endpoint_inclusive":
        candidates = []
        for r, row in enumerate(original):
            for c, cell in enumerate(row):
                if cell != RELAY_COLOR:
                    continue
                neighbors = _any_filled_neighbor(original, filled, (r, c))
                if neighbors:
                    candidates.append(((r, c), neighbors[0]))
        if not candidates:
            return filled
        chosen_relay, chosen_neighbor = candidates[0]
        chosen_color = filled[chosen_neighbor[0]][chosen_neighbor[1]]
        direction = (
            chosen_relay[0] - chosen_neighbor[0],
            chosen_relay[1] - chosen_neighbor[1],
        )
        return _project(filled, chosen_relay, direction, chosen_color)
    raise ValueError(f"unknown variant {variant!r}")


def _replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"reviewed Racket fragment occurrence changed: {old!r}")
    return source.replace(old, new)


def _rival_program(variant: str) -> str:
    source = activated_program()
    if variant == "toward_span":
        return _replace_once(
            source,
            "(dr (- rr nr)) (dc (- rc nc))",
            "(dr (- nr rr)) (dc (- nc rc))",
        )
    if variant == "marker_color":
        return _replace_once(source, "(color (at filled nr nc))", "(color 8)")
    if variant == "leave_relay_gray":
        return _replace_once(
            source,
            "(recolored (set-cell filled rr rc color))",
            "(recolored filled)",
        )
    if variant == "diagonal_down_left":
        return _replace_once(
            source,
            "(dr (- rr nr)) (dc (- rc nc))",
            "(dr 1) (dc -1)",
        )
    if variant == "endpoint_inclusive":
        source = _replace_once(
            source,
            "(and (= (at original (first p) (second p)) 0)\n            (not (= (at filled (first p) (second p)) 0)))",
            "(not (= (at filled (first p) (second p)) 0))",
        )
        source = source.replace(
            "(= (length (newly-filled-neighbors g filled p)) 1)",
            "(>= (length (newly-filled-neighbors g filled p)) 1)",
        )
        source = _replace_once(
            source,
            "(if (= (length relays) 1)",
            "(if (>= (length relays) 1)",
        )
        return source
    raise ValueError(f"unknown rival variant {variant!r}")


def rival_programs(selected_setting: str) -> dict[str, str]:
    selected = _setting(selected_setting)
    alternate = next(setting for setting in ALLOWED_SETTINGS if setting != selected)
    return {
        "alternate_setting": program_for(alternate),
        "endpoint_inclusive": _rival_program("endpoint_inclusive"),
        "toward_span": _rival_program("toward_span"),
        "marker_color": _rival_program("marker_color"),
        "leave_relay_gray": _rival_program("leave_relay_gray"),
        "diagonal_down_left": _rival_program("diagonal_down_left"),
    }


def _rival_output(name: str, value, selected_setting: str) -> list[list[int]]:
    selected = _setting(selected_setting)
    if name == "alternate_setting":
        alternate = next(setting for setting in ALLOWED_SETTINGS if setting != selected)
        return solve_python(value, alternate)
    return _solve_variant(value, name)


def _derived_seed(seed: int, split: str, slot: int, attempt: int = 0) -> int:
    digest = hashlib.sha256(f"{VERSION}:{seed}:{split}:{slot}:{attempt}".encode()).digest()
    return int.from_bytes(digest[:8], "big") & MAX_SEED


def _span_candidates(h: int, w: int, max_steps: int):
    candidates = []
    for diag in range(h + w - 1):
        cells = [(r, diag - r) for r in range(h) if 0 <= diag - r < w]
        for start in range(len(cells)):
            for steps in range(2, max_steps + 1):
                stop = start + steps
                if stop < len(cells):
                    candidates.append((diag, tuple(cells[start : stop + 1])))
    return candidates


def _active_geometry(span: tuple[tuple[int, int], ...], direction_name: str):
    if direction_name == "up":
        neighbor, direction = span[1], (-1, 0)
    elif direction_name == "right":
        neighbor, direction = span[1], (0, 1)
    elif direction_name == "down":
        neighbor, direction = span[-2], (1, 0)
    elif direction_name == "left":
        neighbor, direction = span[-2], (0, -1)
    else:
        raise ValueError(direction_name)
    relay = (neighbor[0] + direction[0], neighbor[1] + direction[1])
    return neighbor, relay, direction


def _candidate_relay_cells(h, w, filled, occupied, used_diags, *, boundary=None):
    cells = []
    for r in range(h):
        for c in range(w):
            if boundary == "top" and r != 0:
                continue
            if boundary == "bottom" and r != h - 1:
                continue
            if boundary == "left" and c != 0:
                continue
            if boundary == "right" and c != w - 1:
                continue
            if (r, c) in occupied or r + c in used_diags or filled[r][c] != 0:
                continue
            cells.append((r, c))
    return cells


def _new_neighbor_count_without_relays(filled, relay):
    return sum(filled[r][c] != 0 for r, c in _neighbors(relay, len(filled), len(filled[0])))


def _choose_endpoint_decoy(rng, endpoints, h, w, filled, occupied, used_diags):
    choices = []
    for endpoint in endpoints:
        for dr, dc in _CARDINAL:
            relay = (endpoint[0] + dr, endpoint[1] + dc)
            if not (0 <= relay[0] < h and 0 <= relay[1] < w):
                continue
            if relay in occupied or sum(relay) in used_diags or filled[relay[0]][relay[1]] != 0:
                continue
            # It must touch an original endpoint but no newly filled interior.
            if _new_neighbor_count_without_relays(filled, relay) != 1:
                continue
            choices.append(relay)
    if not choices:
        return None
    return rng.choice(choices)


def _quadrant_coverage(grid) -> bool:
    h, w = len(grid), len(grid[0])
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return all(
        any((r < h // 2) == top and (c < w // 2) == left for r, c in points)
        for top in (True, False)
        for left in (True, False)
    )


def _boundary_coverage(grid) -> bool:
    h, w = len(grid), len(grid[0])
    return (
        any(grid[0][c] for c in range(w))
        and any(grid[h - 1][c] for c in range(w))
        and any(grid[r][0] for r in range(h))
        and any(grid[r][w - 1] for r in range(h))
    )


def _scene_is_strong(grid) -> bool:
    try:
        activation_record(grid)
    except ValueError:
        return False
    outputs = {name: solve_python(grid, name) for name in ALLOWED_SETTINGS}
    if outputs["fill_only"] == outputs["activated_projection"]:
        return False
    for selected in ALLOWED_SETTINGS:
        selected_output = outputs[selected]
        for name in rival_programs(selected):
            if _rival_output(name, grid, selected) == selected_output:
                return False
    return True


def _construct_scene(seed: int, split: str, slot: int, profile) -> list[list[int]]:
    h, w, n_spans, n_relays, direction_name, blocker, stress = profile
    max_steps = 10 if stress else min(7, min(h, w) - 2)
    candidates = _span_candidates(h, w, max_steps)
    for attempt in range(1024):
        rng = random.Random(_derived_seed(seed, split, slot, attempt))
        active_options = []
        for diag, span in candidates:
            if len(span) < 4:
                continue
            neighbor, relay, direction = _active_geometry(span, direction_name)
            if not (0 <= relay[0] < h and 0 <= relay[1] < w):
                continue
            outward = []
            r, c = relay[0] + direction[0], relay[1] + direction[1]
            while 0 <= r < h and 0 <= c < w:
                outward.append((r, c))
                r += direction[0]
                c += direction[1]
            if len(outward) >= (5 if stress else 3):
                active_options.append((diag, span, neighbor, relay, direction, outward))
        if not active_options:
            raise ValueError(f"profile has no active geometry: {profile}")
        active = rng.choice(active_options)
        active_diag, active_span, neighbor, active_relay, direction, outward = active
        other_by_diag = {}
        for diag, span in candidates:
            if diag == active_diag or active_relay in span:
                continue
            other_by_diag.setdefault(diag, []).append(span)
        if len(other_by_diag) < n_spans - 1:
            continue
        chosen_diags = rng.sample(sorted(other_by_diag), n_spans - 1)
        spans = [active_span] + [rng.choice(other_by_diag[diag]) for diag in chosen_diags]
        rng.shuffle(spans)
        active_index = spans.index(active_span)

        palette = rng.sample(list(SPAN_COLORS), n_spans)
        if (slot + (0 if split == "demos" else 1)) % 3 == 0 and n_spans >= 3:
            repeat_index = 1 if active_index != 1 else 2
            palette[repeat_index] = palette[active_index]
        grid = [[0] * w for _ in range(h)]
        endpoints = []
        occupied = set()
        for color, span in zip(palette, spans):
            for cell in (span[0], span[-1]):
                if cell in occupied:
                    break
                grid[cell[0]][cell[1]] = color
                occupied.add(cell)
                endpoints.append(cell)
            else:
                continue
            break
        else:
            filled = canonical_fill_python(grid)
            # Active relay must see exactly one newly painted cell and no relay diagonal conflict.
            if active_relay in occupied or filled[active_relay[0]][active_relay[1]] != 0:
                continue
            new_neighbors = [
                cell
                for cell in _neighbors(active_relay, h, w)
                if grid[cell[0]][cell[1]] == 0 and filled[cell[0]][cell[1]] != 0
            ]
            if new_neighbors != [neighbor] and set(new_neighbors) != {neighbor}:
                continue
            relays = [active_relay]
            used_diags = {sum(active_relay)}
            occupied_with_relays = occupied | {active_relay}

            if blocker:
                zero_outward = [cell for cell in outward if filled[cell[0]][cell[1]] == 0]
                if len(zero_outward) < 3:
                    continue
                blocker_candidates = [
                    cell
                    for cell in zero_outward[2:]
                    if cell not in occupied_with_relays and sum(cell) not in used_diags
                ]
                if blocker_candidates:
                    stop = rng.choice(blocker_candidates[: max(1, len(blocker_candidates) // 2)])
                    relays.append(stop)
                    used_diags.add(sum(stop))
                    occupied_with_relays.add(stop)

            endpoint_decoy = _choose_endpoint_decoy(
                rng, endpoints, h, w, filled, occupied_with_relays, used_diags
            )
            if endpoint_decoy is None:
                continue
            relays.append(endpoint_decoy)
            used_diags.add(sum(endpoint_decoy))
            occupied_with_relays.add(endpoint_decoy)

            if stress:
                ok = True
                for boundary in ("top", "bottom", "left", "right"):
                    if len(relays) >= n_relays:
                        break
                    choices = [
                        cell
                        for cell in _candidate_relay_cells(
                            h, w, filled, occupied_with_relays, used_diags, boundary=boundary
                        )
                        if _new_neighbor_count_without_relays(filled, cell) == 0
                    ]
                    if not choices:
                        ok = False
                        break
                    relay = rng.choice(choices)
                    relays.append(relay)
                    used_diags.add(sum(relay))
                    occupied_with_relays.add(relay)
                if not ok:
                    continue

            while len(relays) < n_relays:
                choices = [
                    cell
                    for cell in _candidate_relay_cells(
                        h, w, filled, occupied_with_relays, used_diags
                    )
                    if _new_neighbor_count_without_relays(filled, cell) == 0
                ]
                if not choices:
                    break
                relay = rng.choice(choices)
                relays.append(relay)
                used_diags.add(sum(relay))
                occupied_with_relays.add(relay)
            if len(relays) != n_relays:
                continue
            for r, c in relays:
                grid[r][c] = RELAY_COLOR
            try:
                record = activation_record(grid)
            except ValueError:
                continue
            if tuple(record["relay"]) != active_relay or len(record["ray_cells"]) < 2:
                continue
            if stress and (not _boundary_coverage(grid) or not _quadrant_coverage(grid)):
                continue
            if not _scene_is_strong(grid):
                continue
            return grid
    raise ValueError(f"could not construct {split} scene {slot} for profile {profile}")


@lru_cache(maxsize=4096)
def _scene(seed: int, split: str, slot: int) -> tuple[tuple[int, ...], ...]:
    profiles = _DEMO_PROFILES if split == "demos" else _QUERY_PROFILES
    grid = _construct_scene(seed, split, slot, profiles[slot])
    return tuple(tuple(row) for row in grid)


def _scene_grid(seed: int, split: str, slot: int) -> list[list[int]]:
    return [list(row) for row in _scene(seed, split, slot)]


def build_claimed_episode(seed, relay_policy: str, demos: int, queries: int) -> dict:
    seed, demos, queries = validate_request(seed, demos, queries)
    setting = _setting(relay_policy)
    train_inputs = [_scene_grid(seed, "demos", index) for index in range(demos)]
    all_query_inputs = [_scene_grid(seed, "queries", index) for index in range(MAX_QUERIES)]
    inputs = train_inputs + all_query_inputs
    keys = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    if len(keys) != len(set(keys)):
        raise ValueError("all stored demonstration and query inputs must be distinct")
    return {
        "schema": "d57b7deebba2-parametric-episode-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": {PARAMETER_NAME: setting},
        "train": [
            {"input": grid, "output": solve_python(grid, setting)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": solve_python(grid, setting)}
            for grid in all_query_inputs[:queries]
        ],
        "stored_queries": [
            {"input": grid, "output": solve_python(grid, setting)}
            for grid in all_query_inputs
        ],
        "program_solution": program_for(setting),
    }


def teaching_report(episode: dict) -> dict:
    selected = validate_settings(episode["settings"])
    selected_program = program_for(selected)
    if episode.get("program_solution") != selected_program:
        raise ValueError("episode program does not match selected setting")
    all_pairs = episode["train"] + episode["test"]
    all_queries_match = all(
        pair["output"] == solve_python(pair["input"], selected) for pair in all_pairs
    )
    survivors = []
    rejected = []
    query_disagreements = {}
    for name in rival_programs(selected):
        fits = all(
            _rival_output(name, pair["input"], selected) == pair["output"]
            for pair in episode["train"]
        )
        disagreements = sum(
            _rival_output(name, pair["input"], selected) != pair["output"]
            for pair in episode["test"]
        )
        query_disagreements[name] = disagreements
        (survivors if fits else rejected).append(name)
    return {
        "selected_setting": selected,
        "demos_identify_declared_setting": not survivors,
        "surviving_rivals": survivors,
        "rejected_rivals": rejected,
        "query_disagreements": query_disagreements,
        "all_queries_match_selected": all_queries_match,
        "limits": "Finite authored rivals only; this is not a uniqueness proof over all rules.",
    }


def public_challenge(episode: dict, *, query_indices=None) -> dict:
    if query_indices is None:
        query_indices = range(len(episode["test"]))
    indices = list(query_indices)
    if any(type(index) is not int or not 0 <= index < len(episode["test"]) for index in indices):
        raise ValueError("query indices must select stored test pairs")
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": deepcopy(episode["test"][index]["input"])} for index in indices],
    }


def sequential_turn(episode: dict, query_index: int) -> dict:
    _exact_integer(query_index, "query_index", 0, len(episode["test"]) - 1)
    if query_index == 0:
        return public_challenge(episode, query_indices=[0])
    return {"test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}


def public_id(episode: dict) -> str:
    return hashlib.sha256(public_challenge_bytes(public_challenge(episode))).hexdigest()


def causal_record(value) -> dict:
    record = activation_record(value)
    return {
        "step_a": "Complete every same-color anti-diagonal endpoint span with the canonical fill.",
        "intermediate": record,
        "step_b": "Use the unique newly activated relay's touched color and outward vector to cast through post-fill zeros.",
        "why_b_depends_on_a": (
            "Before A, the selected relay has no nonzero neighbor at the touched interior cell; "
            "A creates that colored neighbor, which supplies both B's color and its outward direction."
        ),
    }
