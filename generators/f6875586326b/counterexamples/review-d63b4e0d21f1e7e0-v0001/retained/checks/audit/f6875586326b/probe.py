from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "f6875586326b"
EXPECTED_GENERATOR_SHA256 = "f262727b63ac346ada9629560fadf7eb45343fb5c944c9576b1322d5c70fd839"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
INPUT_PATH = HERE / "input.json"
RACKET_PATH = HERE / "racket-output.json"
OUTPUT_PATH = HERE / "probe.json"


def load_module():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load audited generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict[str, Any]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError("canonical task row not found")


def all_background(grid: list[list[int]]) -> list[list[int]]:
    return [[0 for _ in row] for row in grid]


def conditional_rival(grid: list[list[int]], intended_output: list[list[int]]) -> list[list[int]]:
    colors = {value for row in grid for value in row}
    return intended_output if {1, 3} <= colors else all_background(grid)


def main() -> None:
    generator_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    if generator_sha256 != EXPECTED_GENERATOR_SHA256:
        raise AssertionError(
            f"audited source changed: {generator_sha256} != {EXPECTED_GENERATOR_SHA256}"
        )

    gen = load_module()
    row = canonical_row()
    canonical_pairs = list(row["train"]) + list(row["test"])
    canonical_details = []
    for index, pair in enumerate(canonical_pairs):
        intended = pair["output"]
        rival = conditional_rival(pair["input"], intended)
        canonical_details.append(
            {
                "pair_index": index,
                "input_colors": sorted({value for values in pair["input"] for value in values}),
                "rival_matches_output": rival == intended,
            }
        )

    sample_details = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        with_both = 0
        validator_pass = 0
        for i in range(100):
            seed = 710_000 + 1_000 * band_index + i
            sample_index = 17_000 + i
            grid = gen.generate(seed, sample_index, difficulty=band)
            colors = {value for values in grid for value in values}
            with_both += int({1, 3} <= colors)
            validator_pass += int(not gen.self_check(grid, difficulty=band))
        sample_details.append(
            {
                "difficulty": band,
                "draws": 100,
                "draws_with_both_horizontal_colors": with_both,
                "validator_pass": validator_pass,
            }
        )

    witness = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    racket = json.loads(RACKET_PATH.read_text(encoding="utf-8"))
    result = racket["results"][0]
    intended = result["output"]
    rival = conditional_rival(witness, intended)
    differences = [
        {"row": r, "col": c, "intended": intended[r][c], "rival": rival[r][c]}
        for r in range(len(witness))
        for c in range(len(witness[0]))
        if intended[r][c] != rival[r][c]
    ]

    payload = {
        "schema": "arcpuzzles-audit-probe-v1",
        "classification": "possible shortcut",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha256,
        "rule_hash": racket["executed_rule_hash"],
        "finding": "The generated teaching domain always includes both horizontal marker colors, so a conditional rule can fit every canonical and generated lesson while failing a lawful one-color case.",
        "rival": "Apply the intended projection only when both colors 1 and 3 appear; otherwise return all background.",
        "canonical_pairs": {
            "total": len(canonical_details),
            "fit_by_rival": sum(item["rival_matches_output"] for item in canonical_details),
            "details": canonical_details,
        },
        "generated_samples": sample_details,
        "generated_samples_total": sum(item["draws"] for item in sample_details),
        "generated_samples_with_both_horizontal_colors": sum(
            item["draws_with_both_horizontal_colors"] for item in sample_details
        ),
        "witness": {
            "input": witness,
            "self_check": gen.self_check(witness),
            "canonical_racket_output": intended,
            "rival_output": rival,
            "differences": differences,
            "outputs_differ": intended != rival,
            "domain_note": "Uses only the task's documented colors and isolated singleton markers, but intentionally omits green; the current teaching validator rejects exactly that missing branch.",
        },
        "racket_evidence": str(RACKET_PATH.relative_to(WORK)),
    }
    if not all(item["rival_matches_output"] for item in canonical_details):
        raise AssertionError("rival does not fit every canonical pair")
    if payload["generated_samples_with_both_horizontal_colors"] != payload["generated_samples_total"]:
        raise AssertionError("sampled generator unexpectedly emitted a one-color lesson")
    if intended == rival or not differences:
        raise AssertionError("witness does not distinguish the rival")
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "generator_sha256": generator_sha256,
                "canonical_pairs_fit": [payload["canonical_pairs"]["fit_by_rival"], len(canonical_details)],
                "generated_samples_with_both": [
                    payload["generated_samples_with_both_horizontal_colors"],
                    payload["generated_samples_total"],
                ],
                "witness_differences": len(differences),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
