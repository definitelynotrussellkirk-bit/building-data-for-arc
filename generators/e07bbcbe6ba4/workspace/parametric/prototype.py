#!/usr/bin/env python3
"""Task-local distance/origin family. All labels execute protected Racket.

The exact canonical default is retained. Optional nearest-wall reflection moves
the marker before the fill reads the intermediate grid. Native acceptance and
training admission remain separate from this authoring tool.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper, wrap_rule
from reviewer_support import (canonical_pairs, canonical_path, find_root,
    normalize_grid, public_challenge_bytes, public_challenge_id)

TASK_ID = "e07bbcbe6ba4"
VERSION = "distance-origin-v2"
ALLOWED_DISTANCE_METRICS = ("chebyshev", "manhattan")
ALLOWED_ORIGIN_MODES = ("marker", "nearest_wall_reflection")
DEFAULT_DISTANCE_METRIC = "chebyshev"
DEFAULT_SETTINGS = {"distance_metric": "chebyshev", "origin_mode": "marker"}
CANONICAL_RULE_HASH = "6c9f49f37571"
CANONICAL_SHA256 = "037ff6659c65492403f63da021ff422d16b36719afed937502aaf70fa93d8d02"
CHEBYSHEV_SITE = "(let ((d (max (abs (- r mr)) (abs (- c mc)))))"
MANHATTAN_SITE = "(let ((d (+ (abs (- r mr)) (abs (- c mc)))))"
SEQUENTIAL_DEPENDENCY = {
    "step_a": "Find the unique nearest frame wall and reflect the marker across the frame midpoint in that wall's axis.",
    "intermediate": "A grid with the old interior marker cleared and a new interior marker at the reflected coordinate.",
    "step_b": "Re-detect the interior marker in the intermediate grid and fill zero cells by the chosen distance parity.",
    "why_b_depends_on_a": "The selected wall and new origin depend on this input's frame and marker; using the old or wrong-axis origin changes ordinary painted cells, not just the marker.",
}


def _sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid):
    return _sha256(_stable_json(grid))


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be a literal integer in {lo}..{hi}")
    return value


def _validate_seed(seed):
    _integer(seed, 0, 2**63 - 1, "seed")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != set(DEFAULT_SETTINGS):
        raise ValueError("settings must name exactly distance_metric and origin_mode")
    for key, options in (("distance_metric", ALLOWED_DISTANCE_METRICS),
                         ("origin_mode", ALLOWED_ORIGIN_MODES)):
        if type(settings[key]) is not str or settings[key] not in options:
            raise ValueError(f"unsupported {key}: {settings[key]!r}")
    return dict(settings)


def all_settings():
    return [dict(zip(DEFAULT_SETTINGS, values)) for values in itertools.product(
        ALLOWED_DISTANCE_METRICS, ALLOWED_ORIGIN_MODES)]


def setting_id(settings):
    return settings["distance_metric"] + "-" + settings["origin_mode"]


def parameters_for_seed(seed):
    _validate_seed(seed)
    return dict(random.Random(f"{TASK_ID}:settings:{seed}").choice(all_settings()))


def first_seed_for_metric(distance_metric):
    if distance_metric not in ALLOWED_DISTANCE_METRICS:
        raise ValueError("unknown distance metric")
    return next(seed for seed in range(10000) if parameters_for_seed(seed) == {
        "distance_metric": distance_metric, "origin_mode": "marker"})


def _check_canonical_source(source):
    if type(source) is not str or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(CHEBYSHEV_SITE) != 1 or MANHATTAN_SITE in source:
        raise ValueError("canonical source must contain one guarded distance site")
    return source


def canonical_source(*, root=None):
    root = find_root(__file__) if root is None else Path(root)
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                    sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected one canonical program, found {len(sources)}")
    return _check_canonical_source(sources.pop())


def marker_move_program(mode="nearest_wall_reflection"):
    """Private preprocessing and audit variants, total on admitted inputs."""
    selectors = {
        "nearest_wall_reflection": "(or (= nearest north) (= nearest south))",
        "farthest_wall_reflection": "(or (= farthest north) (= farthest south))",
        "row_reflection": "#t", "column_reflection": "#f", "both_reflection": "#t",
    }
    if mode not in selectors:
        raise ValueError("unknown marker movement")
    col = "(- (+ gc1 gc2) mc)" if mode == "both_reflection" else "(if vertical mc (- (+ gc1 gc2) mc))"
    return f"""(rule! (lambda (g)
      (let* ((greens (find-color g 3)) (bb (bbox-of-cells greens))
             (gr1 (first bb)) (gc1 (second bb)) (gr2 (third bb)) (gc2 (fourth bb))
             (markers (filter (lambda (p) (and (> (first p) gr1) (< (first p) gr2)
                        (> (second p) gc1) (< (second p) gc2))) greens))
             (mr (first (first markers))) (mc (second (first markers)))
             (north (- mr gr1)) (south (- gr2 mr)) (west (- mc gc1)) (east (- gc2 mc))
             (nearest (min north south west east)) (farthest (max north south west east))
             (vertical {selectors[mode]})
             (nr (if vertical (- (+ gr1 gr2) mr) mr)) (nc {col}))
        (cellmap g (r c v)
          (cond ((and (= r nr) (= c nc)) 3)
                ((and (= r mr) (= c mc)) 0) (else v))))))"""


def _compose(base, mode):
    if mode == "marker":
        return base
    return "(rule! (lambda (g) (" + strip_rule_wrapper(base) + " (" + strip_rule_wrapper(
        marker_move_program(mode)) + " g))))"


def materialize_rule(distance_metric=DEFAULT_DISTANCE_METRIC, *, origin_mode="marker", root=None, source=None):
    validate_settings({"distance_metric": distance_metric, "origin_mode": origin_mode})
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    base = canonical if distance_metric == "chebyshev" else canonical.replace(CHEBYSHEV_SITE, MANHATTAN_SITE, 1)
    return _compose(base, origin_mode)


def rule_callable(source):
    return wrap_rule(source)


def _grid_literal(grid):
    # normalize_grid alone coerces bools; this shared validator is strict.
    public_challenge_bytes({"train": [{"input": grid, "output": grid}], "test": [{"input": grid}]})
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def execute_rule(source, grid, *, bridge=None):
    if bridge is None:
        with RacketBridge() as owned:
            return execute_rule(source, grid, bridge=owned)
    return normalize_grid(bridge.eval_text(f"({rule_callable(source)} {_grid_literal(grid)})"))


def _frame_fixture(fixture_id, *, height, width, top, left, frame_h, frame_w, marker):
    bottom, right = top + frame_h - 1, left + frame_w - 1
    if not (0 < top < bottom < height - 1 and 0 < left < right < width - 1):
        raise ValueError("frame must have an exterior margin")
    mr, mc = marker
    if not (top < mr < bottom and left < mc < right):
        raise ValueError("marker must be strictly inside frame")
    grid = [[0] * width for _ in range(height)]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r in (top, bottom) or c in (left, right):
                grid[r][c] = 3
    grid[mr][mc] = 3
    return {"fixture_id": fixture_id, "input": grid, "input_sha256": grid_sha256(grid),
            "geometry": {"grid_h": height, "grid_w": width, "frame_h": frame_h,
                         "frame_w": frame_w, "marker": [mr, mc]}}


def fixtures():
    """Small independent witnesses retained for replay, never the sampler."""
    return [
        _frame_fixture("vertical", height=11, width=12, top=1, left=1,
                       frame_h=8, frame_w=9, marker=(2, 4)),
        _frame_fixture("horizontal", height=15, width=13, top=2, left=2,
                       frame_h=11, frame_w=8, marker=(5, 4)),
        _frame_fixture("vertical_again", height=14, width=15, top=2, left=2,
                       frame_h=10, frame_w=11, marker=(4, 6)),
    ]


def geometry(grid):
    green = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    top, bottom = min(r for r, _ in green), max(r for r, _ in green)
    left, right = min(c for _, c in green), max(c for _, c in green)
    markers = [(r, c) for r, c in green if top < r < bottom and left < c < right]
    if len(markers) != 1:
        raise ValueError("expected one interior marker")
    mr, mc = markers[0]
    distances = [mr - top, bottom - mr, mc - left, right - mc]
    nearest = min(distances)
    if distances.count(nearest) != 1:
        raise ValueError("the admitted grammar requires a unique nearest wall")
    axis = distances.index(nearest) // 2
    reflected = [top + bottom - mr, mc] if axis == 0 else [mr, left + right - mc]
    return {"bbox": [top, left, bottom, right], "marker": [mr, mc],
            "wall_distances_n_s_w_e": distances, "nearest_axis": axis,
            "reflected_marker": reflected}


def _rng(seed, role, index):
    return random.Random(f"{TASK_ID}:inputs-v2:{seed}:{role}:{index}")


def _draw_fixture(seed, role, index):
    rng = _rng(seed, role, index)
    # Two constructive demos expose both axes and opposite parity under both
    # origins. Keep bbox-center phases equal: otherwise a center-origin
    # checkerboard can accidentally match both opposite marker phases.
    # The long second frame also refutes distance caps 4 and 8.
    center_phase = random.Random(f"{TASK_ID}:center-phase:{seed}").randrange(2)
    if role == "demo" and index == 0:
        fh, fw = rng.choice([(h, w) for h in (8, 10) for w in (9, 11)
                             if ((h - 1) // 2 + (w - 1) // 2) % 2 == center_phase])
        h, w = fh + 3, fw + 3
    elif role == "demo" and index == 1:
        fh, fw = rng.choice([(h, w) for h in (15, 17) for w in (8, 10)
                             if ((h - 1) // 2 + (w - 1) // 2) % 2 == center_phase])
        h, w = fh + 3, fw + 4
    elif role == "demo":
        h, w, fh, fw = ((15, 15, 11, 11), (16, 20, 12, 16),
                        (20, 16, 16, 12), (23, 25, 19, 21))[index - 2]
    else:
        h, w, fh, fw = ((9, 9, 7, 7), (21, 23, 17, 19),
                        (25, 27, 21, 23), (30, 30, 24, 24))[index]
    origins = [(r, c) for r in range(1, h - fh) for c in range(1, w - fw)]
    if role == "demo" and index < 2:
        origins = [(r, c) for r, c in origins if (r + c) % 2 == 0]
    top, left = rng.choice(origins)
    candidates = []
    phase = (random.Random(f"{TASK_ID}:phase:{seed}").randrange(2) + index) % 2
    for rr in range(1, fh - 1):
        for cc in range(1, fw - 1):
            ds = [rr, fh - 1 - rr, cc, fw - 1 - cc]
            if ds.count(min(ds)) != 1:
                continue
            axis = ds.index(min(ds)) // 2
            if role == "demo" and index < 2:
                if axis != index or (top + rr + left + cc) % 2 != phase:
                    continue
                if 2 * rr == fh - 1 or 2 * cc == fw - 1:
                    continue
                if index == 0 and min(ds) != 1:
                    continue
                if index == 1 and not (min(ds) == 2 and rr in (3, fh - 4)
                                      and max(ds[:2]) > max(ds[2:])):
                    continue
            elif min(ds) != (1 if (seed + index) % 2 == 0 else 2):
                continue
            candidates.append((top + rr, left + cc))
    if not candidates:
        raise RuntimeError("constructive marker constraints have no solution")
    return _frame_fixture(f"{role}-{index}", height=h, width=w, top=top, left=left,
                          frame_h=fh, frame_w=fw, marker=rng.choice(candidates))


def sample_inputs(seed, demos=3, queries=4):
    _validate_seed(seed)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    return ([_draw_fixture(seed, "demo", i) for i in range(demos)],
            [_draw_fixture(seed, "query", i) for i in range(queries)])


def rival_programs(settings, *, source):
    settings = validate_settings(settings)
    metric, origin = settings["distance_metric"], settings["origin_mode"]
    rivals = {"setting:" + setting_id(s): materialize_rule(s["distance_metric"],
              origin_mode=s["origin_mode"], source=source)
              for s in all_settings() if s != settings}
    base = materialize_rule(metric, source=source)
    centered = base.replace("(mr (first (first markers)))", "(mr (quotient (+ gr1 gr2) 2))").replace(
        "(mc (second (first markers)))", "(mc (quotient (+ gc1 gc2) 2))")
    rivals["frame_center"] = _compose(centered, origin)
    for mode in ("row_reflection", "column_reflection", "both_reflection", "farthest_wall_reflection"):
        rivals[mode] = _compose(base, mode)
    selected = _compose(base, origin)
    rivals["fixed_canonical_bbox"] = f"""(rule! (lambda (g)
        (let ((bb (bbox-of-cells (find-color g 3))))
          (if (equal? bb '(2 3 10 11)) ({strip_rule_wrapper(selected)} g) g))))"""
    site = CHEBYSHEV_SITE if metric == "chebyshev" else MANHATTAN_SITE
    for phase in (0, 1):
        fixed = base.replace(site, f"(let ((d (+ (- r gr1) (- c gc1) {phase})))")
        rivals[f"fixed_bbox_phase_{phase}"] = _compose(fixed, origin)
    for cap in (4, 8):
        capped = base.replace(site, site.replace("((d (", f"((d (min {cap} (") + ")")
        rivals[f"distance_cap_{cap}"] = _compose(capped, origin)
    return rivals


def teaching_check(train, settings, *, source, bridge):
    checks = {}
    for name, program in rival_programs(settings, source=source).items():
        refutations = [i for i, pair in enumerate(train)
                       if execute_rule(program, pair["input"], bridge=bridge) != pair["output"]]
        checks[name] = {"program_sha256": _sha256(program), "refuting_demo_indices": refutations,
                        "refuted_by_demo": bool(refutations)}
    survivors = [name for name, check in checks.items() if not check["refuted_by_demo"]]
    return {"passed": not survivors, "surviving_wrong_rules": survivors, "rivals": checks,
            "basis": "demonstrations only; finite declared rivals, not universal uniqueness",
            "distinguishing_demo_indices": sorted({i for c in checks.values() for i in c["refuting_demo_indices"]})}


def make_episode(seed, *, settings=None, demos=3, queries=4, root=None, bridge=None):
    demo_rows, query_rows = sample_inputs(seed, demos, queries)
    settings = parameters_for_seed(seed) if settings is None else validate_settings(settings)
    if bridge is None:
        with RacketBridge() as owned:
            return make_episode(seed, settings=settings, demos=demos, queries=queries, root=root, bridge=owned)
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        raise RuntimeError("live protected Racket is required")
    canonical = canonical_source(root=root)
    program = materialize_rule(settings["distance_metric"], origin_mode=settings["origin_mode"], source=canonical)
    train = [{"input": row["input"], "output": execute_rule(program, row["input"], bridge=bridge)} for row in demo_rows]
    teaching = teaching_check(train, settings, source=canonical, bridge=bridge)
    if not teaching["passed"]:
        raise ValueError("underidentified demonstrations: " + ", ".join(teaching["surviving_wrong_rules"]))
    test = [{"input": row["input"], "output": execute_rule(program, row["input"], bridge=bridge)} for row in query_rows]
    hashes = [grid_sha256(p["input"]) for p in train + test]
    if len(set(hashes)) != len(hashes):
        raise ValueError("duplicate lesson input")
    return {"schema": "e07bbcbe6ba4-parametric-episode-v2", "prototype_status": "proposed",
            "task_id": TASK_ID, "version": VERSION, "seed": seed, "parameters": settings,
            "program_solution": program, "selected_rule_sha256": _sha256(program),
            "train": train, "test": test, "identifiability": teaching,
            "geometry": [geometry(p["input"]) for p in train + test],
            "racket": {k: identity[k] for k in ("backend", "protected", "binary_sha256", "prelude_sha256")},
            "private_pairs": [{**pair, **settings, "input_sha256": hashes[i]}
                              for i, pair in enumerate(train + test)]}


def public_challenge(episode, query_index=0):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    visible = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(visible))


def _write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_public_queries(episode, directory):
    """One opaque file per turn; ordering and association stay controller-side."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    pending = []
    for index in range(len(episode["test"])):
        public = public_challenge(episode, index)
        identity = public_challenge_id(public)
        pending.append((identity, index, public_challenge_bytes(public)))
    if len({item[0] for item in pending}) != len(pending):
        raise ValueError("duplicate public payload")
    if any((directory / (identity + ".json")).exists() for identity, _, _ in pending):
        raise FileExistsError("duplicate public challenge in batch")
    rows = []
    for identity, index, payload in sorted(pending):
        (directory / (identity + ".json")).write_bytes(payload)
        rows.append({"query_index": index, "public_id": identity, "public_path": "public/" + identity + ".json"})
    return sorted(rows, key=lambda row: row["query_index"])


def bounded_self_review(*, source, bridge):
    rows = fixtures()
    settings = {"distance_metric": "chebyshev", "origin_mode": "nearest_wall_reflection"}
    correct = materialize_rule("chebyshev", origin_mode=settings["origin_mode"], source=source)
    rival = _compose(materialize_rule("chebyshev", source=source), "row_reflection")
    cases = [{"input": rows[i]["input"], "output": execute_rule(correct, rows[i]["input"], bridge=bridge),
              "rival_output": execute_rule(rival, rows[i]["input"], bridge=bridge)} for i in (0, 2, 1)]
    assert all(c["output"] == c["rival_output"] for c in cases[:2])
    assert cases[2]["output"] != cases[2]["rival_output"]
    repaired = make_episode(17, settings=settings, demos=2, queries=4, bridge=bridge)
    return {"settings": settings, "program": correct, "rival_program": rival,
            "finding": "Two vertical-nearest demos admit always-reflect-row; the horizontal query differs.",
            "before": {"train": cases[:2], "query": cases[2]},
            "repair": "Construct one vertical and one horizontal demo without increasing demo count.",
            "after": {"seed": 17, "demos": 2, "queries": 4, "teaching": repaired["identifiability"]},
            "limit": "Only listed finite rivals tested; marker-phased Manhattan checkerboards are equivalent, not wrong."}


def write_witness(qualification, out, *, root=None):
    q = json.loads(Path(qualification).read_text())
    if (q.get("schema") != "arcpuzzles-parametric-qualification-v1"
            or q.get("task_id") != TASK_ID or q.get("status") != "qualified"):
        raise ValueError("a passing native qualification is required")
    source = canonical_source(root=root)
    cases = []
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        for metric in ALLOWED_DISTANCE_METRICS:
            settings = {"distance_metric": metric, "origin_mode": "nearest_wall_reflection"}
            program = materialize_rule(metric, origin_mode=settings["origin_mode"], source=source)
            if q.get("programs", {}).get(_stable_json(settings)) != _sha256(program):
                raise ValueError("witness program is not a qualified setting program")
            counterfactual = materialize_rule(metric, source=source)
            grid = fixtures()[0]["input"]
            output = execute_rule(program, grid, bridge=bridge)
            other = execute_rule(counterfactual, grid, bridge=bridge)
            moved = execute_rule(marker_move_program(), grid, bridge=bridge)
            g = geometry(grid)
            old, new = g["marker"], g["reflected_marker"]
            diffs = [[r, c] for r in range(len(grid)) for c in range(len(grid[0]))
                     if [r, c] not in (old, new) and output[r][c] != other[r][c]]
            if not diffs:
                raise ValueError("causal witness must change non-marker paint")
            cases.append({"input": grid, "settings": settings,
                          "intermediate_value": {**g, "grid": moved},
                          "program": program, "output": output, "counterfactual_program": counterfactual,
                          "counterfactual_output": other, "ablation": "skip_a",
                          "changed_non_marker_cells": len(diffs), "example_changed_cell": diffs[0]})
    witness = {"schema": "arcpuzzles-sequential-dependency-witness-v1", "source_binding": q["source_binding"],
               **SEQUENTIAL_DEPENDENCY, "racket": {"backend": identity["backend"], "protected": identity["protected"]},
               "cases": cases}
    _write_json(out, witness)
    return witness


def write_evidence(*, out, root=None):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    root = find_root(__file__) if root is None else Path(root)
    source = canonical_source(root=root)
    episodes, requests = [], []
    with RacketBridge() as bridge:
        for settings in all_settings():
            episode = make_episode(17, settings=settings, root=root, bridge=bridge)
            private = "private/" + setting_id(settings) + ".json"
            turns = write_public_queries(episode, out / "public")
            _write_json(out / private, episode)
            episodes.append({"settings": settings, "distance_metric": settings["distance_metric"],
                             "seed": 17, "private_path": private, "public_turns": turns,
                             "racket_sha256": episode["selected_rule_sha256"], "identifiability": episode["identifiability"]})
            requests.append({"settings": settings, "seed": 17, "demos": 3, "queries": 4, "status": "passed"})
            for demos, queries in ((2, 1), (6, 4)):
                boundary = make_episode(0, settings=settings, demos=demos, queries=queries, root=root, bridge=bridge)
                requests.append({"settings": settings, "seed": 0, "demos": demos, "queries": queries,
                                 "status": "passed", "input_hashes": [grid_sha256(p["input"]) for p in boundary["train"] + boundary["test"]]})
        canonical_checks = [execute_rule(source, pair["input"], bridge=bridge) == pair["output"]
                            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True)]
        if not canonical_checks or not all(canonical_checks):
            raise ValueError("canonical replay failed")
        review = bounded_self_review(source=source, bridge=bridge)
        _write_json(out / "private/self_review.json", review)
        identity = bridge.runtime_identity
    files = [{"path": p.relative_to(out).as_posix(), "sha256": _sha256(p.read_bytes()), "bytes": p.stat().st_size}
             for p in sorted(out.rglob("*")) if p.is_file()]
    report = {"schema": "e07bbcbe6ba4-parametric-report-v2", "status": "prototype", "task_id": TASK_ID,
              "version": VERSION, "approval": "owner_exact_source_acceptance_pending",
              "parameters": {"distance_metric": list(ALLOWED_DISTANCE_METRICS), "origin_mode": list(ALLOWED_ORIGIN_MODES)},
              "canonical_default": {"sha256": CANONICAL_SHA256, "labeled_pairs_checked": len(canonical_checks),
                                    "all_labeled_pairs_match": all(canonical_checks)},
              "episodes": episodes, "bounded_yield": {"attempted": len(requests), "succeeded": len(requests), "failed": 0,
                                                        "draw_retries": 0, "requests": requests},
              "racket": {k: identity[k] for k in ("backend", "protected", "binary_sha256", "prelude_sha256")},
              "distinguishing_witness": {"path": "private/self_review.json", "outputs_differ": True},
              "sequential_dependency": SEQUENTIAL_DEPENDENCY,
              "limits": ["Finite settings, seeds and declared rivals only; no universal induction or training claim.",
                         "Unique nearest-wall grammar; equal-distance ties excluded.",
                         "One frame and marker, 0/3 input colors; no distracting objects in canonical grammar.",
                         "Manhattan parity equals a marker-phased checkerboard."], "files": files}
    _write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build-evidence")
    build.add_argument("--out", type=Path, required=True)
    witness = commands.add_parser("write-witness")
    witness.add_argument("--qualification", type=Path, required=True)
    witness.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "build-evidence":
        report = write_evidence(out=args.out)
        print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                          "bounded_yield": {k: v for k, v in report["bounded_yield"].items() if k != "requests"},
                          "out": str(args.out)}, sort_keys=True))
    else:
        report = write_witness(args.qualification, args.out)
        print(json.dumps({"cases": len(report["cases"]), "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
