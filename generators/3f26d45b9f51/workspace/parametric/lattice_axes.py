"""Proposed episode-fixed axis variants of the canonical lattice-connection rule.

All emitted labels execute the materialized rule through the bundled Racket
bridge. The original generator and canonical rule are never modified.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

TASK_ID = "3f26d45b9f51"
MODES = ("both", "rows", "columns")
HOME = Path(__file__).resolve().parents[2]
for ancestor in (HOME, *HOME.parents):
    for candidate in (ancestor / "shared/runtime", ancestor):
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    else:
        continue
    break
else:
    raise RuntimeError("Run from a complete ARCpuzzles checkout or selected runtime")
from reviewer_support import (canonical_pairs, canonical_path, find_root,
                              load_selected_generator, public_challenge_bytes,
                              public_challenge_id)
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(axes):
    if type(axes) is not str or axes not in MODES:
        raise ValueError(f"axes must be one of {MODES}")
    return axes


def _grid_key(grid):
    # One shared validator supplies exact integer/shape/color semantics.
    public_challenge_bytes({"train": [{"input": grid, "output": grid}],
                            "test": [{"input": grid}]})
    return _json(grid)


@lru_cache(maxsize=1)
def canonical_program():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if line.strip()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    if len(programs) != 1:
        raise ValueError("Expected exactly one canonical program for the selected task")
    return programs.pop()


@lru_cache(maxsize=3)
def program_for(axes):
    _mode(axes)
    program = canonical_program()
    if axes == "columns":
        old = "(< (length cols-here) 2)"
        if program.count(old) != 1:
            raise ValueError("Canonical horizontal branch changed; review this variant")
        program = program.replace(old, "(or #t (< (length cols-here) 2))")
    if axes == "rows":
        old = "(< (length rows-here) 2)"
        if program.count(old) != 1:
            raise ValueError("Canonical vertical branch changed; review this variant")
        program = program.replace(old, "(or #t (< (length rows-here) 2))")
    return program


class RacketLabels:
    """One persistent reference process; no Python-label fallback."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=15)
        self.calls = 0

    def apply(self, program, grid):
        _grid_key(grid)
        if not program.startswith("(rule!") or not program.rstrip().endswith(")"):
            raise ValueError("Expected a materialized rule! program")
        body = program.rstrip()[len("(rule!"):-1].strip()
        self.bridge.define_grid("g", grid)
        output = self.bridge.eval_text("(" + body + " g)")
        _grid_key(output)
        self.calls += 1
        return output

    def close(self):
        self.bridge.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def solve_python(grid, axes):
    _mode(axes)
    _grid_key(grid)
    return GEN._solve_with_axes(grid, horizontal=axes != "columns", vertical=axes != "rows")


def _nearest_pairs(grid, axes):
    info = GEN._analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [row[:] for row in grid]
    for color, cells in info["markers"].items():
        for axis in (0, 1):
            if (axis == 0 and axes == "columns") or (axis == 1 and axes == "rows"):
                continue
            groups = defaultdict(list)
            for point in cells:
                groups[point[axis]].append(point[1-axis])
            for fixed, values in groups.items():
                values = sorted(set(values))
                if len(values) < 2:
                    continue
                _, lo, hi = min((b-a, a, b) for a, b in zip(values, values[1:]))
                for value in range(lo, hi+1):
                    row, col = (fixed, value) if axis == 0 else (value, fixed)
                    GEN._place_2x2(out, row, col, color)
    return out


def _hypotheses():
    result = {"axes:"+mode: (lambda grid, mode=mode: solve_python(grid, mode)) for mode in MODES}
    result.update({"nearest_pair:"+mode: (lambda grid, mode=mode: _nearest_pairs(grid, mode)) for mode in MODES})
    result.update({"identity": lambda grid: [row[:] for row in grid],
                   "bounding_box": GEN._rival_bbox_fill,
                   "drop_unconnected": GEN._rival_drop_unconnected,
                   "fixed_divider_one": GEN._rival_fixed_divider_one})
    return result


