"""Bounded, deterministic swatch/solid-row audit for a61246736c26.

The fixture and observations below use no generator-private constructors.
Canonical Racket, not this fixture's expected output, is the label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import importlib.machinery
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile

TASK_ID = "a61246736c26"
STANDARD_FRAMES = (5, 9, 0)
FILL_COLORS = (3, 4, 6, 7)


def reviewer_helpers():
    """Find the shared helper within this probe's own library or staged runtime."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        for directory in (ancestor, ancestor / "shared/runtime"):
            if (directory / "reviewer_support.py").is_file():
                sys.path.insert(0, str(directory))
                try:
                    return importlib.import_module("reviewer_support")
                finally:
                    sys.path.pop(0)
    raise RuntimeError("Cannot find local reviewer_support.py")


def selected_generator():
    helpers = reviewer_helpers()
    return helpers.load_selected_generator(TASK_ID, root=helpers.find_root(__file__))


def lattice_case(frames, solid_rows, tile_size=4):
    """Construct a framed lattice and its independent expected output.

    The default 4x4 tiles have distinct singleton-2 interior patterns. Larger
    sizes also let tests construct geometrically valid but oversized grids.
    No generated grid is used.
    """
    frames, solid_rows = tuple(frames), tuple(solid_rows)
    if sorted(frames) != [0, 5, 9] or len(solid_rows) not in (3, 4):
        raise ValueError("Expected three frame swatches and three or four columns")
    if any(type(row) is not int or row not in range(3) for row in solid_rows):
        raise ValueError("Solid rows must be 0, 1 or 2")
    if type(tile_size) is not int or not 4 <= tile_size <= 8:
        raise ValueError("Fixture tile size must be 4..8")
    size, step = tile_size, tile_size + 1
    grid = [[8] * (step * len(solid_rows) + 1) for _ in range(3 * step + 1)]
    expected = [[] for _ in range(size)]
    for column, solid_row in enumerate(solid_rows):
        pattern = [[1 if r in (0, size - 1) or c in (0, size - 1) else
                    2 if (r - 1) * (size - 2) + c - 1 == column else 8
                    for c in range(size)] for r in range(size)]
        for band, frame in enumerate(frames):
            for r in range(size):
                grid[1 + step * band + r][0] = frame
                for c in range(size):
                    value = pattern[r][c]
                    if band == solid_row and 0 < r < size - 1 and 0 < c < size - 1:
                        value = FILL_COLORS[column]
                    grid[1 + step * band + r][1 + step * column + c] = value
        for r in range(size):
            if column:
                expected[r].append(8)
            expected[r].extend(frames[solid_row] if value == 1 else
                               FILL_COLORS[column] if value == 2 else value
                               for value in pattern[r])
    return grid, expected


def recombination_cases():
    """All 6 * (3**3 + 3**4) = 648 independent counterfactuals."""
    for columns in (3, 4):
        for frames in itertools.permutations(STANDARD_FRAMES):
            for solid_rows in itertools.product(range(3), repeat=columns):
                grid, expected = lattice_case(frames, solid_rows)
                yield {"frames": frames, "solid_rows": solid_rows,
                       "input": grid, "expected": expected}


def lattice_features(grid):
    """Observe lawful lattice rows without consulting generator metadata."""
    separators = [r for r, values in enumerate(grid) if set(values) == {8}]
    if len(separators) != 4:
        raise ValueError("Expected four complete separator rows")
    size = separators[1] - 1
    columns = (len(grid[0]) - 1) // (size + 1)
    starts = [1 + band * (size + 1) for band in range(3)]
    frames = tuple(grid[start][0] for start in starts)
    solid_rows = []
    for column in range(columns):
        solid = []
        left = 1 + column * (size + 1)
        for band, top in enumerate(starts):
            interior = {grid[top + r][left + c]
                        for r in range(1, size - 1) for c in range(1, size - 1)}
            if len(interior) == 1 and interior <= set(FILL_COLORS):
                solid.append(band)
        if len(solid) != 1:
            raise ValueError(f"Column {column} does not have one solid tile")
        solid_rows.append(solid[0])
    return {"frames": frames, "solid_rows": tuple(solid_rows),
            "columns": columns, "tile_size": size}


def crossed_same_row_witness(grid):
    """A nonzero same-row case also refuting fixed standard row colors."""
    features = lattice_features(grid)
    rows = features["solid_rows"]
    return (len(set(rows)) == 1 and features["frames"][rows[0]] != 0
            and features["frames"][rows[0]] != STANDARD_FRAMES[rows[0]])


