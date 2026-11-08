#!/usr/bin/env python3
"""Source-bound rectangle-to-cross lessons; labels execute in protected Racket."""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, normalize_grid
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "13507b4f7614"
VERSION = "rectangle-cross-cascade-v1"
CANONICAL_SHA256 = "812105731900a688cc0c44d666e50dd11f6cabdb8858f3d633e471c1dacf4936"
SETTINGS = ({"selection_rule": "all_odd"}, {"selection_rule": "cross_area_cascade"})
COUNTERFACTUAL_MARKER = "(define target-area (occupied-after-a after-a anchor))"
COUNTERFACTUAL_REPLACEMENT = "(define target-area (obj-size anchor))"

CASCADE_PROGRAM = """(rule!
  (let ()
    (define (height obj) (+ 1 (- (obj-r2 obj) (obj-r1 obj))))
    (define (width obj) (+ 1 (- (obj-c2 obj) (obj-c1 obj))))
    (define (eligible? obj)
      (and (= (obj-color obj) 4) (solid-rect? obj)
           (= (modulo (height obj) 2) 1)
           (= (modulo (width obj) 2) 1)))
    (define (cross grid obj)
      (let* ((cleared (paint-cells grid (obj-cells obj) 0))
             (mr (quotient (+ (obj-r1 obj) (obj-r2 obj)) 2))
             (mc (quotient (+ (obj-c1 obj) (obj-c2 obj)) 2))
             (with-row
              (for/fold ((acc cleared))
                        ((c (in-range (obj-c1 obj) (+ 1 (obj-c2 obj)))))
                (set-cell acc mr c 4))))
        (for/fold ((acc with-row))
                  ((r (in-range (obj-r1 obj) (+ 1 (obj-r2 obj)))))
          (set-cell acc r mc 4))))
    (define (occupied-after-a grid obj)
      (for*/sum ((r (in-range (obj-r1 obj) (+ 1 (obj-r2 obj))))
                 (c (in-range (obj-c1 obj) (+ 1 (obj-c2 obj)))))
        (if (= (at grid r c) 4) 1 0)))
    (define candidates (filter eligible? (objects g 0)))
    (if (empty? candidates)
        g
        (let* ((anchor (first (sort candidates
                                   (lambda (a b) (> (obj-size a) (obj-size b))))))
               (after-a (cross g anchor)))
          (define target-area (occupied-after-a after-a anchor))
          (define matches
            (filter (lambda (obj)
                      (and (eligible? obj) (= (obj-size obj) target-area)))
                    (objects after-a 0)))
          (for/fold ((out after-a)) ((obj (in-list matches)))
            (cross out obj))))))"""


def _integer(name, value, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"selection_rule"}
            or type(settings["selection_rule"]) is not str
            or settings["selection_rule"] not in ("all_odd", "cross_area_cascade")):
        raise ValueError("settings must declare exactly one supported selection_rule")
    return settings["selection_rule"]


def canonical_source():
    sources = set()
    for line in canonical_path(find_root(__file__)).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError("expected one selected canonical authority")
    source = sources.pop()
    if (type(source) is not str
            or hashlib.sha256(source.encode()).hexdigest() != CANONICAL_SHA256):
        raise ValueError("canonical authority differs from the pinned source")
    return source


def program(settings):
    return canonical_source() if _setting(settings) == "all_odd" else CASCADE_PROGRAM


def execute(source, grid, bridge=None):
    """Execute supplied source, including diagnostic counterfactuals, in Racket."""
    if bridge is None:
        with RacketBridge() as owned:
            return execute(source, grid, owned)
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("labels require the protected Racket backend")
    inp = normalize_grid(grid)
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in inp) + ")"
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {literal})"))


