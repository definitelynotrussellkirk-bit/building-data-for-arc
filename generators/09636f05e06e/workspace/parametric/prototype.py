"""Proposed episode-fixed zero-line prototype; canonical generator is immutable.

Python countermodels are finite teaching hypotheses, never label authority.
Every retained pair is labeled by its materialized Racket lambda.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import tempfile

from reviewer_support import (
    find_root, load_selected_generator, public_challenge_bytes, public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge

TASK = "09636f05e06e"
ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK, root=ROOT)
SETTINGS = tuple((mode, color) for mode in ("both", "rows", "columns") for color in range(1, 10))
MAX_COUNT = 32
MAX_ATTEMPTS = 256


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _setting(mode, protected_color):
    if mode not in ("both", "rows", "columns"):
        raise ValueError("mode must be both, rows, or columns")
    _integer("protected_color", protected_color, 1, 9)


def materialize_program(mode="both", protected_color=2):
    """Exact standalone Racket lambda, suitable for the supplied bridge."""
    _setting(mode, protected_color)
    row_enabled = "#t" if mode != "columns" else "#f"
    col_enabled = "#t" if mode != "rows" else "#f"
    return f"""(lambda (g)
  (define h (length g))
  (define w (length (car g)))
  (define zero-rows
    (for/list ([r (in-range h)] #:when (member 0 (list-ref g r))) r))
  (define zero-cols
    (for/list ([c (in-range w)]
               #:when (for/or ([row (in-list g)]) (= 0 (list-ref row c)))) c))
  (for/list ([row (in-list g)] [r (in-naturals)])
    (for/list ([v (in-list row)] [c (in-naturals)])
      (if (and (not (= v {protected_color}))
               (or (and {row_enabled} (member r zero-rows))
                   (and {col_enabled} (member c zero-cols))))
          0 v))))
"""


class RacketLabeler:
    def __init__(self):
        self.bridge = RacketBridge()
        self.programs = {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.bridge.close()

    def label(self, program, grid):
        if program not in self.programs:
            name = f"__parametric_rule_{len(self.programs)}"
            self.bridge.eval_text(f"(define {name} {program})")
            self.programs[program] = name
        self.bridge.define_grid("__parametric_input", grid)
        return self.bridge.eval_text(f"({self.programs[program]} __parametric_input)")


def _support(grid):
    points = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0}
    return points, {r for r, c in points}, {c for r, c in points}


def countermodel(grid, mode, protected_color, *, rival=None):
    """Marked Python hypothesis evaluator, not an answer-labeling path."""
    if rival == "fresh_zero":
        current = [list(row) for row in grid]
        # Every changed cell becomes zero and can never change again.
        # Protected-only barriers can prevent some lines ever acquiring zeros.
        for _ in range(sum(len(row) for row in grid) + 1):
            following = countermodel(current, mode, protected_color)
            if following == current:
                return current
            current = following
        raise RuntimeError("monotone fresh-zero rival failed to stabilize")
    points, rows, cols = _support(grid)
    if rival == "hull":
        rows = set(range(min(rows), max(rows) + 1)) if rows else set()
        cols = set(range(min(cols), max(cols) + 1)) if cols else set()
    if rival == "global":
        rows, cols = set(range(len(grid))), set(range(len(grid[0])))
    if rival == "stop_at_protected":
        touched = set(points)
        directions = []
        if mode != "columns":
            directions += [(0, -1), (0, 1)]
        if mode != "rows":
            directions += [(-1, 0), (1, 0)]
        for r, c in points:
            for dr, dc in directions:
                rr, cc = r + dr, c + dc
                while 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    if grid[rr][cc] == protected_color:
                        break
                    touched.add((rr, cc))
                    rr, cc = rr + dr, cc + dc
        return [[0 if (r, c) in touched else v for c, v in enumerate(row)]
                for r, row in enumerate(grid)]
    def touched(r, c):
        if rival == "intersection":
            return r in rows and c in cols
        return (mode != "columns" and r in rows) or (mode != "rows" and c in cols)
    return [[0 if touched(r, c) and (rival == "ignore_protected" or v != protected_color) else v
             for c, v in enumerate(row)] for r, row in enumerate(grid)]


def input_witnesses(grid):
    """All colors on both exclusive arms, untouched area, all-color ray contrasts."""
    points, rows, cols = _support(grid)
    if not points or GEN.self_check(grid):
        return False
    palette = set(range(1, 10))
    if {grid[r][c] for r in rows for c in range(len(grid[0])) if c not in cols} != palette:
        return False
    if {grid[r][c] for r in range(len(grid)) if r not in rows for c in cols} != palette:
        return False
    # Each protected-color hypothesis must see a later ordinary cell beyond it.
    for directions in (((0, -1), (0, 1)), ((-1, 0), (1, 0))):
        witnessed = set()
        for r, c in points:
            for dr, dc in directions:
                ray = []
                rr, cc = r + dr, c + dc
                while 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    ray.append(grid[rr][cc])
                    rr, cc = rr + dr, cc + dc
                for i, v in enumerate(ray):
                    if v and any(w not in (0, v) for w in ray[i+1:]):
                        witnessed.add(v)
        if not palette <= witnessed:
            return False
    return any(grid[r][c] != 0 for r in range(len(grid)) for c in range(len(grid[0]))
               if r not in rows and c not in cols)


def sample_input(seed, sample_index, *, max_attempts=MAX_ATTEMPTS):
    """Canonical source, visible-only witness rejection; no grid surgery."""
    _integer("seed", seed, 0, 2**32 - 1)
    _integer("sample_index", sample_index, 0, 2 * MAX_COUNT - 1)
    _integer("max_attempts", max_attempts, 1, MAX_ATTEMPTS)
    rng = random.Random(f"{TASK}|input-v1|{seed}|{sample_index}")
    profile = ("scatter", "rectangle", "thin")[sample_index % 3]
    for attempt in range(max_attempts):
        nr, nc = (rng.randint(2, 4), rng.randint(2, 4))
        if profile == "scatter":
            nc = nr
        elif profile == "thin":
            nr, nc = rng.choice(((2, 4), (4, 2)))
        controls = dict(grid_h=rng.randint(12, 22), grid_w=rng.randint(12, 22),
                        n_zero_rows=nr, n_zero_cols=nc, palette_size=10,
                        texture="scatter" if profile == "scatter" else "rectangle")
        candidate_index = sample_index * MAX_ATTEMPTS + attempt
        grid = GEN.generate(seed, candidate_index, **controls)
        if input_witnesses(grid):
            return grid, {"source_sample_index": candidate_index, "attempts": attempt + 1,
                          "profile": profile, "controls": controls}
    raise RuntimeError(f"input witness sampling exhausted {max_attempts} attempts at index {sample_index}")


def assess_teaching(demos, query_inputs):
    """Survivors use demo labels ONLY; agreement compares hypotheses, never query labels."""
    parameter_survivors = [
        setting for setting in SETTINGS
        if all(countermodel(p["input"], *setting) == p["output"] for p in demos)
    ]
    structural_survivors = []
    for setting in SETTINGS:
        for rival in ("hull", "global", "ignore_protected", "fresh_zero",
                      "intersection", "stop_at_protected"):
            if all(countermodel(p["input"], *setting, rival=rival) == p["output"] for p in demos):
                structural_survivors.append((setting[0], setting[1], rival))
    queries = []
    for grid in query_inputs:
        predictions = {
            json.dumps(countermodel(grid, *setting), separators=(",", ":"))
            for setting in parameter_survivors
        }
        predictions.update(
            json.dumps(countermodel(grid, mode, color, rival=rival), separators=(",", ":"))
            for mode, color, rival in structural_survivors
        )
        queries.append({"agreement": len(predictions) == 1, "distinct_predictions": len(predictions)})
    return {"parameter_survivors": [list(s) for s in parameter_survivors],
            "structural_survivors": [list(s) for s in structural_survivors],
            "queries": queries, "scope": "27 parameter settings plus 6 structural forms per setting"}


def build_episode(seed, *, n_train=3, n_test=4, mode=None, protected_color=None,
                  max_attempts=MAX_ATTEMPTS, labeler=None):
    _integer("seed", seed, 0, 2**32 - 1)
    for name, value in (("n_train", n_train), ("n_test", n_test)):
        _integer(name, value, 1, MAX_COUNT)
    _integer("max_attempts", max_attempts, 1, MAX_ATTEMPTS)
    chosen = random.Random(f"{TASK}|settings-v1|{seed}").choice(SETTINGS)
    mode = chosen[0] if mode is None else mode
    protected_color = chosen[1] if protected_color is None else protected_color
    _setting(mode, protected_color)
    program = materialize_program(mode, protected_color)
    inputs, draws, seen = [], [], set()
    for i in range(n_train + n_test):
        grid, receipt = sample_input(seed, i, max_attempts=max_attempts)
        key = json.dumps(grid, separators=(",", ":"))
        if key in seen:
            raise RuntimeError("duplicate input; episode rejected, no cloned or short batches")
        seen.add(key)
        inputs.append(grid)
        draws.append(receipt)
    if labeler is None:
        with RacketLabeler() as owned_labeler:
            return _label_episode(seed, mode, protected_color, program, inputs, draws,
                                  n_train, owned_labeler)
    return _label_episode(seed, mode, protected_color, program, inputs, draws, n_train, labeler)


def _label_episode(seed, mode, protected_color, program, inputs, draws, n_train, labeler):
    # Query answers are executed only after demo-only agreement has been checked.
    demos = [{"input": grid, "output": labeler.label(program, grid)} for grid in inputs[:n_train]]
    teaching = assess_teaching(demos, inputs[n_train:])
    if not teaching["parameter_survivors"] or not all(q["agreement"] for q in teaching["queries"]):
        raise RuntimeError("demonstration-only candidate disagreement; episode rejected")
    tests = [{"input": grid, "output": labeler.label(program, grid)} for grid in inputs[n_train:]]
    return {"train": demos, "test": tests, "private": {
        "status": "proposed prototype; not approved or admitted to training",
        "seed": seed, "mode": mode, "protected_color": protected_color,
        "program": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "generator_source_sha256": GENERATOR_SHA256,
        "prototype_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "public_helper_source_sha256": hashlib.sha256((ROOT/"shared/runtime/reviewer_support.py").read_bytes()).hexdigest(),
        "teaching": teaching, "input_draws": draws,
    }}


def write_batch(episodes, output_dir):
    """Fail-closed new directory; opaque content-only public names and exact-byte hashes."""
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError(output_dir)
    if not episodes:
        raise ValueError("cannot write empty batch")
    rows = []
    for episode in episodes:
        body = public_challenge_bytes(episode)
        identifier = public_challenge_id(episode)
        if hashlib.sha256(body).hexdigest() != identifier:
            raise ValueError("public helper ID/bytes mismatch")
        rows.append((identifier, body, episode))
    rows.sort(key=lambda row: row[0])
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("duplicate visible payload")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".parametric-stage-", dir=output_dir.parent))
    try:
        (staging/"public").mkdir()
        (staging/"private").mkdir()
        summary = {"status": "proposed", "public_ids": [r[0] for r in rows], "episodes": []}
        for identifier, body, episode in rows:
            (staging/"public"/f"{identifier}.json").write_bytes(body)
            private_body = (json.dumps(episode, sort_keys=True, indent=2) + "\n").encode()
            (staging/"private"/f"{identifier}.json").write_bytes(private_body)
            summary["episodes"].append({
                "public_id": identifier, "public_sha256": hashlib.sha256(body).hexdigest(),
                "private_sha256": hashlib.sha256(private_body).hexdigest(),
                "train": len(episode["train"]), "test": len(episode["test"]),
            })
        # Public index has visible-only IDs; metadata and order never influence it.
        (staging/"public/index.json").write_text(
            json.dumps({"public_ids": summary["public_ids"]}, sort_keys=True) + "\n")
        (staging/"private/summary.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
        # mkdir is exclusive even if another writer races with us.
        output_dir.mkdir()
        for child in staging.iterdir():
            child.rename(output_dir/child.name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--train", type=int, default=3)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--mode", choices=("both","rows","columns"))
    parser.add_argument("--protected-color", type=int)
    parser.add_argument("--examples", action="store_true",
                        help="two same-input episodes: canonical both+2 and alternative columns+7")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        parser.error("output directory already exists; refusing to overwrite")
    _integer("count", args.count, 1, 16)
    if args.seed + args.count - 1 > 2**32 - 1:
        parser.error("seed range overflow")
    if args.examples and (args.count != 1 or args.mode is not None or args.protected_color is not None):
        parser.error("--examples cannot combine with --count != 1 or explicit settings")
    episodes = []
    with RacketLabeler() as labeler:
        settings = [("both",2),("columns",7)] if args.examples else [(args.mode,args.protected_color)]
        for i in range(args.count):
            for mode, color in settings:
                episodes.append(build_episode(args.seed+i,n_train=args.train,n_test=args.test,
                                              mode=mode,protected_color=color,labeler=labeler))
    print(json.dumps(write_batch(episodes,args.out),sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
