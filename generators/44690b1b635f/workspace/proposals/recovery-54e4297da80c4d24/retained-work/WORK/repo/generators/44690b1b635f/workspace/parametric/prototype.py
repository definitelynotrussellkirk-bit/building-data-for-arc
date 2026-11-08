"""Proposed parametric rule variants for ARC task 44690b1b635f.

This module is intentionally separate from the selected canonical generator.
"""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import importlib
import json
from pathlib import Path


NEIGHBOR_MODES = ("cardinal", "king")
PHASES = (0, 1)
DEFAULT_SETTING = {"neighbor_mode": "cardinal", "phase": 0}

CANONICAL_RACKET = """(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) (begin (define marker-cells (positions-of g (lambda (v) (and (!= v 0) (!= v 8))))) (define marker-colors (remove-duplicates (map (lambda (p) (at g (first p) (second p))) marker-cells))) (define (color-count col) (count-if (lambda (p) (= (at g (first p) (second p)) col)) marker-cells)) (define center-color (find-first (lambda (col) (= (color-count col) 1)) marker-colors)) (define arm-color (find-first (lambda (col) (!= col center-color)) marker-colors)) (define start (first (positions-of g (lambda (v) (= v center-color))))) (define (seen-pos? r c seen) (for/or ((e seen)) (and (= (first e) r) (= (second e) c)))) (define visited (let loop ((frontier (list (list (first start) (second start) 0))) (seen (list (list (first start) (second start) 0)))) (if (empty? frontier) seen (let* ((e (first frontier)) (r (first e)) (c (second e)) (d (third e)) (new (filter identity (map (lambda (delta) (let ((nr (+ r (first delta))) (nc (+ c (second delta)))) (and (and (in-bounds? nr nc h w) (!= (at g nr nc) 8) (not (seen-pos? nr nc seen))) (list nr nc (+ d 1))))) cardinal-deltas)))) (loop (append (rest frontier) new) (append seen new)))))) (define (entry-at r c) (find-first (lambda (e) (and (= (first e) r) (= (second e) c))) visited)) (cellmap g (r c v) (let ((e (entry-at r c))) (if (and e (zero? v)) (if (zero? (modulo (third e) 2)) center-color arm-color) v)))))))"""

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_KING = _CARDINAL + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def normalized_rule_hash(source):
    """Match the repository's source pinning convention."""
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def materialize_racket(*, neighbor_mode="cardinal", phase=0):
    """Return an exact executable Racket rule for one bounded setting."""
    if neighbor_mode not in NEIGHBOR_MODES:
        raise ValueError(f"unknown neighbor_mode: {neighbor_mode!r}")
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase!r}")
    program = CANONICAL_RACKET
    if neighbor_mode == "king":
        king_deltas = (
            "(list (list 1 0) (list -1 0) (list 0 1) (list 0 -1) "
            "(list 1 1) (list 1 -1) (list -1 1) (list -1 -1))"
        )
        program = program.replace("cardinal-deltas", king_deltas)
    if phase == 1:
        program = program.replace(
            "(if (zero? (modulo (third e) 2)) center-color arm-color)",
            "(if (zero? (modulo (+ (third e) 1) 2)) center-color arm-color)",
        )
    return program


