"""Bounded, input-only audit probes; public Racket application labels fixtures."""
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
ROOT = WORK / "repo"
OUT = Path(__file__).resolve().parent
TASK = "23c3ab5fa55f"
SOURCE = ROOT / "generators" / TASK / "generator.py"
EXPECTED_HASH = "1cce6cc32439d1eefebb7d8faa9a128b6788b39a8c31e933e8d72fe954702800"
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs


def compact(value):
    result = []
    for row in value:
        nonzero = list(filter(None, row))
        result.append(nonzero + [0] * (len(row) - len(nonzero)))
    return result


def distinct_compact(value):
    result = []
    for row in value:
        seen = set()
        values = []
        for color in row:
            if color != 0 and color not in seen:
                seen.add(color)
                values.append(color)
        result.append(values + [0] * (len(row) - len(values)))
    return result


def descending_compact(value):
    result = []
    for row in value:
        values = sorted(filter(None, row), reverse=True)
        result.append(values + [0] * (len(row) - len(values)))
    return result


def main():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert digest == EXPECTED_HASH, (digest, EXPECTED_HASH)
    spec = importlib.util.spec_from_file_location("audited_row_compaction", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical = []
    for pair in pairs:
        value = deepcopy(pair["input"])
        canonical.append({
            "split": pair["split"], "pair_index": pair["pair_index"],
            "self_check": generator.self_check(value),
            "mirror_matches_stored": generator.rule_mirror(value) == pair["output"],
            "independent_matches_stored": compact(value) == pair["output"],
            "distinct_compact_matches_stored": distinct_compact(value) == pair["output"],
            "descending_compact_matches_stored": descending_compact(value) == pair["output"],
            "input_unmutated": value == pair["input"],
        })

    overrides = []
    cases = [
        {"grid_h": 6.9}, {"grid_w": "9"}, {"active_rows": 3.8},
        {"n_distinct_colors": 2.9}, {"unrecognized_control": 999},
        {"grid_h": 6, "active_rows": 8},
    ]
    for request in cases:
        record = {"seed": 17, "sample_index": 0, "difficulty": "medium", "overrides": request}
        try:
            value = generator.generate(17, 0, difficulty="medium", **request)
            record.update(status="accepted", observed=generator.observe_overrides(value),
                          self_check=generator.self_check(value))
        except Exception as exc:
            record.update(status="rejected", exception_type=type(exc).__name__, error=str(exc))
        overrides.append(record)

    # Stop on the first five-pair default window with four fitting demos and
    # a changing query. This is a targeted search, not a distribution census.
    found = None
    examined = 0
    for band in ("easy", "medium", "hard"):
        for seed in range(256):
            inputs = [generator.generate(seed, index, difficulty=band) for index in range(5)]
            examined += 1
            matches = [distinct_compact(value) == compact(value) for value in inputs]
            if matches == [True, True, True, True, False]:
                found = {"seed": seed, "sample_index": 0, "difficulty": band,
                         "n_train": 4, "n_test": 1, "inputs": inputs,
                         "rival_matches_independent": matches,
                         "self_check": [generator.self_check(value) for value in inputs],
                         "distinct_inputs": len({tuple(map(tuple, value)) for value in inputs}),
                         "nonidentity_inputs": [compact(value) != value for value in inputs]}
                break
        if found:
            break

    fixtures = [
        {"name": "minimal_duplicate_after_gap", "input": [[4, 0, 4]],
         "expected_from_selected_rule": [[4, 4, 0]],
         "distinct_compact_output": [[4, 0, 0]]},
        {"name": "minimal_distinct_order", "input": [[7, 0, 1, 7]],
         "expected_from_selected_rule": [[7, 1, 7, 0]],
         "distinct_compact_output": [[7, 1, 0, 0]]},
    ]
    for fixture in fixtures:
        fixture["self_check"] = generator.self_check(fixture["input"])
    apply_inputs = [pair["input"] for pair in pairs] + [item["input"] for item in fixtures]
    if found:
        apply_inputs.extend(found["inputs"])
    (OUT / "fixtures.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    (OUT / "apply-inputs.json").write_text(json.dumps({"inputs": apply_inputs}) + "\n")
    report = {
        "schema": "row-compaction-bounded-audit-probe-v1",
        "task_id": TASK, "source": str(SOURCE), "source_sha256": digest,
        "source_sha256_after": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "canonical": canonical, "override_probes": overrides,
        "search": {"five_draw_windows_examined": examined, "maximum_seed_per_band": 255,
                   "rival": "Stable first-occurrence deduplication of each row's nonzero colors, then zero-pad right.",
                   "found": found},
        "apply_input_indices": {"canonical": [0,1,2,3,4], "minimal_fixtures": [5,6],
                                "candidate_lesson": [7,8,9,10,11] if found else []},
        "reference_status": "Candidate outputs require confirmation through public arcpuzzles apply.",
    }
    (OUT / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"source_sha256": digest,
                      "canonical_distinct_rival_fits": [item["distinct_compact_matches_stored"] for item in canonical],
                      "windows_examined": examined,
                      "found": {key: found[key] for key in ("seed","difficulty","rival_matches_independent")} if found else None,
                      "override_statuses": [{"overrides": item["overrides"], "status": item["status"],
                                             "observed": item.get("observed")} for item in overrides]}))


if __name__ == "__main__":
    main()
