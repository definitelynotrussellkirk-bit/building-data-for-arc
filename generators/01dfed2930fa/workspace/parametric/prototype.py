"""Parametric room-fill family with an exact canonical default.

Both settings first segment color-8 walls into four-connected non-wall rooms.
The canonical setting fills a room only when all nonzero seeds share one color.
The alternative makes the causal intermediate explicit: Step A counts every
seed color per room, and Step B fills zeros only when those counts contain a
strict majority. A first-seed ablation changes the output on every teaching
scene because the minority seed is deliberately row-major first.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random


TASK_ID = "01dfed2930fa"
HERE = Path(__file__).resolve().parent
MODES = ("unique_color", "strict_majority")
ROOM_TYPES = (
    "majority_four",
    "majority_five",
    "monochrome_two",
    "monochrome_five",
    "tie_two",
    "plural_no_majority",
    "unique",
    "empty",
)

# (height, width, room rows, room columns, add non-rectangular wall notches)
DEMO_SPECS = (
    (13, 15, 3, 3, False),
    (13, 17, 3, 3, True),
    (15, 19, 3, 3, False),
    (18, 22, 3, 3, True),
    (21, 25, 3, 4, False),
    (24, 28, 4, 4, True),
)
QUERY_SPECS = (
    (14, 18, 3, 3, False),
    (19, 23, 3, 3, True),
    (25, 27, 3, 4, False),
    (30, 30, 4, 4, True),
)


def _integer(value, label, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (
        maximum is not None and value > maximum
    ):
        raise ValueError(f"{label} must be an exact integer in {minimum}..{maximum}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"fill_policy"}:
        raise ValueError("settings must contain exactly fill_policy")
    value = settings["fill_policy"]
    if type(value) is not str or value not in MODES:
        raise ValueError("fill_policy must be unique_color or strict_majority")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("input must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("input must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("input must be rectangular with exact integer colors 0..9")
    return grid


def _output_grid(grid, shape=None):
    _grid(grid)
    if shape is not None and (len(grid), len(grid[0])) != shape:
        raise ValueError("room-fill output must preserve input dimensions")
    return grid


def program(settings):
    return (HERE / f"{_setting(settings)}.rkt").read_text(encoding="utf-8")


def _regions(grid):
    _grid(grid)
    h, w = len(grid), len(grid[0])
    seen = set()
    regions = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            regions.append(sorted(cells))
    return sorted(regions, key=lambda cells: cells[0])


def _seed_sequence(grid, cells):
    return [grid[r][c] for r, c in sorted(cells) if grid[r][c] not in (0, 8)]


def _unique_winner(seeds):
    colors = set(seeds)
    return next(iter(colors)) if len(colors) == 1 else None


def _strict_majority_winner(seeds):
    if not seeds:
        return None
    counts = Counter(seeds)
    for color in dict.fromkeys(seeds):
        if counts[color] * 2 > len(seeds):
            return color
    return None


def strict_majority_state(grid):
    """Return Step A's room/count intermediate consumed by Step B."""
    rooms = []
    for index, cells in enumerate(_regions(grid)):
        seeds = _seed_sequence(grid, cells)
        counts = Counter(seeds)
        rooms.append(
            {
                "room_index": index,
                "bbox": [
                    min(r for r, _ in cells),
                    min(c for _, c in cells),
                    max(r for r, _ in cells),
                    max(c for _, c in cells),
                ],
                "seed_sequence": list(seeds),
                "seed_counts": {str(color): counts[color] for color in sorted(counts)},
                "seed_total": len(seeds),
                "winner": _strict_majority_winner(seeds),
                "zero_count": sum(grid[r][c] == 0 for r, c in cells),
            }
        )
    return {"rooms": rooms}


def _transform_with_selector(grid, selector):
    _grid(grid)
    output = deepcopy(grid)
    for cells in _regions(grid):
        seeds = _seed_sequence(grid, cells)
        winner = selector(seeds)
        if winner is None:
            continue
        for r, c in cells:
            if output[r][c] == 0:
                output[r][c] = winner
    return output


def transform_first_seed(grid):
    return _transform_with_selector(grid, lambda seeds: seeds[0] if seeds else None)


