"""Proposed cells/bounding-box ranking; canonical generator is unchanged.

Use the adjacent adapter for protected native qualification, or this CLI for
Racket-labelled, separately projected authoring examples. Nothing here admits
variants or trajectories to training.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "8118155d8959"
SCHEMA = "blue-rank-metric-prototype-v1"
METRICS = ("cells", "bbox_area")
RIVALS = METRICS + ("descending_cells", "descending_bbox_area", "left_to_right",
                    "top_to_bottom", "identity", "erase_distractors_cells",
                    "erase_distractors_bbox_area", "bbox_then_cells",
                    "bbox_then_descending_cells", "bbox_column_first",
                    "bbox_reverse_row", "bbox_reverse_column")
QUERY_SHAPES = ((10, 12), (16, 20), (24, 24), (30, 30))
_spec = importlib.util.spec_from_file_location("_rank_metric_sampler_8118155d8959", HERE / "sampler.py")
_sampler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sampler)
sample_input = _sampler.sample_input


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def settings(metric):
    if type(metric) is not str or metric not in METRICS:
        raise ValueError("metric must be cells or bbox_area")
    return {"metric": metric}


def materialize_program(*, metric="cells"):
    settings(metric)
    canonical = (HERE / "canonical.rkt").read_text()
    if metric == "cells":
        return canonical
    for name in ("a", "b"):
        marker = f"(obj-size {name})"
        if canonical.count(marker) != 1:
            raise ValueError("canonical score site changed; explicit rule review required")
        score = (f"(let ((box (obj-bbox {name}))) "
                 "(* (+ 1 (- (third box) (first box))) "
                 "(+ 1 (- (fourth box) (second box)))))")
        canonical = canonical.replace(marker, score)
    return canonical


def grid_check(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid requires 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid):
        raise ValueError("grid requires rectangular rows and exact integer colors 0..9")
    return grid


def blue_objects(grid):
    grid_check(grid)
    if any(x not in (0, 1, 5, 6, 7, 9) for row in grid for x in row):
        raise ValueError("input palette must be a subset of 0,1,5,6,7,9")
    unseen = {(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x == 1}
    objects = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in unseen:
                    unseen.remove(q)
                    component.add(q)
                    stack.append(q)
        objects.append(tuple(sorted(component)))
    if len(objects) != 3:
        raise ValueError("input requires exactly three 4-connected blue objects")
    return objects


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def score(cells, metric):
    if metric == "cells":
        return len(cells)
    top, left, bottom, right = bbox(cells)
    return (bottom - top + 1) * (right - left + 1)


def predict(grid, rival):
    objects = blue_objects(grid)
    if rival not in RIVALS:
        raise ValueError("undeclared rival")
    result = copy.deepcopy(grid)
    if rival == "identity":
        return result
    if rival == "left_to_right":
        key = lambda obj: (bbox(obj)[1], bbox(obj)[0])
    elif rival == "top_to_bottom":
        key = lambda obj: bbox(obj)[:2]
    elif rival.startswith("bbox_") and rival != "bbox_area":
        def key(obj):
            top, left = bbox(obj)[:2]
            tie = {
                "bbox_then_cells": (len(obj), top, left),
                "bbox_then_descending_cells": (-len(obj), top, left),
                "bbox_column_first": (left, top),
                "bbox_reverse_row": (-top, left),
                "bbox_reverse_column": (top, -left),
            }[rival]
            return (score(obj, "bbox_area"), *tie)
    else:
        metric = "bbox_area" if rival.endswith("bbox_area") else "cells"
        sign = -1 if rival.startswith("descending_") else 1
        key = lambda obj: (sign * score(obj, metric), *bbox(obj)[:2])
    for obj, color in zip(sorted(objects, key=key), (2, 3, 8)):
        for r, c in obj:
            result[r][c] = color
    if rival.startswith("erase_distractors_"):
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value not in (0, 1):
                    result[r][c] = 0
    return result


def transform(grid, *, metric="cells"):
    settings(metric)
    return predict(grid, metric)


def _lookup_conflict(demos, *, morphology):
    table = {}
    for pair in demos:
        for obj in blue_objects(pair["input"]):
            key = min(_sampler.orient(obj, code) for code in range(8)) if morphology else len(obj)
            colors = {pair["output"][r][c] for r, c in obj}
            if len(colors) != 1:
                return True
            color = colors.pop()
            if key in table and table[key] != color:
                return True
            table[key] = color
    return False


def lesson_certificate(challenge):
    # Project FIRST: query answers and private settings cannot influence fitting.
    visible = json.loads(public_challenge_bytes(challenge))
    demos = visible["train"]
    for pair in demos:
        if (len(pair["input"]), len(pair["input"][0])) != (len(pair["output"]), len(pair["output"][0])):
            raise ValueError("demonstration input/output dimensions differ")
    survivors = [name for name in RIVALS
                 if all(predict(pair["input"], name) == pair["output"] for pair in demos)]
    agreement = []
    for pair in visible["test"]:
        blue_objects(pair["input"])
        outputs = [json_bytes(predict(pair["input"], name)) for name in survivors]
        agreement.append(bool(outputs) and len(set(outputs)) == 1)
    shape_conflict = _lookup_conflict(demos, morphology=True)
    size_conflict = _lookup_conflict(demos, morphology=False)
    identifiable = (len(survivors) == 1 and survivors[0] in METRICS
                    and all(agreement) and shape_conflict and size_conflict)
    return {"schema": "blue-rank-demo-certificate-v1", "survivors": survivors,
            "identifiable": identifiable, "query_agreement": agreement,
            "shape_lookup_refuted": shape_conflict, "size_lookup_refuted": size_conflict,
            "scope": "fourteen declared rules plus per-object size and D4-shape lookup; not universal uniqueness"}


def _teaching_inputs(seed):
    # Counterbalance both settings simultaneously; never condition inputs on the
    # chosen private setting. At most 32 spatial arrangements, not extra demos.
    for attempt in range(32):
        inputs = [_sampler.teaching_input(seed, i, attempt) for i in range(2)]
        if len({json_bytes(g) for g in inputs}) != 2:
            continue
        valid = True
        for metric in METRICS:
            pairs = [{"input": g, "output": transform(g, metric=metric)} for g in inputs]
            certificate = lesson_certificate({"train": pairs, "test": [{"input": inputs[0]}]})
            if certificate["survivors"] != [metric] or not certificate["identifiable"]:
                valid = False
                break
        if valid:
            return inputs, attempt + 1
    raise RuntimeError("teaching arrangement budget exhausted; no partial episode")


def sample_episode(seed, *, metric="cells", n_demo=3, n_query=4):
    """Python label claims for the native worker, which independently runs Racket."""
    _sampler.integer(seed, "seed", 0, 2**63 - 1)
    _sampler.integer(n_demo, "n_demo", 2, 6)
    _sampler.integer(n_query, "n_query", 1, 4)
    settings(metric)
    demos, attempts = _teaching_inputs(seed)
    demo_shapes = ((10, 12), (12, 16), (16, 14), (18, 18))
    for i in range(n_demo - 2):
        h, w = demo_shapes[i]
        demos.append(sample_input(seed, index=100 + i, height=h, width=w))
    queries = [sample_input(seed, index=200 + i, height=h, width=w)
               for i, (h, w) in enumerate(QUERY_SHAPES[:n_query])]
    inputs = demos + queries
    if len({json_bytes(g) for g in inputs}) != len(inputs):
        raise RuntimeError("duplicate input; no partial episode")
    episode = {"train": [{"input": g, "output": transform(g, metric=metric)} for g in demos],
               "test": [{"input": g, "output": transform(g, metric=metric)} for g in queries],
               "program_solution": materialize_program(metric=metric),
               "sampling": {"teaching_attempts": attempts, "teaching_limit": 32}}
    if not lesson_certificate(episode)["identifiable"]:
        raise RuntimeError("demonstrations do not identify selected rule; no episode emitted")
    return episode


def first_turn(episode):
    """Existing one-query consumer projection: no future inputs or count hints."""
    return json.loads(public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]}))


def source_bindings():
    paths = ("prototype.py", "sampler.py", "adapter.py", "promotion.json", "canonical.rkt")
    sources = {name: sha((HERE / name).read_bytes()) for name in paths}
    sources["../../generator.py"] = sha((HERE.parent.parent / "generator.py").read_bytes())
    return sources


def racket_label(bridge, program, grid):
    from puzzle_generators.rule_wrap import wrap_rule
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    result = bridge.eval_text(f"({wrap_rule(program)} {literal})")
    grid_check(result)
    return result


def runtime_identity(bridge):
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise ValueError("retained examples require protected live Racket execution")
    return {k: v for k, v in identity.items()
            if k in ("schema", "backend", "protected") or k.endswith("_sha256")}


def generate_episode(seed, *, metric="cells", n_demo=3, n_query=4, bridge=None):
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=15) as owned:
            return generate_episode(seed, metric=metric, n_demo=n_demo, n_query=n_query, bridge=owned)
    episode = sample_episode(seed, metric=metric, n_demo=n_demo, n_query=n_query)
    for pair in episode["train"] + episode["test"]:
        for candidate in METRICS:
            actual = racket_label(bridge, materialize_program(metric=candidate), pair["input"])
            if actual != transform(pair["input"], metric=candidate):
                raise ValueError("Racket/Python parameter prediction mismatch")
            if candidate == metric:
                pair["output"] = actual
    identity = runtime_identity(bridge)
    program = episode.pop("program_solution")
    episode.update(schema=SCHEMA, task_id=TASK_ID, status="proposed", training_admitted=False,
                   seed=seed, parameters=settings(metric), source_bindings=source_bindings(),
                   program=program, program_sha256=sha(program.encode()), racket=identity,
                   certificate=lesson_certificate(episode))
    return episode


def write_batch(episodes, out):
    """Atomic public/private writer. Semantic replay is verify_batch's job."""
    episodes = list(episodes)
    if not episodes:
        raise ValueError("empty batch")
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    payloads = {}
    for episode in episodes:
        raw = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in payloads:
            raise ValueError("duplicate public payload")
        payloads[public_id] = (raw, json_bytes(episode))
    index = {"schema": "public-challenge-batch-v1", "public_ids": sorted(payloads)}
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rank-stage-", dir=out.parent))
    try:
        (stage / "public").mkdir()
        (stage / "private").mkdir()
        for public_id in index["public_ids"]:
            public, private = payloads[public_id]
            (stage / "public" / (public_id + ".json")).write_bytes(public)
            (stage / "private" / (public_id + ".json")).write_bytes(private)
        (stage / "index.json").write_bytes(json_bytes(index))
        if out.exists() or out.is_symlink():
            raise FileExistsError(out)
        stage.rename(out)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return index


