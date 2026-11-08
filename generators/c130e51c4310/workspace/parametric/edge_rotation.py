"""Episode-fixed edge-rotation family for ``c130e51c4310``.

This is a task-local parametric prototype, not canonical or production
training authority.  The canonical setting is ``edge_shift=0``.  Other
settings rotate the correspondence from full cue-bounding-box edges to frame
interior edges clockwise while preserving cue erasure and the canonical
all-four-edges fill branch.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Callable

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "c130e51c4310"
SCHEMA = "c130-edge-rotation-proposal-v1"
DEFAULT = {"edge_shift": 0}
PARAMETERS = {"edge_shift": [0, 1, 2, 3]}
SETTINGS = [{"edge_shift": shift} for shift in range(4)]
LEGAL_CUE_COLORS = (1, 2, 3, 4, 5, 8, 9)
EDGE_NAMES = ("top", "right", "bottom", "left")
REPO = find_root(__file__)


_PROFILE_OPTIONS: dict[str, tuple[tuple[bool, bool, bool, bool], ...]] = {
    "single_edge": (
        (True, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
        (False, False, False, True),
    ),
    "adjacent_edges": (
        (True, True, False, False),
        (False, True, True, False),
        (False, False, True, True),
        (True, False, False, True),
    ),
    "opposite_edges": (
        (True, False, True, False),
        (False, True, False, True),
    ),
    "three_edges": (
        (False, True, True, True),
        (True, False, True, True),
        (True, True, False, True),
        (True, True, True, False),
    ),
    "all_edges": ((True, True, True, True),),
}

# (height, width, frame_top, frame_left, frame_height, frame_width,
#  cue_top, cue_left, cue_height, cue_width, profile)
_DEMO_SPECS = (
    (12, 14, 1, 1, 6, 8, 8, 8, 3, 5, "single_edge"),
    (13, 15, 5, 5, 7, 9, 0, 0, 4, 5, "all_edges"),
    (15, 16, 1, 7, 8, 8, 10, 0, 4, 6, "adjacent_edges"),
    (17, 18, 7, 1, 9, 10, 0, 12, 6, 5, "opposite_edges"),
    (19, 20, 1, 1, 11, 12, 12, 12, 6, 8, "three_edges"),
    (21, 23, 8, 9, 12, 14, 0, 0, 7, 8, "single_edge"),
)
_QUERY_SPECS = (
    (14, 17, 1, 1, 8, 10, 9, 11, 5, 6, "three_edges"),
    (18, 22, 7, 1, 10, 13, 0, 15, 6, 7, "adjacent_edges"),
    (24, 27, 1, 10, 15, 17, 17, 0, 7, 9, "opposite_edges"),
    (30, 30, 9, 5, 18, 20, 0, 21, 7, 9, "single_edge"),
)


def _load_canonical_program() -> str:
    for line in canonical_path(REPO).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID and row.get("source") == "training":
            value = row.get("program_solution")
            if type(value) is not str or not value:
                raise RuntimeError("canonical program_solution is missing")
            return value
    raise RuntimeError(f"canonical row for {TASK_ID} is missing")


_CANONICAL_PROGRAM = _load_canonical_program()


def _exact_integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(
            f"{name} must be an exact integer in {low}..{high}"
        )
    return value


def _settings(settings: object) -> dict[str, int]:
    if type(settings) is not dict or set(settings) != {"edge_shift"}:
        raise ValueError("settings must name exactly edge_shift")
    shift = settings["edge_shift"]
    if type(shift) is not int or shift not in PARAMETERS["edge_shift"]:
        raise ValueError("edge_shift must be one of 0|1|2|3; booleans rejected")
    return {"edge_shift": shift}


def _grid(grid: object) -> list[list[int]]:
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
        raise ValueError(
            "grid must be rectangular with exact integer colors 0..9"
        )
    return [row[:] for row in grid]


def _digest(value: object) -> str:
    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    token = _digest([TASK_ID, "edge-rotation-v1", seed, domain, index])
    return random.Random(int(token, 16))


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _frame_info(grid: list[list[int]]) -> dict[str, object]:
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 6
    }
    groups = _components(cells)
    if len(groups) != 1:
        raise ValueError("expected one connected color-6 frame")
    frame = groups[0]
    row1, col1, row2, col2 = _bbox(frame)
    if row2 - row1 < 2 or col2 - col1 < 2:
        raise ValueError("frame must have a nonempty interior")
    expected = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    if frame != expected:
        raise ValueError("color 6 must form one exact hollow rectangle")
    return {"bbox": (row1, col1, row2, col2), "cells": frame}


def _mode(grid: list[list[int]]) -> int:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    best = max(counts.values())
    modes = [value for value, count in counts.items() if count == best]
    if len(modes) != 1:
        raise ValueError("background mode must be unique")
    return modes[0]


def _cue_info(
    grid: list[list[int]], background: int, frame_bbox: tuple[int, int, int, int]
) -> dict[str, object]:
    colored = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (background, 6)
    ]
    colors = {value for _, _, value in colored}
    if len(colors) != 1:
        raise ValueError("expected one non-background non-frame cue color")
    color = next(iter(colors))
    cells = {(row, col) for row, col, _ in colored}
    if not cells or len(_components(cells)) != 1:
        raise ValueError("cue must be nonempty and 4-connected")
    row1, col1, row2, col2 = _bbox(cells)
    fr1, fc1, fr2, fc2 = frame_bbox
    if any(fr1 <= row <= fr2 and fc1 <= col <= fc2 for row, col in cells):
        raise ValueError("cue must lie wholly outside the frame bounding box")
    top = all((row1, col) in cells for col in range(col1, col2 + 1))
    right = all((row, col2) in cells for row in range(row1, row2 + 1))
    bottom = all((row2, col) in cells for col in range(col1, col2 + 1))
    left = all((row, col1) in cells for row in range(row1, row2 + 1))
    edges = (top, right, bottom, left)
    if not any(edges):
        raise ValueError("cue must have at least one full bounding-box edge")
    return {
        "bbox": (row1, col1, row2, col2),
        "cells": cells,
        "color": color,
        "edges": edges,
    }


def program(settings: dict[str, int]) -> str:
    """Materialize one of four concrete Racket rules.

    The default is returned from the canonical ledger without normalization, so
    source bytes and whitespace remain exact authority.
    """
    chosen = _settings(settings)
    shift = chosen["edge_shift"]
    if shift == 0:
        return _CANONICAL_PROGRAM

    source_names = ("top-edge", "right-edge", "bot-edge", "left-edge")
    target_sources = {
        target: source_names[(target - shift) % 4] for target in range(4)
    }
    replacements = (
        ("(g2 (if top-edge", f"(g2 (if {target_sources[0]}"),
        ("(g3 (if bot-edge", f"(g3 (if {target_sources[2]}"),
        ("(g4 (if left-edge", f"(g4 (if {target_sources[3]}"),
        ("(g5 (if right-edge", f"(g5 (if {target_sources[1]}"),
    )
    result = _CANONICAL_PROGRAM
    for old, new in replacements:
        if result.count(old) != 1:
            raise RuntimeError(f"canonical program drift around {old!r}")
        result = result.replace(old, new, 1)
    return result


def transform(grid: object, settings: dict[str, int]) -> list[list[int]]:
    """Apply the selected edge mapping without mutating ``grid``."""
    chosen = _settings(settings)
    source = _grid(grid)
    background = _mode(source)
    frame = _frame_info(source)
    cue = _cue_info(source, background, frame["bbox"])
    output = [row[:] for row in source]
    for row, col in cue["cells"]:
        output[row][col] = background

    row1, col1, row2, col2 = frame["bbox"]
    top_row, left_col = row1 + 1, col1 + 1
    bottom_row, right_col = row2 - 1, col2 - 1
    cue_color = cue["color"]
    source_edges = cue["edges"]
    if all(source_edges):
        for row in range(top_row, bottom_row + 1):
            for col in range(left_col, right_col + 1):
                output[row][col] = cue_color
        return output

    target_edges = [False, False, False, False]
    shift = chosen["edge_shift"]
    for source_index, present in enumerate(source_edges):
        if present:
            target_edges[(source_index + shift) % 4] = True
    if target_edges[0]:
        for col in range(left_col, right_col + 1):
            output[top_row][col] = cue_color
    if target_edges[1]:
        for row in range(top_row, bottom_row + 1):
            output[row][right_col] = cue_color
    if target_edges[2]:
        for col in range(left_col, right_col + 1):
            output[bottom_row][col] = cue_color
    if target_edges[3]:
        for row in range(top_row, bottom_row + 1):
            output[row][left_col] = cue_color
    return output


def _cue_mask(
    height: int,
    width: int,
    edges: tuple[bool, bool, bool, bool],
    rng: random.Random,
) -> list[list[bool]]:
    mask = [[False for _ in range(width)] for _ in range(height)]
    top, right, bottom, left = edges
    if top:
        for col in range(width):
            mask[0][col] = True
    if right:
        for row in range(height):
            mask[row][-1] = True
    if bottom:
        for col in range(width):
            mask[-1][col] = True
    if left:
        for row in range(height):
            mask[row][0] = True

    center_row = height // 2
    center_col = width // 2
    # Connect the hub to one point on every side.  This keeps the authored
    # cue bbox exact even for one-edge profiles, while only selected sides are
    # complete.  Dimensions are at least 3, so a single anchor cannot make an
    # unselected side full.
    for row in range(0, height):
        mask[row][center_col] = True
    for col in range(0, width):
        mask[center_row][col] = True

    # Add a small, connected interior branch for richer shapes without changing
    # edge completeness.  Selection is independent of the episode rule.
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if not mask[row][col]
    ]
    rng.shuffle(candidates)
    budget = max(1, (height * width) // 10)
    for _ in range(budget):
        adjacent = [
            (row, col)
            for row, col in candidates
            if not mask[row][col]
            and any(
                mask[row + drow][col + dcol]
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
        ]
        if not adjacent:
            break
        row, col = rng.choice(adjacent)
        mask[row][col] = True
    return mask


def _scene(
    seed: int,
    domain: str,
    index: int,
    spec: tuple[int, int, int, int, int, int, int, int, int, int, str],
) -> list[list[int]]:
    (
        height,
        width,
        frame_top,
        frame_left,
        frame_height,
        frame_width,
        cue_top,
        cue_left,
        cue_height,
        cue_width,
        profile,
    ) = spec
    rng = _rng(seed, domain, index)
    options = _PROFILE_OPTIONS[profile]
    edges = options[rng.randrange(len(options))]
    cue_color = LEGAL_CUE_COLORS[rng.randrange(len(LEGAL_CUE_COLORS))]
    mask = _cue_mask(cue_height, cue_width, edges, rng)
    grid = [[7 for _ in range(width)] for _ in range(height)]
    for drow in range(frame_height):
        for dcol in range(frame_width):
            if drow in (0, frame_height - 1) or dcol in (0, frame_width - 1):
                grid[frame_top + drow][frame_left + dcol] = 6
    for drow in range(cue_height):
        for dcol in range(cue_width):
            if mask[drow][dcol]:
                grid[cue_top + drow][cue_left + dcol] = cue_color
    # Validate the authored scene immediately; malformed templates must never
    # silently enter an episode.
    background = _mode(grid)
    frame = _frame_info(grid)
    cue = _cue_info(grid, background, frame["bbox"])
    if cue["edges"] != edges:
        raise RuntimeError(
            f"cue template drift: requested {edges}, observed {cue['edges']}"
        )
    return grid


def _pair(grid: list[list[int]], settings: dict[str, int]) -> dict[str, object]:
    return {"input": grid, "output": transform(grid, settings)}


def _validate_episode_pairs(
    pairs: object, low: int, high: int, name: str
) -> list[dict[str, object]]:
    if type(pairs) is not list:
        raise ValueError(f"{name} must be a list")
    _exact_integer(len(pairs), low, high, name)
    result: list[dict[str, object]] = []
    for pair in pairs:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError(f"every {name} pair must name input and output")
        result.append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    return result


def _execute_for_setting(
    execute: Callable[[str, list[list[int]]], object] | None,
    setting: dict[str, int],
    grid: list[list[int]],
) -> list[list[int]]:
    if execute is None:
        return transform(grid, setting)
    return _grid(execute(program(setting), copy.deepcopy(grid)))


def certify(
    episode: dict[str, object],
    execute: Callable[[str, list[list[int]]], object] | None = None,
) -> dict[str, object]:
    """Check labels and uniqueness against the four declared settings only."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    chosen = _settings(episode.get("settings"))
    if episode.get("task_id") != TASK_ID:
        raise ValueError("episode task_id mismatch")
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match the fixed episode setting")
    train = _validate_episode_pairs(episode.get("train"), 2, 6, "train")
    test = _validate_episode_pairs(episode.get("test"), 1, 4, "test")
    keys = [_digest(pair["input"]) for pair in train + test]
    if len(keys) != len(set(keys)):
        raise ValueError("all demonstration and query inputs must be distinct")

    refutations: list[dict[str, object]] = []
    survivors: list[dict[str, int]] = []
    for setting in SETTINGS:
        disagreements = []
        for index, pair in enumerate(train):
            prediction = _execute_for_setting(execute, setting, pair["input"])
            if prediction != pair["output"]:
                disagreements.append(index)
        refutations.append(
            {
                "settings": dict(setting),
                "disagreeing_demo_indices": disagreements,
            }
        )
        if not disagreements:
            survivors.append(dict(setting))
    if survivors != [chosen]:
        raise ValueError(
            "demonstrations do not uniquely identify the selected finite "
            f"setting: {survivors}"
        )

    query_certificates = []
    for pair in test:
        prediction = _execute_for_setting(execute, chosen, pair["input"])
        if prediction != pair["output"]:
            raise ValueError(
                "query output disagrees with the selected Racket/mirror rule"
            )
        query_certificates.append(
            {
                "input_sha256": _digest(pair["input"]),
                "output_sha256": _digest(pair["output"]),
                "survivors": copy.deepcopy(survivors),
                "unanimous": True,
            }
        )
    return {
        "scope": "four declared edge_shift settings only; demos fit before queries",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": refutations,
        "queries": query_certificates,
    }


