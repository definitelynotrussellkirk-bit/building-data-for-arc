"""Compare retained independent audit expectations with public Racket output."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


OUT = Path(__file__).resolve().parent
PACKET = OUT.parents[2]
TASK_ID = "561ebfa521f0"
sys.path.insert(0, str(PACKET / "repo" / "shared" / "runtime"))
from src.core.canonical_pairs import iter_task_rows


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    report = read("probe-report.json")
    receipt = read("racket.json")
    expected = read("independent-output.json")
    rivals = read("rival-output.json")
    inputs = read("input.json")
    assert receipt["task_id"] == TASK_ID
    assert receipt["reference"] == "canonical"
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(inputs) == 11
    current_hash = hashlib.sha256((PACKET / "repo" / "generators" / TASK_ID / "generator.py").read_bytes()).hexdigest()
    assert current_hash == report["generator_sha256"] == receipt["generator_sha256"]
    canonical_rows = list(iter_task_rows(TASK_ID, PACKET / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"))
    assert len(canonical_rows) == 1
    assert hashlib.sha256(canonical_rows[0]["program_solution"].encode("utf-8")).hexdigest() == report["canonical_program_sha256_utf8"]
    results = []
    for index, item in enumerate(receipt["results"]):
        assert item["index"] == index
        assert item["input"] == inputs[index]
        assert item["error"] is None
        assert item["valid_output"] is True
        assert item["output"] == expected[index], index
        different = [{"row": r, "col": c, "racket": value, "rival": rivals[index][r][c]}
                     for r, row in enumerate(item["output"]) for c, value in enumerate(row)
                     if value != rivals[index][r][c]]
        results.append({"input_index": index, "independent_bfs_matches_racket": True,
                        "rival_matches_racket": not different, "different_cells": different})
    assert all(case["rival_matches_racket"] for case in results[:3])
    assert results[4]["different_cells"] == [
        {"row": 5, "col": 4, "racket": 0, "rival": 8},
        {"row": 5, "col": 5, "racket": 0, "rival": 8},
    ]
    assert not any(case["rival_matches_racket"] for case in results[5:10])
    source_identity = {key: receipt[key] for key in (
        "task_id", "reference", "executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256"
    )}
    counterexample = {
        "finding_id": "F5", "classification": "reproduced finite-rival teaching ambiguity",
        **source_identity,
        "canonical_program_sha256_utf8": report["canonical_program_sha256_utf8"],
        "episode": report["selected_episode"],
        "rival_definition": "For 2-to-4 and 4-to-3, paint every zero in the endpoints' axis-aligned bounding rectangle color 8; preserve other cells.",
        "rival_fits_all_canonical_pairs": False,
        "rival_canonical_matches": 0, "canonical_pair_denominator": 5,
        "generated_cases": [{
            "seed": report["selected_episode"]["seed"],
            "difficulty": report["selected_episode"]["difficulty"],
            "sample_index": index, "overrides": {},
            "role": "demo" if index < 3 else "query",
            "input": inputs[index], "racket_output": receipt["results"][index]["output"],
            "rival_output": rivals[index], **report["selected_inputs"][index],
            "different_cells": results[index]["different_cells"],
        } for index in range(5)],
        "separate_validator_counterexample": {
            **report["hand_built_case"], "input": inputs[10],
            "racket_output": receipt["results"][10]["output"], "rival_output": rivals[10],
        },
        "public_apply_command": {
            "cwd": "packet_root",
            "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                     "--input", "../checks/audit/561ebfa521f0/input.json", "--out", "../checks/audit/561ebfa521f0/racket.json"],
            "exit_code": 0, "actual_runtime_cwd": receipt["cwd"],
        },
    }
    dump("counterexample.json", counterexample)
    verification = {
        "finding_id": "F5", **source_identity, "racket_cases_checked": 11,
        "racket_parity_passed": 11, "results": results,
        "ambiguous_episodes_by_band": dict(Counter(case["difficulty"] for case in report["ambiguous_episodes"])),
        "note": "300-episode counts use independent BFS; 11 retained cases were executed through public canonical Racket apply.",
        "target_generator_unchanged": True,
        "target_canonical_program_unchanged": True,
    }
    dump("verification-report.json", verification)
    section = f"""## 561ebfa521f0

### F5: Three demonstrations can conceal whether walls constrain the highlighted paths

