"""Causal parametric family for the longest-diagonal ARC task.

The canonical setting paints the highest-scoring diagonal run.  The alternative
first identifies that canonical winner, then paints the highest-scoring strictly
shorter opposite-direction run that crosses the winner.  The generated grammar
makes that crossing follower neither the global runner-up nor the strongest
opposite-direction run, so the composed dependency is visible in every pair.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path
from typing import Any


TASK_ID = "2e9bbcd910a7"
PAINT_TARGETS = ("winner", "crossing_follower")


def _load_generator():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    name = "_arc_2e9bbcd910a7_reviewed_generator_" + hashlib.sha256(
        str(path).encode()
    ).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load reviewed generator at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()

CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((runs (straight-runs g
                                       (lambda (v) (zero? v))
                                       (list (list 1 1) (list 1 -1)))))
             (define (score run)
               (let* ((cells (fst run))
                      (dir (snd run))
                      (start (fst cells))
                      (dc (snd dir)))
                 (+ (* (length cells) 10000)
                    (- (* (fst start) 100))
                    (if (= dc -1) (snd start) (- w (snd start))))))
             (let ((best (fst (sort runs (lambda (a b) (> (score a) (score b)))))))
               (paint-cells g (fst best) 8))))))"""

FOLLOWER_PROGRAM = """(rule! (lambda (g)
         (let* ((w (cols g))
                (runs (straight-runs g
                                     (lambda (v) (zero? v))
                                     (list (list 1 1) (list 1 -1)))))
           (define (score run)
             (let* ((cells (fst run))
                    (dir (snd run))
                    (start (fst cells))
                    (dc (snd dir)))
               (+ (* (length cells) 10000)
                  (- (* (fst start) 100))
                  (if (= dc -1) (snd start) (- w (snd start))))))
           (define (crosses? cells winner-cells)
             (any? (lambda (cell) (member? cell winner-cells)) cells))
           (let* ((ranked (sort runs (lambda (a b) (> (score a) (score b)))))
                  (winner (fst ranked))
                  (winner-cells (fst winner))
                  (winner-dir (snd winner))
                  (winner-len (length winner-cells))
                  (followers
                   (filter (lambda (run)
                             (and (not (equal? (snd run) winner-dir))
                                  (< (length (fst run)) winner-len)
                                  (crosses? (fst run) winner-cells)))
                           ranked))
                  (follower (fst followers)))
             (paint-cells g (fst follower) 8)))))"""


def _path(start: tuple[int, int], delta: tuple[int, int], length: int):
    return tuple(
        (start[0] + index * delta[0], start[1] + index * delta[1])
        for index in range(length)
    )


# Each template contains:
# - the canonical winner;
# - the crossing follower selected by the alternative;
# - a stronger same-direction decoy (refutes global runner-up);
# - a stronger non-crossing opposite-direction decoy (refutes opposite champion).
_TEMPLATES = (
    {
        "name": "se8",
        "winner": _path((1, 1), (1, 1), 8),
        "follower": _path((1, 7), (1, -1), 7),
        "decoy_same": _path((1, 2), (1, 1), 7),
        "decoy_opp": _path((1, 8), (1, -1), 7),
    },
    {
        "name": "sw8",
        "winner": _path((1, 8), (1, -1), 8),
        "follower": _path((2, 1), (1, 1), 7),
        "decoy_same": _path((1, 7), (1, -1), 7),
        "decoy_opp": _path((1, 1), (1, 1), 7),
    },
    {
        "name": "se7",
        "winner": _path((1, 1), (1, 1), 7),
        "follower": _path((1, 7), (1, -1), 6),
        "decoy_same": _path((1, 2), (1, 1), 6),
        "decoy_opp": _path((1, 8), (1, -1), 6),
    },
    {
        "name": "sw7",
        "winner": _path((1, 7), (1, -1), 7),
        "follower": _path((2, 2), (1, 1), 6),
        "decoy_same": _path((1, 8), (1, -1), 6),
        "decoy_opp": _path((1, 2), (1, 1), 6),
    },
    {
        "name": "se6",
        "winner": _path((1, 3), (1, 1), 6),
        "follower": _path((1, 7), (1, -1), 5),
        "decoy_same": _path((1, 2), (1, 1), 5),
        "decoy_opp": _path((1, 8), (1, -1), 5),
    },
    {
        "name": "sw6",
        "winner": _path((1, 6), (1, -1), 6),
        "follower": _path((2, 1), (1, 1), 5),
        "decoy_same": _path((1, 7), (1, -1), 5),
        "decoy_opp": _path((1, 1), (1, 1), 5),
    },
)


