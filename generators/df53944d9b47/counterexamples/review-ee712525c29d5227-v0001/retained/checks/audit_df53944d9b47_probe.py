"""Reproduce the df53944d9b47 canonical guide-line distribution defect."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "shared/runtime"))
from arcpuzzles import Catalog
from arcpuzzles.runtime import prepare_runtime, run_process

TASK = "df53944d9b47"
GENERATOR_PATH = ROOT / f"generators/{TASK}/generator.py"
OUT = ROOT.parent / "checks"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_df_generator", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise RuntimeError("canonical row missing")


def racket_output(row, grid):
    with tempfile.TemporaryDirectory(prefix="audit-df-racket-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "request.json").write_text(
            json.dumps({"program": row["program_solution"], "grids": [grid]})
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
q = json.loads(Path("request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(q["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in q["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"] != 0:
            raise RuntimeError(result)
        return json.loads(result["stdout"])[0]


def main() -> int:
    generator = load_generator()
    row = canonical_row()
    pairs = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    normalized = " ".join(row["program_solution"].split())
    rule_hash = hashlib.sha256(normalized.encode()).hexdigest()[:12]

    canonical = []
    for index, pair in enumerate(pairs):
        grid = pair["input"]
        canonical.append(
            {
                "pair_index": index,
                "color7_count": sum(value == 7 for source_row in grid for value in source_row),
                "color7_columns": sorted(
                    {col for source_row in grid for col, value in enumerate(source_row) if value == 7}
                ),
                "self_check_errors": generator.self_check(grid),
            }
        )

    by_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        examples = []
        for index in range(100):
            seed = 700_000 + band_index * 10_000 + index
            sample_index = index * 9 + 2
            grid = generator.generate(seed, sample_index, difficulty=band)
            count = sum(value == 7 for source_row in grid for value in source_row)
            counts[str(count)] += 1
            if len(examples) < 2:
                examples.append(
                    {"seed": seed, "sample_index": sample_index, "color7_count": count}
                )
        by_band[band] = {"color7_count_histogram": dict(counts), "examples": examples}

    census = {
        "schema": "audit-df53944d9b47-guide-support-v1",
        "task_id": TASK,
        "generator_sha256": generator_sha,
        "rule_hash_12": rule_hash,
        "canonical": canonical,
        "generated_by_band": by_band,
        "sampling": {
            "draws_per_band": 100,
            "seed_formula": "700000 + band_index*10000 + i",
            "sample_index": "i*9+2",
        },
        "finding": (
            "All official inputs use a full vertical color-7 guide (9 or 10 cells) "
            "and are rejected by self_check; all 300 sampled defaults use exactly one color-7 marker."
        ),
        "shortcut_risk": (
            "Training can learn mirror around an isolated marker instead of recognizing a guide line."
        ),
    }
    (OUT / "audit-df53944d9b47-census.json").write_text(
        json.dumps(census, indent=2, sort_keys=True) + "\n"
    )

    pair = row["train"][0]
    actual = racket_output(row, pair["input"])
    counterexample = {
        "schema": "audit-counterexample-v1",
        "task_id": TASK,
        "generator_sha256": generator_sha,
        "rule_hash_12": rule_hash,
        "source": "canonical train[0]",
        "seed": None,
        "sample_index": None,
        "difficulty": None,
        "overrides": None,
        "input": pair["input"],
        "actual_racket_output": actual,
        "rival_name": None,
        "rival_output": None,
        "validator_errors": generator.self_check(pair["input"]),
        "documented_authority_domain": "official canonical input with a full vertical color-7 guide",
        "color7_count": sum(value == 7 for source_row in pair["input"] for value in source_row),
        "generated_default_observation": (
            "300/300 sampled defaults in checks/audit-df53944d9b47-census.json "
            "contain exactly one color-7 cell"
        ),
        "command": {
            "cwd": "packet_root",
            "argv": [
                "python3",
                "run_with_racket.py",
                "python3",
                "../checks/audit_df53944d9b47_probe.py",
            ],
        },
        "finding": (
            "The target validator rejects an authoritative canonical input because it requires "
            "one marker instead of the full guide line used by every official input."
        ),
    }
    (OUT / "audit-df53944d9b47-counterexample.json").write_text(
        json.dumps(counterexample, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"canonical_rejected": sum(bool(x["self_check_errors"]) for x in canonical),
                      "sampled_single_marker": sum(v["color7_count_histogram"].get("1", 0) for v in by_band.values()),
                      "racket_matches_canonical": actual == pair["output"]}, indent=2))
    return 0 if all(x["self_check_errors"] for x in canonical) and actual == pair["output"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
