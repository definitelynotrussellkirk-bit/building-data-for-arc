#!/usr/bin/env python3
"""Relocated Racket-backed census and counterfactual probe for this task.

From the packet root:
  python3 run_with_racket.py python3 generators/5da2f80a4a4f/workspace/review_probe.py \
    --out ../checks/probe --samples-per-band 256 --exhaustive --pytest

Add --baseline-generator PATH to compare a saved v4 source file. No installation,
network access, or predecessor checkout is needed. Output directories must be new.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

TASK = "5da2f80a4a4f"
BANDS = ("easy", "medium", "hard")
LOOKUP = {(6, 6): (2, 2), (10, 10): (2, 2), (8, 10): (3, 2), (10, 8): (2, 3)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def seed_for(label: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{TASK}:probe-v1:{label}".encode()).digest()[:8], "big")


def lookup_rule(analysis):
    rs, cs = LOOKUP.get((analysis["frame_h"], analysis["frame_w"]), (2, 2))
    interior = [[v for v in row for _ in range(cs)]
                for row in analysis["key_matrix"] for _ in range(rs)]
    border = [2] * (len(interior[0]) + 2)
    return [border[:]] + [[2, *row, 2] for row in interior] + [border[:]]


def scene(fh, fw, key, dr=0, dc=0, *, canvas=14, origin=(0, 0)):
    grid = [[0] * canvas for _ in range(canvas)]
    r0, c0 = origin
    for r in range(fh):
        for c in range(fw):
            if r in (0, fh - 1) or c in (0, fw - 1):
                grid[r0 + r][c0 + c] = 2
    for r, row in enumerate(key):
        for c, v in enumerate(row):
            grid[r0 + 1 + dr + r][c0 + 1 + dc + c] = v
    return grid


def worker(args) -> int:
    from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
    from puzzle_generators.rule_wrap import wrap_rule
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash

    current = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
    modules = {"after": current}
    if args.baseline_generator:
        spec = importlib.util.spec_from_file_location("review_baseline", args.baseline_generator)
        baseline = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(baseline)
        modules = {"before": baseline, **modules}
    out = args.out
    failures, witnesses, calls = [], {}, 0
    rule = canonical_rule_source(TASK)
    bridge, fn = _open_bridge_with_rule(wrap_rule(rule))

    def execute(grid):
        nonlocal calls
        calls += 1
        return _apply_rule(bridge, fn, grid)

    def require(condition, kind, **detail):
        if not condition:
            failures.append({"kind": kind, **detail})

    def checked(mod, grid, case):
        require(not mod.self_check(grid), "self_check", case=case, input=grid,
                reasons=mod.self_check(grid))
        actual = execute(grid)
        expected = mod.rule_mirror(grid)
        require(actual == expected, "mirror_racket_mismatch", case=case,
                input=grid, racket_output=actual, mirror_output=expected)
        return actual

    report = {"schema": "arcpuzzles-task-probe-v1", "task_id": TASK,
              "rule_hash": normalized_rule_hash(rule),
              "rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
              "samples_per_band": args.samples_per_band, "census": {}}
    try:
        pairs = canonical_pairs(TASK)
        report["canonical_pairs"] = len(pairs)
        for i, pair in enumerate(pairs):
            actual = checked(current, pair["input"], f"canonical:{i}")
            require(actual == pair["output"], "canonical_output", case=i,
                    expected=pair["output"], actual=actual)
            require(lookup_rule(current._analyze(pair["input"])) == actual,
                    "lookup_does_not_fit_canonical", case=i)
        for label, mod in modules.items():
            frame_keys, canvases = defaultdict(set), defaultdict(set)
            counters = {name: Counter() for name in ("profiles", "palettes", "scales", "frame_shapes", "rival_disagreements")}
            geometries, inputs, outputs = set(), set(), set()
            counts, supports = Counter(), Counter()
            for band in BANDS:
                for index in range(args.samples_per_band):
                    seed = seed_for(f"{band}:{index}")
                    case = {"version": label, "seed": seed, "sample_index": index, "difficulty": band}
                    grid = mod.generate(seed, index, difficulty=band)
                    actual = checked(mod, grid, case)
                    a = mod._analyze(grid)
                    geometry = tuple(a["geometry"])
                    frame = str((a["frame_h"], a["frame_w"]))
                    frame_keys[frame].add((a["key_h"], a["key_w"]))
                    canvases[str((a["height"], a["width"]))].add(geometry)
                    counters["profiles"][a["scene_profile"]] += 1
                    counters["palettes"][str(a["palette_size"])] += 1
                    counters["scales"][str((a["rscale"], a["cscale"]))] += 1
                    counters["frame_shapes"][frame] += 1
                    geometries.add(geometry)
                    inputs.add(json.dumps(grid))
                    outputs.add(json.dumps(actual))
                    counts[band] += 1
                    if (a["height"], a["width"], a["palette_size"]) == (14, 14, 4):
                        supports[band] += 1
                    rivals = dict(mod.SEMANTIC_RIVALS)
                    rivals["frame_size_scale_lookup"] = lambda g: lookup_rule(mod._analyze(g))
                    for name, rival in rivals.items():
                        if rival(grid) != actual:
                            counters["rival_disagreements"][name] += 1
                    if label == "after" and lookup_rule(a) != actual:
                        witness = {**case, "scene_profile": a["scene_profile"], "geometry": geometry,
                                   "input": grid, "racket_output": actual, "lookup_output": lookup_rule(a)}
                        witnesses.setdefault("first_lookup_counterexample", witness)
                        if (a["frame_h"], a["frame_w"]) in LOOKUP:
                            witnesses.setdefault("familiar_frame_counterexample", witness)
            report["census"][label] = {
                "version": mod.VERSION, "generator_sha256": digest(Path(mod.__file__)),
                "draws": sum(counts.values()), "draws_by_band": dict(counts),
                "unique_inputs": len(inputs), "unique_outputs": len(outputs),
                "unique_relative_geometries": len(geometries),
                "canonical_exact_profile_by_band": dict(supports),
                "key_shapes_by_frame": {k: sorted(v) for k, v in frame_keys.items()},
                "geometry_count_by_canvas": {k: len(v) for k, v in canvases.items()},
                **{k: dict(v) for k, v in counters.items()},
            }
        # Every offset, not just a Monte Carlo sample of key placements. One
        # seeded pattern per geometry/palette; this is NOT exhaustive over keys.
        exhaustive = 0
        if args.exhaustive:
            for profile, geometries in current._VARIABLE_GEOMETRIES.items():
                for fh, fw, kh, kw in geometries:
                    for n in (2, 3, 4):
                        key = current._pattern_for(profile, kh, kw, [1, 3, 4, 5][:n],
                                                   random.Random(seed_for(f"{profile}:{fh}:{fw}:{kh}:{kw}:{n}")))
                        reference = None
                        for dr in range(fh - 1 - kh):
                            for dc in range(fw - 1 - kw):
                                grid = scene(fh, fw, key, dr, dc)
                                case = {"profile": profile, "geometry": [fh, fw, kh, kw, dr, dc], "palette_size": n}
                                actual = checked(current, grid, case)
                                a = current._analyze(grid)
                                require(current.observe_overrides(grid)["scene_profile"] == profile,
                                        "profile_observation", case=case)
                                require(actual != lookup_rule(a), "control_fails_lookup", case=case, input=grid)
                                require(actual != current._rival_four_quadrants(grid),
                                        "control_fails_quadrants", case=case, input=grid)
                                if reference is None:
                                    reference = actual
                                require(actual == reference, "offset_changes_answer", case=case)
                                exhaustive += 1
        report["exhaustive_geometry_palette_offset_cases"] = exhaustive
        # Padding/translation, transpose, colour permutation: independent oracle
        # checks of intended invariances, not just the generator's self-report.
        metamorphic = 0
        for index in range(32):
            grid = current.generate(17000, index, difficulty="medium")
            answer = checked(current, grid, f"metamorphic:{index}:base")
            transposed = [list(row) for row in zip(*grid)]
            require(checked(current, transposed, f"transpose:{index}") == [list(row) for row in zip(*answer)],
                    "transpose", case=index)
            padded = [[0] * (len(grid[0]) + 2)] + [[0, *row, 0] for row in grid] + [[0] * (len(grid[0]) + 2)]
            require(checked(current, padded, f"padding:{index}") == answer, "padding", case=index)
            colors = [1, 3, 4, 5, 6, 7, 8, 9]
            shuffled = colors[:]
            random.Random(index).shuffle(shuffled)
            mapping = {0: 0, 2: 2, **dict(zip(colors, shuffled))}
            recolored = [[mapping[v] for v in row] for row in grid]
            target = [[mapping[v] for v in row] for row in answer]
            require(checked(current, recolored, f"recolor:{index}") == target, "color_equivariance", case=index)
            metamorphic += 3
        report["metamorphic_cases"] = metamorphic
        windows = 0
        for seed in range(12):
            for band in BANDS:
                episodes = []
                for index in range(20):
                    grid = current.generate(seed, index, difficulty=band)
                    episodes.append({"input": grid, "output": checked(current, grid, f"lesson:{seed}:{band}:{index}")})
                for start in range(17):
                    demos, query = episodes[start:start + 3], episodes[start + 3]
                    reasons = current.lesson_identifiable(demos, {"input": query["input"]})
                    require(not reasons, "lesson_unidentifiable", seed=seed, band=band, start=start, reasons=reasons)
                    windows += 1
        report["racket_backed_three_demo_windows"] = windows
    finally:
        bridge.shutdown()
    report["racket_executions"] = calls
    report["failures"] = len(failures)
    report["passed"] = not failures
    dump(out / "report.json", report)
    dump(out / "counterexamples.json", witnesses)
    dump(out / "failures.json", failures)
    if args.pytest:
        test = subprocess.run([sys.executable, "-m", "pytest", "-q", f"tests/test_generator_{TASK}.py"],
                              cwd=Path(__file__).resolve().parent, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        (out / "pytest.log").write_text(test.stdout)
        report["pytest_exit_code"] = test.returncode
        report["passed"] &= test.returncode == 0
        dump(out / "report.json", report)
    print(json.dumps({k: report[k] for k in ("passed", "racket_executions", "failures")}, sort_keys=True))
    return 0 if report["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=256)
    parser.add_argument("--baseline-generator", type=Path)
    parser.add_argument("--exhaustive", action="store_true")
    parser.add_argument("--pytest", action="store_true")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")
    args.out = args.out.resolve()
    if args.baseline_generator:
        args.baseline_generator = args.baseline_generator.resolve()
        if not args.baseline_generator.is_file():
            parser.error("--baseline-generator must name a readable source file")
    if args.worker:
        return worker(args)
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    args.out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-task-probe-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(repo), stage, TASK)
        dump(args.out / "runtime_manifest.json", manifest)
        shutil.copy2(__file__, stage / "review_probe_worker.py")
        command = [sys.executable, "-E", "-s", str(stage / "review_probe_worker.py"), "--worker",
                   "--out", str(args.out), "--samples-per-band", str(args.samples_per_band)]
        for flag, enabled in (("--exhaustive", args.exhaustive), ("--pytest", args.pytest)):
            if enabled:
                command.append(flag)
        if args.baseline_generator:
            baseline_copy = stage / "baseline_generator.py"
            shutil.copy2(args.baseline_generator, baseline_copy)
            command += ["--baseline-generator", str(baseline_copy)]
        run = run_process(command, stage, timeout=600)
        run["probe_source_sha256"] = digest(Path(__file__))
        dump(args.out / "execution.json", run)
        print(run["stdout"], end="")
        if run["stderr"]:
            print(run["stderr"], file=sys.stderr, end="")
        return 0 if run["exit_code"] == 0 and not run["timed_out"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
