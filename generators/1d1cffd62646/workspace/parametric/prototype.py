"""Proposed concentric-square ring stride, separate from canonical production.

Run with the packet's ``review.py run``. Default stride 1 is the byte-exact
canonical program; stride 2 retains the center and odd-numbered square rings.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

from reviewer_support import (canonical_path, find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)

TASK_ID = "1d1cffd62646"
PARENT_TASK_ID = "training:5c2c9af4"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
STRIDES = (1, 2)
SCHEMA = "three-dot-ring-stride-prototype-v1"
MODIFIERS = ("first-center", "last-center", "fixed-step-2", "fixed-step-3",
             "fixed-step-4", "fixed-step-5", "fixed-step-6", "manhattan",
             "first-ring-only", "whole-squares-only")
RIVALS = tuple(name for stride in STRIDES for name in
               (f"stride-{stride}", *(f"stride-{stride}/{m}" for m in MODIFIERS)))


def _bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            + "\n").encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _stride(value):
    return _integer(value, "ring_stride", 1, 2)


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
            type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def _geometry(grid):
    _grid(grid)
    dots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    if len(dots) != 3 or len({grid[r][c] for r, c in dots}) != 1:
        raise ValueError("input requires exactly three same-color dots")
    first, center, last = dots
    dr, dc = center[0] - first[0], center[1] - first[1]
    if (last != (center[0] + dr, center[1] + dc) or
            not (dr == 0 or dc == 0 or abs(dr) == abs(dc))):
        raise ValueError("dots must be equally spaced on a row, column, or diagonal")
    step = max(abs(dr), abs(dc))
    _integer(step, "dot step", 2, 6)
    return dots, center, step, grid[center[0]][center[1]]


def materialize_program(ring_stride=1):
    """Return exact default bytes or the one guarded ring-index substitution."""
    stride = _stride(ring_stride)
    program = (HERE / "canonical.rkt").read_text(encoding="utf-8")
    if stride == 1:
        return program
    target = "(range 0 (+ max-k 2))"
    if program.count(target) != 1:
        raise ValueError("canonical ring enumeration changed; review the variant")
    selected = "(filter (lambda (k) (or (= k 0) (= (mod k 2) 1))) " + target + ")"
    return program.replace(target, selected)


def _render(grid, stride, *, center=None, step=None, metric="chebyshev", mode="all"):
    dots, actual_center, actual_step, color = _geometry(grid)
    cr, cc = actual_center if center is None else center
    step = actual_step if step is None else step
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            dr, dc = abs(r - cr), abs(c - cc)
            radius = dr + dc if metric == "manhattan" else max(dr, dc)
            k, remainder = divmod(radius, step)
            if remainder or (k != 0 and (k - 1) % stride):
                continue
            if mode == "first" and k > 1:
                continue
            if mode == "whole" and not (0 <= cr - radius and cr + radius < h and
                                        0 <= cc - radius and cc + radius < w):
                continue
            result[r][c] = color
    return result


def transform(grid, *, ring_stride=1):
    """Independent distance-based mirror; exported labels come from Racket."""
    return _render(grid, _stride(ring_stride))


def _predict(grid, hypothesis):
    name, _, modifier = hypothesis.partition("/")
    stride = int(name.removeprefix("stride-"))
    dots, center, step, color = _geometry(grid)
    if modifier == "first-center":
        return _render(grid, stride, center=dots[0])
    if modifier == "last-center":
        return _render(grid, stride, center=dots[2])
    if modifier.startswith("fixed-step-"):
        return _render(grid, stride, step=int(modifier.removeprefix("fixed-step-")))
    if modifier == "manhattan":
        return _render(grid, stride, metric="manhattan")
    if modifier == "first-ring-only":
        return _render(grid, stride, mode="first")
    if modifier == "whole-squares-only":
        return _render(grid, stride, mode="whole")
    if modifier:
        raise ValueError("unknown hypothesis")
    return transform(grid, ring_stride=stride)


def lesson_certificate(episode):
    """Use only demonstration labels and query inputs, never hidden settings/answers.

    This is a finite declared-rival certificate, not universal rule uniqueness.
    Extra shortcuts are Python hypotheses; both parameter programs are also
    checked through Racket by generation/replay tests.
    """
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or type(test) is not list or not train or not test:
        raise ValueError("certificate needs nonempty train/test lists")
    for pair in train:
        _geometry(pair["input"])
        _grid(pair["output"])
    for pair in test:
        _geometry(pair["input"])
    survivors = [name for name in RIVALS if all(_predict(p["input"], name) == p["output"]
                                               for p in train)]
    queries = []
    for index, pair in enumerate(test):
        predictions = sorted({_sha(_bytes(_predict(pair["input"], name))) for name in survivors})
        queries.append({"index": index, "identifiable": len(predictions) == 1,
                        "prediction_sha256s": predictions})
    return {"rival_count": len(RIVALS), "survivors": survivors,
            "identifiable": bool(survivors) and all(q["identifiable"] for q in queries),
            "queries": queries}


def _draw_input(seed, index, profile):
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    height, width, step, orientation = profile
    return generator.generate(seed, index, grid_h=height, grid_w=width, step=step,
                              orientation=orientation)


def sample_inputs(seed, *, n_demo=2, n_query=4):
    """Setting-neutral, bounded draws; no duplicate pairs or short episodes."""
    _integer(seed, "seed", 0, 2**63 - 1)
    _integer(n_demo, "n_demo", 2, 8)
    _integer(n_query, "n_query", 1, 8)
    input_seed = int.from_bytes(hashlib.sha256(f"three-dot-input-v1:{seed}".encode()).digest()[:8], "big")
    demo_profiles = ((13, 17, 2, "diag_down"), (17, 13, 3, "horizontal"),
                     (21, 21, 4, "diag_up"), (19, 23, 5, "vertical"))
    query_profiles = ((21, 27, 4, "diag_up"), (30, 30, 5, "vertical"),
                      (27, 18, 6, "diag_down"), (19, 30, 2, "horizontal"))
    # Try complete lessons so the acceptance rule is identical for both settings.
    for attempt in range(64):
        demos, queries, seen = [], [], set()
        for i in range(n_demo + n_query):
            demo = i < n_demo
            profiles = demo_profiles if demo else query_profiles
            profile = profiles[(i if demo else i - n_demo) % len(profiles)]
            grid = _draw_input(input_seed, attempt * (n_demo + n_query) + i, profile)
            _geometry(grid)
            identity = _bytes(grid)
            if identity in seen:
                break
            seen.add(identity)
            (demos if demo else queries).append(grid)
        if len(demos) != n_demo or len(queries) != n_query:
            continue
        for stride in STRIDES:
            lesson = {"train": [{"input": g, "output": transform(g, ring_stride=stride)} for g in demos],
                      "test": [{"input": g} for g in queries]}
            proof = lesson_certificate(lesson)
            if not proof["identifiable"] or proof["survivors"] != [f"stride-{stride}"]:
                break
        else:
            return demos, queries
    raise RuntimeError("bounded lesson sampler exhausted; no partial episode returned")


def racket_label(bridge, program, grid):
    from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
    _geometry(grid)
    body = strip_rule_wrapper(strip_line_comments(program))
    if not body.lstrip().startswith("(lambda"):
        raise ValueError("reference must be a self-contained Racket lambda")
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    value = bridge.eval_text(f"({body} {literal})")
    _grid(value)
    return value


def source_bindings():
    paths = {"prototype": Path(__file__).resolve(), "canonical_resource": HERE / "canonical.rkt",
             "generator": ROOT / "generators" / TASK_ID / "generator.py",
             "canonical_ledger": canonical_path(ROOT)}
    return {name: {"path": str(path.relative_to(ROOT)), "sha256": _sha(path.read_bytes())}
            for name, path in paths.items()}


def generate_episode(seed, *, ring_stride=1, n_demo=2, n_query=4, bridge=None):
    stride = _stride(ring_stride)
    demos, queries = sample_inputs(seed, n_demo=n_demo, n_query=n_query)
    if bridge is None:
        from arc_repl.racket_bridge import RacketBridge
        with RacketBridge(timeout=10) as owned:
            return _label_episode(seed, stride, demos, queries, owned)
    return _label_episode(seed, stride, demos, queries, bridge)


def _label_episode(seed, stride, demos, queries, bridge):
    program = materialize_program(stride)
    episode = {"schema": SCHEMA, "task_id": TASK_ID, "parent_task_id": PARENT_TASK_ID,
               "status": "proposed", "training_admitted": False, "seed": seed,
               "parameters": {"ring_stride": stride}, "program": program,
               "program_sha256": _sha(program.encode()), "source_bindings": source_bindings(),
               "label_basis": "executed_matching_racket", "train": [], "test": []}
    for role, grids in (("train", demos), ("test", queries)):
        for grid in grids:
            actual = racket_label(bridge, program, grid)
            if actual != transform(grid, ring_stride=stride):
                raise ValueError("Racket/Python disagreement; episode not emitted")
            episode[role].append({"input": grid, "output": actual})
    episode["certificate"] = lesson_certificate(episode)
    return episode


def verify_episode(episode, *, bridge=None):
    """Recompute structure, Python labels and proof; Racket replay is explicit."""
    if episode.get("schema") != SCHEMA or episode.get("task_id") != TASK_ID:
        raise ValueError("unknown episode schema/task")
    if (episode.get("status") != "proposed" or episode.get("training_admitted") is not False
            or episode.get("parent_task_id") != PARENT_TASK_ID):
        raise ValueError("prototype lineage/admission fields changed")
    params = episode.get("parameters")
    if type(params) is not dict or set(params) != {"ring_stride"}:
        raise ValueError("parameters must contain exactly ring_stride")
    stride = _stride(params["ring_stride"])
    _integer(episode.get("seed"), "seed", 0, 2**63 - 1)
    program = materialize_program(stride)
    if episode.get("program") != program or episode.get("program_sha256") != _sha(program.encode()):
        raise ValueError("stored program does not match its selected parameter")
    if episode.get("source_bindings") != source_bindings():
        raise ValueError("source bindings are stale or changed")
    if type(episode.get("train")) is not list or type(episode.get("test")) is not list:
        raise ValueError("train/test must be lists")
    _integer(len(episode["train"]), "n_demo", 2, 8)
    _integer(len(episode["test"]), "n_query", 1, 8)
    pairs = episode["train"] + episode["test"]
    seen = set()
    for pair in pairs:
        grid, output = pair["input"], pair["output"]
        _geometry(grid)
        _grid(output)
        identity = _bytes(grid)
        if identity in seen:
            raise ValueError("duplicate input within an episode")
        seen.add(identity)
        if output != transform(grid, ring_stride=stride):
            raise ValueError("stored output differs from the selected rule")
        if bridge is not None:
            # Replay both lawful parameter interpretations, including all queries.
            for alternative in STRIDES:
                label = racket_label(bridge, materialize_program(alternative), grid)
                if label != transform(grid, ring_stride=alternative):
                    raise ValueError("Racket/parameter mirror disagreement")
                if alternative == stride and label != output:
                    raise ValueError("stored output differs from executed Racket")
    proof = lesson_certificate(episode)
    if (not proof["identifiable"] or proof["survivors"] != [f"stride-{stride}"]
            or episode.get("certificate") != proof):
        raise ValueError("demonstrations/certificate do not establish every query")
    return {"pairs": len(pairs), "demos": len(episode["train"]), "queries": len(episode["test"]),
            "racket_parameter_replays": len(pairs) * len(STRIDES) if bridge is not None else 0,
            "certificate": proof}


def write_batch(episodes, out):
    """Validate first; public IDs hash only the exact visible bytes written."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    if type(episodes) is not list or not episodes:
        raise ValueError("batch must contain episodes")
    prepared, seen = [], set()
    for episode in episodes:
        verify_episode(episode)
        payload = public_challenge_bytes(episode)
        identity = public_challenge_id(episode)
        if identity in seen:
            raise ValueError("duplicate visible challenge in batch")
        seen.add(identity)
        prepared.append((identity, payload, copy.deepcopy(episode)))
    prepared.sort(key=lambda row: row[0])
    private_rows, files = [], []
    for identity, payload, episode in prepared:
        path = f"public/{identity}.json"
        private_rows.append({"public_id": identity, "episode": episode})
        files.append({"public_id": identity, "public_path": path, "sha256": _sha(payload)})
    # Private annotations may contain unsupported JSON values. Serialize every
    # payload before creating any directory, so such failures are retryable.
    private = b"".join(_bytes(row) for row in private_rows)
    manifest = {"schema": SCHEMA + "-batch", "status": "proposed", "training_admitted": False,
                "files": files, "private_path": "private/episodes.jsonl",
                "private_sha256": _sha(private), "source_bindings": source_bindings()}
    manifest_bytes = _bytes(manifest)
    out.mkdir(parents=True)
    (out / "public").mkdir()
    (out / "private").mkdir()
    for identity, payload, episode in prepared:
        (out / f"public/{identity}.json").write_bytes(payload)
    (out / "private/episodes.jsonl").write_bytes(private)
    (out / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def verify_batch(out, *, bridge=None):
    out = Path(out)
    manifest = json.loads((out / "manifest.json").read_bytes())
    if (manifest.get("schema") != SCHEMA + "-batch" or manifest.get("private_path") != "private/episodes.jsonl"
            or manifest.get("status") != "proposed" or manifest.get("training_admitted") is not False
            or manifest.get("source_bindings") != source_bindings()):
        raise ValueError("invalid/stale batch manifest")
    private = (out / "private/episodes.jsonl").read_bytes()
    if _sha(private) != manifest.get("private_sha256"):
        raise ValueError("private file hash mismatch")
    rows = [json.loads(line) for line in private.splitlines()]
    files = manifest.get("files")
    if type(files) is not list or not files or len(files) != len(rows):
        raise ValueError("private/public row count mismatch")
    identities, reports = [], []
    for row, record in zip(rows, files):
        identity = record.get("public_id", "")
        if not re.fullmatch(r"[0-9a-f]{64}", identity) or record.get("public_path") != f"public/{identity}.json":
            raise ValueError("invalid public path/ID")
        if identity in identities or row.get("public_id") != identity:
            raise ValueError("duplicate or mismatched public identity")
        identities.append(identity)
        payload = (out / record["public_path"]).read_bytes()
        if (_sha(payload) != identity or record.get("sha256") != identity
                or public_challenge_bytes(row["episode"]) != payload):
            raise ValueError("public bytes/hash/projection mismatch")
        reports.append(verify_episode(row["episode"], bridge=bridge))
    if identities != sorted(identities):
        raise ValueError("public rows must be sorted by visible ID")
    if sorted(p.name for p in (out / "public").iterdir()) != sorted(f"{i}.json" for i in identities):
        raise ValueError("unexpected public files")
    return {"episodes": len(rows), "pairs": sum(r["pairs"] for r in reports),
            "queries": sum(r["queries"] for r in reports),
            "racket_parameter_replays": sum(r["racket_parameter_replays"] for r in reports),
            "reports": reports}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--seed", type=int, default=17)
    build.add_argument("--demos", type=int, default=2)
    build.add_argument("--queries", type=int, default=4)
    build.add_argument("--ring-stride", type=int, choices=STRIDES)
    build.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=10) as bridge:
        if args.command == "build":
            settings = STRIDES if args.ring_stride is None else (args.ring_stride,)
            episodes = [generate_episode(args.seed, ring_stride=s, n_demo=args.demos,
                                         n_query=args.queries, bridge=bridge) for s in settings]
            write_batch(episodes, args.out)
            report = {"episodes": len(episodes), "demos_per_episode": args.demos,
                      "queries_per_episode": args.queries,
                      "racket_labels": len(episodes) * (args.demos + args.queries),
                      "status": "proposed", "training_admitted": False}
        else:
            report = verify_batch(args.out, bridge=bridge)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
