from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
HOME = REPO / "generators" / "90e1b47a15f9"
SOURCE = HOME / "generator.py"
spec = importlib.util.spec_from_file_location("audit_90e1b47a15f9", SOURCE)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main():
    here = Path(__file__).resolve().parent
    fixture = json.loads((HOME / "counterexamples" / "erase_keys_and_doors.json").read_text())
    grid = fixture["input"]
    truth = mod.rule_mirror(grid)
    rival = mod.SEMANTIC_RIVALS["erase_keys_and_doors"](grid)
    differing = sum(
        left != right
        for truth_row, rival_row in zip(truth, rival)
        for left, right in zip(truth_row, rival_row)
    )

    rotations = 0
    ambiguous = []
    profile_sets = []
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            pairs = []
            for offset in range(6):
                sample = mod.generate(1207 + start, start + offset, difficulty=band)
                pairs.append({"input": sample, "output": mod.rule_mirror(sample)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = mod.lesson_identifiable(demos, query)
                rotations += 1
                if reasons:
                    ambiguous.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "reasons": reasons,
                        }
                    )
                profile_sets.append(
                    sorted(mod.observe_overrides(pair["input"])["route_profile"] for pair in demos)
                )

    report = {
        "schema": "review-audit-probe-v1",
        "task_id": "90e1b47a15f9",
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "fixture_generator_sha256": fixture["generator_sha256"],
        "fixture_source_current": fixture["generator_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "self_check": mod.self_check(grid, difficulty="medium"),
        "mirror_matches_retained_authority": truth == fixture["authority_output"],
        "erase_rival_matches_retained": rival == fixture["rival_output"],
        "erase_rival_differing_cells": differing,
        "rotations_checked": rotations,
        "ambiguous_rotations": ambiguous,
        "declared_rivals": sorted(mod.SEMANTIC_RIVALS),
        "declared_profiles": list(mod.SCHEDULE_PROFILES),
    }
    (here / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "fixture_source_current": report["fixture_source_current"],
        "differing_cells": differing,
        "rotations_checked": rotations,
        "ambiguous_rotations": len(ambiguous),
    }))


if __name__ == "__main__":
    main()
