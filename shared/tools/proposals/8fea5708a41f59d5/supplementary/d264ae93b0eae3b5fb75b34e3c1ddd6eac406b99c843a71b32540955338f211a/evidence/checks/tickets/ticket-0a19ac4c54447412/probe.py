#!/usr/bin/env python3
"""One source-bound replay of the pinned operation-coverage tool request."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import signal
import sys
import time

TICKET = "ticket-0a19ac4c54447412"
REQUEST = "review-7e737706f3d39f6f:v0001:F1"
ASSET = "shared/tools/proposals/8fea5708a41f59d5"
EXPECTED = {
    "REVIEW/suggestions.json": "a264898541b5dfff6ded18cd1a96798efe9576d7c70b3141864c8e86866c47b2",
    ASSET + "/manifest.json": "2a7122bde98237bbcc27096786f1c59e66c2c36e5217a2fc5f05c66d825112de",
    "generators/bee63e6e52bd/generator.py": "33d8f354812b25e8e5afe7555c6296040b7d63e0b6315dea5a184c5515227b3f",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    started = time.monotonic()
    repo = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    verified = {}
    for relative, expected in EXPECTED.items():
        actual = digest((repo / relative).read_bytes())
        assert actual == expected, (relative, actual, expected)
        verified[relative] = actual
    suggestions = json.loads((repo / "REVIEW/suggestions.json").read_bytes())
    request = next(r for r in suggestions["items"] if r["request_id"] == REQUEST)
    request_sha = digest(json.dumps(request, sort_keys=True, separators=(",", ":")).encode())
    assert request_sha == "7c7ad0ec236951800b3dcf81ec91770cdb8c5128fd0c4432668af56d228a2bd1"
    assets = json.loads((repo / ASSET / "manifest.json").read_bytes())
    assert assets["request_id"] == REQUEST and assets["runtime_approved"] is False
    for row in assets["files"]:
        raw = (repo / row["path"]).read_bytes()
        actual = digest(raw)
        assert len(raw) == row["bytes"] and actual == row["sha256"], row["path"]
        verified[row["path"]] = actual
    coverage = repo / ASSET / "checks/coverage-review"
    baseline = json.loads((coverage / "no_diagonal_baseline.json").read_bytes())
    geometry = json.loads((coverage / "baseline_geometry.json").read_bytes())
    prior = json.loads((coverage / "no_diagonal_racket_witness.json").read_bytes())
    witness = baseline["first_production_witnesses"]["medium"]
    assert (witness["seed"], witness["start_sample_index"], witness["query_pair_index"]) == (44007, 28, 3)
    assert witness["existing_lesson_identifiable"] == []
    cached_pattern = [p["output"] == r for p, r in zip(witness["pairs"], witness["rival_outputs"], strict=True)]
    assert cached_pattern == [True, True, True, False]
    hard_geometry = geometry["baseline_bands"]["hard"]
    hard_census = baseline["bands"]["hard"]
    assert hard_geometry["draws"] == hard_geometry["zero_both_rays"] == 160
    assert hard_census["pairs_without_diagonal"] == hard_census["pairs"] == 400
    assert hard_census["production_ambiguities"] == hard_census["rotation_ambiguities"] == 0
    assert prior["selected_rule_hash"] == baseline["rule_hash"] == "eedba8f59365"

    # Only this batch executes the reference: four retained inputs, no generation/census.
    from arcpuzzles import Catalog
    applied = Catalog(repo).apply("bee63e6e52bd", [p["input"] for p in witness["pairs"]], timeout=90)
    assert applied["generator_sha256"] == EXPECTED["generators/bee63e6e52bd/generator.py"]
    assert applied["executed_rule_hash"] == applied["catalog_rule_hash"] == "eedba8f59365"
    assert applied["rule_hash_matches_catalog"] is True
    results = applied["results"]
    assert len(results) == 4
    output_matches = [r["output"] == p["output"] for r, p in zip(results, witness["pairs"], strict=True)]
    pattern = [r["output"] == rival for r, rival in zip(results, witness["rival_outputs"], strict=True)]
    assert output_matches == [True] * 4
    assert pattern == [True, True, True, False]
    for old, fresh in zip(prior["checks"], results, strict=True):
        assert old["input_sha256"] == fresh["input_sha256"]
        assert old["output_sha256"] == fresh["output_sha256"]
    print(json.dumps({
        "ticket_id": TICKET, "type": "tool_reproduction", "status": "completed",
        "request_id": REQUEST, "request_sha256": request_sha,
        "proposed_request_disposition": "Retain accepted, source-bound operation-expectation request; motivating four-label replay reproduced. Shared tooling implementation and runtime approval remain unassessed.",
        "assets_verified": len(assets["files"]), "verified_sha256": verified,
        "historical_generator_sha256": baseline["generator_sha256"],
        "current_generator_sha256": applied["generator_sha256"],
        "authority": applied,
        "retained_outputs_match_fresh_racket": output_matches,
        "rival_matches_fresh_racket": pattern,
        "historical_hard_geometry": {"draws": 160, "zero_both_rays": 160},
        "historical_hard_census": {"pairs": 400, "pairs_without_diagonal": 400, "production_ambiguities": 0, "rotation_ambiguities": 0},
        "limit": "Four historical inputs freshly relabeled; cached geometry/census arithmetic only. Rival outputs replayed from hash-verified retained grids, not independently recomputed. No present-generator defect, fresh hard-band census, shared-gate implementation, universal semantic coverage, or training benefit established.",
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("115 second whole-probe budget")))
    signal.alarm(115)
    main()
