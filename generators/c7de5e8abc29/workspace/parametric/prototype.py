"""Proposed alignment-parametric connector family; never production authority.

The canonical setting connects same-color diagonal endpoint pairs.  The nearby
variant connects horizontal/vertical pairs instead.  Settings stay fixed across
an episode; the CLI re-executes every retained label through protected Racket.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "c7de5e8abc29"
DEFAULT = {"alignment": "diagonal"}
PARAMETERS = {"alignment": ["diagonal", "orthogonal"]}
SETTINGS = [{"alignment": value} for value in PARAMETERS["alignment"]]

if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import public_challenge_bytes, public_challenge_id

_CANONICAL = '''(rule! (lambda (g)
         (reduce (lambda (acc color)
                   (let* ((dots (find-color g color)))
                     (if (< (length dots) 2)
                         acc
                         (reduce (lambda (a d1)
                                   (reduce (lambda (a2 d2)
                                             (if (<= (fst d2) (fst d1))
                                                 a2
                                                 (let* ((dr (- (fst d2) (fst d1)))
                                                        (dc (- (snd d2) (snd d1))))
                                                   (if (= (abs dr) (abs dc))
                                                       (let* ((sr (if (> dr 0) 1 -1))
                                                              (sc (if (> dc 0) 1 -1)))
                                                         (reduce (lambda (a3 k)
                                                                   (set-cell a3
                                                                             (+ (fst d1)
                                                                                (* k sr))
                                                                             (+ (snd d1)
                                                                                (* k sc))
                                                                             color))
                                                                 a2
                                                                 (range 0
                                                                        (+ (abs dr) 1))))
                                                       a2))))
                                           a
                                           dots))
                                 acc
                                 dots))))
                 g
                 (range 1 10))))'''

_ORTHOGONAL = '''(rule! (lambda (g)
  (reduce (lambda (acc color)
    (let ((dots (find-color g color)))
      (if (< (length dots) 2)
          acc
          (reduce (lambda (a d1)
            (reduce (lambda (a2 d2)
              (if (or (> (fst d2) (fst d1))
                      (and (= (fst d2) (fst d1)) (> (snd d2) (snd d1))))
                  (let* ((dr (- (fst d2) (fst d1)))
                         (dc (- (snd d2) (snd d1))))
                    (if (or (= dr 0) (= dc 0))
                        (let* ((steps (if (= dr 0) (abs dc) (abs dr)))
                               (sr (if (= dr 0) 0 (if (> dr 0) 1 -1)))
                               (sc (if (= dc 0) 0 (if (> dc 0) 1 -1))))
                          (reduce (lambda (a3 k)
                            (set-cell a3
                                      (+ (fst d1) (* k sr))
                                      (+ (snd d1) (* k sc))
                                      color))
                            a2
                            (range 0 (+ steps 1))))
                        a2))
                  a2))
              a
              dots))
            acc
            dots))))
    g
    (range 1 10))))'''


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"alignment"}:
        raise ValueError("settings must name exactly alignment")
    value = settings["alignment"]
    if type(value) is not str or value not in PARAMETERS["alignment"]:
        raise ValueError("alignment must be 'diagonal' or 'orthogonal'")
    return {"alignment": value}


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
    return _CANONICAL if chosen == DEFAULT else _ORTHOGONAL


def _line(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    r1, c1 = a
    r2, c2 = b
    dr, dc = r2 - r1, c2 - c1
    if dr == 0:
        sc = 1 if dc > 0 else -1
        return [(r1, c1 + k * sc) for k in range(abs(dc) + 1)]
    if dc == 0:
        sr = 1 if dr > 0 else -1
        return [(r1 + k * sr, c1) for k in range(abs(dr) + 1)]
    if abs(dr) == abs(dc):
        sr = 1 if dr > 0 else -1
        sc = 1 if dc > 0 else -1
        return [(r1 + k * sr, c1 + k * sc) for k in range(abs(dr) + 1)]
    return []


def _qualifies(a: tuple[int, int], b: tuple[int, int], alignment: str) -> bool:
    dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
    if alignment == "diagonal":
        return dr == dc and dr > 0
    return (dr == 0) != (dc == 0)


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    """Python mirror/proposal. Protected Racket remains the retained authority."""
    _grid(grid)
    chosen = _settings(settings)
    output = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    for color, cells in positions.items():
        if len(cells) != 2 or not _qualifies(cells[0], cells[1], chosen["alignment"]):
            continue
        for r, c in _line(cells[0], cells[1]):
            output[r][c] = color
    return output


def digest(value: object) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "alignment-v1", seed, domain, index]), 16))


def _zone_path(kind: str, bounds: tuple[int, int, int, int], rng: random.Random,
               *, boundary: bool = False, secondary: int = 0) -> list[tuple[int, int]]:
    r0, r1, c0, c1 = bounds
    if kind in ("diag_down", "diag_up"):
        maximum = min(r1 - r0, c1 - c0)
        if boundary and secondary:
            # Alternate parallel lanes between a column shift and a row shift.
            # ``secondary == 1`` must not collapse onto the primary diagonal.
            if secondary % 2:
                offset_r = 0
                offset_c = (secondary + 1) // 2
            else:
                offset_r = secondary // 2
                offset_c = 0
            start_r = r0 + offset_r
            start_c = c0 + offset_c if kind == "diag_down" else c1 - offset_c
            length = min(r1 - start_r,
                         c1 - start_c if kind == "diag_down" else start_c - c0)
        else:
            length = maximum if boundary else rng.randint(2, maximum)
            start_r = r0 if boundary else rng.randint(r0, r1 - length)
            start_c = ((c0 if boundary else rng.randint(c0, c1 - length))
                       if kind == "diag_down"
                       else (c1 if boundary else rng.randint(c0 + length, c1)))
        if length < 2:
            raise RuntimeError("zone is too small for the requested diagonal")
        if kind == "diag_down":
            return _line((start_r, start_c), (start_r + length, start_c + length))
        return _line((start_r, start_c), (start_r + length, start_c - length))
    if kind == "horizontal":
        length = c1 - c0
        row = (r1 if secondary else r0) if boundary else rng.randint(r0, r1)
        return _line((row, c0), (row, c1))
    if kind == "vertical":
        length = r1 - r0
        col = (c1 if secondary else c0) if boundary else rng.randint(c0, c1)
        return _line((r0, col), (r1, col))
    raise ValueError(kind)


def _scene(seed: int, domain: str, index: int) -> list[list[int]]:
    rng = _rng(seed, domain, index)
    if domain == "query":
        sizes = ((8, 10), (14, 16), (22, 24), (30, 30))
        h, w = sizes[index]
        boundary = index >= 2
    else:
        sizes = ((8, 9), (9, 11), (10, 12), (11, 13), (12, 14), (14, 16))
        h, w = sizes[index]
        boundary = index in (0, 5)
    split_r, split_c = h // 2, w // 2
    zones = {
        "tl": (0, split_r - 1, 0, split_c - 1),
        "tr": (0, split_r - 1, split_c, w - 1),
        "bl": (split_r, h - 1, 0, split_c - 1),
        "br": (split_r, h - 1, split_c, w - 1),
    }
    specs = [
        ("diag_down", zones["tl"], 0),
        ("horizontal", zones["tr"], 0),
        ("vertical", zones["bl"], 0),
        ("diag_up", zones["br"], 0),
    ]
    if h >= 18 and w >= 18:
        specs.extend([
            ("diag_down", zones["tl"], 1),
            ("diag_down", zones["tl"], 2),
            ("diag_up", zones["br"], 1),
            ("horizontal", zones["tr"], 1),
            ("vertical", zones["bl"], 1),
        ])
    colors = list(range(1, 10))
    rng.shuffle(colors)
    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()
    for color, (kind, bounds, secondary) in zip(colors, specs):
        path = _zone_path(kind, bounds, rng, boundary=boundary, secondary=secondary)
        if occupied.intersection(path):
            raise RuntimeError("constructive zone paths unexpectedly overlap")
        occupied.update(path)
        for r, c in (path[0], path[-1]):
            grid[r][c] = color
    return grid


def _apply_named(name: str, grid: list[list[int]]) -> list[list[int]]:
    if name == "all_aligned":
        first = transform(grid, {"alignment": "diagonal"})
        # Apply orthogonal lines to the original endpoints while preserving first paint.
        second = transform(grid, {"alignment": "orthogonal"})
        out = [row[:] for row in first]
        for r, row in enumerate(second):
            for c, value in enumerate(row):
                if value:
                    out[r][c] = value
        return out
    if name == "horizontal_only" or name == "vertical_only":
        out = [row[:] for row in grid]
        positions: dict[int, list[tuple[int, int]]] = {}
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    positions.setdefault(value, []).append((r, c))
        for color, cells in positions.items():
            if len(cells) != 2:
                continue
            dr = cells[1][0] - cells[0][0]
            dc = cells[1][1] - cells[0][1]
            qualifies = (name == "horizontal_only" and dr == 0 and dc != 0) or (
                name == "vertical_only" and dc == 0 and dr != 0)
            if qualifies:
                for r, c in _line(cells[0], cells[1]):
                    out[r][c] = color
        return out
    if name == "endpoints_only":
        return [row[:] for row in grid]
    raise KeyError(name)


EXTRA_RIVALS = ("all_aligned", "horizontal_only", "vertical_only", "endpoints_only")


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
        raise ValueError(f"demonstrations do not identify selected alignment: {survivors}")
    extra = {}
    for name in EXTRA_RIVALS:
        disagree = [i for i, pair in enumerate(train)
                    if _apply_named(name, pair["input"]) != pair["output"]]
        if not disagree:
            raise ValueError(f"extra rival {name!r} survives every demonstration")
        extra[name] = disagree
    query_records = []
    for pair in test:
        got = apply(program(chosen), pair["input"])
        if got != pair["output"]:
            raise ValueError("query label disagrees with fixed setting")
        query_records.append({"input_sha256": digest(pair["input"]),
                              "output_sha256": digest(pair["output"]),
                              "survivors": survivors, "unanimous": True})
    return {"scope": "two declared alignments plus four finite shortcuts",
            "racket_checked": execute is not None,
            "survivors": survivors, "demo_refutations": records,
            "extra_refutations": extra, "queries": query_records}


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
    episode = {"schema": "c7de-alignment-parametric-proposal-v1", "task_id": TASK_ID,
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
    private = {"schema": "c7de-alignment-evidence-v1", "status": "prototype_proposed",
               "source_sha256": source_hashes(), "metadata": metadata or {},
               "episodes": [dict(ep, public_id=identifier,
                                  turn_ids=[public_challenge_id(public_turn(ep, i)) for i in range(4)])
                            for identifier, _, ep in rows]}
    (destination / "private.json").write_text(
        json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n")
    files = [destination / "public.jsonl", destination / "private.json"] + sorted(public.iterdir())
    manifest = {"schema": "c7de-alignment-export-v1",
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
    parser.add_argument("--alignment", choices=PARAMETERS["alignment"], default="diagonal")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = SETTINGS if args.all_settings else [{"alignment": args.alignment}]
    episodes = []
    with RacketRunner() as execute:
        for setting in settings:
            for seed in args.seeds or [0]:
                episode = generate(seed, setting, args.demos, args.queries)
                episode["certificate"] = certify(episode, execute)
                episodes.append(episode)
        metadata = {"payload_argv": sys.argv, "runtime_identity": execute.identity,
                    "finite_scope": "two alignment settings plus named shortcuts",
                    "qualification": "not_run", "acceptance": "not_requested",
                    "training_admitted": False}
        manifest = write_batch(episodes, args.out, metadata=metadata)
    print(json.dumps({"status": "prototype_proposed", "episodes": len(episodes),
                      "racket_checked_pairs": sum(len(ep["train"]) + len(ep["test"]) for ep in episodes),
                      "public_ids": manifest["public_ids"], "out": str(args.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
