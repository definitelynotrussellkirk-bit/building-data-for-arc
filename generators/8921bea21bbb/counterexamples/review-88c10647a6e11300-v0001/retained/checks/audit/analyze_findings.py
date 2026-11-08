from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, path


def canonical_row(task_id: str):
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return row
    raise KeyError(task_id)


def occupancy_exact3_rival(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] == 0:
                r += 1
                continue
            start = r
            while r < h and grid[r][c] != 0:
                r += 1
            if r - start == 3:
                out[start][c] = 8
                out[r - 1][c] = 8
    return out


def mixed_exact3(grid):
    h, w = len(grid), len(grid[0])
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] == 0:
                r += 1
                continue
            start = r
            values = []
            while r < h and grid[r][c] != 0:
                values.append(grid[r][c])
                r += 1
            if r - start == 3 and len(set(values)) > 1:
                return True
    return False


def main():
    # Audit 8921bea21bbb: validator accepts a grid on which authority crashes.
    task = "8921bea21bbb"
    mod, gen_path = load_generator(task)
    input_path = ROOT / "checks" / "audit" / task / "input.json"
    grid = json.loads(input_path.read_text())
    racket = json.loads((input_path.parent / "racket.json").read_text())
    finding = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": task,
        "finding": "self_check accepts divider-free input that the authority cannot execute",
        "generator_sha256": sha(gen_path),
        "executed_rule_hash": racket["executed_rule_hash"],
        "seed": None,
        "sample_index": None,
        "overrides": {},
        "input": grid,
        "self_check_errors": mod.self_check(grid),
        "passes_validator": mod.self_check(grid) == [],
        "belongs_to_documented_generator_domain": False,
        "actual_racket_output": racket["results"][0]["output"],
        "actual_racket_error": racket["results"][0]["error"],
        "rival_output": None,
        "command": racket["command"],
        "cwd": racket["cwd"],
        "conclusion": "reproduced validator/authority contract defect",
    }
    (input_path.parent / "finding.json").write_text(
        json.dumps(finding, indent=2, sort_keys=True) + "\n"
    )

    # Audit 50b472d4fc63: mixed-color occupancy shortcut survives all official
    # pairs and all sampled generator defaults, but disagrees on a validator-
    # accepted exact witness.
    task = "50b472d4fc63"
    mod, gen_path = load_generator(task)
    input_path = ROOT / "checks" / "audit" / task / "input.json"
    grid = json.loads(input_path.read_text())
    racket = json.loads((input_path.parent / "racket.json").read_text())
    rival = occupancy_exact3_rival(grid)
    row = canonical_row(task)
    pairs = list(row["train"]) + list(row["test"])
    canonical_matches = [
        occupancy_exact3_rival(pair["input"]) == pair["output"] for pair in pairs
    ]
    sampled = {}
    for band in ("easy", "medium", "hard"):
        hits = 0
        unique = set()
        for i in range(100):
            generated = mod.generate(7000 + i, i * 17 + 3, difficulty=band)
            unique.add(json.dumps(generated, separators=(",", ":")))
            hits += int(mixed_exact3(generated))
        sampled[band] = {
            "draws": 100,
            "unique_inputs": len(unique),
            "mixed_exact3_counterexamples": hits,
        }
    finding = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": task,
        "finding": (
            "wrong rival marks endpoints of every exact three-cell vertical "
            "nonzero occupancy run, ignoring whether the colors match"
        ),
        "generator_sha256": sha(gen_path),
        "executed_rule_hash": racket["executed_rule_hash"],
        "seed": None,
        "sample_index": None,
        "overrides": {},
        "input": grid,
        "self_check_errors": mod.self_check(grid),
        "passes_validator": mod.self_check(grid) == [],
        "belongs_to_documented_generator_domain": False,
        "actual_racket_output": racket["results"][0]["output"],
        "actual_racket_error": racket["results"][0]["error"],
        "rival_output": rival,
        "rival_disagrees_with_authority": rival != racket["results"][0]["output"],
        "canonical_pair_matches": canonical_matches,
        "canonical_pairs_matched": sum(canonical_matches),
        "canonical_pairs_total": len(canonical_matches),
        "default_generator_census": sampled,
        "census_sampler": {
            "bands": ["easy", "medium", "hard"],
            "seeds": "7000..7099",
            "sample_index": "i*17+3",
        },
        "command": racket["command"],
        "cwd": racket["cwd"],
        "conclusion": "reproduced canonical-fitting shortcut absent from sampled generator domain",
    }
    (input_path.parent / "rival_output.json").write_text(
        json.dumps(rival, indent=2) + "\n"
    )
    (input_path.parent / "finding.json").write_text(
        json.dumps(finding, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