def verify_batch(out, *, bridge=None):
    """Check exact public bytes, source bindings, teaching and fresh Racket labels."""
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=15) as owned:
            return verify_batch(out, bridge=owned)
    out = Path(out)
    if out.is_symlink():
        raise ValueError("export cannot be a symlink")
    index = json.loads((out / "index.json").read_bytes())
    ids = index.get("public_ids")
    if (set(index) != {"schema", "public_ids"} or index.get("schema") != "public-challenge-batch-v1"
            or type(ids) is not list or not ids or any(type(i) is not str or len(i) != 64
                or any(c not in "0123456789abcdef" for c in i) for i in ids)
            or ids != sorted(set(ids))):
        raise ValueError("invalid public index")
    expected = {"index.json"} | {f"{kind}/{i}.json" for i in ids for kind in ("public", "private")}
    actual, directories = set(), set()
    for path in out.rglob("*"):
        if path.is_symlink():
            raise ValueError("export contains a symlink")
        if path.is_file():
            actual.add(path.relative_to(out).as_posix())
        elif path.is_dir():
            directories.add(path.relative_to(out).as_posix())
        else:
            raise ValueError("export contains a special file")
    if actual != expected or directories != {"public", "private"}:
        raise ValueError("export inventory differs from public index")
    pairs, queries, rows = 0, 0, []
    current_runtime = runtime_identity(bridge)
    for public_id in ids:
        raw = (out / "public" / (public_id + ".json")).read_bytes()
        episode = json.loads((out / "private" / (public_id + ".json")).read_bytes())
        if raw != public_challenge_bytes(episode) or sha(raw) != public_id:
            raise ValueError("public bytes or visible identity mismatch")
        if (episode.get("schema") != SCHEMA or episode.get("task_id") != TASK_ID
                or episode.get("status") != "proposed" or episode.get("training_admitted") is not False
                or episode.get("source_bindings") != source_bindings()):
            raise ValueError("private status or source binding mismatch")
        if episode.get("racket") != current_runtime:
            raise ValueError("stored Racket runtime identity differs from current protected backend")
        params = episode.get("parameters")
        if type(params) is not dict or set(params) != {"metric"}:
            raise ValueError("invalid private parameters")
        metric = params["metric"]
        settings(metric)
        _sampler.integer(episode.get("seed"), "seed", 0, 2**63 - 1)
        _sampler.integer(len(episode["train"]), "n_demo", 2, 6)
        _sampler.integer(len(episode["test"]), "n_query", 1, 4)
        program = materialize_program(metric=metric)
        if episode.get("program") != program or episode.get("program_sha256") != sha(program.encode()):
            raise ValueError("private program identity mismatch")
        all_pairs = episode["train"] + episode["test"]
        if len({json_bytes(p["input"]) for p in all_pairs}) != len(all_pairs):
            raise ValueError("duplicate input")
        for pair in all_pairs:
            grid_check(pair.get("output"))
        certificate = lesson_certificate(episode)
        if (json_bytes(episode.get("certificate")) != json_bytes(certificate)
                or certificate["survivors"] != [metric] or not certificate["identifiable"]):
            raise ValueError("invalid demonstration-only certificate")
        for pair in all_pairs:
            for candidate in METRICS:
                actual_label = racket_label(bridge, materialize_program(metric=candidate), pair["input"])
                if actual_label != transform(pair["input"], metric=candidate):
                    raise ValueError("Racket/Python prediction mismatch")
                if candidate == metric and actual_label != pair["output"]:
                    raise ValueError("stored label disagrees with Racket")
        pairs += len(all_pairs)
        queries += len(episode["test"])
        rows.append({"public_id": public_id, "parameters": params,
                     "demos": len(episode["train"]), "queries": len(episode["test"]),
                     "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                     "survivors": certificate["survivors"]})
    return {"status": "passed", "episodes": len(ids), "labeled_pairs": pairs,
            "queries": queries, "racket_parameter_replays": 2 * pairs,
            "source_bindings": source_bindings(), "rows": rows, "training_admitted": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--demos", type=int, default=3)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--metric", choices=("all", *METRICS), default="all")
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_batch(args.out), sort_keys=True))
        return 0
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=15) as bridge:
        metrics = METRICS if args.metric == "all" else (args.metric,)
        episodes = [generate_episode(args.seed, metric=metric, n_demo=args.demos,
                                     n_query=args.queries, bridge=bridge) for metric in metrics]
        write_batch(episodes, args.out)
        print(json.dumps(verify_batch(args.out, bridge=bridge), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