def solve_variant(grid, *, neighbor_mode="cardinal", phase=0):
    """Apply one bounded rule setting to a lawful maze grid."""
    if neighbor_mode not in NEIGHBOR_MODES:
        raise ValueError(f"unknown neighbor_mode: {neighbor_mode!r}")
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase!r}")
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be non-empty and rectangular")

    height, width = len(grid), len(grid[0])
    markers = {}
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value not in (0, 8):
                markers.setdefault(value, []).append((row, col))
    singleton = [color for color, cells in markers.items() if len(cells) == 1]
    if len(markers) != 2 or len(singleton) != 1:
        raise ValueError("expected two marker colors and exactly one singleton color")
    center_color = singleton[0]
    arm_color = next(color for color in markers if color != center_color)
    if len(markers[arm_color]) < 2:
        raise ValueError("arm marker color must occur at least twice")

    start = markers[center_color][0]
    distances = {start: 0}
    queue = deque([start])
    directions = _CARDINAL if neighbor_mode == "cardinal" else _KING
    while queue:
        row, col = queue.popleft()
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 8
                and (nr, nc) not in distances
            ):
                distances[(nr, nc)] = distances[(row, col)] + 1
                queue.append((nr, nc))

    output = [list(row) for row in grid]
    for (row, col), distance in distances.items():
        if grid[row][col] == 0:
            output[row][col] = center_color if (distance + phase) % 2 == 0 else arm_color
    return output


def _setting_key(setting):
    return f"{setting['neighbor_mode']}:{setting['phase']}"


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _all_settings():
    return [
        {"neighbor_mode": neighbor_mode, "phase": phase}
        for neighbor_mode in NEIGHBOR_MODES
        for phase in PHASES
    ]


def build_episode(
    *,
    seed,
    neighbor_mode="cardinal",
    phase=0,
    demo_count=2,
    query_count=4,
    difficulty="medium",
):
    """Build one private, fully labelled episode with a fixed rule setting."""
    if neighbor_mode not in NEIGHBOR_MODES:
        raise ValueError(f"unknown neighbor_mode: {neighbor_mode!r}")
    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase!r}")
    if isinstance(demo_count, bool) or not isinstance(demo_count, int) or demo_count < 1:
        raise ValueError("demo_count must be a positive integer")
    if isinstance(query_count, bool) or not isinstance(query_count, int) or query_count < 1:
        raise ValueError("query_count must be a positive integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    canonical = importlib.import_module("puzzle_generators.per_puzzle.44690b1b635f.generator")
    setting = {"neighbor_mode": neighbor_mode, "phase": phase}
    rivals = [candidate for candidate in _all_settings() if candidate != setting]
    chosen_key = _setting_key(setting)

    candidates = []
    seen = set()
    for sample_index in range(256):
        grid = canonical.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            scene_profile="procedural_maze",
        )
        key = _grid_key(grid)
        if key in seen:
            continue
        seen.add(key)
        output = solve_variant(grid, **setting)
        differing = {
            _setting_key(rival)
            for rival in rivals
            if solve_variant(grid, **rival) != output
        }
        candidates.append({"input": grid, "output": output, "differing": differing})
        if len(candidates) >= max(demo_count + query_count + 12, 24):
            break

    if len(candidates) < demo_count + query_count:
        raise RuntimeError("could not generate enough distinct episode inputs")

    selected = set()
    train_candidates = []
    uncovered = {_setting_key(rival) for rival in rivals}
    while uncovered and len(train_candidates) < demo_count:
        available = [
            (len(candidate["differing"] & uncovered), -index, index, candidate)
            for index, candidate in enumerate(candidates)
            if index not in selected
        ]
        _, _, index, candidate = max(available)
        if not (candidate["differing"] & uncovered):
            break
        selected.add(index)
        train_candidates.append(candidate)
        uncovered -= candidate["differing"]
    if uncovered:
        raise RuntimeError(
            f"{demo_count} demonstrations do not distinguish setting {chosen_key} from {sorted(uncovered)}"
        )
    for index, candidate in enumerate(candidates):
        if len(train_candidates) >= demo_count:
            break
        if index not in selected:
            selected.add(index)
            train_candidates.append(candidate)

    query_candidates = []
    for index, candidate in enumerate(candidates):
        if index in selected or not candidate["differing"]:
            continue
        selected.add(index)
        query_candidates.append(candidate)
        if len(query_candidates) == query_count:
            break
    if len(query_candidates) != query_count:
        raise RuntimeError("could not generate enough rival-sensitive distinct queries")

    racket_program = materialize_racket(**setting)
    source_path = Path(canonical.__file__).resolve()
    return {
        "schema": "arcpuzzles-parametric-prototype-v1",
        "task_id": "44690b1b635f",
        "source_version": canonical.VERSION,
        "source_rule_hash": canonical.RULE_HASH,
        "source_generator_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "seed": seed,
        "difficulty": difficulty,
        "setting": setting,
        "setting_fixed": True,
        "parameter_bounds": {
            "neighbor_mode": list(NEIGHBOR_MODES),
            "phase": list(PHASES),
        },
        "demo_count": demo_count,
        "query_count": query_count,
        "train": [
            {"input": copy.deepcopy(candidate["input"]), "output": copy.deepcopy(candidate["output"])}
            for candidate in train_candidates
        ],
        "test": [
            {"input": copy.deepcopy(candidate["input"]), "output": copy.deepcopy(candidate["output"])}
            for candidate in query_candidates
        ],
        "distinguished_rivals": sorted(
            set().union(*(candidate["differing"] for candidate in train_candidates))
        ),
        "query_evidence": [
            {
                "query_index": index,
                "differing_rivals": sorted(candidate["differing"]),
                "differs_from_at_least_one_rival": bool(candidate["differing"]),
            }
            for index, candidate in enumerate(query_candidates)
        ],
        "racket_program": racket_program,
        "racket_sha256": hashlib.sha256(racket_program.encode()).hexdigest(),
        "racket_rule_hash": normalized_rule_hash(racket_program),
    }


