#!/usr/bin/env python3
"""Source-bound anchor-size-relation family for c8e53a07acc8.

The exact canonical default matches template anchor-color multiplicity to a
same-color standalone object's size.  The alternate keeps the complete
multi-template alignment/stamping/unique-source-erasure algorithm but matches
objects one cell larger.  Every generated input contains both candidate object
sizes, so inputs are setting-neutral while demonstrations identify the hidden
relation from outputs alone.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter, deque
import hashlib
import json
import random
from pathlib import Path
import sys
from typing import Any, Callable

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "c8e53a07acc8"
HERE = Path(__file__).resolve().parent
REPO = find_root(__file__)
DEFAULT = {"anchor_size_relation": "same_count"}
PARAMETERS = {"anchor_size_relation": ["same_count", "one_extra"]}
SETTINGS = [{"anchor_size_relation": value} for value in PARAMETERS["anchor_size_relation"]]
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (4, 4)


def _canonical_program() -> str:
    programs: list[str] = []
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError(f"expected one stable canonical program for {TASK_ID}")
    return programs[0]


CANONICAL_PROGRAM = _canonical_program()
_SIZE_PREDICATE = "(= (obj-size o) cnt)"
_ONE_EXTRA_PREDICATE = "(= (obj-size o) (+ cnt 1))"
if CANONICAL_PROGRAM.count(_SIZE_PREDICATE) != 2:
    raise RuntimeError("canonical anchor-size patch points changed")
ONE_EXTRA_PROGRAM = CANONICAL_PROGRAM.replace(_SIZE_PREDICATE, _ONE_EXTRA_PREDICATE)

_ADJ8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Three asymmetric anchor patterns.  ``extra`` is 8-connected to anchor but
# creates exactly one full translated anchor embedding in the larger object.
_SHAPES = (
    {
        "anchor": ((1, 0), (2, 1)),
        "body": ((0, 0), (0, 1), (1, 1), (1, 2)),
        "accent": (2, 2),
        "extra": (2, 0),
    },
    {
        "anchor": ((0, 0), (1, 0), (1, 1)),
        "body": ((0, 1), (0, 2), (1, 2), (2, 2)),
        "accent": (2, 1),
        "extra": (2, 0),
    },
    {
        "anchor": ((0, 0), (0, 1), (1, 2)),
        "body": ((1, 1), (2, 1), (2, 2)),
        "accent": (2, 0),
        "extra": (1, 0),
    },
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"anchor_size_relation"}:
        raise ValueError("settings must name exactly anchor_size_relation")
    relation = value["anchor_size_relation"]
    if type(relation) is not str or relation not in PARAMETERS["anchor_size_relation"]:
        raise ValueError("anchor_size_relation must be same_count or one_extra")
    return {"anchor_size_relation": relation}


def program(settings: object) -> str:
    chosen = _settings(settings)
    return CANONICAL_PROGRAM if chosen == DEFAULT else ONE_EXTRA_PROGRAM


def digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    _integer(seed, "seed", -(2**63), 2**63 - 1)
    return random.Random(int(digest([TASK_ID, "anchor-size-v1", seed, domain, index]), 16))


def _grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return grid


def _mode(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    return max(counts, key=counts.get)


def _components(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] == bg:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _ADJ8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != bg
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Python proposal/mirror; retained qualification executes protected Racket."""
    _grid(grid)
    relation = _settings(settings)["anchor_size_relation"]
    offset = 0 if relation == "same_count" else 1
    h, w = len(grid), len(grid[0])
    bg = _mode(grid)
    comps = _components(grid, bg)

    def colors_of(cells: list[tuple[int, int]]) -> list[int]:
        return list(dict.fromkeys(grid[r][c] for r, c in cells))

    singles = [cells for cells in comps if len(colors_of(cells)) == 1]
    templates = [cells for cells in comps if len(colors_of(cells)) > 1]
    output = copy.deepcopy(grid)
    for cells in templates:
        colors = colors_of(cells)

        def count_color(color: int) -> int:
            return sum(grid[r][c] == color for r, c in cells)

        anchor_colors = [
            color
            for color in colors
            if any(
                grid[obj[0][0]][obj[0][1]] == color
                and len(obj) == count_color(color) + offset
                for obj in singles
            )
        ]
        anchor_cells = [(r, c) for r, c in cells if grid[r][c] in anchor_colors]
        non_anchor = [(r, c) for r, c in cells if grid[r][c] not in anchor_colors]
        stamped = False
        for ar, ac in anchor_cells:
            color = grid[ar][ac]
            count = count_color(color)
            targets = [
                point
                for obj in singles
                if grid[obj[0][0]][obj[0][1]] == color and len(obj) == count + offset
                for point in obj
            ]
            for tr, tc in targets:
                dr, dc = tr - ar, tc - ac
                anchors_ok = all(
                    0 <= rr + dr < h
                    and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == grid[rr][cc]
                    for rr, cc in anchor_cells
                )
                fills_bg = any(
                    0 <= rr + dr < h
                    and 0 <= cc + dc < w
                    and grid[rr + dr][cc + dc] == bg
                    for rr, cc in non_anchor
                )
                if anchors_ok and fills_bg:
                    stamped = True
                    for rr, cc in cells:
                        nr, nc = rr + dr, cc + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            output[nr][nc] = grid[rr][cc]
        if stamped:
            for rr, cc in non_anchor:
                if count_color(grid[rr][cc]) == 1:
                    output[rr][cc] = bg
    return output