def lesson_certificate(demos, query_inputs):
    """Filter finite hypotheses ONLY by demonstrations, then compare query predictions.

    Query answers and the selected hidden setting are deliberately absent from
    this interface. An observationally equivalent survivor is permitted.
    """
    public_challenge_bytes({"train": demos, "test": [{"input": g} for g in query_inputs]})
    hypotheses = _hypotheses()
    survivors = {name: fn for name, fn in hypotheses.items()
                 if all(fn(pair["input"]) == pair["output"] for pair in demos)}
    if not survivors:
        raise ValueError("No hypothesis fits the demonstrations")
    queries = []
    for index, grid in enumerate(query_inputs):
        answers = {_grid_key(fn(grid)) for fn in survivors.values()}
        queries.append({"query_index": index, "identifiable": len(answers) == 1,
                        "prediction_hashes": sorted(_hash(s.encode()) for s in answers)})
    return {"scope": "finite_declared_hypotheses_demo_only", "hypotheses": sorted(hypotheses),
            "surviving_hypotheses": sorted(survivors), "queries": queries}


def distinct_inputs(draw, *, count, max_attempts):
    _integer("count", count, 1, 64)
    _integer("max_attempts", max_attempts, count, 4096)
    result, seen = [], set()
    for index in range(max_attempts):
        grid = draw(index)
        key = _grid_key(grid)
        if key not in seen:
            result.append(grid)
            seen.add(key)
            if len(result) == count:
                return result
    raise ValueError(f"Only {len(result)}/{count} distinct inputs after {max_attempts} attempts")


def make_episode(seed, *, axes=None, n_demo=3, n_query=4, K=None,
                 n_colors=None, max_attempts=None, racket):
    _integer("seed", seed, 0, 2**64-1)
    _integer("n_demo", n_demo, 2, 32)
    _integer("n_query", n_query, 1, 32)
    mode = random.Random(seed ^ 0x3F26D45B9F51).choice(MODES) if axes is None else _mode(axes)
    overrides = {}
    if K is not None:
        overrides["K"] = _integer("K", K, 7, 9)
    if n_colors is not None:
        overrides["n_colors"] = _integer("n_colors", n_colors, 2, 4)
    count = n_demo + n_query
    limit = count*12 if max_attempts is None else _integer("max_attempts", max_attempts, count, 4096)
    # Two successive slots cover horizontal and vertical triple witnesses.
    # Slot 1 also starts with a non-one divider to refute a fixed-color shortcut.
    grids = distinct_inputs(lambda i: GEN.generate(seed, i+1, difficulty="medium", **overrides),
                            count=count, max_attempts=limit)
    program = program_for(mode)
    pairs = [{"input": grid, "output": racket.apply(program, grid)} for grid in grids]
    for pair in pairs:
        if pair["output"] != solve_python(pair["input"], mode):
            raise ValueError("Python/Racket parity failure")
    cert = lesson_certificate(pairs[:n_demo], grids[n_demo:])
    if "axes:"+mode not in cert["surviving_hypotheses"] or not all(q["identifiable"] for q in cert["queries"]):
        raise ValueError("Demonstrations do not determine all requested queries")
    return {"schema": "lattice-axes-prototype-v1", "status": "proposed", "seed": seed,
            "origin": {"task_id": TASK_ID, "source_split": "training", "source_task_id": "06df4c85"},
            "parameters": {"axes": mode}, "program": program,
            "program_sha256": _hash(program.encode()), "train": pairs[:n_demo],
            "test": pairs[n_demo:], "certificate": cert}


def source_hashes():
    return {"prototype": _hash(Path(__file__).read_bytes()), "generator": GENERATOR_SHA256,
            "canonical_program": _hash(canonical_program().encode())}


def verify_episode(episode, *, racket):
    public_challenge_bytes(episode)
    if episode.get("schema") != "lattice-axes-prototype-v1" or episode.get("status") != "proposed":
        raise ValueError("Unexpected episode schema or status")
    _integer("seed", episode.get("seed"), 0, 2**64-1)
    origin = {"task_id": TASK_ID, "source_split": "training", "source_task_id": "06df4c85"}
    if _json(episode.get("origin")) != _json(origin):
        raise ValueError("Unexpected episode origin")
    if type(episode.get("parameters")) is not dict or set(episode["parameters"]) != {"axes"}:
        raise ValueError("Unexpected episode parameters")
    mode = _mode(episode["parameters"]["axes"])
    if episode["program"] != program_for(mode):
        raise ValueError("Episode program disagrees with its fixed setting")
    if episode["program_sha256"] != _hash(episode["program"].encode()):
        raise ValueError("Episode program hash mismatch")
    _integer("n_demo", len(episode["train"]), 2, 32)
    _integer("n_query", len(episode["test"]), 1, 32)
    pairs = episode["train"] + episode["test"]
    if len({_grid_key(p["input"]) for p in pairs}) != len(pairs):
        raise ValueError("Episode inputs must be distinct across demonstrations and queries")
    for pair in pairs:
        _grid_key(pair["output"])
        if racket.apply(episode["program"], pair["input"]) != pair["output"]:
            raise ValueError("Racket label mismatch")
    cert = lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
    if _json(cert) != _json(episode["certificate"]) or "axes:"+mode not in cert["surviving_hypotheses"]:
        raise ValueError("Lesson certificate mismatch")
    if not all(q["identifiable"] for q in cert["queries"]):
        raise ValueError("Ambiguous query in lesson certificate")
    return cert


