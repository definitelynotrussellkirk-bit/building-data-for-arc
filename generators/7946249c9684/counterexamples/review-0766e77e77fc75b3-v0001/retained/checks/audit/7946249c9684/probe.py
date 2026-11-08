#!/usr/bin/env python3
"""Focused current-source audit of per-column/per-color endpoint grouping.

No generator or rule is edited. All outputs are confined to this directory.
Use an explicit --repo so the retained probe can target a relocated checkout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True

TASK = "7946249c9684"
EXPECTED_SOURCE = "0e39b781378bcd3b94bf4bceb407dc9fc1528c0e4fada003a4a1512c0d3bdf6f"
HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def read(name):
    return json.loads((HERE / name).read_text())


def append_command(row):
    path = HERE / "verification_commands.json"
    doc = read(path.name) if path.exists() else {
        "schema": "arcpuzzles-focused-audit-commands-v1", "task_id": TASK, "commands": []}
    doc["commands"].append(row)
    write(path.name, doc)


def load(repo):
    source = repo / "generators" / TASK / "generator.py"
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha != EXPECTED_SOURCE:
        raise ValueError(f"Audit source changed: {source_sha}")
    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_7946249c9684_subject", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [json.loads(line) for line in (repo / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
            if line.strip() and json.loads(line).get("task_id") == TASK]
    rules = {row["program_solution"] for row in rows}
    if len(rules) != 1:
        raise ValueError("Expected one unambiguous canonical rule")
    rule = next(iter(rules))
    identity = {
        "task_id": TASK, "generator_version": module.VERSION,
        "generator_path": f"generators/{TASK}/generator.py",
        "generator_sha256": source_sha, "declared_rule_hash": module.RULE_HASH,
        "canonical_rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_normalized_rule_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "canonical_rule_rows": len(rows),
    }
    assert identity["canonical_normalized_rule_sha256"].startswith(module.RULE_HASH)
    return module, rows, identity


def independent_runs(grid):
    result = []
    for col in range(len(grid[0])):
        row = 0
        while row < len(grid):
            color = grid[row][col]
            if color == 0:
                row += 1
                continue
            start = row
            while row + 1 < len(grid) and grid[row + 1][col] == color:
                row += 1
            result.append([col, start, row, color])
            row += 1
    return result


def independent_output(grid):
    """Local-neighbor endpoint test; imports no generator run/output helper."""
    out = [[0] * len(grid[0]) for _ in grid]
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color and (row == 0 or row == len(grid) - 1
                          or grid[row - 1][col] != color or grid[row + 1][col] != color):
                out[row][col] = color
    return out


def rival(grid):
    """Wrong rival: keep global first/last occurrence of each (column,color)."""
    groups = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                groups[(col, color)].append(row)
    out = [[0] * len(grid[0]) for _ in grid]
    for (col, color), rows in groups.items():
        out[min(rows)][col] = color
        out[max(rows)][col] = color
    return out


def prepare(repo):
    module, canonical, identity = load(repo)
    inputs, samples, expected = [], [], {}

    def add(grid, metadata):
        index = len(inputs)
        errors = module.self_check(grid, difficulty=metadata.get("difficulty"))
        assert errors == [], (index, errors)
        runs = independent_runs(grid)
        repeated = Counter((col, color) for col, start, end, color in runs)
        samples.append({"index": index, **metadata, "input_sha256": digest(grid),
                        "validator_errors": errors, "observed_axes": module.observe_overrides(grid),
                        "runs_column_start_end_color": runs,
                        "repeated_column_color_pairs": [list(key) for key in sorted(repeated) if repeated[key] > 1]})
        inputs.append(grid)
        return index

    for variant, row in enumerate(canonical):
        for split in ("train", "test"):
            for pair_index, pair in enumerate(row.get(split, [])):
                index = add(pair["input"], {"kind": "canonical", "variant": variant,
                           "split": split, "pair_index": pair_index,
                           "seed": None, "sample_index": None, "overrides": {}})
                expected[str(index)] = pair["output"]
    assert len(inputs) == 4

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(18):
            seed = 1000 + 100 * band_index + index
            add(module.generate(seed, index, difficulty=band), {
                "kind": "generated_default", "difficulty": band,
                "seed": seed, "sample_index": index, "overrides": {},
                "scheduled_profile": module.schedule_profile(seed, index, band)})

    # Retain every draw in the two-seed discovery search; no selected successes
    # are silently reported as an unfiltered sample.
    overrides = {"grid_w": 7, "n_runs": 8, "palette_size": 3}
    for seed in (0, 1):
        add(module.generate(seed, 0, difficulty="medium", **overrides), {
            "kind": "generated_exact_override", "difficulty": "medium",
            "seed": seed, "sample_index": 0, "overrides": overrides,
            "scheduled_profile": module.schedule_profile(seed, 0, "medium"),
            "discovery_policy": "first two seeds, both retained; seed 1 is first separating draw"})

    minimal = [[0] * 7 for _ in range(6)]
    for row in (0, 1, 3, 4, 5):
        minimal[row][1] = 1
    for row in (1, 2, 3):
        minimal[row][4] = 2
    add(minimal, {"kind": "constructed_domain_witness", "difficulty": None,
        "seed": None, "sample_index": None, "overrides": {},
        "construction": "6x7 zeros; color 1 at column 1 rows 0,1,3,4,5; color 2 at column 4 rows 1,2,3",
        "domain": "Validator accepted: 6x7, three runs, two colors, length-3 runs; not claimed default-generated"})
    assert len(inputs) == 61
    write("input.json", inputs)
    write("sampling.json", {"source_identity": identity, "samples": samples,
          "canonical_expected": expected,
          "default_policy": "18 draws per band; sample_index i=0..17; seed=1000+100*band_index+i; no overrides, rejection or filtering"})
    write("rival.json", {"name": "column_color_extremes", "outputs": [rival(grid) for grid in inputs],
                         "independent_local_outputs": [independent_output(grid) for grid in inputs]})
    print(json.dumps({"prepared_inputs": len(inputs), "unique_inputs": len({digest(g) for g in inputs}),
                      "source_identity": identity}))


def reference(repo):
    work = repo.parent
    python = work / ".venv-review/bin/python"
    argv = [str(python), "run_with_racket.py", str(python), "-m", "arcpuzzles", "apply", TASK,
            "--input", "../checks/audit/7946249c9684/input.json",
            "--out", "../checks/audit/7946249c9684/racket.json"]
    assert HERE == work / "checks/audit" / TASK, "Reference wrapper expects its portable WORK layout"
    started = time.monotonic()
    completed = subprocess.run(argv, cwd=work, capture_output=True, text=True)
    append_command({"purpose": "actual canonical Racket labels for all 61 audit inputs",
                    "argv": argv, "cwd": str(work), "wrapper_effective_cwd": str(repo),
                    "exit_code": completed.returncode, "elapsed_seconds": round(time.monotonic() - started, 3),
                    "stdout": completed.stdout, "stderr": completed.stderr,
                    "evidence_paths": [str(HERE / "input.json"), str(HERE / "racket.json")]})
    print(json.dumps({"reference_exit_code": completed.returncode,
                      "reference_output": str(HERE / "racket.json")}))
    if completed.returncode:
        raise RuntimeError(completed.stderr or completed.stdout)


def summarize(repo):
    _module, _rows, current = load(repo)
    sampling, alternatives, actual = read("sampling.json"), read("rival.json"), read("racket.json")
    identity = sampling["source_identity"]
    assert current == identity
    assert actual["generator_sha256"] == identity["generator_sha256"]
    assert actual["executed_rule_hash"] == identity["declared_rule_hash"]
    assert actual["rule_hash_matches_catalog"]
    assert len(actual["results"]) == len(sampling["samples"]) == 61
    identity = {**identity, "executed_callable_sha256": actual["rule_text_sha256"]}
    by_kind, compared, witnesses = {}, [], []
    for sample, result, alternative, independent in zip(
            sampling["samples"], actual["results"], alternatives["outputs"],
            alternatives["independent_local_outputs"], strict=True):
        assert not result["error"], result
        assert result["input_sha256"] == sample["input_sha256"]
        assert result["output"] == independent
        if sample["kind"] == "canonical":
            assert result["output"] == sampling["canonical_expected"][str(sample["index"]) ]
        matches = result["output"] == alternative
        counts = by_kind.setdefault(sample["kind"], {"inputs": 0, "rival_matches": 0, "rival_disagreements": 0})
        counts["inputs"] += 1
        counts["rival_matches"] += int(matches)
        counts["rival_disagreements"] += int(not matches)
        compared.append({"index": sample["index"], "kind": sample["kind"],
                         "rival_matches_racket": matches, "independent_matches_racket": True})
        if not matches:
            differences = [[r, c, result["output"][r][c], alternative[r][c]]
                for r in range(len(result["input"])) for c in range(len(result["input"][0]))
                if result["output"][r][c] != alternative[r][c]]
            witnesses.append({"sample": sample, "input": result["input"],
                              "racket_output": result["output"], "rival_output": alternative,
                              "differences_row_col_racket_rival": differences})
    assert by_kind["canonical"]["rival_matches"] == 4
    assert by_kind["generated_default"]["rival_matches"] == 54
    assert [w["sample"]["index"] for w in witnesses] == [59, 60]
    assert witnesses[0]["differences_row_col_racket_rival"] == [[1, 6, 6, 0], [3, 6, 6, 0]]
    assert witnesses[1]["differences_row_col_racket_rival"] == [[1, 1, 1, 0], [3, 1, 1, 0]]
    summary = {"schema": "7946249c9684-column-color-shortcut-v1", "source_identity": identity,
               "reference_inputs": 61, "reference_errors": 0,
               "unique_inputs": len({sample["input_sha256"] for sample in sampling["samples"]}),
               "validator_passes": 61, "independent_local_matches_racket": 61,
               "by_kind": by_kind, "comparisons": compared,
               "scope": "Focused default-distribution shortcut; exact override and constructed witnesses; no full battery, production-lesson census, model evaluation, or claimed wrong Racket label"}
    write("summary.json", summary)
    write("counterexamples.json", {"source_identity": identity, "rival": "column_color_extremes", "witnesses": witnesses})
    print(json.dumps({key: value for key, value in summary.items() if key != "comparisons"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "reference", "summarize"))
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    started, stamp = time.monotonic(), datetime.now(timezone.utc).isoformat()
    status, error = 0, None
    try:
        globals()[args.mode](args.repo.resolve())
    except Exception as exc:
        status, error = 1, f"{type(exc).__name__}: {exc}"
        raise
    finally:
        append_command({"purpose": args.mode, "argv": [sys.executable, *sys.argv],
                        "cwd": str(Path.cwd()), "exit_code": status, "error": error,
                        "started_at": stamp, "elapsed_seconds": round(time.monotonic() - started, 3)})


if __name__ == "__main__":
    main()