**Classification: reproduced finite-rival teaching ambiguity.** The target was audited after the main repair and was left unchanged. This is a generated-lesson weakness; the audit found no wrong canonical Racket labels or default inputs outside the independently checked reachable-marker domain.

The intended rule highlights all empty cells on any shortest path from red (2) to yellow (4), then from yellow (4) to green (3), treating gray (5) cells as walls. The independent rival instead paints every empty cell in each marker pair's axis-aligned bounding rectangle. It preserves walls and markers but ignores whether walls make a particular rectangle cell unavailable to a shortest route. It is an intentional teaching negative, not a submitted solve.

**Concrete reproduction:** generate easy seed 40 with no overrides. Use sample indices 0, 1, 2 as demonstrations and 3, 4 as queries. The rival matches all three demonstration outputs and the first query. On query 4 it wrongly paints zero-based cells (5, 4) and (5, 5) cyan (8); canonical Racket leaves both zero. A wall at (5, 3) prevents those two cells from participating in a shortest route to the checkpoint. All five generated inputs pass the target's self_check and independent border, palette, marker-count and reachability checks. See [counterexample.json](checks/audit/561ebfa521f0/counterexample.json), which retains every input, actual Racket output, rival output, exact seed/index/overrides, source hashes and domain assessments.

**Measured scope:** generator SHA256 `{current_hash}`, version 2.1.0; seeds 0–99, sample indices 0–4, each of easy/medium/hard, no overrides. The policy above yields 300 episodes and 1,500 distinct inputs. The probe found 16 ambiguous episodes: 7/100 easy, 7/100 medium and 2/100 hard. All 1,500 draws passed the recorded structural/reachability checks, with zero identity outputs under independent BFS. These are individual five-input episodes with start index 0; other cyclic starts were not tested. Full counts and seed lists are in [probe-report.json](checks/audit/561ebfa521f0/probe-report.json).

**Canonical and runtime checks:** the independent BFS agrees with all five canonical pairs. This rectangle rival agrees with 0/5 canonical pairs, so it is explicitly not a shortcut compatible with the complete canonical evidence. Public apply executed 11 retained grids: the five generated episode inputs, all five canonical inputs, and the separate validator probe described below. Independent BFS and canonical Racket agreed 11/11. The 300-episode scan used independent BFS; it was not a 1,500-grid Racket run. See [racket.json](checks/audit/561ebfa521f0/racket.json) and [verification-report.json](checks/audit/561ebfa521f0/verification-report.json).

**Separate validator domain gap:** input batch index 10 is a hand-built 7×9 wall-bordered grid with exactly one marker of each required color and five interior walls. Its wall barrier disconnects red from both other markers. self_check returns an empty list, although reachability is an explicit invariant. This example is deliberately outside the documented reachable-marker domain and was not emitted by generate. Racket highlights only the reachable yellow-to-green leg; the validator does not expose the missing red-to-yellow route. The input, output and failed independent domain assessment are retained in the same counterexample file. This is a validator gap, not evidence that the default sampler generated unreachable markers.

**Suggested follow-up, not applied:** require a demonstration in which walls invalidate the bounding-rectangle rival before accepting a three-demo lesson, and verify full lesson rival disagreement rather than individual-grid validity alone. Add the already-used reachability criterion to self_check so its acceptance aligns with the stated domain. No generator, reference rule or approval status was changed.

**Source binding:** canonical executed rule hash `{receipt['executed_rule_hash']}`; actual runtime rule-text SHA256 `{receipt['rule_text_sha256']}`; exact canonical program payload SHA256 `{report['canonical_program_sha256_utf8']}`. The public receipt confirms the executed rule hash matches the catalog and records the runtime command and directory. The different full rule hashes refer to the runtime rule text and the canonical payload respectively.

**Reproduction commands:** [commands.json](checks/audit/561ebfa521f0/commands.json) records the three successful commands from packet_root. [probe.py](checks/audit/561ebfa521f0/probe.py) and [verify.py](checks/audit/561ebfa521f0/verify.py) are the complete retained reproducers; neither imports private reference-runner functions. The supported wrapper changes its working directory to repo, as recorded by public apply. Both target generator and canonical rule were read-only throughout this audit.
"""
    (OUT / "SECTION.md").write_text(section, encoding="utf-8")
    print(json.dumps({"racket_parity": "11/11", "generator_unchanged": True,
                      "ambiguous_episodes": report["ambiguous_episode_count"],
                      "query4_different_cells": results[4]["different_cells"]}, indent=2))


if __name__ == "__main__":
    main()
