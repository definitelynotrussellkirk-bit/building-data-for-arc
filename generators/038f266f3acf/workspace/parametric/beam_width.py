"""Proposed marker-derived beam-width multiplier; task-local, not approved API."""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
from itertools import combinations
import json
from pathlib import Path
import random
import sys

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "shared/runtime"))
from reviewer_support import (canonical_pairs, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)
from arc_repl.racket_bridge import RacketBridge

TASK_ID = "038f266f3acf"
CANONICAL_PROGRAM_SHA256 = "d4bc451f18638b8e2f71528bb3fa627716cef2327f0656cfdb44e86ec68971a0"
WING_RANGE = "(range 1 (+ half 1))"
ALLOWED_MULTIPLIERS = (1, 2)
MODELS = {
    "multiplier_1": (1, None),
    "multiplier_2": (2, None),
    "multiplier_1_cap_depth_4": (1, 4),
    "multiplier_2_cap_depth_4": (2, 4),
}
NATIVE_DEMO_SHAPES = ((24, 26), (25, 27), (26, 28),
                      (27, 29), (28, 30), (29, 30))
NATIVE_QUERY_SHAPES = ((24, 24), (25, 29), (28, 30), (30, 30))


class SamplingExhausted(RuntimeError):
    """The finite draw budget could not yield all requested distinct inputs."""


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _multiplier(value):
    if type(value) is not int or value not in ALLOWED_MULTIPLIERS:
        raise ValueError("wing_multiplier must be the exact integer 1 or 2")
    return value


def _cap(value):
    if value is not None and (type(value) is not int or value != 4):
        raise ValueError("cap_depth is None, or the exact integer 4 for the declared rival")
    return value


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(_grid(grid), separators=(",", ":")).encode()).hexdigest()


@lru_cache(maxsize=1)
def canonical_program():
    programs = set()
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    if len(programs) != 1:
        raise ValueError("expected one exact canonical program across task rows")
    program = programs.pop()
    if hashlib.sha256(program.encode()).hexdigest() != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical source changed; review this prototype before use")
    if program.count(WING_RANGE) != 1:
        raise ValueError("canonical wing range is not an unambiguous edit site")
    return program


def materialize_program(wing_multiplier=1, *, cap_depth=None):
    multiplier, cap = _multiplier(wing_multiplier), _cap(cap_depth)
    program = canonical_program()
    if multiplier == 1 and cap is None:
        return program
    half = "half" if cap is None else "(min half 4)"
    if multiplier == 2:
        half = f"(* 2 {half})"
    return program.replace(WING_RANGE, f"(range 1 (+ {half} 1))")


@lru_cache(maxsize=1)
def _selected():
    return load_selected_generator(TASK_ID, root=REPO_ROOT)


def selected_generator():
    return _selected()[0]


def source_hashes():
    paths = [Path(__file__).resolve().relative_to(REPO_ROOT),
             Path("shared/runtime/reviewer_support.py"),
             Path("shared/runtime/arc_repl/racket_bridge.py"),
             Path("shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt")]
    result = {str(path): hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
              for path in paths}
    _, path, digest = _selected()
    result[str(path.relative_to(REPO_ROOT))] = digest
    return result


