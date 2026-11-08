#!/usr/bin/env python3
"""Read-only cross-check of the retained prototype files; does not run Racket."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import uuid


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid[0]) and row for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def setting_key(setting):
    assert set(setting) == {"min_repeat", "step_blocks"}
    assert type(setting["min_repeat"]) is int and setting["min_repeat"] in (2, 3, 4)
    assert type(setting["step_blocks"]) is int and setting["step_blocks"] in (1, 2)
    return f"m{setting['min_repeat']}_s{setting['step_blocks']}"


def run(evidence, repo):
    evidence = evidence.resolve()
    private = evidence / "private"
    report = json.loads((private / "report.json").read_text())
    assert report["status"] == "bounded_prototype_evidence_passed"
    source_hashes = {}
    for name, info in report["source_identity"].items():
        actual = sha_bytes((repo / info["path"]).read_bytes())
        assert actual == info["sha256"], name
        source_hashes[name] = actual
        if name != "canonical_generator.py":
            assert sha_bytes((private / "source_snapshot" / name).read_bytes()) == actual
    rules = report["rules"]
    assert set(rules) == {f"m{m}_s{s}" for m in (2, 3, 4) for s in (1, 2)}
    for key, rule in rules.items():
        body = (private / "rules" / f"{key}.rkt").read_bytes()
        assert body == rule["program"].encode()
        assert sha_bytes(body) == rule["sha256"]
    assert rules["m2_s1"]["sha256"] == report["canonical_program_sha256"]
    expected_trace = Counter()
    canonical = json.loads((private / "canonical_default.json").read_text())
    assert canonical["pairs_checked"] == len(canonical["pairs"]) == 5
    assert canonical["default_is_exact_canonical_text"] is True
    for pair in canonical["pairs"]:
        assert pair["actual"] == pair["output"]
        expected_trace[(grid_hash(pair["input"]), "m2_s1",
                        grid_hash(pair["actual"]), rules["m2_s1"]["sha256"])] += 1
    seen_inputs, public_paths, shapes, foreground_colors = set(), set(), set(), set()
    pairs_checked = placements_checked = 0
    min_pairwise_witnesses = 7
    explicit_settings = set()
    auto_seeds = []
    for entry in report["episodes"]:
        episode = json.loads((evidence / entry["private"]).read_text())
        selected = setting_key(episode["settings"])
        assert episode["accepted"] is True
        assert episode["source_identity"] == report["source_identity"]
        assert len(episode["pairs"]) == len(episode["draws"]) == 7
        plan = json.loads((private / "plans" / f"episode_{entry['index']:03d}.json").read_text())
        assert all(episode[key] == plan[key] for key in ("seed", "settings", "settings_selection", "draws"))
        if episode["settings_selection"] == "explicit_once":
            explicit_settings.add(selected)
        else:
            assert episode["settings_selection"] == "seeded_once"
            auto_seeds.append(episode["seed"])
        predictions = episode["predictions"]
        assert set(predictions) == set(rules)
        assert all(len(outputs) == 7 for outputs in predictions.values())
        audit = episode["audit"]
        assert audit["candidate_count"] == 6 and audit["rule_applications"] == 42
        assert audit["mirror_parity"] == {"checked": 42, "matched": 42, "failures": []}
        assert audit["all_pairs_have_two_witnesses"] is True
        observed_multiplicities = []
        for i, pair in enumerate(episode["pairs"]):
            grid = pair["input"]
            digest = grid_hash(grid)
            assert digest not in seen_inputs
            seen_inputs.add(digest)
            assert 25 <= len(grid) <= 30 and 25 <= len(grid[0]) <= 30
            shapes.add((len(grid), len(grid[0])))
            foreground_colors.update(cell for row in grid for cell in row if cell != 7)
            corners = Counter((grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]))
            observed_multiplicities.append(max(corners.values()))
            assert max(corners.values()) == episode["draws"][i]["multiplicity"]
            assert pair["output"] == predictions[selected][i]
            for key in rules:
                expected_trace[(digest, key, grid_hash(predictions[key][i]), rules[key]["sha256"])] += 1
        assert Counter(observed_multiplicities[:6]) == {2: 2, 3: 2, 4: 2}
        keys = sorted(rules)
        for i, left in enumerate(keys):
            for right in keys[i + 1:]:
                count = sum(predictions[left][j] != predictions[right][j] for j in range(7))
                assert count >= 2
                min_pairwise_witnesses = min(min_pairwise_witnesses, count)
                pairs_checked += 1
        assert len(audit["query_placements"]) == 7
        assert {row["query_index"] for row in audit["query_placements"]} == set(range(7))
        for row in audit["query_placements"]:
            query = row["query_index"]
            assert len(row["candidates"]) == 6
            assert {setting_key(item["settings"]) for item in row["candidates"]} == set(rules)
            for item in row["candidates"]:
                key = setting_key(item["settings"])
                mismatches = [i for i in range(7) if i != query
                              and predictions[key][i] != episode["pairs"][i]["output"]]
                assert item["demo_mismatch_pair_indexes"] == mismatches
                assert item["fits_demonstrations"] == (not mismatches)
                assert bool(mismatches) == (key != selected)
            assert row["surviving_alternatives"] == []
            assert row["selected_consistent"] is True
            placements_checked += 1
        public_path = evidence / entry["public"]
        assert public_path.parent == evidence / "public"
        assert public_path.name.startswith("challenge_") and public_path.suffix == ".json"
        public_id = public_path.stem.removeprefix("challenge_")
        assert len(public_id) == 32 and uuid.UUID(hex=public_id).version == 4
        assert public_path not in public_paths
        public_paths.add(public_path)
        public = json.loads(public_path.read_text())
        assert public == {
            "train": [{"input": pair["input"], "output": pair["output"]}
                      for pair in episode["pairs"][:6]],
            "test": [{"input": episode["pairs"][6]["input"]}],
        }
    assert set((evidence / "public").glob("*")) == public_paths
    assert explicit_settings == set(rules) and len(auto_seeds) == 1
    trace = [json.loads(line) for line in (private / "racket_trace.jsonl").read_text().splitlines()]
    assert [row["attempt_index"] for row in trace] == list(range(len(trace)))
    assert all(row["status"] == "completed" for row in trace)
    observed_trace = Counter((row["input_sha256"], setting_key(row["settings"]),
                              row["output_sha256"], row["rule_sha256"]) for row in trace)
    assert observed_trace == expected_trace
    assert len(trace) == report["completed_racket_applications"] == report["attempted_racket_applications"] == 299
    assert len(seen_inputs) == report["distinct_episode_inputs"] == 49
    assert len(report["episodes"]) == report["complete_episodes"] == report["attempted_episode_count"] == 7
    assert placements_checked == report["query_placements_checked"] == 49
    witnesses = json.loads((private / "witnesses.json").read_text())
    assert len(witnesses) == 2
    for witness in witnesses:
        assert witness["input_errors"] == []
        different = sum(a != b for left, right in zip(witness["left_output"], witness["right_output"])
                        for a, b in zip(left, right))
        assert different == witness["different_cells"] and different > 0
        for prefix in ("left", "right"):
            key = setting_key(witness[f"{prefix}_settings"])
            expected = (grid_hash(witness["input"]), key,
                        grid_hash(witness[f"{prefix}_output"]), rules[key]["sha256"])
            assert observed_trace[expected] >= 1
    return {
        "status": "retained_evidence_verified", "racket_reexecuted": False,
        "public_challenges_checked": len(public_paths),
        "distinct_episode_inputs": len(seen_inputs), "distinct_grid_shapes": len(shapes),
        "foreground_palette_observed": sorted(foreground_colors),
        "canonical_pairs_checked": 5, "all_setting_racket_results_linked": len(trace),
        "setting_pairs_checked": pairs_checked,
        "minimum_pairwise_witnesses": min_pairwise_witnesses,
        "query_placements_checked": placements_checked,
        "public_query_labels_or_hidden_fields": 0,
        "public_uuid4_names_checked": len(public_paths),
        "automatically_selected_episode_seeds": auto_seeds,
        "rule_sha256": {key: rules[key]["sha256"] for key in sorted(rules)},
        "source_sha256": source_hashes,
        "witness_different_cells": [row["different_cells"] for row in witnesses],
        "evidence_report_sha256": sha_bytes((private / "report.json").read_bytes()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert not args.out.exists(), "verification output already exists"
    result = run(args.evidence, args.repo.resolve())
    result["execution"] = {
        "argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": 0,
        "verifier_sha256": sha_bytes(Path(__file__).read_bytes()),
    }
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