def transform_plurality(grid):
    def choose(seeds):
        if not seeds:
            return None
        counts = Counter(seeds)
        best = max(counts.values())
        return next(color for color in seeds if counts[color] == best)

    return _transform_with_selector(grid, choose)


def transform_exactly_one_seed_cell(grid):
    return _transform_with_selector(grid, lambda seeds: seeds[0] if len(seeds) == 1 else None)


def transform(grid, settings):
    mode = _setting(settings)
    selector = _unique_winner if mode == "unique_color" else _strict_majority_winner
    return _transform_with_selector(grid, selector)


def _rng(seed, stream, index):
    key = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _segments(total, count):
    usable = total - 2 - (count - 1)
    if usable < 3 * count:
        raise ValueError("room lattice is too dense for its canvas")
    base, extra = divmod(usable, count)
    sizes = [base + (index < extra) for index in range(count)]
    start = 1
    result = []
    for size in sizes:
        result.append((start, start + size))
        start += size + 1
    return result


def _paint_seed_pattern(grid, cells, room_type, colors):
    ordered = sorted(cells)
    if len(ordered) < 6:
        raise ValueError("room is too small for the teaching grammar")
    a, b, c = colors
    patterns = {
        # First row-major seed is deliberately the minority in both causal cases.
        "majority_four": (b, a, a, a),
        "majority_five": (b, b, a, a, a),
        # Equal cardinalities now imply different actions, blocking count lookup.
        "monochrome_two": (a, a),
        "monochrome_five": (a, a, a, a, a),
        "tie_two": (a, b),
        "plural_no_majority": (a, a, b, b, c),
        "unique": (a,),
        "empty": (),
    }
    for (r, col), value in zip(ordered, patterns[room_type]):
        grid[r][col] = value


def _build_scene(seed, stream, source_index, spec):
    h, w, room_rows, room_cols, notches = spec
    rng = _rng(seed, stream + "-scene", source_index)
    row_segments = _segments(h, room_rows)
    col_segments = _segments(w, room_cols)
    grid = [[8 for _ in range(w)] for _ in range(h)]
    rectangles = []
    for r0, r1 in row_segments:
        for c0, c1 in col_segments:
            rectangles.append((r0, r1, c0, c1))
            for r in range(r0, r1):
                for c in range(c0, c1):
                    grid[r][c] = 0

    if notches:
        # A one-cell wall hole/protrusion makes selected rooms non-rectangular
        # without disconnecting them or concentrating content in one corner.
        for index, (r0, r1, c0, c1) in enumerate(rectangles):
            if index % 2 == 0 and r1 - r0 >= 4 and c1 - c0 >= 4:
                grid[r0 + (r1 - r0) // 2][c0 + (c1 - c0) // 2] = 8

    regions = _regions(grid)
    if len(regions) < len(ROOM_TYPES):
        raise ValueError("scene must contain every teaching room type")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 8)
    rotation = rng.randrange(len(ROOM_TYPES))
    room_types = ROOM_TYPES[rotation:] + ROOM_TYPES[:rotation]
    for index, cells in enumerate(regions):
        room_type = room_types[index % len(room_types)]
        colors = (
            palette[index % len(palette)],
            palette[(index + 3) % len(palette)],
            palette[(index + 5) % len(palette)],
        )
        _paint_seed_pattern(grid, cells, room_type, colors)
    return grid


def _query_order(seed):
    order = list(range(len(QUERY_SPECS)))
    _rng(seed, "test-order", 0).shuffle(order)
    return order


def sample_input(seed, stream, index):
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(index, "index", 0)
    if stream == "train":
        if index >= len(DEMO_SPECS):
            raise ValueError("index exceeds the bounded demonstration bank")
        source_index = index
        spec = DEMO_SPECS[source_index]
    elif stream == "test":
        if index >= len(QUERY_SPECS):
            raise ValueError("index exceeds the bounded query bank")
        source_index = _query_order(seed)[index]
        spec = QUERY_SPECS[source_index]
    else:
        raise ValueError("stream must be train or test")
    return _build_scene(seed, stream, source_index, spec)


