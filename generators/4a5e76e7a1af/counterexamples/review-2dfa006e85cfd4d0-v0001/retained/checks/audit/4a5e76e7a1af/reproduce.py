"""Reproduce the missed extended-index teaching witness on the pinned source.

Run through WORK/run_with_racket.py from WORK; its payload cwd is WORK/repo.
The saved lesson was materialized by the public production sampler. This
script regenerates its inputs, evaluates the source's gates, and obtains a
fresh canonical Racket query output through the public apply command.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile


TASK_ID = "4a5e76e7a1af"
GENERATOR_SHA256 = "7b5cde03f89ae8725b5508b9742dc9b5c8c062bb27f650d74ec6a0f27d78aa63"
CANONICAL_PROGRAM_SHA256 = "d4a2e13aeda34b22a1671d250ef80b44ef90199b34be39e8e815091002fde8df"
RULE_HASH = "d4a2e13aeda3"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def clamp_indices_to_three(grid):
    """Independent rival: 1 selects first, 2 second, all larger indices third."""
    result = [[0] * 11 for _ in range(3)]
    for output_left in (0, 4, 8):
        index, code, color = grid[4][output_left:output_left + 3]
        source_left = 4 * (min(index, 3) - 1)
        panel = [row[source_left:source_left + 3] for row in grid[:3]]
        if code == 2:
            panel = [list(row) for row in zip(*panel[::-1])]
        elif code == 3:
            panel = [row[::-1] for row in panel]
        elif code == 4:
            panel = panel[::-1]
        else:
            assert code == 1
        for r in range(3):
            for c in range(3):
                result[r][output_left + c] = color if panel[r][c] else 0
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("receipt.json"))
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    assets = Path(__file__).resolve().parent
    source = repo / "generators" / TASK_ID / "generator.py"
    assert digest(source.read_bytes()) == GENERATOR_SHA256, "audit source changed"
    spec = importlib.util.spec_from_file_location("audited_generator_4a5e76e7a1af", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    assert generator.RULE_HASH == RULE_HASH

    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    canonical_rows = []
    for line in canonical_path.open():
        if TASK_ID not in line:
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            canonical_rows.append(row)
    assert len(canonical_rows) == 1
    canonical = canonical_rows[0]
    assert digest(canonical["program_solution"].encode()) == CANONICAL_PROGRAM_SHA256

    lesson_path = assets / "production-hard-seed0.jsonl"
    episode = json.loads(lesson_path.read_text())
    assert episode["provenance"]["generator_sha256"] == GENERATOR_SHA256
    assert episode["executed_rule_hash"] == RULE_HASH
    assert episode["sample_indices"] == [0, 1, 2, 3, 4]
    assert episode["rejections"] == []
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 4 and len(episode["test"]) == 1

    acceptance = []
    for index, pair in enumerate(pairs):
        regenerated = generator.generate(0, index, difficulty="hard")
        assert regenerated == pair["input"], "saved production input failed replay"
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        checks = {
            "self_check": generator.self_check(pair["input"]),
            "strict_canonical_like": generator.strict_canonical_like(pair["input"]),
            "generated_teaching_gate": generator._teaching_errors(pair["input"]),
        }
        assert all(value == [] for value in checks.values())
        acceptance.append({"sample_index": index, **checks})

    hook_reasons = generator.lesson_identifiable(episode["train"], episode["test"][0])
    assert hook_reasons == []
    assert episode["lesson_check"]["status"] == "passed_declared_hook"
    demo_fits = [clamp_indices_to_three(pair["input"]) == pair["output"] for pair in episode["train"]]
    assert demo_fits == [True] * 4
    canonical_pairs = canonical["train"] + canonical["test"]
    canonical_fits = [clamp_indices_to_three(pair["input"]) == pair["output"] for pair in canonical_pairs]
    assert canonical_fits == [True] * 5

    query = episode["test"][0]
    assert json.loads((assets / "input.json").read_text()) == query["input"]
    with tempfile.TemporaryDirectory(prefix="audit-4a5e76e7a1af-") as temporary:
        output_path = Path(temporary) / "racket.json"
        argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK_ID,
                "--input", str(assets / "input.json"), "--out", str(output_path)]
        completed = subprocess.run(argv, cwd=repo, capture_output=True, text=True)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        fresh_racket = json.loads(output_path.read_text())
    assert fresh_racket["executed_rule_hash"] == RULE_HASH
    assert fresh_racket["generator_sha256"] == GENERATOR_SHA256
    executed = fresh_racket["results"][0]
    assert executed["error"] is None and executed["valid_output"] is True
    assert executed["output"] == query["output"]
    assert json.loads((assets / "racket.json").read_text())["results"][0]["output"] == executed["output"]
    rival = clamp_indices_to_three(query["input"])
    assert rival != executed["output"]
    differences = [[r, c] for r in range(3) for c in range(11) if rival[r][c] != executed["output"][r][c]]
    (assets / "rival.json").write_text(json.dumps(rival) + "\n")

    rotations = []
    for held_out, pair in enumerate(pairs):
        fits = all(clamp_indices_to_three(other["input"]) == other["output"]
                   for index, other in enumerate(pairs) if index != held_out)
        differs = clamp_indices_to_three(pair["input"]) != pair["output"]
        rotations.append({"query_sample_index": held_out, "fits_remaining_four_demos": fits,
                          "changes_query": differs, "undistinguished": fits and differs})

    receipt = {
        "schema": "arcpuzzles-audit-teaching-witness-v1", "task_id": TASK_ID,
        "verdict": "reproduced_teaching_defect", "source_modified": False,
        "generator_sha256": GENERATOR_SHA256, "generator_version": generator.VERSION,
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "canonical_ledger_sha256": digest(canonical_path.read_bytes()),
        "rule_hash": RULE_HASH, "fresh_apply_rule_text_sha256": fresh_racket["rule_text_sha256"],
        "production": {"seed": 0, "difficulty": "hard", "overrides": {},
                       "sample_indices": episode["sample_indices"], "rejections": [],
                       "demonstrations": 4, "queries": 1,
                       "lesson_check": episode["lesson_check"],
                       "all_saved_inputs_regenerated_exactly": True},
        "acceptance": acceptance, "lesson_identifiable_reasons": hook_reasons,
        "demo_indices": [[pair["input"][4][left] for left in (0, 4, 8)] for pair in episode["train"]],
        "query_indices": [query["input"][4][left] for left in (0, 4, 8)],
        "rival": {"name": "clamp_indices_to_three", "canonical_pair_fits": canonical_fits,
                  "production_demo_fits": demo_fits, "query_differs": True,
                  "different_query_cells": differences,
                  "actual_racket_first_panel": [row[:3] for row in executed["output"]],
                  "rival_first_panel": [row[:3] for row in rival]},
        "racket_replay": {"exit_code": completed.returncode, "valid_output": True,
                          "output_matches_saved_production_query": True,
                          "input_sha256": executed["input_sha256"], "output_sha256": executed["output_sha256"]},
        "same_lesson_query_rotations": {"count": 5, "undistinguished_count": sum(r["undistinguished"] for r in rotations),
                                        "rows": rotations},
        "evidence_sha256": {name: digest((assets / name).read_bytes()) for name in
                            ("production-hard-seed0.jsonl", "input.json", "racket.json", "rival.json", "reproduce.py")},
        "command_records": "checks/audit/4a5e76e7a1af/commands.json",
        "limits": "One source-bound production lesson plus all five canonical pairs; five query rotations of the same materialized lesson. No population frequency or other-seed claim."
    }
    assert digest(source.read_bytes()) == GENERATOR_SHA256
    args.out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"verdict": receipt["verdict"], "canonical_fits": sum(canonical_fits),
                      "demo_fits": sum(demo_fits), "query_difference_cells": differences,
                      "self_and_teaching_gates_accept": True, "lesson_hook_reasons": hook_reasons,
                      "racket_apply_exit_code": completed.returncode, "receipt": str(args.out)}))


if __name__ == "__main__":
    main()
