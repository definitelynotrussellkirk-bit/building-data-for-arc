from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
TASK = "0a855288946a"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
CANON_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
OUT_DIR = ROOT.parent / "checks" / "audit" / TASK


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator():
    spec = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def canonical_task():
    for line in CANON_PATH.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise RuntimeError("canonical task missing")


def main() -> int:
    gen = load_generator()
    canonical = canonical_task()
    failures: list[dict[str, object]] = []
    canonical_pairs = [*canonical["train"], *canonical["test"]]
    for i, pair in enumerate(canonical_pairs):
        checks = gen.self_check(pair["input"])
        strict = gen.strict_canonical_like(pair["input"])
        mirrored = gen.rule_mirror(pair["input"])
        if checks or strict or mirrored != pair["output"]:
            failures.append({
                "kind": "canonical",
                "index": i,
                "self_check": checks,
                "strict": strict,
                "mirror_matches": mirrored == pair["output"],
            })

    audit_seed = 20261004
    bands = ("easy", "medium", "hard")
    samples_per_band = 100
    profile_counts: dict[str, dict[str, int]] = {}
    unique_inputs: set[str] = set()
    racket_inputs = []
    racket_expected = []
    generated_count = 0
    rival_comparisons = 0

    for band in bands:
        pc = Counter()
        for sample_index in range(samples_per_band):
            grid = gen.generate(audit_seed, sample_index, difficulty=band)
            generated_count += 1
            pc[gen.schedule_profile(audit_seed, sample_index, band)] += 1
            key = json.dumps(grid, separators=(",", ":"))
            unique_inputs.add(key)
            errors = gen.self_check(grid, difficulty=band)
            expected = gen.rule_mirror(grid)
            if errors:
                failures.append({"kind": "self_check", "band": band, "sample_index": sample_index, "errors": errors})
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_comparisons += 1
                if rival(grid) == expected:
                    failures.append({"kind": "surviving_rival", "band": band, "sample_index": sample_index, "rival": name})
            if sample_index < 4:
                racket_inputs.append(grid)
                racket_expected.append(expected)
        profile_counts[band] = dict(sorted(pc.items()))

    override_cases = ((3, 3, 2), (8, 8, 4), (8, 3, 4), (3, 8, 2))
    override_count = 0
    for band in bands:
        for case_index, (h, w, palette_size) in enumerate(override_cases):
            grid = gen.generate(
                audit_seed + case_index,
                1000 + case_index,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                palette_size=palette_size,
            )
            override_count += 1
            observed = gen.observe_overrides(grid)
            expected_observed = {"grid_h": h, "grid_w": w, "palette_size": palette_size}
            if observed != expected_observed or gen.self_check(grid, difficulty=band):
                failures.append({
                    "kind": "override",
                    "band": band,
                    "case": expected_observed,
                    "observed": observed,
                    "errors": gen.self_check(grid, difficulty=band),
                })

    lesson_count = 0
    for band in bands:
        for start in range(4):
            pairs = []
            for sample_index in range(start, start + 4):
                grid = gen.generate(audit_seed, sample_index, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            reasons = gen.lesson_identifiable(pairs[:3], pairs[3])
            lesson_count += 1
            if reasons:
                failures.append({"kind": "lesson", "band": band, "start": start, "reasons": reasons})

    preliminary = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK,
        "generator_sha256": sha256(GEN_PATH),
        "rule_hash": gen.RULE_HASH,
        "audit_seed": audit_seed,
        "sample_policy": {
            "bands": list(bands),
            "sample_indices": [0, samples_per_band - 1],
            "samples_per_band": samples_per_band,
            "generated_total": generated_count,
            "unique_inputs": len(unique_inputs),
        },
        "canonical_pairs_checked": len(canonical_pairs),
        "rival_names": sorted(gen.SEMANTIC_RIVALS),
        "rival_comparisons": rival_comparisons,
        "profile_counts": profile_counts,
        "override_cases_checked": override_count,
        "lesson_windows_checked": lesson_count,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "racket_probe": {
            "input_count": len(racket_inputs),
            "expected_outputs": racket_expected,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "probe.json").write_text(json.dumps(preliminary, indent=2) + "\n")
    (OUT_DIR / "input.json").write_text(json.dumps({"inputs": racket_inputs}, indent=2) + "\n")
    print(json.dumps({k: preliminary[k] for k in ("status", "sample_policy", "canonical_pairs_checked", "rival_comparisons", "override_cases_checked", "lesson_windows_checked", "failures")}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