def normalize_settings(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"paint_target"}:
        raise ValueError("settings must contain exactly paint_target")
    target = settings["paint_target"]
    if type(target) is not str or target not in PAINT_TARGETS:
        raise ValueError(f"paint_target must be one of {PAINT_TARGETS}")
    return {"paint_target": target}


def program(settings: dict[str, Any]) -> str:
    target = normalize_settings(settings)["paint_target"]
    return CANONICAL_PROGRAM if target == "winner" else FOLLOWER_PROGRAM


def select_crossing_follower(grid):
    ranked = GEN._ranked_runs(grid)
    if not ranked:
        raise ValueError("the crossing-follower rule requires at least one run")
    winner = ranked[0]
    winner_cells = set(winner["cells"])
    candidates = [
        run
        for run in ranked[1:]
        if run["direction"] != winner["direction"]
        and len(run["cells"]) < len(winner["cells"])
        and winner_cells.intersection(run["cells"])
    ]
    if not candidates:
        raise ValueError("the crossing-follower rule requires a shorter crossing opposite run")
    return candidates[0]


def solve_python(grid, settings: dict[str, Any]):
    target = normalize_settings(settings)["paint_target"]
    errors = GEN._analysis(grid)["errors"]
    if errors:
        raise ValueError("; ".join(errors))
    if target == "winner":
        return GEN.rule_mirror(grid)
    follower = select_crossing_follower(grid)
    output = [list(row) for row in grid]
    for row, col in follower["cells"]:
        output[row][col] = 8
    return output


def _template_paths(template):
    return [
        template["winner"],
        template["follower"],
        template["decoy_same"],
        template["decoy_opp"],
    ]


def _draw_scene(template, rng: random.Random):
    paths = _template_paths(template)
    protected = set().union(*(set(path) for path in paths))
    forced = GEN._forced_blockers(paths)
    if protected & forced:
        raise AssertionError(f"template {template['name']} has an invalid terminator")
    interior = {(row, col) for row in range(1, 9) for col in range(1, 9)}
    available = sorted(interior - protected - forced)
    for _ in range(5000):
        zero_target = rng.randint(39, 48)
        blockers_needed = 64 - zero_target - len(forced)
        if not 0 <= blockers_needed <= len(available):
            continue
        blockers = forced | set(rng.sample(available, blockers_needed))
        grid = [[5] * 10 for _ in range(10)]
        for row, col in interior - blockers:
            grid[row][col] = 0
        if GEN._analysis(grid)["errors"]:
            continue
        ranked = GEN._ranked_runs(grid)
        if ranked[0]["cells"] != template["winner"]:
            continue
        try:
            follower = select_crossing_follower(grid)
        except ValueError:
            continue
        if follower["cells"] != template["follower"]:
            continue
        if ranked[1]["cells"] == follower["cells"]:
            continue
        opposite = [
            run
            for run in ranked
            if run["direction"] != ranked[0]["direction"]
            and len(run["cells"]) < len(ranked[0]["cells"])
        ]
        if not opposite or opposite[0]["cells"] == follower["cells"]:
            continue
        return grid
    raise RuntimeError(f"could not construct causal template {template['name']!r}")




def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical visible projection: demo labels and query inputs only."""
    from reviewer_support import public_challenge_bytes

    return json.loads(public_challenge_bytes(episode))


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Return one controller turn without future queries or total-count metadata."""
    public = public_challenge(episode)
    if type(query_index) is not int or not 0 <= query_index < len(public["test"]):
        raise IndexError("query_index is outside this episode")
    return {
        "train": copy.deepcopy(public["train"]),
        "test": [copy.deepcopy(public["test"][query_index])],
    }


def controller_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    """Materialize the sequential one-query views in reveal order."""
    public = public_challenge(episode)
    return [public_turn(public, index) for index in range(len(public["test"]))]


def _validate_count(value: int, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _pair_seed(seed: int, index: int) -> int:
    raw = f"{TASK_ID}:{seed}:{index}:crossing-follower-v1".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    normalized = normalize_settings(settings)
    demos = _validate_count(demos, 2, 6, "demos")
    queries = _validate_count(queries, 1, 4, "queries")
    count = demos + queries
    offset = seed % len(_TEMPLATES)
    pairs = []
    seen = set()
    for index in range(count):
        template = _TEMPLATES[(offset + index) % len(_TEMPLATES)]
        rng = random.Random(_pair_seed(seed, index))
        for _ in range(50):
            grid = _draw_scene(template, rng)
            key = tuple(tuple(row) for row in grid)
            if key not in seen:
                seen.add(key)
                break
        else:
            raise RuntimeError("could not produce distinct episode inputs")
        pairs.append(
            {
                "input": copy.deepcopy(grid),
                "output": solve_python(grid, normalized),
            }
        )
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(normalized),
    }
