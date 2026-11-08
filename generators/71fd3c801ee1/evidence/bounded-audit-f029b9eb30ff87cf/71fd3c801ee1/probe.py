from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "71fd3c801ee1"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    canonical_rows = []
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        canonical_rows.append({
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input_sha256": digest(pair["input"]),
            "self_check": GEN.self_check(pair["input"]),
            "strict_canonical_like": GEN.strict_canonical_like(pair["input"]),
            "rule_mirror_exact": GEN.rule_mirror(pair["input"]) == pair["output"],
        })

    samples = []
    rival_match_counts = {name: 0 for name in GEN.LESSON_COMPETITORS}
    unique = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(20):
            seed = 510_000 + band_index * 10_000 + index
            grid = GEN.generate(seed, index, difficulty=band)
            truth = GEN.rule_mirror(grid)
            unique.add(digest(grid))
            matches = {}
            for name, rival in GEN.LESSON_COMPETITORS.items():
                match = rival(grid) == truth
                matches[name] = match
                rival_match_counts[name] += int(match)
            samples.append({
                "band": band,
                "index": index,
                "seed": seed,
                "input_sha256": digest(grid),
                "self_check": GEN.self_check(grid),
                "strict_canonical_like": GEN.strict_canonical_like(grid),
                "rival_matches": matches,
                "observed": GEN.observe_overrides(grid),
            })

    family_rows = []
    for index, family in enumerate(GEN.TARGET_FAMILIES):
        grid = GEN.generate(620_000 + index, index, difficulty="hard", target_family=family)
        family_rows.append({
            "requested": family,
            "observed": GEN.observe_overrides(grid),
            "self_check": GEN.self_check(grid),
            "strict_canonical_like": GEN.strict_canonical_like(grid),
        })

    contract = {}
    for name, kwargs in {
        "unknown_override": {"typo_axis": "small_asym"},
        "invalid_difficulty": {"difficulty": "expert"},
    }.items():
        try:
            if "difficulty" in kwargs:
                GEN.generate(1, 0, **kwargs)
            else:
                GEN.generate(1, 0, difficulty="easy", **kwargs)
        except Exception as exc:
            contract[name] = {"raised": type(exc).__name__, "message": str(exc)}
        else:
            contract[name] = {"raised": None}

    evidence = {
        "schema": "arcpuzzles-audit-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA256,
        "version": getattr(GEN, "VERSION", None),
        "rule_hash": getattr(GEN, "RULE_HASH", None),
        "canonical": canonical_rows,
        "sample_probe": {
            "samples": len(samples),
            "unique_inputs": len(unique),
            "all_self_checks_empty": all(not row["self_check"] for row in samples),
            "all_strict_checks_empty": all(not row["strict_canonical_like"] for row in samples),
            "rival_match_counts": rival_match_counts,
            "rows": samples,
        },
        "family_overrides": family_rows,
        "call_contract": contract,
    }
    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": TASK_ID,
        "source_sha256": SOURCE_SHA256,
        "canonical_pairs": len(canonical_rows),
        "canonical_exact": all(row["rule_mirror_exact"] for row in canonical_rows),
        "samples": len(samples),
        "unique_inputs": len(unique),
        "rival_match_counts": rival_match_counts,
        "all_self_checks_empty": evidence["sample_probe"]["all_self_checks_empty"],
        "all_strict_checks_empty": evidence["sample_probe"]["all_strict_checks_empty"],
        "all_family_overrides_exact": all(
            row["observed"] == {"target_family": row["requested"]}
            for row in family_rows
        ),
        "call_contract": contract,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
