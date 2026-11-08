"""Proposed, unregistered parametric episodes for d377a54f20c6.

Labels and finite-rival predictions are executed by the bundled RacketBridge.
No Python output mirror is used. The selected canonical generator is independent.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import copy
from dataclasses import dataclass
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
# Resolve only this checkout's existing runtime, never a sibling environment.
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper

VERSION = "0.1.0-prototype"
TASK_ID = "d377a54f20c6"


@dataclass(frozen=True)
class Parameters:
    center_extension: bool = True
    stroke_width: int = 1

    def __post_init__(self):
        if type(self.center_extension) is not bool:
            raise ValueError("center_extension must be a boolean")
        if type(self.stroke_width) is not int or self.stroke_width not in (1, 2):
            raise ValueError("stroke_width must be 1 or 2")

    def as_dict(self):
        return {"center_extension": self.center_extension, "stroke_width": self.stroke_width}


DEFAULT = Parameters()
ALL_SETTINGS = tuple(Parameters(extension, width) for extension in (False, True) for width in (1, 2))
_RULE_FILES = {
    Parameters(True, 1): "canonical.rkt",
    Parameters(False, 1): "diagonals_only.rkt",
    Parameters(True, 2): "wide_with_center.rkt",
    Parameters(False, 2): "wide_diagonals_only.rkt",
}


def rule_source(parameters=DEFAULT):
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be Parameters")
    return (HERE / "rules" / _RULE_FILES[parameters]).read_text()


def _arc_grid(grid):
    if not isinstance(grid, list) or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    if any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer colors 0..9")


def validate_input(grid):
    """Validate the original family's bounded rectangular-object domain."""
    _arc_grid(grid)
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    if not unseen or len(unseen) == height * width:
        raise ValueError("expected nonzero objects and zero background")
    count = 0
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue, cells = deque([start]), []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        rs, cs = zip(*cells)
        h, w = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        frequencies = Counter(grid[r][c] for r, c in cells)
        if min(h, w) < 5 or len(cells) != h * w:
            raise ValueError("each object must fill a rectangle at least 5 by 5")
        if len(frequencies) != 2 or len(set(frequencies.values())) != 2:
            raise ValueError("each object needs exactly two colors and a unique majority")
        count += 1
    if count > 3:
        raise ValueError("at most three objects are supported")


def apply_rule(bridge, grids, parameters=DEFAULT):
    """Execute exact explicit-lambda Racket sources on a batch of inputs."""
    grids = list(grids)
    for grid in grids:
        validate_input(grid)
    # All four checked-in sources are explicit lambdas with local h/w bindings,
    # not shorthand DSL bodies. Use the shared wrapper-stripper, not a parser copy.
    body = strip_rule_wrapper(rule_source(parameters))
    literals = ["'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")" for grid in grids]
    expression = "(let ([f " + body + "]) (list " + " ".join("(f " + grid + ")" for grid in literals) + "))"
    outputs = bridge.eval_text(expression)
    if not isinstance(outputs, list) or len(outputs) != len(grids):
        raise RuntimeError("Racket returned an unexpected batch size")
    for grid, output in zip(grids, outputs):
        _arc_grid(output)
        if (len(grid), len(grid[0])) != (len(output), len(output[0])):
            raise RuntimeError("Racket changed the canvas dimensions")
    return outputs


def infer_settings(bridge, demonstrations):
    """Filter the finite hypothesis family using demonstrations only."""
    if not demonstrations:
        raise ValueError("at least one demonstration is required")
    inputs = [pair["input"] for pair in demonstrations]
    labels = [pair["output"] for pair in demonstrations]
    return [parameters for parameters in ALL_SETTINGS if apply_rule(bridge, inputs, parameters) == labels]


