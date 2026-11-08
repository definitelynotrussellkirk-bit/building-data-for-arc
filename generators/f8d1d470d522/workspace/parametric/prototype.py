#!/usr/bin/env python3
"""Prototype an episode-level shortest-path turn preference for f8d1d470d522.

The selected production rule remains ``turn_preference='fewest'``.  The
alternative chooses, among legal shortest paths, the path with the most
direction changes.  A single setting is fixed for the episode.  The native
adapter supports two to six demonstrations and exactly four private queries;
retained evidence executes standalone Racket programs for both settings.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


TASK_ID = "f8d1d470d522"
PARAMETER_NAME = "turn_preference"
ALLOWED_TURN_PREFERENCES = ("fewest", "most")
DEFAULT_TURN_PREFERENCE = "fewest"
PROTOTYPE_VERSION = "2.0.0"
CARDINAL = ((0, 1), (1, 0), (0, -1), (-1, 0))
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"
NATIVE_RULE_PATHS = {
    "fewest": RULE_DIR / "turn_fewest.rkt",
    "most": RULE_DIR / "turn_most.rkt",
}

# Local repository commands do not install authoring helpers.  Portable task
# runtimes do, so prefer the import and otherwise add the nearest shared/runtime
# ancestor without consulting cwd or an environment-selected repository.
try:
    from reviewer_support import find_root, load_selected_generator
except ImportError:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "shared" / "runtime"
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    from reviewer_support import find_root, load_selected_generator


def _selected_generator():
    module, path, digest = load_selected_generator(
        TASK_ID,
        root=find_root(__file__),
    )
    return module, path, digest


def _validate_preference(value: str) -> str:
    if type(value) is not str or value not in ALLOWED_TURN_PREFERENCES:
        raise ValueError(
            "turn_preference must be one of "
            f"{ALLOWED_TURN_PREFERENCES}, got {value!r}"
        )
    return value


def program_for(turn_preference: str) -> str:
    """Return the native ``rule!`` source for one finite setting."""
    preference = _validate_preference(turn_preference)
    path = NATIVE_RULE_PATHS[preference]
    if not path.is_file():
        raise FileNotFoundError(f"missing native rule source: {path}")
    source = path.read_text(encoding="utf-8")
    if not source.startswith("(rule!"):
        raise ValueError(f"native rule source is not one complete rule!: {path}")
    return source


def choose_parameters(episode_seed: int) -> dict[str, str]:
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    return {
        PARAMETER_NAME: ALLOWED_TURN_PREFERENCES[
            episode_seed % len(ALLOWED_TURN_PREFERENCES)
        ]
    }


def _validate_grid(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty row list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(
        type(value) is not int or value not in (0, 7, 8, 9)
        for row in grid
        for value in row
    ):
        raise ValueError("grid must use only colors 0, 7, 8, and 9")
    return [row[:] for row in grid]


def _adjacent_to_seven(grid: list[list[int]], row: int, col: int) -> bool:
    height = len(grid)
    width = len(grid[0])
    return any(
        0 <= row + dr < height
        and 0 <= col + dc < width
        and grid[row + dr][col + dc] == 7
        for dr, dc in CARDINAL
    )


def python_reference(
    grid: list[list[int]],
    *,
    turn_preference: str,
) -> list[list[int]]:
    """Independent shortest-path dynamic program for one parameter setting."""
    preference = _validate_preference(turn_preference)
    source = _validate_grid(grid)
    height = len(source)
    width = len(source[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 9
    ]
    if len(markers) != 2:
        raise ValueError("exactly two color-9 markers are required")
    start, goal = markers
    allowed = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] == 9
        or (
            source[row][col] == 8
            and not _adjacent_to_seven(source, row, col)
        )
    }
    distances = {start: 0}
    queue = deque((start,))
    while queue:
        row, col = queue.popleft()
        for dr, dc in CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor in allowed and neighbor not in distances:
                distances[neighbor] = distances[(row, col)] + 1
                queue.append(neighbor)
    if goal not in distances:
        raise ValueError("markers have no legal route")

    # State: (cell, previous direction) -> (selected turn count, path).
    states = {(start, None): (0, (start,))}
    for distance in range(distances[goal]):
        current = [
            (key, value)
            for key, value in states.items()
            if distances[key[0]] == distance
        ]
        for ((row, col), previous_direction), (count, path) in current:
            for direction in CARDINAL:
                dr, dc = direction
                neighbor = row + dr, col + dc
                if distances.get(neighbor) != distance + 1:
                    continue
                next_count = count + int(
                    previous_direction is not None
                    and previous_direction != direction
                )
                candidate = next_count, path + (neighbor,)
                key = neighbor, direction
                incumbent = states.get(key)
                better = (
                    incumbent is None
                    or (
                        candidate[0] < incumbent[0]
                        if preference == "fewest"
                        else candidate[0] > incumbent[0]
                    )
                    or (
                        candidate[0] == incumbent[0]
                        and candidate[1] < incumbent[1]
                    )
                )
                if better:
                    states[key] = candidate

    goal_states = [
        value
        for (cell, _direction), value in states.items()
        if cell == goal
    ]
    if not goal_states:
        raise ValueError("shortest-path dynamic program produced no goal")
    selected_count = (
        min(value[0] for value in goal_states)
        if preference == "fewest"
        else max(value[0] for value in goal_states)
    )
    selected_path = min(
        value[1]
        for value in goal_states
        if value[0] == selected_count
    )
    output = [row[:] for row in source]
    for row, col in selected_path:
        output[row][col] = 9
    return output


def _derived_seed(episode_seed: int, pair_index: int) -> int:
    digest = hashlib.sha256(
        f"f8d1-parametric:v1:{episode_seed}:{pair_index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def build_input(episode_seed: int, pair_index: int) -> list[list[int]]:
    """Draw a production-domain input with unique optima for both settings."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(pair_index) is not int or pair_index < 0:
        raise ValueError("pair_index must be a nonnegative integer (not bool)")
    generator, _path, _digest = _selected_generator()
    for attempt in range(96):
        recipe_index = pair_index * 97 + attempt
        grid = generator.generate(
            _derived_seed(episode_seed, recipe_index),
            episode_seed * 1009 + recipe_index,
            difficulty="medium",
            selection_mode="fewest_turns",
        )
        fewest = generator._solve(grid, turn_preference="fewest")
        most = generator._solve(grid, turn_preference="most")
        if (
            fewest is not None
            and most is not None
            and fewest["optimal_path_count"] == 1
            and most["optimal_path_count"] == 1
            and fewest["output"] != most["output"]
            and fewest["output"] == generator.rule_mirror(grid)
        ):
            return [row[:] for row in grid]
    raise RuntimeError("could not draw a unique setting-distinguishing route scene")


