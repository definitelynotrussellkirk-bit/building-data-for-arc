"""Proposed episode-fixed block voting; canonical production routing is separate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
TASK_ID = "a2d9d069c7d5"
DEFAULT = {"vote_unit": "objects", "keep_on_tie": False}
SETTINGS = tuple({"vote_unit": unit, "keep_on_tie": tie}
                 for unit in ("objects", "cells") for tie in (False, True))
DEMO_PROFILES = ((1, 1, 7, 4, 6), (5, 5, 2, 2, 2, 6),
                 (1, 3, 2, 4), (1, 1, 1, 1, 2))
QUERY_PROFILES = ((1, 1, 1, 3, 4, 6), (1, 7, 2, 2, 2, 4),
                  (1, 1, 3, 5, 2, 2, 4, 4),
                  (1, 1, 1, 1, 3, 3, 3, 3, 2, 6))
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def parameters(value):
    if (type(value) is not dict or set(value) != set(DEFAULT)
            or value["vote_unit"] not in ("objects", "cells")
            or type(value["keep_on_tie"]) is not bool):
        raise ValueError("settings require vote_unit=objects|cells and boolean keep_on_tie")
    return dict(value)


def _components(grid, color):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color}
    groups = []
    while remaining:
        origin = min(remaining)
        remaining.remove(origin)
        group, queue = [origin], [origin]
        while queue:
            r, c = queue.pop()
            for dr, dc in CARDINAL:
                neighbor = r + dr, c + dc
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
                    group.append(neighbor)
        groups.append(group)
    return groups


def analyze(grid):
    """Read all object roles from the original input, before any recoloring."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a 1..30 rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid requires exact integer colors 0..9")
    counts = {}
    for row in grid:
        for color in row:
            if color != 7:
                counts[color] = counts.get(color, 0) + 1
    if len(counts) != 2:
        raise ValueError("need exactly two non-background colors")
    marker, block = sorted(counts, key=lambda color: (counts[color], color))
    if counts[marker] != 5 or counts[block] <= 5:
        raise ValueError("need a five-cell minority plus and a strict majority block color")
    plus = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == marker]
    center = (sum(r for r, c in plus) // 5, sum(c for r, c in plus) // 5)
    r, c = center
    if set(plus) != {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}:
        raise ValueError("minority color must form a plus")
    groups = _components(grid, block)
    if not 4 <= len(groups) <= 12:
        raise ValueError("need 4..12 distinct block components")
    squares = []
    for group in groups:
        r0, c0 = min(r for r, c in group), min(c for r, c in group)
        h = max(r for r, c in group) - r0 + 1
        w = max(c for r, c in group) - c0 + 1
        if h != w or len(group) != h * w or not 1 <= h <= 7:
            raise ValueError("each block must be a solid square with side 1..7")
        squares.append((r0, c0, h))
    return {"marker_color": marker, "block_color": block, "plus": plus, "squares": squares}


def _paint(grid, scene, keep, mark=True):
    output = [row[:] for row in grid]
    marker = scene["marker_color"]
    if not keep:
        for r, c in scene["plus"]:
            output[r][c] = 7
    if mark:
        for r, c, side in scene["squares"]:
            if side % 2:
                output[r + side // 2][c + side // 2] = marker
    return output


def _validate_label(output, grid):
    # Python equality aliases True/1 and 7.0/7; labels must satisfy the JSON grid contract first.
    if (type(output) is not list or len(output) != len(grid)
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(value) is not int or not 0 <= value <= 9 for value in row)
                   for row in output)):
        raise ValueError("label must have the input shape and exact integer colors 0..9")


def python_output(grid, settings):
    """Independent mirror for parity checks and finite rival certificates, not labels."""
    settings = parameters(settings)
    scene = analyze(grid)
    votes = [0, 0]
    for _, _, side in scene["squares"]:
        votes[side % 2] += 1 if settings["vote_unit"] == "objects" else side * side
    keep = votes[1] > votes[0] or (settings["keep_on_tie"] and votes[1] == votes[0])
    return _paint(grid, scene, keep)


def materialize_program(settings):
    settings = parameters(settings)
    weight = "1" if settings["vote_unit"] == "objects" else (
        "(let ((bb (obj-bbox o))) (* (+ 1 (- (nth bb 2) (nth bb 0))) "
        "(+ 1 (- (nth bb 3) (nth bb 1)))))")
    return (HERE / "rule_template.rkt").read_text().replace("@WEIGHT@", weight).replace(
        "@COMPARE@", ">=" if settings["keep_on_tie"] else ">")


