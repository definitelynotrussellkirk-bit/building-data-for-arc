"""Reproduce an undeclared hole-area shortcut for task f563fafba6ac."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path.cwd()
TASK_ID = "f563fafba6ac"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
AUDIT_DIR = REPO.parent / "checks" / "audit" / TASK_ID
INPUT_PATH = AUDIT_DIR / "hole-area-rival-input.json"
RACKET_PATH = AUDIT_DIR / "hole-area-rival-racket.json"
OUTPUT_PATH = AUDIT_DIR / "hole-area-rival-evidence.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("audited_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def enclosed_area(obj: dict) -> int:
    cells = set(obj["cells"])
    height, width = obj["height"], obj["width"]
    background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in cells
    }
    seen: set[tuple[int, int]] = set()
    total = 0
    for start in background:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[tuple[int, int]] = []
        touches_edge = False
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            touches_edge = touches_edge or row in (0, height - 1) or col in (0, width - 1)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in background and point not in seen:
                    seen.add(point)
                    stack.append(point)
        if not touches_edge:
            total += len(component)
    return total


def hole_area_rival(gen, grid):
    return gen._pack(gen._objects(grid), lambda obj: (enclosed_area(obj), obj["color"]))


def canonical_task():
    for line in CANONICAL_PATH.read_text().splitlines():
        item = json.loads(line)
        if item.get("task_id") == TASK_ID:
            return item
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    gen = load_generator()
    task = canonical_task()
    canonical_pairs = task["train"] + task["test"]
    canonical_rows = []
    for index, pair in enumerate(canonical_pairs):
        objects = gen._objects(pair["input"])
        canonical_rows.append(
            {
                "index": index,
                "objects": [
                    {
                        "color": obj["color"],
                        "hole_count": obj["holes"],
                        "enclosed_area": enclosed_area(obj),
                    }
                    for obj in objects
                ],
                "rival_matches_label": hole_area_rival(gen, pair["input"]) == pair["output"],
            }
        )

    generated_total = 0
    generated_matches = 0
    generated_patterns: set[tuple[tuple[int, int], ...]] = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(100):
            grid = gen.generate(1000 + index, index, difficulty=difficulty)
            generated_total += 1
            generated_matches += hole_area_rival(gen, grid) == gen.rule_mirror(grid)
            generated_patterns.add(
                tuple(sorted((obj["holes"], enclosed_area(obj)) for obj in gen._objects(grid)))
            )

    witness_input = json.loads(INPUT_PATH.read_text())["input"]
    racket_record = json.loads(RACKET_PATH.read_text())
    racket_output = racket_record["results"][0]["output"]
    intended_python = gen.rule_mirror(witness_input)
    rival_output = hole_area_rival(gen, witness_input)
    witness_objects = gen._objects(witness_input)

    evidence = {
        "schema": "arcpuzzles-audit-hole-area-rival-v1",
        "task_id": TASK_ID,
        "finding": (
            "Sorting by total enclosed background-cell area, then color, fits every canonical "
            "pair and every sampled generated input because hole count and enclosed area are "
            "perfectly correlated in the current shape grammar."
        ),
        "generator_sha256": sha256(GENERATOR_PATH),
        "canonical_sha256": sha256(CANONICAL_PATH),
        "executed_rule_hash": racket_record["executed_rule_hash"],
        "canonical_pairs_total": len(canonical_pairs),
        "canonical_pairs_fit": sum(row["rival_matches_label"] for row in canonical_rows),
        "canonical_rows": canonical_rows,
        "generated_sample": {
            "draws": generated_total,
            "rival_matches": generated_matches,
            "difficulties": [None, "easy", "medium", "hard"],
            "draws_per_difficulty": 100,
            "observed_hole_count_enclosed_area_patterns": [
                [list(pair) for pair in pattern] for pattern in sorted(generated_patterns)
            ],
        },
        "counterexample": {
            "input_path": str(INPUT_PATH.relative_to(REPO.parent)),
            "racket_path": str(RACKET_PATH.relative_to(REPO.parent)),
            "generator_domain": racket_record["results"][0]["generator_domain"],
            "objects": [
                {
                    "color": obj["color"],
                    "hole_count": obj["holes"],
                    "enclosed_area": enclosed_area(obj),
                    "area": obj["area"],
                    "height": obj["height"],
                    "width": obj["width"],
                }
                for obj in witness_objects
            ],
            "python_matches_racket": intended_python == racket_output,
            "intended_output": racket_output,
            "hole_area_rival_output": rival_output,
            "outputs_disagree": racket_output != rival_output,
        },
        "generator_emits_distinguishing_cases": generated_matches != generated_total,
        "limitations": (
            "Finite audit: canonical pairs plus 400 deterministic generated draws. The exact "
            "witness is accepted by current self_check and Racket establishes the intended label."
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUTPUT_PATH),
        "canonical_fit": f"{evidence['canonical_pairs_fit']}/{evidence['canonical_pairs_total']}",
        "generated_fit": f"{generated_matches}/{generated_total}",
        "counterexample_disagrees": evidence["counterexample"]["outputs_disagree"],
        "generator_emits_distinguishing_cases": evidence["generator_emits_distinguishing_cases"],
    }, indent=2))


if __name__ == "__main__":
    main()
