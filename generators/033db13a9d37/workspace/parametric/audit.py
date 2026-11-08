"""Bounded independent semantic audit; no owner acceptance or shared edits.

Run through the packet's review.py run wrapper. --fixtures-only performs the
independent protected-language checks without importing the adapter. Full mode
adds 8 seeds x 2 settings x demo counts 3..6 x 4 queries, count prefixes,
determinism, matched inputs, RNG isolation, and representative Racket labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import pickle
import random
import sys
import time

TASK_ID = "033db13a9d37"
HOME = Path(__file__).resolve().parent
DEFAULT_SEEDS = (0, 1, 7, 17, 101, 991, 2027, 8191)
sys.dont_write_bytecode = True


def _load(path, label):
    name = "_review_033db13a9d37_" + label + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R = _load(HOME / "rivals.py", "rivals")


def find_environment():
    """Use reviewer_support.find_root, then test the actual bridge location."""
    for ancestor in (HOME, *HOME.parents):
        for candidate in (ancestor / "shared/runtime/reviewer_support.py", ancestor / "reviewer_support.py"):
            if candidate.is_file():
                support = _load(candidate, "support")
                root = support.find_root(__file__)
                nested = root / "shared/runtime"
                runtime = nested if (nested / "arc_repl/racket_bridge.py").is_file() else root
                if not (runtime / "arc_repl/racket_bridge.py").is_file():
                    raise FileNotFoundError("No same-checkout protected runtime")
                return root, runtime, support
    raise FileNotFoundError("No same-tree reviewer_support helper")


@contextmanager
def _runtime_context(root, runtime):
    # Avoid cached imports from another generator's workspace or copied runtime.
    names = {"arcpuzzles", "arc_repl", "puzzle_generators", "reviewer_support"}
    names.update(path.stem for path in HOME.glob("*.py"))
    saved = {name: module for name, module in sys.modules.items() if name.split(".")[0] in names}
    before = list(sys.path)
    for name in saved:
        del sys.modules[name]
    sys.path[:0] = [str(root / "src"), str(runtime), str(HOME), str(root)]
    try:
        worker = importlib.import_module("arcpuzzles.parametric_worker")
        if not Path(worker.__file__).resolve().is_relative_to(root):
            raise ImportError("parametric_worker belongs to another source tree")
        with worker._local_imports(runtime, HOME):
            yield worker
    finally:
        sys.path[:] = before
        for name in list(sys.modules):
            if name.split(".")[0] in names:
                del sys.modules[name]
        sys.modules.update(saved)


def stress_inputs():
    """32 reproducible 30x30 semantic-domain inputs, independent of sampler."""
    result = []
    colors = R.COLORS[1:]
    for index in range(32):
        rng = random.Random(93017 + index)
        grid = [[0] * 30 for _ in range(30)]
        if index % 4 == 0:
            # A bottom-row origin has a clipped echo and no possible relay hit.
            for col in rng.sample(range(30), 10 + index % 11):
                grid[29][col] = rng.choice(colors)
        elif index % 4 == 1:
            row = rng.randrange(3)
            col = rng.choice((2, 6, 10, 14))
            grid[row][col] = rng.choice(colors)
            # Dense opposite-parity lower markers exercise a genuine no-hit.
            for rr in range(row + 1, 30):
                for cc in range(1, 30, 2):
                    if rng.randrange(5):
                        grid[rr][cc] = rng.choice(colors)
        else:
            first_row = rng.randrange(5)
            for rr in range(first_row, 30):
                for cc in range(30):
                    if rng.randrange(4) != 0:
                        grid[rr][cc] = rng.choice(colors)
        result.append(grid)
    return result


def _signature(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _source_inventory(root):
    files = [HOME.parents[1] / "generator.py", *HOME.glob("*.py"), *HOME.glob("*.rkt"),
             *HOME.glob("rules/*.rkt")]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(files)) if path.is_file()}


def _require(condition, message, **details):
    if not condition:
        raise AssertionError(_signature({"message": message, **details}))


def _rng_state():
    state = {"python": hashlib.sha256(pickle.dumps(random.getstate())).hexdigest()}
    numpy = sys.modules.get("numpy")
    if numpy is not None:
        state["numpy"] = hashlib.sha256(pickle.dumps(numpy.random.get_state())).hexdigest()
    return state


def _features(grids):
    unique = {_signature(grid): grid for grid in grids}
    rows = [R.feature_summary(grid) for grid in unique.values()]
    counts = Counter()
    for row in rows:
        for key in ("relay_active", "relay_fallback", "origin_bottom", "target_bottom",
                    "different_color", "different_column", "skipped_wrong_parity",
                    "column_major_origin_changes", "mode_changes_output"):
            counts[key] += int(row[key])
    return {
        "unique_inputs": len(unique), "feature_counts": dict(counts),
        "shapes": dict(sorted(Counter(f"{row['shape'][0]}x{row['shape'][1]}" for row in rows).items())),
        "marker_count_range": [min(row["markers"] for row in rows), max(row["markers"] for row in rows)],
        "origin_parities": sorted({row["origin_parity"] for row in rows}),
        "substantial_30x30": sum(row["shape"] == [30, 30] and row["markers"] > 100 for row in rows),
    }


def _fixture_checks(apply, report, canonical):
    fixtures = R.fixtures()
    calls = 0
    def check(program, grid, expected, **context):
        nonlocal calls
        actual = apply(program, deepcopy(grid))
        calls += 1
        _require(actual == expected, "protected Racket disagreement", input=grid,
                 expected=expected, actual=actual, **context)
    signatures = {}
    for mode in R.MODES:
        functions = {"intended": lambda g, mode=mode: R.intended(g, mode), **R.bank(mode)}
        for name, function in functions.items():
            program = R.racket(mode, None if name == "intended" else name)
            outputs = []
            for fixture_name, grid in fixtures.items():
                expected = function(grid)
                outputs.append(expected)
                check(program, grid, expected, mode=mode, rival=name, fixture=fixture_name)
            signatures[(mode, name)] = _signature(outputs)
        expected_signature = signatures[(mode, "intended")]
        observed = {}
        for name in R.bank(mode):
            signature = signatures[(mode, name)]
            _require(signature != expected_signature, "fixture bank does not refute rival", mode=mode, rival=name)
            _require(signature not in observed, "rival aliases on fixtures", mode=mode,
                     rival=name, other=observed.get(signature))
            observed[signature] = name
    for name, grid in fixtures.items():
        check(canonical, grid, R.intended(grid, "first"), mode="canonical", fixture=name)
    stress = stress_inputs()
    for mode in R.MODES:
        program = R.racket(mode)
        for index, grid in enumerate(stress):
            check(program, grid, R.intended(grid, mode), mode=mode, stress=index)
    grid = fixtures["odd_active"]
    origin, mask = R.stage_a(grid)
    opposite = [[int(row > origin[0] and col % 2 != origin[1] % 2)
                 for col in range(len(grid[0]))] for row in range(len(grid))]
    ignored = [[1] * len(grid[0]) for _ in grid]
    target = R.stage_b(grid, origin, mask)
    opposite_target = R.stage_b(grid, origin, opposite)
    ignored_target = R.stage_b(grid, origin, ignored)
    _require(target != opposite_target and target != ignored_target,
             "causal mask intervention does not change target")
    actual_output = R.intended(grid, "parity_relay")
    opposite_output = R.bank("parity_relay")["opposite_lane_parity"](grid)
    ignored_output = R.bank("parity_relay")["ignore_lane_mask"](grid)
    _require(actual_output != opposite_output and actual_output != ignored_output,
             "causal mask intervention does not change output")
    report["protected_fixtures"] = {
        "status": "pass", "fixture_count": len(fixtures),
        "rival_counts": {mode: len(R.bank(mode)) for mode in R.MODES},
        "racket_evaluations": calls, "stress": _features(stress),
        "causal_mask_witness": {"input": grid, "origin": list(origin), "actual_lane_mask": mask,
                                "actual_target": list(target), "opposite_mask_target": list(opposite_target),
                                "ignored_mask_target": list(ignored_target), "actual_output": actual_output,
                                "opposite_mask_output": opposite_output, "ignored_mask_output": ignored_output},
    }


def _program_hashes():
    return {mode + ":" + str(name): hashlib.sha256(R.racket(mode, name).encode()).hexdigest()
            for mode in R.MODES for name in (None, *R.bank(mode))}


def _rival_delta_checks(apply, report, names, baseline_path):
    """Replay additions, with exact unchanged-program linkage to earlier replay."""
    _require(all(name in R.RELAY for name in names) and len(set(names)) == len(names),
             "delta controls must be distinct relay rivals")
    baseline = json.loads(baseline_path.read_text())
    previous_path = baseline_path.parent / baseline["protected_report"]
    previous_bytes = previous_path.read_bytes()
    _require(hashlib.sha256(previous_bytes).hexdigest() == baseline["protected_report_sha256"],
             "protected baseline report hash changed")
    previous = json.loads(previous_bytes)
    _require(previous["status"] == "pass", "protected baseline did not pass")
    old_source = previous["source_sha256"][f"generators/{TASK_ID}/workspace/parametric/rivals.py"]
    _require(old_source == baseline["rivals_source_sha256"], "program baseline source differs")
    current = _program_hashes()
    for name, digest in baseline["program_sha256"].items():
        _require(current.get(name) == digest, "previously protected program changed", program=name)
    calls = 0
    for name in names:
        program = R.racket("parity_relay", name)
        for fixture_name, grid in R.fixtures().items():
            expected = R.bank("parity_relay")[name](grid)
            actual = apply(program, deepcopy(grid))
            calls += 1
            _require(actual == expected, "new protected rival disagrees", rival=name,
                     fixture=fixture_name, input=grid, expected=expected, actual=actual)
    report["protected_rival_delta"] = {
        "status": "pass", "new_controls": list(names), "racket_evaluations": calls,
        "unchanged_previously_replayed_programs": len(baseline["program_sha256"]),
        "prior_report_sha256": baseline["protected_report_sha256"],
        "prior_rivals_source_sha256": baseline["rivals_source_sha256"],
        "prior_report": baseline["protected_report"],
        "baseline_program_manifest_sha256": hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
    }


def _episode_checks(adapter, apply, report, seeds, canonical):
    episodes = {}
    rows = []
    all_inputs = []
    labels = prefix_labels = repeated = 0
    protected_labels = 0
    programs = {mode: adapter.program({"seed_mode": mode}) for mode in R.MODES}
    _require(programs["first"] == canonical, "default program differs from exact canonical text")
    _require(programs["first"] != programs["parity_relay"], "program settings collapse")
    try:
        importlib.import_module("numpy")
    except ImportError:
        pass
    rng_checked = sorted(_rng_state())

    def generate(seed, mode, demos, queries):
        setting = {"seed_mode": mode}
        before = _rng_state()
        episode = adapter.generate(seed, setting, demos, queries)
        _require(_rng_state() == before, "generation mutates global RNG", seed=seed, mode=mode)
        _require(setting == {"seed_mode": mode}, "generation mutates settings", seed=seed, mode=mode)
        _require(isinstance(episode, dict) and episode.get("program_solution") == programs[mode],
                 "episode program identity differs", seed=seed, mode=mode)
        return episode

    def validate(episode, seed, mode, demos, queries):
        checked = 0
        seen = set()
        for split, count in (("train", demos), ("test", queries)):
            pairs = episode.get(split)
            _require(type(pairs) is list and len(pairs) == count, "incorrect requested count", split=split)
            for index, pair in enumerate(pairs):
                grid = pair["input"]
                R.validate_grid(grid)
                output = pair["output"]
                _require(type(output) is list and len(output) == len(grid)
                         and all(type(row) is list and len(row) == len(grid[0])
                                 and all(type(value) is int and 0 <= value <= 9 for value in row)
                                 for row in output),
                         "output must preserve shape and exact integer ARC colors",
                         seed=seed, mode=mode, split=split, index=index)
                _require(pair["output"] == R.intended(grid, mode), "independent label disagreement",
                         seed=seed, mode=mode, split=split, index=index, input=grid,
                         claimed=pair["output"], expected=R.intended(grid, mode))
                key = _signature(grid)
                _require(key not in seen, "duplicate input within episode", seed=seed, mode=mode)
                seen.add(key)
                checked += 1
        return checked

    for seed in seeds:
        for demos in range(3, 7):
            for mode in R.MODES:
                episode = generate(seed, mode, demos, 4)
                labels += validate(episode, seed, mode, demos, 4)
                replay = generate(seed, mode, demos, 4)
                _require(episode == replay, "generation is not deterministic", seed=seed, mode=mode, demos=demos)
                repeated += 1
                episodes[(seed, mode, demos)] = episode
                survivors = [name for name, rival in R.bank(mode).items()
                             if all(rival(pair["input"]) == pair["output"] for pair in episode["train"])]
                other = next(value for value in R.MODES if value != mode)
                setting_fits = all(R.intended(pair["input"], other) == pair["output"] for pair in episode["train"])
                _require(not survivors and not setting_fits, "demonstration rival survives",
                         seed=seed, mode=mode, demos=demos, survivors=survivors,
                         opposite_setting_survives=setting_fits)
                all_inputs.extend(pair["input"] for split in ("train", "test") for pair in episode[split])
                rows.append({"seed": seed, "seed_mode": mode, "demos": demos, "queries": 4,
                             "labels": demos + 4, "rivals_refuted": len(R.bank(mode)),
                             "opposite_setting_refuted": True})
                if seed in (seeds[0], seeds[-1]) and demos in (3, 6):
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = apply(programs[mode], deepcopy(pair["input"]))
                            protected_labels += 1
                            _require(actual == R.intended(pair["input"], mode) == pair["output"],
                                     "generated protected label disagrees", seed=seed, mode=mode,
                                     demos=demos, split=split, index=index)
            a, b = (episodes[(seed, mode, demos)] for mode in R.MODES)
            for split in ("train", "test"):
                _require([pair["input"] for pair in a[split]] == [pair["input"] for pair in b[split]],
                         "inputs differ between settings", seed=seed, demos=demos, split=split)
        for mode in R.MODES:
            full = episodes[(seed, mode, 6)]
            for demos in range(3, 7):
                current = episodes[(seed, mode, demos)]
                _require(current["train"] == full["train"][:demos] and current["test"] == full["test"],
                         "demo-count prefix instability", seed=seed, mode=mode, demos=demos)
            for queries in range(1, 4):
                prefix = generate(seed, mode, 3, queries)
                prefix_labels += validate(prefix, seed, mode, 3, queries)
                _require(prefix["train"] == full["train"][:3] and prefix["test"] == full["test"][:queries],
                         "query-count prefix instability", seed=seed, mode=mode, queries=queries)
    report["episodes"] = {
        "status": "pass", "seeds": list(seeds), "primary_episodes": len(rows),
        "primary_independent_labels": labels, "extra_prefix_episodes": len(seeds) * 2 * 3,
        "extra_prefix_independent_labels": prefix_labels, "deterministic_replays": repeated,
        "protected_generated_labels": protected_labels, "global_rngs_checked": rng_checked,
        "features": _features(all_inputs), "rows": rows,
    }


def run(*, seeds=DEFAULT_SEEDS, fixtures_only=False, episodes_only=False,
        rivals_only=(), baseline_programs=None):
    root, runtime, support = find_environment()
    report = {"schema": "033db13a9d37-independent-parametric-audit-v1", "task_id": TASK_ID,
              "status": "running", "source_sha256": _source_inventory(root),
              "scope": "rival_delta" if rivals_only else "bounded_episodes" if episodes_only
                       else "fixtures_only" if fixtures_only else "bounded_full",
              "independent_program_sha256": _program_hashes(),
              "limits": ["Finite independent oracle and named-rival checks do not prove unique induction.",
                         "This report does not accept a variant, resolve a production audit, or admit training data."]}
    started = time.monotonic()
    try:
        with _runtime_context(root, runtime) as worker:
            catalog_module = importlib.import_module("arcpuzzles.catalog")
            catalog = catalog_module.Catalog(root)
            canonical_set = {item.get("program_solution") for item in catalog._variants().get(TASK_ID, [])}
            _require(len(canonical_set) == 1, "canonical authority is not unique")
            canonical = next(iter(canonical_set))
            _require(canonical == (HOME / "canonical.rkt").read_text(), "canonical copy differs from Catalog")
            canonical_pairs = support.canonical_pairs(TASK_ID, root=root, labeled_only=True)
            for pair in canonical_pairs:
                _require(R.intended(pair["input"], "first") == pair["output"], "canonical pair disagrees")
            report["canonical_pairs"] = len(canonical_pairs)
            apply, identity, bridge = worker._real_evaluator(runtime)
            report["racket"] = identity
            try:
                if rivals_only:
                    _rival_delta_checks(apply, report, rivals_only, baseline_programs)
                elif not episodes_only:
                    _fixture_checks(apply, report, canonical)
                if not fixtures_only and not rivals_only:
                    adapter = _load(HOME / "adapter.py", "adapter")
                    _episode_checks(adapter, apply, report, seeds, canonical)
            finally:
                bridge.close()
        _require(report["source_sha256"] == _source_inventory(root), "reviewed source changed during audit")
        report["status"] = "pass"
    except Exception as error:
        report["status"] = "fail"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New JSON report path; existing reports are refused")
    parser.add_argument("--fixtures-only", action="store_true")
    parser.add_argument("--episodes-only", action="store_true")
    parser.add_argument("--rivals-only", help="Comma-separated new relay rivals; replay only these additions")
    parser.add_argument("--baseline-programs", type=Path, help="Source-bound prior protected program hash manifest")
    parser.add_argument("--seeds", default=",".join(map(str, DEFAULT_SEEDS)))
    args = parser.parse_args(argv)
    if sum((args.fixtures_only, args.episodes_only, bool(args.rivals_only))) > 1:
        parser.error("select at most one audit phase")
    if args.rivals_only and not args.baseline_programs:
        parser.error("rival additions require --baseline-programs")
    seeds = tuple(int(value) for value in args.seeds.split(","))
    if not 1 <= len(seeds) <= 16 or len(set(seeds)) != len(seeds) or any(not 0 <= seed < 2**63 for seed in seeds):
        parser.error("supply 1..16 distinct seeds in 0..2**63-1")
    if args.out.exists():
        parser.error("report path already exists")
    report = run(seeds=seeds, fixtures_only=args.fixtures_only, episodes_only=args.episodes_only,
                 rivals_only=tuple(args.rivals_only.split(",")) if args.rivals_only else (),
                 baseline_programs=args.baseline_programs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "scope": report["scope"],
                      "report": str(args.out), "elapsed_seconds": report["elapsed_seconds"],
                      "error": report.get("error")}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
