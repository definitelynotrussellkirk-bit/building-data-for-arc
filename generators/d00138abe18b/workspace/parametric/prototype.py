"""Proposed row-edge/order parametric family; never production authority.

The canonical setting reads the first nonzero value of each nonempty row from
left to right and emits those values top to bottom.  Nearby settings switch the
read edge, the row order, or both.  Every retained label is re-executed through
protected Racket by the evidence CLI.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "d00138abe18b"
DEFAULT = {"read_side": "left", "row_order": "top_down"}
PARAMETERS = {
    "read_side": ["left", "right"],
    "row_order": ["top_down", "bottom_up"],
}
SETTINGS = [
    {"read_side": side, "row_order": order}
    for side in PARAMETERS["read_side"]
    for order in PARAMETERS["row_order"]
]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule! (let* ((firsts (for/list ((r (range 0 (rows g))))
                       (find-first (lambda (v) (!= v 0)) (row g r))))
             (kept (filter values firsts)))
  ;; each row collapses to its FIRST non-0 value (all-0 rows drop); all-empty grid -> [[0]]
  (if (empty? kept) (list (list 0)) (map list kept))))'''

_RIGHT_TOP = '''(rule! (let* ((firsts (for/list ((r (range 0 (rows g))))
                       (find-first (lambda (v) (!= v 0)) (reverse (row g r)))))
             (kept (filter values firsts)))
  (if (empty? kept) (list (list 0)) (map list kept))))'''

_LEFT_BOTTOM = '''(rule! (let* ((firsts (for/list ((r (range 0 (rows g))))
                       (find-first (lambda (v) (!= v 0)) (row g r))))
             (kept (filter values firsts)))
  (if (empty? kept) (list (list 0)) (map list (reverse kept)))))'''

_RIGHT_BOTTOM = '''(rule! (let* ((firsts (for/list ((r (range 0 (rows g))))
                       (find-first (lambda (v) (!= v 0)) (reverse (row g r)))))
             (kept (filter values firsts)))
  (if (empty? kept) (list (list 0)) (map list (reverse kept)))))'''

_PROGRAMS = {
    ("left", "top_down"): _CANONICAL,
    ("left", "bottom_up"): _LEFT_BOTTOM,
    ("right", "top_down"): _RIGHT_TOP,
    ("right", "bottom_up"): _RIGHT_BOTTOM,
}

_LEFT = (2, 5, 2, 7, 4, 6, 4, 8, 3, 8, 5, 1)
_RIGHT = (8, 3, 8, 1, 9, 3, 6, 2, 7, 2, 9, 4)
_MIDDLE = (4, 6, 5, 2, 7, 8, 1, 5, 6, 7, 2, 9)


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"read_side", "row_order"}:
        raise ValueError("settings must name exactly read_side and row_order")
    side, order = settings["read_side"], settings["row_order"]
    if type(side) is not str or side not in PARAMETERS["read_side"]:
        raise ValueError("read_side must be 'left' or 'right'")
    if type(order) is not str or order not in PARAMETERS["row_order"]:
        raise ValueError("row_order must be 'top_down' or 'bottom_up'")
    return {"read_side": side, "row_order": order}


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
    chosen = _settings(settings)
    return _PROGRAMS[(chosen["read_side"], chosen["row_order"])]


def _row_values(grid: list[list[int]], side: str) -> list[int]:
    values: list[int] = []
    for row in grid:
        occupied = [value for value in row if value]
        if occupied:
            values.append(occupied[0] if side == "left" else occupied[-1])
    return values


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Python mirror/proposal. Protected Racket remains label authority."""
    _grid(grid)
    chosen = _settings(settings)
    values = _row_values(grid, chosen["read_side"])
    if chosen["row_order"] == "bottom_up":
        values.reverse()
    return [[value] for value in values] or [[0]]


def digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "row-edge-order-v1", seed, domain, index]), 16))


