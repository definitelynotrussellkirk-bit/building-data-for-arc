"""Proposed control-to-shape mapping family; never production authority.

The canonical setting maps control 1 to hollow orange frames and control 2 to
solid orange rectangles.  The nearby reversed setting swaps those two branches.
Every scene contains both shape classes, and the evidence CLI re-executes every
retained label through protected Racket.
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "c7f337af82e5"
DEFAULT = {"mapping": "standard"}
PARAMETERS = {"mapping": ["standard", "reversed"]}
SETTINGS = [{"mapping": value} for value in PARAMETERS["mapping"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule!
  (let ((control (cell-at g 0 0)))
    (foldl
      (lambda (obj acc)
        (if (= (obj-color obj) 7)
            (let* ((bb (obj-bbox obj))
                   (r0 (first bb))
                   (c0 (second bb))
                   (r1 (third bb))
                   (c1 (fourth bb))
                   (cells (obj-cells obj))
                   (interior (if (and (< (+ r0 1) r1) (< (+ c0 1) c1))
                                 (positions-in-rect (+ r0 1) (+ c0 1) (- r1 1) (- c1 1))
                                 (list)))
                   (hollow
                     (any?
                       (lambda (p)
                         (and (= (cell-at g (fst p) (snd p)) 0)
                              (not (member p cells))))
                       interior)))
              (if (or (and (= control 1) hollow)
                      (and (= control 2) (not hollow)))
                  (paint-cells acc cells 8)
                  acc))
            acc))
      (set-cell g 0 0 0)
      (objects g 0))))'''

_REVERSED = _CANONICAL.replace(
    '''(if (or (and (= control 1) hollow)
                      (and (= control 2) (not hollow)))''',
    '''(if (or (and (= control 1) (not hollow))
                      (and (= control 2) hollow))''',
)
if _REVERSED == _CANONICAL:
    raise RuntimeError("failed to construct reversed control mapping")


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"mapping"}:
        raise ValueError("settings must name exactly mapping")
    value = settings["mapping"]
    if type(value) is not str or value not in PARAMETERS["mapping"]:
        raise ValueError("mapping must be 'standard' or 'reversed'")
    return {"mapping": value}


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be rectangular with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must contain exact integer ARC colors 0..9")
    return grid


def program(settings: object) -> str:
    return _CANONICAL if _settings(settings) == DEFAULT else _REVERSED


def _orange_components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            if grid[r][c] != 7 or (r, c) in seen:
                continue
            pending = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while pending:
                rr, cc = pending.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < height and 0 <= nc < width and grid[nr][nc] == 7
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            components.append(cells)
    return components


def describe_components(grid: list[list[int]]) -> list[dict[str, object]]:
    """Describe orange components using the canonical interior-zero criterion."""
    _grid(grid)
    described: list[dict[str, object]] = []
    for cells in _orange_components(grid):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        hollow = any(grid[r][c] == 0 and (r, c) not in cells for r, c in interior)
        described.append({"color": 7, "bbox": [r0, c0, r1, c1],
                          "cells": sorted(cells), "hollow": hollow})
    return sorted(described, key=lambda item: item["bbox"])


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Python mirror/proposal. Protected Racket remains label authority."""
    _grid(grid)
    chosen = _settings(settings)
    control = grid[0][0]
    output = [row[:] for row in grid]
    output[0][0] = 0
    for component in describe_components(grid):
        hollow = bool(component["hollow"])
        if chosen["mapping"] == "standard":
            selected = (control == 1 and hollow) or (control == 2 and not hollow)
        else:
            selected = (control == 1 and not hollow) or (control == 2 and hollow)
        if selected:
            for r, c in component["cells"]:
                output[r][c] = 8
    return output


def digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "control-mapping-v1", seed, domain, index]), 16))