def public_challenge(episode):
    """Strip settings, reference programs, and query answers from an episode."""
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_identifier(episode):
    """Derive an opaque filename solely from model-visible challenge content."""
    visible = json.dumps(public_challenge(episode), sort_keys=True, separators=(",", ":"))
    return f"maze-{hashlib.sha256(visible.encode()).hexdigest()[:16]}.json"


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_evidence_bundle(
    out_dir,
    *,
    seed=17,
    demo_count=3,
    query_count=4,
    difficulty="medium",
    settings=None,
):
    """Write source-bound public challenges and separate private evidence."""
    out_dir = Path(out_dir)
    settings = settings or [DEFAULT_SETTING, {"neighbor_mode": "king", "phase": 1}]
    rows = []
    for index, setting in enumerate(settings):
        episode = build_episode(
            seed=seed + index,
            demo_count=demo_count,
            query_count=query_count,
            difficulty=difficulty,
            **setting,
        )
        public_file = public_identifier(episode)
        private_file = f"setting-{index + 1}.json"
        public_value = public_challenge(episode)
        _write_json(out_dir / "public" / public_file, public_value)
        _write_json(out_dir / "private" / private_file, episode)
        rows.append({
            "setting": copy.deepcopy(setting),
            "public_file": public_file,
            "private_file": private_file,
            "public_sha256": hashlib.sha256(
                (out_dir / "public" / public_file).read_bytes()
            ).hexdigest(),
            "private_sha256": hashlib.sha256(
                (out_dir / "private" / private_file).read_bytes()
            ).hexdigest(),
            "racket_sha256": episode["racket_sha256"],
            "racket_rule_hash": episode["racket_rule_hash"],
            "distinguished_rivals": episode["distinguished_rivals"],
        })
    manifest = {
        "schema": "arcpuzzles-parametric-evidence-manifest-v1",
        "task_id": "44690b1b635f",
        "seed": seed,
        "difficulty": difficulty,
        "demo_count": demo_count,
        "query_count": query_count,
        "episodes": rows,
        "racket_execution": "pending_full_packet_runtime",
    }
    _write_json(out_dir / "private" / "manifest.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    args = parser.parse_args(argv)
    manifest = write_evidence_bundle(
        args.out,
        seed=args.seed,
        demo_count=args.demos,
        query_count=args.queries,
        difficulty=args.difficulty,
    )
    print(args.out / "private" / "manifest.json")
    return 0 if manifest["episodes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
