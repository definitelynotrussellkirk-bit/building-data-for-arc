"""Opt-in parametric episodes for 7e52d15790d7.

The canonical setting is unchanged: sort nonzero 4-connected components by
true edge perimeter, descending.  Nearby settings change the episode-fixed
measurement (perimeter versus area) and direction (descending versus
ascending), while preserving component discovery, cropping, tie-breaking and
gallery packing.

Only ``public/`` files written by :func:`materialize_batch` are model-visible.
Settings, Racket programs and query answers remain in ``private/``.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import tempfile
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "7e52d15790d7"
PROTOTYPE_VERSION = "1.0.0"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
DEFAULT_SETTINGS = {"metric": "perimeter", "direction": "descending"}
SETTINGS = (
    {"metric": "perimeter", "direction": "descending"},
    {"metric": "perimeter", "direction": "ascending"},
    {"metric": "area", "direction": "descending"},
    {"metric": "area", "direction": "ascending"},
)
PUBLIC_SCHEMA = "7e52d15790d7-public-parametric-v1"
PRIVATE_SCHEMA = "7e52d15790d7-private-parametric-v1"
MANIFEST_SCHEMA = "7e52d15790d7-parametric-batch-v1"


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256(path.read_bytes())


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    return _exact_int(demos, "demos", 2, 6), _exact_int(queries, "queries", 1, 4)


def _validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict) or set(settings) != {"metric", "direction"}:
        raise ValueError("settings must contain only metric and direction")
    metric = settings["metric"]
    direction = settings["direction"]
    if type(metric) is not str or metric not in {"perimeter", "area"}:
        raise ValueError("metric must be perimeter or area")
    if type(direction) is not str or direction not in {"descending", "ascending"}:
        raise ValueError("direction must be descending or ascending")
    return {"metric": metric, "direction": direction}


def setting_name(settings: Any) -> str:
    selected = _validate_settings(settings)
    return f"{selected['metric']}/{selected['direction']}"


def canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one unambiguous canonical program")
    return programs.pop()


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"canonical {label} guard expected one occurrence, found {count}")
    return source.replace(old, new, 1)


def program_for(settings: Any = DEFAULT_SETTINGS) -> str:
    """Return exact Racket source for one bounded setting.

    The canonical default is returned byte-for-byte.  Alternative programs are
    guarded, minimal edits to the same authority source.
    """
    selected = _validate_settings(settings)
    source = canonical_program()
    if selected["metric"] == "area":
        source = _replace_once(
            source,
            "(f4-perimeter comp)",
            "(length comp)",
            "metric expression",
        )
    else:
        if source.count("(f4-perimeter comp)") != 1:
            raise ValueError("canonical perimeter guard failed")
    if selected["direction"] == "ascending":
        source = _replace_once(
            source, "(- (first a))", "(first a)", "ascending comparator a"
        )
        source = _replace_once(
            source, "(- (first b))", "(first b)", "ascending comparator b"
        )
    else:
        if source.count("(- (first a))") != 1 or source.count("(- (first b))") != 1:
            raise ValueError("canonical descending comparator guard failed")
    return source


def _program_body(program: str) -> str:
    source = program.strip()
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("program must be one outer rule! form")
    body = source[len("(rule!") : -1].strip()
    if not body:
        raise ValueError("rule! body is empty")
    return body


def execute_rule(program: str, grid: list[list[int]], *, bridge: RacketBridge) -> list[list[int]]:
    bridge.define_grid("g", grid)
    output = bridge.eval_text(_program_body(program))
    _validate_grid(output)
    return output


def _validate_grid(grid: Any) -> list[list[int]]:
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


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform_shape(
    cells: Iterable[tuple[int, int]], code: int
) -> tuple[tuple[int, int], ...]:
    transformed = _normalize(cells)
    if code >= 4:
        transformed = _normalize((row, -col) for row, col in transformed)
    for _ in range(code % 4):
        transformed = _normalize((col, -row) for row, col in transformed)
    return transformed


def _shape(*rows: str) -> tuple[tuple[int, int], ...]:
    cells = tuple(
        (row, col)
        for row, text in enumerate(rows)
        for col, value in enumerate(text)
        if value == "#"
    )
    if not cells:
        raise ValueError("shape must contain cells")
    return _normalize(cells)


SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "square2": _shape("##", "##"),                         # area 4, perimeter 8
    "plus5": _shape(".#.", "###", ".#."),               # area 5, perimeter 12
    "rect2x3": _shape("###", "###"),                      # area 6, perimeter 10
    "c7": _shape("###", "#..", "###"),                  # area 7, perimeter 16
    "a10p22": _shape("####", "#..#", "###.", "#..."),  # area 10, perimeter 22
    "a11p18": _shape("####", "##.#", "####"),           # area 11, perimeter 18
    "a12p26": _shape("####", ".#.#", "#.##", "###."), # area 12, perimeter 26
    "a13p20": _shape("####", "####", "#.##", "##.."), # area 13, perimeter 20
    "a14p24": _shape("####", "#.##", "##.#", "####"), # area 14, perimeter 24
    "solid4": _shape("####", "####", "####", "####"),  # area 16, perimeter 16
}


def _perimeter(cells: Iterable[tuple[int, int]]) -> int:
    cell_set = set(cells)
    return sum(
        (row + drow, col + dcol) not in cell_set
        for row, col in cell_set
        for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


_EXPECTED_METRICS = {
    "square2": (4, 8),
    "plus5": (5, 12),
    "rect2x3": (6, 10),
    "c7": (7, 16),
    "a10p22": (10, 22),
    "a11p18": (11, 18),
    "a12p26": (12, 26),
    "a13p20": (13, 20),
    "a14p24": (14, 24),
    "solid4": (16, 16),
}
for _name, _cells in SHAPES.items():
    if (len(_cells), _perimeter(_cells)) != _EXPECTED_METRICS[_name]:
        raise AssertionError(f"shape metric drift for {_name}")


def _components_nonzero(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    _validate_grid(grid)
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (row + drow, col + dcol)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] != 0
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(grid: list[list[int]], cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = tuple(cells)
    occupied = set(cells)
    row0, col0, row1, col1 = _bbox(cells)
    return [
        [grid[row][col] if (row, col) in occupied else 0 for col in range(col0, col1 + 1)]
        for row in range(row0, row1 + 1)
    ]


def transform(grid: Any, settings: Any = DEFAULT_SETTINGS) -> list[list[int]]:
    selected = _validate_settings(settings)
    source = _validate_grid(grid)
    records = []
    for cells in _components_nonzero(source):
        row0, col0, _row1, _col1 = _bbox(cells)
        score = _perimeter(cells) if selected["metric"] == "perimeter" else len(cells)
        records.append(
            {
                "score": score,
                "row": row0,
                "col": col0,
                "crop": _crop(source, cells),
            }
        )
    if not records:
        raise ValueError("input must contain at least one nonzero component")
    sign = -1 if selected["direction"] == "descending" else 1
    records.sort(key=lambda item: (sign * item["score"], item["row"], item["col"]))
    height = max(len(item["crop"]) for item in records)
    width = sum(len(item["crop"][0]) for item in records) + len(records) - 1
    if height > 30 or width > 30:
        raise ValueError("gallery output exceeds 30x30")
    output = [[0] * width for _ in range(height)]
    left = 0
    for item in records:
        crop = item["crop"]
        for row, values in enumerate(crop):
            for col, value in enumerate(values):
                if value:
                    output[row][left + col] = value
        left += len(crop[0]) + 1
    return output


def _domain_rng(seed: int, domain: str, index: int) -> random.Random:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    digest = hashlib.sha256(
        f"7e52d15790d7-parametric-v1:{seed}:{domain}:{index}".encode("utf-8")
    ).digest()
    return random.Random(digest)


_DEMO_DIMS = ((12, 16), (14, 18), (16, 20), (18, 22), (20, 24), (22, 26))
_DEMO_SHAPES = ("plus5", "rect2x3", "square2")
_QUERY_SPECS = (
    (14, 18, ("square2", "plus5", "rect2x3", "c7")),
    (20, 24, ("square2", "plus5", "rect2x3", "c7", "a10p22")),
    (30, 30, ("a10p22", "a11p18", "a12p26", "a13p20", "a14p24", "solid4")),
    (24, 28, ("a10p22", "a11p18", "a12p26", "a13p20", "a14p24", "solid4")),
)


def _shape_metric_orders(shape_names: tuple[str, ...]) -> set[tuple[int, ...]]:
    orders: set[tuple[int, ...]] = set()
    for settings in SETTINGS:
        metric_index = 1 if settings["metric"] == "perimeter" else 0
        sign = -1 if settings["direction"] == "descending" else 1
        orders.add(
            tuple(
                sorted(
                    range(len(shape_names)),
                    key=lambda index: (
                        sign * _EXPECTED_METRICS[shape_names[index]][metric_index],
                        index,
                    ),
                )
            )
        )
    if len(orders) != 4:
        raise AssertionError(f"profile does not distinguish four settings: {shape_names}")
    return orders


def _choose_assignment(shape_names: tuple[str, ...], rng: random.Random) -> tuple[int, ...]:
    forbidden = _shape_metric_orders(shape_names)
    values = list(range(len(shape_names)))
    for _ in range(128):
        rng.shuffle(values)
        candidate = tuple(values)
        if candidate not in forbidden:
            return candidate
    raise RuntimeError("could not choose a non-shortcut input order")


def _generic_positions(
    height: int,
    width: int,
    dimensions: list[tuple[int, int]],
    assignment: tuple[int, ...],
    rng: random.Random,
    *,
    touch_edges: bool,
) -> dict[int, tuple[int, int]]:
    count = len(assignment)
    slot_rows = 1 if count <= 3 else 2
    slot_cols = math.ceil(count / slot_rows)
    positions: dict[int, tuple[int, int]] = {}
    for slot_index, shape_index in enumerate(assignment):
        slot_row = slot_index // slot_cols
        slot_col = slot_index % slot_cols
        row0 = slot_row * height // slot_rows
        row1 = (slot_row + 1) * height // slot_rows
        col0 = slot_col * width // slot_cols
        col1 = (slot_col + 1) * width // slot_cols
        shape_h, shape_w = dimensions[shape_index]
        low_row = row0 + (0 if row0 == 0 else 1)
        high_row = row1 - shape_h - (0 if row1 == height else 1)
        low_col = col0 + (0 if col0 == 0 else 1)
        high_col = col1 - shape_w - (0 if col1 == width else 1)
        if low_row > high_row or low_col > high_col:
            raise RuntimeError("shape does not fit its separated placement slot")
        top = rng.randint(low_row, high_row)
        left = rng.randint(low_col, high_col)
        if touch_edges and slot_index == 0:
            top, left = 0, 0
        elif touch_edges and slot_index == count - 1:
            top, left = height - shape_h, width - shape_w
        positions[shape_index] = (top, left)
    return positions


def _boundary_positions(
    height: int,
    width: int,
    dimensions: list[tuple[int, int]],
    assignment: tuple[int, ...],
) -> dict[int, tuple[int, int]]:
    if len(assignment) != 6 or (height, width) != (30, 30):
        raise ValueError("boundary layout is defined for the six-object 30x30 query")
    anchors = (
        ("top", "left"),
        ("top", "middle"),
        ("top", "right"),
        ("bottom", "left"),
        ("bottom", "middle"),
        ("bottom", "right"),
    )
    positions: dict[int, tuple[int, int]] = {}
    for shape_index, (vertical, horizontal) in zip(assignment, anchors):
        shape_h, shape_w = dimensions[shape_index]
        top = 0 if vertical == "top" else height - shape_h
        if horizontal == "left":
            left = 0
        elif horizontal == "right":
            left = width - shape_w
        else:
            left = (width - shape_w) // 2
        positions[shape_index] = (top, left)
    return positions


def _make_scene(seed: int, domain: str, index: int) -> list[list[int]]:
    rng = _domain_rng(seed, domain, index)
    if domain == "demo":
        height, width = _DEMO_DIMS[index]
        shape_names = _DEMO_SHAPES
    elif domain == "query":
        height, width, shape_names = _QUERY_SPECS[index]
    else:
        raise ValueError("unknown scene domain")
    shape_names = tuple(shape_names)
    transformed = [
        _transform_shape(SHAPES[name], rng.randrange(8)) for name in shape_names
    ]
    dimensions = [
        (max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1)
        for cells in transformed
    ]
    assignment = _choose_assignment(shape_names, rng)
    if domain == "query" and index == 2:
        positions = _boundary_positions(height, width, dimensions, assignment)
    else:
        positions = _generic_positions(
            height,
            width,
            dimensions,
            assignment,
            rng,
            touch_edges=(domain == "query"),
        )
    colors = list(range(1, 10))
    rng.shuffle(colors)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for shape_index, cells in enumerate(transformed):
        top, left = positions[shape_index]
        color = colors[shape_index]
        absolute = {(top + row, left + col) for row, col in cells}
        if absolute & occupied:
            raise AssertionError("internal placement overlap")
        for row, col in absolute:
            grid[row][col] = color
        occupied.update(absolute)

    components = _components_nonzero(grid)
    if len(components) != len(shape_names):
        raise AssertionError("internal placement merged components")
    component_colors = [{grid[row][col] for row, col in cells} for cells in components]
    if any(len(colors_) != 1 for colors_ in component_colors):
        raise AssertionError("internal component became multicolor")
    outputs = {setting_name(settings): _json_bytes(transform(grid, settings)) for settings in SETTINGS}
    if len(set(outputs.values())) != 4:
        raise AssertionError("scene does not distinguish all four settings")
    return grid


def _sample_inputs(seed: int, demos: int, queries: int) -> tuple[list[list[list[int]]], list[list[list[int]]]]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    demos, queries = _validate_counts(demos, queries)
    train = [_make_scene(seed, "demo", index) for index in range(demos)]
    test = [_make_scene(seed, "query", index) for index in range(queries)]
    frozen = [
        _json_bytes(grid)
        for grid in train + test
    ]
    if len(set(frozen)) != len(frozen):
        raise AssertionError("episode inputs must be distinct")
    return train, test


def generate_claims(seed: int, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    """Return deterministic Python claims for the protected qualification worker."""
    selected = _validate_settings(settings)
    train_inputs, test_inputs = _sample_inputs(seed, demos, queries)
    return {
        "train": [
            {"input": grid, "output": transform(grid, selected)} for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": transform(grid, selected)} for grid in test_inputs
        ],
        "program_solution": program_for(selected),
    }


def lesson_certificate(challenge: Any) -> dict[str, Any]:
    if not isinstance(challenge, dict) or type(challenge.get("train")) is not list:
        raise ValueError("challenge must contain a train list")
    train = challenge["train"]
    if not train:
        raise ValueError("at least one demonstration is required")
    survivors = []
    mismatches: dict[str, list[int]] = {}
    for settings in SETTINGS:
        name = setting_name(settings)
        failed = [
            index
            for index, pair in enumerate(train)
            if transform(pair["input"], settings) != pair["output"]
        ]
        mismatches[name] = failed
        if not failed:
            survivors.append(name)
    return {
        "schema": "7e52d15790d7-demonstration-certificate-v1",
        "demonstrations": len(train),
        "survivors": survivors,
        "identifiable": len(survivors) == 1,
        "mismatch_indices": mismatches,
    }


def source_bindings() -> dict[str, Any]:
    generator = ROOT / "generators" / TASK_ID / "generator.py"
    prototype = Path(__file__).resolve()
    adapter = HERE / "adapter.py"
    promotion = HERE / "promotion.json"
    source = canonical_program()
    paths = {
        "generator": generator,
        "prototype": prototype,
        "adapter": adapter,
        "promotion": promotion,
    }
    for label, path in paths.items():
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"{label} source is missing or escapes the selected tree: {path}")
    return {
        "generator_path": str(generator.relative_to(ROOT)),
        "generator_sha256": _file_sha256(generator),
        "prototype_path": str(prototype.relative_to(ROOT)),
        "prototype_sha256": _file_sha256(prototype),
        "adapter_path": str(adapter.relative_to(ROOT)),
        "adapter_sha256": _file_sha256(adapter),
        "promotion_path": str(promotion.relative_to(ROOT)),
        "promotion_sha256": _file_sha256(promotion),
        "canonical_program_sha256": _sha256(source.encode("utf-8")),
        "prototype_version": PROTOTYPE_VERSION,
    }


def make_episodes(
    seed: int,
    *,
    demos: Any = 3,
    queries: Any = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Execute every setting over one matched input episode in protected Racket."""
    demos, queries = _validate_counts(demos, queries)
    train_inputs, test_inputs = _sample_inputs(seed, demos, queries)
    inputs = train_inputs + test_inputs
    programs = {setting_name(settings): program_for(settings) for settings in SETTINGS}
    outputs: dict[str, list[list[list[int]]]] = {name: [] for name in programs}
    matches = 0
    context = RacketBridge() if bridge is None else nullcontext(bridge)
    with context as active:
        runtime_identity = active.runtime_identity
        for grid in inputs:
            for settings in SETTINGS:
                name = setting_name(settings)
                actual = execute_rule(programs[name], grid, bridge=active)
                expected = transform(grid, settings)
                if actual != expected:
                    raise AssertionError(f"Racket/Python parity failed for {name}")
                matches += 1
                outputs[name].append(actual)

    episodes = []
    bindings = source_bindings()
    for settings in SETTINGS:
        selected = _validate_settings(settings)
        name = setting_name(selected)
        pairs = [
            {"input": grid, "output": outputs[name][index]}
            for index, grid in enumerate(inputs)
        ]
        episode = {
            "schema": "7e52d15790d7-parametric-episode-v1",
            "task_id": TASK_ID,
            "prototype_version": PROTOTYPE_VERSION,
            "seed": seed,
            "settings": selected,
            "train": pairs[:demos],
            "test": pairs[demos:],
            "program_solution": programs[name],
            "program_sha256": _sha256(programs[name].encode("utf-8")),
            "source": bindings,
            "racket_parity": {
                "pairs": len(inputs),
                "settings": len(SETTINGS),
                "matches": matches,
            },
        }
        certificate = lesson_certificate(episode)
        if certificate["survivors"] != [name] or certificate["identifiable"] is not True:
            raise AssertionError(f"demonstrations do not identify {name}")
        episode["certificate"] = certificate
        episodes.append(episode)

    for query_index in range(queries):
        query_outputs = {
            _json_bytes(episode["test"][query_index]["output"]) for episode in episodes
        }
        if len(query_outputs) != len(SETTINGS):
            raise AssertionError(f"query {query_index} does not distinguish all settings")
    return {"episodes": episodes, "runtime_identity": runtime_identity}


