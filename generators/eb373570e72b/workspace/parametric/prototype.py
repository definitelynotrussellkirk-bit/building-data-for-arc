"""Ranked barriers in the canonical falling-marker puzzle.

Inputs are independent of the episode setting. Labels are executed in protected
Racket; the native worker independently executes them again before admission.
The separate prototype extends height to 30 and allows row-disjoint loose blue
fragments. It does not change the selected canonical generator or reference.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "eb373570e72b"
SETTINGS = ({"blocker_rank": 1}, {"blocker_rank": 2})
HOME = Path(__file__).resolve().parent


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"blocker_rank"}:
        raise ValueError("settings must contain exactly blocker_rank")
    return _integer(settings["blocker_rank"], 1, 2, "blocker_rank")


def _replace(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Canonical program changed; re-review the parameter transformation")
    return source.replace(old, new, 1)


@lru_cache(maxsize=1)
def canonical_program():
    return (HOME / "canonical.rkt").read_text(encoding="utf-8")


def program(settings):
    rank = _settings(settings)
    source = canonical_program()
    if rank == 1:
        return source
    source = _replace(source, "(if (empty? next-vs)", "(if (< (length next-vs) 2)")
    return _replace(source, "(first next-vs)", "(list-ref next-vs 1)")


def _grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("Expected a 3..30 by 7..30 grid")
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w
           or any(type(c) is not int or c not in (0, 1, 2) for c in row)
           for row in grid):
        raise ValueError("Expected rectangular literal integer colors 0, 1, 2")
    return grid


def analyze(grid):
    """Validate the prototype grammar and expose input-derived causal facts."""
    _grid(grid)
    h, w = len(grid), len(grid[0])
    counts = [sum(c != 0 for c in row) for row in grid]
    if not max(counts):
        raise ValueError("A scene must contain markers")
    active = next(r for r, count in enumerate(counts) if count and count >= max(counts) - 1)
    markers = [c for c in range(w) if grid[active][c]]
    if any(b - a < 3 for a, b in zip(markers, markers[1:])):
        raise ValueError("Active markers must be at least three columns apart")
    chains = []
    for c in markers:
        previous = chains[-1][-1] if chains else None
        split = (previous is None or c - previous != 3
                 or (active == 0 and grid[0][previous] == 2 and grid[0][c] == 1))
        if split:
            chains.append([])
        chains[-1].append(c)
    horizontal = []
    vertical = []
    for chain in chains:
        is_horizontal = (any(grid[active][c] == 1 for c in chain) if active
                         else grid[0][chain[0]] == 1)
        (horizontal if is_horizontal else vertical).extend(chain)
    first_rows = {}
    for c in markers:
        rows = [r for r in range(h) if grid[r][c]]
        if rows != list(range(rows[0], h)) or any(grid[r][c] != grid[active][c] for r in rows):
            raise ValueError("Active columns must be constant-color contiguous suffixes")
        first_rows[c] = rows[0]
    loose = [[r, c] for r in range(h) for c in range(w) if grid[r][c] and c not in markers]
    if active == 0:
        if loose or any(start != 0 for start in first_rows.values()):
            raise ValueError("Nonstaggered columns must be full-height")
    else:
        if any(r <= active or grid[r][c] != 1 for r, c in loose):
            raise ValueError("Loose cells must be blue and below the active row")
        if any(sum(r == row for r, _ in loose) > 1 for row in range(h)):
            raise ValueError("At most one extra loose blue cell is allowed per row")
        if not vertical or not loose:
            raise ValueError("Staggered scenes require vertical and loose roles")
    if not horizontal:
        raise ValueError("A scene needs a horizontal chain")
    return {"height": h, "width": w, "active_row": active,
            "markers": markers, "chains": chains, "horizontal_cols": horizontal,
            "vertical_cols": vertical, "loose_cells": loose,
            "first_rows": first_rows}


def _rng(seed, split, index):
    key = f"{TASK_ID}:ranked-barriers-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _scene(h, w, active, markers, early=(), fragments=()):
    grid = [[0] * w for _ in range(h)]
    starts = dict(early)
    for c, color in markers:
        for r in range(starts.get(c, active), h):
            grid[r][c] = color
    for c, lo, hi in fragments:
        for r in range(lo, hi):
            if grid[r][c]:
                raise AssertionError("Loose fragment overlaps an active marker")
            grid[r][c] = 1
    analyze(grid)
    return grid


def _nonstaggered(rng, *, compact=False):
    shift = rng.randrange(3)
    markers = [(1, 2), (4, 1), (7, 2), (11, 2), (14, 2), (18, 1), (21, 2), (25, 2)]
    if compact:
        markers = [(1, 2), (4, 1), (7, 2), (11, 2), (14, 1)]
    markers = [(c + shift, color) for c, color in markers]
    w = rng.randint(markers[-1][0] + 1, 25 if compact else 30)
    h = rng.randint(7, 9) if compact else rng.randint(3, 6)
    return _scene(h, w, 0, markers)


def _rich(rng, height):
    shift = rng.randrange(3)
    w = rng.randint(26 + shift, 30)
    active = rng.randint(1, min(3, height - 4))
    markers = [(1, 2), (4, 1), (8, 2), (11, 2), (15, 1), (18, 2), (22, 2), (25, 1)]
    markers = [(c + shift, color) for c, color in markers]
    # Three distinct loose roles, with disjoint vertical supports. This keeps
    # max row count at M+1, so the first count-M row remains the active row.
    cuts = sorted(rng.sample(range(active + 2, height), 2))
    fragments = [(shift, active + 1, cuts[0]),
                 (10 + shift, cuts[0], cuts[1]),
                 (16 + shift, cuts[1], height)]
    return _scene(height, w, active, markers,
                  early=((8 + shift, 0), (11 + shift, rng.randrange(active + 1))),
                  fragments=fragments)


def _teaching_rich(rng):
    """Keep both ranked endpoints observable in the final painted floor.

    The former two-column vertical chain let base paint hide a short rank-1
    endpoint and the shortage fragment hide a long rank-2 endpoint. A third
    vertical marker separates the shortage witness from those two endpoints.
    """
    height = rng.randint(7, 12)
    active = rng.randint(1, min(3, height - 4))
    markers = [(1, 2), (4, 1), (9, 2), (12, 2), (15, 2),
               (19, 1), (22, 2), (26, 2), (29, 1)]
    cuts = sorted(rng.sample(range(active + 2, height), 2))
    fragments = [(0, active + 1, cuts[0]), (13, cuts[0], cuts[1]),
                 (20, cuts[1], height)]
    return _scene(height, 30, active, markers,
                  early=((9, 0), (12, rng.randrange(active + 1)),
                         (15, rng.randrange(active + 1))), fragments=fragments)


def _suffix(rng, height):
    w = rng.randint(16, 30)
    shift = rng.randrange(3)
    active = rng.randint(1, min(4, height - 2))
    markers = [(1 + shift, 1), (4 + shift, 2), (8 + shift, 2)]
    loose = rng.choice((6 + shift, w - 2, w - 1))
    return _scene(height, w, active, markers,
                  early=((8 + shift, 0),), fragments=((loose, active + 1, height),))


def _dense(rng):
    active = rng.randint(1, 3)
    cut = rng.randint(12, 20)
    markers = [(0, 1), (3, 2), (6, 1), (9, 2)] + [(c, 2) for c in (13, 16, 19, 22, 25, 28)]
    return _scene(30, 30, active, markers, early=((13, 0),),
                  fragments=((2, active + 1, cut), (29, cut, 30)))


def _small(rng):
    markers = rng.choice(([(0, 2), (3, 1), (6, 2)],
                          [(0, 1), (3, 2), (6, 1)], [(0, 1), (4, 2)]))
    return _scene(3, 7, 0, markers)


def sample_inputs(seed, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train, test = [], []
    for i in range(demos):
        rng = _rng(seed, "train", i)
        if i == 0:
            grid = _nonstaggered(rng)
        elif i == 1:
            grid = _teaching_rich(rng)
        elif i == 2:
            grid = _suffix(rng, rng.randint(13, 18))
        elif i == 3:
            grid = _nonstaggered(rng, compact=True)
        elif i == 4:
            grid = _rich(rng, rng.randint(19, 24))
        else:
            grid = _suffix(rng, rng.randint(25, 29))
        train.append(grid)
    for i in range(queries):
        rng = _rng(seed, "test", i)
        if i == 0:
            grid = _rich(rng, rng.randint(13, 17))
        elif i == 1:
            grid = _dense(rng)
        elif i == 2:
            grid = _small(rng)
        else:
            grid = _suffix(rng, rng.randint(20, 23))
        test.append(grid)
    fingerprints = [json.dumps(g) for g in train + test]
    if len(set(fingerprints)) != len(fingerprints):
        raise AssertionError("Constructive roles produced duplicate inputs")
    return {"train": train, "test": test}


class Executor:
    """One protected Racket process and a bounded, per-episode label cache."""
    def __enter__(self):
        self.bridge = RacketBridge()
        self.wrapped = {}
        self.cache = {}
        self.identity = self.bridge.runtime_identity
        if self.identity.get("backend") != "racket" or self.identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("A protected Racket runtime is required")
        return self

    def apply(self, source, grid):
        _grid(grid)
        key = (source, json.dumps(grid, separators=(",", ":")))
        if key not in self.cache:
            if source not in self.wrapped:
                self.wrapped[source] = wrap_rule(source)
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            out = self.bridge.eval_text(f"({self.wrapped[source]} {literal})")
            self.cache[key] = deepcopy(_grid(out))
        return deepcopy(self.cache[key])

    def __exit__(self, *args):
        self.bridge.close()


def generate(seed, settings, demos, queries):
    rank = _settings(settings)
    inputs = sample_inputs(seed, demos, queries)
    source = program(settings)
    with Executor() as executor:
        pairs = {split: [{"input": g, "output": executor.apply(source, g)} for g in grids]
                 for split, grids in inputs.items()}
        survivors = []
        for rival in SETTINGS:
            predictions = [executor.apply(program(rival), pair["input"]) for pair in pairs["train"]]
            if all(out == pair["output"] for out, pair in zip(predictions, pairs["train"])):
                survivors.append(dict(rival))
        if survivors != [{"blocker_rank": rank}]:
            raise ValueError("Demonstrations fail to identify the episode rule")
        identity = {k: v for k, v in executor.identity.items()
                    if k in ("schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                             "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256")}
    return {**pairs, "program_solution": source, "settings": {"blocker_rank": rank},
            "seed": seed, "racket": identity,
            "lesson_certificate": {"basis": "demonstrations_only", "survivors": survivors,
                                   "scope": "two declared settings; finite evidence"}}


def rival_programs(settings):
    """Plausible finite shortcuts; all remain executable on admitted inputs."""
    source = program(settings)
    rank = _settings(settings)
    rivals = {"other_rank": program({"blocker_rank": 3 - rank})}
    vertical = "(filter (lambda (c) (not (horizontal? c))) markers)"
    rivals["raw_red_barriers"] = _replace(source, vertical,
                                         "(filter (lambda (c) (= 2 (at g active-row c))) markers)")
    rivals["all_markers_are_barriers"] = _replace(source, vertical, "markers")
    rivals["ignore_loose_blue"] = _replace(source, "(not (member? c markers))", "#f")
    rivals["skip_red_gap_closure"] = _replace(source, "(zero? (at out (- h 1) c))", "#f")
    rivals["ignore_earlier_red"] = _replace(source, "(first-row-at-col m)", "active-row")
    rivals["exact_busiest_row"] = _replace(source, "(- max-count 1)", "max-count")
    for length in (1, 2, 4):
        rivals[f"fallback_length_{length}"] = _replace(source, "(+ c 2)", f"(+ c {length - 1})")
    rivals["fallback_to_right_edge"] = _replace(source, "(min (- w 1) (+ c 2))", "(- w 1)")
    any_blue = "(any? (lambda (cc) (= 1 (at g active-row cc)))\n                       (chain-cols c))"
    rivals["staggered_first_marker_only"] = _replace(source, any_blue,
                                                    "(= 1 (at g active-row (chain-left c)))")
    handoff = "(not (and (= 2 (at g active-row prev))\n                                    (= 1 (at g active-row x))))"
    rivals["ignore_nonstaggered_handoff"] = _replace(source, handoff, "#t")
    target = "(first next-vs)" if rank == 1 else "(list-ref next-vs 1)"
    for offset in (1, 3):
        rivals[f"barrier_clearance_{offset - 1}"] = _replace(
            source, f"(- {target}\n                                                      2)",
            f"(- {target} {offset})")
    if rank == 2:
        clamped = _replace(source, "(if (< (length next-vs) 2)", "(if (empty? next-vs)")
        rivals["clamp_rank_to_available"] = _replace(
            clamped, "(list-ref next-vs 1)", "(list-ref next-vs (min 1 (- (length next-vs) 1)))")
    return rivals


def audit_episode(episode):
    """Use demos to fit each rival before looking for query disagreements."""
    survivors, rejected, divergences = [], [], []
    with Executor() as executor:
        for name, source in rival_programs(episode["settings"]).items():
            predictions = [executor.apply(source, pair["input"]) for pair in episode["train"]]
            mismatches = [i for i, (out, pair) in enumerate(zip(predictions, episode["train"]))
                          if out != pair["output"]]
            if mismatches:
                rejected.append({"rival": name, "demonstration_indices": mismatches})
            else:
                survivors.append(name)
                for i, pair in enumerate(episode["test"]):
                    out = executor.apply(source, pair["input"])
                    if out != pair["output"]:
                        divergences.append({"rival": name, "query_index": i,
                                            "input": pair["input"], "output": pair["output"],
                                            "rival_program": source, "rival_output": out})
        identity = {"backend": executor.identity["backend"], "protected": executor.identity["protected"]}
    return {"settings": episode["settings"], "seed": episode["seed"],
            "racket": identity, "rejected": rejected, "survivors": survivors,
            "query_divergences": divergences,
            "scope": "finite declared rivals only; no claim of universal uniqueness"}


def visible_query(episode, index):
    _integer(index, 0, len(episode["test"]) - 1, "query index")
    # Reuse the authoritative projection; do not expose any count or turn hint.
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                             "test": [episode["test"][index]]}))


def write_export(out, episodes):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError("Choose a new export destination")
    prepared = []
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        prepared.append((public_challenge_id(episode), raw, deepcopy(episode)))
    if not prepared:
        raise ValueError("An export must contain at least one episode")
    if len({key for key, _, _ in prepared}) != len(prepared):
        raise ValueError("Duplicate visible episodes")
    prepared.sort(key=lambda item: item[0])
    (out / "public").mkdir(parents=True)
    public_files = []
    with (out / "private.jsonl").open("w", encoding="utf-8") as private:
        for key, raw, episode in prepared:
            path = f"public/{key}.json"
            (out / path).write_bytes(raw)
            public_files.append({"id": key, "path": path, "sha256": hashlib.sha256(raw).hexdigest()})
            private.write(json.dumps({**episode, "id": key}, sort_keys=True) + "\n")
    manifest = {"schema": "eb373570e72b-proposed-export-v1", "episode_count": len(prepared),
                "public_files": public_files, "private_file": "private.jsonl",
                "native_accepted": False, "training_admitted": False,
                "visibility": "public files are controller containers; reveal one query at a time"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--rank", type=int, choices=(1, 2))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    settings = SETTINGS if args.rank is None else ({"blocker_rank": args.rank},)
    episodes = [generate(args.seed, setting, args.demos, args.queries) for setting in settings]
    audits = [audit_episode(episode) for episode in episodes]
    if any(audit["query_divergences"] for audit in audits):
        raise ValueError("A plausible rival survives demonstrations and changes a query")
    manifest = write_export(args.out, episodes)
    (args.out / "self-audit.json").write_text(json.dumps(audits, indent=2) + "\n")
    print(json.dumps({"episode_count": manifest["episode_count"], "out": str(args.out),
                      "rivals_rejected": [len(a["rejected"]) for a in audits],
                      "query_divergences": sum(len(a["query_divergences"]) for a in audits)}))


if __name__ == "__main__":
    main()