class RacketLabeler:
    """Context-managed labels from this checkout's protected persistent bridge."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10)
        self.identity = self.bridge.runtime_identity
        self.calls = 0
        self.wrapped = {}
        if not self.identity.get("protected"):
            self.bridge.shutdown()
            raise RuntimeError("protected Racket runtime is required")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def __call__(self, program, grid):
        from puzzle_generators.rule_wrap import wrap_rule
        analyze(grid)
        if program not in self.wrapped:
            self.wrapped[program] = wrap_rule(program)
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = self.bridge.eval_text(f"({self.wrapped[program]} {literal})")
        self.calls += 1
        _validate_label(output, grid)
        return output


def sample_scene(seed, sides, *, height=20, width=20):
    _integer(seed, 0, 2**64 - 1, "seed")
    _integer(height, 16, 30, "height")
    _integer(width, 16, 30, "width")
    if (type(sides) not in (list, tuple) or not 4 <= len(sides) <= 12
            or any(type(side) is not int or not 1 <= side <= 7 for side in sides)
            or sum(side * side for side in sides) <= 5):
        raise ValueError("sides require 4..12 squares in 1..7, with block area above five")
    rng = random.Random(seed)
    marker, block = rng.sample([color for color in range(10) if color != 7], 2)
    for _ in range(80):
        grid = [[7] * width for _ in range(height)]
        occupied, blocked = set(), set()
        for side in sorted(sides, reverse=True):
            for attempt in range(200):
                r0, c0 = rng.randrange(height - side + 1), rng.randrange(width - side + 1)
                cells = {(r0 + dr, c0 + dc) for dr in range(side) for dc in range(side)}
                if not cells & blocked:
                    break
            else:
                break
            occupied.update(cells)
            blocked.update(cells)
            blocked.update((r + dr, c + dc) for r, c in cells for dr, dc in CARDINAL)
            for r, c in cells:
                grid[r][c] = block
        else:
            for _ in range(200):
                r, c = rng.randrange(1, height - 1), rng.randrange(1, width - 1)
                hood = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
                if not hood & occupied:
                    for dr, dc in ((0, 0), *CARDINAL):
                        grid[r + dr][c + dc] = marker
                    analyze(grid)
                    return grid
    raise ValueError("bounded layout search exhausted; choose a larger canvas or another seed")


def _shortcut(grid, name):
    scene = analyze(grid)
    sides = [side for r, c, side in scene["squares"]]
    if name == "always_keep":
        keep = True
    elif name == "always_erase":
        keep = False
    elif name.startswith("side_votes"):
        odd = sum(side for side in sides if side % 2)
        even = sum(side for side in sides if not side % 2)
        keep = odd > even or (name.endswith("ties") and odd == even)
    elif name == "largest_parity":
        keep = bool(max(sides) % 2)
    elif name == "area_includes_plus":
        keep = 5 + sum(side * side for side in sides if side % 2) > sum(
            side * side for side in sides if not side % 2)
    elif name == "no_centers":
        return _paint(grid, scene, sum(side % 2 for side in sides) > len(sides) / 2, mark=False)
    elif name == "identity":
        return [row[:] for row in grid]
    else:
        raise ValueError("unknown rival")
    return _paint(grid, scene, keep)


def certify(train, test):
    """Demonstrations alone select rivals; query output fields are never inspected."""
    if not train or not test:
        raise ValueError("certificate needs demonstrations and query inputs")
    for pair in train:
        analyze(pair["input"])
        _validate_label(pair["output"], pair["input"])
    survivors = [dict(setting) for setting in SETTINGS if all(
        python_output(pair["input"], setting) == pair["output"] for pair in train)]
    shortcuts = ("always_keep", "always_erase", "side_votes_strict", "side_votes_ties",
                 "largest_parity", "area_includes_plus", "no_centers", "identity")
    eliminated, surviving_shortcuts = {}, []
    for name in shortcuts:
        mismatch = next((i for i, pair in enumerate(train)
                         if _shortcut(pair["input"], name) != pair["output"]), None)
        if mismatch is None:
            surviving_shortcuts.append(name)
        else:
            eliminated[name] = mismatch
    queries = []
    for index, pair in enumerate(test):
        predictions = [python_output(pair["input"], setting) for setting in survivors]
        predictions += [_shortcut(pair["input"], name) for name in surviving_shortcuts]
        outputs = {json.dumps(output, separators=(",", ":")) for output in predictions}
        queries.append({"query_index": index, "distinct_survivor_predictions": len(outputs),
                        "identifiable": len(outputs) == 1 and bool(survivors)})
    return {"scope": "four parameter settings and eight declared shortcuts; not universal induction",
            "surviving_settings": survivors, "surviving_shortcuts": surviving_shortcuts,
            "shortcut_rejection_demo": eliminated, "queries": queries}


def build_episode(seed, settings=None, *, demos=4, queries=4, height=20, width=20, labeler=None):
    _integer(seed, 0, 2**64 - 1, "seed")
    _integer(demos, 4, 20, "demos")
    _integer(queries, 1, 32, "queries")
    _integer(height, 16, 30, "height")
    _integer(width, 16, 30, "width")
    settings = parameters(DEFAULT if settings is None else settings)
    if labeler is None:
        with RacketLabeler() as live:
            return build_episode(seed, settings, demos=demos, queries=queries,
                                 height=height, width=width, labeler=live)
    profiles = list(DEMO_PROFILES)
    random.Random(seed ^ 0xC5A17).shuffle(profiles)
    profiles += [DEMO_PROFILES[i % 4] for i in range(demos - 4)]
    profiles += [QUERY_PROFILES[i % 4] for i in range(queries)]
    seen, pairs = set(), []
    program = materialize_program(settings)
    for index, profile in enumerate(profiles):
        for attempt in range(64):
            scene_seed = int.from_bytes(hashlib.sha256(f"{seed}:{index}:{attempt}".encode()).digest()[:8], "big")
            grid = sample_scene(scene_seed, profile, height=height, width=width)
            key = json.dumps(grid, separators=(",", ":"))
            if key not in seen:
                seen.add(key)
                break
        else:
            raise ValueError("distinct-input retry budget exhausted")
        output = labeler(program, grid)
        if output != python_output(grid, settings):
            raise ValueError("Python/Racket parity mismatch")
        pairs.append({"input": grid, "output": output})
    certificate = certify(pairs[:demos], pairs[demos:])
    if (certificate["surviving_settings"] != [settings]
            or not all(query["identifiable"] for query in certificate["queries"])):
        raise ValueError("demonstrations do not identify the query answers")
    return {"schema": "block-vote-parametric-prototype-v1", "task_id": TASK_ID,
            "status": "proposed", "training_admitted": False, "seed": seed,
            "parameters": settings, "program": program,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "train": pairs[:demos], "test": pairs[demos:], "certificate": certificate,
            "racket_identity": labeler.identity}


def verify_episode(episode, *, labeler):
    settings = parameters(episode["parameters"])
    program = materialize_program(settings)
    if (episode.get("program") != program
            or episode.get("program_sha256") != hashlib.sha256(program.encode()).hexdigest()):
        raise ValueError("program identity differs from parameters")
    pairs = episode["train"] + episode["test"]
    if len({json.dumps(pair["input"]) for pair in pairs}) != len(pairs):
        raise ValueError("duplicate episode input")
    for pair in pairs:
        _validate_label(pair["output"], pair["input"])
        if labeler(program, pair["input"]) != pair["output"]:
            raise ValueError("Racket label replay mismatch")
    certificate = certify(episode["train"], episode["test"])
    if (certificate["surviving_settings"] != [settings]
            or not all(q["identifiable"] for q in certificate["queries"])
            or episode.get("certificate") != certificate):
        raise ValueError("invalid demonstration certificate")
    return certificate


def write_batch(episodes, destination):
    """Type-checked projection; callers supply built or explicitly replayed episodes.

    This writer is not an attestation or an independent Racket verification pass.
    """
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episodes = list(episodes)
    if not episodes:
        raise ValueError("empty batch")
    entries = [(public_challenge_id(ep), public_challenge_bytes(ep), ep) for ep in episodes]
    for episode in episodes:
        for pair in episode["train"] + episode["test"]:
            _validate_label(pair["output"], pair["input"])
    if len({entry[0] for entry in entries}) != len(entries):
        raise ValueError("duplicate visible challenge")
    # Finish validation before creating any destination. All names depend only on visible bytes.
    private = json.dumps({entry[0]: entry[2] for entry in sorted(entries)},
                         sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "public").mkdir()
    (destination / "private").mkdir()
    for identifier, raw, _ in sorted(entries):
        (destination / "public" / (identifier + ".json")).write_bytes(raw)
    (destination / "private/episodes.json").write_text(private)
    return {"episodes": len(entries), "public_ids": sorted(entry[0] for entry in entries),
            "query_labels": sum(len(ep["test"]) for ep in episodes)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=4)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument("--width", type=int, default=20)
    parser.add_argument("--vote-unit", choices=("objects", "cells"), default="objects")
    parser.add_argument("--keep-on-tie", action="store_true")
    parser.add_argument("--all-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    selected = SETTINGS if args.all_settings else ({"vote_unit": args.vote_unit,
                                                   "keep_on_tie": args.keep_on_tie},)
    with RacketLabeler() as live:
        episodes = [build_episode(args.seed, setting, demos=args.demos, queries=args.queries,
                    height=args.height, width=args.width, labeler=live) for setting in selected]
        report = write_batch(episodes, args.out)
        report.update({"status": "proposed", "racket_calls": live.calls,
                       "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "template_sha256": hashlib.sha256((HERE / "rule_template.rkt").read_bytes()).hexdigest()})
        (args.out / "summary.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
