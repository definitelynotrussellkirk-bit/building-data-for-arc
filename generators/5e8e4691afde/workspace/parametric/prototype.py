"""Proposed, task-local rotation/scale extension of training:2b9ef948.

The canonical production generator and reference rule are not modified. All
exported labels and demonstration rival comparisons execute matching Racket.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RUNTIME = ROOT / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "5e8e4691afde"
PARENT_FAMILY = "training:2b9ef948"
VERSION = "proposed-rotation-scale-v1"
CANONICAL_PROGRAM_SHA256 = "ae926b19ad08aa049ff2ef63cb8f0ea0f43d56185cdc6429d7b581ba405687d8"
SHORT_SHIFTS = ((3, 0), (-3, 0), (0, 3), (0, -3),
                (3, 3), (3, -3), (-3, 3), (-3, -3))
LONG_SHIFTS = ((5, 2), (-2, 5), (4, -2))
COLORS = (1, 2, 3, 6, 7, 8, 9)
LIMITATIONS = [
    "Proposed task-local extension; no production API, approval, or training admission is changed.",
    "Identifiability is finite: the declared eight rotation/scale hypotheses, not all possible ARC rules.",
    "Sampled paths are straight or have one Manhattan bend; canonical winding paths are covered only by the five default-setting fixtures.",
    "Sampled demonstrations have 16..20 rows/columns; queries have 21..30, with the first query exactly 30x30.",
    "All eight transformed frames must fit each sampled input; this is a deliberately restricted common domain.",
    "Each episode has an explicit finite draw budget and fails without a partial export if it cannot satisfy its counts.",
]


def exact_int(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


@dataclass(frozen=True, order=True)
class Setting:
    quarter_turns: int = 0
    distance_scale: int = 1

    def __post_init__(self):
        exact_int("quarter_turns", self.quarter_turns, 0, 3)
        exact_int("distance_scale", self.distance_scale, 1, 2)

    def as_dict(self):
        return {"quarter_turns": self.quarter_turns, "distance_scale": self.distance_scale}


DEFAULT = Setting()
SETTINGS = tuple(Setting(turns, scale) for turns in range(4) for scale in (1, 2))
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def grid_id(grid):
    return digest(json_bytes(grid))


def canonical_row():
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    matches = [row for line in path.read_text(encoding="utf-8").splitlines()
               if line.strip() and (row := json.loads(line)).get("task_id") == TASK_ID]
    if len(matches) != 1:
        raise ValueError("the selected canonical row must be unambiguous")
    row = matches[0]
    if digest(row["program_solution"].encode()) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical program changed; review this prototype before rebasing")
    return row


def program_for(setting=DEFAULT):
    if not isinstance(setting, Setting):
        raise ValueError("setting must be a validated Setting")
    program = canonical_row()["program_solution"]
    if setting == DEFAULT:
        return program  # Exact canonical text, not a reimplementation.
    old = ("(define nr (+ sr (- (first extra4) (first indicator))))\n"
           "             (define nc (+ sc (- (second extra4) (second indicator))))")
    row_expr, col_expr = (
        ("dr", "dc"), ("dc", "(- dr)"),
        ("(- dr)", "(- dc)"), ("(- dc)", "dr"),
    )[setting.quarter_turns]
    replacement = (
        "(define dr (- (first extra4) (first indicator)))\n"
        "             (define dc (- (second extra4) (second indicator)))\n"
        f"             (define nr (+ sr (* {setting.distance_scale} {row_expr})))\n"
        f"             (define nc (+ sc (* {setting.distance_scale} {col_expr})))"
    )
    if program.count(old) != 1:
        raise ValueError("canonical displacement definitions no longer match the reviewed patch point")
    return program.replace(old, replacement)


def transformed_shift(shift, setting):
    dr, dc = shift
    for _ in range(setting.quarter_turns):
        dr, dc = dc, -dr  # Clockwise on a grid: down becomes left.
    return setting.distance_scale * dr, setting.distance_scale * dc


def validate_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be in 1..30")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be in 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return len(grid), width


def scene_info(grid):
    h, w = validate_grid(grid)
    centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)
               if grid[r][c] in COLORS and
               all(grid[r + dr][c + dc] == 4 for dr in (-1, 0, 1)
                   for dc in (-1, 0, 1) if (dr, dc) != (0, 0))]
    if len(centers) != 1:
        raise ValueError("exactly one colored 3x3 frame center is required")
    sr, sc = centers[0]
    color = grid[sr][sc]
    colored = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    if len(colored) != 2:
        raise ValueError("the frame color must occur once more as the indicator")
    indicator = next(iter(colored - {(sr, sc)}))
    frame = {(r, c) for r in range(sr - 1, sr + 2) for c in range(sc - 1, sc + 2)}
    extras = {(r, c) for r in range(h) for c in range(w)
              if grid[r][c] == 4 and (r, c) not in frame}
    if len(extras) != 1:
        raise ValueError("exactly one extra color-4 endpoint is required")
    endpoint = next(iter(extras))
    gray = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    if not gray or {v for row in grid for v in row} - {0, 4, 5, color}:
        raise ValueError("a gray path and only the four role colors are required")
    path = gray | {indicator, endpoint}
    seen, todo = {indicator}, [indicator]
    while todo:
        r, c = todo.pop()
        neighbors = {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)} & path
        expected = 1 if (r, c) in (indicator, endpoint) else 2
        if len(neighbors) != expected:
            raise ValueError("the gray path must be simple, with the two marked endpoints")
        for neighbor in neighbors - seen:
            seen.add(neighbor)
            todo.append(neighbor)
    if seen != path:
        raise ValueError("the path must be connected")
    return {"height": h, "width": w, "center": (sr, sc), "color": color,
            "indicator": indicator, "endpoint": endpoint,
            "displacement": (endpoint[0] - indicator[0], endpoint[1] - indicator[1])}


def target_center(info, setting):
    dr, dc = transformed_shift(info["displacement"], setting)
    nr, nc = info["center"][0] + dr, info["center"][1] + dc
    if not (1 <= nr < info["height"] - 1 and 1 <= nc < info["width"] - 1):
        raise ValueError("transformed displacement would clip the relocated frame")
    return nr, nc


def mirror(grid, setting=DEFAULT):
    info = scene_info(grid)
    nr, nc = target_center(info, setting)
    color = info["color"]
    return [[color if (r, c) == (nr, nc) else
             4 if (abs(r - nr) <= 1 and abs(c - nc) <= 1) or
             r - c == nr - nc or r + c == nr + nc else color
             for c in range(info["width"])] for r in range(info["height"])]


def seeded_rng(seed, episode_index, purpose):
    exact_int("seed", seed, 0, 2**63 - 1)
    exact_int("episode_index", episode_index, 0, 2**31 - 1)
    return random.Random(digest(f"{VERSION}:{seed}:{episode_index}:{purpose}".encode()))


def sampled_setting(seed, episode_index=0):
    return seeded_rng(seed, episode_index, "setting").choice(SETTINGS)


def _path(start, endpoint, horizontal_first):
    r, c = start
    er, ec = endpoint
    cells = [start]
    for axis in ((1, 0) if horizontal_first else (0, 1)):
        while (c != ec if axis == 1 else r != er):
            if axis == 1:
                c += 1 if ec > c else -1
            else:
                r += 1 if er > r else -1
            cells.append((r, c))
    return cells


def _draw_scene(rng, *, query_index=None):
    if query_index is None:
        h, w = rng.randint(16, 20), rng.randint(16, 20)
        shifts = SHORT_SHIFTS
    elif query_index % 4 == 0:
        h, w = 30, 30
        shifts = LONG_SHIFTS
    else:
        h, w = rng.randint(21, 29), rng.randint(21, 29)
        shifts = SHORT_SHIFTS + LONG_SHIFTS
    dr, dc = rng.choice(shifts)
    radius = 2 * max(abs(dr), abs(dc))
    if min(h, w) < 2 * radius + 3:
        return None
    sr = rng.randint(radius + 1, h - radius - 2)
    sc = rng.randint(radius + 1, w - radius - 2)
    centers = {(sr, sc)} | {(sr + rr, sc + cc) for setting in SETTINGS
                           for rr, cc in [transformed_shift((dr, dc), setting)]}
    footprints = {(r + rr, c + cc) for r, c in centers
                  for rr in (-1, 0, 1) for cc in (-1, 0, 1)}
    indicator = rng.randrange(h), rng.randrange(w)
    endpoint = indicator[0] + dr, indicator[1] + dc
    if not (0 <= endpoint[0] < h and 0 <= endpoint[1] < w):
        return None
    path = _path(indicator, endpoint, bool(rng.randrange(2)))
    if len(path) < 3 or not set(path).isdisjoint(footprints):
        return None
    color = rng.choice(COLORS)
    grid = [[0] * w for _ in range(h)]
    for r in range(sr - 1, sr + 2):
        for c in range(sc - 1, sc + 2):
            grid[r][c] = color if (r, c) == (sr, sc) else 4
    for r, c in path[1:-1]:
        grid[r][c] = 5
    grid[indicator[0]][indicator[1]] = color
    grid[endpoint[0]][endpoint[1]] = 4
    return grid


class SamplingError(RuntimeError):
    pass


def sample_inputs(seed, episode_index=0, *, demos=3, queries=4, max_attempts=4096):
    exact_int("demos", demos, 1, 32)
    exact_int("queries", queries, 1, 32)
    exact_int("max_attempts", max_attempts, 1, 100000)
    rng = seeded_rng(seed, episode_index, "layout")
    inputs, accepted, seen = [], [], set()
    attempts = 0
    while len(inputs) < demos + queries and attempts < max_attempts:
        attempts += 1
        index = len(inputs)
        grid = _draw_scene(rng, query_index=None if index < demos else index - demos)
        if grid is None or grid_id(grid) in seen:
            continue
        info = scene_info(grid)
        # The same visible-input domain applies to all eight settings.
        for setting in SETTINGS:
            target_center(info, setting)
        if index == 0 and len({grid_id(mirror(grid, s)) for s in SETTINGS}) != len(SETTINGS):
            continue
        seen.add(grid_id(grid))
        inputs.append(grid)
        accepted.append(attempts)
    if len(inputs) != demos + queries:
        raise SamplingError(f"accepted {len(inputs)}/{demos + queries} inputs after {attempts}/{max_attempts} attempts")
    return inputs[:demos], inputs[demos:], {
        "attempts": attempts, "max_attempts": max_attempts,
        "rejections": attempts - len(inputs), "accepted_attempts": accepted,
        "input_sha256": [grid_id(grid) for grid in inputs],
        "dimensions": [[len(grid), len(grid[0])] for grid in inputs],
    }


def fit_candidates(demonstrations):
    """Fit only demonstration pairs. No query argument or query labels exist here."""
    if type(demonstrations) is not list or not demonstrations:
        raise ValueError("at least one demonstration is required")
    return tuple(setting for setting in SETTINGS
                 if all(mirror(pair["input"], setting) == pair["output"] for pair in demonstrations))


def _racket_list(value):
    if type(value) is int:
        return str(value)
    return "(" + " ".join(_racket_list(item) for item in value) + ")"


class RacketLabeler:
    """Batch the real protected bridge; cache only exact program/input byte pairs."""
    def __init__(self, *, timeout=30.0, startup_timeout=60.0):
        self.bridge = RacketBridge(timeout=timeout, startup_timeout=startup_timeout)
        self.cache = {}
        self.evaluated_pairs = 0
        self.evaluation_batches = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.bridge.shutdown()

    def outputs(self, program, grids):
        if not program.startswith("(rule! ") or not program.endswith(")"):
            raise ValueError("expected the selected outer rule! wrapper")
        body = program[len("(rule! "):-1]
        program_hash = digest(program.encode())
        unique = {}
        for grid in grids:
            validate_grid(grid)
            key = program_hash, grid_id(grid)
            if key not in self.cache:
                unique[key] = grid
        missing = list(unique.items())
        for start in range(0, len(missing), 32):
            batch = missing[start:start + 32]
            expression = f"(map {body} '{_racket_list([grid for _, grid in batch])})"
            outputs = self.bridge.eval_text(expression)
            if type(outputs) is not list or len(outputs) != len(batch):
                raise ValueError("Racket did not return the requested number of outputs")
            for (key, grid), output in zip(batch, outputs):
                if validate_grid(output) != validate_grid(grid):
                    raise ValueError("Racket changed a grid's dimensions")
                self.cache[key] = output
            self.evaluated_pairs += len(batch)
            self.evaluation_batches += 1
        # Independent nested lists prevent a caller mutating the execution cache.
        return [[row[:] for row in self.cache[(program_hash, grid_id(grid))]] for grid in grids]


def certify(labeler, demonstrations, query_inputs):
    """Check rivals against demos first, then predict each query under survivors."""
    demo_inputs = [pair["input"] for pair in demonstrations]
    actual_survivors = []
    elimination = []
    for setting in SETTINGS:
        predictions = labeler.outputs(program_for(setting), demo_inputs)
        mismatches = [index for index, (pair, predicted) in enumerate(zip(demonstrations, predictions))
                      if pair["output"] != predicted]
        elimination.append({"setting": setting.as_dict(), "mismatching_demonstrations": mismatches})
        if not mismatches:
            actual_survivors.append(setting)
    survivors = tuple(actual_survivors)
    if survivors != fit_candidates(demonstrations):
        raise ValueError("Python candidate filtering disagrees with Racket")
    if len(survivors) != 1:
        raise ValueError(f"demonstrations leave {len(survivors)} of eight settings; redraw or add demonstrations")
    predictions = [labeler.outputs(program_for(setting), query_inputs) for setting in survivors]
    checks = []
    for index, grid in enumerate(query_inputs):
        possibilities = {grid_id(outputs[index]) for outputs in predictions}
        if len(possibilities) != 1:
            raise ValueError(f"query {index} is not identified by the demonstrations")
        checks.append({"input_sha256": grid_id(grid), "surviving_prediction_count": len(possibilities),
                       "prediction_sha256": next(iter(possibilities))})
    return survivors, predictions[0], {
        "candidate_count": len(SETTINGS),
        "fit_uses": "demonstration_inputs_and_outputs_only",
        "rival_execution": "all eight matching Racket programs on demonstration inputs",
        "survivors": [s.as_dict() for s in survivors],
        "eliminations": elimination, "queries": checks,
    }


def source_hashes():
    files = (HERE / "prototype.py", HERE / "README.md",
             ROOT / f"generators/{TASK_ID}/tests/test_parametric.py",
             ROOT / f"generators/{TASK_ID}/generator.py",
             ROOT / "shared/runtime/reviewer_support.py",
             ROOT / "shared/runtime/arc_repl/racket_bridge.py",
             ROOT / "shared/data/canonical/puzzles.jsonl")
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in files}


def generate_episode(seed, setting=DEFAULT, demos=3, queries=QUERY_COUNT):
    """Return one deterministic native-adapter episode using Python label claims.

    Protected qualification independently executes every declared Racket program
    against these inputs and labels; this helper deliberately does not start a
    runtime bridge.
    """
    exact_int("seed", seed, 0, 2**63 - 1)
    if not isinstance(setting, Setting):
        raise ValueError("setting must be a validated Setting")
    exact_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    exact_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    demo_inputs, query_inputs, _ = sample_inputs(
        seed, 0, demos=demos, queries=queries, max_attempts=4096)
    train = [{"input": grid, "output": mirror(grid, setting)} for grid in demo_inputs]
    if fit_candidates(train) != (setting,):
        raise ValueError("demonstrations do not identify the selected setting")
    test = [{"input": grid, "output": mirror(grid, setting)} for grid in query_inputs]
    return {"train": train, "test": test, "program_solution": program_for(setting)}


def make_episode(labeler, seed, episode_index=0, *, setting=DEFAULT,
                 demos=3, queries=4, max_attempts=4096):
    if not isinstance(setting, Setting):
        raise ValueError("setting must be a validated Setting")
    demo_inputs, query_inputs, sampling = sample_inputs(
        seed, episode_index, demos=demos, queries=queries, max_attempts=max_attempts)
    program = program_for(setting)
    demo_outputs = labeler.outputs(program, demo_inputs)
    train = [{"input": inp, "output": out} for inp, out in zip(demo_inputs, demo_outputs)]
    survivors, query_outputs, certificate = certify(labeler, train, query_inputs)
    if survivors != (setting,):
        raise ValueError("the selected fixed setting was not identified")
    test = [{"input": inp, "output": out} for inp, out in zip(query_inputs, query_outputs)]
    for pair in train + test:
        if mirror(pair["input"], setting) != pair["output"]:
            raise ValueError("Python geometry mirror disagrees with a Racket label")
    return {
        "schema": "arc-5e8e4691afde-parametric-prototype-v1", "status": "proposed",
        "task_id": TASK_ID, "parent_family": PARENT_FAMILY, "version": VERSION,
        "seed": seed, "episode_index": episode_index, "settings": setting.as_dict(),
        "program": program, "program_sha256": digest(program.encode()),
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "train": train, "test": test, "sampling": sampling,
        "identifiability": certificate, "source_sha256": source_hashes(),
    }


def difference_witness(labeler, grid):
    settings = (DEFAULT, Setting(1, 2))
    predictions = [labeler.outputs(program_for(setting), [grid])[0] for setting in settings]
    if predictions[0] == predictions[1]:
        raise ValueError("the proposed settings need a lawful difference witness")
    info = scene_info(grid)
    return {"input": grid, "input_sha256": grid_id(grid),
            "original_center": info["center"], "indicator": info["indicator"],
            "endpoint": info["endpoint"], "displacement": info["displacement"],
            "label_source": "actual matching Racket execution",
            "settings": [{"setting": setting.as_dict(), "output": output,
                          "target_center": target_center(info, setting),
                          "program_sha256": digest(program_for(setting).encode())}
                         for setting, output in zip(settings, predictions)],
            "different": True}


def verify_canonical_default(labeler):
    row = canonical_row()
    pairs = [(split, index, pair) for split in ("train", "test")
             for index, pair in enumerate(row[split])]
    outputs = labeler.outputs(program_for(), [pair["input"] for _, _, pair in pairs])
    checks = []
    for (split, index, pair), output in zip(pairs, outputs):
        if output != pair["output"]:
            raise ValueError(f"default Racket changed canonical {split} pair {index}")
        checks.append({"split": split, "pair_index": index,
                       "input_sha256": grid_id(pair["input"]),
                       "output_sha256": grid_id(output), "status": "pass"})
    return checks


def public_rows(episodes):
    rows, seen = [], set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if identifier in seen:
            raise ValueError("duplicate visible payload; private metadata cannot distinguish public challenges")
        seen.add(identifier)
        rows.append((identifier, payload, episode))
    if not rows:
        raise ValueError("at least one episode is required")
    return sorted(rows, key=lambda row: row[0])


def write_export(destination, episodes, *, witness, runtime_identity, command,
                 execution_summary=None, canonical_checks=None):
    rows = public_rows(episodes)  # Validate and reject duplicates before creating any files.
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("output directory must be new")
    programs = {digest(program_for(s).encode()): program_for(s) for s in SETTINGS}
    destination.mkdir(parents=True)
    public = destination / "public"
    private = destination / "private"
    public.mkdir()
    (private / "episodes").mkdir(parents=True)
    (private / "programs").mkdir()
    for identifier, payload, episode in rows:
        (public / f"{identifier}.json").write_bytes(payload)
        (private / "episodes" / f"{identifier}.json").write_text(
            json.dumps(episode, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for program_hash, program in sorted(programs.items()):
        (private / "programs" / f"{program_hash}.rkt").write_bytes(program.encode())
    (private / "difference_witness.json").write_text(
        json.dumps(witness, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema": "arc-parametric-private-export-v1", "status": "proposed",
        "task_id": TASK_ID, "parent_family": PARENT_FAMILY, "command": command,
        "public_identifier_status": "visible_payload_sha256",
        "public_projection": "reviewer_support.public_challenge_bytes/public_challenge_id",
        "public_ids": [identifier for identifier, _, _ in rows],
        "episodes": [{"public_id": identifier, "seed": ep["seed"],
                      "episode_index": ep["episode_index"], "settings": ep["settings"],
                      "demos": len(ep["train"]), "queries": len(ep["test"]),
                      "program_sha256": ep["program_sha256"]}
                     for identifier, _, ep in rows],
        "programs": [{"settings": s.as_dict(), "sha256": digest(program_for(s).encode())}
                     for s in SETTINGS],
        "runtime_identity": runtime_identity, "source_sha256": source_hashes(),
        "execution_summary": execution_summary,
        "canonical_default_checks": canonical_checks,
        "limitations": LIMITATIONS,
    }
    (private / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--count", type=int, default=1, help="episodes per selected setting")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=4096)
    parser.add_argument("--quarter-turns", type=int)
    parser.add_argument("--distance-scale", type=int)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--all-settings", action="store_true")
    mode.add_argument("--sample-settings", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        exact_int("seed", args.seed, 0, 2**63 - 1)
        exact_int("count", args.count, 1, 16)
        exact_int("demos", args.demos, 1, 32)
        exact_int("queries", args.queries, 1, 32)
        exact_int("max_attempts", args.max_attempts, 1, 100000)
        if (args.all_settings or args.sample_settings) and (args.quarter_turns is not None or args.distance_scale is not None):
            raise ValueError("explicit settings cannot be combined with --all-settings or --sample-settings")
        selected = Setting(0 if args.quarter_turns is None else args.quarter_turns,
                           1 if args.distance_scale is None else args.distance_scale)
        if args.out.exists():
            raise ValueError("output directory must be new")
    except ValueError as exc:
        parser.error(str(exc))
    episodes = []
    with RacketLabeler() as labeler:
        for index in range(args.count):
            settings = SETTINGS if args.all_settings else (
                (sampled_setting(args.seed, index),) if args.sample_settings else (selected,))
            for setting in settings:
                episodes.append(make_episode(labeler, args.seed, index, setting=setting,
                                             demos=args.demos, queries=args.queries,
                                             max_attempts=args.max_attempts))
        witness = difference_witness(labeler, episodes[0]["train"][0]["input"])
        canonical_checks = verify_canonical_default(labeler)
        command = shlex.join(["python3", str(Path(__file__).relative_to(ROOT)),
                              *(sys.argv[1:] if argv is None else argv)])
        manifest = write_export(args.out, episodes, witness=witness,
                                runtime_identity=labeler.bridge.runtime_identity, command=command,
                                execution_summary={"racket_evaluated_program_input_pairs": labeler.evaluated_pairs,
                                                   "racket_batches": labeler.evaluation_batches},
                                canonical_checks=canonical_checks)
        print(json.dumps({"status": "proposed", "episodes": len(episodes),
                          "demonstrations": sum(len(ep["train"]) for ep in episodes),
                          "queries": sum(len(ep["test"]) for ep in episodes),
                          "unique_public_payloads": len(manifest["public_ids"]),
                          "racket_evaluated_program_input_pairs": labeler.evaluated_pairs,
                          "racket_batches": labeler.evaluation_batches,
                          "canonical_examples_verified": len(canonical_checks),
                          "manifest": str(args.out / "private/manifest.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