def generate(
    seed: int,
    settings: dict[str, int] | None = None,
    demos: int = 3,
    queries: int = 4,
) -> dict[str, object]:
    """Generate one fixed-setting episode with independent count streams."""
    _exact_integer(seed, -(2**63), 2**63 - 1, "seed")
    _exact_integer(demos, 2, 6, "demos")
    _exact_integer(queries, 1, 4, "queries")
    if settings is None:
        chosen = dict(_rng(seed, "settings").choice(SETTINGS))
    else:
        chosen = _settings(settings)

    train = [
        _pair(_scene(seed, "demo-input", index, _DEMO_SPECS[index]), chosen)
        for index in range(demos)
    ]
    test = [
        _pair(
            _scene(seed, "query-input", index, _QUERY_SPECS[index]), chosen
        )
        for index in range(queries)
    ]
    source = program(chosen)
    episode: dict[str, object] = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "sampling": {
            "demo_stream": "demo-input indices 0..demos-1",
            "query_stream": "query-input indices 0..queries-1",
            "query_sizes": [
                [spec[0], spec[1]] for spec in _QUERY_SPECS[:queries]
            ],
        },
    }
    episode["certificate"] = certify(episode)
    return episode


def model_turn_bytes(episode: dict[str, object], query_index: int) -> bytes:
    """Serialize only information visible at one sequential model turn."""
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    train = _validate_episode_pairs(episode.get("train"), 2, 6, "train")
    test = _validate_episode_pairs(episode.get("test"), 1, 4, "test")
    _exact_integer(query_index, 0, len(test) - 1, "query_index")
    if query_index == 0:
        visible: dict[str, object] = {
            "train": train,
            "test": [{"input": test[0]["input"]}],
        }
    else:
        visible = {"test": [{"input": test[query_index]["input"]}]}
    return (
        json.dumps(
            visible,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


class RacketRunner:
    """One protected live Racket bridge for a bounded evidence batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        self.identity = self.bridge.runtime_identity
        if (
            self.identity.get("backend") != "racket"
            or self.identity.get("protected") is not True
        ):
            self.bridge.close()
            raise RuntimeError("a live protected Racket backend is required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        checked = _grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in checked
        ) + ")"
        result = self.bridge.eval_text(f"({self.cache[source]} {literal})")
        return _grid(result)

    def __exit__(self, *exc: object) -> None:
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    """Bind the prototype, selected authority and protected runtime helpers."""
    paths = (
        Path(__file__).resolve(),
        Path(__file__).with_name("adapter.py"),
        Path(__file__).with_name("promotion.json"),
        Path(__file__).with_name("README.md"),
        REPO / "generators" / TASK_ID / "generator.py",
        canonical_path(REPO),
        REPO / "shared/runtime/reviewer_support.py",
        REPO / "shared/runtime/arc_repl/racket_bridge.py",
        REPO / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt",
        REPO / "shared/runtime/puzzle_generators/rule_wrap.py",
    )
    result: dict[str, str] = {}
    for item in paths:
        resolved = item.resolve()
        result[str(resolved.relative_to(REPO))] = hashlib.sha256(
            resolved.read_bytes()
        ).hexdigest()
    return result


def write_batch(
    episodes: list[dict[str, object]],
    destination: str | Path,
    *,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    """Write a visible-byte-addressed public projection plus private evidence.

    This serializer intentionally does not execute Racket.  The CLI certifies
    every episode before calling it.  Public identity depends only on visible
    demonstrations and query inputs.
    """
    root = Path(destination)
    if root.exists():
        raise FileExistsError(root)
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    rows = sorted(
        [
            (
                public_challenge_id(episode),
                public_challenge_bytes(episode),
                episode,
            )
            for episode in episodes
        ],
        key=lambda row: (row[0], row[1]),
    )
    identifiers = [identifier for identifier, _, _ in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("visible challenges must be distinct")

    root.mkdir(parents=True)
    public_root = root / "public"
    public_root.mkdir()
    for identifier, body, _ in rows:
        (public_root / f"{identifier}.json").write_bytes(body)
    (root / "public.jsonl").write_bytes(
        b"".join(body for _, body, _ in rows)
    )

    private = {
        "schema": "c130-edge-rotation-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": [
            dict(copy.deepcopy(episode), public_id=identifier)
            for identifier, _, episode in rows
        ],
    }
    (root / "private.json").write_text(
        json.dumps(
            private,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    serialized = [root / "public.jsonl", root / "private.json"] + sorted(
        public_root.iterdir()
    )
    manifest: dict[str, object] = {
        "schema": "c130-edge-rotation-export-v1",
        "status": "prototype_proposed",
        "public_ids": identifiers,
        "writer_executes_racket": False,
        "files": {
            str(item.relative_to(root)): hashlib.sha256(
                item.read_bytes()
            ).hexdigest()
            for item in serialized
        },
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--edge-shift", type=int, choices=range(4), default=0)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    selected = SETTINGS if args.all_settings else [
        {"edge_shift": args.edge_shift}
    ]
    episodes: list[dict[str, object]] = []
    with RacketRunner() as execute:
        for setting in selected:
            for seed in args.seeds or [0]:
                episode = generate(
                    seed,
                    setting,
                    demos=args.demos,
                    queries=args.queries,
                )
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {
            "payload_argv": list(sys.argv if argv is None else argv),
            "runtime_identity": execute.identity,
            "finite_scope": (
                "four edge_shift settings only; no unrestricted-rule claim"
            ),
            "qualification": "not_run",
            "acceptance": "not_requested",
            "training_admitted": False,
        }
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(
        json.dumps(
            {
                "status": "prototype_proposed",
                "episodes": len(episodes),
                "demonstrations": sum(len(ep["train"]) for ep in episodes),
                "queries": sum(len(ep["test"]) for ep in episodes),
                "finite_racket_demo_executions": sum(
                    len(SETTINGS) * len(ep["train"]) for ep in episodes
                ),
                "selected_racket_query_executions": sum(
                    len(ep["test"]) for ep in episodes
                ),
                "public_ids": manifest["public_ids"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