def _transform_point(point: tuple[int, int], rotation: int, reflect: bool) -> tuple[int, int]:
    r, c = point
    if reflect:
        c = -c
    for _ in range(rotation % 4):
        r, c = c, -r
    return r, c


def _shape(index: int, rng: random.Random) -> dict[str, Any]:
    source = _SHAPES[index % len(_SHAPES)]
    rotation, reflect = rng.randrange(4), bool(rng.randrange(2))
    groups = [
        tuple(_transform_point(p, rotation, reflect) for p in source["anchor"]),
        tuple(_transform_point(p, rotation, reflect) for p in source["body"]),
        (_transform_point(source["accent"], rotation, reflect),),
        (_transform_point(source["extra"], rotation, reflect),),
    ]
    r0 = min(r for group in groups for r, _ in group)
    c0 = min(c for group in groups for _, c in group)
    normalized = [tuple((r - r0, c - c0) for r, c in group) for group in groups]
    anchor, body, accent, extra = normalized
    if max(r for group in normalized for r, _ in group) > 2 or max(
        c for group in normalized for _, c in group
    ) > 2:
        raise RuntimeError("shape variant escaped its 3x3 footprint")
    return {"anchor": anchor, "body": body, "accent": accent[0], "extra": extra[0]}


def _slot_axis(length: int, *, align_end: bool) -> list[int]:
    # A 3x3 footprint needs at least one complete background row/column before
    # the next footprint under 8-connectivity, so origins are five apart.
    if align_end:
        return sorted(range(length - 3, -1, -5))
    return list(range(0, length - 2, 5))