# A scene is: canvas, anchor, matched rectangle, long odd distractor,
# second odd distractor (packed with the match), even-sided distractor.
# Two mandatory demonstrations change target area/rank/aspect and expose
# both mixed-parity cases. Later scenes include novel cross counts and sizes.
_DEMO_RECIPES = (
    ((20, 26), (5, 5), (3, 3), (7, 3), (3, 7), (6, 9)),
    ((30, 24), (13, 9), (3, 7), (15, 3), (3, 3), (9, 12)),
    ((18, 24), (5, 11), (3, 5), (7, 3), (3, 3), (6, 10)),
    ((22, 28), (9, 13), (3, 7), (3, 9), (3, 5), (10, 11)),
    ((28, 28), (13, 13), (5, 5), (3, 11), (3, 7), (12, 9)),
    ((24, 22), (7, 9), (5, 3), (3, 7), (3, 3), (9, 8)),
)
_QUERY_RECIPES = (
    ((9, 12), (3, 7), (3, 3), (5, 3), None, (4, 4)),
    ((21, 29), (9, 13), (7, 3), (5, 5), (3, 5), (8, 12)),
    ((30, 30), (13, 15), (3, 9), (11, 5), (3, 3), (14, 12)),
    ((25, 30), (11, 15), (5, 5), (7, 5), (3, 7), (12, 13)),
)


def _rng(seed, split, index, candidate=0):
    key = f"{TASK_ID}:{VERSION}:{seed}:{split}:{index}"
    if candidate:
        key += f":candidate:{candidate}"
    raw = key.encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _group_options(first, second):
    if second is None:
        return [(first[0], first[1], [(0, 0, *first)])]
    ah, aw = first
    bh, bw = second
    return [
        (ah + 1 + bh, max(aw, bw), [(0, 0, ah, aw), (ah + 1, 0, bh, bw)]),
        (max(ah, bh), aw + 1 + bw, [(0, 0, ah, aw), (0, aw + 1, bh, bw)]),
        (ah + 1 + bh, max(aw, bw), [(bh + 1, 0, ah, aw), (0, 0, bh, bw)]),
        (max(ah, bh), aw + 1 + bw, [(0, bw + 1, ah, aw), (0, 0, bh, bw)]),
    ]


def _scene(recipe, rng):
    (height, width), anchor, target, distractor, small, even = recipe
    # The small canonical-scale query uses an intentionally unequal partition.
    row_gap = 3 if (height, width) == (9, 12) else height // 2
    col_gap = 7 if (height, width) == (9, 12) else width // 2
    slots = [(r0, c0, rh, cw)
             for r0, rh in ((0, row_gap), (row_gap + 1, height - row_gap - 1))
             for c0, cw in ((0, col_gap), (col_gap + 1, width - col_gap - 1))]
    groups = [_group_options(anchor, None), _group_options(target, small),
              _group_options(distractor, None), _group_options(even, None)]
    lawful = []
    for order in itertools.permutations(range(4)):
        choices = [[option for option in group
                    if option[0] <= slots[slot][2] and option[1] <= slots[slot][3]]
                   for group, slot in zip(groups, order)]
        if all(choices):
            lawful.append((order, choices))
    if not lawful:
        raise RuntimeError("authored recipe has no constructive separated placement")
    order, choices = rng.choice(lawful)
    grid = [[0] * width for _ in range(height)]
    for slot, options in zip(order, choices):
        top, left, slot_h, slot_w = slots[slot]
        group_h, group_w, rects = rng.choice(options)
        top += rng.randrange(slot_h - group_h + 1)
        left += rng.randrange(slot_w - group_w + 1)
        for dr, dc, h, w in rects:
            for r in range(top + dr, top + dr + h):
                for c in range(left + dc, left + dc + w):
                    grid[r][c] = 4
    if rng.randrange(2):
        grid = grid[::-1]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if rng.randrange(2):
        grid = [list(row) for row in zip(*grid)]
    return grid


@lru_cache(maxsize=1)
def _rival_tools():
    path = Path(__file__).resolve().with_name("rivals.py")
    name = "_rect_cross_rivals_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


