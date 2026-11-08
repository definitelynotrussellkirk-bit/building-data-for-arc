"""Multicolor ship ejection and post-clipping ray selection.

Each two-color 8-connected object has a majority-colored hull and minority-
colored particles.  Particles are removed from the hull and emitted from the
unique nose.  The alternate setting selects after clipping, making the visible
ray length a genuine intermediate rather than a restatement of payload count.
"""
from __future__ import annotations

import copy
from collections import Counter
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = ("all_rays", "longest_visible")
EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
DIRECTIONS = (
    ("up", -1, 0),
    ("down", 1, 0),
    ("left", 0, -1),
    ("right", 0, 1),
)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def grid(value):
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("expected a rectangular 1..30 grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact integers in 0..9")
    return value


def setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"selection"}
        or type(settings["selection"]) is not str
        or settings["selection"] not in MODES
    ):
        raise ValueError("settings must name exactly one declared selection")
    return settings["selection"]


def program(settings):
    name = "canonical.rkt" if setting(settings) == "all_rays" else "longest_visible.rkt"
    return (HERE / name).read_text()


def _components(value):
    g = grid(value)
    h, w = len(g), len(g[0])
    todo = {(r, c) for r in range(h) for c in range(w) if g[r][c] != 0}
    out = []
    while todo:
        start = min(todo)
        todo.remove(start)
        stack = [start]
        component = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in EIGHT:
                q = (r + dr, c + dc)
                if q in todo:
                    todo.remove(q)
                    stack.append(q)
                    component.add(q)
        out.append(component)
    return out


def _argmax_first(values, key):
    if not values:
        raise ValueError("expected a nonempty sequence")
    best = values[0]
    best_key = key(best)
    for value in values[1:]:
        candidate = key(value)
        if candidate > best_key:
            best, best_key = value, candidate
    return best


def _argmin_first(values, key):
    if not values:
        raise ValueError("expected a nonempty sequence")
    best = values[0]
    best_key = key(best)
    for value in values[1:]:
        candidate = key(value)
        if candidate < best_key:
            best, best_key = value, candidate
    return best


def _direction(cells, body_cells):
    candidates = []
    for name, dr, dc in DIRECTIONS:
        extreme = max(r * dr + c * dc for r, c in body_cells)
        tips = sorted((r, c) for r, c in body_cells if r * dr + c * dc == extreme)
        if len(tips) != 1:
            continue
        tip = tips[0]
        inward = (-dr, -dc)
        perpendicular = (-dc, dr)
        cone = full = center = 0
        for depth in range(1, 5):
            layer = {
                (
                    tip[0] + inward[0] * depth + perpendicular[0] * offset,
                    tip[1] + inward[1] * depth + perpendicular[1] * offset,
                )
                for offset in range(-depth, depth + 1)
            }
            occupied = sum(point in cells for point in layer)
            cone += occupied
            full += occupied == len(layer)
            center += (
                tip[0] + inward[0] * depth,
                tip[1] + inward[1] * depth,
            ) in cells
        # The 100/10/1 encoding is simply lexicographic (cone, full, center),
        # with stable direction order resolving a true tie.
        score = cone * 100 + full * 10 + center
        candidates.append((score, name, dr, dc, tip, cone, full, center))
    if not candidates:
        raise ValueError("ship hull has no unique directional nose")
    return _argmax_first(candidates, lambda item: item[0])


def descriptors(value):
    g = grid(value)
    h, w = len(g), len(g[0])
    result = []
    for component in _components(g):
        counts = Counter(g[r][c] for r, c in component)
        if len(counts) != 2:
            continue
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        (body_color, body_count), (payload_color, payload_count) = ordered
        if body_count <= payload_count:
            continue
        body_cells = {p for p in component if g[p[0]][p[1]] == body_color}
        payload_cells = {p for p in component if g[p[0]][p[1]] == payload_color}
        score, name, dr, dc, tip, cone, full, center = _direction(component, body_cells)
        ray = [
            (tip[0] + dr * step, tip[1] + dc * step)
            for step in range(1, payload_count + 1)
            if 0 <= tip[0] + dr * step < h and 0 <= tip[1] + dc * step < w
        ]
        result.append(
            {
                "index": len(result),
                "component": component,
                "body_color": body_color,
                "payload_color": payload_color,
                "body_cells": body_cells,
                "payload_cells": payload_cells,
                "payload_count": payload_count,
                "direction": name,
                "vector": (dr, dc),
                "tip": tip,
                "ray_cells": ray,
                "visible_length": len(ray),
                "direction_score": score,
                "cone_score": cone,
                "full_layers": full,
                "center_layers": center,
            }
        )
    if not result:
        raise ValueError("expected at least one two-color ship")
    return result


