from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK_ID = "dfc4967f816f"
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
EXPECTED_SOURCE_SHA = "c3e1e264f25bd4839eec5d91889b22330b83b745bc7cf027246171abf817f452"
RULE_HASH = "136bfe841cf2"
PROBE_SEED_HEX = "c4f83b2baa32c4e0e9d672576af4954f39f35ac1afdd5b26ee69d5a48bc26e93"

sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "src"))


def load_generator():
    actual = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"source hash drift: {actual}")
    spec = importlib.util.spec_from_file_location("ticket_generator", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiles(grid):
    return [[list(row[left:left + 3]) for row in grid] for left in range(0, len(grid[0]), 4)]


def outer_rows_only(grid):
    return [[
        8 if tile[0] == tile[0][::-1] and tile[2] == tile[2][::-1] else 0
        for tile in tiles(grid)
    ]]


def canonical_row():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise RuntimeError("canonical task missing")


def canonical_program(row):
    source = row["program_solution"]
    normalized = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    if normalized != RULE_HASH:
        raise RuntimeError(f"rule hash drift: {normalized}")
    return source


def racket_output(program, grid):
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-ticket-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO), stage, TASK_ID)
        (stage / "request.json").write_text(json.dumps({"program": program, "grid": grid}))
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps(runner._apply_rule(bridge,name,request["grid"])))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=90)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket failed: {result}")
        return json.loads(result["stdout"])


def main():
    started = time.monotonic()
    gen = load_generator()
    row = canonical_row()
    pairs = list(row.get("train", []))
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    pairs.extend(test)
    canonical_fit = [outer_rows_only(pair["input"]) == pair["output"] for pair in pairs]

    seed = int(PROBE_SEED_HEX, 16) % (2**63 - 1)
    witness = None
    checked = 0
    for index in range(120):
        difficulty = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(seed, index, difficulty=difficulty)
        checked += 1
        if gen.self_check(grid):
            continue
        expected = gen.rule_mirror(grid)
        rival = outer_rows_only(grid)
        if expected != rival:
            differing = [i for i, (a, b) in enumerate(zip(expected[0], rival[0])) if a != b]
            witness = {
                "seed": seed,
                "sample_index": index,
                "difficulty": difficulty,
                "input": grid,
                "python_target": expected,
                "rival_output": rival,
                "differing_tile_indices": differing,
                "differing_tiles": [tiles(grid)[i] for i in differing],
            }
            break

    if witness is None:
        result = {
            "schema": "supplementary-adversarial-witness-v1",
            "ticket_id": "ticket-f8f970166f6fe635",
            "status": "unknown",
            "source_sha256": EXPECTED_SOURCE_SHA,
            "rule_hash": RULE_HASH,
            "rival": "outer_rows_only",
            "canonical_fit": canonical_fit,
            "samples_checked": checked,
            "witness_found": False,
            "elapsed_seconds": time.monotonic() - started,
            "limit": "No witness in the bounded 120-sample probe; no broader claim.",
        }
    else:
        racket = racket_output(canonical_program(row), witness["input"])
        witness["racket_output"] = racket
        witness["racket_matches_python_target"] = racket == witness["python_target"]
        witness["racket_differs_from_rival"] = racket != witness["rival_output"]
        result = {
            "schema": "supplementary-adversarial-witness-v1",
            "ticket_id": "ticket-f8f970166f6fe635",
            "status": "completed",
            "source_sha256": EXPECTED_SOURCE_SHA,
            "rule_hash": RULE_HASH,
            "rival": "outer_rows_only",
            "rival_definition": "classify a tile from only its top and bottom rows, ignoring the middle row",
            "canonical_fit": canonical_fit,
            "canonical_pairs_fit": sum(canonical_fit),
            "canonical_pairs_total": len(canonical_fit),
            "samples_checked": checked,
            "witness_found": True,
            "witness": witness,
            "elapsed_seconds": time.monotonic() - started,
            "limit": "One source-bound lawful witness only; lesson-frequency and all-seed coverage were not measured.",
        }
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if witness is not None:
        (HERE / "input.json").write_text(json.dumps(witness["input"], indent=2) + "\n")
        (HERE / "racket.json").write_text(json.dumps({"output": witness["racket_output"]}, indent=2) + "\n")
        (HERE / "rival.json").write_text(json.dumps({"output": witness["rival_output"]}, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
