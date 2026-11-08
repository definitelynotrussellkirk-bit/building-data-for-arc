"""Proposed, task-local left/right ray deflection. Racket supplies all labels.

This is separate from the fixed canonical generator and is not an accepted
parameter family or a training-admission receipt.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys

# Bind imports to this checkout, never a sibling/predecessor environment.
for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared/runtime"
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break

from reviewer_support import (canonical_path, find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "cd818a9d92d1"
VERSION = "direction-prototype-1"
DIRECTIONS = ("left", "right")
ROOT = find_root(__file__)
_LOADED_PROTOTYPE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
MAX_DEMOS = MAX_QUERIES = 8
MAX_ATTEMPTS = 4096


class SamplingLimitError(ValueError):
    """The requested distinct batch exceeds support or its explicit retry cap."""


def _integer(value, name, low=None, high=None):
    if type(value) is not int or (low is not None and value < low) or (
        high is not None and value > high
    ):
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _direction(value):
    if type(value) is not str or value not in DIRECTIONS:
        raise ValueError("bend_direction must be 'left' or 'right'")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    if not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30:
        raise ValueError("ARC grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _key(grid):
    _grid(grid)
    return tuple(tuple(row) for row in grid)


@lru_cache(maxsize=1)
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)


def source_identity():
    """Bind provenance to the bytes actually loaded in this process."""
    _, generator_source, generator_sha = _generator()
    prototype_source = Path(__file__).resolve()
    if (hashlib.sha256(generator_source.read_bytes()).hexdigest() != generator_sha
            or hashlib.sha256(prototype_source.read_bytes()).hexdigest() != _LOADED_PROTOTYPE_SHA256):
        raise ValueError("source changed after import; use a fresh process")
    return {
        str(generator_source.relative_to(ROOT)): generator_sha,
        str(prototype_source.relative_to(ROOT)): _LOADED_PROTOTYPE_SHA256,
    }


@lru_cache(maxsize=1)
def canonical_program():
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("Expected one unambiguous canonical Racket authority")
    return programs.pop()


def program(bend_direction="right"):
    """Materialize exact canonical default or its bounded leftward variant."""
    _direction(bend_direction)
    original = canonical_program()
    if bend_direction == "right":
        return original
    # Pin the two destination occurrences and their guard, fail on rule drift.
    if original.count("(+ c 1)") != 2 or original.count("(< (+ c 1) w)") != 1:
        raise ValueError("Canonical destination structure changed; review variant")
    return original.replace("(+ c 1)", "(- c 1)").replace(
        "(< (- c 1) w)", "(<= 0 (- c 1))"
    )


def validate_input(grid):
    """Common admitted grammar: both directions are total and preserve gray."""
    _grid(grid)
    generator, _, _ = _generator()
    errors = generator.self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = len(grid[0])
    if any(2 in row for row in grid[:-1]):
        raise ValueError("red markers belong only to the bottom guide row")
    markers = {c for c, value in enumerate(grid[-1]) if value == 2}
    if any(c == 0 or c == width - 1 for c in markers):
        raise ValueError("common-direction support requires interior marker columns")
    gray = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    on_columns = {c for _, c in gray if c in markers}
    destinations = {c + delta for c in on_columns for delta in (-1, 1)}
    if any(c in destinations for _, c in gray):
        raise ValueError("a gray cell occupies a left/right bend destination")


def predict_python(grid, bend_direction="right"):
    """Independent test mirror; never used to supply exported labels."""
    validate_input(grid)
    delta = -1 if _direction(bend_direction) == "left" else 1
    height = len(grid)
    out = [grid[-1][:] for _ in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 5:
                continue
            out[r][c] = 5
            if grid[-1][c] == 2:
                for rr in range(r):
                    out[rr][c] = 0
                for rr in range(min(height, r + 2)):
                    out[rr][c + delta] = 2
    return out


def _overrides(values):
    if values is None:
        return {}
    if type(values) is not dict:
        raise ValueError("input_overrides must be a dictionary")
    generator, _, _ = _generator()
    if set(values) - set(generator.AXES):
        raise ValueError("unknown input override")
    result = dict(values)
    for name, bounds in (("grid_h", (5, 16)), ("grid_w", (6, 18))):
        if name in result:
            _integer(result[name], name, *bounds)
    if "branch_profile" in result and (
        type(result["branch_profile"]) is not str
        or result["branch_profile"] not in generator.BRANCH_PROFILES
    ):
        raise ValueError("unknown branch_profile")
    return result


def input_capacity(input_overrides):
    """Exact finite support when both dimensions are fixed, otherwise unknown."""
    overrides = _overrides(input_overrides)
    if not {"grid_h", "grid_w"} <= set(overrides):
        return None
    height, width = overrides["grid_h"], overrides["grid_w"]
    generator, _, _ = _generator()
    profiles = ([overrides["branch_profile"]] if "branch_profile" in overrides
                else list(generator.BRANCH_PROFILES))
    capacity = 0
    for profile in profiles:
        counts = generator.BRANCH_PROFILES[profile]
        blockers = counts[1] + counts[2]
        if blockers > height - 3:
            continue
        supports = generator._joint_placements(width, counts)
        capacity += math.perm(height - 3, blockers) * sum(
            math.comb(len(off_candidates), counts[2])
            for _, _, off_candidates in supports
        )
    return capacity


def sample_inputs(input_seed, count, *, difficulty="medium",
                  input_overrides=None, max_attempts=256):
    _integer(input_seed, "input_seed")
    _integer(count, "count", 1, MAX_DEMOS + MAX_QUERIES)
    _integer(max_attempts, "max_attempts", 1, MAX_ATTEMPTS)
    if max_attempts < count:
        raise SamplingLimitError("attempt budget is smaller than the requested distinct count")
    overrides = _overrides(input_overrides)
    capacity = input_capacity(overrides)
    if capacity is not None and count > capacity:
        raise SamplingLimitError(f"requested {count} distinct inputs; fixed domain has support {capacity}")
    generator, _, _ = _generator()
    samples, seen = [], set()
    for index in range(max_attempts):
        grid = generator.generate(input_seed, index, difficulty=difficulty, **overrides)
        validate_input(grid)
        key = _key(grid)
        if key in seen:
            continue
        seen.add(key)
        samples.append(grid)
        if len(samples) == count:
            return samples
    raise SamplingLimitError(f"found {len(samples)}/{count} distinct inputs in {max_attempts} attempts")


class RacketOracle:
    """One real persistent bridge; no fallback to a Python label implementation."""

    def __init__(self):
        self.bridge = None
        self.functions = {}
        self.cache = {}
        self.evaluations = 0

    def __enter__(self):
        if self.bridge is not None:
            raise RuntimeError("RacketOracle is already open")
        self.bridge = RacketBridge(timeout=10.0)
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.bridge is not None:
            self.bridge.shutdown()
            self.bridge = None
        return False

    def predict(self, grid, program_text):
        if self.bridge is None:
            raise RuntimeError("use RacketOracle as a context manager")
        key = (_key(grid), program_text)
        if key not in self.cache:
            digest = hashlib.sha256(program_text.encode()).hexdigest()
            if digest not in self.functions:
                name = "direction_rule_" + digest
                self.bridge.eval_text(f"(define {name} {wrap_rule(program_text)})")
                self.functions[digest] = name
            self.bridge.define_grid("direction_input", grid)
            output = self.bridge.eval_text(f"({self.functions[digest]} direction_input)")
            _grid(output)
            if len(output) != len(grid) or len(output[0]) != len(grid[0]):
                raise ValueError("reference changed grid dimensions")
            self.cache[key] = copy.deepcopy(output)
            self.evaluations += 1
        return copy.deepcopy(self.cache[key])


def rival_programs():
    """Two lawful settings and seven explicit shortcut programs."""
    candidates = {"direction:" + direction: program(direction) for direction in DIRECTIONS}
    candidates["no_bend"] = (
        "(rule! (lambda (g) (cellmap g (r c v) "
        "(if (= v 5) 5 (at g (- (rows g) 1) c)))))"
    )
    for direction in DIRECTIONS:
        source = program(direction)
        candidates["all_gray:" + direction] = source.replace(
            "(= (at g (- h 1) c) 2)", "#t")
        candidates["short_bridge:" + direction] = source.replace("(+ r 2)", "(+ r 1)")
        candidates["keep_source_above:" + direction] = source.replace(
            "(if (< rr r) (set-cell gg rr c 0) gg)", "gg")
    return candidates


def _certificate(episode, oracle):
    if type(episode) is not dict:
        raise ValueError("episode must be a dictionary")
    settings = episode.get("settings")
    if type(settings) is not dict or set(settings) != {"bend_direction"}:
        raise ValueError("settings must contain only bend_direction")
    direction = _direction(settings["bend_direction"])
    if episode.get("program_solution") != program(direction):
        raise ValueError("program does not match the declared direction")
    if episode.get("program_sha256") != hashlib.sha256(program(direction).encode()).hexdigest():
        raise ValueError("program_sha256 does not bind the executed Racket rule")
    if episode.get("source_sha256") != source_identity():
        raise ValueError("source_sha256 does not bind the current prototype and generator")
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list:
        raise ValueError("train and test must be lists")
    _integer(len(train), "demos", 1, MAX_DEMOS)
    _integer(len(test), "queries", 1, MAX_QUERIES)
    keys = []
    for pair in train + test:
        if type(pair) is not dict or "input" not in pair or "output" not in pair:
            raise ValueError("each private pair needs input and output")
        validate_input(pair["input"])
        _grid(pair["output"])
        keys.append(_key(pair["input"]))
    if len(keys) != len(set(keys)):
        raise ValueError("demonstration and query inputs must all be distinct")

    # Fit using demonstrations ONLY, before reading any query output.
    candidates = rival_programs()
    survivors, witnesses = [], {}
    for name, source in candidates.items():
        mismatches = [index for index, pair in enumerate(train)
                      if oracle.predict(pair["input"], source) != pair["output"]]
        if not mismatches:
            survivors.append(name)
        else:
            witnesses[name] = mismatches[0]
    chosen = "direction:" + direction
    if chosen not in survivors:
        raise ValueError("a demonstration label differs from the chosen Racket rule")
    lawful_survivors = [name for name in survivors if name.startswith("direction:")]
    if lawful_survivors != [chosen]:
        raise ValueError("demonstrations do not identify the episode's direction")

    agreements = []
    for index, pair in enumerate(test):
        expected = oracle.predict(pair["input"], candidates[chosen])
        if expected != pair["output"]:
            raise ValueError(f"query {index} label differs from the chosen Racket rule")
        changed = [name for name in survivors
                   if oracle.predict(pair["input"], candidates[name]) != expected]
        if changed:
            raise ValueError(f"query {index} ambiguous under surviving rivals: {changed}")
        agreements.append({"query_index": index, "agreeing_survivors": survivors[:]})
    return {
        "schema": "cd818a9d92d1-direction-certificate-v1",
        "fitted_on": "demonstrations_only",
        "candidate_program_sha256": {name: hashlib.sha256(source.encode()).hexdigest()
                                     for name, source in candidates.items()},
        "survivors": survivors,
        "first_demo_rebuttals": witnesses,
        "query_agreement": agreements,
        "scope": "Only the two declared settings and seven named shortcuts; not arbitrary programs.",
    }


def certify_episode(episode, oracle=None):
    """Recompute a certificate and all labels; a saved certificate is never trusted."""
    if oracle is not None:
        return _certificate(episode, oracle)
    with RacketOracle() as runtime:
        return _certificate(episode, runtime)


def make_episode(seed, bend_direction=None, *, demos=2, queries=4, input_seed=None,
                 input_overrides=None, max_attempts=256, oracle=None):
    _integer(seed, "seed")
    _integer(demos, "demos", 1, MAX_DEMOS)
    _integer(queries, "queries", 1, MAX_QUERIES)
    _integer(max_attempts, "max_attempts", 1, MAX_ATTEMPTS)
    if bend_direction is None:
        bend_direction = DIRECTIONS[hashlib.sha256(str(seed).encode()).digest()[0] % 2]
    _direction(bend_direction)
    if input_seed is None:
        input_seed = seed
    inputs = sample_inputs(input_seed, demos + queries, input_overrides=input_overrides,
                           max_attempts=max_attempts)
    if oracle is None:
        with RacketOracle() as runtime:
            return make_episode(seed, bend_direction, demos=demos, queries=queries,
                                input_seed=input_seed, input_overrides=input_overrides,
                                max_attempts=max_attempts, oracle=runtime)
    rule = program(bend_direction)
    pairs = [{"input": grid, "output": oracle.predict(grid, rule)} for grid in inputs]
    episode = {
        "schema": "cd818a9d92d1-parametric-prototype-v1",
        "task_id": TASK_ID,
        "status": "proposed_prototype",
        "training_admitted": False,
        "settings": {"bend_direction": bend_direction},
        "seed": seed,
        "input_seed": input_seed,
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": rule,
        "program_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "source_sha256": source_identity(),
    }
    episode["certificate"] = certify_episode(episode, oracle)
    return episode


def write_batch(episodes, out, oracle=None):
    """Validate first, then publish exact visible bytes under content-only names."""
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    if oracle is None:
        with RacketOracle() as runtime:
            return write_batch(episodes, out, runtime)
    prepared, identities = [], set()
    for episode in episodes:
        certificate = certify_episode(episode, oracle)
        visible = public_challenge_bytes(episode)
        identity = public_challenge_id(episode)
        if identity in identities:
            raise ValueError("duplicate visible challenge")
        identities.add(identity)
        private = copy.deepcopy(episode)
        private["certificate"] = certificate
        private["public_id"] = identity
        prepared.append((identity, visible, private))
    prepared.sort(key=lambda item: item[0])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()  # refuses an output directory created during validation
    (out / "public").mkdir()
    for identity, visible, _ in prepared:
        (out / "public" / (identity + ".json")).write_bytes(visible)
    private_bytes = b"".join(
        (json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for _, _, private in prepared
    )
    (out / "private.jsonl").write_bytes(private_bytes)
    manifest = {
        "schema": "cd818a9d92d1-public-export-v1",
        "status": "proposed_prototype",
        "episode_count": len(prepared),
        "public": [{"id": identity, "path": "public/" + identity + ".json",
                    "sha256": hashlib.sha256(visible).hexdigest()}
                   for identity, visible, _ in prepared],
        "private_sha256": hashlib.sha256(private_bytes).hexdigest(),
        "reference_labels": sum(len(private["train"]) + len(private["test"])
                                for _, _, private in prepared),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def verify_export(out, oracle=None):
    """Replay an export through real Racket; reject rehashed forged query labels."""
    out = Path(out)
    if oracle is None:
        with RacketOracle() as runtime:
            return verify_export(out, runtime)
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest.get("schema") != "cd818a9d92d1-public-export-v1":
        raise ValueError("unknown export schema")
    private_bytes = (out / "private.jsonl").read_bytes()
    if hashlib.sha256(private_bytes).hexdigest() != manifest.get("private_sha256"):
        raise ValueError("private digest mismatch")
    episodes = [json.loads(line) for line in private_bytes.splitlines()]
    if not episodes or len(episodes) != manifest.get("episode_count"):
        raise ValueError("episode count mismatch")
    if type(manifest.get("public")) is not list or len(manifest["public"]) != len(episodes):
        raise ValueError("public manifest length mismatch")
    ids = []
    for episode, record in zip(episodes, manifest["public"]):
        identity = public_challenge_id(episode)
        path = "public/" + identity + ".json"
        if record != {"id": identity, "path": path, "sha256": identity}:
            raise ValueError("public identity/path mismatch")
        visible_path = out / path
        if visible_path.is_symlink() or visible_path.read_bytes() != public_challenge_bytes(episode):
            raise ValueError("public visible bytes mismatch")
        if episode.get("public_id") != identity:
            raise ValueError("private public_id mismatch")
        certificate = certify_episode(episode, oracle)
        if certificate != episode.get("certificate"):
            raise ValueError("stored certificate is stale or forged")
        ids.append(identity)
    if ids != sorted(set(ids)):
        raise ValueError("public IDs are duplicated or out of order")
    if {path.name for path in (out / "public").iterdir()} != {identity + ".json" for identity in ids}:
        raise ValueError("unexpected public files")
    labels = sum(len(ep["train"]) + len(ep["test"]) for ep in episodes)
    if labels != manifest.get("reference_labels"):
        raise ValueError("label count mismatch")
    return {"status": "passed", "episodes": len(episodes), "labels_replayed": labels,
            "program_count": len({ep["program_sha256"] for ep in episodes}),
            "scope": "Actual Racket labels, demo-only rivals and exact visible-byte projection."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build", help="write paired direction episodes")
    build.add_argument("--seeds", type=int, nargs="+", default=[17, 29])
    build.add_argument("--directions", choices=DIRECTIONS, nargs="+", default=list(DIRECTIONS))
    build.add_argument("--demos", type=int, default=2)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--max-attempts", type=int, default=256)
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify", help="independently replay a previously written batch")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    with RacketOracle() as oracle:
        if args.action == "build":
            episodes = [
                make_episode(seed, direction, demos=args.demos, queries=args.queries,
                             input_seed=seed, max_attempts=args.max_attempts, oracle=oracle)
                for seed in args.seeds for direction in args.directions
            ]
            result = write_batch(episodes, args.out, oracle)
            result["racket_evaluations"] = oracle.evaluations
        else:
            result = verify_export(args.out, oracle)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