def _safe_relative(path_text: Any) -> Path:
    if type(path_text) is not str:
        raise ValueError("manifest paths must be strings")
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe manifest path: {path_text!r}")
    return path


def _write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def materialize_batch(
    *,
    seed: int,
    demos: Any = 3,
    queries: Any = 4,
    out: Path,
) -> dict[str, Any]:
    """Write a strict all-setting public/private batch, manifest last."""
    demos, queries = _validate_counts(demos, queries)
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    try:
        generated = make_episodes(seed, demos=demos, queries=queries)
        rows = []
        seen_public: set[str] = set()
        for episode in generated["episodes"]:
            public_bytes = public_challenge_bytes(episode)
            public_id = public_challenge_id(episode)
            if public_id in seen_public:
                raise ValueError("duplicate visible public challenge")
            seen_public.add(public_id)
            public_rel = Path("public") / f"{public_id}.json"
            private_rel = Path("private") / f"{public_id}.json"
            private = {
                "schema": PRIVATE_SCHEMA,
                "task_id": TASK_ID,
                "public_id": public_id,
                "seed": seed,
                "counts": {"demos": demos, "queries": queries},
                "settings": episode["settings"],
                "program_solution": episode["program_solution"],
                "program_sha256": episode["program_sha256"],
                "query_outputs": [pair["output"] for pair in episode["test"]],
                "certificate": episode["certificate"],
                "racket_parity": episode["racket_parity"],
                "source": episode["source"],
                "runtime_identity": generated["runtime_identity"],
            }
            private_bytes = _json_bytes(private)
            _write_new(temp / public_rel, public_bytes)
            _write_new(temp / private_rel, private_bytes)
            rows.append(
                {
                    "public_id": public_id,
                    "public_path": public_rel.as_posix(),
                    "private_path": private_rel.as_posix(),
                    "public_sha256": _sha256(public_bytes),
                    "private_sha256": _sha256(private_bytes),
                }
            )
        rows.sort(key=lambda row: row["public_id"])
        files = {
            row[key]: row["public_sha256" if key == "public_path" else "private_sha256"]
            for row in rows
            for key in ("public_path", "private_path")
        }
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "task_id": TASK_ID,
            "source": source_bindings(),
            "counts": {"episodes": len(rows), "demos": demos, "queries": queries},
            "episodes": rows,
            "files": dict(sorted(files.items())),
        }
        _write_new(temp / "manifest.json", _json_bytes(manifest))
        temp.rename(out)
        return {
            "schema": MANIFEST_SCHEMA,
            "path": str(out),
            "episodes": len(rows),
            "demos": demos,
            "queries": queries,
            "manifest_sha256": _file_sha256(out / "manifest.json"),
        }
    except BaseException:
        shutil.rmtree(temp, ignore_errors=True)
        raise


