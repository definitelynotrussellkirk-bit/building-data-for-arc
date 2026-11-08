from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

TASK_ID = "b25434a1b56e"
OUT_DIR = Path("../checks/audit") / TASK_ID
GEN_PATH = Path("generators") / TASK_ID / "generator.py"
CANONICAL = Path("shared/data/canonical/puzzles.jsonl")


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise FileNotFoundError(f"canonical row missing for {TASK_ID}")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    pairs: list[dict] = []
    for split in ("train", "test"):
        value = row.get(split, [])
        if isinstance(value, dict):
            value = [value]
        for pair in value:
            if isinstance(pair, dict) and "input" in pair and "output" in pair:
                pairs.append({"input": pair["input"], "output": pair["output"]})
    return pairs


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


GEN = load_generator()


def empty_positions(grid: list[list[int]]) -> list[int]:
    facts = GEN._analyze(grid)
    return [
        index for index, quadrant in enumerate(facts["quadrants"])
        if not quadrant["counts"]
    ]


def horizontal_half_swap(grid: list[list[int]]) -> list[list[int]]:
    half = len(grid[0]) // 2
    return [row[half:] + row[:half] for row in grid]


def right_empty_rival(grid: list[list[int]]) -> list[list[int]]:
    """Correct except it fills only empty right quadrants with global mode."""
    global_color = GEN._global_mode(grid)
    answers: list[int] = []
    for index, values in enumerate(GEN._quadrant_values(grid)):
        local = GEN._mode_nonzero(values)
        answers.append(global_color if local == 0 and index in (1, 3) else local)
    return [answers[:2], answers[2:]]


histogram: Counter[str] = Counter()
generated_matches = 0
generated_total = 0
witness = None
for band_index, band in enumerate(("easy", "medium", "hard")):
    for index in range(200):
        grid = GEN.generate(90_000 + band_index * 10_000 + index, index, difficulty=band)
        positions = empty_positions(grid)
        key = "none" if not positions else ",".join(map(str, positions))
        histogram[key] += 1
        generated_matches += int(right_empty_rival(grid) == GEN.rule_mirror(grid))
        generated_total += 1
        if witness is None and positions == [0]:
            witness = grid

pairs = canonical_pairs()
canonical_matches = sum(right_empty_rival(pair["input"]) == pair["output"] for pair in pairs)
assert witness is not None
right_empty = horizontal_half_swap(witness)

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "right-empty-input.json").write_text(json.dumps(right_empty, indent=2) + "\n")
report = {
    "schema": "arcpuzzles-audit-probe-preapply-v1",
    "task_id": TASK_ID,
    "generator_sha256": sha256(GEN_PATH),
    "generated_census": {
        "seed_policy": "seed=90000 + band_index*10000 + sample_index",
        "sample_indices": "0..199 in each of easy, medium, hard",
        "total": generated_total,
        "empty_quadrant_histogram": dict(sorted(histogram.items())),
        "right_empty_count": histogram.get("1", 0) + histogram.get("3", 0),
        "rival_matches_official": generated_matches,
    },
    "canonical_census": {
        "total": len(pairs),
        "rival_matches_labels": canonical_matches,
    },
    "lawful_counterexample": {
        "construction": "horizontal half-swap of a generated quadrant-0-empty scene",
        "input_path": f"checks/audit/{TASK_ID}/right-empty-input.json",
        "empty_positions": empty_positions(right_empty),
        "self_check": GEN.self_check(right_empty),
        "strict_canonical_like": GEN.strict_canonical_like(right_empty),
        "python_official": GEN.rule_mirror(right_empty),
        "rival": right_empty_rival(right_empty),
    },
    "apply_command": {
        "cwd": "repo",
        "argv": [
            "python3", "-m", "arcpuzzles", "apply", TASK_ID,
            "--input", f"../checks/audit/{TASK_ID}/right-empty-input.json",
            "--check-generator-domain",
            "--out", f"../checks/audit/{TASK_ID}/right-empty-racket.json",
        ],
    },
}
(OUT_DIR / "probe-preapply.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "generator_sha256": report["generator_sha256"],
    "histogram": report["generated_census"]["empty_quadrant_histogram"],
    "rival_matches": generated_matches,
}, sort_keys=True))