def write_batch(episodes, out, *, racket):
    if type(episodes) is not list or not 1 <= len(episodes) <= 128:
        raise ValueError("Expected 1..128 episodes")
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    records = sorted(((public_challenge_id(ep), public_challenge_bytes(ep), ep) for ep in episodes), key=lambda row: row[0])
    ids = [row[0] for row in records]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate visible payload in batch")
    for _, _, ep in records:
        verify_episode(ep, racket=racket)
    # Validate everything before creating any output path.
    (out / "public").mkdir(parents=True)
    (out / "private/programs").mkdir(parents=True)
    for pid, visible, ep in records:
        (out / "public" / (pid+".json")).write_bytes(visible)
        (out / "private/programs" / (ep["program_sha256"]+".rkt")).write_text(ep["program"])
    (out / "private/episodes.jsonl").write_text("".join(_json({"public_id":pid, "episode":ep}) for pid, _, ep in records))
    report = {"schema": "lattice-axes-export-v1", "status": "proposed", "episodes": len(records),
              "public_ids": ids, "source_hashes": source_hashes(),
              "labels_per_setting": [len(ep["train"])+len(ep["test"]) for _, _, ep in records],
              "query_count": sum(len(ep["test"]) for _, _, ep in records)}
    (out / "private/manifest.json").write_text(_json(report))
    return report


def verify_export(out, *, racket):
    out = Path(out)
    manifest = json.loads((out / "private/manifest.json").read_text())
    records = [json.loads(line) for line in (out / "private/episodes.jsonl").read_text().splitlines()]
    _integer("episode count", len(records), 1, 128)
    ids = [row["public_id"] for row in records]
    if ids != sorted(set(ids)):
        raise ValueError("Export order or duplicate mismatch")
    expected_manifest = {"schema": "lattice-axes-export-v1", "status": "proposed",
                         "episodes": len(records), "public_ids": ids,
                         "source_hashes": source_hashes(),
                         "labels_per_setting": [len(r["episode"]["train"])+len(r["episode"]["test"]) for r in records],
                         "query_count": sum(len(r["episode"]["test"]) for r in records)}
    # Canonical JSON comparison distinguishes exact JSON types (True != 1).
    if _json(manifest) != _json(expected_manifest):
        raise ValueError("Export manifest claims, count types, or source hashes mismatch")
    if {p.name for p in (out / "public").iterdir()} != {pid+".json" for pid in ids}:
        raise ValueError("Unexpected or missing public files")
    for row in records:
        ep, pid = row["episode"], row["public_id"]
        file = out / "public" / (pid+".json")
        if file.is_symlink() or pid != public_challenge_id(ep) or file.read_bytes() != public_challenge_bytes(ep):
            raise ValueError("Changed public bytes or content-derived identifier")
        program = out / "private/programs" / (ep["program_sha256"]+".rkt")
        if program.is_symlink() or program.read_text() != ep["program"]:
            raise ValueError("Changed materialized Racket program")
        verify_episode(ep, racket=racket)
    return {"status": "pass", "episodes": len(records), "query_count": sum(len(r["episode"]["test"]) for r in records),
            "source_hashes": source_hashes()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path)
    target.add_argument("--verify", type=Path)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--axes", choices=(*MODES, "all", "random"), default="all")
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--K", type=int, choices=(7,8,9))
    parser.add_argument("--n-colors", type=int, choices=(2,3,4))
    parser.add_argument("--max-attempts", type=int)
    args = parser.parse_args()
    with RacketLabels() as racket:
        if args.verify:
            result = verify_export(args.verify, racket=racket)
        else:
            modes = MODES if args.axes == "all" else [None if args.axes == "random" else args.axes]
            episodes = [make_episode(args.seed, axes=mode, n_demo=args.demo_count, n_query=args.query_count,
                         K=args.K, n_colors=args.n_colors, max_attempts=args.max_attempts, racket=racket)
                        for mode in modes]
            result = write_batch(episodes, args.out, racket=racket)
        result["racket_applications"] = racket.calls
        print(_json(result), end="")


if __name__ == "__main__":
    main()