def _slots(h: int, w: int, rng: random.Random, *, boundary: bool) -> list[tuple[int, int]]:
    # Use one coherent lattice per axis.  Mixing start- and end-aligned origins
    # can create origins only one cell apart and silently merge ARC objects.
    rows = _slot_axis(h, align_end=boundary or bool(rng.randrange(2)))
    cols = _slot_axis(w, align_end=boundary or bool(rng.randrange(2)))
    slots = [(r, c) for r in rows for c in cols]
    if boundary:
        edge = [cell for cell in slots if cell[0] in {rows[0], rows[-1]} or cell[1] in {cols[0], cols[-1]}]
        inner = [cell for cell in slots if cell not in edge]
        rng.shuffle(edge)
        rng.shuffle(inner)
        return edge + inner
    rng.shuffle(slots)
    return slots


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    if domain == "demo":
        sizes = ((13, 13), (14, 15), (16, 17), (18, 20), (22, 23), (25, 27))
        h, w = sizes[index]
        n_templates = 2 if index < 3 else 3
        boundary = index in {0, 5}
    elif domain == "query":
        sizes = ((15, 16), (20, 21), (24, 26), (30, 30))
        h, w = sizes[index]
        n_templates = 2 if index == 0 else 3
        boundary = index >= 2
    else:
        raise ValueError("domain must be demo or query")

    slots = _slots(h, w, rng, boundary=boundary)
    required = n_templates * 3
    if len(slots) < required:
        raise RuntimeError(f"{h}x{w} has only {len(slots)} separated slots for {required} objects")
    selected = slots[:required]

    bg = rng.randrange(10)
    palette = [color for color in range(10) if color != bg]
    rng.shuffle(palette)
    needed = n_templates * 3
    colors = palette[:needed]
    grid = [[bg for _ in range(w)] for _ in range(h)]

    for template_index in range(n_templates):
        shape = _shape(template_index + index, rng)
        anchor_color, body_color, accent_color = colors[3 * template_index : 3 * template_index + 3]
        template_origin, exact_origin, extra_origin = selected[3 * template_index : 3 * template_index + 3]

        tr, tc = template_origin
        for dr, dc in shape["anchor"]:
            grid[tr + dr][tc + dc] = anchor_color
        for dr, dc in shape["body"]:
            grid[tr + dr][tc + dc] = body_color
        ar, ac = shape["accent"]
        grid[tr + ar][tc + ac] = accent_color

        er, ec = exact_origin
        for dr, dc in shape["anchor"]:
            grid[er + dr][ec + dc] = anchor_color

        xr, xc = extra_origin
        for dr, dc in shape["anchor"]:
            grid[xr + dr][xc + dc] = anchor_color
        dr, dc = shape["extra"]
        grid[xr + dr][xc + dc] = anchor_color

    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise RuntimeError("constructed input does not distinguish anchor-size settings")
    return grid


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
    _integer(len(train), "demos", *DEMO_LIMITS)
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    pairs = train + test
    inputs: set[str] = set()
    for pair in pairs:
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError("each pair needs input and output")
        _grid(pair["input"])
        _grid(pair["output"])
        inputs.add(digest(pair["input"]))
    if len(inputs) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")

    apply = execute or (
        lambda source, grid: transform(
            grid, next(setting for setting in SETTINGS if program(setting) == source)
        )
    )
    refutations = []
    survivors = []
    for candidate in SETTINGS:
        disagreements = [
            index
            for index, pair in enumerate(train)
            if apply(program(candidate), pair["input"]) != pair["output"]
        ]
        refutations.append({"settings": candidate, "disagreeing_demo_indices": disagreements})
        if not disagreements:
            survivors.append(candidate)
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected setting: {survivors}")

    queries = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        queries.append(
            {
                "input_sha256": digest(pair["input"]),
                "output_sha256": digest(pair["output"]),
                "survivors": survivors,
                "unanimous": True,
            }
        )
    return {
        "scope": "two declared anchor-size relations",
        "racket_checked": execute is not None,
        "survivors": survivors,
        "demo_refutations": refutations,
        "queries": queries,
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    _integer(seed, "seed", -(2**63), 2**63 - 1)
    _integer(demos, "demos", *DEMO_LIMITS)
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")
    chosen = _settings(_rng(seed, "settings").choice(SETTINGS) if settings is None else settings)
    train = []
    for index in range(demos):
        grid = _scene(seed, "demo", index)
        train.append({"input": grid, "output": transform(grid, chosen)})
    test = []
    for index in range(4):
        grid = _scene(seed, "query", index)
        test.append({"input": grid, "output": transform(grid, chosen)})
    selected_program = program(chosen)
    episode = {
        "schema": "c8e53-anchor-size-parametric-proposal-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": selected_program,
        "program_sha256": hashlib.sha256(selected_program.encode()).hexdigest(),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict[str, Any], index: int) -> dict[str, Any]:
    _integer(index, "query index", 0, 3)
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


def public_id(episode: dict[str, Any], index: int) -> str:
    return public_challenge_id(public_turn(episode, index))


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(max_calls_before_restart=256)
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        from puzzle_generators.rule_wrap import wrap_rule

        _grid(grid)
        wrapped = self.cache.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({wrapped} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json"]
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def write_batch(
    episodes: list[dict[str, Any]], destination: Path, *, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Write only first-turn public challenges; later query inputs stay private."""
    destination = Path(destination)
    rows = [
        (public_id(episode, 0), public_challenge_bytes(public_turn(episode, 0)), episode)
        for episode in episodes
    ]
    rows.sort(key=lambda row: row[0])
    if not rows or len({identifier for identifier, _, _ in rows}) != len(rows):
        raise ValueError("batch must be nonempty with distinct first-turn challenges")
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    public = destination / "public"
    public.mkdir()
    for identifier, body, _ in rows:
        (public / f"{identifier}.json").write_bytes(body)
    (destination / "public.jsonl").write_bytes(b"".join(body for _, body, _ in rows))
    private = {
        "schema": "c8e53-anchor-size-evidence-v1",
        "status": "prototype_proposed",
        "source_sha256": source_hashes(),
        "metadata": metadata or {},
        "episodes": [
            dict(
                episode,
                public_id=identifier,
                turn_ids=[public_id(episode, index) for index in range(4)],
            )
            for identifier, _, episode in rows
        ],
    }
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n"
    )
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {
        "schema": "c8e53-anchor-size-export-v1",
        "public_projection": "first query only; later turns controller-private",
        "writer_executes_racket": False,
        "public_ids": [identifier for identifier, _, _ in rows],
        "files": {
            str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument(
        "--anchor-size-relation",
        choices=PARAMETERS["anchor_size_relation"],
        default="same_count",
    )
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [
        {"anchor_size_relation": args.anchor_size_relation}
    ]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {
            "payload_argv": sys.argv,
            "runtime_identity": execute.identity,
            "finite_scope": "two anchor-size-relation settings",
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
                "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                "public_ids": manifest["public_ids"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
