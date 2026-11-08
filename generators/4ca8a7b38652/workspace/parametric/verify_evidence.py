#!/usr/bin/env python3
"""Inspect retained parametric evidence without re-executing or relabeling it."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from reviewer_support import find_root, load_selected_generator

TASK_ID = "4ca8a7b38652"
EXPECTED_SELECTED_SHA256 = "9e39ddd0012e5dba7be9e7ae10f3ac8de0ca736e8c7bfad79a3535b4ae352ac5"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_sha(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())


def independent_output(grid, scope):
    colors = set(sum(grid, []))
    if scope == "nonzero":
        colors.discard(0)
    factor = len(colors)
    return [[grid[r // factor][c // factor] for c in range(3 * factor)]
            for r in range(3 * factor)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    root = Path(find_root(__file__))
    source = Path(__file__).with_name("prototype.py")
    spec = importlib.util.spec_from_file_location("count_scope_evidence_audit", source)
    proto = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(proto)
    generator, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    assert generator_sha == EXPECTED_SELECTED_SHA256, "selected generator source changed"
    canonical = proto.canonical_source(root=root)
    programs = {setting: proto.materialize_rule(setting, source=canonical) for setting in proto.SETTINGS}
    rows = []
    global_inputs = []
    global_queries = []
    for directory in args.exports:
        manifest = json.loads((directory / "evidence.json").read_text())
        assert manifest["prototype_source_sha256"] == sha(source.read_bytes())
        assert manifest["selected_generator_sha256"] == generator_sha
        assert set(manifest["records"]) == set(proto.SETTINGS)
        expected_public_paths = set()
        for setting, record in manifest["records"].items():
            private_path = directory / record["private_episode"]
            private_raw = private_path.read_bytes()
            episode = json.loads(private_raw)
            meta = episode["meta"]
            train, queries = episode["train"], episode["test"]
            pairs = train + queries
            expected_count = manifest["requested_counts"]
            assert len(train) == expected_count["train"] >= 1
            assert len(queries) == expected_count["test"] == 4
            assert record["actual_counts"] == expected_count
            assert meta["train_count"] == len(train) and meta["test_count"] == len(queries)
            assert meta["count_scope"] == setting
            assert meta["seed"] == record["seed"]
            assert proto.choose_setting(meta["seed"]) == setting
            assert meta["prototype_source_sha256"] == manifest["prototype_source_sha256"]
            assert meta["selected_generator_sha256"] == generator_sha
            assert sha(private_raw) == record["private_episode_file_sha256"]
            assert json_sha(episode) == record["private_episode_sha256"]
            program_raw = (directory / record["rule"]).read_bytes()
            assert program_raw == programs[setting].encode() == episode["program"].encode()
            assert sha(program_raw) == record["rule_sha256"] == meta["program_sha256"]
            assert meta["racket_verified"] is True
            assert meta["racket_evaluations"] == len(pairs) * len(proto.SETTINGS)
            assert record["racket_evaluations"] == meta["racket_evaluations"]
            assert meta["racket_evaluations_by_setting"] == dict.fromkeys(proto.SETTINGS, len(pairs))
            assert meta["query_labels_racket_verified"] == len(queries)
            assert record["query_labels_racket_verified"] == len(queries)
            for value in proto.SETTINGS:
                assert meta["evaluated_program_sha256"][value] == sha(programs[value].encode())
            inputs = [json_sha(pair["input"]) for pair in pairs]
            assert len(set(inputs)) == len(pairs) == record["unique_inputs"]
            assert meta["input_sha256"] == inputs
            assert meta["sampling"]["unique_inputs"] == len(pairs)
            for pair in pairs:
                assert generator.self_check(pair["input"]) == []
                assert pair["output"] == independent_output(pair["input"], setting)
            audit = meta["query_identifiability"]
            assert record["query_identifiability"] == audit
            fits = {
                value: all(independent_output(pair["input"], value) == pair["output"] for pair in train)
                for value in proto.SETTINGS
            }
            assert audit["consistent_settings"] == [value for value in proto.SETTINGS if fits[value]]
            assert audit["consistent_settings"] == [setting]
            assert len(audit["queries"]) == len(queries)
            for value in proto.SETTINGS:
                if value == setting:
                    continue
                refuting = [index for index, pair in enumerate(train)
                            if independent_output(pair["input"], value) != pair["output"]]
                assert audit["rivals"][value]["refuting_demo_indices"] == refuting
                assert audit["rivals"][value]["fits_demonstrations"] == fits[value]
                assert refuting
            query_checks = []
            for index, pair in enumerate(queries):
                checked = audit["queries"][index]
                assert checked["query_index"] == index
                assert checked["identified_from_demonstrations"] is True
                for value in proto.SETTINGS:
                    if value == setting:
                        continue
                    agrees = independent_output(pair["input"], value) == pair["output"]
                    rival = checked["rivals"][value]
                    assert rival["fits_demonstrations"] == fits[value]
                    assert rival["agrees_with_selected"] == agrees
                    assert rival["ambiguous"] == (fits[value] and not agrees) is False
                query_checks.append({"query_index": index, "input_sha256": json_sha(pair["input"]),
                                     "output_shape": [len(pair["output"]), len(pair["output"][0])],
                                     "identified_from_demos": True})
            public_path = directory / record["public_challenge"]
            expected_public_paths.add(public_path)
            assert public_path.parent == directory / "public"
            assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", public_path.name)
            public_raw = public_path.read_bytes()
            public = json.loads(public_raw)
            assert set(public) == {"schema", "train", "test"}
            assert public["schema"] == "arcpuzzles-challenge-v1"
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert public["train"] == train
            assert public["test"] == [{"input": pair["input"]} for pair in queries]
            assert public_path.name == "challenge-" + json_sha(public) + ".json"
            assert sha(public_raw) == record["public_challenge_file_sha256"]
            assert json_sha(public) == record["public_challenge_sha256"]
            global_inputs.extend(inputs)
            global_queries.extend(json_sha(pair["input"]) for pair in queries)
            rows.append({"export": str(directory), "setting": setting, "seed": meta["seed"],
                         "counts": record["actual_counts"], "unique_inputs": len(set(inputs)),
                         "duplicate_rejections": meta["sampling"]["duplicate_rejections"],
                         "difficulty_bands": sorted({row["difficulty"] for row in meta["profile_sequence"]}),
                         "rule_sha256": record["rule_sha256"],
                         "racket_evaluations": meta["racket_evaluations"], "queries": query_checks,
                         "public_challenge": str(public_path), "private_episode": str(private_path)})
        assert set((directory / "public").iterdir()) == expected_public_paths
        assert manifest["racket_evaluations"] == sum(row["racket_evaluations"] for row in manifest["records"].values())
    report = {
        "schema": "arcpuzzles-parametric-v2-evidence-audit-v1", "status": "pass",
        "prototype_source_sha256": sha(source.read_bytes()),
        "audit_source_sha256": sha(Path(__file__).read_bytes()),
        "selected_generator_sha256": generator_sha,
        "canonical_rule_sha256": sha(canonical.encode()),
        "episode_count": len(rows),
        "demonstration_count": sum(row["counts"]["train"] for row in rows),
        "query_count": sum(row["counts"]["test"] for row in rows),
        "primary_labels": len(global_inputs), "unique_inputs_across_retained_episodes": len(set(global_inputs)),
        "unique_queries_across_retained_episodes": len(set(global_queries)),
        "recorded_protected_racket_evaluations": sum(row["racket_evaluations"] for row in rows),
        "this_audit_racket_evaluations": 0,
        "public_private_separation": "pass", "per_query_demo_only_identifiability": "pass",
        "rows": rows,
        "limits": ["Six retained episodes; no all-seed or universal-rival claim.",
                   "This audit checks retained bytes and an independent Python expansion; labels were executed by each CLI export."]
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