def _scene(rng, role, index):
    category = index % (3 if role == "demo" else 4)
    if role == "demo":
        if category == 0:
            short = rng.choice((7, 8))
            dimensions = [(short, short + rng.randint(7, 9))]
        elif category == 1:
            dimensions = [(rng.randint(14, 17), rng.choice((7, 8)))]
        else:
            dimensions = [(7, rng.choice((7, 8))), (rng.choice((7, 8)), rng.choice((11, 12)))]
    elif category == 0:
        dimensions = [(rng.randint(8, 10), rng.randint(21, 26))]
    elif category == 1:
        dimensions = [(rng.randint(21, 26), rng.randint(8, 10))]
    elif category == 2:
        dimensions = [(rng.choice((10, 11)), rng.choice((8, 9))), (rng.choice((8, 9)), rng.choice((14, 15)))]
    else:
        dimensions = [(26, 26)]
    top, bottom, left, right = [rng.randint(1, 2) for _ in range(4)]
    if role == "query" and category == 3:
        top, left = rng.randint(1, 3), rng.randint(1, 3)
        bottom, right = 4 - top, 4 - left
    gap = rng.randint(1, 2)
    content_h = max(h for h, _ in dimensions)
    content_w = sum(w for _, w in dimensions) + gap * (len(dimensions) - 1)
    grid = [[0] * (content_w + left + right) for _ in range(content_h + top + bottom)]
    palette = rng.sample(range(1, 10), 3)
    cursor = left
    for object_index, (height, width) in enumerate(dimensions):
        major, minor = palette[object_index], palette[object_index + 1]
        r1, c1 = top + rng.randint(0, content_h - height), cursor
        cursor += width + gap
        for r in range(r1, r1 + height):
            grid[r][c1:c1 + width] = [major] * width
        candidates = [(r, c) for r in range(r1, r1 + height) for c in range(c1, c1 + width)]
        for r, c in rng.sample(candidates, rng.randint(1, 3)):
            grid[r][c] = minor
    validate_input(grid)
    return grid


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _source_hashes():
    paths = [HERE / "episode.py"] + sorted((HERE / "rules").glob("*.rkt"))
    return {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def generate_episode(seed, *, demo_count=3, query_count=4, parameters=DEFAULT, bridge=None):
    """Canonical by default; parameters=None samples one seed-fixed setting."""
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    for name, count in (("demo_count", demo_count), ("query_count", query_count)):
        if type(count) is not int or not 1 <= count <= 16:
            raise ValueError(f"{name} must be an integer in 1..16")
    if parameters is None:
        parameters = random.Random(f"{VERSION}:parameters:{seed}").choice(ALL_SETTINGS)
    if not isinstance(parameters, Parameters):
        raise ValueError("parameters must be Parameters or None")
    if bridge is None:
        with RacketBridge() as owned_bridge:
            return generate_episode(seed, demo_count=demo_count, query_count=query_count, parameters=parameters, bridge=owned_bridge)
    rng = random.Random(f"{VERSION}:inputs:{seed}")
    inputs, seen = [], set()
    for role, count in (("demo", demo_count), ("query", query_count)):
        for index in range(count):
            for _ in range(64):
                grid = _scene(rng, role, index)
                key = _json_bytes(grid)
                if key not in seen:
                    seen.add(key)
                    inputs.append(grid)
                    break
            else:
                raise RuntimeError("distinct-input sampling budget exhausted; no episode returned")
    predictions = {candidate: apply_rule(bridge, inputs, candidate) for candidate in ALL_SETTINGS}
    selected = predictions[parameters]
    # Do not inspect query outputs while filtering hypotheses.
    labels = selected[:demo_count]
    survivors = [candidate for candidate in ALL_SETTINGS if predictions[candidate][:demo_count] == labels]
    if survivors != [parameters]:
        raise RuntimeError("demonstrations did not identify the chosen parameter setting")
    eliminations = []
    for rival in ALL_SETTINGS:
        if rival != parameters:
            witness = next(i for i in range(demo_count) if predictions[rival][i] != labels[i])
            eliminations.append({"parameters": rival.as_dict(), "demonstration_index": witness})
    queries = []
    for index in range(query_count):
        absolute = demo_count + index
        identified = all(predictions[candidate][absolute] == selected[absolute] for candidate in survivors)
        if not identified:
            raise RuntimeError("surviving demo-consistent rules disagree on a query")
        queries.append({"query_index": index, "identified_from_demonstrations": identified,
                        "surviving_rule_count": len(survivors)})
    source = rule_source(parameters)
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, selected)]
    return {
        "schema": "d377a54f20c6-parametric-prototype-v1", "status": "proposed_prototype",
        "task_id": TASK_ID, "version": VERSION, "seed": seed, "parameters": parameters.as_dict(),
        "canonical_parameters": DEFAULT.as_dict(), "train": pairs[:demo_count], "test": pairs[demo_count:],
        "reference": {"source": source, "sha256": hashlib.sha256(source.encode()).hexdigest(),
                      "normalized_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]},
        "source_hashes": _source_hashes(),
        "identifiability": {"hypothesis_count": len(ALL_SETTINGS), "evidence_used": "demonstrations_only",
                            "survivors": [candidate.as_dict() for candidate in survivors],
                            "eliminations": eliminations, "queries": queries},
        "racket_execution": {"batch_calls": len(ALL_SETTINGS), "pair_executions": len(ALL_SETTINGS) * len(inputs)},
        "limitations": ["Finite four-setting rival family only; not exhaustive rule identification.",
                        "One or two generated objects; validator and canonical rule permit up to three.",
                        "Proposed extension, not production registration, approval, or training admission."]
    }


def public_challenge(episode):
    return {"train": copy.deepcopy(episode["train"]),
            "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]]}


def public_identifier(episode):
    return "challenge_" + hashlib.sha256(_json_bytes(public_challenge(episode))).hexdigest()[:24]


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def write_episode(episode, destination):
    destination = Path(destination)
    name = public_identifier(episode) + ".json"
    _write_json(destination / "public" / name, public_challenge(episode))
    _write_json(destination / "private" / name, episode)
    return {"public": "public/" + name, "private": "private/" + name,
            "parameters": episode["parameters"], "rule_sha256": episode["reference"]["sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--all-settings", action="store_true")
    mode.add_argument("--sample-parameters", action="store_true")
    parser.add_argument("--center-extension", choices=("on", "off"), default=None)
    parser.add_argument("--stroke-width", type=int, choices=(1, 2), default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
        parser.error("--out must name a new or empty directory; existing exports are preserved")
    explicit = args.center_extension is not None or args.stroke_width is not None
    if explicit and (args.all_settings or args.sample_parameters):
        parser.error("explicit parameters cannot be combined with --all-settings or --sample-parameters")
    settings = ALL_SETTINGS if args.all_settings else [None if args.sample_parameters else Parameters(
        args.center_extension != "off", args.stroke_width or 1)]
    try:
        with RacketBridge() as bridge:
            episodes = [generate_episode(args.seed, demo_count=args.demos, query_count=args.queries,
                                         parameters=parameters, bridge=bridge) for parameters in settings]
        rows = [write_episode(episode, args.out) for episode in episodes]
        manifest = {"status": "proposed_prototype", "command": [sys.executable, str(Path(__file__)), *(sys.argv[1:] if argv is None else argv)],
                    "seed": args.seed, "episode_count": len(rows), "demo_count": args.demos, "query_count": args.queries,
                    "episodes": rows, "source_hashes": _source_hashes()}
        _write_json(args.out / "private/manifest.json", manifest)
        if args.all_settings:
            # The same seed gives identical inputs across settings, so this is a
            # lawful contrast witness without changing geometry or marker roles.
            first = episodes[0]["train"][0]["input"]
            if not all(episode["train"][0]["input"] == first for episode in episodes):
                raise RuntimeError("contrast witness inputs drifted across settings")
            contrasts = []
            for left, right in itertools.combinations(episodes, 2):
                difference = sum(a != b for row_a, row_b in zip(left["train"][0]["output"], right["train"][0]["output"]) for a, b in zip(row_a, row_b))
                if not difference:
                    raise RuntimeError("contrast witness failed to distinguish settings")
                contrasts.append({"left": left["parameters"], "right": right["parameters"], "different_cells": difference})
            _write_json(args.out / "private/witness.json", {"input": first,
                "outputs": [{"parameters": episode["parameters"], "output": episode["train"][0]["output"],
                             "rule_sha256": episode["reference"]["sha256"]} for episode in episodes],
                "pairwise_differences": contrasts})
        print(json.dumps({"status": "proposed_prototype", "episode_count": len(rows),
                          "manifest": str(args.out / "private/manifest.json")}, sort_keys=True))
        return 0
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