def mixed_row_swatch_witness(grid):
    """A mixed-row case whose selected swatches differ from fixed row colors."""
    features = lattice_features(grid)
    rows = features["solid_rows"]
    return (len(set(rows)) > 1
            and any(features["frames"][row] != STANDARD_FRAMES[row] for row in rows))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def reference_batch(inputs, *, root, declared_rule_hash, timeout=45.0):
    """Execute the exact local canonical authority once over the whole batch.

    Catalog.apply is limited to 64 inputs.  This uses its same shared Racket
    bridge and rule wrapper in one session, without modifying any runtime code.
    """
    helpers = reviewer_helpers()
    ledger = helpers.canonical_path(root)
    sources = set()
    with ledger.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError("Canonical authority must have one unambiguous rule source")
    source = sources.pop()
    rule_hash = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    if rule_hash != declared_rule_hash:
        raise ValueError(f"Canonical rule {rule_hash} differs from declared {declared_rule_hash}")
    sys.path.insert(0, str(Path(helpers.__file__).resolve().parent))
    try:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
    finally:
        sys.path.pop(0)
    # Repository shared/tools is staged as scripts/ by prepare_runtime. Bind
    # that same local package here without copying a runtime or changing files.
    if importlib.util.find_spec("scripts") is None:
        spec = importlib.machinery.ModuleSpec("scripts", loader=None, is_package=True)
        spec.submodule_search_locations[:] = [str(root / "shared/tools")]
        sys.modules["scripts"] = importlib.util.module_from_spec(spec)
    callable_text = wrap_rule(source)
    literal = "(" + " ".join("(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")" for grid in inputs) + ")"
    with RacketBridge(timeout=timeout) as bridge:
        bridge.eval_text(f"(define a612-review-rule {callable_text})")
        outputs = bridge.eval_text(f"(map a612-review-rule '{literal})")
        executable = Path(bridge.racket_binary)
        runtime = {"racket_binary": str(executable),
                   "racket_binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                   "racket_restarts": bridge._restarts}
    if not isinstance(outputs, list) or len(outputs) != len(inputs):
        raise ValueError("Canonical batch returned the wrong number of outputs")
    outputs = [helpers.normalize_grid(output) for output in outputs]
    return outputs, {"authority": "canonical", "canonical_ledger": str(ledger.relative_to(root)),
                     "executed_rule_hash": rule_hash,
                     "rule_source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                     "rule_callable_sha256": hashlib.sha256(callable_text.encode()).hexdigest(),
                     "rule_wrap_sha256": hashlib.sha256(Path(sys.modules[wrap_rule.__module__].__file__).read_bytes()).hexdigest(),
                     "parser_sha256": hashlib.sha256(Path(sys.modules["scripts.comment_solutions"].__file__).read_bytes()).hexdigest(),
                     "rule_evaluations": len(outputs), "batch_calls": 1, **runtime}


def run_probe(default_count=600, timeout=45.0):
    helpers = reviewer_helpers()
    root = helpers.find_root(__file__)
    generator, source_path, source_sha256 = selected_generator()
    cases = [{"population": "recombinations", **case} for case in recombination_cases()]
    # Visit every band for each seed: cycling band with seed*29 would alias
    # each difficulty to one phase of a three-phase generation schedule.
    for draw in range(default_count):
        seed, band_index = divmod(draw, 3)
        band = ("easy", "medium", "hard")[band_index]
        cases.append({"population": "defaults", "seed": seed, "sample_index": seed * 29,
                      "difficulty": band,
                      "input": generator.generate(seed, seed * 29, difficulty=band)})
    for pair in helpers.canonical_pairs(TASK_ID, root=root, labeled_only=True):
        cases.append({"population": "canonical_controls", **pair, "expected": pair["output"]})
    inputs = [case["input"] for case in cases]
    outputs, reference = reference_batch(inputs, root=root,
                                        declared_rule_hash=generator.RULE_HASH, timeout=timeout)
    counters = {population: Counter() for population in
                ("recombinations", "defaults", "canonical_controls")}
    failures, witnesses = [], []
    columns, same_row_frames, permutations = Counter(), Counter(), Counter()
    crossed_witnesses = mixed_witnesses = 0
    witnesses_by_band = {band: Counter() for band in ("easy", "medium", "hard")}
    witness_cases = {((5, 9, 0), (0, 0, 0)): "standard_same_row",
                     ((9, 0, 5), (0, 0, 0)): "permuted_same_row",
                     ((9, 0, 5), (0, 1, 2)): "permuted_mixed_rows"}
    for case, output in zip(cases, outputs, strict=True):
        counts = counters[case["population"]]
        counts["checked"] += 1
        errors = []
        try:
            validation = generator.self_check(case["input"])
            if validation:
                counts["validator_rejections"] += 1
                errors.append({"validator": validation})
        except Exception as exc:
            counts["validator_exceptions"] += 1
            errors.append({"validator_exception": f"{type(exc).__name__}: {exc}"})
        try:
            if generator.rule_mirror(case["input"]) != output:
                counts["mirror_mismatches"] += 1
                errors.append({"mirror": "differs from actual canonical Racket"})
        except Exception as exc:
            counts["mirror_exceptions"] += 1
            errors.append({"mirror_exception": f"{type(exc).__name__}: {exc}"})
        if "expected" in case and case["expected"] != output:
            counts["expectation_mismatches"] += 1
            errors.append({"expectation": "fixture/canonical control differs from actual Racket"})
        if errors and len(failures) < 5:
            failures.append({key: value for key, value in case.items()
                             if key not in ("input", "expected", "output")} | {"errors": errors})
        if case["population"] == "defaults":
            features = lattice_features(case["input"])
            columns[str(features["columns"])] += 1
            permutations[",".join(map(str, features["frames"]))] += 1
            if len(set(features["solid_rows"])) == 1:
                same_row_frames[str(features["frames"][features["solid_rows"][0]])] += 1
            same_row = crossed_same_row_witness(case["input"])
            mixed_row = mixed_row_swatch_witness(case["input"])
            crossed_witnesses += same_row
            mixed_witnesses += mixed_row
            witnesses_by_band[case["difficulty"]].update(
                {"draws": 1, "crossed_same_row": same_row, "mixed_row_swatch_sensitive": mixed_row})
        witness_key = (case.get("frames"), case.get("solid_rows"))
        if case["population"] == "recombinations" and witness_key in witness_cases:
            witnesses.append({"case": witness_cases[witness_key],
                              "frames": case["frames"], "solid_rows": case["solid_rows"],
                              "input_rows": ["".join(map(str, row)) for row in case["input"]],
                              "canonical_output_rows": ["".join(map(str, row)) for row in output],
                              "self_check": generator.self_check(case["input"])})
    count_fields = ("checked", "validator_rejections", "validator_exceptions",
                    "mirror_mismatches", "mirror_exceptions", "expectation_mismatches")
    populations = {name: {field: counts[field] for field in count_fields}
                   for name, counts in counters.items()}
    missing = {"same_row_frames": sorted({"0", "5", "9"} - set(same_row_frames)),
               "column_counts": sorted({"3", "4"} - set(columns)),
               "frame_permutations": 6 - len(permutations)} if default_count else {}
    parity_failed = any(counts[field] for counts in populations.values()
                        for field in count_fields if field != "checked")
    support_incomplete = bool(default_count and any(missing.values()))
    return {"schema": "a61246736c26-counterfactual-coverage-v1", "task_id": TASK_ID,
            "status": "fail" if parity_failed or support_incomplete else "pass",
            "generator_version": generator.VERSION, "generator_sha256": source_sha256,
            "generator_source": str(source_path.relative_to(root)),
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "reference": reference, "populations": populations,
            "recombination_domain": {"tile_size": 4, "column_counts": [3, 4],
                                     "frame_permutations": 6, "solid_row_assignments": [27, 81],
                                     "total": 648, "distinct_patterns": "singleton 2 in each interior corner"},
            "default_schedule": {"seed_start": 0, "draws": default_count,
                                 "seed_count": (default_count + 2) // 3,
                                 "sample_index": "seed * 29",
                                 "difficulty": "easy, medium, hard for each seed before incrementing seed"},
            "default_support": {"column_counts": dict(columns), "same_row_frames": dict(same_row_frames),
                                "frame_permutations": dict(permutations),
                                "crossed_same_row_witnesses": crossed_witnesses,
                                "mixed_row_swatch_witnesses": mixed_witnesses,
                                "witnesses_by_band": {band: dict(counts) for band, counts in witnesses_by_band.items()},
                                "missing_observations": missing},
            "input_batch_sha256": digest(inputs), "canonical_output_batch_sha256": digest(outputs),
            "failure_examples": failures, "minimal_witnesses": witnesses,
            "limits": ["The 648 counterfactuals exhaust this fixed 4x4 pattern family, not all lawful grids.",
                       "Default support is a fixed-seed sample, not an all-seed distribution proof.",
                       "All reported labels were computed by actual canonical Racket in this run."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New compact JSON receipt path")
    parser.add_argument("--default-count", type=int, default=600, help="Default draws in addition to 648 cases (0..600)")
    parser.add_argument("--racket-timeout", type=float, default=45.0)
    args = parser.parse_args()
    if not 0 <= args.default_count <= 600:
        parser.error("--default-count must be 0..600")
    if not 0 < args.racket_timeout <= 60:
        parser.error("--racket-timeout must be in (0,60]")
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}")
    try:
        report = run_probe(args.default_count, args.racket_timeout)
    except Exception as exc:
        report = {"schema": "a61246736c26-counterfactual-coverage-v1", "task_id": TASK_ID,
                  "status": "error", "exception": f"{type(exc).__name__}: {exc}",
                  "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    report.update({"command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                   "exit_code": 0 if report["status"] == "pass" else 1})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=args.out.parent, prefix="coverage-",
                                         suffix=".tmp", encoding="utf-8", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        if args.out.exists():
            raise FileExistsError(args.out)
        temporary.replace(args.out)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"status": report["status"], "populations": report.get("populations"),
                      "report": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest()}))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