def verify_batch(
    out: Path,
    *,
    bridge: RacketBridge | None = None,
    report: Path | None = None,
) -> dict[str, Any]:
    """Verify hashes, strict projection, teaching and chosen-rule Racket labels."""
    out = Path(out)
    if out.is_symlink() or not out.is_dir():
        raise ValueError("batch path must be a real directory")
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink not allowed: {path.relative_to(out)}")
    top = {path.name for path in out.iterdir()}
    expected_top = {"public", "private", "manifest.json"}
    unexpected_top = sorted(top - expected_top)
    if unexpected_top:
        raise ValueError(f"unexpected top-level entries: {unexpected_top}")
    if top != expected_top or not (out / "public").is_dir() or not (out / "private").is_dir():
        raise ValueError("batch must contain only public/, private/, and manifest.json")

    for folder_name in ("public", "private"):
        folder = out / folder_name
        for child in folder.iterdir():
            if child.is_symlink() or not child.is_file():
                raise ValueError(f"{folder_name}/ may contain only regular episode files: {child.name}")

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("task_id") != TASK_ID:
        raise ValueError("wrong manifest schema or task")
    expected_source = source_bindings()
    if manifest.get("source") != expected_source:
        raise ValueError("manifest source binding mismatch")
    rows = manifest.get("episodes")
    files = manifest.get("files")
    counts = manifest.get("counts")
    if type(rows) is not list or type(files) is not dict or not rows:
        raise ValueError("manifest must declare nonempty episodes and files")
    if type(counts) is not dict or set(counts) != {"episodes", "demos", "queries"}:
        raise ValueError("manifest counts have wrong fields")
    manifest_demos, manifest_queries = _validate_counts(counts["demos"], counts["queries"])
    if counts["episodes"] != len(SETTINGS) or len(rows) != len(SETTINGS):
        raise ValueError("manifest must contain exactly one episode per setting")
    actual_files = {
        path.relative_to(out).as_posix()
        for path in out.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    declared_files = set(files)
    unexpected = sorted(actual_files - declared_files)
    missing = sorted(declared_files - actual_files)
    if unexpected or missing:
        raise ValueError(f"unexpected or missing files: unexpected={unexpected}, missing={missing}")
    for relative_text, expected_hash in files.items():
        relative = _safe_relative(relative_text)
        path = out / relative
        if path.resolve().parent == out.resolve().parent or not path.resolve().is_relative_to(out.resolve()):
            raise ValueError(f"file escapes batch: {relative_text}")
        if type(expected_hash) is not str or _file_sha256(path) != expected_hash:
            raise ValueError(f"hash mismatch: {relative_text}")

    public_ids: set[str] = set()
    referenced_files: set[str] = set()
    reconstructed = []
    for row in rows:
        required_row = {
            "public_id",
            "public_path",
            "private_path",
            "public_sha256",
            "private_sha256",
        }
        if not isinstance(row, dict) or set(row) != required_row:
            raise ValueError("episode manifest row has wrong fields")
        public_id = row["public_id"]
        if type(public_id) is not str or len(public_id) != 64 or public_id in public_ids:
            raise ValueError("invalid or duplicate public id")
        public_ids.add(public_id)
        public_rel = _safe_relative(row["public_path"])
        private_rel = _safe_relative(row["private_path"])
        if public_rel != Path("public") / f"{public_id}.json":
            raise ValueError("public path must be hash-named")
        if private_rel != Path("private") / f"{public_id}.json":
            raise ValueError("private path must match public id")
        referenced_files.update((public_rel.as_posix(), private_rel.as_posix()))
        public_raw = (out / public_rel).read_bytes()
        private_raw = (out / private_rel).read_bytes()
        if _sha256(public_raw) != row["public_sha256"] or _sha256(private_raw) != row["private_sha256"]:
            raise ValueError("episode row hash mismatch")
        if _sha256(public_raw) != public_id:
            raise ValueError("public filename/id is not exact visible-byte hash")
        public = json.loads(public_raw)
        if set(public) != {"train", "test"}:
            raise ValueError("public challenge leaked or omitted top-level fields")
        if any(set(pair) != {"input", "output"} for pair in public["train"]):
            raise ValueError("public demonstrations require only input/output")
        if any(set(pair) != {"input"} for pair in public["test"]):
            raise ValueError("public queries must be answer-free")
        if public_challenge_bytes(public) != public_raw or public_challenge_id(public) != public_id:
            raise ValueError("public bytes are not canonical helper projection")

        private = json.loads(private_raw)
        required_private = {
            "schema",
            "task_id",
            "public_id",
            "seed",
            "counts",
            "settings",
            "program_solution",
            "program_sha256",
            "query_outputs",
            "certificate",
            "racket_parity",
            "source",
            "runtime_identity",
        }
        if set(private) != required_private:
            raise ValueError("private episode has wrong fields")
        if (
            private["schema"] != PRIVATE_SCHEMA
            or private["task_id"] != TASK_ID
            or private["public_id"] != public_id
        ):
            raise ValueError("private episode binding mismatch")
        if type(private["counts"]) is not dict or set(private["counts"]) != {"demos", "queries"}:
            raise ValueError("private counts have wrong fields")
        demos, queries = _validate_counts(
            private["counts"].get("demos"), private["counts"].get("queries")
        )
        if (demos, queries) != (manifest_demos, manifest_queries):
            raise ValueError("private counts disagree with manifest")
        if len(public["train"]) != demos or len(public["test"]) != queries:
            raise ValueError("serialized pair counts disagree")
        if private["source"] != expected_source:
            raise ValueError("private source binding mismatch")
        expected_parity = {
            "pairs": demos + queries,
            "settings": len(SETTINGS),
            "matches": (demos + queries) * len(SETTINGS),
        }
        if private["racket_parity"] != expected_parity:
            raise ValueError("private Racket parity summary mismatch")
        selected = _validate_settings(private["settings"])
        program = program_for(selected)
        if private["program_solution"] != program or private["program_sha256"] != _sha256(program.encode("utf-8")):
            raise ValueError("private program does not match settings")
        query_outputs = private["query_outputs"]
        if type(query_outputs) is not list or len(query_outputs) != queries:
            raise ValueError("private query outputs have wrong count")
        for output in query_outputs:
            _validate_grid(output)
        challenge = {
            "train": public["train"],
            "test": [
                {"input": pair["input"], "output": output}
                for pair, output in zip(public["test"], query_outputs)
            ],
        }
        inputs = [pair["input"] for pair in challenge["train"] + challenge["test"]]
        if len({_json_bytes(grid) for grid in inputs}) != len(inputs):
            raise ValueError("episode inputs must be distinct")
        certificate = lesson_certificate(challenge)
        if certificate != private["certificate"] or certificate["survivors"] != [setting_name(selected)]:
            raise ValueError("demonstration certificate mismatch")
        prefix = generate_claims(private["seed"], selected, demos=demos, queries=1)
        if prefix["test"][0]["input"] != challenge["test"][0]["input"]:
            raise ValueError("first query is not stable under one-query use")
        reconstructed.append((program, challenge, private["runtime_identity"]))

    if declared_files != referenced_files:
        raise ValueError("manifest files must be exactly the episode-referenced public/private files")
    if [row["public_id"] for row in rows] != sorted(public_ids):
        raise ValueError("episode rows must be sorted by public id")

    context = RacketBridge() if bridge is None else nullcontext(bridge)
    racket_pairs = 0
    with context as active:
        runtime_identity = active.runtime_identity
        for program, challenge, declared_runtime in reconstructed:
            if declared_runtime != runtime_identity:
                raise ValueError("private runtime identity mismatch")
            for pair in challenge["train"] + challenge["test"]:
                actual = execute_rule(program, pair["input"], bridge=active)
                if actual != pair["output"]:
                    raise ValueError("serialized Racket label mismatch")
                racket_pairs += 1
    result = {
        "schema": "7e52d15790d7-parametric-verification-v1",
        "episodes": len(rows),
        "racket_pairs": racket_pairs,
        "runtime_identity": runtime_identity,
        "manifest_sha256": _file_sha256(out / "manifest.json"),
        "status": "pass",
    }
    if report is not None:
        report = Path(report)
        if report.exists() or report.is_symlink():
            raise FileExistsError(report)
        report.parent.mkdir(parents=True, exist_ok=True)
        _write_new(report, _json_bytes(result))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--seed", type=int, default=17)
    materialize.add_argument("--demos", type=int, default=3)
    materialize.add_argument("--queries", type=int, default=4)
    materialize.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("path", type=Path)
    verify.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.command == "materialize":
        result = materialize_batch(
            seed=args.seed, demos=args.demos, queries=args.queries, out=args.out
        )
    else:
        result = verify_batch(args.path, report=args.report)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
