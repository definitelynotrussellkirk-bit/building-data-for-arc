"""Bounded current-source schedule/rival probe; uses no Racket executions."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def digest(value) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import canonical_pairs, load_selected_generator

    task_id = "28423cdf02cc"
    mod, source, source_hash = load_selected_generator(task_id, root=repo)
    seeds = [0, 20261021]
    bands = ["easy", "medium", "hard"]
    period, demonstrations = mod.LESSON_SCHEDULE_PERIOD, mod.EXAMPLES_NEEDED
    positions = range(period + demonstrations)
    failures, generated, lessons = [], [], []
    rival_refutations = Counter()
    seen_inputs = set()
    strict_count = 0
    for seed in seeds:
        for band in bands:
            pairs = []
            for index in positions:
                grid = mod.generate(seed, index, difficulty=band)
                output = mod.rule_mirror(grid)
                pair = {"input": grid, "output": output}
                pairs.append(pair)
                facts = mod._analyze(grid)["facts"]
                profile = mod.schedule_profile(seed, index, difficulty=band)
                canonical = not mod.strict_canonical_like(grid)
                off_lattice = any((r - 1) % 3 != 0 or (c - 5) % 3 != 0 for r, c in facts["markers"])
                valid = not mod.self_check(grid)
                realized = canonical if profile == "canonical_profile" else off_lattice and not canonical
                if not (valid and realized):
                    failures.append({"kind": "profile", "seed": seed, "band": band, "sample_index": index, "pair": pair})
                for name, rival in mod.LESSON_COMPETITORS.items():
                    rival_refutations[name] += rival(grid) != output
                strict_count += canonical
                seen_inputs.add(digest(grid))
                generated.append({"seed": seed, "band": band, "sample_index": index, "profile": profile,
                                  "canonical_profile_index": facts["canonical_profile"], "valid": valid,
                                  "profile_realized": realized, "input_sha256": digest(grid)})
            for start in range(period):
                window = pairs[start:start + demonstrations + 1]
                rotation_reasons = []
                for query_index, query in enumerate(window):
                    demos = [pair for index, pair in enumerate(window) if index != query_index]
                    reasons = mod.lesson_identifiable(demos, query)
                    rotation_reasons.append(reasons)
                    if reasons:
                        failures.append({"kind": "rotation", "seed": seed, "band": band, "start": start,
                                         "query_index": query_index, "reasons": reasons, "pairs": window})
                lessons.append({"seed": seed, "band": band, "start": start,
                                "production_reasons": rotation_reasons[-1], "rotation_reasons": rotation_reasons})

    canonical = canonical_pairs(task_id, root=repo, labeled_only=True)
    canonical_checks = {
        "pair_count": len(canonical),
        "self_check_passes": sum(not mod.self_check(pair["input"]) for pair in canonical),
        "strict_profile_passes": sum(not mod.strict_canonical_like(pair["input"]) for pair in canonical),
        "mirror_matches_retained_outputs": sum(mod.rule_mirror(pair["input"]) == pair["output"] for pair in canonical),
        "declared_shortcut_fits": {name: sum(rival(pair["input"]) == pair["output"] for pair in canonical)
                                   for name, rival in mod.CANONICAL_SHORTCUTS.items()},
    }
    report = {
        "task_id": task_id, "generator_sha256": source_hash,
        "source_unchanged_during_probe": digest(source.read_bytes()) == source_hash,
        "scope": {"seeds": seeds, "bands": bands, "sample_indices": list(positions),
                  "cyclic_start_residues": list(range(period)), "demonstrations": demonstrations,
                  "query_policy": "Each of four consecutive pairs held out once"},
        "generated_positions": len(generated), "unique_inputs": len(seen_inputs),
        "strict_generated_positions": strict_count, "lesson_count": len(lessons),
        "pair_placements_in_overlapping_windows": len(lessons) * (demonstrations + 1),
        "rotation_count": sum(len(row["rotation_reasons"]) for row in lessons),
        "rival_refutations_over_generated_positions": dict(rival_refutations),
        "canonical_checks": canonical_checks, "generated": generated, "lessons": lessons,
        "failures": failures,
        "limits": "Python-mirror diagnostics at two fixed seeds; no new Racket execution. Consecutive attempted indices only, without materializer rejection filtering. Finite declared rivals, not unique induction over all programs.",
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("generated", "lessons")}, indent=2))
    if failures or not report["source_unchanged_during_probe"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
