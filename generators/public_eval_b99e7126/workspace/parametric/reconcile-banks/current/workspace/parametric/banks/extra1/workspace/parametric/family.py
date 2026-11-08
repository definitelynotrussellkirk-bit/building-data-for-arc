"""Self-similar periodic-lattice completion for public parent b99e7126.

A modal-color separator lattice contains one repeated ordinary 3x3 tile and
several copies of one anomalous tile.  The anomalous tile introduces one ink
color absent from the ordinary tile.  Its ink mask is also the macro pattern:
translate that mask so it covers every anomalous clue tile, then place copies of
the anomalous tile at all selected macro positions.

The canonical setting uses the complete ink mask.  The alternate setting uses
only its unique largest four-connected component.  Generated clues come from
that component, so both settings receive identical lawful inputs while the
missing disconnected component distinguishes the rules.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import random

SCOPES = ("all_ink", "largest_component")
RIVALS = ("other_setting", "clue_only", "bbox", "smallest_component", "rotate_cw", "transpose")


def _rng(seed: int, tag: str) -> random.Random:
    raw = hashlib.sha256(f"b99e7126:{seed}:{tag}".encode()).digest()
    return random.Random(int.from_bytes(raw, "big"))


def validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("rectangular grid required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    return tuple(tuple(row) for row in grid)


def _modal(values):
    counts = Counter(values)
    return min(counts, key=lambda v: (-counts[v], v))


def _bands(separators):
    return [(a + 1, b - 1) for a, b in zip(separators, separators[1:]) if a + 1 <= b - 1]


def _components(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        q = [start]
        remaining.remove(start)
        comp = []
        while q:
            r, c = q.pop()
            comp.append((r, c))
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    q.append(p)
        result.append(tuple(sorted(comp)))
    return tuple(sorted(result, key=lambda x: x[0]))


def _tile(grid, rb, cb):
    return tuple(tuple(grid[r][c] for c in range(cb[0], cb[1] + 1)) for r in range(rb[0], rb[1] + 1))


def analyze(grid):
    g = validate_grid(grid)
    h, w = len(g), len(g[0])
    bg = _modal(v for row in g for v in row)
    sep_rows = [r for r, row in enumerate(g) if all(v == bg for v in row)]
    sep_cols = [c for c in range(w) if all(g[r][c] == bg for r in range(h))]
    row_bands, col_bands = _bands(sep_rows), _bands(sep_cols)
    if len(row_bands) < 3 or len(col_bands) < 3:
        raise ValueError("at least a 3x3 separator lattice is required")
    heights = {b - a + 1 for a, b in row_bands}
    widths = {b - a + 1 for a, b in col_bands}
    if len(heights) != 1 or len(widths) != 1:
        raise ValueError("uniform tile dimensions required")
    th, tw = next(iter(heights)), next(iter(widths))
    if not 2 <= th <= 5 or not 2 <= tw <= 5:
        raise ValueError("tile dimensions outside supported grammar")
    records = []
    for ri, rb in enumerate(row_bands):
        for ci, cb in enumerate(col_bands):
            records.append((ri, ci, _tile(g, rb, cb)))
    counts = Counter(tile for _, _, tile in records)
    if len(counts) != 2:
        raise ValueError("exactly one ordinary and one anomalous tile pattern required")
    base = min(counts, key=lambda tile: (-counts[tile], tile))
    anomalies = [(ri, ci, tile) for ri, ci, tile in records if tile != base]
    if not anomalies or any(tile != anomalies[0][2] for _, _, tile in anomalies):
        raise ValueError("all anomalous clue tiles must match")
    anomaly = anomalies[0][2]
    base_colors = {v for row in base for v in row}
    introduced = sorted({v for row in anomaly for v in row} - base_colors)
    if len(introduced) != 1:
        raise ValueError("anomalous tile must introduce exactly one ink color")
    ink = introduced[0]
    mask = tuple(sorted((r, c) for r, row in enumerate(anomaly) for c, v in enumerate(row) if v == ink))
    if not mask:
        raise ValueError("empty ink mask")
    components = _components(mask)
    clues = tuple(sorted((ri, ci) for ri, ci, _ in anomalies))
    anchors = []
    for ar in range(len(row_bands) - th + 1):
        for ac in range(len(col_bands) - tw + 1):
            target = {(ar + r, ac + c) for r, c in mask}
            if set(clues) <= target:
                anchors.append((ar, ac))
    if len(anchors) != 1:
        raise ValueError(f"expected unique mask translation, found {len(anchors)}")
    return {
        "grid": g,
        "background": bg,
        "row_bands": tuple(row_bands),
        "col_bands": tuple(col_bands),
        "tile_height": th,
        "tile_width": tw,
        "base_tile": base,
        "anomaly_tile": anomaly,
        "ink": ink,
        "mask": mask,
        "components": components,
        "clues": clues,
        "anchor": anchors[0],
    }


def _selected_mask(info, scope, rival=None):
    if scope not in SCOPES:
        raise ValueError("unknown scope")
    if rival == "other_setting":
        scope = SCOPES[1 - SCOPES.index(scope)]
    if rival == "all_ink":
        scope = "all_ink"
    if rival == "largest_component":
        scope = "largest_component"
    mask = tuple(info["mask"])
    comps = info["components"]
    if scope == "largest_component":
        mask = max(comps, key=lambda comp: (len(comp), tuple(reversed(comp))))
    if rival == "clue_only":
        return ()
    if rival == "bbox":
        return tuple((r, c) for r in range(info["tile_height"]) for c in range(info["tile_width"]))
    if rival == "smallest_component":
        return min(comps, key=lambda comp: (len(comp), comp))
    if rival == "rotate_cw":
        h = info["tile_height"]
        return tuple(sorted((c, h - 1 - r) for r, c in mask))
    if rival == "transpose":
        return tuple(sorted((c, r) for r, c in mask))
    return tuple(mask)


def _render(info, selected_mask):
    out = [list(row) for row in info["grid"]]
    ar, ac = info["anchor"]
    tile = info["anomaly_tile"]
    for mr, mc in ((ar + r, ac + c) for r, c in selected_mask):
        if not (0 <= mr < len(info["row_bands"]) and 0 <= mc < len(info["col_bands"])):
            continue
        r1, r2 = info["row_bands"][mr]
        c1, c2 = info["col_bands"][mc]
        for r in range(r2 - r1 + 1):
            for c in range(c2 - c1 + 1):
                out[r1 + r][c1 + c] = tile[r][c]
    return out


def solve(grid, scope="all_ink", *, rival=None):
    if rival is not None and rival not in RIVALS and rival not in {"all_ink", "largest_component"}:
        raise ValueError("unknown rival")
    info = analyze(grid)
    return _render(info, _selected_mask(info, scope, rival))


def _unique_subset(mask, large):
    mask = set(mask)
    large = tuple(sorted(large))
    for size in range(min(4, len(large) - 1), 1, -1):
        for subset in itertools.combinations(large, size):
            subset = set(subset)
            ok = True
            for source in (mask, set(large)):
                shifts = []
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        shifted = {(r + dr, c + dc) for r, c in source}
                        if subset <= shifted:
                            shifts.append((dr, dc))
                if shifts != [(0, 0)]:
                    ok = False
                    break
            if ok:
                return tuple(sorted(subset))
    return None


def _sample_mask(rng):
    cells = [(r, c) for r in range(3) for c in range(3)]
    for _ in range(512):
        count = rng.choice((6, 7))
        mask = tuple(sorted(rng.sample(cells, count)))
        comps = _components(mask)
        if len(comps) != 2:
            continue
        sizes = sorted((len(c) for c in comps), reverse=True)
        if sizes[0] <= sizes[1] or sizes[0] < 4:
            continue
        large = max(comps, key=len)
        subset = _unique_subset(mask, large)
        if subset is None:
            continue
        rotate = tuple(sorted((c, 2 - r) for r, c in mask))
        trans = tuple(sorted((c, r) for r, c in mask))
        if rotate == mask or trans == mask:
            continue
        return mask, large, subset
    raise ValueError("bounded asymmetric mask construction exhausted")


def _scene(seed, tag, *, stress=False, attempt=0):
    rng = _rng(seed, f"{tag}:{attempt}")
    n = 7 if stress else rng.choice((5, 6, 7))
    mask, large, clues_local = _sample_mask(rng)
    anchor = (rng.randrange(n - 2), rng.randrange(n - 2))
    colors = rng.sample(range(10), 4)
    bg, base_a, base_b, ink = colors
    # Balanced ordinary tile keeps the separator color modal.
    positions = [(r, c) for r in range(3) for c in range(3)]
    rng.shuffle(positions)
    a_cells = set(positions[:4])
    base = [[base_a if (r, c) in a_cells else base_b for c in range(3)] for r in range(3)]
    fill = rng.choice((base_a, base_b))
    anomaly = [[ink if (r, c) in set(mask) else fill for c in range(3)] for r in range(3)]
    size = 4 * n + 1
    grid = [[bg for _ in range(size)] for _ in range(size)]
    for mr in range(n):
        for mc in range(n):
            r0, c0 = 4 * mr + 1, 4 * mc + 1
            for r in range(3):
                for c in range(3):
                    grid[r0 + r][c0 + c] = base[r][c]
    for r, c in clues_local:
        mr, mc = anchor[0] + r, anchor[1] + c
        r0, c0 = 4 * mr + 1, 4 * mc + 1
        for rr in range(3):
            for cc in range(3):
                grid[r0 + rr][c0 + cc] = anomaly[rr][cc]
    return grid


def _distinguishes_all(grid):
    for scope in SCOPES:
        correct = solve(grid, scope)
        for rival in RIVALS:
            if solve(grid, scope, rival=rival) == correct:
                return False
    return True


@lru_cache(maxsize=128)
def _inputs(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError("nonnegative integer seed required")
    demos = []
    used = set()
    for index in range(6):
        found = None
        for attempt in range(256):
            grid = _scene(seed, f"demo:{index}", attempt=attempt)
            key = validate_grid(grid)
            if key not in used and _distinguishes_all(grid):
                found = grid
                break
        if found is None:
            raise ValueError("bounded distinguishing demonstration search exhausted")
        used.add(validate_grid(found))
        demos.append(found)
    queries = []
    for index in range(4):
        found = None
        for attempt in range(256):
            grid = _scene(seed, f"query:{index}", stress=index == 3, attempt=attempt)
            key = validate_grid(grid)
            if key not in used and _distinguishes_all(grid):
                found = grid
                break
        if found is None:
            raise ValueError("bounded distinct query search exhausted")
        used.add(validate_grid(found))
        queries.append(found)
    return tuple(validate_grid(g) for g in demos), tuple(validate_grid(g) for g in queries)


def _request(seed, settings, demos, queries):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in [0, 2^63)")
    if type(settings) is not dict or set(settings) != {"scope"} or settings["scope"] not in SCOPES:
        raise ValueError("one declared scope setting required")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be 1..4")
    return settings["scope"]


def program(settings):
    scope = _request(0, settings, 2, 4)
    name = "canonical.rkt" if scope == "all_ink" else "largest-component.rkt"
    return Path(__file__).with_name(name).read_text()


def generate(seed, settings, demos, queries):
    scope = _request(seed, settings, demos, queries)
    ds, qs = _inputs(seed)
    pair = lambda g: {"input": [list(row) for row in g], "output": solve(g, scope)}
    return {
        "train": [pair(g) for g in ds[:demos]],
        "test": [pair(g) for g in qs[:queries]],
        "program_solution": program(settings),
    }


def present(seed, settings, demos, queries, presentation_seed=0):
    _request(seed, settings, demos, queries)
    if type(presentation_seed) is not int:
        raise ValueError("integer presentation seed required")
    episode = generate(seed, settings, demos, 4)
    order = list(range(4))
    _rng(seed, f"presentation:{presentation_seed}").shuffle(order)
    public = []
    for index in order[:queries]:
        public.append({
            "train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][index]["input"])}],
        })
    return {
        "public": public,
        "private": {
            "seed": seed,
            "settings": deepcopy(settings),
            "presentation_seed": presentation_seed,
            "source_indices": order[:queries],
            "program": episode["program_solution"],
            "source_pairs": deepcopy(episode["test"]),
        },
    }


def intermediate(grid, settings):
    scope = _request(0, settings, 2, 4)
    info = analyze(grid)
    selected = _selected_mask(info, scope)
    counter = _selected_mask(info, scope, "other_setting")
    return {
        "ink": info["ink"],
        "anchor": list(info["anchor"]),
        "full_mask": [list(p) for p in info["mask"]],
        "components": [[list(p) for p in comp] for comp in info["components"]],
        "selected_mask": [list(p) for p in selected],
        "counterfactual_mask": [list(p) for p in counter],
    }


def dependency():
    return {
        "step_a": "Infer the separator lattice, identify the anomalous tile's newly introduced ink color, and segment its input-derived ink mask into four-connected components.",
        "intermediate": "The translated complete ink mask or its unique largest component, together with the unique macro-grid anchor covering all visible anomalous clue tiles.",
        "step_b": "Copy the complete anomalous tile into every macro position selected by that translated mask while preserving separators and ordinary tiles elsewhere.",
        "why_b_depends_on_a": "The macro positions are not fixed: their shape and anchor are encoded by the anomalous tile and visible clues in each input. Replacing the chosen mask with the other setting changes which tiles are completed while leaving the renderer unchanged.",
    }


def self_check(grid, **_):
    try:
        info = analyze(grid)
        if solve(grid, "all_ink") == [list(row) for row in info["grid"]]:
            return ["canonical completion must add at least one tile"]
        if len(info["components"]) < 2:
            return ["generated mask must have multiple components"]
        if len(max(info["components"], key=len)) == len(info["mask"]):
            return ["settings must disagree"]
        return []
    except (TypeError, ValueError) as exc:
        return [str(exc)]


def ordinary(seed, sample_index, *, stress=False):
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError("nonnegative exact integer seed and sample_index required")
    for attempt in range(256):
        grid = _scene(seed, f"ordinary:{sample_index}", stress=stress, attempt=attempt)
        if not self_check(grid):
            return grid
    raise ValueError("bounded ordinary generation exhausted")