def generate(seed, settings, demos, queries):
    """Native adapter contract with matched inputs and query-prefix stability."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    episode = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("deterministic sampler produced duplicate inputs")
            seen.add(key)
            episode[split].append({"input": grid, "output": transform(grid, settings)})
    return episode


def hypotheses(settings):
    _setting(settings)
    return {
        **{f"setting:{mode}": program({"fill_policy": mode}) for mode in MODES},
        "identity": "(rule! (lambda (g) g))",
        "first_seed": (HERE / "first_seed.rkt").read_text(encoding="utf-8"),
        "plurality": (HERE / "plurality.rkt").read_text(encoding="utf-8"),
        "exactly_one_seed_cell": (HERE / "exactly_one_seed_cell.rkt").read_text(encoding="utf-8"),
        "seed_count_lookup": (HERE / "seed_count_lookup.rkt").read_text(encoding="utf-8"),
        "three_of_four_only": (HERE / "three_of_four_only.rkt").read_text(encoding="utf-8"),
    }


class Reference:
    """One protected-Racket process reused across bounded authoring checks."""

    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=15.0)
        self.names = {}
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.bridge.shutdown()

    def apply(self, source, grid):
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        if source not in self.names:
            name = "room_fill_rule_" + str(len(self.names))
            self.bridge.eval_text(f"(define {name} {wrap_rule(source)})")
            self.names[source] = name
        self.bridge.define_grid("room_fill_input", grid)
        output = self.bridge.eval_text(f"({self.names[source]} room_fill_input)")
        self.calls += 1
        return deepcopy(_output_grid(output, (len(grid), len(grid[0]))))


def fit_demonstrations(train, settings, reference):
    programs = hypotheses(settings)
    survivors = []
    rejected = {}
    for name, source in programs.items():
        mismatches = []
        for index, pair in enumerate(train):
            if reference.apply(source, pair["input"]) != pair["output"]:
                mismatches.append(index)
        if mismatches:
            rejected[name] = mismatches
        else:
            survivors.append(name)
    return {
        "survivors": survivors,
        "rejected_by_demo": rejected,
        "program_sha256": {
            name: hashlib.sha256(source.encode()).hexdigest() for name, source in programs.items()
        },
    }


def verify_episode(episode, reference):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = episode.get("settings")
    chosen = _setting(settings)
    if episode.get("program_solution") != program(settings):
        raise ValueError("episode program differs from its fixed setting")
    seen = set()
    for split, minimum, maximum in (("train", 2, 6), ("test", 1, 4)):
        pairs = episode.get(split)
        if type(pairs) is not list or not minimum <= len(pairs) <= maximum:
            raise ValueError(f"{split} count must be in {minimum}..{maximum}")
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                raise ValueError("every private pair needs input and output")
            source_grid = _grid(pair["input"])
            _output_grid(pair["output"], (len(source_grid), len(source_grid[0])))
            key = json.dumps(source_grid, separators=(",", ":"))
            if key in seen:
                raise ValueError("duplicate demonstration/query input")
            seen.add(key)
            if reference.apply(program(settings), source_grid) != pair["output"]:
                raise ValueError("claimed output differs from executed Racket")
    fit = fit_demonstrations(episode["train"], settings, reference)
    if fit["survivors"] != ["setting:" + chosen]:
        raise ValueError("demonstrations do not uniquely identify the selected finite setting")
    programs = hypotheses(settings)
    checks = []
    for index, pair in enumerate(episode["test"]):
        for name in fit["survivors"]:
            if reference.apply(programs[name], pair["input"]) != pair["output"]:
                raise ValueError(f"demonstrations do not identify query {index}: {name}")
        checks.append({"query_index": index, "identified_from_demonstrations": True})
    return {
        "schema": "room-fill-policy-finite-rivals-v1",
        **fit,
        "fit_uses": "demonstrations_only",
        "query_checks": checks,
        "limit": "Only two declared settings and six named shortcuts are tested.",
    }


def source_bindings():
    files = [
        HERE / name
        for name in (
            "prototype.py",
            "adapter.py",
            "promotion.json",
            "unique_color.rkt",
            "strict_majority.rkt",
            "first_seed.rkt",
            "plurality.rkt",
            "exactly_one_seed_cell.rkt",
            "seed_count_lookup.rkt",
            "three_of_four_only.rkt",
            "probe.py",
        )
    ]
    files.append(HERE.parents[1] / "generator.py")
    return {
        str(path.relative_to(HERE.parents[3])): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in files
    }
