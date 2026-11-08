"""Reproduce the c1b540a1d7b0 canonical-bitmap shortcut risk."""
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

TASK = "c1b540a1d7b0"
GENERATOR_PATH = ROOT / f"generators/{TASK}/generator.py"
OUT = ROOT.parent / "checks"


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_c1_generator", GENERATOR_PATH)
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


def components(grid, value=5):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] != value or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == value
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(cells)
    return result


def normalize(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return (row0, col0), tuple(sorted((row - row0, col - col0) for row, col in cells))


def racket_output(row, grid):
    with tempfile.TemporaryDirectory(prefix="audit-c1-racket-") as directory:
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
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    normalized_rule = " ".join(row["program_solution"].split())
    rule_hash = hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]
    patterns = {
        key: tuple(sorted(tuple(sorted(component)) for component in value))
        for key, value in generator._CANONICAL_BITMAPS.items()
    }

    by_band = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter(draws=200)
        examples = []
        for index in range(200):
            seed = 910_000 + band_index * 10_000 + index
            sample_index = index * 13 + 5
            grid = generator.generate(seed, sample_index, difficulty=band)
            normalized_components = tuple(sorted(normalize(cells)[1] for cells in components(grid)))
            key = (len(grid), len(grid[0]), len(normalized_components))
            replay = key in patterns and normalized_components == patterns[key]
            counts["exact_official_bitmap_up_to_translation"] += replay
            if replay and len(examples) < 5:
                examples.append({"seed": seed, "sample_index": sample_index, "key": list(key)})
        by_band[band] = {
            **counts,
            "rate": counts["exact_official_bitmap_up_to_translation"] / counts["draws"],
            "examples": examples,
        }

    census = {
        "schema": "audit-c1b540a1d7b0-canonical-replay-v1",
        "task_id": TASK,
        "generator_sha256": generator_sha,
        "rule_hash_12": rule_hash,
        "sampling": {
            "bands": ["easy", "medium", "hard"],
            "draws_per_band": 200,
            "seed_formula": "910000 + band_index*10000 + i",
            "sample_index": "i*13+5",
        },
        "criterion": (
            "Normalized 4-connected 5-components exactly equal one of "
            "generator._CANONICAL_BITMAPS for the same (h,w,n_components)."
        ),
        "by_band": by_band,
        "total_draws": 600,
        "total_exact_official_bitmap_up_to_translation": sum(
            value["exact_official_bitmap_up_to_translation"] for value in by_band.values()
        ),
        "source_lines": "generator.py:658-678 and 605-630",
        "interpretation": (
            "Default training examples replay extracted official input bitmaps up to translation, "
            "so layout recognition can substitute for compositional room/arm inference."
        ),
    }
    (OUT / "audit-c1b540a1d7b0-census.json").write_text(
        json.dumps(census, indent=2, sort_keys=True) + "\n"
    )

    seed, sample_index, difficulty = 123_002, 15, "medium"
    grid = generator.generate(seed, sample_index, difficulty=difficulty)
    pair = next(
        pair
        for pair in row["train"]
        if len(pair["input"]) == 8
        and len(pair["input"][0]) == 9
        and len(components(pair["input"])) == 2
    )
    templates = {}
    for component in components(pair["input"]):
        (row0, col0), shape = normalize(component)
        templates[shape] = {
            (row - row0, col - col0): pair["output"][row][col]
            for row, col in component
        }
    rival = [[0 for _ in source_row] for source_row in grid]
    for component in components(grid):
        (row0, col0), shape = normalize(component)
        for (drow, dcol), color in templates[shape].items():
            rival[row0 + drow][col0 + dcol] = color
    actual = racket_output(row, grid)

    counterexample = {
        "schema": "audit-counterexample-v1",
        "task_id": TASK,
        "generator_sha256": generator_sha,
        "rule_hash_12": rule_hash,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "overrides": {},
        "input": grid,
        "actual_racket_output": actual,
        "rival_name": "memorize each official normalized component bitmap and its local output coloring",
        "rival_output": rival,
        "rival_matches_actual": rival == actual,
        "validator_errors": generator.self_check(grid),
        "documented_domain": "default medium draw; no overrides",
        "matched_official_profile": (
            "canonical 8x9 two-component input; each component is an extracted official bitmap up to translation"
        ),
        "command": {
            "cwd": "packet_root",
            "argv": [
                "python3",
                "run_with_racket.py",
                "python3",
                "../checks/audit_c1b540a1d7b0_probe.py",
            ],
        },
        "finding": (
            "A non-compositional template rival exactly solves this default generated example "
            "by memorizing the two official component bitmaps."
        ),
    }
    (OUT / "audit-c1b540a1d7b0-counterexample.json").write_text(
        json.dumps(counterexample, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "exact_replays": census["total_exact_official_bitmap_up_to_translation"],
                "draws": census["total_draws"],
                "counterexample_valid": not counterexample["validator_errors"],
                "template_rival_matches_racket": counterexample["rival_matches_actual"],
            },
            indent=2,
        )
    )
    return 0 if counterexample["rival_matches_actual"] and not counterexample["validator_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