class RacketOracle:
    """Execute exact selected programs; cache only results obtained from Racket."""
    def __init__(self):
        self.programs = {name: materialize_program(multiplier, cap_depth=cap)
                         for name, (multiplier, cap) in MODELS.items()}
        self.bridge = RacketBridge(timeout=20.0)
        self.cache = {}
        self.evaluations = 0

    def evaluate(self, grid, model):
        if model not in MODELS:
            raise ValueError("unknown declared Racket model")
        key = (model, grid_sha256(grid))
        if key not in self.cache:
            program = self.programs[model]
            if not program.startswith("(rule!") or not program.endswith(")"):
                raise ValueError("expected canonical rule! wrapper")
            expression = program[len("(rule!"):-1]
            literal = "(" + " ".join("(" + " ".join(map(str, row)) + ")"
                                       for row in grid) + ")"
            # This canonical lambda reads h/w supplied by the executor. Bind the
            # actual input dimensions locally, without changing program bytes.
            call = (f"(let* ((input-grid '{literal}) (h (rows input-grid)) "
                    f"(w (cols input-grid))) ({expression} input-grid))")
            output = self.bridge.eval_text(call)
            _grid(output)
            if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                raise ValueError("Racket output dimensions changed")
            self.cache[key] = output
            self.evaluations += 1
        return copy.deepcopy(self.cache[key])

    def close(self):
        self.bridge.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def _analysis(grid):
    _grid(grid)
    analysis = selected_generator()._analysis(grid)
    if analysis["errors"]:
        raise ValueError("structural grammar: " + "; ".join(analysis["errors"]))
    return analysis


def _beam_cells(rect, half, h, w):
    dr, dc = rect["direction"]
    mr, mc = rect["marker"]
    r, c = mr+dr, mc+dc
    while 0 <= r < h and 0 <= c < w:
        yield r, c, 2
        for offset in range(1, half+1):
            positions = ((r-offset, c), (r+offset, c)) if dr == 0 else ((r, c-offset), (r, c+offset))
            for sr, sc in positions:
                if 0 <= sr < h and 0 <= sc < w:
                    yield sr, sc, 3
        r, c = r+dr, c+dc


def simulate(grid, wing_multiplier=1, *, cap_depth=None):
    """Lawful-rectangle sampling mirror; retained labels come from Racket."""
    multiplier, cap = _multiplier(wing_multiplier), _cap(cap_depth)
    analysis = _analysis(grid)
    output = [row[:] for row in grid]
    # Canonical order is row-major over markers, even when paint overlaps.
    for rect in sorted(analysis["rectangles"], key=lambda row: row["marker"]):
        depth = rect["half_width"]
        half = multiplier * (depth if cap is None else min(depth, cap))
        for r, c, color in _beam_cells(rect, half, len(grid), len(grid[0])):
            output[r][c] = color
    return output


def _corridors_disjoint(grid, analysis):
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    emitted = set()
    for rect in analysis["rectangles"]:
        cells = {(r, c) for r, c, _ in _beam_cells(
            rect, 2*rect["half_width"], len(grid), len(grid[0]))}
        if cells & occupied or cells & emitted:
            return False
        emitted.update(cells)
    return True


def _transform(r, c, index):
    return ((r, c), (c, -r), (-r, -c), (-c, r),
            (r, -c), (-c, -r), (-r, c), (c, r))[index]


