from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / "repo"
TASK = "28f91ad53b1b"
GENERATOR_PATH = REPO / "generators" / TASK / "generator.py"
OUT = PACKET / "checks" / "audit" / TASK / "probe.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    import sys
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    from reviewer_support import canonical_pairs as read_pairs
    return read_pairs(TASK, root=REPO, labeled_only=True)


def main():
    mod = load_generator()
    canonical = canonical_pairs()
    canonical_mismatches = [
        index for index, pair in enumerate(canonical)
        if mod.rule_mirror(pair["input"]) != pair["output"]
    ]

    exact_failures = []
    exact_checked = 0
    textures = tuple(mod.SCHEDULE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for h, w, n, texture in itertools.product(range(8, 11), range(10, 13), range(2, 6), textures):
            exact_checked += 1
            try:
                grid = mod.generate(
                    20261007,
                    exact_checked,
                    difficulty=difficulty,
                    grid_h=h,
                    grid_w=w,
                    n_seeds=n,
                    texture=texture,
                )
                observed = mod.observe_overrides(grid)
                expected = {"grid_h": h, "grid_w": w, "n_seeds": n, "texture": texture}
                findings = mod.self_check(grid)
                if findings or observed != expected or mod.rule_mirror(grid) is None:
                    exact_failures.append({
                        "difficulty": difficulty,
                        "expected": expected,
                        "observed": observed,
                        "self_check": findings,
                    })
            except Exception as exc:
                exact_failures.append({
                    "difficulty": difficulty,
                    "expected": {"grid_h": h, "grid_w": w, "n_seeds": n, "texture": texture},
                    "error": f"{type(exc).__name__}: {exc}",
                })

    seed = 20261007
    starts_per_band = 100
    lessons = 0
    rotations = 0
    ambiguous = []
    unique_inputs = set()
    witness_hits = {name: 0 for name in mod.SEMANTIC_WITNESSES}
    rival_disagreements = {name: 0 for name in mod.LESSON_COMPETITORS}
    for difficulty in ("easy", "medium", "hard"):
        for start in range(starts_per_band):
            pairs = []
            for offset in range(6):
                grid = mod.generate(seed, start + offset, difficulty=difficulty)
                output = mod.rule_mirror(grid)
                pairs.append({"input": grid, "output": output})
                unique_inputs.add(grid_hash(grid))
                for name, witness in mod.SEMANTIC_WITNESSES.items():
                    witness_hits[name] += bool(witness(grid))
                for name, rival in mod.LESSON_COMPETITORS.items():
                    rival_disagreements[name] += rival(grid) != output
            lessons += 1
            for query_index in range(6):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                reasons = mod.lesson_identifiable(demos, query)
                rotations += 1
                if reasons:
                    ambiguous.append({
                        "difficulty": difficulty,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    })

    result = {
        "schema": "audit-generator-probe-v1",
        "task_id": TASK,
        "generator_sha256": sha256(GENERATOR_PATH),
        "rule_hash": getattr(mod, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_rule_mirror_mismatches": canonical_mismatches,
        "exact_override_combinations_checked": exact_checked,
        "exact_override_failures": exact_failures,
        "lesson_seed": seed,
        "starts_per_band": starts_per_band,
        "lesson_windows": lessons,
        "pairs_per_lesson": 6,
        "query_rotations_checked": rotations,
        "ambiguous_rotations": len(ambiguous),
        "ambiguous_examples": ambiguous[:10],
        "unique_inputs": len(unique_inputs),
        "witness_hits_across_overlapping_pairs": witness_hits,
        "declared_rival_disagreements_across_overlapping_pairs": rival_disagreements,
        "verdict": "no issue found in canonical parity, exact controls, or declared-rival lesson identifiability" if not canonical_mismatches and not exact_failures and not ambiguous else "finding",
        "limitations": [
            "Finite probe against declared rivals only; not exhaustive over all seeds or all plausible programs.",
            "Lesson windows overlap, so witness totals are counts over materialized pair occurrences, not unique inputs.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "canonical_mismatches": canonical_mismatches,
        "exact_checked": exact_checked,
        "exact_failures": len(exact_failures),
        "lessons": lessons,
        "rotations": rotations,
        "ambiguous": len(ambiguous),
        "unique_inputs": len(unique_inputs),
        "witness_hits": witness_hits,
        "rival_disagreements": rival_disagreements,
        "verdict": result["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()