def _render(value, selected=None):
    g = grid(value)
    ships = descriptors(g)
    out = [row[:] for row in g]
    for ship in ships:
        for r, c in ship["payload_cells"]:
            out[r][c] = 0
    chosen = set(range(len(ships))) if selected is None else {selected}
    for ship in ships:
        if ship["index"] not in chosen:
            continue
        for r, c in ship["ray_cells"]:
            out[r][c] = ship["payload_color"]
    return out, ships


def solve(value, mode="all_rays"):
    if mode not in MODES:
        raise ValueError("unknown selection mode")
    if mode == "all_rays":
        return _render(value)[0]
    ships = descriptors(value)
    selected = _argmax_first(ships, lambda ship: ship["visible_length"])
    return _render(value, selected["index"])[0]


def counterfactual(value):
    """Wrong order: choose the largest payload before rays are clipped."""
    ships = descriptors(value)
    selected = _argmax_first(ships, lambda ship: ship["payload_count"])
    return _render(value, selected["index"])[0]


def causal_intermediate(value):
    ships = descriptors(value)
    visible = _argmax_first(ships, lambda ship: ship["visible_length"])
    before = _argmax_first(ships, lambda ship: ship["payload_count"])
    return {
        "payload_counts": [ship["payload_count"] for ship in ships],
        "visible_lengths": [ship["visible_length"] for ship in ships],
        "directions": [ship["direction"] for ship in ships],
        "payload_colors": [ship["payload_color"] for ship in ships],
        "selected_index": visible["index"],
        "pre_ejection_selected_index": before["index"],
    }