def _rotate_square(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def build_stress_input(episode_seed: int) -> list[list[int]]:
    """Construct a 30x30 two-route graph with unique min/max-turn paths."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    grid = [[0 for _ in range(30)] for _ in range(30)]
    start = (2, 14)
    goal = (27, 14)

    # Route A: 49 steps and two turns.
    route_a = [(2, col) for col in range(14, 27)]
    route_a += [(row, 26) for row in range(3, 28)]
    route_a += [(27, col) for col in range(25, 13, -1)]

    # Route B: the same 49 steps, but 23 turns.  Two-cell horizontal and
    # vertical runs make this an induced corridor: nonconsecutive path cells
    # never become orthogonal neighbors, so there are no hidden shortcuts.
    route_b = [start]
    row, col = start
    for _ in range(6):
        for _ in range(2):
            col -= 1
            route_b.append((row, col))
        for _ in range(2):
            row += 1
            route_b.append((row, col))
        for _ in range(2):
            col += 1
            route_b.append((row, col))
        for _ in range(2):
            row += 1
            route_b.append((row, col))
    row += 1
    route_b.append((row, col))
    if route_b[-1] != goal:
        raise AssertionError("stress route construction did not reach the goal")

    for row, col in {*route_a, *route_b}:
        grid[row][col] = 8
    grid[start[0]][start[1]] = 9
    grid[goal[0]][goal[1]] = 9

    # Substantive disconnected branches and obstacle-colored distractors span
    # the unused half of the canvas without touching either legal route.
    for index, row in enumerate((5, 9, 13, 17, 21, 25)):
        stop = 7 + (index % 3)
        for col in range(1 + (index % 2), stop):
            grid[row][col] = 8
        grid[row - 1][stop + 1] = 7
        grid[row + (index % 2)][29] = 7

    for _ in range(episode_seed % 4):
        grid = _rotate_square(grid)
    fewest = python_reference(grid, turn_preference="fewest")
    most = python_reference(grid, turn_preference="most")
    if fewest == most:
        raise AssertionError("30x30 stress scene does not distinguish turn settings")
    return grid


def build_episode(
    episode_seed: int,
    *,
    turn_preference: str | None = None,
    demos: int = 2,
    queries: int = 1,
) -> dict[str, Any]:
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be an integer (not bool)")
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an integer in 2..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be an integer in 1..4")
    preference = (
        choose_parameters(episode_seed)[PARAMETER_NAME]
        if turn_preference is None
        else _validate_preference(turn_preference)
    )
    grids = [build_input(episode_seed, pair_index) for pair_index in range(demos + queries)]
    if queries == 4:
        grids[-1] = build_stress_input(episode_seed)
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    if len(frozen) != len(set(frozen)):
        raise AssertionError("episode inputs must be distinct")
    pairs = [
        {
            "input": deepcopy(grid),
            "output": python_reference(grid, turn_preference=preference),
        }
        for grid in grids
    ]
    return {
        "schema": "arcpuzzles-parametric-turn-preference-episode-v2",
        "prototype_version": PROTOTYPE_VERSION,
        "seed": episode_seed,
        "parameter": {PARAMETER_NAME: preference},
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(preference),
    }


def generate_episode(
    episode_seed: int,
    turn_preference: str,
    demos: int,
    queries: int,
) -> dict[str, Any]:
    episode = build_episode(
        episode_seed,
        turn_preference=turn_preference,
        demos=demos,
        queries=queries,
    )
    return {
        "train": episode["train"],
        "test": episode["test"],
        "program_solution": episode["program_solution"],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "arcpuzzles-parametric-turn-preference-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def racket_program(turn_preference: str) -> str:
    preference = _validate_preference(turn_preference)
    return f'''#lang racket
(require json)

(define TURN-PREFERENCE '{preference})
(define DIRS '((0 1) (1 0) (0 -1) (-1 0)))
(define input-grid (read-json))
(define H (length input-grid))
(define W (length (first input-grid)))
(define source (list->vector (map list->vector input-grid)))
(define out (list->vector (map (lambda (row) (list->vector (vector->list row)))
                               (vector->list source))))

(define (cell grid r c) (vector-ref (vector-ref grid r) c))
(define (set-cell! grid r c value) (vector-set! (vector-ref grid r) c value))
(define (inside? r c) (and (<= 0 r) (< r H) (<= 0 c) (< c W)))
(define (plus point direction)
  (list (+ (first point) (first direction))
        (+ (second point) (second direction))))
(define (adjacent-seven? point)
  (for/or ([direction DIRS])
    (define next (plus point direction))
    (and (inside? (first next) (second next))
         (= (cell source (first next) (second next)) 7))))
(define (allowed? point)
  (define value (cell source (first point) (second point)))
  (or (= value 9) (and (= value 8) (not (adjacent-seven? point)))))

(define markers
  (for*/list ([r (in-range H)] [c (in-range W)]
              #:when (= (cell source r c) 9))
    (list r c)))
(define start (first markers))
(define goal (second markers))
(define distance (make-hash))
(hash-set! distance start 0)
(define queue (list start))
(let bfs ()
  (unless (null? queue)
    (define current (first queue))
    (set! queue (rest queue))
    (for ([direction DIRS])
      (define next (plus current direction))
      (when (and (inside? (first next) (second next))
                 (allowed? next)
                 (not (hash-has-key? distance next)))
        (hash-set! distance next (+ 1 (hash-ref distance current)))
        (set! queue (append queue (list next)))))
    (bfs)))

(define shortest-paths '())
(define (walk current reverse-path)
  (if (equal? current goal)
      (set! shortest-paths (cons (reverse reverse-path) shortest-paths))
      (for ([direction DIRS])
        (define next (plus current direction))
        (when (and (hash-has-key? distance next)
                   (= (hash-ref distance next)
                      (+ 1 (hash-ref distance current))))
          (walk next (cons next reverse-path))))))
(walk start (list start))

(define (turn-count path)
  (define directions
    (for/list ([a path] [b (rest path)])
      (list (- (first b) (first a)) (- (second b) (second a)))))
  (for/sum ([a directions] [b (rest directions)])
    (if (equal? a b) 0 1)))
(define (point<? a b)
  (or (< (first a) (first b))
      (and (= (first a) (first b)) (< (second a) (second b)))))
(define (path<? a b)
  (cond [(null? a) (not (null? b))]
        [(null? b) #f]
        [(equal? (first a) (first b)) (path<? (rest a) (rest b))]
        [else (point<? (first a) (first b))]))
(define (better? candidate incumbent)
  (define ct (turn-count candidate))
  (define it (turn-count incumbent))
  (or (if (eq? TURN-PREFERENCE 'fewest) (< ct it) (> ct it))
      (and (= ct it) (path<? candidate incumbent))))
(define selected
  (for/fold ([best (first shortest-paths)])
            ([candidate (rest shortest-paths)])
    (if (better? candidate best) candidate best)))
(for ([point selected])
  (set-cell! out (first point) (second point) 9))
(write-json (for/list ([row (in-vector out)]) (vector->list row)))
(newline)
'''


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rule_sha256(turn_preference: str) -> str:
    return sha256_text(racket_program(turn_preference))


def rule_path(turn_preference: str) -> Path:
    return ROOT / "legacy_rules" / f"turn_{_validate_preference(turn_preference)}.rkt"


def materialize_rules() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for preference in ALLOWED_TURN_PREFERENCES:
        rule_path(preference).write_text(
            racket_program(preference),
            encoding="utf-8",
        )


def run_racket(
    turn_preference: str,
    grid: list[list[int]],
) -> list[list[int]]:
    preference = _validate_preference(turn_preference)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    path = rule_path(preference)
    expected = racket_program(preference)
    if not path.is_file() or path.read_text(encoding="utf-8") != expected:
        raise RuntimeError(f"retained Racket source is stale: {path}")
    proc = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Racket failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    result = json.loads(proc.stdout)
    if not isinstance(result, list):
        raise RuntimeError(f"Racket returned non-grid JSON: {result!r}")
    return result


def build_evidence(episode_seed: int) -> dict[str, Any]:
    materialize_rules()
    _generator, generator_path, generator_sha = _selected_generator()
    settings: dict[str, Any] = {}
    for preference in ALLOWED_TURN_PREFERENCES:
        other = next(
            value
            for value in ALLOWED_TURN_PREFERENCES
            if value != preference
        )
        episode = build_episode(
            episode_seed,
            turn_preference=preference,
        )
        executions = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(preference, pair["input"])
                alternative = run_racket(other, pair["input"])
                mirror = python_reference(
                    pair["input"],
                    turn_preference=preference,
                )
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(
                        "Racket/Python/episode mismatch for "
                        f"{preference} {split}[{pair_index}]"
                    )
                executions.append({
                    "split": split,
                    "pair_index": pair_index,
                    "input": pair["input"],
                    "racket_output": actual,
                    "alternative_preference": other,
                    "alternative_racket_output": alternative,
                    "settings_disagree": actual != alternative,
                })
        settings[preference] = {
            "turn_preference": preference,
            "is_canonical_default": preference == DEFAULT_TURN_PREFERENCE,
            "racket_path": str(rule_path(preference).relative_to(find_root(__file__))),
            "racket_text": racket_program(preference),
            "racket_sha256": rule_sha256(preference),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executions": executions,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": all(
                row["settings_disagree"]
                for row in executions
                if row["split"] == "train"
            ),
        }
    return {
        "schema": "arcpuzzles-parametric-turn-preference-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": episode_seed,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_TURN_PREFERENCES),
            "canonical_default": DEFAULT_TURN_PREFERENCE,
            "selection": (
                "ALLOWED_TURN_PREFERENCES[episode_seed % 2], once per episode"
            ),
        },
        "prototype_source_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "selected_generator_path": str(generator_path),
        "selected_generator_sha256": generator_sha,
        "settings": settings,
        "limits": [
            "Bounded evidence for two settings at one seed, not production approval.",
            "The selected generator and canonical Racket authority remain fixed at turn_preference='fewest'.",
            "The demonstrations refute only the retained opposite setting; undeclared rival rules are not exhausted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args()
    evidence = build_evidence(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for preference, setting in evidence["settings"].items():
            path = args.write_public / f"turn_{preference}_public.json"
            path.write_text(
                json.dumps(
                    setting["public_challenge"],
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
    print(json.dumps({
        "status": evidence["status"],
        "seed": evidence["seed"],
        "settings": {
            preference: {
                "racket_sha256": row["racket_sha256"],
                "all_pairs_match_racket": row["all_pairs_match_racket"],
                "every_demo_refutes_alternative_setting": row[
                    "every_demo_refutes_alternative_setting"
                ],
            }
            for preference, row in evidence["settings"].items()
        },
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
