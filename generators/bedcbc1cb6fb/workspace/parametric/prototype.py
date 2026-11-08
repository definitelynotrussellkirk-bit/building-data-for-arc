"""Native nested-ring episodes; every delivered label is protected Racket output.

The sampler is a separate extension of the calibrated production grammar.
Outside shape completion is an opt-in rule, never a canonical relabeling.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from types import ModuleType


TASK_ID = "bedcbc1cb6fb"
VERSION = "1.0.0"
SETTINGS = ({"rule": "rings"}, {"rule": "ring_area_fill"})
ROOT = Path(__file__).resolve().parents[4]
CANONICAL_SHA256 = "dc479cd51b3b078affe590a422cbc364d59a96b4cefd70df6982899af00aa1e9"
INSPIRATION = {
    "source_task_id": "f560132c",
    "source_split": "evaluation",
    "source_path": "shared/data/raw/arc-agi_evaluation_challenges.json",
    "challenge_sha256": "b141518eed470efcd0dba940f1cbf7e722b9f3c48eba852dc6432bb66df9cea6",
    "mode": "inspired_extension",
    "relationship_verified": False,
    "training_admitted": False,
}

# canvas h/w, partition coordinate, marker count, frame h/w, key-area offsets.
# First three: same marker count/different frame AND same frame/different count.
DEMO_RECIPES = (
    (28, 29, 10, 3, 13, 14, (0, 1, 4)),
    (22, 25, 8, 5, 13, 14, (0, -2, -5)),
    (20, 23, 8, 3, 10, 11, (0, -2, 3)),
    (24, 28, 9, 3, 12, 13, (0, 1, 5)),
    (26, 27, 9, 4, 15, 16, (0, -3, -8)),
    (18, 20, 7, 2, 9, 9, (0, -1, 4)),
)
QUERY_RECIPES = (
    (14, 16, 6, 2, 7, 7, (0, -2, 3)),
    (21, 24, 8, 3, 11, 12, (0, 1, 4)),
    (30, 30, 10, 5, 18, 19, (0, -5, 3)),
    (25, 29, 9, 4, 14, 15, (0, -2, -5)),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"rule"}
            or type(settings["rule"]) is not str
            or settings["rule"] not in ("rings", "ring_area_fill")):
        raise ValueError("settings must name exactly rule=rings or rule=ring_area_fill")
    return settings["rule"]


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


@lru_cache(maxsize=1)
def canonical_source():
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row["program_solution"]
                if hashlib.sha256(source.encode()).hexdigest() != CANONICAL_SHA256:
                    raise ValueError("selected canonical source differs from this candidate's authority")
                return source
    raise ValueError("canonical task missing from this checkout")


@lru_cache(maxsize=1)
def _area_program():
    from puzzle_generators.rule_wrap import strip_rule_wrapper

    fill_rings = strip_rule_wrapper(canonical_source())
    return """(rule! (lambda (g)
  (define fill-rings %s)
  (define after-a (fill-rings g))
  (define palette
    (filter (lambda (v) (and (!= v 0) (!= v 1)))
      (for/list ((k (range 0 (min (rows g) (cols g))))) (at g k k))))
  (define center-color (last palette))
  (define blues (find-color g 1))
  (define r1 (min-of first blues))
  (define c1 (min-of second blues))
  (define r2 (max-of first blues))
  (define c2 (max-of second blues))
  (define (count-center state)
    (for*/sum ((r (range (+ r1 1) r2)) (c (range (+ c1 1) c2)))
      (if (= (at state r c) center-color) 1 0)))
  (define key-area (count-center after-a))
  (define keys
    (filter
      (lambda (o)
        (and (!= (obj-color o) 1) (> (obj-size o) 1)
          (for/and ((p (obj-cells o)))
            (and (!= (first p) (second p))
                 (not (and (<= r1 (first p) r2) (<= c1 (second p) c2)))))))
      (objects g 0)))
  (define matches (filter (lambda (o) (= (obj-size o) key-area)) keys))
  (if (null? matches) after-a
    (let ((target (car matches)))
      (cellmap after-a (r c v)
        (if (and (<= (obj-r1 target) r (obj-r2 target))
                 (<= (obj-c1 target) c (obj-c2 target)))
            center-color v))))))""" % fill_rings


def program(settings):
    return canonical_source() if _settings(settings) == "rings" else _area_program()


def execute(source, grid, bridge=None):
    """Execute exact source with the same-checkout protected bridge; no mirror labels."""
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    _grid(grid)
    if type(source) is not str or not source.strip():
        raise ValueError("source must be nonempty Racket text")
    if bridge is None:
        with RacketBridge() as owned:
            return execute(source, grid, bridge=owned)
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("labels require a live protected Racket backend")
    datum = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return _grid(bridge.eval_text(f"({wrap_rule(source)} {datum})"))


def _rng(seed, split, index, candidate=0):
    key = f"{TASK_ID}/{VERSION}/{seed}/{split}/{index}/{candidate}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _polyomino(area, slot_height, slot_width, rng):
    """Construct one connected, nonrectangular shape with exact area and bbox."""
    dimensions = [(h, w) for h in range(2, slot_height + 1)
                  for w in range(2, slot_width + 1)
                  if h + w - 1 <= area < h * w <= area + max(3, area // 3)]
    if not dimensions:
        raise ValueError(f"no nonrectangular shape of area {area} in slot {slot_height}x{slot_width}")
    h, w = rng.choice(dimensions)
    # A full top/left backbone pins the bbox and ensures connected growth.
    cells = {(0, c) for c in range(w)} | {(r, 0) for r in range(h)}
    while len(cells) < area:
        frontier = {(rr, cc) for r, c in cells
                    for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                    if 0 <= rr < h and 0 <= cc < w and (rr, cc) not in cells}
        cells.add(rng.choice(sorted(frontier)))
    if rng.randrange(2):
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, w - 1 - c) for r, c in cells}
    return h, w, cells


def _scene(seed, split, index, candidate=0):
    recipe = (DEMO_RECIPES if split == "train" else QUERY_RECIPES)[index]
    h, w, cut, marker_count, frame_h, frame_w, offsets = recipe
    rng = _rng(seed, split, index, candidate)
    grid = [[0] * w for _ in range(h)]
    colors = rng.sample(range(2, 10), marker_count + 3)
    if split == "train" and index == 0:
        # The first three-marker example deliberately uses a nonnumeric order,
        # with a middle-valued last marker, to teach order rather than color ID.
        low, middle, high = sorted(colors[:marker_count])
        colors[:marker_count] = [high, low, middle]
    positions = sorted([0, cut - 2] + rng.sample(range(1, cut - 2), marker_count - 2))
    for k, color in zip(positions, colors[:marker_count]):
        grid[k][k] = color
    stress = split == "test" and index == 2
    frame_r = h - frame_h if stress else cut + rng.randrange(h - cut - frame_h + 1)
    frame_c = w - frame_w if stress else cut + rng.randrange(w - cut - frame_w + 1)
    for r in range(frame_r, frame_r + frame_h):
        for c in range(frame_c, frame_c + frame_w):
            if r in (frame_r, frame_r + frame_h - 1) or c in (frame_c, frame_c + frame_w - 1):
                grid[r][c] = 1
    lower_first_h = (h - cut - 1) // 2
    slots = ((0, cut, cut - 1, w - cut),
             (cut, 0, lower_first_h, cut - 1),
             (cut + lower_first_h + 1, 0, h - cut - lower_first_h - 1, cut - 1))
    order = rng.sample(range(3), 3)
    center_area = (frame_h - 2 * marker_count) * (frame_w - 2 * marker_count)
    for key_index, delta in enumerate(offsets):
        sr, sc, sh, sw = slots[order[key_index]]
        oh, ow, cells = _polyomino(center_area + delta, sh, sw, rng)
        if stress:
            r0 = sr if sr == 0 else sr + sh - oh
            c0 = sc + sw - ow if sr == 0 else sc
        else:
            r0, c0 = sr + rng.randrange(sh - oh + 1), sc + rng.randrange(sw - ow + 1)
        for r, c in cells:
            grid[r0 + r][c0 + c] = colors[marker_count + key_index]
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    return grid


@lru_cache(maxsize=1)
def _rivals():
    path = Path(__file__).with_name("rivals.py")
    module = ModuleType("_bedcbc1cb6fb_demo_diagnostics")
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


@lru_cache(maxsize=128)
def _teaching_pair(seed):
    """Bounded demo-only selection; never reads query inputs or query labels.

    Independent Python diagnostics choose layouts, not delivered labels. The
    audit separately compares their intended predictions to protected Racket.
    """
    rivals = _rivals()
    hypotheses = [(s["rule"], name) for s in SETTINGS for name in rivals.active_rivals(s["rule"])]
    full = (1 << len(hypotheses)) - 1
    seen = [[], []]
    attempts = 0
    for candidate in range(64):
        for side in (0, 1):
            grid = _scene(seed, "train", side, candidate)
            truth = {s["rule"]: rivals.predict(grid, s["rule"]) for s in SETTINGS}
            mask = 0
            for bit, (rule, name) in enumerate(hypotheses):
                if rivals.predict(grid, rule, name) != truth[rule]:
                    mask |= 1 << bit
            attempts += 1
            current = (grid, mask, candidate)
            for other in seen[1 - side]:
                if mask | other[1] == full:
                    pair = [current, other] if side == 0 else [other, current]
                    return ([x[0] for x in pair], {
                        "candidate_count": attempts, "candidate_limit": 128,
                        "chosen_candidates": [x[2] for x in pair],
                        "declared_wrong_rule_comparisons": len(hypotheses),
                        "query_inputs_consulted": False, "query_labels_consulted": False,
                        "method": "constructive shapes plus bounded demonstration-only refutation",
                    })
            seen[side].append(current)
    raise RuntimeError(f"no distinguishing two-demo pair in 128 candidates for seed {seed}")


def teaching_metadata(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    return copy.deepcopy(_teaching_pair(seed)[1])


def sample_inputs(seed, demos=3, queries=4):
    """Setting-independent split streams; count changes retain each prefix."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    first_two = copy.deepcopy(_teaching_pair(seed)[0])
    return {"train": first_two + [_scene(seed, "train", i) for i in range(2, demos)],
            "test": [_scene(seed, "test", i) for i in range(queries)]}