@lru_cache(maxsize=32)
def _teaching_pair(seed):
    """Choose two demos by finite rival refutation, without looking at queries.

    Python diagnostics choose *inputs only*. generate() obtains every output
    through Racket, and self_audit checks these diagnostics against that runtime.
    Each of two recipes has at most 64 deterministic layout/orientation choices;
    failure is explicit, never a shorter or silently ambiguous lesson.
    """
    rivals = _rival_tools()
    comparisons = [(truth, rival) for truth in ("all_odd", "cascade_correct")
                   for rival in rivals.RIVALS if not (truth == rival == "all_odd")]
    required = (1 << len(comparisons)) - 1
    candidates = ([], [])
    examined = 0
    for attempt in range(64):
        for index in (0, 1):
            grid = _scene(_DEMO_RECIPES[index], _rng(seed, "train", index, attempt))
            predictions = {name: rivals.diagnostic(grid, name) for name in rivals.RIVALS}
            predictions["cascade_correct"] = rivals.diagnostic(grid, "cascade_correct")
            mask = sum(1 << bit for bit, (truth, rival) in enumerate(comparisons)
                       if predictions[truth] != predictions[rival])
            current = (mask, grid, attempt)
            examined += 1
            candidates[index].append(current)
            for other in candidates[1 - index]:
                if mask | other[0] == required:
                    ordered = (current, other) if index == 0 else (other, current)
                    return ([entry[1] for entry in ordered], {
                        "candidate_indices": [entry[2] for entry in ordered],
                        "candidates_examined": examined,
                        "maximum_candidates": 128,
                        "rival_count": len(rivals.RIVALS),
                        "wrong_rule_comparisons": len(comparisons),
                        "selection_uses": "demonstrations_only",
                    })
    raise RuntimeError("no teaching pair refuted the declared finite rivals within 128 candidates")


def teaching_metadata(seed):
    _integer("seed", seed, 0, 2**63 - 1)
    return copy.deepcopy(_teaching_pair(seed)[1])


def sample_inputs(seed, demos=3, queries=4):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    mandatory = copy.deepcopy(_teaching_pair(seed)[0])
    return {
        "train": mandatory + [_scene(_DEMO_RECIPES[i], _rng(seed, "train", i))
                              for i in range(2, demos)],
        "test": [_scene(recipe, _rng(seed, "test", i))
                 for i, recipe in enumerate(_QUERY_RECIPES[:queries])],
    }


def generate(seed, settings, demos=3, queries=4):
    source = program(settings)
    inputs = sample_inputs(seed, demos, queries)
    with RacketBridge() as bridge:
        pairs = {split: [{"input": grid, "output": execute(source, grid, bridge)}
                         for grid in grids] for split, grids in inputs.items()}
    return {**pairs, "program_solution": source}


def public_turn(episode, query_index=0):
    _integer("query_index", query_index, 0, len(episode["test"]) - 1)
    return {
        "train": [{"input": copy.deepcopy(pair["input"]),
                   "output": copy.deepcopy(pair["output"])} for pair in episode["train"]],
        "test": [{"input": copy.deepcopy(episode["test"][query_index]["input"])}],
    }


def write_examples(out, seed=17, demos=3):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private").mkdir()
    records = []
    for settings in SETTINGS:
        episode = generate(seed, settings, demos=demos, queries=4)
        visible = public_turn(episode)
        ident = public_challenge_id(visible)
        public = out / "public" / f"challenge-{ident}.json"
        public.write_bytes(public_challenge_bytes(visible))
        private = out / "private" / f"{settings['selection_rule']}.json"
        private.write_text(json.dumps({**episode, "seed": seed, "settings": settings},
                                     sort_keys=True, separators=(",", ":")) + "\n")
        records.append({"settings": settings, "public": public.relative_to(out).as_posix(),
                        "private": private.relative_to(out).as_posix(), "public_sha256": ident,
                        "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest()})
    report = {"task_id": TASK_ID, "seed": seed, "demos": demos, "queries": 4,
              "records": records, "status": "reviewer_reported", "owner_acceptance": "pending"}
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(write_examples(args.out, args.seed, args.demos), indent=2))


if __name__ == "__main__":
    main()
