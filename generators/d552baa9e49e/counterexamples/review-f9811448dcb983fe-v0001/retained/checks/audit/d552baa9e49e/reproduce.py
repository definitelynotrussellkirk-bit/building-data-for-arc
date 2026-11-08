"""Findings-only audit: command meanings can be absent from a generated lesson.

Run from the packet root:
    python3 review.py run ../.venv-review/bin/python ../checks/audit/d552baa9e49e/reproduce.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "d552baa9e49e"
EXPECTED_SOURCE = "78b013356c78b80565774363b6dd3eed029b9f825c4a343325f0822c32ccbc5a"
BANDS = ("easy", "medium", "hard")
OUT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def crop_content(grid):
    cells = [
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0 and (row, column) != (0, 0)
    ]
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    return [row[col0:col1 + 1] for row in grid[row0:row1 + 1]]


def predict(grid, swap=None):
    """Independent transform table; a rival exchanges two command meanings."""
    command = grid[0][0]
    if swap:
        first, second = swap
        command = second if command == first else first if command == second else command
    crop = crop_content(grid)
    if command == 1:
        return [list(row) for row in zip(*crop[::-1])]
    if command == 2:
        return [row[::-1] for row in crop[::-1]]
    if command == 3:
        return [list(row) for row in zip(*crop)]
    if command == 4:
        return [row[::-1] for row in crop]
    if command == 5:
        return crop[::-1]
    raise ValueError(command)


def rival_witness(pairs):
    commands = [pair["input"][0][0] for pair in pairs]
    demonstrated = set(commands[:3])
    query_command = commands[3]
    if query_command in demonstrated:
        return None
    other_unseen = min(set(range(1, 6)) - demonstrated - {query_command})
    swap = (query_command, other_unseen)
    predictions = [predict(pair["input"], swap) for pair in pairs]
    assert all(predictions[i] == pairs[i]["output"] for i in range(3))
    assert predictions[3] != pairs[3]["output"]
    return {
        "commands": commands,
        "swap_commands": list(swap),
        "all_three_demonstrations_fit": True,
        "query_prediction_differs": True,
        "query_output": pairs[3]["output"],
        "rival_query_output": predictions[3],
        "query_input_sha256": digest(pairs[3]["input"]),
        "query_output_sha256": digest(pairs[3]["output"]),
        "rival_query_output_sha256": digest(predictions[3]),
    }


def main():
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    assert source_sha == EXPECTED_SOURCE, (source_sha, EXPECTED_SOURCE)
    catalog = Catalog(root)
    canonical = canonical_pairs(TASK_ID, root=root)
    assert all(predict(pair["input"]) == pair["output"] for pair in canonical)

    draws = []
    for difficulty in BANDS:
        for sample_index in range(23):
            grid = generator.generate(0, sample_index, difficulty=difficulty)
            assert generator.self_check(grid, difficulty=difficulty) == []
            draws.append({"difficulty": difficulty, "seed": 0, "sample_index": sample_index, "input": grid})

    authority_receipts = []
    for start in range(0, len(draws), 64):
        batch = draws[start:start + 64]
        receipt = catalog.apply(TASK_ID, [draw["input"] for draw in batch], timeout=60)
        assert receipt["generator_sha256"] == source_sha
        assert receipt["rule_hash_matches_catalog"]
        for draw, result in zip(batch, receipt["results"], strict=True):
            assert result["output"] is not None, result
            assert predict(draw["input"]) == result["output"]
            draw.update({"output": result["output"], "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"]})
        authority_receipts.append(receipt)

    census = []
    for difficulty in BANDS:
        band_draws = [draw for draw in draws if draw["difficulty"] == difficulty]
        for start in range(20):
            window = band_draws[start:start + 4]
            witness = rival_witness(window)
            census.append({
                "difficulty": difficulty,
                "seed": 0,
                "start": start,
                "sample_indices": [draw["sample_index"] for draw in window],
                "commands": [draw["input"][0][0] for draw in window],
                "input_sha256": [draw["input_sha256"] for draw in window],
                "ambiguous_under_command_permutation": witness is not None,
                "witness": witness,
            })

    production = catalog.generate(TASK_ID, count=1, seed=0, sample_index=1, difficulty="medium", timeout=60)[0]
    production_pairs = production["train"] + production["test"]
    production_witness = rival_witness(production_pairs)
    assert production["sample_indices"] == [1, 2, 3, 4]
    assert production_witness is not None
    assert production_witness["commands"] == [2, 3, 1, 4]
    assert production["rejections"] == []

    report = {
        "schema": "d552baa9e49e-focused-audit-v1",
        "task_id": TASK_ID,
        "source_path_relative_to_root": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "interpreter": sys.executable,
        "hash_encoding": "SHA-256 of UTF-8 json.dumps(value, sort_keys=True, separators=(',', ':'))",
        "scope": {"seed": 0, "difficulty_bands": list(BANDS), "draw_indices": [0, 22], "lesson_starts": [0, 19], "demonstrations": 3, "queries": 1},
        "canonical_label_matches": len(canonical),
        "authoritative_generated_label_matches": len(draws),
        "ambiguous_windows": sum(row["ambiguous_under_command_permutation"] for row in census),
        "total_windows": len(census),
        "per_band": {band: {"ambiguous": sum(row["ambiguous_under_command_permutation"] for row in census if row["difficulty"] == band), "checked": 20} for band in BANDS},
        "census": census,
        "draws": draws,
        "authority_receipts": authority_receipts,
        "production_recipe": {"api": "Catalog.generate", "task_id": TASK_ID, "count": 1, "seed": 0, "sample_index": 1, "difficulty": "medium", "n_train": "omitted; EXAMPLES_NEEDED resolves to 3", "n_test": "omitted; resolves to 1"},
        "production_episode": production,
        "production_witness": production_witness,
        "limitations": ["Finite census: only seed 0 and 20 consecutive lesson starts in each band were measured.", "Aligned starts divisible by four repeat a demonstrated query command; the reproduced gap concerns other supported starts.", "No sampled canonical-authority output mismatch was found; the issue is lesson identifiability among command permutations.", "No audited generator, test, note, rule, or approval record was modified."],
    }
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generator_sha256": source_sha, "canonical_label_matches": len(canonical), "authoritative_generated_label_matches": len(draws), "ambiguous_windows": report["ambiguous_windows"], "total_windows": len(census), "per_band": report["per_band"], "production_sample_indices": production["sample_indices"], "production_witness": production_witness, "report": str(path)}, indent=2))


if __name__ == "__main__":
    main()