def _transform_grid(grid, index):
    h, w = len(grid), len(grid[0])
    corners = [_transform(r, c, index) for r, c in ((0, 0), (h-1, 0), (0, w-1), (h-1, w-1))]
    mr, mc = min(r for r, _ in corners), min(c for _, c in corners)
    nh, nw = max(r for r, _ in corners)-mr+1, max(c for _, c in corners)-mc+1
    output = [[0] * nw for _ in range(nh)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            a, b = _transform(r, c, index)
            output[a-mr][b-mc] = value
    return output


def _paint_rectangle(grid, r, c, h, w, edge, offset):
    for rr in range(r, r+h):
        for cc in range(c, c+w):
            if grid[rr][cc] != 0:
                raise ValueError("source rectangle overlap")
            grid[rr][cc] = 3
    mr, mc = (r+offset, c) if edge == "left" else (r, c+offset)
    grid[mr][mc] = 2


def _make_scene(rng, *, height=None, width=None):
    """Two deep source objects with perpendicular, noninteracting beams."""
    h = rng.randint(24, 30) if height is None else _integer("height", height, 24, 30)
    w = rng.randint(24, 30) if width is None else _integer("width", width, 24, 30)
    grid = [[0] * w for _ in range(h)]
    depth_a, depth_b = rng.choice(((5, 6), (6, 5)))
    ah, aw = rng.choice((5, 7)), depth_a+1
    marker_offset = rng.choice([i for i in range(1, ah-1) if i != (ah-1)//2])
    marker_row, ac = rng.randint(12, h-12), rng.randint(2, 4)
    ar = marker_row-marker_offset
    _paint_rectangle(grid, ar, ac, ah, aw, "left", marker_offset)
    bh, bw, br = depth_b+1, rng.randint(4, 7), rng.randint(2, 4)
    candidates = [(bc, offset) for bc in range(ac+aw+2, w-bw)
                  for offset in range(1, bw-1)
                  if bc+offset-2*depth_b >= ac+1]
    if not candidates:
        raise ValueError("no disjoint placement for second beam")
    bc, offset = rng.choice(candidates)
    _paint_rectangle(grid, br, bc, bh, bw, "top", offset)
    return _transform_grid(grid, rng.randrange(8))


def _difference(first, second):
    return sum(a != b for row1, row2 in zip(first, second) for a, b in zip(row1, row2))


def certify_episode(train, queries, oracle):
    """Use demonstrations to retain models; never read held-out answers."""
    if not train or not queries:
        raise ValueError("nonempty demonstrations and query inputs are required")
    demo_checks = []
    for name in MODELS:
        rejected = [index for index, pair in enumerate(train)
                    if oracle.evaluate(pair["input"], name) != pair["output"]]
        demo_checks.append({"model": name, "compatible": not rejected,
                            "rejected_by_demonstrations": rejected})
    survivors = [row["model"] for row in demo_checks if row["compatible"]]
    query_checks = []
    for pair in queries:
        outputs = {name: oracle.evaluate(pair["input"], name) for name in MODELS}
        hashes = {name: grid_sha256(output) for name, output in outputs.items()}
        surviving_hashes = {hashes[name] for name in survivors}
        identified = len(surviving_hashes) == 1
        query_checks.append({
            "input_sha256": grid_sha256(pair["input"]), "identified": identified,
            "prediction_sha256_by_model": hashes,
            "surviving_prediction_sha256": next(iter(surviving_hashes)) if identified else None,
            "parameter_disagreement_cells": _difference(outputs["multiplier_1"], outputs["multiplier_2"]),
            "cap_four_disagreement_cells": {
                str(value): _difference(outputs[f"multiplier_{value}"], outputs[f"multiplier_{value}_cap_depth_4"])
                for value in ALLOWED_MULTIPLIERS},
        })
    return {"evidence_source": "demonstrations_only",
            "claim_scope": "two multipliers and two cap-depth-four rivals; not universal uniqueness",
            "surviving_models": survivors,
            "surviving_parameters": [value for value in ALLOWED_MULTIPLIERS if f"multiplier_{value}" in survivors],
            "surviving_cap_rivals": [name for name in survivors if MODELS[name][1] is not None],
            "demonstrations": demo_checks, "queries": query_checks}


def generate_episode(*, seed, wing_multiplier=None, n_train=2, n_test=4,
                     max_attempts=128, oracle=None):
    _integer("seed", seed, 0, 2**64-1)
    _integer("n_train", n_train, 1, 16)
    _integer("n_test", n_test, 1, 16)
    _integer("max_attempts", max_attempts, 1, 4096)
    multiplier = (random.Random(seed ^ 0x038F266F3ACF).choice(ALLOWED_MULTIPLIERS)
                  if wing_multiplier is None else _multiplier(wing_multiplier))
    chosen = f"multiplier_{multiplier}"
    rng = random.Random(seed)
    needed, accepted, seen, rejections = n_train+n_test, [], set(), {}
    for draw_index in range(max_attempts):
        try:
            grid = _make_scene(rng)
            _grid(grid)
            errors = selected_generator().self_check(grid)
            if errors:
                raise ValueError("self_check: " + "; ".join(errors))
            analysis = _analysis(grid)
            identity = grid_sha256(grid)
            if identity in seen:
                raise ValueError("duplicate input")
            if not _corridors_disjoint(grid, analysis):
                raise ValueError("beam corridors collide at multiplier 2")
            outputs = {name: simulate(grid, value, cap_depth=cap)
                       for name, (value, cap) in MODELS.items()}
            if any(outputs[a] == outputs[b] for a, b in combinations(MODELS, 2)):
                raise ValueError("declared models lack distinct observable predictions")
        except ValueError as error:
            reason = str(error)
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
        seen.add(identity)
        rects = analysis["rectangles"]
        witness = {
            "input_sha256": identity, "draw_index": draw_index, "height": len(grid), "width": len(grid[0]),
            "source_depths": [rect["half_width"] for rect in rects],
            "markers": [list(rect["marker"]) for rect in rects],
            "source_bboxes": [list(rect["bbox"]) for rect in rects],
            "launch_edges": [rect["edge"] for rect in rects],
            "launch_axes": sorted({"horizontal" if rect["direction"][0] == 0 else "vertical" for rect in rects}),
            "noncentral_marker": any(rect["offset"] != (rect["span"]-1)//2 for rect in rects),
            "corridors_disjoint_at_multiplier_2": True,
            "parameter_disagreement_cells": _difference(outputs["multiplier_1"], outputs["multiplier_2"]),
            "cap_four_disagreement_cells": {
                str(value): _difference(outputs[f"multiplier_{value}"], outputs[f"multiplier_{value}_cap_depth_4"])
                for value in ALLOWED_MULTIPLIERS},
        }
        accepted.append((grid, outputs, witness))
        if len(accepted) == needed:
            break
    if len(accepted) != needed:
        raise SamplingExhausted(f"accepted {len(accepted)} of {needed} inputs in {max_attempts} attempts; rejections={rejections}")
    owned = oracle is None
    oracle = oracle or RacketOracle()
    try:
        pairs, label_evidence = [], []
        for grid, predictions, witness in accepted:
            outputs = {name: oracle.evaluate(grid, name) for name in MODELS}
            if outputs != predictions:
                raise RuntimeError("Python sampler mirror disagrees with exact Racket execution")
            pairs.append({"input": grid, "output": outputs[chosen]})
            label_evidence.append({"input_sha256": witness["input_sha256"], "racket_outputs_by_model": outputs})
        train, test = pairs[:n_train], pairs[n_train:]
        certificate = certify_episode(train, test, oracle)
        if certificate["surviving_models"] != [chosen] or not all(row["identified"] for row in certificate["queries"]):
            raise RuntimeError("demonstrations do not identify the selected multiplier against declared rivals")
        program = materialize_program(multiplier)
        executed_programs = {name: {"program_solution": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
                             for name, text in oracle.programs.items()}
        return {"schema": "038f266f3acf-beam-width-prototype-v1", "status": "proposed",
                "task_id": TASK_ID, "parent": "training:b527c5c6", "seed": seed,
                "parameters": {"wing_multiplier": multiplier},
                "program_solution": program, "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
                "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
                "executed_programs": executed_programs, "source_hashes": source_hashes(),
                "train": train, "test": test, "certificate": certificate, "label_evidence": label_evidence,
                "sampling": {"max_attempts": max_attempts, "attempts": accepted[-1][2]["draw_index"]+1,
                             "rejections": rejections, "accepted": [row[2] for row in accepted]}}
    finally:
        if owned:
            oracle.close()


class MirrorOracle:
    """Pure claim-label oracle; native qualification independently runs Racket."""
    def __init__(self):
        self.programs = {name: materialize_program(multiplier, cap_depth=cap)
                         for name, (multiplier, cap) in MODELS.items()}
        self.evaluations = 0

    def evaluate(self, grid, model):
        if model not in MODELS:
            raise ValueError("unknown declared model")
        multiplier, cap = MODELS[model]
        self.evaluations += 1
        return simulate(grid, multiplier, cap_depth=cap)


def _screen_native_scene(grid, *, draw_index, seen):
    _grid(grid)
    errors = selected_generator().self_check(grid)
    if errors:
        raise ValueError("self_check: " + "; ".join(errors))
    analysis = _analysis(grid)
    identity = grid_sha256(grid)
    if identity in seen:
        raise ValueError("duplicate input")
    if not _corridors_disjoint(grid, analysis):
        raise ValueError("beam corridors collide at multiplier 2")
    outputs = {name: simulate(grid, value, cap_depth=cap)
               for name, (value, cap) in MODELS.items()}
    if any(outputs[a] == outputs[b] for a, b in combinations(MODELS, 2)):
        raise ValueError("declared models lack distinct observable predictions")
    rects = analysis["rectangles"]
    witness = {
        "input_sha256": identity, "draw_index": draw_index,
        "height": len(grid), "width": len(grid[0]),
        "source_depths": [rect["half_width"] for rect in rects],
        "markers": [list(rect["marker"]) for rect in rects],
        "source_bboxes": [list(rect["bbox"]) for rect in rects],
        "launch_edges": [rect["edge"] for rect in rects],
        "launch_axes": sorted({"horizontal" if rect["direction"][0] == 0 else "vertical"
                               for rect in rects}),
        "noncentral_marker": any(rect["offset"] != (rect["span"]-1)//2 for rect in rects),
        "corridors_disjoint_at_multiplier_2": True,
        "parameter_disagreement_cells": _difference(
            outputs["multiplier_1"], outputs["multiplier_2"]),
        "cap_four_disagreement_cells": {
            str(value): _difference(outputs[f"multiplier_{value}"],
                                    outputs[f"multiplier_{value}_cap_depth_4"])
            for value in ALLOWED_MULTIPLIERS},
    }
    return grid, outputs, witness


def _sample_native_scenes(rng, shapes, *, max_attempts, seen):
    accepted, rejections, attempts = [], {}, 0
    for height, width in shapes:
        while attempts < max_attempts:
            draw_index = attempts
            attempts += 1
            try:
                record = _screen_native_scene(
                    _make_scene(rng, height=height, width=width),
                    draw_index=draw_index, seen=seen)
            except ValueError as error:
                reason = str(error)
                rejections[reason] = rejections.get(reason, 0) + 1
                continue
            seen.add(record[2]["input_sha256"])
            accepted.append(record)
            break
        else:
            raise SamplingExhausted(
                f"accepted {len(accepted)} of {len(shapes)} scheduled inputs in "
                f"{max_attempts} attempts; rejections={rejections}")
    return accepted, {"attempts": attempts, "rejections": rejections}


def generate_native_episode(*, seed, wing_multiplier, n_train, n_test=4,
                            max_attempts=512):
    """Deterministic claim labels for the native adapter; no nested Racket."""
    _integer("seed", seed, 0, 2**63-1)
    _integer("n_train", n_train, 2, 6)
    if type(n_test) is not int or n_test != 4:
        raise ValueError("n_test must be the exact integer 4")
    _integer("max_attempts", max_attempts, 1, 4096)
    multiplier = _multiplier(wing_multiplier)
    chosen = f"multiplier_{multiplier}"
    seen = set()
    demos, demo_sampling = _sample_native_scenes(
        random.Random(seed ^ 0xD3A09E3779B97F4A),
        NATIVE_DEMO_SHAPES[:n_train], max_attempts=max_attempts, seen=seen)
    queries, query_sampling = _sample_native_scenes(
        random.Random(seed ^ 0x51ED270B5A1D3C67),
        NATIVE_QUERY_SHAPES, max_attempts=max_attempts, seen=seen)
    pairs = [{"input": grid, "output": outputs[chosen]}
             for grid, outputs, _ in demos + queries]
    train, test = pairs[:n_train], pairs[n_train:]
    oracle = MirrorOracle()
    certificate = certify_episode(train, test, oracle)
    if certificate["surviving_models"] != [chosen] or not all(
            row["identified"] for row in certificate["queries"]):
        raise RuntimeError(
            "demonstrations do not identify the selected multiplier against declared rivals")
    return {
        "schema": "038f266f3acf-beam-width-native-claim-v1",
        "task_id": TASK_ID,
        "seed": seed,
        "parameters": {"wing_multiplier": multiplier},
        "program_solution": materialize_program(multiplier),
        "train": train,
        "test": test,
        "certificate": certificate,
        "sampling": {
            "demonstrations": demo_sampling,
            "queries": query_sampling,
            "accepted": [record[2] for record in demos + queries],
        },
    }


def write_batch(episodes, out):
    """Public identities derive only from the shared canonical visible bytes."""
    if type(episodes) is not list or not episodes:
        raise ValueError("episodes must be a nonempty list")
    prepared, seen = [], set()
    for episode in episodes:
        payload, identity = public_challenge_bytes(episode), public_challenge_id(episode)
        if identity in seen:
            raise ValueError("duplicate visible challenge payload")
        seen.add(identity)
        prepared.append((identity, payload, episode))
    prepared.sort(key=lambda row: row[0])
    for _, _, episode in prepared:
        chosen = materialize_program(episode["parameters"]["wing_multiplier"])
        if (episode["program_solution"] != chosen
                or episode["program_sha256"] != hashlib.sha256(chosen.encode()).hexdigest()):
            raise ValueError("private selected program does not match its bytes and parameter")
        if set(episode["executed_programs"]) != set(MODELS):
            raise ValueError("all four exact executed programs must be retained")
        for name, record in episode["executed_programs"].items():
            value, cap = MODELS[name]
            text = materialize_program(value, cap_depth=cap)
            if record != {"program_solution": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}:
                raise ValueError("private executed program does not match its declared model")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "public").mkdir()
    (out / "private/programs").mkdir(parents=True)
    rows = []
    for identity, payload, episode in prepared:
        (out / "public" / (identity + ".json")).write_bytes(payload)
        for record in episode["executed_programs"].values():
            (out / "private/programs" / (record["sha256"] + ".rkt")).write_text(record["program_solution"])
        rows.append(dict(episode, public_id=identity))
    (out / "private/episodes.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows))
    receipt = {"schema": "038f266f3acf-beam-width-export-v1", "status": "proposed",
               "episodes": len(prepared), "public_ids": [row[0] for row in prepared],
               "public_identifier_source": "exact visible challenge bytes",
               "program_sha256": sorted({record["sha256"] for _, _, ep in prepared for record in ep["executed_programs"].values()})}
    (out / "private/export.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--settings", type=int, nargs="+", choices=ALLOWED_MULTIPLIERS, default=[1, 2])
    parser.add_argument("--train", type=int, default=2)
    parser.add_argument("--test", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    with RacketOracle() as oracle:
        episodes = [generate_episode(seed=args.seed, wing_multiplier=value, n_train=args.train,
                    n_test=args.test, max_attempts=args.max_attempts, oracle=oracle) for value in args.settings]
        runtime_identity = oracle.bridge.runtime_identity
        receipt = write_batch(episodes, args.out)
        receipt.update({"command": [sys.executable] + sys.argv, "cwd": str(Path.cwd()),
                        "racket_evaluations": oracle.evaluations, "runtime_identity": runtime_identity,
                        "source_hashes": source_hashes(),
                        "pair_counts": [{"public_id": public_challenge_id(ep), "train": len(ep["train"]), "test": len(ep["test"])}
                                        for ep in sorted(episodes, key=public_challenge_id)]})
        (args.out / "private/export.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "proposed", "episodes": receipt["episodes"],
                      "public_ids": receipt["public_ids"], "racket_evaluations": receipt["racket_evaluations"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