def _nonempty_rows(height: int, count: int, rng: random.Random, *, boundary: bool) -> list[int]:
    if not 4 <= count < height:
        raise ValueError("scene must leave an empty row and retain at least four runs")
    if boundary:
        interior = list(range(1, height - 1))
        rng.shuffle(interior)
        return sorted([0, height - 1, *interior[: count - 2]])
    rows = list(range(height))
    rng.shuffle(rows)
    return sorted(rows[:count])


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    if domain == "query":
        sizes = ((8, 11), (12, 15), (20, 24), (30, 30))
        counts = (6, 8, 14, 24)
        height, width = sizes[index]
        count = counts[index]
        boundary = index == 3
    else:
        sizes = ((7, 9), (8, 10), (9, 11), (10, 12), (12, 14), (14, 16))
        height, width = sizes[index]
        count = min(height - 1, 5 + index)
        boundary = index in (0, 5)
    rows = _nonempty_rows(height, count, rng, boundary=boundary)
    grid = [[0] * width for _ in range(height)]
    for ordinal, row_index in enumerate(rows):
        left = _LEFT[ordinal % len(_LEFT)]
        right = _RIGHT[ordinal % len(_RIGHT)]
        middle = _MIDDLE[ordinal % len(_MIDDLE)]
        if len({left, middle, right}) != 3:
            raise RuntimeError("row palette contract is not decisive")
        if boundary and ordinal == 0:
            start = 0
        elif boundary and ordinal == 1:
            start = width - 4
        else:
            start = rng.randrange(0, width - 3)
        grid[row_index][start : start + 4] = [left, middle, middle, right]
    return grid


def _shortcut(name: str, grid: list[list[int]], chosen: dict[str, str]) -> list[list[int]]:
    rows = [[value for value in row if value] for row in grid]
    rows = [row for row in rows if row]
    if name == "modal_row":
        values = []
        for row in rows:
            counts = Counter(row)
            values.append(max(counts, key=lambda value: (counts[value], -row.index(value))))
        if chosen["row_order"] == "bottom_up":
            values.reverse()
    else:
        values = [row[0] if chosen["read_side"] == "left" else row[-1] for row in rows]
        if chosen["row_order"] == "bottom_up":
            values.reverse()
        if name == "deduplicate":
            values = list(dict.fromkeys(values))
        elif name == "sort_values":
            values = sorted(values)
        else:
            raise KeyError(name)
    return [[value] for value in values] or [[0]]


SHORTCUTS = ("modal_row", "deduplicate", "sort_values")


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
    pairs = train + test
    if len({digest(pair.get("input")) for pair in pairs}) != len(pairs):
        raise ValueError("all demonstration and query inputs must be distinct")
    for pair in pairs:
        _grid(pair.get("input"))
        _grid(pair.get("output"))
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
        raise ValueError(f"demonstrations do not identify selected row rule: {survivors}")
    extra: dict[str, list[int]] = {}
    shortcut_survivors: list[str] = []
    for name in SHORTCUTS:
        disagree = [i for i, pair in enumerate(train)
                    if _shortcut(name, pair["input"], chosen) != pair["output"]]
        if not disagree:
            shortcut_survivors.append(name)
        extra[name] = disagree
    if shortcut_survivors:
        raise ValueError(f"named row shortcuts survive: {shortcut_survivors}")
    query_records = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        query_records.append({"input_sha256": digest(pair["input"]),
                              "output_sha256": digest(pair["output"]),
                              "survivors": survivors, "unanimous": True})
    return {"scope": "four edge/order settings plus three finite shortcuts",
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
    episode = {"schema": "d001-row-edge-order-parametric-proposal-v1", "task_id": TASK_ID,
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
    private = {"schema": "d001-row-edge-order-evidence-v1", "status": "prototype_proposed",
               "source_sha256": source_hashes(), "metadata": metadata or {},
               "episodes": [dict(ep, public_id=identifier,
                                  turn_ids=[public_challenge_id(public_turn(ep, i)) for i in range(4)])
                            for identifier, _, ep in rows]}
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n")
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {"schema": "d001-row-edge-order-export-v1",
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
    parser.add_argument("--read-side", choices=PARAMETERS["read_side"], default="left")
    parser.add_argument("--row-order", choices=PARAMETERS["row_order"], default="top_down")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"read_side": args.read_side,
                                                     "row_order": args.row_order}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {"payload_argv": sys.argv, "runtime_identity": execute.identity,
                    "finite_scope": "four edge/order settings plus named shortcuts",
                    "qualification": "not_run", "acceptance": "not_requested",
                    "training_admitted": False}
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(json.dumps({"status": "prototype_proposed", "episodes": len(episodes),
                      "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                      "public_ids": manifest["public_ids"], "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