def _seeded(seed, label):
    raw = hashlib.sha256(f"public_eval_3dc255db:{seed}:{label}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def _paint_ship(g, tip, direction, body_color, payload_color, payload_count):
    h, w = len(g), len(g[0])
    vectors = {name: (dr, dc) for name, dr, dc in DIRECTIONS}
    if direction not in vectors:
        raise ValueError(direction)
    dr, dc = vectors[direction]
    inward = (-dr, -dc)
    perpendicular = (-dc, dr)
    cells = []
    by_layer = {}
    for depth in range(4):
        layer = []
        for offset in range(-depth, depth + 1):
            point = (
                tip[0] + inward[0] * depth + perpendicular[0] * offset,
                tip[1] + inward[1] * depth + perpendicular[1] * offset,
            )
            if not (0 <= point[0] < h and 0 <= point[1] < w):
                raise ValueError("ship leaves canvas")
            if g[point[0]][point[1]] != 0:
                raise ValueError("ships overlap")
            cells.append(point)
            layer.append(point)
        by_layer[depth] = layer
    candidates = [
        by_layer[2][2],
        by_layer[2][1],
        by_layer[2][3],
        by_layer[3][3],
        by_layer[3][2],
        by_layer[3][4],
    ]
    if not 1 <= payload_count <= len(candidates):
        raise ValueError("payload_count must be 1..6")
    payload = set(candidates[:payload_count])
    for r, c in cells:
        g[r][c] = payload_color if (r, c) in payload else body_color
    return {"cells": set(cells), "payload": payload}


def _regular_specs(index, h, w):
    profiles = {
        # Pre-ejection winner is first; post-clipping winner is last.
        0: [((1, 4), "up", 4, 6, 5), ((10, w - 4), "right", 3, 7, 3)],
        # Post-clipping winner is first; pre-ejection winner is last.
        1: [((4, w - 4), "right", 6, 2, 3), ((h - 2, 5), "down", 4, 9, 5)],
        2: [((4, 4), "left", 7, 3, 3), ((h - 5, w - 5), "down", 2, 8, 4)],
        3: [((h - 4, 4), "down", 8, 4, 3), ((5, w - 5), "up", 3, 6, 4)],
        4: [((5, 2), "left", 5, 8, 2), ((h - 5, w - 4), "right", 2, 4, 4)],
        5: [((2, w // 2), "up", 9, 3, 4), ((h - 3, 5), "down", 6, 7, 3)],
        6: [((4, w - 3), "right", 4, 2, 3), ((h - 5, 4), "left", 7, 9, 5)],
        7: [((2, 5), "up", 2, 8, 5), ((h - 5, w - 5), "down", 6, 3, 4)],
        8: [((h // 2, 2), "left", 9, 4, 2), ((4, w - 4), "right", 3, 7, 5)],
    }
    return profiles[index]


def scene(seed, index):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(index, 0, 2**31 - 1, "index")
    profile = index % 10
    if profile == 9:
        h = w = 30
        specs = [
            ((2, 4), "up", 4, 6, 4),
            ((7, 26), "right", 3, 7, 5),
            ((27, 5), "down", 8, 2, 3),
            ((19, 2), "left", 5, 9, 2),
            ((13, 17), "up", 2, 4, 6),
        ]
    else:
        h = 18 + ((seed + profile) % 4)
        w = 22 + ((seed * 3 + profile) % 4)
        specs = _regular_specs(profile, h, w)
    # Counts, geometry and palette jointly vary across profiles.  Keep the
    # first two palettes fixed so numeric-color shortcuts are constructively
    # contradicted by the minimum lesson for every seed.
    g = [[0] * w for _ in range(h)]
    used_colors = set()
    for tip, direction, body, payload, count in specs:
        if body == payload:
            raise AssertionError("body and payload colors collided")
        _paint_ship(g, tip, direction, body, payload, count)
        used_colors.add(payload)
    # A single connected color-1 barcode gives the bounded seed sweep genuinely
    # different inputs without multiplying the number of ignored components.
    # It is placed in a padded empty rectangle outside all future ray cells.
    raw_info = descriptors(g)
    future_rays = {p for ship in raw_info for p in ship["ray_cells"]}
    signature = None
    for r0 in range(1, h - 3):
        for c0 in range(1, w - 7):
            padded = {
                (r, c)
                for r in range(r0 - 1, r0 + 4)
                for c in range(c0 - 1, c0 + 8)
            }
            if all(g[r][c] == 0 and (r, c) not in future_rays for r, c in padded):
                signature = (r0, c0)
                break
        if signature is not None:
            break
    if signature is None:
        raise AssertionError("no padded barcode location")
    r0, c0 = signature
    for c in range(c0, c0 + 7):
        g[r0 + 1][c] = 1
    for bit in range(6):
        if (seed >> bit) & 1:
            g[r0][c0 + bit + 1] = 1

    # A separate same-palette particle mirrors the official parents and verifies
    # that only minority cells embedded in a two-color ship are ejected.
    placed = False
    for r in range(h - 1, -1, -1):
        for c in range(w - 1, -1, -1):
            if g[r][c] != 0 or (r, c) in future_rays:
                continue
            if all(
                not (0 <= r + dr < h and 0 <= c + dc < w and g[r + dr][c + dc] != 0)
                for dr, dc in EIGHT
            ):
                g[r][c] = min(used_colors)
                placed = True
                break
        if placed:
            break
    if not placed:
        raise AssertionError("no isolated same-palette decoy location")
    info = descriptors(g)
    if len(info) != len(specs):
        raise AssertionError("generated ships merged or were not recognized")
    if profile in (0, 1):
        causal = causal_intermediate(g)
        if causal["selected_index"] == causal["pre_ejection_selected_index"]:
            raise AssertionError("teaching profile failed to reverse the winner")
    return g


def generate(seed, settings, demos=2, queries=4):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(demos, 2, 6, "demos")
    integer(queries, 1, 4, "queries")
    mode = setting(settings)

    def pair(index):
        value = scene(seed, index)
        return {"input": value, "output": solve(value, mode)}

    return {
        "train": [pair(i) for i in range(demos)],
        "test": [pair(i) for i in range(6, 6 + queries)],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def query_order(presentation_seed=0):
    integer(presentation_seed, 0, 2**63 - 1, "presentation_seed")
    order = list(range(4))
    _seeded(presentation_seed, "presentation").shuffle(order)
    return order


def public_turn(episode, turn, *, presentation_seed=0):
    integer(turn, 0, 3, "turn")
    if type(episode) is not dict:
        raise ValueError("episode must be a private episode mapping")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("invalid private demonstrations")
    if type(test) is not list or len(test) != 4:
        raise ValueError("project from the complete four-query private bank")
    index = query_order(presentation_seed)[turn]
    return copy.deepcopy(
        {
            "train": [
                {"input": grid(pair["input"]), "output": grid(pair["output"])}
                for pair in train
            ],
            "test": [{"input": grid(test[index]["input"])}],
        }
    )


def _select(value, chooser):
    ships = descriptors(value)
    selected = chooser(ships)
    return _render(value, selected["index"])[0]


def rival(value, name):
    if name in MODES:
        return solve(value, name)
    if name == "pre_ejection_longest":
        return counterfactual(value)
    if name == "identity":
        return copy.deepcopy(grid(value))
    if name == "erase_payloads":
        out = [row[:] for row in grid(value)]
        for ship in descriptors(value):
            for r, c in ship["payload_cells"]:
                out[r][c] = 0
        return out
    selectors = {
        "shortest_visible": lambda ships: _argmin_first(ships, lambda s: s["visible_length"]),
        "first_ship": lambda ships: ships[0],
        "last_ship": lambda ships: ships[-1],
        "maximum_payload_color": lambda ships: _argmax_first(ships, lambda s: s["payload_color"]),
        "minimum_payload_color": lambda ships: _argmin_first(ships, lambda s: s["payload_color"]),
        "maximum_body_color": lambda ships: _argmax_first(ships, lambda s: s["body_color"]),
    }
    if name not in selectors:
        raise ValueError(name)
    return _select(value, selectors[name])


RIVALS = MODES + (
    "pre_ejection_longest",
    "shortest_visible",
    "first_ship",
    "last_ship",
    "maximum_payload_color",
    "minimum_payload_color",
    "maximum_body_color",
    "identity",
    "erase_payloads",
)
