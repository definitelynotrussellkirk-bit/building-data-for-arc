"""Source-bound reflection-scope family for ARC task 7d970a1ea99b.

The default ``all`` setting is the exact canonical Racket program.  The nearby
``diagonal_cued`` setting keeps the same reflection geometry but adds a genuine
sequential dependency:

A. locate the unique nonzero cell on the main diagonal and read its color;
B. reflect only off-diagonal cells carrying that input-derived color.

Inputs are sampled independently of the private setting.  Every scene contains
four colors, a unique diagonal cue, sources on both sides of the main diagonal,
and no occupied transpose pair, so both settings preserve every original cell.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import random
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "7d970a1ea99b"
DEFAULT = {"reflection_scope": "all"}
PARAMETERS = {"reflection_scope": ["all", "diagonal_cued"]}
SETTINGS = [{"reflection_scope": value} for value in PARAMETERS["reflection_scope"]]

_CANONICAL = """(rule!
 ;; Overlay the TRANSPOSE onto the grid: every non-zero cell also lands at
 ;; its mirrored (c, r) position.
 (overlay g (transpose g)))"""

_DIAGONAL_CUED = """(rule! (lambda (g)
  (let* ((cue-index
          (first (filter (lambda (i) (not (= (at g i i) 0)))
                         (range (rows g)))))
         (cue-color (at g cue-index cue-index))
         (selected
          (grid-from-fn (rows g) (cols g)
            (lambda (r c)
              (if (= (at g r c) cue-color) (at g r c) 0)))))
    (overlay g (transpose selected)))))"""

# Constructive profiles.  Counts are (cue off-diagonal, decoy1, decoy2, decoy3).
# The unique diagonal cue adds one to the cue color's total frequency.
_DEMO_PROFILES = (
    (10, (2, 4, 5, 6), "least", True),
    (10, (8, 2, 3, 4), "most", False),
    (12, (4, 2, 6, 5), "middle", True),
    (12, (2, 4, 5, 6), "least", False),
    (14, (9, 3, 4, 5), "most", True),
    (16, (4, 2, 7, 6), "middle", False),
)
_QUERY_PROFILES = (
    (8, (4, 2, 5, 4), "middle", False),
    (13, (2, 5, 6, 7), "least", True),
    (20, (10, 4, 5, 6), "most", True),
    (30, (6, 11, 12, 13), "least", True),
)


def digest(value: object) -> str:
    if isinstance(value, bytes):
        body = value
    else:
        body = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _settings(settings: object) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"reflection_scope"}:
        raise ValueError("settings must contain exactly reflection_scope")
    scope = settings["reflection_scope"]
    if type(scope) is not str or scope not in PARAMETERS["reflection_scope"]:
        raise ValueError("reflection_scope must be 'all' or 'diagonal_cued'")
    return {"reflection_scope": scope}


def _grid(grid: object) -> list[list[int]]:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty rectangle with 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact ARC integers 0..9")
    return grid


def program(settings: object) -> str:
    chosen = _settings(settings)
    return _CANONICAL if chosen == DEFAULT else _DIAGONAL_CUED


def diagonal_cue_color(grid: list[list[int]]) -> int:
    _grid(grid)
    if len(grid) != len(grid[0]):
        raise ValueError("reflection scenes must be square")
    cues = [grid[i][i] for i in range(len(grid)) if grid[i][i] != 0]
    if len(cues) != 1:
        raise ValueError(f"expected exactly one nonzero diagonal cue; found {len(cues)}")
    return cues[0]


def _scene_errors(grid: list[list[int]]) -> list[str]:
    try:
        _grid(grid)
    except ValueError as exc:
        return [str(exc)]
    if len(grid) != len(grid[0]):
        return ["scene must be square"]
    n = len(grid)
    errors: list[str] = []
    try:
        cue = diagonal_cue_color(grid)
    except ValueError as exc:
        errors.append(str(exc))
        cue = None
    colors = {value for row in grid for value in row if value}
    if len(colors) != 4:
        errors.append(f"expected four nonzero colors; found {len(colors)}")
    collisions = [(r, c) for r in range(n) for c in range(r + 1, n)
                  if grid[r][c] and grid[c][r]]
    if collisions:
        errors.append(f"occupied transpose pairs are forbidden: {collisions[:3]}")
    upper = sum(bool(grid[r][c]) for r in range(n) for c in range(r + 1, n))
    lower = sum(bool(grid[r][c]) for r in range(1, n) for c in range(r))
    if not upper or not lower:
        errors.append("sources must occur on both sides of the main diagonal")
    if cue is not None:
        cue_off = sum(grid[r][c] == cue for r in range(n) for c in range(n) if r != c)
        if cue_off < 2:
            errors.append("cue color needs at least two off-diagonal sources")
    return errors


def transform(grid: list[list[int]], settings: object) -> list[list[int]]:
    _grid(grid)
    chosen = _settings(settings)
    n = len(grid)
    if n != len(grid[0]):
        raise ValueError("reflection scenes must be square")
    selected = None if chosen["reflection_scope"] == "all" else diagonal_cue_color(grid)
    output = [row[:] for row in grid]
    for r in range(n):
        for c in range(n):
            value = grid[r][c]
            if value and (selected is None or value == selected):
                output[c][r] = value
    return output


def _rng(seed: int, domain: str, index: int = 0) -> random.Random:
    return random.Random(int(digest([TASK_ID, "reflection-scope-v1", seed, domain, index]), 16))


def _palette(seed: int) -> tuple[int, int, int, int]:
    colors = list(range(1, 10))
    _rng(seed, "palette").shuffle(colors)
    return tuple(colors[:4])


def _rank(counts: dict[int, int], cue: int) -> str:
    value = counts[cue]
    if value == min(counts.values()) and list(counts.values()).count(value) == 1:
        return "least"
    if value == max(counts.values()) and list(counts.values()).count(value) == 1:
        return "most"
    return "middle"


def profile(grid: list[list[int]]) -> dict[str, object]:
    errors = _scene_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    n = len(grid)
    cue = diagonal_cue_color(grid)
    counts = {color: 0 for color in {value for row in grid for value in row if value}}
    for row in grid:
        for value in row:
            if value:
                counts[value] += 1
    cue_pos = next(i for i in range(n) if grid[i][i])
    return {
        "shape": f"{n}x{n}",
        "cue_color": cue,
        "cue_position": cue_pos,
        "cue_frequency_rank": _rank(counts, cue),
        "color_counts": {str(k): counts[k] for k in sorted(counts)},
        "upper_sources": sum(bool(grid[r][c]) for r in range(n) for c in range(r + 1, n)),
        "lower_sources": sum(bool(grid[r][c]) for r in range(1, n) for c in range(r)),
        "boundary_sources": sum(bool(grid[r][c]) for r in range(n) for c in range(n)
                                if r != c and (r in (0, n - 1) or c in (0, n - 1))),
    }


def _build_scene(seed: int, domain: str, index: int,
                 spec: tuple[int, tuple[int, int, int, int], str, bool]) -> list[list[int]]:
    n, requested_counts, expected_rank, boundary = spec
    rng = _rng(seed, domain, index)
    base_palette = _palette(seed)
    cue_color = base_palette[index % len(base_palette)]
    decoys = [color for color in base_palette if color != cue_color]
    colors = [cue_color, *decoys]
    color_stream = [color for color, count in zip(colors, requested_counts) for _ in range(count)]
    rng.shuffle(color_stream)

    pairs = [(r, c) for r in range(n) for c in range(r + 1, n)]
    forced: list[tuple[int, int, bool]] = []
    if boundary:
        # These two one-sided sources and their transposes span all four borders.
        forced = [(0, n - 2, True), (2, n - 1, False)]
        used_pairs = {(0, n - 2), (2, n - 1)}
        pairs = [pair for pair in pairs if pair not in used_pairs]
    rng.shuffle(pairs)
    need = len(color_stream) - len(forced)
    selected = forced + [(r, c, bool(rng.randrange(2))) for r, c in pairs[:need]]
    if len(selected) != len(color_stream):
        raise RuntimeError("scene profile exceeds available transpose pairs")

    # Ensure both triangle directions, independently of random choices.
    if selected:
        r, c, _ = selected[0]
        selected[0] = (r, c, True)
    if len(selected) > 1:
        r, c, _ = selected[1]
        selected[1] = (r, c, False)

    grid = [[0] * n for _ in range(n)]
    for color, (r, c, upper) in zip(color_stream, selected):
        rr, cc = (r, c) if upper else (c, r)
        grid[rr][cc] = color
    diagonal_candidates = list(range(1, n - 1)) or list(range(n))
    cue_index = diagonal_candidates[_rng(seed, domain + "-cue", index).randrange(len(diagonal_candidates))]
    grid[cue_index][cue_index] = cue_color

    errors = _scene_errors(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    actual = profile(grid)["cue_frequency_rank"]
    if actual != expected_rank:
        raise RuntimeError(f"profile rank mismatch: expected {expected_rank}, got {actual}")
    return grid


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _reflect_fixed(grid: list[list[int]], color: int) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c] == color:
                output[c][r] = color
    return output


def _frequency_color(grid: list[list[int]], *, largest: bool) -> list[list[int]]:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value:
                counts[value] = counts.get(value, 0) + 1
    ordered = sorted(counts, key=lambda color: (counts[color], color), reverse=largest)
    return _reflect_fixed(grid, ordered[0])


def _upper_only(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(r + 1, n):
            if grid[r][c]:
                output[c][r] = grid[r][c]
    return output


def _lower_only(grid: list[list[int]]) -> list[list[int]]:
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(1, n):
        for c in range(r):
            if grid[r][c]:
                output[c][r] = grid[r][c]
    return output


def _all_recolored_as_cue(grid: list[list[int]]) -> list[list[int]]:
    cue = diagonal_cue_color(grid)
    output = [row[:] for row in grid]
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c]:
                output[c][r] = cue
    return output


EXTRA_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "fixed_color_1": lambda grid: _reflect_fixed(grid, 1),
    "most_frequent_color": lambda grid: _frequency_color(grid, largest=True),
    "least_frequent_color": lambda grid: _frequency_color(grid, largest=False),
    "upper_triangle_only": _upper_only,
    "lower_triangle_only": _lower_only,
    "reflect_all_recolored_as_cue": _all_recolored_as_cue,
}


def certify(episode: dict, execute: Callable[[str, list[list[int]]], list[list[int]]] | None = None) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be a dict")
    chosen = _settings(episode.get("settings"))
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("episode must contain 2..6 demonstrations")
    if type(test) is not list or not 1 <= len(test) <= 4:
        raise ValueError("episode must contain 1..4 queries")
    all_pairs = train + test
    seen: set[str] = set()
    for index, pair in enumerate(all_pairs):
        if type(pair) is not dict or set(pair) < {"input", "output"}:
            raise ValueError(f"pair {index} needs input and output")
        errors = _scene_errors(pair["input"])
        if errors:
            raise ValueError(f"pair {index} invalid: {errors[0]}")
        key = digest(pair["input"])
        if key in seen:
            raise ValueError("all demonstration and query inputs must be distinct")
        seen.add(key)
        expected = transform(pair["input"], chosen)
        if pair["output"] != expected:
            raise ValueError(f"pair {index} output disagrees with selected transform")

    apply = execute or (lambda text, grid: transform(grid, next(
        setting for setting in SETTINGS if program(setting) == text)))
    survivors = []
    for setting in SETTINGS:
        text = program(setting)
        if all(apply(text, pair["input"]) == pair["output"] for pair in train):
            survivors.append(copy.deepcopy(setting))
    if survivors != [chosen]:
        raise ValueError(f"demonstrations do not uniquely identify setting: {survivors}")

    rival_results: dict[str, str] = {}
    for name, rival in EXTRA_RIVALS.items():
        rival_results[name] = (
            "survived_all" if all(rival(pair["input"]) == pair["output"] for pair in train)
            else "refuted"
        )
    if any(value != "refuted" for value in rival_results.values()):
        raise ValueError(f"named shortcut survived demonstrations: {rival_results}")
    return {
        "survivors": survivors,
        "rivals": rival_results,
        "queries": [{"index": i, "input_sha256": digest(pair["input"])} for i, pair in enumerate(test)],
    }


def generate(seed: int, settings: object = None, demos: int = 3, queries: int = 4) -> dict:
    seed = _integer(seed, 0, 2**63 - 1, "seed")
    chosen = _settings(DEFAULT if settings is None else settings)
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 4, "queries")

    demo_grids = [_build_scene(seed, "demo", index, spec)
                  for index, spec in enumerate(_DEMO_PROFILES)]
    # Construct the complete four-query bank before slicing, so changing query
    # count never changes the first query or any public first-turn bytes.
    query_grids = [_build_scene(seed, "query", index, spec)
                   for index, spec in enumerate(_QUERY_PROFILES)]
    train = [{"input": grid, "output": transform(grid, chosen)} for grid in demo_grids[:demos]]
    test = [{"input": grid, "output": transform(grid, chosen)} for grid in query_grids[:queries]]
    episode = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": chosen,
        "train": train,
        "test": test,
        "program_solution": program(chosen),
    }
    episode["certificate"] = certify(episode)
    return episode


def public_turn(episode: dict, index: int) -> dict:
    if type(index) is not int or isinstance(index, bool):
        raise ValueError("turn index must be an exact integer")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= index < len(test):
        raise ValueError("turn index outside episode query bank")
    return {
        "train": copy.deepcopy(train),
        "test": [{"input": copy.deepcopy(test[index]["input"])}],
    }


class RacketRunner:
    def __init__(self):
        self.bridge = None
        self.wrap = None
        self.cache: dict[str, str] = {}

    def __enter__(self):
        bridge_module = importlib.import_module("arc_repl.racket_bridge")
        wrap_module = importlib.import_module("puzzle_generators.rule_wrap")
        self.bridge = bridge_module.RacketBridge(max_calls_before_restart=512)
        self.wrap = wrap_module.wrap_rule
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.bridge is not None:
            self.bridge.close()
        self.bridge = None

    def __call__(self, text: str, grid: list[list[int]]) -> list[list[int]]:
        if self.bridge is None or self.wrap is None:
            raise RuntimeError("RacketRunner must be used as a context manager")
        wrapped = self.cache.setdefault(text, self.wrap(text))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return self.bridge.eval_text(f"({wrapped} {literal})")


def _summary(seed: int, demos: int, queries: int, all_settings: bool) -> dict:
    settings = SETTINGS if all_settings else [DEFAULT]
    episodes = [generate(seed, setting, demos, queries) for setting in settings]
    with RacketRunner() as run:
        evaluations = 0
        for episode in episodes:
            for pair in episode["train"] + episode["test"]:
                actual = run(episode["program_solution"], pair["input"])
                if actual != pair["output"]:
                    raise ValueError("protected Racket output disagrees with claimed label")
                evaluations += 1
    return {
        "schema": "7d970a1ea99b-reflection-scope-evidence-v1",
        "seed": seed,
        "demos": demos,
        "queries": queries,
        "settings": [episode["settings"] for episode in episodes],
        "episodes": episodes,
        "racket": {"backend": "racket", "protected": True, "evaluations": evaluations},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = _summary(args.seed, args.demos, args.queries, args.all_settings)
    body = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body)
    print(json.dumps({
        "status": "passed",
        "settings": len(report["settings"]),
        "racket_evaluations": report["racket"]["evaluations"],
        "receipt": str(args.out) if args.out else None,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
