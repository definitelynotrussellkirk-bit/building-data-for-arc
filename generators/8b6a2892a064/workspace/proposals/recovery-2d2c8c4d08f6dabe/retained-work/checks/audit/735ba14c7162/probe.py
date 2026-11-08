"""Replay the bounded A735 source/contract audit; no Racket execution."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import types
import zipfile

TASK = "735ba14c7162"
EXPECTED_SOURCE = "9fe7aac58ae7ec3b3a859dc2b5e00daa55cea264b6f21014bdf2e4d0c0aaf630"
parser = argparse.ArgumentParser()
origin = parser.add_mutually_exclusive_group(required=True)
origin.add_argument("--source-zip")
origin.add_argument("--repo")
parser.add_argument("--out", required=True)
args = parser.parse_args()
sys.dont_write_bytecode = True
output = Path(args.out).resolve()
if output.exists():
    raise SystemExit("Use a new evidence output path")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())

nonmutation_failures = []
def pure_call(fn, grid, label):
    value = copy.deepcopy(grid)
    before = copy.deepcopy(value)
    result = fn(value)
    if value != before:
        nonmutation_failures.append(label)
    return result

def direct_right_pack(grid):
    result = []
    for row in grid:
        values = [v for v in row if v != 0]
        result.append([0] * (len(row) - len(values)) + values)
    return result

with tempfile.TemporaryDirectory(prefix="arc-a735-replay-") as temporary:
    dependency_hashes = {}
    if args.source_zip:
        archive = zipfile.ZipFile(args.source_zip)
        def read(relative):
            return archive.read("WORK/repo/" + relative)
        dependencies = ["puzzle_generators/__init__.py", "puzzle_generators/base.py",
            "puzzle_generators/helpers/__init__.py", "puzzle_generators/helpers/grid.py",
            "puzzle_generators/helpers/shape.py", "puzzle_generators/helpers/place.py",
            "puzzle_generators/helpers/palette.py", "puzzle_generators/helpers/blobs.py"]
        for relative in dependencies:
            data = read("shared/runtime/" + relative)
            destination = Path(temporary) / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            dependency_hashes["shared/runtime/" + relative] = sha(data)
        sys.path.insert(0, temporary)
        canonical_stream = archive.open("WORK/repo/shared/data/canonical/puzzles.jsonl")
        origin_name = str(Path(args.source_zip).resolve())
    else:
        repository = Path(args.repo).resolve()
        def read(relative):
            return (repository / relative).read_bytes()
        sys.path.insert(0, str(repository / "shared/runtime"))
        canonical_stream = (repository / "shared/data/canonical/puzzles.jsonl").open("rb")
        origin_name = str(repository)
        for relative in ["shared/runtime/puzzle_generators/base.py", "shared/runtime/puzzle_generators/helpers/grid.py"]:
            dependency_hashes[relative] = sha(read(relative))
    source = read(f"generators/{TASK}/generator.py")
    assert sha(source) == EXPECTED_SOURCE, "Audited source changed"
    with canonical_stream as stream:
        for canonical_raw in stream:
            canonical = json.loads(canonical_raw)
            if canonical.get("task_id") == TASK:
                break
        else:
            raise AssertionError("Canonical task missing")
    selected = types.ModuleType("audit_selected_735ba14c7162")
    selected.__file__ = origin_name + "/generators/" + TASK + "/generator.py"
    sys.modules[selected.__name__] = selected
    exec(compile(source, selected.__file__, "exec"), selected.__dict__)
    rule = canonical["program_solution"]
    assert sha(" ".join(rule.split()).encode())[:12] == selected.RULE_HASH
    pairs = canonical["train"] + canonical["test"]
    mismatches = {name: [] for name in selected.CANONICAL_SHORTCUTS}
    canonical_rows = []
    counterexample = None
    for index, pair in enumerate(pairs):
        grid, expected = pair["input"], pair["output"]
        label = f"canonical:{index}"
        row = {"pair_index": index, "input_sha256": grid_hash(grid),
            "provided_output_sha256": grid_hash(expected),
            "self_check_errors": pure_call(selected.self_check, grid, label + ":self_check"),
            "strict_errors": pure_call(selected.strict_canonical_like, grid, label + ":strict"),
            "python_mirror_matches": pure_call(selected.rule_mirror, grid, label + ":mirror") == expected}
        rival_outputs = {}
        for name, fn in selected.CANONICAL_SHORTCUTS.items():
            result = pure_call(fn, grid, label + ":" + name)
            rival_outputs[name] = result
            if result != expected:
                mismatches[name].append(index)
        canonical_rows.append(row)
        if index == 0:
            counterexample = {"input": grid, "provided_canonical_output": expected,
                "declared_canonical_shortcut_outputs": rival_outputs,
                "label_source": "supplied canonical JSONL; no Racket executed"}
    cases = [(band, seed, index, {}) for band in ("easy", "medium", "hard")
        for seed, index in ((0, 0), (17, 1), (20261023, 2))]
    cases += [("medium", 17, 2, dict(zip(("grid_h", "grid_w", "active_rows", "palette_size"), values)))
        for values in ((4, 7, 3, 4), (8, 11, 8, 9), (5, 9, 4, 9))]
    draw_rows = []
    witness_hits = {name: 0 for name in selected.SEMANTIC_WITNESSES}
    rival_disagreements = {name: 0 for name in selected.SEMANTIC_RIVALS}
    for case_index, (band, seed, index, overrides) in enumerate(cases):
        rng_before = random.getstate()
        grid = selected.generate(seed, index, difficulty=band, **overrides)
        rng_unchanged = random.getstate() == rng_before
        expected = direct_right_pack(grid)
        label = f"draw:{case_index}"
        row = {"difficulty": band, "seed": seed, "sample_index": index, "overrides": overrides,
            "input_sha256": grid_hash(grid), "shape": [len(grid), len(grid[0])],
            "self_check_errors": pure_call(selected.self_check, grid, label + ":self_check"),
            "strict_errors": pure_call(selected.strict_canonical_like, grid, label + ":strict"),
            "mirror_matches_direct_pack": pure_call(selected.rule_mirror, grid, label + ":mirror") == expected,
            "observed_axes": pure_call(selected.observe_overrides, grid, label + ":axes"),
            "process_global_rng_unchanged": rng_unchanged}
        for name, fn in selected.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(pure_call(fn, grid, label + ":" + name))
        for name, fn in selected.SEMANTIC_RIVALS.items():
            rival_disagreements[name] += pure_call(fn, grid, label + ":" + name) != expected
        draw_rows.append(row)
    scalar_rows = []
    for seed, index in ((True, 0), (1.0, 0), ("1", 0), (1, True), (1, -1), (1, 1.5), (1, "1")):
        row = {"seed_repr": repr(seed), "sample_index_repr": repr(index),
            "seed_type": type(seed).__name__, "sample_index_type": type(index).__name__}
        try:
            grid = selected.generate(seed, index)
            row.update(outcome="accepted", shape=[len(grid), len(grid[0])],
                input_sha256=grid_hash(grid), self_check_errors=selected.self_check(grid))
        except Exception as error:
            row.update(outcome="rejected", exception_type=type(error).__name__, message=str(error))
        scalar_rows.append(row)
    mutation_rows = []
    for name, grid in selected.mutation_fixtures():
        errors = pure_call(selected.self_check, grid, "mutation:" + name)
        mutation_rows.append({"name": name, "validator_errors": errors, "rejected": bool(errors)})
    report = {"schema": "arcpuzzles-bounded-audit-replay-v1", "task_id": TASK,
        "source_origin": origin_name, "generator_path": f"generators/{TASK}/generator.py",
        "generator_sha256": sha(source), "rule_hash": selected.RULE_HASH,
        "canonical_rule_text_sha256": sha(rule.encode()), "canonical_row_sha256": sha(canonical_raw),
        "dependency_sha256": dependency_hashes, "canonical_pairs": canonical_rows,
        "false_shortcut_mismatch_indices": mismatches, "canonical_counterexample": counterexample,
        "draws": draw_rows, "draw_count": len(draw_rows),
        "unique_input_count": len({row["input_sha256"] for row in draw_rows}),
        "witness_hits": witness_hits, "rival_disagreements": rival_disagreements,
        "scalar_probes": scalar_rows, "mutation_fixtures": mutation_rows,
        "nonmutation_failures": nonmutation_failures, "racket_executed": False,
        "frozen_test_preflight_reexecuted": False,
        "scope": "Three canonical pairs, 12 generation calls, seven scalar calls, four declared mutations; Python only",
        "argv": [sys.executable, *sys.orig_argv[1:]], "cwd": str(Path.cwd()),
        "python_version": sys.version, "probe_sha256": sha(Path(__file__).read_bytes())}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_sha256": report["generator_sha256"],
        "rule_hash": report["rule_hash"], "canonical_pairs": len(canonical_rows),
        "false_shortcut_mismatch_indices": mismatches, "draws": len(draw_rows),
        "unique_inputs": report["unique_input_count"], "scalar_accepted": sum(r["outcome"] == "accepted" for r in scalar_rows),
        "witness_hits": witness_hits, "rival_disagreements": rival_disagreements,
        "nonmutation_failures": nonmutation_failures, "mutations_rejected": sum(r["rejected"] for r in mutation_rows),
        "racket_executed": False, "evidence_sha256": sha(output.read_bytes())}, sort_keys=True))