def generate(seed, settings, demos=3, queries=4):
    from arc_repl.racket_bridge import RacketBridge

    source = program(settings)
    inputs = sample_inputs(seed, demos=demos, queries=queries)
    result = {"program_solution": source, "settings": copy.deepcopy(settings),
              "seed": seed, "prototype_version": VERSION,
              "inspiration": copy.deepcopy(INSPIRATION)}
    with RacketBridge() as bridge:
        for split in ("train", "test"):
            result[split] = [{"input": grid, "output": execute(source, grid, bridge=bridge)}
                             for grid in inputs[split]]
    return result


def public_turn(episode, query_index=0):
    """One visible query, without controller metadata or fields added to pairs."""
    from reviewer_support import public_challenge_bytes

    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(visible))


def write_examples(out, seed=17, demos=3):
    from reviewer_support import public_challenge_bytes

    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError("example destination must be new or empty")
    public, private = out / "public", out / "private"
    public.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    entries = []
    for index, settings in enumerate(SETTINGS):
        episode = generate(seed, settings, demos=demos, queries=4)
        data = public_challenge_bytes(public_turn(episode))
        identifier = hashlib.sha256(data).hexdigest()
        filename = f"challenge-{identifier}.json"
        (public / filename).write_bytes(data)
        private_name = f"episode-{index}.json"
        (private / private_name).write_text(json.dumps(episode, indent=2) + "\n")
        entries.append({"settings": settings, "public": "public/" + filename,
                        "private": "private/" + private_name,
                        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest()})
    report = {"task_id": TASK_ID, "seed": seed, "demos": demos, "private_queries": 4,
              "entries": entries, "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "status": "reviewer_examples", "owner_acceptance": "pending", "training_admitted": False}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(write_examples(args.out, seed=args.seed, demos=args.demos), indent=2))


if __name__ == "__main__":
    main()