def _paint_rect(grid: list[list[int]], bbox: tuple[int, int, int, int], hollow: bool) -> None:
    r0, c0, r1, c1 = bbox
    if not (0 <= r0 <= r1 < len(grid) and 0 <= c0 <= c1 < len(grid[0])):
        raise ValueError(f"rectangle outside grid: {bbox}")
    if hollow and (r1 - r0 < 2 or c1 - c0 < 2):
        raise ValueError("hollow frame must be at least 3x3")
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if not hollow or r in (r0, r1) or c in (c0, c1):
                if grid[r][c] != 0:
                    raise RuntimeError("constructive rectangle slots unexpectedly overlap")
                grid[r][c] = 7


def _small_scene(height: int, width: int, rng: random.Random) -> list[list[int]]:
    grid = [[0] * width for _ in range(height)]
    slots = [
        (0, 2, 2, 4),
        (0, width - 3, 2, width - 1),
        (height - 3, 0, height - 1, 2),
        (height - 3, width - 4, height - 1, width - 1),
    ]
    pattern = rng.randrange(2)
    hollow_flags = (True, False, False, True) if pattern == 0 else (False, True, True, False)
    for bbox, hollow in zip(slots, hollow_flags):
        _paint_rect(grid, bbox, hollow)
    return grid


def _large_scene() -> list[list[int]]:
    grid = [[0] * 30 for _ in range(30)]
    placements = [
        ((0, 2, 5, 10), True),       # top boundary frame
        ((0, 16, 7, 29), False),     # top/right solid
        ((8, 0, 14, 6), True),       # left boundary frame
        ((18, 0, 29, 10), False),    # bottom/left solid
        ((16, 15, 29, 29), True),    # bottom/right frame
    ]
    for bbox, hollow in placements:
        _paint_rect(grid, bbox, hollow)
    return grid


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    if domain == "query":
        sizes = ((8, 10), (13, 15), (20, 24), (30, 30))
        controls = (1, 2, 2, 1)
        height, width = sizes[index]
        grid = _large_scene() if index == 3 else _small_scene(height, width, rng)
        control = controls[index]
    else:
        sizes = ((8, 9), (9, 11), (10, 12), (11, 13), (12, 14), (14, 16))
        height, width = sizes[index]
        grid = _small_scene(height, width, rng)
        control = 1 if index % 2 == 0 else 2
    if grid[0][0] != 0:
        raise RuntimeError("control slot overlaps an orange object")
    grid[0][0] = control
    return grid


