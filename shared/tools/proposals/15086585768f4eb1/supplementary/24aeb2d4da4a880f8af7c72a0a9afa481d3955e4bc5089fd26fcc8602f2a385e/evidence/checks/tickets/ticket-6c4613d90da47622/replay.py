#!/usr/bin/env python3
"""One bounded replay of the pinned proposal's retained labels and rivals.

Reads exact issued ZIP members without extracting a runtime or making new draws.
The reference probe is executed unchanged; authoritative labels are retained
labels, not a fresh Racket execution.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import zipfile

PINS = {
    "repo/REVIEW/suggestions.json": "0e728d53a0192eb8043ce9534ee09abe8aa488785255bfc05d7160ffc07fc603",
    "repo/shared/tools/proposals/15086585768f4eb1/manifest.json": "8f2d3269b1b1b10b24a594e8bc51f866fd87b7bdb6ae3a4bac90e1e6edbd75d1",
    "repo/generators/27b865c5f43a/generator.py": "495ba0e0517cf001c44dfcd69c0ca56e98e4bc767fdcfd76e56e726424be377e",
}
REQUEST_ID = "review-fa7d98e55ec14764:v0001:F1"
REQUEST_HASH = "ec2759c73779519118221f5e103ae6cbe0224686a36efe726faa10bd22f9e4ab"
PROBE = "repo/generators/27b865c5f43a/workspace/reference_probe.py"
TASK = "repo/shared/data/base/solutions/banks/f716aa11d181/hard_119_build_pairwise_union_gallery__27b865c5f43a.json"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--archive", required=True)
    args.add_argument("--output", required=True)
    opt = args.parse_args()
    work = Path(__file__).resolve().parents[3]
    hashes = {}
    with zipfile.ZipFile(opt.archive) as archive:
        packet_raw = archive.read("WORK/PACKET-MANIFEST.json")
        packet = json.loads(packet_raw)

        def verified(name, local=False):
            raw = (work / name).read_bytes() if local else archive.read("WORK/" + name)
            actual = digest(raw)
            assert actual == packet["files"][name], (name, "packet hash mismatch")
            if name in PINS:
                assert actual == PINS[name], (name, "ticket hash mismatch")
            hashes[name] = actual
            return raw

        requests = json.loads(verified("repo/REVIEW/suggestions.json", local=True))
        request = next(x for x in requests["items"] if x["request_id"] == REQUEST_ID)
        request_hash = digest(json.dumps(request, sort_keys=True, separators=(",", ":")).encode())
        assert request_hash == REQUEST_HASH
        manifest = json.loads(verified("repo/shared/tools/proposals/15086585768f4eb1/manifest.json", local=True))
        assert manifest["request_id"] == REQUEST_ID and len(manifest["files"]) == 1
        declared = manifest["files"][0]
        asset_name = "repo/" + declared["path"]
        raw = verified(asset_name, local=True)
        assert digest(raw) == declared["sha256"] and len(raw) == declared["bytes"]
        audit = json.loads(raw)["audits"][0]
        verified("repo/generators/27b865c5f43a/generator.py")
        source = verified(PROBE)
        task = json.loads(verified(TASK))
        namespace = {"__name__": "retained_reference_probe", "__file__": str(work / PROBE)}
        exec(compile(source, "ZIP:WORK/" + PROBE, "exec"), namespace)

    functions = {
        "left_column_rule": namespace["rule_output"],
        "color_sort": namespace["color_sorted_output"],
        "row_sort": namespace["row_sorted_output"],
    }
    canonical = list(task["visible_context"]["train"])
    for inp, out in zip(task["visible_context"]["test_inputs"], task["verification"]["expected_test_outputs"]):
        canonical.append({"input": inp["input"], "output": out})
    canonical_checks = {
        name: {"checked": len(canonical), "matches": sum(fn(pair["input"]) == pair["output"] for pair in canonical)}
        for name, fn in functions.items()
    }
    assert len(canonical) == 5 and all(x["matches"] == 5 for x in canonical_checks.values())
    rule_source_hash = digest(task["racket_target"]["target_code"].encode())
    witnesses = []
    for name, record in audit["witnesses"].items():
        for rival, fixture in record["rival_claim"]["witness_examples"].items():
            binding = fixture["source_binding"]
            assert binding["generator_sha256"] == PINS["repo/generators/27b865c5f43a/generator.py"]
            assert binding["rule_task_id"] == "27b865c5f43a"
            assert binding["rule_source_sha256"].startswith("de4d9d03f710")
            expected = fixture["authoritative_output"]
            actual_rule = functions["left_column_rule"](fixture["input"])
            actual_rival = functions[rival](fixture["input"])
            assert actual_rule == expected
            assert actual_rival == fixture["rival_output"]
            changed = [[r, c] for r, row in enumerate(expected) for c, val in enumerate(row) if actual_rival[r][c] != val]
            assert changed
            witnesses.append({
                "witness": name, "rival": rival, "recipe": fixture["recipe"],
                "source_binding": binding, "input": fixture["input"],
                "retained_authoritative_output": expected, "replayed_rival_output": actual_rival,
                "rule_matches_retained_label": True, "rival_matches_retained_prediction": True,
                "differing_cells": changed, "differing_cell_count": len(changed),
            })
    assert len(witnesses) == 2
    searched = audit["lessons"]["searched_rivals"]
    production = [entry["production"] for entry in searched]
    rotations = [rotation for entry in searched for rotation in entry["rotations"]]

    def summary(records):
        statuses = collections.Counter()
        providers = collections.Counter()
        for record in records:
            providers[record["provider_status"]] += 1
            for candidate in record["candidates"].values():
                statuses[candidate["status"]] += 1
        return {"records": len(records), "provider_status_counts": dict(providers), "candidate_status_counts": dict(statuses)}

    result = {
        "ticket_id": "ticket-6c4613d90da47622", "request_id": REQUEST_ID,
        "request_sha256": request_hash, "existing_request_status": request["status"],
        "packet_manifest_sha256": digest(packet_raw), "source_hashes": hashes,
        "canonical_checks": canonical_checks, "replayed_witnesses": witnesses,
        "active_target_code_sha256": rule_source_hash,
        "retained_report": {
            "status": audit["status"], "strict_hits": audit["strict_hits"],
            "strict_draws": audit["strict_draws"],
            "canonical_ambiguity": audit["canonical_ambiguity"],
            "lesson_assessment_basis": audit["lessons"]["assessment_basis"],
            "declared_competitors": audit["lessons"]["competitors_declared"],
            "production": summary(production), "rotations": summary(rotations),
            "rotation_policy": sorted({entry["rotation_policy"] for entry in searched}),
            "require_rotations": audit["require_rotations"],
        },
        "new_generator_draws": 0, "fresh_racket_execution": False,
        "probe_scope": "Five retained canonical labels and two retained counterexample grids, evaluated using unchanged issued independent reference_probe.py; report counters inspected, not rerun.",
        "proposed_request_disposition": "Retain accepted status for an independent applicable-rival provider; implementation remains pending. The evidence supports the motivating ordering shortcuts and their repair, but does not establish automatic discovery or shared-provider installation.",
        "remaining_limits": [
            "No fresh authoritative Racket run, full battery, or new lesson census.",
            "Cached report's rotation results are diagnostic; supported consumer rotations must govern future blocking checks.",
            "Retained generic mutations are mostly inapplicable; these outcomes must not be counted as rival refutations.",
            "No shared code changed and no independent provider was implemented in this ticket.",
        ],
    }
    Path(opt.output).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": "completed", "canonical_pairs": 5, "replayed_witnesses": len(witnesses),
                      "differing_cells": {w["rival"]: w["differing_cell_count"] for w in witnesses},
                      "production": result["retained_report"]["production"],
                      "rotations": result["retained_report"]["rotations"]}, sort_keys=True))


if __name__ == "__main__":
    main()