def _shortcut(name: str, grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    output[0][0] = 0
    for component in describe_components(grid):
        hollow = bool(component["hollow"])
        selected = {
            "paint_all": True,
            "paint_none": False,
            "always_hollow": hollow,
            "always_solid": not hollow,
        }[name]
        if selected:
            for r, c in component["cells"]:
                output[r][c] = 8
    return output


SHORTCUTS = ("paint_all", "paint_none", "always_hollow", "always_solid")


def certify(episode: dict, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict:
    chosen = _settings(episode.get("settings"))
    if episode.get("program_solution") != program(chosen):
        raise ValueError("program does not match fixed episode settings")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("episode must contain train/test lists")
    _integer(len(train), 2, 6, "demos")
    if len(test) != 4:
        raise ValueError("queries must contain exactly four pairs")
    if {pair.get("input", [[None]])[0][0] for pair in train} != {1, 2}:
        raise ValueError("demonstrations must teach both control branches")
    pairs = train + test
    if len({digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    for pair in pairs:
        _grid(pair.get("input"))
        _grid(pair.get("output"))
        shapes = describe_components(pair["input"])
        if not any(item["hollow"] for item in shapes) or not any(not item["hollow"] for item in shapes):
            raise ValueError("every scene must contain both hollow and solid orange objects")
    apply = execute or (lambda text, grid: transform(
        grid, next(setting for setting in SETTINGS if program(setting) == text)))
    records = []
    for setting in SETTINGS:
        predictions = [apply(program(setting), pair["input"]) for pair in train]
        records.append({"settings": setting, "disagreeing_demo_indices": [
            i for i, (got, pair) in enumerate(zip(predictions, train))
            if got != pair["output"]]})
    survivors = [dict(row["settings"]) for row in records if not row["disagreeing_demo_indices"]]
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not identify selected mapping: {survivors}")
    extra: dict[str, list[int]] = {}
    shortcut_survivors: list[str] = []
    for name in SHORTCUTS:
        disagree = [i for i, pair in enumerate(train)
                    if _shortcut(name, pair["input"]) != pair["output"]]
        if not disagree:
            shortcut_survivors.append(name)
        extra[name] = disagree
    if shortcut_survivors:
        raise ValueError(f"named mapping shortcuts survive: {shortcut_survivors}")
    query_records = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        query_records.append({"input_sha256": digest(pair["input"]),
                              "output_sha256": digest(pair["output"]),
                              "survivors": survivors, "unanimous": True})
    return {"scope": "two control mappings plus four finite shortcuts",
            "racket_checked": execute is not None,
            "survivors": survivors, "shortcut_survivors": shortcut_survivors,
            "demo_refutations": records, "extra_refutations": extra,
            "queries": query_records}


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    _integer(seed, -(2 ** 63), 2 ** 63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
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
    episode = {"schema": "c7f-control-mapping-parametric-proposal-v1", "task_id": TASK_ID,
               "seed": seed, "settings": chosen, "train": train, "test": test,
               "program_solution": program(chosen),
               "program_sha256": hashlib.sha256(program(chosen).encode()).hexdigest()}
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    _integer(index, 0, 3, "query index")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or len(test) != 4:
        raise ValueError("episode must retain four controller-side queries")
    return {"train": [{"input": copy.deepcopy(pair["input"]),
                       "output": copy.deepcopy(pair["output"])} for pair in train],
            "test": [{"input": copy.deepcopy(test[index]["input"])}]}


class RacketRunner:
    """One live protected bridge for bounded evidence; never a Python fallback."""
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

    def __exit__(self, *exc):
        self.bridge.close()


def source_hashes() -> dict[str, str]:
    paths = [HERE / "prototype.py", HERE / "adapter.py", HERE / "promotion.json",
             HERE.parents[1] / "generator.py", REPO / "shared/data/canonical/puzzles.jsonl",
             REPO / "shared/runtime/reviewer_support.py"]
    return {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def write_batch(episodes: list[dict], destination: Path, *, metadata: dict | None = None) -> dict:
    """Write only first-turn public challenges; all four queries remain private."""
    destination = Path(destination)
    rows = [(public_challenge_id(public_turn(ep, 0)),
             public_challenge_bytes(public_turn(ep, 0)), ep) for ep in episodes]
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
    private = {"schema": "c7f-control-mapping-evidence-v1", "status": "prototype_proposed",
               "source_sha256": source_hashes(), "metadata": metadata or {},
               "episodes": [dict(ep, public_id=identifier,
                                  turn_ids=[public_challenge_id(public_turn(ep, i)) for i in range(4)])
                            for identifier, _, ep in rows]}
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n")
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {"schema": "c7f-control-mapping-export-v1",
                "public_projection": "first query only; later turns controller-private",
                "writer_executes_racket": False,
                "public_ids": [identifier for identifier, _, _ in rows],
                "files": {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in files}}
    (destination / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--mapping", choices=PARAMETERS["mapping"], default="standard")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"mapping": args.mapping}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {"payload_argv": sys.argv, "runtime_identity": execute.identity,
                    "finite_scope": "two control mappings plus named shortcuts",
                    "qualification": "not_run", "acceptance": "not_requested",
                    "training_admitted": False}
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(json.dumps({"status": "prototype_proposed", "episodes": len(episodes),
                      "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                      "public_ids": manifest["public_ids"], "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
